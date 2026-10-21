"""Generate additive TruthGuard v2 corpus and benchmark artifacts."""

from __future__ import annotations

import argparse
import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

from generate_corpus import DocumentPlan, _fact_ids, _fact_map, _safe_filename, load_facts, render_document


ROOT = Path(__file__).resolve().parents[1]


V2_PLANS = [
    DocumentPlan("CIR-2026-T6-ROOM-A", "Circular AH/2026/T6-ROOM-A — Room Rent Cap", "circular", "2026/T6-ROOM-A", "2026-05-01", "2026-04-15", _fact_ids("t6_room_rent_cap"), (("Room rent", "The Standard plan inpatient room rent cap is 1% of sum insured per day."),), authority_rank=2, special_statements=(("t6_room_rent_cap", "1% of sum insured per day"),)),
    DocumentPlan("CIR-2026-T6-ROOM-B", "Circular AH/2026/T6-ROOM-B — Room Rent Cap", "circular", "2026/T6-ROOM-B", "2026-05-01", "2026-04-15", _fact_ids("t6_room_rent_cap"), (("Room rent", "The Standard plan inpatient room rent cap is 2% of sum insured per day."),), authority_rank=2, special_statements=(("t6_room_rent_cap", "2% of sum insured per day"),)),
    DocumentPlan("CIR-2026-T6-COPAY-A", "Circular AH/2026/T6-COPAY-A — Co-payment Rate", "circular", "2026/T6-COPAY-A", "2026-06-01", "2026-05-15", _fact_ids("t6_copay_rate"), (("Co-payment", "The Standard plan co-payment rate is 15%."),), authority_rank=2, special_statements=(("t6_copay_rate", "15%"),)),
    DocumentPlan("CIR-2026-T6-COPAY-B", "Circular AH/2026/T6-COPAY-B — Co-payment Rate", "circular", "2026/T6-COPAY-B", "2026-06-01", "2026-05-15", _fact_ids("t6_copay_rate"), (("Co-payment", "The Standard plan co-payment rate is 25%."),), authority_rank=2, special_statements=(("t6_copay_rate", "25%"),)),
    DocumentPlan("CIR-2026-T6-GRV-A", "Circular AH/2026/T6-GRV-A — Grievance Response Window", "circular", "2026/T6-GRV-A", "2026-07-01", "2026-06-15", _fact_ids("t6_grievance_response_window"), (("Grievances", "The Standard plan grievance response window is 15 days."),), authority_rank=2, special_statements=(("t6_grievance_response_window", "15 days"),)),
    DocumentPlan("CIR-2026-T6-GRV-B", "Circular AH/2026/T6-GRV-B — Grievance Response Window", "circular", "2026/T6-GRV-B", "2026-07-01", "2026-06-15", _fact_ids("t6_grievance_response_window"), (("Grievances", "The Standard plan grievance response window is 30 days."),), authority_rank=2, special_statements=(("t6_grievance_response_window", "30 days"),)),
    DocumentPlan("CIR-2026-T6-CLAIM-A", "Circular AH/2026/T6-CLAIM-A — Claim Filing Deadline", "circular", "2026/T6-CLAIM-A", "2026-08-01", "2026-07-15", _fact_ids("t6_claim_filing_deadline"), (("Claims", "The Standard plan claim filing deadline is 45 days after discharge."),), authority_rank=2, special_statements=(("t6_claim_filing_deadline", "45 days after discharge"),)),
    DocumentPlan("CIR-2026-T6-CLAIM-B", "Circular AH/2026/T6-CLAIM-B — Claim Filing Deadline", "circular", "2026/T6-CLAIM-B", "2026-08-01", "2026-07-15", _fact_ids("t6_claim_filing_deadline"), (("Claims", "The Standard plan claim filing deadline is 75 days after discharge."),), authority_rank=2, special_statements=(("t6_claim_filing_deadline", "75 days after discharge"),)),
    DocumentPlan("CIR-2026-T6-PREAUTH-A", "Circular AH/2026/T6-PREAUTH-A — Cashless Pre-authorization Window", "circular", "2026/T6-PREAUTH-A", "2026-09-01", "2026-08-15", _fact_ids("t6_cashless_preauth_window"), (("Admissions", "The cashless pre-authorization window is 2 hours before admission."),), authority_rank=2, special_statements=(("t6_cashless_preauth_window", "2 hours before admission"),)),
    DocumentPlan("CIR-2026-T6-PREAUTH-B", "Circular AH/2026/T6-PREAUTH-B — Cashless Pre-authorization Window", "circular", "2026/T6-PREAUTH-B", "2026-09-01", "2026-08-15", _fact_ids("t6_cashless_preauth_window"), (("Admissions", "The cashless pre-authorization window is 6 hours before admission."),), authority_rank=2, special_statements=(("t6_cashless_preauth_window", "6 hours before admission"),)),
    DocumentPlan("CIR-2026-T6-RENEW-A", "Circular AH/2026/T6-RENEW-A — Renewal Reinstatement Grace", "circular", "2026/T6-RENEW-A", "2026-10-01", "2026-09-15", _fact_ids("t6_renewal_grace_period"), (("Renewals", "The Standard plan renewal reinstatement grace period is 14 days after the renewal due date."),), authority_rank=2, special_statements=(("t6_renewal_grace_period", "14 days after renewal due date"),)),
    DocumentPlan("CIR-2026-T6-RENEW-B", "Circular AH/2026/T6-RENEW-B — Renewal Reinstatement Grace", "circular", "2026/T6-RENEW-B", "2026-10-01", "2026-09-15", _fact_ids("t6_renewal_grace_period"), (("Renewals", "The Standard plan renewal reinstatement grace period is 21 days after the renewal due date."),), authority_rank=2, special_statements=(("t6_renewal_grace_period", "21 days after renewal due date"),)),
]


