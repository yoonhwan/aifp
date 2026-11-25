<div align="center">

# ctx-plan

**アカウント構成から定員 · ピークセッション · ゴール処理量を計算し、目標規模に必要なサブスクリプション数を逆算する処理能力ツール**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- 相棒ツール `ctx-burn` が「使った量」を測るのに対し、`ctx-plan` は「さばける量」をシミュレーションします。両者は **JSON の契約 1 つ(`ctx.v1`)だけ** でつながります。
- `--capacity`: アカウント構成(`--accounts 5x:N,ultra:N`)から pool 表 · シミュレーション 4 行 · ゴールモデル 2 行を出します。
- `--inventory`: 優先度 0 の固定定数 19 キー(サブスクリプション数 · 週間リミットなど)を点検し、「優先度 0 の問題 N 件」 · 必要アカウントの逆算 · 基準線 A を出します。
- `--need K:N`: 目標規模(同時セッション · セッション · チーム · 同時ゴール)から必要な Ultra / 5x の数を逆算します。
- `--scales`: 無駄を減らしたときの倍率リストで計算し直します。
- セッションログも実際の HOME も読みません。入力は `ctx-burn --json` の出力と定数ファイル 1 つだけ · 書き込み 0 · ネットワーク 0。

## クイックスタート

```bash
git clone https://github.com/yoonhwan/aifp.git
cd aifp/feature-pack/ctx-plan
bash install.sh                                 # ~/.local/bin/ctx-plan

cp accounts.env.example /tmp/accounts.env       # 定数ファイル — 値はマシンごとに埋める
ctx-burn --hours 168 --json > /tmp/burn.json    # ctx-burn パックが必要

CTX_PLAN_CAP_FILE=/tmp/accounts.env ctx-plan --from /tmp/burn.json --inventory   # 優先度 0 の定数を点検
ctx-plan --from /tmp/burn.json --inv-file /tmp/accounts.env --capacity --accounts 5x:5,ultra:5
ctx-plan --from /tmp/burn.json --inv-file /tmp/accounts.env --need concurrent:40
```

## インストール

### エージェントに任せる

このパックには `INSTALL.md` がありません。エージェントに「Read feature-pack/ctx-plan/README.md and install it」と伝えれば、下の手動インストールの手順に沿って進められます。定数ファイルの値は人が埋めます。

### 手動インストール

`install.sh` が作るのは `~/.local/bin/ctx-plan` のシンボリックリンク 1 つだけです。定数ファイルの置き場所は決めません — 呼び出す側が `--inv-file` か `CTX_PLAN_CAP_FILE` で渡します。

```bash
bash install.sh                                 # ~/.local/bin/ctx-plan
CTX_PLAN_BIN_DIR="$HOME/bin" bash install.sh    # インストール先を変える
cp accounts.env.example /path/to/accounts.env   # 見本 — 値は空。埋めないと「優先度 0 の問題」で止まる
bash uninstall.sh                               # 削除 — シンボリックリンクだけ消す
```

## 使い方

### モード

| モード | 出すもの |
|---|---|
| (なし) | ヘッダ 3 行 — 契約 · 軸の定義 · 定数ファイルのパス + pool 1 行 |
| `--inventory` | 優先度 0 の定数 19 キーを点検 · 「優先度 0 の問題 N 件」 · ゴールモデル 2 行(同時ゴール · ゴール/週 · 遊休/不足チーム) · 必要アカウントの逆算 · 基準線 A |
| `--capacity` | pool 表(pool があるものだけ) · シミュレーション 4 行 · ゴールモデル 2 行 |
| `--need K:N` | `concurrent:N` · `sessions:N` · `teams:N` · `goals:N`(同時ゴール N 個) → 必要な Ultra / 5x の数 · `goals` は必要アカウントのブロックも出す · N が `FT_GOAL_PARALLEL_MAX` を超えても削らず通知 1 行(rc 0) |
| `--scales 1.0,0.9,…` | 無駄削減の倍率リスト(既定 4 値 = 実測 · -10% · -20% · -30%) |

### オプション

| オプション | 既定値 | 意味 |
|---|---|---|
| `--from FILE\|-` | stdin | `ctx-burn --json` の出力 |
| `--inv-file FILE` | (下の順序) | 固定定数ファイル |
| `--accounts 5x:N,ultra:N` | なし | `--capacity` の定員 · ピーク計算に使うアカウント構成 |
| `--wk-5x N` / `--wk-ultra N` | 630 / 2520 | 週間リミットのアンカー(重み付き M) — ファイルに値があればファイルが優先 |
| `--c5h-5x N` | 60 | 5x の 5 時間ウィンドウのアンカー |
| `--target-util F` | 0.85 | 週間の目標使用率(運用ポリシー) |
| `--seats-per-team N` | 4 | 1 チームあたりのセッション数 |
| `--hours-per-week N` | 40 | 1 セッションの週あたり時間 |
| `--teams-per-goal N` | 3 | 1 つのゴールに同時に付くチーム数 |
| `--team-hours-per-goal N` | 8 | 1 つのゴールに 1 チームが付いている時間 |

### 定数ファイル

