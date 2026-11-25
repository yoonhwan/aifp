<div align="center">

# auto

**エージェントはコードだけを直し、`uv run` が実験を回し、stdout の JSON で keep/discard を判定する自律実験ループ。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- Karpathy AutoResearch パターンの自律実験ループを、エージェントスキル `/auto` として使えます。
- エージェントの仕事は 4 ステップです: コード修正 → 実験実行 → JSON 読み取り → 判定。
- インフラの確認とセットアップは `prepare.py`、実験の実行とメトリクス出力は `run_experiment.py` が担当します。
- `program.md` に目標（メトリクス・修正範囲・制約）を宣言すると、エージェントはその範囲内で繰り返します。
- 実験の記録は `results.tsv` に溜まり、終了後にレポートを作成できます。

## クイックスタート

```bash
# 1. スキルをインストール
mkdir -p ~/.claude/skills/auto/references
cp skill/SKILL.md ~/.claude/skills/auto/SKILL.md
cp skill/references/*.md ~/.claude/skills/auto/references/

# 2. プロジェクトにテンプレートをコピーして uv 環境を作成
mkdir -p your-project/autoresearch
cp config/templates/* your-project/autoresearch/
cd your-project/autoresearch && uv sync

# 3. program.md、prepare.py、run_experiment.py をプロジェクトに合わせて編集
# 4. エージェントセッションで /auto を実行
```

## インストール

エージェントに「Read feature-pack/auto/INSTALL.md and install it」と頼めば進みます。手動で入れる場合は [INSTALL.md](INSTALL.md) の手順に従います。

1. スキルファイルを `~/.claude/skills/auto/` にコピーします。
2. プロジェクトのルートに `autoresearch/` フォルダを作り、テンプレート 4 つ（`pyproject.toml`・`prepare.py`・`run_experiment.py`・`program.md`）をコピーして `uv sync` を実行します。
3. `program.md` に目標を書き、`prepare.py` の `check_runtime()`・`check_data()` と、`run_experiment.py` の `RUN_CMD`・`parse_result()`・`TIMEOUT` をプロジェクトに合わせて直します。
4. 実験の生成物が git に混ざらないよう `.gitignore` を追加し、スキルが読み込まれたか確認します。

```bash
# autoresearch/.gitignore に追加
cat >> autoresearch/.gitignore << 'EOF'
.venv/
run.log
results.tsv
upstream/
__pycache__/
EOF

# スキルの読み込みを確認（期待値: version: "3.0.0"）
grep "version" ~/.claude/skills/auto/SKILL.md
```

## 使い方

### コマンド

エージェントセッションで実行します。

| コマンド | 説明 |
|----------|------|
| `/auto` | 全体フローを開始（setup → ベースライン → 目標 → 自律走行） |
| `/auto setup` | `autoresearch/` の初期化のみ |
| `/auto 2h` | 2 時間の自律走行 |
| `/auto 30m` | 30 分の自律走行 |
| `/auto overnight` | 8 時間の自律走行 |
| `/auto resume` | 既存のブランチから再開 |
| `/auto report` | `results.tsv` からレポートを作成 |
| `/auto update` | `upstream/` を git pull |

### 3 層構造

```
Layer 1: uv run prepare.py         (1 回) インフラ確認 + セットアップ
Layer 2: エージェントの自律ループ          コード修正 → 実行 → JSON → 判定
Layer 3: uv run run_experiment.py  (毎回) テスト実行 → メトリクス出力
```

### stdout JSON の契約

`run_experiment.py` は stdout の最終行に JSON を 1 行だけ出力します。それ以外の出力（進捗・警告）は stderr か `run.log` に出ます。

```json
{
  "score": 0.004,
  "passed": 13,
  "total": 14,
  "failed": ["case-14"],
  "grade_summary": "13S 1A",
  "flush_e2e_ms": null,
  "status": "ok",
  "duration_s": 187.3
}
```

- `status` は `"ok"`・`"crash"`・`"error"` のいずれかで、crash/error のときは `reason` が付くことがあります。`flush_e2e_ms` は任意項目（セカンダリメトリクス）です。
- exit 0 = 正常終了: エージェントが `score` で keep/discard を判定します。
- exit 1 = クラッシュまたはインフラ失敗: エージェントが元に戻すか直して再試行します（最大 2 回）。

### ドメイン別の例

| ドメイン | primary_metric | RUN_CMD | prepare.py |
|----------|---------------|---------|------------|
| ML 学習 | val_bpb | `uv run train.py` | GPU + データセットの確認 |
| STT 品質 | avg_cer | `python3 e2e_test.py --baseline --json` | サーバー + ブラウザ + 音声 |
| API レイテンシ | p99_ms | `pytest tests/perf.py --json` | サーバー + DB |
| コード品質 | coverage | `pytest --cov --json` | 依存関係の確認 |

### ヒント

- `program.md` をきちんと書くことが要です。メトリクス・範囲・制約がエージェントの行動範囲を決めます。
- `prepare.py` は 1 回だけ実行すればよく、冪等なので不安なら再実行しても構いません。
- 1 実験あたりの時間予算を 5 分以内にすると、多くの実験を回せます。
- 専用ブランチで、一度に 1 つだけ、1 領域につき 1〜2 ファイルだけを変更します。
- `autoresearch/` 内のインフラファイルはエージェントが直しません。直すのはプロジェクトのソースだけです。

## 必要なもの

- macOS または Linux
- Python 3.11+
- git
- [uv](https://docs.astral.sh/uv/)
- Claude Code または互換のエージェント CLI
- API キー不要 · 所要時間 (約2分)

## リンク

- [INSTALL.md](INSTALL.md) — インストールガイド
- [stdout JSON の契約の詳細](skill/references/run-experiment-contract.md)
- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) — 元になったパターン
- [AI Feature Pack カタログ](../../README.ja.md)
