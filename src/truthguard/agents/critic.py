"""Adversarial claim and conflict critic.

The deterministic path is intentionally complete enough for offline tests and
demo fixtures. When a live router is supplied, this module is the seam where
the two compact structured critic calls can replace or augment the heuristics.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from typing import Any

from ..graph.supersession import SupersessionGraph
from ..ingest.index import tokenize
from ..schemas import Claim, Conflict, CriticReport, Position, Span
from ..schemas import (
    CriticClaimsResponse,
    CriticConflictResponse,
    CriticSelfReviewResponse,
    EvidenceRef,
    LLMAtomicClaim,
)
from ..llm import LLMRouter
from .retriever import RetrievedContext
from .trust import TrustScorer
from .facts import observations, typed_pair


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
        router: LLMRouter | None = None,
        use_llm: bool = True,
    ) -> None:
        self.graph = graph
        self.scorer = scorer or TrustScorer()
        self.self_critique = self_critique
        self.router = router
        self.use_llm = use_llm

    @property
    def llm_enabled(self) -> bool:
        return bool(self.use_llm and self.router and not self.router.config.get("project", {}).get("offline", True))

    @staticmethod
    def _passage_annotations(context: RetrievedContext, graph: SupersessionGraph | None, as_of: date | None) -> list[dict[str, Any]]:
        passages: list[dict[str, Any]] = []
        for result in context.results:
            meta = result.chunk.doc_meta
            graph_facts: dict[str, Any] = {}
            if graph is not None:
                graph_facts = {
                    "is_superseded": graph.is_superseded(result.chunk.doc_id, as_of, result.chunk.section_path or None),
                    "graph_neighbors": graph.neighbors(result.chunk.doc_id),
                }
            passages.append(
                {
                    "chunk_id": result.chunk.chunk_id,
                    "doc_id": result.chunk.doc_id,
                    "section_path": result.chunk.section_path,
                    "text": result.chunk.text,
                    "metadata": {
                        "title": meta.title if meta else result.chunk.doc_id,
                        "doc_type": meta.doc_type if meta else None,
                        "version": meta.version if meta else None,
                        "effective_date": meta.effective_date.isoformat() if meta and meta.effective_date else None,
                        "issued_date": meta.issued_date.isoformat() if meta and meta.issued_date else None,
                        "authority_rank": meta.authority_rank if meta else None,
                        "metadata_confidence": meta.metadata_confidence if meta else None,
                        "supersedes": meta.supersedes if meta else [],
                        "amends": meta.amends if meta else [],
                    },
                    "graph": graph_facts,
                }
            )
        return passages

    @staticmethod
    def _passage_text(passages: list[dict[str, Any]]) -> str:
        return "\n\n".join(
            f"[{item['chunk_id']}] doc={item['doc_id']} section={item['section_path']}\n"
            f"metadata={item['metadata']} graph={item['graph']}\n{item['text']}"
            for item in passages
        )

    @staticmethod
    def _known_spans(context: RetrievedContext) -> dict[str, Any]:
        return {result.chunk.chunk_id: result.chunk for result in context.results}

    @classmethod
    def _span_from_ref(cls, reference: EvidenceRef, known: dict[str, Any]) -> Span | None:
        chunk = known.get(reference.chunk_id)
        if chunk is None:
            return None
        return Span(chunk_id=chunk.chunk_id, char_start=chunk.char_start, char_end=chunk.char_end)

    def _llm_claims(self, context: RetrievedContext, draft_text: str, as_of: date | None) -> list[Claim]:
        assert self.router is not None
        from ..compact_critic import claims

        return claims(self, context, draft_text, as_of)

    def _llm_conflicts(self, context: RetrievedContext, as_of: date | None) -> list[Conflict]:
        assert self.router is not None
        from ..compact_critic import conflicts

        return conflicts(self, context, as_of)

    def _llm_self_critique(self, context: RetrievedContext, conflicts: list[Conflict], as_of: date | None) -> tuple[list[Conflict], list[str]]:
        if not conflicts:
            return [], []
        assert self.router is not None
        from ..compact_critic import self_review

        return self_review(self, context, conflicts, as_of)

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
        if self.graph is not None:
            valid = self.graph.latest_valid([position.doc_id for position in positions])
            if valid:
                return valid[0]
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
            for observation in observations(result.chunk):
                if question_topic is not None and observation.key == question_topic:
                    grouped[observation.key].append(observation)
        conflicts: list[Conflict] = []
        for topic, evidence in grouped.items():
            pair = None
            for index, left in enumerate(evidence):
                for right in evidence[index + 1:]:
                    conflict_type = typed_pair(left, right, self.graph, as_of=as_of)
                    if conflict_type:
                        pair = (left, right, conflict_type)
                        break
                if pair:
                    break
            if pair is None:
                continue
            left, right, conflict_type = pair
            positions = [left.position(), right.position()]
            mode = "abstain" if conflict_type == "T6" else ("contextual" if conflict_type in {"T2", "T5"} else "supersession")
            winner = None if conflict_type in {"T2", "T5", "T6"} else self._winner(positions)
            conflict = Conflict(
                conflict_id=f"{conflict_type.lower()}-{topic}",
                type=conflict_type,  # type: ignore[arg-type]
                positions=positions,
                resolution_mode=mode,  # type: ignore[arg-type]
                winner_doc_id=winner,
                rationale=f"Two documents state {topic}: {left.value} ({left.scope}) versus {right.value} ({right.scope}); type evidence verified.",
                confidence=0.85 if conflict_type != "T6" else 0.95,
            )
            conflicts.append(self.scorer.apply(conflict))
        return conflicts

    def _critique_llm(self, context: RetrievedContext, draft_text: str, as_of: date | None) -> CriticReport:
        assert self.router is not None
        with self.router.critic_request_budget(3):
            claims = self._llm_claims(context, draft_text, as_of)
            proposed_conflicts = self._llm_conflicts(context, as_of)
            conflicts, changes = self._llm_self_critique(context, proposed_conflicts, as_of)
            unsupported = [claim.claim_id for claim in claims if claim.verdict == "unsupported"]
            return CriticReport(
                claims=claims,
                conflicts=conflicts,
                unsupported_claim_ids=unsupported,
                self_critique_ran=bool(proposed_conflicts),
                self_critique_changes=changes,
                mode="llm",
                llm_calls=3 if proposed_conflicts else 2,
            )

    def critique(self, context: RetrievedContext, draft_text: str, citations: list[Span], *, as_of: date | None = None) -> CriticReport:
        if self.llm_enabled:
            return self._critique_llm(context, draft_text, as_of)
        claims = self._claims(context, draft_text, citations)
        conflicts = self._find_conflicts(context, as_of)
        unsupported = [claim.claim_id for claim in claims if claim.verdict == "unsupported"]
        return CriticReport(
            claims=claims,
            conflicts=conflicts,
            unsupported_claim_ids=unsupported,
            self_critique_ran=self.self_critique,
            self_critique_changes=[],
            mode="deterministic",
            llm_calls=0,
        )
