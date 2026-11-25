<div align="center">

# headroom

**AI コーディングエージェントのコンテキストを LLM に届く前に圧縮するローカルプロキシ — `ANTHROPIC_BASE_URL` 1行、コード変更 0。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- オープンソースの `headroom-ai` プロキシをエージェントと LLM API の間に置きます。クライアントは `ANTHROPIC_BASE_URL`(または `OPENAI_BASE_URL`)を変えるだけです。
- 内容の種類(JSON · コード(AST) · 散文)ごとに分けて圧縮します。原本はローカルに残し、モデルには圧縮版と復元用の `headroom_retrieve` を渡します。
- 圧縮出力を決定的に揃えて prefix キャッシュキーを守ります(`token` モードで `cache_bust_count: 0`)。
- ラッパー `claude-hr.sh` が headroom(:8790、圧縮)と cliproxy(:8317、マルチアカウントのローテーション)の2レイヤーをプロジェクトごとに個別にオン・オフします。経由を指定したレイヤーが落ちていれば、黙って直結せずに止まります。
- Claude Code 用トグルスキル `/headroom on|off|status` と、`headroom-ai==0.33.x` 向け運用パッチ(`patches/apply.sh`)を同梱します。
- 効果が積み上がるのは長いセッションや同じファイルを何度も読む作業だけです。短い単発の入力では効果がありません。

## クイックスタート

```bash
# リポジトリのルートで
python3.12 -m venv ~/.headroom-venv
~/.headroom-venv/bin/pip install "headroom-ai==0.33.0"
bash feature-pack/headroom/patches/apply.sh

# プロキシ起動 (圧縮 + キャッシュ共存 · テレメトリ off)
HEADROOM_MODE=token HEADROOM_COMPRESS_USER_MESSAGES=1 HEADROOM_CODE_AWARE_ENABLED=1 HEADROOM_TELEMETRY=off \
  ~/.headroom-venv/bin/python -m headroom.proxy.server \
  --port 8790 --compress-user-messages --exclude-tools Bash --code-aware

# 別のシェルで: 確認してから1セッションだけプロキシ経由で起動 (グローバルに export しない)
curl -s localhost:8790/health
ANTHROPIC_BASE_URL=http://localhost:8790 claude
```

## インストール

このパックには `INSTALL.md` がありません。エージェントに任せるなら「`feature-pack/headroom/README.md` を読んで headroom とトグルスキルをインストールして」と伝えてください。この README のエージェント手順は、有効にするプロジェクトを先にユーザーに聞き、自動ではオンにしません。手作業の場合は、リポジトリのルートで次の3ステップを行います。

### 1. headroom-ai をインストール

ML extras(`headroom-ai[ml]` · `[all]`、Kompress)は、キャッシュの安定性とメモリコストのため既定のインストールから外します。

```bash
python3.12 -m venv ~/.headroom-venv
~/.headroom-venv/bin/pip install "headroom-ai==0.33.0"
~/.headroom-venv/bin/headroom --version       # 0.33.0
```

### 2. 運用パッチを適用

`apply.sh` はインストール済みのバージョンを見てパッチを選び(0.33.x には 0009、その他の互換バージョンには 0006)、何度実行しても結果は同じです。既定の Python は `~/.headroom-venv/bin/python` で、第1引数で変えられます。

```bash
bash feature-pack/headroom/patches/apply.sh   # [/path/to/venv/bin/python]
```

### 3. トグルスキルとラッパーをインストール

```bash
HR_DIR="$PWD/feature-pack/headroom"
mkdir -p ~/.claude/skills/headroom ~/.headroom
cp "$HR_DIR/SKILL.md" ~/.claude/skills/headroom/SKILL.md
cp "$HR_DIR/templates/claude-hr.sh" ~/.headroom/claude-hr.sh
mkdir -p ~/.claude/skills/headroom-cliproxyapi/scripts
cp "$HR_DIR/scripts/file-logs.sh" ~/.claude/skills/headroom-cliproxyapi/scripts/file-logs.sh
cp "$HR_DIR/scripts/clean-proxy-logs.sh" ~/.claude/skills/headroom-cliproxyapi/scripts/clean-proxy-logs.sh
cp "$HR_DIR/scripts/file-logs.sh" ~/.headroom/headroom-cliproxy-file-logs.sh
cp "$HR_DIR/scripts/clean-proxy-logs.sh" ~/.headroom/clean-proxy-logs.sh
# ルーティング状態ファイル — 既定は両方 off (直結)
[ -f ~/.headroom/routing.json ] || cp "$HR_DIR/templates/routing.json" ~/.headroom/routing.json
chmod +x ~/.headroom/claude-hr.sh ~/.headroom/headroom-cliproxy-file-logs.sh ~/.headroom/clean-proxy-logs.sh ~/.claude/skills/headroom-cliproxyapi/scripts/*.sh
```

