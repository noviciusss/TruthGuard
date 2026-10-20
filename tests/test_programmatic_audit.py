"""Regression boundaries for the evidence-only audit; all fixtures are offline."""

from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import pytest

from scripts.audit_corpus_programmatic import (
    audit_metadata,
    audit_question,
    markdown,
    read_questions,
    run_audit,
)
from truthguard.ingest.loader import LoadedDocument
from truthguard.ingest.metadata import infer_metadata


ROOT = Path(__file__).resolve().parents[1]
FACTS = {
    "renewal_grace": {"topic": "renewal grace period"},
    "annual_limit": {"topic": "annual hospitalization limit"},
}


def document(doc_id, text, *, effective="2025-08-01", issued="2025-08-01", version="1.0", kind="circular"):
    full = (f"---\nDoc ID: {doc_id}\nTitle: {doc_id}\nType: {kind}\nVersion: {version}\n"
            f"Effective: {effective}\nIssued: {issued}\n---\n# {doc_id}\n{text}")
    path = Path(f"{doc_id}.md")
    meta = infer_metadata(full, path, authority_ranks={"circular": 2, "notice": 3})
    return LoadedDocument(path, full, meta)


def question(**updates):
    row = {"qid": "fixture", "question": "What is the waiting period?", "type": "T1",
           "gold_status": "resolved", "gold_answer": "45 days", "gold_winner_doc": "A",
           "gold_conflicting_docs": ["A"], "gold_claims": []}
    row.update(updates)
    return row


def get_check(result, name):
    return next(item for item in result["checks"] if item["check"] == name)


def test_actual_cited_section_and_winner_are_required():
    docs = {"A": document("A", "## Wrong\n145 days.\n## Right\n45 days."),
            "B": document("B", "## Rules\n45 days.")}
    q = question(gold_conflicting_docs=["A", "B"], source_passages=["A#Wrong", "B#Rules"])
    result = audit_question(q, docs, {}, FACTS)
    value = get_check(result, "gold_value_presence")
    assert value["status"] == "fail"
    assert value["literal_hits"] == ["B#Rules"]
    assert value["eligible_hits"] == []
    q["source_passages"][0] = "A#Right"
    assert audit_question(q, docs, {}, FACTS)["status"] == "pass"


def test_missing_document_or_heading_is_a_failure():
    docs = {"A": document("A", "## Rules\n45 days.")}
    result = audit_question(question(source_passages=["A#Invented", "MISSING#Rules"]), docs, {}, FACTS)
    refs = get_check(result, "cited_sources")
    assert result["status"] == "fail"
    assert refs["missing_docs"] == ["MISSING"]
    assert refs["missing_sections"] == ["A#Invented"]


def test_composed_quantities_are_not_semantic_or_literal_passes():
    docs = {"A": document("A", "## Rules\nMembers pay 10%; seniors pay 20%.")}
    q = question(type="T2", gold_status="conditional", gold_winner_doc=None,
                 gold_answer="10% for standard members; 20% for members aged 60 and above")
    value = get_check(audit_question(q, docs, {}, FACTS), "gold_value_presence")
    assert value["status"] == "unverifiable"
    assert value["literal_hits"] == []
    assert value["quantity_hits"] == {"10%": ["A"], "20%": ["A"]}
    # Numbers occurring in hypothetical scenarios are not fabricated source matches.
    q["gold_answer"] = "Yes; 48 months includes treatment 40 months before policy start"
    value = get_check(audit_question(q, {"A": document("A", "48 months")}, {}, FACTS), "gold_value_presence")
    assert value["status"] == "unverifiable"
    assert value["quantity_hits"]["40 months"] == []


@pytest.mark.parametrize("text,has_hit", [("## Care\nNo listed benefit.", False), ("## Care\nHearing-aid batteries are excluded.", True)])
def test_t7_no_hit_and_exclusion_mentions_remain_unverifiable(text, has_hit):
    q = question(type="T7", question="Are hearing-aid batteries covered?", gold_status="not_in_corpus",
                 gold_answer=None, gold_winner_doc=None, gold_conflicting_docs=[])
    result = audit_question(q, {"A": document("A", text)}, {}, FACTS)
    absence = get_check(result, "t7_absence")
    assert result["status"] == "unverifiable"
    assert bool(absence["hits"]) == has_hit
    assert absence["lexical_no_hit"] == (not has_hit)


def test_t7_unrecognized_subject_cannot_get_a_no_hit_pass():
    q = question(type="T7", question="Are lunar implants covered?", gold_status="not_in_corpus",
                 gold_answer=None, gold_winner_doc=None, gold_conflicting_docs=[])
    item = get_check(audit_question(q, {}, {}, FACTS), "t7_absence")
    assert item["families"] == []
    assert item["lexical_no_hit"] is False
    assert item["status"] == "unverifiable"


def test_t0_competing_values_must_be_for_the_same_fact():
    q = question(type="T0", gold_status="no_conflict", gold_answer="30 days", gold_winner_doc=None)
    docs = {"A": document("A", "## Rules\nThe renewal grace period is 30 days.\n"
                          "Members have a 30-day renewal grace period.\nClaims close in 60 days.")}
    assert get_check(audit_question(q, docs, {}, FACTS), "t0_same_fact_competition")["status"] == "pass"
    docs["B"] = document("B", "## Rules\nMembers have a 60-day renewal grace period.")
    item = get_check(audit_question(q, docs, {}, FACTS), "t0_same_fact_competition")
    assert item["status"] == "fail"
    assert [row["doc_id"] for row in item["competing_positions"]] == ["B"]


