<div align="center">

# tmm

**폰(SSH)에서 수십 개의 tmux 에이전트 좌석을 고르고, 붙지 않고 미리 보고, 메시지를 보내는 한 화면 TUI**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- tmux 세션 하나를 좌석 한 줄로 보여 줍니다 — 분류 · 에이전트 실행 여부 · 상태 · 모델 · 마지막 메시지 시각 · 경과 · 폴더. 퍼지 필터로 좁힙니다.
- 사람 입력을 기다리는 좌석(`HUMAN` · `BLOCK` · `STUCK`)을 맨 위로 올리고, 새로 생기면 터미널 벨을 울립니다.
- 붙지 않고 pane 을 미리 봅니다. `Enter` 로 attach, `C-a d` 로 떼면 피커로 돌아옵니다.
- `^S` 로 커서 좌석에 메시지를 보내고 도달을 확인합니다 · `^K` 로 좌석을 닫습니다.
- `^D` 종료된 세션 뷰: 재부팅 · kill 로 사라진 에이전트 세션을 트랜스크립트에서 찾아 resume 으로 복구합니다.
- `^F` fork 로 대화를 다른 에이전트로 이어받고, `^Y` 로 대화 기록(트랜스크립트) 경로를 봅니다.

`tmuxc` 로 띄운 Claude Code · Codex · OMX · OpenCode · Command Code · Pi 좌석을 전제로 만들었지만 일반 tmux 세션에도 그대로 씁니다.

## 빠른 시작

```bash
brew install bash tmux fzf               # 없으면 (bash 4 이상 필요)
bash feature-pack/tmuxc/install.sh       # 필수 팩 tmuxc 먼저
bash feature-pack/tmm/install.sh
tmm doctor                               # 의존성 · 환경 점검
tmm                                      # TUI 열기
```

## 설치

### 에이전트에게 맡기기

에이전트에게 «`feature-pack/tmm/INSTALL.md` 를 읽고 설치해 줘» 라고 말합니다. 에이전트가 사전 요구 확인 → `install.sh` → 카테고리 규칙 → 검증 → (선택) fork 모델 별칭 · 폰 연결 차례로 진행합니다. 설치 시간 (~1분).

### 직접 설치

`install.sh` 가 하는 일:

1. `bash>=4` · `tmux` · `fzf` 를 확인합니다(없으면 exit 2 와 설치 명령 안내). `tmuxc` 가 없으면 중단합니다.
2. 본체 · libexec 를 `~/.tmm/versions/<version>/core/` 에 복사하고 `~/.tmm/current` 심링크를 바꿉니다.
3. `~/.local/bin/tmm` 심링크를 만들고(기존 일반 파일은 백업), `~/.local/bin` 이 PATH 에 없으면 `~/.zshrc` / `~/.bashrc` 에 넣습니다.
4. `~/.zshrc` 에 `alias tmm=` 이 있으면 경고합니다(alias 가 바이너리를 가로챔).
5. `~/.tmm/categories` · `~/.tmm/models` 가 없으면 예시를 복사하고(있으면 보존) `~/.tmm/forks/` 를 만듭니다.
6. `tmm doctor` 로 검증합니다.

```bash
bash feature-pack/tmm/install.sh
tmm doctor
tmm ls | head                          # 상태 열이 ? 면 seat-scan 경로 확인 → TMM_SCAN
bash feature-pack/tmm/test/verify.sh   # 격리 tmux 소켓에서 회귀 시험 (기존 세션 무접촉)
bash feature-pack/tmm/uninstall.sh     # 제거 (~/.tmm/categories 는 보존)
```

### 카테고리 규칙

`~/.tmm/categories` 에 `글롭<TAB>라벨` 을 한 줄씩 적습니다. 위에서부터 첫 매치가 이깁니다. 규칙에 안 걸리면 역할 접두(`TMM_CAT_STRIP`, 기본 `FB_ ft-`)를 뗀 세션명의 첫 토큰(`-` / `_` 앞 5자)이 라벨이 되므로, 규칙 파일에는 일반화로 안 되는 것(별칭 병합 · 대소문자 통일)만 적으면 됩니다. 소문자 · 숫자 · `-` 로 된 `<프로젝트>-<팀>-<역할>…` 이름은 셋째 토큰이 역할 예약어(master · arch · da · tester · checker · analyst · pm · nano · repro · tool)면 둘째 토큰(팀)이 라벨입니다.

