<div align="center">

# ctx-burn

**ローカルの AI コーディングエージェントがコンテキストをどれだけ消費しているかを、自分のログの数字とグラフで示す読み取り専用の監査ツール**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- エージェントは毎ターン **会話全体 + 自動ロードされるメモリ + ツール定義** を送り直します。`ctx-burn` はそのコストをローカルのセッションログから測って示します(重み: キャッシュ読み取り `0.1x` · キャッシュ再書き込み `2x` · 出力 `5x`)。
- インストール済み・実行中のランタイムを自動で検出します: `claude` · `codex` · `pi` · `opencode` はトークン使用量まで、`hermes` · `openclaw` · `commandcode` は自動ロードファイルのサイズと実行中プロセス数だけを見ます。
- キャッシュ全面再書き込みの割合 · リクエストあたりの平均コンテキスト · 4KB を超える自動ロードファイル · 蒸留の損益分岐ターン数 · 開始予算(新規蒸留 vs 再開)をグラフで出します。
- `--request` でキャプチャしたリクエスト本文を 1 つ分解し、ツール定義のサイズを見ます。
- 同じパックの `ctx-time`(実時間をどこに使ったか) · `ctx-window`(会話ウィンドウをどこに使ったか) · `ctx-share`(調整の割合と週換算ボード)も一緒に入ります。
- `--json` は相棒ツール `ctx-plan` が読む契約 `ctx.v1` ブロックを出します。設定・ファイルの書き込み 0 · ネットワーク 0 · API キー 0。

## クイックスタート

```bash
git clone https://github.com/yoonhwan/aifp.git
cd aifp/feature-pack/ctx-burn
bash install.sh            # ~/.local/bin にシンボリックリンク (ctx-burn + ctx-waste alias)

cd ~/my-project
ctx-burn                   # 直近 3 時間 · 今のフォルダ
ctx-burn --lang ko         # 韓国語で出力 (既定は英語)
```

## インストール

### エージェントに任せる

エージェントに「Read feature-pack/ctx-burn/INSTALL.md and install it」と伝えるか、下のブロックを Claude Code · Codex · Pi · OpenCode などのコーディングエージェントにそのまま貼り付けると、インストール · 実行 · 結果の解説まで自分で行います。ツールは読み取り専用なので実行は安全です。

```text
Install and run ctx-burn on this project, then explain the output.
https://github.com/yoonhwan/aifp/tree/main/feature-pack/ctx-burn

1. Clone the repo and run feature-pack/ctx-burn/install.sh (creates ~/.local/bin/ctx-burn).
2. Run `ctx-burn --hours 6` in this project root. Use `--lang ko` if I speak Korean.
3. From the output, report only these: cache full-rewrite share, average context per request,
   and the top 3 auto-loaded files over 4KB.
4. If full rewrite is above 20%, find the cause from local logs (resume size, sessions starting
   together, account switching) and show the evidence line.
5. If auto-loaded files are over 4KB, propose moving them out of the auto-load path with a 1KB digest.
6. Ask me before changing any setting. The tool itself is read-only, so running it is safe.
```

### 手動インストール

`install.sh` は `~/.local/bin` にシンボリックリンクを作るだけです: `ctx-burn` · `ctx-waste`(`ctx-burn` の恒久 alias) · `ctx-share` · `ctx-time` · `ctx-window`。`command not found` が出たら `~/.local/bin` が PATH に入っていません。

```bash
CTX_BURN_BIN_DIR="$HOME/bin" bash install.sh   # インストール先を変える (旧名 CTX_WASTE_BIN_DIR も読む)
export PATH="$HOME/.local/bin:$PATH"           # PATH になければシェルの rc に追加
bash uninstall.sh                              # 削除 — シンボリックリンクだけ消す
```

`uninstall.sh` は `ctx-burn` · `ctx-waste` · `ctx-time` · `ctx-window` のシンボリックリンクを消します。セッションログ・設定には触れません。

## 使い方

### 出力の読み方

| 節 | 示すもの | 見どころ |
|---|---|---|
| `[0]` ランタイム環境 | ランタイムごとのインストール · 実行中 · セッション数 · 最終時刻 · データの種類 | 設定なしで自動検出 |
| `[1]` 自動ロードメモリ | 毎リクエストでコストがかかるファイルとトークン数 | `!` = 4KB を超えるファイル。大きなルールファイルは必要なときに開く場所へ移し、1KB の要約だけ残します |
| `[2]` 消費の構造 | キャッシュ全面再書き込み · キャッシュ読み取りなどの重み付き割合 | 全面再書き込みが 20% を超えたら第一の容疑者。再書き込み 1 回 = 通常リクエスト 20 回分 |
| `[3]` リクエストあたりのコンテキスト | 平均 · 最大トークン | 平均 200k 超 = 会話がウィンドウの端まで伸び、蒸留が効いていない |
| 蒸留の損益分岐 | 再起動コスト · ターンあたりの節約 · 損益分岐ターン数 | セッションあたりのターン数が損益分岐を超えたら、もっと頻繁に蒸留 |
| 開始予算 | ゲート · 固定 prefix · 引き継ぎサイズから、新規開始 vs 再開の残り容量と再書き込みコスト | ウィンドウサイズより「セッション開始時に会話へ残る分」の方が大きな手綱。`--gate` · `--resume-caps`(カンマ区切り)で調整 |

