<div align="center">

# agent-surface-sync

**Installs or updates shared agent surfaces from `feature-pack/*` and `hooks/` into local runtime folders as links — dry-run by default.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Reads each pack's `manifest.json` and links shared CLIs into `~/.agents/bin`.
- Links runtime skills and support files that the manifest marks `installable`. If that runtime's folder does not exist, it skips them.
- Links the shared hook source `hooks/` to `~/.agents/hooks`.
- If `hooks/manifests/` exists, merges hook entries into `~/.claude/settings.json` (Claude Code) and `~/.codex/hooks.json` (Codex). Existing entries are kept.
- Dry-run by default. It changes things only with `--apply`, and backs up the original first.

## Quick start

```bash
# from the repo root — see the plan only (dry-run)
feature-pack/agent-surface-sync/core/bin/agent-surface-sync
# apply once the plan looks right
feature-pack/agent-surface-sync/core/bin/agent-surface-sync --apply --package baton
```

## Install

To let your agent do it, say "Read `feature-pack/agent-surface-sync/INSTALL.md` and install it". There is nothing else to install; run it in place from the repo root (the default `--repo-root` is the current folder).

```bash
feature-pack/agent-surface-sync/core/bin/agent-surface-sync
```

To call it by name from your shell, add it to PATH (from the repo root).

```bash
export PATH="$PWD/feature-pack/agent-surface-sync/core/bin:$PATH"
agent-surface-sync --package baton,tmuxc
```

Use `--apply` only after the dry-run output looks correct.

## Usage

### Example commands

```bash
agent-surface-sync                                   # dry-run for all packs and runtimes
agent-surface-sync --package baton,tmuxc             # chosen packs only
agent-surface-sync --runtime claude-code --format json
agent-surface-sync --apply --package baton           # really apply
```

### Options

| Option | Values | Default |
|---|---|---|
| `--dry-run` · `--apply` | See the plan only · really apply | `--dry-run` |
| `--package` | Comma-separated pack names | all packs |
| `--runtime` | `all` · `agents` · `claude-code` · `codex-cli` | `all` |
| `--format` | `human` · `json` | `human` |
| `--json` | Path to also save the report as a JSON file | none |
| `--repo-root` | Repo root | current folder |
| `--home` | Path to use instead of your home folder | your home |

Exit codes: 0 = success · 2 = argument or path error · 1 = file read or write error.

### Reading the report

The dry-run report lists planned changes, skipped items and rollback commands. Each change has a state.

| State | Meaning |
|---|---|
| `install` | New link |
| `relink` | Repoints a link that pointed elsewhere |
| `replace-existing` | Backs up a file or folder that is not a link and replaces it with a link |
| `merge` | Merges entries into a hook config file |
| `up-to-date` | Nothing to change |

### Backup and rollback

- Backups go to `~/.agents/state/agent-surface-sync/backups/<operation_id>/`.
- Run a `rollback` line from the report (`rm -rf <target> && mv <backup> <target>`) as is to put things back.

## Requirements

- Python 3.12 or later (standard library only · `typing.override`)
- Runtime folders to link into: Claude Code = `~/.claude` · Codex = `~/.codex` (a missing one is skipped)
- API keys / accounts: none

## Links

- [INSTALL.md](INSTALL.md)
- [AI Feature Pack catalog](../../README.md)
