<div align="center">

# rag

**`airag` (CLI `ai-rag`): a RAG engine that keeps your documents in an encrypted local DB, searches them and returns evidence as JSON**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Stores sources, chunks and vectors in one encrypted SQLite (SQLCipher) file. Vectors use sqlite-vec, keywords use FTS5.
- Handles explicit requests only: `add` · `update` · `delete` · `manage restore`. No folder watching, scheduling or auto-discovery — the consuming project sends the events.
- An update creates a new revision; earlier original bytes and past search results (manifests) are kept. Deleted sources can be restored.
- A processing profile (embedding + optional LLM + normalizer settings) is registered once and never changes. With an LLM attached, it builds semantic groups, tags, summaries and an English translation before embedding.
- Search = BM25 + vectors + RRF. From the results it expands structural, reference and semantic links within a budget (depth · chunks · tokens · bytes) and returns an evidence bundle.
- Document adapters (`documents` extra): PDF · DOCX · XLSX · HWP5 · HWPX, plus an explicit OCR / vision mode for PNG · JPEG · BMP · TIFF.
- Every command prints one JSON envelope `{schema_version, request_id, ok, command, data, error}`. Backup, restore and diagnostics use the same shape.
- The engine only returns evidence. Writing the final answer is the job of the agent on top.

### Pipeline

```text
source --[Docling · HWP/HWPX adapter · conversation adapter]--> standard bundle (Markdown + structure · anchors)
  --[HybridChunker]--> chunks --[publish embeddings · FTS]--> index
  --[BM25 + vectors + RRF]--> search --[budgeted structural · semantic expansion]--> evidence (can include the original)
```

## Quick start

```bash
cd feature-pack/rag
uv sync                                     # creates .venv and installs airag

head -c 32 /dev/urandom > my.key            # 32-byte key — lose it and the DB cannot be opened
chmod 600 my.key
.venv/bin/ai-rag init my.db --key-fd 3 3< my.key
.venv/bin/ai-rag manage doctor              # runtime diagnosis
```

## Install

### No INSTALL.md

This pack has no `INSTALL.md` yet. To let your agent install it, say "Read `feature-pack/rag/README.md` and `pyproject.toml` and install it"; it follows the manual steps below.

### Manual install

The package name is `ai-feature-rag` and the entry command is `ai-rag` (`krb-rag` is an alias for the same command).

```bash
cd feature-pack/rag
uv sync                                     # base dependencies
uv sync --extra documents                   # PDF · DOCX · XLSX · OCR adapters (docling · easyocr)
uv run pytest                               # offline tests (tests marked integration are skipped by default)
```

## Usage

### Commands

| Command | What it does |
|---|---|
| `ai-rag init <db>` | create a new encrypted DB |
| `ai-rag add` · `update` · `delete` | register · update (new revision) · delete a source — resending the same `--request-id` is applied only once |
| `ai-rag search` | search with `--collection` · `--query` · `--profile-key` · `--expand` expands in the same snapshot |
| `ai-rag expand --manifest-id N` | widen the evidence of a past search (`--max-depth` · `--max-chunks` · `--max-tokens` · `--max-bytes` · `--max-edges`) |
| `ai-rag fetch original` · `source` · `chunk` · `manifest` · `expansion` | get back original bytes · normalized output · a chunk · a past search · a past expansion |
| `ai-rag manage profile --config <file>` | register a processing profile (JSON file: `embedding` · optional `llm` · `normalizer`) |
| `ai-rag manage status` · `list` · `show` | status · list · one source |
| `ai-rag manage retry` · `reindex` · `restore` | retry a failed job · reprocess with another profile · restore a deleted source |
| `ai-rag manage backup` · `restore-backup` | make a backup · restore from a backup |
| `ai-rag manage doctor` · `verify` | install diagnosis · DB check |

DB commands other than `init` take `--db <db>` and `--key-fd <fd>`.

### Example

```bash
K="--db my.db --key-fd 3"

# 1) register a processing profile — keep profile_key from the response data
.venv/bin/ai-rag manage profile $K --config profile.json 3< my.key

# 2) add a text source
.venv/bin/ai-rag add $K --request-id req-1 --collection notes --source-key note-1 \
  --text "hello" --profile-key <profile_key> 3< my.key

# 3) search — use manifest_id from the response for expand · fetch manifest later
.venv/bin/ai-rag search $K --collection notes --query "hello" \
  --profile-key <profile_key> --top-k 5 3< my.key
```

In `profile.json`, `embedding` holds `provider` (`lmstudio` or `openai-compatible`) · `endpoint` · `model` · `revision` · `dimension` · `tokenizer_revision` (a pinned commit or tag). The full field list is `EmbeddingSpaceConfig` in [src/airag/embeddings.py](src/airag/embeddings.py); LLM fields are `ChatCompletionConfig` in [src/airag/llm_enrichment.py](src/airag/llm_enrichment.py). For calling it from Python, see [examples/explicit_consumer.py](examples/explicit_consumer.py).

### Key handling

- The key is 32 raw bytes, read only from an open file descriptor given with `--key-fd`. Keys never appear in command-line arguments or logs.
- Reading the key from the macOS Keychain is not available yet.

### Known limits

- Vector search is an exact full comparison (O(N)). No claim is made about ANN performance or Korean keyword-search quality.
- Not supported: XLSX recalculation and array/data-table formulas, protected or distribution HWP, automatic rendering of DOCX DrawingML other than bitmaps.
- HWP/HWPX anchors are by section · paragraph · table (no rendered page numbers).
- Pictures inside documents are extracted and kept, but vision processing is not run on them automatically.
- The model weight revision is not proven automatically. The operator's declared value and the runtime fingerprint are kept apart.

## Requirements

- Python 3.13 or newer, below 3.15 · `uv` 0.10.0 or newer
- Embedding server: OpenAI-compatible `/v1/embeddings` (LM Studio and others)
- Optional: OpenAI-compatible chat server (LLM preprocessing)
- Optional: HWP5 documents = `java` + a local hwplib jar (document adapter setting `hwp_classpath`)
- API keys / accounts: none for the engine itself

## Links

- [docs/README.md](docs/README.md) — documentation guide (Korean)
- [docs/PLAN.md](docs/PLAN.md) — implementation plan · verification record · support limits (Korean)
- [docs/DECISIONS.md](docs/DECISIONS.md) — design decision log (Korean)
- [examples/explicit_consumer.py](examples/explicit_consumer.py) — example consumer-side event adapter
- [rag-consumer](../rag-consumer/README.md) — companion pack that feeds conversation logs into this engine
- [AI Feature Pack catalog](../../README.md)
