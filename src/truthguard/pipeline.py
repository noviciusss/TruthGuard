"""TruthGuard retrieval → draft → critic → resolver pipeline."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, TypedDict

from .agents.critic import CriticAgent
from .agents.resolver import ResolverAgent
from .agents.retriever import RetrieverAgent
from .agents.synthesizer import SynthesizerAgent
from .config import ROOT, load_config
from .graph.supersession import SupersessionGraph
from .ingest.chunker import chunk_document
from .ingest.index import HybridIndex
from .ingest.loader import load_documents
from .llm import LLMRouter
from .schemas import AgentStep, FinalAnswer


class PipelineState(TypedDict, total=False):
    question: str
    as_of: date | None
    context: Any
    draft: Any
    report: Any
    final: FinalAnswer


class TruthGuardPipeline:
    def __init__(
        self,
        retriever: RetrieverAgent,
        synthesizer: SynthesizerAgent,
        critic: CriticAgent,
        resolver: ResolverAgent,
        *,
        max_revision_loops: int = 2,
    ) -> None:
        self.retriever = retriever
        self.synthesizer = synthesizer
        self.critic = critic
        self.resolver = resolver
        self.max_revision_loops = max_revision_loops

    def compile_langgraph(self):
        """Compile the required state-machine flow when LangGraph is installed.

        The manually executed ``run`` method remains the offline fallback so
        schema and graph tests do not need the orchestration package installed.
        """

        try:
            from langgraph.graph import END, START, StateGraph
        except ImportError as exc:  # pragma: no cover - depends on optional install
            raise RuntimeError("LangGraph is not installed; run `make install` for the full runtime") from exc

        graph = StateGraph(PipelineState)
        graph.add_node("retrieve", lambda state: {"context": self.retriever.retrieve(state["question"], as_of=state.get("as_of"))})
        graph.add_node("synthesize", lambda state: {"draft": self.synthesizer.draft(state["question"], state["context"])})
        graph.add_node(
            "critic",
            lambda state: {
                "report": self.critic.critique(
                    state["context"], state["draft"].answer_text, state["draft"].citations, as_of=state.get("as_of")
                )
            },
        )
        graph.add_node(
            "resolve",
            lambda state: {
                "final": self.resolver.resolve(
                    state["question"], state["context"], state["report"], as_of=state.get("as_of")
                )
            },
        )
        graph.add_edge(START, "retrieve")
        graph.add_edge("retrieve", "synthesize")
        graph.add_edge("synthesize", "critic")
        graph.add_edge("critic", "resolve")
        graph.add_edge("resolve", END)
        return graph.compile()

    @staticmethod
    def _step(agent: str, action: str, started: datetime, *, output: str = "", error: str | None = None) -> AgentStep:
        return AgentStep(
            agent=agent,
            action=action,
            started_at=started,
            finished_at=datetime.now(timezone.utc),
            status="failed" if error else "completed",
            output_summary=output,
            error=error,
        )

    def run(self, question: str, *, as_of: date | None = None) -> FinalAnswer:
        trace: list[AgentStep] = []
        start = datetime.now(timezone.utc)
        context = self.retriever.retrieve(question, as_of=as_of)
        trace.append(self._step("retriever", "retrieve", start, output=f"{len(context.results)} chunks"))

        start = datetime.now(timezone.utc)
        draft = self.synthesizer.draft(question, context)
        trace.append(self._step("synthesizer", "draft", start, output=f"{len(draft.citations)} citations"))

        start = datetime.now(timezone.utc)
        report = self.critic.critique(context, draft.answer_text, draft.citations, as_of=as_of)
        trace.append(
            self._step(
                "critic",
                "claims-conflicts-self-critique",
                start,
                output=f"{len(report.claims)} claims; {len(report.conflicts)} conflicts",
            )
        )

        revision_loops = 0
        allowed_revision_loops = 0 if self.critic.llm_enabled else self.max_revision_loops
        while report.unsupported_claim_ids and revision_loops < allowed_revision_loops:
            revision_loops += 1
            start = datetime.now(timezone.utc)
            revised = self.synthesizer.draft(question, context)
            report = self.critic.critique(context, revised.answer_text, revised.citations, as_of=as_of)
            trace.append(
                self._step(
                    "pipeline",
                    f"revise-{revision_loops}",
                    start,
                    output=f"{len(report.unsupported_claim_ids)} unsupported claims remain",
                )
            )

        start = datetime.now(timezone.utc)
        final = self.resolver.resolve(question, context, report, trace=trace, as_of=as_of)
        final.trace.append(self._step("resolver", "resolve-render", start, output=final.status))
        return final


def build_default_pipeline(
    *,
    corpus_dir: str | Path | None = None,
    router: LLMRouter | None = None,
    no_llm_critic: bool = False,
) -> TruthGuardPipeline:
    config = load_config()
    corpus_dir = Path(corpus_dir or ROOT / config["project"].get("data_dir", "data") / "corpus")
    documents = load_documents(corpus_dir, authority_ranks=config.get("authority_rank"))
    chunks = [chunk for document in documents for chunk in chunk_document(document)]
    index = HybridIndex()
    index.build(chunks)
    graph = SupersessionGraph.from_documents(document.meta for document in documents)
    router = router or LLMRouter(config)
    return TruthGuardPipeline(
        RetrieverAgent(index, graph, router=router),
        SynthesizerAgent(router),
        CriticAgent(
            graph,
            router=router,
            use_llm=not no_llm_critic and bool(config.get("critic", {}).get("llm_enabled", True)),
        ),
        ResolverAgent(float(config.get("trust_weights", {}).get("resolution_gap_threshold", 0.15))),
        max_revision_loops=int(config.get("evaluation", {}).get("max_revision_loops", 2)),
    )
