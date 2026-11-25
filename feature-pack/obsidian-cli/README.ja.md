<div align="center">

# obsidian-cli

**エージェントが Obsidian のボールト(Markdown ノート)を CLI で参照・検索・作成・編集・削除・移動できるようにします**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- 参照: ボールトのファイル・フォルダ一覧を見て、ノートの内容を読みます。
- 検索: ノート名のあいまい検索・ノート内容の検索。
- 作成: ノートを作り(存在しないフォルダも一緒に作成)、デイリーノートを開きます。
- 編集: 上書き・追記(append)・frontmatter の参照・編集・キー削除。
- 削除・移動: ノートを削除し、移動や名前変更をするとウィキリンクを自動で直します。
- エージェントが `.md` ファイルを `read` / `write` / `edit` ツールで直接編集しても構いません。Obsidian が変更を検知します。

## クイックスタート

```bash
brew install yakitrak/yakitrak/obsidian-cli
obsidian-cli set-default "my-vault"
obsidian-cli create "Projects/my-note" --content "# My note"
obsidian-cli print "Projects/my-note"
```

## インストール

### エージェントに任せる

エージェントに「`feature-pack/obsidian-cli/INSTALL.md` を読んでインストールして」と頼んでください。所要時間は約3分です。エージェントがボールト名を尋ねます。

### 手動インストール

```bash
# 1. CLI のインストール — v0.2.3 以上
brew install yakitrak/yakitrak/obsidian-cli
obsidian-cli --version

# 2. 既定のボールトを設定 — Obsidian が把握しているボールト一覧はこのファイル
cat ~/Library/Application\ Support/obsidian/obsidian.json
obsidian-cli set-default "my-vault"
obsidian-cli print-default

# 3. スキル — OpenClaw 公式の obsidian スキルがあればコピー不要
ls /opt/homebrew/lib/node_modules/openclaw/skills/obsidian/SKILL.md
mkdir -p ~/.openclaw/workspace/skills/obsidian/
cp skill/SKILL.md ~/.openclaw/workspace/skills/obsidian/SKILL.md
```

4. `config/tools-section.md` を参考に、OpenClaw ワークスペースの `TOOLS.md` に Obsidian CLI の節(バイナリのパス・既定のボールト・主なコマンド)を追加します。
5. 任意: Obsidian アプリで Daily notes(Core plugin)を有効にします。おすすめの Community plugin は Dataview・Templater・Calendar です(`obsidian/setup.md`)。
6. `test/verify.md` の CRUD テストを実行します。すべての段階が exit code 0 ならインストール完了です。

## 使い方

### コマンド

| コマンド | 内容 |
|---|---|
| `obsidian-cli set-default "<vault>"`・`print-default [--path-only]` | 既定のボールトの設定・確認 |
| `obsidian-cli list ["<folder>"]` | ボールトのルートまたはフォルダの一覧 |
| `obsidian-cli print "<note>"` | ノートを読む |
| `obsidian-cli search "<query>"`・`search-content "<query>"` | 名前のあいまい検索・内容検索(インタラクティブ) |
| `obsidian-cli create "<note>" --content "<text>" [--open]` | ノート作成(フォルダは自動作成) |
| `obsidian-cli create "<note>" --content "<text>" --overwrite`・`--append` | 上書き・追記 |
| `obsidian-cli daily` | デイリーノートの作成・表示 |
| `obsidian-cli frontmatter "<note>" --print` | frontmatter の表示 |
| `obsidian-cli frontmatter "<note>" --edit --key <k> --value <v>`・`--delete --key <k>` | frontmatter の編集・キー削除 |
| `obsidian-cli move "<old>" "<new>"` | 移動・名前変更 + ウィキリンク更新 |
| `obsidian-cli delete "<note>"` | 削除 |
| `obsidian-cli open "<note>"` | Obsidian アプリで開く |

### コツ

- `search`・`search-content` はインタラクティブなので、エージェント環境では動きません。`grep -r` か `list` + `print` を使います。
- ノートの移動には `mv` ではなく必ず `move` を使います。`mv` はウィキリンクを壊します。
- ボールトのパスは直書きせず、`print-default --path-only` で取得します。
- `.obsidian/` フォルダには触れません(設定・プラグインの衝突)。
- 大量のノートを一度に直すときは、CLI よりファイルを直接編集する方が速いです。

### トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| `brew: command not found` | Homebrew が無い | Homebrew をインストール |
| `Cannot find note in vault` | 既定のボールト未設定・ノートのパス誤り | `set-default` を確認、パスから `.md` を外す |
| `search-content` が動かない | 非インタラクティブ環境 | `grep -r` または `list` + `print` |
| 作ったノートが Obsidian に出ない | iCloud 同期の遅れ | 数秒待ってアプリで再読み込み |
| URI handler のエラー | Obsidian アプリが起動していない | アプリを起動して再試行 |

## 必要なもの

- OS: macOS
- Homebrew
- Obsidian アプリ(URI handler)・ボールト1つ以上
- API キー・アカウント: 不要

## リンク

- [INSTALL.md](INSTALL.md) — エージェント向けのインストール手順
- [skill/SKILL.md](skill/SKILL.md) — OpenClaw スキル
- [config/tools-section.md](config/tools-section.md) — `TOOLS.md` に追加する節
- [obsidian/setup.md](obsidian/setup.md) — Obsidian アプリの設定
- [test/verify.md](test/verify.md) — インストール検証の CRUD テスト
- [AI Feature Pack カタログ](../../README.ja.md)
