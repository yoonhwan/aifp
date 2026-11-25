<div align="center">

# agent-browser

**AI 에이전트용 브라우저 자동화 CLI — 웹 스크래핑 · 스크린샷 · 폼 입력 · 영상 녹화 · 디버그 · 스타일드 카드 생성.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- 동적 SPA · React 페이지를 포함해 웹 페이지의 내용을 추출합니다(스크래핑).
- 전체 · 부분 스크린샷을 찍고, 2× 레티나 카드 이미지를 만듭니다.
- 로그인 · 회원가입 같은 폼을 자동으로 채우고, 로그인 세션(쿠키)을 저장 · 복원합니다.
- WebM 으로 녹화하고 GIF 로 변환합니다.
- 콘솔 로그 · 에러를 보고 네트워크 응답을 모킹합니다.
- Rust CDP 데몬이 Chrome 에 직접 연결하며, 확장 프로그램이 필요할 때도 쓸 수 있습니다.

## 빠른 시작

```bash
npm install -g agent-browser
agent-browser install    # Chromium 다운로드 (최초 1회, 약 150MB)
agent-browser --native open "https://example.com" && agent-browser --native snapshot -i && agent-browser --native close
```

## 설치

이 팩은 세 가지를 설치합니다: agent-browser CLI(0.16.3 이상), 에이전트가 브라우저 작업에서 자동으로 쓰는 스킬, 환경별 설정 · 속도 비교 · 팁을 담은 TOOLS.md 섹션.

### 에이전트로 설치

에이전트에게 다음과 같이 요청하세요.

```text
feature-pack/agent-browser/INSTALL.md 를 읽고 설치해 줘
```

### 직접 설치

```bash
# feature-pack/agent-browser/ 안에서 실행
npm install -g agent-browser
agent-browser install                  # Chromium 다운로드 (최초 1회, 약 150MB)
agent-browser --version                # 0.16.3 이상이어야 함
pip3 install Pillow                    # 스크린샷 카드용
cp -r skill/ ~/.openclaw/workspace/skills/agent-browser/   # Claude Code 는 ~/.claude/skills/agent-browser/
cat config/tools-section.md >> ~/.openclaw/workspace/TOOLS.md
```

- 스킬 폴더(`~/.openclaw/workspace/skills`)와 workspace(`~/.openclaw/workspace`)는 OpenClaw 기본 경로입니다. 다르면 자기 경로로 바꾸세요.
- `config/tools-section.md` 는 TOOLS.md 에 agent-browser 사용 규칙(native 우선, 검색 도구가 아님), 속도 비교 표, 영상 캡처 명령, 스크린샷 카드 파이프라인을 추가합니다.

### 설치 확인

```bash
agent-browser --version
agent-browser --native open "https://example.com" && agent-browser --native get title && agent-browser --native screenshot /tmp/ab-verify.png && agent-browser --native close
agent-browser --native open "https://example.com" && agent-browser --native snapshot -i && agent-browser --native close
python3 -c "from PIL import Image; print('Pillow OK')"
```

모두 통과하면 설치가 끝난 것입니다.

### 문제 해결

| 증상 | 해결 |
|------|------|
| `agent-browser: command not found` | `npm install -g agent-browser` 를 다시 실행 |
| `Chromium not found` | `agent-browser install` 실행 |
| `--native` 모드 실패 | `--native` 없이 standard 모드로 fallback |
| Pillow import 에러 | `pip3 install Pillow` 를 다시 실행 |
| 스크린샷이 잘림 | HTML 높이가 620px 이하인지 확인하고, 넘으면 카드를 나눔 |

## 사용법

### 모드 선택

| 상황 | 모드 | 이유 |
|------|------|------|
| 일반 브라우징 · 스크래핑 | `--native` | 더 빠름(페이지당 약 150ms), Node.js 불필요 |
| 스크린샷 · 캡처 | `--native` | 지연이 낮음 |
| Chrome 확장 프로그램이 필요 | `--native connect <port>` | 실제 Chrome 만 가능 |
| JS 가 복잡한 SPA 렌더링 문제 | standard (플래그 없음) | Playwright 의 안정성 |
| CI/CD 파이프라인 | standard headless | 검증된 안정성 |

- 기본은 항상 `--native` 를 먼저 시도하고, 문제가 있으면 standard 로 돌아갑니다.
- 웹 검색 도구가 아닙니다. 검색이나 단순한 URL 내용 읽기에는 web search / fetch 도구를 쓰세요.

### 기본 흐름

```bash
SESSION="task-$(date +%s)"
trap "agent-browser close --session $SESSION 2>/dev/null" EXIT ERR

agent-browser --native --session "$SESSION" --headed open "https://example.com"
agent-browser --native --session "$SESSION" wait --load networkidle
agent-browser --native --session "$SESSION" snapshot -i          # 요소를 @ref 로 나열
agent-browser --native --session "$SESSION" click @e3
agent-browser --native --session "$SESSION" fill @e5 "you@example.com"
agent-browser --native --session "$SESSION" get text ".result"
agent-browser --native --session "$SESSION" screenshot ./result.png
agent-browser --native --session "$SESSION" close
```

