<div align="center">

# AI Feature Pack

**Feature packs you install one at a time into your AI coding agent setup**
Claude Code · Codex · Pi · OpenCode · OpenClaw

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

[![Packs](https://img.shields.io/badge/packs-26-0b6e5f)](#-catalog)
[![Guide](https://img.shields.io/badge/guide-GitHub%20Pages-0b6e5f)](https://yoonhwan.github.io/aifp/)
[![Platform](https://img.shields.io/badge/platform-macOS-555)](#-notes)

</div>

---

## 📱 Work from your phone

Your agents keep running on your Mac. Your phone is just the window.

- **Tailscale** puts the phone and the Mac on one private network, and **Termius** (SSH) is the door in.
- **tmux** keeps every session alive after you disconnect. **`tmuxc`** opens sessions and **`tmm`** lets you pick one with your thumb.

**→ Official guide: [Work from your phone](https://yoonhwan.github.io/aifp/)**

## What is this?

- A collection of **feature packs** for AI coding agents. One pack = one folder under [`feature-pack/`](feature-pack/). Packs are independent — install only what you need.
- Every pack ships an `INSTALL.md` written **for the agent**: hand it to your agent and it checks prerequisites, installs the CLI, registers the skill and verifies the result.

## 🚀 Quick start

**Option A — the phone-remote pair (`tmuxc` + `tmm`)**

```bash
git clone https://github.com/yoonhwan/aifp.git && cd aifp \
  && bash feature-pack/tmuxc/install.sh \
  && bash feature-pack/tmm/install.sh
```

Requires macOS, bash 4+, git, tmux, and fzf (for `tmm`).

**Option B — let your agent install a pack**

```bash
git clone https://github.com/yoonhwan/aifp.git
# then tell your agent, for example:
#   "Read feature-pack/agent-browser/INSTALL.md and install it"
```

The agent reads `INSTALL.md` and then:

1. checks prerequisites
2. installs the CLI
3. sets up auth/config (asks you when needed)
4. registers the skill
5. adds the `TOOLS.md` / `AGENTS.md` sections
6. verifies the install

## 📦 Catalog

| # | Pack | What it does | Install | API key | Auth |
|---|------|--------------|---------|---------|------|
| 1 | [agent-browser](feature-pack/agent-browser/) | Web automation — scraping, screenshots, form filling, recording | ~3 min | — | — |
| 2 | [imsg](feature-pack/imsg/) | iMessage/SMS — read conversations, send messages, live watch | ~3 min | — | — |
| 3 | [notebooklm](feature-pack/notebooklm/) | Google NotebookLM — source-grounded Q&A, research, audio generation | ~5 min | — | Google |
| 4 | [obsidian-cli](feature-pack/obsidian-cli/) | Obsidian vault CLI — read, create, search and move notes | ~3 min | — | — |
| 5 | [tts-say](feature-pack/tts-say/) | Unified TTS — macOS `say` + ElevenLabs speech synthesis | ~3 min | ElevenLabs | — |
| 6 | [yt-transcribe](feature-pack/yt-transcribe/) | YouTube → speech-to-text → summary pipeline | ~10 min | — | — |
| 7 | [termaid](feature-pack/termaid/) | Mermaid diagrams rendered in the terminal — triggers automatically for design visuals | ~2 min | — | — |
| 8 | [baton](feature-pack/baton/) | Multi-agent handoff / worktree / archive standard — pass work between Claude Code, Codex and Gemini | ~2 min | — | — |
| 9 | [cairn](feature-pack/cairn/) | Schedule + multi-agent recovery ledger — milestone / task / session lineage, works with baton and tmuxc | ~2 min | — | — |
| 10 | [tmuxc](feature-pack/tmuxc/) | tmux session launcher and control for Claude Code, Codex and OMX — includes a verified send/capture messaging standard | ~1 min | — | — |
| 11 | [auto](feature-pack/auto/) | AutoResearch autonomous experiment loop — baseline → goal → self-driving optimization | ~1 min | — | — |
| 12 | [nanoclaw](feature-pack/nanoclaw/) | Multi-agent platform (an OpenClaw alternative) — Claude SDK brain, Docker isolation, multi-crew | ~15 min | — | Slack |
| 13 | [agent-cli](feature-pack/agent-cli/) | **AI coding agent CLI toolkit** — install and compare CLIs, plus non-interactive delegation with personas | ~3 min | — | — |
| 14 | [headroom](feature-pack/headroom/) | Context-compression proxy for AI coding agents such as Claude Code and Codex, with a `/headroom` toggle | ~5 min | — | — |
| 15 | [fable-team](feature-pack/fable-team/ft2/) | **Team orchestration harness (ft 2.0)** — shared core for seats, notes and work orders; contract definitions; Codex / Pi / Slack adapters; diagnostics. Folder responsibilities are in `ft2/README.md` | — | — | — |
| 16 | [tmm](feature-pack/tmm/) | **Mobile (SSH) tmux seat TUI** — pick among dozens of agent sessions with a cursor on your phone: preview, most-recent-first, waiting-seats-first, send messages (fzf) | ~1 min | — | — |
| 17 | [ctx-burn](feature-pack/ctx-burn/) | **Local context-waste auditor** — auto-detects 7 runtimes (claude, codex, pi, opencode, hermes, openclaw, commandcode) | ~1 min | — | — |
| 18 | [ctx-plan](feature-pack/ctx-plan/) | **Capacity planner** — reads only ctx-burn's `ctx.v1` output to size seats and peak sessions for your account mix | ~1 min | — | — |

**Also in the tree** (each folder has its own docs):
[agent-surface-audit](feature-pack/agent-surface-audit/) — dry-run inventory of agent skill and hook surfaces ·
[agent-surface-sync](feature-pack/agent-surface-sync/) — installs or updates shared agent surfaces from `feature-pack/*` and `hooks/` ·
[code-intel](feature-pack/code-intel/) — code intelligence behind a single `ci` entry point ·
[daily-trend-viewer](feature-pack/daily-trend-viewer/) — local site for daily popular videos and AI video news ·
[mcp-manager](feature-pack/mcp-manager/) — audit and trim MCP server surfaces ·
[memory-system](feature-pack/memory-system/) — memory structure for OpenClaw agents ·
[rag](feature-pack/rag/) and [rag-consumer](feature-pack/rag-consumer/) — the `airag` RAG package and its consumer (start at [`rag/docs/README.md`](feature-pack/rag/docs/README.md)).

## 📋 Recommended order

Packs do not depend on each other. By usefulness:

1. **obsidian-cli** — second-brain base (where other packs store notes)
2. **agent-browser** — web automation (the most general)
3. **yt-transcribe** — YouTube transcripts (pairs well with obsidian-cli)
4. **notebooklm** — knowledge Q&A (source-grounded answers)
5. **tts-say** — voice output
6. **imsg** — iMessage integration (macOS only)

For operating many agents at once:

1. **baton** — the reference point for worktree / handoff / archive
2. **cairn** — schedule and session-lineage ledger
3. **tmuxc** — run Claude Code / Codex / OMX in tmux sessions with verified-send messaging
4. **tmm** — pick and attach to those seats from your phone (Termius)

| Tool | Owns |
|------|------|
| baton | `.baton/handoff/` for starting, saving and recovering work, plus worktree / archive |
| cairn | `.cairn/plan.yaml`-based milestone / task / session lineage |
| tmuxc | live tmux agent sessions — create, capture, send, kill |
| tmm | seat list, preview, attach and messages over mobile SSH (a consumer of tmuxc seats) |

## 🔧 Other ways to install

**Manual** — read the pack's `README.md` and follow it in order:

```
feature-pack/{name}/
├── README.md        ← overview for humans (start here)
├── INSTALL.md       ← install prompt for the agent
├── cli/install.md   ← CLI install commands
├── skill/SKILL.md   ← skill definition
├── config/          ← sections to add to TOOLS.md / AGENTS.md
└── test/verify.md   ← install verification
```

Not every pack has every file; five packs (`ctx-plan`, `fable-team`, `headroom`, `rag`, `rag-consumer`) have no `INSTALL.md` — start from their README or docs.

**Everything** — tell your agent: "Install every feature pack in the aifp repo, in order." This takes about 25 minutes.

## 🔒 About this repository

- This is an **exported copy** of a private working repository. Internal operation notes were removed and personal or organization identifiers were replaced with placeholders, so some tests that need private data are skipped or will not run here.
- Every export runs a 58-pattern scan (keys, tokens, addresses, IDs) and stops unless nothing is left outside a reviewed allowlist. Key-shaped strings that remain are test fixtures or documentation placeholders.
- When you install a pack, do not write your own keys or tokens into files inside the repo folder.

## 📌 Notes

- **OS**: macOS only for now (Linux / Windows later).
- **OpenClaw**: [openclaw.ai](https://openclaw.ai) · [GitHub](https://github.com/openclaw/openclaw)
- **Questions**: open an issue or join the [Discord](https://discord.com/invite/clawd).

## License

[MIT](LICENSE)
