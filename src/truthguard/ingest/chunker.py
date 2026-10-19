"""Section-aware chunking that preserves exact character offsets."""

from __future__ import annotations

import re

from .loader import LoadedDocument
from ..schemas import Chunk


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", flags=re.MULTILINE)


def _section_path(headings: list[tuple[int, str]], level: int, title: str) -> str:
    while headings and headings[-1][0] >= level:
        headings.pop()
    headings.append((level, title))
    return " / ".join(item[1] for item in headings)


def chunk_document(document: LoadedDocument, *, max_words: int = 280) -> list[Chunk]:
    """Split a document by headings, then by words, without losing source spans."""

    if max_words < 1:
        raise ValueError("max_words must be positive")
    matches = list(HEADING_RE.finditer(document.text))
    sections: list[tuple[int, int, str]] = []
    headings: list[tuple[int, str]] = []
    if not matches:
        sections.append((0, len(document.text), ""))
    else:
        if matches[0].start() > 0:
            sections.append((0, matches[0].start(), ""))
        for index, match in enumerate(matches):
            level = len(match.group(1))
            section_path = _section_path(headings, level, match.group(2).strip())
            end = matches[index + 1].start() if index + 1 < len(matches) else len(document.text)
            sections.append((match.start(), end, section_path))

    chunks: list[Chunk] = []
    for section_start, section_end, section_path in sections:
        section_text = document.text[section_start:section_end]
        words = list(re.finditer(r"\S+", section_text))
        if not words:
            continue
        for start_index in range(0, len(words), max_words):
            selected = words[start_index : start_index + max_words]
            local_start = selected[0].start()
            local_end = selected[-1].end()
            char_start = section_start + local_start
            char_end = section_start + local_end
            chunk_text = document.text[char_start:char_end]
            chunk_id = f"{document.meta.doc_id}:c{len(chunks):03d}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    doc_id=document.meta.doc_id,
                    section_path=section_path,
                    text=chunk_text,
                    char_start=char_start,
                    char_end=char_end,
                    doc_meta=document.meta,
                )
            )
    return chunks
