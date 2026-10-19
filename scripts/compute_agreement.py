"""Compute agreement rates from a filled TruthGuard review sheet."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW_COLUMNS = (
    "reviewer_agrees_answer",
    "reviewer_agrees_type",
    "reviewer_agrees_docs",
)


def _value(raw: str) -> str:
    return raw.strip().lower()


def compute_agreement(path: str | Path) -> dict[str, object]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    result: dict[str, object] = {"rows": len(rows), "columns": {}}
    total_yes = 0
    total_answered = 0
    for column in REVIEW_COLUMNS:
        counts = {"yes": 0, "no": 0, "blank": 0, "other": 0}
        for row in rows:
            value = _value(row.get(column, ""))
            if value in {"yes", "y", "true", "1", "agree", "agrees"}:
                counts["yes"] += 1
            elif value in {"no", "n", "false", "0", "disagree", "disagrees"}:
                counts["no"] += 1
            elif not value:
                counts["blank"] += 1
            else:
                counts["other"] += 1
        answered = counts["yes"] + counts["no"]
        result["columns"][column] = {
            **counts,
            "answered": answered,
            "agreement_rate": counts["yes"] / answered if answered else None,
        }
        total_yes += counts["yes"]
        total_answered += answered
    result["overall"] = {
        "yes": total_yes,
        "answered": total_answered,
        "agreement_rate": total_yes / total_answered if total_answered else None,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=ROOT / "reports/review_sheet.csv")
    args = parser.parse_args()
    result = compute_agreement(args.csv)
    print(f"Rows: {result['rows']}")
    for column, values in result["columns"].items():
        rate = values["agreement_rate"]
        formatted = "pending" if rate is None else f"{rate:.1%}"
        print(f"{column}: {formatted} ({values['answered']} answered, {values['blank']} blank)")
    overall = result["overall"]["agreement_rate"]
    print(f"overall: {'pending' if overall is None else f'{overall:.1%}'}")


if __name__ == "__main__":
    main()
