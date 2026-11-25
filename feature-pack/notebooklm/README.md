<div align="center">

# notebooklm

**The `nlm` CLI and an OpenClaw skill package for controlling Google NotebookLM from the terminal.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Source-based Q&A: answers come only from the documents you uploaded.
- Generates audio podcasts and video overviews from your documents.
- Generates study material such as reports, quizzes and flashcards.
- Deep research collects and analyzes web sources automatically.
- Manages notebooks: create, delete, share and alias them.
- Uses documents from an Obsidian vault as NotebookLM sources.

## Quick start

```bash
# 1. Install
uv tool install notebooklm-mcp-cli

# 2. Authenticate (Chrome opens)
nlm login

# 3. Use
nlm notebook list
nlm query notebook <notebook_id> "your question"
```

## Install

Ask your agent: "Read feature-pack/notebooklm/INSTALL.md and install it". To install by hand, follow [INSTALL.md](INSTALL.md):

1. Install the `nlm` CLI with `uv` (`notebooklm-mcp-cli`).
2. Sign in to your Google account with `nlm login` and check with `nlm auth status`. A session lasts about 20 minutes; run `nlm login` again when it expires.
3. Copy this pack's `skill/` folder into the skills folder of your OpenClaw workspace.
4. Add a NotebookLM section to the workspace `TOOLS.md` (the content is in [INSTALL.md](INSTALL.md)).
5. Optional: set up the Obsidian integration.
6. Check that it works with `nlm --version`, `nlm auth status` and `nlm notebook list`.

```bash
# Install uv if you do not have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the CLI and check it
uv tool install notebooklm-mcp-cli
nlm --version

# If nlm is not found, add ~/.local/bin to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc

# Copy the skill (default OpenClaw workspace: ~/.openclaw/workspace)
cp -r skill/ ~/.openclaw/workspace/skills/notebooklm

# Update
uv tool upgrade notebooklm-mcp-cli
```

## Usage

### Main commands

```bash
# Notebooks
nlm notebook list
nlm notebook create "Name"
nlm notebook get <notebook_id>
nlm notebook describe <notebook_id>

# Sources
nlm source add <notebook_id> --file <path>
nlm source add <notebook_id> --url <url>
nlm source add <notebook_id> --text "content" --title "Title"

# Q&A
nlm query notebook <notebook_id> "your question"

# Generate
nlm audio create <notebook_id> --confirm
nlm video create <notebook_id> --confirm
nlm report create <notebook_id> --confirm
nlm quiz create <notebook_id> --confirm
nlm flashcards create <notebook_id> --confirm
nlm mindmap create <notebook_id> --confirm
nlm slides create <notebook_id> --confirm

# Research
nlm research start <notebook_id> "topic" --mode deep
nlm research status <notebook_id>

# Download
nlm download audio <notebook_id> <artifact_id> -o <path>

# Aliases (short names instead of UUIDs)
nlm alias set myproject <notebook_id>
nlm alias list
```

### Q&A from an agent

- An agent always asks with `nlm query notebook`, one question and one answer at a time.
- Do not use `nlm chat start` (REPL mode); an agent cannot control it.
- Run `nlm --ai` for a guide to all commands.

### Obsidian integration

This works by uploading files through the CLI, not through a plugin.

```bash
# Create a dedicated notebook and give it an alias
nlm notebook create "My Obsidian Vault"
nlm alias set vault <notebook_id>

# Upload a document as a source
nlm source add vault --file "<path-to-vault>/note.md" --wait

# Ask a question
nlm query notebook vault "Explain the project structure"
```

### Troubleshooting

| Symptom | Fix |
|---------|-----|
| `nlm: command not found` | Add `~/.local/bin` to PATH |
| `uv: command not found` | Install uv |
| "Cookies have expired" / "authentication may have expired" | Run `nlm login` again |
| Chrome does not open | Install Chrome (`brew install --cask google-chrome`) |
| Rate limit error | It retries 3 times automatically. If it keeps failing, wait a while |
| Adding a source fails | Check that the file is within the NotebookLM source size limit |

## Requirements

- macOS (Apple Silicon or Intel)
- Python 3.10+
- A Google account (with NotebookLM access)
- Chrome browser (used for authentication)
- uv (the install step installs it if missing)

## Links

- [INSTALL.md](INSTALL.md) — installation guide
- [Obsidian integration guide](obsidian/setup.md)
- [AI Feature Pack catalog](../../README.md)