```bash
tmux ls -F '#S' | sed 's/#[0-9]*$//' | sort -u     # 지금 세션 접두 목록 보기
```

### 폰 접속 (Termius 예)

1. Mac: 시스템 설정 → 일반 → 공유 → 원격 로그인 켜기.
2. 전용 키를 만들어 공개키를 `~/.ssh/authorized_keys` 에 넣고, 개인키는 비밀번호 관리자에 보관한 뒤 폰 Termius Keychain 에 붙여 넣습니다.
3. 주소: 같은 Wi-Fi 면 `ipconfig getifaddr en0`, 밖에서는 `tailscale ip -4`(Tailscale 권장).
4. Termius 호스트: 주소 · 포트 22 · 사용자 · 키 · **Startup command = `tmm`** — 접속하자마자 피커가 뜹니다.
5. 폰 키보드 툴바의 Ctrl 로 `^S` 등을 누릅니다. tmux prefix 가 `C-a` 면 Ctrl → a → d 로 뗍니다.

```bash
ssh-keygen -t ed25519 -f ~/.ssh/mobile_ed25519 -N ''
cat ~/.ssh/mobile_ed25519.pub >> ~/.ssh/authorized_keys
# 데스크탑에서 자가 시험 — 비대화 ssh 는 PATH 가 짧아 zsh -ilc 로 감싼다
ssh -i ~/.ssh/mobile_ed25519 -o IdentitiesOnly=yes <IP> -t 'zsh -ilc tmm'
```

## 사용법

### 한 줄 = 한 좌석

| 열 | 뜻 |
|---|---|
| 카테고리 | `~/.tmm/categories` 규칙, 없으면 역할 접두를 뗀 세션명 첫 토큰 |
| `●` / `○` | 에이전트 실행 중 / 셸만 있음 |
| 세션명 | tmux 세션명. 창 폭에 따라 20~44칸 · 잘릴 때는 가운데를 접고 끝의 `#N` 을 남김 |
| `HUMAN` `BLOCK` `STUCK` `IDLE` `BUSY` | seat-scan 판정. HUMAN = 사람 입력 대기, BLOCK = API 오류로 멈춤, STUCK = 제출 안 된 입력이 남음 |
| 모델 | 쓰는 모델의 줄임 이름(예: `opus5·1m`). `·1m` = 1M 컨텍스트 창 |
| `12:33` / `12~33` | 마지막 메시지 시각. `:` = Claude 완료 마커에서 읽음, `~` = 마커가 없어 tmux 마지막 출력 시각 |
| `26m` | 지금까지 경과 (m / h / d) |
| 폴더 | pane cwd 의 마지막 폴더. 창 폭에 따라 6~28칸 |

정렬: `^T` 최근순(기본 — 가장 최근에 말한 좌석이 맨 위) · `^W` 대기 좌석을 위에 고정한 뒤 최근순 · `^G` 카테고리 묶음 안에서 최근순 · `^H` 대기 좌석만.

### 키

| 키 | 동작 |
|---|---|
| ↑↓ / 타이핑 | 커서 이동 / 퍼지 필터 (`HUMAN`, 세션명 일부 …) |
| `Enter`(분류 칸) · `Esc` / `⌫`(목록, 질의가 비었을 때) | 칸 이동 — 분류 칸 ↔ 목록. `→` / `←` 도 같음 |
| `Enter`, `^E`, 더블탭 | attach. `C-a d` 로 떼면 피커로 돌아옴 |
| `^S` | 커서 좌석에 메시지 — `[mobile→세션명] …` 접두 + 2초 뒤 도달 확인. 에이전트 없는 좌석은 막음 |
| `^K` | 좌석 닫기 (tmux 세션 + 그 안의 에이전트) |
| `^F` | fork — 대화를 새 에이전트 세션으로 이어받기 |
| `^Y` | 대화 기록 인덱스 — 커서 세션의 트랜스크립트 경로 표시 |
| `^H` / `^A` | 대기 좌석만 / 전체 |
| `^T` / `^W` / `^G` | 최근순 / 대기 우선 / 카테고리순 |
| `^V` | 분류 칸 숨김 / 보임 (숨기면 탭 줄 — `Tab` / `S-Tab` 으로 회전) |
| `^R` | 상태 다시 스캔 (캐시 무시 · 정렬 · 필터 유지) |
| `^U` | 미리보기 자동 갱신 주기 순환 1 → 5 → 10 → 15초 |
| `^P` / `^O` | 미리보기 끄기 · 켜기 / 크게 · 작게 |
| `^D` / `^A` | 종료된 세션 뷰 ↔ 살아 있는 좌석 뷰 |
| `^/` | 도움말(헤더) 다시 그리기. `?` 는 필터 글자 |
| `^X` | 끝 |

