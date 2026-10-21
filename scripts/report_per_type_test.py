"""Report frozen v2 TEST conflict and abstention metrics by type."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from bench.metrics import score_question
from bench.run_eval import load_questions
from truthguard.schemas import FinalAnswer


ROOT = Path(__file__).resolve().parents[1]


def load_predictions(path: Path) -> dict[str, FinalAnswer]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if "answer" in row:
                result[row["qid"]] = FinalAnswer.model_validate(row["answer"])
    return result


def f1(tp: float, fp: float, fn: float) -> float:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def conflict(rows):
    tp = sum(row["conflict_tp"] for row in rows)
    fp = sum(row["conflict_fp"] for row in rows)
    fn = sum(row["conflict_fn"] for row in rows)
    return (tp / (tp + fp) if tp + fp else 0.0, tp / (tp + fn) if tp + fn else 0.0, f1(tp, fp, fn))


def report(questions_path: Path, predictions_path: Path, output: Path) -> None:
    questions = [question for question in load_questions(questions_path) if question.split == "test"]
    predictions = load_predictions(predictions_path)
    scored = {question.qid: score_question(question, predictions[question.qid]) for question in questions}
    by_type = {kind: [question for question in questions if question.type == kind] for kind in [f"T{i}" for i in range(8)]}
    t6_questions = by_type["T6"]
    t6_tp = sum(predictions[q.qid].status == "abstained" for q in t6_questions)
    t6_fp = sum(q.type != "T6" and predictions[q.qid].status == "abstained" for q in questions)
    t6_precision = t6_tp / (t6_tp + t6_fp) if t6_tp + t6_fp else 0.0
    t6_recall = t6_tp / len(t6_questions) if t6_questions else 0.0
    non_t6 = [q for q in questions if q.type != "T6"]
    false_abstain_rate = sum(predictions[q.qid].status == "abstained" for q in non_t6) / len(non_t6) if non_t6 else 0.0
    lines = [
        "# Frozen v2 TEST metrics by type",
        "",
        "All values are deterministic/offline results from the frozen 146-question v2 TEST split using HashEmbedder retrieval and the deterministic critic. No provider answered these rows.",
        "",
        "Conflict precision/recall/F1 treat each question as conflict-positive for T1–T6 and conflict-negative for T0/T7. Mode accuracy requires the gold final status. T6 abstention is strict `status=abstained`; T7 `not_in_corpus` recall is reported separately.",
        "",
        "| Type | n | Conflict P | Conflict R | Conflict F1 | Mode accuracy | T6 abstention precision | T6 abstention recall | Non-T6 false-abstain rate | T0 false-conflict rate | T7 not-in-corpus recall |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for kind, group in by_type.items():
        rows = [scored[q.qid] for q in group]
        precision, recall, conflict_f1 = conflict(rows)
        mode = sum(scored[q.qid]["resolution_mode_accuracy"] for q in group) / len(group) if group else 0.0
        t0_rate = sum(bool(predictions[q.qid].conflicts) for q in group) / len(group) if kind == "T0" and group else None
        t7_recall = sum(predictions[q.qid].status == "not_in_corpus" for q in group) / len(group) if kind == "T7" and group else None
        t6_precision_text = f"{t6_precision:.4f}" if kind == "T6" else "—"
        t6_recall_text = f"{t6_recall:.4f}" if kind == "T6" else "—"
        false_abstain_text = f"{false_abstain_rate:.4f}" if kind == "T6" else "—"
        t0_text = f"{t0_rate:.4f}" if t0_rate is not None else "—"
        t7_text = f"{t7_recall:.4f}" if t7_recall is not None else "—"
        # Keep non-applicable focus metrics explicit rather than repeating a
        # global number as if it were per-type.
        lines.append(
            f"| {kind} | {len(group)} | {precision:.4f} | {recall:.4f} | {conflict_f1:.4f} | {mode:.4f} | "
            f"{t6_precision_text} | {t6_recall_text} | {false_abstain_text} | {t0_text} | {t7_text} |"
        )
    all_rows = list(scored.values())
    precision, recall, conflict_f1 = conflict(all_rows)
    mode = sum(row["resolution_mode_accuracy"] for row in all_rows) / len(all_rows)
    t0_rate = sum(bool(predictions[q.qid].conflicts) for q in by_type["T0"]) / len(by_type["T0"])
    t7_recall = sum(predictions[q.qid].status == "not_in_corpus" for q in by_type["T7"]) / len(by_type["T7"])
    lines += [
        f"| **Overall** | **{len(questions)}** | **{precision:.4f}** | **{recall:.4f}** | **{conflict_f1:.4f}** | **{mode:.4f}** | **{t6_precision:.4f}** | **{t6_recall:.4f}** | **{false_abstain_rate:.4f}** | **{t0_rate:.4f}** | **{t7_recall:.4f}** |",
        "",
        "## Focus metrics",
        "",
        f"- T6 abstention: `{t6_tp}/{len(t6_questions)}` true positives; precision `{t6_precision:.4f}`, recall `{t6_recall:.4f}`.",
        f"- False abstention on non-T6: `{t6_fp}/{len(non_t6)}` = `{false_abstain_rate:.4f}`. This counts only strict `abstained`, not T7's intentional `not_in_corpus` status.",
        f"- T0 false-conflict rate: `{sum(bool(predictions[q.qid].conflicts) for q in by_type['T0'])}/{len(by_type['T0'])}` = `{t0_rate:.4f}`.",
        f"- T7 not-in-corpus recall: `{sum(predictions[q.qid].status == 'not_in_corpus' for q in by_type['T7'])}/{len(by_type['T7'])}` = `{t7_recall:.4f}`.",
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=ROOT / "data/benchmark/questions_v2.jsonl")
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/per_type_test.md")
    args = parser.parse_args()
    report(args.questions, args.predictions, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
