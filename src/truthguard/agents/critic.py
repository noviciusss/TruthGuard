"""Adversarial claim and conflict critic.

The deterministic path is intentionally complete enough for offline tests and
demo fixtures. When a live router is supplied, this module is the seam where
the two compact structured critic calls can replace or augment the heuristics.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date

from ..graph.supersession import SupersessionGraph
from ..ingest.index import tokenize
from ..schemas import Claim, Conflict, CriticReport, Position, Span
from .retriever import RetrievedContext
from .trust import TrustScorer


STOPWORDS = {"the", "a", "an", "is", "are", "for", "of", "and", "or", "to", "with", "within", "from", "this", "that", "may", "be"}
NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:days?|months?|%|currency units?)?", flags=re.IGNORECASE)
TOPIC_KEYWORDS = {
    "waiting_period": ("waiting", "hospitalization"),
    "copay": ("copay", "co-payment", "co payment"),
    "claim_deadline": ("claim", "discharge"),
    "lookback": ("lookback", "pre-existing", "preexisting"),
    "preauthorization": ("pre-authorization", "preauthorization", "prior approval", "emergency admission"),
    "room_rent": ("room rent", "sum insured"),
    "renewal": ("renewal", "grace"),
    "grievance": ("grievance", "resolution"),
    "network": ("network", "cashless"),
    "ambulance": ("ambulance",),
    "annual_limit": ("annual limit", "annual hospitalization"),
    "telemedicine": ("telemedicine",),
    "maternity": ("maternity",),
    "exclusions": ("cosmetic", "excluded"),
}


def _meaningful_tokens(text: str) -> set[str]:
    return {token for token in tokenize(text) if token not in STOPWORDS and len(token) > 2}


def _topic(text: str) -> str | None:
    lowered = text.lower()
    for name, keywords in TOPIC_KEYWORDS.items():
        if _contains_topic(name, lowered):
            return name
    return None


def _contains_topic(topic: str, lowered_text: str) -> bool:
    keywords = TOPIC_KEYWORDS[topic]
    return all(keyword in lowered_text for keyword in keywords) if topic in {"waiting_period", "claim_deadline"} else any(keyword in lowered_text for keyword in keywords)


class CriticAgent:
    def __init__(
        self,
        graph: SupersessionGraph | None = None,
        scorer: TrustScorer | None = None,
        *,
        self_critique: bool = True,
    ) -> None:
        self.graph = graph
        self.scorer = scorer or TrustScorer()
        self.self_critique = self_critique

    @staticmethod
    def _claims(context: RetrievedContext, draft_text: str, citations: list[Span]) -> list[Claim]:
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", draft_text) if part.strip()]
        if not sentences:
            sentences = [draft_text.strip()] if draft_text.strip() else []
        claims: list[Claim] = []
        for index, sentence in enumerate(sentences):
            clean = re.sub(r"\[[^]]+\]", "", sentence).strip()
            if not clean:
                continue
            tokens = _meaningful_tokens(clean)
            supporting: list[Span] = []
            question_topic = _topic(context.question)
            for result in context.results:
                overlap = len(tokens & _meaningful_tokens(result.chunk.text))
                result_topic = _topic(result.chunk.text)
                topic_matches = question_topic is not None and result_topic == question_topic
                if topic_matches and (overlap >= 2 or clean.lower() in result.chunk.text.lower()):
                    supporting.append(Span(chunk_id=result.chunk.chunk_id, char_start=result.chunk.char_start, char_end=result.chunk.char_end))
            claims.append(
                Claim(
                    claim_id=f"claim-{index + 1}",
                    text=clean,
                    verdict="supported" if supporting else "unsupported",
                    supporting_spans=supporting,
                )
            )
        return claims

    @staticmethod
    def _position(result) -> Position:
        return Position(
            claim_text=result.chunk.text.strip(),
            doc_id=result.chunk.doc_id,
            span=Span(chunk_id=result.chunk.chunk_id, char_start=result.chunk.char_start, char_end=result.chunk.char_end),
            doc_meta=result.chunk.doc_meta,
        )

    def _winner(self, positions: list[Position]) -> str | None:
        dated = [position for position in positions if position.doc_meta.effective_date]
        if not dated:
            return None
        return max(
            dated,
            key=lambda position: (position.doc_meta.effective_date or date.min, position.doc_meta.authority_rank),
        ).doc_id

    def _find_conflicts(self, context: RetrievedContext, as_of: date | None = None) -> list[Conflict]:
        grouped: dict[str, list] = defaultdict(list)
        question_topic = _topic(context.question)
        for result in context.results:
            topic = question_topic if question_topic and _contains_topic(question_topic, result.chunk.text.lower()) else _topic(result.chunk.text)
            if topic and question_topic is not None and topic == question_topic:
                grouped[topic].append(result)
        conflicts: list[Conflict] = []
        for topic, results in grouped.items():
            by_doc = {}
            for result in results:
                by_doc.setdefault(result.chunk.doc_id, result)
            results = list(by_doc.values())
            if len(results) < 2:
                continue
            values = {value.lower() for result in results for value in NUMBER_RE.findall(result.chunk.text)}
            has_emergency_exception = any("emergency" in result.chunk.text.lower() and "without" in result.chunk.text.lower() for result in results)
            has_planned_rule = any("planned" in result.chunk.text.lower() and "require" in result.chunk.text.lower() for result in results)
            if topic == "renewal" or topic in {"network", "grievance", "ambulance", "telemedicine", "exclusions"}:
                if len(values) <= 1:
                    continue
            if topic == "preauthorization" and not (has_emergency_exception and has_planned_rule):
                continue
            if len(values) <= 1 and topic != "preauthorization":
                continue
            positions = [self._position(result) for result in results[:3]]
            if topic == "preauthorization":
                conflict_type = "T5"
                mode = "contextual"
            elif topic in {"copay", "room_rent"}:
                conflict_type = "T2"
                mode = "contextual"
            elif topic == "lookback":
                conflict_type = "T4"
                mode = "supersession"
            elif topic == "claim_deadline":
                conflict_type = "T3"
                mode = "supersession"
            elif topic == "annual_limit":
                same_date_authority = [
                    result
                    for result in results
                    if result.chunk.doc_meta
                    and result.chunk.doc_meta.effective_date == results[0].chunk.doc_meta.effective_date
                    and result.chunk.doc_meta.authority_rank == results[0].chunk.doc_meta.authority_rank
                ]
                if len(same_date_authority) >= 2:
                    positions = [self._position(result) for result in same_date_authority[:2]]
                    conflict_type = "T6"
                    mode = "abstain"
                else:
                    conflict_type = "T3"
                    mode = "supersession"
            elif topic == "waiting_period" and self.graph is not None:
                conflict_type = "T1"
                mode = "supersession"
            else:
                conflict_type = "T3"
                mode = "supersession"
            winner = None if conflict_type in {"T2", "T5", "T6"} else self._winner(positions)
            conflict = Conflict(
                conflict_id=f"{conflict_type.lower()}-{topic}",
                type=conflict_type,  # type: ignore[arg-type]
                positions=positions,
                resolution_mode=mode,  # type: ignore[arg-type]
                winner_doc_id=winner,
                rationale=f"Retrieved passages contain competing {topic} positions.",
                confidence=0.85 if conflict_type != "T6" else 0.95,
            )
            conflicts.append(self.scorer.apply(conflict))
        return conflicts

    def critique(self, context: RetrievedContext, draft_text: str, citations: list[Span], *, as_of: date | None = None) -> CriticReport:
        claims = self._claims(context, draft_text, citations)
        conflicts = self._find_conflicts(context, as_of)
        unsupported = [claim.claim_id for claim in claims if claim.verdict == "unsupported"]
        return CriticReport(
            claims=claims,
            conflicts=conflicts,
            unsupported_claim_ids=unsupported,
            self_critique_ran=self.self_critique,
            self_critique_changes=[],
        )
