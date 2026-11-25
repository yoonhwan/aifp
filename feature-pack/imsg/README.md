<div align="center">

# imsg

**A CLI and OpenClaw skill that drives macOS Messages.app from the terminal — and doubles as an iMessage notification channel for agents · scripts · cron**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- **Chat list** — see recent iMessage / SMS conversations.
- **Message history** — read past messages of one conversation, with date filters and attachment info.
- **Send messages** — send text and attachments (images · documents and more).
- **Live watch** — stream new messages as they arrive.
- **Agent notification channel** — send an iMessage alert from other agents · coding tools · cron · CI with one `imsg send` line.
- The CLI is the third-party Homebrew package `steipete/tap/imsg`; this pack holds its install guide · an OpenClaw skill · a `TOOLS.md` section.

## Quick start

```bash
brew install steipete/tap/imsg
imsg --help                                        # success if the command list prints
imsg chats --limit 3 --json                        # chat list (checks Full Disk Access)
imsg send --to "<your-phone>" --text "imsg install test"   # send to yourself (checks Automation)
```

## Install

### Let your agent install it

Tell your agent "Read feature-pack/imsg/INSTALL.md and install it". `INSTALL.md` is written for an OpenClaw agent to read and install on its own; the agent asks you for the 3 placeholders (`{{OPENCLAW_WORKSPACE}}` · `{{USER_PHONE}}` · `{{NOTIFY_PHONE}}`) and fills them in.

### Manual install

1. Install the CLI with `brew install steipete/tap/imsg`.
2. Give your terminal app (Terminal.app · iTerm2 and so on) **Full Disk Access**: System Settings → Privacy & Security → Full Disk Access. It is needed to read `chat.db`.
3. The first `imsg send` shows an "allow Terminal to control Messages" prompt → allow it (the **Automation** permission).
4. If you use OpenClaw, copy the skill and add the section from [`config/tools-section.md`](config/tools-section.md) to the `TOOLS.md` of your workspace.

```bash
SKILL_DIR="$HOME/.openclaw/workspace/skills/imsg"   # default OpenClaw workspace path
cp -r skill/ "$SKILL_DIR"
ls "$SKILL_DIR/SKILL.md"                            # check the skill
```

## Usage

### Commands

| command | does | main options |
|---|---|---|
| `imsg chats` | chat list | `--limit N` · `--json` · `--db <path>` (default `~/Library/Messages/chat.db`) |
| `imsg history` | messages of one chat | `--chat-id <ID>` · `--limit N` · `--start` / `--end <ISO8601>` · `--participants` · `--attachments` · `--json` |
| `imsg send` | send a message | `--to <phone/email>` or `--chat-id` · `--text` · `--file <path>` · `--service imessage\|sms\|auto` · `--region` |
| `imsg watch` | live watch | `--chat-id` · `--participants` · `--since-rowid` · `--debounce 250ms` · `--attachments` · `--json` |
| `imsg rpc` | JSON-RPC mode over stdin / stdout | for MCP servers and similar integrations |

### Examples

```bash
imsg chats --limit 10 --json                                   # find the chat-id
imsg history --chat-id 1 --start 2026-03-01T00:00:00Z --attachments --json
imsg send --to "<your-phone>" --text "Here is the report" --file ~/reports/daily.pdf
imsg send --chat-id 42 --text "Replying here"
imsg watch --chat-id 1 --attachments --debounce 250ms
```

### Notification channel

Any CLI tool · script · agent can send an alert with one `imsg send` line. If you use it often, register a shell function.

```bash
# success / failure alert when a task ends
long_running_task && imsg send --to "<your-phone>" --text "Task done" \
                  || imsg send --to "<your-phone>" --text "Task failed"

# add to ~/.zshrc — usage: notify "build done"
notify() {
  imsg send --to "<your-phone>" --text "$*"
}
```

### Troubleshooting

| symptom | cause | fix |
|---|---|---|
| `imsg: command not found` | not installed with brew | `brew install steipete/tap/imsg` |
| `permission denied` (chats) | no Full Disk Access | System Settings → Privacy → Full Disk Access → add your terminal |
| send fails | Automation not allowed | System Settings → Automation → Terminal → check Messages |
| "Messages is not running" | Messages.app is not running | start Messages.app and retry |
| recipient has no iMessage | needs SMS | add `--service sms` |
| chat-id unknown | conversation ID not looked up | find it with `imsg chats --json` |

## Requirements

- macOS (Apple Silicon or Intel) + Messages.app signed in with an iCloud account
- Homebrew
- Full Disk Access for your terminal app · Automation permission for Messages
- Optional: OpenClaw, to use the skill
- No API key

## Links

- [INSTALL.md](INSTALL.md) — install guide for agents (steps · verification checklist · placeholders)
- [skill/SKILL.md](skill/SKILL.md) — OpenClaw skill (when to use · command reference)
- [config/tools-section.md](config/tools-section.md) — the section to add to `TOOLS.md`
- [AI Feature Pack catalog](../../README.md)
