<div align="center">

# headroom

**在上下文到达 LLM 之前将其压缩的本地代理 — 只需一行 `ANTHROPIC_BASE_URL`,无需改代码。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 在智能体与 LLM API 之间放置开源的 `headroom-ai` 代理。客户端只需修改 `ANTHROPIC_BASE_URL`(或 `OPENAI_BASE_URL`)。
- 按内容类型(JSON · 代码(AST) · 散文)分别压缩。原文保留在本地,模型拿到压缩版和用于还原的 `headroom_retrieve` 通道。
- 让压缩输出保持确定性,从而保住 prefix 缓存键(`token` 模式下 `cache_bust_count: 0`)。
- 包装脚本 `claude-hr.sh` 按项目分别开关两层:headroom(:8790,压缩)和 cliproxy(:8317,多账号轮换)。若指定经过的那一层已停止,它会直接停下,而不会悄悄改为直连。
- 附带 Claude Code 开关技能 `/headroom on|off|status`,以及针对 `headroom-ai==0.33.x` 的运维补丁(`patches/apply.sh`)。
- 只有在长会话、反复读取同一文件的工作中效果才会累积。短小的单次输入没有效果。

## 快速开始

```bash
# 在仓库根目录
python3.12 -m venv ~/.headroom-venv
~/.headroom-venv/bin/pip install "headroom-ai==0.33.0"
bash feature-pack/headroom/patches/apply.sh

# 启动代理 (压缩 + 缓存共存 · 关闭遥测)
HEADROOM_MODE=token HEADROOM_COMPRESS_USER_MESSAGES=1 HEADROOM_CODE_AWARE_ENABLED=1 HEADROOM_TELEMETRY=off \
  ~/.headroom-venv/bin/python -m headroom.proxy.server \
  --port 8790 --compress-user-messages --exclude-tools Bash --code-aware

# 在另一个 shell 中: 确认后只让一个会话经过代理 (不要全局 export)
curl -s localhost:8790/health
ANTHROPIC_BASE_URL=http://localhost:8790 claude
```

## 安装

本包没有 `INSTALL.md`。如果交给智能体,可以说"读 `feature-pack/headroom/README.md`,安装 headroom 和开关技能"。本 README 中的智能体步骤会先询问用户要启用哪些项目,不会自动开启。手动安装时,在仓库根目录执行下面 3 步。

### 1. 安装 headroom-ai

出于缓存稳定性和内存开销的考虑,默认安装不包含 ML extras(`headroom-ai[ml]` · `[all]`,Kompress)。

```bash
python3.12 -m venv ~/.headroom-venv
~/.headroom-venv/bin/pip install "headroom-ai==0.33.0"
~/.headroom-venv/bin/headroom --version       # 0.33.0
```

### 2. 应用运维补丁

`apply.sh` 根据已安装的版本选择补丁(0.33.x 用 0009,其他兼容版本用 0006),重复运行结果相同。默认 Python 为 `~/.headroom-venv/bin/python`,可用第一个参数更换。

```bash
bash feature-pack/headroom/patches/apply.sh   # [/path/to/venv/bin/python]
```

