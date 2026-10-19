from __future__ import annotations

import json
from pathlib import Path

from bench.generate_corpus import generate_corpus, validate_manifest


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
        "T6",
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
