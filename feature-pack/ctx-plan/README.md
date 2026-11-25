<div align="center">

# ctx-plan

**A capacity tool that turns an account mix into seats · peak sessions · goal throughput, and works back to how many subscriptions a target scale needs**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Where the sibling tool `ctx-burn` measures "what was used", `ctx-plan` simulates "what you can carry". The two connect **only through one JSON contract (`ctx.v1`)**.
- `--capacity`: from an account mix (`--accounts 5x:N,ultra:N`) prints the pool table · 4 simulation rows · 2 goal-model rows.
- `--inventory`: checks the 19 priority-0 fixed constants (subscription counts · weekly limits and more) and prints "N priority-0 problems" · the required-accounts estimate · baseline A.
- `--need K:N`: works back from a target scale (concurrent sessions · sessions · teams · concurrent goals) to the Ultra / 5x subscriptions needed.
- `--scales`: recomputes with a list of waste-reduction multipliers.
- Reads no session logs and not your real HOME. Input is the `ctx-burn --json` output and one constants file only · no writes · no network.

## Quick start

```bash
git clone https://github.com/yoonhwan/aifp.git
cd aifp/feature-pack/ctx-plan
bash install.sh                                 # ~/.local/bin/ctx-plan

cp accounts.env.example /tmp/accounts.env       # constants file — fill the values per machine
ctx-burn --hours 168 --json > /tmp/burn.json    # needs the ctx-burn pack

CTX_PLAN_CAP_FILE=/tmp/accounts.env ctx-plan --from /tmp/burn.json --inventory   # priority-0 constants check
ctx-plan --from /tmp/burn.json --inv-file /tmp/accounts.env --capacity --accounts 5x:5,ultra:5
ctx-plan --from /tmp/burn.json --inv-file /tmp/accounts.env --need concurrent:40
```

## Install

### Let your agent install it

This pack has no `INSTALL.md`. Tell your agent "Read feature-pack/ctx-plan/README.md and install it" and it can follow the manual steps below. A person fills in the constants file values.

### Manual install

`install.sh` creates one symlink, `~/.local/bin/ctx-plan`. It does not pick a place for the constants file — the caller passes it with `--inv-file` or `CTX_PLAN_CAP_FILE`.

```bash
bash install.sh                                 # ~/.local/bin/ctx-plan
CTX_PLAN_BIN_DIR="$HOME/bin" bash install.sh    # change the install folder
cp accounts.env.example /path/to/accounts.env   # sample — values are empty; unfilled values stop with a "priority-0 problem"
bash uninstall.sh                               # remove — deletes the symlink only
```

## Usage

### Modes

| mode | prints |
|---|---|
| (none) | 3 header lines — contract · axis definition · constants file path + one pool line |
| `--inventory` | 19 priority-0 constants checked · "N priority-0 problems" · 2 goal-model rows (concurrent goals · goals/week · idle/short teams) · required-accounts estimate · baseline A |
| `--capacity` | pool table (only pools that exist) · 4 simulation rows · 2 goal-model rows |
| `--need K:N` | `concurrent:N` · `sessions:N` · `teams:N` · `goals:N` (N concurrent goals) → Ultra / 5x subscriptions needed · `goals` also prints the required-accounts block · if N exceeds `FT_GOAL_PARALLEL_MAX` it is not cut, one notice line is printed (rc 0) |
| `--scales 1.0,0.9,…` | waste-reduction multipliers (default 4 values = measured · -10% · -20% · -30%) |

### Options

| option | default | meaning |
|---|---|---|
| `--from FILE\|-` | stdin | `ctx-burn --json` output |
| `--inv-file FILE` | (order below) | fixed constants file |
| `--accounts 5x:N,ultra:N` | none | account mix for the `--capacity` seat · peak calculation |
| `--wk-5x N` / `--wk-ultra N` | 630 / 2520 | weekly limit anchors (weighted M) — a value in the file wins |
| `--c5h-5x N` | 60 | 5x 5-hour window anchor |
| `--target-util F` | 0.85 | weekly target utilization (operating policy) |
| `--seats-per-team N` | 4 | sessions per team |
| `--hours-per-week N` | 40 | hours per week of one session |
| `--teams-per-goal N` | 3 | teams working one goal at the same time |
| `--team-hours-per-goal N` | 8 | hours one team stays on one goal |

### Constants file

