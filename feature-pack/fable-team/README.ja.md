<div align="center">

# fable-team

**fable-team ft 2.0 のソース — 席 · メモ · 発注のコア、契約、Slack · Codex · Pi アダプター、ゴールを閉じる流れを、フォルダー 1 つ = 責任 1 つで分けています。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- `ft2/` に ft 2.0 の新しい骨組みがあります。2.0 の現役ソースはこのフォルダーの中だけで書きます。
- 席 · メモ · 発注などの共通コアは、実行環境の違いを知りません。環境ごとに違う部分はアダプター(Slack · Codex · Pi)が受け持ちます。
- カード · 契約 · テスト対応表の契約定義とモデル表は `ft2/contracts/` にあります。
- `goal-close/` は、大きなゴールを条件のマスに分けて 1 マスずつ閉じる流れ 1 つとルール 6 行をまとめたモジュールです。
- `legacy_guard.py` は、`ft2/` が 1.x のツールを実行 · import · source していないかを検査します。

## クイックスタート

```bash
# リポジトリのルートから — ft2/ の自己検査 (0 = 違反なし)
python3 feature-pack/fable-team/ft2/tools/legacy_guard.py
```

## インストール

このパックのフォルダーには `INSTALL.md` がありません。公開コピーにあるのは ft 2.0 のソースと `goal-close/` モジュールで、ここに書かれたインストール手順はありません。1.x ハーネスは公開コピーに含まれていません。リポジトリを取得してこのフォルダーのファイルをその場で読み、検査ツールは上の「クイックスタート」のようにその場で実行します。

## 使い方

### フォルダーの責任

フォルダー 1 つ = 責任 1 つです。

| フォルダー | 責任 |
|---|---|
| `ft2/core/` | 席 · メモ · 発注などの 2.0 共通コア。実行環境の違いを知りません |
| `ft2/contracts/` | カード · 契約 · テスト対応表の 2.0 契約定義 |
| `ft2/contracts/models/` | モデル表 3 つ(model-scope · model-fallback · provider-of-model)の正本の置き場 — `tools/models.py` が読みます |
| `ft2/adapters/slack/` | Slack の受信 · 発行アダプター |
| `ft2/adapters/codex/` | Codex 実行アダプター |
| `ft2/adapters/pi/` | Pi 実行アダプター · 席を開く(`launch.py`) |
| `ft2/doctor/` | インストール · 環境の診断 |
| `ft2/tools/` | 検査ツール · 補助ツール |
| `ft2/tests/` | ft2 のテスト |

### legacy_guard

`ft2/` のどのファイルも、1.x のパス · ツールを実行 · import · source してはいけません。検査パターンは 1.x のパス · ツールの置き場 5 種(一覧 = [ft2/README.md](ft2/README.md))、検査する拡張子は `.py` `.sh` `.ts` `.js` `.json` です。`*.md` は文章なので許可します。コードファイルのコメントも検査します。

```bash
python3 feature-pack/fable-team/ft2/tools/legacy_guard.py          # ft2/ の自己検査
python3 feature-pack/fable-team/ft2/tools/legacy_guard.py <dir>    # 別のツリーを検査
```

| 終了コード | 意味 |
|---|---|
| `0` | 違反なし |
| `1` | 違反あり(`<ファイル>:<行>: <パターン>` を 1 行ずつ) |
| `2` | 使い方 · パスのエラー |

制限: 文字列の検査なので、動的に組み立てたパスは検出できません。そうしたパスはレビューで確認します。

### goal-close

大きなゴールを N 個の条件マスに分け、1 マスを 1 つの席が企画から閉じるまで担当します: 企画 → 実装(テスト Red → Green · PR) → DA 判定 → インストール済みの環境で検証 → 翌日モニター → 閉じる。

| ファイル | 内容 |
|---|---|
| `00-flow.md` | 流れ 1 つとルール 6 行 |
| `10-cell.md` | ゴールファイルのマスとマスのルール |
| `20-situations.md` · `30-direct.md` | 状況ごとの対処 · チームリーダーを通さない道 |
| `40-conduct.md` | 指針となくす特徴 |
| `roles/` | 役割ごとの文書(`arch` · `da` · `master` · `nano`) |
| `phrases.tsv` · `MODULE.json` | 文言表 · モジュールの版(`gc-1.3`)とファイルごとの sha256 |

## 必要なもの

- Python 3(`legacy_guard.py` · 標準ライブラリのみ)
- API キー / アカウント: なし(`legacy_guard.py` の場合)
- アダプターの実行に必要なものは、このフォルダーの文書には書かれていません。

## リンク

- [ft2/README.md](ft2/README.md) — ft 2.0 のフォルダーの責任と 1.x 依存の禁止
- [goal-close/00-flow.md](goal-close/00-flow.md) — ゴールを閉じる流れ
- [AI Feature Pack カタログ](../../README.ja.md)
