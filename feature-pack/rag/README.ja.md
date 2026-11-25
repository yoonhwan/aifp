<div align="center">

# rag

**文書を暗号化されたローカル DB に入れて検索し、根拠を JSON で返す RAG エンジン `airag` (CLI `ai-rag`)**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- 原本・チャンク・ベクトルを暗号化された SQLite(SQLCipher)1 ファイルに保存します。ベクトルは sqlite-vec、キーワードは FTS5。
- 明示的なリクエストだけを処理します: `add` · `update` · `delete` · `manage restore`。フォルダ監視・スケジュール・自動探索はなく、利用側のプロジェクトがイベントを送ります。
- 更新すると新しいリビジョンができ、以前の原本バイトと過去の検索結果(manifest)は残ります。削除した原本は復元できます。
- 処理プロファイル(埋め込み + 任意の LLM + 正規化設定)は一度登録すると変わりません。LLM をつなぐと、意味グループ・タグ・要約・英訳を作ってから埋め込みます。
- 検索 = BM25 + ベクトル + RRF。結果から構造・参照・意味のつながりを予算(深さ・チャンク・トークン・バイト)の範囲で広げ、根拠の束として返します。
- 文書アダプタ(`documents` 追加インストール): PDF · DOCX · XLSX · HWP5 · HWPX、そして PNG · JPEG · BMP · TIFF の明示的な OCR・ビジョンモード。
- すべてのコマンドは JSON 応答ひとつ `{schema_version, request_id, ok, command, data, error}` を出します。バックアップ・復元・診断も同じ形です。
- エンジンは根拠を返すだけです。最終的な回答を書くのは上にいるエージェントの役目です。

### 処理の流れ

```text
原本 --[Docling · HWP/HWPX アダプタ · 会話アダプタ]--> 標準バンドル (Markdown + 構造 · アンカー)
  --[HybridChunker]--> チャンク --[埋め込み · FTS の発行]--> インデックス
  --[BM25 + ベクトル + RRF]--> 検索 --[予算つきの構造 · 意味の拡張]--> 根拠 (原本の返却を含む)
```

## クイックスタート

```bash
cd feature-pack/rag
uv sync                                     # .venv を作って airag をインストール

head -c 32 /dev/urandom > my.key            # 32 バイトの鍵 — なくすと DB を開けません
chmod 600 my.key
.venv/bin/ai-rag init my.db --key-fd 3 3< my.key
.venv/bin/ai-rag manage doctor              # 実行環境の診断
```

## インストール

### INSTALL.md なし

このパックにはまだ `INSTALL.md` がありません。エージェントに任せるときは「`feature-pack/rag/README.md` と `pyproject.toml` を読んでインストールして」と伝えると、下の手動インストールの手順に従います。

### 手動インストール

パッケージ名は `ai-feature-rag`、入口のコマンドは `ai-rag` です(同じコマンドの別名 `krb-rag` もあります)。

```bash
cd feature-pack/rag
uv sync                                     # 基本の依存関係
uv sync --extra documents                   # PDF · DOCX · XLSX · OCR アダプタ (docling · easyocr)
uv run pytest                               # オフラインのテスト (integration 印のテストは既定で飛ばす)
```

## 使い方

### コマンド

| コマンド | すること |
|---|---|
| `ai-rag init <db>` | 新しい暗号化 DB を作る |
| `ai-rag add` · `update` · `delete` | 原本の登録・更新(新リビジョン)・削除 — 同じ `--request-id` を送り直しても反映は 1 回だけ |
| `ai-rag search` | `--collection` · `--query` · `--profile-key` で検索 · `--expand` で同じスナップショットのまま拡張 |
| `ai-rag expand --manifest-id N` | 過去の検索結果から根拠を広げる (`--max-depth` · `--max-chunks` · `--max-tokens` · `--max-bytes` · `--max-edges`) |
| `ai-rag fetch original` · `source` · `chunk` · `manifest` · `expansion` | 原本バイト・正規化結果・チャンク・過去の検索・過去の拡張を取り出す |
| `ai-rag manage profile --config <file>` | 処理プロファイルの登録 (JSON ファイル: `embedding` · 任意の `llm` · `normalizer`) |
| `ai-rag manage status` · `list` · `show` | 状態・一覧・原本ひとつの表示 |
| `ai-rag manage retry` · `reindex` · `restore` | 失敗したジョブのやり直し・別プロファイルで再処理・削除した原本の復元 |
| `ai-rag manage backup` · `restore-backup` | バックアップ作成・バックアップから復元 |
| `ai-rag manage doctor` · `verify` | インストール診断・DB 検査 |

