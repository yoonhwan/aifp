<div align="center">

# imsg

**macOS の Messages.app をターミナルから操作する CLI と OpenClaw スキル — エージェント · スクリプト · cron の iMessage 通知チャネルとしても使えます**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- **会話一覧** — 最近の iMessage / SMS の会話を見ます。
- **メッセージ履歴** — 1 つの会話の過去のメッセージを、日付フィルタ · 添付ファイル情報付きで見ます。
- **メッセージ送信** — テキストと添付ファイル(画像 · 文書など)を送ります。
- **リアルタイム受信監視** — 新しいメッセージが届くとストリームで出力します。
- **エージェント通知チャネル** — ほかのエージェント · コーディングツール · cron · CI から `imsg send` 1 行で iMessage 通知を送ります。
- CLI はサードパーティの Homebrew パッケージ `steipete/tap/imsg` で、このパックはそのインストール手順 · OpenClaw スキル · `TOOLS.md` セクションを収めています。

## クイックスタート

```bash
brew install steipete/tap/imsg
imsg --help                                        # コマンド一覧が出れば成功
imsg chats --limit 3 --json                        # 会話一覧 (Full Disk Access の確認)
imsg send --to "<your-phone>" --text "imsg インストールテスト"   # 自分に送る (Automation 権限の確認)
```

## インストール

### エージェントに任せる

エージェントに「Read feature-pack/imsg/INSTALL.md and install it」と伝えてください。`INSTALL.md` は OpenClaw エージェントが読んで自分でインストールするための文書で、プレースホルダ 3 つ(`{{OPENCLAW_WORKSPACE}}` · `{{USER_PHONE}}` · `{{NOTIFY_PHONE}}`)はエージェントがユーザーに聞いてから埋めます。

### 手動インストール

1. `brew install steipete/tap/imsg` で CLI を入れます。
2. ターミナルアプリ(Terminal.app · iTerm2 など)に **Full Disk Access** を与えます: システム設定 → プライバシーとセキュリティ → Full Disk Access。`chat.db` を読むのに必要です。
3. 最初の `imsg send` で「Terminal に Messages の制御を許可」のポップアップが出ます → 許可します(**Automation** 権限)。
4. OpenClaw を使うなら、スキルをコピーし、[`config/tools-section.md`](config/tools-section.md) のセクションをワークスペースの `TOOLS.md` に追加します。

```bash
SKILL_DIR="$HOME/.openclaw/workspace/skills/imsg"   # OpenClaw ワークスペースの既定パス
cp -r skill/ "$SKILL_DIR"
ls "$SKILL_DIR/SKILL.md"                            # スキルの確認
```

## 使い方

### コマンド

| コマンド | すること | 主なオプション |
|---|---|---|
| `imsg chats` | 会話一覧 | `--limit N` · `--json` · `--db <path>`(既定 `~/Library/Messages/chat.db`) |
| `imsg history` | 1 つの会話のメッセージ | `--chat-id <ID>` · `--limit N` · `--start` / `--end <ISO8601>` · `--participants` · `--attachments` · `--json` |
| `imsg send` | メッセージ送信 | `--to <phone/email>` または `--chat-id` · `--text` · `--file <path>` · `--service imessage\|sms\|auto` · `--region` |
| `imsg watch` | リアルタイム受信監視 | `--chat-id` · `--participants` · `--since-rowid` · `--debounce 250ms` · `--attachments` · `--json` |
| `imsg rpc` | stdin / stdout の JSON-RPC モード | MCP サーバーなどとの連携用 |

### 例

```bash
imsg chats --limit 10 --json                                   # chat-id を確認
imsg history --chat-id 1 --start 2026-03-01T00:00:00Z --attachments --json
imsg send --to "<your-phone>" --text "レポートです" --file ~/reports/daily.pdf
imsg send --chat-id 42 --text "返信します"
imsg watch --chat-id 1 --attachments --debounce 250ms
```

### 通知チャネル

どの CLI ツール · スクリプト · エージェントからでも `imsg send` 1 行で通知を送れます。よく使うならシェル関数として登録します。

```bash
# 作業が終わったら成功 / 失敗を通知
long_running_task && imsg send --to "<your-phone>" --text "作業完了" \
                  || imsg send --to "<your-phone>" --text "作業失敗"

# ~/.zshrc に追加 — 使い方: notify "ビルド完了"
notify() {
  imsg send --to "<your-phone>" --text "$*"
}
```

### トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| `imsg: command not found` | brew でインストールされていない | `brew install steipete/tap/imsg` |
| `permission denied`(chats) | Full Disk Access がない | システム設定 → プライバシー → Full Disk Access → ターミナルを追加 |
| 送信に失敗する | Automation が許可されていない | システム設定 → オートメーション → Terminal → Messages にチェック |
| 「Messages is not running」 | Messages.app が起動していない | Messages.app を起動して再試行 |
| 相手が iMessage 非対応 | SMS で送る必要がある | `--service sms` を追加 |
| chat-id がわからない | 会話 ID を確認していない | `imsg chats --json` で確認 |

## 必要なもの

- macOS(Apple Silicon または Intel) + iCloud アカウントでサインインした Messages.app
- Homebrew
- ターミナルアプリの Full Disk Access · Messages に対する Automation 権限
- 任意: スキルを使うなら OpenClaw
- API キー不要

## リンク

- [INSTALL.md](INSTALL.md) — エージェント向けインストール手順(ステップ · 検証チェックリスト · プレースホルダ)
- [skill/SKILL.md](skill/SKILL.md) — OpenClaw スキル(使う場面 · コマンドリファレンス)
- [config/tools-section.md](config/tools-section.md) — `TOOLS.md` に追加するセクション
- [AI Feature Pack カタログ](../../README.ja.md)
