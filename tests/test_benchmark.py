from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from bench.generate_questions import build_questions, validate_questions, write_questions
from bench.generate_questions import ANNUAL_GOLD, refresh_related


ROOT = Path(__file__).resolve().parents[1]
FIXED_QIDS = "t0-004 t0-012 t1-003 t1-011 t1-017 t1-019 t1-023 t1-024 t2-002 t2-004 t2-005 t2-017 t2-022 t2-024 t3-001 t3-002 t3-008 t3-013 t3-016 t3-018 t4-003 t4-005 t4-007 t4-008 t4-011 t4-013 t5-001 t5-004 t5-005 t5-015 t5-016 t5-020 t6-001 t6-008 t6-016 t6-018 t6-021 t6-023 t7-007 t7-011".split()


def test_benchmark_distribution_and_split() -> None:
    questions = build_questions()
    assert validate_questions(questions) == []
    assert len(questions) == 180
    assert sum(question.multi_hop for question in questions) == 36
    assert sum(question.split == "dev" for question in questions) == 40


def test_benchmark_jsonl_is_reproducible(tmp_path) -> None:
    first_path = tmp_path / "first.jsonl"
    second_path = tmp_path / "second.jsonl"
    write_questions(first_path)
    write_questions(second_path)
    assert first_path.read_text() == second_path.read_text()
    records = [json.loads(line) for line in first_path.read_text().splitlines()]
    assert len(records) == 180
    assert all(record["hand_verified"] is False for record in records)
    assert Counter(record["type"] for record in records) == {"T0": 20, "T1": 24, "T2": 24, "T3": 48, "T4": 24, "T5": 24, "T7": 16}
    assert first_path.read_bytes() == (ROOT / "data/benchmark/questions.jsonl").read_bytes()


def test_wild_questions_validate_with_source_passages() -> None:
    wild_path = Path(__file__).resolve().parents[1] / "data/benchmark/wild.jsonl"
    records = [json.loads(line) for line in wild_path.read_text().splitlines()]
    assert len(records) == 20
    assert all(record["source_passages"] is not None for record in records)


def test_fixed_eval_subset_preserves_qids_and_copies_revised_test_gold() -> None:
    selected = [json.loads(line) for line in (ROOT / "data/benchmark/eval_subset_40.jsonl").read_text().splitlines()]
    main = {row["qid"]: row for row in map(json.loads, (ROOT / "data/benchmark/questions.jsonl").read_text().splitlines())}
    assert len(selected) == 40
    assert [row["qid"] for row in selected] == FIXED_QIDS
    assert Counter(record["type"] for record in selected) == {"T0": 2, "T1": 6, "T2": 6, "T3": 12, "T4": 6, "T5": 6, "T7": 2}
    assert all(record["split"] == "test" for record in selected)
    assert all(record == main[record["qid"]] for record in selected)


def test_every_original_t6_is_adjudicated_and_related_refresh_is_idempotent(tmp_path) -> None:
    questions = build_questions()
    original_t6 = [q for q in questions if q.qid.startswith("t6-")]
    assert {q.qid for q in original_t6} == {f"t6-{index:03}" for index in range(1, 25)}
    for q in original_t6:
        assert {key: q.model_dump()[key] for key in ANNUAL_GOLD} == ANNUAL_GOLD
    for name in ("questions.jsonl", "wild.jsonl", "eval_subset_40.jsonl"):
        (tmp_path / name).write_bytes((ROOT / "data/benchmark" / name).read_bytes())
    ledger = tmp_path / "gold_changes.md"
    refresh_related(tmp_path / "questions.jsonl", ledger)
    for path in tmp_path.glob("*.jsonl"):
        assert path.read_bytes() == (ROOT / "data/benchmark" / path.name).read_bytes()
    assert ledger.read_bytes() == (ROOT / "reports/gold_changes.md").read_bytes()
    for q in original_t6:
        assert f"questions.jsonl / {q.qid}" in ledger.read_text()
    assert "wild.jsonl / wild-011" in ledger.read_text()
    assert "wild.jsonl / wild-012" in ledger.read_text()