### ctx-burn のオプション

| オプション | 既定値 | 意味 |
|---|---|---|
| `--lang en\|ko` | `en` | 出力言語 |
| `--runtime auto\|all\|<name>` | `auto` | 詳細を見るランタイム (`auto` = データのあるもの全部) |
| `--hours N` | 3 | 時間ウィンドウ |
| `--project PATH` | 今のフォルダ | CLAUDE.md · rules · memory を探すプロジェクトルート |
| `--request FILE` | なし | キャプチャした **リクエスト本文** のログを 1 つ分解 (ツールサイズ · `defer_loading`) |
| `--rewrite-tokens N` | 150000 | 全面再書き込みとみなすサイズ |
| `--budget N` | 250000 | 提案する蒸留しきい値 |
| `--top N` | 6 | ランタイムごとのセッション行数 |
| `--json` | オフ | 機械可読 · `ctx-plan` が読む `plan_input` ブロック(契約 `ctx.v1`)を追加 |

`--capacity` · `--inventory` · `--need` · `--scales` はここにはありません — `ctx-plan` に移りました。

### `--request` と `--json`

```bash
ctx-burn --request ~/.cli-proxy-api/logs/error-v1-messages-*.log   # ツール定義のサイズまで
ctx-burn --hours 168 --json > /tmp/burn.json                      # 契約 ctx.v1
ctx-plan --from /tmp/burn.json --capacity --accounts 5x:5,ultra:5
```

`--request` は JSON のリクエスト本文を含むファイルなら何でも読めます(`=== REQUEST BODY ===` マーカーも理解します)。プロキシを使わないなら省いてかまいません。ほかの節は単独で動きます。`--json` の `plan_input` は `schema: ctx.v1` の契約です(`window_hours` · `pools{…}` · `rate_claude`)。`ctx-plan` はほかの schema を拒否します。

### ctx-time

`ctx-burn` が **支払った量** を測るのに対し、`ctx-time` は実時間を **何に使ったか** を測ります。同じローカルのセッションログ(pi · codex)を読み、カテゴリ · 上限を超えたコマンド · 時間の行き先をターミナルと html ファイル 1 つに出します。

```bash
ctx-time                                   # 直近 3 時間 · 最大 40 セッション · 80MB · html
ctx-time --seat 'my-team-' --role arch --hours 14
ctx-time --split '2026-11-23 15:13:38'     # ある時点の前 / 後
ctx-burn --time --role nano                # ctx-burn から同じ本体を呼ぶ
```

| オプション | 既定値 | 意味 |
|---|---|---|
| `--seat REGEX` · `--role NAME` | 全部 | 席(セッション)名のパターン · 名前の `-<role>-` トークン |
| `--hours N` | 3 | 時間ウィンドウ(ファイルの mtime と行の timestamp の両方) |
| `--max-sessions N` · `--max-mb N` · `--max-scan N` | 40 · 80 · 3000 | サンプル上限(0 = 上限なし)。削った段階ごとに 1 行出し、黙って減らしません |
| `--from` · `--to` · `--split` | — | epoch または `YYYY-MM-DD HH:MM[:SS]`(ローカル) |
| `--runtime pi\|codex\|all` | all | |
| `--limit N` | 70 | 「上限超え」とみなす秒数 |
| `--out DIR` | `~/.cache/ctx-burn/time` | html フォルダ |
| `--no-html` · `--json` · `--lang en\|ko` | — | html オフ · stdout に契約 `ctx-time.v1` · 言語 |

pi は全部、codex はコマンドとターン時間を見ます。claude は呼び出しごとの時間がないため「省略」と出ます。

### ctx-window

`ctx-window` は会話ウィンドウが **どこに使われたか** を pi のセッションログから 4 つの数字で示します(先にターミナル、あとに html ファイル 1 つ)。codex · claude · hermes はスキップと表示されます。

```bash
ctx-window                                 # 直近 3 時間 · 40 セッション · 40MB · html
ctx-window --seat 'my-team-' --role arch --hours 14
ctx-window --split '2026-11-23 15:13:38'   # ある時点の前 / 後
ctx-burn --window --lang ko                # ctx-burn から同じ本体を呼ぶ
```