### 3. 安装开关技能和包装脚本

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
# 路由状态文件 — 默认两层都 off (直连)
[ -f ~/.headroom/routing.json ] || cp "$HR_DIR/templates/routing.json" ~/.headroom/routing.json
chmod +x ~/.headroom/claude-hr.sh ~/.headroom/headroom-cliproxy-file-logs.sh ~/.headroom/clean-proxy-logs.sh ~/.claude/skills/headroom-cliproxyapi/scripts/*.sh
```

然后在 `~/.zshrc` 中加入 `alias claude-hr='~/.headroom/claude-hr.sh'`,用 `claude-hr` 启动。

## 用法

### 路由切换器 (`claude-hr.sh`)

| headroom | cliproxy | `ANTHROPIC_BASE_URL` |
|---|---|---|
| on | on | `http://localhost:8790` — 压缩 → 轮换 → 订阅 |
| off | on | `http://127.0.0.1:8317` — 轮换 → 订阅,不压缩 |
| off | off | unset — 直连 Anthropic |
| on | off | 不允许 — headroom LaunchAgent 的 upstream 固定为 `127.0.0.1:8317`,包装脚本以 exit 78 拒绝 |

```bash
HR=~/.headroom/claude-hr.sh
$HR route status                    # 本项目的生效值 + 进程实际状态
$HR route headroom on|off           # 仅本项目
$HR route cliproxy on|off
$HR route headroom on --global      # 所有项目的默认值
$HR route reset [--global]
```

状态文件只有 `~/.headroom/routing.json` 一个。不要手动编辑,用 `route` 修改。

```json
{
  "default":  { "headroom": false, "cliproxy": false },
  "projects": { "/abs/project/root": { "headroom": true, "cliproxy": true } }
}
```

- 有项目条目就用它,没有就用 `default`。没有文件则为直连。
- 项目 root 以 `git --git-common-dir` 为准,因此 worktree 也会归并到主项目。
- 一次性覆盖:环境变量 `HEADROOM_ROUTE=0|1` · `CLIPROXY_ROUTE=0|1` 优先于配置。
- 若指定经过的那一层已停止,会以 exit 69 停下(不会静默回退)。
- 若 `--model` 不在 cliproxy 的目录中,启动前会在 stderr 发出警告(不阻止)。
- 在 Claude Code 中,技能把 `/headroom on` → `route headroom on` · `/headroom off` → `route headroom off` · `/headroom status` → `route status`。
- 环境变量在进程启动时就已固定。已在运行的会话需要重启。若要让 tmux 或编排器启动的会话也经过代理,把平时用的 claude alias 指向包装脚本(例如 `alias cc='~/.headroom/claude-hr.sh --model "..."'`)。

### 启动代理

```bash
HEADROOM_MODE=token HEADROOM_COMPRESS_USER_MESSAGES=1 HEADROOM_CODE_AWARE_ENABLED=1 HEADROOM_TELEMETRY=off \
  ~/.headroom-venv/bin/python -m headroom.proxy.server \
  --port 8790 --compress-user-messages --exclude-tools Bash --code-aware
```

- `headroom proxy`(click)选项较少。要完全控制,请直接运行 `python -m headroom.proxy.server`。此时用 `HEADROOM_TELEMETRY=off` 代替 `--no-telemetry`。
- 模式:`cache` = 固定 prefix,只观察(压缩 ~0%) · `token` = 积极压缩 + 缓存共存(重读时 25~30%)。
- 如果 8790 已在 LISTEN,就复用它,不要再启动一个。多个会话各自启动会导致 `Errno48 Address already in use` 崩溃循环。技能的 `on` 会保证这一点。

### 其他智能体

`headroom wrap <agent>` 一步完成代理启动和智能体运行。

```bash
headroom wrap claude        # Claude Code (ANTHROPIC_BASE_URL)
headroom wrap codex         # Codex
headroom wrap cursor        # Cursor — 输出配置,粘贴一次
headroom wrap aider         # Aider
headroom wrap copilot       # GitHub Copilot CLI
headroom proxy --port 8790  # 其他 OpenAI 兼容客户端: OPENAI_BASE_URL=http://localhost:8790/v1
```

Codex 与 cliproxy 一起使用时,不要用 `headroom wrap codex`,而是用 Codex custom provider 固定。这样 `codex` · `codex exec` · tmux 都走同一条路径。认证由 cliproxy OAuth 完成,所以 `CODEX_DUMMY_API_KEY` 填占位值即可。

```toml
# ~/.codex/config.toml
model_provider = "headroom"

[model_providers.headroom]
name = "Headroom"
base_url = "http://127.0.0.1:8790/v1"
env_key = "CODEX_DUMMY_API_KEY"
wire_api = "responses"
```

其他安装渠道为 `npm install headroom-ai` · `docker pull ghcr.io/chopratejas/headroom:latest`,常驻服务用 `headroom install apply --preset persistent-service --providers auto`。

### 确认运行 (`/stats`)

```bash
curl -s localhost:8790/health        # status healthy
curl -s localhost:8790/stats         # 压缩率 + cache_bust_count (应为 0)
```

| 指标 | 含义 |
|---|---|
| `avg_compression_pct` | 压缩生效的程度 |
| `cache_bust_count` | 必须保持 0。大于 0 表示缓存被破坏 = 亏损 |
| `cache_write_1h_tokens` | 是否使用了 1h extended 缓存 |

`/stats` 中的 `api_req` 从 0 开始增加,说明流量确实经过了代理。

### 隐私

- 提示词 · 代码 · 凭据不会离开本机(只发往预期的 upstream)。
- 匿名使用遥测默认开启(每 5 分钟只发送汇总统计)。用 `HEADROOM_TELEMETRY=off` 关闭(上面的启动命令已包含)。
- `learn` · `memory` 默认关闭。请保持关闭。
- 供应链注意:附带 RTK 二进制文件,启动时会从 huggingface.co 下载模型。

### 已知限制

| 路径 | 压缩率 |
|---|---|
| 直接调用库(`compress_user_messages=True`) | 83.7% |
| 实时代理 — 单次 read | 0% |
| 实时代理 — 重读 / supersede | 25~30% (最高 30.7%) |

- 单次读取为 0% 是设计如此。`DEFAULT_EXCLUDE_TOOLS = {Read,Bash,Grep,Glob,Edit,Write}` 与 `protect_recent`(默认 4)保护标准工具结果和最近的消息。
- 可逆压缩在上下文内是 lossy 的。在调试工作中,请另外确认 `headroom_retrieve` 能正确还原。
- 数值可能因环境 · 版本(v0.33.0)而不同。

### 故障排查

- `400 messages.N: user messages must have non-empty content` — 压缩返回了空字符串。`patches/apply.sh` 中的空值保护可防止此问题。临时办法是从启动命令中去掉 `--compress-user-messages`。
- 大请求出现 500 · `compression_first_stage` RuntimeError — 多个线程共享 tree-sitter 解析器引发的 panic。`patches/apply.sh` 可修复。日志中出现 `pyo3_runtime.PanicException: _native::Parser is unsendable` 即为此情况。
- 所有会话都报 `API Error: Connection refused` — 代理(8790)已停止。在不经过代理的 shell 中重启它,然后在卡住的会话中重新发送同样的输入。

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.headroom.proxy.plist 2>/dev/null
launchctl enable    gui/$(id -u)/com.headroom.proxy
launchctl kickstart -k gui/$(id -u)/com.headroom.proxy
curl -sf -m1 http://localhost:8790/health
```

- 预防:不要在 shell 中全局 export `ANTHROPIC_BASE_URL`。代理一旦停止,所有会话会同时停住。请通过包装脚本启动。

## 环境要求

- Python 3.12(`python3.12 -m venv`) · `headroom-ai==0.33.0`
- zsh(`claude-hr.sh`) · bash · python3 · curl
- 常驻服务和恢复命令以 macOS LaunchAgent(`launchctl`)为前提。
- 本包不包含 cliproxy(:8317)。要使用 headroom + cliproxy 路径,需要另行启动。
- API 密钥 / 账号:直接沿用所用智能体现有的认证。

## 链接

- [SKILL.md](SKILL.md) — `/headroom` 开关技能
- [patches/README.md](patches/README.md) — 按版本整理的运维补丁及原因
- [SSOT.md](SSOT.md) — 上下文成本整理
- [NOTES.md](NOTES.md) — 补丁说明
- [AI Feature Pack 目录](../../README.zh-CN.md)
