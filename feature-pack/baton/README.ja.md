<div align="center">

# baton

**worktree・作業メモリ・archive を一か所にまとめ、どのエージェントが始めた作業でも次のエージェントがそのまま引き継げるようにします**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- Claude Code・Codex・Gemini・OpenCode・Hermes が同じ置き場 `.baton/handoff/`(`PLAN.md`・`JOURNAL.md`・`CURRENT.md`・`NEXT.md`)に結果をためます。次のセッションはどのエージェントでもここを読んで続けます。
- worktree を作成・整理します。作成時にポート割り当て・シンボリックリンク・メモリ初期化を行い、完了時に archive へ保管します。
- archive は git で追跡します。push すれば別のマシンからも過去の判断を検索でき、古い archive は 30 日を基準に整理します。
- `BATON_TMUX_ENABLE=true` なら worktree ごとに tmux セッションを作ります。ノート PC を閉じてもセッションは残り、別のエージェントやスマートフォンの SSH から attach して続けられます。
- main / master のルートでは plan・save・resume・finish を拒否します。phase は worktree の中にだけ置きます。
- 作業そのもの(plan インタビュー・コーディング・レビュー・テスト)は行いません。外部ハーネス(superpowers・OMX・OMC など)に任せ、結果だけを置き場にためます。

## クイックスタート

```bash
git clone https://github.com/yoonhwan/aifp
bash aifp/feature-pack/baton/install.sh   # 対話式インストール
export BATON_TMUX_ENABLE=true             # 任意 — worktree ごとに tmux セッション

# エージェントの中で — main ルート
/baton:wt-create my-task
cd .worktrees/my-task

# worktree の中で
/baton:plan my-task     # 任意 — 大きな作業のみ
# ... 外部ハーネスで作業 ...
/baton:save             # 中断時に handoff を保存
/baton:finish           # phase 完了
/baton:wt-clean         # 整理 + archive に保管
```

次のセッションでは、どのエージェントでもその worktree に入って `/baton:resume` を呼ぶか、`go`・`continue` と言えば `NEXT.md` を読んで続けます。

## インストール

### エージェントに任せる

エージェントに「`feature-pack/baton/INSTALL.md` を読んでインストールして」と頼んでください。所要時間は約3分です。

### 手動インストール

```bash
bash feature-pack/baton/install.sh        # 対話式インストール
export PATH="$HOME/.baton/current/bin:$PATH"   # ~/.zshrc または ~/.bashrc に追加
~/.baton/current/bin/baton doctor         # 検証
bash feature-pack/baton/uninstall.sh      # 削除
```

`install.sh` が行うこと:

1. インストール済みのエージェントを探します(Claude Code・Gemini CLI・OpenCode・Hermes)。
2. core を `~/.baton/versions/<version>/` にコピーし、`~/.baton/current` のリンクを張ります(複数バージョンが共存できます)。
3. エージェントごとに登録します。

| エージェント | 登録するもの |
|---|---|
| Claude Code | `~/.claude/commands/baton/` のコマンド・`~/.claude/skills/baton/SKILL.md` のリンク・`~/.claude/settings.json` の hook |
| Gemini CLI | `~/.gemini/commands/baton/` の TOML・`~/.gemini/settings.json` の hook |
| OpenCode | `~/.config/opencode/commands/baton/`・plugins |
| Hermes | `~/.hermes/plugins/baton.py` |
| Codex・OpenClaw | 手動登録の手順を出力 |

4. どの hook にどの baton 処理を掛けるかを尋ねます(推奨セットを自動で選ぶこともできます)。

`settings.json` は `settings.json.baton-backup` にバックアップしてからマージします。削除してもプロジェクト内の `.baton/` はユーザーデータなので残ります。必要なら手で消してください。

## 使い方

### コマンド

| コマンド | 内容 |
|---|---|
| `/baton:wt-create <name>` | worktree + ポート + シンボリックリンク + メモリ初期化 |
| `/baton:plan <id>` | phase の計画(`PLAN.md`・`phase.json`)— worktree の中でのみ |
| `/baton:save` | handoff をすぐ保存(`CURRENT.md` は paused、`NEXT.md` を更新) |
| `/baton:resume` | `NEXT.md` を出力して続行 |
| `/baton:finish` | phase 完了 + wt-clean を提案 |
| `/baton:wt-clean [path] [--merged]` | worktree の整理 + archive に保管 |
| `/baton:status` | phase + アクティブな worktree(tmux セッション付き) |
| `/baton:hotfix-mode [finish]` | main で直接 hotfix(lite mode・メモリ無効) |
| `/baton:digest <topic>` | 複数セッションのコンテキストを1ファイルに圧縮 |
| `/baton:migrate [--dry-run] [path]` | 既存の worktree を sidecar 構成に移行 |
| `/baton:help` | 流れを ASCII 図で出力 |
| `/baton:install`・`/baton:doctor`・`/baton:upgrade` | インストール・診断・新バージョンのインストール |
| `/baton:archive list` | 直近30日の archive |
| `/baton:archive search <query> [--global]` | メタデータ + 内容の検索 |
| `/baton:archive show <id>` | 詳細 |
| `/baton:archive extract <id>`・`close <id>` | 一時フォルダに展開・そのフォルダを片付け |
| `/baton:archive prune [--dry-run] [--days N]` | 期限切れの archive を整理 |

