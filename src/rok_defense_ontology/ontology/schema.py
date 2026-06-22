"""The defense-domain ontology schema.

An :class:`Ontology` is a lightweight in-memory knowledge graph: a set of typed
:class:`Entity` nodes connected by typed :class:`Relation` edges. Retrieval uses
it to expand a query with related entities before scoring documents, so an
answer about a *unit* can also surface its *doctrine* and *equipment*.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EntityType(str, Enum):
    """The node types modeled in the ROK defense domain."""

    UNIT = "unit"  # 부대
    EQUIPMENT = "equipment"  # 장비/무기체계
    DOCTRINE = "doctrine"  # 교리
    OPERATION = "operation"  # 작전
    PERSONNEL = "personnel"  # 인원/병과
    COMMAND = "command"  # 지휘체계 (e.g. 임무형 지휘)


class RelationType(str, Enum):
    """The edge types connecting entities."""

    OPERATES = "operates"  # unit -> equipment
    SUBORDINATE_TO = "subordinate_to"  # unit -> unit
    GOVERNED_BY = "governed_by"  # operation -> doctrine
    COMMANDS = "commands"  # personnel -> unit
    PART_OF = "part_of"  # equipment -> equipment


@dataclass(frozen=True)
class Entity:
    """A typed node, addressed by a stable ``id``."""

    id: str
    type: EntityType
    name: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class Relation:
    """A directed, typed edge between two entity ids."""

    source: str
    type: RelationType
    target: str


@dataclass
class Ontology:
    """An in-memory graph of entities and relations."""

    entities: dict[str, Entity] = field(default_factory=dict)
    relations: list[Relation] = field(default_factory=list)

    def add_entity(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def add_relation(self, relation: Relation) -> None:
        for endpoint in (relation.source, relation.target):
            if endpoint not in self.entities:
                raise KeyError(f"unknown entity id: {endpoint!r}")
        self.relations.append(relation)

    def neighbors(self, entity_id: str) -> list[Entity]:
        """Return entities directly connected to ``entity_id`` in either direction."""
        if entity_id not in self.entities:
            raise KeyError(f"unknown entity id: {entity_id!r}")
        linked: list[str] = []
        for rel in self.relations:
            if rel.source == entity_id:
                linked.append(rel.target)
            elif rel.target == entity_id:
                linked.append(rel.source)
        return [self.entities[i] for i in linked]
