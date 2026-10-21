"""Offline, evidence-only benchmark audit. Never runs retrieval or a provider.

Run from any directory with Python 3.11 and the project's pinned dependencies:
    .venv/bin/python scripts/audit_corpus_programmatic.py
Exit 0 means the audit ran, not that the benchmark passed. --fail-on-findings
returns 1 for failures OR unverifiable results; malformed inputs return 2.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import yaml

from truthguard.ingest.loader import load_documents
from truthguard.ingest.metadata import HEADER_RE, parse_header


# Explicit, bounded lexical probes; no embeddings, inferred synonyms, or runtime tuning.
ABSENCE_PROBES = {
    "hearing aid": (r"hearing[\s-]*aids?", r"batter(?:y|ies)"),
    "robotic home surgery": (r"robot(?:ic)?", r"home[\s-]+surg(?:ery|ical)"),
    "gene therapy": (r"gene[\s-]+therap(?:y|ies)", r"genetic[\s-]+therap(?:y|ies)"),
    "underwater rehabilitation": (r"underwater", r"aquatic", r"hydrotherap(?:y|ies)"),
}
QUANTITY = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?:\s*-\s*|\s*)(?:%|days?\b|months?\b|hours?\b|currency units?\b)", re.I)
SCOPED_QUANTITY = re.compile(r"(?<![\w.])(?:\d+(?:\.\d+)?|four)(?:\s*-\s*|\s*)(?:%|business days?\b|days?\b|months?\b|hours?\b|currency units?\b|telemedicine consultations?\b)", re.I)
PHYSICAL_FIELDS = ("doc_id", "title", "doc_type", "version", "effective_date", "issued_date", "authority_rank", "supersedes", "amends")
FACT_PATTERNS = {
    "waiting_period": r"(?<!maternity )waiting period",
    "copay": r"co[ -]?pay(?:ment)?|members? (?:aged 60 and above )?pay",
    "claim_deadline": r"claim submission deadline|(?:reimbursement )?claims?.*(?:submit|discharge)|submit.*claims?",
    "pre_existing_lookback": r"look[ -]?back|pre-existing condition",
    "preauthorization": r"pre[ -]?authorization|prior approval|(?:planned|emergency) admissions?",
    "room_rent": r"room[ -]rent",
    "renewal_grace": r"renewal.*(?:grace|completed)",
    "grievance_timeline": r"grievance|acknowledge|acknowledgement|resolve|resolution",
    "network_cashless": r"network.*(?:hospital|cashless)|cashless.*network",
    "ambulance_limit": r"ambulance",
    "annual_limit": r"annual\s+(?:hospitalization\s+)?limit",
    "telemedicine": r"telemedicine",
    "maternity": r"maternity",
    "exclusions": r"cosmetic",
}


def normalized(text: str) -> str:
    """Case/whitespace only: deliberately no paraphrase or punctuation rewriting."""
    return " ".join(text.casefold().split())


def present(value: str, text: str) -> bool:
    # A substring of 145 days must not establish the value 45 days.
    return re.search(r"(?<!\w)" + re.escape(normalized(value)) + r"(?!\w)", normalized(text)) is not None


def canonical_quantity(value: str) -> str:
    """Only same-fact competition treats 30-day and 30 days as one duration."""
    value = re.sub(r"(?<=\d)\s*-\s*", " ", normalized(value))
    return re.sub(r"\b(day|month|hour)\b", r"\1s", value)


def body(text: str) -> str:
    return HEADER_RE.sub("", text, count=1)


def sections(text: str) -> dict[str, str]:
    """Use actual Markdown headings, never manifest section names as evidence."""
    result: dict[str, str] = {}
    matches = list(re.finditer(r"^(#{1,6})\s+(.+?)\s*$", body(text), re.M))
    text = body(text)
    for index, match in enumerate(matches):
        end = len(text)
        for next_match in matches[index + 1:]:
            if len(next_match[1]) <= len(match[1]):
                end = next_match.start()
                break
        name = match[2].strip()
        # Repeated headings are all searched; never silently discard one.
        result[name] = result.get(name, "") + text[match.end():end]
    return result


def check(name: str, status: str, detail: str, **evidence: Any) -> dict:
    return {"check": name, "status": status, "detail": detail, **evidence}


def rollup(checks: list[dict]) -> str:
    statuses = {item["status"] for item in checks}
    return "fail" if "fail" in statuses else "unverifiable" if "unverifiable" in statuses else "pass"


def counts(records: list[dict]) -> dict[str, int]:
    counter = Counter(item["status"] for item in records)
    return {key: counter[key] for key in ("pass", "fail", "unverifiable")}


def per_type_counts(records: list[dict]) -> dict[str, dict[str, int]]:
    return {kind: counts([row for row in records if row["type"] == kind]) for kind in (f"T{i}" for i in range(8))}


def read_questions(path: Path) -> list[dict]:
    records = []
    seen = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        for field in ("qid", "question", "type", "gold_status", "gold_answer", "gold_winner_doc", "gold_conflicting_docs", "gold_claims"):
            if field not in row:
                raise ValueError(f"{path.name}:{line_number}: missing {field}")
        if not isinstance(row["qid"], str) or row["qid"] in seen:
            raise ValueError(f"{path.name}:{line_number}: invalid or duplicate qid")
        seen.add(row["qid"])
        records.append(row)
    if not records:
        raise ValueError(f"{path.name}: empty question set")
    return records


def fact_lines(documents: dict, topic: str) -> list[dict]:
    """Collect topic-bearing lines only; unrelated numeric values never compete."""
    rows = []
    # Disclosed bounded aliases capture prose as well as generated topic bullets.
    # In particular a filed "annual limit" is the same fact, not an unrelated number.
    pattern = {"annual hospitalization limit": r"annual\s+(?:hospitalization\s+)?limit",
               "renewal grace period": r"renewal\s+(?:grace\s+period|may\s+be\s+completed)"}.get(topic, re.escape(topic))
    topic_pattern = re.compile(pattern, re.I)
    for doc_id, document in sorted(documents.items()):
        for line_number, line in enumerate(document.text.splitlines(), 1):
            if line.startswith(("#", "---")) or not topic_pattern.search(line):
                continue
            values = QUANTITY.findall(line)
            if values:
                rows.append({"doc_id": doc_id, "line": line_number, "text": line, "values": values,
                             "effective_date": str(document.meta.effective_date),
                             "issued_date": str(document.meta.issued_date),
                             "authority_rank": document.meta.authority_rank})
    return rows


def scoped_fact_positions(documents: dict, facts: dict) -> list[dict]:
    """Bounded clause/heading probes with explicit age, plan and phase scopes.

    Quantities from distinct clauses or phases never compete merely because they
    share a document. This is a numeric consistency scan, not semantic entailment.
    Unknown age/plan/phase scope is retained as unverifiable, not guessed.
    """
    rows = []
    for doc_id, document in sorted(documents.items()):
        heading = ""
        header = HEADER_RE.match(document.text)
        header_lines = document.text[:header.end()].count("\n") if header else 0
        for line_number, line in enumerate(document.text.splitlines(), 1):
            if line_number <= header_lines:
                continue
            if line.startswith("#"):
                heading = line.lstrip("# ")
                continue
            if not line.strip() or line.startswith("This document "):
                continue
            bullet = re.match(r"- \*\*(.+?)\*\* \((.*?)\): (.*)", line)
            for fact_id, fact in facts.items():
                pattern = FACT_PATTERNS.get(fact_id, re.escape(fact["topic"]))
                if bullet and normalized(bullet[1]) != normalized(fact["topic"]):
                    continue
                clauses = re.split(r";|/|,\s*(?=\d)|\band\s+(?=(?:premium|standard|members|seniors?|resolution|resolve|\d+)\b)", bullet[3] if bullet else line, flags=re.I)
                for clause in clauses:
                    context = f"{bullet[1]} {clause}" if bullet else clause
                    if not re.search(pattern, context, re.I):
                        # A scope-only continuation may inherit the line's fact,
                        # but a clause explicitly naming another fact may not.
                        other_fact = any(re.search(other, clause, re.I) for key, other in FACT_PATTERNS.items() if key != fact_id)
                        inherited = re.search(pattern, line, re.I) and not other_fact
                        if bullet or not (inherited or re.search(pattern, heading, re.I)):
                            continue
                    # Prevent the generic waiting-period alias from treating a
                    # maternity schedule as ordinary hospitalization evidence.
                    if fact_id == "waiting_period" and re.search(r"maternity", context + heading, re.I):
                        continue
                    scope = normalized(fact.get("scope", fact["topic"]))
                    known_scope = True
                    lower = normalized(clause)
                    if fact_id in {"copay", "room_rent", "annual_limit", "maternity"}:
                        populations = [name for name, probe in (("senior", r"aged\s+60|senior"), ("premium", r"premium"), ("standard", r"standard")) if re.search(probe, lower)]
                        if len(populations) > 1:
                            scope, known_scope = "ambiguous age/plan clause", False
                        elif "senior" in populations:
                            scope = "senior members aged 60 and above"
                        elif "premium" in lower:
                            scope = "premium plan"
                        elif "standard" in lower:
                            scope = "standard plan"
                        elif fact_id == "annual_limit":
                            # The disclosed annual-limit fact is Standard-only;
                            # generated bullet scope supplies the population.
                            scope = "standard plan" if bullet and "standard" in normalized(bullet[2]) else "unspecified plan"
                            known_scope = scope != "unspecified plan"
                        else:
                            scope, known_scope = "unspecified age/plan", False
                    matches = list(SCOPED_QUANTITY.finditer(clause))
                    if not matches:
                        rows.append({"doc_id": doc_id, "fact_id": fact_id, "scope": scope, "scope_known": known_scope,
                                     "line": line_number, "text": line, "clause": clause.strip(), "value": None,
                                     "effective_date": document.meta.model_dump(mode="json")["effective_date"],
                                     "issued_date": document.meta.model_dump(mode="json")["issued_date"],
                                     "authority_rank": document.meta.authority_rank})
                    for match in matches:
                        value_scope, value_known = scope, known_scope
                        if fact_id == "grievance_timeline":
                            # Separate acknowledgement and resolution deadlines.
                            prefix = lower[:match.start()]
                            cues = list(re.finditer(r"acknowledge(?:ment)?|resol(?:ve|ution)", prefix))
                            value_scope = "acknowledgement" if cues and cues[-1][0].startswith("ack") else "resolution" if cues else "unspecified phase"
                            value_known = bool(cues)
                        if fact_id == "preauthorization":
                            value_scope = "emergency notification" if "emergency" in lower else "unspecified admission"
                            value_known = "emergency" in lower
                        rows.append({"doc_id": doc_id, "fact_id": fact_id, "scope": value_scope, "scope_known": value_known,
                                     "line": line_number, "text": line, "clause": clause.strip(), "value": canonical_quantity(match[0]),
                                     "effective_date": document.meta.model_dump(mode="json")["effective_date"],
                                     "issued_date": document.meta.model_dump(mode="json")["issued_date"],
                                     "authority_rank": document.meta.authority_rank})
    return rows


def audit_intra_document(documents: dict, facts: dict) -> dict:
    positions = scoped_fact_positions(documents, facts)
    groups = {}
    for row in positions:
        groups.setdefault((row["doc_id"], row["fact_id"], row["scope"]), []).append(row)
    records = []
    for (doc_id, fact_id, scope), rows in sorted(groups.items()):
        values = sorted({row["value"] for row in rows if row["value"] is not None})
        known = all(row["scope_known"] for row in rows)
        status = "unverifiable" if not known or not values else "fail" if len(values) > 1 else "pass"
        records.append({"doc_id": doc_id, "fact_id": fact_id, "scope": scope, "values": values,
                        "status": status, "detail": "Competing quantities for the same fact AND same scope." if status == "fail" else
                        "One distinct quantity in bounded same-fact/scope positions; not semantic proof." if status == "pass" else
                        "No quantitative value or no explicit scope; semantic consistency is unverifiable.", "positions": rows})
    return {"counts": counts(records), "records": records, "positions": positions,
            "fact_patterns": FACT_PATTERNS, "scope_rules": "Age/plan and grievance phase are distinct scopes. Unknown scope stays unverifiable. Annual generated bullets use explicit Standard scope."}


def absence_check(question: dict, documents: dict) -> dict:
    families = [name for name, patterns in ABSENCE_PROBES.items()
                if any(re.search(pattern, question["question"], re.I) for pattern in patterns)]
    hits = []
    for name in families:
        for doc_id, document in sorted(documents.items()):
            for line_number, line in enumerate(document.text.splitlines(), 1):
                if any(re.search(pattern, line, re.I) for pattern in ABSENCE_PROBES[name]):
                    hits.append({"family": name, "doc_id": doc_id, "line": line_number, "text": line})
    return check("t7_absence", "unverifiable",
                 "Lexical candidates require review; a mention does not establish coverage." if hits else
                 "No selected lexical probe hit; semantic absence is not provable by this scan.",
                 families=families, hits=hits, lexical_no_hit=bool(families) and not hits)


def audit_question(question: dict, documents: dict, manifest_docs: dict, facts: dict) -> dict:
    checks = []
    cited = list(dict.fromkeys(question["gold_conflicting_docs"] +
                               ([question["gold_winner_doc"]] if question["gold_winner_doc"] else [])))
    passages = question.get("source_passages", [])
    refs = list(dict.fromkeys(cited + [ref.split("#", 1)[0] for ref in passages]))
    missing = [ref for ref in refs if ref not in documents]
    missing_sections = []
    targets = {}
    for ref in passages:
        doc_id, separator, section = ref.partition("#")
        if doc_id not in documents:
            continue
        available = sections(documents[doc_id].text)
        if separator and section not in available:
            missing_sections.append(ref)
        else:
            targets[ref] = available[section] if separator else body(documents[doc_id].text)
    # If a document has an explicit section citation, do not broaden it to its body.
    for doc_id in cited:
        if doc_id in documents and not any(ref.split("#", 1)[0] == doc_id for ref in passages):
            targets[doc_id] = body(documents[doc_id].text)
    checks.append(check("cited_sources", "fail" if missing else "unverifiable" if missing_sections else "pass",
                        "Actual cited documents and headings checked; no implied section citations.",
                        missing_docs=missing, missing_sections=missing_sections, targets=list(targets)))
    answer = question["gold_answer"]
    if answer is not None:
        hits = [ref for ref, text in targets.items() if present(answer, text)]
        raw_hits = [ref for ref, text in targets.items() if answer in text]
        simple = QUANTITY.fullmatch(answer.strip()) is not None or bool(re.fullmatch(r"\d+ days after discharge|\d+ currency units per (?:policy year|hospitalization)", answer))
        # Resolved values must occur in the actual winner, not just a losing source.
        winner = question["gold_winner_doc"]
        eligible = [ref for ref in hits if not winner or ref.split("#", 1)[0] == winner]
        atoms = sorted(set(QUANTITY.findall(answer)))
        atom_hits = {atom: [ref for ref, text in targets.items() if present(atom, text)] for atom in atoms}
        checks.append(check("gold_value_presence", "unverifiable" if missing_sections or not simple else "pass" if eligible else "fail",
                            "Missing cited section prevents evidence verification." if missing_sections else
                            "Composed/paraphrased answer remains unverifiable even if a full string or all quantities occur." if not simple else
                            "Literal value found in eligible cited evidence; this is not an entailment judgment." if eligible else
                            "Simple gold value missing from eligible cited evidence." if simple else
                            "Composed/paraphrased answer is not a literal string; atom hits do not prove its semantics.",
                            answer_kind="literal_value" if simple else "composed_or_paraphrased",
                            literal_hits=hits, raw_case_sensitive_hits=raw_hits, eligible_hits=eligible,
                            literal_evidence={ref: text.strip() for ref, text in targets.items() if ref in hits},
                            quantity_hits=atom_hits,
                            claim_literal_hits={claim: [ref for ref, text in targets.items() if present(claim, text)]
                                                for claim in question["gold_claims"]}))
    elif question["type"] not in ("T6", "T7"):
        checks.append(check("gold_value_presence", "unverifiable", "No gold value is supplied."))
    if question["type"] == "T7":
        valid = (question["gold_status"] == "not_in_corpus" and answer is None and not refs and not question["gold_claims"])
        checks.append(check("t7_gold_shape", "pass" if valid else "fail", "Checked null answer, no claims/citations, and not_in_corpus status."))
        checks.append(absence_check(question, documents))
    if question["type"] == "T0":
        topic = facts["renewal_grace"]["topic"]
        rows = fact_lines(documents, topic)
        competing = [row for row in rows if any(canonical_quantity(value) != canonical_quantity(answer or "") for value in row["values"])]
        checks.append(check("t0_same_fact_competition", "fail" if competing else "pass" if rows else "unverifiable",
                            "Whole-corpus bounded topic/alias-line duration scan; no temporal/scope adjudication or synonym completeness claimed.",
                            topic=topic, positions=rows, competing_positions=competing))
    if question["type"] == "T6":
        rows = fact_lines(documents, facts["annual_limit"]["topic"])
        pair = []
        for left_index, left in enumerate(cited):
            for right in cited[left_index + 1:]:
                if left not in documents or right not in documents:
                    continue
                a, b = documents[left].meta, documents[right].meta
                values_a = {v for row in rows if row["doc_id"] == left for v in row["values"]}
                values_b = {v for row in rows if row["doc_id"] == right for v in row["values"]}
                if not values_a or not values_b or values_a == values_b:
                    continue
                expected_a = manifest_docs.get(left, {}).get("expected_metadata", {})
                expected_b = manifest_docs.get(right, {}).get("expected_metadata", {})
                same = a.effective_date is not None and a.issued_date is not None and all(
                    getattr(a, field) == getattr(b, field) for field in ("effective_date", "issued_date", "authority_rank"))
                manifest_same = all(expected_a.get(field) is not None and expected_a.get(field) == expected_b.get(field)
                                    for field in ("effective_date", "issued_date", "authority_rank"))
                agrees = all(doc.meta.model_dump(mode="json").get(field) == expected.get(field)
                             for doc, expected in ((documents[left], expected_a), (documents[right], expected_b))
                             for field in ("effective_date", "issued_date", "authority_rank"))
                pair.append({"docs": [left, right], "values": [sorted(values_a), sorted(values_b)],
                             "same_date_authority_loaded": same, "same_date_authority_manifest": manifest_same,
                             "loaded_agrees_with_manifest": agrees,
                             "effective_dates": [str(a.effective_date), str(b.effective_date)],
                             "issued_dates": [str(a.issued_date), str(b.issued_date)],
                             "authority_ranks": [a.authority_rank, b.authority_rank]})
        tied = [item for item in pair if item["same_date_authority_loaded"] and item["same_date_authority_manifest"] and item["loaded_agrees_with_manifest"]]
        checks.append(check("t6_pair", "pass" if tied else "fail" if pair else "unverifiable",
                            "Different same-topic values checked against effective date, issued date, and authority in loader AND manifest.", pairs=pair))
        tied_docs = {doc_id for item in tied for doc_id in item["docs"]}
        other = [row for row in rows if row["doc_id"] not in tied_docs]
        internal = {}
        for doc_id in sorted({row["doc_id"] for row in rows}):
            values = sorted({re.match(r"\d+(?:\.\d+)?", value)[0]
                             for row in rows if row["doc_id"] == doc_id for value in row["values"]})
            if len(values) > 1:
                internal[doc_id] = values
        # A strictly higher-authority AND later applicable Standard position is
        # counterevidence to a purported current pair tie. Never call a local tie
        # proof of global abstention, and never manufacture a global T6 pass.
        dated_tied = [row for row in rows if row["doc_id"] in tied_docs]
        dominating = [row for row in other if dated_tied and "premium" not in normalized(row["text"]) and row["effective_date"] != "None" and
                      all(row["authority_rank"] > tied_row["authority_rank"] and
                          row["effective_date"] > tied_row["effective_date"] for tied_row in dated_tied) and
                      not question.get("as_of_date")]
        checks.append(check("t6_global_abstention", "fail" if dominating else "unverifiable",
                            "Later, higher-authority same-fact positions defeat this current pair-only abstention; applicability still needs adjudication." if dominating else
                            "Pair tie alone cannot establish global abstention; review other same-fact documents and applicability.",
                            other_positions=other, dominating_positions=dominating, internal_competing_values=internal))
        checks.append(check("t6_gold_shape", "pass" if answer is None and question["gold_status"] == "abstained" and not question["gold_winner_doc"] else "fail",
                            "Checked null answer/winner and abstained status."))
    return {"qid": question["qid"], "type": question["type"], "split": question.get("split", "unspecified"),
            "status": rollup(checks), "checks": checks}


def audit_metadata(documents: dict, manifest: dict) -> list[dict]:
    records = []
    for entry in manifest["documents"]:
        doc_id = entry["doc_id"]
        if doc_id not in documents:
            records.append({"doc_id": doc_id, "status": "fail", "differences": {"document": "missing"}})
            continue
        document = documents[doc_id]
        actual = document.meta.model_dump(mode="json")
        expected = entry["expected_metadata"]
        differences = {field: {"expected": expected.get(field), "loaded": actual.get(field)}
                       for field in PHYSICAL_FIELDS if expected.get(field) != actual.get(field)}
        header = parse_header(document.text)
        corrupt_version = entry["header_metadata"]["corruption_kind"] == "wrong_version" and header.get("version") == "0.0"
        accepted = corrupt_version and actual["version"] is None and actual["metadata_confidence"] == 0.0
        unexpected = {key: value for key, value in differences.items() if not (accepted and key == "version")}
        records.append({"doc_id": doc_id, "status": "fail" if unexpected or (corrupt_version and not accepted) else "pass",
                         "corrupted": entry["metadata_corrupted"],
                        "corruption_kind": entry["header_metadata"]["corruption_kind"],
                        "header_version": header.get("version"), "header_effective": header.get("effective"),
                         "differences": differences,
                        "accepted_loss": {"version": differences["version"]} if accepted and "version" in differences else {},
                        "version_recovered": False if corrupt_version else None,
                        "recovery_outcome": "accepted_unknown_version" if accepted else "unsupported_corrupted_version" if corrupt_version else "physical_fields_compared",
                        "derived_diagnostics": {field: {"manifest": expected.get(field), "loaded": actual.get(field)}
                                                for field in ("metadata_source", "metadata_confidence")}})
    for doc_id in sorted(set(documents) - {entry["doc_id"] for entry in manifest["documents"]}):
        records.append({"doc_id": doc_id, "status": "fail", "differences": {"manifest": "unlisted document"}})
    return records


def run_audit(root: Path) -> dict:
    corpus = root / "data/corpus"
    manifest_path = corpus / "corpus_manifest.json"
    facts_path = root / "data/factsheet/aurelia_facts.yaml"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    factsheet = yaml.safe_load(facts_path.read_text(encoding="utf-8"))
    facts = {fact["fact_id"]: fact for fact in factsheet["facts"]}
    # Explicit authority config only; no .env reads, model loads, or provider imports.
    config_path = root / "config.yaml"
    authority = yaml.safe_load(config_path.read_text(encoding="utf-8"))["authority_rank"]
    if not isinstance(authority, dict) or not authority:
        raise ValueError("config.yaml must provide a nonempty authority_rank mapping")
    loaded = load_documents(corpus, authority_ranks=authority)
    documents = {document.meta.doc_id: document for document in loaded}
    if len(documents) != len(loaded):
        raise ValueError("Duplicate loaded document IDs")
    manifest_docs = {entry["doc_id"]: entry for entry in manifest["documents"]}
    datasets = {}
    paths = [manifest_path, facts_path, config_path] + [document.path for document in loaded]
    source_records = {}
    for filename in ("questions.jsonl", "wild.jsonl", "eval_subset_40.jsonl"):
        path = root / "data/benchmark" / filename
        paths.append(path)
        questions = read_questions(path)
        source_records[filename] = {q["qid"]: q for q in questions}
        records = [audit_question(q, documents, manifest_docs, facts) for q in questions]
        datasets[filename] = {"count": len(records), "counts": counts(records), "per_type_counts": per_type_counts(records), "records": records}
    for record in datasets["eval_subset_40.jsonl"]["records"]:
        qid = record["qid"]
        original = source_records["questions.jsonl"].get(qid)
        valid = original == source_records["eval_subset_40.jsonl"][qid] and original.get("split") == "test" if original else False
        record["checks"].append(check("subset_membership", "pass" if valid else "fail", "Frozen subset row must exactly equal its TEST source row."))
        record["status"] = rollup(record["checks"])
    datasets["eval_subset_40.jsonl"]["counts"] = counts(datasets["eval_subset_40.jsonl"]["records"])
    datasets["eval_subset_40.jsonl"]["per_type_counts"] = per_type_counts(datasets["eval_subset_40.jsonl"]["records"])
    metadata = audit_metadata(documents, manifest)
    for row in metadata:
        row["cited_by"] = {
            name: [record["qid"] for record in dataset["records"]
                   if any(target.split("#", 1)[0] == row["doc_id"]
                          for target in record["checks"][0]["targets"])]
            for name, dataset in datasets.items()
        }
    unique = [row for name, dataset in datasets.items() if name != "eval_subset_40.jsonl" for row in dataset["records"]]
    return {"format_version": 2, "input_sha256": {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(paths)},
            "unique_question_counts": counts(unique), "unique_per_type_counts": per_type_counts(unique), "unique_questions": len(unique), "datasets": datasets,
            "intra_document": audit_intra_document(documents, facts),
            "gold_adjudication": manifest.get("gold_adjudication", {}),
            "metadata": {"counts": counts(metadata), "accepted_unknown_version_count": sum(row.get("recovery_outcome") == "accepted_unknown_version" for row in metadata), "corrupted_counts": counts([row for row in metadata if row.get("corrupted")]), "records": metadata},
            "absence_probes": ABSENCE_PROBES,
            "factsheet_reference": {key: facts[key] for key in ("renewal_grace", "annual_limit")}}


def markdown(report: dict) -> str:
    lines = ["# Programmatic corpus audit (offline)", "",
             "## Reproduce", "", "```bash", "TRUTHGUARD_OFFLINE=true .venv/bin/python scripts/audit_corpus_programmatic.py",
              "TRUTHGUARD_OFFLINE=true PYTHONPATH=.:src .venv/bin/python -m pytest -q tests/test_corpus.py tests/test_benchmark.py tests/test_programmatic_audit.py", "```", "",
             "Default outputs: `reports/corpus_audit_programmatic.md` and `.json`. Use `--root`, `--output`, and `--json-output` to select paths. "
             "No network, API, retrieval, critic, model, or pipeline execution. Exit 0 means completion; `--fail-on-findings` exits 1 for any fail/unverifiable finding. Invalid inputs exit 2.", "",
             "## Interpretation and limits", "",
             "Pass means only the named mechanical check passed, never semantic gold correctness. Question rollup: any failure → fail; otherwise any unverifiable check → unverifiable; otherwise pass. "
              "Metadata handling is counted separately, not folded into question gold counts. The fixed subset overlaps the main benchmark and is not additional unique evidence.", "",
             "Value evidence is read from actual Markdown bodies/headings, not the factsheet, manifest answers, or runtime predictions. "
             "Matching is case/whitespace-normalized with word boundaries; raw case-sensitive hits are also recorded. "
             "Explicit section citations restrict matching to that section. Resolved answers must match the winner's cited evidence. "
              "Simple missing values fail when cited sections exist. Missing cited sections are unverifiable, never widened to the body or passed. "
              "Composed/paraphrased answers remain unverifiable even when full strings or quantities match; scenario arithmetic, exceptions, scope, and entailment require review. "
             "Literal claims and quantity matches are diagnostics in JSON, not substitute passes.", "",
             "T7 searches every document with only the disclosed selected probe families. No hit is lexical evidence only and remains unverifiable; "
             "unknown subject families also remain unverifiable. A hit is a review candidate, not proof of coverage. Synonyms outside the probes, implicit statements, and semantic entailment are not detectable.", "",
             "T0 scans lines containing the factsheet topic or bounded aliases (`renewal grace period`, `renewal may be completed`) and compares numeric durations only; unrelated durations do not count. "
             "For competition only, singular/plural and hyphenated durations such as `30-day` and `30 days` are treated alike. "
             "It cannot guarantee synonym completeness or adjudicate time/scope. T6 checks actual distinct annual-limit values, both issued/effective dates, and authority against loader and manifest. "
             "Its bounded topic aliases are `annual hospitalization limit` and `annual limit`; all matching positions are retained, including disagreements inside one document. "
              "The local tie does not prove whole-corpus abstention. Later higher-authority same-fact counterevidence fails current pair-only abstention. "
              "Gold was revised by explicit corpus adjudication; see `reports/gold_changes.md`. The audit performs no runtime tuning or benchmark freeze.", "",
             "## Measured question counts", "", "| Dataset | Rows | Pass | Fail | Unverifiable |", "|---|---:|---:|---:|---:|"]
    for name, dataset in report["datasets"].items():
        c = dataset["counts"]
        lines.append(f"| {name} | {dataset['count']} | {c['pass']} | {c['fail']} | {c['unverifiable']} |")
    c = report["unique_question_counts"]
    lines += [f"| Unique (main + wild) | {report['unique_questions']} | {c['pass']} | {c['fail']} | {c['unverifiable']} |", "",
               "## Per-type question counts", "", "| Dataset | Type | Pass | Fail | Unverifiable |", "|---|---|---:|---:|---:|"]
    for name, dataset in report["datasets"].items():
        for kind, c in dataset["per_type_counts"].items():
            lines.append(f"| {name} | {kind} | {c['pass']} | {c['fail']} | {c['unverifiable']} |")
    for kind, c in report["unique_per_type_counts"].items():
        lines.append(f"| Unique (main + wild) | {kind} | {c['pass']} | {c['fail']} | {c['unverifiable']} |")
    lines += ["", "## Check counts and exact affected qids", ""]
    for name, dataset in report["datasets"].items():
        lines += [f"### {name}", "", "| Check | Pass | Fail | Unverifiable |", "|---|---:|---:|---:|"]
        names = sorted({item["check"] for row in dataset["records"] for item in row["checks"]})
        for check_name in names:
            items = [item for row in dataset["records"] for item in row["checks"] if item["check"] == check_name]
            c = counts(items)
            lines.append(f"| {check_name} | {c['pass']} | {c['fail']} | {c['unverifiable']} |")
        for status in ("fail", "unverifiable"):
            qids = [row["qid"] for row in dataset["records"] if row["status"] == status]
            lines += ["", f"**Exact {status} qids ({len(qids)}):** " + (", ".join(f"`{qid}`" for qid in qids) or "none")]
        groups: dict[tuple, list] = {}
        for row in dataset["records"]:
            for item in row["checks"]:
                if item["status"] != "pass":
                    groups.setdefault((item["check"], item["detail"]), []).append(row["qid"])
        for (check_name, detail), qids in groups.items():
            lines += ["", f"- **{check_name}:** {detail} Qids: " + ", ".join(f"`{qid}`" for qid in qids)]
    lines += ["", "## Metadata handling against manifest", "",
               f"All documents: `{report['metadata']['counts']}`. Corrupted only: `{report['metadata']['corrupted_counts']}`.", "",
               "Compared identity, title, type, version, issued/effective dates, authority, supersedes, and amends. "
               "A corrupted header version `0.0` must become null with metadata_confidence `0.0`: this is an accepted information loss, **not recovered-version success**. "
               "The expected manifest version is comparison-only and must never be copied into loaded metadata. Other physical-field differences still fail. "
               "Derived annotations are disclosed in JSON; confidence zero is required for the accepted unknown-version case.", "",
               f"Accepted unknown versions: **{report['metadata']['accepted_unknown_version_count']}** (version_recovered=false).", "",
               "| Document | Corruption | Result | Outcome | Physical-field differences |", "|---|---|---|---|---|"]
    for row in report["metadata"]["records"]:
        differences = json.dumps(row["differences"], sort_keys=True)
        lines.append(f"| {row['doc_id']} | {row.get('corruption_kind') or 'none'} | {row['status']} | {row.get('recovery_outcome', 'missing')} | `{differences}` |")
    lines += ["", "### Exact qids citing failed metadata documents", "",
              "These are metadata-impact qids, separate from question gold failures above.", ""]
    for row in report["metadata"]["records"]:
        if row["status"] == "fail":
            for name, qids in row["cited_by"].items():
                lines.append(f"- `{row['doc_id']}` / `{name}`: " + (", ".join(f"`{qid}`" for qid in qids) or "none"))
    lines += ["", "## T7 lexical probes", "", "```json", json.dumps(report["absence_probes"], indent=2), "```", "",
               "## Evidence and adjudication limits", "",
              "1. **Composed gold:** review all `gold_value_presence` unverifiable qids listed above. Check clauses, scope, exception, and scenario arithmetic against the exact cited sections in JSON. "
              "Safe proposal: add independently reviewed atomic evidence mappings or correct a section citation if it points to the wrong passage. "
               "Missing full strings must not be relabeled as literal passes.", "",
               "2. **Annual-limit adjudication:** both sections of NOTICE-2025-11 use the owner-adjudicated 500000 fallback, effective 2025-11-01, authority 3. "
               "The simultaneous August 500000/600000 history has no unique pre-notice value. Current POL-2026-V3 gives 600000 at authority 4, effective 2026-01-01. "
               "All original annual-limit T6 qids now have T3/resolved gold with supersession mode recorded in the manifest. "
               "No 12 genuine current whole-corpus TEST T6 examples exist in the reviewed evidence; zero were retained. No pair-only query scoping or invented evidence was used. "
               "The full per-qid old/new ledger and existing-fact review are in `reports/gold_changes.md`.", "",
               "3. **Metadata:** safe unknown versions are explicitly accepted losses with confidence zero, not successful version recovery. "
               "An unsupported non-null corrupted version fails, even if it happens to equal manifest gold.", "",
              "4. **T7:** a human must adjudicate semantic absence for every T7 qid; the lexical no-hit result is insufficient. "
              "T0 passes are bounded topic/alias scans, not a proof that no paraphrased competing rule exists.", "",
               "5. **Intra-document same-fact AND same-scope scan:** bounded topic/heading aliases and numeric quantities are listed in JSON, including exact lines, dates and authority. "
               "10% Standard / 20% senior, 1% Standard / 2% Premium, and acknowledgement / resolution deadlines are separate scopes, not internal contradictions. "
               "A one-value pass means only quantitative consistency for the scanned scope; missing quantities, unknown scopes and non-numeric semantics remain unverifiable.", "",
               "## Intra-document quantitative consistency", "",
               f"Counts by document/fact/scope group: `{report['intra_document']['counts']}`.", "",
               "| Document | Fact | Scope | Values | Result | Effective | Issued | Authority |", "|---|---|---|---|---|---|---|---:|"]
    for row in report["intra_document"]["records"]:
        position = row["positions"][0]
        lines.append(f"| {row['doc_id']} | {row['fact_id']} | {row['scope']} | {', '.join(row['values']) or 'non-numeric'} | {row['status']} | {position['effective_date']} | {position['issued_date']} | {position['authority_rank']} |")
    lines += ["",
              "### T0 and T6 actual corpus positions", ""]
    emitted = set()
    pair_emitted = set()
    for dataset in report["datasets"].values():
        for row in dataset["records"]:
            for item in row["checks"]:
                for pair in item.get("pairs", []):
                    key = tuple(pair["docs"])
                    if key not in pair_emitted:
                        pair_emitted.add(key)
                        lines.append(f"- Pair `{key[0]}` / `{key[1]}`: values `{pair['values']}`, effective `{pair['effective_dates']}`, issued `{pair['issued_dates']}`, authority `{pair['authority_ranks']}`; loaded tie `{pair['same_date_authority_loaded']}`, manifest tie `{pair['same_date_authority_manifest']}`, loaded agrees with manifest `{pair['loaded_agrees_with_manifest']}`.")
                for position in item.get("positions", []) + item.get("other_positions", []):
                    key = (position["doc_id"], position["line"])
                    if key not in emitted:
                        emitted.add(key)
                        lines.append(f"- `{position['doc_id']}:{position['line']}` (effective {position['effective_date']}, issued {position['issued_date']}, authority {position['authority_rank']}): {position['text']}")
    lines += ["", "## Input SHA-256 fingerprints", "", "The companion JSON records every qid/check and all input hashes; hashes below make reruns auditable.", "", "```text"]
    lines += [f"{digest}  {path}" for path, digest in report["input_sha256"].items()]
    return "\n".join(lines + ["```", ""])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=Path("reports/corpus_audit_programmatic.md"))
    parser.add_argument("--json-output", type=Path, default=Path("reports/corpus_audit_programmatic.json"))
    parser.add_argument("--fail-on-findings", action="store_true")
    args = parser.parse_args()
    try:
        report = run_audit(args.root.resolve())
        for path, content in ((args.output, markdown(report)), (args.json_output, json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")):
            path = path if path.is_absolute() else args.root / path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as error:
        print(f"Audit input/output error: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"unique_questions": report["unique_questions"], "question_counts": report["unique_question_counts"], "metadata_counts": report["metadata"]["counts"]}, sort_keys=True))
    findings = report["unique_question_counts"]["fail"] + report["unique_question_counts"]["unverifiable"] + report["metadata"]["counts"]["fail"] + report["intra_document"]["counts"]["fail"] + report["intra_document"]["counts"]["unverifiable"]
    return 1 if args.fail_on_findings and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
