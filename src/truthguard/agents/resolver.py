"""Conflict resolver with explicit supersession, contextual, and abstain modes."""

from __future__ import annotations

from datetime import date

from ..schemas import Conflict, FinalAnswer, Span
from .critic import CriticReport
from .retriever import RetrievedContext


class ResolverAgent:
    def __init__(self, resolution_gap_threshold: float = 0.15) -> None:
        self.resolution_gap_threshold = resolution_gap_threshold

    @staticmethod
    def _citations(context: RetrievedContext, conflicts: list[Conflict]) -> list[Span]:
        spans: dict[str, Span] = {}
        for result in context.results:
            spans[result.chunk.chunk_id] = Span(
                chunk_id=result.chunk.chunk_id,
                char_start=result.chunk.char_start,
                char_end=result.chunk.char_end,
            )
        for conflict in conflicts:
            for position in conflict.positions:
                spans[position.span.chunk_id] = position.span
        return list(spans.values())

    def _resolve_conflict(self, conflict: Conflict) -> tuple[Conflict, str, str]:
        breakdown = conflict.trust_breakdown
        ordered = sorted(breakdown.items(), key=lambda item: item[1].total, reverse=True)
        gap = ordered[0][1].total - ordered[1][1].total if len(ordered) > 1 else 1.0
        if conflict.type == "T6" or not ordered:
            conflict = conflict.model_copy(update={"resolution_mode": "abstain", "winner_doc_id": None})
            return conflict, "abstained", "The sources conflict and have no reliable tie-breaker."
        if conflict.type in {"T2", "T5"}:
            positions = " ".join(f"{position.claim_text} ({position.doc_id})" for position in conflict.positions)
            conflict = conflict.model_copy(update={"resolution_mode": "contextual", "winner_doc_id": None})
            return conflict, "conditional", f"The positions apply under different conditions: {positions}"
        winner = conflict.winner_doc_id or ordered[0][0]
        if gap < self.resolution_gap_threshold and conflict.type not in {"T1", "T3", "T4"}:
            conflict = conflict.model_copy(update={"resolution_mode": "abstain", "winner_doc_id": None})
            return conflict, "abstained", "The trust scores are too close to resolve the conflict safely."
        winning_position = next((position for position in conflict.positions if position.doc_id == winner), conflict.positions[0])
        conflict = conflict.model_copy(update={"resolution_mode": "supersession", "winner_doc_id": winner})
        return conflict, "resolved", f"{winning_position.claim_text} ({winner})"

    def resolve(
        self,
        question: str,
        context: RetrievedContext,
        critic: CriticReport,
        *,
        trace=None,
        as_of: date | None = None,
    ) -> FinalAnswer:
        del as_of
        if not context.results:
            return FinalAnswer(
                question=question,
                answer_text="This question is not answerable from the available corpus.",
                status="not_in_corpus",
                claims=critic.claims,
                conflicts=[],
                citations=[],
                trace=trace or [],
            )
        if not critic.conflicts and critic.claims and all(claim.verdict == "unsupported" for claim in critic.claims):
            return FinalAnswer(
                question=question,
                answer_text="This question is not answerable from the available corpus.",
                status="not_in_corpus",
                claims=critic.claims,
                conflicts=[],
                citations=self._citations(context, []),
                trace=trace or [],
            )
        if not critic.conflicts:
            return FinalAnswer(
                question=question,
                answer_text=" ".join(claim.text for claim in critic.claims) or "No supported answer was found.",
                status="no_conflict",
                claims=critic.claims,
                conflicts=[],
                citations=self._citations(context, []),
                trace=trace or [],
            )

        statuses: list[str] = []
        answers: list[str] = []
        resolved_conflicts: list[Conflict] = []
        for conflict in critic.conflicts:
            resolved, status, answer = self._resolve_conflict(conflict)
            resolved_conflicts.append(resolved)
            statuses.append(status)
            answers.append(answer)
        if "abstained" in statuses:
            status = "abstained"
        elif "conditional" in statuses:
            status = "conditional"
        else:
            status = "resolved"
        prefix = {
            "resolved": "Resolved using the highest-trust current position:",
            "conditional": "Conditional answer:",
            "abstained": "I cannot safely resolve this conflict:",
        }[status]
        return FinalAnswer(
            question=question,
            answer_text=prefix + " " + " ".join(answers),
            status=status,
            claims=critic.claims,
            conflicts=resolved_conflicts,
            citations=self._citations(context, resolved_conflicts),
            trace=trace or [],
        )
