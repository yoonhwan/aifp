<div align="center">

# baton

**把 worktree、工作记忆和 archive 放在同一处,无论哪个智能体开始的工作,下一个智能体都能直接接手**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- Claude Code、Codex、Gemini、OpenCode、Hermes 都把结果写到同一处 `.baton/handoff/`(`PLAN.md` · `JOURNAL.md` · `CURRENT.md` · `NEXT.md`)。下一个 session 无论用哪个智能体,读取这里即可继续。
- 创建和清理 worktree。创建时分配端口、建立符号链接、初始化记忆;完成时存入 archive。
- archive 由 git 跟踪。push 之后,其他机器也能搜索过去的决定;旧的 archive 按 30 天清理。
- 设置 `BATON_TMUX_ENABLE=true` 后,每个 worktree 有自己的 tmux 会话。合上笔记本会话仍在,其他智能体或手机 SSH 可以 attach 后继续。
- 在 main / master 根目录拒绝 plan、save、resume、finish。phase 只存在于 worktree 中。
- 不做工作本身(plan 访谈、编码、评审、测试)。这些交给外部 harness(superpowers、OMX、OMC 等),baton 只收集结果。

## 快速开始

```bash
git clone https://github.com/yoonhwan/aifp
bash aifp/feature-pack/baton/install.sh   # 交互式安装
export BATON_TMUX_ENABLE=true             # 可选 — 每个 worktree 一个 tmux 会话

# 在智能体中 — main 根目录
/baton:wt-create my-task
cd .worktrees/my-task

# 在 worktree 中
/baton:plan my-task     # 可选 — 仅限大任务
# ... 用外部 harness 工作 ...
/baton:save             # 暂停时保存 handoff
/baton:finish           # phase 完成
/baton:wt-clean         # 清理 + 存入 archive
```

下一个 session 中,任何智能体进入该 worktree 后调用 `/baton:resume`,或直接说 `go` / `continue`,就会读取 `NEXT.md` 并继续。

## 安装

### 交给智能体

对智能体说:"读取 `feature-pack/baton/INSTALL.md` 并安装。" 安装时间约3分钟。

### 手动安装

```bash
bash feature-pack/baton/install.sh        # 交互式安装
export PATH="$HOME/.baton/current/bin:$PATH"   # 加入 ~/.zshrc 或 ~/.bashrc
~/.baton/current/bin/baton doctor         # 验证
bash feature-pack/baton/uninstall.sh      # 卸载
```

`install.sh` 做的事:

1. 查找已安装的智能体(Claude Code · Gemini CLI · OpenCode · Hermes)。
2. 把 core 复制到 `~/.baton/versions/<version>/`,并建立 `~/.baton/current` 链接(多个版本可以共存)。
3. 为每个智能体注册。

| 智能体 | 注册内容 |
|---|---|
| Claude Code | `~/.claude/commands/baton/` 命令 · `~/.claude/skills/baton/SKILL.md` 链接 · `~/.claude/settings.json` 中的 hook |
| Gemini CLI | `~/.gemini/commands/baton/` TOML · `~/.gemini/settings.json` 中的 hook |
| OpenCode | `~/.config/opencode/commands/baton/` · plugins |
| Hermes | `~/.hermes/plugins/baton.py` |
| Codex · OpenClaw | 输出手动注册步骤 |

4. 询问把哪个 baton 任务挂到哪个 hook(可自动选择推荐组合)。

合并前会把 `settings.json` 备份为 `settings.json.baton-backup`。卸载时会保留项目中的 `.baton/`(那是用户数据),需要手动删除。

## 用法

### 命令

| 命令 | 作用 |
|---|---|
| `/baton:wt-create <name>` | worktree + 端口 + 符号链接 + 记忆初始化 |
| `/baton:plan <id>` | phase 计划(`PLAN.md` · `phase.json`)— 仅限 worktree 中 |
| `/baton:save` | 立即保存 handoff(`CURRENT.md` 设为 paused,更新 `NEXT.md`) |
| `/baton:resume` | 输出 `NEXT.md` 并继续 |
| `/baton:finish` | phase 完成 + 建议 wt-clean |
| `/baton:wt-clean [path] [--merged]` | 清理 worktree + 存入 archive |
| `/baton:status` | phase + 活动的 worktree(含 tmux 会话) |
| `/baton:hotfix-mode [finish]` | 直接在 main 上 hotfix(lite mode · 关闭记忆) |
| `/baton:digest <topic>` | 把多个 session 的上下文压缩成一个文件 |
| `/baton:migrate [--dry-run] [path]` | 把已有 worktree 迁移到 sidecar 结构 |
| `/baton:help` | 用 ASCII 图输出流程 |
| `/baton:install` · `/baton:doctor` · `/baton:upgrade` | 安装 · 诊断 · 安装新版本 |
| `/baton:archive list` | 最近30天的 archive |
| `/baton:archive search <query> [--global]` | 搜索元数据 + 内容 |
| `/baton:archive show <id>` | 详情 |
| `/baton:archive extract <id>` · `close <id>` | 解压到临时文件夹 · 清理该文件夹 |
| `/baton:archive prune [--dry-run] [--days N]` | 清理过期的 archive |

