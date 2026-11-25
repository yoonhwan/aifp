<div align="center">

# tmm

**スマホ(SSH)から数十の tmux エージェント席を選び、アタッチせずにのぞき、メッセージを送る 1 画面の TUI**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- tmux セッション 1 つを席 1 行で表示します — 分類 · エージェント実行の有無 · 状態 · モデル · 最後のメッセージ時刻 · 経過 · フォルダ。ファジーフィルタで絞り込みます。
- 人の入力を待つ席(`HUMAN` · `BLOCK` · `STUCK`)を上に出し、新しく現れたらターミナルのベルを鳴らします。
- アタッチせずに pane をプレビューします。`Enter` で attach、`C-a d` で離れるとピッカーに戻ります。
- `^S` でカーソルの席にメッセージを送り到達を確認します · `^K` で席を閉じます。
- `^D` 終了セッションビュー: 再起動や kill で消えたエージェントセッションをトランスクリプトから見つけ、resume で復旧します。
- `^F` fork で会話を別のエージェントに引き継ぎ、`^Y` で会話記録(トランスクリプト)のパスを表示します。

`tmuxc` で起動した Claude Code · Codex · OMX · OpenCode · Command Code · Pi の席を前提にしていますが、普通の tmux セッションにもそのまま使えます。

## クイックスタート

```bash
brew install bash tmux fzf               # なければ (bash 4 以上が必要)
bash feature-pack/tmuxc/install.sh       # 必須パック tmuxc を先に
bash feature-pack/tmm/install.sh
tmm doctor                               # 依存関係 · 環境のチェック
tmm                                      # TUI を開く
```

## インストール

### エージェントに任せる

エージェントに「`feature-pack/tmm/INSTALL.md` を読んでインストールして」と伝えます。エージェントは前提条件の確認 → `install.sh` → カテゴリ規則 → 検証 → (任意) fork モデル別名 · スマホ接続の順に進めます。所要時間 (約1分)。

### 手動インストール

`install.sh` がすること:

1. `bash>=4` · `tmux` · `fzf` を確認します(なければ exit 2 とインストールコマンドの案内)。`tmuxc` がなければ中断します。
2. 本体と libexec を `~/.tmm/versions/<version>/core/` にコピーし、`~/.tmm/current` シンボリックリンクを更新します。
3. `~/.local/bin/tmm` シンボリックリンクを作り(既存の通常ファイルはバックアップ)、`~/.local/bin` が PATH になければ `~/.zshrc` / `~/.bashrc` に追加します。
4. `~/.zshrc` に `alias tmm=` があれば警告します(alias がバイナリを横取りするため)。
5. `~/.tmm/categories` · `~/.tmm/models` がなければ例をコピーし(あれば保持)、`~/.tmm/forks/` を作ります。
6. `tmm doctor` で検証します。

```bash
bash feature-pack/tmm/install.sh
tmm doctor
tmm ls | head                          # 状態の列が ? なら seat-scan のパスを確認 → TMM_SCAN
bash feature-pack/tmm/test/verify.sh   # 隔離した tmux ソケットで回帰テスト (既存セッションに触れない)
bash feature-pack/tmm/uninstall.sh     # アンインストール (~/.tmm/categories は残す)
```

### カテゴリ規則

`~/.tmm/categories` に `グロブ<TAB>ラベル` を 1 行ずつ書きます。上から最初に一致したものが使われます。どの規則にも当たらないセッションは、役割の接頭辞(`TMM_CAT_STRIP`、既定 `FB_ ft-`)を外した名前の最初のトークン(`-` / `_` の前の 5 文字)がラベルになるので、規則ファイルにはこれでは足りないもの(別名の統合 · 大文字小文字の統一)だけを書けば済みます。小文字 · 数字 · `-` だけの `<プロジェクト>-<チーム>-<役割>…` という名前で 3 番目のトークンが役割の予約語(master · arch · da · tester · checker · analyst · pm · nano · repro · tool)なら、2 番目のトークン(チーム)がラベルです。

