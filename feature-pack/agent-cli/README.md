<div align="center">

# agent-cli

**An install-and-compare guide for AI coding agent CLIs, plus a delegation harness that hands work to another model non-interactively.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Guides you through installing, authenticating and comparing six agent CLIs: Claude Code, Codex, Gemini, OpenCode, Cursor Agent and Pi.
- From your current session, calls another model non-interactively, lets it run autonomously, and continues the same session with `resume`.
- Injects a persona (DA, designer or architect) so the delegated model gets a role right away.
- Has a different model check, adversarially, what one model produced (author and review stay separate).
- Sends the same task to several providers so you can cross-check the results.
- Can link to higher-level harnesses such as oh-my-\*, baton and tmuxc (optional). They are ignored when not installed; non-interactive delegation, personas and resume work without them.

## Quick start

```bash
# from the repository root: check your OS and which CLIs you can use now
bash feature-pack/agent-cli/scripts/detect-env.sh
# after installing the skill (see Install): ask codex to review with the DA persona, then follow up
bash ~/.claude/skills/agent-cli/scripts/resume_chain.sh codex DA "Review this diff adversarially" "Rank the findings by priority"
```

## Install

### Install with an agent

Ask your agent:

```text
Read feature-pack/agent-cli/INSTALL.md and install it
```

### Manual install

```bash
mkdir -p ~/.claude/skills/agent-cli/references ~/.claude/skills/agent-cli/scripts
cp SKILL.md            ~/.claude/skills/agent-cli/SKILL.md
cp references/*.md     ~/.claude/skills/agent-cli/references/
cp scripts/*.sh        ~/.claude/skills/agent-cli/scripts/
chmod +x ~/.claude/skills/agent-cli/scripts/*.sh
```

- Run the commands above inside `feature-pack/agent-cli/`. For OpenClaw or another agent, only change the skill path to match its convention. `SKILL.md` is self-contained.
- Run `bash scripts/detect-env.sh` first. It tells macOS, Linux and WSL apart and prints the CLIs you can use now, install hints for the missing ones, and WSL notes.
- If your agent has a TOOLS.md (or an equivalent catalog), add the contents of `config/tools-section.md` to it.
- The default OpenCode model is `opencode/deepseek-v4-flash-free`. To use another one, run `export OPENCODE_MODEL=<provider/model>` (list them with `opencode models`).
- For Pi, change the default model with `export PI_MODEL=<provider/model>`. Check authentication first with `pi auth check --provider <provider> --json`. Use `--skill` to inject skills and `--tools` to restrict tools.

### Verify

```bash
bash ~/.claude/skills/agent-cli/scripts/selftest.sh   # run in an isolated or trusted folder
```

Also go through the checklist in `test/verify.md`.

## Usage

### Supported CLIs

| CLI | Non-interactive | Autonomous | Resume |
|-----|--------|---------|--------|
| Claude Code | `claude -p` | `--dangerously-skip-permissions` | `--resume <sid>` |
| Codex | `codex exec` | `--full-auto` ⎮ `--yolo` | `codex exec resume --last` |
| Gemini | `gemini -p` | `--approval-mode yolo` | `--resume <session_id>` |
| OpenCode | `opencode run` | no approval by default | `-s <sid>` / `-c` |
| Cursor Agent | `cursor-agent -p` | `-f` / `--force` | `--resume <chatId>` |
| Pi | `pi -p` | `--tools <allowlist>` (no approval prompt) | `--session-id <sid>` / `--session <sid>` |

- Aider and Amp are covered only as notes (`references/install-and-compare.md`).
- During a session the skill triggers on requests such as "have codex adversarially review this PR", "cross-check this design with Gemini" or "resume the earlier session and ask a follow-up".

### Delegate and resume

```bash
bash ~/.claude/skills/agent-cli/scripts/resume_chain.sh codex DA "Review this diff adversarially" "Rank the findings by priority"

# To pin the Claude model and effort
CLAUDE_MODEL=<model-id> CLAUDE_EFFORT=high \
bash ~/.claude/skills/agent-cli/scripts/resume_chain.sh claude DA \
  "Review this change adversarially" \
  "Just tell me the final approval decision again"
```

