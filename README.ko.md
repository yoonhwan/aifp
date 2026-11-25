<div align="center">

# AI Feature Pack

**AI 코딩 에이전트 환경에 하나씩 골라 설치하는 피처 팩 모음**
Claude Code · Codex · Pi · OpenCode · OpenClaw

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

[![Packs](https://img.shields.io/badge/packs-26-0b6e5f)](#-카탈로그)
[![Guide](https://img.shields.io/badge/guide-GitHub%20Pages-0b6e5f)](https://yoonhwan.github.io/aifp/ko.html)
[![Platform](https://img.shields.io/badge/platform-macOS-555)](#-참고)

</div>

---

## 이 리포는 무엇인가요?

- AI 코딩 에이전트를 위한 **피처 팩** 모음입니다. 팩 하나는 [`feature-pack/`](feature-pack/) 아래 폴더 하나입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.
- 팩마다 **에이전트가 읽는** `INSTALL.md` 가 있습니다. 에이전트에게 건네면 사전 요구사항 확인, CLI 설치, 스킬 등록, 설치 검증까지 진행합니다.
- 처음이라면 그림으로 설명한 안내 글부터 보세요: **[내 AI 에이전트를 폰에서 쓰는 법](https://yoonhwan.github.io/aifp/ko.html)** ([English](https://yoonhwan.github.io/aifp/)).

## 🚀 빠른 시작

**방법 A — 폰 원격 조합 (`tmuxc` + `tmm`)**

```bash
git clone https://github.com/yoonhwan/aifp.git && cd aifp \
  && bash feature-pack/tmuxc/install.sh \
  && bash feature-pack/tmm/install.sh
```

필요한 것: macOS, bash 4 이상, git, tmux, fzf(`tmm` 용).

**방법 B — 에이전트에게 팩 설치 맡기기**

```bash
git clone https://github.com/yoonhwan/aifp.git
# 그다음 에이전트에게 이렇게 말합니다. 예:
#   "feature-pack/agent-browser/INSTALL.md 읽고 설치해줘"
```

에이전트가 `INSTALL.md` 를 읽고 다음을 진행합니다.

1. 사전 요구사항 확인
2. CLI 설치
3. 인증/설정 (필요하면 사용자에게 질문)
4. 스킬 등록
5. `TOOLS.md` / `AGENTS.md` 설정 추가
6. 설치 검증

## 📦 카탈로그

| # | 팩 | 하는 일 | 설치 시간 | API 키 | 인증 |
|---|----|---------|-----------|--------|------|
| 1 | [agent-browser](feature-pack/agent-browser/) | 웹 자동화 — 스크래핑, 스크린샷, 폼 입력, 녹화 | ~3분 | — | — |
| 2 | [imsg](feature-pack/imsg/) | iMessage/SMS — 대화 조회, 메시지 전송, 실시간 감시 | ~3분 | — | — |
| 3 | [notebooklm](feature-pack/notebooklm/) | Google NotebookLM — 소스 기반 Q&A, 리서치, 오디오 생성 | ~5분 | — | Google |
| 4 | [obsidian-cli](feature-pack/obsidian-cli/) | Obsidian 볼트 CLI — 노트 조회/생성/검색/이동 | ~3분 | — | — |
| 5 | [tts-say](feature-pack/tts-say/) | 통합 TTS — macOS `say` + ElevenLabs 음성 합성 | ~3분 | ElevenLabs | — |
| 6 | [yt-transcribe](feature-pack/yt-transcribe/) | YouTube → STT → 요약 자동 파이프라인 | ~10분 | — | — |
| 7 | [termaid](feature-pack/termaid/) | Mermaid 다이어그램 터미널 렌더링 — 설계 시각화 때 자동 발동 | ~2분 | — | — |
| 8 | [baton](feature-pack/baton/) | 멀티 에이전트 handoff/worktree/archive 표준 — Claude Code·Codex·Gemini 간 작업 인계 | ~2분 | — | — |
| 9 | [cairn](feature-pack/cairn/) | 일정 + 멀티 에이전트 복구 원장 — milestone/task/session lineage, baton·tmuxc 연동 | ~2분 | — | — |
| 10 | [tmuxc](feature-pack/tmuxc/) | tmux 기반 Claude Code·Codex·OMX 세션 launcher/control — verified send/capture 통신 표준 포함 | ~1분 | — | — |
| 11 | [auto](feature-pack/auto/) | AutoResearch 자율 실험 루프 — 베이스라인 → 목표 → 자율주행 최적화 | ~1분 | — | — |
| 12 | [nanoclaw](feature-pack/nanoclaw/) | AI 멀티 에이전트 플랫폼(OpenClaw 대체) — Claude SDK Brain, Docker 격리, 멀티 크루 | ~15분 | — | Slack |
| 13 | [agent-cli](feature-pack/agent-cli/) | **AI 코딩 에이전트 CLI 툴킷** — 설치·비교 + 페르소나를 쓰는 비대화 위임 | ~3분 | — | — |
| 14 | [headroom](feature-pack/headroom/) | Claude Code·Codex 등 AI 코딩 에이전트 컨텍스트 압축 프록시 + `/headroom` 토글 | ~5분 | — | — |
| 15 | [fable-team](feature-pack/fable-team/ft2/) | **팀 오케스트레이션 하네스 (ft 2.0)** — 좌석·쪽지·발주 공통 코어, 계약 정의, Codex·Pi·Slack 어댑터, 진단 도구. 폴더별 책임은 `ft2/README.md` | — | — | — |
| 16 | [tmm](feature-pack/tmm/) | **모바일(SSH) tmux 좌석 TUI** — 폰에서 수십 개 에이전트 세션을 커서로 고르기: 미리보기, 최근 응답순, 대기 좌석 우선, 메시지 전송 (fzf) | ~1분 | — | — |
| 17 | [ctx-burn](feature-pack/ctx-burn/) | **로컬 컨텍스트 낭비 감사기** — 7종 런타임(claude, codex, pi, opencode, hermes, openclaw, commandcode) 자동 감지 | ~1분 | — | — |
| 18 | [ctx-plan](feature-pack/ctx-plan/) | **용량 산정기** — ctx-burn 의 `ctx.v1` 출력만 읽어 계정 구성에 맞는 정원과 피크 세션을 산정 | ~1분 | — | — |

**트리에 함께 있는 것** (폴더마다 자체 문서가 있습니다):
[agent-surface-audit](feature-pack/agent-surface-audit/) — 에이전트 스킬·훅 표면의 dry-run 목록 도구 ·
[agent-surface-sync](feature-pack/agent-surface-sync/) — `feature-pack/*` 와 `hooks/` 의 공용 에이전트 표면을 설치·갱신 ·
[code-intel](feature-pack/code-intel/) — `ci` 단일 진입점 코드 인텔리전스 ·
[daily-trend-viewer](feature-pack/daily-trend-viewer/) — 인기 영상과 AI 영상 소식을 매일 보는 로컬 사이트 ·
[mcp-manager](feature-pack/mcp-manager/) — MCP 서버 표면 점검·정리 ·
[memory-system](feature-pack/memory-system/) — OpenClaw 에이전트 기억 구조 ·
[rag](feature-pack/rag/) · [rag-consumer](feature-pack/rag-consumer/) — `airag` RAG 패키지와 그 소비자([`rag/docs/README.md`](feature-pack/rag/docs/README.md) 에서 시작).

## 📋 추천 설치 순서

피처 간 의존성은 없습니다. 활용도 기준 추천 순서입니다.

1. **obsidian-cli** — 세컨드브레인 기반 (다른 팩의 노트 저장처)
2. **agent-browser** — 웹 자동화 (가장 범용적)
3. **yt-transcribe** — YouTube 전사 (obsidian-cli 와 잘 맞음)
4. **notebooklm** — 지식 Q&A (소스 기반 답변)
5. **tts-say** — 음성 출력
6. **imsg** — iMessage 연동 (macOS 전용)

에이전트를 여럿 굴리는 운영에는 다음 순서를 권합니다.

1. **baton** — worktree/handoff/archive 기준점
2. **cairn** — 일정과 session lineage 원장
3. **tmuxc** — Claude Code/Codex/OMX tmux 세션 실행과 verified-send 통신
4. **tmm** — 폰(Termius)에서 그 좌석들을 커서로 고르고 붙는 TUI

| 도구 | 담당 |
|------|------|
| baton | 작업 시작/저장/복구용 `.baton/handoff/` 와 worktree/archive |
| cairn | `.cairn/plan.yaml` 기반 milestone/task/session lineage |
| tmuxc | live tmux 에이전트 세션 생성, capture, send, kill |
| tmm | 모바일 SSH 에서 좌석 목록·미리보기·attach·메시지 (tmuxc 좌석 소비자) |

## 🔧 다른 설치 방법

**수동 설치** — 팩 폴더의 `README.md` 를 읽고 순서대로 진행합니다.

```
feature-pack/{name}/
├── README.md        ← 사람용 개요 (여기서 시작)
├── INSTALL.md       ← 에이전트용 설치 프롬프트
├── cli/install.md   ← CLI 설치 명령어
├── skill/SKILL.md   ← 스킬 정의
├── config/          ← TOOLS.md / AGENTS.md 추가 내용
└── test/verify.md   ← 설치 검증
```

모든 팩에 모든 파일이 있는 것은 아닙니다. 다섯 팩(`ctx-plan`, `fable-team`, `headroom`, `rag`, `rag-consumer`)에는 `INSTALL.md` 가 없으니 README 나 docs 에서 시작하세요.

**전체 설치** — 에이전트에게 "aifp 레포의 모든 피처팩을 순서대로 설치해줘" 라고 말합니다. 약 25분 걸립니다.

## 🔒 이 리포에 대하여

- 이 리포는 비공개 작업 리포에서 **내보낸 사본**입니다. 내부 운영 기록은 빼고 개인·조직 식별자는 자리표시로 바꿨습니다. 그래서 비공개 자료가 필요한 일부 시험은 여기서 건너뛰거나 돌지 않습니다.
- 내보낼 때마다 58종 패턴(키, 토큰, 주소, ID)을 검사하고, 검토한 허용 목록 밖에 남은 것이 없을 때만 내보냅니다. 남아 있는 키 꼴 글자는 시험 고정값이나 문서의 자리표시입니다.
- 팩을 설치할 때 본인의 키와 토큰을 리포 폴더 안의 파일에 적지 마세요.

## 📌 참고

- **OS**: 현재 macOS 만 지원 (Linux/Windows 는 추후).
- **OpenClaw**: [openclaw.ai](https://openclaw.ai) · [GitHub](https://github.com/openclaw/openclaw)
- **문의**: 이슈 등록 또는 [Discord](https://discord.com/invite/clawd).

## 라이선스

MIT
