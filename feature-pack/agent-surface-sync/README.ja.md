<div align="center">

# agent-surface-sync

**`feature-pack/*` と `hooks/` の共有エージェント surface を、ローカルのランタイムフォルダにリンクとしてインストール · 更新するツール — 既定は dry-run。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- 各パックの `manifest.json` を読み、共有 CLI を `~/.agents/bin` にリンクします。
- manifest がインストール可能(`installable`)と記したランタイムのスキル · 補助ファイルをリンクします。そのランタイムのフォルダがなければスキップします。
- 共有 hook ソース `hooks/` を `~/.agents/hooks` にリンクします。
- `hooks/manifests/` があれば、hook の項目を `~/.claude/settings.json`(Claude Code) · `~/.codex/hooks.json`(Codex)にマージします。既存の項目は残します。
- 既定は dry-run です。`--apply` を付けたときだけ変更し、変更前に元のものをバックアップします。

## クイックスタート

```bash
# リポジトリのルートで — 計画だけ見る (dry-run)
feature-pack/agent-surface-sync/core/bin/agent-surface-sync
# 計画が正しければ適用
feature-pack/agent-surface-sync/core/bin/agent-surface-sync --apply --package baton
```

## インストール

エージェントに任せるなら「`feature-pack/agent-surface-sync/INSTALL.md` を読んでインストールして」と伝えてください。別にインストールするものはなく、リポジトリのルートでその場で実行します(既定の `--repo-root` は現在のフォルダです)。

```bash
feature-pack/agent-surface-sync/core/bin/agent-surface-sync
```

シェルから名前だけで呼ぶには PATH に追加します(リポジトリのルートで)。

```bash
export PATH="$PWD/feature-pack/agent-surface-sync/core/bin:$PATH"
agent-surface-sync --package baton,tmuxc
```

`--apply` は dry-run の出力が正しいことを確認してから使います。

## 使い方

### コマンド例

```bash
agent-surface-sync                                   # 全パック · 全ランタイムで dry-run
agent-surface-sync --package baton,tmuxc             # 選んだパックのみ
agent-surface-sync --runtime claude-code --format json
agent-surface-sync --apply --package baton           # 実際に適用
```

### オプション

| オプション | 値 | 既定値 |
|---|---|---|
| `--dry-run` · `--apply` | 計画だけ見る · 実際に適用 | `--dry-run` |
| `--package` | カンマ区切りのパック名 | 全パック |
| `--runtime` | `all` · `agents` · `claude-code` · `codex-cli` | `all` |
| `--format` | `human` · `json` | `human` |
| `--json` | レポートを JSON ファイルにも保存するパス | なし |
| `--repo-root` | リポジトリのルート | 現在のフォルダ |
| `--home` | ホームフォルダの代わりに使うパス | ユーザーのホーム |

終了コード: 0 = 成功 · 2 = 引数 · パスの誤り · 1 = ファイルの読み書きエラー。

### レポートの見方

dry-run のレポートには、計画された変更 · スキップしたもの · 元に戻すコマンドが入っています。変更ごとに状態が付きます。

| 状態 | 意味 |
|---|---|
| `install` | 新しくリンク |
| `relink` | 別の場所を指していたリンクを張り替え |
| `replace-existing` | リンクではないファイル · フォルダをバックアップしてリンクに置き換え |
| `merge` | hook 設定ファイルに項目をマージ |
| `up-to-date` | 変更なし |

### バックアップと元に戻す

- バックアップは `~/.agents/state/agent-surface-sync/backups/<operation_id>/` に残ります。
- レポートの `rollback` 行(`rm -rf <target> && mv <backup> <target>`)をそのまま実行すれば元に戻ります。

## 必要なもの

- Python 3.12 以上(標準ライブラリのみ · `typing.override`)
- リンク先のランタイムフォルダ: Claude Code = `~/.claude` · Codex = `~/.codex`(ないものはスキップ)
- API キー · アカウント: 不要

## リンク

- [INSTALL.md](INSTALL.md)
- [AI Feature Pack カタログ](../../README.ja.md)
