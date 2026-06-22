"""Tests for the RAG pipeline using a stub Claude client (no network)."""

from dataclasses import dataclass

from rok_defense_ontology.config import Settings
from rok_defense_ontology.ingestion.loader import Document
from rok_defense_ontology.rag.pipeline import RagPipeline
from rok_defense_ontology.retrieval import KeywordRetriever


@dataclass
class _TextBlock:
    text: str
    type: str = "text"


@dataclass
class _Response:
    content: list


class _StubMessages:
    def __init__(self) -> None:
        self.last_kwargs: dict | None = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return _Response(content=[_TextBlock(text="grounded answer [doc:a]")])


class _StubClient:
    def __init__(self) -> None:
        self.messages = _StubMessages()


def test_answer_grounds_on_retrieved_context():
    docs = [
        Document(id="a", text="임무형 지휘는 지휘관 의도 중심이다"),
        Document(id="b", text="무관한 보급 문서"),
    ]
    retriever = KeywordRetriever(docs)
    client = _StubClient()
    pipeline = RagPipeline(retriever, Settings(), client=client)

    result = pipeline.answer("임무형 지휘란?")

    assert result.answer == "grounded answer [doc:a]"
    assert result.sources[0].document.id == "a"

    # The retrieved context must be embedded in the prompt sent to Claude.
    sent = client.messages.last_kwargs
    assert sent is not None
    assert "[doc:a]" in sent["messages"][0]["content"]
    assert sent["thinking"] == {"type": "adaptive"}
