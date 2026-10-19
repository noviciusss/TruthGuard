"""Transparent arithmetic trust scoring for conflict positions."""

from __future__ import annotations

from datetime import date
from typing import Iterable

from ..config import load_config
from ..schemas import Conflict, Position, TrustScore


class TrustScorer:
    def __init__(self, weights: dict[str, float] | None = None) -> None:
        configured = load_config().get("trust_weights", {})
        self.weights = {
            "recency": float((weights or configured).get("recency", 0.25)),
            "authority": float((weights or configured).get("authority", 0.25)),
            "specificity": float((weights or configured).get("specificity", 0.20)),
            "corroboration": float((weights or configured).get("corroboration", 0.15)),
            "metadata_confidence": float((weights or configured).get("metadata_confidence", 0.15)),
        }
        total = sum(self.weights.values())
        if total <= 0:
            raise ValueError("trust weights must have a positive sum")
        self.weights = {key: value / total for key, value in self.weights.items()}

    @staticmethod
    def _recency(position: Position, dates: list[date]) -> float:
        if position.doc_meta.effective_date is None or len(set(dates)) <= 1:
            return 0.5
        earliest, latest = min(dates), max(dates)
        span = (latest - earliest).days or 1
        return max(0.0, min(1.0, (position.doc_meta.effective_date - earliest).days / span))

    @staticmethod
    def _authority(position: Position, positions: list[Position]) -> float:
        maximum = max((item.doc_meta.authority_rank for item in positions), default=1) or 1
        return max(0.0, min(1.0, position.doc_meta.authority_rank / maximum))

    @staticmethod
    def _specificity(position: Position) -> float:
        if position.doc_meta.doc_type in {"amendment", "notice"}:
            return 0.9
        if position.doc_meta.doc_type == "policy":
            return 0.7
        return 0.5

    @staticmethod
    def _corroboration(position: Position, positions: list[Position]) -> float:
        same = sum(1 for item in positions if item.claim_text.strip().lower() == position.claim_text.strip().lower())
        return max(0.0, min(1.0, (same - 1) / max(1, len(positions) - 1)))

    def score_positions(self, positions: Iterable[Position]) -> dict[str, TrustScore]:
        positions = list(positions)
        dates = [position.doc_meta.effective_date for position in positions if position.doc_meta.effective_date]
        scores: dict[str, TrustScore] = {}
        for position in positions:
            breakdown = {
                "recency": self._recency(position, dates),
                "authority": self._authority(position, positions),
                "specificity": self._specificity(position),
                "corroboration": self._corroboration(position, positions),
                "metadata_confidence": position.doc_meta.metadata_confidence,
            }
            total = sum(self.weights[key] * value for key, value in breakdown.items())
            scores[position.doc_id] = TrustScore(
                **breakdown,
                total=total,
                rationale=(
                    f"recency={breakdown['recency']:.2f}, authority={breakdown['authority']:.2f}, "
                    f"specificity={breakdown['specificity']:.2f}, corroboration={breakdown['corroboration']:.2f}, "
                    f"metadata_confidence={breakdown['metadata_confidence']:.2f}"
                ),
            )
        return scores

    def apply(self, conflict: Conflict) -> Conflict:
        scores = self.score_positions(conflict.positions)
        return conflict.model_copy(update={"trust_breakdown": scores})
