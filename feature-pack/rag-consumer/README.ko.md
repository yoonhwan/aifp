<div align="center">

# rag-consumer

**에이전트 대화 기록을 명시적으로 등록한 것만 읽어 `rag` 엔진에 넣고, 검색 · 기억 · 백업을 맡는 짝 팩 (CLI `ai-rag-consumer`)**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- 설정 파일에 경로를 적어 등록한 Codex rollout JSONL 파일만 읽습니다. 세션을 스스로 찾지 않고, 폴더를 감시하지 않습니다.
- 읽은 위치(바이트 범위 · checksum)를 암호화된 SQLCipher 장부에 남겨, 중간에 멈춰도 이어서 읽습니다. 메시지 본문을 장부에 쌓아 두지 않습니다.
- 저장하기 전에 버전이 붙은 가림 규칙(redaction)을 적용합니다. 규칙을 통과하지 못하면 쓰지 않습니다.
- 대화 구간을 `rag` 엔진에 발행해 `search` 로 찾습니다. 지난 대화는 검색과 따로 둔 불변 암호화 archive 에 묶고 `archive-search` 로 찾습니다.
- 선택: 대화에서 기억 후보를 뽑고, 원문 인용과 맞춰 본 뒤 사람이 확정 · 거절 · 검증합니다.
- 저장소 암호화 백업과 백업 검증.
- 한 번에 한 번만 도는 `tick` 을 launchd 나 macOS 메뉴 막대 앱(AIRAG.app)이 5분마다 부릅니다.

## 빠른 시작

```bash
cd feature-pack/rag-consumer
uv venv --python 3.13
uv pip install ../rag .                     # rag 팩(ai-feature-rag)과 이 팩을 함께 설치

# 저장소 키 3개 + rag DB 키 — 64자리 hex, 서로 달라야 함 (런타임은 키를 만들지 않음)
export AIRAG_CONSUMER_KEY_HEX=<64-hex> AIRAG_PROJECTION_KEY_HEX=<64-hex> AIRAG_ARCHIVE_KEY_HEX=<64-hex>
export AIRAG_PROFILE_SOURCE_KEY_HEX=<64-hex>

.venv/bin/ai-rag-consumer --config /abs/path/runtime.json init
.venv/bin/ai-rag-consumer --config /abs/path/runtime.json run --once
.venv/bin/ai-rag-consumer --config /abs/path/runtime.json search "query"
```

## 설치

### INSTALL.md 없음

이 팩에는 아직 `INSTALL.md` 도 README 원문도 없습니다. 아래 단계는 `pyproject.toml` · 소스 머리 주석 · `ops/` · `macos/` 에서 확인한 것입니다. 에이전트에게 맡길 때는 «`feature-pack/rag-consumer/README.md` 를 읽고 설치해 줘» 라고 말합니다.

### 직접 설치

패키지 이름은 `ai-feature-rag-consumer`, 진입 명령은 `ai-rag-consumer` 입니다. 의존성 `ai-feature-rag==0.1.0` 은 같은 리포의 `rag` 팩이므로 함께 설치합니다(빠른 시작의 `uv pip install ../rag .`).

1. 키 4개를 비밀 저장소에 만들어 둡니다(각 32바이트 = 64자리 hex · 서로 다름).
2. `runtime.json` 을 씁니다(아래 «런타임 설정»). 경로는 모두 절대 경로여야 하고 심링크는 거절합니다.
3. `init` 으로 장부 · projection DB · archive · 백업 폴더를 만듭니다.
4. `run --once` 로 한 번 돌려 보고, 아래처럼 주기 실행을 붙입니다.

### 5분마다 돌리기

```bash
# A) launchd — 템플릿의 __PYTHON__ · __CONFIG__ · __CREDENTIALS__ · __LOG_DIR__ 를 채워서
cp ops/com.airag.consumer.plist.template ~/Library/LaunchAgents/com.airag.consumer.plist
launchctl load ~/Library/LaunchAgents/com.airag.consumer.plist

# B) 메뉴 막대 앱 AIRAG.app — Xcode 없이 swiftc 만 필요
bash macos/build.sh            # 빌드 + 서명 (서명 이름이 없으면 ad-hoc)
bash macos/build.sh test       # 순수 로직 시험 (앱은 켜지 않음)
bash macos/build.sh install    # ~/Applications/AIRAG.app 에 복사
```

