"""Streamlit demo for provenance-preserving TruthGuard answers."""

from __future__ import annotations

import json
import html
import re
from datetime import date
from pathlib import Path

from truthguard.baselines import naive_rag
from truthguard.pipeline import TruthGuardPipeline, build_default_pipeline


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = {
    "T1 · Temporal supersession": "What is the hospitalization waiting period?",
    "T2 · Scope conflict": "What co-payment applies to members on the Standard plan?",
    "T3 · Numeric conflict": "How long after discharge can a reimbursement claim be submitted?",
    "T4 · Definitional conflict": "How many months is the pre-existing condition lookback period?",
    "T5 · Implicit contradiction": "Can an emergency admission proceed without prior approval?",
    "T6 · Unresolvable": "What is the annual hospitalization limit for the Aurelia Standard plan?",
}


def _status_color(status: str) -> str:
    return {
        "resolved": "#198754",
        "conditional": "#0d6efd",
        "abstained": "#dc3545",
        "no_conflict": "#6c757d",
        "not_in_corpus": "#fd7e14",
    }.get(status, "#6c757d")


def _render_answer(st, answer, pipeline: TruthGuardPipeline | None = None) -> None:
    color = _status_color(answer.status)
    st.markdown(
        f"<div style='background:{color};color:white;padding:0.6rem;border-radius:0.35rem'>"
        f"<strong>{answer.status.replace('_', ' ').title()}</strong></div>",
        unsafe_allow_html=True,
    )
    highlighted = html.escape(answer.answer_text)
    highlighted = re.sub(r"(\[[^]]+\])", r"<mark>\1</mark>", highlighted)
    st.markdown(highlighted, unsafe_allow_html=True)
    st.subheader("Claim-level verification")
    for claim in answer.claims:
        icon = {"supported": "✅", "contradicted": "❌", "unsupported": "⚠️"}[claim.verdict]
        st.write(f"{icon} **{claim.verdict}** — {claim.text}")
    if answer.conflicts:
        st.subheader("Conflict positions and trust breakdown")
        for conflict in answer.conflicts:
            with st.expander(f"{conflict.type}: {conflict.rationale}", expanded=True):
                for position in conflict.positions:
                    score = conflict.trust_breakdown.get(position.doc_id)
                    st.write(f"**{position.doc_id}** — {position.claim_text}")
                    if score:
                        st.progress(score.total, text=f"trust {score.total:.2f} · {score.rationale}")
                st.caption(f"Resolution mode: {conflict.resolution_mode}; winner: {conflict.winner_doc_id or 'none'}")
        if pipeline is not None:
            _render_supersession_graph(st, answer, pipeline)
    with st.expander("Agent trace"):
        for step in answer.trace:
            st.write(f"`{step.agent}` → `{step.action}` — {step.output_summary}")
    with st.expander("Citations"):
        for citation in answer.citations:
            st.code(f"{citation.chunk_id} [{citation.char_start}:{citation.char_end}]")


def _render_supersession_graph(st, answer, pipeline: TruthGuardPipeline) -> None:
    """Render the involved document neighborhood when pyvis is available."""

    try:
        from pyvis.network import Network
        import streamlit.components.v1 as components
    except ImportError:
        st.info("Install the full UI dependencies to view the supersession graph.")
        return
    involved = {position.doc_id for conflict in answer.conflicts for position in conflict.positions}
    neighbors = {neighbor for doc_id in involved for neighbor in pipeline.retriever.graph.neighbors(doc_id)}
    nodes = involved | neighbors
    graph = pipeline.retriever.graph.graph.subgraph(nodes).copy()
    if not graph.nodes:
        return
    st.subheader("Supersession graph / timeline")
    network = Network(height="360px", width="100%", directed=True, notebook=False)
    for node, data in graph.nodes(data=True):
        meta = data.get("meta")
        label = f"{node}\n{meta.effective_date if meta else 'unknown'}"
        network.add_node(node, label=label, color="#198754" if node in involved else "#adb5bd")
    for source, target, data in graph.edges(data=True):
        network.add_edge(source, target, label=data.get("kind", "related"))
    components.html(network.generate_html(notebook=False), height=390, scrolling=False)


def _render_benchmark(st) -> None:
    results_path = ROOT / "reports/results.json"
    if not results_path.exists():
        st.info("Run the benchmark evaluation before opening this tab.")
        return
    st.json(json.loads(results_path.read_text(encoding="utf-8")))


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="TruthGuard", page_icon="🛡️", layout="wide")
    st.title("🛡️ TruthGuard")
    st.caption("Adversarial verification for inconsistent document Q&A")
    pipeline: TruthGuardPipeline = build_default_pipeline()

    ask_tab, compare_tab, benchmark_tab = st.tabs(["Ask", "Compare mode", "Benchmark"])
    with ask_tab:
        example = st.selectbox("Demo question", ["Custom question", *EXAMPLES.keys()])
        default = "" if example == "Custom question" else EXAMPLES[example]
        question = st.text_area("Question", value=default, height=90)
        use_as_of = st.checkbox("Use an as-of date", value=False)
        as_of = st.date_input("As-of date", value=date.today(), disabled=not use_as_of)
        if st.button("Verify answer", type="primary") and question.strip():
            answer = pipeline.run(question.strip(), as_of=as_of if use_as_of and isinstance(as_of, date) else None)
            _render_answer(st, answer, pipeline)
    with compare_tab:
        question = st.text_area("Question to compare", value=EXAMPLES["T1 · Temporal supersession"], key="compare_question")
        if st.button("Run Naive RAG vs TruthGuard") and question.strip():
            left, right = st.columns(2)
            with left:
                st.subheader("B0 · Naive RAG")
                _render_answer(st, naive_rag(question, pipeline.retriever, pipeline.synthesizer))
            with right:
                st.subheader("TruthGuard")
                _render_answer(st, pipeline.run(question), pipeline)
    with benchmark_tab:
        _render_benchmark(st)


if __name__ == "__main__":
    main()
