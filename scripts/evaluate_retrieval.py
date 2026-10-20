"""Measure dev retrieval recall and wild-set behavior for one backend."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from bench.metrics import evaluate_predictions, score_question
from bench.run_eval import load_questions
from truthguard.pipeline import build_default_pipeline


ROOT = Path(__file__).resolve().parents[1]


def _retrieval_recall(questions, pipeline) -> tuple[float, int, list[str]]:
    hits = 0
    eligible = 0
    misses: list[str] = []
    for question in questions:
        if not question.gold_conflicting_docs:
            continue
        eligible += 1
        context = pipeline.retriever.retrieve(question.question, expand=True)
        retrieved = {result.chunk.doc_id for result in context.results[:8]}
        if retrieved & set(question.gold_conflicting_docs):
            hits += 1
        else:
            misses.append(question.qid)
    return (hits / eligible if eligible else 0.0), eligible, misses


def _wild_failure_rows(questions, pipeline) -> tuple[dict, dict[str, list[str]]]:
    predictions = {}
    failures: dict[str, list[str]] = {"retrieval miss": [], "wrong conflict type": [], "wrong mode": []}
    for question in questions:
        context = pipeline.retriever.retrieve(question.question, expand=True)
        answer = pipeline.run(question.question)
        predictions[question.qid] = answer
        retrieved = {result.chunk.doc_id for result in context.results[:8]}
        if question.gold_conflicting_docs and not retrieved.intersection(question.gold_conflicting_docs):
            failures["retrieval miss"].append(question.qid)
        predicted_type = answer.conflicts[0].type if answer.conflicts else None
        if question.type in {"T1", "T2", "T3", "T4", "T5", "T6"} and predicted_type is not None and predicted_type != question.type:
            failures["wrong conflict type"].append(question.qid)
        if answer.status != question.gold_status:
            failures["wrong mode"].append(question.qid)
    metrics = evaluate_predictions(questions, predictions, bootstrap_samples=200)
    return metrics, failures


def evaluate_backend(backend: str, questions_path: str | Path, wild_path: str | Path) -> dict:
    os.environ["TRUTHGUARD_OFFLINE"] = "true"
    os.environ["TRUTHGUARD_RETRIEVAL_BACKEND"] = backend
    if backend == "bge":
        os.environ["TRUTHGUARD_ALLOW_BGE_OFFLINE"] = "true"
    pipeline = build_default_pipeline(no_llm_critic=True)
    dev = [question for question in load_questions(questions_path) if question.split == "dev"]
    wild = load_questions(wild_path)
    recall, eligible, misses = _retrieval_recall(dev, pipeline)
    wild_metrics, failures = _wild_failure_rows(wild, pipeline)
    return {
        "backend": backend,
        "dev_recall_at_8": recall,
        "dev_recall_eligible": eligible,
        "dev_recall_misses": misses,
        "wild_questions": len(wild),
        "wild_answer_accuracy": wild_metrics["answer_accuracy"]["value"],
        "wild_conflict_f1": wild_metrics["conflict_detection"]["f1"],
        "wild_mode_accuracy": wild_metrics["resolution_mode_accuracy"]["value"],
        "wild_false_conflict_rate": wild_metrics["false_conflict"]["value"],
        "wild_abstention_recall": wild_metrics["abstention"]["recall"],
        "wild_failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=["hash", "bge"], required=True)
    parser.add_argument("--questions", type=Path, default=ROOT / "data/benchmark/questions.jsonl")
    parser.add_argument("--wild", type=Path, default=ROOT / "data/benchmark/wild.jsonl")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate_backend(args.backend, args.questions, args.wild)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    import json

    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote retrieval evaluation to {args.output}")


if __name__ == "__main__":
    main()
