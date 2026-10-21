from __future__ import annotations

import json
from pathlib import Path

import pytest

from bench.generate_corpus import _statement, generate_corpus, load_facts, validate_manifest


ROOT = Path(__file__).resolve().parents[1]
FACTSHEET = ROOT / "data/factsheet/aurelia_facts.yaml"


def test_corpus_has_manifested_docs_and_taxonomy(tmp_path) -> None:
    output = tmp_path / "corpus"
    manifest = generate_corpus(FACTSHEET, output)
    assert manifest["document_count"] == 35
    assert manifest["metadata_corrupted_count"] == 14
    assert manifest["metadata_corrupted_fraction"] == 0.4
    assert validate_manifest(manifest) == []
    assert {item["type"] for item in manifest["conflicts"]} == {
        "T0",
        "T1",
        "T2",
        "T3",
        "T4",
        "T5",
        "T7",
    }
    for document in manifest["documents"]:
        assert (output / document["path"]).exists()
    assert (output / "corpus_manifest.json").exists()


def test_corpus_contains_known_conflicting_positions(tmp_path) -> None:
    output = tmp_path / "corpus"
    generate_corpus(FACTSHEET, output)
    old_policy = (output / "POL-2024-V1.md").read_text(encoding="utf-8")
    amendment = (output / "AMD-2025-03.md").read_text(encoding="utf-8")
    assert "30 days" in old_policy
    assert "45 days" in amendment
    assert "Amendment AH/2025/03" in amendment


def test_generation_is_reproducible(tmp_path) -> None:
    first = generate_corpus(FACTSHEET, tmp_path / "first")
    second = generate_corpus(FACTSHEET, tmp_path / "second")
    assert first == second
    first_manifest = json.loads((tmp_path / "first/corpus_manifest.json").read_text())
    second_manifest = json.loads((tmp_path / "second/corpus_manifest.json").read_text())
    assert first_manifest == second_manifest


def test_annual_limit_requires_explicit_owner_adjudication(tmp_path) -> None:
    facts = {fact["fact_id"]: fact for fact in load_facts(FACTSHEET)["facts"]}
    for target in ("2025-08-01", "2025-11-01", "2026-01-01"):
        with pytest.raises(ValueError, match="No unique in-force value"):
            _statement(facts["annual_limit"], target)
    facts["annual_limit"]["versions"].reverse()
    with pytest.raises(ValueError, match="No unique in-force value"):
        _statement(facts["annual_limit"], "2025-11-01")
    manifest = generate_corpus(FACTSHEET, tmp_path)
    notice = (tmp_path / "NOTICE-2025-11.md").read_text()
    assert notice.count("500000 currency units") == 2
    assert "600000" not in notice
    assert "600000 currency units" in (tmp_path / "POL-2026-V3.md").read_text()
    decision = manifest["gold_adjudication"]["annual_limit"]
    assert decision["current"]["authority_rank"] == 4
    assert decision["genuine_current_whole_corpus_t6"] == 0


def test_generated_corpus_matches_tracked_gold(tmp_path) -> None:
    generate_corpus(FACTSHEET, tmp_path)
    for path in tmp_path.iterdir():
        assert path.read_bytes() == (ROOT / "data/corpus" / path.name).read_bytes(), path.name
