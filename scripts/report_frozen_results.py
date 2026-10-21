"""Write deterministic v2 results with micro and macro metrics."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from bench.metrics import evaluate_predictions
from bench.run_eval import load_questions
from truthguard.schemas import FinalAnswer


ROOT = Path(__file__).resolve().parents[1]


def _load_predictions(path: Path) -> dict[str, FinalAnswer]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if "answer" in row:
                result[row["qid"]] = FinalAnswer.model_validate(row["answer"])
    return result


def _fact_key(question) -> str:
    if question.gold_fact_id:
        return question.gold_fact_id
    if question.qid.startswith("t6-"):
        return "annual_limit"
    return {
        "T0": "renewal_grace",
        "T1": "waiting_period",
        "T2": "copay",
        "T3": "claim_deadline",
        "T4": "pre_existing_lookback",
        "T5": "preauthorization",
        "T7": "not_in_corpus",
    }.get(question.type, question.type)


def _fmt(value: float) -> str:
    return f"{value:.4f}"


def report(questions_path: Path, dev_path: Path, test_path: Path, wild_questions_path: Path, wild_path: Path, output: Path, retrieval_backend: str) -> None:
    main = load_questions(questions_path)
    wild = load_questions(wild_questions_path)
    runs = {
        "DEV": ([q for q in main if q.split == "dev"], _load_predictions(dev_path)),
        "TEST": ([q for q in main if q.split == "test"], _load_predictions(test_path)),
        "wild": (wild, _load_predictions(wild_path)),
    }
    lines = [
        "# Frozen deterministic results — v2",
        "",
        f"V2 uses the additive genuine-T6 corpus and benchmark. Provider/model: none; deterministic pipeline only. Retrieval backend: {retrieval_backend}. No API calls.",
        "",
        "## Micro and macro metrics",
        "",
        "Micro metrics average every question. Macro metrics average the per-type metric values, giving each present type equal weight.",
        "",
        "| Split | Questions | T0 | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T0 false conflicts | Micro conflict F1 | Macro conflict F1 | Micro answer | Macro answer | Micro mode | Macro mode | Abstention recall |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for split, (questions, predictions) in runs.items():
        metrics = evaluate_predictions(questions, predictions)
        counts = Counter(q.type for q in questions)
        t0 = [q for q in questions if q.type == "T0"]
        t0_fp = sum(bool(predictions[q.qid].conflicts) for q in t0)
        lines.append(
            f"| {split} | {len(questions)} | " + " | ".join(str(counts.get(f"T{i}", 0)) for i in range(8)) +
            f" | {t0_fp}/{len(t0)} ({_fmt(t0_fp / len(t0) if t0 else 0)}) | "
            f"{_fmt(metrics['conflict_detection']['f1'])} | {_fmt(metrics['macro']['conflict_f1'])} | "
            f"{_fmt(metrics['answer_accuracy']['value'])} | {_fmt(metrics['macro']['answer_accuracy'])} | "
            f"{_fmt(metrics['resolution_mode_accuracy']['value'])} | {_fmt(metrics['macro']['resolution_mode_accuracy'])} | "
            f"{_fmt(metrics['abstention']['recall'])} |"
        )
    lines += ["", "## TEST distribution by fact key", "", "The fact-key view uses explicit v2 `gold_fact_id` and conservative legacy mappings for v1 rows.", "", "| Fact key | Questions | Types |", "|---|---:|---|"]
    test_questions = runs["TEST"][0]
    by_fact: dict[str, list] = defaultdict(list)
    for question in test_questions:
        by_fact[_fact_key(question)].append(question)
    for fact_id, group in sorted(by_fact.items()):
        lines.append(f"| {fact_id} | {len(group)} | {', '.join(sorted({q.type for q in group}))} |")
    lines += ["", "## Per-type TEST metrics", "", "| Type | n | Answer | Conflict F1 | Mode |", "|---|---:|---:|---:|---:|"]
    test_metrics = evaluate_predictions(test_questions, runs["TEST"][1])
    for type_name, metrics in sorted(test_metrics["by_type"].items()):
        lines.append(f"| {type_name} | {metrics['questions_scored']} | {_fmt(metrics['answer_accuracy']['value'])} | {_fmt(metrics['conflict_detection']['f1'])} | {_fmt(metrics['resolution_mode_accuracy']['value'])} |")
    lines += ["", "## Audit boundaries", "", "- Provenance is document-level citation/overlap, not semantic supporting-span verification.", "- The wild set remains a small manually written robustness set, not production accuracy.", "- The fixed v2 subset is 40 questions: 2 T0, 6 each T1–T6, and 2 T7. Live critic/baseline results are not included here.", "- Deterministic metrics exercise retrieval, synthesis, fact detection, conflict typing, supersession, metadata inference, and resolver behavior without a provider.", ""]
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=ROOT / "data/benchmark/questions_v2.jsonl")
    parser.add_argument("--dev", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    parser.add_argument("--wild-questions", type=Path, default=ROOT / "data/benchmark/wild_v2.jsonl")
    parser.add_argument("--wild", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/frozen_results.md")
    parser.add_argument("--retrieval-backend", default="configured", help="Backend used for all supplied prediction files")
    args = parser.parse_args()
    report(args.questions, args.dev, args.test, args.wild_questions, args.wild, args.output, args.retrieval_backend)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
