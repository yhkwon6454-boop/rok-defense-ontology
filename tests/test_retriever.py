"""Tests for the keyword retriever and ontology query expansion."""

from rok_defense_ontology.ingestion.loader import Document
from rok_defense_ontology.ontology import (
    Entity,
    EntityType,
    Ontology,
    Relation,
    RelationType,
)
from rok_defense_ontology.retrieval import KeywordRetriever


def test_ranks_by_term_overlap():
    docs = [
        Document(id="a", text="임무형 지휘는 분권화된 의사결정을 강조한다"),
        Document(id="b", text="보급 체계와 정비 절차"),
    ]
    results = KeywordRetriever(docs).search("임무형 지휘", top_k=5)
    assert results[0].document.id == "a"
    assert all(r.score > 0 for r in results)


def test_ontology_expansion_boosts_linked_documents():
    onto = Ontology()
    onto.add_entity(Entity("u1", EntityType.UNIT, "기갑여단"))
    onto.add_entity(Entity("e1", EntityType.EQUIPMENT, "K2 전차"))
    onto.add_relation(Relation("u1", RelationType.OPERATES, "e1"))

    docs = [
        # No query-term overlap, but tagged with the neighbor entity e1.
        Document(id="linked", text="장갑 방호력과 기동성", entities=("e1",)),
        Document(id="plain", text="행정 보고서"),
    ]
    results = KeywordRetriever(docs, ontology=onto).search("기갑여단", top_k=5)
    assert [r.document.id for r in results] == ["linked"]


def test_no_matches_returns_empty():
    docs = [Document(id="a", text="alpha bravo")]
    assert KeywordRetriever(docs).search("charlie", top_k=5) == []
