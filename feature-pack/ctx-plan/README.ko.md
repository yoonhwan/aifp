<div align="center">

# ctx-plan

**계정 구성으로 정원 · 피크 세션 · 골 처리량을 계산하고, 목표 규모에 필요한 구독 장수를 역산하는 감당량 도구**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- 짝 도구 `ctx-burn` 이 «쓴 양» 을 잰다면 `ctx-plan` 은 «감당량» 을 시뮬레이션합니다. 둘은 **JSON 계약 하나(`ctx.v1`)로만** 붙습니다.
- `--capacity`: 계정 구성(`--accounts 5x:N,ultra:N`)으로 pool 표 · 시뮬 4행 · 골 모형 2행을 냅니다.
- `--inventory`: 0순위 고정상수 19키(구독 장수 · 주간 리밋 등)를 점검하고 «0순위 문제 N건» · 요구 계정 역산 · 기준선 A 를 냅니다.
- `--need K:N`: 목표 규모(동시 세션 · 세션 · 팀 · 동시 골)에서 필요한 Ultra / 5x 장수를 역산합니다.
- `--scales`: 낭비를 줄였을 때의 배율 목록으로 다시 계산합니다.
- 세션 로그도, 실제 HOME 도 읽지 않습니다. 입력은 `ctx-burn --json` 출력과 상수 파일 하나뿐 · 쓰기 0 · 네트워크 0.

## 빠른 시작

```bash
git clone https://github.com/yoonhwan/aifp.git
cd aifp/feature-pack/ctx-plan
bash install.sh                                 # ~/.local/bin/ctx-plan

cp accounts.env.example /tmp/accounts.env       # 상수 파일 — 값은 머신마다 채운다
ctx-burn --hours 168 --json > /tmp/burn.json    # ctx-burn 팩이 필요

CTX_PLAN_CAP_FILE=/tmp/accounts.env ctx-plan --from /tmp/burn.json --inventory   # 0순위 상수 점검
ctx-plan --from /tmp/burn.json --inv-file /tmp/accounts.env --capacity --accounts 5x:5,ultra:5
ctx-plan --from /tmp/burn.json --inv-file /tmp/accounts.env --need concurrent:40
```

## 설치

### 에이전트에게 맡기기

이 팩에는 `INSTALL.md` 가 없습니다. 에이전트에게 «Read feature-pack/ctx-plan/README.md and install it» 이라고 하면 아래 직접 설치 단계를 따라 할 수 있습니다. 상수 파일 값은 사람이 채웁니다.

### 직접 설치

`install.sh` 는 `~/.local/bin/ctx-plan` 심링크 하나만 만듭니다. 상수 파일 자리는 정하지 않습니다 — 부르는 쪽이 `--inv-file` 이나 `CTX_PLAN_CAP_FILE` 로 줍니다.

```bash
bash install.sh                                 # ~/.local/bin/ctx-plan
CTX_PLAN_BIN_DIR="$HOME/bin" bash install.sh    # 설치 폴더 바꾸기
cp accounts.env.example /path/to/accounts.env   # 견본 — 값은 비어 있다. 채우지 않으면 «0순위 문제» 로 멈춘다
bash uninstall.sh                               # 제거 — 심링크만 지움
```

## 사용법

### 모드

| 모드 | 무엇을 내나 |
|---|---|
| (없음) | 머리 3줄 — 계약 · 축 정의 · 상수 파일 경로 + pool 한 줄 |
| `--inventory` | 0순위 상수 19키 점검 · «0순위 문제 N건» · 골 모형 2행(동시 골 · 골/주 · 유휴/부족 팀) · 요구 계정 역산 · 기준선 A |
| `--capacity` | pool 표(pool 있는 것만) · 시뮬 4행 · 골 모형 2행 |
| `--need K:N` | `concurrent:N` · `sessions:N` · `teams:N` · `goals:N`(동시 골 N개) → 필요 Ultra / 5x 장수 · `goals` 는 요구 계정 블록도 냄 · N 이 `FT_GOAL_PARALLEL_MAX` 를 넘으면 깎지 않고 알림 1줄(rc 0) |
| `--scales 1.0,0.9,…` | 낭비 감소 배율 목록(기본 4값 = 실측 · -10% · -20% · -30%) |

### 옵션

| 옵션 | 기본값 | 뜻 |
|---|---|---|
| `--from FILE\|-` | stdin | `ctx-burn --json` 출력 |
| `--inv-file FILE` | (아래 순서) | 고정상수 파일 |
| `--accounts 5x:N,ultra:N` | 없음 | `--capacity` 정원 · 피크 계산용 계정 구성 |
| `--wk-5x N` / `--wk-ultra N` | 630 / 2520 | 주간 리밋 앵커(가중 M) — 파일 값이 있으면 파일이 이김 |
| `--c5h-5x N` | 60 | 5x 5시간 창 앵커 |
| `--target-util F` | 0.85 | 주간 목표 사용률(운영 정책) |
| `--seats-per-team N` | 4 | 팀 하나 = 세션 몇 석 |
| `--hours-per-week N` | 40 | 세션 하나의 주당 시간 |
| `--teams-per-goal N` | 3 | 한 골에 동시에 붙는 팀 수 |
| `--team-hours-per-goal N` | 8 | 골 하나에서 팀 하나가 붙어 있는 시간 |

