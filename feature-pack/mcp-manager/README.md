<div align="center">

# mcp-manager

**A local tool to audit, disable, re-enable and trim Claude Code and Codex MCP servers without printing secret config values.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Lists Claude Code and Codex MCP servers by name only (active and disabled). Config values are not printed.
- Disables one MCP server and enables it again. It keeps a backup before each change so you can restore.
- Keeps only a list you give (`--keep`) and disables every other server in one go (prune).
- Stores the config fragments of disabled servers under `~/.agents/state/mcp-manager/disabled/`.
- Commands that change things are dry-run by default. Files are written only with `--apply`.

## Quick start

```bash
# from the repo root
feature-pack/mcp-manager/core/bin/mcp-manager list --format human
feature-pack/mcp-manager/core/bin/mcp-manager disable stitch --runtime claude --dry-run
```

## Install

To let your agent do it, say "Read `feature-pack/mcp-manager/INSTALL.md` and install it". For now the tool is repo-local and runs in place, so there is nothing else to install.

```bash
feature-pack/mcp-manager/core/bin/mcp-manager list --format human
```

To call it by name from your shell, add it to PATH (from the repo root).

```bash
export PATH="$PWD/feature-pack/mcp-manager/core/bin:$PATH"
mcp-manager list --format human
```

## Usage

### Commands

| Command | What it does |
|---|---|
| `mcp-manager list` | Active and disabled server names per runtime |
| `mcp-manager disable <server>` | Disables one server and stores its config fragment |
| `mcp-manager enable <server>` | Enables a stored server again |
| `mcp-manager prune --keep a,b,c` | Disables every server not in `--keep` (`--keep` is required) |

```bash
mcp-manager list --format human
mcp-manager disable stitch --runtime claude --dry-run
mcp-manager disable stitch --runtime codex --dry-run
mcp-manager prune --runtime claude --keep context,filesystem,think --dry-run
mcp-manager prune --runtime codex --keep filesystem,node_repl,serena,think --dry-run
```

### Options

| Option | Values | Default |
|---|---|---|
| `--runtime` | `list`: `all` · `claude` · `codex` / others: `claude` · `codex` (also accepts `claude-code` · `codex-cli`) | `list` = `all` · others = `codex` |
| `--dry-run` · `--apply` | Show planned changes only · really write | `--dry-run` |
| `--format` | `human` · `json` | `human` |
| `--home` | Path to use instead of your home folder | your home |
| `--keep` | Comma-separated server names (`prune` only) | none |

Exit codes: 0 = success · 2 = bad arguments or a request it cannot do (for example, no stored fragment) · 1 = file read or write error.

### Files it touches

- Codex: `~/.codex/config.toml`
- Claude Code: changes `~/.claude.json` and reads the MCP maps `~/.claude/.mcp.json` · `~/.claude/mcp.json`.
- Stored fragments and backups: `~/.agents/state/mcp-manager/` (`disabled/<runtime>/` · `backups/<runtime>/`)
- These files are written only with `--apply`.

## Requirements

- Python 3.12 or later (standard library only · `typing.override` · `tomllib`)
- bash (the `core/bin/mcp-manager` launcher)
- API keys / accounts: none

## Links

- [INSTALL.md](INSTALL.md)
- [AI Feature Pack catalog](../../README.md)
