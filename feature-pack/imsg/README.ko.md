<div align="center">

# imsg

**macOS Messages.app 을 터미널에서 다루는 CLI 와 OpenClaw 스킬 — 에이전트 · 스크립트 · cron 의 iMessage 알림 채널로도 씁니다**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- **대화 목록** — 최근 iMessage / SMS 대화를 봅니다.
- **메시지 히스토리** — 한 대화의 지난 메시지를 날짜 필터 · 첨부파일 정보와 함께 봅니다.
- **메시지 전송** — 텍스트와 첨부파일(이미지 · 문서 등)을 보냅니다.
- **실시간 수신 감시** — 새 메시지가 오면 스트림으로 찍습니다.
- **에이전트 알림 채널** — 다른 에이전트 · 코딩 도구 · cron · CI 에서 `imsg send` 한 줄로 iMessage 알림을 보냅니다.
- CLI 는 서드파티 Homebrew 패키지 `steipete/tap/imsg` 이고, 이 팩은 그 설치 안내 · OpenClaw 스킬 · `TOOLS.md` 섹션을 담습니다.

## 빠른 시작

```bash
brew install steipete/tap/imsg
imsg --help                                        # 명령 목록이 나오면 성공
imsg chats --limit 3 --json                        # 대화 목록 (Full Disk Access 확인)
imsg send --to "<your-phone>" --text "imsg 설치 테스트"   # 나에게 보내기 (Automation 권한 확인)
```

## 설치

### 에이전트에게 맡기기

에이전트에게 «Read feature-pack/imsg/INSTALL.md and install it» 이라고 하면 됩니다. `INSTALL.md` 는 OpenClaw 에이전트가 읽고 스스로 설치하도록 쓴 글이고, 자리표시 3개(`{{OPENCLAW_WORKSPACE}}` · `{{USER_PHONE}}` · `{{NOTIFY_PHONE}}`)는 에이전트가 사용자에게 물어본 뒤 채웁니다.

### 직접 설치

1. `brew install steipete/tap/imsg` 로 CLI 를 설치합니다.
2. 터미널 앱(Terminal.app · iTerm2 등)에 **Full Disk Access** 를 줍니다: 시스템 설정 → 개인정보 보호 및 보안 → Full Disk Access. `chat.db` 를 읽는 데 필요합니다.
3. 처음 `imsg send` 를 하면 «Terminal 이 Messages 를 제어하도록 허용» 팝업이 뜹니다 → 허용(**Automation** 권한).
4. OpenClaw 를 쓴다면 스킬을 복사하고 [`config/tools-section.md`](config/tools-section.md) 의 섹션을 워크스페이스의 `TOOLS.md` 에 붙입니다.

```bash
SKILL_DIR="$HOME/.openclaw/workspace/skills/imsg"   # OpenClaw 워크스페이스 기본 경로
cp -r skill/ "$SKILL_DIR"
ls "$SKILL_DIR/SKILL.md"                            # 스킬 확인
```

## 사용법

### 명령

| 명령 | 하는 일 | 주요 옵션 |
|---|---|---|
| `imsg chats` | 대화 목록 | `--limit N` · `--json` · `--db <path>`(기본 `~/Library/Messages/chat.db`) |
| `imsg history` | 한 대화의 메시지 | `--chat-id <ID>` · `--limit N` · `--start` / `--end <ISO8601>` · `--participants` · `--attachments` · `--json` |
| `imsg send` | 메시지 전송 | `--to <phone/email>` 또는 `--chat-id` · `--text` · `--file <path>` · `--service imessage\|sms\|auto` · `--region` |
| `imsg watch` | 실시간 수신 감시 | `--chat-id` · `--participants` · `--since-rowid` · `--debounce 250ms` · `--attachments` · `--json` |
| `imsg rpc` | stdin / stdout JSON-RPC 모드 | MCP 서버 등과 연동 |

### 예시

```bash
imsg chats --limit 10 --json                                   # chat-id 확인
imsg history --chat-id 1 --start 2026-03-01T00:00:00Z --attachments --json
imsg send --to "<your-phone>" --text "보고서입니다" --file ~/reports/daily.pdf
imsg send --chat-id 42 --text "답장합니다"
imsg watch --chat-id 1 --attachments --debounce 250ms
```

### 알림 채널

어떤 CLI 도구 · 스크립트 · 에이전트에서든 `imsg send` 한 줄로 알림을 보낼 수 있습니다. 자주 쓴다면 셸 함수로 등록합니다.

```bash
# 작업이 끝나면 성공 / 실패 알림
long_running_task && imsg send --to "<your-phone>" --text "작업 완료" \
                  || imsg send --to "<your-phone>" --text "작업 실패"

# ~/.zshrc 에 추가 — 사용: notify "빌드 완료"
notify() {
  imsg send --to "<your-phone>" --text "$*"
}
```

### 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| `imsg: command not found` | brew 설치 안 됨 | `brew install steipete/tap/imsg` |
| `permission denied`(chats) | Full Disk Access 없음 | 시스템 설정 → 개인정보 보호 → Full Disk Access → 터미널 추가 |
| 전송 실패 | Automation 미허용 | 시스템 설정 → 자동화 → Terminal → Messages 체크 |
| «Messages is not running» | Messages.app 이 꺼져 있음 | Messages.app 실행 뒤 다시 시도 |
| 받는 쪽이 iMessage 미지원 | SMS 로 보내야 함 | `--service sms` 추가 |
| chat-id 를 모름 | 대화 ID 미확인 | `imsg chats --json` 으로 확인 |

## 요구사항

- macOS(Apple Silicon 또는 Intel) + iCloud 계정으로 로그인한 Messages.app
- Homebrew
- 터미널 앱의 Full Disk Access · Messages 에 대한 Automation 권한
- 선택: 스킬을 쓰려면 OpenClaw
- API 키 없음

## 링크

- [INSTALL.md](INSTALL.md) — 에이전트용 설치 안내(단계 · 검증 체크리스트 · 자리표시)
- [skill/SKILL.md](skill/SKILL.md) — OpenClaw 스킬(언제 쓰나 · 명령 레퍼런스)
- [config/tools-section.md](config/tools-section.md) — `TOOLS.md` 에 붙일 섹션
- [AI Feature Pack 카탈로그](../../README.ko.md)
