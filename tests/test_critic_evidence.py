from datetime import datetime, timezone

import pytest

from scripts.evaluate_critic import _call_evidence, run_evaluation
from truthguard.schemas import CallRecord


def _record(role="critic", stage="critic-call-a-claims", provider="groq", model="qwen", **kwargs):
    return CallRecord(cache_key="key", created_at=datetime.now(timezone.utc),
                      role=role, stage=stage, provider=provider, model=model, **kwargs)


def test_evidence_excludes_cache_and_fallbacks_from_first_try():
    records = [
        _record(role="synthesizer", stage="synthesis", model="gpt-oss"),
        _record(success=False, error="non-JSON"),
        _record(provider="mistral", model="mistral-small", success=True),
        _record(stage="critic-call-b-conflicts", cached=True),
    ]
    evidence = _call_evidence(records)
    assert evidence["critic_first_try_json_stages"] == 0
    assert evidence["critic_fallback_events"] == 1
    assert evidence["critic_cached_stages"] == 1
    assert evidence["call_records"][1]["error"] == "non-JSON"
    assert evidence["actual_request_cap_verified"] is False


def test_evidence_does_not_count_different_role_models_as_fallbacks():
    evidence = _call_evidence([
        _record(role="synthesizer", stage="synthesis", model="gpt-oss"),
        _record(),
    ])
    assert evidence["critic_fallback_events"] == 0
    assert evidence["critic_first_try_json_stages"] == 1


def test_runner_rejects_legacy_output_instead_of_mixing_modes(tmp_path):
    questions = tmp_path / "questions.jsonl"
    questions.write_text('{"qid":"q1","question":"Question?","type":"T0","gold_status":"no_conflict"}\n')
    output = tmp_path / "output.jsonl"
    output.write_text('{"qid":"q1","mode":"deterministic","answer":{}}\n')
    with pytest.raises(ValueError, match="different or legacy run"):
        run_evaluation(questions, output, mode="llm", database_path=tmp_path / "cache.sqlite3")


def test_runner_stops_on_first_quota_failure(tmp_path, monkeypatch):
    questions = tmp_path / "questions.jsonl"
    questions.write_text(
        '{"qid":"q1","question":"Question one?","type":"T0","gold_status":"no_conflict"}\n'
        '{"qid":"q2","question":"Question two?","type":"T0","gold_status":"no_conflict"}\n'
    )
    attempted = []

    class BlockedPipeline:
        def run(self, question):
            attempted.append(question)
            raise RuntimeError("groq HTTP 429: rate limit exceeded")

    monkeypatch.setattr("scripts.evaluate_critic.build_default_pipeline", lambda **kwargs: BlockedPipeline())
    result = run_evaluation(questions, tmp_path / "results.jsonl", mode="llm", database_path=tmp_path / "cache.sqlite3")
    assert result["blocked"] == "quota_or_rate_limit"
    assert result["completed"] == 0
    assert len(attempted) == 1
