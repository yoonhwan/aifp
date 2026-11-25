# Feature Pack: ctx-burn

A **read-only audit tool** that shows, with graphs, how much context your local AI coding agents waste.

> Answers "why did my $100 plan hit the rate limit 10 minutes after I paid?" with numbers from your own logs.

## Why

Agents re-send **the whole conversation + auto-loaded memory + tool definitions** on every turn.
So cost is `turns × context size`.

- Prompt cache alive → billed at `0.1x`. Cache broken → rewritten at `2x`.
- Restarting (distilling) a session pays the fixed prefix again at `2x`.
- Output is `5x`.

## Quick start

```bash
git clone https://github.com/yoonhwan/aifp.git
cd aifp/feature-pack/ctx-burn
bash install.sh            # symlink into ~/.local/bin (ctx-burn + ctx-waste alias)

cd ~/my-project
ctx-burn                    # last 3 hours, current folder
```

English by default. Korean: `ctx-burn --lang ko`

`ctx-waste` still works — it is a permanent alias of `ctx-burn`. This tool **only measures what was
burned**. Capacity, subscription count and goal throughput live in the sibling tool `ctx-plan`
(`ctx-burn --hours 168 --json | ctx-plan --capacity --accounts 5x:5,ultra:5`).

## Supported runtimes

Detected automatically (dirs + live processes), no config needed.

| runtime | session logs | token usage | memory / rules |
|---|---|---|---|
| `claude` | `~/.claude/projects/**/*.jsonl` | yes | `CLAUDE.md`, `rules/*.md`, project `CLAUDE.md`, `memory/MEMORY.md` |
| `codex` | `~/.codex/sessions/**/rollout-*.jsonl` | yes | `AGENTS.md`, `AGENTS.user.md` |
| `pi` | `~/.pi/agent/sessions/**/*.jsonl` | yes | `AGENTS.md` |
| `opencode` | `~/.local/share/opencode/opencode.db` | yes (sqlite) | `~/.config/opencode/AGENTS.md` |
| `hermes` | `~/.hermes/sessions/*.jsonl` | no (memory only) | `SOUL.md` |
| `openclaw` | registry only | no | `AGENTS.md` if present |
| `commandcode` | history only | no (memory only) | `AGENTS.md` |

Runtimes without token counters are still checked for **auto-loaded file size** and **live process count**.

## Reading the output

```
[0] Runtime environment
  runtime      installed running sessions last          data
  claude       yes       29      127      10:14         usage+memory
  pi           yes       20      9        10:15         usage+memory
```

```
[1] claude — auto-loaded memory — paid on every request
  !   3,876 tok ████████████████████████ ~/.claude/CLAUDE.md     9,474
  total 5,971 tokens · 15,504 chars
```
`!` marks a file over 4KB. `~/.claude/rules/*.md` is **auto-loaded**; `~/.claude/guides/*.md` is
opened only when needed. Big rule files belong in `guides/`, with a 1KB digest left in `rules/`.

```
[2] claude — burn structure (weighted · total 80.0M)
  cache full rewrite  60.8% ███████████████·········  48.7M  61
  cache read (normal) 27.6% ███████·················  22.1M
```
If **full rewrite** is above 20%, that is the primary suspect. One rewrite costs as much as
20 normal requests.

```
[3] context per request
  avg 269,470 · max 582,588 tokens
```
An average over 200k means the conversation has grown to the end of the window — distillation
is not kicking in.

```
break-even for distillation
  restart cost        3k  (prefix 12,757 x 2.0)
  saving per turn     1,947  (distill at 250,000)
  break-even 13.1 turns · avg 12.1 turns/session -> current cadence is fine
```
Tells you **where to put the threshold**. If turns per session exceed the break-even, distill more often.


## Hand it to your own agent

You do not have to run anything by hand. Paste this into Claude Code, Codex, pi, opencode or any
coding agent and it installs, runs, and explains the result itself.

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

Any agent can do this because every number comes from files on the machine: session logs and
rule files. No API key, no network.


## The core lever: start budget, not window size

A 1M window is not usable if you distill at 300k. What matters is **how much of the gate is left
for actual conversation** when a session starts.

