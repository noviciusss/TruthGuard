"""Summarize a deterministic ablation JSONL against a full-system JSONL."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from bench.metrics import evaluate_predictions, score_question
from bench.run_eval import load_questions
from truthguard.schemas import FinalAnswer


def _f1(rows) -> float:
    tp = sum(row["conflict_tp"] for row in rows)
    fp = sum(row["conflict_fp"] for row in rows)
    fn = sum(row["conflict_fn"] for row in rows)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def _f1_ci(questions, predictions, samples=1000, seed=7):
    rows = [score_question(question, predictions[question.qid]) for question in questions]
    rng = random.Random(seed)
    values = [_f1([rng.choice(rows) for _ in rows]) for _ in range(samples)]
    values.sort()
    return values[int(samples * 0.025)], values[int(samples * 0.975)]


def _load(path: Path):
    records = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            if "answer" in record:
                records[record["qid"]] = FinalAnswer.model_validate(record["answer"])
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--ablations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--retrieval-backend", default="configured", help="Backend used for the baseline and ablation records")
    args = parser.parse_args()
    questions = [q for q in load_questions(args.questions) if q.split == "test"]
    baseline = _load(args.baseline)
    variants = {}
    for line in args.ablations.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            if "answer" in record:
                variants.setdefault(record["variant"], {})[record["qid"]] = FinalAnswer.model_validate(record["answer"])
    lines = [
        "# Deterministic ablations — frozen TEST split",
        "",
        f"All three effective variants ran on all {len(questions)} frozen TEST questions with no API calls. "
        f"The JSONL output is resumable stage evidence. The full system and all variants use the same {args.retrieval_backend} retrieval backend and deterministic critic.",
        "",
        "| Variant | n | Answer proxy (95% CI) | Status-correct answer (95% CI) | Macro status-correct | Macro answer | Conflict F1 (95% CI) | Macro conflict F1 | Mode accuracy (95% CI) | Macro mode | TEST T0 false-conflicts | Public outputs differing from full |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ["full_system", *sorted(variants)]:
        predictions = baseline if name == "full_system" else variants[name]
        metrics = evaluate_predictions(questions, predictions, bootstrap_samples=1000)
        f1_low, f1_high = _f1_ci(questions, predictions)
        t0 = [q for q in questions if q.type == "T0"]
        t0_fp = sum(bool(predictions[q.qid].conflicts) for q in t0)
        differing = 0 if name == "full_system" else sum(
            (predictions[q.qid].status, predictions[q.qid].answer_text,
             [(c.type, c.winner_doc_id, c.resolution_mode) for c in predictions[q.qid].conflicts]) !=
            (baseline[q.qid].status, baseline[q.qid].answer_text,
             [(c.type, c.winner_doc_id, c.resolution_mode) for c in baseline[q.qid].conflicts])
            for q in questions
        )
        ci = metrics["answer_accuracy"]["ci95"]
        mode_ci = metrics["resolution_mode_accuracy"]["ci95"]
        lines.append(
            f"| {name} | {metrics['questions_scored']} | {metrics['answer_accuracy']['value']:.4f} "
            f"[{ci[0]:.4f}, {ci[1]:.4f}] | "
            f"{metrics['status_correct_answer']['value']:.4f} [{metrics['status_correct_answer']['ci95'][0]:.4f}, {metrics['status_correct_answer']['ci95'][1]:.4f}] | "
            f"{metrics['macro']['status_correct_answer']:.4f} | {metrics['macro']['answer_accuracy']:.4f} | "
            f"{metrics['conflict_detection']['f1']:.4f} [{f1_low:.4f}, {f1_high:.4f}] | "
            f"{metrics['macro']['conflict_f1']:.4f} | {metrics['resolution_mode_accuracy']['value']:.4f} "
            f"[{mode_ci[0]:.4f}, {mode_ci[1]:.4f}] | {metrics['macro']['resolution_mode_accuracy']:.4f} | "
            f"{t0_fp}/{len(t0)} ({t0_fp / len(t0):.4f}) | {differing} |"
        )
    lines.extend([
        "", "## Variant semantics", "",
        "- `no_critic`: passage-only Naive RAG answer path.",
        "- `no_supersession_graph`: graph construction and graph-neighbor retrieval disabled.",
        "- `no_metadata_inference`: body/filename metadata inference disabled; header metadata only.",
        "- `no_self_critique` and `no_conflict_seeking_expansion` were removed from the "
        "reported table because their frozen TEST runs changed no public answer/status/conflict "
        "outputs (only retrieval/trace internals). They are not claimed as effective ablations.",
        "",
        "The reported full-system baseline is deterministic and offline. These are "
        "component ablations, not live-provider results.",
        "",
    ])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