その後 `~/.zshrc` に `alias claude-hr='~/.headroom/claude-hr.sh'` を追加し、`claude-hr` で起動します。

## 使い方

### ルーティングスイッチャー (`claude-hr.sh`)

| headroom | cliproxy | `ANTHROPIC_BASE_URL` |
|---|---|---|
| on | on | `http://localhost:8790` — 圧縮 → ローテーション → サブスクリプション |
| off | on | `http://127.0.0.1:8317` — ローテーション → サブスクリプション、圧縮なし |
| off | off | unset — Anthropic へ直結 |
| on | off | 不可 — headroom LaunchAgent の upstream が `127.0.0.1:8317` に固定されているため、ラッパーが exit 78 で拒否 |

```bash
HR=~/.headroom/claude-hr.sh
$HR route status                    # このプロジェクトの有効値 + プロセスの実際の状態
$HR route headroom on|off           # このプロジェクトのみ
$HR route cliproxy on|off
$HR route headroom on --global      # 全プロジェクトの既定値
$HR route reset [--global]
```

状態ファイルは `~/.headroom/routing.json` ひとつだけです。手で編集せず `route` で変更します。

```json
{
  "default":  { "headroom": false, "cliproxy": false },
  "projects": { "/abs/project/root": { "headroom": true, "cliproxy": true } }
}
```

- プロジェクトの項目があればそれを、なければ `default` を使います。ファイルがなければ直結です。
- プロジェクト root は `git --git-common-dir` 基準なので、worktree も本体プロジェクトひとつにまとまります。
- 一回限りの上書き: 環境変数 `HEADROOM_ROUTE=0|1` · `CLIPROXY_ROUTE=0|1` が設定より優先されます。
- 経由を指定したレイヤーが落ちていれば exit 69 で止まります(黙ったフォールバックなし)。
- `--model` が cliproxy のカタログになければ、起動前に stderr で警告します(ブロックはしません)。
- Claude Code の中ではスキルで `/headroom on` → `route headroom on` · `/headroom off` → `route headroom off` · `/headroom status` → `route status` です。
- 環境変数はプロセス起動時に固定されます。すでに動いているセッションは再起動が必要です。tmux やオーケストレーターが起動するセッションまで経由させるには、普段使う claude の alias をラッパーに向けます(例: `alias cc='~/.headroom/claude-hr.sh --model "..."'`)。

### プロキシの起動

```bash
HEADROOM_MODE=token HEADROOM_COMPRESS_USER_MESSAGES=1 HEADROOM_CODE_AWARE_ENABLED=1 HEADROOM_TELEMETRY=off \
  ~/.headroom-venv/bin/python -m headroom.proxy.server \
  --port 8790 --compress-user-messages --exclude-tools Bash --code-aware
```

- `headroom proxy`(click)はオプションが少ないです。すべて選ぶには `python -m headroom.proxy.server` を直接実行します。その場合は `--no-telemetry` の代わりに `HEADROOM_TELEMETRY=off` を使います。
- モード: `cache` = prefix を固定し観察のみ(圧縮 ~0%) · `token` = 積極的な圧縮 + キャッシュ共存(再読込で 25~30%)。
- 8790 がすでに LISTEN していれば新しく起動せずそれを使います。複数のセッションがそれぞれ起動すると `Errno48 Address already in use` のクラッシュループになります。スキルの `on` はこれを守ります。

### ほかのエージェント

`headroom wrap <agent>` がプロキシの起動とエージェントの実行を一度に行います。

```bash
headroom wrap claude        # Claude Code (ANTHROPIC_BASE_URL)
headroom wrap codex         # Codex
headroom wrap cursor        # Cursor — 設定を出力、1回貼り付け
headroom wrap aider         # Aider
headroom wrap copilot       # GitHub Copilot CLI
headroom proxy --port 8790  # その他の OpenAI 互換クライアント: OPENAI_BASE_URL=http://localhost:8790/v1
```

Codex を cliproxy と一緒に使うときは、`headroom wrap codex` ではなく Codex の custom provider で固定します。そうすると `codex` · `codex exec` · tmux がすべて同じ経路を通ります。認証は cliproxy の OAuth が行うので、`CODEX_DUMMY_API_KEY` はダミー値で構いません。

