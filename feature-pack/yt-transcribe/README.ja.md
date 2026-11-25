<div align="center">

# yt-transcribe

**YouTube のリンク 1 つから、ローカルの文字起こしと AI 要約ドキュメントを作ります — whisper.cpp のオフライン STT なので API キーは不要です。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- YouTube 動画の音声だけをローカルにダウンロードします(`ytdl`)。
- whisper.cpp(`whisper-cli`)でオフライン文字起こしをします。API キー不要 · 無料で、韓国語 · 英語 · 日本語などの言語を自動判定します。Apple Silicon では Metal で高速化します。
- エージェントが文字起こしから要約 · アウトライン · 要点を書き、元の URL を入れた `README.md` 1 つに保存します。
- 保存先は毎回ユーザーに確認します(例: Obsidian ボールトのフォルダー)。最後に一時ファイルをすべて削除します。

## クイックスタート

```bash
# 1) OpenClaw エージェントに: "feature-pack/yt-transcribe/INSTALL.md を読んでインストールして"
# 2) エージェントに YouTube の URL を送るか、CLI を直接試す
ytdl info "https://youtube.com/watch?v=VIDEO_ID"
```

## インストール

エージェントに任せるなら「`feature-pack/yt-transcribe/INSTALL.md` を読んでインストールして」と伝えてください。`INSTALL.md` は OpenClaw エージェントが読んで自分でインストールを進めるプロンプトで、`{{OPENCLAW_WORKSPACE}}`(既定 `~/.openclaw/workspace`) · `{{OBSIDIAN_VAULT_PATH}}` · `{{DEFAULT_SAVE_PATH}}` はユーザーに質問して埋めます。

手動の場合は次の順番です。`ytdl` が見つからないときは PATH に `~/.cargo/bin` を追加します。

```bash
cargo install rust-yt-downloader          # ytdl
brew install whisper-cpp ffmpeg yt-dlp
mkdir -p ~/.whisper/models
curl -L -o ~/.whisper/models/ggml-small.bin \
  "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin"
# feature-pack/yt-transcribe/ から — スキルをコピー
cp -r skill/ ~/.openclaw/workspace/skills/yt-transcribe
```

## 使い方

### パイプライン

エージェントに YouTube の URL を送るか、「YouTube を文字起こしして」「動画の内容をまとめて」のように話しかけると始まります。

```text
YouTube URL
  ↓ ytdl audio (MP3)
  ↓ ffmpeg (MP3 → 16kHz mono WAV)
  ↓ whisper-cli (STT)
  ↓ AI (summary + outline + key points)
  ↓ README.md (save_to)
  ↓ temp files deleted
```

### パラメーター

| パラメーター | 既定値 | 意味 |
|---|---|---|
| `url` | (必須) | YouTube の URL |
| `save_to` | (必須 · 毎回確認) | ドキュメントを保存するフォルダー |
| `language` | `auto` | STT の言語コード(`auto` · `ko` · `en` など) |
| `model` | `small` | Whisper モデル(`small` · `medium` · `large-v3`) |
| `format` | `mp3` | 音声のダウンロード形式 |

### CLI

```bash
ytdl info "https://youtube.com/watch?v=VIDEO_ID"
ytdl audio "https://youtube.com/watch?v=VIDEO_ID" -f mp3 -o ~/Downloads
ytdl download "https://youtube.com/watch?v=VIDEO_ID" -q 1080p -f mp4 -o ~/Downloads
ffmpeg -i audio.mp3 -ar 16000 -ac 1 -c:a pcm_s16le audio.wav -y
whisper-cli -m ~/.whisper/models/ggml-small.bin -l auto -otxt -f audio.wav --output-file transcript
```

### Whisper モデル

| モデル | サイズ | 用途 |
|---|---|---|
| `small` | 462MB | 日常の文字起こし(既定) |
| `medium` | 1.5GB | より高い精度 · 1 時間を超える動画 |
| `large-v3` | 2.9GB | 最高の精度 |

### トラブルシューティング

| 問題 | 対処 |
|---|---|
| `ytdl: command not found` | PATH に `~/.cargo/bin` を追加 |
| ytdl のビルド失敗 | `brew install cmake` のあと再試行 |
| ytdl のダウンロード失敗 | 非公開 · メンバー限定動画 — 公開動画で再試行 |
| 文字起こしの品質が低い | `medium` · `large-v3` モデルに切り替え |
| 韓国語が化ける · 認識されない | `-l ko` で言語を指定 |

## 必要なもの

- macOS(Apple Silicon 推奨 · Intel も対応)
- Homebrew · Rust/Cargo
- 空きディスク 500MB 以上(Whisper モデル)
- OpenClaw エージェント環境 · 任意: Obsidian
- API キー / アカウント: なし
- 所要時間: 約 10 分

## リンク

- [INSTALL.md](INSTALL.md)
- [skill/SKILL.md](skill/SKILL.md) — エージェントのスキル
- [cli/install.md](cli/install.md)
- [test/verify.md](test/verify.md)
- [AI Feature Pack カタログ](../../README.ja.md)
