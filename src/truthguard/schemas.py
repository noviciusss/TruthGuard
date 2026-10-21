"""Typed data contracts shared by TruthGuard agents, API, and evaluation."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator


DocType = Literal["policy", "amendment", "circular", "faq", "manual", "notice"]
MetadataSource = Literal["provided", "inferred"]
ConflictType = Literal["T0", "T1", "T2", "T3", "T4", "T5", "T6", "T7"]
ResolutionMode = Literal["supersession", "contextual", "abstain"]
AnswerStatus = Literal["resolved", "conditional", "abstained", "no_conflict", "not_in_corpus"]
ClaimVerdict = Literal["supported", "contradicted", "unsupported"]


class TGModel(BaseModel):
    """Base model that rejects silently misspelled structured-output fields."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class DocMeta(TGModel):
    doc_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    doc_type: DocType
    version: str | None = None
    effective_date: date | None = None
    issued_date: date | None = None
    supersedes: list[str] = Field(default_factory=list)
    amends: list[tuple[str, str]] = Field(default_factory=list)
    authority_rank: int = Field(ge=0)
    metadata_source: MetadataSource
    metadata_confidence: float = Field(ge=0.0, le=1.0)


class Span(TGModel):
    chunk_id: str = Field(min_length=1)
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)

    @field_validator("char_end")
    @classmethod
    def end_is_not_before_start(cls, value: int, info) -> int:
        start = info.data.get("char_start")
        if start is not None and value < start:
            raise ValueError("char_end must be greater than or equal to char_start")
        return value


class Chunk(TGModel):
    chunk_id: str = Field(min_length=1)
    doc_id: str = Field(min_length=1)
    section_path: str = ""
    text: str = Field(min_length=1)
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)
    doc_meta: DocMeta | None = None

    @field_validator("char_end")
    @classmethod
    def chunk_end_is_not_before_start(cls, value: int, info) -> int:
        start = info.data.get("char_start")
        if start is not None and value < start:
            raise ValueError("char_end must be greater than or equal to char_start")
        return value


class Claim(TGModel):
    claim_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    verdict: ClaimVerdict
    supporting_spans: list[Span] = Field(default_factory=list)
    contradicting_spans: list[Span] = Field(default_factory=list)


class TrustScore(TGModel):
    recency: float = Field(ge=0.0, le=1.0)
    authority: float = Field(ge=0.0, le=1.0)
    specificity: float = Field(ge=0.0, le=1.0)
    corroboration: float = Field(ge=0.0, le=1.0)
    metadata_confidence: float = Field(ge=0.0, le=1.0)
    total: float = Field(ge=0.0, le=1.0)
    rationale: str = ""


class Position(TGModel):
    claim_text: str = Field(min_length=1)
    doc_id: str = Field(min_length=1)
    span: Span
    doc_meta: DocMeta


class Conflict(TGModel):
    conflict_id: str = Field(min_length=1)
    type: ConflictType
    positions: list[Position] = Field(default_factory=list)
    resolution_mode: ResolutionMode
    winner_doc_id: str | None = None
    rationale: str = ""
    trust_breakdown: dict[str, TrustScore] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)


class AgentStep(TGModel):
    agent: str = Field(min_length=1)
    action: str = Field(min_length=1)
    started_at: datetime
    finished_at: datetime | None = None
    status: Literal["started", "completed", "failed"] = "completed"
    input_summary: str = ""
    output_summary: str = ""
    error: str | None = None


class FinalAnswer(TGModel):
    question: str = Field(min_length=1)
    answer_text: str
    status: AnswerStatus
    claims: list[Claim] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    citations: list[Span] = Field(default_factory=list)
    trace: list[AgentStep] = Field(default_factory=list)


class DraftAnswer(TGModel):
    answer_text: str
    citations: list[Span | str] = Field(default_factory=list)


class BenchmarkQuestion(TGModel):
    qid: str = Field(min_length=1)
    question: str = Field(min_length=1)
    type: ConflictType
    gold_status: AnswerStatus
    gold_answer: str | None = None
    gold_winner_doc: str | None = None
    gold_conflicting_docs: list[str] = Field(default_factory=list)
    gold_claims: list[str] = Field(default_factory=list)
    as_of_date: date | None = None
    split: Literal["dev", "test"] = "dev"
    hand_verified: bool = False
    multi_hop: bool = False
    paraphrase_group: str | None = None
    source_passages: list[str] = Field(default_factory=list)


class ReformulationResponse(TGModel):
    topic: str = ""
    queries: list[str] = Field(default_factory=list, max_length=3)


class CriticReport(TGModel):
    claims: list[Claim] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    unsupported_claim_ids: list[str] = Field(default_factory=list)
    self_critique_ran: bool = False
    self_critique_changes: list[str] = Field(default_factory=list)
    mode: Literal["deterministic", "llm"] = "deterministic"
    llm_calls: int = Field(default=0, ge=0, le=3)


class EvidenceRef(TGModel):
    chunk_id: str = Field(min_length=1)
    rationale: str = ""


class LLMAtomicClaim(TGModel):
    claim_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    verdict: ClaimVerdict
    supporting_evidence: list[EvidenceRef] = Field(default_factory=list)
    contradicting_evidence: list[EvidenceRef] = Field(default_factory=list)
    rationale: str = ""


