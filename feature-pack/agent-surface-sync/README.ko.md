<div align="center">

# agent-surface-sync

**`feature-pack/*` 와 `hooks/` 의 공용 에이전트 surface 를 로컬 런타임 폴더에 링크로 설치 · 갱신하는 도구 — 기본은 dry-run.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- 각 팩의 `manifest.json` 을 읽어 공용 CLI 를 `~/.agents/bin` 에 링크합니다.
- manifest 가 설치 가능(`installable`)으로 적은 런타임 스킬 · 보조 파일을 링크합니다. 그 런타임 폴더가 없으면 건너뜁니다.
- 공용 hook 소스 `hooks/` 를 `~/.agents/hooks` 에 링크합니다.
- `hooks/manifests/` 가 있으면 hook 항목을 `~/.claude/settings.json`(Claude Code) · `~/.codex/hooks.json`(Codex)에 합칩니다. 있던 항목은 남깁니다.
- 기본은 dry-run 입니다. `--apply` 를 줄 때만 바꾸고, 바꾸기 전에 원래 것을 백업합니다.

## 빠른 시작

```bash
# 리포 루트에서 — 계획만 보기(dry-run)
feature-pack/agent-surface-sync/core/bin/agent-surface-sync
# 계획이 맞으면 적용
feature-pack/agent-surface-sync/core/bin/agent-surface-sync --apply --package baton
```

## 설치

에이전트에게 맡길 때는 «`feature-pack/agent-surface-sync/INSTALL.md` 를 읽고 설치해 줘» 라고 하면 됩니다. 따로 설치할 것 없이 리포 루트에서 그 자리에서 돌립니다(기본 `--repo-root` 가 지금 폴더입니다).

```bash
feature-pack/agent-surface-sync/core/bin/agent-surface-sync
```

셸에서 이름만으로 부르려면 PATH 에 넣습니다(리포 루트에서).

```bash
export PATH="$PWD/feature-pack/agent-surface-sync/core/bin:$PATH"
agent-surface-sync --package baton,tmuxc
```

`--apply` 는 dry-run 출력이 맞는지 본 뒤에만 씁니다.

## 사용법

### 명령 예시

```bash
agent-surface-sync                                   # 모든 팩 · 모든 런타임 dry-run
agent-surface-sync --package baton,tmuxc             # 고른 팩만
agent-surface-sync --runtime claude-code --format json
agent-surface-sync --apply --package baton           # 실제로 적용
```

### 옵션

| 옵션 | 값 | 기본값 |
|---|---|---|
| `--dry-run` · `--apply` | 계획만 보기 · 실제로 적용 | `--dry-run` |
| `--package` | 쉼표로 나눈 팩 이름 | 모든 팩 |
| `--runtime` | `all` · `agents` · `claude-code` · `codex-cli` | `all` |
| `--format` | `human` · `json` | `human` |
| `--json` | 보고서를 JSON 파일로도 저장할 경로 | 없음 |
| `--repo-root` | 리포 루트 | 지금 폴더 |
| `--home` | 홈 폴더 대신 쓸 경로 | 사용자 홈 |

종료 코드: 0 = 성공 · 2 = 인자 · 경로 오류 · 1 = 파일 읽기 · 쓰기 오류.

### 보고서 읽기

dry-run 보고서에는 계획된 바꿈 · 건너뛴 것 · 되돌리기 명령이 들어 있습니다. 바꿈마다 상태가 붙습니다.

| 상태 | 뜻 |
|---|---|
| `install` | 새로 링크 |
| `relink` | 다른 곳을 가리키던 링크를 바꿈 |
| `replace-existing` | 링크가 아닌 파일 · 폴더를 백업하고 링크로 바꿈 |
| `merge` | hook 설정 파일에 항목을 합침 |
| `up-to-date` | 바꿀 것 없음 |

### 백업과 되돌리기

- 백업은 `~/.agents/state/agent-surface-sync/backups/<operation_id>/` 에 남습니다.
- 보고서의 `rollback` 줄(`rm -rf <target> && mv <backup> <target>`)을 그대로 돌리면 원래대로 돌아갑니다.

## 요구사항

- Python 3.12 이상(표준 라이브러리만 씀 · `typing.override`)
- 링크를 걸 런타임 폴더: Claude Code = `~/.claude` · Codex = `~/.codex`(없으면 그 런타임은 건너뜀)
- API 키 · 계정: 없음

## 링크

- [INSTALL.md](INSTALL.md)
- [AI Feature Pack 카탈로그](../../README.ko.md)
