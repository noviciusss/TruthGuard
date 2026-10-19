"""Resumable local/live benchmark runner."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from truthguard.baselines import naive_rag, recency_rag, self_consistency_rag
from truthguard.pipeline import build_default_pipeline
from truthguard.schemas import BenchmarkQuestion, FinalAnswer


ROOT = Path(__file__).resolve().parents[1]


def load_questions(path: str | Path) -> list[BenchmarkQuestion]:
    return [
        BenchmarkQuestion.model_validate(json.loads(line))
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _system_answer(system: str, question: str, pipeline) -> FinalAnswer:
    if system == "truthguard":
        return pipeline.run(question)
    if system == "b0":
        return naive_rag(question, pipeline.retriever, pipeline.synthesizer)
    if system == "b1":
        return recency_rag(question, pipeline.retriever, pipeline.synthesizer)
    if system == "b2":
        return self_consistency_rag(question, pipeline.retriever, pipeline.synthesizer)
    raise ValueError(f"Unknown evaluation system: {system}")


def run_evaluation(
    questions_path: str | Path,
    output_path: str | Path,
    *,
    system: str = "truthguard",
    split: str = "dev",
    limit: int | None = None,
) -> list[dict[str, Any]]:
    questions = [question for question in load_questions(questions_path) if question.split == split]
    if limit is not None:
        questions = questions[:limit]
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed: set[str] = set()
    if output_path.exists():
        for line in output_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                if record.get("system") == system and record.get("split") == split:
                    completed.add(record["qid"])
    pipeline = build_default_pipeline()
    records: list[dict[str, Any]] = []
    with output_path.open("a", encoding="utf-8") as handle:
        for question in questions:
            if question.qid in completed:
                continue
            started = time.perf_counter()
            try:
                answer = _system_answer(system, question.question, pipeline)
                record = {
                    "qid": question.qid,
                    "system": system,
                    "split": split,
                    "latency_ms": (time.perf_counter() - started) * 1000,
                    "answer": answer.model_dump(mode="json"),
                }
            except Exception as exc:  # noqa: BLE001 - persist failure for resumability diagnostics
                record = {"qid": question.qid, "system": system, "split": split, "error": str(exc)}
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            handle.flush()
            records.append(record)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=ROOT / "data/benchmark/questions.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/eval_results.jsonl")
    parser.add_argument("--system", choices=["b0", "b1", "b2", "truthguard"], default="truthguard")
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    records = run_evaluation(args.questions, args.output, system=args.system, split=args.split, limit=args.limit)
    print(f"Wrote {len(records)} new {args.system} records to {args.output}")


if __name__ == "__main__":
    main()