def test_t6_retains_conflicting_prose_and_operational_values_in_one_notice():
    docs = {"A": document("A", "The filed Standard plan annual limit is 500000 currency units.\n"
                          "- **annual hospitalization limit**: 600000 currency units per policy year.")}
    q = question(type="T6", gold_status="abstained", gold_answer=None, gold_winner_doc=None)
    result = audit_question(q, docs, {}, FACTS)
    positions = get_check(result, "t6_global_abstention")["other_positions"]
    assert len(positions) == 2
    assert positions[0]["values"] == ["500000 currency units"]
    assert positions[1]["values"] == ["600000 currency units"]
    assert get_check(result, "t6_global_abstention")["internal_competing_values"] == {"A": ["500000", "600000"]}


@pytest.mark.parametrize("change", [None, "issued", "effective", "authority", "manifest", "shared_manifest_drift"])
def test_t6_pair_requires_dates_authority_and_manifest_agreement(change):
    docs = {
        "A": document("A", "## Annual limit\nThe annual hospitalization limit is 500000 currency units."),
        "B": document("B", "## Annual limit\nThe annual hospitalization limit is 600000 currency units.",
                      issued="2025-08-02" if change == "issued" else "2025-08-01",
                      effective="2025-08-02" if change == "effective" else "2025-08-01",
                      kind="notice" if change == "authority" else "circular"),
        "LATER": document("LATER", "## Filing\nThe annual hospitalization limit is 500000 currency units.",
                          effective="2025-11-01", kind="notice"),
    }
    manifest_docs = {key: {"expected_metadata": doc.meta.model_dump(mode="json")} for key, doc in docs.items()}
    if change == "manifest":
        manifest_docs["B"]["expected_metadata"]["effective_date"] = "2025-09-01"
    if change == "shared_manifest_drift":
        for doc_id in ("A", "B"):
            manifest_docs[doc_id]["expected_metadata"]["effective_date"] = "2025-09-01"
    q = question(type="T6", gold_status="abstained", gold_answer=None, gold_winner_doc=None, gold_conflicting_docs=["A", "B"])
    result = audit_question(q, docs, manifest_docs, FACTS)
    assert get_check(result, "t6_pair")["status"] == ("pass" if change is None else "fail")
    global_check = get_check(result, "t6_global_abstention")
    assert global_check["status"] == "unverifiable"
    assert "LATER" in {row["doc_id"] for row in global_check["other_positions"]}


def test_metadata_recovery_does_not_hide_wrong_version_or_score_derived_annotations():
    a = document("A", "This document is effective from 2025-08-01.", effective="", version="1.0")
    b = document("B", "## Rules\nNo independent version cue.", version="0.0")
    entries = []
    for doc, kind in ((a, "missing_effective"), (b, "wrong_version")):
        expected = doc.meta.model_dump(mode="json")
        expected.update(version="1.0", metadata_source="provided", metadata_confidence=0.45)
        entries.append({"doc_id": doc.meta.doc_id, "expected_metadata": expected,
                        "metadata_corrupted": True, "header_metadata": {"corruption_kind": kind}})
    records = audit_metadata({"A": a, "B": b}, {"documents": entries})
    assert records[0]["status"] == "pass"
    assert records[1]["differences"] == {"version": {"expected": "1.0", "loaded": "0.0"}}
    assert records[1]["status"] == "fail"


def test_duplicate_qids_fail_with_line_context(tmp_path):
    path = tmp_path / "questions.jsonl"
    path.write_text((json.dumps(question()) + "\n") * 2)
    with pytest.raises(ValueError, match="questions.jsonl:2: invalid or duplicate qid"):
        read_questions(path)


def test_full_audit_is_offline_complete_and_deterministic(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Network access forbidden during audit")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setenv("TRUTHGUARD_OFFLINE", "true")
    first = run_audit(ROOT)
    second = run_audit(ROOT)
    assert first == second
    assert {name: ds["count"] for name, ds in first["datasets"].items()} == {
        "questions.jsonl": 180, "wild.jsonl": 20, "eval_subset_40.jsonl": 40,
    }
    assert first["unique_questions"] == 200
    assert len(first["metadata"]["records"]) == 35
    for ds in first["datasets"].values():
        assert sum(ds["counts"].values()) == ds["count"]
    assert all(get_check(row, "subset_membership")["status"] == "pass"
               for row in first["datasets"]["eval_subset_40.jsonl"]["records"])
    assert markdown(first) == markdown(second)
    # Serialization must preserve dates/hashes for a clean-machine rerun.
    json.dumps(first, default=str)


def test_cli_writes_reports_from_another_working_directory_and_has_strict_exit(tmp_path):
    output, json_output = tmp_path / "audit.md", tmp_path / "audit.json"
    command = [sys.executable, str(ROOT / "scripts/audit_corpus_programmatic.py"),
               "--output", str(output), "--json-output", str(json_output)]
    env = {**os.environ, "TRUTHGUARD_OFFLINE": "true"}
    result = subprocess.run(command, cwd=tmp_path, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report = json.loads(json_output.read_text())
    assert "## Measured question counts" in output.read_text()
    assert json.loads(result.stdout)["unique_questions"] == report["unique_questions"]
    strict = subprocess.run(command + ["--fail-on-findings"], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert strict.returncode == 1, strict.stderr
    invalid = subprocess.run(command + ["--root", str(tmp_path)], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert invalid.returncode == 2
    assert "Audit input/output error:" in invalid.stderr
