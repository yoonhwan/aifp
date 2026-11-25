<div align="center">

# tmuxc

**用一条命令,在 tmux 里打开并控制 Claude Code · Codex · OMX · OpenCode · Command Code · Pi 的智能体会话。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 用一行 `tmuxc open`,在项目文件夹或 git worktree 里打开 Claude Code、Codex CLI、OMX、OpenCode、Command Code、Pi 的会话。
- 打开会话时可以指定角色(`worker` · `orchestrator` · `designer`)。
- 向另一个会话发送消息并读取它的屏幕(`tmuxc send` · `tmuxc msg` · `tmuxc ask`)。发送和读取统一采用 verified send / capture 流程。
- 关机前把已打开的会话保存为快照,重启后用 `tmuxc restore` 恢复。
- 不影响原来的对话,分出一个新对话(`tmuxc fork` · 使用各引擎的原生 fork)。
- 用同一个 CLI 查看、结束和清理会话(`tmuxc list` · `kill` · `clean`)。

## 快速开始

```bash
bash feature-pack/tmuxc/install.sh
tmuxc --help
tmuxc open "$PWD" --name TMUXC_SMOKE --agent codex --role worker --dry-run
```

## 安装

### 让智能体安装

对智能体说:

```text
读取 feature-pack/tmuxc/INSTALL.md 并安装
```

### 手动安装

```bash
bash feature-pack/tmuxc/install.sh
```

`install.sh` 的操作:

- 检查 `bash` · `git` · `tmux` 是否存在。
- 把 core 和 Claude Code skill 复制到 `~/.tmuxc/versions/<version>/`,并更新 `~/.tmuxc/current` 符号链接。
- 把 CLI 链接为 `~/.local/bin/tmuxc`。如果 `~/.local/bin` 不在 PATH 里,会把它写入 `~/.zshrc` 或 `~/.bashrc`。
- 如果装有 Claude Code,把 `~/.claude/skills/tmuxc` 链接到已安装的副本。

### 验证安装

```bash
tmuxc --help
tmuxc list
test -e "$HOME/.claude/skills/tmuxc/SKILL.md"
test -e "$HOME/.claude/skills/tmuxc/COMM-GUIDE.md"
```

### 卸载

```bash
bash feature-pack/tmuxc/uninstall.sh
```

卸载脚本只删除 `~/.tmuxc`,以及指向已安装副本的 `~/.local/bin/tmuxc` 和 `~/.claude/skills/tmuxc` 链接。不会删除你的项目文件和 tmux 会话。

## 用法

### 命令

```bash
tmuxc open <path> --name NAME --agent claude|codex|omx|opencode|cmd|pi --role worker|orchestrator|designer [--pi-skill PATH]...
tmuxc wt <worktree-path> --name NAME --prompt "读取 NEXT.md 后开始"
tmuxc list
tmuxc ask <name> [lines]              # 读取会话屏幕的最后几行 (capture-pane)
tmuxc send <name> "message"           # 向会话发送消息
tmuxc msg <name> "message"
tmuxc kill <name>
tmuxc clean
tmuxc save [--keep N]                 # 关机前保存全局会话快照 (保留 [1m] · effort · session_id)
tmuxc restore [--from latest] [--go]  # 重启后恢复 (优先用快照,--scan 强制扫描日志)
tmuxc fork <path> --name NEW (--from LIVE_SESSION | --source ID --agent claude|codex|opencode|cmd|pi) [--model ID] [--ctx 1m] [--effort E] [--prompt TEXT]
```

- 对于非 Claude 的席位(pi · codex · opencode · cmd),`open` 和 `fork` 会在 tmux 会话的 env 中设置 `GIT_EDITOR=true` · `GIT_SEQUENCE_EDITOR=true` · `GIT_TERMINAL_PROMPT=0`,这样 git 不会停在编辑器或输入提示上。已经在运行的席位不受影响,只对新席位生效。

### Pi 席位

