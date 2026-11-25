<div align="center">

# agent-browser

**AI エージェント向けのブラウザ自動化 CLI — Web スクレイピング · スクリーンショット · フォーム入力 · 動画録画 · デバッグ · スタイル付きカードの生成。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- 動的な SPA や React のページを含め、Web ページの内容を抽出します(スクレイピング)。
- ページ全体や一部のスクリーンショットを撮り、2× レティナのカード画像を作れます。
- ログインやサインアップなどのフォームを自動で入力し、ログインセッション(クッキー)を保存 · 復元できます。
- WebM で録画し、GIF に変換できます。
- コンソールログとエラーを確認し、ネットワークの応答をモックできます。
- Rust 製の CDP デーモンが Chrome に直接つながります。ブラウザ拡張が必要なときにも使えます。

## クイックスタート

```bash
npm install -g agent-browser
agent-browser install    # Chromium をダウンロード (初回のみ、約 150MB)
agent-browser --native open "https://example.com" && agent-browser --native snapshot -i && agent-browser --native close
```

## インストール

このパックは 3 つをインストールします: agent-browser CLI(0.16.3 以上)、ブラウザ作業でエージェントが自動的に使うスキル、環境ごとの設定 · 速度比較 · ヒントをまとめた TOOLS.md のセクション。

### エージェントでインストール

エージェントに次のように頼んでください。

```text
feature-pack/agent-browser/INSTALL.md を読んでインストールして
```

### 手動でインストール

```bash
# feature-pack/agent-browser/ の中で実行
npm install -g agent-browser
agent-browser install                  # Chromium をダウンロード (初回のみ、約 150MB)
agent-browser --version                # 0.16.3 以上であること
pip3 install Pillow                    # スクリーンショットカード用
cp -r skill/ ~/.openclaw/workspace/skills/agent-browser/   # Claude Code は ~/.claude/skills/agent-browser/
cat config/tools-section.md >> ~/.openclaw/workspace/TOOLS.md
```

- スキルのフォルダ(`~/.openclaw/workspace/skills`)と workspace(`~/.openclaw/workspace`)は OpenClaw の既定のパスです。違う場合は自分のパスに置き換えてください。
- `config/tools-section.md` は、agent-browser の使用ルール(native を優先、検索ツールではない)、速度比較の表、動画キャプチャのコマンド、スクリーンショットカードのパイプラインを TOOLS.md に追加します。

### 動作確認

```bash
agent-browser --version
agent-browser --native open "https://example.com" && agent-browser --native get title && agent-browser --native screenshot /tmp/ab-verify.png && agent-browser --native close
agent-browser --native open "https://example.com" && agent-browser --native snapshot -i && agent-browser --native close
python3 -c "from PIL import Image; print('Pillow OK')"
```

すべて通れば、インストールは完了です。

### トラブルシューティング

| 症状 | 対処 |
|------|------|
| `agent-browser: command not found` | `npm install -g agent-browser` をもう一度実行 |
| `Chromium not found` | `agent-browser install` を実行 |
| `--native` モードが失敗する | `--native` を付けず standard モードに戻す |
| Pillow の import エラー | `pip3 install Pillow` をもう一度実行 |
| スクリーンショットが切れる | HTML の高さが 620px 以下か確認し、超えるならカードを分ける |

## 使い方

### モードの選び方

| 場面 | モード | 理由 |
|------|------|------|
| 一般的なブラウジングとスクレイピング | `--native` | 速い(1 ページ約 150ms)、Node.js 不要 |
| スクリーンショットとキャプチャ | `--native` | 遅延が小さい |
| Chrome 拡張が必要 | `--native connect <port>` | 本物の Chrome のみ |
| 複雑な JS の SPA で描画に問題がある | standard (フラグなし) | Playwright の安定性 |
| CI/CD パイプライン | standard headless | 実績のある安定性 |

- 基本は常に先に `--native` を試し、問題があれば standard に戻します。
- Web 検索ツールではありません。検索や単純な URL の読み取りには、web search / fetch のツールを使ってください。

### 基本の流れ

```bash
SESSION="task-$(date +%s)"
trap "agent-browser close --session $SESSION 2>/dev/null" EXIT ERR

agent-browser --native --session "$SESSION" --headed open "https://example.com"
agent-browser --native --session "$SESSION" wait --load networkidle
agent-browser --native --session "$SESSION" snapshot -i          # 要素を @ref として一覧表示
agent-browser --native --session "$SESSION" click @e3
agent-browser --native --session "$SESSION" fill @e5 "you@example.com"
agent-browser --native --session "$SESSION" get text ".result"
agent-browser --native --session "$SESSION" screenshot ./result.png
agent-browser --native --session "$SESSION" close
```

