"""No credentials or network: fake time plus scripted physical transports."""

from __future__ import annotations

import json
import sqlite3

import httpx
import pytest

from truthguard.llm import (
    AllProvidersUnavailable, CriticBudgetExceeded, LLMRouter, ProviderError, ProviderQuotaExceeded,
)
from test_llm import FakeClock, TinyPayload


def config(model="model-a", **limits):
    return {"project": {"offline": False}, "providers": {"groq": {
        "models": {"critic": model, "synthesizer": "model-b"}, **limits}},
        "role_chains": {"critic": ["groq"], "synthesizer": ["groq"]}}


def router(tmp_path, settings=None, transport=None, tokens=10, clock=None):
    clock = clock or FakeClock()
    instance = LLMRouter(settings or config(), database_path=tmp_path / "limits.sqlite3",
                         transport=transport or (lambda *_: {"answer": "ok"}),
                         clock=clock, sleep=clock.sleep, token_counter=lambda *_: tokens)
    return instance, clock


def complete(instance, text, role="critic", **kwargs):
    return instance.complete_json(role, [{"role": "user", "content": text}], TinyPayload, **kwargs)


def test_qwen_1000_otpm_cap_and_350_per_actual_call_cross_minute_boundary(tmp_path):
    starts, requested = [], []
    clock = FakeClock(59)

    def transport(provider, model, headers, payload):
        starts.append(clock())
        requested.append(payload["max_tokens"])
        return {"answer": "ok"}

    instance, _ = router(tmp_path, config("qwen/qwen3.8-27b", output_tpm_limit=99999), transport, clock=clock)
    with instance.critic_request_budget(3):
        for text in ("one", "two", "three"):
            complete(instance, text, params={"max_tokens": 4000})
    assert requested == [350, 350, 350]
    assert starts == [59, 80, 119]  # third waits for first reservation, not the wall minute
    assert [row.reserved_output_tokens for row in instance.call_records()] == [350] * 3
    assert instance.model_budget_status()["groq"]["qwen/qwen3.8-27b"]["output_tpm_limit"] == 1000


def test_critic_model_and_completion_params_cannot_bypass_accounting(tmp_path):
    calls = []
    instance, _ = router(tmp_path, transport=lambda *args: calls.append(args[-1]) or {"answer": "ok"})
    complete(instance, "bounded", params={"model": "unaccounted-model", "messages": [],
                                        "max_completion_tokens": 9000, "n": 10, "stream": True})
    assert calls[0]["model"] == "model-a"
    assert calls[0]["messages"] == [{"role": "user", "content": "bounded"}]
    assert calls[0]["max_tokens"] == 350
    assert calls[0]["n"] == 1 and calls[0]["stream"] is False
    assert "max_completion_tokens" not in calls[0]


def test_response_reported_model_is_preserved_in_records_results_and_cache(tmp_path):
    instance, _ = router(tmp_path, transport=lambda *_: {
        "model": "actual/served-model", "choices": [{"message": {"content": '{"answer":"ok"}'}}]})
    _, first = complete(instance, "routed")
    _, cached = complete(instance, "routed")
    assert first.model == cached.model == "actual/served-model"
    assert first.requested_model == cached.requested_model == "model-a"
    assert [row.model for row in instance.call_records()] == ["actual/served-model"] * 2
    assert all(row.requested_model == "model-a" for row in instance.call_records())
    # Enforcement follows the configured request bucket, even when a provider
    # reports a versioned model or resolves an automatic routing alias.
    assert instance.model_budget_status()["groq"]["model-a"]["requests_this_minute"] == 1


@pytest.mark.parametrize("limit,tokens,expected", [
    ({"input_tpm_limit": 100}, 60, [59, 119]),
    ({"output_tpm_limit": 600}, 10, [59, 119]),
    ({"rpm_limit": 1}, 10, [59, 119]),
    ({"tpm_limit": 700}, 10, [59, 119]),
    ({"rps_limit": 1}, 10, [59, 60]),
])
def test_independent_sliding_windows_and_smooth_starts(tmp_path, limit, tokens, expected):
    instance, clock = router(tmp_path, config(**limit), tokens=tokens)
    complete(instance, "first")
    first = instance.call_records()[0].created_at.timestamp()
    complete(instance, "second")
    assert [first, clock()] == expected


