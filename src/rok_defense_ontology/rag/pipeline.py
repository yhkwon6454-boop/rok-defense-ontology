"""The retrieval-augmented generation pipeline.

:class:`RagPipeline` ties a :class:`Retriever` to the Claude Messages API:
retrieve context for a question, render it into a grounded prompt, and ask
Claude to answer using only that context. The Anthropic client is injected so
tests can pass a stub and never touch the network.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from rok_defense_ontology.config import Settings
from rok_defense_ontology.retrieval.retriever import Retriever, ScoredDocument

if TYPE_CHECKING:  # avoid importing anthropic at module import time
    from anthropic import Anthropic

SYSTEM_PROMPT = (
    "You are a defense analyst assistant for ROK (Republic of Korea) doctrine "
    "and force structure. Answer strictly from the provided context. If the "
    "context does not contain the answer, say so plainly. Cite the [doc:<id>] "
    "tags you relied on."
)


@dataclass(frozen=True)
class RagResult:
    """The answer plus the context it was grounded in."""

    answer: str
    sources: list[ScoredDocument]


class RagPipeline:
    """Retrieve-then-generate over the ROK defense corpus."""

    def __init__(
        self,
        retriever: Retriever,
        settings: Settings,
        client: Anthropic | None = None,
    ) -> None:
        self._retriever = retriever
        self._settings = settings
        self._client = client

    def _ensure_client(self) -> Anthropic:
        if self._client is None:
            from anthropic import Anthropic  # imported lazily

            self._client = Anthropic(api_key=self._settings.api_key)
        return self._client

    @staticmethod
    def _render_context(sources: list[ScoredDocument]) -> str:
        return "\n\n".join(f"[doc:{s.document.id}] {s.document.text}" for s in sources)

    def answer(self, question: str) -> RagResult:
        """Answer ``question`` using retrieved context, grounded via Claude."""
        sources = self._retriever.search(question, top_k=self._settings.top_k)
        context = self._render_context(sources)
        user_content = (
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer using only the context above."
        )

        client = self._ensure_client()
        response = client.messages.create(
            model=self._settings.model,
            max_tokens=self._settings.max_tokens,
            system=SYSTEM_PROMPT,
            thinking={"type": "adaptive"},
            output_config={"effort": self._settings.effort},
            messages=[{"role": "user", "content": user_content}],
        )

        answer = "".join(block.text for block in response.content if block.type == "text")
        return RagResult(answer=answer, sources=sources)
