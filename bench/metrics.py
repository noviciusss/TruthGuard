"""Evaluation metrics for conflict disclosure, resolution, and provenance."""

from __future__ import annotations

import math
import random
import re
from collections import Counter
from typing import Any, Iterable, Mapping

from truthguard.schemas import BenchmarkQuestion, FinalAnswer


NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def _normalize(text: str | None) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9%]+", " ", (text or "").lower())).strip()


def _numeric_match(gold: str | None, predicted: str) -> bool:
    gold_values = NUMBER_RE.findall(gold or "")
    predicted_values = NUMBER_RE.findall(predicted)
    return bool(gold_values) and all(value in predicted_values for value in gold_values)


def _predicted_doc_ids(answer: FinalAnswer) -> set[str]:
    return {citation.chunk_id.split(":", 1)[0] for citation in answer.citations}


def score_question(gold: BenchmarkQuestion, predicted: FinalAnswer) -> dict[str, float]:
    gold_conflict = gold.type in {"T1", "T2", "T3", "T4", "T5", "T6"}
    predicted_conflict = bool(predicted.conflicts)
    predicted_type = predicted.conflicts[0].type if predicted.conflicts else None
    answer_correct = float(
        bool(gold.gold_answer)
        and (_normalize(gold.gold_answer) in _normalize(predicted.answer_text) or _numeric_match(gold.gold_answer, predicted.answer_text))
    )
    if gold.type == "T7":
        answer_correct = float(predicted.status == "not_in_corpus")
    if gold.type == "T6":
        answer_correct = float(predicted.status == "abstained")
    type_correct = float(gold.type == predicted_type) if gold_conflict else 0.0
    winner_correct = float(
        gold.gold_winner_doc is not None
        and any(conflict.winner_doc_id == gold.gold_winner_doc for conflict in predicted.conflicts)
    )
    mode_correct = float(
        (gold.gold_status == "resolved" and predicted.status == "resolved")
        or (gold.gold_status == "conditional" and predicted.status == "conditional")
        or (gold.gold_status == "abstained" and predicted.status == "abstained")
        or (gold.gold_status == "no_conflict" and predicted.status == "no_conflict")
        or (gold.gold_status == "not_in_corpus" and predicted.status == "not_in_corpus")
    )
    provenance = float(bool(_predicted_doc_ids(predicted) & set(gold.gold_conflicting_docs or []))) if gold_conflict else float(bool(predicted.citations))
    unsupported_rate = float(sum(claim.verdict == "unsupported" for claim in predicted.claims) / len(predicted.claims)) if predicted.claims else 0.0
    blended = float(gold_conflict and not predicted_conflict and predicted.status == "resolved")
    abstention_gold = gold.type in {"T6", "T7"}
    abstained = predicted.status in {"abstained", "not_in_corpus"}
    status_correct_answer = answer_correct if gold.gold_status == "resolved" else float(predicted.status == gold.gold_status)
    return {
        "answer_accuracy": answer_correct,
        "status_correct_answer": status_correct_answer,
        "conflict_tp": float(gold_conflict and predicted_conflict),
        "conflict_fp": float(not gold_conflict and predicted_conflict),
        "conflict_fn": float(gold_conflict and not predicted_conflict),
        "type_accuracy": type_correct,
        "winner_accuracy": winner_correct,
        "resolution_mode_accuracy": mode_correct,
        "provenance_correctness": provenance,
        "unsupported_claim_rate": unsupported_rate,
        "blended_answer_rate": blended,
        "abstention_tp": float(abstention_gold and abstained),
        "abstention_fp": float(not abstention_gold and abstained),
        "abstention_fn": float(abstention_gold and not abstained),
        "false_conflict": float(gold.type == "T0" and predicted_conflict),
    }


def bootstrap_ci(values: Iterable[float], *, samples: int = 1000, seed: int = 7) -> tuple[float, float]:
    values = list(values)
    if not values:
        return (0.0, 0.0)
    rng = random.Random(seed)
    means = [sum(rng.choice(values) for _ in values) / len(values) for _ in range(samples)]
    means.sort()
    low = means[max(0, int(0.025 * samples) - 1)]
    high = means[min(samples - 1, int(0.975 * samples))]
    return low, high


