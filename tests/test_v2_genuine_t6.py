"""Offline invariants for the additive genuine-T6 v2 fixture."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from scripts.audit_corpus_programmatic import run_audit


ROOT = Path(__file__).resolve().parents[1]


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_v2_is_additive_and_has_t6_across_six_fact_keys():
    v1 = read_rows(ROOT / "data/benchmark/questions.jsonl")
    v2 = read_rows(ROOT / "data/benchmark/questions_v2.jsonl")
    wild = read_rows(ROOT / "data/benchmark/wild_v2.jsonl")
    assert v2[: len(v1)] == v1
    assert len(v2) == 190
    assert len(wild) == 22
    t6 = [row for row in v2 + wild if row["type"] == "T6"]
    assert len(t6) == 12
    assert Counter(row.get("split", "wild") for row in t6) == Counter({"dev": 4, "test": 6, "wild": 2})
    assert len({row["gold_fact_id"] for row in t6}) == 6
    assert all(row["gold_status"] == "abstained" and row["gold_answer"] is None for row in t6)
    assert all(len(row["gold_conflicting_docs"]) == 2 for row in t6)


def test_v2_corpus_has_exact_same_date_authority_pairs_and_no_third_documents():
    manifest = json.loads((ROOT / "data/corpus_v2/corpus_manifest.json").read_text())
    t6 = [item for item in manifest["conflicts"] if item["type"] == "T6"]
    assert len(t6) == 6
    by_id = {item["doc_id"]: item for item in manifest["documents"]}
    for conflict in t6:
        left, right = (by_id[doc_id] for doc_id in conflict["documents"])
        left_meta, right_meta = left["expected_metadata"], right["expected_metadata"]
        assert left_meta["effective_date"] == right_meta["effective_date"]
        assert left_meta["issued_date"] == right_meta["issued_date"]
        assert left_meta["authority_rank"] == right_meta["authority_rank"] == 2
        assert not left_meta["supersedes"] and not right_meta["supersedes"]
        assert not left_meta["amends"] and not right_meta["amends"]
        assert manifest["fact_use_counts"][conflict["fact_id"]] == 2


def test_v2_programmatic_audit_passes_all_new_t6_mechanical_checks():
    report = run_audit(
        ROOT,
        corpus_rel="data/corpus_v2",
        facts_rel="data/factsheet/aurelia_facts_v2.yaml",
        question_files=("questions_v2.jsonl", "wild_v2.jsonl", "eval_subset_v2_40.jsonl"),
    )
    t6_records = [
        row
        for dataset in report["datasets"].values()
        for row in dataset["records"]
        if row["type"] == "T6"
    ]
    assert len(t6_records) == 18  # subset overlaps the six TEST rows
    assert all(row["status"] == "pass" for row in t6_records)
    for row in t6_records:
        names = {item["check"]: item["status"] for item in row["checks"]}
        assert names.get("t6_same_date_same_authority", names.get("t6_pair")) == "pass"
        assert names["t6_no_third_document"] == "pass"
        assert names["t6_global_abstention"] == "pass"