```bash
tmux ls -F '#S' | sed 's/#[0-9]*$//' | sort -u     # いまのセッション接頭辞の一覧
```

### スマホからの接続 (Termius の例)

1. Mac: システム設定 → 一般 → 共有 → リモートログインをオン。
2. 専用の鍵を作り、公開鍵を `~/.ssh/authorized_keys` に追加し、秘密鍵はパスワードマネージャーに保管してスマホの Termius Keychain に貼り付けます。
3. アドレス: 同じ Wi-Fi なら `ipconfig getifaddr en0`、外からは `tailscale ip -4`(Tailscale 推奨)。
4. Termius のホスト: アドレス · ポート 22 · ユーザー · 鍵 · **Startup command = `tmm`** — 接続するとすぐピッカーが開きます。
5. スマホのキーボードツールバーの Ctrl で `^S` などを押します。tmux の prefix が `C-a` なら Ctrl → a → d で離れます。

```bash
ssh-keygen -t ed25519 -f ~/.ssh/mobile_ed25519 -N ''
cat ~/.ssh/mobile_ed25519.pub >> ~/.ssh/authorized_keys
# デスクトップから自己テスト — 非対話 ssh は PATH が短いので zsh -ilc で包む
ssh -i ~/.ssh/mobile_ed25519 -o IdentitiesOnly=yes <IP> -t 'zsh -ilc tmm'
```

## 使い方

### 1 行 = 1 席

| 列 | 意味 |
|---|---|
| カテゴリ | `~/.tmm/categories` の規則、なければ役割の接頭辞を外したセッション名の最初のトークン |
| `●` / `○` | エージェント実行中 / シェルだけ |
| セッション名 | tmux のセッション名。幅に応じて 20〜44 文字 · 切れるときは真ん中を畳み、末尾の `#N` を残す |
| `HUMAN` `BLOCK` `STUCK` `IDLE` `BUSY` | seat-scan の判定。HUMAN = 人の入力待ち、BLOCK = API エラーで停止、STUCK = 未送信の入力が残っている |
| モデル | 使っているモデルの短い名前(例: `opus5·1m`)。`·1m` = 1M コンテキストウィンドウ |
| `12:33` / `12~33` | 最後のメッセージ時刻。`:` = Claude の完了マーカーから読んだ、`~` = マーカーがなく tmux の最後の出力時刻 |
| `26m` | そこからの経過 (m / h / d) |
| フォルダ | pane の cwd の最後のフォルダ。幅に応じて 6〜28 文字 |

並べ替え: `^T` 新しい順(既定 — 最後に話した席がいちばん上) · `^W` 待機中の席を上に固定してから新しい順 · `^G` カテゴリごとに新しい順 · `^H` 待機中の席だけ。

### キー

| キー | 動作 |
|---|---|
| ↑↓ / 入力 | カーソル移動 / ファジーフィルタ (`HUMAN`、セッション名の一部 …) |
| `Enter`(分類ペイン) · `Esc` / `⌫`(一覧、クエリが空のとき) | ペイン移動 — 分類ペイン ↔ 一覧。`→` / `←` も同じ |
| `Enter`, `^E`, ダブルタップ | attach。`C-a d` で離れるとピッカーに戻る |
| `^S` | カーソルの席にメッセージ — `[mobile→セッション名] …` 接頭辞 + 2 秒後に到達確認。エージェントのない席は拒否 |
| `^K` | 席を閉じる (tmux セッション + その中のエージェント) |
| `^F` | fork — 会話を新しいエージェントセッションに引き継ぐ |
| `^Y` | 会話記録インデックス — カーソルのセッションのトランスクリプトのパスを表示 |
| `^H` / `^A` | 待機中の席だけ / 全部 |
| `^T` / `^W` / `^G` | 新しい順 / 待機優先 / カテゴリ順 |
| `^V` | 分類ペインを隠す / 出す (隠すとタブバー — `Tab` / `S-Tab` で回す) |
| `^R` | 状態を再スキャン (キャッシュ無視 · 並べ替えとフィルタは維持) |
| `^U` | プレビュー自動更新の間隔を 1 → 5 → 10 → 15 秒で切り替え |
| `^P` / `^O` | プレビューのオフ · オン / 大きく · 小さく |
| `^D` / `^A` | 終了セッションビュー ↔ 生きている席のビュー |
| `^/` | ヘルプ(ヘッダー)を描き直す。`?` はただのフィルタ文字 |
| `^X` | 終了 |

