<div align="center">

# headroom

**A local proxy that compresses your AI coding agent's context before it reaches the LLM — one `ANTHROPIC_BASE_URL` line, zero code changes.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Puts the open-source `headroom-ai` proxy between your agent and the LLM API. The client only changes `ANTHROPIC_BASE_URL` (or `OPENAI_BASE_URL`).
- Classifies content (JSON · code (AST) · prose) and compresses each kind its own way. The original stays local; the model gets the compressed copy plus a `headroom_retrieve` path to restore it.
- Keeps compressed output deterministic so the prefix cache key survives (`cache_bust_count: 0` in `token` mode).
- The `claude-hr.sh` wrapper turns two layers on and off per project: headroom (:8790, compression) and cliproxy (:8317, multi-account rotation). If a layer you asked for is down, it stops instead of silently going direct.
- Ships a Claude Code toggle skill `/headroom on|off|status` and ops patches for `headroom-ai==0.33.x` (`patches/apply.sh`).
- The gain only builds up in long sessions and work that re-reads the same files. Short one-off inputs see no benefit.

## Quick start

```bash
# from the repo root
python3.12 -m venv ~/.headroom-venv
~/.headroom-venv/bin/pip install "headroom-ai==0.33.0"
bash feature-pack/headroom/patches/apply.sh

# start the proxy (compression + cache together, telemetry off)
HEADROOM_MODE=token HEADROOM_COMPRESS_USER_MESSAGES=1 HEADROOM_CODE_AWARE_ENABLED=1 HEADROOM_TELEMETRY=off \
  ~/.headroom-venv/bin/python -m headroom.proxy.server \
  --port 8790 --compress-user-messages --exclude-tools Bash --code-aware

# in another shell: check, then route one session through the proxy (do not export it globally)
curl -s localhost:8790/health
ANTHROPIC_BASE_URL=http://localhost:8790 claude
```

## Install

This pack has no `INSTALL.md`. To let your agent do it, say "Read `feature-pack/headroom/README.md` and install headroom and the toggle skill". The agent steps in this README ask you which projects to enable first and never turn it on automatically. To do it by hand, run the three steps below from the repo root.

### 1. Install headroom-ai

ML extras (`headroom-ai[ml]` · `[all]`, Kompress) are left out of the default install because of cache stability and memory cost.

```bash
python3.12 -m venv ~/.headroom-venv
~/.headroom-venv/bin/pip install "headroom-ai==0.33.0"
~/.headroom-venv/bin/headroom --version       # 0.33.0
```

### 2. Apply the ops patches

`apply.sh` picks patches by installed version (0009 for 0.33.x, 0006 for other compatible versions) and is safe to run again. The default Python is `~/.headroom-venv/bin/python`; pass another one as the first argument.

```bash
bash feature-pack/headroom/patches/apply.sh   # [/path/to/venv/bin/python]
```

### 3. Install the toggle skill and the wrapper

```bash
HR_DIR="$PWD/feature-pack/headroom"
mkdir -p ~/.claude/skills/headroom ~/.headroom
cp "$HR_DIR/SKILL.md" ~/.claude/skills/headroom/SKILL.md
cp "$HR_DIR/templates/claude-hr.sh" ~/.headroom/claude-hr.sh
mkdir -p ~/.claude/skills/headroom-cliproxyapi/scripts
cp "$HR_DIR/scripts/file-logs.sh" ~/.claude/skills/headroom-cliproxyapi/scripts/file-logs.sh
cp "$HR_DIR/scripts/clean-proxy-logs.sh" ~/.claude/skills/headroom-cliproxyapi/scripts/clean-proxy-logs.sh
cp "$HR_DIR/scripts/file-logs.sh" ~/.headroom/headroom-cliproxy-file-logs.sh
cp "$HR_DIR/scripts/clean-proxy-logs.sh" ~/.headroom/clean-proxy-logs.sh
# routing state file — both layers off (direct) by default
[ -f ~/.headroom/routing.json ] || cp "$HR_DIR/templates/routing.json" ~/.headroom/routing.json
chmod +x ~/.headroom/claude-hr.sh ~/.headroom/headroom-cliproxy-file-logs.sh ~/.headroom/clean-proxy-logs.sh ~/.claude/skills/headroom-cliproxyapi/scripts/*.sh
```

