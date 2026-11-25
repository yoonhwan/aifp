<div align="center">

# code-intel

**에이전트 하네스 어디서나 같은 명령 `ci` 하나로 코드 검색 · 심볼 · 참조 · 구조 패턴을 찾는 코드 인텔리전스 팩**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- 의미 · 키워드 검색(BM25 + AST 완결 블록) — `ci search "<q>" <path>`
- 심볼 정의 · 호출자 · 의존성(정의 우선 정렬) — `ci sym <sym> --callers --scope <dir>`
- 파일을 읽기 전에 구조와 토큰 수를 본다 — `ci outline <file>`
- LSP 정밀 참조 · 정의 · 구현(필요할 때만 띄움) — `ci refs "<file>#<sym>"`
- ast-grep 구조 패턴 — `ci ast '<pattern>' <path> -l py`
- 에이전트가 `ci` 를 지침대로 쓰는지 준수율을 잰다 — `ci-audit --days 1 --by-harness`
- 인덱스 없음 · 상주 프로세스 0. Claude Code · Codex · OpenCode · Pi · Hermes 에서 같은 명령으로 쓴다. Serena MCP 를 대체한다.

### 왜 만들었나

파일 62k 개 · 49GB worktree 에서 잰 값입니다.

| 작업 | Serena | code-intel |
|---|---|---|
| 의미 검색 | 127.25s (빈 결과) | 4.6s (순위 매긴 결과) |
| 호출자 추적 | 4.2s+ (활성화 먼저) | 0.36s |
| 상주 메모리 | 946MB → 5.1GB 누수 (peak 21GB) | 0MB |
| 사전 절차 | activate_project + 설정 확인 | 없음 |

## 빠른 시작

```bash
# 리포 루트에서: 바이너리 + 스킬 연결 + ci 진입점 + 진단 (여러 번 돌려도 같음)
bash feature-pack/code-intel/skill/scripts/install.sh

ci doctor                                  # 설치 · 버전 · LSP · smoke
ci search "dispatch" src --max 5           # 첫 검색
```

## 설치

### 에이전트에게 맡기기

에이전트에게 «`feature-pack/code-intel/INSTALL.md` 를 읽고 설치해 줘» 라고 말합니다. 에이전트가 스킬 연결 → 바이너리 설치 → 검증 → 지침 연결까지 합니다. 설치 시간 (~3분).

### 직접 설치

`install.sh` 가 하는 일:

1. `probe`(0.6.0-rc342) · `tilth`(0.12.0) 가 있으면 그대로 두고, 없으면 `~/.local/bin` 에 설치합니다.
2. 스킬 폴더를 Claude Code · Pi/Hermes · Codex · OpenCode 스킬 루트에 심링크합니다(루트 폴더가 없는 하네스는 건너뜀).
3. `~/.local/bin/ci` 진입점을 만듭니다.
4. `ci doctor` 로 마지막 진단을 합니다.

```bash
# 변경 없이 진단만
bash feature-pack/code-intel/skill/scripts/install.sh --check

# 설치 후 확인
ci doctor                                  # probe/tilth 버전 + LSP + smoke
ci sym <any-symbol> --scope <subdir>       # 0.4초 안에 응답
ci outline <file>                          # 머리에 토큰 수
```

합격 기준: `ci doctor` 출력 + `ci sym` 응답 + `ci outline` 토큰 표시.

### 에이전트 지침에 연결하기

연결하지 않으면 에이전트가 `ci` 를 쓰지 않습니다. 하네스의 전역 지침 파일(Claude Code `~/.claude/CLAUDE.md` · Codex `~/.codex/AGENTS.md` · OpenCode `~/.config/opencode/AGENTS.md` · Pi `~/.pi/agent/AGENTS.md`)에 아래 줄을 넣습니다.

```markdown
**HARD RULE: 코드 심볼 · 참조 · 구조 탐색은 `ci` 우선. grep/rg/git grep 은 로그 · 설정 · 문자열 · 파일 존재 확인에만.
`probe`/`tilth` 직접 호출 금지 — 반드시 `ci` 경유(타임아웃 · scope 가드 내장). 사전 활성화 없음.**
```

### 되돌리기