### main 分支保护

在 main / master 根目录只能用 `wt-create`、`archive list/search`、`status`、`hotfix-mode`。`plan`、`save`、`resume`、`finish` 会被拒绝。main 保持干净,phase 只存在于 worktree 中。

### tmux 与手机 attach

设置 `BATON_TMUX_ENABLE=true` 后,`wt-create` 会创建 tmux 会话并显示 `tmux attach -t <会话>` 命令。装有 Tailscale 时,还会用 `tailscale ip -4` 和 `$USER` 拼出一行 SSH 命令,粘贴到 Termius、Blink 等手机应用即可。会话中的智能体由 `BATON_AGENT` 决定;未设置时,`CODEX_*` / `OMX_SESSION_ID` 视为 Codex,`CLAUDE_*` 视为 Claude。macOS 准备(只需一次):

```bash
sudo tailscale set --ssh             # 开启 Tailscale SSH
sudo systemsetup -setremotelogin on  # 开启 SSH
sudo pmset -c sleep 0                # 接电源时不休眠
```

### Claude Code hook

| hook | baton 的处理 |
|---|---|
| SessionStart | paused 提醒 + 环境检查 + 清理 archive |
| UserPromptSubmit | 立即把用户输入追加到 `JOURNAL.md` |
| PostToolUse | 把外部 harness 的使用记录到 `JOURNAL.md` |
| PreCompact | 提示做备份 dump |
| SessionEnd | 提示做备份 dump |

### 外部 harness

`/baton:plan` 会列出可用的 harness 候选。baton 加入指令,让计划类(`/superpowers:writing-plans`、`$plan`、`/oh-my-claudecode:plan` 等)的结果写入 `PLAN.md`,执行类(`/superpowers:executing-plans`、`$autopilot`、`/oh-my-claudecode:autopilot` 等)的结果写入 `JOURNAL.md`。没有目录文件,按名称匹配。推荐项可用 `config.json` 中的 `harnesses.preferred_plan` 修改。

### 文件位置

```
~/.baton/
├── versions/<version>/      # bin · lib · templates · SPEC.md
└── current -> versions/<version>/

<project>/.baton/
├── config.json              # commit
├── version.lock             # commit
└── archive/                 # commit (在机器间 sync)

<worktree>/.baton/
├── config.json              # 继承项目设置
├── phase.json               # commit
├── handoff/                 # gitignore — PLAN · JOURNAL · CURRENT · NEXT
└── session.lock
```

### 流程案例

| 案例 | 情形 |
|---|---|
| [plan-first](flows/plan-first.md) | 长任务 — 从 plan 开始 |
| [wt-first](flows/wt-first.md) | 轻任务 — 直接建 worktree |
| [wt-finish](flows/wt-finish.md) | 完成一个任务 |
| [branch-pivot](flows/branch-pivot.md) | 拆成多个分支后的整理 |
| [abandoned](flows/abandoned.md) | 放弃 phase |
| [hotfix-mode](flows/hotfix-mode.md) | 直接在 main 上 hotfix |
| [orphan-recovery](flows/orphan-recovery.md) | 恢复损坏的 `.baton/` |
| [handoff-rollback](flows/handoff-rollback.md) | 从 archive 恢复损坏的 `handoff/` |

## 环境要求

- 操作系统: macOS · Linux
- 必需: `bash` 4+ · `git` 2.30+ · `jq` 1.6+ · `tar`
- 可选: `ripgrep` · `gh` · tmux(`BATON_TMUX_ENABLE`)· Tailscale(手机 attach)
- API 密钥 / 账号: 无

## 链接

- [INSTALL.md](INSTALL.md) — 面向智能体的安装说明
- [core/SPEC.md](core/SPEC.md) — 与其他智能体对齐的4条规则(handoff 4文件格式 · `phase.json` schema · worktree 位置与 main 保护 · 端口分配)
- [flows/_index.md](flows/_index.md) — 8个流程案例
- [docs/MULTI_AGENT_SCENARIOS.md](docs/MULTI_AGENT_SCENARIOS.md) — 多个智能体同时工作
- 适配器: [Codex](adapters/codex/INSTRUCTIONS.md) · [Gemini](adapters/gemini/INSTRUCTIONS.md) · [OpenCode](adapters/opencode/INSTRUCTIONS.md) · [Hermes](adapters/hermes/INSTALL.md)
- [cairn](../cairn/README.zh-CN.md) — 搭配使用的包: 日程与返回点台账
- [AI Feature Pack 目录](../../README.zh-CN.md)
- 许可证: MIT
