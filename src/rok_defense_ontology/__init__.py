"""Ontology-grounded RAG over ROK defense knowledge.

The package is organized into four stages that compose into a pipeline:

    ingestion -> ontology -> retrieval -> rag

Each stage is independently importable so it can be tested and swapped in
isolation (e.g. replacing the keyword retriever with a vector store).
"""

from rok_defense_ontology.config import Settings

__version__ = "0.1.0"
__all__ = ["Settings", "__version__"]
