<div align="center">

# notebooklm

**Google NotebookLM をターミナルから操作する `nlm` CLI と OpenClaw スキルのパッケージ。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- ソースに基づく Q&A: アップロードした文書だけを根拠に答えます。
- 文書からオーディオポッドキャストとビデオオーバービューを作ります。
- レポート・クイズ・フラッシュカードなどの学習資料を作ります。
- ディープリサーチで Web ソースを自動で集めて分析します。
- ノートブックの作成・削除・共有・エイリアス設定を管理します。
- Obsidian ボルトの文書を NotebookLM のソースとして使います。

## クイックスタート

```bash
# 1. インストール
uv tool install notebooklm-mcp-cli

# 2. 認証 (Chrome が開きます)
nlm login

# 3. 使う
nlm notebook list
nlm query notebook <notebook_id> "質問"
```

## インストール

エージェントに「Read feature-pack/notebooklm/INSTALL.md and install it」と頼めば進みます。手動で入れる場合は [INSTALL.md](INSTALL.md) の手順に従います。

1. `uv` で `nlm` CLI をインストールします（`notebooklm-mcp-cli`）。
2. `nlm login` で Google アカウントにログインし、`nlm auth status` で確認します。セッションは約 20 分有効で、切れたら `nlm login` をもう一度実行します。
3. このパックの `skill/` フォルダを OpenClaw ワークスペースのスキルフォルダにコピーします。
4. ワークスペースの `TOOLS.md` に NotebookLM セクションを追加します（内容は [INSTALL.md](INSTALL.md) にあります）。
5. 任意: Obsidian 連携を設定します。
6. `nlm --version`・`nlm auth status`・`nlm notebook list` で動作を確認します。

```bash
# uv が無ければインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# CLI のインストールと確認
uv tool install notebooklm-mcp-cli
nlm --version

# nlm が見つからないときは PATH に ~/.local/bin を追加
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc

# スキルをコピー (OpenClaw ワークスペースの既定値: ~/.openclaw/workspace)
cp -r skill/ ~/.openclaw/workspace/skills/notebooklm

# アップデート
uv tool upgrade notebooklm-mcp-cli
```

## 使い方

### 主なコマンド

```bash
# ノートブック
nlm notebook list
nlm notebook create "名前"
nlm notebook get <notebook_id>
nlm notebook describe <notebook_id>

# ソース
nlm source add <notebook_id> --file <path>
nlm source add <notebook_id> --url <url>
nlm source add <notebook_id> --text "内容" --title "タイトル"

# Q&A
nlm query notebook <notebook_id> "質問"

# 生成
nlm audio create <notebook_id> --confirm
nlm video create <notebook_id> --confirm
nlm report create <notebook_id> --confirm
nlm quiz create <notebook_id> --confirm
nlm flashcards create <notebook_id> --confirm
nlm mindmap create <notebook_id> --confirm
nlm slides create <notebook_id> --confirm

# リサーチ
nlm research start <notebook_id> "テーマ" --mode deep
nlm research status <notebook_id>

# ダウンロード
nlm download audio <notebook_id> <artifact_id> -o <path>

# エイリアス (UUID の代わりに短い名前)
nlm alias set myproject <notebook_id>
nlm alias list
```

### エージェントから Q&A するとき

- エージェントは常に `nlm query notebook` で、1 回の質問に 1 回の答えを受け取ります。
- `nlm chat start` (REPL モード) はエージェントが制御できないので使いません。
- すべてのコマンドの案内は `nlm --ai` で見られます。

### Obsidian 連携

プラグインではなく、CLI でファイルをアップロードする方式です。

```bash
# 専用のノートブックを作ってエイリアスを付ける
nlm notebook create "My Obsidian Vault"
nlm alias set vault <notebook_id>

# 文書をソースとしてアップロードする
nlm source add vault --file "<path-to-vault>/note.md" --wait

# 質問する
nlm query notebook vault "プロジェクトの構成を説明して"
```

### トラブルシューティング

| 症状 | 対処 |
|------|------|
| `nlm: command not found` | PATH に `~/.local/bin` を追加します |
| `uv: command not found` | uv をインストールします |
| "Cookies have expired" / "authentication may have expired" | `nlm login` をもう一度実行します |
| Chrome が開かない | Chrome をインストールします (`brew install --cask google-chrome`) |
| Rate limit エラー | 自動で 3 回再試行します。失敗が続くときは少し待ちます |
| ソースの追加に失敗する | ファイルが NotebookLM のソースサイズ上限を超えていないか確認します |

## 必要なもの

- macOS (Apple Silicon または Intel)
- Python 3.10+
- Google アカウント (NotebookLM を使える権限)
- Chrome ブラウザ (認証に使います)
- uv (無ければインストール手順で入れます)

## リンク

- [INSTALL.md](INSTALL.md) — インストールガイド
- [Obsidian 連携ガイド](obsidian/setup.md)
- [AI Feature Pack カタログ](../../README.ja.md)
