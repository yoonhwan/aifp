<div align="center">

# yt-transcribe

**YouTube 링크 하나로 로컬 전사본과 AI 요약 문서를 만듭니다 — whisper.cpp 오프라인 STT 라 API 키가 필요 없습니다.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- YouTube 영상의 오디오만 로컬로 내려받습니다(`ytdl`).
- whisper.cpp(`whisper-cli`)로 오프라인 전사를 합니다. API 키가 없고 무료이며, 한국어 · 영어 · 일본어 등 언어를 자동 감지합니다. Apple Silicon 에서는 Metal 가속을 씁니다.
- 에이전트가 전사본으로 요약 · 아웃라인 · 키포인트를 쓰고, 원본 URL 을 넣은 `README.md` 하나로 저장합니다.
- 저장 경로는 매번 사용자에게 묻습니다(예: Obsidian 볼트 폴더). 끝나면 임시 파일을 모두 지웁니다.

## 빠른 시작

```bash
# 1) OpenClaw 에이전트에게: "feature-pack/yt-transcribe/INSTALL.md 를 읽고 설치해줘"
# 2) 에이전트에게 YouTube URL 을 보내거나, CLI 를 바로 써 봅니다
ytdl info "https://youtube.com/watch?v=VIDEO_ID"
```

## 설치

에이전트에게 맡기려면 «`feature-pack/yt-transcribe/INSTALL.md` 를 읽고 설치해줘» 라고 말하세요. `INSTALL.md` 는 OpenClaw 에이전트가 읽고 스스로 설치하는 프롬프트이고, `{{OPENCLAW_WORKSPACE}}`(기본 `~/.openclaw/workspace`) · `{{OBSIDIAN_VAULT_PATH}}` · `{{DEFAULT_SAVE_PATH}}` 는 사용자에게 물어서 채웁니다.

손으로 할 때는 아래 차례입니다. `ytdl` 을 못 찾으면 PATH 에 `~/.cargo/bin` 을 넣습니다.

```bash
cargo install rust-yt-downloader          # ytdl
brew install whisper-cpp ffmpeg yt-dlp
mkdir -p ~/.whisper/models
curl -L -o ~/.whisper/models/ggml-small.bin \
  "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin"
# feature-pack/yt-transcribe/ 에서 — 스킬 복사
cp -r skill/ ~/.openclaw/workspace/skills/yt-transcribe
```

## 사용법

### 파이프라인

에이전트에게 YouTube URL 을 보내거나 «유튜브 전사해줘» · «영상 내용 정리해줘» 처럼 말하면 시작합니다.

```text
YouTube URL
  ↓ ytdl audio (MP3)
  ↓ ffmpeg (MP3 → 16kHz mono WAV)
  ↓ whisper-cli (STT)
  ↓ AI (summary + outline + key points)
  ↓ README.md (save_to)
  ↓ temp files deleted
```

### 매개변수

| 매개변수 | 기본값 | 뜻 |
|---|---|---|
| `url` | (필수) | YouTube URL |
| `save_to` | (필수 · 사용자에게 물음) | 문서를 저장할 폴더 |
| `language` | `auto` | STT 언어 코드(`auto` · `ko` · `en` 등) |
| `model` | `small` | Whisper 모델(`small` · `medium` · `large-v3`) |
| `format` | `mp3` | 오디오 내려받기 형식 |

### CLI

```bash
ytdl info "https://youtube.com/watch?v=VIDEO_ID"
ytdl audio "https://youtube.com/watch?v=VIDEO_ID" -f mp3 -o ~/Downloads
ytdl download "https://youtube.com/watch?v=VIDEO_ID" -q 1080p -f mp4 -o ~/Downloads
ffmpeg -i audio.mp3 -ar 16000 -ac 1 -c:a pcm_s16le audio.wav -y
whisper-cli -m ~/.whisper/models/ggml-small.bin -l auto -otxt -f audio.wav --output-file transcript
```

### Whisper 모델

| 모델 | 크기 | 용도 |
|---|---|---|
| `small` | 462MB | 일상 전사(기본) |
| `medium` | 1.5GB | 더 높은 정확도 · 1시간 넘는 영상 |
| `large-v3` | 2.9GB | 가장 높은 정확도 |

### 문제 해결

| 문제 | 해결 |
|---|---|
| `ytdl: command not found` | PATH 에 `~/.cargo/bin` 추가 |
| ytdl 빌드 실패 | `brew install cmake` 뒤 다시 |
| ytdl 내려받기 실패 | 비공개 · 멤버십 영상 — 공개 영상으로 다시 |
| 전사 품질이 낮음 | `medium` · `large-v3` 모델로 바꿈 |
| 한국어가 깨지거나 인식 안 됨 | `-l ko` 로 언어 지정 |

## 요구사항

- macOS(Apple Silicon 권장 · Intel 도 지원)
- Homebrew · Rust/Cargo
- 디스크 여유 500MB 이상(Whisper 모델)
- OpenClaw 에이전트 환경 · 선택: Obsidian
- API 키 · 계정: 없음
- 설치 시간: 약 10분

## 링크

- [INSTALL.md](INSTALL.md)
- [skill/SKILL.md](skill/SKILL.md) — 에이전트 스킬
- [cli/install.md](cli/install.md)
- [test/verify.md](test/verify.md)
- [AI Feature Pack 목록](../../README.ko.md)