- When `resume_chain.sh` calls Claude, it passes the `CLAUDE_MODEL` and `CLAUDE_EFFORT` environment variables through unchanged.

### Scripts

| Script | What it does |
|---|---|
| `scripts/detect-env.sh` | tells the OS apart, lists usable CLIs, install hints, WSL notes |
| `scripts/selftest.sh` | checks non-interactive, autonomous and resume for all six CLIs in one run (with timeouts and logs) |
| `scripts/test_opencode.sh` | checks OpenCode alone (finds the model automatically) |
| `scripts/resume_chain.sh` | a chain of a persona plus several resume turns |
| `scripts/cloud-dataset-batch.sh` | generates training and labeling data in bulk with cloud session credits, then retrieves it |

### Cloud credits batch

Claude cloud session credits (credits granted separately from a subscription) are charged only in cloud sessions. Calls from a local CLI or through a proxy are not charged. `scripts/cloud-dataset-batch.sh` starts a cloud session in an empty folder with no repository and no code, retrieves it (teleport) when it finishes, extracts only the JSONL printed in the answer, and accumulates it as a dataset.

```bash
bash scripts/cloud-dataset-batch.sh --task lexicon --lang ko,ja,th --count 300 --batch 25 --parallel 3 --budget 20
bash scripts/cloud-dataset-batch.sh --task label   --lang ko --labels work,tech,legal,daily,billing,other --count 200
bash scripts/cloud-dataset-batch.sh --task doc     --lang ko --count 4 --batch 4 --parallel 1 --budget 1   # small trial run
```

| task | Data it produces |
|---|---|
| `lexicon` | linguistic dictionary entries (lemma, pos, IPA, gloss, example, register) |
| `parallel` | parallel corpus (src / tgt, domain) |
| `label` | classification labels (text, label, rationale); `--labels` fixes the label set |
| `qa` | language-learning Q/A (level, topic) |
| `doc` | long-document sections (520 characters per line); for burning through credits in bulk |
| `free` | free format |

- Output: `<out>/data.jsonl` (duplicates removed across batches, `id` reassigned) · `<out>/run-*/index.tsv` (ledger of sessions and counts) · `ledger.json` (credit change)
- Measured: about 25 records per session, about $0.03 per record, scaling with parallelism 2 to 4.
- Note: cloud credits have an expiry date, so use them before it, and set a spending cap with `--budget`. Large repeated generation can be judged as account abuse, so generate data you will actually use.

### Safety

- Autonomous flags (dangerous / full-auto / yolo / force) remove the human approval gate. Use them only in an isolated or trusted workspace.
- Each delegated CLI needs its own authentication. This pack does not inject credentials.
- Treat delegated results as untrusted input and review them in your own session before use.

## Requirements

- Supported: macOS, Linux and WSL
- `perl` and `python3` — built into macOS. On WSL or Ubuntu without them: `sudo apt install -y perl python3`
- At least one of the six agent CLIs on your PATH, with its own authentication done. A CLI that is not installed is skipped automatically.
- WSL: OAuth opens in the Windows browser (you can copy and paste the URL by hand). cursor-agent may be missing (skipped automatically). Work inside `~/`.
- Cloud credits batch only: `~/.headroom/claude-credit.sh` (ccx / ccxt), `claude` 2.1.310 or newer, and tmux

## Links

- [INSTALL.md](INSTALL.md) — install guide for agents
- [SKILL.md](SKILL.md) — the skill definition
- [references/per-cli.md](references/per-cli.md) — per-CLI details for non-interactive, autonomous and resume
- [references/install-and-compare.md](references/install-and-compare.md) — install, authentication and comparison
- [references/personas.md](references/personas.md) — the DA, designer and architect personas
- [AI Feature Pack catalog](../../README.md)
