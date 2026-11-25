<div align="center">

# agent-browser

**面向 AI 智能体的浏览器自动化 CLI — 网页抓取 · 截图 · 表单填写 · 视频录制 · 调试 · 生成样式化卡片。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 提取网页内容,包括动态的 SPA 和 React 页面(抓取)。
- 对整页或局部截图,并生成 2× 视网膜(retina)卡片图片。
- 自动填写登录、注册等表单,并保存和恢复登录会话(cookie)。
- 以 WebM 录制视频,并转换为 GIF。
- 查看控制台日志和错误,并模拟(mock)网络响应。
- 基于 Rust 的 CDP 守护进程直接连接 Chrome,需要浏览器扩展时也能使用。

## 快速开始

```bash
npm install -g agent-browser
agent-browser install    # 下载 Chromium (仅首次,约 150MB)
agent-browser --native open "https://example.com" && agent-browser --native snapshot -i && agent-browser --native close
```

## 安装

这个包会安装三样东西: agent-browser CLI(0.16.3 或更高版本)、智能体处理浏览器任务时会自动使用的技能,以及一段 TOOLS.md 内容(包含各环境的设置、速度对比和技巧)。

### 让智能体安装

对智能体说:

```text
读取 feature-pack/agent-browser/INSTALL.md 并安装
```

### 手动安装

```bash
# 在 feature-pack/agent-browser/ 目录内执行
npm install -g agent-browser
agent-browser install                  # 下载 Chromium (仅首次,约 150MB)
agent-browser --version                # 必须是 0.16.3 或更高版本
pip3 install Pillow                    # 用于截图卡片
cp -r skill/ ~/.openclaw/workspace/skills/agent-browser/   # Claude Code 用 ~/.claude/skills/agent-browser/
cat config/tools-section.md >> ~/.openclaw/workspace/TOOLS.md
```

- 技能目录(`~/.openclaw/workspace/skills`)和 workspace(`~/.openclaw/workspace`)是 OpenClaw 的默认路径。不同的话请换成你自己的路径。
- `config/tools-section.md` 会向 TOOLS.md 追加: agent-browser 的使用规则(优先 native,不是搜索工具)、速度对比表、视频捕获命令和截图卡片流程。

### 验证安装

```bash
agent-browser --version
agent-browser --native open "https://example.com" && agent-browser --native get title && agent-browser --native screenshot /tmp/ab-verify.png && agent-browser --native close
agent-browser --native open "https://example.com" && agent-browser --native snapshot -i && agent-browser --native close
python3 -c "from PIL import Image; print('Pillow OK')"
```

全部通过就说明安装完成。

### 故障排查

| 现象 | 解决 |
|------|------|
| `agent-browser: command not found` | 重新运行 `npm install -g agent-browser` |
| `Chromium not found` | 运行 `agent-browser install` |
| `--native` 模式失败 | 去掉 `--native`,退回 standard 模式 |
| Pillow import 报错 | 重新运行 `pip3 install Pillow` |
| 截图被截断 | 确认 HTML 高度不超过 620px,超过就拆分卡片 |

## 用法

### 选择模式

| 场景 | 模式 | 原因 |
|------|------|------|
| 一般浏览和抓取 | `--native` | 更快(每页约 150ms),不需要 Node.js |
| 截图和捕获 | `--native` | 延迟更低 |
| 需要 Chrome 扩展 | `--native connect <port>` | 只能用真实的 Chrome |
| 复杂 JS 的 SPA 渲染有问题 | standard (不加标志) | Playwright 更稳定 |
| CI/CD 流水线 | standard headless | 久经验证的稳定性 |

- 默认总是先试 `--native`,出问题再退回 standard。
- 它不是网页搜索工具。搜索或只是读取某个 URL 的内容,请用 web search / fetch 工具。

### 基本流程

```bash
SESSION="task-$(date +%s)"
trap "agent-browser close --session $SESSION 2>/dev/null" EXIT ERR

agent-browser --native --session "$SESSION" --headed open "https://example.com"
agent-browser --native --session "$SESSION" wait --load networkidle
agent-browser --native --session "$SESSION" snapshot -i          # 把元素列为 @ref
agent-browser --native --session "$SESSION" click @e3
agent-browser --native --session "$SESSION" fill @e5 "you@example.com"
agent-browser --native --session "$SESSION" get text ".result"
agent-browser --native --session "$SESSION" screenshot ./result.png
agent-browser --native --session "$SESSION" close
```

