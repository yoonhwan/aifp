<div align="center">

# fable-team

**Source of fable-team ft 2.0 — the seat · note · work-order core, contracts, Slack · Codex · Pi adapters and the goal-close flow, split as one folder = one responsibility.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- `ft2/` holds the new skeleton of ft 2.0. Active 2.0 source is written only inside this folder.
- The shared core for seats, notes and work orders does not know about runtime differences. Adapters (Slack · Codex · Pi) handle what differs per runtime.
- Contract definitions for cards, contracts and test maps, plus the model tables, are in `ft2/contracts/`.
- `goal-close/` is a module with one flow and six rules for splitting a large goal into condition cells and closing them one by one.
- `legacy_guard.py` checks that `ft2/` never runs, imports or sources 1.x tools.

## Quick start

```bash
# from the repo root — self-check of ft2/ (0 = no violations)
python3 feature-pack/fable-team/ft2/tools/legacy_guard.py
```

## Install

This pack folder has no `INSTALL.md`. The public copy contains the ft 2.0 source and the `goal-close/` module, and no install steps are written for them here. The 1.x harness is not included in the public copy. Clone the repo, read the files in place, and run the checker in place as in "Quick start" above.

## Usage

### Folder responsibilities

One folder = one responsibility.

| Folder | Responsibility |
|---|---|
| `ft2/core/` | Shared 2.0 core for seats, notes and work orders. Does not know about runtime differences |
| `ft2/contracts/` | 2.0 contract definitions for cards, contracts and test maps |
| `ft2/contracts/models/` | Home of the three model tables (model-scope · model-fallback · provider-of-model) — read by `tools/models.py` |
| `ft2/adapters/slack/` | Slack receive · publish adapter |
| `ft2/adapters/codex/` | Codex runtime adapter |
| `ft2/adapters/pi/` | Pi runtime adapter · opens seats (`launch.py`) |
| `ft2/doctor/` | Install and environment diagnostics |
| `ft2/tools/` | Checkers and helper tools |
| `ft2/tests/` | ft2 tests |

### legacy_guard

No file in `ft2/` may run, import or source a 1.x path or tool. Checked patterns: 5 kinds of 1.x paths and tool locations (list in [ft2/README.md](ft2/README.md)). Checked extensions: `.py` `.sh` `.ts` `.js` `.json`. `*.md` is prose and allowed. Comments in code files are checked too.

```bash
python3 feature-pack/fable-team/ft2/tools/legacy_guard.py          # self-check of ft2/
python3 feature-pack/fable-team/ft2/tools/legacy_guard.py <dir>    # check another tree
```

| Exit code | Meaning |
|---|---|
| `0` | No violations |
| `1` | Violations found (one `<file>:<line>: <pattern>` line each) |
| `2` | Usage or path error |

Limit: it is a string check, so it cannot catch paths built at run time. Those are left to review.

### goal-close

A large goal is split into N condition cells, and one seat carries one cell from planning to closing: plan → implement (tests Red → Green · PR) → DA review → verify on the installed copy → monitor the next day → close.

| File | Contents |
|---|---|
| `00-flow.md` | One flow and six rules |
| `10-cell.md` | Goal-file cells and cell rules |
| `20-situations.md` · `30-direct.md` | Handling by situation · the path that skips the team lead |
| `40-conduct.md` | Guidelines and traits to remove |
| `roles/` | Text per role (`arch` · `da` · `master` · `nano`) |
| `phrases.tsv` · `MODULE.json` | Phrase table · module version (`gc-1.3`) and sha256 per file |

## Requirements

- Python 3 (`legacy_guard.py` · standard library only)
- API keys / accounts: none (for `legacy_guard.py`)
- What the adapters need to run is not written in the docs of this folder.

## Links

- [ft2/README.md](ft2/README.md) — ft 2.0 folder responsibilities and the no-1.x rule
- [goal-close/00-flow.md](goal-close/00-flow.md) — goal-close flow
- [AI Feature Pack catalog](../../README.md)
