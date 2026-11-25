<div align="center">

# tmuxc

**Open and control Claude Code, Codex, OMX, OpenCode, Command Code and Pi agent sessions in tmux with one command.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Open a Claude Code, Codex CLI, OMX, OpenCode, Command Code or Pi session in a project folder or git worktree with a single `tmuxc open` line.
- Give each session a role (`worker`, `orchestrator` or `designer`) when you open it.
- Send a message to another session and read its screen (`tmuxc send`, `tmuxc msg`, `tmuxc ask`). Sending and capturing follow a standard verified send / capture procedure.
- Save the open sessions as a snapshot before shutdown and bring them back with `tmuxc restore` after a reboot.
- Branch into a new conversation without touching the parent one (`tmuxc fork`, using each engine's native fork).
- List, kill and clean up sessions with the same CLI (`tmuxc list`, `kill`, `clean`).

## Quick start

```bash
bash feature-pack/tmuxc/install.sh
tmuxc --help
tmuxc open "$PWD" --name TMUXC_SMOKE --agent codex --role worker --dry-run
```

## Install

### Install with an agent

Ask your agent:

```text
Read feature-pack/tmuxc/INSTALL.md and install it
```

### Manual install

```bash
bash feature-pack/tmuxc/install.sh
```

What `install.sh` does:

- Checks that `bash`, `git` and `tmux` are present.
- Copies the core and the Claude Code skill to `~/.tmuxc/versions/<version>/` and updates the `~/.tmuxc/current` symlink.
- Links the CLI as `~/.local/bin/tmuxc`. If `~/.local/bin` is not on your PATH, it is added to `~/.zshrc` or `~/.bashrc`.
- If Claude Code is installed, links `~/.claude/skills/tmuxc` to the installed copy.

### Verify

```bash
tmuxc --help
tmuxc list
test -e "$HOME/.claude/skills/tmuxc/SKILL.md"
test -e "$HOME/.claude/skills/tmuxc/COMM-GUIDE.md"
```

### Uninstall

```bash
bash feature-pack/tmuxc/uninstall.sh
```

The uninstall script removes only `~/.tmuxc` and the `~/.local/bin/tmuxc` and `~/.claude/skills/tmuxc` links that point to the installed copy. It does not delete your project files or tmux sessions.

## Usage

### Commands

```bash
tmuxc open <path> --name NAME --agent claude|codex|omx|opencode|cmd|pi --role worker|orchestrator|designer [--pi-skill PATH]...
tmuxc wt <worktree-path> --name NAME --prompt "Read NEXT.md and start"
tmuxc list
tmuxc ask <name> [lines]              # read the last lines of a session screen (capture-pane)
tmuxc send <name> "message"           # send a message to a session
tmuxc msg <name> "message"
tmuxc kill <name>
tmuxc clean
tmuxc save [--keep N]                 # global session snapshot before shutdown (keeps [1m], effort, session_id)
tmuxc restore [--from latest] [--go]  # restore after reboot (snapshot first; --scan forces a log scan)
tmuxc fork <path> --name NEW (--from LIVE_SESSION | --source ID --agent claude|codex|opencode|cmd|pi) [--model ID] [--ctx 1m] [--effort E] [--prompt TEXT]
```

- For seats that are not Claude (pi, codex, opencode, cmd), `open` and `fork` set `GIT_EDITOR=true`, `GIT_SEQUENCE_EDITOR=true` and `GIT_TERMINAL_PROMPT=0` in the tmux session env, so git never stalls waiting for an editor or a prompt. This applies to new seats only, not to seats that are already running.

### Pi seats

```bash
tmuxc open . --name PI_WORKER --agent pi --role worker --model <provider/model>
tmuxc open . --name PI_REVIEW --agent pi --role orchestrator --effort high
```

- tmuxc issues a `--session-id <uuid>` and stores it in the session env (`TMUXC_PI_SESSION_ID`, `TMUXC_PI_MODEL`, `TMUXC_PI_THINKING`). Even when the process title hides argv, `save` and `restore` recover the exact session.
- `worker` and `implementer` get the tools `read,bash,edit,write,grep,find,ls`; `orchestrator`, `planner` and `analysis` get read-only tools.
- `--effort` maps to Pi's `--thinking`.
- `--like <pi-session>` inherits the model and thinking level of a running Pi.

`--pi-skill` loads only the skills you pick into a Pi seat:

```bash
tmuxc open <path> --agent pi --pi-skill ~/.agents/skills/code-intel --pi-skill ~/.agents/skills/tmuxc --dry-run
```

- It turns off Pi's automatic skill discovery (`--no-skills`) and loads only the given paths, in order.
- A path is a `SKILL.md` file or a folder that contains `SKILL.md`. A missing path is rejected with rc≠0 and nothing is created.
- It is accepted only with `--agent pi` (any other agent gives rc≠0). Without the option, the command is the same as before.
- Seats started again by `tmuxc fork` or `tmuxc restore` do not use this option.

### Fork

| Engine | argv | Notes |
|---|---|---|
| claude | `--resume <ID> --fork-session` | through the headroom wrapper; keeps `[1m]` and effort |
| codex | `codex fork <ID>` | passes `-c model=` and `-c model_reasoning_effort=` |
| opencode | `--session <ID> --fork` | the model is passed in the session env `OPENCODE_CONFIG_CONTENT` |
| cmd | `--resume <ID> --fork-session` | `--model` and `--effort` |
| pi | `--fork <ID> --session-id <NEW>` | `--model` and `--thinking` |

- `--from <live session>`: reads the engine, model and conversation id from the running process and its transcript. It works within the same engine only, not across engines.
- `--source <ID> --agent <engine>`: gives the id directly. tmuxc checks on a best-effort basis that the engine store has that id.
- `omx` has no native fork, so it is not a target.

### Recommended workflow

```bash
# 1) open a session in a worktree that has a baton handoff
tmuxc open /path/to/project/.worktrees/my-task --name MY_TASK_ORCH --agent codex --role orchestrator --prompt "Read AGENTS.md, .baton/handoff/CURRENT.md and .baton/handoff/NEXT.md, then start"

# 2) record the task / session ref in cairn
cairn link t7 --session-ref MY_TASK_ORCH --execution-ref "tmuxc:MY_TASK_ORCH"

# 3) check progress with list / ask
tmuxc list
tmuxc ask MY_TASK_ORCH 80
```

### Companion tools

| Tool | Role |
| --- | --- |
| `baton` | worktree, handoff, archive, memory |
| `cairn` | milestone / task schedule ledger, session lineage |
| `tmuxc` | launcher and control for live tmux agent sessions |

## Requirements

- Required: `bash`, `git` and `tmux` (macOS: `brew install tmux` · Ubuntu: `sudo apt install tmux`)
- Optional: the CLI of each agent you want to open (`claude`, `codex`, `omx` and so on)
- Optional: `baton` and `cairn` (the companion tool set)
- tmuxc itself needs no account or API key. Each agent CLI asks for its own authentication.

## Links

- [INSTALL.md](INSTALL.md) — install guide for agents
- [AI Feature Pack catalog](../../README.md)
