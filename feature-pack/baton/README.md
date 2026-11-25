<div align="center">

# baton

**Keeps worktrees, working memory and archives in one place, so any agent can pick up the work where the last one stopped**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Claude Code, Codex, Gemini, OpenCode and Hermes all write their results to one shared place, `.baton/handoff/` (`PLAN.md` · `JOURNAL.md` · `CURRENT.md` · `NEXT.md`). The next session, with any agent, reads it and continues.
- Creates and cleans up worktrees. On create it assigns ports, makes symlinks and sets up memory; on finish it stores the work in the archive.
- The archive is tracked by git. After a push, other machines can search past decisions. Old archives are pruned on a 30-day basis.
- With `BATON_TMUX_ENABLE=true`, each worktree gets its own tmux session. The session survives a closed laptop, and another agent or a phone over SSH can attach and continue.
- On the main / master root it refuses plan, save, resume and finish. Phases live only inside worktrees.
- It does not do the work itself (plan interviews, coding, review, tests). That goes to an external harness (superpowers, OMX, OMC and others); baton only collects the results.

## Quick start

```bash
git clone https://github.com/yoonhwan/aifp
bash aifp/feature-pack/baton/install.sh   # interactive install
export BATON_TMUX_ENABLE=true             # optional — one tmux session per worktree

# inside your agent — on the main root
/baton:wt-create my-task
cd .worktrees/my-task

# inside the worktree
/baton:plan my-task     # optional — large tasks only
# ... work with an external harness ...
/baton:save             # save the handoff when you stop
/baton:finish           # phase done
/baton:wt-clean         # clean up + archive
```

In the next session, any agent can enter that worktree and call `/baton:resume`, or just say `go` / `continue`; it reads `NEXT.md` and carries on.

## Install

### Let your agent do it

Tell your agent: "Read `feature-pack/baton/INSTALL.md` and install it." Install time is about 3 minutes.

### Manual install

```bash
bash feature-pack/baton/install.sh        # interactive install
export PATH="$HOME/.baton/current/bin:$PATH"   # add to ~/.zshrc or ~/.bashrc
~/.baton/current/bin/baton doctor         # verify
bash feature-pack/baton/uninstall.sh      # remove
```

What `install.sh` does:

1. Detects installed agents (Claude Code · Gemini CLI · OpenCode · Hermes).
2. Copies core to `~/.baton/versions/<version>/` and links `~/.baton/current` (several versions can coexist).
3. Registers baton with each agent.

| Agent | What gets registered |
|---|---|
| Claude Code | commands in `~/.claude/commands/baton/` · link `~/.claude/skills/baton/SKILL.md` · hooks in `~/.claude/settings.json` |
| Gemini CLI | TOML in `~/.gemini/commands/baton/` · hooks in `~/.gemini/settings.json` |
| OpenCode | `~/.config/opencode/commands/baton/` · plugins |
| Hermes | `~/.hermes/plugins/baton.py` |
| Codex · OpenClaw | prints manual setup steps |

4. Asks which baton task to attach to which hook (the recommended set can be chosen automatically).

`settings.json` is backed up to `settings.json.baton-backup` before merging. Uninstall keeps the `.baton/` folders inside your projects (that is your data); delete them by hand.

## Usage

### Commands

| Command | What it does |
|---|---|
| `/baton:wt-create <name>` | worktree + ports + symlinks + memory setup |
| `/baton:plan <id>` | phase plan (`PLAN.md` · `phase.json`) — inside a worktree only |
| `/baton:save` | save the handoff now (`CURRENT.md` set to paused, `NEXT.md` updated) |
| `/baton:resume` | print `NEXT.md` and continue |
| `/baton:finish` | phase done + suggests wt-clean |
| `/baton:wt-clean [path] [--merged]` | clean up the worktree + archive |
| `/baton:status` | phase + active worktrees (with tmux sessions) |
| `/baton:hotfix-mode [finish]` | hotfix directly on main (lite mode · memory off) |
| `/baton:digest <topic>` | compress context from several sessions into one file |
| `/baton:migrate [--dry-run] [path]` | move an existing worktree to the sidecar layout |
| `/baton:help` | print the flow as an ASCII diagram |
| `/baton:install` · `/baton:doctor` · `/baton:upgrade` | install · diagnose · install a new version |
| `/baton:archive list` | archives from the last 30 days |
| `/baton:archive search <query> [--global]` | search metadata + content |
| `/baton:archive show <id>` | details |
| `/baton:archive extract <id>` · `close <id>` | unpack to a temp folder · remove that folder |
| `/baton:archive prune [--dry-run] [--days N]` | remove expired archives |

