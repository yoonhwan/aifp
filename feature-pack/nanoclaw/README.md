<div align="center">

# nanoclaw

**A multi-agent platform built on the Claude Agent SDK. Each agent runs in an isolated Docker container and talks to you through Slack.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Runs conversational AI agents in your Slack channels. It is a replacement for OpenClaw.
- Runs coding agents (Bash, Read, Write, Edit and more) inside Docker containers, so a crash stays contained.
- Splits personas with `groups/`: one `CLAUDE.md` plus a `memory/` folder per group.
- Persists sessions in SQLite and `memory/` files, with a Redis mirror.
- Extends through skills (about 31 built in, plus your own) on a Configure-Don't-Code basis.
- Supports multiple instances: one NanoClaw per crew member.

## Quick start

```bash
git clone https://github.com/qwibitai/nanoclaw.git
cd nanoclaw
npm install
npm run build

# Build the agent image
cd container && docker build -t nanoclaw-agent:latest . && cd ..

# First run, then type /setup in the chat to install OneCLI and register the agent
node dist/index.js
```

## Install

Ask your agent: "Read feature-pack/nanoclaw/INSTALL.md and install it". The agent will ask you for the install path and the agent name. To install by hand, follow [INSTALL.md](INSTALL.md) (about 15 minutes):

1. Start Docker (Colima is recommended) sized for the number of agents you plan to run.
2. Clone, install and build NanoClaw (upstream: `qwibitai/nanoclaw`).
3. Run `node dist/index.js` once and use `/setup` to set up OneCLI, the proxy that injects your Claude API access into the containers (it listens on `localhost:10254`).
4. Create a Slack app (Socket Mode on) and put its two tokens in `.env`.
5. Create a group with its persona and memory files.
6. Build the `nanoclaw-agent` image and start NanoClaw.
7. Optional: migrate skills and scheduled tasks from OpenClaw. The two can run side by side with different bot tokens.
8. Optional: start NanoClaw at login with a launchd plist (see Step 8 in [INSTALL.md](INSTALL.md)).

```bash
# Docker via Colima (see the sizing table below)
brew install colima docker
colima start --cpu 2 --memory 4 --disk 30
docker info

# Slack tokens
cat > .env << 'EOF'
SLACK_BOT_TOKEN=<your-bot-token>
SLACK_APP_TOKEN=<your-app-token>
ASSISTANT_NAME=NanoClaw
EOF

# A persona group
mkdir -p groups/main/memory
cp groups/global/CLAUDE.md groups/main/CLAUDE.md
touch groups/main/memory/{directives,mistakes,achievements}.md
```

## Usage

### Key concepts

- **Group**: the persona unit of an agent, defined in `groups/{name}/CLAUDE.md`.
- **Container**: a Docker container is spawned for each task, does the work, then exits.
- **Skill**: a `SKILL.md` file under `.claude/skills/`.
- **Memory**: mistakes, achievements and directives persist in `groups/{name}/memory/`.
- **OneCLI**: a proxy for the Claude API key, injected into containers automatically.

### OpenClaw vs NanoClaw

| Item | OpenClaw | NanoClaw |
|------|----------|----------|
| Brain | Built-in LLM routing | Claude Agent SDK (covered by a Claude subscription, no API cost) |
| Runtime | Host process | Docker container (isolated) |
| Extension | Skills + plugins | `groups/` + `skills/` (Configure-Don't-Code) |
| Multi-agent | Single instance | 1 NanoClaw = 1 crew member (multiple instances) |
| Persistence | Internal DB | SQLite + `memory/` files + Redis mirror |
| Communication | HTTP API + Slack | Native Slack + Redis Stream |

### Colima sizing

| Setting | 1 agent | 3 to 5 agents | 10+ agents |
|---------|---------|---------------|------------|
| CPU cores | 2 | 4 | 6 |
| RAM (GB) | 4 | 8 | 12 |
| Disk (GB) | 30 | 60 | 100 |

### Managing NanoClaw

```bash
# List groups
ls groups/

# Create a group (then write groups/{name}/CLAUDE.md)
mkdir -p groups/{name}/memory

# Check running containers and OneCLI
docker ps --filter "name=nanoclaw"
docker ps --filter "name=onecli"

# Check the launchd service
launchctl list | grep nanoclaw

# Count stored messages
sqlite3 store/messages.db "SELECT COUNT(*) FROM messages;"

# List built-in skills, and add a custom one (then write its SKILL.md)
ls .claude/skills/
mkdir -p groups/{name}/skills/{skill-name}
```

## Requirements

- macOS (Apple Silicon M1 or newer recommended)
- Node.js 20+ and npm
- Docker Desktop or Colima
- Git
- A Claude Pro or Max subscription
- A Slack workspace where you can create an app
- Install time (~15 min)

## Links

- [INSTALL.md](INSTALL.md) — installation guide
- [qwibitai/nanoclaw](https://github.com/qwibitai/nanoclaw) — upstream project
- [AI Feature Pack catalog](../../README.md)
