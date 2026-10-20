from __future__ import annotations

from pathlib import Path
from copy import deepcopy

from truthguard.agents.retriever import RetrieverAgent
from truthguard.agents.synthesizer import SynthesizerAgent
from truthguard.baselines import naive_rag, recency_rag, self_consistency_rag
from truthguard.graph.supersession import SupersessionGraph
from truthguard.ingest.chunker import chunk_document
from truthguard.ingest.index import HybridIndex
from truthguard.ingest.loader import load_documents
from truthguard.config import load_config
from truthguard.llm import LLMRouter


ROOT = Path(__file__).resolve().parents[1]


def make_agents() -> tuple[RetrieverAgent, SynthesizerAgent]:
    documents = load_documents(ROOT / "data/corpus")
    chunks = [chunk for document in documents for chunk in chunk_document(document)]
    index = HybridIndex()
    index.build(chunks)
    graph = SupersessionGraph.from_documents(document.meta for document in documents)
    return RetrieverAgent(index, graph), SynthesizerAgent()


def test_retriever_expands_queries_and_surfaces_related_documents() -> None:
    retriever, _ = make_agents()
    context = retriever.retrieve("What is the hospitalization waiting period?", expand=True)
    assert len(context.reformulations) == 2
    assert context.results
    assert {result.chunk.doc_id for result in context.results} & {"AMD-2025-03", "FAQ-2024-01"}
    assert context.neighbor_doc_ids


def test_retriever_handles_indirect_wild_wording() -> None:
    retriever, _ = make_agents()
    context = retriever.retrieve(
        "A reimbursement was not filed immediately after discharge. Is the window measured in weeks or months?",
        expand=True,
    )
    document_ids = {result.chunk.doc_id for result in context.results}
    assert document_ids & {"AMD-2025-04", "MAN-2025-CLAIMS", "POL-2024-V1"}


def test_live_reformulation_is_one_cached_call_with_topic(tmp_path) -> None:
    documents = load_documents(ROOT / "data/corpus")
    chunks = [chunk for document in documents for chunk in chunk_document(document)]
    index = HybridIndex()
    index.build(chunks)
    config = deepcopy(load_config())
    config["project"]["offline"] = False
    config["role_chains"]["generation"] = ["groq"]
    calls = []

    def transport(provider, model, headers, payload):
        calls.append(payload)
        return {"choices": [{"message": {"content": '{"topic":"claim deadline","queries":["reimbursement deadline after discharge","amendment claim filing window"]}'}}]}

    router = LLMRouter(config, database_path=tmp_path / "reformulation.sqlite3", transport=transport)
    retriever = RetrieverAgent(index, router=router)
    first = retriever.retrieve("When can a reimbursement claim be filed?", expand=True)
    second = retriever.retrieve("When can a reimbursement claim be filed?", expand=True)

    assert len(calls) == 1
    assert first.topic == "claim deadline"
    assert first.reformulations == second.reformulations
    assert router.call_records()[1].cached is True


def test_synthesizer_is_passage_grounded_in_offline_mode() -> None:
    retriever, synthesizer = make_agents()
    context = retriever.retrieve("What is the hospitalization waiting period?")
    draft = synthesizer.draft(context.question, context)
    assert draft.answer_text
    assert draft.citations
    assert any(citation.chunk_id in draft.answer_text for citation in draft.citations)


def test_baselines_produce_comparable_final_answers() -> None:
    retriever, synthesizer = make_agents()
    question = "What is the hospitalization waiting period?"
    answers = [
        naive_rag(question, retriever, synthesizer),
        recency_rag(question, retriever, synthesizer),
        self_consistency_rag(question, retriever, synthesizer),
    ]
    assert all(answer.status == "no_conflict" for answer in answers)
    assert all(answer.answer_text for answer in answers)
    assert all(answer.citations for answer in answers)
