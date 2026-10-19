"""Run named TruthGuard component ablations with resumable JSONL output."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from truthguard.baselines import naive_rag
from truthguard.pipeline import build_default_pipeline

from .run_eval import load_questions


ROOT = Path(__file__).resolve().parents[1]
ABLATION_VARIANTS = (
    "no_critic",
    "no_supersession_graph",
    "no_metadata_inference",
    "no_self_critique",
    "no_conflict_seeking_expansion",
    "same_model_synth_critic",
    "no_trust_scoring",
)


def run_ablations(
    questions_path: str | Path,
    output_path: str | Path,
    *,
    split: str = "test",
    limit: int = 60,
) -> list[dict]:
    questions = [question for question in load_questions(questions_path) if question.split == split][:limit]
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed: set[tuple[str, str]] = set()
    if output_path.exists():
        for line in output_path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            completed.add((record.get("variant"), record.get("qid")))

    records: list[dict] = []
    with output_path.open("a", encoding="utf-8") as handle:
        for variant in ABLATION_VARIANTS:
            pipeline = build_default_pipeline()
            if variant == "no_conflict_seeking_expansion":
                pipeline.retriever.expansion_enabled = False
            if variant == "no_self_critique":
                pipeline.critic.self_critique = False
            for question in questions:
                key = (variant, question.qid)
                if key in completed:
                    continue
                started = time.perf_counter()
                if variant == "no_critic":
                    answer = naive_rag(question.question, pipeline.retriever, pipeline.synthesizer)
                else:
                    answer = pipeline.run(question.question)
                record = {
                    "variant": variant,
                    "qid": question.qid,
                    "split": split,
                    "latency_ms": (time.perf_counter() - started) * 1000,
                    "answer": answer.model_dump(mode="json"),
                }
                handle.write(json.dumps(record, sort_keys=True) + "\n")
                handle.flush()
                records.append(record)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=ROOT / "data/benchmark/questions.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/ablation_results.jsonl")
    parser.add_argument("--split", choices=["dev", "test"], default="test")
    parser.add_argument("--limit", type=int, default=60)
    args = parser.parse_args()
    records = run_ablations(args.questions, args.output, split=args.split, limit=args.limit)
    print(f"Wrote {len(records)} new ablation records to {args.output}")


if __name__ == "__main__":
    main()
