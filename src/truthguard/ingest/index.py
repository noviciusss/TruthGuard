"""Hybrid BM25 plus dense retrieval with RRF merging."""

from __future__ import annotations

import json
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import numpy as np

from ..schemas import Chunk

try:  # Optional in minimal/offline environments.
    from rank_bm25 import BM25Okapi
except ImportError:  # pragma: no cover - exercised only without optional install
    BM25Okapi = None

try:  # Optional BGE/FAISS path; the hash path remains fully offline.
    import faiss
except ImportError:  # pragma: no cover - optional dependency
    faiss = None

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


class HashEmbedder:
    """Small deterministic embedding fallback; no model download is required."""

    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def __call__(self, texts: list[str]) -> np.ndarray:
        matrix = np.zeros((len(texts), self.dimensions), dtype=np.float32)
        for row, text in enumerate(texts):
            for token in tokenize(text):
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:8], "big") % self.dimensions
                matrix[row, index] += 1.0
            norm = np.linalg.norm(matrix[row])
            if norm:
                matrix[row] /= norm
        return matrix


class BGEEmbedder:
    """Sentence-transformers BGE embedder for the optional ML retrieval path."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("BGE retrieval requires `make install-ml`") from exc
        if SentenceTransformer is None:
            raise RuntimeError("BGE retrieval requires `make install-ml`")
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def __call__(self, texts: list[str]) -> np.ndarray:
        return np.asarray(
            self.model.encode(
                texts,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            ),
            dtype=np.float32,
        )


@dataclass(frozen=True)
class SearchResult:
    chunk: Chunk
    score: float
    bm25_score: float
    dense_score: float


def reciprocal_rank_fusion(rankings: Iterable[list[int]], *, k: int = 60) -> dict[int, float]:
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, index in enumerate(ranking, start=1):
            scores[index] = scores.get(index, 0.0) + 1.0 / (k + rank)
    return scores


class HybridIndex:
    """In-memory hybrid index with JSON persistence for local development."""

    def __init__(
        self,
        *,
        embedder: Callable[[list[str]], np.ndarray] | None = None,
        use_faiss: bool = False,
    ) -> None:
        self.chunks: list[Chunk] = []
        self._tokenized: list[list[str]] = []
        self._bm25 = None
        self._embeddings = np.empty((0, 0), dtype=np.float32)
        self.embedder = embedder or HashEmbedder()
        self.use_faiss = use_faiss
        self._faiss_index = None

    def build(self, chunks: Iterable[Chunk]) -> None:
        self.chunks = list(chunks)
        self._tokenized = [tokenize(chunk.text) for chunk in self.chunks]
        if BM25Okapi is not None and self._tokenized:
            self._bm25 = BM25Okapi(self._tokenized)
        else:
            self._bm25 = None
        self._embeddings = self.embedder([chunk.text for chunk in self.chunks]) if self.chunks else np.empty((0, 0))
        if self.use_faiss:
            if faiss is None:
                raise RuntimeError("FAISS retrieval requires `make install-ml`")
            self._faiss_index = faiss.IndexFlatIP(int(self._embeddings.shape[1]))
            self._faiss_index.add(np.ascontiguousarray(self._embeddings, dtype=np.float32))

    def _bm25_scores(self, query: str) -> np.ndarray:
        if not self.chunks:
            return np.empty((0,), dtype=np.float32)
        if self._bm25 is not None:
            return np.asarray(self._bm25.get_scores(tokenize(query)), dtype=np.float32)
        query_tokens = set(tokenize(query))
        return np.asarray([len(query_tokens & set(tokens)) for tokens in self._tokenized], dtype=np.float32)

    def _dense_scores(self, query: str) -> np.ndarray:
        if not self.chunks:
            return np.empty((0,), dtype=np.float32)
        query_vector = self.embedder([query])[0]
        return self._embeddings @ query_vector

    def _dense_ranking(self, query: str, limit: int) -> list[int]:
        if self._faiss_index is None:
            return self._ranking(self._dense_scores(query), limit)
        query_vector = np.ascontiguousarray(self.embedder([query]), dtype=np.float32)
        _, indexes = self._faiss_index.search(query_vector, limit)
        return [int(index) for index in indexes[0] if index >= 0]

    @staticmethod
    def _ranking(scores: np.ndarray, limit: int) -> list[int]:
        if len(scores) == 0:
            return []
        return list(np.argsort(-scores, kind="stable")[:limit])

    def search(self, query: str, *, initial_k: int = 20, final_k: int = 8) -> list[SearchResult]:
        if not self.chunks:
            return []
        bm25_scores = self._bm25_scores(query)
        dense_scores = self._dense_scores(query)
        bm25_rank = self._ranking(bm25_scores, min(initial_k, len(self.chunks)))
        dense_rank = self._dense_ranking(query, min(initial_k, len(self.chunks)))
        rrf_scores = reciprocal_rank_fusion([bm25_rank, dense_rank])
        indexes = sorted(rrf_scores, key=lambda item: (-rrf_scores[item], item))[:final_k]
        return [
            SearchResult(
                chunk=self.chunks[index],
                score=rrf_scores[index],
                bm25_score=float(bm25_scores[index]),
                dense_score=float(dense_scores[index]),
            )
            for index in indexes
        ]

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "chunks": [chunk.model_dump(mode="json") for chunk in self.chunks],
            "embedding_dimensions": int(self._embeddings.shape[1]) if self._embeddings.ndim == 2 and len(self._embeddings) else 256,
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path, *, embedder: Callable[[list[str]], np.ndarray] | None = None) -> "HybridIndex":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        index = cls(embedder=embedder or HashEmbedder(payload.get("embedding_dimensions", 256)))
        index.build(Chunk.model_validate(item) for item in payload["chunks"])
        return index
