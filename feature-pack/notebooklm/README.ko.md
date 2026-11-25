<div align="center">

# notebooklm

**Google NotebookLM 을 터미널에서 제어하는 `nlm` CLI 와 OpenClaw 스킬 패키지.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- 소스 기반 Q&A: 업로드한 문서만 근거로 답합니다.
- 오디오 팟캐스트와 비디오 오버뷰를 문서에서 만듭니다.
- 리포트 · 퀴즈 · 플래시카드 같은 학습 자료를 만듭니다.
- 딥 리서치로 웹 소스를 자동 수집하고 분석합니다.
- 노트북을 만들고 · 지우고 · 공유하고 · 별칭을 붙여 관리합니다.
- Obsidian 볼트의 문서를 NotebookLM 소스로 올려 씁니다.

## 빠른 시작

```bash
# 1. 설치
uv tool install notebooklm-mcp-cli

# 2. 인증 (Chrome 이 열립니다)
nlm login

# 3. 사용
nlm notebook list
nlm query notebook <notebook_id> "질문"
```

## 설치

에이전트에게 "Read feature-pack/notebooklm/INSTALL.md and install it" 이라고 맡기면 됩니다. 직접 설치하려면 [INSTALL.md](INSTALL.md) 의 순서를 따릅니다.

1. `uv` 로 `nlm` CLI 를 설치합니다(`notebooklm-mcp-cli`).
2. `nlm login` 으로 Google 계정에 로그인하고 `nlm auth status` 로 확인합니다. 세션은 약 20분 유지되며, 만료되면 `nlm login` 을 다시 실행합니다.
3. 이 팩의 `skill/` 폴더를 OpenClaw 워크스페이스의 스킬 폴더에 복사합니다.
4. 워크스페이스 `TOOLS.md` 에 NotebookLM 섹션을 추가합니다(내용은 [INSTALL.md](INSTALL.md) 에 있습니다).
5. 선택: Obsidian 연동을 설정합니다.
6. `nlm --version` · `nlm auth status` · `nlm notebook list` 로 동작을 확인합니다.

```bash
# uv 가 없으면 설치
curl -LsSf https://astral.sh/uv/install.sh | sh

# CLI 설치와 확인
uv tool install notebooklm-mcp-cli
nlm --version

# nlm 을 찾을 수 없으면 PATH 에 ~/.local/bin 추가
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc

# 스킬 복사 (OpenClaw 워크스페이스 기본값: ~/.openclaw/workspace)
cp -r skill/ ~/.openclaw/workspace/skills/notebooklm

# 업데이트
uv tool upgrade notebooklm-mcp-cli
```

## 사용법

### 주요 명령

```bash
# 노트북
nlm notebook list
nlm notebook create "이름"
nlm notebook get <notebook_id>
nlm notebook describe <notebook_id>

# 소스
nlm source add <notebook_id> --file <path>
nlm source add <notebook_id> --url <url>
nlm source add <notebook_id> --text "내용" --title "제목"

# Q&A
nlm query notebook <notebook_id> "질문"

# 생성
nlm audio create <notebook_id> --confirm
nlm video create <notebook_id> --confirm
nlm report create <notebook_id> --confirm
nlm quiz create <notebook_id> --confirm
nlm flashcards create <notebook_id> --confirm
nlm mindmap create <notebook_id> --confirm
nlm slides create <notebook_id> --confirm

# 리서치
nlm research start <notebook_id> "주제" --mode deep
nlm research status <notebook_id>

# 다운로드
nlm download audio <notebook_id> <artifact_id> -o <path>

# 별칭 (UUID 대신 짧은 이름)
nlm alias set myproject <notebook_id>
nlm alias list
```

### 에이전트에서 Q&A 할 때

- 에이전트는 항상 `nlm query notebook` 으로 한 번에 묻고 답을 받습니다.
- `nlm chat start` (REPL 모드)는 에이전트가 제어할 수 없으니 쓰지 않습니다.
- 전체 명령 안내는 `nlm --ai` 로 볼 수 있습니다.

### Obsidian 연동

플러그인이 아니라 CLI 로 파일을 올리는 방식입니다.

```bash
# 전용 노트북을 만들고 별칭을 붙인다
nlm notebook create "My Obsidian Vault"
nlm alias set vault <notebook_id>

# 문서를 소스로 올린다
nlm source add vault --file "<path-to-vault>/note.md" --wait

# 질문한다
nlm query notebook vault "프로젝트 구조를 설명해줘"
```

### 문제 해결

| 증상 | 해결 |
|------|------|
| `nlm: command not found` | PATH 에 `~/.local/bin` 을 추가합니다 |
| `uv: command not found` | uv 를 설치합니다 |
| "Cookies have expired" / "authentication may have expired" | `nlm login` 을 다시 실행합니다 |
| Chrome 이 열리지 않음 | Chrome 을 설치합니다 (`brew install --cask google-chrome`) |
| Rate limit 에러 | 자동으로 3회 재시도합니다. 계속 실패하면 잠시 기다립니다 |
| 소스 추가 실패 | 파일 크기가 NotebookLM 소스 크기 제한을 넘지 않았는지 확인합니다 |

## 요구사항

- macOS (Apple Silicon 또는 Intel)
- Python 3.10+
- Google 계정 (NotebookLM 접근 권한)
- Chrome 브라우저 (인증에 사용)
- uv (없으면 설치 단계에서 설치합니다)

## 링크

- [INSTALL.md](INSTALL.md) — 설치 가이드
- [Obsidian 연동 가이드](obsidian/setup.md)
- [AI Feature Pack 카탈로그](../../README.ko.md)
