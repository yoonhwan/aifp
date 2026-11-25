<div align="center">

# tmuxc

**Claude Code · Codex · OMX · OpenCode · Command Code · Pi のエージェントセッションを、tmux 上で 1 つのコマンドから開いて操作できます。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- プロジェクトフォルダや git worktree で、Claude Code・Codex CLI・OMX・OpenCode・Command Code・Pi のセッションを `tmuxc open` の 1 行で開けます。
- セッションを開くときに、役割(`worker` · `orchestrator` · `designer`)を指定できます。
- 別のセッションにメッセージを送り、その画面を読めます(`tmuxc send` · `tmuxc msg` · `tmuxc ask`)。送信と取得は verified send / capture の手順に統一されています。
- 終了前に開いているセッションをスナップショットとして保存し、再起動後に `tmuxc restore` で復元できます。
- 親の会話には触れずに、新しい会話へ分岐できます(`tmuxc fork` · 各エンジンのネイティブ fork)。
- セッションの一覧・終了・整理も同じ CLI で行えます(`tmuxc list` · `kill` · `clean`)。

## クイックスタート

```bash
bash feature-pack/tmuxc/install.sh
tmuxc --help
tmuxc open "$PWD" --name TMUXC_SMOKE --agent codex --role worker --dry-run
```

## インストール

### エージェントでインストール

エージェントに次のように頼んでください。

```text
feature-pack/tmuxc/INSTALL.md を読んでインストールして
```

### 手動でインストール

```bash
bash feature-pack/tmuxc/install.sh
```

`install.sh` の処理:

- `bash` · `git` · `tmux` があるか確認します。
- core と Claude Code skill を `~/.tmuxc/versions/<version>/` にコピーし、`~/.tmuxc/current` のシンボリックリンクを更新します。
- CLI を `~/.local/bin/tmuxc` にリンクします。`~/.local/bin` が PATH になければ、`~/.zshrc` か `~/.bashrc` に追加します。
- Claude Code がある場合は、`~/.claude/skills/tmuxc` をインストールしたコピーにリンクします。

### 動作確認

```bash
tmuxc --help
tmuxc list
test -e "$HOME/.claude/skills/tmuxc/SKILL.md"
test -e "$HOME/.claude/skills/tmuxc/COMM-GUIDE.md"
```

### アンインストール

```bash
bash feature-pack/tmuxc/uninstall.sh
```

アンインストールのスクリプトが消すのは、`~/.tmuxc` と、インストールしたコピーを指す `~/.local/bin/tmuxc` · `~/.claude/skills/tmuxc` のリンクだけです。プロジェクトのファイルと tmux セッションは消しません。

## 使い方

### コマンド

```bash
tmuxc open <path> --name NAME --agent claude|codex|omx|opencode|cmd|pi --role worker|orchestrator|designer [--pi-skill PATH]...
tmuxc wt <worktree-path> --name NAME --prompt "NEXT.md を読んで開始"
tmuxc list
tmuxc ask <name> [lines]              # セッション画面の末尾を読む (capture-pane)
tmuxc send <name> "message"           # セッションにメッセージを送る
tmuxc msg <name> "message"
tmuxc kill <name>
tmuxc clean
tmuxc save [--keep N]                 # 終了前に全体のセッションをスナップショット保存 ([1m] · effort · session_id を保持)
tmuxc restore [--from latest] [--go]  # 再起動後に復元 (スナップショット優先、--scan でログのスキャンを強制)
tmuxc fork <path> --name NEW (--from LIVE_SESSION | --source ID --agent claude|codex|opencode|cmd|pi) [--model ID] [--ctx 1m] [--effort E] [--prompt TEXT]
```

- Claude 以外の席(pi · codex · opencode · cmd)では、`open` と `fork` が tmux セッションの env に `GIT_EDITOR=true` · `GIT_SEQUENCE_EDITOR=true` · `GIT_TERMINAL_PROMPT=0` を設定します。git がエディタや入力待ちで止まることはありません。すでに動いている席には適用されず、新しい席から有効になります。

### Pi の席

