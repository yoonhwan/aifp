<div align="center">

# nanoclaw

**Claude Agent SDK 기반 멀티 에이전트 플랫폼. 에이전트마다 격리된 Docker 컨테이너에서 돌고, Slack 으로 대화합니다.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- Slack 채널에서 대화형 AI 에이전트를 운영합니다. OpenClaw 를 대체합니다.
- Docker 컨테이너 안에서 코딩 에이전트(Bash · Read · Write · Edit 등)를 실행하므로 크래시가 밖으로 번지지 않습니다.
- `groups/` 로 페르소나를 나눕니다: 그룹마다 `CLAUDE.md` 하나와 `memory/` 폴더 하나.
- 세션을 SQLite 와 `memory/` 파일에 남기고 Redis 로 미러링합니다.
- 스킬(내장 약 31개 + 직접 추가)로 Configure-Don't-Code 방식으로 확장합니다.
- 멀티 인스턴스를 지원합니다: NanoClaw 하나가 크루원 한 명입니다.

## 빠른 시작

```bash
git clone https://github.com/qwibitai/nanoclaw.git
cd nanoclaw
npm install
npm run build

# 에이전트 이미지 빌드
cd container && docker build -t nanoclaw-agent:latest . && cd ..

# 첫 실행 후 대화창에서 /setup 을 입력해 OneCLI 설치와 에이전트 등록을 진행
node dist/index.js
```

## 설치

에이전트에게 "Read feature-pack/nanoclaw/INSTALL.md and install it" 이라고 맡기면 됩니다. 에이전트가 설치 경로와 에이전트 이름을 물어봅니다. 직접 설치하려면 [INSTALL.md](INSTALL.md) 의 순서를 따릅니다(약 15분).

1. 돌릴 에이전트 수에 맞춰 Docker(Colima 권장)를 시작합니다.
2. NanoClaw 를 clone · 의존성 설치 · 빌드합니다(upstream: `qwibitai/nanoclaw`).
3. `node dist/index.js` 를 한 번 실행하고 `/setup` 으로 OneCLI 를 설정합니다. OneCLI 는 Claude API 접근을 컨테이너에 넣어 주는 프록시이며 `localhost:10254` 에서 동작합니다.
4. Slack 앱을 만들고(Socket Mode 켜기) 토큰 2개를 `.env` 에 넣습니다.
5. 페르소나와 memory 파일이 있는 그룹을 만듭니다.
6. `nanoclaw-agent` 이미지를 빌드하고 NanoClaw 를 시작합니다.
7. 선택: OpenClaw 의 스킬과 예약 작업을 옮깁니다. 봇 토큰만 다르면 둘을 함께 돌릴 수 있습니다.
8. 선택: launchd plist 로 로그인할 때 NanoClaw 를 자동 시작합니다([INSTALL.md](INSTALL.md) 의 Step 8).

```bash
# Colima 로 Docker 준비 (아래 크기 표 참고)
brew install colima docker
colima start --cpu 2 --memory 4 --disk 30
docker info

# Slack 토큰
cat > .env << 'EOF'
SLACK_BOT_TOKEN=<your-bot-token>
SLACK_APP_TOKEN=<your-app-token>
ASSISTANT_NAME=NanoClaw
EOF

# 페르소나 그룹
mkdir -p groups/main/memory
cp groups/global/CLAUDE.md groups/main/CLAUDE.md
touch groups/main/memory/{directives,mistakes,achievements}.md
```

## 사용법

### 핵심 개념

- **Group**: 에이전트의 페르소나 단위. `groups/{name}/CLAUDE.md` 로 정의합니다.
- **Container**: 태스크마다 Docker 컨테이너를 띄워 일하고 종료합니다.
- **Skill**: `.claude/skills/` 아래의 `SKILL.md` 파일.
- **Memory**: 실수 · 성과 · 지침이 `groups/{name}/memory/` 에 남습니다.
- **OneCLI**: Claude API 키 프록시. 컨테이너에 자동으로 주입됩니다.

### OpenClaw 와 NanoClaw 비교

| 항목 | OpenClaw | NanoClaw |
|------|----------|----------|
| Brain | 내장 LLM 라우팅 | Claude Agent SDK (Claude 구독에 포함, API 비용 없음) |
| 실행 환경 | 호스트 프로세스 | Docker 컨테이너 (격리) |
| 확장 | 스킬 + 플러그인 | `groups/` + `skills/` (Configure-Don't-Code) |
| 멀티 에이전트 | 단일 인스턴스 | 1 NanoClaw = 1 크루원 (멀티 인스턴스) |
| 영속성 | 내부 DB | SQLite + `memory/` 파일 + Redis 미러 |
| 통신 | HTTP API + Slack | Slack 네이티브 + Redis Stream |

### Colima 크기

| 설정 | 에이전트 1개 | 3~5개 | 10개+ |
|------|------------|-------|-------|
| CPU 코어 | 2 | 4 | 6 |
| RAM (GB) | 4 | 8 | 12 |
| 디스크 (GB) | 30 | 60 | 100 |

### NanoClaw 관리

```bash
# 그룹 목록
ls groups/

# 그룹 생성 (그 뒤 groups/{name}/CLAUDE.md 작성)
mkdir -p groups/{name}/memory

# 실행 중인 컨테이너와 OneCLI 확인
docker ps --filter "name=nanoclaw"
docker ps --filter "name=onecli"

# launchd 서비스 확인
launchctl list | grep nanoclaw

# 저장된 메시지 수
sqlite3 store/messages.db "SELECT COUNT(*) FROM messages;"

# 내장 스킬 목록, 커스텀 스킬 추가 (그 뒤 SKILL.md 작성)
ls .claude/skills/
mkdir -p groups/{name}/skills/{skill-name}
```

## 요구사항

- macOS (Apple Silicon M1 이상 권장)
- Node.js 20+ 와 npm
- Docker Desktop 또는 Colima
- Git
- Claude Pro 또는 Max 구독
- 앱을 만들 수 있는 Slack 워크스페이스
- 설치 시간 (~15분)

## 링크

- [INSTALL.md](INSTALL.md) — 설치 가이드
- [qwibitai/nanoclaw](https://github.com/qwibitai/nanoclaw) — upstream 프로젝트
- [AI Feature Pack 카탈로그](../../README.ko.md)
