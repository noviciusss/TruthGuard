"""Offline before/after evidence; DEV, TEST and wild stay separate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

from bench.metrics import evaluate_predictions
from bench.run_eval import load_questions
from truthguard.pipeline import build_default_pipeline


ROOT = Path(__file__).resolve().parents[1]


def measure(output: Path, label: str, backend: str = "bge", only_dev: bool = False) -> dict:
    os.environ["TRUTHGUARD_OFFLINE"] = "true"
    os.environ["TRUTHGUARD_RETRIEVAL_BACKEND"] = backend
    os.environ["TRUTHGUARD_ALLOW_BGE_OFFLINE"] = "true"
    main_path = ROOT / "data/benchmark/questions.jsonl"
    wild_path = ROOT / "data/benchmark/wild.jsonl"
    main = load_questions(main_path)
    groups = {"DEV": [q for q in main if q.split == "dev"]}
    if not only_dev:
        groups.update({"TEST": [q for q in main if q.split == "test"], "wild": load_questions(wild_path)})
    pipeline = build_default_pipeline(no_llm_critic=True)
    summaries = {}
    for name, questions in groups.items():
        predictions = {q.qid: pipeline.run(q.question) for q in questions}
        controls = [q for q in questions if q.type == "T0"]
        false_positives = [q.qid for q in controls if predictions[q.qid].conflicts]
        summaries[name] = {
            "questions": len(questions), "t0_questions": len(controls),
            "t0_false_positives": false_positives,
            "t0_false_conflict_rate": len(false_positives) / len(controls) if controls else None,
            "metrics": evaluate_predictions(questions, predictions),
            "rows": [{"qid": q.qid, "gold_type": q.type, "gold_status": q.gold_status,
                      "status": predictions[q.qid].status,
                      "conflict_types": [c.type for c in predictions[q.qid].conflicts],
                      "conflicts": [{"id": c.conflict_id, "type": c.type,
                                     "evidence": [{"doc": p.doc_id, "text": p.claim_text,
                                                   "span": p.span.model_dump()} for p in c.positions]}
                                    for c in predictions[q.qid].conflicts]}
                     for q in questions],
        }
        print(name, "questions", len(questions), "T0", len(false_positives), "/", len(controls), flush=True)
    result = {"label": label, "provider": "none", "critic": "deterministic", "retrieval": backend,
              "input_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in (main_path, wild_path)}, "groups": summaries}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--backend", choices=["hash", "bge"], default="bge")
    parser.add_argument("--only-dev", action="store_true")
    args = parser.parse_args()
    measure(args.output, args.label, args.backend, args.only_dev)


if __name__ == "__main__":
    main()
