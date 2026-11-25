<div align="center">

# memory-system

**Sets up a three-layer memory for an OpenClaw agent — workspace memory files, an Obsidian vault as a second brain, and memory search across the whole vault (NotebookLM optional).**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- The agent keeps conversations, decisions and lessons in long-term memory `MEMORY.md` and daily notes `memory/YYYY-MM-DD.md`.
- Creates a folder structure in your Obsidian vault (Daily · News-Links · Meetings · People · Projects · Reference · Ideas · Archive and more) with `HOME.md` and index notes.
- Adds the whole vault to the agent's memory search (`extraPaths` · OpenAI embeddings · file watch).
- Mirrors daily notes and `MEMORY.md` into the vault's `Daily/` (symlink or periodic copy).
- Turns news links into notes and builds people profiles from conversation records.
- Optional: adds vault documents to NotebookLM as sources with the `nlm` CLI for source-based Q&A.

## Quick start

```bash
# 1) Tell your OpenClaw agent: "Read feature-pack/memory-system/INSTALL.md and install it"
# 2) After install, check
ls ~/.openclaw/workspace/MEMORY.md
obsidian-cli print-default
```

## Install

To let your agent do it, say "Read `feature-pack/memory-system/INSTALL.md` and install it". `INSTALL.md` is a prompt that an OpenClaw agent reads to install everything by itself. When it finds a `{{PLACEHOLDER}}`, the agent asks you and fills it in.

| Placeholder | Meaning | Default |
|---|---|---|
| `{{OC_WORKSPACE}}` | OpenClaw workspace path | `~/.openclaw/workspace` |
| `{{VAULT_PATH}}` | Absolute path of the Obsidian vault | — |
| `{{VAULT_NAME}}` | Obsidian vault name (folder name) | — |

Install order: ① workspace memory files ② vault folder structure + obsidian-cli ③ memory search integration ④ Obsidian entry in `TOOLS.md` ⑤ daily memory mirror ⑥ NotebookLM (optional) ⑦ install check. The key commands for manual steps are below.

```bash
brew install yakitrak/yakitrak/obsidian-cli
obsidian-cli set-default "my-vault"
# after editing openclaw.json, apply the settings
openclaw gateway restart
```

## Usage

### Three layers

| Layer | What | Where |
|---|---|---|
| 1 · Workspace memory | Long-term memory (curated) + daily notes (raw log) | `MEMORY.md` · `memory/*.md` |
| 2 · Obsidian vault | Daily mirror · link notes · conversation records · people profiles | `Daily/memory/` · `News-Links/` · `Meetings/` · `People/` |
| 3 · NotebookLM (optional) | Source-based Q&A | `nlm` CLI |

### Session rules

- At the start of a session, list files with `exec("ls memory/")` and read today's and yesterday's daily notes. In the main session, also read `MEMORY.md`.
- Never read the folder as a whole like `read("memory")` (EISDIR error). Read files one by one.
- Do not write personal information or API keys in daily notes. Do not load `MEMORY.md` in group chats.
- Move the important parts of daily notes into `MEMORY.md` from time to time.

### Memory search settings

These settings go into `openclaw.json`. `OPENAI_API_KEY` must be set in the OpenClaw environment or settings.

```json
{
  "agents": {
    "defaults": {
      "memorySearch": {
        "enabled": true,
        "sources": ["memory", "sessions"],
        "extraPaths": ["{{VAULT_PATH}}"],
        "provider": "openai",
        "model": "text-embedding-3-small",
        "sync": { "watch": true, "watchDebounceMs": 1500 },
        "query": {
          "hybrid": { "enabled": true, "vectorWeight": 0.7, "textWeight": 0.3, "candidateMultiplier": 4 }
        }
      }
    }
  }
}
```

### NotebookLM

An optional step that needs the `notebooklm` pack. Skip it if you do not have it.

```bash
nlm notebook create "my-vault Knowledge Base"
nlm source add <notebook-id> --file "<vault-path>/HOME.md"
nlm chat query <notebook-id> "What is the most important decision in this project?"
```

### Troubleshooting

- Vault files do not show up in memory search: check the absolute vault path in `extraPaths`, `watch: true` and the OpenAI API key, then run `openclaw gateway restart`. Indexing a large vault can take minutes to tens of minutes.
- obsidian-cli cannot find the vault: run `obsidian-cli set-default` again and make sure you have opened that vault in the Obsidian app at least once.
- Symlinks may not sync in an iCloud vault. In that case mirror with a periodic copy (rsync).
- NotebookLM sign-in fails: see the sign-in step of the `notebooklm` pack (Chrome required).

## Requirements

- macOS (Apple Silicon or Intel)
- OpenClaw installed and running
- Obsidian app · obsidian-cli (Homebrew)
- API keys / accounts: OpenAI API key (embeddings `text-embedding-3-small`) · optional: `nlm` CLI and a Google account (NotebookLM)
- Install time: about 15 minutes

## Links

- [INSTALL.md](INSTALL.md)
- [skill/SKILL.md](skill/SKILL.md) — agent skill
- [obsidian/setup.md](obsidian/setup.md)
- [test/verify.md](test/verify.md)
- [notebooklm pack](../notebooklm/)
- [AI Feature Pack catalog](../../README.md)
