<div align="center">

# code-intel

**どのエージェントハーネスでも同じコマンド `ci` ひとつで、コード検索・シンボル・参照・構造パターンを調べるパック**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- 意味・キーワード検索(BM25 + 完結した AST ブロック) — `ci search "<q>" <path>`
- シンボルの定義・呼び出し元・依存関係(定義を先に並べる) — `ci sym <sym> --callers --scope <dir>`
- ファイルを読む前に構造とトークン数を見る — `ci outline <file>`
- LSP による正確な参照・定義・実装(必要なときだけ起動) — `ci refs "<file>#<sym>"`
- ast-grep の構造パターン — `ci ast '<pattern>' <path> -l py`
- エージェントが `ci` を指示どおり使っているか遵守率を測る — `ci-audit --days 1 --by-harness`
- インデックスなし・常駐プロセス 0。Claude Code · Codex · OpenCode · Pi · Hermes で同じコマンドが使えます。Serena MCP の置き換えです。

### なぜ作ったか

ファイル 62k 個・49GB の worktree で測った値です。

| 作業 | Serena | code-intel |
|---|---|---|
| 意味検索 | 127.25s (結果なし) | 4.6s (順位付きの結果) |
| 呼び出し元の追跡 | 4.2s+ (先に有効化が必要) | 0.36s |
| 常駐メモリ | 946MB → 5.1GB リーク (peak 21GB) | 0MB |
| 事前手順 | activate_project + 設定確認 | なし |

## クイックスタート

```bash
# リポジトリのルートで: バイナリ + スキルのリンク + ci 入口 + 診断(何度実行しても同じ)
bash feature-pack/code-intel/skill/scripts/install.sh

ci doctor                                  # インストール · バージョン · LSP · smoke
ci search "dispatch" src --max 5           # 最初の検索
```

## インストール

### エージェントに任せる

エージェントに「`feature-pack/code-intel/INSTALL.md` を読んでインストールして」と伝えます。エージェントがスキルのリンク → バイナリのインストール → 検証 → 指示ファイルへの接続まで行います。所要時間 (約3分)。

### 手動インストール

`install.sh` がすること:

1. `probe`(0.6.0-rc342)・`tilth`(0.12.0)がすでにあればそのまま使い、なければ `~/.local/bin` に入れます。
2. スキルフォルダを Claude Code · Pi/Hermes · Codex · OpenCode のスキルルートにシンボリックリンクします(ルートフォルダがないハーネスは飛ばします)。
3. `~/.local/bin/ci` の入口を作ります。
4. 最後に `ci doctor` で診断します。

```bash
# 何も変えずに診断だけ
bash feature-pack/code-intel/skill/scripts/install.sh --check

# インストール後の確認
ci doctor                                  # probe/tilth バージョン + LSP + smoke
ci sym <any-symbol> --scope <subdir>       # 0.4 秒以内に応答
ci outline <file>                          # 先頭にトークン数
```

合格基準: `ci doctor` の出力 + `ci sym` の応答 + `ci outline` のトークン数表示。

### エージェントの指示ファイルにつなぐ

つながないとエージェントは `ci` を使いません。ハーネスのグローバル指示ファイル(Claude Code `~/.claude/CLAUDE.md` · Codex `~/.codex/AGENTS.md` · OpenCode `~/.config/opencode/AGENTS.md` · Pi `~/.pi/agent/AGENTS.md`)に次の行を加えます。

```markdown
**HARD RULE: コードのシンボル・参照・構造の探索は `ci` を優先。grep/rg/git grep はログ・設定・文字列・ファイル存在の確認だけに使う。
`probe`/`tilth` の直接呼び出し禁止 — 必ず `ci` を経由する(タイムアウト・scope ガード内蔵)。事前の有効化なし。**
```

### 元に戻す

```bash
rm ~/.claude/skills/code-intel ~/.agents/skills/code-intel \
   ~/.codex/skills/code-intel ~/.config/opencode/skills/code-intel \
   ~/.local/bin/ci ~/.local/bin/ci-audit
# probe/tilth のバイナリは残してもかまいません — 単体の CLI としても使えます
```