### 分割画面

- tmux の中では、左 = 分類ペイン、右 = セッション一覧(+ pane プレビュー)です。分類ペインで ↑↓ を動かすと右の一覧がすぐ変わります。
- 引数なしで `tmm` を実行すると、`tmm` という tmux セッションの中でピッカーが開きます — ターミナルのウィンドウサイズを変えてもピッカーは落ちません。ウィンドウを複数開くとそれぞれが自分のピッカー(`tmm`, `tmm-2` …)を持ちます。
- 幅 120 桁未満(スマホ)では分類ペインは 11 文字、それ以上では 16 文字です。一覧ペインが 120 桁以上ならプレビューは右、そうでなければ下に付きます。
- プレビューは新しい内容が先に見え、下の入力ボックスと statusline を切ってスマホの画面を節約します。
- `TMM_SPLIT=0` のときや tmux の外では、タブバーの画面になります。

### 終了セッションビュー (`^D`)

一覧が、いま tmux にないエージェントセッションに切り替わります。`tmuxc` で起動したものでもターミナルで直接動かしたものでも、トランスクリプトが残っていれば見つけます。

| キー · 表示 | 意味 |
|---|---|
| `◌` | 終了 |
| バッジ | どこで見つけたか: `SNAP` = `tmuxc save` のスナップショット(保存時の argv のまま) · `CC` Claude · `CDX` Codex · `CMD` Command Code · `OC` OpenCode |
| `^]` / `^\` | 期間を 12 時間ずつ広げる / 狭める (最初は直近 12 時間 · 判定はトランスクリプトの mtime) |
| `^L` | 系譜の全世代を表示 (既定は最新世代のみ) |
| `^T` / `^W` / `^G` | 新しい順 / SNAP 優先 / カテゴリ |
| `Enter` | 復旧 — 元の cwd に tmux セッションを作り、`--resume <session_id>` でエージェントを起動し直して attach |
| `^B` | 選択復旧モード — 見えている行が全部チェックされた状態で入り、スペースでチェックを切り替え、もう一度 `^B` でチェックしたものだけ復旧 (5 件ずつ並列 · attach なし) |

- プレビューはそのセッションの最後の user / assistant メッセージを表示します。
- 復旧するモデル: SNAP ならスナップショットの argv のまま、そうでなければトランスクリプトの `model` + `--effort high`。Claude は fable 系でなければ 1M ウィンドウ(`[1m]`)を付けます。
- Pi のセッションは `tmuxc save` のスナップショットがあるときに復旧します。`--scan` は Claude · Codex のみ対応です。
- このビューでは `^S`(メッセージ)は使えません。先に復旧してください。

### fork (`^F` · `tmm fork`)

生きている、または終了したセッションの会話を別のエージェント · モデルに移して続けます(レートリミットのときなど)。元の会話には触れません。

- 同じエンジン = `tmuxc fork` のネイティブ分岐 — 履歴はそのまま、新しい conversation id。
- 別のエンジン = `tmuxc open` の新しいセッション + コンテキスト注入 — トランスクリプトのパスと最近の会話の抜粋(`~/.tmm/forks/<時刻>-<ソース>.md`)をプロンプトとして渡します。
- `^F` で名前 · エージェント(claude / codex / opencode / cmd) · モデル(fzf 検索)を選ぶと、作成してピッカーに戻ります。名前の既定値はソースの `#N` → `#N+1`。どの段階でも `^C` で取り消せます。
- モデル別名 = `~/.tmm/models`(ユーザー · 優先) + `~/.tmm/models.generated`(`tmm models refresh` の生成物)。OpenCode は `--model` の接頭辞がそのままゲートウェイなので `TMM_MODELS_PROVIDER`(既定 `openrouter`)で選びます — `opencode/` = zen、`openrouter/` = OpenRouter。
- Claude は fable 系でなければ `--ctx 1m` が自動で付きます。