def _f1(tp: float, fp: float, fn: float) -> float:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def evaluate_predictions(
    questions: Iterable[BenchmarkQuestion],
    predictions: Mapping[str, FinalAnswer | dict[str, Any]],
    *,
    bootstrap_samples: int = 1000,
    include_breakdowns: bool = True,
) -> dict[str, Any]:
    """Aggregate question-level metrics and 95% bootstrap confidence intervals."""

    questions = list(questions)
    rows: list[dict[str, float]] = []
    missing = []
    for question in questions:
        prediction = predictions.get(question.qid)
        if prediction is None:
            missing.append(question.qid)
            continue
        if isinstance(prediction, dict):
            prediction = FinalAnswer.model_validate(prediction)
        rows.append(score_question(question, prediction))
    totals = Counter()
    for row in rows:
        totals.update(row)
    count = len(rows)
    metrics: dict[str, Any] = {"questions_scored": count, "missing_qids": missing}
    for key in ("answer_accuracy", "status_correct_answer", "type_accuracy", "winner_accuracy", "resolution_mode_accuracy", "provenance_correctness", "unsupported_claim_rate", "blended_answer_rate", "false_conflict"):
        values = [row[key] for row in rows]
        mean = sum(values) / count if count else 0.0
        metrics[key] = {"value": mean, "ci95": bootstrap_ci(values, samples=bootstrap_samples)}
    conflict_tp = totals["conflict_tp"]
    conflict_fp = totals["conflict_fp"]
    conflict_fn = totals["conflict_fn"]
    conflict_precision = conflict_tp / (conflict_tp + conflict_fp) if conflict_tp + conflict_fp else 0.0
    conflict_recall = conflict_tp / (conflict_tp + conflict_fn) if conflict_tp + conflict_fn else 0.0
    metrics["conflict_detection"] = {
        "precision": conflict_precision,
        "recall": conflict_recall,
        "f1": _f1(conflict_tp, conflict_fp, conflict_fn),
    }
    abstention_tp = totals["abstention_tp"]
    abstention_fp = totals["abstention_fp"]
    abstention_fn = totals["abstention_fn"]
    metrics["abstention"] = {
        "precision": abstention_tp / (abstention_tp + abstention_fp) if abstention_tp + abstention_fp else 0.0,
        "recall": abstention_tp / (abstention_tp + abstention_fn) if abstention_tp + abstention_fn else 0.0,
        "f1": _f1(abstention_tp, abstention_fp, abstention_fn),
    }
    if include_breakdowns:
        grouped: dict[str, list[BenchmarkQuestion]] = {}
        for question in questions:
            grouped.setdefault(question.type, []).append(question)
        by_type = {
            question_type: evaluate_predictions(
                group,
                predictions,
                bootstrap_samples=bootstrap_samples,
                include_breakdowns=False,
            )
            for question_type, group in sorted(grouped.items())
        }
        metrics["by_type"] = by_type
        macro_keys = {
            "answer_accuracy": lambda item: item["answer_accuracy"]["value"],
            "status_correct_answer": lambda item: item["status_correct_answer"]["value"],
            "conflict_f1": lambda item: item["conflict_detection"]["f1"],
            "resolution_mode_accuracy": lambda item: item["resolution_mode_accuracy"]["value"],
            "provenance_correctness": lambda item: item["provenance_correctness"]["value"],
            "false_conflict_rate": lambda item: item["false_conflict"]["value"],
            "abstention_recall": lambda item: item["abstention"]["recall"],
        }
        metrics["macro"] = {
            key: sum(selector(item) for item in by_type.values()) / len(by_type) if by_type else 0.0
            for key, selector in macro_keys.items()
        }
    return metrics


def compare_systems(
    questions: Iterable[BenchmarkQuestion],
    system_predictions: Mapping[str, Mapping[str, FinalAnswer | dict[str, Any]]],
    *,
    bootstrap_samples: int = 1000,
) -> dict[str, dict[str, Any]]:
    return {
        name: evaluate_predictions(questions, predictions, bootstrap_samples=bootstrap_samples)
        for name, predictions in system_predictions.items()
    }