```
gate 300,000 · measured prefix 48,551 · handover 5,000
fresh distill (handover)   ▒▒▒▒▒▒██████████████████████████  remaining 246,449 (82%) · rewrite 107k
resume 200k                ▒▒▒▒▒▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓███████████  remaining 100,000 (33%) · rewrite 400k
resume 250k                ▒▒▒▒▒▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓█████  remaining  50,000 (17%) · rewrite 500k
prefix ▒ · carried ▓ · remaining █
fresh start: 4.9x the working room · 4.7x less rewrite cost (vs resume 250k)
```

**Resuming a 250k conversation leaves 50k of room and costs 500k to re-write. Starting fresh with a
5k handover leaves 246k and costs 107k.** That single ratio is the biggest lever in agent cost, and
it is why `ctx-burn` prints this table before the break-even section.

Tune with `--gate` and `--resume-caps` (comma separated).

## Options

| option | default | meaning |
|---|---|---|
| `--lang en\|ko` | `en` | output language |
| `--runtime auto\|all\|<name>` | `auto` | which runtimes to detail (`auto` = all with data) |
| `--hours N` | 3 | window in hours |
| `--project PATH` | cwd | project root for CLAUDE.md / rules / memory lookup |
| `--request FILE` | none | dissect one captured **request body** log (tool sizes, `defer_loading`) |
| `--rewrite-tokens N` | 150000 | what counts as a full rewrite |
| `--budget N` | 250000 | proposed distill threshold |
| `--top N` | 6 | session rows per runtime |
| `--json` | off | machine readable · adds the `plan_input` block (contract `ctx.v1`) consumed by `ctx-plan` |

`--capacity` / `--inventory` / `--need` / `--scales` are **not** here — they moved to `ctx-plan`.

### `--request` — see tool definitions too

```bash
ctx-burn --request ~/.cli-proxy-api/logs/error-v1-messages-*.log
```

Any file containing a JSON request body works (a `=== REQUEST BODY ===` marker is also understood).

`ctx-burn --json` adds one block that is a **contract**: `plan_input` with `schema: ctx.v1`
(`window_hours` · `pools{req, usage0, ctx_per_req, active_hours, cache_reuse, cache_reuse_of_input,
w_per_session_hour, samples, sessions, w_total}` · `rate_claude`). `ctx-plan` refuses anything else.

```bash
ctx-burn --hours 168 --json > /tmp/burn.json
ctx-plan --from /tmp/burn.json --inventory                     # 0순위 상수 점검
ctx-plan --from /tmp/burn.json --capacity --accounts 5x:5,ultra:5
```

## `ctx-share` — 조율 몫과 주간 환산 보드

`ctx-burn` 이 «쓴 양» 을 재면 `ctx-share` 는 «그중 조율이 얼마인지» 와 «주간 한도의 몇 %인지» 를
보드 한 장에 쓴다. 정의 정본 = (내부 문서).

```bash
ctx-share                                  # 48시간 창을 재서 보드 폴더에 쓴다
ctx-share --hours 24 --json                # 기계 판독(보드 쓰기 0)
ctx-share --now 2026-11-17T13:00:00 --force # 시험·재측정
```

### 정의 1 — 조율/구현 분류 = 좌석 이름의 역할 칸

세션 파일이 스스로 가진 이름(`session_info.name`, 없으면 seat-resume 기록의 `jsonl` → `name`)을
문법 `<프로젝트>-<팀>-<역할>[-<꼬리>]#<N>` 로 가른다. `#` 뒤가 숫자뿐이고, `#` 앞을 `-` 로 갈라
토큰이 3개 이상(빈 토큰 0)이면 **셋째 토큰이 역할**이다. 팀 이름·카드 slug 는 읽지 않는다.

| 갈래 | 역할 토큰 |
|---|---|
| 구현 | `nano` · `tester` · `qa` · `repro` · `tool` · `implementer` · `worker` |
| 조율 | `master` · `arch` · `da` · `desk` · `pm` · `checker` · `analyst` · `lead` · `architect` · `orch` |
| 못 가림 | 이름 없음 · 문법으로 안 풀리는 이름 · 표에 없는 역할 |

조율 몫 % = 조율 ÷ (조율 + 구현). 못 가림은 분모에서 빼고 따로 보인다. 10% 를 넘으면 판정 불가다.

### 정의 2 — 주간 환산 사용률

