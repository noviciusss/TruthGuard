from __future__ import annotations

from copy import deepcopy

from pydantic import BaseModel

from truthguard.config import load_config
from truthguard.llm import LLMRouter, ProviderError


class TinyPayload(BaseModel):
    answer: str


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
