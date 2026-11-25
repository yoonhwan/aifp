<div align="center">

# yt-transcribe

**一个 YouTube 链接,生成本地转写稿和 AI 摘要文档 —— 使用 whisper.cpp 离线 STT,无需 API 密钥。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 只把 YouTube 视频的音频下载到本地(`ytdl`)。
- 用 whisper.cpp(`whisper-cli`)离线转写。无需 API 密钥、免费,自动识别韩语 · 英语 · 日语等语言。在 Apple Silicon 上使用 Metal 加速。
- 智能体根据转写稿写出摘要 · 大纲 · 要点,连同原始 URL 保存为一个 `README.md`。
- 每次都会询问保存位置(例如 Obsidian 库中的文件夹)。结束后删除所有临时文件。

## 快速开始

```bash
# 1) 对 OpenClaw 智能体说: "阅读 feature-pack/yt-transcribe/INSTALL.md 并安装"
# 2) 把 YouTube URL 发给智能体,或者直接试用 CLI
ytdl info "https://youtube.com/watch?v=VIDEO_ID"
```

## 安装

让智能体来装:对它说"阅读 `feature-pack/yt-transcribe/INSTALL.md` 并安装"。`INSTALL.md` 是供 OpenClaw 智能体阅读并自行完成安装的提示词,`{{OPENCLAW_WORKSPACE}}`(默认 `~/.openclaw/workspace`) · `{{OBSIDIAN_VAULT_PATH}}` · `{{DEFAULT_SAVE_PATH}}` 会询问用户后填入。

手动安装按下面的顺序。找不到 `ytdl` 时,把 `~/.cargo/bin` 加入 PATH。

```bash
cargo install rust-yt-downloader          # ytdl
brew install whisper-cpp ffmpeg yt-dlp
mkdir -p ~/.whisper/models
curl -L -o ~/.whisper/models/ggml-small.bin \
  "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin"
# 在 feature-pack/yt-transcribe/ 下 —— 复制技能
cp -r skill/ ~/.openclaw/workspace/skills/yt-transcribe
```

## 用法

### 流程

把 YouTube URL 发给智能体,或者说"转写这个 YouTube 视频""整理一下视频内容"即可开始。

```text
YouTube URL
  ↓ ytdl audio (MP3)
  ↓ ffmpeg (MP3 → 16kHz mono WAV)
  ↓ whisper-cli (STT)
  ↓ AI (summary + outline + key points)
  ↓ README.md (save_to)
  ↓ temp files deleted
```

### 参数

| 参数 | 默认值 | 含义 |
|---|---|---|
| `url` | (必填) | YouTube URL |
| `save_to` | (必填 · 每次询问) | 保存文档的文件夹 |
| `language` | `auto` | STT 语言代码(`auto` · `ko` · `en` 等) |
| `model` | `small` | Whisper 模型(`small` · `medium` · `large-v3`) |
| `format` | `mp3` | 音频下载格式 |

### CLI

```bash
ytdl info "https://youtube.com/watch?v=VIDEO_ID"
ytdl audio "https://youtube.com/watch?v=VIDEO_ID" -f mp3 -o ~/Downloads
ytdl download "https://youtube.com/watch?v=VIDEO_ID" -q 1080p -f mp4 -o ~/Downloads
ffmpeg -i audio.mp3 -ar 16000 -ac 1 -c:a pcm_s16le audio.wav -y
whisper-cli -m ~/.whisper/models/ggml-small.bin -l auto -otxt -f audio.wav --output-file transcript
```

### Whisper 模型

| 模型 | 大小 | 用途 |
|---|---|---|
| `small` | 462MB | 日常转写(默认) |
| `medium` | 1.5GB | 更高准确率 · 超过 1 小时的视频 |
| `large-v3` | 2.9GB | 最高准确率 |

### 故障排查

| 问题 | 解决 |
|---|---|
| `ytdl: command not found` | 把 `~/.cargo/bin` 加入 PATH |
| ytdl 构建失败 | `brew install cmake` 后重试 |
| ytdl 下载失败 | 私密或会员专属视频 —— 换公开视频重试 |
| 转写质量低 | 换用 `medium` 或 `large-v3` 模型 |
| 韩语乱码或无法识别 | 用 `-l ko` 指定语言 |

## 环境要求

- macOS(推荐 Apple Silicon · 也支持 Intel)
- Homebrew · Rust/Cargo
- 至少 500MB 可用磁盘空间(Whisper 模型)
- OpenClaw 智能体环境 · 可选:Obsidian
- API 密钥 / 账号:无
- 安装时间:约 10 分钟

## 链接

- [INSTALL.md](INSTALL.md)
- [skill/SKILL.md](skill/SKILL.md) —— 智能体技能
- [cli/install.md](cli/install.md)
- [test/verify.md](test/verify.md)
- [AI Feature Pack 目录](../../README.zh-CN.md)
