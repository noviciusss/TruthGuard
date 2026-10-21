"""Metadata parsing and inference for intentionally incomplete document headers."""

from __future__ import annotations

import re
from datetime import date, datetime
from difflib import get_close_matches
from pathlib import Path
from typing import Any, Iterable

from ..config import load_config
from ..schemas import DocMeta


HEADER_RE = re.compile(r"^---\s*\n(?P<body>.*?)\n---\s*(?:\n|$)", re.DOTALL)
DATE_FORMATS = ("%Y-%m-%d", "%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y")
DOC_TYPE_BY_PREFIX = {
    "POL": "policy",
    "AMD": "amendment",
    "CIR": "circular",
    "FAQ": "faq",
    "MAN": "manual",
    "NOTICE": "notice",
}


def parse_header(text: str) -> dict[str, str]:
    """Parse the simple Markdown front matter used by the corpus generator."""

    match = HEADER_RE.match(text)
    if not match:
        return {}
    values: dict[str, str] = {}
    for line in match.group("body").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip().lower().replace(" ", "_")] = value.strip()
    return values


def _parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    value = str(value).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    match = re.fullmatch(r"20\d{2}", value)
    return date(int(match.group(0)), 1, 1) if match else None


def resolve_doc_reference(reference: str, known_doc_ids: Iterable[str]) -> str | None:
    """Resolve exact, contained, or fuzzy document references without guessing freely."""

    candidates = sorted(set(known_doc_ids))
    cleaned = re.sub(r"[^A-Za-z0-9-]", "", reference).upper()
    if not cleaned:
        return None
    normalized = {re.sub(r"[^A-Za-z0-9-]", "", candidate).upper(): candidate for candidate in candidates}
    if cleaned in normalized:
        return normalized[cleaned]
    contained = [candidate for candidate in candidates if cleaned in re.sub(r"[^A-Za-z0-9-]", "", candidate).upper()]
    if len(contained) == 1:
        return contained[0]
    matches = get_close_matches(reference.upper(), candidates, n=1, cutoff=0.82)
    return matches[0] if matches else None


def _references(value: str, known_doc_ids: Iterable[str]) -> list[str]:
    if not value:
        return []
    references: list[str] = []
    for raw in re.split(r"[,;]", value):
        resolved = resolve_doc_reference(raw.strip(), known_doc_ids)
        if resolved and resolved not in references:
            references.append(resolved)
    return references


def _body_references(text: str, pattern: str, known_doc_ids: Iterable[str]) -> list[str]:
    references: list[str] = []
    for match in re.finditer(pattern, text, flags=re.IGNORECASE):
        resolved = resolve_doc_reference(match.group(1), known_doc_ids)
        if resolved and resolved not in references:
            references.append(resolved)
    return references


def _parse_amends(value: str, known_doc_ids: Iterable[str]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    if not value:
        return result
    for raw in re.split(r"[,;]", value):
        if "#" in raw:
            reference, section = raw.split("#", 1)
        else:
            reference, section = raw, ""
        resolved = resolve_doc_reference(reference.strip(), known_doc_ids)
        if resolved:
            result.append((resolved, section.strip()))
    return result


def _filename_date(path: Path) -> date | None:
    match = re.search(r"(?<!\d)(20\d{2})(?:[-_/](0?[1-9]|1[0-2]))?", path.stem)
    if not match:
        return None
    return date(int(match.group(1)), int(match.group(2) or 1), 1)


def infer_metadata(
    text: str,
    path: str | Path,
    *,
    known_doc_ids: Iterable[str] = (),
    authority_ranks: dict[str, int] | None = None,
    infer_missing: bool = True,
) -> DocMeta:
    """Infer a ``DocMeta`` while preserving unknown dates as ``None``."""

    path = Path(path)
    header = parse_header(text)
    known = list(known_doc_ids)
    doc_id = header.get("doc_id") or resolve_doc_reference(path.stem, known) or path.stem
    title_match = re.search(r"^#\s+(.+?)\s*$", text, flags=re.MULTILINE)
    title = header.get("title") or (title_match.group(1).strip() if title_match else path.stem)
    prefix = doc_id.split("-", 1)[0].upper()
    doc_type = header.get("type") or DOC_TYPE_BY_PREFIX.get(prefix, "manual")
    if doc_type not in {"policy", "amendment", "circular", "faq", "manual", "notice"}:
        doc_type = "manual"

    effective = _parse_date(header.get("effective"))
    issued = _parse_date(header.get("issued"))
    body_effective = re.search(
        r"effective\s+(?:from|on)\s+([0-9]{4}-[0-9]{2}-[0-9]{2}|\d{1,2}\s+[A-Za-z]+\s+20\d{2})",
        text,
        flags=re.IGNORECASE,
    )
    if infer_missing and effective is None and body_effective:
        effective = _parse_date(body_effective.group(1))
    if infer_missing and effective is None:
        effective = _filename_date(path)

    supersedes = _references(header.get("supersedes", ""), known)
    if infer_missing and not supersedes:
        supersedes = _body_references(
            text,
            r"(?:supersedes|replaces)\s+([A-Z][A-Z0-9-]+)",
            known,
        )
    amends = _parse_amends(header.get("amends", ""), known)
    if infer_missing and not amends:
        for match in re.finditer(
            r"amends\s+(?:Section\s+)?([A-Za-z0-9. -]+?)\s+of\s+([A-Z][A-Z0-9-]+)",
            text,
            flags=re.IGNORECASE,
        ):
            resolved = resolve_doc_reference(match.group(2), known)
            if resolved:
                amends.append((resolved, match.group(1).strip()))

    authority_ranks = authority_ranks or load_config().get("authority_rank", {})
    explicit_fields = sum(bool(header.get(key)) for key in ("doc_id", "title", "type", "version", "effective", "issued"))
    inferred_fields = int(effective is not None and not header.get("effective"))
    inferred_fields += int(bool(supersedes) and not header.get("supersedes"))
    inferred_fields += int(bool(amends) and not header.get("amends"))
    metadata_source = "provided" if explicit_fields >= 5 and inferred_fields == 0 else "inferred"
    confidence = min(1.0, 0.35 + explicit_fields * 0.1 + inferred_fields * 0.1)
    if not effective:
        confidence -= 0.2
    confidence = max(0.0, confidence)
    # The corpus generator uses 0.0 as an intentional wrong-version
    # corruption. Preserve the information loss instead of treating that
    # sentinel as a real version or copying manifest gold into runtime state.
    raw_version = header.get("version") or None
    version = None if raw_version == "0.0" else raw_version
    if raw_version == "0.0":
        confidence = 0.0
    return DocMeta(
        doc_id=doc_id,
        title=title,
        doc_type=doc_type,  # type: ignore[arg-type]
        version=version,
        effective_date=effective,
        issued_date=issued,
        supersedes=supersedes,
        amends=amends,
        authority_rank=int(authority_ranks.get(doc_type, 0)),
        metadata_source=metadata_source,
        metadata_confidence=confidence,
    )
