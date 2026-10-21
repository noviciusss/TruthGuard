from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from truthguard.agents.critic import CriticAgent
from truthguard.llm import AllProvidersUnavailable, CriticBudgetExceeded, LLMRouter
from truthguard.schemas import CompactClaimsResponse, CompactConflictsResponse, CompactSelfReviewResponse
from test_llm import FakeClock
from test_llm_critic import _context


def make_agent(tmp_path, responses):
    clock, calls = FakeClock(), []
    settings = {"project": {"offline": False}, "providers": {"groq": {
        "models": {"critic": "qwen/qwen3.8-27b"}, "input_tpm_limit": 8000}},
        "role_chains": {"critic": ["groq"]}}

    def transport(provider, model, headers, payload):
        calls.append(payload)
        response = responses.pop(0)
        return {"choices": [{"message": {"content": response if isinstance(response, str) else json.dumps(response)}}]}

    router = LLMRouter(settings, database_path=tmp_path / "compact.sqlite3", transport=transport,
                       clock=clock, sleep=clock.sleep)
    return CriticAgent(router=router), router, calls


def test_compact_roundtrip_preserves_text_evidence_type_confidence_and_review(tmp_path):
    context = _context()
    agent, router, calls = make_agent(tmp_path, [
        {"c": [{"i": "c1", "v": "s", "s": ["p2"], "x": ["p1"]}]},
        {"f": [{"i": "f7", "t": "T1", "p": ["p1", "p2"], "r": "The two values differ.", "c": 0.91}]},
        {"k": ["f1"], "d": [], "r": "Same scope; contradiction retained."},
    ])
    draft = "The hospitalization waiting period is 45 days."
    report = agent.critique(context, draft, [])
    assert report.claims[0].text == draft
    assert report.claims[0].supporting_spans[0].model_dump() == {
        "chunk_id": "DOC-NEW:c1", "char_start": 0, "char_end": 48}
    assert report.claims[0].contradicting_spans[0].chunk_id == "DOC-OLD:c1"
    finding = report.conflicts[0]
    assert finding.conflict_id == "f7"  # review f1 is local, not a fabricated public ID
    assert finding.type == "T1" and finding.confidence == 0.91
    assert finding.rationale == "The two values differ."
    assert finding.winner_doc_id == "DOC-NEW"
    assert [position.doc_id for position in finding.positions] == ["DOC-OLD", "DOC-NEW"]
    assert [position.claim_text for position in finding.positions] == [result.chunk.text for result in context.results]
    assert report.self_critique_changes == ["Same scope; contradiction retained."]
    assert all(call["max_tokens"] == 350 for call in calls)
    # Self-review evidence text appears once per passage, never inside each proposal.
    review_prompt = calls[2]["messages"][0]["content"]
    for result in context.results:
        assert review_prompt.count(result.chunk.text) == 1
    assert "DOC-OLD:c1" not in review_prompt
    assert [row.outcome for row in router.call_records()] == ["valid"] * 3


def test_atomic_subspans_recover_exact_unicode_source_instead_of_model_paraphrase(tmp_path):
    draft = "α Waiting is 45 days; copay is 10%."
    split = draft.index("copay")
    agent, _, _ = make_agent(tmp_path, [{"c": [
        {"i": "c1", "a": 0, "b": split - 2, "v": "s", "s": ["p2"]},
        {"i": "c1", "a": split, "v": "u"},
    ]}])
    claims = agent._llm_claims(_context(), draft, None)
    assert [claim.text for claim in claims] == ["α Waiting is 45 days", "copay is 10%."]
    assert [claim.claim_id for claim in claims] == ["claim-1", "claim-2"]
    assert [claim.verdict for claim in claims] == ["supported", "unsupported"]


@pytest.mark.parametrize("kind,mode", [("T1", "supersession"), ("T2", "contextual"),
                                      ("T3", "supersession"), ("T4", "supersession"),
                                      ("T5", "contextual"), ("T6", "abstain")])
def test_compact_types_keep_existing_public_resolution_semantics(tmp_path, kind, mode):
    agent, _, _ = make_agent(tmp_path, [{"f": [
        {"i": "f1", "t": kind, "p": ["p1", "p2"], "r": "Different values.", "c": 0.72}]}])
    finding = agent._llm_conflicts(_context(), None)[0]
    assert finding.type == kind and finding.resolution_mode == mode
    assert finding.winner_doc_id == ("DOC-NEW" if mode == "supersession" else None)
    assert finding.confidence == 0.72