주간 % = (창 안 claude 모델 가중 합 × 168 ÷ 창 시간)
÷ ((5x 장수 × `FT_CAP_WK_5X` + ultra 장수 × `FT_CAP_WK_ULTRA`) × `FT_CAP_TARGET_UTIL`) × 100

가중 = `input` + 1.25 × (cacheWrite − cacheWrite1h) + 2.0 × cacheWrite1h + 0.1 × cacheRead + 5 × output
(`ctx-burn` 과 같은 상수). 상수는 `accounts.env` 에서 읽고, 하나라도 비면 % 를 내지 않는다.
보드에는 낮은 앵커(`WK_*_LOW`) 값도 괄호로 함께 쓴다.

### 정의 2-2 — 계정 실측 %(대조 값)

`anchor-snapshots.jsonl` 의 마지막 표본으로 Σ(w × 계정 한도) ÷ Σ 계정 한도를 낸다(`TARGET_UTIL` 0).
차 = 계정 실측 − 로컬 W 환산. +20%p 이상이면 «다른 머신·밖 경로 의심», −20%p 이하이면
«로컬이 더 큼 · 자 차» 표지를 붙인다. 판정(목표 안)은 두 값 모두 ≤ 100% 일 때만이다.

### 정의 3 — 보드 자리와 갱신 주기

보드 = `<out>/board.md`(사람) · `last.json`(기계) · `samples.tsv`(갱신마다 1줄) · 기본 `out` =
`$FT_ROOT/.fable-team/state/usage-monitor`(없으면 BIZ 루트). 30분 안에 잰 값이 있으면 스스로
건너뛰고 rc 0(`--force` 로 바로 잼). 보드는 임시 파일에 쓴 뒤 이름을 바꾼다.

`board.md` 줄 순서 = ① 잰 시각·창 ② 조율·구현(목표 ≤ 50%) ③ 로컬 W 환산(낮은 앵커)·계정 실측·차·표지
④ 못 가림 ⑤ 24시간·168시간 참고 ⑥ 조율 상위 5좌석 ⑦ 판정(목표 안 / 목표 밖 / 판정 불가 <사유>).
rc 0 = 쟀다(목표 안·밖), rc 1 = 판정 불가(세션 폴더 없음 · 상수 결손 · 계정 표본 문제 · 못 가림 초과).
보드 폴더 밖 쓰기 0 · 네트워크 0 · 세션 로그·좌석 기록·상수·계정 표본은 읽기만 한다.

| option | default | meaning |
|---|---|---|
| `--hours N` | 48 | 창 시간 |
| `--now ISO` | 지금 | 재는 시각(시험) |
| `--sessions-dir` / `--resume-dir` | `~/.pi/agent/sessions` · `~/.claude/state/seat-resume` | 읽을 곳 |
| `--inv-file` | `accounts.env`(`$CTX_PLAN_CAP_FILE`) | 상수 |
| `--acct-file` | `anchor-snapshots.jsonl` | 계정 표본 |
| `--out` | 위 «정의 3» | 보드 폴더 |
| `--json` | off | 기계 판독 · 보드 쓰기 0 |
| `--force` | off | 30분 건너뜀 무시 |

## `ctx-time` — where the seats spent their time

`ctx-burn` measures what was **paid**; `ctx-time` measures what the wall clock was **spent on**.
It reads the same local session logs (pi · codex) and prints the categories, the commands that ran over
the limit, and where the time went — in the terminal and as one html file.

```bash
ctx-time                                   # last 3h · up to 40 sessions · 80MB · html
ctx-time --seat 'biz-harness-' --role arch --hours 14
ctx-time --split '2026-11-23 15:13:38'     # before / after one moment
ctx-burn --time --role nano                # same body through ctx-burn
```

