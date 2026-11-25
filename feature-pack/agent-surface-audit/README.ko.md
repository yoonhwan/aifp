<div align="center">

# agent-surface-audit

**에이전트 스킬과 hook 이 놓인 자리를 읽기만 해서 목록으로 보여주는, 공개해도 안전한 dry-run 점검 도구.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- 에이전트가 볼 수 있는 스킬 · hook 자리를 목록으로 만듭니다: 소스 팩, 사용자 스킬 루트, 프로젝트 overlay, hook 설정 경로.
- 안전한 메타데이터만 읽습니다. 비밀 내용은 읽지 않습니다.
- 실제 `~/.claude` · `~/.codex` · `~/.agents` · 프로젝트 overlay 설정 · symlink · hook · session · log · auth 자료는 고치지 않습니다.
- 중복 노출 위험과 끊어진 symlink 를 찾고, 앞으로 할 조치를 되돌리는 명령과 함께 제안합니다.
- 사람이 읽는 리포트나 JSON 을 출력하고, JSON 을 파일로 저장할 수도 있습니다.

## 빠른 시작

```bash
feature-pack/agent-surface-audit/core/bin/agent-surface-audit --dry-run
```

## 설치

이 팩은 실제 런타임에 아무것도 설치하지 않습니다. 일부러 읽기 전용으로 만들어서, checkout 한 자리에서 그대로 실행합니다. 자세한 내용은 [INSTALL.md](INSTALL.md) 를 보세요.

`agent-surface-audit` 이라는 이름으로 부르려면 `bin` 폴더를 현재 셸의 `PATH` 에 넣습니다.

```bash
export PATH="$PWD/feature-pack/agent-surface-audit/core/bin:$PATH"
agent-surface-audit --dry-run
```

dry-run 점검을 하는 동안에는 이 팩을 `~/.claude` · `~/.codex` · `~/.agents` · 프로젝트 overlay 루트에 symlink 로 걸지 않습니다. 이후의 설치 도구는 검토한 리포트에서 만들어지고 되돌리는 명령을 포함하도록 되어 있습니다.

## 사용법

### 옵션

| 옵션 | 설명 |
|------|------|
| `--dry-run` | 필수. 읽기 전용이 계약이라 이 옵션이 없으면 실행하지 않습니다 |
| `--repo-root PATH` | 점검할 리포지터리 (기본값: 현재 디렉터리) |
| `--home PATH` | 점검할 홈 디렉터리 (기본값: 내 홈 디렉터리) |
| `--json PATH` | JSON 리포트를 이 파일에도 저장합니다 |
| `--format human\|json` | stdout 출력 형식 |
| `--public-safety` | 공개 안전 절만 리포트합니다 |

### 예시

```bash
agent-surface-audit --dry-run
agent-surface-audit --dry-run --repo-root "$PWD" --home "$HOME" --json report.json
agent-surface-audit --dry-run --format json
agent-surface-audit --dry-run --public-safety --format json
```

### 리포트에 담기는 것

- 공개 안전 버킷
- `feature-pack/*` 아래의 소스 팩
- `$HOME/.claude/skills` · `$HOME/.codex/skills` · `$HOME/.agents/skills` 아래의 사용자 런타임 스킬 루트
- `.claude/skills` · `.codex/skills` · `.agents/skills` 아래의 프로젝트 overlay
- hook 설정 경로의 존재 여부 메타데이터만
- 중복 노출 위험과 끊어진 symlink
- 앞으로 할 조치 제안과 되돌리는 명령
- 건너뛴 비공개 경로 (종류만)

### 참고

- 발견 사항은 리포트 데이터이지 프로세스 실패가 아닙니다. 인자가 잘못됐거나 런타임/도구 오류일 때만 0 이 아닌 종료 코드를 냅니다.
- 실제로 로드되는 동작이 확인되기 전까지 Codex/OMO 스킬 노출 위치는 `~/.codex/skills` 입니다. `~/.agents/skills` 는 호환 · overlay 용입니다.
- 검증 스크립트는 `test/` 아래에 있습니다 (`verify.sh` · `verify_manifest_contract.sh`).

## 요구사항

- `bash`
- `python3` (3.10 이상 — 코드가 `match` 문을 씁니다)
- `jq` (`test/` 아래 검증 스크립트용)
- API 키 불필요

## 링크

- [INSTALL.md](INSTALL.md) — 그 자리에서 실행하는 방법
- [AI Feature Pack 카탈로그](../../README.ko.md)