- 상호작용 전에 항상 `snapshot -i` 로 요소를 확인합니다. `@ref` 값은 세션마다 바뀌므로 다른 세션에 재사용하지 마세요.
- 항상 `--session <name>` 을 쓰고 `trap` 으로 정리합니다.
- 로컬에서는 `--headed`(동작이 보임), CI/CD 에서는 생략(headless 가 기본)합니다.
- 요소를 찾는 우선순위: ① `snapshot -i` 의 `@ref` ② CSS 선택자 ③ `find` 명령(`find role button click` · `find text "Submit" click` · `find testid "btn" click`).

### 자주 쓰는 작업

```bash
# 대기 방식
agent-browser --native --session "$SESSION" wait "#element"            # 요소가 나타날 때까지
agent-browser --native --session "$SESSION" wait 2000                  # 고정 지연 (ms)
agent-browser --native --session "$SESSION" wait --text "Success"      # 텍스트가 나타날 때까지
agent-browser --native --session "$SESSION" wait --url "**/dashboard"  # URL 이 일치할 때까지
agent-browser --native --session "$SESSION" wait --load networkidle    # 요청이 모두 끝날 때까지

# 쿠키 저장 / 복원
agent-browser --native --session "$SESSION" cookies get > cookies.json
agent-browser --native --session "$SESSION" cookies set "$(cat cookies.json)"

# 네트워크 모킹
agent-browser --native --session "$SESSION" network route "**/analytics/*" --abort
agent-browser --native --session "$SESSION" network route "**/api/user" --body '{"id":1,"name":"Test"}'
agent-browser --native --session "$SESSION" network unroute

# 영상 녹화 후 GIF 변환
agent-browser --native --session "$SESSION" record start "./demo.webm"
agent-browser --native --session "$SESSION" record stop
ffmpeg -i demo.webm -vf "fps=10,scale=480:-1:flags=lanczos" -c:v gif demo.gif

# 디버그
agent-browser --native --session "$SESSION" console                    # 로그 보기
agent-browser --native --session "$SESSION" errors                     # 에러 보기
agent-browser --native --session "$SESSION" eval "document.title"      # JS 실행
```

- 로그인 팝업을 피할 때는 DOM 요소를 `remove()` 하지 말고 CSS 로 숨기세요(`remove()` 는 내용을 망가뜨립니다).

### 실행 중인 Chrome 에 연결

```bash
agent-browser --native connect 9222 --session "$SESSION"                                     # 포트로
agent-browser --native connect "ws://127.0.0.1:9222/devtools/browser/UUID" --session "$SESSION"  # WebSocket URL 로
agent-browser --auto-connect --native snapshot                                                # 실행 중인 Chrome 자동 탐색
```

- Chrome 확장 프로그램이 필요할 때, macOS 오디오(BlackHole) 루프백이 필요할 때, 원격 · 디버그 Chrome 에 붙을 때 `--native connect` 를 씁니다.

### 스크린샷 카드

공유용(Slack · Discord 등)으로 모바일에 맞춘 스타일드 카드를 HTML 로 만듭니다.

```bash
agent-browser --native --session cap open "file:///tmp/card.html"   # 375px 폭, 높이 620px 이하의 HTML
agent-browser --native --session cap screenshot "/tmp/raw.png"
agent-browser --native --session cap close
```

- agent-browser 의 뷰포트는 1280×720px 로 고정이라, 약 620px 보다 긴 내용은 잘립니다. 긴 내용은 카드를 나누세요(카드 1장 = 주제 1개).
- 카드 폭은 375px, 최종 출력은 2× 레티나(폭 830px)입니다. 위 스크린샷을 Pillow 로 잘라 2배로 키웁니다(전체 스크립트는 [skill/SKILL.md](skill/SKILL.md)).
- 글자 크기: 짧은 내용 제목 15px · 본문 12px · 코드 11px · 여백 20px / 중간 14 · 11 · 10 · 16px / 긴 표(20행 이상) 13 · 10.5 · 9.5 · 14px.
- 테마는 다크입니다(배경 `#1a1a2e`, 카드 `#16213e`, 표 머리 `#0f3460`, 테두리 `#1a4080`). 마지막 줄(footer)이 보이는지 꼭 확인하세요.

### 오류 복구

| 오류 | 해결 |
|------|------|
| `No session found` | 먼저 `open` 실행 |
| `Element not found` | `snapshot -i` 를 다시 실행해 ref 확인 |
| `Timeout` | `--timeout` 을 늘리고 `wait` 조건 확인 |
| 좀비 세션 | `agent-browser session list` → `close --session <name>` |
| `--native` 실패 | `--native` 플래그를 빼고 standard 모드 사용 |

전체 명령은 `agent-browser --help` 와 `agent-browser <command> --help` 에서 볼 수 있습니다.

## 요구사항

- macOS (arm64 / x86_64)
- Node.js 18 이상 · npm
- Python 3 + Pillow (스크린샷 카드용)
- ffmpeg (WebM 을 GIF 로 바꿀 때만)
- 계정이나 API 키는 필요 없습니다.

## 링크

- [INSTALL.md](INSTALL.md) — 에이전트용 설치 안내
- [skill/SKILL.md](skill/SKILL.md) — 스킬 정의
- [AI Feature Pack 카탈로그](../../README.ko.md)