@pytest.mark.parametrize("payload", [
    {"c": [{"i": "c999", "v": "u"}]},
    {"c": [{"i": "c1", "v": "s", "s": ["p999"]}]},
    {"c": [{"i": "c1", "v": "s"}]},
    {"c": [{"i": "c1", "v": "c"}]},
    {"c": [{"i": "c1", "v": "u", "a": 4, "b": 2}]},
    {"c": [{"i": "c1", "v": "u", "b": 999}]},
    {"c": [{"i": "c1", "v": "u"}, {"i": "c1", "v": "u"}]},
    {"c": []},
    {"c": [{"i": "c1", "v": "u", "text": "invented"}]},
    {"c": [{"i": "c1", "v": "u", "r": "first\nsecond"}]},
    {"c": [{"i": "c1", "v": "u", "r": "a" * 161}]},
])
def test_claim_schema_rejects_hallucinations_missing_units_and_unbounded_rationale(payload):
    with pytest.raises(ValidationError):
        CompactClaimsResponse.model_validate(payload, context={"claims": {"c1": "Text."}, "passages": {"p1": "DOC"}})


@pytest.mark.parametrize("refs", [["p1", "p999"], ["p1", "p1"], ["p1", "p2"]])
def test_conflict_references_require_known_passages_and_two_documents(refs):
    with pytest.raises(ValidationError):
        CompactConflictsResponse.model_validate({"f": [{"i": "f1", "t": "T1", "p": refs, "c": 0.9}]},
                                               context={"passages": {"p1": "SAME-DOC", "p2": "SAME-DOC"}})


@pytest.mark.parametrize("payload", [
    {"k": ["f999"], "d": []}, {"k": ["f1"], "d": ["f1"]},
    {"k": [], "d": []}, {"k": ["f1", "f1"], "d": []},
])
def test_review_ids_are_an_exact_partition(payload):
    with pytest.raises(ValidationError):
        CompactSelfReviewResponse.model_validate(payload, context={"conflicts": {"f1": object()}})


def test_unknown_evidence_triggers_real_repair_and_cache_is_revalidated(tmp_path):
    agent, router, calls = make_agent(tmp_path, [
        {"c": [{"i": "c1", "v": "s", "s": ["p999"]}]},
        {"c": [{"i": "c1", "v": "s", "s": ["p2"]}]},
    ])
    draft = "The hospitalization waiting period is 45 days."
    with router.critic_request_budget():
        claims = agent._llm_claims(_context(), draft, None)
        cached = agent._llm_claims(_context(), draft, None)
        assert router._critic_requests_remaining == 1
    assert cached == claims
    assert len(calls) == 2
    rows = router.call_records()
    assert [row.attempt_kind for row in rows] == ["first_json", "repair", "cache"]
    assert [row.outcome for row in rows] == ["invalid_schema", "valid", "cache"]
    assert "fresh complete JSON" in calls[1]["messages"][-1]["content"]
    assert claims[0].supporting_spans[0].chunk_id == "DOC-NEW:c1"


def test_corrupt_compact_cache_is_revalidated_and_cannot_introduce_unknown_references(tmp_path):
    valid = {"c": [{"i": "c1", "v": "s", "s": ["p2"]}]}
    agent, router, calls = make_agent(tmp_path, [valid, valid])
    draft = "Waiting is 45 days."
    agent._llm_claims(_context(), draft, None)
    record = router.call_records()[0]
    router._store_payload(record.cache_key, record.provider, record.requested_model,
                          {"c": [{"i": "c1", "v": "s", "s": ["p999"]}]})
    claims = agent._llm_claims(_context(), draft, None)
    assert claims[0].supporting_spans[0].chunk_id == "DOC-NEW:c1"
    assert len(calls) == 2
    assert not any(row.cached for row in router.call_records())


def test_invalid_json_repair_consumes_whole_question_budget_before_self_review(tmp_path):
    agent, router, calls = make_agent(tmp_path, [
        '{"c":[', {"c": [{"i": "c1", "v": "u"}]},
        {"f": [{"i": "f1", "t": "T1", "p": ["p1", "p2"], "c": 0.8}]},
    ])
    with pytest.raises(CriticBudgetExceeded):
        agent.critique(_context(), "Waiting is 45 days.", [])
    assert len(calls) == 3
    assert [row.outcome for row in router.call_records()] == ["invalid_json", "valid", "valid"]
    assert [row.stage for row in router.call_records()] == [
        "critic-call-a-claims", "critic-call-a-claims", "critic-call-b-conflicts"]


def test_invalid_reference_never_silently_drops_or_becomes_a_public_claim(tmp_path):
    agent, router, calls = make_agent(tmp_path, [
        {"c": [{"i": "c1", "v": "c", "x": ["p999"]}]},
        {"c": [{"i": "c1", "v": "c", "x": ["p999"]}]},
    ])
    with pytest.raises(AllProvidersUnavailable, match="schema/reference"):
        agent._llm_claims(_context(), "Waiting is 45 days.", None)
    assert len(calls) == 2
    assert not any(row.success for row in router.call_records())


def test_empty_conflict_scan_skips_actual_self_review(tmp_path):
    agent, router, calls = make_agent(tmp_path, [{"c": [{"i": "c1", "v": "u"}]}, {"f": []}])
    report = agent.critique(_context(), "Waiting is 45 days.", [])
    assert len(calls) == 2 and len(router.call_records()) == 2
    assert report.conflicts == []
    assert not report.self_critique_ran