```bash
rm ~/.claude/skills/code-intel ~/.agents/skills/code-intel \
   ~/.codex/skills/code-intel ~/.config/opencode/skills/code-intel \
   ~/.local/bin/ci ~/.local/bin/ci-audit
# probe/tilth 바이너리는 남겨도 됩니다 — 단독 CLI 로도 쓸 수 있습니다
```

## 사용법

### 명령

| 명령 | 하는 일 |
|---|---|
| `ci search "<query>" [path] [--max N] [--no-tests]` | 의미 · 키워드 검색 (BM25 + AST 블록 · 시험 파일 포함이 기본) |
| `ci sym <name> [--scope P] [--callers\|--deps]` | 심볼 정의 · 호출자 · 의존성 (정의 우선 정렬) |
| `ci outline <file> [--section S]` | 파일 outline (+ 토큰 수) |
| `ci refs "<file>#<sym>" [--json]` | LSP 정밀 참조 |
| `ci def "file#sym"` · `ci impl "file#sym"` | LSP 정의 · 구현체 |
| `ci ast '<pattern>' [path] [-l lang]` | ast-grep 구조 패턴 |
| `ci lsp up [--scope P]` · `down` · `status` | LSP 데몬 켜기 · 끄기 · 상태 |
| `ci lsp repair [--ws <name>]` | LSP crash-loop 수리 (캐시를 지우지 않고 옆으로 옮김) |
| `ci doctor` | 설치 · 버전 · 데몬 · smoke 진단 |
| `ci bench [--queries FILE]` | 성능 회귀 (p50/p95) |
| `ci-audit [--days N] [--by-harness] [--csv FILE] [--json]` | 세션 기록에서 `ci` · grep · Serena 호출을 세어 준수율 계측 |

`PROBE_BIN` · `TILTH_BIN` 환경 변수로 바이너리 경로를 강제로 지정할 수 있습니다.

### 안전장치

- 검색 하나는 `CI_TIMEOUT`(기본 60초) 안에서만 돕니다. 리포 루트를 scope 로 주면 경고합니다. 정말 전체를 봐야 하면 `CI_ALLOW_HEAVY=1 CI_TIMEOUT=600` 으로 예외를 둡니다.
- 한국어 마크다운에서 probe 가 panic 하면 `-i '*.md'` 로 자동 재시도합니다.
- 여러 낱말 질의가 0건이면 `A OR B` 로 자동 재시도합니다.
- Python 구조 패턴은 ast-grep 으로 폴백합니다.
- `probe` · `tilth` 를 직접 부르지 말고 항상 `ci` 를 거칩니다.

### 알려진 함정

| 함정 | 대응 |
|---|---|
| `tilth` 를 리포 루트 scope 로 직접 부르면 CPU 폭주 (585% CPU · load 139 실측) | `ci` 경유 · scope 는 하위 폴더 · 전체 스캔은 `CI_ALLOW_HEAVY=1 CI_TIMEOUT=600` |
| 한국어 마크다운에서 probe panic (SIGABRT) | `ci search` 가 자동으로 `-i '*.md'` 재시도 |
| 여러 낱말 질의를 AND 로 해석해 0건 | `ci search` 가 자동으로 `A OR B` 재시도 |
| Python 구조 패턴 0건 (probe 버그) | `ci ast` 가 ast-grep 으로 폴백 (`ast-grep` 설치 필요) |
| Python LSP 는 pylsp (pyright 아님) · `call-hierarchy` 미지원 | `uv tool install python-lsp-server` · 호출자는 `ci sym --callers` |

## 요구사항

- macOS (arm64 · x86_64) 또는 Linux. `install.sh` 는 macOS 용 `probe` 를 내려받습니다. Linux 에서는 `probe` 0.6.0-rc342 를 먼저 PATH 에 두면 그대로 씁니다.
- `curl` · `tar` · `python3`
- `tilth` 설치에 `npx` 또는 `cargo`
- 선택: `ast-grep` (`brew install ast-grep` · Python 구조 패턴 폴백) · `python-lsp-server` (`uv tool install python-lsp-server` · `ci refs` Python)
- API 키 · 계정: 없음

## 링크

- [INSTALL.md](INSTALL.md) — 에이전트용 설치 안내
- [skill/SKILL.md](skill/SKILL.md) — 에이전트 스킬
- [skill/scripts/install.sh](skill/scripts/install.sh) — 설치 스크립트
- [AI Feature Pack 목록](../../README.ko.md)
