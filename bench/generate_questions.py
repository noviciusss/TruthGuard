"""Generate the fixed, labeled TruthGuard benchmark from corpus manifest cases."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

from truthguard.schemas import BenchmarkQuestion


ROOT = Path(__file__).resolve().parents[1]

# Qids and shuffle buckets retain the original design. Only adjudicated labels
# change: annual limits are a resolvable numeric conflict in the complete corpus.
ANNUAL_GOLD = {
    "type": "T3", "gold_status": "resolved",
    "gold_answer": "600000 currency units per policy year",
    "gold_winner_doc": "POL-2026-V3",
    "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"],
    "gold_claims": ["The current Aurelia Standard plan annual hospitalization limit is 600000 currency units per policy year.",
                    "NOTICE-2025-11 filed 500000 currency units; the higher-authority policy effective 2026-01-01 governs the current limit."],
    "source_passages": ["CIR-2025-08-A#Annual limit", "CIR-2025-08-B#Annual limit", "NOTICE-2025-11#Filing",
                        "NOTICE-2025-11#Operational rules", "POL-2026-V3#Operational rules"],
}


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
    """Retain all original 180 qids/splits, then apply whole-corpus adjudication."""

    counts = {"T1": 24, "T2": 24, "T3": 24, "T4": 24, "T5": 24, "T6": 24, "T0": 20, "T7": 16}
    questions = [question for conflict_type, count in counts.items() for question in _build_type_questions(conflict_type, count)]
    random.Random(seed).shuffle(questions)
    for index, question in enumerate(questions):
        question.split = "dev" if index < 40 else "test"
        question.multi_hop = index < 36
        if question.qid.startswith("t6-"):
            for field, value in ANNUAL_GOLD.items():
                setattr(question, field, value)
    return questions


def validate_questions(questions: list[BenchmarkQuestion]) -> list[str]:
    errors: list[str] = []
    expected = {"T1": 24, "T2": 24, "T3": 48, "T4": 24, "T5": 24, "T6": 0, "T0": 20, "T7": 16}
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
        "".join(json.dumps(serialized_question(question), sort_keys=True) + "\n" for question in questions),
        encoding="utf-8",
    )
    return questions


def serialized_question(question: BenchmarkQuestion) -> dict[str, Any]:
    row = question.model_dump(mode="json")
    if not row["source_passages"]:
        row.pop("source_passages")  # Preserve original unrelated row serialization.
    return row


def refresh_related(main_path: Path, report_path: Path) -> None:
    """Refresh gold by qid, preserving the existing subset membership and order.

    This is label synchronization, not selection or benchmark freezing. Wild
    phrasing is retained except for the independently identified false premise.
    """
    main = [json.loads(line) for line in main_path.read_text().splitlines() if line.strip()]
    by_id = {row["qid"]: row for row in main}
    datasets = {"questions.jsonl": main}
    for filename in ("wild.jsonl", "eval_subset_40.jsonl"):
        path = main_path.parent / filename
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        if filename == "eval_subset_40.jsonl":
            if len(rows) != 40 or len({row["qid"] for row in rows}) != 40:
                raise ValueError("Expected the existing 40 distinct subset qids; no resampling permitted")
            rows = [by_id[row["qid"]] for row in rows]
            if any(row["split"] != "test" for row in rows):
                raise ValueError("Existing fixed subset must remain TEST only")
        else:
            for row in rows:
                if row["qid"] in {"wild-011", "wild-012"}:
                    row.update(ANNUAL_GOLD)
                if row["qid"] == "wild-011":
                    row["question"] = "Two same-day circulars from the same authority publish different annual limits for Standard. Considering the complete corpus, including the later filing notice and current policy, which annual limit governs now?"
        path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
        datasets[filename] = rows
    report_path.write_text(gold_changes(datasets), encoding="utf-8")


def gold_changes(datasets: dict[str, list[dict]]) -> str:
    lines = ["# Corpus and gold adjudication (offline)", "",
             "## Decision and provenance", "",
             "All 24 original main T6 qids and both original wild T6 qids were re-adjudicated against all 35 documents. "
             "No rows were dropped: main remains 180 = 40 DEV + 140 TEST. The fixed-40 retains exactly its original qids and order, copying complete revised rows from main. No benchmark freeze was performed.", "",
             "- The annual-limit history contains simultaneous **500000 and 600000**, both effective **2025-08-01**, at authority **2** "
             "(`CIR-2025-08-A` and `CIR-2025-08-B`). There is **no unique in-force historical value before the notice**. YAML/list order is not precedence.",
             "- Explicit owner adjudication: **NOTICE-2025-11 uses fallback 500000 in both Filing and Operational rules**, effective **2025-11-01**, issued **2025-11-01**, authority **3**. "
             "This resolves the generated internal contradiction; it is not an inferred unique August winner.",
             "- The current policy **POL-2026-V3** already states **600000 currency units per policy year**, effective **2026-01-01**, issued **2025-12-01**, authority **4**. "
             "It governs current whole-corpus questions. Relabel **T3 (numeric conflict), resolved, supersession**, winner **POL-2026-V3**. "
             "Resolution mode lives in the corpus manifest (`correct_mode`); the existing question schema represents it with `gold_status=resolved` plus winner/claims, and has no mode field.",
             "- `wild-011` originally asserted there was no later notice breaking the tie. Its wording now asks about the complete corpus and current limit; retaining that false premise would be misleading. Other annual questions retain their wording.",
             "- Generation now rejects ambiguous coeffective values rather than silently choosing the last entry. "
             "Existing age/plan-specific co-payment and room-rent schedules retain both explicitly scoped values; this also restores the omitted Standard room-rent schedule in CIR-2024-03/FAQ-2025-01 and Standard co-payment in FAQ-2025-01. No new fact or document was invented.", "",
             "## Existing-fact search and semantic blocker", "",
             "**0 defensible current whole-corpus T6 examples found; the target of at least 12 genuine TEST T6 examples cannot be met with existing evidence.** "
             "The historical August tie is real but is not a current whole-corpus tie. No queries were restricted to two circulars, time-shifted, or replaced by fabricated facts to retain T6. "
             "The original DEV/TEST assignments remain unchanged; all 24 original T6 labels become T3.", "",
             "| Existing fact | Whole-corpus conflict review |", "|---|---|",
             "| waiting_period | Historical 30/45 days; amendment and later policy state 45, no unresolved top tie. |",
             "| copay | 10% standard / 20% senior are distinct age scopes, not competing same-scope values. |",
             "| claim_deadline | Historical 30/60 days; amendment and later policy give 60. |",
             "| pre_existing_lookback | Historical 36/48 months; amendment and later policy give 48. |",
             "| preauthorization | Planned prior approval and emergency 24-hour notification are contextual scopes. |",
             "| room_rent | 1% Standard / 2% Premium are distinct plan scopes. |",
             "| renewal_grace | All existing positions agree on 30 days. |",
             "| grievance_timeline | Acknowledgement 3 business days and resolution 30 days are distinct phases. |",
             "| network_cashless | Active network and approval; no competing eligibility rule found. |",
             "| ambulance_limit | All existing positions give 10000 per hospitalization. |",
             "| annual_limit | August 500000/600000 tie; November fallback 500000; current authority-4 policy 600000. |",
             "| telemedicine | Existing positions agree on four consultations per year. |",
             "| maternity | 24-month history is not asserted in existing corpus; Premium positions give 18 months. |",
             "| exclusions | Cosmetic exclusion consistently retains medically necessary post-accident exception. |", "",
             "This is evidence-based adjudication, not a claim that lexical scans prove semantic completeness. "
             "Missing cited headings and composed answers remain programmatically unverifiable; T7 semantic absence remains unverifiable even with no lexical hits. "
             "The audit inventories bounded same-fact/same-scope quantities, including dates and authority. Non-numeric semantics require review.", "",
             "## Every changed qid (original → revised)", "",
             "Old and new snapshots include type, status, answer, winner, documents, claims and source passages. "
             "Mode for every entry: **abstain → supersession**. Dataset occurrences are listed separately, including the overlapping fixed subset. "
             "`hand_verified` remains unchanged; this task does not claim an independent human review.", ""]
    for name, rows in datasets.items():
        for row in sorted(rows, key=lambda item: item["qid"]):
            if not (row["qid"].startswith("t6-") or row["qid"] in {"wild-011", "wild-012"}):
                continue
            old = {"type": "T6", "gold_status": "abstained", "gold_answer": None, "gold_winner_doc": None,
                   "gold_conflicting_docs": ["CIR-2025-08-A", "CIR-2025-08-B"], "gold_claims": []}
            if name == "wild.jsonl":
                if row["qid"] == "wild-012":
                    old["gold_conflicting_docs"].append("NOTICE-2025-11")
                old["source_passages"] = [f"{doc}#" + ("Filing" if doc.startswith("NOTICE") else "Annual limit") for doc in old["gold_conflicting_docs"]]
            new = {field: row[field] for field in ANNUAL_GOLD}
            lines += [f"### {name} / {row['qid']} ({row.get('split', 'wild')})", "",
                      "- Old: `" + json.dumps(old, sort_keys=True) + "`",
                      "- New: `" + json.dumps(new, sort_keys=True) + "`", ""]
    lines += ["## Reproduce without resampling or freezing", "", "```bash",
              "TRUTHGUARD_OFFLINE=true PYTHONPATH=src .venv/bin/python -m bench.generate_corpus",
              "TRUTHGUARD_OFFLINE=true PYTHONPATH=src .venv/bin/python -m bench.generate_questions --refresh-related",
              "TRUTHGUARD_OFFLINE=true .venv/bin/python scripts/audit_corpus_programmatic.py",
              "TRUTHGUARD_OFFLINE=true PYTHONPATH=.:src .venv/bin/python -m pytest -q tests/test_corpus.py tests/test_benchmark.py tests/test_programmatic_audit.py", "```", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/benchmark/questions.jsonl")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--refresh-related", action="store_true", help="Synchronize existing fixed-40/wild gold by qid and write the per-qid change ledger; never resample")
    args = parser.parse_args()
    questions = write_questions(args.output, seed=args.seed)
    if args.refresh_related:
        refresh_related(args.output, ROOT / "reports/gold_changes.md")
    print(f"Wrote {len(questions)} questions to {args.output}")


if __name__ == "__main__":
    main()
