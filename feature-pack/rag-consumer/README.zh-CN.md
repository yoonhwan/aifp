<div align="center">

# rag-consumer

**只读取你登记的智能体对话记录、送进 `rag` 引擎,并负责检索 · 记忆 · 备份的配套包 (CLI `ai-rag-consumer`)**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 只读取在配置文件里写明路径并登记的 Codex rollout JSONL 文件。不会自己查找会话,也不监视文件夹。
- 把读取位置(字节范围 · checksum)记在加密的 SQLCipher 账本里,中断后可以接着读。消息正文不会存进账本。
- 写入之前先应用带版本的脱敏规则(redaction)。规则不通过就不写。
- 把对话片段发布到 `rag` 引擎,用 `search` 检索。过去的对话放进与检索分开的不可变加密 archive,用 `archive-search` 检索。
- 可选: 从对话中提取记忆候选,与原文引用核对后,由人来确认 · 拒绝 · 验证。
- 存储的加密备份,以及备份验证。
- 只运行一次的 `tick` 由 launchd 或 macOS 菜单栏应用(AIRAG.app)每 5 分钟调用一次。

## 快速开始

```bash
cd feature-pack/rag-consumer
uv venv --python 3.13
uv pip install ../rag .                     # 同时安装 rag 包(ai-feature-rag)和本包

# 3 个存储密钥 + rag 数据库密钥 — 各 64 位 hex,互不相同 (运行时不会生成密钥)
export AIRAG_CONSUMER_KEY_HEX=<64-hex> AIRAG_PROJECTION_KEY_HEX=<64-hex> AIRAG_ARCHIVE_KEY_HEX=<64-hex>
export AIRAG_PROFILE_SOURCE_KEY_HEX=<64-hex>

.venv/bin/ai-rag-consumer --config /abs/path/runtime.json init
.venv/bin/ai-rag-consumer --config /abs/path/runtime.json run --once
.venv/bin/ai-rag-consumer --config /abs/path/runtime.json search "query"
```

## 安装

### 没有 INSTALL.md

这个包目前既没有 `INSTALL.md`,也没有原始 README。下面的步骤来自 `pyproject.toml` · 源码头部注释 · `ops/` · `macos/`。想让智能体来装时,说"读 `feature-pack/rag-consumer/README.md` 并安装"。

### 手动安装

包名是 `ai-feature-rag-consumer`,入口命令是 `ai-rag-consumer`。依赖 `ai-feature-rag==0.1.0` 就是同一仓库里的 `rag` 包,所以要一起安装(快速开始里的 `uv pip install ../rag .`)。

1. 在密钥库里准备 4 个密钥(各 32 字节 = 64 位 hex · 互不相同)。
2. 编写 `runtime.json`(见下面的"运行时配置")。所有路径都必须是绝对路径,软链接会被拒绝。
3. 用 `init` 创建账本 · projection 数据库 · archive · 备份文件夹。
4. 先用 `run --once` 跑一次,再按下面的方式加上定时运行。

### 每 5 分钟运行一次

```bash
# A) launchd — 填好模板里的 __PYTHON__ · __CONFIG__ · __CREDENTIALS__ · __LOG_DIR__
cp ops/com.airag.consumer.plist.template ~/Library/LaunchAgents/com.airag.consumer.plist
launchctl load ~/Library/LaunchAgents/com.airag.consumer.plist

# B) 菜单栏应用 AIRAG.app — 不需要 Xcode,只要 swiftc
bash macos/build.sh            # 构建 + 签名 (没有设置签名身份时用 ad-hoc)
bash macos/build.sh test       # 纯逻辑测试 (不启动应用)
bash macos/build.sh install    # 复制到 ~/Applications/AIRAG.app
```

- 一次 tick = consumer 的一次处理。重试由 launchd 的下一个周期负责。
- 密钥从 `--credentials` 指定的本地配置文件里取(1Password CLI `op`,或只有所有者可读的密钥文件)。环境变量里已有的密钥优先。
- AIRAG.app 会从自己的菜单把自己注册为登录项。路径可以用 `~/.config/airag/app.json` 里的 `python` · `config` · `credentials` · `log_dir` 修改。

