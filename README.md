# rok-defense-ontology

Ontology-grounded retrieval-augmented generation (RAG) over ROK (Republic of
Korea) defense knowledge — doctrine, force structure, equipment, and command
philosophy (e.g. 임무형 지휘 / Mission Command).

## Architecture

The package is a four-stage pipeline; each stage is independently importable and
swappable:

```
ingestion  ->  ontology   ->  retrieval  ->  rag
(load corpus)  (typed graph)  (rank docs)    (answer with Claude)
```

- **`ingestion`** — `load_jsonl()` reads a JSON-Lines corpus into `Document`
  chunks (`text`, optional `id`, optional `entities`).
- **`ontology`** — `Ontology` is a small in-memory knowledge graph of typed
  `Entity` nodes and `Relation` edges (unit → equipment, operation → doctrine, …).
- **`retrieval`** — `KeywordRetriever` ranks documents by term overlap and
  **expands the query through the ontology**: entities named in the query boost
  documents tagged with their graph neighbors. `Retriever` is a `Protocol`, so a
  vector store can replace it without touching the pipeline.
- **`rag`** — `RagPipeline` renders retrieved context into a grounded prompt and
  answers via the Claude Messages API. The Anthropic client is injected, so
  tests run offline against a stub.

Configuration lives only in `config.Settings` (resolved from env vars); the
default model is **`claude-opus-4-8`** with adaptive thinking.

## Install

```bash
pip install -e ".[dev]"
```

## Use

```bash
export ANTHROPIC_API_KEY=sk-...
rok-onto answer --corpus data/corpus.sample.jsonl "임무형 지휘란 무엇인가?"
```

## Develop

```bash
ruff check .      # lint
pytest            # tests (offline; no API key needed)
```

## Configuration

| Env var               | Default           | Meaning                          |
| --------------------- | ----------------- | -------------------------------- |
| `ANTHROPIC_API_KEY`   | —                 | Claude API key                   |
| `ROK_ONTO_MODEL`      | `claude-opus-4-8` | Model id                         |
| `ROK_ONTO_TOP_K`      | `5`               | Documents retrieved per question |
| `ROK_ONTO_MAX_TOKENS` | `16000`           | Max output tokens                |
| `ROK_ONTO_EFFORT`     | `high`            | Thinking effort (low–max)        |