### 분할 화면

- tmux 안에서는 왼쪽 = 분류 칸, 오른쪽 = 세션 목록(+ pane 미리보기)입니다. 분류 칸에서 ↑↓ 로 고르면 오른쪽 목록이 바로 바뀝니다.
- `tmm` 을 인자 없이 실행하면 `tmm` 이라는 tmux 세션 안에서 피커가 뜹니다 — 터미널 창 크기를 바꿔도 피커가 죽지 않습니다. 창을 여러 개 열면 각자 피커(`tmm`, `tmm-2` …)를 갖습니다.
- 폭 120열 미만(폰)은 분류 칸 11칸, 이상은 16칸입니다. 목록 칸이 120열 이상이면 미리보기가 오른쪽에, 아니면 아래에 붙습니다.
- 미리보기는 최신 내용이 먼저 보이고, 바닥의 입력 상자 · statusline 을 잘라 폰 화면을 아낍니다.
- `TMM_SPLIT=0` 이거나 tmux 밖이면 탭 줄 화면이 됩니다.

### 종료된 세션 뷰 (`^D`)

지금 tmux 에 없는 에이전트 세션으로 목록이 바뀝니다. `tmuxc` 로 띄웠든 터미널에서 직접 돌렸든 트랜스크립트가 남아 있으면 잡습니다.

| 키 · 표시 | 뜻 |
|---|---|
| `◌` | 종료됨 |
| 배지 | 어디서 찾았나: `SNAP` = `tmuxc save` 스냅샷(저장 때 argv 그대로) · `CC` Claude · `CDX` Codex · `CMD` Command Code · `OC` OpenCode |
| `^]` / `^\` | 창을 12시간씩 넓힘 / 좁힘 (진입 때 최근 12시간 · 판정 = 트랜스크립트 mtime) |
| `^L` | 계보 전체 세대 보기 (기본은 최신 세대만) |
| `^T` / `^W` / `^G` | 최근순 / SNAP 우선 / 카테고리 |
| `Enter` | 복구 — 원래 cwd 에 tmux 세션을 만들고 `--resume <session_id>` 로 에이전트를 다시 띄운 뒤 attach |
| `^B` | 선택 복구 모드 — 보이는 행이 전부 체크된 채 들어가고, 스페이스로 체크를 바꾸고, `^B` 를 한 번 더 누르면 체크된 것만 복구 (5개씩 배치 병렬 · attach 없음) |

- 미리보기는 그 세션의 마지막 user / assistant 메시지를 보여 줍니다.
- 복구 모델: SNAP 이면 스냅샷 argv 그대로, 아니면 트랜스크립트의 `model` + `--effort high`. Claude 는 fable 계열이 아니면 1M 창(`[1m]`)을 붙입니다.
- Pi 세션은 `tmuxc save` 스냅샷이 있을 때 복구합니다. `--scan` 은 Claude · Codex 만 지원합니다.
- `^S`(메시지)는 이 뷰에서 쓸 수 없습니다. 먼저 복구합니다.

### fork (`^F` · `tmm fork`)

살아 있거나 종료된 세션의 대화를 다른 에이전트 · 모델로 옮겨 이어갑니다(레이트 리밋 등). 소스 대화는 건드리지 않습니다.

- 같은 엔진 = `tmuxc fork` 네이티브 분기 — 전체 히스토리 그대로, 새 conversation id.
- 다른 엔진 = `tmuxc open` 새 세션 + 컨텍스트 주입 — 트랜스크립트 경로와 최근 대화 발췌(`~/.tmm/forks/<시각>-<소스>.md`)를 프롬프트로 줍니다.
- `^F` 에서 이름 · 에이전트(claude / codex / opencode / cmd) · 모델(fzf 검색)을 고르면 만든 뒤 피커로 돌아옵니다. 이름 기본값은 소스의 `#N` → `#N+1`. 어느 단계에서든 `^C` 로 취소합니다.
- 모델 별칭 = `~/.tmm/models`(사용자 · 우선) + `~/.tmm/models.generated`(`tmm models refresh` 생성본). OpenCode 는 `--model` 접두사가 곧 게이트웨이라 `TMM_MODELS_PROVIDER`(기본 `openrouter`)로 고릅니다 — `opencode/` = zen, `openrouter/` = OpenRouter.
- Claude 는 fable 계열이 아니면 `--ctx 1m` 이 자동으로 붙습니다.

