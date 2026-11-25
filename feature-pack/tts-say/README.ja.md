<div align="center">

# tts-say

**macOS `say` と ElevenLabs `sag` をひとつのコマンド `tts-say` にまとめた TTS CLI**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- テキストを読み上げます(`tts-say "テキスト"`) · stdin パイプも受け付けます(`echo "テキスト" | tts-say`)。
- 音声ファイルに保存します(`tts-say speak -o out.mp3 "テキスト"`)。
- エンジンを自動で選びます — `ELEVENLABS_API_KEY` があれば `sag`、なければ macOS `say`。
- 既定のエンジン · ボイス · オプションを config に保存しておけば毎回適用されます。
- エンジンごとのボイス一覧を表示します(`tts-say voices`)。
- エージェントやスクリプトの音声通知に使えます: `pytest && tts-say "テスト成功"`。

## クイックスタート

```bash
# パックのフォルダで: CLI を PATH にコピー
cp skill/scripts/tts-say ~/.local/bin/tts-say
chmod +x ~/.local/bin/tts-say

# 最初の音声 (sag がなければ macOS say で読む)
tts-say "Build finished"
```

## インストール

### エージェントに任せる

エージェントに「`feature-pack/tts-say/INSTALL.md` を読んでインストールして」と伝えます。エージェントは `sag` のインストール(任意) → ElevenLabs API キー(任意) → CLI のコピー → 既定の config → スキルのインストール → 検証の順に進め、API キー · インストール先 · 既定のボイスを尋ねます。所要時間 (約3分)。

### 手動インストール

```bash
# 1. sag のインストール (任意 · ElevenLabs の高品質な音声)
brew install steipete/tap/sag
export ELEVENLABS_API_KEY="<your-key>"   # ~/.zshrc に書く

# 2. CLI を PATH にコピー (パックのフォルダで)
cp skill/scripts/tts-say ~/.local/bin/tts-say
chmod +x ~/.local/bin/tts-say

# 3. 既定の config
tts-say config set default_engine auto
tts-say config set say.voice Yuna
tts-say config set sag.model_id eleven_multilingual_v2
tts-say config set sag.lang ko

# 4. スキルのインストール (OpenClaw ワークスペース)
cp -r skill/ ~/.openclaw/workspace/skills/tts-say/

# 5. 検証
tts-say --help
tts-say config show
tts-say voices --engine say
```

- OpenClaw を使うなら、`config/tools-section.md` の内容をワークスペースの `TOOLS.md` に追記します(任意)。
- `~/.local/bin` が PATH にない場合は `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc` で追加します。

`INSTALL.md` が尋ねる値と既定値:

| プレースホルダー | 意味 | 既定値 |
|---|---|---|
| `{{ELEVENLABS_API_KEY}}` | ElevenLabs API キー(なければ `say` のみ) | なし |
| `{{TTS_INSTALL_PATH}}` | CLI のインストール先 | `~/.local/bin/tts-say` |
| `{{DEFAULT_ENGINE}}` | 既定のエンジン | `auto` |
| `{{SAG_DEFAULT_VOICE}}` | `sag` の既定ボイス | `tts-say voices --engine sag` の一覧から選ぶ |
| `{{OPENCLAW_SKILLS_PATH}}` | スキルのインストール先 | `~/.openclaw/workspace/skills` |
| `{{OPENCLAW_WORKSPACE}}` | ワークスペースのパス | `~/.openclaw/workspace` |

## 使い方

```bash
# 読み上げ (config の既定値を使う)
tts-say "Build finished"

# エンジンを指定
tts-say speak --engine say --voice Yuna "Hello"
tts-say speak --engine sag --voice Aria --lang ko "Hello"

# ファイルに保存
tts-say speak -o /tmp/alert.mp3 "Alert"

# ボイス一覧
tts-say voices --engine say
tts-say voices --engine sag --search korean --limit 10

# config
tts-say config show
tts-say config set sag.speed 1.1
tts-say config unset say.rate
tts-say config example-env
tts-say config path

# ビルド · テストの通知
npm run build && tts-say "Build OK" || tts-say "Build failed"
```

### サブコマンド

| コマンド | すること |
|---|---|
| `tts-say "text"` · `tts-say speak [オプション] "text"` | 読み上げ · ファイル保存 |
| `tts-say voices [--engine say\|sag] [--search X] [--limit N]` | ボイス一覧(`--engine` なしなら使えるエンジン両方) |
| `tts-say config {show\|set\|unset\|example-env\|path}` | config の管理(`~/.config/tts-say/config.json`) |

### `speak` のオプション

| オプション | エンジン | 意味 |
|---|---|---|
| `--engine {auto,say,sag}` | 両方 | エンジンを固定 |
| `--voice`, `-v` | 両方 | ボイス名 · ID |
| `--output`, `-o` | 両方 | 音声をファイルに保存 |
| `--say-rate` | say | 1 分あたりの単語数 |
| `--model-id` | sag | ElevenLabs のモデル |
| `--lang` | sag | 言語コード(ko, en …) |
| `--speed` | sag | 速度の倍率 |
| `--stability` | sag | ボイスの安定度 0–1 |
| `--style` | sag | スタイルの強さ 0–1 |
| `--similarity` | sag | ボイスの類似度 0–1 |
| `--speaker-boost` | sag | 明瞭さを上げる |
| `--no-play` | sag | 再生しない(ファイルのみ) |

エンジンに合わないオプションは黙って無視されます。

### エンジンとオプションの決まり方

- エンジン: `--engine` オプション → config の `default_engine` → 自動(API キーがあれば `sag`、なければ `say`)。
- オプション: コマンド引数 → config の既定値(`tts-say config set …`) → エンジン組み込みの既定値。
- config はドット区切りのパスで変更します: `tts-say config set sag.stability 0.6`。
- モデル · 発音のコツ · v3 オーディオタグ(`[whispers]` など) · ボイス検索は [skill/references/engines.md](skill/references/engines.md) にあります。

### トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| `tts-say: command not found` | PATH にない | `echo $PATH` を確認し `~/.local/bin` を追加 |
| `sag: command not found` | `sag` 未インストール | `brew install steipete/tap/sag` |
| `ELEVENLABS_API_KEY not set` | 環境変数がない | `~/.zshrc` に export を足して `source ~/.zshrc` |
| `voice "X" not found` | ボイス名の誤り | `tts-say voices --engine sag` で確認 |
| `say` で韓国語が出ない | ボイス未インストール | システム設定 > アクセシビリティ > 読み上げコンテンツ で韓国語ボイスをダウンロード |

## 必要なもの

- macOS (`say` は内蔵)
- Python 3.10+
- 任意: `sag`(`brew install steipete/tap/sag`) + ElevenLabs API キー(`ELEVENLABS_API_KEY`) — なくても `say` だけで動きます。

## リンク

- [INSTALL.md](INSTALL.md) — エージェント向けインストール手順
- [skill/SKILL.md](skill/SKILL.md) — エージェント用スキル
- [skill/references/engines.md](skill/references/engines.md) — エンジンごとのオプションとモデル
- [cli/install.md](cli/install.md) — CLI だけをインストール
- [AI Feature Pack カタログ](../../README.ja.md)
