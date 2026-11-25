<div align="center">

# cairn

**予定と、複数エージェントの作業の復帰点を1つの台帳(`.cairn/plan.yaml`)に記録する CLI**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- プロジェクト / milestone(start・end)/ タスク(start・due)の予定を記録し、overdue と全体のガントチャート(Mermaid)を表示します。
- 作業を分けて任せるとき(fan-out)に系譜を記録します: `spawned_from`・`return_to`・`merge_back_to`・`fanout_depth`。session を整理したり worktree を消したりした後も、戻る場所が残ります。
- 戻るとき(fan-in)は `cairn return` がそのノードを再びつかみ、baton resume につなぎます。
- baton(記憶)・tmuxc(実行)・git は読むだけです。cairn が自分で書くのは計画と復旧メタデータだけです。
- すべての書き込みは1本に直列化されます: lock + atomic write + validate + git commit。作業ツリーが汚れていると書き込みを止めます。
- 一度グローバルにインストールすれば、どのプロジェクトのフォルダで実行してもそのプロジェクトの `.cairn/` 台帳を扱います。

## クイックスタート

```bash
git clone https://github.com/yoonhwan/aifp
bash aifp/feature-pack/cairn/install.sh   # ~/.cairn にグローバルインストール + Claude Code のコマンド・スキルを登録
cairn self-test                           # 検証

cd my-app
cairn new-project demo                    # .cairn/plan.yaml を作成
cairn status
```

## インストール

### エージェントに任せる

Claude Code に「`feature-pack/cairn/INSTALL.md` を読んで `bash feature-pack/cairn/install.sh` を実行し、self-test と hook smoke まで検証して」と頼んでください。Codex では `bash feature-pack/cairn/install.sh` を実行します。所要時間は約2分です。

### 手動インストール

```bash
bash feature-pack/cairn/install.sh
export PATH="$HOME/.cairn/current/bin:$PATH"   # 新しいシェルを開かない場合
cairn self-test                                # self-test OK
bash feature-pack/cairn/uninstall.sh           # 削除 — グローバルのみ、プロジェクトの .cairn/ は残す
```

`install.sh` が行うこと: core を `~/.cairn/versions/<version>` にコピー・`current` のリンク・`~/.cairn/venv`(ruamel.yaml)・`~/.zshrc` に PATH・`~/.cairn/current/hooks/*`・`~/.claude/commands/cairn`・`~/.claude/skills/cairn/SKILL.md` のリンク・`cairn self-test`。再実行しても安全です(新しいバージョンのフォルダを足して `current` を切り替えます)。

プロジェクトごとに git hook を掛けます:

```bash
mkdir -p .git/hooks
ln -sfn "$HOME/.cairn/current/hooks/post-merge" .git/hooks/post-merge
ln -sfn "$HOME/.cairn/current/hooks/post-checkout" .git/hooks/post-checkout
```

## 使い方

### 予定のコマンド

| コマンド | 内容 |
|---|---|
| `cairn init` | プロジェクトに `.cairn` 台帳を初期化 |
| `cairn new-project <name>`・`add-milestone <p> <name>`・`add-task <p> <ms> <name> [--days N]` | 作成 |
| `cairn status`・`show <p>`・`overdue [--today]` | 参照 |
| `cairn render` | 全体のガントチャート(Mermaid)→ `.cairn/views/plan.md` |
| `cairn set-status`・`set-date`・`set-priority` | 変更 |

### 復旧のコマンド(fan-out / fan-in)

| コマンド | 内容 |
|---|---|
| `cairn spawn <name> --from <parent>` | 分岐(fan-out)— `spawned_from`・`return_to`・`fanout_depth` を自動設定 |
| `cairn complete <task> [--force]` | 完了 + `return_to` を表示(欠けていれば止める) |
| `cairn return --to <node>` | 復帰(fan-in)— ノードを再びつかみ baton resume につなぐ |
| `cairn map [--focus] [--render]` | 復旧グラフ(recovery-map)を Mermaid で → termaid |
| `cairn link <node> --execution-ref / --session-ref / --merge-back-to` | hook が呼ぶメタデータの記録 |
| `cairn reconcile` | アクティブな worktree とノードを照合して orphan を探す |
| `cairn validate` | 台帳の整合性チェック — 切れた復旧リンク 0 |

task id は台帳全体で一意です(復旧メタデータがグローバルに参照するため)。

### 自動進捗 hook

`~/.cairn/current/hooks/cairn-auto-progress` は検証の合格(`CAIRN_VERIFICATION_STATUS=pass`)を受けると、既定では `.cairn/auto-progress/candidates/` に完了候補を残すだけです。`CAIRN_AUTO_PROGRESS=apply` と `CAIRN_TASK_ID` を両方渡したときだけ `cairn complete <task>` を実行します。

```bash
# 候補を残すだけ
CAIRN_TASK_ID=t2 CAIRN_VERIFICATION_STATUS=pass \
  "$HOME/.cairn/current/hooks/cairn-auto-progress"

# 台帳に反映
CAIRN_AUTO_PROGRESS=apply CAIRN_TASK_ID=t2 CAIRN_VERIFICATION_STATUS=pass \
  "$HOME/.cairn/current/hooks/cairn-auto-progress"
```

Claude Code では PostToolUse hook から、Codex では shell hook や tmuxc セッションの終了・検証の段階から同じコマンドを呼びます。

## 必要なもの

- OS: macOS・Linux
- 必須: `python3` 3.9 以上・`git` 2.30 以上・`ruamel.yaml`(インストール時に `~/.cairn/venv` へ自動で入ります)
- 任意: termaid(`cairn map --render`)
- API キー・アカウント: 不要
- トラブルシューティング: `cairn: command not found` → 新しいシェルを開くか上の PATH を export・`ModuleNotFoundError: ruamel` → `bash install.sh` を再実行

## リンク

- [INSTALL.md](INSTALL.md) — エージェント向けのインストール手順
- [docs/cairn-design.md](docs/cairn-design.md) — 設計
- [docs/agent-lifecycle-hook-design.md](docs/agent-lifecycle-hook-design.md) — エージェントのライフサイクル hook の設計
- [baton](../baton/README.ja.md) — 一緒に使うパック: worktree・作業メモリ・archive
- [AI Feature Pack カタログ](../../README.ja.md)
- ライセンス: MIT
