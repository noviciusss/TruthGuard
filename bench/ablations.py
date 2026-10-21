"""Run named TruthGuard component ablations with resumable JSONL output."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from truthguard.baselines import naive_rag
from truthguard.pipeline import build_default_pipeline
from bench.metrics import evaluate_predictions
from truthguard.schemas import BenchmarkQuestion, FinalAnswer

from .run_eval import load_questions


ROOT = Path(__file__).resolve().parents[1]
ABLATION_VARIANTS = (
    "no_critic",
    "no_supersession_graph",
    "no_metadata_inference",
)


def run_ablations(
    questions_path: str | Path,
    output_path: str | Path,
    *,
    split: str = "test",
    limit: int = 60,
    corpus_dir: str | Path | None = None,
    offset: int = 0,
) -> list[dict]:
    questions = [question for question in load_questions(questions_path) if question.split == split][offset:offset + limit]
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
            pipeline = build_default_pipeline(
                no_llm_critic=True,
                corpus_dir=corpus_dir,
                use_supersession_graph=variant != "no_supersession_graph",
                use_metadata_inference=variant != "no_metadata_inference",
                use_self_critique=True,
            )
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
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--corpus", type=Path, help="Corpus directory; defaults to configured v1 corpus")
    args = parser.parse_args()
    records = run_ablations(args.questions, args.output, split=args.split, limit=args.limit, corpus_dir=args.corpus, offset=args.offset)
    print(f"Wrote {len(records)} new ablation records to {args.output}")
    questions = [question for question in load_questions(args.questions) if question.split == args.split][args.offset:args.offset + args.limit]
    by_variant: dict[str, dict[str, FinalAnswer]] = {}
    for line in Path(args.output).read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("split") == args.split and record.get("qid") in {q.qid for q in questions} and "answer" in record:
            by_variant.setdefault(record["variant"], {})[record["qid"]] = FinalAnswer.model_validate(record["answer"])
    report_lines = ["# Deterministic ablation results", "", f"Split: {args.split}; questions: {len(questions)}", "",
                    "All variants use no LLM calls. Results are deterministic and resumable via the JSONL stage cache.", "",
                    "| Variant | Questions | Answer proxy | Conflict F1 | Mode accuracy | T0 false-conflict rate |", "|---|---:|---:|---:|---:|---:|"]
    for variant, predictions in sorted(by_variant.items()):
        metrics = evaluate_predictions(questions, predictions, bootstrap_samples=1000)
        t0 = [q for q in questions if q.type == "T0"]
        t0_fp = sum(bool(predictions[q.qid].conflicts) for q in t0)
        report_lines.append(
            f"| {variant} | {metrics['questions_scored']} | {metrics['answer_accuracy']['value']:.4f} "
            f"[{metrics['answer_accuracy']['ci95'][0]:.4f}, {metrics['answer_accuracy']['ci95'][1]:.4f}] | "
            f"{metrics['conflict_detection']['f1']:.4f} | {metrics['resolution_mode_accuracy']['value']:.4f} | "
            f"{t0_fp}/{len(t0)} ({t0_fp / len(t0) if t0 else 0:.4f}) |"
        )
    report_path = args.output.with_suffix(".md")
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"Wrote ablation report to {report_path}")


if __name__ == "__main__":
    main()
