from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import BaseModel

from truthguard.config import load_config
from truthguard.llm import AllProvidersUnavailable, CriticBudgetExceeded, LLMRouter, ProviderError


class TinyPayload(BaseModel):
    answer: str


class FakeClock:
    def __init__(self, now=59.0):
        self.now = now
        self.waits = []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        assert seconds > 0
        self.waits.append(seconds)
        self.now += seconds


def router_with_clock(config, **kwargs):
    clock = FakeClock()
    return LLMRouter(config, clock=clock, sleep=clock.sleep, **kwargs)


def test_provider_limits_match_supplied_dashboards() -> None:
    config = load_config()

    gemini = config["providers"]["gemini"]
    assert gemini["models"]["critic"] == "gemini-3.8-flash"
    assert gemini["rpm_limit"] == 5
    assert gemini["tpm_limit"] == 250000
    assert gemini["rpd_limit"] == 20

    mistral = config["providers"]["mistral"]
    assert mistral["models"]["generation"] == "mistral-small-2603"
    assert mistral["rps_limit"] == 1
    assert mistral["tpm_limit"] == 20000
    assert mistral["rpd_limit"] == 0
    assert mistral["min_interval_seconds"] == 1.1

    groq = config["providers"]["groq"]
    assert groq["models"]["critic"] == "qwen/qwen3.8-27b"
    assert groq["tpm_limit"] == 8000


def test_offline_fixture_is_validated_cached_and_accounted(tmp_path) -> None:
    config = deepcopy(load_config())
    config["project"]["offline"] = True
    database = tmp_path / "router.sqlite3"
    router = router_with_clock(config, database_path=database)
    messages = [{"role": "user", "content": "answer"}]

    first, first_result = router.complete_json(
        "synthesizer",
        messages,
        TinyPayload,
        stage="unit-test",
        offline_payload={"answer": "cached answer"},
    )
    second, second_result = router.complete_json(
        "synthesizer",
        messages,
        TinyPayload,
        stage="unit-test",
        offline_payload={"answer": "different fixture ignored by cache"},
    )

    assert first.answer == "cached answer"
    assert second.answer == "cached answer"
    assert first_result.cached is False
    assert second_result.cached is True
    assert len(router.call_records()) == 2
    assert router.call_records()[1].cached is True


def test_router_falls_back_after_transport_failure(tmp_path) -> None:
    config = deepcopy(load_config())
    config["project"]["offline"] = False
    config["role_chains"]["synthesizer"] = ["groq", "mistral"]
    calls: list[str] = []

    def transport(provider, model, headers, payload):
        calls.append(provider)
        if provider == "groq":
            raise RuntimeError("simulated rate limit")
        return {"choices": [{"message": {"content": '{"answer":"fallback"}'}}]}

    router = router_with_clock(config, database_path=tmp_path / "router.sqlite3", transport=transport)
    result, metadata = router.complete_json(
        "synthesizer",
        [{"role": "user", "content": "answer"}],
        TinyPayload,
    )
    assert result.answer == "fallback"
    assert metadata.provider == "mistral"
    assert calls == ["groq", "mistral"]


def test_router_repairs_one_invalid_live_response(tmp_path) -> None:
    config = deepcopy(load_config())
    config["project"]["offline"] = False
    config["role_chains"]["synthesizer"] = ["groq"]
    responses = [
        {"choices": [{"message": {"content": '{"wrong":"field"}'}}]},
        {"choices": [{"message": {"content": '{"answer":"repaired"}'}}]},
    ]

    def transport(provider, model, headers, payload):
        return responses.pop(0)

    router = router_with_clock(config, database_path=tmp_path / "router.sqlite3", transport=transport)
    result, metadata = router.complete_json(
        "synthesizer",
        [{"role": "user", "content": "answer"}],
        TinyPayload,
    )
    assert result.answer == "repaired"
    assert metadata.repaired is True
    assert len(router.call_records()) == 2


def test_router_retries_provider_rate_limit(tmp_path) -> None:
    config = deepcopy(load_config())
    config["project"]["offline"] = False
    config["role_chains"]["synthesizer"] = ["groq"]
    attempts = {"count": 0}

    def transport(provider, model, headers, payload):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise ProviderError("rate limited", retry_after=0.001)
        return {"choices": [{"message": {"content": '{"answer":"after retry"}'}}]}

    router = router_with_clock(config, database_path=tmp_path / "router.sqlite3", transport=transport)
    result, _ = router.complete_json(
        "synthesizer",
        [{"role": "user", "content": "answer"}],
        TinyPayload,
    )
    assert result.answer == "after retry"
    assert attempts["count"] == 2
    assert [row.outcome for row in router.call_records()] == ["rate_error", "valid"]
    assert [row.attempt_kind for row in router.call_records()] == ["first_json", "rate_retry"]


def test_critic_has_no_automatic_rate_retries_and_shared_budget_counts_failures(tmp_path) -> None:
    config = deepcopy(load_config())
    config["project"]["offline"] = False
    config["role_chains"]["critic"] = ["groq"]
    attempts = []

    def transport(*args):
        attempts.append(args)
        if len(attempts) < 3:
            raise ProviderError("rate limited", retry_after=0.001)
        return {"answer": "valid"}

    router = router_with_clock(config, database_path=tmp_path / "bounded.sqlite3", transport=transport)
    with router.critic_request_budget(3):
        for index in range(2):
            with pytest.raises(AllProvidersUnavailable, match="rate limited"):
                router.complete_json("critic", [{"role": "user", "content": f"failed stage {index}"}], TinyPayload)
            assert len(attempts) == index + 1
        router.complete_json("critic", [{"role": "user", "content": "third stage"}], TinyPayload)
        with pytest.raises(CriticBudgetExceeded, match="request budget exhausted"):
            router.complete_json("critic", [{"role": "user", "content": "fourth stage"}], TinyPayload)
    assert len(attempts) == 3
    assert len(router.call_records()) == 3
