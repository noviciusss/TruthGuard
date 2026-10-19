"""Document and section-level supersession graph."""

from __future__ import annotations

from datetime import date
from typing import Iterable

import networkx as nx

from ..schemas import DocMeta


class SupersessionGraph:
    """A graph whose edge direction is newer document -> older document."""

    def __init__(self, documents: Iterable[DocMeta] = ()) -> None:
        self.graph = nx.DiGraph()
        self.documents: dict[str, DocMeta] = {}
        for document in documents:
            self.add_document(document)
        self._build_edges()

    def add_document(self, document: DocMeta) -> None:
        self.documents[document.doc_id] = document
        self.graph.add_node(document.doc_id, meta=document)

    def _build_edges(self) -> None:
        for document in self.documents.values():
            for target in document.supersedes:
                if target in self.documents:
                    self.graph.add_edge(document.doc_id, target, kind="supersedes", section=None)
            for target, section in document.amends:
                if target in self.documents:
                    self.graph.add_edge(document.doc_id, target, kind="amends", section=section or None)

    @classmethod
    def from_documents(cls, documents: Iterable[DocMeta]) -> "SupersessionGraph":
        return cls(documents)

    @staticmethod
    def _edge_applies(data: dict, section: str | None) -> bool:
        edge_section = data.get("section")
        if edge_section is None:
            return True
        return section is not None and edge_section == section

    def _newer_edge_applies(self, newer: DocMeta, older: DocMeta, as_of: date | None) -> bool:
        if as_of is None:
            return True
        if newer.effective_date is None:
            return False
        return newer.effective_date <= as_of

    def is_superseded(self, doc_id: str, as_of: date | None = None, section: str | None = None) -> bool:
        if doc_id not in self.graph:
            return False
        for newer_id in self.graph.predecessors(doc_id):
            edge = self.graph.edges[newer_id, doc_id]
            if not self._edge_applies(edge, section):
                continue
            newer = self.documents[newer_id]
            older = self.documents[doc_id]
            if self._newer_edge_applies(newer, older, as_of):
                return True
        return False

    def latest_valid(
        self,
        doc_ids: Iterable[str],
        *,
        section: str | None = None,
        as_of: date | None = None,
    ) -> list[str]:
        candidates = [doc_id for doc_id in doc_ids if doc_id in self.documents]
        valid = [doc_id for doc_id in candidates if not self.is_superseded(doc_id, as_of, section)]
        return sorted(
            valid,
            key=lambda doc_id: (
                self.documents[doc_id].effective_date or date.min,
                self.documents[doc_id].authority_rank,
                doc_id,
            ),
            reverse=True,
        )

    def chain(self, doc_id: str) -> list[str]:
        if doc_id not in self.graph:
            return []
        result = [doc_id]
        frontier = [doc_id]
        while frontier:
            current = frontier.pop(0)
            for older in self.graph.successors(current):
                if older not in result:
                    result.append(older)
                    frontier.append(older)
        return result

    def neighbors(self, doc_id: str) -> list[str]:
        if doc_id not in self.graph:
            return []
        return sorted(set(self.graph.predecessors(doc_id)) | set(self.graph.successors(doc_id)))

    def detect_cycles(self) -> list[list[str]]:
        return [list(cycle) for cycle in nx.simple_cycles(self.graph)]