def test_separate_models_and_persisted_reservations_visible_before_transport(tmp_path):
    clock, observed = FakeClock(), []
    settings = config("qwen/qwen3.8-27b", rpm_limit=1, input_tpm_limit=100,
                      model_limits={"model-b": {"rpm_limit": 10, "output_tpm_limit": 2000}})

    def transport(provider, model, headers, payload):
        peer, _ = router(tmp_path, settings, clock=clock)
        observed.append(peer.model_budget_status()[provider][model]["requests_this_minute"])
        assert peer.call_records()[-1].outcome == "pending"
        return {"answer": "ok"}

    instance, _ = router(tmp_path, settings, transport, clock=clock)
    complete(instance, "critic")
    complete(instance, "synth", role="synthesizer", params={"max_tokens": 1000})
    assert clock() == 59  # neither critic's RPM nor OTPM throttles the other model
    assert observed == [1, 1]
    peer, _ = router(tmp_path, settings, clock=clock)
    complete(peer, "next critic")
    assert clock() == 119


def test_failed_attempts_reserve_tokens_cache_hits_and_fixtures_do_not(tmp_path):
    clock, calls = FakeClock(), []

    def transport(*args):
        calls.append(clock())
        if len(calls) == 1:
            raise ProviderError("temporary error")
        return {"answer": "ok", "usage": {"prompt_tokens": 2, "completion_tokens": 1}}

    instance, _ = router(tmp_path, config(output_tpm_limit=600), transport, clock=clock)
    with pytest.raises(AllProvidersUnavailable):
        complete(instance, "fails")
    complete(instance, "works")
    complete(instance, "works")
    assert calls == [59, 119]
    rows = instance.call_records()
    assert [row.physical_attempt for row in rows] == [True, True, False]
    assert [row.outcome for row in rows] == ["transport_error", "valid", "cache"]
    assert [row.reserved_output_tokens for row in rows] == [350, 350, 0]
    assert instance.budget_status()["groq"]["requests_today"] == 2
    fixture_config = config()
    fixture_config["project"]["offline"] = True
    fixture, _ = router(tmp_path, fixture_config, clock=clock)
    complete(fixture, "fixture", offline_payload={"answer": "fixture"})
    assert fixture.call_records()[-1].attempt_kind == "offline"
    assert not fixture.call_records()[-1].physical_attempt


def test_oversized_reservation_does_not_spend_physical_budget(tmp_path):
    instance, clock = router(tmp_path, config(input_tpm_limit=9), tokens=10,
                             transport=lambda *_: pytest.fail("must reject before transport"))
    with instance.critic_request_budget():
        with pytest.raises(AllProvidersUnavailable, match="request exceeds input_tpm_limit"):
            complete(instance, "too big")
        assert instance._critic_requests_remaining == 3
    assert instance.call_records() == []
    assert clock.waits == []


def test_budget_includes_repair_and_fallback_and_nested_context_cannot_replenish(tmp_path):
    settings = config()
    settings["providers"]["backup"] = {"models": {"critic": "actual-backup-model"}}
    settings["role_chains"]["critic"] += ["backup"]
    calls = []

    def transport(provider, model, headers, payload):
        calls.append((provider, model, payload["max_tokens"]))
        return {"answer": "backup"} if provider == "backup" else {"bad": "schema"}

    instance, _ = router(tmp_path, settings, transport)
    with instance.critic_request_budget(99):
        with instance.critic_request_budget(3):
            parsed, result = complete(instance, "first")
        assert parsed.answer == "backup"
        assert result.provider == "backup"
        assert result.model == "actual-backup-model"
        assert len(result.attempt_ids) == 3
        # Cache can still serve after exhaustion and consumes nothing.
        assert complete(instance, "first")[1].cached
        with pytest.raises(CriticBudgetExceeded):
            complete(instance, "another stage")
    assert len(calls) == 3
    assert all(item[2] == 350 for item in calls)
    physical = [row for row in instance.call_records() if row.physical_attempt]
    assert [row.attempt_kind for row in physical] == ["first_json", "repair", "first_json"]
    assert [row.outcome for row in physical] == ["invalid_schema", "invalid_schema", "valid"]


def test_http_rate_headers_survive_restart_export_and_errors_do_not_leak_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("UNIT_PROVIDER_KEY", "highly-secret-key")
    settings = config()
    settings["providers"]["groq"]["api_key_env"] = "UNIT_PROVIDER_KEY"
    responses = [httpx.Response(429, headers={
        "X-RateLimit-Limit-Requests": "30", "x-ratelimit-remaining-tokens": "0",
        "x-ratelimit-reset-tokens": "1m2.5s", "Authorization": "Bearer highly-secret-key",
        "x-ratelimit-secret": "highly-secret-key", "retry-after": "3",
    }, text="try again in 3s; highly-secret-key"), {"answer": "ok"}]
    instance, clock = router(tmp_path, settings, lambda *_: responses.pop(0))
    with pytest.raises(AllProvidersUnavailable, match="HTTP 429"):
        complete(instance, "rate")
    assert len(responses) == 1  # no automatic critic retry
    row = instance.call_records()[0]
    assert row.outcome == "rate_error" and row.status_code == 429
    assert row.rate_limit_headers == {"x-ratelimit-limit-requests": "30", "x-ratelimit-remaining-tokens": "0",
                                      "x-ratelimit-reset-tokens": "1m2.5s"}
    peer, _ = router(tmp_path, settings, clock=clock)
    report = peer.export_call_report()
    assert "first_json / rate_error" in report and "1m2.5s" in report
    assert "highly-secret-key" not in report
    assert "highly-secret-key" not in json.dumps([record.model_dump(mode="json") for record in peer.call_records()])