```bash
tmuxc open . --name PI_WORKER --agent pi --role worker --model <provider/model>
tmuxc open . --name PI_REVIEW --agent pi --role orchestrator --effort high
```

- tmuxc 会生成 `--session-id <uuid>`,并存入会话 env(`TMUXC_PI_SESSION_ID` · `TMUXC_PI_MODEL` · `TMUXC_PI_THINKING`)。即使进程标题隐藏了 argv,`save` 和 `restore` 也能恢复到准确的会话。
- `worker` 和 `implementer` 获得 `read,bash,edit,write,grep,find,ls` 工具;`orchestrator` · `planner` · `analysis` 只获得只读工具。
- `--effort` 对应 Pi 的 `--thinking`。
- `--like <pi-session>` 可以继承正在运行的 Pi 的 model 和 thinking。

用 `--pi-skill` 可以只给 Pi 席位加载你选的技能:

```bash
tmuxc open <path> --agent pi --pi-skill ~/.agents/skills/code-intel --pi-skill ~/.agents/skills/tmuxc --dry-run
```

- 它会关闭 Pi 的技能自动发现(`--no-skills`),只按顺序加载你给的路径。
- 路径可以是 `SKILL.md` 文件,也可以是包含 `SKILL.md` 的文件夹。路径不存在时不会创建任何东西,并以 rc≠0 拒绝。
- 只在 `--agent pi` 时接受(其他智能体会返回 rc≠0)。不加该选项时,命令与之前完全相同。
- 通过 `tmuxc fork` 或 `tmuxc restore` 重新启动的席位不使用这个选项。

### Fork

| 引擎 | argv | 备注 |
|---|---|---|
| claude | `--resume <ID> --fork-session` | 经由 headroom 包装器,继承 `[1m]` 和 effort |
| codex | `codex fork <ID>` | 传递 `-c model=` 和 `-c model_reasoning_effort=` |
| opencode | `--session <ID> --fork` | 模型通过会话 env `OPENCODE_CONFIG_CONTENT` 传递 |
| cmd | `--resume <ID> --fork-session` | `--model` 和 `--effort` |
| pi | `--fork <ID> --session-id <NEW>` | `--model` 和 `--thinking` |

- `--from <运行中的会话>`: 从运行中的进程和对话记录里读取引擎、模型和对话 id。只能在同一引擎内进行,不能跨引擎。
- `--source <ID> --agent <引擎>`: 直接指定 id。会尽力确认该引擎的存储里有这个 id。
- `omx` 没有原生 fork,所以不支持。

### 推荐流程

```bash
# 1) 在带有 baton handoff 的 worktree 里打开会话
tmuxc open /path/to/project/.worktrees/my-task --name MY_TASK_ORCH --agent codex --role orchestrator --prompt "读取 AGENTS.md、.baton/handoff/CURRENT.md、.baton/handoff/NEXT.md 后开始"

# 2) 在 cairn 里记录 task / session ref
cairn link t7 --session-ref MY_TASK_ORCH --execution-ref "tmuxc:MY_TASK_ORCH"

# 3) 用 list / ask 查看进度
tmuxc list
tmuxc ask MY_TASK_ORCH 80
```

### 配套工具

| 工具 | 作用 |
| --- | --- |
| `baton` | worktree, handoff, archive, memory |
| `cairn` | milestone / task 日程 ledger, session lineage |
| `tmuxc` | 运行中 tmux 智能体会话的启动与控制 |

## 环境要求

- 必需: `bash` · `git` · `tmux` (macOS: `brew install tmux` · Ubuntu: `sudo apt install tmux`)
- 可选: 想打开的智能体的 CLI (`claude` · `codex` · `omx` 等)
- 可选: `baton` · `cairn` (配套工具集)
- tmuxc 本身不需要账号或 API key。各智能体 CLI 的认证由该 CLI 另行要求。

## 链接

- [INSTALL.md](INSTALL.md) — 面向智能体的安装说明
- [AI Feature Pack 目录](../../README.zh-CN.md)
