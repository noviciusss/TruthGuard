"""Evaluate deterministic or LLM critic runs with per-question call evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from bench.metrics import evaluate_predictions
from bench.run_eval import load_questions
from truthguard.config import load_config
from truthguard.llm import LLMRouter
from truthguard.pipeline import build_default_pipeline
from truthguard.schemas import FinalAnswer


ROOT = Path(__file__).resolve().parents[1]


def _stage_records(records, prefix: str) -> dict[str, list]:
    return {
        stage: [record for record in records if record.stage == stage]
        for stage in {record.stage for record in records if record.stage.startswith(prefix)}
    }


def _call_evidence(records) -> dict[str, Any]:
    critic_records = [record for record in records if record.stage.startswith("critic-call-")]
    by_stage = _stage_records(critic_records, "critic-call-")
    schema_repairs = [record for record in critic_records if record.error and "schema validation before repair" in record.error]
    successful_stages = [stage for stage, items in by_stage.items() if any(item.success for item in items)]
    first_try_stages = [
        stage for stage, items in by_stage.items()
        if len(items) == 1 and items[0].success and not items[0].cached
    ]
    repaired_stages = [
        stage for stage, items in by_stage.items()
        if any(item.success for item in items)
        and any(item.error and "schema validation before repair" in item.error for item in items)
    ]
    providers = [record.model_dump(mode="json") for record in records]
    provider_sequence = []
    for item in providers:
        pair = {"provider": item["provider"], "model": item["model"]}
        if pair not in provider_sequence:
            provider_sequence.append(pair)
    return {
        "critic_logical_calls": len(successful_stages),
        "critic_first_try_json_stages": len(first_try_stages),
        "critic_repaired_json_stages": len(repaired_stages),
        "critic_schema_repair_events": len(schema_repairs),
        "critic_fallback_events": sum(
            max(0, len({item.provider for item in items}) - 1)
            for items in by_stage.values()
        ),
        "critic_cached_stages": sum(any(item.cached for item in items) for items in by_stage.values()),
        "actual_request_cap_verified": False,
        "attempt_accounting_note": "Router records do not include each internal HTTP retry; actual request count is not verified.",
        "provider_sequence": provider_sequence,
        "call_records": providers,
    }


def run_evaluation(questions_path: str | Path, output_path: str | Path, *, mode: str, database_path: str | Path) -> dict[str, Any]:
    questions = load_questions(questions_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    config = load_config()
    config["project"]["offline"] = mode == "deterministic"
    run_identity = hashlib.sha256(json.dumps({
        "questions": [question.model_dump(mode="json") for question in questions],
        "mode": mode,
        "config": config,
        "overrides": {key: os.getenv(key) for key in (
            "TRUTHGUARD_RETRIEVAL_BACKEND", "TRUTHGUARD_ALLOW_BGE_OFFLINE",
            "TRUTHGUARD_CRITIC_PROVIDER", "TRUTHGUARD_CRITIC_CHAIN",
            "TRUTHGUARD_GENERATION_PROVIDER", "TRUTHGUARD_SYNTHESIZER_PROVIDER",
        )},
    }, sort_keys=True).encode()).hexdigest()
    requested_qids = {question.qid for question in questions}
    completed: dict[str, dict] = {}
    if output_path.exists():
        for line in output_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                if record.get("run_identity") != run_identity:
                    raise ValueError("Output belongs to a different or legacy run; use a new output path rather than mixing results")
                if "answer" in record and "error" not in record:
                    if record["qid"] in requested_qids:
                        completed[record["qid"]] = record

    router = LLMRouter(config, database_path=database_path)
    pipeline = build_default_pipeline(router=router, no_llm_critic=mode == "deterministic")
    blocked = None
    with output_path.open("a", encoding="utf-8") as handle:
        for question in questions:
            if question.qid in completed:
                continue
            before = len(router.call_records())
            started = time.perf_counter()
            try:
                answer = pipeline.run(question.question)
                records = router.call_records()[before:]
                evidence = _call_evidence(records)
                result = {
                    "qid": question.qid,
                    "mode": mode,
                    "latency_ms": (time.perf_counter() - started) * 1000,
                    "answer": answer.model_dump(mode="json"),
                    "provider_models": evidence["provider_sequence"],
                    "critic": evidence,
                }
            except Exception as exc:  # noqa: BLE001 - resumable evidence runner
                result = {"qid": question.qid, "mode": mode, "error": str(exc),
                          "critic": _call_evidence(router.call_records()[before:])}
                if any(marker in str(exc).lower() for marker in ("429", "budget", "tpm limit", "daily", "rate limit")):
                    blocked = "quota_or_rate_limit"
            if "provider_models" not in result:
                result["provider_models"] = result["critic"]["provider_sequence"]
            if mode == "deterministic":
                result["provider_models"] = [{"provider": "none", "model": "deterministic"}]
            result["run_identity"] = run_identity
            handle.write(json.dumps(result, sort_keys=True) + "\n")
            handle.flush()
            completed[question.qid] = result if "answer" in result else completed.get(question.qid, result)
            if blocked:
                break

    predictions = {
        qid: FinalAnswer.model_validate(record["answer"])
        for qid, record in completed.items()
        if "answer" in record
    }
    metrics = evaluate_predictions(questions, predictions, bootstrap_samples=200)
    return {"mode": mode, "run_identity": run_identity, "questions": len(questions), "completed": len(predictions),
            "blocked": blocked, "comparison_note": "End-to-end modes differ in synthesis and reformulation as well as critic; not a controlled critic ablation.",
            "metrics": metrics}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--mode", choices=["deterministic", "llm"], required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    result = run_evaluation(args.questions, args.output, mode=args.mode, database_path=args.database)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("mode", "questions", "completed")}, sort_keys=True))


if __name__ == "__main__":
    main()
