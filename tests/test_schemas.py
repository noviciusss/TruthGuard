from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from truthguard.schemas import (
    Claim,
    Conflict,
    DocMeta,
    FinalAnswer,
    Span,
    TrustScore,
)


def make_meta() -> DocMeta:
    return DocMeta(
        doc_id="POL-v1",
        title="Aurelia Policy v1",
        doc_type="policy",
        version="1.0",
        effective_date=date(2024, 1, 1),
        issued_date=date(2023, 12, 1),
        authority_rank=4,
        metadata_source="provided",
        metadata_confidence=1.0,
    )


def test_span_and_document_schema_round_trip() -> None:
    span = Span(chunk_id="c1", char_start=0, char_end=12)
    meta = make_meta()
    answer = FinalAnswer(
        question="What is the waiting period?",
        answer_text="30 days [c1]",
        status="no_conflict",
        claims=[
            Claim(
                claim_id="claim-1",
                text="The waiting period is 30 days.",
                verdict="supported",
                supporting_spans=[span],
            )
        ],
        citations=[span],
    )
    assert answer.model_dump(mode="json")["claims"][0]["verdict"] == "supported"
    assert meta.doc_type == "policy"


def test_conflict_schema_includes_control_and_unanswerable_types() -> None:
    span = Span(chunk_id="c1", char_start=0, char_end=4)
    meta = make_meta()
    conflict = Conflict(
        conflict_id="conflict-1",
        type="T6",
        positions=[
            {"claim_text": "A", "doc_id": "POL-v1", "span": span, "doc_meta": meta}
        ],
        resolution_mode="abstain",
        confidence=0.9,
        trust_breakdown={
            "POL-v1": TrustScore(
                recency=0.5,
                authority=1.0,
                specificity=0.5,
                corroboration=0.0,
                metadata_confidence=1.0,
                total=0.65,
            )
        },
    )
    assert conflict.type == "T6"


def test_invalid_offsets_and_confidence_are_rejected() -> None:
    with pytest.raises(ValidationError):
        Span(chunk_id="c1", char_start=10, char_end=2)
    with pytest.raises(ValidationError):
        DocMeta(
            doc_id="bad",
            title="Bad",
            doc_type="policy",
            authority_rank=4,
            metadata_source="provided",
            metadata_confidence=1.5,
        )
