<div align="center">

# obsidian-cli

**Lets your agent list, search, create, edit, delete and move notes in an Obsidian vault (Markdown notes) from the CLI**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- View: list files and folders in the vault and read note content.
- Search: fuzzy search by note name and search note content.
- Create: make notes (missing folders are created too) and open the daily note.
- Edit: overwrite, append, and view / edit / delete frontmatter keys.
- Delete and move: delete notes; moving or renaming a note updates wikilinks automatically.
- Your agent can also edit `.md` files directly with `read` / `write` / `edit` tools. Obsidian picks up the changes.

## Quick start

```bash
brew install yakitrak/yakitrak/obsidian-cli
obsidian-cli set-default "my-vault"
obsidian-cli create "Projects/my-note" --content "# My note"
obsidian-cli print "Projects/my-note"
```

## Install

### Let your agent do it

Tell your agent: "Read `feature-pack/obsidian-cli/INSTALL.md` and install it." Install time is about 3 minutes. The agent will ask for your vault name.

### Manual install

```bash
# 1. install the CLI — v0.2.3 or later
brew install yakitrak/yakitrak/obsidian-cli
obsidian-cli --version

# 2. set the default vault — Obsidian keeps its vault list in this file
cat ~/Library/Application\ Support/obsidian/obsidian.json
obsidian-cli set-default "my-vault"
obsidian-cli print-default

# 3. skill — skip the copy if the official OpenClaw obsidian skill is present
ls /opt/homebrew/lib/node_modules/openclaw/skills/obsidian/SKILL.md
mkdir -p ~/.openclaw/workspace/skills/obsidian/
cp skill/SKILL.md ~/.openclaw/workspace/skills/obsidian/SKILL.md
```

4. Using `config/tools-section.md`, add an Obsidian CLI section (binary path, default vault, main commands) to `TOOLS.md` in your OpenClaw workspace.
5. Optional: in the Obsidian app, turn on Daily notes (Core plugin). Recommended Community plugins are Dataview, Templater and Calendar (`obsidian/setup.md`).
6. Run the CRUD test in `test/verify.md`. If every step exits with code 0, the install is done.

## Usage

### Commands

| Command | What it does |
|---|---|
| `obsidian-cli set-default "<vault>"` · `print-default [--path-only]` | set · show the default vault |
| `obsidian-cli list ["<folder>"]` | list the vault root or a folder |
| `obsidian-cli print "<note>"` | read a note |
| `obsidian-cli search "<query>"` · `search-content "<query>"` | fuzzy name search · content search (interactive) |
| `obsidian-cli create "<note>" --content "<text>" [--open]` | create a note (folders created automatically) |
| `obsidian-cli create "<note>" --content "<text>" --overwrite` · `--append` | overwrite · append |
| `obsidian-cli daily` | create · open the daily note |
| `obsidian-cli frontmatter "<note>" --print` | show frontmatter |
| `obsidian-cli frontmatter "<note>" --edit --key <k> --value <v>` · `--delete --key <k>` | edit frontmatter · delete a key |
| `obsidian-cli move "<old>" "<new>"` | move · rename + update wikilinks |
| `obsidian-cli delete "<note>"` | delete |
| `obsidian-cli open "<note>"` | open in the Obsidian app |

### Tips

- `search` and `search-content` are interactive and do not work in an agent environment. Use `grep -r` or `list` + `print`.
- Always use `move`, not `mv`, to move notes. `mv` breaks wikilinks.
- Do not hard-code the vault path; get it with `print-default --path-only`.
- Leave the `.obsidian/` folder alone (settings and plugin conflicts).
- For bulk edits, editing the files directly is faster than the CLI.

### Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `brew: command not found` | Homebrew missing | install Homebrew |
| `Cannot find note in vault` | no default vault · wrong note path | check `set-default`, drop `.md` from the path |
| `search-content` does not work | non-interactive environment | `grep -r` or `list` + `print` |
| a new note does not show in Obsidian | iCloud sync delay | wait a few seconds, then refresh in the app |
| URI handler error | the Obsidian app is not running | start the app and try again |

## Requirements

- OS: macOS
- Homebrew
- Obsidian app (URI handler) · at least one vault
- API keys / accounts: none

## Links

- [INSTALL.md](INSTALL.md) — install guide for agents
- [skill/SKILL.md](skill/SKILL.md) — OpenClaw skill
- [config/tools-section.md](config/tools-section.md) — section to add to `TOOLS.md`
- [obsidian/setup.md](obsidian/setup.md) — Obsidian app setup
- [test/verify.md](test/verify.md) — CRUD test to verify the install
- [AI Feature Pack catalog](../../README.md)
