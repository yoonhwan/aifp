<div align="center">

# memory-system

**OpenClaw エージェントに 3 層の記憶構造を組み込みます — ワークスペースのメモリファイル、セカンドブレインとしての Obsidian ボールト、ボールト全体を対象にしたメモリ検索(NotebookLM は任意)。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- エージェントが会話 · 決定 · 教訓を長期記憶 `MEMORY.md` とデイリーノート `memory/YYYY-MM-DD.md` に蓄積します。
- Obsidian ボールトにフォルダー構成(Daily · News-Links · Meetings · People · Projects · Reference · Ideas · Archive など)と `HOME.md` · インデックスノートを作ります。
- ボールト全体をエージェントのメモリ検索の範囲に入れます(`extraPaths` · OpenAI 埋め込み · ファイル変更の監視)。
- デイリーノートと `MEMORY.md` をボールトの `Daily/` にミラーします(シンボリックリンクまたは定期コピー)。
- ニュースのリンクはノートに、会話の記録は人物プロフィールに蓄積します。
- 任意: `nlm` CLI でボールトの文書を NotebookLM のソースに追加し、ソースに基づく Q&A を行います。

## クイックスタート

```bash
# 1) OpenClaw エージェントに: "feature-pack/memory-system/INSTALL.md を読んでインストールして"
# 2) インストール後に確認
ls ~/.openclaw/workspace/MEMORY.md
obsidian-cli print-default
```

## インストール

エージェントに任せるなら「`feature-pack/memory-system/INSTALL.md` を読んでインストールして」と伝えてください。`INSTALL.md` は OpenClaw エージェントが読んで自分でインストールを進めるプロンプトです。`{{PLACEHOLDER}}` があると、エージェントがユーザーに質問して埋めます。

| プレースホルダー | 意味 | 既定値 |
|---|---|---|
| `{{OC_WORKSPACE}}` | OpenClaw ワークスペースのパス | `~/.openclaw/workspace` |
| `{{VAULT_PATH}}` | Obsidian ボールトの絶対パス | — |
| `{{VAULT_NAME}}` | Obsidian ボールトの名前(フォルダー名) | — |

インストールの順番: ① ワークスペースのメモリファイル ② ボールトのフォルダー構成 + obsidian-cli ③ メモリ検索の統合 ④ `TOOLS.md` に Obsidian の項目 ⑤ デイリーメモリのミラー ⑥ NotebookLM 連携(任意) ⑦ インストール確認。手動の場合の主なコマンドは次のとおりです。

```bash
brew install yakitrak/yakitrak/obsidian-cli
obsidian-cli set-default "my-vault"
# openclaw.json を編集したあと設定を反映
openclaw gateway restart
```

## 使い方

### 3 つの層

| 層 | 内容 | 場所 |
|---|---|---|
| 1 · ワークスペースのメモリ | 長期記憶(整理済み) + デイリーノート(生ログ) | `MEMORY.md` · `memory/*.md` |
| 2 · Obsidian ボールト | デイリーのミラー · リンクノート · 会話の記録 · 人物プロフィール | `Daily/memory/` · `News-Links/` · `Meetings/` · `People/` |
| 3 · NotebookLM(任意) | ソースに基づく Q&A | `nlm` CLI |

### セッションのルール

- セッション開始時に `exec("ls memory/")` でファイル一覧を見て、今日 · 昨日のデイリーノートを読みます。メインセッションなら `MEMORY.md` も読みます。
- `read("memory")` のようにフォルダーを丸ごと読まないでください(EISDIR エラー)。ファイルを 1 つずつ読みます。
- デイリーノートに個人情報 · API キーを書きません。`MEMORY.md` はグループチャットでは読み込みません。
- デイリーノートの大事な内容は、定期的に `MEMORY.md` に移して整理します。

### メモリ検索の設定

`openclaw.json` に入れる設定です。`OPENAI_API_KEY` が OpenClaw の環境変数か設定に必要です。

```json
{
  "agents": {
    "defaults": {
      "memorySearch": {
        "enabled": true,
        "sources": ["memory", "sessions"],
        "extraPaths": ["{{VAULT_PATH}}"],
        "provider": "openai",
        "model": "text-embedding-3-small",
        "sync": { "watch": true, "watchDebounceMs": 1500 },
        "query": {
          "hybrid": { "enabled": true, "vectorWeight": 0.7, "textWeight": 0.3, "candidateMultiplier": 4 }
        }
      }
    }
  }
}
```

### NotebookLM

`notebooklm` パックが必要な任意の手順です。なければ飛ばしてください。

```bash
nlm notebook create "my-vault Knowledge Base"
nlm source add <notebook-id> --file "<vault-path>/HOME.md"
nlm chat query <notebook-id> "このプロジェクトで一番重要な決定は?"
```

### トラブルシューティング

- メモリ検索にボールトのファイルが出ない: `extraPaths` のボールト絶対パス · `watch: true` · OpenAI API キーを確認し、`openclaw gateway restart` を実行します。大きなボールトはインデックス作成に数分 〜 数十分かかることがあります。
- obsidian-cli がボールトを見つけられない: `obsidian-cli set-default` をもう一度実行し、Obsidian アプリでそのボールトを一度以上開いたか確認します。
- iCloud のボールトではシンボリックリンクが同期されないことがあります。その場合は定期コピー(rsync)でミラーします。
- NotebookLM の認証に失敗する: `notebooklm` パックの認証手順を見てください(Chrome が必要)。

## 必要なもの

- macOS(Apple Silicon または Intel)
- OpenClaw のインストールと起動
- Obsidian アプリ · obsidian-cli(Homebrew)
- API キー / アカウント: OpenAI API キー(埋め込み `text-embedding-3-small`) · 任意: `nlm` CLI と Google アカウント(NotebookLM)
- 所要時間: 約 15 分

## リンク

- [INSTALL.md](INSTALL.md)
- [skill/SKILL.md](skill/SKILL.md) — エージェントのスキル
- [obsidian/setup.md](obsidian/setup.md)
- [test/verify.md](test/verify.md)
- [notebooklm パック](../notebooklm/)
- [AI Feature Pack カタログ](../../README.ja.md)