- tick 하나 = consumer 1회 통과입니다. 다시 시도는 launchd 의 다음 주기가 맡습니다.
- 키는 `--credentials` 로 준 로컬 설정 파일에서 채웁니다(1Password CLI `op` 또는 소유자만 읽는 키 파일). 이미 환경 변수에 있는 키가 이깁니다.
- AIRAG.app 은 메뉴에서 로그인 항목으로 스스로 등록합니다. 경로는 `~/.config/airag/app.json` 의 `python` · `config` · `credentials` · `log_dir` 로 바꿉니다.

## 사용법

### 명령

모든 명령은 `ai-rag-consumer --config <runtime.json> <명령>` 꼴이고 JSON 한 줄을 냅니다.

| 명령 | 하는 일 |
|---|---|
| `init` | 장부 · projection DB · archive · 백업 폴더를 만든다 |
| `run [--once] [--task-completed] [--save] [--allow-gaps]` | 등록한 소스를 읽어 발행 · `--once` 가 없으면 `poll_seconds` 마다 되풀이 (Ctrl-C 로 멈춤) |
| `status` | 지금 상태 |
| `search "<query>" [--limit N]` | 발행한 대화 검색 (기본 5) |
| `archive-search "<query>" [--limit N]` | archive 검색 (기본 20) |
| `memory-candidates --state <state> [--limit N] [--skip N]` | 기억 후보 목록 |
| `memory-confirm` · `memory-reject` · `memory-verify <candidate_id>` | 기억 후보 확정 · 거절 · 검증 |
| `backup` | 암호화 백업 만들기 |
| `verify <backup_id>` | 백업 검증 |

`python -m airag_consumer.tick --config <runtime.json> [--credentials <file>] [--log-dir <dir>]` 는 1회 통과용 진입점입니다(종료 코드 0 ok · 10 skipped · 20 config · 30 key · 40 runtime · 50 internal).

### 런타임 설정

`runtime.json` (`schema_version` = 1) 의 필수 항목:

| 항목 | 뜻 |
|---|---|
| `project_root` | 프로젝트 폴더 (절대 경로 · 있어야 함) |
| `owner_id` · `tenant_id` · `project_id` | 식별자 (영문 · 숫자 · `_` · `-`) |
| `consumer_db` · `projection_db` | 장부 DB · projection DB 경로 |
| `archive_root` · `backup_root` | archive · 백업 폴더 |
| `profile_source_db` · `profile_key` | 처리 프로필을 가진 `rag` DB 와 그 `profile_key` (64자리 hex) |
| `collection` | 발행할 `rag` collection 이름 |
| `sources` | 읽을 파일 목록 — 항목마다 `path` · `session_id` · `source_id` |

선택 항목: `token_mode`(기본 `estimated`) · `allow_gaps` · `memory_enabled` · `memory_endpoint` · `memory_model` · `poll_seconds`(기본 30) · `reference`.

### 환경 변수 키

| 이름 | 쓰임 |
|---|---|
| `AIRAG_CONSUMER_KEY_HEX` | 장부 DB 키 |
| `AIRAG_PROJECTION_KEY_HEX` | projection DB 키 |
| `AIRAG_ARCHIVE_KEY_HEX` | archive 키 |
| `AIRAG_PROFILE_SOURCE_KEY_HEX` | `profile_source_db`(rag DB) 키 · 저장소를 처음 만들 때 필요 |
| `AIRAG_MEMORY_API_KEY` | 선택 · 기억 추출 서버 키 |

키는 모두 64자리 hex 이고 서로 달라야 합니다. 런타임은 관계없는 자식 프로세스에 이 값들을 넘기지 않습니다.

## 요구사항

- Python 3.13 이상 3.15 미만 · `uv`
- `rag` 팩 (`ai-feature-rag` 0.1.0) · `sqlcipher3` 0.6.2
- 주기 실행: macOS launchd, 또는 AIRAG.app 빌드용 `swiftc`
- 선택: 1Password CLI `op` (tick 키 공급원) · 기억 추출 서버 (`memory_endpoint` · `memory_model`)
- API 키 · 계정: 기억 추출을 켤 때만 `AIRAG_MEMORY_API_KEY`

## 링크

- [rag](../rag/README.ko.md) — 이 팩이 쓰는 암호화 RAG 엔진
- [ops/com.airag.consumer.plist.template](ops/com.airag.consumer.plist.template) — launchd 템플릿
- [macos/build.sh](macos/build.sh) — AIRAG.app 빌드 · 시험 · 설치
- [AI Feature Pack 목록](../../README.ko.md)
