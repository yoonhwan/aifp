<div align="center">

# cairn

**A CLI that keeps schedules and the return points of multi-agent work in one ledger (`.cairn/plan.yaml`)**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Tracks project / milestone (start · end) / task (start · due) schedules, and shows overdue items and a full Gantt chart (Mermaid).
- When work is split out (fan-out), it records the lineage: `spawned_from` · `return_to` · `merge_back_to` · `fanout_depth`. The return point survives even after a session is cleaned up or a worktree is removed.
- On the way back (fan-in), `cairn return` re-anchors that node and hands off to baton resume.
- It only reads baton (memory), tmuxc (execution) and git. The only things cairn writes are the plan and the recovery metadata.
- Every write goes through one serial writer: lock + atomic write + validate + git commit. It refuses to write on a dirty tree.
- Install once globally; from any project folder it works on that project's `.cairn/` ledger.

## Quick start

```bash
git clone https://github.com/yoonhwan/aifp
bash aifp/feature-pack/cairn/install.sh   # global install to ~/.cairn + Claude Code commands and skill
cairn self-test                           # verify

cd my-app
cairn new-project demo                    # creates .cairn/plan.yaml
cairn status
```

## Install

### Let your agent do it

Tell Claude Code: "Read `feature-pack/cairn/INSTALL.md`, run `bash feature-pack/cairn/install.sh`, then verify with self-test and the hook smoke test." In Codex, run `bash feature-pack/cairn/install.sh`. Install time is about 2 minutes.

### Manual install

```bash
bash feature-pack/cairn/install.sh
export PATH="$HOME/.cairn/current/bin:$PATH"   # unless you open a new shell
cairn self-test                                # self-test OK
bash feature-pack/cairn/uninstall.sh           # remove — global files only, project .cairn/ is kept
```

What `install.sh` does: copies core to `~/.cairn/versions/<version>` · links `current` · creates `~/.cairn/venv` (ruamel.yaml) · adds PATH to `~/.zshrc` · installs `~/.cairn/current/hooks/*` · `~/.claude/commands/cairn` · links `~/.claude/skills/cairn/SKILL.md` · runs `cairn self-test`. Running it again is safe (it adds the new version folder and switches `current`).

Attach the git hooks in each project:

```bash
mkdir -p .git/hooks
ln -sfn "$HOME/.cairn/current/hooks/post-merge" .git/hooks/post-merge
ln -sfn "$HOME/.cairn/current/hooks/post-checkout" .git/hooks/post-checkout
```

## Usage

### Schedule commands

| Command | What it does |
|---|---|
| `cairn init` | set up a `.cairn` ledger in the project |
| `cairn new-project <name>` · `add-milestone <p> <name>` · `add-task <p> <ms> <name> [--days N]` | create |
| `cairn status` · `show <p>` · `overdue [--today]` | view |
| `cairn render` | full Gantt chart (Mermaid) → `.cairn/views/plan.md` |
| `cairn set-status` · `set-date` · `set-priority` | change |

### Recovery commands (fan-out / fan-in)

| Command | What it does |
|---|---|
| `cairn spawn <name> --from <parent>` | split (fan-out) — `spawned_from` · `return_to` · `fanout_depth` set automatically |
| `cairn complete <task> [--force]` | complete + show `return_to` (blocked if missing) |
| `cairn return --to <node>` | come back (fan-in) — re-anchor the node and hand off to baton resume |
| `cairn map [--focus] [--render]` | recovery graph (recovery-map) in Mermaid → termaid |
| `cairn link <node> --execution-ref / --session-ref / --merge-back-to` | record metadata (called by hooks) |
| `cairn reconcile` | compare active worktrees with nodes and find orphans |
| `cairn validate` | check ledger integrity — zero broken recovery links |

Task ids are unique across the whole ledger, because recovery metadata refers to them globally.

### Auto-progress hook

`~/.cairn/current/hooks/cairn-auto-progress` takes a verification pass (`CAIRN_VERIFICATION_STATUS=pass`) and by default only leaves a completion candidate in `.cairn/auto-progress/candidates/`. It runs `cairn complete <task>` only when both `CAIRN_AUTO_PROGRESS=apply` and `CAIRN_TASK_ID` are given.

```bash
# leave a candidate only
CAIRN_TASK_ID=t2 CAIRN_VERIFICATION_STATUS=pass \
  "$HOME/.cairn/current/hooks/cairn-auto-progress"

# apply to the ledger
CAIRN_AUTO_PROGRESS=apply CAIRN_TASK_ID=t2 CAIRN_VERIFICATION_STATUS=pass \
  "$HOME/.cairn/current/hooks/cairn-auto-progress"
```

Call the same command from a PostToolUse hook in Claude Code, or from a shell hook or the end / verification step of a tmuxc session in Codex.

## Requirements

- OS: macOS · Linux
- Required: `python3` 3.9+ · `git` 2.30+ · `ruamel.yaml` (installed into `~/.cairn/venv` automatically)
- Optional: termaid (`cairn map --render`)
- API keys / accounts: none
- Troubleshooting: `cairn: command not found` → open a new shell or export the PATH above · `ModuleNotFoundError: ruamel` → run `bash install.sh` again

## Links

- [INSTALL.md](INSTALL.md) — install guide for agents
- [docs/cairn-design.md](docs/cairn-design.md) — design
- [docs/agent-lifecycle-hook-design.md](docs/agent-lifecycle-hook-design.md) — agent lifecycle hook design
- [baton](../baton/README.md) — companion pack: worktrees, working memory, archive
- [AI Feature Pack catalog](../../README.md)
- License: MIT
