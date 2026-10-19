from __future__ import annotations

import json
from pathlib import Path

from bench.generate_questions import build_questions, validate_questions, write_questions


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