```bash
# --dry-run 은 명령만 보여 줌 (부작용 없음)
tmm fork my-app-dev#1 --agent codex --model <alias> --dry-run
tmm fork my-app-dev#1 --agent claude --model sonnet --attach     # 같은 엔진 네이티브 fork
tmm models refresh                                    # 라이브 목록 → ~/.tmm/models.generated
TMM_MODELS_PROVIDER=opencode tmm models refresh opencode
tmm models find <query>                               # 별칭 · 모델 id 검색
```

### 대화 기록 인덱스 (`^Y` · `tmm idx`)

- `^Y` 는 커서 세션의 `agent · session_id · cwd · transcript · match` 를 화면에 보여 줍니다(아무 키로 복귀). 에이전트에게 «이전 대화는 이 파일» 이라고 바로 알려 줄 때 씁니다.
- `tmm idx NAME|SID` 는 같은 정보를 CLI 로 냅니다 · `--path` = 경로만 · `--json` = JSON.
- `match`: `exact`(이름 정확 매치) · `cwd`(cwd 기반) · `fallback`(살아 있는 세션의 최근 활성 파일).

### 자동 갱신

| 단 | 무엇을 | 기본 주기 |
|---|---|---|
| pane | 커서 좌석 미리보기만 다시 그림 | 1초 (`^U` 로 1/5/10/15 순환 · `TMM_AUTO_PREVIEW`) |
| 전체 좌석 | 상태 · 마지막 시각 · 정렬 다시 계산 | 20초 고정 (`TMM_AUTO`) |

attach 중에는 멈추고 `C-a d` 로 떼면 다시 돕니다. 갱신돼도 커서는 보던 좌석을 따라가고 필터도 남습니다.

### CLI 하위 명령

```bash
tmm                 # TUI
tmm --auto N        # TUI, 미리보기 자동 갱신 N초 (0=off)
tmm ls [PAT]        # 텍스트 목록 (필터)
tmm h               # HUMAN/BLOCK/STUCK 좌석만
tmm p NAME [N]      # pane 최근 N줄
tmm s NAME "msg"    # 메시지 (가드 + 도달 확인)
tmm a NAME [-i]     # attach (-i: 데스크탑 창 크기 고정)
tmm kill NAME [--yes]                 # 좌석 닫기
tmm ss              # seat-scan 원본 출력
tmm save            # tmuxc save (tmuxc 필요)
tmm doctor          # 의존성 · 환경 점검
tmm menu            # fzf 가 없을 때 숫자 메뉴
tmm dead [PAT] [--since H] [--all]    # 종료된 세션 목록
tmm dp NAME|SID [N]                   # 종료 세션의 마지막 대화 N줄
tmm restore NAME [--dry-run]          # 종료 세션 1건 복구 → attach
tmm restore-all [--since H] [--dry-run] [--yes]   # 창 안 전부 복구 (attach 없음)
tmm idx NAME|SID [--json|--path]      # 트랜스크립트 경로
tmm fork SRC --agent AG --model M [--name N] [--cwd C] [--effort E] [--ctx 1m] [--prompt P] [--dry-run] [--attach]
tmm models [AG]                       # fork 모델 별칭 목록
tmm models refresh [AG...]            # 라이브 목록에서 생성본 갱신
tmm models find QUERY                 # 별칭 · 모델 id 검색
```

### 설정

