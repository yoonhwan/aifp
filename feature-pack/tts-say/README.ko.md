<div align="center">

# tts-say

**macOS `say` 와 ElevenLabs `sag` 를 명령 하나 `tts-say` 로 묶은 TTS CLI**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- 글을 소리 내어 읽습니다(`tts-say "텍스트"`) · stdin 파이프도 받습니다(`echo "텍스트" | tts-say`).
- 오디오 파일로 저장합니다(`tts-say speak -o out.mp3 "텍스트"`).
- 엔진을 알아서 고릅니다 — `ELEVENLABS_API_KEY` 가 있으면 `sag`, 없으면 macOS `say`.
- 기본 엔진 · 보이스 · 옵션을 config 에 저장해 두면 매번 적용됩니다.
- 엔진별 보이스 목록을 봅니다(`tts-say voices`).
- 에이전트 · 스크립트 음성 알림에 씁니다: `pytest && tts-say "테스트 통과"`.

## 빠른 시작

```bash
# 팩 폴더에서: CLI 를 PATH 에 복사
cp skill/scripts/tts-say ~/.local/bin/tts-say
chmod +x ~/.local/bin/tts-say

# 첫 음성 (sag 가 없으면 macOS say 로 읽음)
tts-say "Build finished"
```

## 설치

### 에이전트에게 맡기기

에이전트에게 «`feature-pack/tts-say/INSTALL.md` 를 읽고 설치해 줘» 라고 말합니다. 에이전트가 `sag` 설치(선택) → ElevenLabs API 키(선택) → CLI 복사 → 기본 config → 스킬 설치 → 검증 차례로 진행하고, API 키 · 설치 경로 · 기본 보이스를 물어봅니다. 설치 시간 (~3분).

### 직접 설치

```bash
# 1. sag 설치 (선택 · ElevenLabs 고품질 음성)
brew install steipete/tap/sag
export ELEVENLABS_API_KEY="<your-key>"   # ~/.zshrc 에 넣기

# 2. CLI 를 PATH 에 복사 (팩 폴더에서)
cp skill/scripts/tts-say ~/.local/bin/tts-say
chmod +x ~/.local/bin/tts-say

# 3. 기본 config
tts-say config set default_engine auto
tts-say config set say.voice Yuna
tts-say config set sag.model_id eleven_multilingual_v2
tts-say config set sag.lang ko

# 4. 스킬 설치 (OpenClaw 워크스페이스)
cp -r skill/ ~/.openclaw/workspace/skills/tts-say/

# 5. 검증
tts-say --help
tts-say config show
tts-say voices --engine say
```

- OpenClaw 를 쓰면 `config/tools-section.md` 내용을 워크스페이스의 `TOOLS.md` 에 덧붙입니다(선택).
- `~/.local/bin` 이 PATH 에 없으면 `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc` 로 넣습니다.

`INSTALL.md` 가 묻는 값과 기본값:

| 자리표시 | 뜻 | 기본값 |
|---|---|---|
| `{{ELEVENLABS_API_KEY}}` | ElevenLabs API 키(없으면 `say` 만 씀) | 없음 |
| `{{TTS_INSTALL_PATH}}` | CLI 설치 경로 | `~/.local/bin/tts-say` |
| `{{DEFAULT_ENGINE}}` | 기본 엔진 | `auto` |
| `{{SAG_DEFAULT_VOICE}}` | `sag` 기본 보이스 | `tts-say voices --engine sag` 목록에서 고름 |
| `{{OPENCLAW_SKILLS_PATH}}` | 스킬 설치 경로 | `~/.openclaw/workspace/skills` |
| `{{OPENCLAW_WORKSPACE}}` | 워크스페이스 경로 | `~/.openclaw/workspace` |

## 사용법