def _t6_conflicts() -> list[dict[str, Any]]:
    return [
        {"conflict_id": f"T6-{plan.facts[0]}", "type": "T6", "fact_id": plan.facts[0], "documents": [V2_PLANS[index].doc_id, V2_PLANS[index + 1].doc_id], "correct_mode": "abstain", "winner_doc_id": None, "gold_answer": None}
        for index, plan in enumerate(V2_PLANS)
        if index % 2 == 0
    ]


def generate_v2_corpus(*, base_dir: Path, factsheet_path: Path, output_dir: Path) -> dict[str, Any]:
    factsheet = load_facts(factsheet_path)
    facts = _fact_map(factsheet)
    missing = sorted({fact_id for plan in V2_PLANS for fact_id in plan.facts if fact_id not in facts})
    if missing:
        raise ValueError(f"v2 plans reference missing facts: {missing}")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    for source in base_dir.iterdir():
        if source.name == "corpus_manifest.json":
            continue
        if source.is_file():
            # Normalize only incidental trailing whitespace in copied v1
            # Markdown. Question labels and document content remain additive;
            # this keeps the v2 artifact portable under git whitespace checks.
            destination = output_dir / source.name
            normalized = "\n".join(line.rstrip() for line in source.read_text(encoding="utf-8").splitlines()) + "\n"
            destination.write_text(normalized, encoding="utf-8")
    base_manifest = json.loads((base_dir / "corpus_manifest.json").read_text(encoding="utf-8"))
    manifest = deepcopy(base_manifest)
    manifest["manifest_version"] = 2
    manifest["generator"] = "bench.generate_v2"
    manifest["document_count"] = len(base_manifest["documents"]) + len(V2_PLANS)
    manifest["metadata_corrupted_count"] = base_manifest["metadata_corrupted_count"]
    manifest["metadata_corrupted_fraction"] = manifest["metadata_corrupted_count"] / manifest["document_count"]
    manifest["fact_use_counts"] = dict(base_manifest["fact_use_counts"])
    for plan in V2_PLANS:
        manifest["fact_use_counts"][plan.facts[0]] = 2
    for index, plan in enumerate(V2_PLANS):
        # Use only non-corrupt indices for the deliberately auditable tie pairs.
        meta, text, header_meta = render_document(plan, facts, 2 + index * 5)
        path = output_dir / _safe_filename(plan.doc_id)
        path.write_text(text, encoding="utf-8")
        manifest["documents"].append({
            "doc_id": plan.doc_id,
            "path": path.name,
            "title": plan.title,
            "doc_type": plan.doc_type,
            "expected_metadata": meta.model_dump(mode="json"),
            "header_metadata": header_meta,
            "metadata_corrupted": False,
            "sections": [section for section, _ in plan.sections] + ["Operational rules", "Contact"],
            "char_count": len(text),
        })
    manifest["conflicts"] = list(base_manifest["conflicts"]) + _t6_conflicts()
    manifest["gold_adjudication"] = {
        **base_manifest.get("gold_adjudication", {}),
        "v2_genuine_t6": {
            "fact_keys": [plan.facts[0] for plan in V2_PLANS[::2]],
            "pair_rule": "Exactly two circulars per fact key; equal effective/issued dates and authority rank; no supersedes/amends edge; no third document mentions the key.",
            "question_additions": {"dev": 4, "test": 6, "wild": 2},
        },
    }
    manifest["audit"] = {"status": "offline-v2-genuine-t6", "llm_audit_required": False}
    (output_dir / "corpus_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=ROOT / "data/corpus")
    parser.add_argument("--factsheet", type=Path, default=ROOT / "data/factsheet/aurelia_facts_v2.yaml")
    parser.add_argument("--output", type=Path, default=ROOT / "data/corpus_v2")
    args = parser.parse_args()
    manifest = generate_v2_corpus(base_dir=args.base, factsheet_path=args.factsheet, output_dir=args.output)
    print(f"Generated {manifest['document_count']} v2 documents in {args.output}")


if __name__ == "__main__":
    main()