| option | default | meaning |
|---|---|---|
| `--seat REGEX` | all | seat name pattern (pi `session_info.name` · codex `session_meta.cwd` folder) |
| `--role NAME` | all | master · arch · nano · desk · da (read from the `-<role>-` token of the seat name) |
| `--hours N` | 3 | window, applied to file mtime **and** line timestamps |
| `--max-sessions N` | 40 | sessions measured (0 = no cap) |
| `--max-mb N` | 80 | bytes read, name lookup included (0 = no cap) |
| `--max-scan N` | 3000 | session files stat'ed (0 = no cap) |
| `--from` · `--to` · `--split` | — | epoch or `YYYY-MM-DD HH:MM[:SS]` (local) |
| `--runtime pi\|codex\|all` | all | |
| `--limit N` | 70 | "over the limit" threshold in seconds |
| `--out DIR` | `~/.cache/ctx-burn/time` | html folder |
| `--no-html` · `--json` · `--lang en\|ko` | — | html off · contract `ctx-time.v1` on stdout · language |

Sample selection has a cap on every step — list names → stat up to `--max-scan` → name lookup inside
1/5 of `--max-mb` → read bodies until `--max-mb` is spent. Every cut prints its own line
(`훑기 줄임` · `이름 조회 줄임` · `표본 줄임`); nothing is trimmed silently.

The default sample takes **2 seconds** on the machine that measured it (1,414 session files). That is a
target for that file count, not a promise that holds for any session count —
2초는 재는 머신의 파일 수에서의 목표이고 세션 파일 수가 얼마든 지킨다는 보장이 아니다 — 파일 이름 나열·정렬은 총수에 비례한다.

Two safety promises are separate: body keys are never queried (only `timestamp` · `durationMs` ·
`type` · `role` · `session_info.name` · toolCall `name`/`id` · `arguments.command`(or `path`) head 400 ·
`arguments.timeout` · `errorMessage` head 60), and nothing but numbers · timestamps · fixed words ·
seat names · session paths leaves the tool. Command lines and error messages pick a category and are
dropped — not even the first word is printed. Runtime coverage: pi fully · codex commands and turn
time · claude is reported as omitted (no per-call timing).

## `ctx-window` — where the conversation window went

`ctx-burn` counts tokens; `ctx-window` shows **where the window was spent**. It reads pi session logs and
prints four numbers — terminal first, one html file after.

```bash
ctx-window                                       # last 3h · 40 sessions · 40MB · html
ctx-window --seat 'biz-harness-' --role arch --hours 14
ctx-window --split '2026-11-23 15:13:38'         # before / after one moment
ctx-burn --window --lang ko                      # same body through ctx-burn
```

| number | meaning |
|---|---|
| **W1** bell-turn share | a turn = one assistant line with `usage`. **W1a** = turns whose preceding input was a `custom_message` or a user line starting with `[발주 #` in its first 40 chars. **W1b** = W1a turns whose every tool call was one *pure recv* line. Share = weighted cost of bell turns ÷ weighted cost of every turn after boot (weights: read 0.1 · write 1.25 · input 1.0). |
| **W2** boot window | window at the boot end minus the first turn, plus the tool calls spent there. Boot end = the first turn that is already *after boot* — i.e. the turn following the one that ran `[부팅 보고]`; 20 turns after the first when no boot report is there. |
| **W3** past the gate | per session, from the turn the window first crossed `--recv-gate` to the last turn (last window − the turn before crossing). Sessions crossed · median · max · three biggest end windows. |
| **W4** tool result size | results · bytes · results over `--result-cap` (and the excess bytes) · cut notices (W4c) · re-reads (`ft-tool-result/` in a call) · re-read ratio. |

A *cut notice* (W4c) is counted only when all three hold: one line of the result reads exactly
`[결과 상한] 전문 <N>바이트[ · <N>줄] 중 머리 <A> · 꼬리 <B> 만 실음 · 전문 = …` from its first character, the
utf-8 bytes before that line (less the one newline in front) equal `<A>`, and the bytes after it (less the one
newline behind) equal `<B>`. That is how pi truncates: `head + newline + notice + newline + tail`, where `<A>` and
`<B>` are the head and tail sizes. This is a **shape** test, not a quote test — original text that quotes a notice
with the right byte counts cannot be told apart, so no "zero quotes" guarantee is claimed. Several matching lines
in one result still count as one.

A *pure recv* command (W1c) must match one shape end to end — no partial match:
`[cd <word> &&] [NAME=<word> …] [bash] <path>mbox.sh recv [<word> 0–3] [2>&1] [| tail -N · tail -n N · head -N · head -n N]`,
where `<word>` is single-quoted text · double-quoted text without `$` or a backtick · or only `A-Za-z0-9_@%+=:,./#~-`.
Command lines are read to 400 chars; a line cut at 400 is never pure recv.

