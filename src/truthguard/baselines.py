"""Naive comparison systems used in the TruthGuard evaluation."""

from __future__ import annotations

from dataclasses import replace

from .agents.retriever import RetrievedContext, RetrieverAgent
from .agents.synthesizer import SynthesizerAgent
from .schemas import FinalAnswer


def _final(question: str, context: RetrievedContext, answer: str) -> FinalAnswer:
    return FinalAnswer(
        question=question,
        answer_text=answer,
        status="no_conflict",
        citations=[
            {
                "chunk_id": result.chunk.chunk_id,
                "char_start": result.chunk.char_start,
                "char_end": result.chunk.char_end,
            }
            for result in context.results[:3]
        ],
    )


def naive_rag(question: str, retriever: RetrieverAgent, synthesizer: SynthesizerAgent) -> FinalAnswer:
    context = retriever.retrieve(question, expand=False)
    draft = synthesizer.draft(question, context)
    return _final(question, context, draft.answer_text)


def recency_rag(question: str, retriever: RetrieverAgent, synthesizer: SynthesizerAgent) -> FinalAnswer:
    context = retriever.retrieve(question, expand=False)
    sorted_results = sorted(
        context.results,
        key=lambda result: result.chunk.doc_meta.effective_date if result.chunk.doc_meta and result.chunk.doc_meta.effective_date else __import__("datetime").date.min,
        reverse=True,
    )
    recency_context = replace(context, results=sorted_results)
    draft = synthesizer.draft(question, recency_context)
    return _final(question, recency_context, draft.answer_text)


def self_consistency_rag(question: str, retriever: RetrieverAgent, synthesizer: SynthesizerAgent) -> FinalAnswer:
    first = retriever.retrieve(question, expand=False)
    second = retriever.retrieve(question, expand=True)
    first_draft = synthesizer.draft(question, first)
    second_draft = synthesizer.draft(question, second)
    selected = second if len(second_draft.answer_text) >= len(first_draft.answer_text) else first
    answer = second_draft.answer_text if selected is second else first_draft.answer_text
    return _final(question, selected, answer)
