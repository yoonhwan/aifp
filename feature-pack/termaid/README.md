<div align="center">

# termaid

**A CLI, `termaid-render`, and an agent skill that draw Mermaid diagrams right in your terminal**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Parses Mermaid syntax and prints a styled diagram in the terminal (colors, borders and bold via lipgloss).
- Flowcharts (`graph LR/TD`) — node shapes (box · diamond · round · cylinder), subgraphs, edge labels.
- Sequence diagrams — participants, sync and async arrows, `loop` · `alt/else` blocks.
- Basic support for class, state and ER diagrams.
- Input from a stdin pipe (`echo '...' | termaid-render`) or a file (`termaid-render diagram.mmd`).
- With the skill installed, your agent draws diagrams on its own during design talks and architecture explanations.

## Quick start

```bash
# get the source · patch the build · build · put it on PATH
git clone https://github.com/MKlolbullen/termaid.git ~/scripts/termaid
cd ~/scripts/termaid
mv internal/tui/builder.go internal/tui/builder.go.wip 2>/dev/null || true
sed -i '' 's/return NewBuilder(catalogueNames()), nil/return errView(fmt.Errorf("workflow builder not yet available")), nil/' internal/tui/menu.go 2>/dev/null || true
go build -o termaid-render ./cmd/render/
cp termaid-render /opt/homebrew/bin/termaid-render

# first diagram
echo 'graph LR
  A[Client] --> B{Auth?}
  B -->|yes| C[Service]
  B -->|no| D[401]' | termaid-render
```

## Install

### Let your agent do it

Tell your agent: "Read `feature-pack/termaid/INSTALL.md` and install it." The agent checks Go → clones the source → patches the build → builds → installs to PATH → installs the skill → verifies. Install time (~2 min).

### Manual install

1. Clone the source (run `git pull` if it is already there).
2. Patch the build (required). Upstream `internal/tui/builder.go` does not compile, so move it aside and remove the `NewBuilder` reference from `internal/tui/menu.go` — the `mv` and `sed` lines in "Quick start".
3. Build with `go build -o termaid-render ./cmd/render/` and copy the binary to your PATH.
4. Copy the skill into the Claude Code skills path and verify.

```bash
# install the skill (from the pack folder)
mkdir -p ~/.claude/skills/termaid/
cp skill/SKILL.md ~/.claude/skills/termaid/

# verify
which termaid-render && echo "OK" || echo "FAIL"
termaid-render --help

# rebuild after changing the source
cd ~/scripts/termaid && go build -o termaid-render ./cmd/render/ && cp termaid-render /opt/homebrew/bin/
```

Paths that `INSTALL.md` asks for, with defaults:

| Placeholder | Meaning | Default |
|---|---|---|
| `{{TERMAID_SOURCE_PATH}}` | where the source lives | `~/scripts/termaid` |
| `{{TERMAID_INSTALL_PATH}}` | where the binary goes | `/opt/homebrew/bin/termaid-render` |
| `{{CLAUDE_SKILLS_PATH}}` | Claude skills path | `~/.claude/skills` |

## Usage

```bash
# flowchart (stdin pipe — the most common use)
echo 'graph LR
  A[Client] --> B{Auth?}
  B -->|yes| C[Service]
  B -->|no| D[401]' | termaid-render

# sequence diagram
echo 'sequenceDiagram
  C ->> S : POST /login
  S -->> C : 200 OK' | termaid-render

# from a file
termaid-render workflow.mmd

# help
termaid-render --help
```

### Supported diagrams

| Type | Keyword | Supported |
|---|---|---|
| Flowchart | `graph TD/LR`, `flowchart` | O |
| Sequence | `sequenceDiagram` | O |
| Class | `classDiagram` | O |
| State | `stateDiagram-v2` | O |
| ER | `erDiagram` | O |
| Gantt | `gantt` | X (code block only) |

- Nodes: `[box]` · `(round)` · `{diamond}` · `[(cylinder)]` · `((circle))`
- Arrows (sequence): `->>` sync · `-->>` async · `-x` failure

### When the agent uses it

- Design talks (architecture, API design, DB schema), explaining system structure or code flow, and requests like "show me as a picture".
- Keywords: "diagram" · "chart" · "sequence" · "flow" · "architecture" · "mermaid" · "termaid", plus their Korean equivalents.
- Not used for simple code fixes, short questions, or when a code block is enough.
- Diagrams stay short — split them when they pass 20 lines or reach 10 nodes.

### Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `termaid-render: command not found` | not on PATH | `cp termaid-render /opt/homebrew/bin/` |
| `go: command not found` | Go not installed | `brew install go` |
| `builder.go compile error` | unfinished upstream code | check the build patch |
| `yaml unmarshal error` | TUI `init()` panic | build only `cmd/render/` (skips the TUI) |

## Requirements

- macOS
- Go 1.22+ (`go version` · if missing, `brew install go`)
- API keys / accounts: none

## Links

- [INSTALL.md](INSTALL.md) — install guide for the agent
- [skill/SKILL.md](skill/SKILL.md) — agent skill
- [cli/install.md](cli/install.md) — install the CLI only
- [termaid upstream source](https://github.com/MKlolbullen/termaid)
- [AI Feature Pack catalog](../../README.md)
