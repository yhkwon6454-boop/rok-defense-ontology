"""Corpus ingestion: turn source files into retrievable :class:`Document` chunks."""

from rok_defense_ontology.ingestion.loader import Document, load_jsonl

__all__ = ["Document", "load_jsonl"]
