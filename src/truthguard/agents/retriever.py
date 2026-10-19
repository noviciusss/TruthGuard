"""Hybrid retriever with conflict-seeking query expansion and graph neighbors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ..config import load_config
from ..graph.supersession import SupersessionGraph
from ..ingest.index import HybridIndex, SearchResult
from ..ingest.index import tokenize
from ..llm import LLMRouter
from ..schemas import ReformulationResponse


@dataclass(frozen=True)
class RetrievedContext:
    question: str
    results: list[SearchResult]
    reformulations: list[str]
    neighbor_doc_ids: list[str]

    @property
    def chunks(self):
        return [result.chunk for result in self.results]


class RetrieverAgent:
    def __init__(
        self,
        index: HybridIndex,
        graph: SupersessionGraph | None = None,
        *,
        router: LLMRouter | None = None,
        initial_k: int | None = None,
        final_k: int | None = None,
        expansion_enabled: bool = True,
    ) -> None:
        config = load_config()
        retrieval = config.get("retrieval", {})
        self.index = index
        self.graph = graph
        self.router = router
        self.initial_k = initial_k or int(retrieval.get("initial_k", 20))
        self.final_k = final_k or int(retrieval.get("final_k", 8))
        self.expansion_enabled = expansion_enabled

    @staticmethod
    def _deterministic_reformulations(question: str) -> list[str]:
        return [
            f"what else could govern this question: {question}",
            f"amendment exception circular or notice about: {question}",
        ]

    def _reformulations(self, question: str) -> list[str]:
        if self.router is None or self.router.config.get("project", {}).get("offline", True):
            return self._deterministic_reformulations(question)
        response, _ = self.router.complete_json(
            "generation",
            [
                {"role": "system", "content": "Return at most two short search reformulations as JSON."},
                {"role": "user", "content": question},
            ],
            ReformulationResponse,
            stage="retrieval-expansion",
        )
        return [query for query in response.queries if query.strip()][:2]

    def retrieve(
        self,
        question: str,
        *,
        as_of: date | None = None,
        expand: bool = True,
    ) -> RetrievedContext:
        queries = [question]
        if expand and self.expansion_enabled:
            queries.extend(self._reformulations(question))
        by_chunk: dict[str, SearchResult] = {}
        for query_index, query in enumerate(queries):
            for result in self.index.search(query, initial_k=self.initial_k, final_k=self.final_k):
                if as_of and result.chunk.doc_meta and result.chunk.doc_meta.effective_date:
                    if result.chunk.doc_meta.effective_date > as_of:
                        continue
                # Keep the original user query ahead of broad conflict-seeking
                # expansions while still retaining expansion-only evidence.
                if query_index == 0:
                    result = SearchResult(
                        chunk=result.chunk,
                        score=result.score + 0.1,
                        bm25_score=result.bm25_score,
                        dense_score=result.dense_score,
                    )
                existing = by_chunk.get(result.chunk.chunk_id)
                if existing is None or result.score > existing.score:
                    by_chunk[result.chunk.chunk_id] = result

        neighbor_doc_ids: list[str] = []
        pre_neighbor = sorted(by_chunk.values(), key=lambda item: (-item.score, item.chunk.chunk_id))
        source_doc_ids: list[str] = []
        if self.graph is not None:
            for result in pre_neighbor:
                if result.chunk.doc_id not in source_doc_ids:
                    source_doc_ids.append(result.chunk.doc_id)
                if len(source_doc_ids) == 3:
                    break
            for result in [item for item in pre_neighbor if item.chunk.doc_id in source_doc_ids]:
                for neighbor in self.graph.neighbors(result.chunk.doc_id):
                    if neighbor not in neighbor_doc_ids:
                        neighbor_doc_ids.append(neighbor)
            for neighbor in neighbor_doc_ids:
                neighbor_chunks = [chunk for chunk in self.index.chunks if chunk.doc_id == neighbor]
                query_tokens = set(tokenize(question))
                neighbor_chunks.sort(
                    key=lambda chunk: len(query_tokens & set(tokenize(chunk.text))),
                    reverse=True,
                )
                for chunk in neighbor_chunks[:2]:
                    if as_of and chunk.doc_meta and chunk.doc_meta.effective_date and chunk.doc_meta.effective_date > as_of:
                        continue
                    by_chunk.setdefault(
                        chunk.chunk_id,
                        SearchResult(
                            chunk=chunk,
                            score=0.13 + 0.005 * len(query_tokens & set(tokenize(chunk.text))),
                            bm25_score=0.0,
                            dense_score=0.0,
                        ),
                    )
        ranked = sorted(by_chunk.values(), key=lambda item: (-item.score, item.chunk.chunk_id))
        if neighbor_doc_ids:
            base_ids = {item.chunk.chunk_id for item in pre_neighbor[: self.final_k]}
            results = [item for item in ranked if item.chunk.chunk_id in base_ids]
            results.extend(item for item in ranked if item.chunk.chunk_id not in base_ids and item.chunk.doc_id in neighbor_doc_ids)
        else:
            results = ranked[: self.final_k]
        return RetrievedContext(
            question=question,
            results=results,
            reformulations=queries[1:],
            neighbor_doc_ids=neighbor_doc_ids,
        )
