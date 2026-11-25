<div align="center">

# rag-consumer

**登録したエージェントの会話記録だけを読んで `rag` エンジンに入れ、検索・記憶・バックアップを受け持つ対のパック (CLI `ai-rag-consumer`)**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- 設定ファイルにパスを書いて登録した Codex rollout JSONL ファイルだけを読みます。セッションを自分で探したり、フォルダを監視したりはしません。
- 読んだ位置(バイト範囲・checksum)を暗号化された SQLCipher の台帳に残すので、途中で止まっても続きから読めます。メッセージ本文は台帳にためません。
- 保存する前に、バージョン付きのマスキング規則(redaction)をかけます。規則を通らなければ書きません。
- 会話の区間を `rag` エンジンに発行し、`search` で探せます。過去の会話は検索とは別の不変な暗号化 archive にまとめ、`archive-search` で探せます。
- 任意: 会話から記憶の候補を取り出し、原文の引用と照らし合わせたうえで、人が確定・却下・検証します。
- ストアの暗号化バックアップと、バックアップの検証。
- 1 回だけ動く `tick` を、launchd か macOS のメニューバーアプリ(AIRAG.app)が 5 分ごとに呼びます。

## クイックスタート

```bash
cd feature-pack/rag-consumer
uv venv --python 3.13
uv pip install ../rag .                     # rag パック(ai-feature-rag)とこのパックを一緒にインストール

# ストアの鍵 3 つ + rag DB の鍵 — 64 桁の hex、すべて別の値 (ランタイムは鍵を作らない)
export AIRAG_CONSUMER_KEY_HEX=<64-hex> AIRAG_PROJECTION_KEY_HEX=<64-hex> AIRAG_ARCHIVE_KEY_HEX=<64-hex>
export AIRAG_PROFILE_SOURCE_KEY_HEX=<64-hex>

.venv/bin/ai-rag-consumer --config /abs/path/runtime.json init
.venv/bin/ai-rag-consumer --config /abs/path/runtime.json run --once
.venv/bin/ai-rag-consumer --config /abs/path/runtime.json search "query"
```

## インストール

### INSTALL.md なし

このパックにはまだ `INSTALL.md` も元の README もありません。下の手順は `pyproject.toml`・ソースの先頭コメント・`ops/`・`macos/` で確かめたものです。エージェントに任せるときは「`feature-pack/rag-consumer/README.md` を読んでインストールして」と伝えます。

### 手動インストール

パッケージ名は `ai-feature-rag-consumer`、入口のコマンドは `ai-rag-consumer` です。依存する `ai-feature-rag==0.1.0` は同じリポジトリの `rag` パックなので、一緒に入れます(クイックスタートの `uv pip install ../rag .`)。

1. 鍵を 4 つ、シークレットストアに作っておきます(それぞれ 32 バイト = 64 桁の hex・すべて別の値)。
2. `runtime.json` を書きます(下の「ランタイム設定」)。パスはすべて絶対パスで、シンボリックリンクは拒否されます。
3. `init` で台帳・projection DB・archive・バックアップのフォルダを作ります。
4. `run --once` で 1 回動かしてみて、下のように定期実行をつけます。

### 5 分ごとに動かす

```bash
# A) launchd — テンプレートの __PYTHON__ · __CONFIG__ · __CREDENTIALS__ · __LOG_DIR__ を埋めて
cp ops/com.airag.consumer.plist.template ~/Library/LaunchAgents/com.airag.consumer.plist
launchctl load ~/Library/LaunchAgents/com.airag.consumer.plist

# B) メニューバーアプリ AIRAG.app — Xcode なしで swiftc だけ必要
bash macos/build.sh            # ビルド + 署名 (署名 ID がなければ ad-hoc)
bash macos/build.sh test       # 純粋ロジックのテスト (アプリは起動しない)
bash macos/build.sh install    # ~/Applications/AIRAG.app にコピー
```

- tick 1 回 = consumer の 1 パスです。やり直しは launchd の次の周期が受け持ちます。
- 鍵は `--credentials` で渡すローカル設定ファイルから埋めます(1Password CLI `op`、または所有者だけが読める鍵ファイル)。すでに環境変数にある鍵が優先されます。
- AIRAG.app はメニューからログイン項目として自分を登録します。パスは `~/.config/airag/app.json` の `python` · `config` · `credentials` · `log_dir` で変えられます。