```bash
# --dry-run はコマンドを表示するだけ (副作用なし)
tmm fork my-app-dev#1 --agent codex --model <alias> --dry-run
tmm fork my-app-dev#1 --agent claude --model sonnet --attach     # 同じエンジンのネイティブ fork
tmm models refresh                                    # ライブ一覧 → ~/.tmm/models.generated
TMM_MODELS_PROVIDER=opencode tmm models refresh opencode
tmm models find <query>                               # 別名 · モデル id を検索
```

### 会話記録インデックス (`^Y` · `tmm idx`)

- `^Y` はカーソルのセッションの `agent · session_id · cwd · transcript · match` を画面に表示します(どのキーでも戻る)。エージェントに「前の会話はこのファイル」とすぐ伝えたいときに使います。
- `tmm idx NAME|SID` は同じ情報を CLI で出します · `--path` = パスだけ · `--json` = JSON。
- `match`: `exact`(名前が完全一致) · `cwd`(cwd による) · `fallback`(生きているセッションで最近使われたファイル)。

### 自動更新

| 段 | 何を | 既定の間隔 |
|---|---|---|
| pane | カーソルの席のプレビューだけ描き直す | 1 秒 (`^U` で 1/5/10/15 · `TMM_AUTO_PREVIEW`) |
| 全席 | 状態 · 最後の時刻 · 並び順を計算し直す | 20 秒固定 (`TMM_AUTO`) |

attach 中は止まり、`C-a d` で離れると再開します。更新されてもカーソルは見ていた席を追い、フィルタも残ります。

### CLI サブコマンド

```bash
tmm                 # TUI
tmm --auto N        # TUI、プレビュー自動更新 N 秒 (0=off)
tmm ls [PAT]        # テキスト一覧 (フィルタ)
tmm h               # HUMAN/BLOCK/STUCK の席だけ
tmm p NAME [N]      # pane の直近 N 行
tmm s NAME "msg"    # メッセージ (ガード + 到達確認)
tmm a NAME [-i]     # attach (-i: デスクトップのウィンドウサイズを固定)
tmm kill NAME [--yes]                 # 席を閉じる
tmm ss              # seat-scan の生出力
tmm save            # tmuxc save (tmuxc が必要)
tmm doctor          # 依存関係 · 環境のチェック
tmm menu            # fzf がないときの番号メニュー
tmm dead [PAT] [--since H] [--all]    # 終了セッションの一覧
tmm dp NAME|SID [N]                   # 終了セッションの最後の会話 N 行
tmm restore NAME [--dry-run]          # 終了セッションを 1 件復旧 → attach
tmm restore-all [--since H] [--dry-run] [--yes]   # 期間内を全部復旧 (attach なし)
tmm idx NAME|SID [--json|--path]      # トランスクリプトのパス
tmm fork SRC --agent AG --model M [--name N] [--cwd C] [--effort E] [--ctx 1m] [--prompt P] [--dry-run] [--attach]
tmm models [AG]                       # fork モデル別名の一覧
tmm models refresh [AG...]            # ライブ一覧から生成物を更新
tmm models find QUERY                 # 別名 · モデル id を検索
```

### 設定

