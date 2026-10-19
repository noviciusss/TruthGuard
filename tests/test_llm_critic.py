from __future__ import annotations

from copy import deepcopy
from datetime import date

from truthguard.agents.critic import CriticAgent
from truthguard.config import load_config
from truthguard.graph.supersession import SupersessionGraph
from truthguard.ingest.index import SearchResult
from truthguard.llm import LLMRouter
from truthguard.schemas import Chunk, DocMeta
from truthguard.agents.retriever import RetrievedContext


def _meta(doc_id: str, effective: date) -> DocMeta:
    return DocMeta(
        doc_id=doc_id,
        title=doc_id,
        doc_type="policy",
        effective_date=effective,
        authority_rank=4,
        metadata_source="provided",
        metadata_confidence=1.0,
    )


def _context() -> RetrievedContext:
    old = _meta("DOC-OLD", date(2024, 1, 1))
    new = _meta("DOC-NEW", date(2025, 1, 1))
    old_chunk = Chunk(
        chunk_id="DOC-OLD:c1",
        doc_id="DOC-OLD",
        section_path="Rules",
        text="The hospitalization waiting period is 30 days.",
        char_start=0,
        char_end=48,
        doc_meta=old,
    )
    new_chunk = Chunk(
        chunk_id="DOC-NEW:c1",
        doc_id="DOC-NEW",
        section_path="Rules",
        text="The hospitalization waiting period is 45 days.",
        char_start=0,
        char_end=48,
        doc_meta=new,
    )
    return RetrievedContext(
        question="What is the hospitalization waiting period?",
        results=[
            SearchResult(old_chunk, 1.0, 1.0, 1.0),
            SearchResult(new_chunk, 0.9, 0.9, 0.9),
        ],
        reformulations=[],
        neighbor_doc_ids=[],
    )


def test_llm_critic_runs_three_structured_calls_and_returns_mode(tmp_path) -> None:
    config = deepcopy(load_config())
    config["project"]["offline"] = False
    config["role_chains"]["critic"] = ["gemini"]
    calls: list[str] = []

    def transport(provider, model, headers, payload):
        content = payload["messages"][0]["content"]
        calls.append(content)
        if "atomic claim decomposition" in content:
            return {
                "choices": [{"message": {"content": '{"claims":[{"claim_id":"claim-1","text":"The hospitalization waiting period is 45 days.","verdict":"supported","supporting_evidence":[{"chunk_id":"DOC-NEW:c1"}],"contradicting_evidence":[],"rationale":"New passage supports the claim."}]}'}}]
            }
        if "pairwise within each topic cluster" in content:
            return {
                "choices": [{"message": {"content": '{"conflicts":[{"conflict_id":"t1-waiting","type":"T1","position_evidence":{"DOC-OLD":[{"chunk_id":"DOC-OLD:c1"}],"DOC-NEW":[{"chunk_id":"DOC-NEW:c1"}]},"rationale":"The later document changes the value.","confidence":0.95}]}'}}]
            }
        return {
            "choices": [{"message": {"content": '{"keep_conflict_ids":["t1-waiting"],"dropped_conflict_ids":[],"changes":[]}'}}]
        }

    router = LLMRouter(config, database_path=tmp_path / "critic.sqlite3", transport=transport)
    graph = SupersessionGraph.from_documents([_meta("DOC-OLD", date(2024, 1, 1)), _meta("DOC-NEW", date(2025, 1, 1))])
    report = CriticAgent(graph, router=router).critique(_context(), "The hospitalization waiting period is 45 days.", [])

    assert report.mode == "llm"
    assert report.llm_calls == 3
    assert len(calls) == 3
    assert '"claims"' in calls[0]
    assert "Do not use wrapper keys" in calls[0]
    assert '"position_evidence"' in calls[1]
    assert '"keep_conflict_ids"' in calls[2]
    assert report.claims[0].verdict == "supported"
    assert report.conflicts[0].type == "T1"
    assert report.conflicts[0].winner_doc_id == "DOC-NEW"
    assert report.conflicts[0].trust_breakdown


def test_no_llm_critic_flag_preserves_deterministic_mode(tmp_path) -> None:
    config = deepcopy(load_config())
    config["project"]["offline"] = False
    config["role_chains"]["critic"] = ["gemini"]
    router = LLMRouter(
        config,
        database_path=tmp_path / "critic.sqlite3",
        transport=lambda *_args: (_ for _ in ()).throw(AssertionError("LLM must not be called")),
    )
    report = CriticAgent(router=router, use_llm=False).critique(
        _context(), "The hospitalization waiting period is 45 days.", []
    )
    assert report.mode == "deterministic"
    assert report.llm_calls == 0
