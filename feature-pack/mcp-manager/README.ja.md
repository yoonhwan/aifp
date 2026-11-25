<div align="center">

# mcp-manager

**Claude Code と Codex の MCP サーバーを、秘密の設定値を出さずに確認 · 無効化 · 再有効化 · 整理するローカルツール。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- Claude Code と Codex の MCP サーバーを名前だけ表示します(有効なもの · 無効なもの)。設定値は出力しません。
- MCP サーバーをひとつ無効にし、また有効に戻します。変更の前にバックアップを残すので元に戻せます。
- 残すリスト(`--keep`)だけを残し、ほかのサーバーをまとめて無効にします(prune)。
- 無効にしたサーバーの設定断片は `~/.agents/state/mcp-manager/disabled/` に保管します。
- 変更するコマンドは既定で dry-run です。`--apply` を付けたときだけファイルに書き込みます。

## クイックスタート

```bash
# リポジトリのルートで
feature-pack/mcp-manager/core/bin/mcp-manager list --format human
feature-pack/mcp-manager/core/bin/mcp-manager disable stitch --runtime claude --dry-run
```

## インストール

エージェントに任せるなら「`feature-pack/mcp-manager/INSTALL.md` を読んでインストールして」と伝えてください。今はリポジトリ内でその場で動かすツールなので、別にインストールするものはありません。

```bash
feature-pack/mcp-manager/core/bin/mcp-manager list --format human
```

シェルから名前だけで呼ぶには PATH に追加します(リポジトリのルートで)。

```bash
export PATH="$PWD/feature-pack/mcp-manager/core/bin:$PATH"
mcp-manager list --format human
```

## 使い方

### コマンド

| コマンド | 内容 |
|---|---|
| `mcp-manager list` | ランタイムごとの有効なサーバー · 無効なサーバーの名前 |
| `mcp-manager disable <server>` | サーバーをひとつ無効にし、設定断片を保管 |
| `mcp-manager enable <server>` | 保管したサーバーを再び有効にする |
| `mcp-manager prune --keep a,b,c` | `--keep` にないサーバーをすべて無効にする(`--keep` は必須) |

```bash
mcp-manager list --format human
mcp-manager disable stitch --runtime claude --dry-run
mcp-manager disable stitch --runtime codex --dry-run
mcp-manager prune --runtime claude --keep context,filesystem,think --dry-run
mcp-manager prune --runtime codex --keep filesystem,node_repl,serena,think --dry-run
```

### オプション

| オプション | 値 | 既定値 |
|---|---|---|
| `--runtime` | `list`: `all` · `claude` · `codex` / その他: `claude` · `codex` (`claude-code` · `codex-cli` も可) | `list` = `all` · その他 = `codex` |
| `--dry-run` · `--apply` | 変更内容を表示するだけ · 実際に書き込む | `--dry-run` |
| `--format` | `human` · `json` | `human` |
| `--home` | ホームフォルダの代わりに見るパス | ユーザーのホーム |
| `--keep` | カンマ区切りのサーバー名(`prune` 専用) | なし |

終了コード: 0 = 成功 · 2 = 引数の誤り、または処理できない要求(例: 保管された断片がない) · 1 = ファイルの読み書きエラー。

### 触るファイル

- Codex: `~/.codex/config.toml`
- Claude Code: `~/.claude.json` を変更し、MCP マップ `~/.claude/.mcp.json` · `~/.claude/mcp.json` を読みます。
- 保管 · バックアップ: `~/.agents/state/mcp-manager/`(`disabled/<runtime>/` · `backups/<runtime>/`)
- これらのファイルは `--apply` を付けたときだけ書き込みます。

## 必要なもの

- Python 3.12 以上(標準ライブラリのみ · `typing.override` · `tomllib`)
- bash(`core/bin/mcp-manager` 起動スクリプト)
- API キー · アカウント: 不要

## リンク

- [INSTALL.md](INSTALL.md)
- [AI Feature Pack カタログ](../../README.ja.md)
