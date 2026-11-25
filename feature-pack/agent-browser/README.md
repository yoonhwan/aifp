<div align="center">

# agent-browser

**A browser automation CLI for AI agents — web scraping, screenshots, form filling, video recording, debugging and styled card generation.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Extracts the content of web pages, including dynamic SPA and React pages (scraping).
- Takes full-page and partial screenshots, and builds 2× retina card images.
- Fills in forms such as login and sign-up automatically, and saves and restores the login session (cookies).
- Records video as WebM and converts it to GIF.
- Shows console logs and errors, and mocks network responses.
- A Rust CDP daemon connects directly to Chrome, which also works when you need browser extensions.

## Quick start

```bash
npm install -g agent-browser
agent-browser install    # download Chromium (first time only, about 150MB)
agent-browser --native open "https://example.com" && agent-browser --native snapshot -i && agent-browser --native close
```

## Install

This pack installs three things: the agent-browser CLI (0.16.3 or newer), a skill that your agent uses automatically for browser tasks, and a TOOLS.md section with per-environment settings, a speed comparison and tips.

### Install with an agent

Ask your agent:

```text
Read feature-pack/agent-browser/INSTALL.md and install it
```

### Manual install

```bash
# run inside feature-pack/agent-browser/
npm install -g agent-browser
agent-browser install                  # download Chromium (first time only, about 150MB)
agent-browser --version                # must be 0.16.3 or newer
pip3 install Pillow                    # for screenshot cards
cp -r skill/ ~/.openclaw/workspace/skills/agent-browser/   # for Claude Code: ~/.claude/skills/agent-browser/
cat config/tools-section.md >> ~/.openclaw/workspace/TOOLS.md
```

- The skills folder (`~/.openclaw/workspace/skills`) and the workspace (`~/.openclaw/workspace`) are the OpenClaw defaults. Change them to your own paths if they differ.
- `config/tools-section.md` adds the following to TOOLS.md: usage rules for agent-browser (native first, not a search tool), a speed comparison table, video capture commands and the screenshot card pipeline.

### Verify

```bash
agent-browser --version
agent-browser --native open "https://example.com" && agent-browser --native get title && agent-browser --native screenshot /tmp/ab-verify.png && agent-browser --native close
agent-browser --native open "https://example.com" && agent-browser --native snapshot -i && agent-browser --native close
python3 -c "from PIL import Image; print('Pillow OK')"
```

If every check passes, the install is done.

### Troubleshooting

| Symptom | Fix |
|------|------|
| `agent-browser: command not found` | run `npm install -g agent-browser` again |
| `Chromium not found` | run `agent-browser install` |
| `--native` mode fails | fall back to standard mode without `--native` |
| Pillow import error | run `pip3 install Pillow` again |
| Screenshot is cut off | check that the HTML height is 620px or less; split the card if it is taller |

## Usage

### Choosing a mode

| Situation | Mode | Why |
|------|------|------|
| General browsing and scraping | `--native` | faster (about 150ms per page), no Node.js needed |
| Screenshots and captures | `--native` | lower latency |
| Chrome extensions needed | `--native connect <port>` | real Chrome only |
| Rendering problems on complex JS SPAs | standard (no flag) | Playwright stability |
| CI/CD pipeline | standard headless | proven reliability |

- Always try `--native` first and fall back to standard if there is a problem.
- It is not a web search tool. For search or for simply reading a URL, use a web search / fetch tool.

### Basic flow

```bash
SESSION="task-$(date +%s)"
trap "agent-browser close --session $SESSION 2>/dev/null" EXIT ERR

agent-browser --native --session "$SESSION" --headed open "https://example.com"
agent-browser --native --session "$SESSION" wait --load networkidle
agent-browser --native --session "$SESSION" snapshot -i          # lists elements as @refs
agent-browser --native --session "$SESSION" click @e3
agent-browser --native --session "$SESSION" fill @e5 "you@example.com"
agent-browser --native --session "$SESSION" get text ".result"
agent-browser --native --session "$SESSION" screenshot ./result.png
agent-browser --native --session "$SESSION" close
```

