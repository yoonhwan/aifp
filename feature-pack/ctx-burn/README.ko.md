<div align="center">

# ctx-burn

**로컬 AI 코딩 에이전트가 컨텍스트를 얼마나 태우는지 내 로그의 숫자와 그래프로 보여주는 읽기 전용 감사 도구**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- 에이전트는 매 턴 **대화 전체 + 자동 로드 메모리 + 툴 정의**를 다시 보냅니다. `ctx-burn` 은 그 비용을 로컬 세션 로그에서 재어 보여줍니다(캐시 읽기 `0.1x` · 캐시 재작성 `2x` · 출력 `5x` 가중).
- 설치·실행 중인 런타임을 스스로 찾습니다: `claude` · `codex` · `pi` · `opencode` 는 토큰 사용량까지, `hermes` · `openclaw` · `commandcode` 는 자동 로드 파일 크기와 실행 중 프로세스 수만 봅니다.
- 캐시 전면 재작성 비중 · 요청당 평균 컨텍스트 · 4KB 넘는 자동 로드 파일 · 증류 손익분기 턴 수 · 시작 예산(새로 증류 vs 이어 붙이기)을 그래프로 냅니다.
- `--request` 로 캡처한 요청 본문 하나를 갈라 툴 정의 크기를 봅니다.
- 같은 팩의 `ctx-time`(벽시계 시간을 어디에 썼나) · `ctx-window`(대화창을 어디에 썼나) · `ctx-share`(조율 몫과 주간 환산 보드)를 함께 설치합니다.
- `--json` 은 짝 도구 `ctx-plan` 이 읽는 계약 `ctx.v1` 블록을 냅니다. 설정·파일 쓰기 0 · 네트워크 0 · API 키 0.

## 빠른 시작

```bash
git clone https://github.com/yoonhwan/aifp.git
cd aifp/feature-pack/ctx-burn
bash install.sh            # ~/.local/bin 에 심링크 (ctx-burn + ctx-waste alias)

cd ~/my-project
ctx-burn                   # 최근 3시간 · 지금 폴더
ctx-burn --lang ko         # 한국어 출력 (기본은 영어)
```

## 설치

### 에이전트에게 맡기기

에이전트에게 «Read feature-pack/ctx-burn/INSTALL.md and install it» 라고 하거나, 아래 블록을 Claude Code · Codex · Pi · OpenCode 같은 코딩 에이전트에 그대로 붙여넣으면 설치 · 실행 · 해석까지 스스로 합니다. 도구가 읽기 전용이라 실행은 안전합니다.

```text
ctx-burn 를 이 프로젝트에 설치하고 돌린 뒤 결과를 해석해줘.
https://github.com/yoonhwan/aifp/tree/main/feature-pack/ctx-burn

1. 클론 후 feature-pack/ctx-burn/install.sh 실행 (~/.local/bin/ctx-burn 심링크)
2. 이 프로젝트 루트에서 ctx-burn --hours 6 실행 (한국어면 --lang ko)
3. 출력에서 캐시 전면 재작성 비중 · 요청당 평균 컨텍스트 · 4KB 넘는 자동 로드 파일 top3 만 보고
4. 재작성 비중이 20% 넘으면 로컬 로그로 원인(리줌 크기·세션 동시 시작·계정 전환)을 찾아 근거 줄과 함께 제시
5. 4KB 넘는 자동 로드 파일은 자동 로드 경로 밖으로 옮기고 1KB 다이제스트를 남기는 안을 제안
6. 설정을 바꾸기 전에는 나에게 물어봐. 툴 자체는 읽기 전용이라 실행은 안전하다
```

### 직접 설치

`install.sh` 는 `~/.local/bin` 에 심링크만 만듭니다: `ctx-burn` · `ctx-waste`(`ctx-burn` 의 영구 alias) · `ctx-share` · `ctx-time` · `ctx-window`. `command not found` 가 나오면 `~/.local/bin` 이 PATH 에 없는 것입니다.

