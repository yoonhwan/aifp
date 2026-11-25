<div align="center">

# agent-cli

**AI コーディングエージェント CLI のインストール・比較ガイドと、別のモデルへ非対話で作業を任せる委任ハーネスを、1 つのパックにまとめました。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- Claude Code · Codex · Gemini · OpenCode · Cursor Agent · Pi の 6 種の CLI について、インストール・認証・比較を案内します。
- 今使っているセッションの中から別のモデルを非対話で呼び出して作業を任せ、自律実行させ、`resume` で続きを進められます。
- ペルソナ(DA · designer · architect)を注入して、任せたモデルにすぐ役割を与えられます。
- あるモデルが作った結果を、別のモデルが敵対的に検証します(author と review を分離)。
- 同じ作業を複数のプロバイダに投げて cross-check できます。
- oh-my-\* · baton · tmuxc などの上位ハーネスと連携できます(任意)。入っていなければ無視され、非対話の委任・ペルソナ・resume はそれらなしでも動きます。

## クイックスタート

```bash
# リポジトリのルートで: OS と、今使える CLI を確認
bash feature-pack/agent-cli/scripts/detect-env.sh
# スキルをインストールしたあと(インストールの節を参照): codex に DA ペルソナで検証を任せ、続けて質問
bash ~/.claude/skills/agent-cli/scripts/resume_chain.sh codex DA "この diff を敵対的に検証して" "指摘を優先順位でまとめて"
```

## インストール

### エージェントでインストール

エージェントに次のように頼んでください。

```text
feature-pack/agent-cli/INSTALL.md を読んでインストールして
```

### 手動でインストール

```bash
mkdir -p ~/.claude/skills/agent-cli/references ~/.claude/skills/agent-cli/scripts
cp SKILL.md            ~/.claude/skills/agent-cli/SKILL.md
cp references/*.md     ~/.claude/skills/agent-cli/references/
cp scripts/*.sh        ~/.claude/skills/agent-cli/scripts/
chmod +x ~/.claude/skills/agent-cli/scripts/*.sh
```

- 上のコマンドは `feature-pack/agent-cli/` の中で実行します。OpenClaw など別のエージェントなら、スキルのパスだけをその規約に合わせます。`SKILL.md` は単体で読めます。
- 先に `bash scripts/detect-env.sh` を実行すると、macOS · Linux · WSL を見分けて、今使える CLI、未インストールの CLI のインストール方法、WSL の注意点をまとめて表示します。
- エージェントの TOOLS.md(または同じ役割のカタログ)があれば、`config/tools-section.md` の内容を追加します。
- OpenCode の既定モデルは `opencode/deepseek-v4-flash-free` です。別のモデルを使うなら `export OPENCODE_MODEL=<provider/model>` を設定します(一覧: `opencode models`)。
- Pi は `export PI_MODEL=<provider/model>` で既定モデルを変えます。先に `pi auth check --provider <provider> --json` で認証を確認してください。スキルの注入は `--skill`、ツールの制限は `--tools` です。

### 動作確認

```bash
bash ~/.claude/skills/agent-cli/scripts/selftest.sh   # 隔離した、または信頼できるフォルダで実行
```

`test/verify.md` のチェックリストも合わせて確認します。

## 使い方

### 対応している CLI

| CLI | 非対話 | 自動実行 | resume |
|-----|--------|---------|--------|
| Claude Code | `claude -p` | `--dangerously-skip-permissions` | `--resume <sid>` |
| Codex | `codex exec` | `--full-auto` ⎮ `--yolo` | `codex exec resume --last` |
| Gemini | `gemini -p` | `--approval-mode yolo` | `--resume <session_id>` |
| OpenCode | `opencode run` | 既定で承認なし | `-s <sid>` / `-c` |
| Cursor Agent | `cursor-agent -p` | `-f` / `--force` | `--resume <chatId>` |
| Pi | `pi -p` | `--tools <allowlist>` (承認プロンプトなし) | `--session-id <sid>` / `--session <sid>` |

- Aider と Amp は参考として扱うだけです(`references/install-and-compare.md`)。
- セッション中は、「この PR を codex で DA 敵対検証して」「この設計を Gemini で cross-check して」「さっきのセッションを resume して追加で質問」といった依頼で自動的に動きます。

### 委任と resume

```bash
bash ~/.claude/skills/agent-cli/scripts/resume_chain.sh codex DA "この diff を敵対的に検証して" "指摘を優先順位でまとめて"

# Claude のモデルと effort を固定する場合
CLAUDE_MODEL=<model-id> CLAUDE_EFFORT=high \
bash ~/.claude/skills/agent-cli/scripts/resume_chain.sh claude DA \
  "この変更を敵対的に検証して" \
  "最終的に承認してよいかだけ、もう一度教えて"
```