| 数字 | 意味 |
|---|---|
| **W1** 通知ターンの割合 | 直前の入力が `custom_message` か作業指示だったターンの重み付きコスト ÷ 起動後の全ターンの重み付きコスト |
| **W2** 起動ウィンドウ | 起動が終わったターンのウィンドウ − 最初のターン、およびその間のツール呼び出し |
| **W3** ゲート超え後 | ウィンドウが初めて `--recv-gate` を超えたターンから最後のターンまでの増加(超えたセッション数 · 中央値 · 最大) |
| **W4** ツール結果のサイズ | 結果数 · バイト · `--result-cap` を超えた結果 · 切り詰め通知 · 再読み込み率 |

オプションは `ctx-time` と同じで(`--max-mb` の既定は 40)、`--recv-gate N`(既定 280000 トークン) · `--result-cap N`(既定 2048 バイト) · `--out DIR`(既定 `~/.cache/ctx-burn/window`) · `--json`(契約 `ctx-window.v1`)が加わります。行は自分の `timestamp` で切ります(from を含む · to を含まない)。

### ctx-share

`ctx-burn` が「使った量」を測るのに対し、`ctx-share` は「そのうち調整がどれだけか」と「週の上限の何 % か」をボード 1 枚に書きます。

```bash
ctx-share                                   # 48 時間のウィンドウを測ってボードフォルダに書く
ctx-share --hours 24 --json                 # 機械可読(ボード書き込み 0)
ctx-share --now 2026-11-17T13:00:00 --force # テスト · 測り直し
```

- 調整 / 実装はセッション名 `<project>-<team>-<role>[-<tail>]#<N>` の 3 番目のトークン(役割)で分けます。名前がない、または文法に合わないものは「分類不能」として別に数えます。
- 週 % = ウィンドウ内の claude 重み付き合計を週単位に引き伸ばし、`accounts.env` の定数(`FT_CAP_WK_5X` · `FT_CAP_WK_ULTRA` · `FT_CAP_TARGET_UTIL`)と比べます。定数が 1 つでも空なら % を出しません。
- `--out` フォルダに `board.md`(人向け) · `last.json`(機械向け) · `samples.tsv` を書きます。30 分以内に測った値があればスキップして rc 0(`--force` ですぐ測る)。rc 1 = 判定不能。
- オプション: `--hours N`(48) · `--now ISO` · `--sessions-dir` · `--resume-dir` · `--inv-file` · `--acct-file` · `--out` · `--json` · `--force`。

### 見つけたものの直し方

| 優先 | やること | 方法 |
|---|---|---|
| 1 | 使わない組み込みツールを切る | `settings.json` → `env`: `CLAUDE_CODE_DISABLE_ARTIFACT=1`, `CLAUDE_CODE_DISABLE_WORKFLOWS=1` |
| 2 | 自動ロードのルールを減らす | 大きなファイルは `~/.claude/guides/` へ移し、`rules/` には 1KB の要約だけ |
| 3 | 蒸留しきい値を下げる | 損益分岐ターン数まで、ふつうは平均コンテキストの 50% |
| 4 | 再開時のコンテキストに上限 | 500k の会話ではなく、要約 + 最後の数ターンだけ引き継ぐ |
| 5 | セッション開始をばらす | cron · tick の群れを同じ分に起動しない(jitter) |

### 安全性

- **読むだけです。** 設定・ファイルを書かず、ネットワーク呼び出しもありません(`ctx-time` · `ctx-window` は `--out` の下に html ファイル 1 つ、`ctx-share` はボードフォルダにだけ書きます)。
- セッションログはローカルに残ります。読むのはトークンカウンタだけで、会話本文は読みません。
- `ctx-time` · `ctx-window` が出すのは数字 · 時刻 · 固定語 · 席名 · セッションパスだけです。コマンド行とエラーメッセージはカテゴリを選ぶのに使うだけで、出力しません。
- 重み(読み取り 0.1 · 書き込み 2.0 · 出力 5)は公開価格の比率に沿った **近似** です。実際の上限の式は公開されていないので、数字は **相対比較** に使ってください。

## 必要なもの

- python3 3.8 以上 · 標準ライブラリのみ(pip インストールなし)
- macOS · Linux
- API キー · アカウント · ネットワーク不要
- 任意: ツール定義のサイズを見るには、リクエスト本文を含むプロキシログ(例: CLIProxyAPI)
- 任意: `ctx-share` の週 % には `accounts.env` の定数が必要です(見本は `ctx-plan`)

## リンク

- [INSTALL.md](INSTALL.md) — インストール · 確認 · 削除 · トラブルシューティング
- [ctx-plan](../ctx-plan/README.ja.md) — `ctx.v1` を読む相棒ツール(処理能力 · 必要なサブスクリプション数)
- [AI Feature Pack カタログ](../../README.ja.md)
