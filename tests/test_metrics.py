from __future__ import annotations

from truthguard.schemas import BenchmarkQuestion, Claim, Conflict, FinalAnswer, Span
from bench.metrics import bootstrap_ci, evaluate_predictions, score_question


def make_gold(qid: str = "q1") -> BenchmarkQuestion:
    return BenchmarkQuestion(
        qid=qid,
        question="What is the current waiting period?",
        type="T1",
        gold_status="resolved",
        gold_answer="45 days",
        gold_winner_doc="AMD-2025-03",
        gold_conflicting_docs=["POL-2024-V1", "AMD-2025-03"],
        gold_claims=["The current waiting period is 45 days."],
    )


def make_prediction(qid: str = "q1") -> FinalAnswer:
    return FinalAnswer(
        question="What is the current waiting period?",
        answer_text="The current waiting period is 45 days.",
        status="resolved",
        claims=[
            Claim(
                claim_id="claim-1",
                text="The current waiting period is 45 days.",
                verdict="supported",
                supporting_spans=[Span(chunk_id="AMD-2025-03:c1", char_start=0, char_end=10)],
            )
        ],
        citations=[Span(chunk_id="AMD-2025-03:c1", char_start=0, char_end=10)],
        conflicts=[
            Conflict(
                conflict_id="t1",
                type="T1",
                resolution_mode="supersession",
                winner_doc_id="AMD-2025-03",
                confidence=0.9,
            )
        ],
    )


def test_question_metrics_and_aggregation() -> None:
    row = score_question(make_gold(), make_prediction())
    assert row["answer_accuracy"] == 1.0
    assert row["conflict_tp"] == 1.0
    assert row["winner_accuracy"] == 1.0
    report = evaluate_predictions([make_gold()], {"q1": make_prediction()}, bootstrap_samples=50)
    assert report["questions_scored"] == 1
    assert report["conflict_detection"]["f1"] == 1.0
    assert report["answer_accuracy"]["ci95"] == (1.0, 1.0)


def test_bootstrap_is_deterministic_and_bounded() -> None:
    first = bootstrap_ci([0.0, 1.0, 1.0, 0.0], samples=100, seed=11)
    second = bootstrap_ci([0.0, 1.0, 1.0, 0.0], samples=100, seed=11)
    assert first == second
    assert 0.0 <= first[0] <= first[1] <= 1.0
