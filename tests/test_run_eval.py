from __future__ import annotations

import json

from bench.generate_questions import write_questions
from bench.run_eval import run_evaluation


def test_evaluation_runner_is_resumable(tmp_path) -> None:
    questions = tmp_path / "questions.jsonl"
    results = tmp_path / "results.jsonl"
    write_questions(questions)
    first = run_evaluation(questions, results, system="truthguard", split="dev", limit=2)
    second = run_evaluation(questions, results, system="truthguard", split="dev", limit=2)
    assert len(first) == 2
    assert second == []
    assert len(results.read_text().splitlines()) == 2
    records = [json.loads(line) for line in results.read_text().splitlines()]
    assert all("answer" in record for record in records)
