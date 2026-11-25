<div align="center">

# nanoclaw

**Claude Agent SDK ベースのマルチエージェントプラットフォーム。エージェントごとに隔離された Docker コンテナで動き、Slack で会話します。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- Slack チャンネルで対話型の AI エージェントを運用します。OpenClaw の代わりになります。
- Docker コンテナの中でコーディングエージェント (Bash・Read・Write・Edit など) を動かすので、クラッシュが外に広がりません。
- `groups/` でペルソナを分けます: グループごとに `CLAUDE.md` 1 つと `memory/` フォルダ 1 つ。
- セッションを SQLite と `memory/` ファイルに残し、Redis にミラーします。
- スキル (内蔵が約 31 個 + 自作) で、Configure-Don't-Code 方式で拡張します。
- マルチインスタンスに対応します: NanoClaw 1 つがクルー 1 人です。

## クイックスタート

```bash
git clone https://github.com/qwibitai/nanoclaw.git
cd nanoclaw
npm install
npm run build

# エージェントのイメージをビルド
cd container && docker build -t nanoclaw-agent:latest . && cd ..

# 初回起動のあと、チャットで /setup を入力して OneCLI のインストールとエージェント登録を進める
node dist/index.js
```

## インストール

エージェントに「Read feature-pack/nanoclaw/INSTALL.md and install it」と頼めば進みます。エージェントがインストール先とエージェント名を聞いてきます。手動で入れる場合は [INSTALL.md](INSTALL.md) の手順に従います (約 15 分)。

1. 動かすエージェントの数に合わせて Docker (Colima 推奨) を起動します。
2. NanoClaw を clone・依存関係のインストール・ビルドします (upstream: `qwibitai/nanoclaw`)。
3. `node dist/index.js` を一度実行し、`/setup` で OneCLI を設定します。OneCLI は Claude API へのアクセスをコンテナに渡すプロキシで、`localhost:10254` で動きます。
4. Slack アプリを作り (Socket Mode をオン)、2 つのトークンを `.env` に入れます。
5. ペルソナと memory ファイルを持つグループを作ります。
6. `nanoclaw-agent` イメージをビルドして NanoClaw を起動します。
7. 任意: OpenClaw のスキルと定期タスクを移行します。ボットトークンが別なら、両方を並行して動かせます。
8. 任意: launchd の plist でログイン時に NanoClaw を自動起動します ([INSTALL.md](INSTALL.md) の Step 8)。

```bash
# Colima で Docker を用意 (下のサイズ表を参照)
brew install colima docker
colima start --cpu 2 --memory 4 --disk 30
docker info

# Slack トークン
cat > .env << 'EOF'
SLACK_BOT_TOKEN=<your-bot-token>
SLACK_APP_TOKEN=<your-app-token>
ASSISTANT_NAME=NanoClaw
EOF

# ペルソナのグループ
mkdir -p groups/main/memory
cp groups/global/CLAUDE.md groups/main/CLAUDE.md
touch groups/main/memory/{directives,mistakes,achievements}.md
```

## 使い方

### 主な概念

- **Group**: エージェントのペルソナの単位。`groups/{name}/CLAUDE.md` で定義します。
- **Container**: タスクごとに Docker コンテナを起動し、作業して終了します。
- **Skill**: `.claude/skills/` 配下の `SKILL.md` ファイル。
- **Memory**: ミス・成果・指針が `groups/{name}/memory/` に残ります。
- **OneCLI**: Claude API キーのプロキシ。コンテナに自動で渡されます。

### OpenClaw と NanoClaw の比較

| 項目 | OpenClaw | NanoClaw |
|------|----------|----------|
| Brain | 内蔵の LLM ルーティング | Claude Agent SDK (Claude のサブスクリプションに含まれ、API 費用なし) |
| 実行環境 | ホストのプロセス | Docker コンテナ (隔離) |
| 拡張 | スキル + プラグイン | `groups/` + `skills/` (Configure-Don't-Code) |
| マルチエージェント | 単一インスタンス | 1 NanoClaw = クルー 1 人 (マルチインスタンス) |
| 永続化 | 内部 DB | SQLite + `memory/` ファイル + Redis ミラー |
| 通信 | HTTP API + Slack | Slack ネイティブ + Redis Stream |

### Colima のサイズ

| 設定 | エージェント 1 つ | 3〜5 つ | 10 以上 |
|------|------------------|---------|---------|
| CPU コア | 2 | 4 | 6 |
| RAM (GB) | 4 | 8 | 12 |
| ディスク (GB) | 30 | 60 | 100 |

### NanoClaw の管理

```bash
# グループの一覧
ls groups/

# グループを作成 (そのあと groups/{name}/CLAUDE.md を書く)
mkdir -p groups/{name}/memory

# 実行中のコンテナと OneCLI を確認
docker ps --filter "name=nanoclaw"
docker ps --filter "name=onecli"

# launchd サービスを確認
launchctl list | grep nanoclaw

# 保存されたメッセージ数
sqlite3 store/messages.db "SELECT COUNT(*) FROM messages;"

# 内蔵スキルの一覧、カスタムスキルの追加 (そのあと SKILL.md を書く)
ls .claude/skills/
mkdir -p groups/{name}/skills/{skill-name}
```

## 必要なもの

- macOS (Apple Silicon の M1 以降を推奨)
- Node.js 20+ と npm
- Docker Desktop または Colima
- Git
- Claude Pro または Max のサブスクリプション
- アプリを作れる Slack ワークスペース
- 所要時間 (約15分)

## リンク

- [INSTALL.md](INSTALL.md) — インストールガイド
- [qwibitai/nanoclaw](https://github.com/qwibitai/nanoclaw) — upstream プロジェクト
- [AI Feature Pack カタログ](../../README.ja.md)
