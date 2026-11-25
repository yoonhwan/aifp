<div align="center">

# termaid

**Mermaid 다이어그램을 터미널에서 바로 그려 주는 CLI `termaid-render` 와 에이전트 스킬**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- Mermaid 문법을 읽어 터미널에 스타일을 입힌 다이어그램으로 그립니다(lipgloss 로 색 · 테두리 · 굵은 글씨).
- flowchart(`graph LR/TD`) — 노드 모양(box · diamond · round · cylinder), subgraph, 엣지 라벨.
- sequence diagram — participant, 동기 · 비동기 화살표, `loop` · `alt/else` 블록.
- class · state · ER 다이어그램을 기본 지원합니다.
- 입력은 stdin 파이프(`echo '...' | termaid-render`)나 파일(`termaid-render diagram.mmd`)입니다.
- 스킬을 넣으면 에이전트가 설계 논의 · 아키텍처 설명 때 다이어그램을 알아서 그립니다.

## 빠른 시작

```bash
# 소스 받기 · 빌드 패치 · 빌드 · PATH 에 넣기
git clone https://github.com/MKlolbullen/termaid.git ~/scripts/termaid
cd ~/scripts/termaid
mv internal/tui/builder.go internal/tui/builder.go.wip 2>/dev/null || true
sed -i '' 's/return NewBuilder(catalogueNames()), nil/return errView(fmt.Errorf("workflow builder not yet available")), nil/' internal/tui/menu.go 2>/dev/null || true
go build -o termaid-render ./cmd/render/
cp termaid-render /opt/homebrew/bin/termaid-render

# 첫 다이어그램
echo 'graph LR
  A[Client] --> B{Auth?}
  B -->|yes| C[Service]
  B -->|no| D[401]' | termaid-render
```

## 설치

### 에이전트에게 맡기기

에이전트에게 «`feature-pack/termaid/INSTALL.md` 를 읽고 설치해 줘» 라고 말합니다. 에이전트가 Go 확인 → 소스 클론 → 빌드 패치 → 빌드 → PATH 설치 → 스킬 설치 → 검증 차례로 진행합니다. 설치 시간 (~2분).

### 직접 설치

1. 소스를 클론합니다(이미 있으면 `git pull`).
2. 빌드 패치를 합니다(필수). 업스트림 `internal/tui/builder.go` 에 컴파일 오류가 있어 빼고, `internal/tui/menu.go` 에서 `NewBuilder` 참조를 지웁니다 — 위 «빠른 시작» 의 `mv` · `sed` 두 줄입니다.
3. `go build -o termaid-render ./cmd/render/` 로 빌드하고 PATH 에 복사합니다.
4. 스킬을 Claude Code 스킬 경로에 복사하고 검증합니다.

```bash
# 스킬 설치 (팩 폴더에서)
mkdir -p ~/.claude/skills/termaid/
cp skill/SKILL.md ~/.claude/skills/termaid/

# 검증
which termaid-render && echo "OK" || echo "FAIL"
termaid-render --help

# 소스를 고친 뒤 다시 빌드
cd ~/scripts/termaid && go build -o termaid-render ./cmd/render/ && cp termaid-render /opt/homebrew/bin/
```

`INSTALL.md` 가 묻는 경로와 기본값:

| 자리표시 | 뜻 | 기본값 |
|---|---|---|
| `{{TERMAID_SOURCE_PATH}}` | 소스 저장 경로 | `~/scripts/termaid` |
| `{{TERMAID_INSTALL_PATH}}` | 바이너리 설치 경로 | `/opt/homebrew/bin/termaid-render` |
| `{{CLAUDE_SKILLS_PATH}}` | Claude 스킬 경로 | `~/.claude/skills` |

## 사용법

```bash
# 플로우차트 (stdin 파이프 — 가장 흔한 쓰임)
echo 'graph LR
  A[Client] --> B{Auth?}
  B -->|yes| C[Service]
  B -->|no| D[401]' | termaid-render

# 시퀀스 다이어그램
echo 'sequenceDiagram
  C ->> S : POST /login
  S -->> C : 200 OK' | termaid-render

# 파일에서
termaid-render workflow.mmd

# 도움말
termaid-render --help
```

### 지원 다이어그램

| 종류 | 키워드 | 지원 |
|---|---|---|
| Flowchart | `graph TD/LR`, `flowchart` | O |
| Sequence | `sequenceDiagram` | O |
| Class | `classDiagram` | O |
| State | `stateDiagram-v2` | O |
| ER | `erDiagram` | O |
| Gantt | `gantt` | X (코드 블록만) |

- 노드: `[box]` · `(round)` · `{diamond}` · `[(cylinder)]` · `((circle))`
- 화살표(sequence): `->>` 동기 · `-->>` 비동기 · `-x` 실패

### 에이전트가 쓰는 때

- 설계 논의(아키텍처 · API 설계 · DB 스키마), 시스템 구조 · 코드 흐름 설명, «그림으로» 같은 요청에서 씁니다.
- 키워드: «diagram» · «chart» · «sequence» · «flow» · «architecture» · «mermaid» · «termaid» 와 그 한국어 표현.
- 단순 코드 수정 · 짧은 질문 · 코드 블록으로 충분한 경우에는 쓰지 않습니다.
- 다이어그램은 짧게 둡니다 — 20줄이 넘거나 노드가 10개 이상이면 나눕니다.

### 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| `termaid-render: command not found` | PATH 에 없음 | `cp termaid-render /opt/homebrew/bin/` |
| `go: command not found` | Go 미설치 | `brew install go` |
| `builder.go compile error` | 업스트림 미완성 | 빌드 패치 확인 |
| `yaml unmarshal error` | TUI `init()` 패닉 | `cmd/render/` 만 빌드(TUI 우회) |

## 요구사항

- macOS
- Go 1.22+ (`go version` · 없으면 `brew install go`)
- API 키 · 계정: 없음

## 링크

- [INSTALL.md](INSTALL.md) — 에이전트용 설치 안내
- [skill/SKILL.md](skill/SKILL.md) — 에이전트 스킬
- [cli/install.md](cli/install.md) — CLI 만 설치
- [termaid 업스트림 소스](https://github.com/MKlolbullen/termaid)
- [AI Feature Pack 카탈로그](../../README.ko.md)
