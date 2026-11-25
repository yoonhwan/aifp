<div align="center">

# AI Feature Pack

**为 AI 编程智能体环境按需挑选、逐个安装的功能包合集**
Claude Code · Codex · Pi · OpenCode · OpenClaw

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

[![Packs](https://img.shields.io/badge/packs-26-0b6e5f)](#-功能包目录)
[![Guide](https://img.shields.io/badge/guide-GitHub%20Pages-0b6e5f)](https://yoonhwan.github.io/aifp/)
[![Platform](https://img.shields.io/badge/platform-macOS-555)](#-说明)

</div>

---

## 这是什么?

- 面向 AI 编程智能体的**功能包**合集。一个包 = [`feature-pack/`](feature-pack/) 下的一个文件夹。各包相互独立,只装需要的即可。
- 每个包都带有**写给智能体看的** `INSTALL.md`。把它交给你的智能体,它会检查前置条件、安装 CLI、注册技能并验证结果。
- 第一次来?先看图解指南:**[用手机操作你的 AI 智能体](https://yoonhwan.github.io/aifp/)**(英文 · [韩文](https://yoonhwan.github.io/aifp/ko.html))。

## 🚀 快速开始

**方式 A — 手机远程组合 (`tmuxc` + `tmm`)**

```bash
git clone https://github.com/yoonhwan/aifp.git && cd aifp \
  && bash feature-pack/tmuxc/install.sh \
  && bash feature-pack/tmm/install.sh
```

需要:macOS、bash 4 及以上、git、tmux、fzf(`tmm` 使用)。

**方式 B — 让智能体安装某个包**

```bash
git clone https://github.com/yoonhwan/aifp.git
# 然后对你的智能体说,例如:
#   "阅读 feature-pack/agent-browser/INSTALL.md 并安装"
```

智能体读取 `INSTALL.md` 后会:

1. 检查前置条件
2. 安装 CLI
3. 配置认证与设置(需要时会询问你)
4. 注册技能
5. 添加 `TOOLS.md` / `AGENTS.md` 配置
6. 验证安装

## 📦 功能包目录

| # | 包 | 功能 | 安装时间 | API 密钥 | 认证 |
|---|----|------|----------|----------|------|
| 1 | [agent-browser](feature-pack/agent-browser/) | 网页自动化 — 抓取、截图、表单填写、录制 | 约3分钟 | — | — |
| 2 | [imsg](feature-pack/imsg/) | iMessage/短信 — 查看对话、发送消息、实时监听 | 约3分钟 | — | — |
| 3 | [notebooklm](feature-pack/notebooklm/) | Google NotebookLM — 基于来源的问答、调研、音频生成 | 约5分钟 | — | Google |
| 4 | [obsidian-cli](feature-pack/obsidian-cli/) | Obsidian 仓库 CLI — 查看、创建、搜索、移动笔记 | 约3分钟 | — | — |
| 5 | [tts-say](feature-pack/tts-say/) | 统一 TTS — macOS `say` + ElevenLabs 语音合成 | 约3分钟 | ElevenLabs | — |
| 6 | [yt-transcribe](feature-pack/yt-transcribe/) | YouTube → 语音转文字 → 摘要的自动流水线 | 约10分钟 | — | — |
| 7 | [termaid](feature-pack/termaid/) | 在终端渲染 Mermaid 图 — 设计可视化时自动触发 | 约2分钟 | — | — |
| 8 | [baton](feature-pack/baton/) | 多智能体 handoff / worktree / archive 规范 — 在 Claude Code、Codex、Gemini 之间交接工作 | 约2分钟 | — | — |
| 9 | [cairn](feature-pack/cairn/) | 日程 + 多智能体恢复台账 — milestone / task / session lineage,与 baton、tmuxc 联动 | 约2分钟 | — | — |
| 10 | [tmuxc](feature-pack/tmuxc/) | 基于 tmux 的 Claude Code、Codex、OMX 会话 launcher / control — 含 verified send/capture 通信规范 | 约1分钟 | — | — |
| 11 | [auto](feature-pack/auto/) | AutoResearch 自主实验循环 — 基线 → 目标 → 自动优化 | 约1分钟 | — | — |
| 12 | [nanoclaw](feature-pack/nanoclaw/) | AI 多智能体平台(OpenClaw 的替代)— Claude SDK Brain、Docker 隔离、多团队 | 约15分钟 | — | Slack |
| 13 | [agent-cli](feature-pack/agent-cli/) | **AI 编程智能体 CLI 工具集** — 安装与对比,以及使用角色设定的非交互式委派 | 约3分钟 | — | — |
| 14 | [headroom](feature-pack/headroom/) | 面向 Claude Code、Codex 等的上下文压缩代理 + `/headroom` 开关 | 约5分钟 | — | — |
| 15 | [fable-team](feature-pack/fable-team/ft2/) | **团队编排框架 (ft 2.0)** — 席位、便条、派工的公共核心,契约定义,Codex / Pi / Slack 适配器,诊断工具。各文件夹职责见 `ft2/README.md` | — | — | — |
| 16 | [tmm](feature-pack/tmm/) | **移动端(SSH) tmux 席位 TUI** — 在手机上用光标从几十个智能体会话中挑选:预览、最近响应优先、等待中的席位优先、发送消息 (fzf) | 约1分钟 | — | — |
| 17 | [ctx-burn](feature-pack/ctx-burn/) | **本地上下文浪费审计工具** — 自动识别 7 种运行时(claude, codex, pi, opencode, hermes, openclaw, commandcode) | 约1分钟 | — | — |
| 18 | [ctx-plan](feature-pack/ctx-plan/) | **容量测算工具** — 只读取 ctx-burn 的 `ctx.v1` 输出,按账号组合估算席位数与峰值会话数 | 约1分钟 | — | — |

**目录树中还有**(每个文件夹自带文档):
[agent-surface-audit](feature-pack/agent-surface-audit/) — 以 dry-run 方式盘点智能体的技能与钩子面 ·
[agent-surface-sync](feature-pack/agent-surface-sync/) — 安装或更新来自 `feature-pack/*` 与 `hooks/` 的共享智能体面 ·
[code-intel](feature-pack/code-intel/) — 以 `ci` 为单一入口的代码智能 ·
[daily-trend-viewer](feature-pack/daily-trend-viewer/) — 每天查看热门视频与 AI 视频资讯的本地站点 ·
[mcp-manager](feature-pack/mcp-manager/) — 检查并精简 MCP 服务器面 ·
[memory-system](feature-pack/memory-system/) — OpenClaw 智能体的记忆结构 ·
[rag](feature-pack/rag/) · [rag-consumer](feature-pack/rag-consumer/) — `airag` RAG 包及其消费端(从 [`rag/docs/README.md`](feature-pack/rag/docs/README.md) 开始)。

## 📋 推荐安装顺序

各包之间没有依赖。按实用程度排序:

1. **obsidian-cli** — 第二大脑的基础(其他包的笔记存放处)
2. **agent-browser** — 网页自动化(最通用)
3. **yt-transcribe** — YouTube 转写(与 obsidian-cli 搭配很好)
4. **notebooklm** — 知识问答(基于来源的回答)
5. **tts-say** — 语音输出
6. **imsg** — iMessage 集成(仅 macOS)

同时运行多个智能体时,建议按以下顺序:

1. **baton** — worktree / handoff / archive 的基准
2. **cairn** — 日程与 session lineage 台账
3. **tmuxc** — 在 tmux 会话中运行 Claude Code / Codex / OMX,并用 verified-send 通信
4. **tmm** — 在手机(Termius)上用光标挑选并接入这些席位的 TUI

| 工具 | 负责 |
|------|------|
| baton | 用于开始、保存、恢复工作的 `.baton/handoff/`,以及 worktree / archive |
| cairn | 基于 `.cairn/plan.yaml` 的 milestone / task / session lineage |
| tmuxc | live tmux 智能体会话的创建、capture、send、kill |
| tmm | 移动端 SSH 下的席位列表、预览、attach、消息(使用 tmuxc 的席位) |

## 🔧 其他安装方式

**手动** — 阅读包文件夹里的 `README.md` 并按顺序操作:

```
feature-pack/{name}/
├── README.md        ← 给人看的概览(从这里开始)
├── INSTALL.md       ← 给智能体的安装提示
├── cli/install.md   ← CLI 安装命令
├── skill/SKILL.md   ← 技能定义
├── config/          ← 要添加到 TOOLS.md / AGENTS.md 的内容
└── test/verify.md   ← 安装验证
```

并非每个包都有全部文件。有五个包(`ctx-plan`、`fable-team`、`headroom`、`rag`、`rag-consumer`)没有 `INSTALL.md`,请从它们的 README 或 docs 开始。

**全部安装** — 对你的智能体说:"按顺序安装 aifp 仓库里的所有功能包。" 大约需要 25 分钟。

## 🔒 关于本仓库

- 这是从一个私有工作仓库**导出的副本**。内部运营记录已移除,个人与组织标识已替换为占位符,因此部分依赖私有数据的测试在这里会被跳过或无法运行。
- 每次导出都会扫描 58 种模式(密钥、令牌、地址、ID),只有在已审核的允许清单之外没有任何残留时才会导出。仍然存在的密钥形态字符串是测试固定值或文档占位符。
- 安装功能包时,请不要把自己的密钥或令牌写进仓库文件夹内的文件。

## 📌 说明

- **操作系统**:目前仅支持 macOS(Linux / Windows 以后支持)。
- **OpenClaw**:[openclaw.ai](https://openclaw.ai) · [GitHub](https://github.com/openclaw/openclaw)
- **提问**:提交 Issue,或加入 [Discord](https://discord.com/invite/clawd)。

## 许可证

[MIT](LICENSE)
