<div align="center">

# imsg

**在终端里操作 macOS Messages.app 的 CLI 和 OpenClaw 技能 — 也可作为智能体 · 脚本 · cron 的 iMessage 通知通道**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- **会话列表** — 查看最近的 iMessage / SMS 会话。
- **消息历史** — 查看某个会话的历史消息,支持日期过滤和附件信息。
- **发送消息** — 发送文本和附件(图片 · 文档等)。
- **实时接收监听** — 新消息到达时以流的形式输出。
- **智能体通知通道** — 从其他智能体 · 编程工具 · cron · CI 用一行 `imsg send` 发送 iMessage 通知。
- CLI 是第三方 Homebrew 包 `steipete/tap/imsg`,本包收录它的安装指南 · OpenClaw 技能 · `TOOLS.md` 段落。

## 快速开始

```bash
brew install steipete/tap/imsg
imsg --help                                        # 打印出命令列表即成功
imsg chats --limit 3 --json                        # 会话列表 (检查 Full Disk Access)
imsg send --to "<your-phone>" --text "imsg 安装测试"   # 发给自己 (检查 Automation 权限)
```

## 安装

### 交给智能体

对智能体说 "Read feature-pack/imsg/INSTALL.md and install it" 即可。`INSTALL.md` 是写给 OpenClaw 智能体阅读并自行安装的文档,3 个占位符(`{{OPENCLAW_WORKSPACE}}` · `{{USER_PHONE}}` · `{{NOTIFY_PHONE}}`)由智能体先询问用户再填入。

### 手动安装

1. 用 `brew install steipete/tap/imsg` 安装 CLI。
2. 给终端应用(Terminal.app · iTerm2 等)授予 **Full Disk Access**:系统设置 → 隐私与安全性 → Full Disk Access。读取 `chat.db` 需要它。
3. 第一次 `imsg send` 时会弹出"允许 Terminal 控制 Messages" → 允许(**Automation** 权限)。
4. 如果使用 OpenClaw,复制技能,并把 [`config/tools-section.md`](config/tools-section.md) 中的段落加入工作区的 `TOOLS.md`。

```bash
SKILL_DIR="$HOME/.openclaw/workspace/skills/imsg"   # OpenClaw 工作区默认路径
cp -r skill/ "$SKILL_DIR"
ls "$SKILL_DIR/SKILL.md"                            # 检查技能
```

## 用法

### 命令

| 命令 | 作用 | 主要选项 |
|---|---|---|
| `imsg chats` | 会话列表 | `--limit N` · `--json` · `--db <path>`(默认 `~/Library/Messages/chat.db`) |
| `imsg history` | 某个会话的消息 | `--chat-id <ID>` · `--limit N` · `--start` / `--end <ISO8601>` · `--participants` · `--attachments` · `--json` |
| `imsg send` | 发送消息 | `--to <phone/email>` 或 `--chat-id` · `--text` · `--file <path>` · `--service imessage\|sms\|auto` · `--region` |
| `imsg watch` | 实时接收监听 | `--chat-id` · `--participants` · `--since-rowid` · `--debounce 250ms` · `--attachments` · `--json` |
| `imsg rpc` | 基于 stdin / stdout 的 JSON-RPC 模式 | 用于对接 MCP 服务器等 |

### 示例

```bash
imsg chats --limit 10 --json                                   # 查 chat-id
imsg history --chat-id 1 --start 2026-03-01T00:00:00Z --attachments --json
imsg send --to "<your-phone>" --text "报告在此" --file ~/reports/daily.pdf
imsg send --chat-id 42 --text "回复一下"
imsg watch --chat-id 1 --attachments --debounce 250ms
```

### 通知通道

任何 CLI 工具 · 脚本 · 智能体都能用一行 `imsg send` 发送通知。经常用的话可以注册成 shell 函数。

```bash
# 任务结束时通知成功 / 失败
long_running_task && imsg send --to "<your-phone>" --text "任务完成" \
                  || imsg send --to "<your-phone>" --text "任务失败"

# 加到 ~/.zshrc — 用法: notify "构建完成"
notify() {
  imsg send --to "<your-phone>" --text "$*"
}
```

### 故障排查

| 症状 | 原因 | 解决 |
|---|---|---|
| `imsg: command not found` | 未用 brew 安装 | `brew install steipete/tap/imsg` |
| `permission denied`(chats) | 没有 Full Disk Access | 系统设置 → 隐私 → Full Disk Access → 添加终端 |
| 发送失败 | 未允许 Automation | 系统设置 → 自动化 → Terminal → 勾选 Messages |
| "Messages is not running" | Messages.app 未运行 | 启动 Messages.app 后重试 |
| 对方不支持 iMessage | 需要走 SMS | 加上 `--service sms` |
| 不知道 chat-id | 未查会话 ID | 用 `imsg chats --json` 查看 |

## 环境要求

- macOS(Apple Silicon 或 Intel) + 已用 iCloud 账号登录的 Messages.app
- Homebrew
- 终端应用的 Full Disk Access · 对 Messages 的 Automation 权限
- 可选:要用技能需要 OpenClaw
- 无需 API 密钥

## 链接

- [INSTALL.md](INSTALL.md) — 给智能体的安装指南(步骤 · 验证清单 · 占位符)
- [skill/SKILL.md](skill/SKILL.md) — OpenClaw 技能(使用场景 · 命令参考)
- [config/tools-section.md](config/tools-section.md) — 要加入 `TOOLS.md` 的段落
- [AI Feature Pack 目录](../../README.zh-CN.md)