- 任何操作之前,先用 `snapshot -i` 查看元素。`@ref` 的值每个会话都会变,不要在别的会话里复用。
- 始终使用 `--session <name>`,并用 `trap` 做清理。
- 本地用 `--headed`(能看到操作过程),CI/CD 里省略(默认是 headless)。
- 定位元素的优先顺序: ① `snapshot -i` 给出的 `@ref` ② CSS 选择器 ③ `find` 命令(`find role button click` · `find text "Submit" click` · `find testid "btn" click`)。

### 常用操作

```bash
# 等待方式
agent-browser --native --session "$SESSION" wait "#element"            # 等到元素出现
agent-browser --native --session "$SESSION" wait 2000                  # 固定延迟 (ms)
agent-browser --native --session "$SESSION" wait --text "Success"      # 等到文本出现
agent-browser --native --session "$SESSION" wait --url "**/dashboard"  # 等到 URL 匹配
agent-browser --native --session "$SESSION" wait --load networkidle    # 等到所有请求结束

# 保存 / 恢复 cookie
agent-browser --native --session "$SESSION" cookies get > cookies.json
agent-browser --native --session "$SESSION" cookies set "$(cat cookies.json)"

# 网络模拟
agent-browser --native --session "$SESSION" network route "**/analytics/*" --abort
agent-browser --native --session "$SESSION" network route "**/api/user" --body '{"id":1,"name":"Test"}'
agent-browser --native --session "$SESSION" network unroute

# 录制视频,再转换为 GIF
agent-browser --native --session "$SESSION" record start "./demo.webm"
agent-browser --native --session "$SESSION" record stop
ffmpeg -i demo.webm -vf "fps=10,scale=480:-1:flags=lanczos" -c:v gif demo.gif

# 调试
agent-browser --native --session "$SESSION" console                    # 查看日志
agent-browser --native --session "$SESSION" errors                     # 查看错误
agent-browser --native --session "$SESSION" eval "document.title"      # 运行 JS
```

- 绕过登录弹窗时,不要对 DOM 元素调用 `remove()`,而是用 CSS 把它隐藏(`remove()` 会破坏页面内容)。

### 连接正在运行的 Chrome

```bash
agent-browser --native connect 9222 --session "$SESSION"                                     # 按端口
agent-browser --native connect "ws://127.0.0.1:9222/devtools/browser/UUID" --session "$SESSION"  # 按 WebSocket URL
agent-browser --auto-connect --native snapshot                                                # 自动发现运行中的 Chrome
```

- 需要 Chrome 扩展、需要 macOS 音频(BlackHole)回环,或要连接远程 / 调试用的 Chrome 时,使用 `--native connect`。

### 截图卡片

用 HTML 生成适合手机查看、便于分享(Slack · Discord 等)的样式化卡片。

```bash
agent-browser --native --session cap open "file:///tmp/card.html"   # 宽 375px、高不超过 620px 的 HTML
agent-browser --native --session cap screenshot "/tmp/raw.png"
agent-browser --native --session cap close
```

- agent-browser 的视口固定为 1280×720px,所以超过约 620px 的内容会被截断。内容太长就拆成多张卡片(一张卡片 = 一个主题)。
- 卡片宽度是 375px,最终输出是 2× 视网膜(宽 830px)。用 Pillow 裁剪上面的截图并放大 2 倍(完整脚本见 [skill/SKILL.md](skill/SKILL.md))。
- 字号: 短内容 标题 15px · 正文 12px · 代码 11px · 内边距 20px / 中等 14 · 11 · 10 · 16px / 长表格(20 行以上) 13 · 10.5 · 9.5 · 14px。
- 主题是深色(背景 `#1a1a2e`,卡片 `#16213e`,表头 `#0f3460`,边框 `#1a4080`)。务必确认最后一行(footer)可见。

### 错误恢复

| 错误 | 解决 |
|------|------|
| `No session found` | 先运行 `open` |
| `Element not found` | 重新运行 `snapshot -i`,检查 ref |
| `Timeout` | 调大 `--timeout`,检查 `wait` 条件 |
| 僵尸会话 | `agent-browser session list` → `close --session <name>` |
| `--native` 失败 | 去掉 `--native` 标志,使用 standard 模式 |

完整的命令列表见 `agent-browser --help` 和 `agent-browser <command> --help`。

## 环境要求

- macOS (arm64 / x86_64)
- Node.js 18 或更高版本,以及 npm
- Python 3 + Pillow (用于截图卡片)
- ffmpeg (仅在把 WebM 转成 GIF 时需要)
- 不需要账号或 API key。

## 链接

- [INSTALL.md](INSTALL.md) — 面向智能体的安装说明
- [skill/SKILL.md](skill/SKILL.md) — 技能定义
- [AI Feature Pack 目录](../../README.zh-CN.md)