### 상수 파일

찾는 순서는 두 개뿐입니다: ① `--inv-file FILE` ② `$CTX_PLAN_CAP_FILE`. 상위 폴더를 뒤지거나 홈의 특정 경로를 가정하지 않습니다. 파일이 없으면 표를 하나도 내지 않고 rc 3 + 1줄(`--inv-file` · `CTX_PLAN_CAP_FILE` · `install.sh` 를 가리킴)로 끝납니다.

- 출력 머리에 읽은 경로 1줄을 찍습니다. 키 19개 = 구독 5 · 주간 리밋 4(상한 · 하한) · 모형 5(동시 골 참고값 포함) · 기준선 5.
- 값이 비면 «0순위 문제» 이고 **기본값으로 대체하지 않습니다** — 계산이 필요한 표는 «산정 불가» 로 나옵니다.
- 계약 키가 아닌 두 손잡이(`FT_CAP_C5H_5X` · `FT_CAP_HOURS_PER_WEEK`)만 기본값을 쓰고, 화면에 «기본값(계약 키 아님)» 이라고 적습니다.
- 견본 = [`accounts.env.example`](accounts.env.example)(값은 비어 있음).

### 골 모형(참고)

- 한 골 = 팀 3 동시 × 8시간 = 24 팀-시간 = 96 세션-시간 · 동시 골은 최대 3개 · 골/주 = min(가용 세션-시간 ÷ 96, 3 × 168 ÷ 8).
- 숫자는 상수(`FT_GOAL_PARALLEL_MAX` · `FT_GOAL_TEAMS` · `FT_GOAL_TEAM_HOURS` · `FT_CAP_SEATS_PER_TEAM`)에서 채웁니다.
- 계산 예시일 뿐 운영 규칙이 아니며, 출력에 «참고 — 운영 규칙 아님» 라벨이 붙습니다. 값을 넘어도 거부 · 축소하지 않고 알림만 냅니다.
- 기준선 A(`FT_BASE_*` 5키) = 상시 팀은 팀당 1석 × 168h, 이슈 · 골 팀은 낮 시간 × 7일 × 세션/팀으로 셉니다. `팀-시간/주` 는 중간 단위라 성과 판정에 쓰지 않습니다.

### 지키는 규칙

- **하한은 한 곳에서만** — `FT_CAP_WK_5X_LOW` · `FT_CAP_WK_ULTRA_LOW`. «상한 ÷ 3» 같은 대체 계산을 하지 않고, 비면 «산정 불가» 라고 씁니다.
- **라벨은 «낮은 용량 가정 · 높은 용량 가정»** — «낙관 · 보수» 를 쓰지 않습니다(작은 용량이 보수라는 보장이 없음).
- **앵커에는 상태가 붙습니다**(미검증 · 추정 · 실측 필요 · 운영 정책 등). 상태 표기가 남아 있는 동안은 그 숫자로 계정 결정을 내리지 마세요.
- **계약 검사** — `plan_input.schema` 가 `ctx.v1` 이 아니면 계산하지 않고 rc 2 + 사유 1줄로 멈춥니다.
- **모형 상수는 한 곳에서 해석** — `CLI 명시 > 상수 파일` 순서이고, 계약 키는 둘 다 없으면 «산정 불가» 입니다. 출처(`CLI` · `파일` · `없음` · `기본값(계약 키 아님)`)를 머리에 찍습니다.
- **표본 0 = 미산정** — 0 으로 채우지 않습니다. rc 는 0.

### 입력 계약 (ctx.v1)

`ctx-burn --json` 의 `plan_input`:

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

- `rate_claude` = claude pool 의 **세션-시간당 가중 토큰 중앙값**(표본 = 요청 20건 이상 세션). 계산 예산(M = 백만 가중 토큰)으로 바꾸는 곳은 한 줄뿐입니다. `units` 필드는 계약이 스스로 단위를 말하게 하는 표식입니다.
- `usage0` = 가중 0 레코드(API 오류)로, 요청률 분모에서 빠집니다. `unknown` pool = 모델 미상이고 다른 pool 에 섞지 않습니다.

### 안전

- 읽는 것: `--from` JSON 하나 · 상수 파일 하나. 그 밖은 0.
- 쓰기 0 · 네트워크 0 · 세션 로그 직접 읽기 0 · `ctx-burn` 을 실행하지 않음(subprocess 0).
- 상수 파일은 **읽기만** 합니다(`--set` 없음). 값은 사람이 채웁니다.

## 요구사항

- python3 3.8 이상 · 표준 라이브러리만
- macOS · Linux
- 입력: `ctx-burn --json` 출력([ctx-burn](../ctx-burn/README.ko.md) 팩)
- 값을 채운 상수 파일(`accounts.env.example` 에서 복사) · API 키 · 네트워크 없음

## 링크

- [accounts.env.example](accounts.env.example) — 상수 파일 견본(값은 비어 있음)
- [docs/plan-cost-table.md](docs/plan-cost-table.md) — Claude Opus 5.5 구독 요금제 vs API 비용(하루 기준) 표
- [ctx-burn](../ctx-burn/README.ko.md) — `ctx.v1` 을 내는 짝 도구(쓴 양 측정)
- [AI Feature Pack 카탈로그](../../README.ko.md)