探す場所は 2 つだけです: ① `--inv-file FILE` ② `$CTX_PLAN_CAP_FILE`。親フォルダを探したり、ホームの特定パスを仮定したりしません。ファイルがなければ表を 1 つも出さず、rc 3 + 1 行(`--inv-file` · `CTX_PLAN_CAP_FILE` · `install.sh` を指す)で終わります。

- 出力のヘッダに読んだパスを 1 行出します。キー 19 個 = サブスクリプション 5 · 週間リミット 4(上限 · 下限) · モデル 5(同時ゴールの参考値を含む) · 基準線 5。
- 値が空なら「優先度 0 の問題」で、**既定値で置き換えません** — 計算が必要な表は「算出不能」と出ます。
- 契約キーではない 2 つのつまみ(`FT_CAP_C5H_5X` · `FT_CAP_HOURS_PER_WEEK`)だけが既定値を使い、画面に「既定値(契約キーではない)」と書きます。
- 見本 = [`accounts.env.example`](accounts.env.example)(値は空)。

### ゴールモデル(参考)

- 1 ゴール = 3 チーム同時 × 8 時間 = 24 チーム時間 = 96 セッション時間 · 同時ゴールは最大 3 個 · ゴール/週 = min(使えるセッション時間 ÷ 96, 3 × 168 ÷ 8)。
- 数字は定数(`FT_GOAL_PARALLEL_MAX` · `FT_GOAL_TEAMS` · `FT_GOAL_TEAM_HOURS` · `FT_CAP_SEATS_PER_TEAM`)から埋めます。
- 計算例であって運用ルールではなく、出力に「参考 — 運用ルールではない」ラベルが付きます。値を超えても拒否 · 縮小はせず、通知だけ出します。
- 基準線 A(`FT_BASE_*` 5 キー) = 常設チームはチームあたり 1 席 × 168h、イシュー · ゴールのチームは昼間の時間 × 7 日 × セッション/チームで数えます。`チーム時間/週` は中間単位なので成果の判定には使いません。

### 守るルール

- **下限は 1 か所だけ** — `FT_CAP_WK_5X_LOW` · `FT_CAP_WK_ULTRA_LOW`。「上限 ÷ 3」のような代わりの計算はせず、空なら「算出不能」と書きます。
- **ラベルは「低容量の仮定 · 高容量の仮定」** — 「楽観 · 保守」は使いません(小さい容量が保守的だという保証はありません)。
- **アンカーには状態が付きます**(未検証 · 推定 · 実測が必要 · 運用ポリシーなど)。状態の表示が残っている間は、その数字でアカウントを決めないでください。
- **契約チェック** — `plan_input.schema` が `ctx.v1` でなければ計算せず、rc 2 + 理由 1 行で止まります。
- **モデル定数は 1 か所で解釈** — 順序は `CLI 指定 > 定数ファイル` で、契約キーはどちらもなければ「算出不能」です。出どころ(`CLI` · `ファイル` · `なし` · `既定値(契約キーではない)`)をヘッダに出します。
- **サンプル 0 = 未算出** — 0 で埋めません。rc は 0。

### 入力契約 (ctx.v1)

`ctx-burn --json` の `plan_input`:

```json
{"schema": "ctx.v1", "window_hours": 168,
 "units": {"rate_claude": "weighted_tokens_per_session_hour",
           "w_per_session_hour": "weighted_tokens_per_session_hour",
           "w_total": "weighted_tokens", "ctx_per_req": "tokens"},
 "pools": {"claude": {"req": 0, "usage0": 0, "ctx_per_req": 0.0, "active_hours": 0,
                      "cache_reuse": 0.0, "cache_reuse_of_input": 0.0,
                      "w_per_session_hour": null, "samples": 0, "sessions": 0, "w_total": 0}},
 "rate_claude": null}
```

- `rate_claude` = claude pool の **セッション時間あたり重み付きトークンの中央値**(サンプル = リクエスト 20 件以上のセッション)。計算予算(M = 百万重み付きトークン)へ単位を変えるのは 1 行だけです。`units` フィールドは契約が自分で単位を名乗るための印です。
- `usage0` = 重み 0 のレコード(API エラー)で、リクエスト率の分母から外れます。`unknown` pool = モデル不明で、ほかの pool に混ぜません。

### 安全性

- 読むもの: `--from` の JSON 1 つ · 定数ファイル 1 つ。それ以外は 0。
- 書き込み 0 · ネットワーク 0 · セッションログの直接読み取り 0 · `ctx-burn` を実行しない(subprocess 0)。
- 定数ファイルは **読むだけ** です(`--set` なし)。値は人が埋めます。

## 必要なもの

- python3 3.8 以上 · 標準ライブラリのみ
- macOS · Linux
- 入力: `ctx-burn --json` の出力([ctx-burn](../ctx-burn/README.ja.md) パック)
- 値を埋めた定数ファイル(`accounts.env.example` からコピー) · API キー · ネットワーク不要

## リンク

- [accounts.env.example](accounts.env.example) — 定数ファイルの見本(値は空)
- [docs/plan-cost-table.md](docs/plan-cost-table.md) — Claude Opus 5.5 サブスクリプションプラン vs API コスト(1 日あたり)の表(韓国語)
- [ctx-burn](../ctx-burn/README.ja.md) — `ctx.v1` を出す相棒ツール(使用量の測定)
- [AI Feature Pack カタログ](../../README.ja.md)
