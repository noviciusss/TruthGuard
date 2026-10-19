"""Streamlit demo for provenance-preserving TruthGuard answers."""

from __future__ import annotations

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


def _inject_styles(st) -> None:
    st.markdown(
        """
        <style>
        .tg-hero {
            padding: 1.25rem 1.5rem;
            border-radius: 1rem;
            background: linear-gradient(135deg, #102a43 0%, #1f4e79 55%, #2f80ed 100%);
            color: white;
            margin-bottom: 1rem;
        }
        .tg-hero h1 { margin: 0; font-size: 2.1rem; }
        .tg-hero p { margin: .35rem 0 0; color: #d9eaf7; }
        .tg-card {
            border: 1px solid #d9e2ec;
            border-radius: .75rem;
            padding: .75rem 1rem;
            background: #f7fafc;
            min-height: 5rem;
        }
        .tg-card-label { color: #627d98; font-size: .78rem; text-transform: uppercase; letter-spacing: .05em; }
        .tg-card-value { color: #102a43; font-size: 1.35rem; font-weight: 700; margin-top: .25rem; }
        mark { background: #fff3bf; color: #102a43; border-radius: .2rem; padding: 0 .15rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_metric_cards(st, answer) -> None:
    cards = [
        ("Status", answer.status.replace("_", " ").title()),
        ("Claims checked", str(len(answer.claims))),
        ("Conflicts", str(len(answer.conflicts))),
        ("Citations", str(len(answer.citations))),
    ]
    columns = st.columns(len(cards))
    for column, (label, value) in zip(columns, cards):
        with column:
            st.markdown(
                f"<div class='tg-card'><div class='tg-card-label'>{label}</div>"
                f"<div class='tg-card-value'>{value}</div></div>",
                unsafe_allow_html=True,
            )


def _render_answer(st, answer, pipeline: TruthGuardPipeline | None = None) -> None:
    _render_metric_cards(st, answer)
    st.markdown("### Answer")
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
    results_path = ROOT / "reports/results.md"
    if not results_path.exists():
        st.info("Run the benchmark evaluation before opening this tab.")
        return
    st.markdown(results_path.read_text(encoding="utf-8"))


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="TruthGuard", page_icon="🛡️", layout="wide")
    _inject_styles(st)
    st.markdown(
        "<div class='tg-hero'><h1>🛡️ TruthGuard</h1>"
        "<p>Adversarial verification for inconsistent document Q&amp;A — expose conflict, preserve provenance, abstain safely.</p></div>",
        unsafe_allow_html=True,
    )
    pipeline: TruthGuardPipeline = build_default_pipeline()

    with st.sidebar:
        st.header("Control panel")
        st.success("Offline demo ready")
        st.caption("The current UI uses the local synthetic Aurelia Health corpus.")
        st.divider()
        st.subheader("What to inspect")
        st.markdown(
            "- **Ask**: run a question through TruthGuard.\n"
            "- **Compare**: see naive RAG beside TruthGuard.\n"
            "- **Benchmark**: read the recorded results."
        )
        st.divider()
        st.caption("Tip: start with T1 or T6 to see resolution versus abstention.")

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
