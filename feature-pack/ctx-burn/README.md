<div align="center">

# ctx-burn

**A read-only audit tool that shows, with numbers and graphs from your own logs, how much context your local AI coding agents burn**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Agents re-send **the whole conversation + auto-loaded memory + tool definitions** on every turn. `ctx-burn` measures that cost from local session logs (weighted: cache read `0.1x` · cache rewrite `2x` · output `5x`).
- Detects installed and running runtimes by itself: `claude` · `codex` · `pi` · `opencode` down to token usage; `hermes` · `openclaw` · `commandcode` for auto-loaded file size and live process count only.
- Graphs the cache full-rewrite share · average context per request · auto-loaded files over 4KB · the distillation break-even turn count · the start budget (fresh distill vs resume).
- `--request` dissects one captured request body to show tool definition sizes.
- Installs the sibling commands `ctx-time` (where the wall clock went) · `ctx-window` (where the conversation window went) · `ctx-share` (coordination share and weekly usage board).
- `--json` emits the `ctx.v1` contract block read by the sibling tool `ctx-plan`. No setting or file writes · no network · no API key.

## Quick start

```bash
git clone https://github.com/yoonhwan/aifp.git
cd aifp/feature-pack/ctx-burn
bash install.sh            # symlink into ~/.local/bin (ctx-burn + ctx-waste alias)

cd ~/my-project
ctx-burn                   # last 3 hours, current folder
ctx-burn --lang ko         # Korean output (English by default)
```

## Install

### Let your agent install it

Tell your agent "Read feature-pack/ctx-burn/INSTALL.md and install it", or paste the block below into Claude Code · Codex · Pi · OpenCode or any coding agent; it installs, runs and explains the result itself. The tool is read-only, so running it is safe.

```text
Install and run ctx-burn on this project, then explain the output.
https://github.com/yoonhwan/aifp/tree/main/feature-pack/ctx-burn

1. Clone the repo and run feature-pack/ctx-burn/install.sh (creates ~/.local/bin/ctx-burn).
2. Run `ctx-burn --hours 6` in this project root. Use `--lang ko` if I speak Korean.
3. From the output, report only these: cache full-rewrite share, average context per request,
   and the top 3 auto-loaded files over 4KB.
4. If full rewrite is above 20%, find the cause from local logs (resume size, sessions starting
   together, account switching) and show the evidence line.
5. If auto-loaded files are over 4KB, propose moving them out of the auto-load path with a 1KB digest.
6. Ask me before changing any setting. The tool itself is read-only, so running it is safe.
```

### Manual install

`install.sh` only creates symlinks in `~/.local/bin`: `ctx-burn` · `ctx-waste` (a permanent alias of `ctx-burn`) · `ctx-share` · `ctx-time` · `ctx-window`. If you get `command not found`, `~/.local/bin` is not on your PATH.

```bash
CTX_BURN_BIN_DIR="$HOME/bin" bash install.sh   # change the install folder (the old name CTX_WASTE_BIN_DIR is read too)
export PATH="$HOME/.local/bin:$PATH"           # add to your shell rc if missing
bash uninstall.sh                              # remove — deletes symlinks only
```

`uninstall.sh` removes the `ctx-burn` · `ctx-waste` · `ctx-time` · `ctx-window` symlinks. Session logs and settings are not touched.

## Usage

### Reading the output

| section | shows | what to look for |
|---|---|---|
| `[0]` runtime environment | per runtime: installed · running · sessions · last seen · data kind | detected automatically, no config |
| `[1]` auto-loaded memory | files paid for on every request, with token counts | `!` = a file over 4KB. Move big rule files to an open-when-needed place and keep a 1KB digest |
| `[2]` burn structure | weighted share of cache full rewrite · cache read and the rest | full rewrite above 20% is the primary suspect. One rewrite costs as much as 20 normal requests |
| `[3]` context per request | average · max tokens | an average over 200k means the conversation grew to the end of the window and distillation is not kicking in |
| break-even for distillation | restart cost · saving per turn · break-even turn count | if turns per session exceed the break-even, distill more often |
| start budget | room left and rewrite cost for a fresh start vs a resume, from gate · fixed prefix · handover size | "how much of the gate is left for conversation at session start" is a bigger lever than window size. Tune with `--gate` · `--resume-caps` (comma separated) |

