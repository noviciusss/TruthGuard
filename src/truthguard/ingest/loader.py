"""Load Markdown corpus documents without coupling ingestion to retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .metadata import infer_metadata
from ..schemas import DocMeta


@dataclass(frozen=True)
class LoadedDocument:
    path: Path
    text: str
    meta: DocMeta


def load_documents(
    corpus_dir: str | Path,
    *,
    authority_ranks: dict[str, int] | None = None,
    infer_metadata_fields: bool = True,
) -> list[LoadedDocument]:
    """Read all Markdown documents and infer metadata consistently."""

    directory = Path(corpus_dir)
    paths = sorted(directory.glob("*.md"))
    known_doc_ids = [path.stem for path in paths]
    documents: list[LoadedDocument] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        meta = infer_metadata(
            text,
            path,
            known_doc_ids=known_doc_ids,
            authority_ranks=authority_ranks,
            infer_missing=infer_metadata_fields,
        )
        documents.append(LoadedDocument(path=path, text=text, meta=meta))
    return documents
