<div align="center">

# mcp-manager

**Claude Code · Codex 의 MCP 서버를 비밀 설정 값을 꺼내지 않고 살펴보고, 끄고, 다시 켜고, 줄이는 로컬 도구.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- Claude Code · Codex 의 MCP 서버를 이름만 보여 줍니다(켜진 것 · 꺼진 것). 설정 값은 출력하지 않습니다.
- MCP 서버 하나를 끄고 다시 켭니다. 바꾸기 전에 백업을 남겨 되돌릴 수 있습니다.
- 남길 목록(`--keep`)만 두고 나머지 서버를 한 번에 끕니다(prune).
- 끈 서버의 설정 조각은 `~/.agents/state/mcp-manager/disabled/` 아래에 보관합니다.
- 바꾸는 명령은 기본이 dry-run 입니다. `--apply` 를 줄 때만 파일을 씁니다.

## 빠른 시작

```bash
# 리포 루트에서
feature-pack/mcp-manager/core/bin/mcp-manager list --format human
feature-pack/mcp-manager/core/bin/mcp-manager disable stitch --runtime claude --dry-run
```

## 설치

에이전트에게 맡길 때는 «`feature-pack/mcp-manager/INSTALL.md` 를 읽고 설치해 줘» 라고 하면 됩니다. 지금은 리포 안에서 그 자리에서 돌리는 도구라 따로 설치할 것이 없습니다.

```bash
feature-pack/mcp-manager/core/bin/mcp-manager list --format human
```

셸에서 이름만으로 부르려면 PATH 에 넣습니다(리포 루트에서).

```bash
export PATH="$PWD/feature-pack/mcp-manager/core/bin:$PATH"
mcp-manager list --format human
```

## 사용법

### 명령

| 명령 | 하는 일 |
|---|---|
| `mcp-manager list` | 런타임별 켜진 서버 · 꺼진 서버 이름 |
| `mcp-manager disable <server>` | 서버 하나를 끄고 설정 조각을 보관 |
| `mcp-manager enable <server>` | 보관한 서버를 다시 켬 |
| `mcp-manager prune --keep a,b,c` | `--keep` 에 없는 서버를 모두 끔(`--keep` 필수) |

```bash
mcp-manager list --format human
mcp-manager disable stitch --runtime claude --dry-run
mcp-manager disable stitch --runtime codex --dry-run
mcp-manager prune --runtime claude --keep context,filesystem,think --dry-run
mcp-manager prune --runtime codex --keep filesystem,node_repl,serena,think --dry-run
```

### 옵션

| 옵션 | 값 | 기본값 |
|---|---|---|
| `--runtime` | `list`: `all` · `claude` · `codex` / 나머지: `claude` · `codex` (`claude-code` · `codex-cli` 도 받음) | `list` = `all` · 나머지 = `codex` |
| `--dry-run` · `--apply` | 바꿀 것만 보여 주기 · 실제로 쓰기 | `--dry-run` |
| `--format` | `human` · `json` | `human` |
| `--home` | 홈 폴더 대신 볼 경로 | 사용자 홈 |
| `--keep` | 쉼표로 나눈 서버 이름(`prune` 전용) | 없음 |

종료 코드: 0 = 성공 · 2 = 인자 오류 또는 처리할 수 없는 요청(예: 보관된 조각이 없음) · 1 = 파일 읽기 · 쓰기 오류.

### 건드리는 파일

- Codex: `~/.codex/config.toml`
- Claude Code: `~/.claude.json` 을 고치고, MCP 맵 `~/.claude/.mcp.json` · `~/.claude/mcp.json` 을 읽습니다.
- 보관 · 백업: `~/.agents/state/mcp-manager/`(`disabled/<runtime>/` · `backups/<runtime>/`)
- 위 파일은 `--apply` 를 줄 때만 씁니다.

## 요구사항

- Python 3.12 이상(표준 라이브러리만 씀 · `typing.override` · `tomllib`)
- bash(`core/bin/mcp-manager` 실행 파일)
- API 키 · 계정: 없음

## 링크

- [INSTALL.md](INSTALL.md)
- [AI Feature Pack 카탈로그](../../README.ko.md)
