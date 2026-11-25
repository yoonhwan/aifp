<div align="center">

# headroom

**AI 코딩 에이전트의 컨텍스트를 LLM 에 닿기 전에 압축하는 로컬 프록시 — `ANTHROPIC_BASE_URL` 한 줄, 코드 변경 0.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- 오픈소스 `headroom-ai` 프록시를 에이전트와 LLM API 사이에 둡니다. 클라이언트는 `ANTHROPIC_BASE_URL`(또는 `OPENAI_BASE_URL`)만 바꾸면 됩니다.
- 내용 종류(JSON · 코드(AST) · 산문)를 나눠 따로 압축합니다. 원본은 로컬에 두고 모델에는 압축본과 `headroom_retrieve` 복원 통로를 줍니다.
- 압축 출력을 결정론적으로 맞춰 prefix 캐시 키를 지킵니다(`token` 모드에서 `cache_bust_count: 0`).
- 래퍼 `claude-hr.sh` 가 headroom(:8790, 압축)과 cliproxy(:8317, 멀티계정 회전) 두 레이어를 프로젝트마다 따로 켜고 끕니다. 경유를 요청한 레이어가 죽어 있으면 직결로 새지 않고 멈춥니다.
- Claude Code 토글 스킬 `/headroom on|off|status` 와 `headroom-ai==0.33.x` 용 운영 패치(`patches/apply.sh`)를 함께 줍니다.
- 효과는 긴 세션 · 같은 파일을 여러 번 읽는 작업에서만 쌓입니다. 짧은 단발 입력에는 효과가 없습니다.

## 빠른 시작

```bash
# 리포 루트에서
python3.12 -m venv ~/.headroom-venv
~/.headroom-venv/bin/pip install "headroom-ai==0.33.0"
bash feature-pack/headroom/patches/apply.sh

# 프록시 기동 (압축 + 캐시 공존 · 텔레메트리 off)
HEADROOM_MODE=token HEADROOM_COMPRESS_USER_MESSAGES=1 HEADROOM_CODE_AWARE_ENABLED=1 HEADROOM_TELEMETRY=off \
  ~/.headroom-venv/bin/python -m headroom.proxy.server \
  --port 8790 --compress-user-messages --exclude-tools Bash --code-aware

# 다른 셸에서: 확인 후 세션 하나만 프록시로 띄운다 (전역 export 는 하지 않는다)
curl -s localhost:8790/health
ANTHROPIC_BASE_URL=http://localhost:8790 claude
```

## 설치

이 팩에는 `INSTALL.md` 가 없습니다. 에이전트에게 맡길 때는 «`feature-pack/headroom/README.md` 를 읽고 headroom 과 토글 스킬을 설치해 줘» 라고 하면 됩니다. 이 README 의 에이전트 절차는 켤 프로젝트를 사용자에게 먼저 묻고, 자동으로 켜지 않습니다. 손으로 할 때는 아래 3단계를 리포 루트에서 합니다.

### 1. headroom-ai 설치

ML extras(`headroom-ai[ml]` · `[all]`, Kompress)는 캐시 안정성 · 메모리 비용 때문에 기본 설치에서 뺍니다.

```bash
python3.12 -m venv ~/.headroom-venv
~/.headroom-venv/bin/pip install "headroom-ai==0.33.0"
~/.headroom-venv/bin/headroom --version       # 0.33.0
```

### 2. 운영 패치 적용

`apply.sh` 는 설치된 버전을 보고 패치를 고르며(0.33.x 에는 0009, 그 밖의 호환 버전에는 0006), 여러 번 돌려도 같습니다. 기본 Python 은 `~/.headroom-venv/bin/python` 이고 첫 인자로 바꿀 수 있습니다.

```bash
bash feature-pack/headroom/patches/apply.sh   # [/path/to/venv/bin/python]
```

### 3. 토글 스킬과 래퍼 설치

```bash
HR_DIR="$PWD/feature-pack/headroom"
mkdir -p ~/.claude/skills/headroom ~/.headroom
cp "$HR_DIR/SKILL.md" ~/.claude/skills/headroom/SKILL.md
cp "$HR_DIR/templates/claude-hr.sh" ~/.headroom/claude-hr.sh
mkdir -p ~/.claude/skills/headroom-cliproxyapi/scripts
cp "$HR_DIR/scripts/file-logs.sh" ~/.claude/skills/headroom-cliproxyapi/scripts/file-logs.sh
cp "$HR_DIR/scripts/clean-proxy-logs.sh" ~/.claude/skills/headroom-cliproxyapi/scripts/clean-proxy-logs.sh
cp "$HR_DIR/scripts/file-logs.sh" ~/.headroom/headroom-cliproxy-file-logs.sh
cp "$HR_DIR/scripts/clean-proxy-logs.sh" ~/.headroom/clean-proxy-logs.sh
# 라우팅 상태 파일 — 기본은 둘 다 off(직결)
[ -f ~/.headroom/routing.json ] || cp "$HR_DIR/templates/routing.json" ~/.headroom/routing.json
chmod +x ~/.headroom/claude-hr.sh ~/.headroom/headroom-cliproxy-file-logs.sh ~/.headroom/clean-proxy-logs.sh ~/.claude/skills/headroom-cliproxyapi/scripts/*.sh
```

