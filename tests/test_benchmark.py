from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from bench.generate_questions import build_questions, validate_questions, write_questions
from scripts.create_eval_subset import TARGET_COUNTS, create_subset


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
    assert {record["type"] for record in records} == {"T0", "T1", "T2", "T3", "T4", "T5", "T6", "T7"}


def test_wild_questions_validate_with_source_passages() -> None:
    wild_path = Path(__file__).resolve().parents[1] / "data/benchmark/wild.jsonl"
    records = [json.loads(line) for line in wild_path.read_text().splitlines()]
    assert len(records) == 20
    assert all(record["source_passages"] is not None for record in records)


def test_fixed_eval_subset_is_stratified_and_test_only(tmp_path) -> None:
    source = Path(__file__).resolve().parents[1] / "data/benchmark/questions.jsonl"
    output = tmp_path / "subset.jsonl"
    selected = create_subset(source, output)
    assert len(selected) == 40
    assert Counter(record["type"] for record in selected) == TARGET_COUNTS
    assert all(record["split"] == "test" for record in selected)