- Before any interaction, run `snapshot -i` to see the elements. `@ref` values change per session, so never reuse them in another session.
- Always use `--session <name>` and clean up with `trap`.
- Use `--headed` locally (you can watch it work); omit it in CI/CD (headless is the default).
- Order for finding an element: ① the `@ref` from `snapshot -i` ② a CSS selector ③ `find` commands (`find role button click`, `find text "Submit" click`, `find testid "btn" click`).

### Common tasks

```bash
# wait strategies
agent-browser --native --session "$SESSION" wait "#element"            # until an element appears
agent-browser --native --session "$SESSION" wait 2000                  # fixed delay (ms)
agent-browser --native --session "$SESSION" wait --text "Success"      # until text appears
agent-browser --native --session "$SESSION" wait --url "**/dashboard"  # until the URL matches
agent-browser --native --session "$SESSION" wait --load networkidle    # until all requests settle

# save / restore cookies
agent-browser --native --session "$SESSION" cookies get > cookies.json
agent-browser --native --session "$SESSION" cookies set "$(cat cookies.json)"

# network mocking
agent-browser --native --session "$SESSION" network route "**/analytics/*" --abort
agent-browser --native --session "$SESSION" network route "**/api/user" --body '{"id":1,"name":"Test"}'
agent-browser --native --session "$SESSION" network unroute

# record video, then convert to GIF
agent-browser --native --session "$SESSION" record start "./demo.webm"
agent-browser --native --session "$SESSION" record stop
ffmpeg -i demo.webm -vf "fps=10,scale=480:-1:flags=lanczos" -c:v gif demo.gif

# debug
agent-browser --native --session "$SESSION" console                    # view logs
agent-browser --native --session "$SESSION" errors                     # view errors
agent-browser --native --session "$SESSION" eval "document.title"      # run JS
```

- To get past a login popup, hide the DOM element with CSS instead of calling `remove()` (`remove()` destroys the content).

### Connect to a running Chrome

```bash
agent-browser --native connect 9222 --session "$SESSION"                                     # by port
agent-browser --native connect "ws://127.0.0.1:9222/devtools/browser/UUID" --session "$SESSION"  # by WebSocket URL
agent-browser --auto-connect --native snapshot                                                # find a running Chrome automatically
```

- Use `--native connect` when you need Chrome extensions, need macOS audio (BlackHole) loopback, or attach to a remote or debug Chrome.

### Screenshot cards

Builds mobile-friendly styled cards from HTML for sharing (Slack, Discord and so on).

```bash
agent-browser --native --session cap open "file:///tmp/card.html"   # HTML 375px wide and 620px tall or less
agent-browser --native --session cap screenshot "/tmp/raw.png"
agent-browser --native --session cap close
```

- The agent-browser viewport is fixed at 1280×720px, so content taller than about 620px is cut off. Split long content into several cards (one card = one topic).
- The card width is 375px and the final output is 2× retina (830px wide). Crop the screenshot above with Pillow and scale it up 2× (the full script is in [skill/SKILL.md](skill/SKILL.md)).
- Font sizes: short content title 15px · body 12px · code 11px · padding 20px / medium 14 · 11 · 10 · 16px / long table (20+ rows) 13 · 10.5 · 9.5 · 14px.
- The theme is dark (background `#1a1a2e`, card `#16213e`, table header `#0f3460`, border `#1a4080`). Always check that the last line (footer) is visible.

### Error recovery

| Error | Fix |
|------|------|
| `No session found` | run `open` first |
| `Element not found` | run `snapshot -i` again and check the refs |
| `Timeout` | raise `--timeout` and check the `wait` condition |
| Zombie session | `agent-browser session list`, then `close --session <name>` |
| `--native` fails | drop the `--native` flag and use standard mode |

For the full command list, see `agent-browser --help` and `agent-browser <command> --help`.

## Requirements

- macOS (arm64 / x86_64)
- Node.js 18 or newer, and npm
- Python 3 + Pillow (for screenshot cards)
- ffmpeg (only to convert WebM to GIF)
- No account or API key is needed.

## Links

- [INSTALL.md](INSTALL.md) — install guide for agents
- [skill/SKILL.md](skill/SKILL.md) — the skill definition
- [AI Feature Pack catalog](../../README.md)
