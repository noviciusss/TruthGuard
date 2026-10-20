"""Provider routing, caching, and persisted free-tier budget accounting.

The router deliberately uses the OpenAI-compatible HTTP shape rather than
provider SDKs. This keeps the runtime small and makes provider behavior easy to
mock in the offline test suite.
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
Transport = Callable[[str, str, dict[str, str], dict[str, Any]], dict[str, Any]]


class ProviderError(RuntimeError):
    """A provider could not complete one request."""

    def __init__(self, message: str, *, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class BudgetExceeded(ProviderError):
    """A configured RPM or RPD limit has been reached."""


class AllProvidersUnavailable(ProviderError):
    """No provider in the role's fallback chain can serve the request."""


class LLMRouter:
    """Route structured calls with caching, fallback, and persisted counters."""

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        *,
        database_path: str | Path | None = None,
        transport: Transport | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.config = config or load_config()
        configured_path = database_path or self.config["project"].get(
            "database_path", "data/cache/truthguard.sqlite3"
        )
        self.database_path = self._resolve_path(configured_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.transport = transport
        self.client = client
        self._last_request_monotonic: dict[str, float] = {}
        self._critic_requests_remaining: int | None = None
        self._initialize_database()

    def _resolve_path(self, path: str | Path) -> Path:
        path = Path(path)
        return path if path.is_absolute() else ROOT / path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_database(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS response_cache (
                    cache_key TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS call_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    role TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    model TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    cached INTEGER NOT NULL DEFAULT 0,
                    success INTEGER NOT NULL DEFAULT 1,
                    error TEXT,
                    usage_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_call_log_provider_time
                    ON call_log(provider, created_at);
                """
            )

    @staticmethod
    def make_cache_key(
        provider: str,
        model: str,
        messages: Sequence[dict[str, str]],
        params: dict[str, Any] | None = None,
    ) -> str:
        """Create a stable cache key for an unchanged provider request."""

        canonical = json.dumps(
            {
                "provider": provider,
                "model": model,
                "messages": list(messages),
                "params": params or {},
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _cached_payload(self, cache_key: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM response_cache WHERE cache_key = ?", (cache_key,)
            ).fetchone()
        return json.loads(row["payload"]) if row else None

    def _store_payload(self, cache_key: str, provider: str, model: str, payload: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO response_cache(cache_key, provider, model, payload, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET payload=excluded.payload,
                    created_at=excluded.created_at
                """,
                (cache_key, provider, model, json.dumps(payload, sort_keys=True), time.time()),
            )

    def _record_call(
        self,
        *,
        cache_key: str,
        provider: str,
        role: str,
        stage: str,
        model: str,
        cached: bool,
        success: bool,
        error: str | None = None,
        usage: LLMUsage | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO call_log(
                    cache_key, provider, role, stage, model, created_at,
                    cached, success, error, usage_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cache_key,
                    provider,
                    role,
                    stage,
                    model,
                    time.time(),
                    int(cached),
                    int(success),
                    error,
                    json.dumps((usage or LLMUsage()).model_dump(mode="json")),
                ),
            )

    def call_records(self, provider: str | None = None) -> list[CallRecord]:
        """Return persisted call records for dashboards and debugging."""

        query = "SELECT * FROM call_log"
        args: tuple[Any, ...] = ()
        if provider:
            query += " WHERE provider = ?"
            args = (provider,)
        query += " ORDER BY id"
        with self._connect() as connection:
            rows = connection.execute(query, args).fetchall()
        records: list[CallRecord] = []
        for row in rows:
            records.append(
                CallRecord(
                    cache_key=row["cache_key"],
                    provider=row["provider"],
                    role=row["role"],
                    stage=row["stage"],
                    model=row["model"],
                    created_at=datetime.fromtimestamp(row["created_at"], tz=timezone.utc),
                    cached=bool(row["cached"]),
                    success=bool(row["success"]),
                    error=row["error"],
                    usage=LLMUsage.model_validate(json.loads(row["usage_json"])),
                )
            )
        return records

    def budget_status(self) -> dict[str, dict[str, int]]:
        """Return configured and observed provider request/token windows."""

        now = time.time()
        day_start = now - (now % 86400)
        minute_start = now - (now % 60)
        second_start = now - 1.0
        result: dict[str, dict[str, int]] = {}
        with self._connect() as connection:
            for provider, settings in self.config.get("providers", {}).items():
                rows = connection.execute(
                    """
                    SELECT created_at, usage_json
                    FROM call_log
                    WHERE provider = ? AND created_at >= ? AND cached = 0
                    """,
                    (provider, day_start),
                ).fetchall()
                minute_rows = [row for row in rows if row["created_at"] >= minute_start]
                second_rows = [row for row in minute_rows if row["created_at"] >= second_start]
                tokens_this_minute = sum(
                    int(json.loads(row["usage_json"]).get("total_tokens", 0))
                    for row in minute_rows
                )
                result[provider] = {
                    "requests_today": len(rows),
                    "daily_limit": int(settings.get("rpd_limit", 0)),
                    "requests_this_minute": len(minute_rows),
                    "rpm_limit": int(settings.get("rpm_limit", 0)),
                    "requests_this_second": len(second_rows),
                    "rps_limit": int(settings.get("rps_limit", 0)),
                    "tokens_this_minute": tokens_this_minute,
                    "tpm_limit": int(settings.get("tpm_limit", 0)),
                    "min_interval_seconds": float(settings.get("min_interval_seconds", 0.0)),
                }
        return result

    def _check_budget(self, provider: str) -> None:
        settings = self.config.get("providers", {}).get(provider, {})
        status = self.budget_status().get(provider, {})
        if status.get("rpm_limit", 0) and status["requests_this_minute"] >= status["rpm_limit"]:
            raise BudgetExceeded(f"{provider} RPM limit reached")
        if status.get("rps_limit", 0) and status["requests_this_second"] >= status["rps_limit"]:
            raise BudgetExceeded(f"{provider} RPS limit reached")
        if status.get("tpm_limit", 0) and status["tokens_this_minute"] >= status["tpm_limit"]:
            raise BudgetExceeded(f"{provider} TPM limit reached")
        if status.get("daily_limit", 0) and status["requests_today"] >= status["daily_limit"]:
            raise BudgetExceeded(f"{provider} daily request limit reached")

    def _wait_for_budget(self, provider: str) -> None:
        """Wait for a configured RPM window; fail immediately on daily exhaustion."""

        while True:
            status = self.budget_status().get(provider, {})
            if status.get("daily_limit", 0) and status["requests_today"] >= status["daily_limit"]:
                raise BudgetExceeded(f"{provider} daily request limit reached")
            if status.get("tpm_limit", 0) and status["tokens_this_minute"] >= status["tpm_limit"]:
                raise BudgetExceeded(f"{provider} TPM limit reached")
            if status.get("rps_limit", 0) and status["requests_this_second"] >= status["rps_limit"]:
                time.sleep(max(0.05, 1.0 - (time.time() % 1.0) + 0.05))
                continue
            min_interval = float(status.get("min_interval_seconds", 0.0))
            if min_interval:
                elapsed = time.monotonic() - self._last_request_monotonic.get(provider, 0.0)
                if elapsed < min_interval:
                    time.sleep(min_interval - elapsed)
                    continue
            if not status.get("rpm_limit", 0) or status["requests_this_minute"] < status["rpm_limit"]:
                return
            wait_seconds = max(1.0, 60.0 - (time.time() % 60.0) + 0.1)
            time.sleep(wait_seconds)

    def _provider_model(self, provider: str, role: str) -> str:
        settings = self.config.get("providers", {}).get(provider, {})
        models = settings.get("models", {})
        return models.get(role) or models.get("generation") or models.get("fallback") or next(
            iter(models.values()), "unknown"
        )

    def _provider_chain(self, role: str) -> list[str]:
        override = os.getenv(f"TRUTHGUARD_{role.upper()}_PROVIDER")
        if override:
            return [override]
        chain_override = os.getenv(f"TRUTHGUARD_{role.upper()}_CHAIN")
        if chain_override:
            return [provider.strip() for provider in chain_override.split(",") if provider.strip()]
        configured = self.config.get("role_chains", {}).get(role)
        if configured:
            return list(configured)
        return list(self.config.get("providers", {}))

    def _api_key(self, provider: str) -> str | None:
        env_name = self.config.get("providers", {}).get(provider, {}).get("api_key_env")
        return os.getenv(env_name) if env_name else None

    def _invoke(
        self,
        provider: str,
        model: str,
        messages: Sequence[dict[str, str]],
        params: dict[str, Any],
    ) -> dict[str, Any]:
        if self.transport is not None:
            return self.transport(provider, model, {}, {"model": model, "messages": list(messages), **params})

        settings = self.config["providers"][provider]
        key = self._api_key(provider)
        if not key:
            raise ProviderError(f"{provider} is not configured; set {settings.get('api_key_env')}")
        payload = {"model": model, "messages": list(messages), **params}
        payload.setdefault("temperature", 0)
        payload.setdefault("response_format", {"type": "json_object"})
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        if self.client is not None:
            response = self.client.post(settings["base_url"] + "/chat/completions", headers=headers, json=payload)
        else:
            with httpx.Client(timeout=90.0) as client:
                response = client.post(settings["base_url"] + "/chat/completions", headers=headers, json=payload)
        if response.is_error:
            detail = response.text[:1000].replace("\n", " ")
            retry_after: float | None = None
            if response.status_code == 429:
                if re.search(r"tokens? per day|requests? per day", detail, flags=re.IGNORECASE):
                    raise BudgetExceeded(f"{provider} daily provider budget exhausted: {detail}")
                header_value = response.headers.get("retry-after")
                match = re.search(r"try again in ([0-9.]+)s", detail, flags=re.IGNORECASE)
                try:
                    retry_after = float(header_value) if header_value else (float(match.group(1)) if match else 5.0)
                except ValueError:
                    retry_after = 5.0
            raise ProviderError(
                f"{provider} HTTP {response.status_code}: {detail}",
                retry_after=retry_after,
            )
        return response.json()

    def _invoke_with_retry(
        self,
        provider: str,
        model: str,
        messages: Sequence[dict[str, str]],
        params: dict[str, Any],
        *,
        attempts: int = 3,
        role: str | None = None,
    ) -> dict[str, Any]:
        """Retry provider 429s with bounded exponential/backoff waiting."""

        for attempt in range(attempts):
            try:
                if role == "critic" and self._critic_requests_remaining is not None:
                    if self._critic_requests_remaining <= 0:
                        raise BudgetExceeded("Per-question critic request budget exhausted (maximum three actual requests)")
                self._wait_for_budget(provider)
                if role == "critic" and self._critic_requests_remaining is not None:
                    self._critic_requests_remaining -= 1
                self._last_request_monotonic[provider] = time.monotonic()
                return self._invoke(provider, model, messages, params)
            except ProviderError as exc:
                if exc.retry_after is None or attempt == attempts - 1:
                    raise
                delay = min(max(exc.retry_after, 0.5) * (2**attempt), 60.0)
                time.sleep(delay)
        raise AssertionError("unreachable")

    @contextmanager
    def critic_request_budget(self, limit: int = 3):
        """Bound actual critic transport attempts, including repairs and retries."""
        previous = self._critic_requests_remaining
        self._critic_requests_remaining = limit if previous is None else min(limit, previous)
        try:
            yield
        finally:
            self._critic_requests_remaining = previous

    @staticmethod
    def _content_from_response(response: dict[str, Any]) -> Any:
        if "choices" not in response:
            return response.get("payload", response)
        content = response["choices"][0]["message"]["content"]
        if isinstance(content, (dict, list)):
            return content
        text = str(content).strip()
        if text.startswith("```"):
            text = text.removeprefix("```").removeprefix("json").removesuffix("```").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProviderError(f"Provider returned non-JSON content: {text[:200]}") from exc

    @staticmethod
    def _usage_from_response(response: dict[str, Any]) -> LLMUsage:
        usage = response.get("usage", {})
        return LLMUsage(
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )

    def complete_json(
        self,
        role: str,
        messages: Sequence[dict[str, str]],
        response_model: type[ModelT],
        *,
        stage: str | None = None,
        params: dict[str, Any] | None = None,
        offline_payload: dict[str, Any] | None = None,
    ) -> tuple[ModelT, LLMResult]:
        """Complete one structured request, trying the configured fallback chain."""

        params = dict(params or {})
        stage = stage or role
        errors: list[str] = []
        offline = bool(self.config.get("project", {}).get("offline", True))

        for provider in self._provider_chain(role):
            model = self._provider_model(provider, role)
            cache_key = self.make_cache_key(provider, model, messages, params)
            cached = self._cached_payload(cache_key)
            if cached is not None:
                try:
                    parsed = response_model.model_validate(cached)
                except ValidationError as exc:
                    errors.append(f"{provider} cache validation failed: {exc}")
                else:
                    usage = LLMUsage()
                    self._record_call(
                        cache_key=cache_key,
                        provider=provider,
                        role=role,
                        stage=stage,
                        model=model,
                        cached=True,
                        success=True,
                        usage=usage,
                    )
                    return parsed, LLMResult(
                        payload=parsed.model_dump(mode="json"),
                        provider=provider,
                        model=model,
                        cache_key=cache_key,
                        cached=True,
                        usage=usage,
                    )

            if offline and offline_payload is None:
                errors.append(f"{provider} skipped: offline mode has no fixture payload")
                continue
            if not offline:
                try:
                    self._wait_for_budget(provider)
                except BudgetExceeded as exc:
                    errors.append(str(exc))
                    continue
                if self.transport is None and not self._api_key(provider):
                    errors.append(f"{provider} skipped: API key is not configured")
                    continue

            started = time.perf_counter()
            repaired = False
            try:
                raw = offline_payload if offline else self._invoke_with_retry(provider, model, messages, params, role=role)
                payload = self._content_from_response(raw)
                try:
                    parsed = response_model.model_validate(payload)
                except ValidationError as validation_error:
                    if offline:
                        raise
                    self._record_call(
                        cache_key=cache_key,
                        provider=provider,
                        role=role,
                        stage=stage,
                        model=model,
                        cached=False,
                        success=False,
                        error=f"schema validation before repair: {validation_error}",
                        usage=self._usage_from_response(raw),
                    )
                    repaired = True
                    repair_messages = list(messages) + [
                        {
                            "role": "user",
                            "content": "Repair the previous response. Return only valid JSON matching the requested schema.",
                        }
                    ]
                    self._wait_for_budget(provider)
                    raw = self._invoke_with_retry(provider, model, repair_messages, params, role=role)
                    payload = self._content_from_response(raw)
                    parsed = response_model.model_validate(payload)
                validated_payload = parsed.model_dump(mode="json")
                usage = self._usage_from_response(raw)
                latency_ms = (time.perf_counter() - started) * 1000
                self._store_payload(cache_key, provider, model, validated_payload)
                self._record_call(
                    cache_key=cache_key,
                    provider=provider,
                    role=role,
                    stage=stage,
                    model=model,
                    cached=False,
                    success=True,
                    usage=usage,
                )
                return parsed, LLMResult(
                    payload=validated_payload,
                    provider=provider,
                    model=model,
                    cache_key=cache_key,
                    cached=False,
                    repaired=repaired,
                    usage=usage,
                    latency_ms=latency_ms,
                )
            except Exception as exc:  # noqa: BLE001 - continue through fallback chain
                errors.append(f"{provider}: {exc}")
                self._record_call(
                    cache_key=cache_key,
                    provider=provider,
                    role=role,
                    stage=stage,
                    model=model,
                    cached=False,
                    success=False,
                    error=str(exc),
                )

        raise AllProvidersUnavailable(
            f"No provider could complete role={role}. Attempts: " + "; ".join(errors)
        )