### Main branch guard

On the main / master root only `wt-create`, `archive list/search`, `status` and `hotfix-mode` work. `plan`, `save`, `resume` and `finish` are refused. Main stays clean and phases live only in worktrees.

### tmux and phone attach

With `BATON_TMUX_ENABLE=true`, `wt-create` makes a tmux session and shows the `tmux attach -t <session>` command. If Tailscale is installed it also prints a one-line SSH command built from `tailscale ip -4` and `$USER`; paste it into a phone app such as Termius or Blink. The agent in a session is set by `BATON_AGENT`; without it, `CODEX_*` / `OMX_SESSION_ID` means Codex and `CLAUDE_*` means Claude. macOS setup (once):

```bash
sudo tailscale set --ssh             # turn on Tailscale SSH
sudo systemsetup -setremotelogin on  # turn on SSH
sudo pmset -c sleep 0                # no sleep while on power
```

### Claude Code hooks

| Hook | What baton does |
|---|---|
| SessionStart | paused notice + environment check + archive prune |
| UserPromptSubmit | append the user's input to `JOURNAL.md` right away |
| PostToolUse | record external harness use in `JOURNAL.md` |
| PreCompact | ask for a backup dump |
| SessionEnd | ask for a backup dump |

### External harnesses

`/baton:plan` lists the harnesses you can use. baton adds instructions so that planning results (`/superpowers:writing-plans`, `$plan`, `/oh-my-claudecode:plan` and so on) go to `PLAN.md`, and execution results (`/superpowers:executing-plans`, `$autopilot`, `/oh-my-claudecode:autopilot` and so on) go to `JOURNAL.md`. There is no catalog file; matching is by name. Change the recommendation with `harnesses.preferred_plan` in `config.json`.

### File layout

```
~/.baton/
├── versions/<version>/      # bin · lib · templates · SPEC.md
└── current -> versions/<version>/

<project>/.baton/
├── config.json              # commit
├── version.lock             # commit
└── archive/                 # commit (synced between machines)

<worktree>/.baton/
├── config.json              # inherits project settings
├── phase.json               # commit
├── handoff/                 # gitignore — PLAN · JOURNAL · CURRENT · NEXT
└── session.lock
```

### Flow cases

| Case | Situation |
|---|---|
| [plan-first](flows/plan-first.md) | long task — start with a plan |
| [wt-first](flows/wt-first.md) | light task — worktree right away |
| [wt-finish](flows/wt-finish.md) | finish one task |
| [branch-pivot](flows/branch-pivot.md) | clean up after splitting into several branches |
| [abandoned](flows/abandoned.md) | give up a phase |
| [hotfix-mode](flows/hotfix-mode.md) | hotfix directly on main |
| [orphan-recovery](flows/orphan-recovery.md) | recover a damaged `.baton/` |
| [handoff-rollback](flows/handoff-rollback.md) | restore a damaged `handoff/` from the archive |

## Requirements

- OS: macOS · Linux
- Required: `bash` 4+ · `git` 2.30+ · `jq` 1.6+ · `tar`
- Optional: `ripgrep` · `gh` · tmux (`BATON_TMUX_ENABLE`) · Tailscale (phone attach)
- API keys / accounts: none

## Links

- [INSTALL.md](INSTALL.md) — install guide for agents
- [core/SPEC.md](core/SPEC.md) — the 4 rules other agents follow (4-file handoff format · `phase.json` schema · worktree location and main guard · port assignment)
- [flows/_index.md](flows/_index.md) — the 8 flow cases
- [docs/MULTI_AGENT_SCENARIOS.md](docs/MULTI_AGENT_SCENARIOS.md) — several agents at once
- Adapters: [Codex](adapters/codex/INSTRUCTIONS.md) · [Gemini](adapters/gemini/INSTRUCTIONS.md) · [OpenCode](adapters/opencode/INSTRUCTIONS.md) · [Hermes](adapters/hermes/INSTALL.md)
- [cairn](../cairn/README.md) — companion pack: ledger for schedules and return points
- [AI Feature Pack catalog](../../README.md)
- License: MIT
