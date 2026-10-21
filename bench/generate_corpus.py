"""Generate the deterministic synthetic Aurelia Health document corpus.

Templates and explicit owner adjudications produce a reproducible, offline
corpus. The companion programmatic audit reads physical evidence without any
provider calls; manifest annotations are never runtime metadata recovery cues.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from truthguard.schemas import DocMeta


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class DocumentPlan:
    doc_id: str
    title: str
    doc_type: str
    version: str
    effective_date: str
    issued_date: str
    facts: tuple[str, ...]
    sections: tuple[tuple[str, str], ...]
    supersedes: tuple[str, ...] = ()
    amends: tuple[tuple[str, str], ...] = ()
    authority_rank: int = 0
    special_statements: tuple[tuple[str, str], ...] = ()


AUTHORITY = {"policy": 4, "amendment": 3, "notice": 3, "circular": 2, "manual": 1, "faq": 0}


def _fact_ids(*values: str) -> tuple[str, ...]:
    return tuple(values)


def document_plans() -> list[DocumentPlan]:
    """Return the fixed 35-document plan used by every generation run."""

    return [
        DocumentPlan("POL-2024-V1", "Aurelia Health Standard Policy Wording v1", "policy", "1.0", "2024-01-01", "2023-12-15", _fact_ids("waiting_period", "copay", "claim_deadline", "pre_existing_lookback", "preauthorization"), (("Eligibility", "The Standard plan covers eligible members and covered hospitalization."), ("Benefits", "The benefit schedule applies to covered services.")), authority_rank=4, special_statements=(("copay", "10% for standard plan members"), ("preauthorization", "All planned admissions require pre-authorization"))),
        DocumentPlan("POL-2025-V2", "Aurelia Health Standard Policy Wording v2", "policy", "2.0", "2025-06-01", "2025-05-01", _fact_ids("waiting_period", "copay", "claim_deadline", "pre_existing_lookback", "preauthorization"), (("Eligibility", "The Standard plan covers eligible members and covered hospitalization."), ("Benefits", "The revised benefit schedule applies from the effective date.")), supersedes=("POL-2024-V1",), authority_rank=4, special_statements=(("copay", "10% for standard plan members"), ("preauthorization", "All planned admissions require pre-authorization"))),
        DocumentPlan("POL-2026-V3", "Aurelia Health Standard Policy Wording v3", "policy", "3.0", "2026-01-01", "2025-12-01", _fact_ids("renewal_grace", "grievance_timeline", "annual_limit", "telemedicine", "maternity"), (("Administration", "This consolidated wording applies to the Standard plan."), ("Benefits", "Benefits remain subject to eligibility and exclusions.")), supersedes=("POL-2025-V2",), authority_rank=4, special_statements=(("annual_limit", "600000 currency units per policy year"),)),
        DocumentPlan("AMD-2025-03", "Amendment AH/2025/03 — Hospitalization Waiting Period", "amendment", "2025-03", "2025-03-01", "2025-02-15", _fact_ids("waiting_period"), (("Section 4.1", "The non-accidental hospitalization waiting period is 45 days."),), supersedes=(), amends=(("POL-2024-V1", "Section 4.1"),), authority_rank=3),
        DocumentPlan("AMD-2025-04", "Amendment AH/2025/04 — Claim Submission", "amendment", "2025-04", "2025-04-15", "2025-04-01", _fact_ids("claim_deadline"), (("Section 8.2", "A reimbursement claim must be submitted within 60 days after discharge."),), amends=(("POL-2024-V1", "Section 8.2"),), authority_rank=3),
        DocumentPlan("AMD-2025-05", "Amendment AH/2025/05 — Pre-existing Conditions", "amendment", "2025-05", "2025-05-01", "2025-04-20", _fact_ids("pre_existing_lookback"), (("Section 3.2", "The lookback period for a pre-existing condition is 48 months."),), amends=(("POL-2024-V1", "Section 3.2"),), authority_rank=3),
        DocumentPlan("AMD-2025-07", "Amendment AH/2025/07 — Maternity", "amendment", "2025-07", "2025-07-01", "2025-06-15", _fact_ids("maternity"), (("Section 11", "Premium plan maternity waiting period is 18 months."),), amends=(("POL-2025-V2", "Section 11"),), authority_rank=3),
        DocumentPlan("AMD-2025-09", "Amendment AH/2025/09 — Network Hospitals", "amendment", "2025-09", "2025-09-01", "2025-08-15", _fact_ids("network_cashless"), (("Section 6", "Cashless treatment requires an active network hospital and approval."),), amends=(("POL-2025-V2", "Section 6"),), authority_rank=3),
        DocumentPlan("AMD-2026-01", "Amendment AH/2026/01 — Telemedicine", "amendment", "2026-01", "2026-01-01", "2025-12-15", _fact_ids("telemedicine"), (("Section 12", "Members receive four telemedicine consultations per policy year."),), amends=(("POL-2025-V2", "Section 12"),), authority_rank=3),
        DocumentPlan("AMD-2026-02", "Amendment AH/2026/02 — Grievances", "amendment", "2026-02", "2026-02-01", "2026-01-15", _fact_ids("grievance_timeline"), (("Section 14", "Grievances are resolved within 30 days."),), amends=(("POL-2025-V2", "Section 14"),), authority_rank=3),
        DocumentPlan("AMD-2026-03", "Amendment AH/2026/03 — Ambulance", "amendment", "2026-03", "2026-03-01", "2026-02-15", _fact_ids("ambulance_limit"), (("Section 7", "The road ambulance benefit is capped at 10000 currency units per hospitalization."),), amends=(("POL-2024-V1", "Section 7"),), authority_rank=3),
        DocumentPlan("AMD-2026-04", "Amendment AH/2026/04 — Exclusions", "amendment", "2026-04", "2026-04-01", "2026-03-15", _fact_ids("exclusions"), (("Section 15", "Cosmetic treatment remains excluded unless medically necessary after an accident."),), amends=(("POL-2025-V2", "Section 15"),), authority_rank=3),
        DocumentPlan("CIR-2024-01", "Circular AH/2024/01 — Member Administration", "circular", "2024/01", "2024-02-01", "2024-01-20", _fact_ids("renewal_grace"), (("Renewals", "A renewal may be completed within 30 days after the due date."),), authority_rank=2),
        DocumentPlan("CIR-2024-02", "Circular AH/2024/02 — Co-payment Examples", "circular", "2024/02", "2024-03-01", "2024-02-15", _fact_ids("copay"), (("Examples", "Standard plan members pay 10%; members aged 60 and above pay 20%."),), authority_rank=2, special_statements=(("copay", "10% for standard plan members; 20% for members aged 60 and above"),)),
        DocumentPlan("CIR-2024-03", "Circular AH/2024/03 — Room Rent Schedule", "circular", "2024/03", "2024-04-01", "2024-03-20", _fact_ids("room_rent"), (("Schedule", "Standard room rent is 1% and Premium room rent is 2% of sum insured per day."),), authority_rank=2),
        DocumentPlan("CIR-2025-06", "Circular AH/2025/06 — Emergency Admission Exception", "circular", "2025/06", "2025-06-01", "2025-05-20", _fact_ids("preauthorization"), (("Emergency exception", "Emergency admissions may use cashless treatment without prior approval if Aurelia is notified within 24 hours."),), amends=(("POL-2025-V2", "Section 5.4"),), authority_rank=2),
        DocumentPlan("CIR-2025-08-A", "Circular AH/2025/08-A — Annual Limit", "circular", "2025/08-A", "2025-08-01", "2025-08-01", _fact_ids("annual_limit"), (("Annual limit", "The Aurelia Standard plan annual hospitalization limit is 500000 currency units."),), authority_rank=2, special_statements=(("annual_limit", "500000 currency units per policy year"),)),
        DocumentPlan("CIR-2025-08-B", "Circular AH/2025/08-B — Annual Limit", "circular", "2025/08-B", "2025-08-01", "2025-08-01", _fact_ids("annual_limit"), (("Annual limit", "The Aurelia Standard plan annual hospitalization limit is 600000 currency units."),), authority_rank=2, special_statements=(("annual_limit", "600000 currency units per policy year"),)),
        DocumentPlan("CIR-2025-10", "Circular AH/2025/10 — Renewal Operations", "circular", "2025/10", "2025-10-01", "2025-09-15", _fact_ids("renewal_grace"), (("Renewals", "The 30-day renewal grace period applies to all active plans."),), authority_rank=2),
        DocumentPlan("CIR-2026-01", "Circular AH/2026/01 — Digital Care", "circular", "2026/01", "2026-01-10", "2025-12-20", _fact_ids("telemedicine"), (("Digital care", "Four telemedicine consultations are available per policy year."),), authority_rank=2),
        DocumentPlan("CIR-2026-02", "Circular AH/2026/02 — Ambulance Claims", "circular", "2026/02", "2026-02-10", "2026-01-25", _fact_ids("ambulance_limit"), (("Ambulance", "Road ambulance reimbursement is limited to 10000 currency units per hospitalization."),), authority_rank=2),
        DocumentPlan("FAQ-2024-01", "Aurelia Health FAQ — Waiting Periods", "faq", "2024.1", "2024-02-15", "2024-02-15", _fact_ids("waiting_period"), (("Question", "How long is the hospitalization waiting period?"), ("Answer", "The Standard plan has a 30-day waiting period for non-accidental hospitalization."),), authority_rank=0),
        DocumentPlan("FAQ-2024-02", "Aurelia Health FAQ — Definitions", "faq", "2024.2", "2024-03-15", "2024-03-15", _fact_ids("pre_existing_lookback"), (("Question", "What is a pre-existing condition?"), ("Answer", "The lookback period is 36 months before policy start."),), authority_rank=0),
        DocumentPlan("FAQ-2025-01", "Aurelia Health FAQ — Plan Comparisons", "faq", "2025.1", "2025-01-15", "2025-01-15", _fact_ids("room_rent", "copay"), (("Question", "Do plan rules differ?"), ("Answer", "Standard and Premium plans have different room-rent limits; age can also change co-payment."),), authority_rank=0),
        DocumentPlan("FAQ-2025-06", "Aurelia Health FAQ — Current Benefits", "faq", "2025.6", "2025-06-15", "2025-06-15", _fact_ids("waiting_period", "pre_existing_lookback", "maternity"), (("Current answer", "The current waiting period is 45 days; the pre-existing condition lookback is 48 months."),), authority_rank=0),
        DocumentPlan("FAQ-2026-01", "Aurelia Health FAQ — Renewal", "faq", "2026.1", "2026-01-20", "2026-01-20", _fact_ids("renewal_grace"), (("Answer", "Members have a 30-day renewal grace period."),), authority_rank=0),
        DocumentPlan("FAQ-2026-02", "Aurelia Health FAQ — Network and Digital Care", "faq", "2026.2", "2026-02-20", "2026-02-20", _fact_ids("network_cashless", "telemedicine"), (("Answer", "Network cashless care requires approval; members have four telemedicine consultations per year."),), authority_rank=0),
        DocumentPlan("MAN-2024-CLAIMS", "Claims Processing Manual 2024", "manual", "2024", "2024-01-10", "2024-01-10", _fact_ids("claim_deadline", "exclusions"), (("Claims", "Submit reimbursement claims within 30 days after discharge."), ("Exclusions", "Cosmetic treatment is excluded unless medically necessary after an accident."),), authority_rank=1),
        DocumentPlan("MAN-2025-CLAIMS", "Claims Processing Manual 2025", "manual", "2025", "2025-05-15", "2025-05-15", _fact_ids("claim_deadline"), (("Claims", "Submit reimbursement claims within 60 days after discharge."),), authority_rank=1),
        DocumentPlan("MAN-2025-CASHLESS", "Cashless Hospital Operations Manual", "manual", "2025", "2025-06-15", "2025-06-15", _fact_ids("preauthorization", "network_cashless"), (("Operations", "Planned admissions require pre-authorization. Emergency admissions may be notified within 24 hours."),), authority_rank=1),
        DocumentPlan("MAN-2026-GRIEVANCE", "Member Grievance Operations Manual", "manual", "2026", "2026-02-15", "2026-02-15", _fact_ids("grievance_timeline"), (("Grievances", "Acknowledge within 3 business days and resolve within 30 days."),), authority_rank=1),
        DocumentPlan("NOTICE-2024-01", "Regulatory Notice AH/2024/01 — Coverage Disclosures", "notice", "2024/01", "2024-05-01", "2024-05-01", _fact_ids("exclusions"), (("Disclosure", "Cosmetic treatment is not covered unless medically necessary after an accident."),), authority_rank=3),
        DocumentPlan("NOTICE-2025-02", "Regulatory Notice AH/2025/02 — Emergency Cashless", "notice", "2025/02", "2025-06-05", "2025-06-05", _fact_ids("preauthorization"), (("Emergency care", "Emergency admissions can proceed without prior approval, followed by notification within 24 hours."),), authority_rank=3),
        DocumentPlan("NOTICE-2025-11", "Regulatory Notice AH/2025/11 — Annual Limit Filing", "notice", "2025/11", "2025-11-01", "2025-11-01", _fact_ids("annual_limit"), (("Filing", "The filed Standard plan annual limit is 500000 currency units."),), authority_rank=3, special_statements=(("annual_limit", "500000 currency units per policy year"),)),
        DocumentPlan("NOTICE-2026-01", "Regulatory Notice AH/2026/01 — Grievance Standard", "notice", "2026/01", "2026-01-05", "2026-01-05", _fact_ids("grievance_timeline"), (("Standard", "Grievances should be resolved within 30 days."),), authority_rank=3),
    ]


def load_facts(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not data.get("facts"):
        raise ValueError("Factsheet must contain a non-empty facts list")
    ids = [fact.get("fact_id") for fact in data["facts"]]
    if len(ids) != len(set(ids)) or any(not fact_id for fact_id in ids):
        raise ValueError("Factsheet fact_id values must be unique and non-empty")
    return data


def _fact_map(factsheet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {fact["fact_id"]: fact for fact in factsheet["facts"]}


def _statement(fact: dict[str, Any], effective_date: str) -> str:
    target = date.fromisoformat(effective_date)
    eligible = [(date.fromisoformat(str(item["effective_date"])), str(item["value"]))
                for item in fact["versions"] if date.fromisoformat(str(item["effective_date"])) <= target]
    if not eligible:
        raise ValueError(f"No in-force value for {fact['fact_id']} at {effective_date}")
    latest = max(day for day, _ in eligible)
    values = sorted({value for day, value in eligible if day == latest})
    if len(values) > 1 and fact["fact_id"] not in {"copay", "room_rent"}:
        raise ValueError(f"No unique in-force value for {fact['fact_id']} at {effective_date}: {values}; explicit adjudication required")
    # These two schedules explicitly name distinct age/plan scopes. Preserve both,
    # rather than using YAML list order as precedence between simultaneous entries.
    return "; ".join(values)


def _frontmatter(meta: DocMeta, *, corrupt_kind: str | None = None) -> str:
    effective = "" if corrupt_kind == "missing_effective" else (meta.effective_date.isoformat() if meta.effective_date else "")
    version = "0.0" if corrupt_kind == "wrong_version" else (meta.version or "")
    supersedes = ", ".join(meta.supersedes)
    return "\n".join(
        [
            "---",
            f"Doc ID: {meta.doc_id}",
            f"Title: {meta.title}",
            f"Type: {meta.doc_type}",
            f"Version: {version}",
            f"Effective: {effective}",
            f"Issued: {meta.issued_date.isoformat() if meta.issued_date else ''}",
            f"Supersedes: {supersedes}".rstrip(),
            f"Amends: {', '.join(f'{doc_id}#{section}' for doc_id, section in meta.amends)}".rstrip(),
            "---",
            "",
        ]
    )


def _safe_filename(doc_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", doc_id) + ".md"


def render_document(plan: DocumentPlan, facts: dict[str, dict[str, Any]], index: int) -> tuple[DocMeta, str, dict[str, Any]]:
    metadata_corrupted = index % 5 in (0, 1)
    corrupt_kind = "missing_effective" if index % 5 == 0 else ("wrong_version" if index % 5 == 1 else None)
    meta = DocMeta(
        doc_id=plan.doc_id,
        title=plan.title,
        doc_type=plan.doc_type,  # type: ignore[arg-type]
        version=plan.version,
        effective_date=date.fromisoformat(plan.effective_date),
        issued_date=date.fromisoformat(plan.issued_date),
        supersedes=list(plan.supersedes),
        amends=list(plan.amends),
        authority_rank=plan.authority_rank or AUTHORITY[plan.doc_type],
        metadata_source="provided",
        metadata_confidence=0.45 if metadata_corrupted else 1.0,
    )
    lines = [_frontmatter(meta, corrupt_kind=corrupt_kind), f"# {plan.title}", ""]
    lines.append(f"This document is effective from {plan.effective_date}.")
    if plan.supersedes:
        lines.append(f"This document supersedes {', '.join(plan.supersedes)}.")
    if plan.amends:
        lines.append(
            "This document amends "
            + ", ".join(
                f"{section if section.lower().startswith('section ') else 'Section ' + section} of {doc_id}"
                for doc_id, section in plan.amends
            )
            + "."
        )
    lines.append("")
    for section, text in plan.sections:
        lines.extend([f"## {section}", text, ""])
    if plan.facts:
        lines.extend(["## Operational rules", ""])
        overrides = dict(plan.special_statements)
        for fact_id in plan.facts:
            fact = facts[fact_id]
            value = overrides[fact_id] if fact_id in overrides else _statement(fact, plan.effective_date)
            lines.append(f"- **{fact['topic']}** ({fact['scope']}): {value}.")
        lines.append("")
    lines.extend(["## Contact", "Members may contact Aurelia Health support for clarification.", ""])
    header_meta = {
        "effective_date": None if corrupt_kind == "missing_effective" else plan.effective_date,
        "version": "0.0" if corrupt_kind == "wrong_version" else plan.version,
        "metadata_corrupted": metadata_corrupted,
        "corruption_kind": corrupt_kind,
    }
    return meta, "\n".join(lines), header_meta


def conflict_manifest() -> list[dict[str, Any]]:
    return [
        {"conflict_id": "T1-waiting-period", "type": "T1", "documents": ["POL-2024-V1", "AMD-2025-03"], "correct_mode": "supersession", "winner_doc_id": "AMD-2025-03", "gold_answer": "45 days"},
        {"conflict_id": "T2-copay-scope", "type": "T2", "documents": ["CIR-2024-02", "POL-2024-V1"], "correct_mode": "contextual", "winner_doc_id": None, "gold_answer": "10% for standard members; 20% for members aged 60 and above"},
        {"conflict_id": "T3-claim-deadline", "type": "T3", "documents": ["POL-2024-V1", "AMD-2025-04"], "correct_mode": "supersession", "winner_doc_id": "AMD-2025-04", "gold_answer": "60 days after discharge"},
        {"conflict_id": "T4-lookback-definition", "type": "T4", "documents": ["FAQ-2024-02", "AMD-2025-05"], "correct_mode": "supersession", "winner_doc_id": "AMD-2025-05", "gold_answer": "48 months"},
        {"conflict_id": "T5-emergency-preauth", "type": "T5", "documents": ["POL-2025-V2", "CIR-2025-06"], "correct_mode": "contextual", "winner_doc_id": None, "gold_answer": "Planned admissions require prior approval; emergency admissions may proceed without it if notified within 24 hours"},
        {"conflict_id": "T3-annual-limit", "original_conflict_id": "T6-annual-limit", "type": "T3", "documents": ["CIR-2025-08-A", "CIR-2025-08-B", "NOTICE-2025-11", "POL-2026-V3"], "correct_mode": "supersession", "winner_doc_id": "POL-2026-V3", "gold_answer": "600000 currency units per policy year"},
        {"conflict_id": "T0-renewal-grace", "type": "T0", "documents": ["CIR-2024-01", "CIR-2025-10"], "correct_mode": None, "winner_doc_id": None, "gold_answer": "30 days"},
        {"conflict_id": "T7-hearing-aid", "type": "T7", "documents": [], "correct_mode": "abstain", "winner_doc_id": None, "gold_answer": None},
    ]


def generate_corpus(
    factsheet_path: str | Path,
    output_dir: str | Path,
    *,
    seed: int = 7,
) -> dict[str, Any]:
    """Generate all documents and return/write a self-contained manifest."""

    # The plan is deterministic; retain the argument for future LLM generation.
    factsheet = load_facts(factsheet_path)
    facts = _fact_map(factsheet)
    plans = document_plans()
    unknown = sorted({fact_id for plan in plans for fact_id in plan.facts if fact_id not in facts})
    if unknown:
        raise ValueError(f"Document plan references unknown facts: {unknown}")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    documents: list[dict[str, Any]] = []
    fact_use: dict[str, int] = {fact_id: 0 for fact_id in facts}
    for index, plan in enumerate(plans):
        meta, text, header_meta = render_document(plan, facts, index)
        for fact_id in plan.facts:
            fact_use[fact_id] += 1
        filename = _safe_filename(plan.doc_id)
        path = output / filename
        path.write_text(text, encoding="utf-8")
        documents.append(
            {
                "doc_id": plan.doc_id,
                "path": str(path.name),
                "title": plan.title,
                "doc_type": plan.doc_type,
                "expected_metadata": meta.model_dump(mode="json"),
                "header_metadata": header_meta,
                "metadata_corrupted": header_meta["metadata_corrupted"],
                "sections": [section for section, _ in plan.sections] + ["Operational rules", "Contact"],
                "char_count": len(text),
            }
        )

    if len(documents) < 35:
        raise AssertionError("Corpus must contain at least 35 documents")
    manifest = {
        "manifest_version": 1,
        "domain": factsheet.get("domain", "Aurelia Health"),
        "generator": "bench.generate_corpus",
        "seed": seed,
        "document_count": len(documents),
        "metadata_corrupted_count": sum(item["metadata_corrupted"] for item in documents),
        "metadata_corrupted_fraction": sum(item["metadata_corrupted"] for item in documents) / len(documents),
        "fact_use_counts": fact_use,
        "documents": documents,
        "conflicts": conflict_manifest(),
        "gold_adjudication": {
            "annual_limit": {
                "scope": "Aurelia Standard plan",
                "history": "Simultaneous 500000/600000 entries effective 2025-08-01; no unique in-force value before the notice. List order is not precedence.",
                "notice": {"doc_id": "NOTICE-2025-11", "value": "500000 currency units per policy year", "effective_date": "2025-11-01", "authority_rank": 3, "basis": "Explicit owner adjudication: both Filing and Operational rules use fallback 500000."},
                "current": {"doc_id": "POL-2026-V3", "value": "600000 currency units per policy year", "effective_date": "2026-01-01", "authority_rank": 4, "type": "T3", "correct_mode": "supersession", "source_passage": "POL-2026-V3#Operational rules"},
                "genuine_current_whole_corpus_t6": 0,
                "t6_target_blocker": "Existing fact conflicts supply no 12 defensible current whole-corpus T6 examples; do not invent evidence or restrict queries to the August pair.",
            },
        },
        "audit": {"status": "offline-owner-adjudicated-gold", "llm_audit_required": False},
    }
    (output / "corpus_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    documents = manifest.get("documents", [])
    doc_ids = {item.get("doc_id") for item in documents}
    if len(doc_ids) != len(documents):
        errors.append("document IDs are not unique")
    if len(documents) < 35:
        errors.append("fewer than 35 documents")
    for item in manifest.get("conflicts", []):
        missing = sorted(set(item.get("documents", [])) - doc_ids)
        if missing:
            errors.append(f"{item.get('conflict_id')} references missing docs: {missing}")
        if item.get("type") not in {"T0", "T1", "T2", "T3", "T4", "T5", "T6", "T7"}:
            errors.append(f"invalid conflict type in {item.get('conflict_id')}")
    for fact_id, count in manifest.get("fact_use_counts", {}).items():
        if count < 2 or count > 5:
            errors.append(f"fact {fact_id} appears {count} times; expected 2-5")
    fraction = manifest.get("metadata_corrupted_fraction", 0)
    if not 0.35 <= fraction <= 0.45:
        errors.append(f"metadata corruption fraction {fraction:.3f} is outside target range")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--factsheet", type=Path, default=ROOT / "data/factsheet/aurelia_facts.yaml")
    parser.add_argument("--output", type=Path, default=ROOT / "data/corpus")
    args = parser.parse_args()
    manifest = generate_corpus(args.factsheet, args.output)
    errors = validate_manifest(manifest)
    if errors:
        raise SystemExit("Corpus validation failed:\n- " + "\n- ".join(errors))
    print(f"Generated {manifest['document_count']} documents in {args.output}")
    print(f"Metadata corruption: {manifest['metadata_corrupted_fraction']:.1%}")


if __name__ == "__main__":
    main()
