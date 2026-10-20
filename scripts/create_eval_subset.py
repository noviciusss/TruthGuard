"""Create the frozen stratified 40-question evaluation subset."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEED = 20261020
TARGET_COUNTS = {"T0": 2, "T1": 6, "T2": 6, "T3": 6, "T4": 6, "T5": 6, "T6": 6, "T7": 2}


def create_subset(input_path: str | Path, output_path: str | Path) -> list[dict]:
    records = [json.loads(line) for line in Path(input_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    test_records = [record for record in records if record["split"] == "test"]
    rng = random.Random(SEED)
    selected: list[dict] = []
    for question_type, count in TARGET_COUNTS.items():
        candidates = [record for record in test_records if record["type"] == question_type]
        if len(candidates) < count:
            raise ValueError(f"Only {len(candidates)} test records available for {question_type}; need {count}")
        selected.extend(rng.sample(candidates, count))
    selected.sort(key=lambda record: record["qid"])
    if len({record["qid"] for record in selected}) != 40:
        raise AssertionError("subset contains duplicate qids")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(json.dumps(record, sort_keys=True) for record in selected) + "\n"
    if output_path.exists() and output_path.read_text(encoding="utf-8") != content:
        raise ValueError("Refusing to overwrite a frozen subset with different selections")
    output_path.write_text(content, encoding="utf-8")
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/benchmark/questions.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "data/benchmark/eval_subset_40.jsonl")
    args = parser.parse_args()
    selected = create_subset(args.input, args.output)
    print(f"Wrote {len(selected)} records with seed {SEED}: {dict(Counter(record['type'] for record in selected))}")


if __name__ == "__main__":
    main()