`init` 以外の DB コマンドは `--db <db>` と `--key-fd <fd>` を受け取ります。

### 例

```bash
K="--db my.db --key-fd 3"

# 1) 処理プロファイルの登録 — 応答 data の profile_key を控えておく
.venv/bin/ai-rag manage profile $K --config profile.json 3< my.key

# 2) テキストの原本を登録
.venv/bin/ai-rag add $K --request-id req-1 --collection notes --source-key note-1 \
  --text "hello" --profile-key <profile_key> 3< my.key

# 3) 検索 — 応答の manifest_id で後から expand · fetch manifest
.venv/bin/ai-rag search $K --collection notes --query "hello" \
  --profile-key <profile_key> --top-k 5 3< my.key
```

`profile.json` の `embedding` には `provider`(`lmstudio` または `openai-compatible`)· `endpoint` · `model` · `revision` · `dimension` · `tokenizer_revision`(固定したコミット・タグ)を入れます。全項目は [src/airag/embeddings.py](src/airag/embeddings.py) の `EmbeddingSpaceConfig`、LLM の項目は [src/airag/llm_enrichment.py](src/airag/llm_enrichment.py) の `ChatCompletionConfig` にあります。Python から直接呼ぶ例は [examples/explicit_consumer.py](examples/explicit_consumer.py) です。

### 鍵の扱い

- 鍵は 32 バイトの生の値で、`--key-fd` で渡す開いたファイル記述子からだけ読みます。コマンドライン引数やログに鍵は出ません。
- macOS Keychain から鍵を読む機能はまだありません。

### 既知の制限

- ベクトル検索は全件比較(O(N))です。ANN の性能や韓国語キーワード検索の品質は検証済みとは言いません。
- 対応しないもの: XLSX の再計算と array/data-table 数式、保護・配布用 HWP、DOCX のビットマップ以外の DrawingML の自動レンダリング。
- HWP/HWPX のアンカーはセクション・段落・表が単位です(レンダリング上のページ番号なし)。
- 文書内の画像は抽出・保存しますが、ビジョン処理は自動では走らせません。
- モデルの重みのリビジョンは自動では証明しません。運用者が書いた値と実行時の fingerprint を分けて持ちます。

## 必要なもの

- Python 3.13 以上 3.15 未満 · `uv` 0.10.0 以上
- 埋め込みサーバー: OpenAI 互換の `/v1/embeddings` (LM Studio など)
- 任意: OpenAI 互換の chat サーバー (LLM 前処理)
- 任意: HWP5 文書 = `java` + ローカルの hwplib jar (文書アダプタ設定 `hwp_classpath`)
- API キー / アカウント: エンジン自体はなし

## リンク

- [docs/README.md](docs/README.md) — ドキュメント案内 (韓国語)
- [docs/PLAN.md](docs/PLAN.md) — 実装計画・検証記録・サポート範囲 (韓国語)
- [docs/DECISIONS.md](docs/DECISIONS.md) — 設計判断の記録 (韓国語)
- [examples/explicit_consumer.py](examples/explicit_consumer.py) — 利用側イベントアダプタの例
- [rag-consumer](../rag-consumer/README.ja.md) — このエンジンに会話記録を入れる対のパック
- [AI Feature Pack カタログ](../../README.ja.md)
