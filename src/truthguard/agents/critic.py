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
        passages = self._passage_annotations(context, self.graph, as_of)
        prompt = (
            'Return ONLY one JSON object with exactly this top-level shape: '
            '{"claims":[{"claim_id":"claim-1","text":"...","verdict":"supported|contradicted|unsupported",'
            '"supporting_evidence":[{"chunk_id":"EXACT_CHUNK_ID","rationale":"..."}],'
            '"contradicting_evidence":[],"rationale":"..."}]}. '
            'Use exactly these keys: claims, claim_id, text, verdict, supporting_evidence, '
            'contradicting_evidence, rationale. Do not use wrapper keys or alternate names such as '
            'raw_claims, evaluated_claims, claim, claim_text, evidence, or support. Do not return markdown. '
            'Perform atomic claim decomposition and verify every claim against ALL supplied passages, not only cited '
            'passages. Evidence references must use exact chunk_id values.\n\n'
            f"QUESTION:\n{context.question}\n\nDRAFT:\n{draft_text}\n\nALL PASSAGES:\n{self._passage_text(passages)}"
        )
        response, _ = self.router.complete_json(
            "critic",
            [{"role": "system", "content": prompt}, {"role": "user", "content": "Return the JSON critic report."}],
            CriticClaimsResponse,
            stage="critic-call-a-claims",
        )
        known = self._known_spans(context)
        claims: list[Claim] = []
        for item in response.claims:
            supporting = [span for ref in item.supporting_evidence if (span := self._span_from_ref(ref, known))]
            contradicting = [span for ref in item.contradicting_evidence if (span := self._span_from_ref(ref, known))]
            claims.append(
                Claim(
                    claim_id=item.claim_id,
                    text=item.text,
                    verdict=item.verdict,
                    supporting_spans=supporting,
                    contradicting_spans=contradicting,
                )
            )
        return claims

    def _llm_conflicts(self, context: RetrievedContext, as_of: date | None) -> list[Conflict]:
        assert self.router is not None
        passages = self._passage_annotations(context, self.graph, as_of)
        clusters: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for passage in passages:
            clusters[_topic(passage["text"]) or "other"].append(passage)
        cluster_text = "\n\n".join(
            f"TOPIC={topic}\n{self._passage_text(items)}" for topic, items in clusters.items()
        )
        prompt = (
            'Return ONLY one JSON object with exactly this top-level shape: '
            '{"conflicts":[{"conflict_id":"t1-example","type":"T1|T2|T3|T4|T5|T6",'
            '"position_evidence":{"DOC-ID":[{"chunk_id":"EXACT_CHUNK_ID","rationale":"..."}]},'
            '"rationale":"...","confidence":0.0}]}. Use exactly these keys: conflicts, conflict_id, type, '
            'position_evidence, rationale, confidence. Do not use wrapper keys or alternate names such as '
            'findings, positions, evidence, conflict_type, or score. Do not return markdown. Compare passages '
            'pairwise within each topic cluster. Detect genuine contradictions, including implicit contradictions. '
            'Use the supplied graph and metadata annotations for staleness and supersession; do not invent dates or '
            'authority. Assign only T1, T2, T3, T4, T5, or T6. Each conflict must include at least two document '
            'positions, represented by exact chunk_id evidence references.\n\n'
            f"QUESTION:\n{context.question}\n\nCLUSTERED PASSAGES:\n{cluster_text}"
        )
        response, _ = self.router.complete_json(
            "critic",
            [{"role": "system", "content": prompt}, {"role": "user", "content": "Return the JSON conflict scan."}],
            CriticConflictResponse,
            stage="critic-call-b-conflicts",
        )
        known = self._known_spans(context)
        by_doc = {chunk.doc_id: chunk for chunk in known.values()}
        conflicts: list[Conflict] = []
        for finding in response.conflicts:
            positions: list[Position] = []
            for doc_id, refs in finding.position_evidence.items():
                for ref in refs:
                    chunk = known.get(ref.chunk_id)
                    if chunk is None or chunk.doc_id != doc_id:
                        continue
                    position = self._position(next(result for result in context.results if result.chunk.chunk_id == ref.chunk_id))
                    if all(existing.doc_id != position.doc_id for existing in positions):
                        positions.append(position)
                    break
            if len(positions) < 2:
                continue
            mode = "abstain" if finding.type == "T6" else ("contextual" if finding.type in {"T2", "T5"} else "supersession")
            winner = self._winner(positions)
            conflict = Conflict(
                conflict_id=finding.conflict_id,
                type=finding.type,
                positions=positions,
                resolution_mode=mode,
                winner_doc_id=None if mode != "supersession" else winner,
                rationale=finding.rationale,
                confidence=finding.confidence,
            )
            conflicts.append(self.scorer.apply(conflict))
        return conflicts

    def _llm_self_critique(self, context: RetrievedContext, conflicts: list[Conflict], as_of: date | None) -> tuple[list[Conflict], list[str]]:
        if not conflicts:
            return [], []
        assert self.router is not None
        prompt = (
            'Return ONLY one JSON object with exactly this top-level shape: '
            '{"keep_conflict_ids":["t1-example"],"dropped_conflict_ids":[],"changes":[]}. '
            'Use exactly these keys: keep_conflict_ids, dropped_conflict_ids, changes. Do not use wrapper keys or '
            'alternate names such as conflicts, kept, dropped, review, or notes. Do not return markdown. Attack each '
            'proposed conflict. Drop false positives caused by different scopes, unrelated topics, or a valid '
            'supersession relationship. Keep only conflict IDs that are genuine after reviewing the evidence.\n\n'
            f"QUESTION:\n{context.question}\n\nPROPOSED CONFLICTS:\n"
            + "\n".join(conflict.model_dump_json() for conflict in conflicts)
        )
        response, _ = self.router.complete_json(
            "critic",
            [{"role": "system", "content": prompt}, {"role": "user", "content": "Return the JSON self-critique."}],
            CriticSelfReviewResponse,
            stage="critic-call-c-self-critique",
        )
        keep = set(response.keep_conflict_ids)
        if not keep:
            return [], response.changes
        return [conflict for conflict in conflicts if conflict.conflict_id in keep], response.changes

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
        if self.llm_enabled:
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