Then add `alias claude-hr='~/.headroom/claude-hr.sh'` to `~/.zshrc` and start with `claude-hr`.

## Usage

### Routing switcher (`claude-hr.sh`)

| headroom | cliproxy | `ANTHROPIC_BASE_URL` |
|---|---|---|
| on | on | `http://localhost:8790` — compress → rotate → subscription |
| off | on | `http://127.0.0.1:8317` — rotate → subscription, no compression |
| off | off | unset — direct to Anthropic |
| on | off | not allowed — the headroom LaunchAgent upstream is pinned to `127.0.0.1:8317`, so the wrapper refuses with exit 78 |

```bash
HR=~/.headroom/claude-hr.sh
$HR route status                    # effective value for this project + real process state
$HR route headroom on|off           # this project only
$HR route cliproxy on|off
$HR route headroom on --global      # default for all projects
$HR route reset [--global]
```

The only state file is `~/.headroom/routing.json`. Do not edit it by hand; change it with `route`.

```json
{
  "default":  { "headroom": false, "cliproxy": false },
  "projects": { "/abs/project/root": { "headroom": true, "cliproxy": true } }
}
```

- A project entry wins; otherwise `default` applies. No file means direct.
- The project root comes from `git --git-common-dir`, so a worktree folds into its main project.
- One-off override: the `HEADROOM_ROUTE=0|1` · `CLIPROXY_ROUTE=0|1` environment variables win over the file.
- If a layer you asked for is down, it stops with exit 69 (no silent fallback).
- If `--model` is not in the cliproxy catalog, it warns on stderr before launch (it does not block).
- Inside Claude Code the skill maps `/headroom on` → `route headroom on` · `/headroom off` → `route headroom off` · `/headroom status` → `route status`.
- Environment variables are fixed when a process starts. Sessions already running must be restarted. To cover sessions that tmux or an orchestrator starts, point your usual claude alias at the wrapper (for example `alias cc='~/.headroom/claude-hr.sh --model "..."'`).

### Starting the proxy

```bash
HEADROOM_MODE=token HEADROOM_COMPRESS_USER_MESSAGES=1 HEADROOM_CODE_AWARE_ENABLED=1 HEADROOM_TELEMETRY=off \
  ~/.headroom-venv/bin/python -m headroom.proxy.server \
  --port 8790 --compress-user-messages --exclude-tools Bash --code-aware
```

- `headroom proxy` (click) has few options. Run `python -m headroom.proxy.server` directly for full control. In that case use `HEADROOM_TELEMETRY=off` instead of `--no-telemetry`.
- Modes: `cache` = freeze the prefix, observe only (~0% compression) · `token` = aggressive compression alongside the cache (25-30% on re-reads).
- If 8790 is already LISTENing, reuse it; do not start another one. Several sessions each starting their own proxy cause an `Errno48 Address already in use` crash loop. The skill's `on` enforces this.

### Other agents

`headroom wrap <agent>` starts the proxy and launches the agent in one step.

```bash
headroom wrap claude        # Claude Code (ANTHROPIC_BASE_URL)
headroom wrap codex         # Codex
headroom wrap cursor        # Cursor — prints config, paste once
headroom wrap aider         # Aider
headroom wrap copilot       # GitHub Copilot CLI
headroom proxy --port 8790  # any other OpenAI-compatible client: OPENAI_BASE_URL=http://localhost:8790/v1
```

