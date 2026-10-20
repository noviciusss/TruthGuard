"""Evaluate the manually written wild-question robustness set offline."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from bench.metrics import evaluate_predictions
from bench.run_eval import load_questions
from truthguard.pipeline import build_default_pipeline


ROOT = Path(__file__).resolve().parents[1]


def _value(metrics: dict, key: str) -> float:
    return float(metrics[key]["value"])


def evaluate_wild(questions_path: str | Path, output_path: str | Path) -> Path:
    questions = load_questions(questions_path)
    pipeline = build_default_pipeline(no_llm_critic=True)
    predictions = {question.qid: pipeline.run(question.question) for question in questions}
    overall = evaluate_predictions(questions, predictions)

    by_type: dict[str, list] = defaultdict(list)
    for question in questions:
        by_type[question.type].append(question)
    type_metrics = {
        question_type: evaluate_predictions(group, {item.qid: predictions[item.qid] for item in group}, bootstrap_samples=200)
        for question_type, group in sorted(by_type.items())
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Wild Robustness Evaluation",
        "",
        "This report evaluates the 20 manually written questions in "
        "`data/benchmark/wild.jsonl` using the offline deterministic critic. "
        "It is separate from the frozen 140-question test result.",
        "",
        "## Overall",
        "",
        f"- Questions scored: `{overall['questions_scored']}`",
        f"- Answer accuracy: `{_value(overall, 'answer_accuracy'):.4f}`",
        f"- Conflict F1: `{overall['conflict_detection']['f1']:.4f}`",
        f"- Resolution-mode accuracy: `{_value(overall, 'resolution_mode_accuracy'):.4f}`",
        f"- Provenance correctness: `{_value(overall, 'provenance_correctness'):.4f}`",
        f"- False-conflict rate: `{_value(overall, 'false_conflict'):.4f}`",
        f"- Abstention recall: `{overall['abstention']['recall']:.4f}`",
        "",
        "## By question type",
        "",
        "| Type | Count | Answer accuracy | Conflict F1 | Mode accuracy | False-conflict rate |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for question_type, metrics in type_metrics.items():
        lines.append(
            f"| {question_type} | {metrics['questions_scored']} | "
            f"{_value(metrics, 'answer_accuracy'):.4f} | "
            f"{metrics['conflict_detection']['f1']:.4f} | "
            f"{_value(metrics, 'resolution_mode_accuracy'):.4f} | "
            f"{_value(metrics, 'false_conflict'):.4f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The wild set tests indirect wording, multi-hop combinations, mixed "
            "topics, exceptions, unresolvable conflicts, no-conflict controls, "
            "and questions outside the corpus. These results are robustness "
            "evidence for the offline path, not additional official test-set "
            "performance.",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=ROOT / "data/benchmark/wild.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/wild_results.md")
    args = parser.parse_args()
    path = evaluate_wild(args.questions, args.output)
    print(f"Wrote wild robustness report to {path}")


if __name__ == "__main__":
    main()
