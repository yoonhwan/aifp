<div align="center">

# AI Feature Pack

**AI コーディングエージェント環境に、必要なものだけ選んで入れるフィーチャーパック集**
Claude Code · Codex · Pi · OpenCode · OpenClaw

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

[![Packs](https://img.shields.io/badge/packs-26-0b6e5f)](#-カタログ)
[![Guide](https://img.shields.io/badge/guide-GitHub%20Pages-0b6e5f)](https://yoonhwan.github.io/aifp/)
[![Platform](https://img.shields.io/badge/platform-macOS-555)](#-補足)

</div>

---

## このリポジトリについて

- AI コーディングエージェント向けの**フィーチャーパック**集です。1 パック = [`feature-pack/`](feature-pack/) 配下の 1 フォルダ。パック同士は独立しているので、必要なものだけ入れてください。
- 各パックには**エージェントが読む** `INSTALL.md` があります。エージェントに渡すと、前提条件の確認、CLI のインストール、スキル登録、動作確認まで進めます。
- 初めての方は図解ガイドからどうぞ: **[スマホから自分の AI エージェントを使う方法](https://yoonhwan.github.io/aifp/)**(英語 · [韓国語](https://yoonhwan.github.io/aifp/ko.html))。

## 🚀 クイックスタート

**方法 A — スマホ遠隔の組み合わせ (`tmuxc` + `tmm`)**

```bash
git clone https://github.com/yoonhwan/aifp.git && cd aifp \
  && bash feature-pack/tmuxc/install.sh \
  && bash feature-pack/tmm/install.sh
```

必要なもの: macOS、bash 4 以上、git、tmux、fzf(`tmm` 用)。

**方法 B — エージェントにパックを入れてもらう**

```bash
git clone https://github.com/yoonhwan/aifp.git
# その後、エージェントにこう伝えます。例:
#   "feature-pack/agent-browser/INSTALL.md を読んでインストールして"
```

エージェントは `INSTALL.md` を読み、次を行います。

1. 前提条件の確認
2. CLI のインストール
3. 認証・設定(必要ならユーザーに質問)
4. スキル登録
5. `TOOLS.md` / `AGENTS.md` への設定追加
6. インストールの検証

## 📦 カタログ

| # | パック | できること | 所要時間 | API キー | 認証 |
|---|--------|------------|----------|----------|------|
| 1 | [agent-browser](feature-pack/agent-browser/) | Web 自動化 — スクレイピング、スクリーンショット、フォーム入力、録画 | 約3分 | — | — |
| 2 | [imsg](feature-pack/imsg/) | iMessage/SMS — 会話の参照、メッセージ送信、リアルタイム監視 | 約3分 | — | — |
| 3 | [notebooklm](feature-pack/notebooklm/) | Google NotebookLM — ソースに基づく Q&A、リサーチ、音声生成 | 約5分 | — | Google |
| 4 | [obsidian-cli](feature-pack/obsidian-cli/) | Obsidian ボールト CLI — ノートの参照・作成・検索・移動 | 約3分 | — | — |
| 5 | [tts-say](feature-pack/tts-say/) | 統合 TTS — macOS `say` + ElevenLabs 音声合成 | 約3分 | ElevenLabs | — |
| 6 | [yt-transcribe](feature-pack/yt-transcribe/) | YouTube → 音声認識 → 要約の自動パイプライン | 約10分 | — | — |
| 7 | [termaid](feature-pack/termaid/) | Mermaid 図をターミナルに描画 — 設計の可視化時に自動で動作 | 約2分 | — | — |
| 8 | [baton](feature-pack/baton/) | マルチエージェントの handoff / worktree / archive 標準 — Claude Code・Codex・Gemini 間で作業を引き継ぐ | 約2分 | — | — |
| 9 | [cairn](feature-pack/cairn/) | スケジュール + マルチエージェント復旧台帳 — milestone / task / session lineage、baton・tmuxc と連携 | 約2分 | — | — |
| 10 | [tmuxc](feature-pack/tmuxc/) | tmux ベースの Claude Code・Codex・OMX セッション launcher / control — verified send/capture 通信標準を含む | 約1分 | — | — |
| 11 | [auto](feature-pack/auto/) | AutoResearch 自律実験ループ — ベースライン → 目標 → 自動最適化 | 約1分 | — | — |
| 12 | [nanoclaw](feature-pack/nanoclaw/) | AI マルチエージェントプラットフォーム(OpenClaw の代替)— Claude SDK Brain、Docker 分離、マルチクルー | 約15分 | — | Slack |
| 13 | [agent-cli](feature-pack/agent-cli/) | **AI コーディングエージェント CLI ツールキット** — インストールと比較、ペルソナを使う非対話の委任 | 約3分 | — | — |
| 14 | [headroom](feature-pack/headroom/) | Claude Code・Codex などのコンテキスト圧縮プロキシ + `/headroom` トグル | 約5分 | — | — |
| 15 | [fable-team](feature-pack/fable-team/ft2/) | **チームオーケストレーションハーネス (ft 2.0)** — 席・メモ・作業指示の共通コア、契約定義、Codex・Pi・Slack アダプター、診断ツール。フォルダごとの責任は `ft2/README.md` | — | — | — |
| 16 | [tmm](feature-pack/tmm/) | **モバイル(SSH) tmux 席 TUI** — スマホで数十のエージェントセッションをカーソルで選ぶ: プレビュー、最近の応答順、待機中の席を優先、メッセージ送信 (fzf) | 約1分 | — | — |
| 17 | [ctx-burn](feature-pack/ctx-burn/) | **ローカルのコンテキスト浪費監査ツール** — 7 種のランタイム(claude, codex, pi, opencode, hermes, openclaw, commandcode)を自動検出 | 約1分 | — | — |
| 18 | [ctx-plan](feature-pack/ctx-plan/) | **キャパシティ算定ツール** — ctx-burn の `ctx.v1` 出力だけを読み、アカウント構成に合う席数とピークセッション数を見積もる | 約1分 | — | — |

**ツリーに含まれるその他のもの**(各フォルダに独自のドキュメントがあります):
[agent-surface-audit](feature-pack/agent-surface-audit/) — エージェントのスキル・フック面を dry-run で棚卸し ·
[agent-surface-sync](feature-pack/agent-surface-sync/) — `feature-pack/*` と `hooks/` の共有エージェント面をインストール・更新 ·
[code-intel](feature-pack/code-intel/) — `ci` 単一エントリのコードインテリジェンス ·
[daily-trend-viewer](feature-pack/daily-trend-viewer/) — 人気動画と AI 動画ニュースを毎日見るローカルサイト ·
[mcp-manager](feature-pack/mcp-manager/) — MCP サーバー面の点検と整理 ·
[memory-system](feature-pack/memory-system/) — OpenClaw エージェントの記憶構造 ·
[rag](feature-pack/rag/) · [rag-consumer](feature-pack/rag-consumer/) — `airag` RAG パッケージとそのコンシューマー([`rag/docs/README.md`](feature-pack/rag/docs/README.md) から)。

## 📋 おすすめの順番

パック間の依存はありません。使いやすさの順です。

1. **obsidian-cli** — セカンドブレインの土台(他のパックのノート保存先)
2. **agent-browser** — Web 自動化(もっとも汎用的)
3. **yt-transcribe** — YouTube 文字起こし(obsidian-cli と相性が良い)
4. **notebooklm** — ナレッジ Q&A(ソースに基づく回答)
5. **tts-say** — 音声出力
6. **imsg** — iMessage 連携(macOS 専用)

複数のエージェントを運用する場合は次の順をおすすめします。

1. **baton** — worktree / handoff / archive の基準点
2. **cairn** — スケジュールと session lineage の台帳
3. **tmuxc** — Claude Code / Codex / OMX を tmux セッションで動かし、verified-send で通信
4. **tmm** — スマホ(Termius)からその席をカーソルで選んで接続する TUI

| ツール | 担当 |
|--------|------|
| baton | 作業の開始・保存・復旧用の `.baton/handoff/` と worktree / archive |
| cairn | `.cairn/plan.yaml` ベースの milestone / task / session lineage |
| tmuxc | live tmux エージェントセッションの作成、capture、send、kill |
| tmm | モバイル SSH での席一覧・プレビュー・attach・メッセージ(tmuxc の席を利用) |

## 🔧 その他のインストール方法

**手動** — パックフォルダの `README.md` を読んで順に進めます。

```
feature-pack/{name}/
├── README.md        ← 人向けの概要(ここから)
├── INSTALL.md       ← エージェント向けインストールプロンプト
├── cli/install.md   ← CLI インストールコマンド
├── skill/SKILL.md   ← スキル定義
├── config/          ← TOOLS.md / AGENTS.md に追加する内容
└── test/verify.md   ← インストール検証
```

すべてのパックにすべてのファイルがあるわけではありません。5 つのパック(`ctx-plan`、`fable-team`、`headroom`、`rag`、`rag-consumer`)には `INSTALL.md` がないので、README か docs から始めてください。

**すべて** — エージェントに「aifp リポジトリのフィーチャーパックを順番に全部インストールして」と伝えます。約 25 分かかります。

## 🔒 このリポジトリの成り立ち

- これは非公開の作業リポジトリから**書き出したコピー**です。内部の運用記録は取り除き、個人・組織の識別子はプレースホルダーに置き換えています。そのため、非公開データが必要な一部のテストはここではスキップされるか動きません。
- 書き出しのたびに 58 種のパターン(キー、トークン、アドレス、ID)を検査し、確認済みの許可リスト外に何も残っていない場合だけ書き出します。残っているキー形式の文字列はテスト用の固定値かドキュメントのプレースホルダーです。
- パックを入れるとき、自分のキーやトークンをリポジトリフォルダ内のファイルに書かないでください。

## 📌 補足

- **OS**: 現在は macOS のみ(Linux / Windows は今後)。
- **OpenClaw**: [openclaw.ai](https://openclaw.ai) · [GitHub](https://github.com/openclaw/openclaw)
- **質問**: Issue を立てるか [Discord](https://discord.com/invite/clawd) へ。

## ライセンス

MIT
