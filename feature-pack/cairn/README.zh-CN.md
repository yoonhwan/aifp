<div align="center">

# cairn

**把日程和多智能体工作的返回点记在一本台账(`.cairn/plan.yaml`)里的 CLI**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 记录项目 / milestone(start · end)/ 任务(start · due)的日程,并显示 overdue 和完整甘特图(Mermaid)。
- 把工作分出去时(fan-out)记录谱系: `spawned_from` · `return_to` · `merge_back_to` · `fanout_depth`。即使清理了 session 或删除了 worktree,返回点仍然保留。
- 返回时(fan-in),`cairn return` 重新锚定该节点,并衔接到 baton resume。
- 对 baton(记忆)、tmuxc(执行)和 git 只读。cairn 自己写入的只有计划和恢复元数据。
- 所有写入都串行进行: lock + atomic write + validate + git commit。工作区有未提交改动时拒绝写入。
- 全局安装一次后,在任何项目文件夹中运行,都会操作该项目的 `.cairn/` 台账。

## 快速开始

```bash
git clone https://github.com/yoonhwan/aifp
bash aifp/feature-pack/cairn/install.sh   # 全局安装到 ~/.cairn + 注册 Claude Code 命令和技能
cairn self-test                           # 验证

cd my-app
cairn new-project demo                    # 创建 .cairn/plan.yaml
cairn status
```

## 安装

### 交给智能体

对 Claude Code 说:"读取 `feature-pack/cairn/INSTALL.md`,运行 `bash feature-pack/cairn/install.sh`,然后用 self-test 和 hook smoke 测试验证。" 在 Codex 中运行 `bash feature-pack/cairn/install.sh`。安装时间约2分钟。

### 手动安装

```bash
bash feature-pack/cairn/install.sh
export PATH="$HOME/.cairn/current/bin:$PATH"   # 如果不开新 shell
cairn self-test                                # self-test OK
bash feature-pack/cairn/uninstall.sh           # 卸载 — 只删全局文件,保留项目中的 .cairn/
```

`install.sh` 做的事: 把 core 复制到 `~/.cairn/versions/<version>` · 建立 `current` 链接 · 创建 `~/.cairn/venv`(ruamel.yaml)· 在 `~/.zshrc` 中加入 PATH · 安装 `~/.cairn/current/hooks/*` · `~/.claude/commands/cairn` · 链接 `~/.claude/skills/cairn/SKILL.md` · 运行 `cairn self-test`。重复运行是安全的(会新增版本文件夹并切换 `current`)。

在每个项目中挂上 git hook:

```bash
mkdir -p .git/hooks
ln -sfn "$HOME/.cairn/current/hooks/post-merge" .git/hooks/post-merge
ln -sfn "$HOME/.cairn/current/hooks/post-checkout" .git/hooks/post-checkout
```

## 用法

### 日程命令

| 命令 | 作用 |
|---|---|
| `cairn init` | 在项目中初始化 `.cairn` 台账 |
| `cairn new-project <name>` · `add-milestone <p> <name>` · `add-task <p> <ms> <name> [--days N]` | 创建 |
| `cairn status` · `show <p>` · `overdue [--today]` | 查看 |
| `cairn render` | 完整甘特图(Mermaid)→ `.cairn/views/plan.md` |
| `cairn set-status` · `set-date` · `set-priority` | 修改 |

### 恢复命令(fan-out / fan-in)

| 命令 | 作用 |
|---|---|
| `cairn spawn <name> --from <parent>` | 分出(fan-out)— 自动设置 `spawned_from` · `return_to` · `fanout_depth` |
| `cairn complete <task> [--force]` | 完成 + 显示 `return_to`(缺失时阻止) |
| `cairn return --to <node>` | 返回(fan-in)— 重新锚定节点并衔接到 baton resume |
| `cairn map [--focus] [--render]` | 用 Mermaid 生成恢复图(recovery-map)→ termaid |
| `cairn link <node> --execution-ref / --session-ref / --merge-back-to` | 记录元数据(由 hook 调用) |
| `cairn reconcile` | 对照活动的 worktree 与节点,找出 orphan |
| `cairn validate` | 检查台账完整性 — 断开的恢复连接为 0 |

task id 在整本台账中唯一(因为恢复元数据会全局引用它)。

### 自动进度 hook

`~/.cairn/current/hooks/cairn-auto-progress` 收到验证通过(`CAIRN_VERIFICATION_STATUS=pass`)后,默认只在 `.cairn/auto-progress/candidates/` 中留下完成候选。只有同时给出 `CAIRN_AUTO_PROGRESS=apply` 和 `CAIRN_TASK_ID` 时,才会运行 `cairn complete <task>`。

```bash
# 只留下候选
CAIRN_TASK_ID=t2 CAIRN_VERIFICATION_STATUS=pass \
  "$HOME/.cairn/current/hooks/cairn-auto-progress"

# 写入台账
CAIRN_AUTO_PROGRESS=apply CAIRN_TASK_ID=t2 CAIRN_VERIFICATION_STATUS=pass \
  "$HOME/.cairn/current/hooks/cairn-auto-progress"
```

在 Claude Code 中从 PostToolUse hook 调用,在 Codex 中从 shell hook 或 tmuxc 会话的结束 / 验证步骤调用同一命令。

## 环境要求

- 操作系统: macOS · Linux
- 必需: `python3` 3.9+ · `git` 2.30+ · `ruamel.yaml`(安装时自动装进 `~/.cairn/venv`)
- 可选: termaid(`cairn map --render`)
- API 密钥 / 账号: 无
- 故障排除: `cairn: command not found` → 打开新 shell 或 export 上面的 PATH · `ModuleNotFoundError: ruamel` → 重新运行 `bash install.sh`

## 链接

- [INSTALL.md](INSTALL.md) — 面向智能体的安装说明
- [docs/cairn-design.md](docs/cairn-design.md) — 设计
- [docs/agent-lifecycle-hook-design.md](docs/agent-lifecycle-hook-design.md) — 智能体生命周期 hook 设计
- [baton](../baton/README.zh-CN.md) — 搭配使用的包: worktree、工作记忆、archive
- [AI Feature Pack 目录](../../README.zh-CN.md)
- 许可证: MIT
