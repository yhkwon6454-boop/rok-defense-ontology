# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Ontology-grounded RAG over ROK (Republic of Korea) defense knowledge — doctrine,
force structure, equipment, and command philosophy (notably 임무형 지휘 / Mission
Command). The corpus and domain content are Korean; code and identifiers are English.

## Commands

Dependencies, lint, and test all assume an editable install with dev extras.

```bash
pip install -e ".[dev]"              # install package + pytest + ruff
ruff check .                         # lint
ruff check --fix .                   # lint + autofix
pytest                               # full test suite (offline, no API key)
pytest tests/test_retriever.py       # single file
pytest tests/test_pipeline.py::test_answer_grounds_on_retrieved_context  # single test
rok-onto answer --corpus data/corpus.sample.jsonl "임무형 지휘란?"   # run the CLI (needs ANTHROPIC_API_KEY)
```

Tests never hit the network — the pipeline test injects a stub Claude client, so
`pytest` runs without `ANTHROPIC_API_KEY`. Only the live CLI/pipeline needs it.

## Architecture

A four-stage pipeline under `src/rok_defense_ontology/`. Each stage is its own
subpackage, independently importable, and depends only on the stage(s) before it:

```
ingestion  ->  ontology   ->  retrieval  ->  rag
(loader)       (schema)       (retriever)    (pipeline)
```

- **`ingestion/loader.py`** — `load_jsonl()` reads a JSON-Lines corpus into
  frozen `Document` chunks (`id`, `text`, optional `entities` = ontology entity ids).
- **`ontology/schema.py`** — `Ontology` is an in-memory knowledge graph of typed
  `Entity` nodes and `Relation` edges. `neighbors()` is bidirectional. Entity and
  relation kinds are closed enums (`EntityType`, `RelationType`).
- **`retrieval/retriever.py`** — ranks documents and returns `ScoredDocument`s.
  `Retriever` is a `typing.Protocol` — the pipeline depends on the protocol, not
  the implementation, so a vector store can replace `KeywordRetriever` with no
  pipeline change. `KeywordRetriever` does term overlap **plus ontology query
  expansion**: entities named in the query pull in their graph neighbors, and
  documents tagged with those neighbor entities get a score bonus even with zero
  term overlap (see `test_ontology_expansion_boosts_linked_documents`).
- **`rag/pipeline.py`** — `RagPipeline.answer()` retrieves context, renders it
  with `[doc:<id>]` tags into a grounded prompt, and calls the Claude Messages
  API. Returns `RagResult(answer, sources)`.

`cli.py` wires the stages together for the `rok-onto` entry point.

## Conventions

- **Configuration is centralized.** Only `config.Settings` reads `os.environ`
  (via `Settings.from_env()`); everything else takes a `Settings` instance. Do
  not scatter `os.environ` reads into other modules. Env knobs are `ROK_ONTO_*`
  (model, top_k, max_tokens, effort) plus `ANTHROPIC_API_KEY`.
- **The Anthropic client is injected, never constructed eagerly.** `RagPipeline`
  takes an optional `client`; it's lazily built (and `anthropic` lazily imported)
  only when an answer is actually generated. Preserve this — it's what keeps the
  test suite offline. When testing pipeline behavior, pass a stub client like the
  one in `tests/test_pipeline.py`.
- **Data models are frozen dataclasses** (`Document`, `Entity`, `Relation`,
  `ScoredDocument`, `RagResult`); the graph container `Ontology` is mutable.
- **Tokenization is Unicode-aware** (`retriever.tokenize`, regex `\w+`) so Hangul
  is handled — don't swap in ASCII-only splitting.
- Every module uses `from __future__ import annotations`; write annotations
  unquoted (ruff `UP037` enforces this).
- Ruff lint set: `E, F, I, UP, B`, line length 100. Run `ruff check` before committing.

## Claude API usage

When touching `rag/pipeline.py` or adding model calls, follow the in-repo
conventions, which match the current Anthropic SDK:

- Default model is `claude-opus-4-8` (`config.DEFAULT_MODEL`); override via
  `ROK_ONTO_MODEL`.
- Use adaptive thinking — `thinking={"type": "adaptive"}`. Do **not** use
  `budget_tokens` (rejected with a 400 on this model family).
- Control depth via `output_config={"effort": ...}` (`low|medium|high|max`),
  driven by `Settings.effort`.
- Read text from the response by filtering `block.type == "text"` over
  `response.content` — content is a list of typed blocks, not a string.