```toml
# ~/.codex/config.toml
model_provider = "headroom"

[model_providers.headroom]
name = "Headroom"
base_url = "http://127.0.0.1:8790/v1"
env_key = "CODEX_DUMMY_API_KEY"
wire_api = "responses"
```

ほかのインストール手段は `npm install headroom-ai` · `docker pull ghcr.io/chopratejas/headroom:latest` で、常駐サービスは `headroom install apply --preset persistent-service --providers auto` です。

### 動作確認 (`/stats`)

```bash
curl -s localhost:8790/health        # status healthy
curl -s localhost:8790/stats         # 圧縮率 + cache_bust_count (0 が正常)
```

| 指標 | 意味 |
|---|---|
| `avg_compression_pct` | 圧縮がどれだけ効いたか |
| `cache_bust_count` | 0 を保つ必要があります。0 より大きければキャッシュが壊れた = 損 |
| `cache_write_1h_tokens` | 1h extended キャッシュを使っているか |

`/stats` の `api_req` が 0 から増えれば、実際に経由が始まっています。

### プライバシー

- プロンプト · コード · 認証情報は外に出ません(意図した upstream にだけ送られます)。
- 匿名の利用テレメトリが既定でオンです(5分ごとに集計統計のみ)。止めるには `HEADROOM_TELEMETRY=off` を使います(上の起動コマンドに含まれています)。
- `learn` · `memory` は既定で off です。off のままにしてください。
- サプライチェーンの注意: 同梱の RTK バイナリと、起動時に huggingface.co からモデルをダウンロードします。

### 既知の制限

| 経路 | 圧縮率 |
|---|---|
| ライブラリ直接呼び出し(`compress_user_messages=True`) | 83.7% |
| ライブプロキシ — 単発の read | 0% |
| ライブプロキシ — 再読込 / supersede | 25~30% (最高 30.7%) |

- 単発で 0% なのは設計どおりです。`DEFAULT_EXCLUDE_TOOLS = {Read,Bash,Grep,Glob,Edit,Write}` と `protect_recent`(既定 4)が標準ツールの結果と最近のメッセージを守ります。
- 可逆圧縮はコンテキスト内では lossy です。デバッグ作業では `headroom_retrieve` の復元が正しいかを別途確認してください。
- 数値は環境 · バージョン(v0.33.0)によって変わることがあります。

### トラブルシューティング

- `400 messages.N: user messages must have non-empty content` — 圧縮が空文字列を返したケースです。`patches/apply.sh` の空値ガードが防ぎます。一時的には起動コマンドから `--compress-user-messages` を外します。
- 大きなリクエストで 500 · `compression_first_stage` RuntimeError — tree-sitter パーサーをスレッド間で共有して起きた panic です。`patches/apply.sh` が直します。ログに `pyo3_runtime.PanicException: _native::Parser is unsendable` が出ていればこのケースです。
- すべてのセッションで `API Error: Connection refused` — プロキシ(8790)が落ちています。プロキシを経由しないシェルから再起動し、止まっていたセッションでは同じ入力を送り直します。

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.headroom.proxy.plist 2>/dev/null
launchctl enable    gui/$(id -u)/com.headroom.proxy
launchctl kickstart -k gui/$(id -u)/com.headroom.proxy
curl -sf -m1 http://localhost:8790/health
```

- 予防: `ANTHROPIC_BASE_URL` をシェル全体に export しないでください。プロキシが落ちるとすべてのセッションが一斉に止まります。ラッパーから起動します。

## 必要なもの

- Python 3.12(`python3.12 -m venv`) · `headroom-ai==0.33.0`
- zsh(`claude-hr.sh`) · bash · python3 · curl
- 常駐サービスと復旧コマンドは macOS の LaunchAgent(`launchctl`)が前提です。
- cliproxy(:8317)はこのパックに含まれていません。headroom + cliproxy の経路を使うには別途起動してください。
- API キー · アカウント: 使っているエージェントの既存の認証をそのまま使います。

## リンク

- [SKILL.md](SKILL.md) — `/headroom` トグルスキル
- [patches/README.md](patches/README.md) — バージョン別の運用パッチと原因
- [SSOT.md](SSOT.md) — コンテキストコストの整理
- [NOTES.md](NOTES.md) — パッチノート
- [AI Feature Pack カタログ](../../README.ja.md)
