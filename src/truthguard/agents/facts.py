"""Conservative, sentence-local fact observations for the deterministic critic.

No benchmark labels or manifest values are consulted here. Numbers in document
headers, other facts, ages, dates and section names are not competing values.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..schemas import Chunk, Position, Span


@dataclass(frozen=True)
class FactObservation:
    key: str
    value: str
    scope: str
    text: str
    chunk: Chunk
    start: int
    end: int

    def position(self) -> Position:
        return Position(
            claim_text=self.text, doc_id=self.chunk.doc_id,
            span=Span(chunk_id=self.chunk.chunk_id, char_start=self.start, char_end=self.end),
            doc_meta=self.chunk.doc_meta,
        )


def _scope(text: str) -> str:
    lower = text.lower()
    if re.search(r"aged?\s+60|senior", lower):
        return "senior"
    if "premium" in lower:
        return "premium"
    if "standard" in lower:
        return "standard"
    return "unspecified"


def _segments(chunk: Chunk):
    for match in re.finditer(r"[^\n]+", chunk.text):
        line = match.group()
        # An explicit Markdown fact key governs its semicolon value clauses.
        # Prose clauses must each identify their own fact; do not carry a
        # numeric topic across sentence or semicolon boundaries.
        parts = [line] if "**" in line and ":" in line else re.split(r"(?<=[.!?])\s+|;\s*", line)
        offset = 0
        for part in parts:
            index = line.find(part, offset)
            offset = index + len(part)
            text = part.strip()
            if text:
                start = chunk.char_start + match.start() + index + len(part) - len(part.lstrip())
                yield text, start


def observations(chunk: Chunk) -> list[FactObservation]:
    """Extract only values bound to an explicit fact in the same physical line."""
    found = []
    for text, start in _segments(chunk):
        if not text or text.startswith("#"):
            continue
        lower = text.lower()
        value_text = text.split(":", 1)[1] if "**" in text and ":" in text else text
        values_lower = value_text.lower()
        key = None
        pattern = None
        if "hospitalization" in lower and "waiting period" in lower:
            key, pattern = "waiting_period", r"\b(\d+)\s*[- ]?\s*days?\b"
        elif re.search(r"co[- ]?pay(?:ment)?", lower):
            key, pattern = "copay", r"\b(\d+(?:\.\d+)?)\s*%"
        elif "claim" in lower and ("discharge" in lower or "reimbursement" in lower) and re.search(r"deadline|submi|fil", lower):
            key, pattern = "claim_deadline", r"\b(\d+)\s*[- ]?\s*days?\b"
        elif re.search(r"look[- ]?back|pre[- ]existing", lower):
            key, pattern = "lookback", r"\b(\d+)\s*[- ]?\s*months?\b"
        elif "room rent" in lower:
            key, pattern = "room_rent", r"\b(\d+(?:\.\d+)?)\s*%"
        elif "renewal" in lower and re.search(r"grace|due date|completed", lower):
            key, pattern = "renewal", r"\b(\d+)\s*[- ]?\s*days?\b"
        elif "annual" in lower and "limit" in lower:
            key, pattern = "annual_limit", r"\b(\d[\d,]*)\s+currency units?\b"

        end = start + len(text)
        if key and pattern:
            # Each semicolon clause carries its own value/scope. This prevents
            # treating a senior age as a percentage, or two equal rule lists as
            # unrelated numeric disagreement.
            for clause in value_text.split(";"):
                for value_match in re.finditer(pattern, clause, flags=re.IGNORECASE):
                    value = value_match.group(1).replace(",", "")
                    found.append(FactObservation(key, value, _scope(clause), text, chunk, start, end))

        if re.search(r"pre[- ]authorization|prior approval", lower):
            if "planned" in values_lower and re.search(r"require|must|obtain", values_lower):
                found.append(FactObservation("preauthorization", "required", "planned", text, chunk, start, end))
            if "emergency" in values_lower and re.search(r"without|exception", values_lower):
                # A notification duration is evidence for the exception's
                # conditions, not a conflicting authorization value itself.
                if re.search(r"\b\d+\s*hours?", values_lower) and re.search(r"notif", values_lower):
                    found.append(FactObservation("preauthorization", "not-required-with-notification", "emergency", text, chunk, start, end))
    return found


def typed_pair(left: FactObservation, right: FactObservation, graph=None, *, as_of=None) -> str | None:
    """Require distinct documents, same fact, different values, and type evidence."""
    if left.chunk.doc_id == right.chunk.doc_id or left.key != right.key or left.value == right.value:
        return None
    a, b = left.chunk.doc_meta, right.chunk.doc_meta
    if a is None or b is None:
        return None
    if left.key == "preauthorization":
        return "T5" if {left.scope, right.scope} == {"planned", "emergency"} else None
    if left.key in {"copay", "room_rent"}:
        expected = {"standard", "senior"} if left.key == "copay" else {"standard", "premium"}
        return "T2" if {left.scope, right.scope} == expected else None
    if left.scope != right.scope and "unspecified" not in {left.scope, right.scope}:
        return None
    if left.key == "annual_limit":
        if a.effective_date and a.effective_date == b.effective_date and a.authority_rank == b.authority_rank:
            return "T6"
    if left.key == "waiting_period":
        if graph is not None:
            for newer, older in ((a.doc_id, b.doc_id), (b.doc_id, a.doc_id)):
                if graph.graph.has_edge(newer, older):
                    edge = graph.graph.edges[newer, older]
                    section = edge.get("section")
                    if section is None or any(section.lower() in item.chunk.section_path.lower() for item in (left, right)):
                        return "T1"
        return None
    if left.key in {"claim_deadline", "lookback", "annual_limit"}:
        # Version/numeric resolution requires actual temporal ordering. A date
        # missing from metadata is not invented to justify a conflict type.
        if a.effective_date and b.effective_date and a.effective_date != b.effective_date:
            return "T4" if left.key == "lookback" else "T3"
    return None
