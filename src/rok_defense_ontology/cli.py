"""Command-line entry point: ``rok-onto answer --corpus data/corpus.jsonl "<question>"``.

Wires the stages together: load corpus -> build retriever -> run the pipeline.
"""

from __future__ import annotations

import argparse
import sys

from rok_defense_ontology.config import Settings
from rok_defense_ontology.ingestion.loader import load_jsonl
from rok_defense_ontology.rag.pipeline import RagPipeline
from rok_defense_ontology.retrieval.retriever import KeywordRetriever


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rok-onto", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    answer = sub.add_parser("answer", help="Answer a question over the corpus.")
    answer.add_argument("question", help="The question to answer.")
    answer.add_argument("--corpus", required=True, help="Path to a .jsonl corpus file.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    settings = Settings.from_env()

    if args.command == "answer":
        documents = load_jsonl(args.corpus)
        retriever = KeywordRetriever(documents)
        pipeline = RagPipeline(retriever, settings)
        result = pipeline.answer(args.question)
        print(result.answer)
        print("\nSources:", ", ".join(s.document.id for s in result.sources))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
