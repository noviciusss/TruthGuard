"""Analyze the frozen TEST answer proxy without tuning or changing labels."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from bench.metrics import bootstrap_ci, score_question
from bench.run_eval import load_questions
from truthguard.schemas import FinalAnswer


ROOT = Path(__file__).resolve().parents[1]


def load_predictions(path: Path, variant: str | None = None) -> dict[str, FinalAnswer]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if "answer" in row and (variant is None or row.get("variant") == variant):
                result[row["qid"]] = FinalAnswer.model_validate(row["answer"])
    return result


def grouped_rows(questions, predictions):
    groups = defaultdict(list)
    for question in questions:
        groups[(question.type, question.gold_status)].append(score_question(question, predictions[question.qid]))
    return groups


def metric_summary(rows, key: str) -> tuple[float, tuple[float, float]]:
    values = [row[key] for row in rows]
    return (sum(values) / len(values) if values else 0.0, bootstrap_ci(values, samples=1000))


def analyze(questions_path: Path, full_path: Path, no_critic_path: Path, output: Path) -> None:
    questions = [question for question in load_questions(questions_path) if question.split == "test"]
    systems = {
        "full_system": load_predictions(full_path),
        "no_critic": load_predictions(no_critic_path, "no_critic"),
    }
    grouped = {name: grouped_rows(questions, predictions) for name, predictions in systems.items()}
    lines = [
        "# TEST answer-proxy analysis",
        "",
        "This is a diagnostic report over the frozen v2 TEST split. It does not tune detector rules, labels, retrieval, or prompts. Both systems use the same 146 questions and the same deterministic HashEmbedder evaluation path; the only comparison is the measured full system versus the recorded `no_critic` ablation.",
        "",
        "## Metric definitions",
        "",
        "- **Answer proxy:** the existing numeric/substring score for a non-null gold answer, exact `not_in_corpus` for T7, and exact abstained status for T6. It is retained for historical comparability.",
        "- **Status-correct answer rate:** for resolved rows, the same answer proxy; for conditional, abstained, no-conflict, and not-in-corpus rows, exact final-status correctness. This is computed identically for both systems and does not claim semantic entailment.",
        "- Intervals are 1,000-sample question-level bootstrap 95% CIs. Values are deterministic/offline; no provider answered these rows.",
        "",
        "## By gold type and gold status",
        "",
        "| Type | Gold status | n | Full answer proxy | No-critic answer proxy | Full status-correct | No-critic status-correct | Full predicted statuses | No-critic predicted statuses |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    all_groups = sorted({key for group in grouped.values() for key in group})
    for type_name, gold_status in all_groups:
        full_rows = grouped["full_system"].get((type_name, gold_status), [])
        naive_rows = grouped["no_critic"].get((type_name, gold_status), [])
        full_answer, _ = metric_summary(full_rows, "answer_accuracy")
        naive_answer, _ = metric_summary(naive_rows, "answer_accuracy")
        full_status, _ = metric_summary(full_rows, "status_correct_answer")
        naive_status, _ = metric_summary(naive_rows, "status_correct_answer")
        full_statuses = Counter(
            systems["full_system"][q.qid].status for q in questions if q.type == type_name and q.gold_status == gold_status
        )
        naive_statuses = Counter(
            systems["no_critic"][q.qid].status for q in questions if q.type == type_name and q.gold_status == gold_status
        )
        lines.append(
            f"| {type_name} | {gold_status} | {len(full_rows)} | {full_answer:.4f} | {naive_answer:.4f} | {full_status:.4f} | {naive_status:.4f} | "
            f"{', '.join(f'{key}:{value}' for key, value in sorted(full_statuses.items()))} | "
            f"{', '.join(f'{key}:{value}' for key, value in sorted(naive_statuses.items()))} |"
        )
    lines += ["", "## Overall TEST comparison with bootstrap CIs", "", "| System | n | Answer proxy (95% CI) | Status-correct answer (95% CI) |", "|---|---:|---:|---:|"]
    for name, predictions in systems.items():
        rows = [score_question(q, predictions[q.qid]) for q in questions]
        answer, answer_ci = metric_summary(rows, "answer_accuracy")
        status, status_ci = metric_summary(rows, "status_correct_answer")
        lines.append(f"| {name} | {len(rows)} | {answer:.4f} [{answer_ci[0]:.4f}, {answer_ci[1]:.4f}] | {status:.4f} [{status_ci[0]:.4f}, {status_ci[1]:.4f}] |")
    lines += ["", "## Conflict-disclosure interpretation", ""]
    conflict_types = {"T2", "T5", "T6"}
    for name, predictions in systems.items():
        rows = [score_question(q, predictions[q.qid]) for q in questions if q.type in conflict_types]
        answer, answer_ci = metric_summary(rows, "answer_accuracy")
        status, status_ci = metric_summary(rows, "status_correct_answer")
        lines.append(f"- `{name}` on T2/T5/T6 conditional-or-abstention rows (n={len(rows)}): answer proxy `{answer:.4f}` [{answer_ci[0]:.4f}, {answer_ci[1]:.4f}], status-correct answer `{status:.4f}` [{status_ci[0]:.4f}, {status_ci[1]:.4f}].")
    lines += [
        "",
        "The higher `no_critic` micro answer proxy is not evidence that conflict checking is harmful: the no-critic path scores 0.0000 conflict F1 and 0.1233 resolution-mode accuracy in the frozen ablation. The old proxy can reward a value-containing blended answer on a conflict row while failing to credit a correct conditional or abstained final status unless its special T6/T7 rule applies. The status-correct metric makes the final behavior comparison explicit, while preserving the old proxy rather than replacing it.",
        "",
        "This report does not tune on TEST or wild and does not change frozen gold labels.",
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=ROOT / "data/benchmark/questions_v2.jsonl")
    parser.add_argument("--full", type=Path, required=True)
    parser.add_argument("--no-critic", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/accuracy_proxy_analysis.md")
    args = parser.parse_args()
    analyze(args.questions, args.full, args.no_critic, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