## 使い方

### コマンド

すべてのコマンドは `ai-rag-consumer --config <runtime.json> <コマンド>` の形で、JSON を 1 行出します。

| コマンド | すること |
|---|---|
| `init` | 台帳・projection DB・archive・バックアップのフォルダを作る |
| `run [--once] [--task-completed] [--save] [--allow-gaps]` | 登録したソースを読んで発行 · `--once` がなければ `poll_seconds` ごとに繰り返す (Ctrl-C で停止) |
| `status` | 現在の状態 |
| `search "<query>" [--limit N]` | 発行した会話を検索 (既定 5) |
| `archive-search "<query>" [--limit N]` | archive を検索 (既定 20) |
| `memory-candidates --state <state> [--limit N] [--skip N]` | 記憶候補の一覧 |
| `memory-confirm` · `memory-reject` · `memory-verify <candidate_id>` | 記憶候補の確定・却下・検証 |
| `backup` | 暗号化バックアップを作る |
| `verify <backup_id>` | バックアップを検証 |

`python -m airag_consumer.tick --config <runtime.json> [--credentials <file>] [--log-dir <dir>]` は 1 パス用の入口です(終了コード 0 ok · 10 skipped · 20 config · 30 key · 40 runtime · 50 internal)。

### ランタイム設定

`runtime.json`(`schema_version` = 1)の必須項目:

| 項目 | 意味 |
|---|---|
| `project_root` | プロジェクトのフォルダ (絶対パス · 存在すること) |
| `owner_id` · `tenant_id` · `project_id` | 識別子 (英字 · 数字 · `_` · `-`) |
| `consumer_db` · `projection_db` | 台帳 DB · projection DB のパス |
| `archive_root` · `backup_root` | archive · バックアップのフォルダ |
| `profile_source_db` · `profile_key` | 処理プロファイルを持つ `rag` DB と、その `profile_key` (64 桁の hex) |
| `collection` | 発行先の `rag` collection 名 |
| `sources` | 読むファイルの一覧 — 各項目に `path` · `session_id` · `source_id` |

任意項目: `token_mode`(既定 `estimated`)· `allow_gaps` · `memory_enabled` · `memory_endpoint` · `memory_model` · `poll_seconds`(既定 30)· `reference`。

### 環境変数の鍵

| 名前 | 用途 |
|---|---|
| `AIRAG_CONSUMER_KEY_HEX` | 台帳 DB の鍵 |
| `AIRAG_PROJECTION_KEY_HEX` | projection DB の鍵 |
| `AIRAG_ARCHIVE_KEY_HEX` | archive の鍵 |
| `AIRAG_PROFILE_SOURCE_KEY_HEX` | `profile_source_db`(rag DB)の鍵 · ストアを最初に作るときに必要 |
| `AIRAG_MEMORY_API_KEY` | 任意 · 記憶抽出サーバーの鍵 |

鍵はすべて 64 桁の hex で、互いに別の値である必要があります。ランタイムは関係のない子プロセスにこれらの値を渡しません。

## 必要なもの

- Python 3.13 以上 3.15 未満 · `uv`
- `rag` パック (`ai-feature-rag` 0.1.0) · `sqlcipher3` 0.6.2
- 定期実行: macOS の launchd、または AIRAG.app をビルドする `swiftc`
- 任意: 1Password CLI `op` (tick の鍵の供給元) · 記憶抽出サーバー (`memory_endpoint` · `memory_model`)
- API キー / アカウント: 記憶抽出を有効にするときだけ `AIRAG_MEMORY_API_KEY`

## リンク

- [rag](../rag/README.ja.md) — このパックが使う暗号化 RAG エンジン
- [ops/com.airag.consumer.plist.template](ops/com.airag.consumer.plist.template) — launchd テンプレート
- [macos/build.sh](macos/build.sh) — AIRAG.app のビルド・テスト・インストール
- [AI Feature Pack カタログ](../../README.ja.md)
