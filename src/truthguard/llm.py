"""OpenAI-compatible routing with persisted, sliding-window reservations.

Each physical attempt is reserved and logged *before* transport, including failed
attempts. Cache/fixture events are explicitly nonphysical. Token reservations are
conservative and never refunded on failure or a short completion.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import time
from collections.abc import Callable, Sequence
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from .config import ROOT, load_config
from .schemas import CallRecord, LLMResult, LLMUsage


ModelT = TypeVar("ModelT", bound=BaseModel)
Transport = Callable[[str, str, dict[str, str], dict[str, Any]], dict[str, Any] | httpx.Response]
TokenCounter = Callable[[str, str, Sequence[dict[str, str]]], int]


def sanitized_rate_headers(headers: Any) -> dict[str, str]:
    """Keep only numeric/duration rate-limit telemetry, never arbitrary headers."""
    result = {}
    for key, value in dict(headers or {}).items():
        key, value = str(key).lower(), str(value).strip()
        if (re.fullmatch(r"x-ratelimit-[a-z0-9-]{1,80}", key)
                and len(value) <= 120
                and re.fullmatch(r"[0-9. :+/,%-]+|(?:\d+(?:\.\d+)?(?:ms|s|m|h|d)\s*)+", value)):
            result[key] = value
    return result


class ProviderError(RuntimeError):
    def __init__(self, message: str, *, retry_after: float | None = None,
                 rate_limit_headers: dict[str, str] | None = None,
                 status_code: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after
        self.rate_limit_headers = sanitized_rate_headers(rate_limit_headers)
        self.status_code = status_code


class BudgetExceeded(ProviderError):
    """A local reservation cannot be served."""


class CriticBudgetExceeded(BudgetExceeded):
    """The whole-question physical critic budget is exhausted."""


class ProviderQuotaExceeded(BudgetExceeded):
    """A provider reported quota exhaustion; stop this flow cleanly."""


class AllProvidersUnavailable(ProviderError):
    """No configured provider completed the request."""


class InvalidResponse(ProviderError):
    """A physical attempt returned invalid JSON or a schema mismatch."""


class LLMRouter:
    def __init__(self, config: dict[str, Any] | None = None, *,
                 database_path: str | Path | None = None, transport: Transport | None = None,
                 client: httpx.Client | None = None, clock: Callable[[], float] | None = None,
                 sleep: Callable[[float], None] | None = None,
                 token_counter: TokenCounter | None = None) -> None:
        self.config = config or load_config()
        path = Path(database_path or self.config["project"].get(
            "database_path", "data/cache/truthguard.sqlite3"))
        self.database_path = path if path.is_absolute() else ROOT / path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.transport, self.client = transport, client
        self.clock, self.sleep = clock or time.time, sleep or time.sleep
        self.token_counter = token_counter or self.estimate_input_tokens
        self._critic_requests_remaining: int | None = None
        self._initialize_database()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_database(self) -> None:
        with self._connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS response_cache (
                    cache_key TEXT PRIMARY KEY, provider TEXT NOT NULL, model TEXT NOT NULL,
                    payload TEXT NOT NULL, created_at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS call_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, cache_key TEXT NOT NULL,
                    provider TEXT NOT NULL, role TEXT NOT NULL, stage TEXT NOT NULL,
                    model TEXT NOT NULL, created_at REAL NOT NULL,
                    cached INTEGER NOT NULL DEFAULT 0, success INTEGER NOT NULL DEFAULT 1,
                    error TEXT, usage_json TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS idx_call_log_provider_time ON call_log(provider, created_at);
                CREATE TABLE IF NOT EXISTS provider_quota (
                    provider TEXT PRIMARY KEY, blocked_until REAL NOT NULL);
            """)
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(call_log)")}
            additions = {
                "physical_attempt": "INTEGER NOT NULL DEFAULT 1",
                "attempt_kind": "TEXT NOT NULL DEFAULT 'first_json'",
                "outcome": "TEXT NOT NULL DEFAULT 'valid'",
                "reserved_input_tokens": "INTEGER NOT NULL DEFAULT 0",
                "reserved_output_tokens": "INTEGER NOT NULL DEFAULT 0",
                "headers_json": "TEXT NOT NULL DEFAULT '{}'",
                "status_code": "INTEGER",
                "served_model": "TEXT",
                "accounting_version": "INTEGER NOT NULL DEFAULT 0",
            }
            for name, definition in additions.items():
                if name not in columns:
                    connection.execute(f"ALTER TABLE call_log ADD COLUMN {name} {definition}")
            connection.execute("UPDATE call_log SET physical_attempt=0, attempt_kind='cache' WHERE cached=1")
            cache_columns = {row["name"] for row in connection.execute("PRAGMA table_info(response_cache)")}
            if "served_model" not in cache_columns:
                connection.execute("ALTER TABLE response_cache ADD COLUMN served_model TEXT")
            connection.execute("""CREATE INDEX IF NOT EXISTS idx_call_log_model_time
                ON call_log(provider, model, created_at)""")

    @staticmethod
    def make_cache_key(provider: str, model: str, messages: Sequence[dict[str, str]],
                       params: dict[str, Any] | None = None) -> str:
        canonical = json.dumps({"provider": provider, "model": model, "messages": list(messages),
                                "params": params or {}}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def estimate_input_tokens(provider: str, model: str, messages: Sequence[dict[str, str]]) -> int:
        """Offline byte upper estimate, including envelope overhead; no tokenizer download.

        Inject a model-specific offline token_counter when an exact tokenizer is
        available. A byte estimate deliberately sacrifices throughput for headroom.
        """
        return 64 + len(json.dumps(list(messages), ensure_ascii=False).encode("utf-8"))

    def _cached_payload(self, cache_key: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT payload FROM response_cache WHERE cache_key=?", (cache_key,)).fetchone()
        return json.loads(row["payload"]) if row else None

    def _cached_model(self, cache_key: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute("SELECT served_model FROM response_cache WHERE cache_key=?", (cache_key,)).fetchone()
        return row[0] if row else None

    def _store_payload(self, cache_key: str, provider: str, model: str, payload: dict[str, Any],
                       served_model: str | None = None) -> None:
        with self._connect() as connection:
            connection.execute("""INSERT INTO response_cache
                (cache_key, provider, model, payload, created_at, served_model) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET payload=excluded.payload, created_at=excluded.created_at,
                    served_model=excluded.served_model""",
                (cache_key, provider, model, json.dumps(payload, sort_keys=True), self.clock(), served_model))

    def _safe_error(self, error: Any) -> str:
        text = str(error)
        for settings in self.config.get("providers", {}).values():
            key = os.getenv(settings.get("api_key_env", ""))
            if key:
                text = text.replace(key, "[REDACTED]")
        text = re.sub(r"(?i)bearer\s+\S+|\b(?:sk|gsk)-[\w-]+", "[REDACTED]", text)
        return text.replace("\n", " ").replace("\r", " ")[:400]

    def _insert_record(self, connection: sqlite3.Connection, *, cache_key: str, provider: str,
                       model: str, role: str, stage: str, kind: str, physical: bool,
                       input_tokens: int = 0, output_tokens: int = 0, served_model: str | None = None) -> int:
        cursor = connection.execute("""INSERT INTO call_log
            (cache_key, provider, role, stage, model, created_at, cached, success, usage_json,
             physical_attempt, attempt_kind, outcome, reserved_input_tokens, reserved_output_tokens,
             served_model, accounting_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
            (cache_key, provider, role, stage, model, self.clock(), int(kind == "cache"),
             int(not physical), LLMUsage().model_dump_json(), int(physical), kind,
              "pending" if physical else kind, input_tokens, output_tokens, served_model))
        return int(cursor.lastrowid)

    def _finish_record(self, record_id: int, *, outcome: str, usage: LLMUsage | None = None,
                       error: Any = None, headers: Any = None, status_code: int | None = None,
                       served_model: str | None = None) -> None:
        usage = usage or LLMUsage()
        with self._connect() as connection:
            connection.execute("""UPDATE call_log SET success=?, outcome=?, error=?, usage_json=?,
                headers_json=?, status_code=?, served_model=?,
                reserved_input_tokens=MAX(reserved_input_tokens, ?),
                reserved_output_tokens=MAX(reserved_output_tokens, ?) WHERE id=?""",
                (int(outcome in {"valid", "cache", "offline"}), outcome,
                 self._safe_error(error) if error is not None else None, usage.model_dump_json(),
                 json.dumps(sanitized_rate_headers(headers)), status_code, served_model,
                 usage.prompt_tokens, usage.completion_tokens, record_id))

    def call_records(self, provider: str | None = None) -> list[CallRecord]:
        query, args = "SELECT * FROM call_log", ()
        if provider:
            query, args = query + " WHERE provider=?", (provider,)
        with self._connect() as connection:
            rows = connection.execute(query + " ORDER BY id", args).fetchall()
        return [CallRecord(
            record_id=row["id"], cache_key=row["cache_key"], provider=row["provider"], role=row["role"],
            stage=row["stage"], model=row["served_model"] or row["model"], requested_model=row["model"],
            created_at=datetime.fromtimestamp(row["created_at"], tz=timezone.utc),
            cached=bool(row["cached"]), success=bool(row["success"]), error=row["error"],
            usage=LLMUsage.model_validate_json(row["usage_json"]), physical_attempt=bool(row["physical_attempt"]),
            attempt_kind=row["attempt_kind"] if row["accounting_version"] or row["cached"] else "legacy",
            outcome=row["outcome"] if row["accounting_version"] else "legacy_unknown",
            reserved_input_tokens=row["reserved_input_tokens"], reserved_output_tokens=row["reserved_output_tokens"],
            rate_limit_headers=sanitized_rate_headers(json.loads(row["headers_json"])), status_code=row["status_code"],
            accounting_version=row["accounting_version"],
        ) for row in rows]

    def export_call_report(self, provider: str | None = None) -> str:
        """Readable, persistent-record export; prompts, payloads and auth headers are excluded."""
        lines = ["# LLM physical-attempt evidence", "", "Cache/fixture events reserve no budget.",
                 "Accounting v1 records each physical attempt; legacy v0 rows cannot prove attempt counts.",
                 "Model is response-reported when available, otherwise requested; budgets key on requested model.", ""]
        records = self.call_records(provider)
        physical = [row for row in records if row.physical_attempt and row.accounting_version == 1]
        lines.extend([
            f"Physical attempts (v1): {len(physical)}; "
            f"first-JSON valid: {sum(row.attempt_kind == 'first_json' and row.outcome == 'valid' for row in physical)}; "
            f"repair attempts: {sum(row.attempt_kind == 'repair' for row in physical)}; "
            f"cache hits: {sum(row.cached for row in records)}; "
            f"rate errors: {sum(row.outcome == 'rate_error' for row in physical)}; "
            f"quota errors: {sum(row.outcome == 'quota_error' for row in physical)}.", "",
        ])
        for row in records:
            lines.append(f"- #{row.record_id} {row.created_at.isoformat()} {row.provider}/{row.model} "
                         f"{row.stage}: {row.attempt_kind} / {row.outcome}; physical={row.physical_attempt}; "
                         f"reserved input/output={row.reserved_input_tokens}/{row.reserved_output_tokens}; "
                         f"HTTP={row.status_code or '-'}; requested={row.requested_model}; accounting=v{row.accounting_version}")
            if row.rate_limit_headers:
                lines.append("  rate limits: " + json.dumps(row.rate_limit_headers, sort_keys=True))
            if row.error:
                lines.append("  error: " + self._safe_error(row.error))
        return "\n".join(lines) + "\n"

    def _model_limits(self, provider: str, model: str) -> dict[str, Any]:
        settings = self.config.get("providers", {}).get(provider, {})
        limits = {key: settings.get(key, 0) for key in (
            "rpm_limit", "rps_limit", "tpm_limit", "input_tpm_limit", "output_tpm_limit", "min_interval_seconds")}
        limits.update(settings.get("model_limits", {}).get(model, {}))
        if any(float(value) < 0 for value in limits.values()):
            raise ValueError("model rate limits must be nonnegative")
        if provider == "groq" and model == "qwen/qwen3.8-27b":
            limits["output_tpm_limit"] = min(float(limits.get("output_tpm_limit") or 1000), 1000)
        return limits

    def model_budget_status(self) -> dict[str, dict[str, dict[str, Any]]]:
        now = self.clock()
        result = {}
        with self._connect() as connection:
            for provider, settings in self.config.get("providers", {}).items():
                models = set(settings.get("models", {}).values())
                models.update(row[0] for row in connection.execute(
                    "SELECT DISTINCT model FROM call_log WHERE provider=?", (provider,)))
                result[provider] = {}
                for model in sorted(models):
                    rows = connection.execute("""SELECT * FROM call_log WHERE provider=? AND model=?
                        AND physical_attempt=1 AND cached=0 AND created_at>?""", (provider, model, now - 60)).fetchall()
                    result[provider][model] = {
                        **self._model_limits(provider, model), "requests_this_minute": len(rows),
                        "input_tokens_this_minute": sum(row["reserved_input_tokens"] for row in rows),
                        "output_tokens_this_minute": sum(row["reserved_output_tokens"] for row in rows),
                    }
        return result

    def budget_status(self) -> dict[str, dict[str, Any]]:
        """Legacy provider summary; enforcement uses separate provider+model windows."""
        now, result = self.clock(), {}
        with self._connect() as connection:
            for provider, settings in self.config.get("providers", {}).items():
                rows = connection.execute("""SELECT * FROM call_log WHERE provider=?
                    AND physical_attempt=1 AND cached=0 AND created_at>=?""",
                    (provider, min(now - 60, now - now % 86400))).fetchall()
                minute = [row for row in rows if row["created_at"] > now - 60]
                result[provider] = {
                    "requests_today": sum(row["created_at"] >= now - now % 86400 for row in rows),
                    "daily_limit": int(settings.get("rpd_limit", 0)),
                    "requests_this_minute": len(minute), "rpm_limit": int(settings.get("rpm_limit", 0)),
                    "requests_this_second": sum(row["created_at"] > now - 1 for row in rows),
                    "rps_limit": int(settings.get("rps_limit", 0)),
                    "tokens_this_minute": sum(row["reserved_input_tokens"] + row["reserved_output_tokens"] for row in minute),
                    "tpm_limit": int(settings.get("tpm_limit", 0)),
                    "min_interval_seconds": float(settings.get("min_interval_seconds", 0)),
                }
        return result

    def _reserve(self, provider: str, model: str, messages: Sequence[dict[str, str]],
                 params: dict[str, Any], *, role: str, stage: str, cache_key: str, kind: str) -> int:
        input_tokens = int(self.token_counter(provider, model, messages))
        output_tokens = max(int(params["max_tokens"]), int(params.get("max_completion_tokens", 0))) * int(params.get("n", 1))
        if input_tokens < 0 or output_tokens < 1:
            raise ValueError("token reservations must be nonnegative input and positive output")
        limits = self._model_limits(provider, model)
        sizes = {"input_tpm_limit": input_tokens, "output_tpm_limit": output_tokens,
                 "tpm_limit": input_tokens + output_tokens}
        for key, size in sizes.items():
            if limits.get(key) and size > limits[key]:
                raise BudgetExceeded(f"{provider}/{model} request exceeds {key} ({size}>{limits[key]})")
        while True:
            if role == "critic" and self._critic_requests_remaining is not None and self._critic_requests_remaining <= 0:
                raise CriticBudgetExceeded("Per-question critic request budget exhausted (maximum three actual requests)")
            wait = 0.0
            with self._connect() as connection:
                # Serialize check+reservation across router instances/processes.
                connection.execute("BEGIN IMMEDIATE")
                now = self.clock()
                quota = connection.execute("SELECT blocked_until FROM provider_quota WHERE provider=?", (provider,)).fetchone()
                if quota and quota[0] > now:
                    raise ProviderQuotaExceeded(f"{provider} provider quota budget exhausted")
                day_start = now - now % 86400
                daily = connection.execute("""SELECT COUNT(*) FROM call_log WHERE provider=?
                    AND physical_attempt=1 AND cached=0 AND created_at>=?""", (provider, day_start)).fetchone()[0]
                day_limit = self.config["providers"][provider].get("rpd_limit", 0)
                if day_limit and daily >= day_limit:
                    raise ProviderQuotaExceeded(f"{provider} daily request limit reached")
                rows = connection.execute("""SELECT * FROM call_log WHERE provider=? AND model=?
                    AND physical_attempt=1 AND cached=0 AND created_at>? ORDER BY created_at""",
                    (provider, model, now - 60)).fetchall()
                # Old logical logs cannot reveal missing retries or max_tokens.
                # Wait out any active legacy window rather than invent headroom.
                for row in rows:
                    if not row["accounting_version"]:
                        wait = max(wait, row["created_at"] + 60 - now)
                # Smooth starts as well as enforcing the exact sliding windows.
                interval = float(limits.get("min_interval_seconds") or 0)
                for key, size in {"rpm_limit": 1, **sizes}.items():
                    if limits.get(key):
                        interval = max(interval, 60 * size / limits[key])
                if limits.get("rps_limit"):
                    interval = max(interval, 1 / limits["rps_limit"])
                if rows:
                    wait = max(wait, rows[-1]["created_at"] + interval - now)
                windows = [("rpm_limit", 1, lambda row: 1, 60),
                           ("rps_limit", 1, lambda row: 1, 1),
                           ("input_tpm_limit", input_tokens, lambda row: row["reserved_input_tokens"], 60),
                           ("output_tpm_limit", output_tokens, lambda row: row["reserved_output_tokens"], 60),
                           ("tpm_limit", input_tokens + output_tokens,
                            lambda row: row["reserved_input_tokens"] + row["reserved_output_tokens"], 60)]
                for key, size, amount, window in windows:
                    limit = limits.get(key, 0)
                    active = [row for row in rows if row["created_at"] > now - window]
                    total = sum(amount(row) for row in active)
                    for row in active:
                        if not limit or total + size <= limit:
                            break
                        wait = max(wait, row["created_at"] + window - now)
                        total -= amount(row)
                if wait <= 0:
                    record_id = self._insert_record(connection, cache_key=cache_key, provider=provider,
                        model=model, role=role, stage=stage, kind=kind, physical=True,
                        input_tokens=input_tokens, output_tokens=output_tokens)
                    if role == "critic" and self._critic_requests_remaining is not None:
                        self._critic_requests_remaining -= 1
                    return record_id
            self.sleep(max(wait, 0.001))

    def _provider_model(self, provider: str, role: str) -> str:
        models = self.config.get("providers", {}).get(provider, {}).get("models", {})
        return models.get(role) or models.get("generation") or models.get("fallback") or next(iter(models.values()), "unknown")

    def _provider_chain(self, role: str) -> list[str]:
        override = os.getenv(f"TRUTHGUARD_{role.upper()}_PROVIDER")
        if override:
            return [override]
        override = os.getenv(f"TRUTHGUARD_{role.upper()}_CHAIN")
        if override:
            return [provider.strip() for provider in override.split(",") if provider.strip()]
        return list(self.config.get("role_chains", {}).get(role) or self.config.get("providers", {}))

    def _api_key(self, provider: str) -> str | None:
        name = self.config.get("providers", {}).get(provider, {}).get("api_key_env")
        return os.getenv(name) if name else None

    def _decode_http(self, provider: str, response: httpx.Response) -> dict[str, Any]:
        headers = sanitized_rate_headers(response.headers)
        if response.is_error:
            # Inspect but never persist raw provider bodies (they can echo prompts/secrets).
            detail = response.text[:4000]
            kwargs = {"rate_limit_headers": headers, "status_code": response.status_code}
            if response.status_code in {402, 403, 429} and re.search(
                r"tokens? per day|requests? per day|insufficient_quota|quota.{0,20}(?:exceed|exhaust)|"
                r"(?:exceed|exhaust).{0,20}quota|billing|daily.{0,20}limit", detail, re.I):
                raise ProviderQuotaExceeded(f"{provider} provider quota budget exhausted", **kwargs)
            delay = None
            if response.status_code == 429:
                match = re.search(r"try again in ([0-9.]+)s", detail, re.I)
                try:
                    delay = float(response.headers.get("retry-after") or (match.group(1) if match else 5))
                except ValueError:
                    delay = 5.0
                delay = max(0.0, min(delay, 86400))
            raise ProviderError(f"{provider} HTTP {response.status_code}", retry_after=delay, **kwargs)
        try:
            raw = response.json()
            if not isinstance(raw, dict):
                raise ValueError("response must be an object")
        except ValueError as exc:
            raise InvalidResponse("Provider returned non-JSON HTTP body", rate_limit_headers=headers,
                                  status_code=response.status_code) from exc
        return {**raw, "_rate_limit_headers": headers, "_status_code": response.status_code}

    def _invoke(self, provider: str, model: str, messages: Sequence[dict[str, str]],
                params: dict[str, Any]) -> dict[str, Any]:
        payload = {**params, "model": model, "messages": list(messages)}
        if self.transport is not None:
            response = self.transport(provider, model, {}, payload)
            return self._decode_http(provider, response) if isinstance(response, httpx.Response) else response
        settings = self.config["providers"][provider]
        key = self._api_key(provider)
        if not key:
            raise ProviderError(f"{provider} API key is not configured")
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        if self.client is not None:
            response = self.client.post(settings["base_url"] + "/chat/completions", headers=headers, json=payload)
        else:
            with httpx.Client(timeout=90.0) as client:
                response = client.post(settings["base_url"] + "/chat/completions", headers=headers, json=payload)
        return self._decode_http(provider, response)

    @contextmanager
    def critic_request_budget(self, limit: int = 3):
        """One shared physical budget, including repairs/fallbacks; nesting cannot replenish it."""
        previous = self._critic_requests_remaining
        start = min(3, max(0, limit), previous if previous is not None else 3)
        self._critic_requests_remaining = start
        try:
            yield
        finally:
            consumed = start - self._critic_requests_remaining
            self._critic_requests_remaining = None if previous is None else previous - consumed

    @property
    def critic_requests_remaining(self) -> int | None:
        """Remaining physical requests inside the active whole-question context."""
        return self._critic_requests_remaining

    @staticmethod
    def _content_from_response(response: dict[str, Any]) -> Any:
        if "choices" not in response:
            return response.get("payload", response)
        try:
            content = response["choices"][0]["message"]["content"]
            if isinstance(content, (dict, list)):
                return content
            text = str(content).strip()
            if text.startswith("```"):
                text = text.removeprefix("```").removeprefix("json").removesuffix("```").strip()
            return json.loads(text)
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise InvalidResponse("Provider returned non-JSON content") from exc

    @staticmethod
    def _usage_from_response(response: dict[str, Any]) -> LLMUsage:
        usage = response.get("usage") or {}
        return LLMUsage(prompt_tokens=usage.get("prompt_tokens") or 0,
                        completion_tokens=usage.get("completion_tokens") or 0,
                        total_tokens=usage.get("total_tokens") or 0)

    def _request_json(self, provider: str, model: str, messages: Sequence[dict[str, str]],
                      params: dict[str, Any], response_model: type[ModelT], *, role: str, stage: str,
                      cache_key: str, kind: str, validation_context: dict[str, Any] | None,
                      attempt_ids: list[int]) -> ModelT:
        for retry in range(1 if role == "critic" else 3):
            record_id = self._reserve(provider, model, messages, params, role=role, stage=stage,
                                      cache_key=cache_key, kind="rate_retry" if retry else kind)
            attempt_ids.append(record_id)
            raw: dict[str, Any] = {}
            headers: dict[str, str] = {}
            usage, status_code, served_model = LLMUsage(), None, None
            try:
                raw = self._invoke(provider, model, messages, params)
                headers = sanitized_rate_headers(raw.get("_rate_limit_headers"))
                status_code = raw.get("_status_code")
                reported = raw.get("model")
                if isinstance(reported, str) and re.fullmatch(r"[a-zA-Z0-9_./:@+-]{1,160}", reported):
                    served_model = reported
                usage = self._usage_from_response(raw)
                payload = self._content_from_response(raw)
                try:
                    parsed = response_model.model_validate(payload, context=validation_context)
                except ValidationError as exc:
                    # Do not persist validation_error strings: they include raw input.
                    raise InvalidResponse("Provider JSON failed schema/reference validation") from exc
            except Exception as exc:
                if isinstance(exc, ProviderError):
                    headers = exc.rate_limit_headers or headers
                    status_code = exc.status_code or status_code
                outcome = ("quota_error" if isinstance(exc, ProviderQuotaExceeded) else
                           "rate_error" if isinstance(exc, ProviderError) and (exc.retry_after is not None or status_code == 429) else
                           "invalid_schema" if isinstance(exc, InvalidResponse) and isinstance(exc.__cause__, ValidationError) else
                           "invalid_json" if isinstance(exc, InvalidResponse) else "transport_error")
                self._finish_record(record_id, outcome=outcome, usage=usage, error=exc,
                                    headers=headers, status_code=status_code, served_model=served_model)
                if isinstance(exc, ProviderQuotaExceeded):
                    now = self.clock()
                    with self._connect() as connection:
                        connection.execute("INSERT OR REPLACE INTO provider_quota VALUES (?, ?)",
                                           (provider, now - now % 86400 + 86400))
                    raise
                if role != "critic" and isinstance(exc, ProviderError) and exc.retry_after is not None and retry < 2:
                    self.sleep(min(max(exc.retry_after, 0.5) * 2**retry, 60))
                    continue
                raise
            self._finish_record(record_id, outcome="valid", usage=usage, headers=headers, status_code=status_code,
                                served_model=served_model)
            return parsed
        raise AssertionError("unreachable")

    def complete_json(self, role: str, messages: Sequence[dict[str, str]], response_model: type[ModelT], *,
                      stage: str | None = None, params: dict[str, Any] | None = None,
                      offline_payload: dict[str, Any] | None = None,
                      validation_context: dict[str, Any] | None = None) -> tuple[ModelT, LLMResult]:
        params = dict(params or {})
        params.pop("model", None)
        params.pop("messages", None)
        params.setdefault("temperature", 0)
        params.setdefault("response_format", {"type": "json_object"})
        params["max_tokens"] = min(int(params.get("max_tokens", 350)), 350) if role == "critic" else int(params.get("max_tokens", 1024))
        if role == "critic":
            # Prevent alternate completion knobs from bypassing the per-attempt cap.
            params.pop("max_completion_tokens", None)
            params["n"] = 1
            params["stream"] = False
        if params["max_tokens"] < 1:
            raise ValueError("max_tokens must be positive")
        stage, errors, attempt_ids = stage or role, [], []
        offline = bool(self.config.get("project", {}).get("offline", True))
        started = time.perf_counter()
        chain = self._provider_chain(role)
        # Look through the whole chain before spending a physical request. In
        # particular, a fallback cache is usable after the shared budget runs out.
        for provider in chain:
            model = self._provider_model(provider, role)
            cache_key = self.make_cache_key(provider, model, messages, params)
            cached = self._cached_payload(cache_key)
            if cached is not None:
                try:
                    parsed = response_model.model_validate(cached, context=validation_context)
                except ValidationError:
                    pass
                else:
                    served_model = self._cached_model(cache_key)
                    with self._connect() as connection:
                        self._insert_record(connection, cache_key=cache_key, provider=provider, model=model,
                                            role=role, stage=stage, kind="cache", physical=False, served_model=served_model)
                    return parsed, LLMResult(payload=parsed.model_dump(mode="json"), provider=provider,
                        model=served_model or model, requested_model=model,
                        cache_key=cache_key, cached=True, attempt_ids=attempt_ids)
        for provider in chain:
            model = self._provider_model(provider, role)
            cache_key = self.make_cache_key(provider, model, messages, params)
            if offline and offline_payload is None:
                errors.append(f"{provider} skipped: offline mode has no fixture payload")
                continue
            if not offline and self.transport is None and self.client is None and not self._api_key(provider):
                errors.append(f"{provider} skipped: API key is not configured")
                continue
            repaired = False
            try:
                if offline:
                    parsed = response_model.model_validate(offline_payload, context=validation_context)
                    with self._connect() as connection:
                        self._insert_record(connection, cache_key=cache_key, provider=provider, model=model,
                                            role=role, stage=stage, kind="offline", physical=False)
                else:
                    kwargs = dict(role=role, stage=stage, cache_key=cache_key,
                                  validation_context=validation_context, attempt_ids=attempt_ids)
                    try:
                        parsed = self._request_json(provider, model, messages, params, response_model, kind="first_json", **kwargs)
                    except InvalidResponse:
                        repaired = True
                        repair_messages = list(messages) + [{"role": "user", "content":
                            "The previous attempt was invalid JSON or violated the schema/reference constraints. "
                            "Return a fresh complete JSON object following the original schema exactly; only supplied local IDs."}]
                        parsed = self._request_json(provider, model, repair_messages, params, response_model, kind="repair", **kwargs)
                payload = parsed.model_dump(mode="json")
                with self._connect() as connection:
                    row = connection.execute("SELECT usage_json, served_model FROM call_log WHERE id=?",
                                             (attempt_ids[-1] if attempt_ids else -1,)).fetchone()
                usage = LLMUsage.model_validate_json(row[0]) if row else LLMUsage()
                served_model = row[1] if row else None
                self._store_payload(cache_key, provider, model, payload, served_model)
                return parsed, LLMResult(payload=payload, provider=provider, model=served_model or model,
                    requested_model=model, cache_key=cache_key,
                    repaired=repaired, usage=usage, latency_ms=(time.perf_counter() - started) * 1000,
                    attempt_ids=attempt_ids)
            except (CriticBudgetExceeded, ProviderQuotaExceeded):
                raise
            except Exception as exc:  # fallback; each physical attempt is already recorded
                errors.append(f"{provider}/{model}: {self._safe_error(exc)}")
        raise AllProvidersUnavailable(f"No provider could complete role={role}. Attempts: " + "; ".join(errors))