```bash
tmuxc open . --name PI_WORKER --agent pi --role worker --model <provider/model>
tmuxc open . --name PI_REVIEW --agent pi --role orchestrator --effort high
```

- tmuxc が `--session-id <uuid>` を発行し、セッションの env(`TMUXC_PI_SESSION_ID` · `TMUXC_PI_MODEL` · `TMUXC_PI_THINKING`)に保存します。プロセス名が argv を隠していても、`save` と `restore` は正確なセッションを復元します。
- `worker` と `implementer` には `read,bash,edit,write,grep,find,ls` のツールが、`orchestrator` · `planner` · `analysis` には読み取り専用のツールが渡されます。
- `--effort` は Pi の `--thinking` に対応します。
- `--like <pi-session>` で、実行中の Pi の model と thinking を引き継げます。

`--pi-skill` を使うと、Pi の席に選んだスキルだけを読み込めます。

```bash
tmuxc open <path> --agent pi --pi-skill ~/.agents/skills/code-intel --pi-skill ~/.agents/skills/tmuxc --dry-run
```

- Pi のスキル自動検出を切り(`--no-skills`)、指定したパスだけを順に読み込みます。
- パスは `SKILL.md` のファイルか、`SKILL.md` を含むフォルダです。存在しないパスは何も作らず rc≠0 で拒否します。
- `--agent pi` のときだけ受け付けます(他のエージェントでは rc≠0)。オプションを付けなければ、コマンドは従来と同じです。
- `tmuxc fork` や `tmuxc restore` で立ち上げ直した席には、このオプションは適用されません。

### Fork

| エンジン | argv | 備考 |
|---|---|---|
| claude | `--resume <ID> --fork-session` | headroom ラッパー経由、`[1m]` と effort を引き継ぎ |
| codex | `codex fork <ID>` | `-c model=` と `-c model_reasoning_effort=` を渡す |
| opencode | `--session <ID> --fork` | モデルはセッション env の `OPENCODE_CONFIG_CONTENT` で渡す |
| cmd | `--resume <ID> --fork-session` | `--model` と `--effort` |
| pi | `--fork <ID> --session-id <NEW>` | `--model` と `--thinking` |

- `--from <ライブセッション>`: 実行中のプロセスとトランスクリプトから、エンジン・モデル・会話 id を読み取ります。同じエンジンの間だけで、別のエンジンへは分岐できません。
- `--source <ID> --agent <エンジン>`: id を直接指定します。その id がエンジンの保存先にあるか、可能な範囲で確認します。
- `omx` にはネイティブ fork がないため、対象外です。

### おすすめの流れ

```bash
# 1) baton handoff のある worktree でセッションを開く
tmuxc open /path/to/project/.worktrees/my-task --name MY_TASK_ORCH --agent codex --role orchestrator --prompt "AGENTS.md、.baton/handoff/CURRENT.md、.baton/handoff/NEXT.md を読んで開始"

# 2) cairn に task / session ref を残す
cairn link t7 --session-ref MY_TASK_ORCH --execution-ref "tmuxc:MY_TASK_ORCH"

# 3) 進み具合は list / ask で確認する
tmuxc list
tmuxc ask MY_TASK_ORCH 80
```

### 組み合わせて使うツール

| ツール | 役割 |
| --- | --- |
| `baton` | worktree, handoff, archive, memory |
| `cairn` | milestone / task のスケジュール ledger, session lineage |
| `tmuxc` | 動作中の tmux エージェントセッションの起動と制御 |

## 必要なもの

- 必須: `bash` · `git` · `tmux` (macOS: `brew install tmux` · Ubuntu: `sudo apt install tmux`)
- 任意: 開きたいエージェントの CLI (`claude` · `codex` · `omx` など)
- 任意: `baton` · `cairn` (組み合わせて使うツール群)
- tmuxc 自体にアカウントや API キーは要りません。各エージェント CLI の認証は、その CLI が別に求めます。

## リンク

- [INSTALL.md](INSTALL.md) — エージェント向けのインストール手順
- [AI Feature Pack カタログ](../../README.ja.md)
