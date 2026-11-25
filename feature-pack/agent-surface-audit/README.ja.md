<div align="center">

# agent-surface-audit

**エージェントのスキルと hook の置き場所を、読み取りだけで一覧にする、公開しても安全な dry-run 点検ツール。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- エージェントから見えるスキルと hook の置き場所を一覧にします: ソースパック、ユーザーのスキルルート、プロジェクトの overlay、hook 設定のパス。
- 安全なメタデータだけを読みます。秘密の中身は読みません。
- 実際の `~/.claude`・`~/.codex`・`~/.agents`・プロジェクト overlay の設定・symlink・hook・session・log・auth の情報は変更しません。
- 重複して公開されるリスクと壊れた symlink を見つけ、今後の対応をロールバックのコマンド付きで提案します。
- 人が読めるレポートか JSON を出力し、JSON をファイルに保存することもできます。

## クイックスタート

```bash
feature-pack/agent-surface-audit/core/bin/agent-surface-audit --dry-run
```

## インストール

このパックは実際のランタイムには何もインストールしません。あえて読み取り専用にしてあるので、checkout した場所でそのまま実行します。詳しくは [INSTALL.md](INSTALL.md) を見てください。

`agent-surface-audit` という名前で呼びたいときは、`bin` フォルダを今のシェルの `PATH` に入れます。

```bash
export PATH="$PWD/feature-pack/agent-surface-audit/core/bin:$PATH"
agent-surface-audit --dry-run
```

dry-run の確認をしている間は、このパックを `~/.claude`・`~/.codex`・`~/.agents`・プロジェクト overlay のルートに symlink で入れないでください。今後のインストーラは、確認済みのレポートから生成され、ロールバックのコマンドを含むようにする予定です。

## 使い方

### オプション

| オプション | 説明 |
|------------|------|
| `--dry-run` | 必須。読み取り専用が契約なので、これが無いと実行しません |
| `--repo-root PATH` | 点検するリポジトリ (既定値: カレントディレクトリ) |
| `--home PATH` | 点検するホームディレクトリ (既定値: 自分のホーム) |
| `--json PATH` | JSON レポートをこのファイルにも保存します |
| `--format human\|json` | stdout の出力形式 |
| `--public-safety` | 公開安全のセクションだけをレポートします |

### 例

```bash
agent-surface-audit --dry-run
agent-surface-audit --dry-run --repo-root "$PWD" --home "$HOME" --json report.json
agent-surface-audit --dry-run --format json
agent-surface-audit --dry-run --public-safety --format json
```

### レポートに含まれるもの

- 公開安全のバケット
- `feature-pack/*` 配下のソースパック
- `$HOME/.claude/skills`・`$HOME/.codex/skills`・`$HOME/.agents/skills` 配下のユーザーランタイムのスキルルート
- `.claude/skills`・`.codex/skills`・`.agents/skills` 配下のプロジェクト overlay
- hook 設定パスの存在メタデータのみ
- 重複して公開されるリスクと壊れた symlink
- 今後の対応の提案とロールバックのコマンド
- スキップした非公開パス (種類のみ)

### 補足

- 検出結果はレポートのデータであり、プロセスの失敗ではありません。引数が不正なときとランタイム/ツールのエラーのときだけ、0 以外の終了コードを返します。
- 実際に読み込まれる動作が確認できるまでは、Codex/OMO のスキルの公開場所は `~/.codex/skills` のままです。`~/.agents/skills` は互換性と overlay のためだけに使います。
- 検証スクリプトは `test/` 配下にあります (`verify.sh`・`verify_manifest_contract.sh`)。

## 必要なもの

- `bash`
- `python3` (3.10 以上 — コードが `match` 文を使っています)
- `jq` (`test/` 配下の検証スクリプト用)
- API キー不要

## リンク

- [INSTALL.md](INSTALL.md) — その場で実行する方法
- [AI Feature Pack カタログ](../../README.ja.md)
