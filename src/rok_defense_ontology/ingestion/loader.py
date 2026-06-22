"""Load and normalize the source corpus into :class:`Document` chunks.

The on-disk format is JSON Lines: one JSON object per line with at least a
``text`` field. Optional ``id`` and ``entities`` (a list of ontology entity ids
the chunk mentions) let the retriever tie documents back to the graph.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Document:
    """A retrievable chunk of the corpus."""

    id: str
    text: str
    entities: tuple[str, ...] = field(default=())


def load_jsonl(path: str | Path) -> list[Document]:
    """Read a ``.jsonl`` corpus file into a list of :class:`Document`.

    Each line must be a JSON object with a ``text`` field. ``id`` defaults to the
    line number; ``entities`` defaults to empty.
    """
    path = Path(path)
    documents: list[Document] = []
    with path.open(encoding="utf-8") as handle:
        for lineno, line in enumerate(handle):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if "text" not in record:
                raise ValueError(f"{path}:{lineno + 1} missing required 'text' field")
            documents.append(
                Document(
                    id=str(record.get("id", lineno)),
                    text=record["text"],
                    entities=tuple(record.get("entities", ())),
                )
            )
    return documents