그다음 `~/.zshrc` 에 `alias claude-hr='~/.headroom/claude-hr.sh'` 를 넣고 `claude-hr` 로 실행합니다.

## 사용법

### 라우팅 스위처 (`claude-hr.sh`)

| headroom | cliproxy | `ANTHROPIC_BASE_URL` |
|---|---|---|
| on | on | `http://localhost:8790` — 압축 → 회전 → 구독 |
| off | on | `http://127.0.0.1:8317` — 회전 → 구독, 압축 생략 |
| off | off | unset — Anthropic 직결 |
| on | off | 불가 — headroom LaunchAgent 의 upstream 이 `127.0.0.1:8317` 로 고정돼 있어 래퍼가 exit 78 로 거부 |

```bash
HR=~/.headroom/claude-hr.sh
$HR route status                    # 이 프로젝트의 유효값 + 프로세스 실제 상태
$HR route headroom on|off           # 이 프로젝트만
$HR route cliproxy on|off
$HR route headroom on --global      # 전 프로젝트 기본값
$HR route reset [--global]
```

상태 파일은 `~/.headroom/routing.json` 하나입니다. 손으로 고치지 말고 `route` 로 바꿉니다.

```json
{
  "default":  { "headroom": false, "cliproxy": false },
  "projects": { "/abs/project/root": { "headroom": true, "cliproxy": true } }
}
```

- 프로젝트 항목이 있으면 그것, 없으면 `default` 를 씁니다. 파일이 없으면 직결입니다.
- 프로젝트 root 는 `git --git-common-dir` 기준이라 worktree 도 본 프로젝트 하나로 접힙니다.
- 1회성 오버라이드: `HEADROOM_ROUTE=0|1` · `CLIPROXY_ROUTE=0|1` 환경 변수가 설정보다 먼저입니다.
- 경유를 요청한 레이어가 죽어 있으면 exit 69 로 멈춥니다(조용한 폴백 0).
- `--model` 이 cliproxy 카탈로그에 없으면 기동 전에 stderr 로 경고합니다(막지는 않음).
- Claude Code 안에서는 스킬로 `/headroom on` → `route headroom on` · `/headroom off` → `route headroom off` · `/headroom status` → `route status` 입니다.
- 환경 변수는 프로세스 시작 때 굳습니다. 이미 떠 있는 세션은 다시 띄워야 반영됩니다. tmux · 오케스트레이터가 띄우는 세션까지 태우려면 평소 쓰는 claude alias 를 래퍼로 바꿉니다(예: `alias cc='~/.headroom/claude-hr.sh --model "..."'`).

### 프록시 기동

```bash
HEADROOM_MODE=token HEADROOM_COMPRESS_USER_MESSAGES=1 HEADROOM_CODE_AWARE_ENABLED=1 HEADROOM_TELEMETRY=off \
  ~/.headroom-venv/bin/python -m headroom.proxy.server \
  --port 8790 --compress-user-messages --exclude-tools Bash --code-aware
```

- `headroom proxy`(click)는 옵션이 적습니다. `python -m headroom.proxy.server` 를 직접 돌려야 다 고를 수 있습니다. 이때는 `--no-telemetry` 대신 `HEADROOM_TELEMETRY=off` 를 씁니다.
- 모드: `cache` = prefix 고정 · 관찰만(압축 ~0%) · `token` = 공격 압축 + 캐시 공존(재독 25~30%).
- 8790 이 이미 LISTEN 이면 새로 띄우지 말고 그것을 씁니다. 여러 세션이 각자 띄우면 `Errno48 Address already in use` 크래시 루프가 납니다. 스킬의 `on` 은 이를 지킵니다.

### 다른 에이전트

`headroom wrap <agent>` 가 프록시 기동과 에이전트 실행을 한 번에 합니다.

```bash
headroom wrap claude        # Claude Code (ANTHROPIC_BASE_URL)
headroom wrap codex         # Codex
headroom wrap cursor        # Cursor — 설정을 출력, 1회 붙여넣기
headroom wrap aider         # Aider
headroom wrap copilot       # GitHub Copilot CLI
headroom proxy --port 8790  # 그 밖의 OpenAI 호환 클라이언트: OPENAI_BASE_URL=http://localhost:8790/v1
```

Codex 를 cliproxy 와 함께 쓸 때는 `headroom wrap codex` 대신 Codex custom provider 로 고정합니다. 그래야 `codex` · `codex exec` · tmux 가 모두 같은 경로를 탑니다. 인증은 cliproxy OAuth 가 하므로 `CODEX_DUMMY_API_KEY` 는 더미 값이면 됩니다.

