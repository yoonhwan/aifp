<div align="center">

# auto

**An autonomous experiment loop where the agent only edits code, `uv run` runs the experiment, and stdout JSON decides keep or discard.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Provides the Karpathy AutoResearch pattern as an agent skill, `/auto`.
- The agent's job is four steps: edit code → run the experiment → read the JSON → judge.
- `prepare.py` handles infrastructure checks and setup; `run_experiment.py` runs the experiment and prints the metric.
- You declare the goal (metric, editable scope, constraints) in `program.md`, and the agent iterates inside that scope.
- Results accumulate in `results.tsv`, and a report can be generated when the run ends.

## Quick start

```bash
# 1. Install the skill
mkdir -p ~/.claude/skills/auto/references
cp skill/SKILL.md ~/.claude/skills/auto/SKILL.md
cp skill/references/*.md ~/.claude/skills/auto/references/

# 2. Copy the templates into your project and create the uv environment
mkdir -p your-project/autoresearch
cp config/templates/* your-project/autoresearch/
cd your-project/autoresearch && uv sync

# 3. Edit program.md, prepare.py and run_experiment.py for your project
# 4. Run /auto in your agent session
```

## Install

Ask your agent: "Read feature-pack/auto/INSTALL.md and install it". To install by hand, follow [INSTALL.md](INSTALL.md):

1. Copy the skill files to `~/.claude/skills/auto/`.
2. Create an `autoresearch/` folder in your project root, copy the four templates (`pyproject.toml`, `prepare.py`, `run_experiment.py`, `program.md`) into it, and run `uv sync`.
3. Write your goal in `program.md`, and adapt `check_runtime()` and `check_data()` in `prepare.py` plus `RUN_CMD`, `parse_result()` and `TIMEOUT` in `run_experiment.py`.
4. Add a `.gitignore` so experiment artifacts stay out of git, then check that the skill loaded.

```bash
# Add to autoresearch/.gitignore
cat >> autoresearch/.gitignore << 'EOF'
.venv/
run.log
results.tsv
upstream/
__pycache__/
EOF

# Check that the skill loaded (expected: version: "3.0.0")
grep "version" ~/.claude/skills/auto/SKILL.md
```

## Usage

### Commands

Run these in an agent session.

| Command | Description |
|---------|-------------|
| `/auto` | Start the full flow (setup → baseline → goal → autonomous run) |
| `/auto setup` | Initialize `autoresearch/` only |
| `/auto 2h` | Run autonomously for 2 hours |
| `/auto 30m` | Run autonomously for 30 minutes |
| `/auto overnight` | Run autonomously for 8 hours |
| `/auto resume` | Continue on the existing branch |
| `/auto report` | Generate a report from `results.tsv` |
| `/auto update` | `git pull` the `upstream/` clone |

### Three layers

```
Layer 1: uv run prepare.py         (once)  infra check + setup
Layer 2: agent autonomous loop             edit code → run → JSON → judge
Layer 3: uv run run_experiment.py  (each run)  run tests → print metric
```

### stdout JSON contract

`run_experiment.py` prints exactly one JSON line as the last line of stdout. All other output (progress, warnings) goes to stderr or `run.log`.

```json
{
  "score": 0.004,
  "passed": 13,
  "total": 14,
  "failed": ["case-14"],
  "grade_summary": "13S 1A",
  "flush_e2e_ms": null,
  "status": "ok",
  "duration_s": 187.3
}
```

- `status` is one of `"ok"`, `"crash"` or `"error"`; a `reason` may be added for crash/error. `flush_e2e_ms` is optional (a secondary metric).
- Exit 0 = finished normally: the agent judges keep or discard from `score`.
- Exit 1 = crash or infrastructure failure: the agent reverts or fixes and retries (at most 2 times).

### Domain examples

| Domain | primary_metric | RUN_CMD | prepare.py |
|--------|---------------|---------|------------|
| ML training | val_bpb | `uv run train.py` | GPU + dataset check |
| STT quality | avg_cer | `python3 e2e_test.py --baseline --json` | server + browser + audio |
| API latency | p99_ms | `pytest tests/perf.py --json` | server + DB |
| Code quality | coverage | `pytest --cov --json` | dependency check |

### Tips

- Writing a good `program.md` is the key. Metric, scope and constraints set the agent's boundaries.
- `prepare.py` only needs to run once and is idempotent, so run it again if in doubt.
- Keep the time budget per experiment under 5 minutes so you can run many experiments.
- Work on a dedicated branch, change one thing at a time, and edit only 1 to 2 files per area.
- The agent does not edit the infrastructure files inside `autoresearch/`. It edits project source only.

## Requirements

- macOS or Linux
- Python 3.11+
- git
- [uv](https://docs.astral.sh/uv/)
- Claude Code or a compatible agent CLI
- No API key needed · install time (~2 min)

## Links

- [INSTALL.md](INSTALL.md) — installation guide
- [stdout JSON contract in detail](skill/references/run-experiment-contract.md)
- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) — the original pattern
- [AI Feature Pack catalog](../../README.md)
