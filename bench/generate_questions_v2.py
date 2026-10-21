"""Append additive genuine-T6 v2 questions without rewriting v1 rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


CASES: list[dict[str, Any]] = [
    {"fact": "t6_room_rent_cap", "docs": ["CIR-2026-T6-ROOM-A", "CIR-2026-T6-ROOM-B"], "question": "Two same-date circulars disagree about the Standard inpatient room rent cap. Can the corpus establish which percentage applies?", "passage": "Room rent", "split": "dev"},
    {"fact": "t6_copay_rate", "docs": ["CIR-2026-T6-COPAY-A", "CIR-2026-T6-COPAY-B"], "question": "The same-date Standard plan circulars state different co-payment rates. Should the assistant choose 15% or 25%?", "passage": "Co-payment", "split": "dev"},
    {"fact": "t6_grievance_response_window", "docs": ["CIR-2026-T6-GRV-A", "CIR-2026-T6-GRV-B"], "question": "Which grievance response window is current when the two same-authority circulars effective together disagree?", "passage": "Grievances", "split": "dev"},
    {"fact": "t6_claim_filing_deadline", "docs": ["CIR-2026-T6-CLAIM-A", "CIR-2026-T6-CLAIM-B"], "question": "Two circulars issued together give different claim filing deadlines after discharge. What deadline governs?", "passage": "Claims", "split": "dev"},
    {"fact": "t6_room_rent_cap", "docs": ["CIR-2026-T6-ROOM-A", "CIR-2026-T6-ROOM-B"], "question": "For a Standard inpatient room, the evidence gives two different caps effective on the same date. Is either cap authoritative?", "passage": "Room rent", "split": "test"},
    {"fact": "t6_copay_rate", "docs": ["CIR-2026-T6-COPAY-A", "CIR-2026-T6-COPAY-B"], "question": "Can a member be told the Standard co-payment rate when two same-authority same-day circulars publish conflicting percentages?", "passage": "Co-payment", "split": "test"},
    {"fact": "t6_grievance_response_window", "docs": ["CIR-2026-T6-GRV-A", "CIR-2026-T6-GRV-B"], "question": "The two circulars in force on the same date disagree on how long a grievance response may take. Which one should be used?", "passage": "Grievances", "split": "test"},
    {"fact": "t6_claim_filing_deadline", "docs": ["CIR-2026-T6-CLAIM-A", "CIR-2026-T6-CLAIM-B"], "question": "A Standard reimbursement claim has two different same-date filing windows in the corpus. Can the current deadline be resolved?", "passage": "Claims", "split": "test"},
    {"fact": "t6_cashless_preauth_window", "docs": ["CIR-2026-T6-PREAUTH-A", "CIR-2026-T6-PREAUTH-B"], "question": "How far before admission must cashless pre-authorization be requested when the same-date circulars disagree?", "passage": "Admissions", "split": "test"},
    {"fact": "t6_renewal_grace_period", "docs": ["CIR-2026-T6-RENEW-A", "CIR-2026-T6-RENEW-B"], "question": "Two equal-authority circulars give different renewal reinstatement grace periods effective together. Which period applies?", "passage": "Renewals", "split": "test"},
    {"fact": "t6_renewal_grace_period", "docs": ["CIR-2026-T6-RENEW-A", "CIR-2026-T6-RENEW-B"], "question": "A member finds conflicting same-day renewal reinstatement rules with no later amendment. What can the assistant conclude?", "passage": "Renewals", "split": "wild"},
    {"fact": "t6_copay_rate", "docs": ["CIR-2026-T6-COPAY-A", "CIR-2026-T6-COPAY-B"], "question": "The Standard plan's co-payment percentage differs between two circulars released for the same effective date. Is the disagreement resolvable from this corpus?", "passage": "Co-payment", "split": "wild"},
]


def _row(case: dict[str, Any], index: int) -> dict[str, Any]:
    qid = f"v2-t6-{index:03d}" if case["split"] != "wild" else f"v2-wild-t6-{index:03d}"
    row = {
        "qid": qid,
        "question": case["question"],
        "type": "T6",
        "gold_status": "abstained",
        "gold_answer": None,
        "gold_winner_doc": None,
        "gold_conflicting_docs": case["docs"],
        "gold_claims": [],
        "gold_fact_id": case["fact"],
        "source_passages": [f"{doc}#Operational rules" for doc in case["docs"]],
        "hand_verified": False,
        "multi_hop": False,
        "paraphrase_group": f"{case['fact']}-group",
    }
    if case["split"] != "wild":
        row["split"] = case["split"]
    return row


def generate_v2_questions(base_path: Path, output_path: Path, wild_path: Path, wild_output_path: Path) -> tuple[list[dict], list[dict]]:
    base_rows = [json.loads(line) for line in base_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    base_wild = [json.loads(line) for line in wild_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    additions = [_row(case, index) for index, case in enumerate(CASES, 1)]
    main_additions = [row for row in additions if row.get("split") in {"dev", "test"}]
    wild_additions = [row for row in additions if "split" not in row]
    if len(main_rows := base_rows) != 180 or len(base_wild) != 20:
        raise ValueError(f"Expected v1 180/20 rows, got {len(main_rows)}/{len(base_wild)}")
    main = base_rows + main_additions
    wild = base_wild + wild_additions
    if len(main) != 190 or len(wild) != 22:
        raise AssertionError("unexpected v2 row count")
    if sum(row["split"] == "dev" and row["type"] == "T6" for row in main) != 4:
        raise AssertionError("v2 needs four DEV T6 rows")
    if sum(row["split"] == "test" and row["type"] == "T6" for row in main) != 6:
        raise AssertionError("v2 needs six TEST T6 rows")
    for rows in (main, wild):
        if len({row["qid"] for row in rows}) != len(rows):
            raise AssertionError("v2 qids are not unique")
    output_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in main), encoding="utf-8")
    wild_output_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in wild), encoding="utf-8")
    return main, wild


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=ROOT / "data/benchmark/questions.jsonl")
    parser.add_argument("--wild", type=Path, default=ROOT / "data/benchmark/wild.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "data/benchmark/questions_v2.jsonl")
    parser.add_argument("--wild-output", type=Path, default=ROOT / "data/benchmark/wild_v2.jsonl")
    args = parser.parse_args()
    main_rows, wild_rows = generate_v2_questions(args.base, args.output, args.wild, args.wild_output)
    print(f"Wrote {len(main_rows)} v2 main and {len(wild_rows)} v2 wild rows")


if __name__ == "__main__":
    main()
