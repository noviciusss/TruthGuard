"""Export the required stratified 30-question human review sheet."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from truthguard.ingest.chunker import chunk_document  # noqa: E402
from truthguard.ingest.loader import LoadedDocument, load_documents  # noqa: E402
from truthguard.schemas import BenchmarkQuestion  # noqa: E402


FIELDNAMES = [
    "qid",
    "question",
    "gold_answer",
    "gold_type",
    "gold_status",
    "gold_conflicting_docs",
    "gold_winner_doc",
    "gold_justifying_passages",
    "reviewer_agrees_answer",
    "reviewer_agrees_type",
    "reviewer_agrees_docs",
    "notes",
]

SAMPLE_COUNTS = {"T1": 4, "T2": 4, "T3": 4, "T4": 4, "T5": 4, "T6": 4, "T0": 3, "T7": 3}
TOPIC_TERMS = {
    "T0": ("renewal", "grace"),
    "T1": ("waiting", "hospitalization"),
    "T2": ("co-payment", "copay", "room rent"),
    "T3": ("claim", "discharge"),
    "T4": ("lookback", "pre-existing"),
    "T5": ("pre-authorization", "prior approval", "emergency"),
    "T6": ("annual limit", "annual hospitalization"),
    "T7": (),
}


def _load_questions(path: Path) -> list[BenchmarkQuestion]:
    questions = [
        BenchmarkQuestion.model_validate(json.loads(line))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return [question for question in questions if question.split == "test"]


def _chunk_map(corpus_dir: Path) -> tuple[dict[str, Any], dict[str, list[Any]]]:
    documents = load_documents(corpus_dir)
    by_id: dict[str, Any] = {}
    chunks: dict[str, list[Any]] = {}
    for document in documents:
        by_id[document.meta.doc_id] = document.meta
        chunks[document.meta.doc_id] = chunk_document(document)
    return by_id, chunks


def _select_passages(question: BenchmarkQuestion, chunks_by_doc: dict[str, list[Any]]) -> list[dict[str, str]]:
    terms = TOPIC_TERMS.get(question.type, ())
    passages: list[dict[str, str]] = []
    for doc_id in question.gold_conflicting_docs:
        candidates = chunks_by_doc.get(doc_id, [])
        matching = [
            chunk for chunk in candidates if any(term.lower() in chunk.text.lower() for term in terms)
        ]
        selected = matching[:2] or candidates[:1]
        for chunk in selected:
            passages.append(
                {
                    "doc_id": doc_id,
                    "doc_title": chunk.doc_meta.title if chunk.doc_meta else doc_id,
                    "section": chunk.section_path,
                    "text": chunk.text,
                }
            )
    return passages


def choose_sample(questions: list[BenchmarkQuestion]) -> list[BenchmarkQuestion]:
    by_type: dict[str, list[BenchmarkQuestion]] = {key: [] for key in SAMPLE_COUNTS}
    for question in sorted(questions, key=lambda item: item.qid):
        if question.type in by_type and len(by_type[question.type]) < SAMPLE_COUNTS[question.type]:
            by_type[question.type].append(question)
    selected = [question for conflict_type in SAMPLE_COUNTS for question in by_type[conflict_type]]
    if len(selected) != 30:
        counts = {key: len(value) for key, value in by_type.items()}
        raise ValueError(f"Could not select 30 questions with required strata: {counts}")
    return selected


def export_review_sheet(
    questions_path: str | Path = ROOT / "data/benchmark/questions.jsonl",
    corpus_dir: str | Path = ROOT / "data/corpus",
    output_path: str | Path = ROOT / "reports/review_sheet.csv",
) -> list[dict[str, str]]:
    questions = choose_sample(_load_questions(Path(questions_path)))
    metadata, chunks_by_doc = _chunk_map(Path(corpus_dir))
    rows: list[dict[str, str]] = []
    for question in questions:
        docs = [
            {
                "doc_id": doc_id,
                "title": metadata[doc_id].title if doc_id in metadata else doc_id,
            }
            for doc_id in question.gold_conflicting_docs
        ]
        rows.append(
            {
                "qid": question.qid,
                "question": question.question,
                "gold_answer": question.gold_answer or "",
                "gold_type": question.type,
                "gold_status": question.gold_status,
                "gold_conflicting_docs": json.dumps(docs, ensure_ascii=False, sort_keys=True),
                "gold_winner_doc": question.gold_winner_doc or "",
                "gold_justifying_passages": json.dumps(
                    _select_passages(question, chunks_by_doc), ensure_ascii=False
                ),
                "reviewer_agrees_answer": "",
                "reviewer_agrees_type": "",
                "reviewer_agrees_docs": "",
                "notes": "",
            }
        )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=ROOT / "data/benchmark/questions.jsonl")
    parser.add_argument("--corpus", type=Path, default=ROOT / "data/corpus")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/review_sheet.csv")
    args = parser.parse_args()
    rows = export_review_sheet(args.questions, args.corpus, args.output)
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