```toml
# ~/.codex/config.toml
model_provider = "headroom"

[model_providers.headroom]
name = "Headroom"
base_url = "http://127.0.0.1:8790/v1"
env_key = "CODEX_DUMMY_API_KEY"
wire_api = "responses"
```

그 밖의 설치 채널은 `npm install headroom-ai` · `docker pull ghcr.io/chopratejas/headroom:latest` 이고, 상주 서비스는 `headroom install apply --preset persistent-service --providers auto` 입니다.

### 동작 확인 (`/stats`)

```bash
curl -s localhost:8790/health        # status healthy
curl -s localhost:8790/stats         # 압축률 + cache_bust_count (0 이어야 정상)
```

| 지표 | 뜻 |
|---|---|
| `avg_compression_pct` | 압축이 얼마나 걸렸나 |
| `cache_bust_count` | 0 을 지켜야 합니다. 0 보다 크면 캐시가 깨진 것 = 손해 |
| `cache_write_1h_tokens` | 1h extended 캐시를 쓰는지 |

`/stats` 의 `api_req` 가 0 에서 늘면 실제로 경유가 시작된 것입니다.

### 개인정보

- 프롬프트 · 코드 · 크레덴셜은 밖으로 나가지 않습니다(의도한 upstream 으로만 감).
- 익명 사용량 텔레메트리가 기본으로 켜져 있습니다(5분마다 집계 통계만). 끄려면 `HEADROOM_TELEMETRY=off` 를 씁니다(위 기동 명령에 들어 있음).
- `learn` · `memory` 는 기본 off 입니다. 끈 채로 둡니다.
- 공급망 주의: 번들 RTK 바이너리, 기동 때 huggingface.co 에서 모델을 받습니다.

### 알려진 한계

| 경로 | 압축률 |
|---|---|
| 라이브러리 직접 호출(`compress_user_messages=True`) | 83.7% |
| 라이브 프록시 — 단발 read | 0% |
| 라이브 프록시 — 재독 / supersede | 25~30% (최고 30.7%) |

- 단발 0% 는 설계입니다. `DEFAULT_EXCLUDE_TOOLS = {Read,Bash,Grep,Glob,Edit,Write}` 와 `protect_recent`(기본 4)가 표준 도구 결과와 최근 메시지를 지킵니다.
- 가역 압축은 컨텍스트 안에서는 lossy 입니다. 디버깅 작업에서는 `headroom_retrieve` 복원이 맞는지 따로 봅니다.
- 수치는 환경 · 버전(v0.33.0)에 따라 다를 수 있습니다.

### 문제 해결

- `400 messages.N: user messages must have non-empty content` — 압축이 빈 문자열을 돌려준 경우입니다. `patches/apply.sh` 의 빈값 가드가 막습니다. 임시로는 기동 명령에서 `--compress-user-messages` 를 뺍니다.
- 큰 요청에서 500 · `compression_first_stage` RuntimeError — tree-sitter 파서를 스레드끼리 나눠 쓰다 난 panic 입니다. `patches/apply.sh` 가 고칩니다. 로그에 `pyo3_runtime.PanicException: _native::Parser is unsendable` 이 보이면 이 경우입니다.
- 모든 세션이 `API Error: Connection refused` — 프록시(8790)가 죽은 것입니다. 프록시를 거치지 않는 셸에서 다시 띄우고, 멈췄던 세션은 같은 입력을 다시 보냅니다.

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.headroom.proxy.plist 2>/dev/null
launchctl enable    gui/$(id -u)/com.headroom.proxy
launchctl kickstart -k gui/$(id -u)/com.headroom.proxy
curl -sf -m1 http://localhost:8790/health
```

- 예방: `ANTHROPIC_BASE_URL` 를 셸 전역에 export 하지 않습니다. 프록시가 죽으면 모든 세션이 한꺼번에 멈춥니다. 래퍼로 띄웁니다.

## 요구사항

- Python 3.12(`python3.12 -m venv`) · `headroom-ai==0.33.0`
- zsh(`claude-hr.sh`) · bash · python3 · curl
- 상주 서비스 · 복구 명령은 macOS LaunchAgent(`launchctl`) 기준입니다.
- cliproxy(:8317)는 이 팩에 들어 있지 않습니다. headroom + cliproxy 경로를 쓰려면 따로 띄워야 합니다.
- API 키 · 계정: 쓰는 에이전트의 기존 인증을 그대로 씁니다.

## 링크

- [SKILL.md](SKILL.md) — `/headroom` 토글 스킬
- [patches/README.md](patches/README.md) — 버전별 운영 패치와 원인
- [SSOT.md](SSOT.md) — 컨텍스트 비용 구조 정리
- [NOTES.md](NOTES.md) — 패치 노트
- [AI Feature Pack 카탈로그](../../README.ko.md)
