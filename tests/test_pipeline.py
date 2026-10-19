from __future__ import annotations

import pytest

from truthguard.pipeline import TruthGuardPipeline, build_default_pipeline


@pytest.fixture(scope="module")
def pipeline() -> TruthGuardPipeline:
    return build_default_pipeline()


@pytest.mark.parametrize(
    ("question", "status", "conflict_type"),
    [
        ("What is the hospitalization waiting period?", "resolved", "T1"),
        ("What co-payment applies to members on the Standard plan?", "conditional", "T2"),
        ("How long after discharge can a reimbursement claim be submitted?", "resolved", "T3"),
        ("How many months is the pre-existing condition lookback period?", "resolved", "T4"),
        ("Can an emergency admission proceed without prior approval?", "conditional", "T5"),
        ("What is the annual hospitalization limit for the Aurelia Standard plan?", "abstained", "T6"),
        ("How many days is the renewal grace period?", "no_conflict", None),
        ("Does Aurelia cover hearing-aid batteries after a routine replacement?", "not_in_corpus", None),
    ],
)
def test_pipeline_behaves_for_taxonomy_fixtures(pipeline, question, status, conflict_type) -> None:
    answer = pipeline.run(question)
    assert answer.status == status
    if conflict_type:
        assert any(conflict.type == conflict_type for conflict in answer.conflicts)
        assert all(conflict.trust_breakdown for conflict in answer.conflicts)
    assert answer.trace
    assert {step.agent for step in answer.trace} >= {"retriever", "synthesizer", "critic", "resolver"}
