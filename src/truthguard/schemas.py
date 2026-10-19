"""Typed data contracts shared by TruthGuard agents, API, and evaluation."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class ReformulationResponse(TGModel):
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