| option | default | meaning |
|---|---|---|
| `--seat REGEX` · `--role NAME` · `--hours N` | all · all · 3 | same as `ctx-time` |
| `--max-sessions N` · `--max-mb N` · `--max-scan N` | 40 · 40 · 3000 | sample caps (0 = no cap) |
| `--recv-gate N` | 280000 | W3 threshold in tokens |
| `--result-cap N` | 2048 | W4 result size threshold in bytes |
| `--from` · `--to` · `--split` | — | epoch or `YYYY-MM-DD HH:MM[:SS]` (local) |
| `--out DIR` | `~/.cache/ctx-burn/window` | html folder |
| `--no-html` · `--json` · `--lang en\|ko` | — | html off · contract `ctx-window.v1` on stdout · language |

Rows are cut by their own `timestamp` before W1 – W4 are summed, with the same rule as `ctx-time`: a row whose
timestamp is missing, or `t < --from`, or `t >= --to`, is not counted (from included · to excluded). File mtime
only picks the sample; it does not decide which rows inside a picked file count.

The original-file comparison (`analyze2.py` · `cap.py`) reads the whole log with no window, so it cannot catch a
missing row filter — that limit is checked by the fixed inputs instead (`test_window_cut_rows` · `test_window_edges`).

The sample is chosen and read by the landed `ctx-time` body itself (`Budget` · `list_files` · `scan_window` ·
`pick` · `read_lines`, loaded with `importlib` and bytecode writing off) — the limits are not rebuilt. Only pi
sessions are measured (the four numbers come from pi-only markers); codex · claude · hermes print as skipped.
A session with no marker at all (`[발주 #` · `[부팅 보고]` · `ft-tool-result/`) is left out of
W1 · W2 and still counted in W3 · W4. A session whose read was cut at the reserved size is left out of W3
(the last turn of a cut log is not the real last turn) and prints `읽기 잘림`.

The four numbers mirror the harness originals (`analyze2.py` · `cap.py`) so a value measured here can be
compared with the values those cards landed.

## How to fix what you find

| priority | action | how |
|---|---|---|
| 1 | turn off unused built-in tools | `settings.json` → `env`: `CLAUDE_CODE_DISABLE_ARTIFACT=1`, `CLAUDE_CODE_DISABLE_WORKFLOWS=1` |
| 2 | slim auto-loaded rules | move big files to `~/.claude/guides/`, keep a 1KB digest in `rules/` |
| 3 | lower the distill threshold | to the break-even turn count, usually 50% of average context |
| 4 | cap resume context | hand over a summary + the last few turns, not a 500k conversation |
| 5 | spread session starts | do not start a cron/tick herd in the same minute (jitter) |

`defer_loading` keeps a tool definition at 0 tokens until it is loaded, but it is not a
user-facing switch — so the practical fix for unused tools is turning the feature off.

## Safety

- **Reads only.** Never writes settings or files. No network calls (`ctx-time` writes one html file under `--out`;
  `ctx-window` writes one html file under `--out` too).
- Session logs stay local. Only token counters are read, never conversation text.
- `ctx-time` never queries body keys and exports only numbers · timestamps · fixed words · seat names · session paths.
  Command lines and error messages are read to pick a category and never printed — not even the first word.
- `ctx-window` exports numbers · timestamps · fixed words · seat names · session paths only. Tool result text is
  read as a utf-8 byte count and the W4c shape (a notice line found anywhere in the text, its two numbers compared
  with the byte counts in front of and behind it); only the count leaves the tool, never the notice numbers, path
  or text. User text is read only for `[발주 #` inside its first 40 chars, tool call arguments only for
  `[부팅 보고]` and `ft-tool-result/`. Model text and thinking are not read. Command lines are never printed.
  Three fixed markers (`[발주 #` · `[부팅 보고]` · `ft-tool-result/`) and two shape tests (W1c · W4c) is all the
  text is used for, and both shape tests answer yes/no only.
- Weights (read 0.1 / write 2.0 / output 5) follow public price ratios as an **approximation**.
  Real limit formulas are not public, so use the numbers for **relative** comparison.

## Requirements

- python3 (3.8+), standard library only
- macOS · Linux
