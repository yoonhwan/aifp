<div align="center">

# yt-transcribe

**Turns a YouTube link into a local transcript and an AI summary document — offline STT with whisper.cpp, so no API key is needed.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Downloads only the audio of a YouTube video to your machine (`ytdl`).
- Transcribes offline with whisper.cpp (`whisper-cli`). No API key, free, and it detects the language (Korean, English, Japanese and more). Uses Metal acceleration on Apple Silicon.
- The agent writes a summary, an outline and key points from the transcript and saves them with the source URL in a single `README.md`.
- Asks you where to save every time (for example, an Obsidian vault folder). Deletes all temporary files at the end.

## Quick start

```bash
# 1) Tell your OpenClaw agent: "Read feature-pack/yt-transcribe/INSTALL.md and install it"
# 2) Send a YouTube URL to the agent, or try the CLI directly
ytdl info "https://youtube.com/watch?v=VIDEO_ID"
```

## Install

To let your agent do it, say "Read `feature-pack/yt-transcribe/INSTALL.md` and install it". `INSTALL.md` is a prompt that an OpenClaw agent reads to install everything by itself. It asks you for `{{OPENCLAW_WORKSPACE}}` (default `~/.openclaw/workspace`), `{{OBSIDIAN_VAULT_PATH}}` and `{{DEFAULT_SAVE_PATH}}`.

Manual steps are below. If `ytdl` is not found, add `~/.cargo/bin` to PATH.

```bash
cargo install rust-yt-downloader          # ytdl
brew install whisper-cpp ffmpeg yt-dlp
mkdir -p ~/.whisper/models
curl -L -o ~/.whisper/models/ggml-small.bin \
  "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin"
# from feature-pack/yt-transcribe/ — copy the skill
cp -r skill/ ~/.openclaw/workspace/skills/yt-transcribe
```

## Usage

### Pipeline

Send a YouTube URL to the agent, or say something like "transcribe this YouTube video" or "summarize this video".

```text
YouTube URL
  ↓ ytdl audio (MP3)
  ↓ ffmpeg (MP3 → 16kHz mono WAV)
  ↓ whisper-cli (STT)
  ↓ AI (summary + outline + key points)
  ↓ README.md (save_to)
  ↓ temp files deleted
```

### Parameters

| Parameter | Default | Meaning |
|---|---|---|
| `url` | (required) | YouTube URL |
| `save_to` | (required · asked every time) | Folder to save the document |
| `language` | `auto` | STT language code (`auto` · `ko` · `en` and more) |
| `model` | `small` | Whisper model (`small` · `medium` · `large-v3`) |
| `format` | `mp3` | Audio download format |

### CLI

```bash
ytdl info "https://youtube.com/watch?v=VIDEO_ID"
ytdl audio "https://youtube.com/watch?v=VIDEO_ID" -f mp3 -o ~/Downloads
ytdl download "https://youtube.com/watch?v=VIDEO_ID" -q 1080p -f mp4 -o ~/Downloads
ffmpeg -i audio.mp3 -ar 16000 -ac 1 -c:a pcm_s16le audio.wav -y
whisper-cli -m ~/.whisper/models/ggml-small.bin -l auto -otxt -f audio.wav --output-file transcript
```

### Whisper models

| Model | Size | Use |
|---|---|---|
| `small` | 462MB | Everyday transcription (default) |
| `medium` | 1.5GB | Higher accuracy · videos over 1 hour |
| `large-v3` | 2.9GB | Highest accuracy |

### Troubleshooting

| Problem | Fix |
|---|---|
| `ytdl: command not found` | Add `~/.cargo/bin` to PATH |
| ytdl build fails | `brew install cmake`, then retry |
| ytdl download fails | Private or members-only video — retry with a public video |
| Low transcript quality | Switch to the `medium` or `large-v3` model |
| Korean text broken or not recognized | Set the language with `-l ko` |

## Requirements

- macOS (Apple Silicon recommended · Intel also supported)
- Homebrew · Rust/Cargo
- At least 500MB free disk space (Whisper model)
- OpenClaw agent environment · optional: Obsidian
- API keys / accounts: none
- Install time: about 10 minutes

## Links

- [INSTALL.md](INSTALL.md)
- [skill/SKILL.md](skill/SKILL.md) — agent skill
- [cli/install.md](cli/install.md)
- [test/verify.md](test/verify.md)
- [AI Feature Pack catalog](../../README.md)
