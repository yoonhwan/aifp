<div align="center">

# rag-consumer

**Companion pack that reads only the agent conversation logs you enroll, feeds them into the `rag` engine, and handles search, memory and backups (CLI `ai-rag-consumer`)**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Reads only the Codex rollout JSONL files whose paths you enroll in the config file. It never discovers sessions on its own and never watches folders.
- Records read positions (byte ranges · checksums) in an encrypted SQLCipher ledger, so it resumes after an interruption. Message bodies are not kept in the ledger.
- Applies versioned redaction before anything is stored. If redaction fails, nothing is written.
- Publishes conversation windows into the `rag` engine, searchable with `search`. Past conversations go into an immutable encrypted archive kept apart from search, searchable with `archive-search`.
- Optional: extracts memory candidates from conversations, checks them against exact source quotes, and lets a person confirm · reject · verify them.
- Encrypted backups of the stores, and backup verification.
- A run-once `tick` is called every 5 minutes by launchd or by a macOS menu-bar app (AIRAG.app).

## Quick start

```bash
cd feature-pack/rag-consumer
uv venv --python 3.13
uv pip install ../rag .                     # installs the rag pack (ai-feature-rag) together with this pack

# three store keys + the rag DB key — 64 hex digits each, all different (the runtime never creates keys)
export AIRAG_CONSUMER_KEY_HEX=<64-hex> AIRAG_PROJECTION_KEY_HEX=<64-hex> AIRAG_ARCHIVE_KEY_HEX=<64-hex>
export AIRAG_PROFILE_SOURCE_KEY_HEX=<64-hex>

.venv/bin/ai-rag-consumer --config /abs/path/runtime.json init
.venv/bin/ai-rag-consumer --config /abs/path/runtime.json run --once
.venv/bin/ai-rag-consumer --config /abs/path/runtime.json search "query"
```

## Install

### No INSTALL.md

This pack has no `INSTALL.md` and no original README yet. The steps below come from `pyproject.toml`, source header comments, `ops/` and `macos/`. To let your agent do it, say "Read `feature-pack/rag-consumer/README.md` and install it."

### Manual install

The package name is `ai-feature-rag-consumer` and the entry command is `ai-rag-consumer`. Its dependency `ai-feature-rag==0.1.0` is the `rag` pack in the same repo, so install both together (`uv pip install ../rag .` in Quick start).

1. Create four keys in your secret store (32 bytes = 64 hex digits each · all different).
2. Write `runtime.json` (see "Runtime config" below). Every path must be absolute; symlinks are rejected.
3. Run `init` to create the ledger, projection DB, archive and backup folders.
4. Try one pass with `run --once`, then add a schedule as below.

### Run every 5 minutes

```bash
# A) launchd — fill __PYTHON__ · __CONFIG__ · __CREDENTIALS__ · __LOG_DIR__ in the template
cp ops/com.airag.consumer.plist.template ~/Library/LaunchAgents/com.airag.consumer.plist
launchctl load ~/Library/LaunchAgents/com.airag.consumer.plist

# B) menu-bar app AIRAG.app — needs only swiftc, no Xcode
bash macos/build.sh            # build + sign (ad-hoc when no signing identity is set)
bash macos/build.sh test       # pure-logic tests (never starts the app)
bash macos/build.sh install    # copy to ~/Applications/AIRAG.app
```

- One tick = one consumer pass. launchd's next interval is the retry.
- Keys are filled from a local settings file given with `--credentials` (1Password CLI `op`, or an owner-only key file). Keys already in the environment win.
- AIRAG.app registers itself as a login item from its menu. Change its paths with `python` · `config` · `credentials` · `log_dir` in `~/.config/airag/app.json`.

## Usage

### Commands

Every command has the form `ai-rag-consumer --config <runtime.json> <command>` and prints one JSON line.

| Command | What it does |
|---|---|
| `init` | create the ledger, projection DB, archive and backup folders |
| `run [--once] [--task-completed] [--save] [--allow-gaps]` | read enrolled sources and publish · without `--once` it repeats every `poll_seconds` (stop with Ctrl-C) |
| `status` | current state |
| `search "<query>" [--limit N]` | search published conversations (default 5) |
| `archive-search "<query>" [--limit N]` | search the archive (default 20) |
| `memory-candidates --state <state> [--limit N] [--skip N]` | list memory candidates |
| `memory-confirm` · `memory-reject` · `memory-verify <candidate_id>` | confirm · reject · verify a memory candidate |
| `backup` | make an encrypted backup |
| `verify <backup_id>` | verify a backup |

`python -m airag_consumer.tick --config <runtime.json> [--credentials <file>] [--log-dir <dir>]` is the single-pass entry point (exit codes 0 ok · 10 skipped · 20 config · 30 key · 40 runtime · 50 internal).

### Runtime config

Required fields of `runtime.json` (`schema_version` = 1):

| Field | Meaning |
|---|---|
| `project_root` | project folder (absolute path · must exist) |
| `owner_id` · `tenant_id` · `project_id` | identifiers (letters · digits · `_` · `-`) |
| `consumer_db` · `projection_db` | ledger DB · projection DB paths |
| `archive_root` · `backup_root` | archive · backup folders |
| `profile_source_db` · `profile_key` | the `rag` DB that holds the processing profile, and its `profile_key` (64 hex digits) |
| `collection` | `rag` collection name to publish into |
| `sources` | files to read — each item has `path` · `session_id` · `source_id` |

Optional fields: `token_mode` (default `estimated`) · `allow_gaps` · `memory_enabled` · `memory_endpoint` · `memory_model` · `poll_seconds` (default 30) · `reference`.

### Environment keys

| Name | Used for |
|---|---|
| `AIRAG_CONSUMER_KEY_HEX` | ledger DB key |
| `AIRAG_PROJECTION_KEY_HEX` | projection DB key |
| `AIRAG_ARCHIVE_KEY_HEX` | archive key |
| `AIRAG_PROFILE_SOURCE_KEY_HEX` | key of `profile_source_db` (the rag DB) · needed when the stores are first created |
| `AIRAG_MEMORY_API_KEY` | optional · key for the memory-extraction server |

All keys are 64 hex digits and must differ from each other. The runtime does not pass them on to unrelated child processes.

## Requirements

- Python 3.13 or newer, below 3.15 · `uv`
- The `rag` pack (`ai-feature-rag` 0.1.0) · `sqlcipher3` 0.6.2
- Scheduling: macOS launchd, or `swiftc` to build AIRAG.app
- Optional: 1Password CLI `op` (tick key source) · a memory-extraction server (`memory_endpoint` · `memory_model`)
- API keys / accounts: `AIRAG_MEMORY_API_KEY` only when memory extraction is on

## Links

- [rag](../rag/README.md) — the encrypted RAG engine this pack uses
- [ops/com.airag.consumer.plist.template](ops/com.airag.consumer.plist.template) — launchd template
- [macos/build.sh](macos/build.sh) — build · test · install AIRAG.app
- [AI Feature Pack catalog](../../README.md)
