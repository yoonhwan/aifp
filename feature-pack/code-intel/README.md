<div align="center">

# code-intel

**One command, `ci`, for code search, symbols, references and structural patterns — the same in every agent harness**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Semantic and keyword search (BM25 + complete AST blocks) — `ci search "<q>" <path>`
- Symbol definitions, callers and dependencies (definitions first) — `ci sym <sym> --callers --scope <dir>`
- File structure and token count before you read a file — `ci outline <file>`
- Precise LSP references, definitions and implementations (started only when needed) — `ci refs "<file>#<sym>"`
- ast-grep structural patterns — `ci ast '<pattern>' <path> -l py`
- Measures how well your agents follow the "use `ci`" rule — `ci-audit --days 1 --by-harness`
- No index, zero resident processes. The same commands in Claude Code · Codex · OpenCode · Pi · Hermes. Replaces Serena MCP.

### Why it exists

Measured on a 62k-file, 49 GB worktree.

| Task | Serena | code-intel |
|---|---|---|
| Semantic search | 127.25 s (empty result) | 4.6 s (ranked results) |
| Caller tracing | 4.2 s+ (activation first) | 0.36 s |
| Resident memory | 946 MB → 5.1 GB leak (peak 21 GB) | 0 MB |
| Setup steps | activate_project + config check | none |

## Quick start

```bash
# from the repo root: binaries + skill links + ci entry point + diagnosis (safe to run again)
bash feature-pack/code-intel/skill/scripts/install.sh

ci doctor                                  # install · versions · LSP · smoke
ci search "dispatch" src --max 5           # first search
```

## Install

### Let your agent do it

Tell your agent: "Read `feature-pack/code-intel/INSTALL.md` and install it." The agent links the skill → installs the binaries → verifies → connects the instructions. Install time (~3 min).

### Manual install

What `install.sh` does:

1. Keeps `probe` (0.6.0-rc342) and `tilth` (0.12.0) if they are already there; otherwise installs them into `~/.local/bin`.
2. Symlinks the skill folder into the Claude Code · Pi/Hermes · Codex · OpenCode skill roots (a harness whose root folder does not exist is skipped).
3. Creates the `~/.local/bin/ci` entry point.
4. Runs `ci doctor` as a final check.

```bash
# diagnose only, change nothing
bash feature-pack/code-intel/skill/scripts/install.sh --check

# verify after install
ci doctor                                  # probe/tilth versions + LSP + smoke
ci sym <any-symbol> --scope <subdir>       # answers within 0.4 s
ci outline <file>                          # token count in the header
```

Pass criteria: `ci doctor` output + a `ci sym` answer + a token count from `ci outline`.

### Connect your agent's instructions

Without this, agents do not use `ci`. Add the lines below to your harness's global instruction file (Claude Code `~/.claude/CLAUDE.md` · Codex `~/.codex/AGENTS.md` · OpenCode `~/.config/opencode/AGENTS.md` · Pi `~/.pi/agent/AGENTS.md`).

```markdown
**HARD RULE: use `ci` first for code symbols, references and structure. Use grep/rg/git grep only for logs, config, strings and file-existence checks.
Never call `probe`/`tilth` directly — always go through `ci` (built-in timeout and scope guard). No activation step.**
```

### Rollback

```bash
rm ~/.claude/skills/code-intel ~/.agents/skills/code-intel \
   ~/.codex/skills/code-intel ~/.config/opencode/skills/code-intel \
   ~/.local/bin/ci ~/.local/bin/ci-audit
# you may keep the probe/tilth binaries — they also work as standalone CLIs
```

## Usage

### Commands

| Command | What it does |
|---|---|
| `ci search "<query>" [path] [--max N] [--no-tests]` | semantic / keyword search (BM25 + AST blocks · test files included by default) |
| `ci sym <name> [--scope P] [--callers\|--deps]` | symbol definition, callers, dependencies (definitions first) |
| `ci outline <file> [--section S]` | file outline (+ token count) |
| `ci refs "<file>#<sym>" [--json]` | precise LSP references |
| `ci def "file#sym"` · `ci impl "file#sym"` | LSP definition · implementations |
| `ci ast '<pattern>' [path] [-l lang]` | ast-grep structural pattern |
| `ci lsp up [--scope P]` · `down` · `status` | start · stop · status of the LSP daemon |
| `ci lsp repair [--ws <name>]` | repair an LSP crash loop (moves the cache aside instead of deleting it) |
| `ci doctor` | install · versions · daemon · smoke diagnosis |
| `ci bench [--queries FILE]` | performance regression (p50/p95) |
| `ci-audit [--days N] [--by-harness] [--csv FILE] [--json]` | counts `ci`, grep and Serena calls in session logs to measure compliance |

Set `PROBE_BIN` · `TILTH_BIN` to force a binary path.

### Safety guards

- Each search runs only within `CI_TIMEOUT` (default 60 s). Using the repo root as scope prints a warning. If you really need a full scan, use `CI_ALLOW_HEAVY=1 CI_TIMEOUT=600`.
- When probe panics on Korean Markdown, the search retries with `-i '*.md'` automatically.
- When a multi-word query returns nothing, it retries as `A OR B` automatically.
- Python structural patterns fall back to ast-grep.
- Do not call `probe` or `tilth` directly; always go through `ci`.

### Known pitfalls

| Pitfall | What to do |
|---|---|
| Calling `tilth` directly with the repo root as scope runs the CPU away (measured 585% CPU · load 139) | go through `ci` · scope a subfolder · full scan with `CI_ALLOW_HEAVY=1 CI_TIMEOUT=600` |
| probe panics on Korean Markdown (SIGABRT) | `ci search` retries with `-i '*.md'` automatically |
| Multi-word queries are read as AND and return nothing | `ci search` retries as `A OR B` automatically |
| Python structural patterns return nothing (probe bug) | `ci ast` falls back to ast-grep (install `ast-grep`) |
| The Python LSP is pylsp (not pyright) · no `call-hierarchy` | `uv tool install python-lsp-server` · for callers use `ci sym --callers` |

## Requirements

- macOS (arm64 · x86_64) or Linux. `install.sh` downloads the macOS build of `probe`; on Linux, put `probe` 0.6.0-rc342 on your PATH first and it is used as is.
- `curl` · `tar` · `python3`
- `npx` or `cargo` to install `tilth`
- Optional: `ast-grep` (`brew install ast-grep` · Python structural-pattern fallback) · `python-lsp-server` (`uv tool install python-lsp-server` · `ci refs` for Python)
- API keys / accounts: none

## Links

- [INSTALL.md](INSTALL.md) — install guide for the agent
- [skill/SKILL.md](skill/SKILL.md) — agent skill
- [skill/scripts/install.sh](skill/scripts/install.sh) — install script
- [AI Feature Pack catalog](../../README.md)