def test_successful_http_headers_and_usage_are_recorded_without_auth(tmp_path, monkeypatch):
    monkeypatch.setenv("UNIT_PROVIDER_KEY", "unit-key")
    settings = config()
    settings["providers"]["groq"].update(api_key_env="UNIT_PROVIDER_KEY", base_url="https://offline.invalid/v1")
    seen = []

    def respond(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200, headers={"X-RateLimit-Remaining-Requests": "29", "set-cookie": "secret"},
                              json={"choices": [{"message": {"content": '{"answer":"ok"}'}}],
                                    "usage": {"prompt_tokens": 11, "completion_tokens": 3, "total_tokens": 14}})

    clock = FakeClock()
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        instance = LLMRouter(settings, database_path=tmp_path / "http.sqlite3", client=client,
                             clock=clock, sleep=clock.sleep, token_counter=lambda *_: 10)
        _, result = complete(instance, "only mocked HTTP")
    assert seen[0]["max_tokens"] == 350
    assert result.usage.total_tokens == 14
    row = instance.call_records()[0]
    assert row.reserved_input_tokens == 11  # usage can increase, never release a reservation
    assert row.reserved_output_tokens == 350
    assert row.rate_limit_headers == {"x-ratelimit-remaining-requests": "29"}


def test_provider_quota_stops_flow_and_persists_without_fallback_or_repeated_failure(tmp_path):
    settings = config()
    settings["providers"]["backup"] = {"models": {"critic": "other"}}
    settings["role_chains"]["critic"].append("backup")
    calls = []

    def transport(*args):
        calls.append(args)
        return httpx.Response(429, headers={"x-ratelimit-remaining-requests": "0"},
                              json={"error": {"code": "insufficient_quota"}})

    instance, clock = router(tmp_path, settings, transport)
    with instance.critic_request_budget():
        with pytest.raises(ProviderQuotaExceeded):
            complete(instance, "quota")
        with pytest.raises(ProviderQuotaExceeded):
            complete(instance, "next stage")
    peer, _ = router(tmp_path, settings, transport, clock=clock)
    with pytest.raises(ProviderQuotaExceeded):
        complete(peer, "after restart")
    assert len(calls) == 1
    assert len(peer.call_records()) == 1
    assert peer.call_records()[0].outcome == "quota_error"


def test_local_daily_exhaustion_is_distinct_and_does_not_send_again(tmp_path):
    instance, _ = router(tmp_path, config(rpd_limit=1))
    complete(instance, "one")
    with pytest.raises(ProviderQuotaExceeded, match="daily"):
        complete(instance, "two")
    assert len(instance.call_records()) == 1


def test_legacy_database_migration_does_not_fabricate_physical_attempt_evidence(tmp_path):
    path = tmp_path / "limits.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.executescript("""CREATE TABLE call_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, cache_key TEXT NOT NULL,
            provider TEXT NOT NULL, role TEXT NOT NULL, stage TEXT NOT NULL, model TEXT NOT NULL,
            created_at REAL NOT NULL, cached INTEGER NOT NULL DEFAULT 0,
            success INTEGER NOT NULL DEFAULT 1, error TEXT, usage_json TEXT NOT NULL);
            INSERT INTO call_log(cache_key, provider, role, stage, model, created_at, usage_json)
            VALUES ('old', 'groq', 'critic', 'old-stage', 'model-a', 59, '{}');""")
    instance, clock = router(tmp_path)
    old = instance.call_records()[0]
    assert old.accounting_version == 0
    assert old.attempt_kind == "legacy" and old.outcome == "legacy_unknown"
    assert "Physical attempts (v1): 0" in instance.export_call_report()
    complete(instance, "after migration")
    assert clock() == 119  # unknown legacy reservations must first leave the window
    assert instance.call_records()[1].accounting_version == 1


def test_byte_estimator_is_offline_unicode_conservative():
    messages = [{"role": "user", "content": "α😀中文"}]
    assert LLMRouter.estimate_input_tokens("groq", "any", messages) > len(messages[0]["content"].encode("utf-8"))