### ctx-burn options

| option | default | meaning |
|---|---|---|
| `--lang en\|ko` | `en` | output language |
| `--runtime auto\|all\|<name>` | `auto` | which runtimes to detail (`auto` = all with data) |
| `--hours N` | 3 | window in hours |
| `--project PATH` | cwd | project root for CLAUDE.md · rules · memory lookup |
| `--request FILE` | none | dissect one captured **request body** log (tool sizes · `defer_loading`) |
| `--rewrite-tokens N` | 150000 | what counts as a full rewrite |
| `--budget N` | 250000 | proposed distill threshold |
| `--top N` | 6 | session rows per runtime |
| `--json` | off | machine readable · adds the `plan_input` block (contract `ctx.v1`) read by `ctx-plan` |

`--capacity` · `--inventory` · `--need` · `--scales` are not here — they moved to `ctx-plan`.

### `--request` and `--json`

```bash
ctx-burn --request ~/.cli-proxy-api/logs/error-v1-messages-*.log   # tool definition sizes too
ctx-burn --hours 168 --json > /tmp/burn.json                      # contract ctx.v1
ctx-plan --from /tmp/burn.json --capacity --accounts 5x:5,ultra:5
```

`--request` accepts any file with a JSON request body (a `=== REQUEST BODY ===` marker is understood too). Without a proxy you can skip it; the other sections work on their own. The `plan_input` block of `--json` is the `schema: ctx.v1` contract (`window_hours` · `pools{…}` · `rate_claude`). `ctx-plan` refuses any other schema.

### ctx-time

`ctx-burn` measures what was **paid**; `ctx-time` measures what the wall clock was **spent on**. It reads the same local session logs (pi · codex) and prints the categories, the commands that ran over the limit and where the time went — in the terminal and as one html file.

```bash
ctx-time                                   # last 3h · up to 40 sessions · 80MB · html
ctx-time --seat 'my-team-' --role arch --hours 14
ctx-time --split '2026-11-23 15:13:38'     # before / after one moment
ctx-burn --time --role nano                # same body through ctx-burn
```

| option | default | meaning |
|---|---|---|
| `--seat REGEX` · `--role NAME` | all | seat (session) name pattern · the `-<role>-` token of the name |
| `--hours N` | 3 | window, applied to file mtime and line timestamps |
| `--max-sessions N` · `--max-mb N` · `--max-scan N` | 40 · 80 · 3000 | sample caps (0 = no cap). Every cut prints its own line; nothing is trimmed silently |
| `--from` · `--to` · `--split` | — | epoch or `YYYY-MM-DD HH:MM[:SS]` (local) |
| `--runtime pi\|codex\|all` | all | |
| `--limit N` | 70 | "over the limit" threshold in seconds |
| `--out DIR` | `~/.cache/ctx-burn/time` | html folder |
| `--no-html` · `--json` · `--lang en\|ko` | — | html off · contract `ctx-time.v1` on stdout · language |

pi is covered fully, codex for commands and turn time. claude is reported as omitted (no per-call timing).

### ctx-window

`ctx-window` shows **where the conversation window was spent**, as four numbers from pi session logs (terminal first, one html file after). codex · claude · hermes print as skipped.

```bash
ctx-window                                 # last 3h · 40 sessions · 40MB · html
ctx-window --seat 'my-team-' --role arch --hours 14
ctx-window --split '2026-11-23 15:13:38'   # before / after one moment
ctx-burn --window --lang ko                # same body through ctx-burn
```