- 操作の前に、必ず `snapshot -i` で要素を確認します。`@ref` の値はセッションごとに変わるので、別のセッションで使い回さないでください。
- 必ず `--session <name>` を使い、`trap` で後始末します。
- ローカルでは `--headed`(動きが見える)、CI/CD では付けません(headless が既定)。
- 要素を探す優先順位: ① `snapshot -i` の `@ref` ② CSS セレクタ ③ `find` コマンド(`find role button click` · `find text "Submit" click` · `find testid "btn" click`)。

### よく使う作業

```bash
# 待機の方法
agent-browser --native --session "$SESSION" wait "#element"            # 要素が現れるまで
agent-browser --native --session "$SESSION" wait 2000                  # 固定の待ち時間 (ms)
agent-browser --native --session "$SESSION" wait --text "Success"      # テキストが現れるまで
agent-browser --native --session "$SESSION" wait --url "**/dashboard"  # URL が一致するまで
agent-browser --native --session "$SESSION" wait --load networkidle    # すべてのリクエストが落ち着くまで

# クッキーの保存 / 復元
agent-browser --native --session "$SESSION" cookies get > cookies.json
agent-browser --native --session "$SESSION" cookies set "$(cat cookies.json)"

# ネットワークのモック
agent-browser --native --session "$SESSION" network route "**/analytics/*" --abort
agent-browser --native --session "$SESSION" network route "**/api/user" --body '{"id":1,"name":"Test"}'
agent-browser --native --session "$SESSION" network unroute

# 動画を録画して GIF に変換
agent-browser --native --session "$SESSION" record start "./demo.webm"
agent-browser --native --session "$SESSION" record stop
ffmpeg -i demo.webm -vf "fps=10,scale=480:-1:flags=lanczos" -c:v gif demo.gif

# デバッグ
agent-browser --native --session "$SESSION" console                    # ログを見る
agent-browser --native --session "$SESSION" errors                     # エラーを見る
agent-browser --native --session "$SESSION" eval "document.title"      # JS を実行
```

- ログインのポップアップを避けるときは、DOM 要素を `remove()` せず、CSS で隠してください(`remove()` は内容を壊します)。

### 起動中の Chrome に接続する

```bash
agent-browser --native connect 9222 --session "$SESSION"                                     # ポートで
agent-browser --native connect "ws://127.0.0.1:9222/devtools/browser/UUID" --session "$SESSION"  # WebSocket URL で
agent-browser --auto-connect --native snapshot                                                # 起動中の Chrome を自動で探す
```

- Chrome 拡張が必要なとき、macOS のオーディオ(BlackHole)ループバックが必要なとき、リモートやデバッグ用の Chrome につなぐときに `--native connect` を使います。

### スクリーンショットカード

共有用(Slack · Discord など)に、モバイル向けのスタイル付きカードを HTML から作ります。

```bash
agent-browser --native --session cap open "file:///tmp/card.html"   # 幅 375px、高さ 620px 以下の HTML
agent-browser --native --session cap screenshot "/tmp/raw.png"
agent-browser --native --session cap close
```

- agent-browser のビューポートは 1280×720px に固定なので、約 620px を超える内容は切れます。長い内容はカードを分けてください(カード 1 枚 = 話題 1 つ)。
- カードの幅は 375px、最終出力は 2× レティナ(幅 830px)です。上のスクリーンショットを Pillow で切り抜いて 2 倍に拡大します(スクリプト全体は [skill/SKILL.md](skill/SKILL.md))。
- フォントサイズ: 短い内容は見出し 15px · 本文 12px · コード 11px · 余白 20px / 中くらい 14 · 11 · 10 · 16px / 長い表(20 行以上) 13 · 10.5 · 9.5 · 14px。
- テーマはダークです(背景 `#1a1a2e`、カード `#16213e`、表の見出し `#0f3460`、枠線 `#1a4080`)。最後の行(footer)が見えているか必ず確認してください。

### エラーからの復旧

| エラー | 対処 |
|------|------|
| `No session found` | 先に `open` を実行 |
| `Element not found` | `snapshot -i` をやり直して ref を確認 |
| `Timeout` | `--timeout` を増やし、`wait` の条件を確認 |
| ゾンビセッション | `agent-browser session list` → `close --session <name>` |
| `--native` が失敗する | `--native` フラグを外して standard モードを使う |

コマンドの全一覧は `agent-browser --help` と `agent-browser <command> --help` で見られます。

## 必要なもの

- macOS (arm64 / x86_64)
- Node.js 18 以上と npm
- Python 3 + Pillow (スクリーンショットカード用)
- ffmpeg (WebM を GIF に変換するときだけ)
- アカウントや API キーは要りません。

## リンク

- [INSTALL.md](INSTALL.md) — エージェント向けのインストール手順
- [skill/SKILL.md](skill/SKILL.md) — スキルの定義
- [AI Feature Pack カタログ](../../README.ja.md)
