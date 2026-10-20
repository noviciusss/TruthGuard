from datetime import date

from truthguard.agents.critic import CriticAgent
from truthguard.agents.facts import observations, typed_pair
from truthguard.agents.retriever import RetrievedContext
from truthguard.graph.supersession import SupersessionGraph
from truthguard.ingest.index import SearchResult
from truthguard.schemas import Chunk, DocMeta


def _chunk(doc, text, *, effective=date(2025, 1, 1), authority=2, chunk="1"):
    return Chunk(chunk_id=f"{doc}:{chunk}", doc_id=doc, section_path="Rules", text=text,
                 char_start=10, char_end=10 + len(text), doc_meta=DocMeta(
                     doc_id=doc, title=doc, doc_type="circular", effective_date=effective,
                     authority_rank=authority, metadata_source="provided", metadata_confidence=1))


def _conflicts(question, *chunks):
    context = RetrievedContext(question, [SearchResult(c, 1, 1, 1) for c in chunks], [], [])
    return CriticAgent()._find_conflicts(context)


def test_unrelated_numbers_do_not_create_renewal_conflict():
    first = _chunk("A", "A renewal may be completed within 30 days after the due date.\nThe claim deadline is 60 days after discharge.")
    second = _chunk("B", "The 30-day renewal grace period applies to all active plans.\nVersion 2026.")
    assert _conflicts("What is the renewal grace period?", first, second) == []


def test_same_line_other_fact_value_does_not_contaminate_renewal():
    a = _chunk("A", "The renewal grace period is 30 days; the claim submission deadline is 60 days after discharge.")
    b = _chunk("B", "The renewal grace period is 30 days. The claim submission deadline is 90 days after discharge.")
    assert {o.value for o in observations(a) if o.key == "renewal"} == {"30"}
    assert {o.value for o in observations(b) if o.key == "renewal"} == {"30"}
    assert _conflicts("What is the renewal grace period?", a, b) == []


def test_same_document_different_passages_never_suffice():
    first = _chunk("A", "The annual hospitalization limit is 500000 currency units.")
    second = _chunk("A", "The annual hospitalization limit is 600000 currency units.", chunk="2")
    assert _conflicts("What is the annual hospitalization limit?", first, second) == []


def test_age_is_not_a_copayment_percentage():
    a = _chunk("A", "Members aged 60 and above pay 10% co-payment.")
    b = _chunk("B", "Members aged 60 and above pay 10% co-payment.")
    assert _conflicts("What co-payment applies?", a, b) == []
    assert {o.value for o in observations(a)} == {"10"}


def test_type_requires_scope_evidence():
    a = _chunk("A", "The co-payment is 10%.")
    b = _chunk("B", "The co-payment is 20%.")
    assert _conflicts("What co-payment applies?", a, b) == []


def test_t6_requires_known_matching_date_and_authority():
    a = _chunk("A", "The annual hospitalization limit is 500000 currency units.", effective=None)
    b = _chunk("B", "The annual hospitalization limit is 600000 currency units.", effective=None)
    assert _conflicts("What is the annual hospitalization limit?", a, b) == []
    a.doc_meta.effective_date = b.doc_meta.effective_date = date(2025, 1, 1)
    assert _conflicts("What is the annual hospitalization limit?", a, b)[0].type == "T6"


def test_t2_positions_are_exact_fact_lines_not_whole_multifact_chunk():
    a = _chunk("A", "Other rule: 800 units.\n- **co-payment**: 10% for standard plan members.\n")
    b = _chunk("B", "- **co-payment**: 20% for members aged 60 and above.")
    conflict = _conflicts("What co-payment applies?", a, b)[0]
    assert conflict.type == "T2"
    for chunk, position in zip((a, b), conflict.positions):
        assert position.claim_text == chunk.text[position.span.char_start - chunk.char_start: position.span.char_end - chunk.char_start]
        assert "800" not in position.claim_text


def test_t1_requires_an_actual_applicable_graph_edge():
    a = _chunk("A", "The hospitalization waiting period is 30 days.")
    b = _chunk("B", "The hospitalization waiting period is 45 days.")
    left, right = observations(a)[0], observations(b)[0]
    graph = SupersessionGraph([a.doc_meta, b.doc_meta])
    assert typed_pair(left, right, graph) is None
    graph.graph.add_edge("B", "A", kind="supersedes", section=None)
    assert typed_pair(left, right, graph) == "T1"