```bash
# 읽기 (config 기본값 사용)
tts-say "Build finished"

# 엔진 지정
tts-say speak --engine say --voice Yuna "Hello"
tts-say speak --engine sag --voice Aria --lang ko "Hello"

# 파일로 저장
tts-say speak -o /tmp/alert.mp3 "Alert"

# 보이스 목록
tts-say voices --engine say
tts-say voices --engine sag --search korean --limit 10

# config
tts-say config show
tts-say config set sag.speed 1.1
tts-say config unset say.rate
tts-say config example-env
tts-say config path

# 빌드 · 시험 알림
npm run build && tts-say "Build OK" || tts-say "Build failed"
```

### 하위 명령

| 명령 | 하는 일 |
|---|---|
| `tts-say "text"` · `tts-say speak [옵션] "text"` | 읽기 · 파일 저장 |
| `tts-say voices [--engine say\|sag] [--search X] [--limit N]` | 보이스 목록(`--engine` 없으면 쓸 수 있는 엔진 둘 다) |
| `tts-say config {show\|set\|unset\|example-env\|path}` | config 관리(`~/.config/tts-say/config.json`) |

### `speak` 옵션

| 옵션 | 엔진 | 뜻 |
|---|---|---|
| `--engine {auto,say,sag}` | 둘 다 | 엔진 강제 |
| `--voice`, `-v` | 둘 다 | 보이스 이름 · ID |
| `--output`, `-o` | 둘 다 | 오디오 파일로 저장 |
| `--say-rate` | say | 분당 단어 수 |
| `--model-id` | sag | ElevenLabs 모델 |
| `--lang` | sag | 언어 코드(ko, en …) |
| `--speed` | sag | 속도 배수 |
| `--stability` | sag | 보이스 안정도 0–1 |
| `--style` | sag | 스타일 강조 0–1 |
| `--similarity` | sag | 보이스 유사도 0–1 |
| `--speaker-boost` | sag | 또렷하게 |
| `--no-play` | sag | 재생 안 함(파일만) |

엔진에 맞지 않는 옵션은 말없이 무시됩니다.

### 엔진 · 옵션 고르는 차례

- 엔진: `--engine` 옵션 → config 의 `default_engine` → 자동(API 키가 있으면 `sag`, 없으면 `say`).
- 옵션: 명령 인자 → config 기본값(`tts-say config set …`) → 엔진 내장 기본값.
- config 는 점 경로로 고칩니다: `tts-say config set sag.stability 0.6`.
- 모델 · 발음 팁 · v3 오디오 태그(`[whispers]` 등) · 보이스 검색은 [skill/references/engines.md](skill/references/engines.md) 에 있습니다.

### 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| `tts-say: command not found` | PATH 에 없음 | `echo $PATH` 확인 후 `~/.local/bin` 추가 |
| `sag: command not found` | `sag` 미설치 | `brew install steipete/tap/sag` |
| `ELEVENLABS_API_KEY not set` | 환경 변수 없음 | `~/.zshrc` 에 export 추가 후 `source ~/.zshrc` |
| `voice "X" not found` | 보이스 이름이 틀림 | `tts-say voices --engine sag` 로 확인 |
| `say` 로 한국어가 안 나옴 | 보이스 미설치 | 시스템 설정 > 접근성 > 음성 콘텐츠에서 한국어 보이스 받기 |

## 요구사항

- macOS (`say` 내장)
- Python 3.10+
- 선택: `sag`(`brew install steipete/tap/sag`) + ElevenLabs API 키(`ELEVENLABS_API_KEY`) — 없으면 `say` 만으로 동작합니다.

## 링크

- [INSTALL.md](INSTALL.md) — 에이전트용 설치 안내
- [skill/SKILL.md](skill/SKILL.md) — 에이전트 스킬
- [skill/references/engines.md](skill/references/engines.md) — 엔진별 옵션 · 모델
- [cli/install.md](cli/install.md) — CLI 만 설치
- [AI Feature Pack 카탈로그](../../README.ko.md)
