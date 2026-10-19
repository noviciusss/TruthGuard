"""Generate the fixed, labeled TruthGuard benchmark from corpus manifest cases."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

from truthguard.schemas import BenchmarkQuestion


ROOT = Path(__file__).resolve().parents[1]


QUESTION_TEMPLATES: dict[str, list[str]] = {
    "T1": [
        "What is the hospitalization waiting period for the Standard plan?",
        "How many days must a Standard plan member wait for non-accidental hospitalization?",
        "Which waiting period applies now to a regular hospitalization?",
        "Has the hospitalization waiting period changed, and what is the current rule?",
    ],
    "T2": [
        "What co-payment applies to members on the Standard plan?",
        "Is the co-payment different for a member aged 60 or above?",
        "Explain the co-payment rule for standard and senior members.",
        "Which member population pays 20% instead of 10% co-payment?",
    ],
    "T3": [
        "How long after discharge can a reimbursement claim be submitted?",
        "What is the current deadline for filing a reimbursement claim?",
        "When does the claim submission window close after discharge?",
        "Has the reimbursement claim deadline changed from the old policy?",
    ],
    "T4": [
        "How many months is the pre-existing condition lookback period?",
        "What definition period applies before the policy starts?",
        "Which pre-existing condition lookback rule is current?",
        "Did the pre-existing condition lookback change from the FAQ?",
    ],
    "T5": [
        "Is prior authorization required for every hospital admission?",
        "Can an emergency admission proceed without prior approval?",
        "Explain pre-authorization for planned versus emergency admissions.",
        "What should a member do when an emergency admission happens without approval?",
    ],
    "T6": [
        "What is the annual hospitalization limit for the Aurelia Standard plan?",
        "How much annual hospitalization coverage does the Standard plan provide?",
        "Which annual limit should be used for the Standard plan?",
        "Can the conflicting annual limit circulars be reconciled?",
    ],
    "T0": [
        "How many days is the renewal grace period?",
        "What renewal grace period applies to active plans?",
        "When can a member complete a late renewal?",
        "Is the renewal grace period consistent across the current documents?",
    ],
    "T7": [
        "Does Aurelia cover hearing-aid batteries after a routine replacement?",
        "What is the policy for robotic home surgery equipment?",
        "How many days of coverage apply to an experimental gene therapy trial?",
        "Is there a benefit for underwater rehabilitation sessions?",
    ],
}


GOLD_BY_TYPE = {
    "T1": {"status": "resolved", "answer": "45 days", "winner": "AMD-2025-03", "docs": ["POL-2024-V1", "AMD-2025-03"], "claims": ["The current hospitalization waiting period is 45 days."]},
    "T2": {"status": "conditional", "answer": "10% for standard members; 20% for members aged 60 and above", "winner": None, "docs": ["CIR-2024-02", "POL-2024-V1"], "claims": ["Standard plan members pay 10% co-payment.", "Members aged 60 and above pay 20% co-payment."]},
    "T3": {"status": "resolved", "answer": "60 days after discharge", "winner": "AMD-2025-04", "docs": ["POL-2024-V1", "AMD-2025-04"], "claims": ["A reimbursement claim must be submitted within 60 days after discharge."]},
    "T4": {"status": "resolved", "answer": "48 months", "winner": "AMD-2025-05", "docs": ["FAQ-2024-02", "AMD-2025-05"], "claims": ["The pre-existing condition lookback period is 48 months."]},
    "T5": {"status": "conditional", "answer": "Planned admissions require prior approval; emergency admissions may proceed without it if notified within 24 hours", "winner": None, "docs": ["POL-2025-V2", "CIR-2025-06"], "claims": ["Planned admissions require pre-authorization.", "Emergency admissions may proceed without prior approval if Aurelia is notified within 24 hours."]},
    "T6": {"status": "abstained", "answer": None, "winner": None, "docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "claims": []},
    "T0": {"status": "no_conflict", "answer": "30 days", "winner": None, "docs": ["CIR-2024-01", "CIR-2025-10"], "claims": ["The renewal grace period is 30 days."]},
    "T7": {"status": "not_in_corpus", "answer": None, "winner": None, "docs": [], "claims": []},
}


def _build_type_questions(conflict_type: str, count: int) -> list[BenchmarkQuestion]:
    gold = GOLD_BY_TYPE[conflict_type]
    templates = QUESTION_TEMPLATES[conflict_type]
    result: list[BenchmarkQuestion] = []
    for index in range(count):
        template = templates[index % len(templates)]
        variant = index // len(templates)
        qid = f"{conflict_type.lower()}-{index + 1:03d}"
        result.append(
            BenchmarkQuestion(
                qid=qid,
                question=template if variant == 0 else f"{template} (case variant {variant + 1})",
                type=conflict_type,  # type: ignore[arg-type]
                gold_status=gold["status"],  # type: ignore[arg-type]
                gold_answer=gold["answer"],
                gold_winner_doc=gold["winner"],
                gold_conflicting_docs=gold["docs"],
                gold_claims=gold["claims"],
                hand_verified=False,
                multi_hop=False,
                paraphrase_group=f"{conflict_type}-group-{index % len(templates)}",
            )
        )
    return result


def build_questions(*, seed: int = 7) -> list[BenchmarkQuestion]:
    """Build exactly 180 questions with the specification's type distribution."""

    counts = {"T1": 24, "T2": 24, "T3": 24, "T4": 24, "T5": 24, "T6": 24, "T0": 20, "T7": 16}
    questions = [question for conflict_type, count in counts.items() for question in _build_type_questions(conflict_type, count)]
    random.Random(seed).shuffle(questions)
    for index, question in enumerate(questions):
        question.split = "dev" if index < 40 else "test"
        question.multi_hop = index < 36
    return questions


def validate_questions(questions: list[BenchmarkQuestion]) -> list[str]:
    errors: list[str] = []
    expected = {"T1": 24, "T2": 24, "T3": 24, "T4": 24, "T5": 24, "T6": 24, "T0": 20, "T7": 16}
    actual: dict[str, int] = {key: 0 for key in expected}
    for question in questions:
        actual[question.type] = actual.get(question.type, 0) + 1
    if len(questions) != 180:
        errors.append(f"expected 180 questions, got {len(questions)}")
    if actual != expected:
        errors.append(f"type counts differ: {actual}")
    if sum(question.split == "dev" for question in questions) != 40:
        errors.append("dev split must contain 40 questions")
    if sum(question.split == "test" for question in questions) != 140:
        errors.append("test split must contain 140 questions")
    if len({question.qid for question in questions}) != len(questions):
        errors.append("question IDs are not unique")
    if sum(question.multi_hop for question in questions) < 36:
        errors.append("multi-hop target should be approximately 20%")
    return errors


def write_questions(output_path: str | Path, *, seed: int = 7) -> list[BenchmarkQuestion]:
    questions = build_questions(seed=seed)
    errors = validate_questions(questions)
    if errors:
        raise ValueError("Benchmark validation failed: " + "; ".join(errors))
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(json.dumps(question.model_dump(mode="json"), sort_keys=True) + "\n" for question in questions),
        encoding="utf-8",
    )
    return questions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/benchmark/questions.jsonl")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    questions = write_questions(args.output, seed=args.seed)
    print(f"Wrote {len(questions)} questions to {args.output}")


if __name__ == "__main__":
    main()
