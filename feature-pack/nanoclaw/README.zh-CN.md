<div align="center">

# nanoclaw

**基于 Claude Agent SDK 的多智能体平台。每个智能体在隔离的 Docker 容器中运行,并通过 Slack 与你对话。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 在 Slack 频道中运行对话式 AI 智能体,可替代 OpenClaw。
- 在 Docker 容器内运行编码智能体(Bash、Read、Write、Edit 等),崩溃不会波及外部。
- 用 `groups/` 划分人设:每个 group 有一个 `CLAUDE.md` 和一个 `memory/` 文件夹。
- 会话保存在 SQLite 和 `memory/` 文件中,并镜像到 Redis。
- 通过技能(内置约 31 个,可自行添加)以 Configure-Don't-Code 的方式扩展。
- 支持多实例:一个 NanoClaw 对应一名成员。

## 快速开始

```bash
git clone https://github.com/qwibitai/nanoclaw.git
cd nanoclaw
npm install
npm run build

# 构建智能体镜像
cd container && docker build -t nanoclaw-agent:latest . && cd ..

# 首次运行后,在聊天中输入 /setup,完成 OneCLI 安装和智能体注册
node dist/index.js
```

## 安装

可以直接让智能体执行 "Read feature-pack/nanoclaw/INSTALL.md and install it"。智能体会询问安装路径和智能体名称。手动安装则按 [INSTALL.md](INSTALL.md) 的步骤进行(约 15 分钟):

1. 按计划运行的智能体数量启动 Docker(推荐 Colima)。
2. clone、安装依赖并构建 NanoClaw(upstream: `qwibitai/nanoclaw`)。
3. 运行一次 `node dist/index.js`,再用 `/setup` 设置 OneCLI。OneCLI 是把 Claude API 访问注入容器的代理,监听 `localhost:10254`。
4. 创建 Slack 应用(开启 Socket Mode),把两个令牌写入 `.env`。
5. 创建带有人设和 memory 文件的 group。
6. 构建 `nanoclaw-agent` 镜像并启动 NanoClaw。
7. 可选:从 OpenClaw 迁移技能和定时任务。只要 bot 令牌不同,两者可以并行运行。
8. 可选:用 launchd plist 在登录时自动启动 NanoClaw(见 [INSTALL.md](INSTALL.md) 的 Step 8)。

```bash
# 用 Colima 准备 Docker (参见下面的规格表)
brew install colima docker
colima start --cpu 2 --memory 4 --disk 30
docker info

# Slack 令牌
cat > .env << 'EOF'
SLACK_BOT_TOKEN=<your-bot-token>
SLACK_APP_TOKEN=<your-app-token>
ASSISTANT_NAME=NanoClaw
EOF

# 人设 group
mkdir -p groups/main/memory
cp groups/global/CLAUDE.md groups/main/CLAUDE.md
touch groups/main/memory/{directives,mistakes,achievements}.md
```

## 用法

### 核心概念

- **Group**: 智能体的人设单位,由 `groups/{name}/CLAUDE.md` 定义。
- **Container**: 每个任务启动一个 Docker 容器,完成后退出。
- **Skill**: `.claude/skills/` 下的 `SKILL.md` 文件。
- **Memory**: 失误、成果和指令保存在 `groups/{name}/memory/` 中。
- **OneCLI**: Claude API 密钥代理,会自动注入容器。

### OpenClaw 与 NanoClaw 对比

| 项目 | OpenClaw | NanoClaw |
|------|----------|----------|
| Brain | 内置 LLM 路由 | Claude Agent SDK (包含在 Claude 订阅内,无 API 费用) |
| 运行环境 | 主机进程 | Docker 容器 (隔离) |
| 扩展 | 技能 + 插件 | `groups/` + `skills/` (Configure-Don't-Code) |
| 多智能体 | 单实例 | 1 个 NanoClaw = 1 名成员 (多实例) |
| 持久化 | 内部 DB | SQLite + `memory/` 文件 + Redis 镜像 |
| 通信 | HTTP API + Slack | 原生 Slack + Redis Stream |

### Colima 规格

| 设置 | 1 个智能体 | 3 到 5 个 | 10 个以上 |
|------|-----------|-----------|-----------|
| CPU 核数 | 2 | 4 | 6 |
| RAM (GB) | 4 | 8 | 12 |
| 磁盘 (GB) | 30 | 60 | 100 |

### 管理 NanoClaw

```bash
# 列出 group
ls groups/

# 创建 group (之后编写 groups/{name}/CLAUDE.md)
mkdir -p groups/{name}/memory

# 查看正在运行的容器和 OneCLI
docker ps --filter "name=nanoclaw"
docker ps --filter "name=onecli"

# 查看 launchd 服务
launchctl list | grep nanoclaw

# 统计已保存的消息数
sqlite3 store/messages.db "SELECT COUNT(*) FROM messages;"

# 列出内置技能,添加自定义技能 (之后编写 SKILL.md)
ls .claude/skills/
mkdir -p groups/{name}/skills/{skill-name}
```

## 环境要求

- macOS (推荐 Apple Silicon M1 或更新)
- Node.js 20+ 和 npm
- Docker Desktop 或 Colima
- Git
- Claude Pro 或 Max 订阅
- 可以创建应用的 Slack 工作区
- 安装时间 (约15分钟)

## 链接

- [INSTALL.md](INSTALL.md) — 安装指南
- [qwibitai/nanoclaw](https://github.com/qwibitai/nanoclaw) — upstream 项目
- [AI Feature Pack 目录](../../README.zh-CN.md)
