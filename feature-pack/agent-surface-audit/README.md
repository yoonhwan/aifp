<div align="center">

# agent-surface-audit

**A public-safe, read-only dry-run inventory of your agent skill and hook surfaces.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Lists the skill and hook surfaces that agents can see: source packages, user skill roots, project overlays and hook config paths.
- Reads only safe metadata. It never reads secret contents.
- Does not modify live `~/.claude`, `~/.codex`, `~/.agents`, project overlay settings, symlinks, hooks, sessions, logs or auth material.
- Flags duplicate exposure risks and broken symlinks, and proposes future actions together with rollback commands.
- Prints a human-readable report or JSON, and can write the JSON to a file.

## Quick start

```bash
feature-pack/agent-surface-audit/core/bin/agent-surface-audit --dry-run
```

## Install

This pack does not install anything into your live runtime. It is intentionally read-only, so you run it in place from a checkout. See [INSTALL.md](INSTALL.md).

To call it as `agent-surface-audit`, put its `bin` folder on your `PATH` for the current shell:

```bash
export PATH="$PWD/feature-pack/agent-surface-audit/core/bin:$PATH"
agent-surface-audit --dry-run
```

Do not symlink this pack into `~/.claude`, `~/.codex`, `~/.agents` or project overlay roots as part of the dry-run review. Future installers are meant to be generated from reviewed reports and to include rollback commands.

## Usage

### Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Required. The tool is read-only by contract and refuses to run without it |
| `--repo-root PATH` | Repository to inspect (default: the current directory) |
| `--home PATH` | Home directory to inspect (default: your home directory) |
| `--json PATH` | Also write the JSON report to this file |
| `--format human\|json` | Output format on stdout |
| `--public-safety` | Report only the public safety section |

### Examples

```bash
agent-surface-audit --dry-run
agent-surface-audit --dry-run --repo-root "$PWD" --home "$HOME" --json report.json
agent-surface-audit --dry-run --format json
agent-surface-audit --dry-run --public-safety --format json
```

### What the report covers

- Public safety buckets
- Source packages under `feature-pack/*`
- User runtime skill roots under `$HOME/.claude/skills`, `$HOME/.codex/skills` and `$HOME/.agents/skills`
- Project overlays under `.claude/skills`, `.codex/skills` and `.agents/skills`
- Hook config path existence metadata only
- Duplicate exposure risks and broken symlinks
- Proposed future actions and rollback commands
- Skipped private paths, by class only

### Notes

- Findings are report data, not process failures. The command exits non-zero only for invalid arguments or runtime/tool errors.
- Codex/OMO skill exposure remains `~/.codex/skills` until active load behavior proves otherwise. `~/.agents/skills` is for compatibility and overlay only.
- Verification scripts live under `test/` (`verify.sh` and `verify_manifest_contract.sh`).

## Requirements

- `bash`
- `python3` (3.10 or newer — the code uses `match` statements)
- `jq` (for the verification scripts under `test/`)
- No API key needed

## Links

- [INSTALL.md](INSTALL.md) — how to run it in place
- [AI Feature Pack catalog](../../README.md)