| 항목 | 위치 / 변수 | 기본 |
|---|---|---|
| 카테고리 규칙 | `~/.tmm/categories` (`TMM_CATEGORIES`) | 설치 때 예시 복사 |
| 카테고리 역할 접두 | `TMM_CAT_STRIP` | `FB_ ft-` (공백 구분) |
| fork 모델 별칭 | `~/.tmm/models` (`TMM_MODELS`) | 설치 때 예시 복사 · 생성본보다 우선 |
| fork 모델 생성본 | `~/.tmm/models.generated` (`TMM_MODELS_GEN`) | `tmm models refresh` 가 만듦 · 직접 고치지 않음 |
| OpenCode 프로바이더 | `TMM_MODELS_PROVIDER` | `openrouter` |
| fork 발췌 폴더 / 메시지 수 | `~/.tmm/forks/` (`TMM_FORKS`) / `TMM_FORK_EXCERPT_N` | 40 |
| 상태 스캔 캐시 | `TMM_CACHE_TTL` | 20초 (`^R` 은 무시) |
| seat-scan 경로 | `TMM_SCAN` | 설치본 `libexec/seat-scan.sh` → `~/.claude/skills/tmuxc/scripts/seat-scan.sh` |
| 미리보기 줄 수 | `TMM_PREVIEW_LINES` | 40 |
| pane 자동 갱신 | `TMM_AUTO_PREVIEW` / `tmm --auto N` / `^U` | 1초 · 0 = off |
| 전체 좌석 자동 갱신 | `TMM_AUTO` | 20초 · 0 = off |
| 새 대기 좌석 벨 | `TMM_BELL` | 1 (0 = 끔) |
| 시작 화면 | `TMM_TAB` | 1 = 탭 뷰 · 0 = 목록 |
| 분할 화면 | `TMM_SPLIT` | 1 (tmux 안에서만) · 0 = 탭 줄 |
| 종료 뷰 진입 창 | `TMM_DEAD_SINCE` | 12 (시간) |
| 라이브 판정 여유 | `TMM_LIVE_GRACE` | 90초 — 이 안에 쓰인 트랜스크립트는 살아 있다고 봄 |
| 복구 부팅 대기 | `TMM_RESTORE_TRIES` | 20 (× 3초) |
| 선택 복구 배치 크기 | `TMM_RESTORE_BATCH` | 5 |

### 알려진 한계 · 문제 해결

- 완료 마커는 시:분만 있어 날짜가 없습니다. 이틀 넘게 둔 좌석은 경과가 작게 보일 수 있습니다.
- fzf 헤더는 줄바꿈 없이 잘리므로 폭이 좁은 폰에서는 헤더 뒤쪽이 안 보일 수 있습니다.

| 증상 | 처방 |
|---|---|
| 자동 갱신이 안 돎 · `^Y` 가 안 먹음 | `tmm doctor` 로 fzf 버전(≥ 0.54) · `curl` 확인 |
| 같은 엔진 fork 인데 히스토리가 안 이어짐 | `tmuxc` < 0.4.0 — `tmuxc` 재설치 |
| fork 모델 메뉴가 비었거나 원하는 모델이 없음 | `install.sh` 재실행(예시 복사) 또는 `tmm models refresh` → `tmm models find QUERY` |
| OpenCode fork 가 다른 게이트웨이로 열림 | 별칭 접두사 확인 · `TMM_MODELS_PROVIDER=openrouter tmm models refresh` |
| `tmm idx NAME` 이 «인덱스 없음» | `tmm idx NAME --json` 의 `match` 확인 |
| 복구 뒤 «부팅 확인 못 함» | 세션은 남아 있음 — attach 해서 pane 확인 |

## 요구사항

- macOS 또는 Linux
- `bash` ≥ 4 (macOS 기본 3.2 는 안 됨 → `brew install bash`) · `tmux` ≥ 3.2 · `fzf` ≥ 0.54 · `python3` ≥ 3.9 (표준 라이브러리만) · `curl`
- `tmuxc` ≥ 0.4.0 (`feature-pack/tmuxc`) — 없으면 `install.sh` 가 멈춥니다.
- 선택: Tailscale(집 밖 접속) · 폰 SSH 클라이언트(예: Termius)
- API 키 · 계정: 없음

## 링크

- [INSTALL.md](INSTALL.md) — 에이전트용 설치 안내
- [tmuxc 팩](../tmuxc/) — 필수 팩
- [test/verify.sh](test/verify.sh) — 회귀 시험
- [AI Feature Pack 카탈로그](../../README.ko.md)