## 使い方

### コマンド

| コマンド | すること |
|---|---|
| `ci search "<query>" [path] [--max N] [--no-tests]` | 意味・キーワード検索 (BM25 + AST ブロック · テストファイルも既定で含む) |
| `ci sym <name> [--scope P] [--callers\|--deps]` | シンボルの定義・呼び出し元・依存関係 (定義を先に並べる) |
| `ci outline <file> [--section S]` | ファイルの outline (+ トークン数) |
| `ci refs "<file>#<sym>" [--json]` | LSP による正確な参照 |
| `ci def "file#sym"` · `ci impl "file#sym"` | LSP の定義・実装 |
| `ci ast '<pattern>' [path] [-l lang]` | ast-grep の構造パターン |
| `ci lsp up [--scope P]` · `down` · `status` | LSP デーモンの起動・停止・状態 |
| `ci lsp repair [--ws <name>]` | LSP の crash-loop を修復 (キャッシュは消さずに脇へ移す) |
| `ci doctor` | インストール・バージョン・デーモン・smoke の診断 |
| `ci bench [--queries FILE]` | 性能の回帰チェック (p50/p95) |
| `ci-audit [--days N] [--by-harness] [--csv FILE] [--json]` | セッション記録から `ci` · grep · Serena の呼び出しを数えて遵守率を測る |

環境変数 `PROBE_BIN` · `TILTH_BIN` でバイナリのパスを指定できます。

### 安全装置

- 検索 1 回は `CI_TIMEOUT`(既定 60 秒)の中でだけ動きます。リポジトリのルートを scope にすると警告します。どうしても全体を見るときは `CI_ALLOW_HEAVY=1 CI_TIMEOUT=600` で例外にします。
- 韓国語の Markdown で probe が panic したら、`-i '*.md'` で自動的にやり直します。
- 複数語のクエリが 0 件なら、`A OR B` で自動的にやり直します。
- Python の構造パターンは ast-grep にフォールバックします。
- `probe` · `tilth` を直接呼ばず、いつも `ci` を経由します。

### 既知の落とし穴

| 落とし穴 | 対処 |
|---|---|
| `tilth` をリポジトリのルートを scope にして直接呼ぶと CPU が暴走 (585% CPU · load 139 を実測) | `ci` 経由 · scope は下位フォルダ · 全体スキャンは `CI_ALLOW_HEAVY=1 CI_TIMEOUT=600` |
| 韓国語の Markdown で probe が panic (SIGABRT) | `ci search` が自動で `-i '*.md'` でやり直す |
| 複数語のクエリが AND と解釈されて 0 件 | `ci search` が自動で `A OR B` でやり直す |
| Python の構造パターンが 0 件 (probe のバグ) | `ci ast` が ast-grep にフォールバック (`ast-grep` のインストールが必要) |
| Python の LSP は pylsp (pyright ではない) · `call-hierarchy` 非対応 | `uv tool install python-lsp-server` · 呼び出し元は `ci sym --callers` |

## 必要なもの

- macOS (arm64 · x86_64) または Linux。`install.sh` は macOS 用の `probe` をダウンロードします。Linux では先に `probe` 0.6.0-rc342 を PATH に置けばそれをそのまま使います。
- `curl` · `tar` · `python3`
- `tilth` のインストールに `npx` または `cargo`
- 任意: `ast-grep` (`brew install ast-grep` · Python 構造パターンのフォールバック) · `python-lsp-server` (`uv tool install python-lsp-server` · Python の `ci refs`)
- API キー / アカウント: なし

## リンク

- [INSTALL.md](INSTALL.md) — エージェント向けインストール案内
- [skill/SKILL.md](skill/SKILL.md) — エージェントスキル
- [skill/scripts/install.sh](skill/scripts/install.sh) — インストールスクリプト
- [AI Feature Pack カタログ](../../README.ja.md)