```bash
CTX_BURN_BIN_DIR="$HOME/bin" bash install.sh   # 설치 폴더 바꾸기 (옛 이름 CTX_WASTE_BIN_DIR 도 읽음)
export PATH="$HOME/.local/bin:$PATH"           # PATH 에 없으면 셸 rc 에 추가
bash uninstall.sh                              # 제거 — 심링크만 지움
```

`uninstall.sh` 는 `ctx-burn` · `ctx-waste` · `ctx-time` · `ctx-window` 심링크를 지웁니다. 세션 로그 · 설정은 건드리지 않습니다.

## 사용법

### 출력 읽기

| 절 | 보여주는 것 | 볼 점 |
|---|---|---|
| `[0]` 런타임 환경 | 런타임별 설치 · 실행 중 · 세션 수 · 마지막 시각 · 데이터 종류 | 설정 없이 자동 감지 |
| `[1]` 자동 로드 메모리 | 매 요청마다 값을 치르는 파일과 토큰 수 | `!` = 4KB 넘는 파일. 큰 규칙 파일은 필요할 때 여는 자리로 옮기고 1KB 요약만 남깁니다 |
| `[2]` 태운 구조 | 캐시 전면 재작성 · 캐시 읽기 등의 가중 비중 | 전면 재작성이 20% 를 넘으면 첫 용의자. 재작성 1번 = 보통 요청 20번 값 |
| `[3]` 요청당 컨텍스트 | 평균 · 최대 토큰 | 평균 200k 넘음 = 대화가 창 끝까지 자랐고 증류가 안 걸림 |
| 증류 손익분기 | 재시작 비용 · 턴당 절약 · 손익분기 턴 수 | 세션당 턴 수가 손익분기를 넘으면 더 자주 증류 |
| 시작 예산 | 게이트 · 고정 prefix · 인계 크기로 새로 시작 vs 이어 붙이기의 남은 공간과 재작성 비용 | 창 크기보다 «세션을 열 때 대화에 남는 몫» 이 큰 손잡이. `--gate` · `--resume-caps`(쉼표) 로 조정 |

### ctx-burn 옵션

| 옵션 | 기본값 | 뜻 |
|---|---|---|
| `--lang en\|ko` | `en` | 출력 언어 |
| `--runtime auto\|all\|<name>` | `auto` | 상세를 볼 런타임 (`auto` = 데이터 있는 것 전부) |
| `--hours N` | 3 | 창 시간 |
| `--project PATH` | 지금 폴더 | CLAUDE.md · rules · memory 를 찾을 프로젝트 루트 |
| `--request FILE` | 없음 | 캡처한 **요청 본문** 로그 하나를 가름(툴 크기 · `defer_loading`) |
| `--rewrite-tokens N` | 150000 | 전면 재작성으로 칠 크기 |
| `--budget N` | 250000 | 제안 증류 임계값 |
| `--top N` | 6 | 런타임별 세션 줄 수 |
| `--json` | 끔 | 기계 판독 · `ctx-plan` 이 읽는 `plan_input` 블록(계약 `ctx.v1`) 추가 |

`--capacity` · `--inventory` · `--need` · `--scales` 는 여기 없습니다 — `ctx-plan` 으로 옮겼습니다.

### `--request` 와 `--json`

```bash
ctx-burn --request ~/.cli-proxy-api/logs/error-v1-messages-*.log   # 툴 정의 크기까지
ctx-burn --hours 168 --json > /tmp/burn.json                      # 계약 ctx.v1
ctx-plan --from /tmp/burn.json --capacity --accounts 5x:5,ultra:5
```

`--request` 는 JSON 요청 본문이 든 파일이면 됩니다(`=== REQUEST BODY ===` 표지도 읽음). 프록시를 쓰지 않으면 생략해도 나머지 절은 혼자 동작합니다. `--json` 의 `plan_input` 은 `schema: ctx.v1` 계약입니다(`window_hours` · `pools{…}` · `rate_claude`). `ctx-plan` 은 다른 schema 를 거부합니다.