There are only two places it looks: ① `--inv-file FILE` ② `$CTX_PLAN_CAP_FILE`. It does not search parent folders or assume a path in your home. With no file it prints no table and ends with rc 3 + one line that points to `--inv-file` · `CTX_PLAN_CAP_FILE` · `install.sh`.

- The output header prints the path it read. 19 keys = subscriptions 5 · weekly limits 4 (upper · lower) · model 5 (including the concurrent-goal reference) · baseline 5.
- An empty value is a "priority-0 problem" and is **not replaced by a default** — tables that need it print "cannot compute".
- Only two knobs that are not contract keys (`FT_CAP_C5H_5X` · `FT_CAP_HOURS_PER_WEEK`) use defaults, and the screen says "default (not a contract key)".
- Sample = [`accounts.env.example`](accounts.env.example) (values are empty).

### Goal model (reference)

- One goal = 3 teams at once × 8 hours = 24 team-hours = 96 session-hours · up to 3 concurrent goals · goals/week = min(available session-hours ÷ 96, 3 × 168 ÷ 8).
- The numbers come from constants (`FT_GOAL_PARALLEL_MAX` · `FT_GOAL_TEAMS` · `FT_GOAL_TEAM_HOURS` · `FT_CAP_SEATS_PER_TEAM`).
- It is a calculation example, not an operating rule, and the output carries a "reference — not an operating rule" label. Going over a value is never refused or cut; it only prints a notice.
- Baseline A (`FT_BASE_*`, 5 keys) counts always-on teams as 1 seat per team × 168h, and issue · goal teams as daytime hours × 7 days × sessions per team. `team-hours/week` is an intermediate unit and is not used to judge results.

### Rules it keeps

- **One place for lower bounds** — `FT_CAP_WK_5X_LOW` · `FT_CAP_WK_ULTRA_LOW`. No stand-in math such as "upper ÷ 3"; empty means "cannot compute".
- **Labels are "low-capacity assumption · high-capacity assumption"** — never "optimistic · conservative" (a small capacity is not guaranteed to be the conservative one).
- **Anchors carry a status** (unverified · estimate · needs measuring · operating policy and so on). Do not make account decisions on a number while its status mark is still there.
- **Contract check** — if `plan_input.schema` is not `ctx.v1`, it does not compute and stops with rc 2 + one reason line.
- **Model constants resolved in one place** — order is `CLI flag > constants file`; a contract key with neither is "cannot compute". The source (`CLI` · `file` · `none` · `default (not a contract key)`) is printed in the header.
- **0 samples = not computed** — never filled with 0. rc stays 0.

### Input contract (ctx.v1)

`plan_input` from `ctx-burn --json`:

```json
{"schema": "ctx.v1", "window_hours": 168,
 "units": {"rate_claude": "weighted_tokens_per_session_hour",
           "w_per_session_hour": "weighted_tokens_per_session_hour",
           "w_total": "weighted_tokens", "ctx_per_req": "tokens"},
 "pools": {"claude": {"req": 0, "usage0": 0, "ctx_per_req": 0.0, "active_hours": 0,
                      "cache_reuse": 0.0, "cache_reuse_of_input": 0.0,
                      "w_per_session_hour": null, "samples": 0, "sessions": 0, "w_total": 0}},
 "rate_claude": null}
```

- `rate_claude` = the **median weighted tokens per session-hour** of the claude pool (sample = sessions with 20+ requests). There is exactly one line that converts it to the compute budget (M = million weighted tokens). The `units` field lets the contract state its own units.
- `usage0` = weight-0 records (API errors), left out of the request-rate denominator. The `unknown` pool = unknown model and is never merged into another pool.

### Safety

- Reads: one `--from` JSON · one constants file. Nothing else.
- No writes · no network · no direct session log reads · does not run `ctx-burn` (no subprocess).
- The constants file is **read only** (no `--set`). A person fills in the values.

## Requirements

- python3 3.8+ · standard library only
- macOS · Linux
- Input: `ctx-burn --json` output (the [ctx-burn](../ctx-burn/README.md) pack)
- A filled constants file (copied from `accounts.env.example`) · no API key · no network

## Links

- [accounts.env.example](accounts.env.example) — constants file sample (values are empty)
- [docs/plan-cost-table.md](docs/plan-cost-table.md) — Claude Opus 5.5 subscription plans vs API cost (per day) table, in Korean
- [ctx-burn](../ctx-burn/README.md) — the sibling tool that emits `ctx.v1` (measures usage)
- [AI Feature Pack catalog](../../README.md)
