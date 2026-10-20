from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import BaseModel

from truthguard.config import load_config
from truthguard.llm import AllProvidersUnavailable, LLMRouter, ProviderError


class TinyPayload(BaseModel):
    answer: str


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
    router = LLMRouter(config, database_path=database)
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

    router = LLMRouter(config, database_path=tmp_path / "router.sqlite3", transport=transport)
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

    router = LLMRouter(config, database_path=tmp_path / "router.sqlite3", transport=transport)
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
    router = LLMRouter(config, database_path=tmp_path / "router.sqlite3")
    attempts = {"count": 0}

    def invoke(provider, model, messages, params):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise ProviderError("rate limited", retry_after=0.001)
        return {"choices": [{"message": {"content": '{"answer":"after retry"}'}}]}

    router._invoke = invoke
    result, _ = router.complete_json(
        "synthesizer",
        [{"role": "user", "content": "answer"}],
        TinyPayload,
    )
    assert result.answer == "after retry"
    assert attempts["count"] == 2


def test_critic_budget_counts_retries_as_actual_requests(tmp_path, monkeypatch) -> None:
    config = deepcopy(load_config())
    config["project"]["offline"] = False
    config["role_chains"]["critic"] = ["groq"]
    attempts = []

    def transport(*args):
        attempts.append(args)
        if len(attempts) < 3:
            raise ProviderError("rate limited", retry_after=0.001)
        return {"answer": "valid"}

    monkeypatch.setattr("truthguard.llm.time.sleep", lambda seconds: None)
    router = LLMRouter(config, database_path=tmp_path / "bounded.sqlite3", transport=transport)
    with router.critic_request_budget(3):
        router.complete_json("critic", [{"role": "user", "content": "first stage"}], TinyPayload)
        with pytest.raises(AllProvidersUnavailable, match="request budget exhausted"):
            router.complete_json("critic", [{"role": "user", "content": "second stage"}], TinyPayload)
    assert len(attempts) == 3
