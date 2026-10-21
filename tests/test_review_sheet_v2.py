"""Checks for the v2 human-review artifact."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_v2_review_sheet_has_required_strata_and_t6_evidence():
    with (ROOT / "reports/review_sheet.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 30
    assert Counter(row["gold_type"] for row in rows) == Counter({"T1": 4, "T2": 4, "T3": 4, "T4": 4, "T5": 4, "T6": 4, "T0": 3, "T7": 3})
    t6 = [row for row in rows if row["gold_type"] == "T6"]
    assert all(row["qid"].startswith("v2-t6-") for row in t6)
    for row in t6:
        docs = json.loads(row["gold_conflicting_docs"])
        passages = json.loads(row["gold_justifying_passages"])
        assert {item["doc_id"] for item in docs} == {item["doc_id"] for item in passages}
        assert all("%" in item["text"] or " days" in item["text"] or " hours" in item["text"] for item in passages)
