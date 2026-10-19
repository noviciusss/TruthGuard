"""Passage-grounded draft answer agent."""

from __future__ import annotations

from ..llm import LLMRouter
from ..ingest.index import tokenize
from ..schemas import DraftAnswer, Span
from .retriever import RetrievedContext


STOPWORDS = {"the", "a", "an", "is", "are", "for", "of", "and", "or", "to", "with", "within", "from", "this", "that", "may", "be", "how", "what"}


class SynthesizerAgent:
    def __init__(self, router: LLMRouter | None = None) -> None:
        self.router = router

    @staticmethod
    def _source_prompt(context: RetrievedContext) -> str:
        blocks: list[str] = []
        for result in context.results:
            meta = result.chunk.doc_meta
            date_text = meta.effective_date.isoformat() if meta and meta.effective_date else "unknown date"
            title = meta.title if meta else result.chunk.doc_id
            blocks.append(f"[{result.chunk.chunk_id}] {title} ({date_text})\n{result.chunk.text}")
        return "\n\n".join(blocks)

    def draft(self, question: str, context: RetrievedContext) -> DraftAnswer:
        source_text = self._source_prompt(context)
        if self.router is not None and not self.router.config.get("project", {}).get("offline", True):
            response, _ = self.router.complete_json(
                "synthesizer",
                [
                    {
                        "role": "system",
                        "content": "Answer only from the supplied passages. Keep conflicting positions visible and cite chunk IDs inline.",
                    },
                    {"role": "user", "content": f"Question: {question}\n\nPassages:\n{source_text}"},
                ],
                DraftAnswer,
                stage="synthesis",
            )
            return response

        if not context.results:
            return DraftAnswer(answer_text="I could not find a relevant passage in the corpus.", citations=[])
        unique_docs: set[str] = set()
        selected = []
        question_tokens = set(tokenize(question)) - STOPWORDS
        ranked_results = sorted(
            context.results,
            key=lambda result: (len(question_tokens & (set(tokenize(result.chunk.text)) - STOPWORDS)), result.score),
            reverse=True,
        )
        for neighbor_id in context.neighbor_doc_ids[:2]:
            neighbor_result = next((result for result in ranked_results if result.chunk.doc_id == neighbor_id), None)
            if neighbor_result is not None:
                unique_docs.add(neighbor_id)
                selected.append(neighbor_result)
        for result in ranked_results:
            if len(selected) == 4:
                break
            if result.chunk.doc_id not in unique_docs:
                unique_docs.add(result.chunk.doc_id)
                selected.append(result)
        citations = [
            Span(chunk_id=result.chunk.chunk_id, char_start=result.chunk.char_start, char_end=result.chunk.char_end)
            for result in selected
        ]
        answer = " ".join(f"{result.chunk.text.strip()} [{result.chunk.chunk_id}]" for result in selected)
        return DraftAnswer(answer_text=answer, citations=citations)