- `resume_chain.sh` は Claude を呼ぶとき、`CLAUDE_MODEL` と `CLAUDE_EFFORT` の環境変数をそのまま渡します。

### スクリプト

| スクリプト | 内容 |
|---|---|
| `scripts/detect-env.sh` | OS の判別 · 今使える CLI · インストールのヒント · WSL の注意 |
| `scripts/selftest.sh` | 6 種の非対話 · 自動実行 · resume をまとめて点検(タイムアウトとログ付き) |
| `scripts/test_opencode.sh` | OpenCode 単独の点検(モデルを自動検出) |
| `scripts/resume_chain.sh` | ペルソナ + 複数回の resume をつなぐチェーン |
| `scripts/cloud-dataset-batch.sh` | cloud session credits で学習 · ラベリング用データを大量に生成し、回収 |

### クラウドクレジットのバッチ

Claude の cloud session credits(サブスクリプションとは別に付与されるクレジット)は、cloud session でだけ消費されます。ローカルの CLI やプロキシ経由の呼び出しでは消費されません。`scripts/cloud-dataset-batch.sh` は、リポジトリもコードもない空のフォルダで cloud session を起動し、終わったら回収(teleport)して、回答に出力された JSONL だけを抜き出し、データセットとして蓄積します。

```bash
bash scripts/cloud-dataset-batch.sh --task lexicon --lang ko,ja,th --count 300 --batch 25 --parallel 3 --budget 20
bash scripts/cloud-dataset-batch.sh --task label   --lang ko --labels work,tech,legal,daily,billing,other --count 200
bash scripts/cloud-dataset-batch.sh --task doc     --lang ko --count 4 --batch 4 --parallel 1 --budget 1   # 少量の試験
```

| task | 作るデータ |
|---|---|
| `lexicon` | 言語学の辞書項目(lemma · pos · IPA · gloss · 例文 · register) |
| `parallel` | 並列コーパス(src / tgt · domain) |
| `label` | 分類ラベリング(text · label · rationale)。`--labels` でラベルの集合を固定 |
| `qa` | 言語学習の Q/A(level · topic) |
| `doc` | 長文ドキュメントの節(1 行 520 文字)。大量にクレジットを使い切る用 |
| `free` | 自由形式 |

- 出力: `<out>/data.jsonl`(バッチ間の重複を除き `id` を振り直す) · `<out>/run-*/index.tsv`(セッションと件数の台帳) · `ledger.json`(クレジットの増減)
- 実測: 1 セッションあたり約 25 レコード、1 レコードあたり約 $0.03、並列 2〜4 で拡張。
- 注意: cloud credits には有効期限があるので、期限前に使い切ってください。`--budget` で支出の上限を設定します。大量の繰り返し生成はアカウントの不正利用と判定される可能性があるため、実際に使うデータを作ってください。

### 安全

- 自動実行のフラグ(dangerous / full-auto / yolo / force)は、人の承認ゲートをなくします。隔離した、または信頼できるワークスペースでだけ使ってください。
- 委任先の CLI には、それぞれの認証が必要です。このパックは認証情報を入れません。
- 委任の結果は信頼できない入力として扱い、本セッションで確認してから使ってください。

## 必要なもの

- 対応環境: macOS · Linux · WSL
- `perl` と `python3` — macOS には標準で入っています。WSL や Ubuntu に無ければ `sudo apt install -y perl python3`
- 6 種のうち少なくとも 1 つのエージェント CLI が PATH にあり、その CLI 自身の認証が済んでいること。未インストールの CLI は自動的にスキップされます。
- WSL: OAuth は Windows のブラウザで開きます(URL は手でコピーして貼り付けられます)。cursor-agent は無い場合があります(自動で SKIP)。作業は `~/` の中で行ってください。
- クラウドクレジットのバッチだけ: `~/.headroom/claude-credit.sh`(ccx / ccxt) · `claude` 2.1.310 以上 · tmux

## リンク

- [INSTALL.md](INSTALL.md) — エージェント向けのインストール手順
- [SKILL.md](SKILL.md) — スキルの定義
- [references/per-cli.md](references/per-cli.md) — CLI ごとの非対話 · 自動実行 · resume の詳細
- [references/install-and-compare.md](references/install-and-compare.md) — インストール · 認証 · 比較
- [references/personas.md](references/personas.md) — DA · designer · architect のペルソナ
- [AI Feature Pack カタログ](../../README.ja.md)