class CriticClaimsResponse(TGModel):
    claims: list[LLMAtomicClaim] = Field(default_factory=list)


class LLMConflictFinding(TGModel):
    conflict_id: str = Field(min_length=1)
    type: Literal["T1", "T2", "T3", "T4", "T5", "T6"]
    position_evidence: dict[str, list[EvidenceRef]] = Field(default_factory=dict)
    rationale: str = ""
    confidence: float = Field(ge=0.0, le=1.0)


class CriticConflictResponse(TGModel):
    conflicts: list[LLMConflictFinding] = Field(default_factory=list)


class CriticSelfReviewResponse(TGModel):
    keep_conflict_ids: list[str] = Field(default_factory=list)
    dropped_conflict_ids: list[str] = Field(default_factory=list)
    changes: list[str] = Field(default_factory=list)


class CompactRationale(TGModel):
    r: str = Field(default="", max_length=160)

    @field_validator("r")
    @classmethod
    def one_line(cls, value: str) -> str:
        if any(character in value for character in "\r\n\u2028\u2029"):
            raise ValueError("rationale must be one short line")
        return value


class CompactClaim(CompactRationale):
    i: str = Field(pattern=r"^c[1-9][0-9]*$")
    v: Literal["s", "c", "u"]
    s: list[str] = Field(default_factory=list)
    x: list[str] = Field(default_factory=list)
    a: int = Field(default=0, ge=0)
    b: int | None = Field(default=None, ge=1)


class CompactClaimsResponse(TGModel):
    c: list[CompactClaim]

    @model_validator(mode="after")
    def references(self, info: ValidationInfo) -> CompactClaimsResponse:
        context = info.context or {}
        sources, passages = context.get("claims", {}), context.get("passages", {})
        seen: set[tuple[str, int, int]] = set()
        for claim in self.c:
            if claim.i not in sources:
                raise ValueError("unknown local claim ID")
            end = claim.b if claim.b is not None else len(sources[claim.i])
            if not 0 <= claim.a < end <= len(sources[claim.i]):
                raise ValueError("invalid claim source offsets")
            if not sources[claim.i][claim.a:end].strip():
                raise ValueError("empty claim source span")
            key = (claim.i, claim.a, end)
            if key in seen:
                raise ValueError("duplicate claim source span")
            seen.add(key)
            for refs in (claim.s, claim.x):
                if len(refs) != len(set(refs)) or any(ref not in passages for ref in refs):
                    raise ValueError("unknown or duplicate passage ID")
            if (claim.v == "s" and not claim.s) or (claim.v == "c" and not claim.x):
                raise ValueError("verdict requires matching evidence")
        if {claim.i for claim in self.c} != set(sources):
            raise ValueError("every draft unit must be evaluated")
        return self


class CompactConflict(CompactRationale):
    i: str = Field(pattern=r"^f[1-9][0-9]*$")
    t: Literal["T1", "T2", "T3", "T4", "T5", "T6"]
    p: list[str] = Field(min_length=2)
    c: float = Field(ge=0.0, le=1.0)


class CompactConflictsResponse(TGModel):
    f: list[CompactConflict]

    @model_validator(mode="after")
    def references(self, info: ValidationInfo) -> CompactConflictsResponse:
        passages = (info.context or {}).get("passages", {})
        if len({finding.i for finding in self.f}) != len(self.f):
            raise ValueError("duplicate conflict ID")
        for finding in self.f:
            if len(set(finding.p)) != len(finding.p) or any(ref not in passages for ref in finding.p):
                raise ValueError("unknown or duplicate passage ID")
            if len({passages[ref] for ref in finding.p}) < 2:
                raise ValueError("conflict requires at least two distinct documents")
        return self


class CompactSelfReviewResponse(CompactRationale):
    k: list[str]
    d: list[str]

    @model_validator(mode="after")
    def references(self, info: ValidationInfo) -> CompactSelfReviewResponse:
        known = set((info.context or {}).get("conflicts", {}))
        if len(self.k + self.d) != len(set(self.k + self.d)) or set(self.k + self.d) != known:
            raise ValueError("keep/drop must partition the supplied conflict IDs exactly")
        return self


class LLMUsage(TGModel):
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)


class LLMResult(TGModel):
    payload: dict[str, Any]
    provider: str
    model: str
    cache_key: str
    cached: bool = False
    repaired: bool = False
    usage: LLMUsage = Field(default_factory=LLMUsage)
    latency_ms: float = Field(default=0.0, ge=0.0)
    attempt_ids: list[int] = Field(default_factory=list)
    requested_model: str | None = None


class CallRecord(TGModel):
    cache_key: str
    provider: str
    role: str
    stage: str
    model: str
    created_at: datetime
    cached: bool = False
    success: bool = True
    error: str | None = None
    usage: LLMUsage = Field(default_factory=LLMUsage)
    record_id: int | None = None
    physical_attempt: bool = True
    attempt_kind: str = "first_json"
    outcome: str = "valid"
    reserved_input_tokens: int = Field(default=0, ge=0)
    reserved_output_tokens: int = Field(default=0, ge=0)
    rate_limit_headers: dict[str, str] = Field(default_factory=dict)
    status_code: int | None = None
    requested_model: str | None = None
    accounting_version: int = 0