### ctx-time

`ctx-burn` 이 **치른 값**을 잰다면 `ctx-time` 은 벽시계 시간을 **어디에 썼나**를 잽니다. 같은 로컬 세션 로그(pi · codex)를 읽어 갈래 · 한도를 넘은 명령 · 시간이 간 곳을 터미널과 html 파일 1개로 냅니다.

```bash
ctx-time                                   # 최근 3시간 · 세션 40개까지 · 80MB · html
ctx-time --seat 'my-team-' --role arch --hours 14
ctx-time --split '2026-11-23 15:13:38'     # 한 시점 앞 / 뒤
ctx-burn --time --role nano                # ctx-burn 으로 같은 본체 부르기
```

| 옵션 | 기본값 | 뜻 |
|---|---|---|
| `--seat REGEX` · `--role NAME` | 전부 | 좌석(세션) 이름 패턴 · 이름의 `-<role>-` 토큰 |
| `--hours N` | 3 | 창 시간(파일 mtime 과 줄 timestamp 둘 다) |
| `--max-sessions N` · `--max-mb N` · `--max-scan N` | 40 · 80 · 3000 | 표본 상한(0 = 상한 없음). 자른 단계마다 1줄을 찍고 몰래 줄이지 않음 |
| `--from` · `--to` · `--split` | — | epoch 또는 `YYYY-MM-DD HH:MM[:SS]`(로컬) |
| `--runtime pi\|codex\|all` | all | |
| `--limit N` | 70 | «한도 넘음» 기준 초 |
| `--out DIR` | `~/.cache/ctx-burn/time` | html 폴더 |
| `--no-html` · `--json` · `--lang en\|ko` | — | html 끔 · stdout 에 계약 `ctx-time.v1` · 언어 |

pi 는 전부, codex 는 명령과 턴 시간을 봅니다. claude 는 호출별 시간이 없어 «생략» 으로 나옵니다.

### ctx-window

`ctx-window` 는 대화창이 **어디에 쓰였나**를 pi 세션 로그에서 숫자 4개로 냅니다(터미널 먼저, html 파일 1개 뒤). codex · claude · hermes 는 건너뜀으로 나옵니다.

```bash
ctx-window                                 # 최근 3시간 · 세션 40개 · 40MB · html
ctx-window --seat 'my-team-' --role arch --hours 14
ctx-window --split '2026-11-23 15:13:38'   # 한 시점 앞 / 뒤
ctx-burn --window --lang ko                # ctx-burn 으로 같은 본체 부르기
```

| 숫자 | 뜻 |
|---|---|
| **W1** 알림 턴 몫 | 앞 입력이 `custom_message` 이거나 작업 지시로 시작한 턴의 가중 비용 ÷ 부팅 뒤 모든 턴의 가중 비용 |
| **W2** 부팅 창 | 부팅이 끝난 턴의 창 − 첫 턴, 그리고 그 사이 툴 호출 |
| **W3** 게이트 넘은 뒤 | 창이 `--recv-gate` 를 처음 넘은 턴부터 마지막 턴까지 늘어난 양(넘은 세션 수 · 중앙값 · 최대) |
| **W4** 툴 결과 크기 | 결과 수 · 바이트 · `--result-cap` 넘은 결과 · 잘림 알림 · 다시 읽기 비율 |

옵션은 `ctx-time` 과 같고(`--max-mb` 기본 40) `--recv-gate N`(기본 280000 토큰) · `--result-cap N`(기본 2048 바이트) · `--out DIR`(기본 `~/.cache/ctx-burn/window`) · `--json`(계약 `ctx-window.v1`) 이 더 있습니다. 줄은 자기 `timestamp` 로 자릅니다(from 포함 · to 제외).

### ctx-share

`ctx-burn` 이 «쓴 양» 을 잰다면 `ctx-share` 는 «그중 조율이 얼마인지» 와 «주간 한도의 몇 % 인지» 를 보드 한 장에 씁니다.

