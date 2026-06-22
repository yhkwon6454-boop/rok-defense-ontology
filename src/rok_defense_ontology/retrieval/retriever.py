"""Document retrieval over the ingested corpus.

:class:`Retriever` is the interface the RAG pipeline depends on; swap in a
vector-store implementation later without touching the pipeline. The default
:class:`KeywordRetriever` is a dependency-free term-overlap baseline that also
expands the query through the ontology graph: when a query term matches an
entity, that entity's neighbors boost documents tagged with them.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Protocol

from rok_defense_ontology.ingestion.loader import Document
from rok_defense_ontology.ontology.schema import Ontology

_TOKEN = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Lowercase word-tokenize, Unicode-aware (handles Hangul)."""
    return [t.lower() for t in _TOKEN.findall(text)]


@dataclass(frozen=True)
class ScoredDocument:
    """A retrieved document paired with its relevance score."""

    document: Document
    score: float


class Retriever(Protocol):
    """The contract the RAG pipeline relies on."""

    def search(self, query: str, top_k: int) -> list[ScoredDocument]:
        """Return the ``top_k`` most relevant documents for ``query``."""
        ...


class KeywordRetriever:
    """Term-overlap retriever with optional ontology-driven query expansion."""

    def __init__(self, documents: list[Document], ontology: Ontology | None = None) -> None:
        self._documents = documents
        self._ontology = ontology
        self._doc_tokens = {doc.id: Counter(tokenize(doc.text)) for doc in documents}

    def _expanded_entity_ids(self, query: str) -> set[str]:
        """Find ontology entities named in the query, plus their neighbors."""
        if self._ontology is None:
            return set()
        terms = set(tokenize(query))
        matched: set[str] = set()
        for entity in self._ontology.entities.values():
            names = (entity.name, *entity.aliases)
            if any(set(tokenize(name)) & terms for name in names):
                matched.add(entity.id)
        expanded = set(matched)
        for entity_id in matched:
            expanded.update(n.id for n in self._ontology.neighbors(entity_id))
        return expanded

    def search(self, query: str, top_k: int) -> list[ScoredDocument]:
        query_terms = Counter(tokenize(query))
        boost_ids = self._expanded_entity_ids(query)

        scored: list[ScoredDocument] = []
        for doc in self._documents:
            counts = self._doc_tokens[doc.id]
            overlap = sum(min(query_terms[t], counts[t]) for t in query_terms)
            if overlap == 0 and not (boost_ids & set(doc.entities)):
                continue
            # Each ontology-linked entity adds a flat bonus to the term overlap.
            entity_bonus = len(boost_ids & set(doc.entities))
            scored.append(ScoredDocument(document=doc, score=overlap + entity_bonus))

        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:top_k]
