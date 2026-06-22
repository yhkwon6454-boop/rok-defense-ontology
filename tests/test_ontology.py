"""Tests for the ontology graph."""

import pytest

from rok_defense_ontology.ontology import (
    Entity,
    EntityType,
    Ontology,
    Relation,
    RelationType,
)


def _sample_ontology() -> Ontology:
    onto = Ontology()
    onto.add_entity(Entity("u1", EntityType.UNIT, "수도기계화보병사단"))
    onto.add_entity(Entity("e1", EntityType.EQUIPMENT, "K2 전차", aliases=("흑표",)))
    onto.add_relation(Relation("u1", RelationType.OPERATES, "e1"))
    return onto


def test_neighbors_are_bidirectional():
    onto = _sample_ontology()
    assert [e.id for e in onto.neighbors("u1")] == ["e1"]
    assert [e.id for e in onto.neighbors("e1")] == ["u1"]


def test_relation_to_unknown_entity_raises():
    onto = _sample_ontology()
    with pytest.raises(KeyError):
        onto.add_relation(Relation("u1", RelationType.OPERATES, "missing"))


def test_neighbors_unknown_entity_raises():
    with pytest.raises(KeyError):
        Ontology().neighbors("nope")