### main ブランチの保護

main / master のルートで使えるのは `wt-create`・`archive list/search`・`status`・`hotfix-mode` だけです。`plan`・`save`・`resume`・`finish` は拒否します。main を汚さず、phase は worktree にだけ置きます。

### tmux とスマートフォンからの attach

`BATON_TMUX_ENABLE=true` なら `wt-create` が tmux セッションを作り、`tmux attach -t <セッション>` コマンドを表示します。Tailscale があれば `tailscale ip -4` と `$USER` から作った SSH コマンドも1行表示するので、Termius や Blink などのスマートフォンアプリに貼り付けてください。セッション内のエージェントは `BATON_AGENT` で決まり、未設定なら `CODEX_*`・`OMX_SESSION_ID` は Codex、`CLAUDE_*` は Claude とみなします。macOS の準備(1回だけ):

```bash
sudo tailscale set --ssh             # Tailscale SSH を有効化
sudo systemsetup -setremotelogin on  # SSH を有効化
sudo pmset -c sleep 0                # 電源接続中はスリープしない
```

### Claude Code の hook

| hook | baton の処理 |
|---|---|
| SessionStart | paused の通知 + 環境チェック + archive の整理 |
| UserPromptSubmit | ユーザー入力をすぐ `JOURNAL.md` に追記 |
| PostToolUse | 外部ハーネスの利用を `JOURNAL.md` に記録 |
| PreCompact | バックアップ dump を指示 |
| SessionEnd | バックアップ dump を指示 |

### 外部ハーネス

`/baton:plan` は使えるハーネスの候補を表示します。計画系(`/superpowers:writing-plans`・`$plan`・`/oh-my-claudecode:plan` など)の結果は `PLAN.md` に、実行系(`/superpowers:executing-plans`・`$autopilot`・`/oh-my-claudecode:autopilot` など)の結果は `JOURNAL.md` にためるよう指示を加えます。カタログファイルはなく、名前で照合します。推奨は `config.json` の `harnesses.preferred_plan` で変えられます。

### ファイルの場所

```
~/.baton/
├── versions/<version>/      # bin · lib · templates · SPEC.md
└── current -> versions/<version>/

<project>/.baton/
├── config.json              # commit
├── version.lock             # commit
└── archive/                 # commit (マシン間で sync)

<worktree>/.baton/
├── config.json              # プロジェクト設定を継承
├── phase.json               # commit
├── handoff/                 # gitignore — PLAN · JOURNAL · CURRENT · NEXT
└── session.lock
```

### フローの事例

| 事例 | 状況 |
|---|---|
| [plan-first](flows/plan-first.md) | 長い作業 — plan から |
| [wt-first](flows/wt-first.md) | 軽い作業 — すぐ worktree だけ |
| [wt-finish](flows/wt-finish.md) | 1件を終える |
| [branch-pivot](flows/branch-pivot.md) | 複数ブランチに分かれた後の整理 |
| [abandoned](flows/abandoned.md) | phase の中止 |
| [hotfix-mode](flows/hotfix-mode.md) | main で直接 hotfix |
| [orphan-recovery](flows/orphan-recovery.md) | 壊れた `.baton/` の復旧 |
| [handoff-rollback](flows/handoff-rollback.md) | 壊れた `handoff/` を archive から復元 |

## 必要なもの

- OS: macOS・Linux
- 必須: `bash` 4 以上・`git` 2.30 以上・`jq` 1.6 以上・`tar`
- 任意: `ripgrep`・`gh`・tmux(`BATON_TMUX_ENABLE`)・Tailscale(スマートフォンから attach)
- API キー・アカウント: 不要

## リンク

- [INSTALL.md](INSTALL.md) — エージェント向けのインストール手順
- [core/SPEC.md](core/SPEC.md) — 他のエージェントと合わせる4つのルール(handoff 4ファイルの形式・`phase.json` のスキーマ・worktree の場所と main の保護・ポート割り当て)
- [flows/_index.md](flows/_index.md) — フローの事例8件
- [docs/MULTI_AGENT_SCENARIOS.md](docs/MULTI_AGENT_SCENARIOS.md) — 複数エージェントの同時作業
- アダプター: [Codex](adapters/codex/INSTRUCTIONS.md) · [Gemini](adapters/gemini/INSTRUCTIONS.md) · [OpenCode](adapters/opencode/INSTRUCTIONS.md) · [Hermes](adapters/hermes/INSTALL.md)
- [cairn](../cairn/README.ja.md) — 一緒に使うパック: 予定と復帰点の台帳
- [AI Feature Pack カタログ](../../README.ja.md)
- ライセンス: MIT