## 用法

### 命令

所有命令的形式都是 `ai-rag-consumer --config <runtime.json> <命令>`,输出一行 JSON。

| 命令 | 作用 |
|---|---|
| `init` | 创建账本 · projection 数据库 · archive · 备份文件夹 |
| `run [--once] [--task-completed] [--save] [--allow-gaps]` | 读取已登记的源并发布 · 不带 `--once` 时每隔 `poll_seconds` 重复 (Ctrl-C 停止) |
| `status` | 当前状态 |
| `search "<query>" [--limit N]` | 检索已发布的对话 (默认 5) |
| `archive-search "<query>" [--limit N]` | 检索 archive (默认 20) |
| `memory-candidates --state <state> [--limit N] [--skip N]` | 列出记忆候选 |
| `memory-confirm` · `memory-reject` · `memory-verify <candidate_id>` | 确认 · 拒绝 · 验证记忆候选 |
| `backup` | 创建加密备份 |
| `verify <backup_id>` | 验证备份 |

`python -m airag_consumer.tick --config <runtime.json> [--credentials <file>] [--log-dir <dir>]` 是单次处理的入口(退出码 0 ok · 10 skipped · 20 config · 30 key · 40 runtime · 50 internal)。

### 运行时配置

`runtime.json`(`schema_version` = 1)的必填字段:

| 字段 | 含义 |
|---|---|
| `project_root` | 项目文件夹 (绝对路径 · 必须存在) |
| `owner_id` · `tenant_id` · `project_id` | 标识符 (字母 · 数字 · `_` · `-`) |
| `consumer_db` · `projection_db` | 账本数据库 · projection 数据库路径 |
| `archive_root` · `backup_root` | archive · 备份文件夹 |
| `profile_source_db` · `profile_key` | 持有处理配置的 `rag` 数据库及其 `profile_key` (64 位 hex) |
| `collection` | 要发布到的 `rag` collection 名称 |
| `sources` | 要读取的文件列表 — 每项包含 `path` · `session_id` · `source_id` |

可选字段: `token_mode`(默认 `estimated`)· `allow_gaps` · `memory_enabled` · `memory_endpoint` · `memory_model` · `poll_seconds`(默认 30)· `reference`。

### 环境变量密钥

| 名称 | 用途 |
|---|---|
| `AIRAG_CONSUMER_KEY_HEX` | 账本数据库密钥 |
| `AIRAG_PROJECTION_KEY_HEX` | projection 数据库密钥 |
| `AIRAG_ARCHIVE_KEY_HEX` | archive 密钥 |
| `AIRAG_PROFILE_SOURCE_KEY_HEX` | `profile_source_db`(rag 数据库)的密钥 · 首次创建存储时需要 |
| `AIRAG_MEMORY_API_KEY` | 可选 · 记忆提取服务的密钥 |

所有密钥都是 64 位 hex,且必须互不相同。运行时不会把这些值传给无关的子进程。

## 环境要求

- Python 3.13 及以上、低于 3.15 · `uv`
- `rag` 包 (`ai-feature-rag` 0.1.0) · `sqlcipher3` 0.6.2
- 定时运行: macOS launchd,或用于构建 AIRAG.app 的 `swiftc`
- 可选: 1Password CLI `op` (tick 的密钥来源) · 记忆提取服务 (`memory_endpoint` · `memory_model`)
- API 密钥 / 账号: 仅在开启记忆提取时需要 `AIRAG_MEMORY_API_KEY`

## 链接

- [rag](../rag/README.zh-CN.md) — 本包使用的加密 RAG 引擎
- [ops/com.airag.consumer.plist.template](ops/com.airag.consumer.plist.template) — launchd 模板
- [macos/build.sh](macos/build.sh) — 构建 · 测试 · 安装 AIRAG.app
- [AI Feature Pack 目录](../../README.zh-CN.md)
