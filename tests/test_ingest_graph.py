from __future__ import annotations

from datetime import date
from pathlib import Path

from truthguard.graph.supersession import SupersessionGraph
from truthguard.ingest.chunker import chunk_document
from truthguard.ingest.index import HybridIndex
from truthguard.ingest.loader import LoadedDocument, load_documents
from truthguard.ingest.metadata import infer_metadata, parse_header
from truthguard.schemas import DocMeta


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data/corpus"


def make_meta(doc_id: str, effective: date | None, **kwargs) -> DocMeta:
    return DocMeta(
        doc_id=doc_id,
        title=doc_id,
        doc_type=kwargs.pop("doc_type", "policy"),
        effective_date=effective,
        authority_rank=kwargs.pop("authority_rank", 4),
        metadata_source="provided",
        metadata_confidence=1.0,
        **kwargs,
    )


def test_loader_and_metadata_inference_cover_generated_corpus() -> None:
    documents = load_documents(CORPUS)
    assert len(documents) == 35
    assert any(document.meta.metadata_source == "inferred" for document in documents)
    amendment = next(document for document in documents if document.meta.doc_id == "AMD-2025-03")
    assert amendment.meta.effective_date == date(2025, 3, 1)
    assert amendment.meta.amends == [("POL-2024-V1", "Section 4.1")]


def test_metadata_parser_uses_body_and_keeps_unknown_dates_unknown(tmp_path) -> None:
    text = """---\nDoc ID: AMD-CUSTOM\nTitle: Custom amendment\nType: amendment\nVersion: 1\n---\n# Custom amendment\nThis amendment is effective from 1 March 2025.\nIt supersedes POL-2024-V1.\n"""
    parsed = parse_header(text)
    assert parsed["doc_id"] == "AMD-CUSTOM"
    metadata = infer_metadata(text, tmp_path / "AMD-CUSTOM.md", known_doc_ids=["POL-2024-V1", "AMD-CUSTOM"])
    assert metadata.effective_date == date(2025, 3, 1)
    assert metadata.supersedes == ["POL-2024-V1"]
    unknown = infer_metadata("# No date", tmp_path / "unknown.md", known_doc_ids=[])
    assert unknown.effective_date is None


def test_chunk_offsets_are_exact_and_section_aware() -> None:
    metadata = make_meta("DOC-1", date(2025, 1, 1))
    text = "# Intro\nOne two three.\n## Rules\n" + "word " * 20
    chunks = chunk_document(LoadedDocument(Path("DOC-1.md"), text, metadata), max_words=5)
    assert len(chunks) > 2
    for chunk in chunks:
        assert text[chunk.char_start : chunk.char_end] == chunk.text
        assert chunk.doc_id == "DOC-1"
    assert any("Rules" in chunk.section_path for chunk in chunks)


def test_hybrid_index_search_and_json_round_trip(tmp_path) -> None:
    metadata = make_meta("DOC-1", date(2025, 1, 1))
    chunks = [
        chunk
        for text in ["waiting period is 45 days", "annual limit is 500000", "network hospital approval"]
        for chunk in chunk_document(LoadedDocument(Path("DOC-1.md"), f"# Rules\n{text}", metadata))
    ]
    index = HybridIndex()
    index.build(chunks)
    results = index.search("waiting period", final_k=2)
    assert results
    assert "waiting period" in results[0].chunk.text
    saved = tmp_path / "index.json"
    index.save(saved)
    loaded = HybridIndex.load(saved)
    assert loaded.search("annual limit", final_k=1)[0].chunk.text.endswith("500000")


def test_supersession_graph_chains_partial_amendments_cycles_and_missing_dates() -> None:
    base = make_meta("P1", date(2024, 1, 1))
    latest = make_meta("P2", date(2025, 1, 1), supersedes=["P1"])
    partial = make_meta("A1", date(2025, 6, 1), doc_type="amendment", authority_rank=3, amends=[("P2", "Section 4")])
    graph = SupersessionGraph.from_documents([base, latest, partial])
    assert graph.is_superseded("P1") is True
    assert graph.latest_valid(["P1", "P2"]) == ["P2"]
    assert graph.is_superseded("P2", section="Section 3") is False
    assert graph.is_superseded("P2", section="Section 4") is True
    assert graph.chain("A1") == ["A1", "P2", "P1"]
    assert graph.detect_cycles() == []

    cycle_a = make_meta("A", date(2024, 1, 1), supersedes=["B"])
    cycle_b = make_meta("B", date(2024, 1, 2), supersedes=["A"])
    cyclic = SupersessionGraph.from_documents([cycle_a, cycle_b])
    assert cyclic.detect_cycles()

    unknown_date = make_meta("UNKNOWN", None)
    old = make_meta("OLD", date(2024, 1, 1), supersedes=[])
    missing_graph = SupersessionGraph.from_documents([old, unknown_date.model_copy(update={"supersedes": ["OLD"]})])
    assert missing_graph.is_superseded("OLD") is True
    assert missing_graph.is_superseded("OLD", as_of=date(2025, 1, 1)) is False