```bash
ctx-share                                   # 48시간 창을 재서 보드 폴더에 씀
ctx-share --hours 24 --json                 # 기계 판독(보드 쓰기 0)
ctx-share --now 2026-11-17T13:00:00 --force # 시험 · 다시 재기
```

- 조율 / 구현 = 세션 이름 `<project>-<team>-<role>[-<tail>]#<N>` 의 셋째 토큰(역할)으로 가릅니다. 이름이 없거나 문법에 안 맞으면 «못 가림» 으로 따로 셉니다.
- 주간 % = 창 안 claude 가중 합을 주 단위로 늘려 `accounts.env` 의 상수(`FT_CAP_WK_5X` · `FT_CAP_WK_ULTRA` · `FT_CAP_TARGET_UTIL`)와 견줍니다. 상수가 하나라도 비면 % 를 내지 않습니다.
- `--out` 폴더에 `board.md`(사람) · `last.json`(기계) · `samples.tsv` 를 씁니다. 30분 안에 잰 값이 있으면 건너뛰고 rc 0(`--force` 로 바로 잼). rc 1 = 판정 불가.
- 옵션: `--hours N`(48) · `--now ISO` · `--sessions-dir` · `--resume-dir` · `--inv-file` · `--acct-file` · `--out` · `--json` · `--force`.

### 찾은 것 고치기

| 순위 | 할 일 | 방법 |
|---|---|---|
| 1 | 안 쓰는 내장 툴 끄기 | `settings.json` → `env`: `CLAUDE_CODE_DISABLE_ARTIFACT=1`, `CLAUDE_CODE_DISABLE_WORKFLOWS=1` |
| 2 | 자동 로드 규칙 줄이기 | 큰 파일은 `~/.claude/guides/` 로 옮기고 `rules/` 에 1KB 요약만 |
| 3 | 증류 임계값 낮추기 | 손익분기 턴 수까지, 보통 평균 컨텍스트의 50% |
| 4 | 이어 붙일 컨텍스트 상한 | 500k 대화 대신 요약 + 마지막 몇 턴만 넘기기 |
| 5 | 세션 시작 흩기 | cron · tick 무리를 같은 분에 띄우지 않기(jitter) |

### 안전

- **읽기만 합니다.** 설정 · 파일을 쓰지 않고 네트워크 호출이 없습니다(`ctx-time` · `ctx-window` 는 `--out` 아래 html 파일 1개, `ctx-share` 는 보드 폴더에만 씀).
- 세션 로그는 로컬에 남습니다. 토큰 카운터만 읽고 대화 본문은 읽지 않습니다.
- `ctx-time` · `ctx-window` 는 숫자 · 시각 · 고정 낱말 · 좌석 이름 · 세션 경로만 내보냅니다. 명령 줄과 오류 문구는 갈래를 고르는 데만 쓰고 찍지 않습니다.
- 가중치(읽기 0.1 · 쓰기 2.0 · 출력 5)는 공개 가격 비율을 따른 **근사**입니다. 실제 한도 공식은 공개되지 않았으니 **상대 비교**에 쓰세요.

## 요구사항

- python3 3.8 이상 · 표준 라이브러리만(pip 설치 없음)
- macOS · Linux
- API 키 · 계정 · 네트워크 없음
- 선택: 툴 정의 크기를 보려면 요청 본문이 든 프록시 로그(예: CLIProxyAPI)
- 선택: `ctx-share` 의 주간 % 는 `accounts.env` 상수가 필요합니다(`ctx-plan` 견본)

## 링크

- [INSTALL.md](INSTALL.md) — 설치 · 확인 · 제거 · 문제 해결
- [ctx-plan](../ctx-plan/README.ko.md) — `ctx.v1` 을 읽는 짝 도구(감당량 · 필요 구독 수)
- [AI Feature Pack 카탈로그](../../README.ko.md)