| number | meaning |
|---|---|
| **W1** bell-turn share | weighted cost of turns whose preceding input was a `custom_message` or a task order ÷ weighted cost of every turn after boot |
| **W2** boot window | window at the boot end minus the first turn, plus the tool calls spent there |
| **W3** past the gate | growth from the turn the window first crossed `--recv-gate` to the last turn (sessions crossed · median · max) |
| **W4** tool result size | results · bytes · results over `--result-cap` · cut notices · re-read ratio |

Options are the same as `ctx-time` (`--max-mb` default 40), plus `--recv-gate N` (default 280000 tokens) · `--result-cap N` (default 2048 bytes) · `--out DIR` (default `~/.cache/ctx-burn/window`) · `--json` (contract `ctx-window.v1`). Rows are cut by their own `timestamp` (from included · to excluded).

### ctx-share

Where `ctx-burn` measures what was used, `ctx-share` writes "how much of it was coordination" and "what % of the weekly limit it is" on one board.

```bash
ctx-share                                   # measure a 48h window and write the board folder
ctx-share --hours 24 --json                 # machine readable (no board write)
ctx-share --now 2026-11-17T13:00:00 --force # tests · re-measure
```

- Coordination / implementation is split by the third token (the role) of the session name `<project>-<team>-<role>[-<tail>]#<N>`. Names that are missing or do not parse are counted separately as "unclassified".
- Weekly % = the weighted claude total in the window, scaled to a week, against the constants in `accounts.env` (`FT_CAP_WK_5X` · `FT_CAP_WK_ULTRA` · `FT_CAP_TARGET_UTIL`). If any constant is empty, no % is printed.
- Writes `board.md` (human) · `last.json` (machine) · `samples.tsv` into the `--out` folder. If a value was measured within 30 minutes it skips with rc 0 (`--force` measures now). rc 1 = cannot judge.
- Options: `--hours N` (48) · `--now ISO` · `--sessions-dir` · `--resume-dir` · `--inv-file` · `--acct-file` · `--out` · `--json` · `--force`.

### Fixing what you find

| priority | action | how |
|---|---|---|
| 1 | turn off unused built-in tools | `settings.json` → `env`: `CLAUDE_CODE_DISABLE_ARTIFACT=1`, `CLAUDE_CODE_DISABLE_WORKFLOWS=1` |
| 2 | slim auto-loaded rules | move big files to `~/.claude/guides/`, keep a 1KB digest in `rules/` |
| 3 | lower the distill threshold | to the break-even turn count, usually 50% of average context |
| 4 | cap resume context | hand over a summary + the last few turns, not a 500k conversation |
| 5 | spread session starts | do not start a cron · tick herd in the same minute (jitter) |

### Safety

- **Reads only.** Never writes settings or files, no network calls (`ctx-time` · `ctx-window` write one html file under `--out`; `ctx-share` writes only into its board folder).
- Session logs stay local. Only token counters are read, never conversation text.
- `ctx-time` · `ctx-window` export only numbers · timestamps · fixed words · seat names · session paths. Command lines and error messages are used to pick a category and are never printed.
- Weights (read 0.1 · write 2.0 · output 5) follow public price ratios as an **approximation**. Real limit formulas are not public, so use the numbers for **relative** comparison.

## Requirements

- python3 3.8+ · standard library only (no pip install)
- macOS · Linux
- No API key · account · network
- Optional: a proxy log that holds request bodies (for example CLIProxyAPI) to see tool definition sizes
- Optional: the weekly % of `ctx-share` needs the `accounts.env` constants (sample in `ctx-plan`)

## Links

- [INSTALL.md](INSTALL.md) — install · verify · uninstall · troubleshooting
- [ctx-plan](../ctx-plan/README.md) — the sibling tool that reads `ctx.v1` (capacity · subscriptions needed)
- [AI Feature Pack catalog](../../README.md)