When you use Codex with cliproxy, pin it with a Codex custom provider instead of `headroom wrap codex`. Then `codex`, `codex exec` and tmux all take the same path. cliproxy OAuth does the auth, so `CODEX_DUMMY_API_KEY` can be a dummy value.

```toml
# ~/.codex/config.toml
model_provider = "headroom"

[model_providers.headroom]
name = "Headroom"
base_url = "http://127.0.0.1:8790/v1"
env_key = "CODEX_DUMMY_API_KEY"
wire_api = "responses"
```

Other install channels are `npm install headroom-ai` and `docker pull ghcr.io/chopratejas/headroom:latest`; for a resident service use `headroom install apply --preset persistent-service --providers auto`.

### Checking it works (`/stats`)

```bash
curl -s localhost:8790/health        # status healthy
curl -s localhost:8790/stats         # compression + cache_bust_count (should be 0)
```

| Metric | Meaning |
|---|---|
| `avg_compression_pct` | How much compression kicked in |
| `cache_bust_count` | Must stay 0. Above 0 means the cache broke = a loss |
| `cache_write_1h_tokens` | Whether the 1h extended cache is used |

When `api_req` in `/stats` grows from 0, traffic is really going through the proxy.

### Privacy

- Prompts, code and credentials do not leave your machine (they go only to the intended upstream).
- Anonymous usage telemetry is on by default (aggregate stats only, every 5 minutes). Turn it off with `HEADROOM_TELEMETRY=off` (already in the start command above).
- `learn` and `memory` are off by default. Keep them off.
- Supply chain: a bundled RTK binary, and models are downloaded from huggingface.co at startup.

### Known limits

| Path | Compression |
|---|---|
| Library call (`compress_user_messages=True`) | 83.7% |
| Live proxy — single read | 0% |
| Live proxy — re-read / supersede | 25-30% (best 30.7%) |

- The 0% on single reads is by design. `DEFAULT_EXCLUDE_TOOLS = {Read,Bash,Grep,Glob,Edit,Write}` and `protect_recent` (default 4) protect standard tool results and recent messages.
- Reversible compression is lossy inside the context. In debugging work, check separately that `headroom_retrieve` restores correctly.
- Numbers can differ by environment and version (v0.33.0).

### Troubleshooting

- `400 messages.N: user messages must have non-empty content` — compression returned an empty string. The empty-output guard in `patches/apply.sh` prevents it. As a stopgap, drop `--compress-user-messages` from the start command.
- 500 on large requests · `compression_first_stage` RuntimeError — a panic from tree-sitter parsers shared across threads. `patches/apply.sh` fixes it. A log line `pyo3_runtime.PanicException: _native::Parser is unsendable` means this case.
- Every session shows `API Error: Connection refused` — the proxy (8790) is down. Restart it from a shell that does not go through the proxy, then resend the same input in the stuck sessions.

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.headroom.proxy.plist 2>/dev/null
launchctl enable    gui/$(id -u)/com.headroom.proxy
launchctl kickstart -k gui/$(id -u)/com.headroom.proxy
curl -sf -m1 http://localhost:8790/health
```

- Prevention: do not export `ANTHROPIC_BASE_URL` globally in your shell. If the proxy dies, every session stops at once. Start sessions through the wrapper.

## Requirements

- Python 3.12 (`python3.12 -m venv`) · `headroom-ai==0.33.0`
- zsh (`claude-hr.sh`) · bash · python3 · curl
- The resident service and recovery commands assume a macOS LaunchAgent (`launchctl`).
- cliproxy (:8317) is not included in this pack. Run it separately to use the headroom + cliproxy path.
- API keys / accounts: uses your agent's existing auth as is.

## Links

- [SKILL.md](SKILL.md) — the `/headroom` toggle skill
- [patches/README.md](patches/README.md) — ops patches by version and their causes
- [SSOT.md](SSOT.md) — notes on context cost
- [NOTES.md](NOTES.md) — patch notes
- [AI Feature Pack catalog](../../README.md)