| 項目 | 場所 / 変数 | 既定 |
|---|---|---|
| カテゴリ規則 | `~/.tmm/categories` (`TMM_CATEGORIES`) | インストール時に例をコピー |
| カテゴリの役割接頭辞 | `TMM_CAT_STRIP` | `FB_ ft-` (空白区切り) |
| fork モデル別名 | `~/.tmm/models` (`TMM_MODELS`) | インストール時に例をコピー · 生成物より優先 |
| fork モデル生成物 | `~/.tmm/models.generated` (`TMM_MODELS_GEN`) | `tmm models refresh` が作る · 手で編集しない |
| OpenCode プロバイダー | `TMM_MODELS_PROVIDER` | `openrouter` |
| fork 抜粋フォルダ / メッセージ数 | `~/.tmm/forks/` (`TMM_FORKS`) / `TMM_FORK_EXCERPT_N` | 40 |
| 状態スキャンのキャッシュ | `TMM_CACHE_TTL` | 20 秒 (`^R` は無視) |
| seat-scan のパス | `TMM_SCAN` | インストール版 `libexec/seat-scan.sh` → `~/.claude/skills/tmuxc/scripts/seat-scan.sh` |
| プレビュー行数 | `TMM_PREVIEW_LINES` | 40 |
| pane 自動更新 | `TMM_AUTO_PREVIEW` / `tmm --auto N` / `^U` | 1 秒 · 0 = off |
| 全席自動更新 | `TMM_AUTO` | 20 秒 · 0 = off |
| 新しい待機席のベル | `TMM_BELL` | 1 (0 = オフ) |
| 開始画面 | `TMM_TAB` | 1 = タブビュー · 0 = 一覧 |
| 分割画面 | `TMM_SPLIT` | 1 (tmux の中だけ) · 0 = タブバー |
| 終了ビューの初期期間 | `TMM_DEAD_SINCE` | 12 (時間) |
| 生存判定の猶予 | `TMM_LIVE_GRACE` | 90 秒 — この間に書かれたトランスクリプトは生きているとみなす |
| 復旧時の起動待ち | `TMM_RESTORE_TRIES` | 20 (× 3 秒) |
| 選択復旧のバッチサイズ | `TMM_RESTORE_BATCH` | 5 |

### 既知の制限 · トラブルシューティング

- 完了マーカーには時:分しかなく日付がありません。2 日以上放置した席は経過が小さく見えることがあります。
- fzf はヘッダーを折り返さずに切るので、幅の狭いスマホではヘッダーの後ろが見えないことがあります。

| 症状 | 対処 |
|---|---|
| 自動更新が動かない · `^Y` が効かない | `tmm doctor` で fzf のバージョン(≥ 0.54)と `curl` を確認 |
| 同じエンジンの fork なのに履歴が引き継がれない | `tmuxc` < 0.4.0 — `tmuxc` を入れ直す |
| fork のモデルメニューが空 · 欲しいモデルがない | `install.sh` を再実行(例をコピー)するか `tmm models refresh` → `tmm models find QUERY` |
| OpenCode の fork が別のゲートウェイで開く | 別名の接頭辞を確認 · `TMM_MODELS_PROVIDER=openrouter tmm models refresh` |
| `tmm idx NAME` が「インデックスなし」 | `tmm idx NAME --json` の `match` を確認 |
| 復旧後に「起動を確認できない」 | セッションは残っている — attach して pane を見る |

## 必要なもの

- macOS または Linux
- `bash` ≥ 4 (macOS 標準の 3.2 は不可 → `brew install bash`) · `tmux` ≥ 3.2 · `fzf` ≥ 0.54 · `python3` ≥ 3.9 (標準ライブラリのみ) · `curl`
- `tmuxc` ≥ 0.4.0 (`feature-pack/tmuxc`) — なければ `install.sh` が止まります。
- 任意: Tailscale(外からの接続) · スマホの SSH クライアント(例: Termius)
- API キー · アカウント: なし

## リンク

- [INSTALL.md](INSTALL.md) — エージェント向けインストール手順
- [tmuxc パック](../tmuxc/) — 必須パック
- [test/verify.sh](test/verify.sh) — 回帰テスト
- [AI Feature Pack カタログ](../../README.ja.md)
