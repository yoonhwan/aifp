<div align="center">

# code-intel

**在任何智能体环境里都用同一个命令 `ci` 完成代码搜索、符号、引用和结构模式查询的功能包**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 语义 · 关键词搜索(BM25 + 完整的 AST 代码块) — `ci search "<q>" <path>`
- 符号的定义 · 调用方 · 依赖(定义排在前面) — `ci sym <sym> --callers --scope <dir>`
- 读文件之前先看结构和 token 数 — `ci outline <file>`
- 基于 LSP 的精确引用 · 定义 · 实现(仅在需要时启动) — `ci refs "<file>#<sym>"`
- ast-grep 结构模式 — `ci ast '<pattern>' <path> -l py`
- 统计智能体是否按指令使用 `ci` 的遵守率 — `ci-audit --days 1 --by-harness`
- 无索引 · 常驻进程为 0。在 Claude Code · Codex · OpenCode · Pi · Hermes 中命令完全相同。用来替代 Serena MCP。

### 为什么做这个

在 62k 个文件 · 49GB 的 worktree 上实测的数据。

| 操作 | Serena | code-intel |
|---|---|---|
| 语义搜索 | 127.25s (空结果) | 4.6s (排序后的结果) |
| 调用方追踪 | 4.2s+ (需先激活) | 0.36s |
| 常驻内存 | 946MB → 5.1GB 泄漏 (peak 21GB) | 0MB |
| 前置步骤 | activate_project + 检查配置 | 无 |

## 快速开始

```bash
# 在仓库根目录: 二进制 + 技能链接 + ci 入口 + 诊断(重复运行结果相同)
bash feature-pack/code-intel/skill/scripts/install.sh

ci doctor                                  # 安装 · 版本 · LSP · smoke
ci search "dispatch" src --max 5           # 第一次搜索
```

## 安装

### 让智能体来装

对智能体说:"读 `feature-pack/code-intel/INSTALL.md` 并安装。" 智能体会依次完成技能链接 → 安装二进制 → 验证 → 接入指令文件。安装时间 (约3分钟)。

### 手动安装

`install.sh` 做的事:

1. 已有 `probe`(0.6.0-rc342)· `tilth`(0.12.0)就直接使用,没有就装到 `~/.local/bin`。
2. 把技能文件夹软链接到 Claude Code · Pi/Hermes · Codex · OpenCode 的技能根目录(根目录不存在的环境会跳过)。
3. 创建 `~/.local/bin/ci` 入口。
4. 最后用 `ci doctor` 诊断。

```bash
# 只诊断,不做任何改动
bash feature-pack/code-intel/skill/scripts/install.sh --check

# 安装后确认
ci doctor                                  # probe/tilth 版本 + LSP + smoke
ci sym <any-symbol> --scope <subdir>       # 0.4 秒内返回
ci outline <file>                          # 头部显示 token 数
```

通过标准: `ci doctor` 有输出 + `ci sym` 有返回 + `ci outline` 显示 token 数。

### 接入智能体的指令文件

不接入的话,智能体不会用 `ci`。在所用环境的全局指令文件(Claude Code `~/.claude/CLAUDE.md` · Codex `~/.codex/AGENTS.md` · OpenCode `~/.config/opencode/AGENTS.md` · Pi `~/.pi/agent/AGENTS.md`)里加入下面几行。

```markdown
**HARD RULE: 代码符号 · 引用 · 结构的查找优先用 `ci`。grep/rg/git grep 只用于日志 · 配置 · 字符串 · 文件是否存在。
禁止直接调用 `probe`/`tilth` — 必须经过 `ci`(内置超时和 scope 保护)。无需预先激活。**
```

### 回滚

```bash
rm ~/.claude/skills/code-intel ~/.agents/skills/code-intel \
   ~/.codex/skills/code-intel ~/.config/opencode/skills/code-intel \
   ~/.local/bin/ci ~/.local/bin/ci-audit
# probe/tilth 二进制可以保留 — 它们也能作为独立 CLI 使用
```

## 用法

### 命令

| 命令 | 作用 |
|---|---|
| `ci search "<query>" [path] [--max N] [--no-tests]` | 语义 · 关键词搜索 (BM25 + AST 代码块 · 默认包含测试文件) |
| `ci sym <name> [--scope P] [--callers\|--deps]` | 符号定义 · 调用方 · 依赖 (定义排在前面) |
| `ci outline <file> [--section S]` | 文件 outline (+ token 数) |
| `ci refs "<file>#<sym>" [--json]` | LSP 精确引用 |
| `ci def "file#sym"` · `ci impl "file#sym"` | LSP 定义 · 实现 |
| `ci ast '<pattern>' [path] [-l lang]` | ast-grep 结构模式 |
| `ci lsp up [--scope P]` · `down` · `status` | LSP 守护进程的启动 · 停止 · 状态 |
| `ci lsp repair [--ws <name>]` | 修复 LSP crash-loop (不删除缓存,而是移到一旁) |
| `ci doctor` | 安装 · 版本 · 守护进程 · smoke 诊断 |
| `ci bench [--queries FILE]` | 性能回归 (p50/p95) |
| `ci-audit [--days N] [--by-harness] [--csv FILE] [--json]` | 从会话记录统计 `ci` · grep · Serena 的调用次数,计算遵守率 |

可以用环境变量 `PROBE_BIN` · `TILTH_BIN` 指定二进制路径。

### 安全保护

- 每次搜索只在 `CI_TIMEOUT`(默认 60 秒)内运行。把仓库根目录当作 scope 会给出警告。确实需要全量扫描时,用 `CI_ALLOW_HEAVY=1 CI_TIMEOUT=600` 作为例外。
- probe 在韩语 Markdown 上 panic 时,会自动加 `-i '*.md'` 重试。
- 多词查询结果为 0 时,会自动改成 `A OR B` 重试。
- Python 结构模式会回退到 ast-grep。
- 不要直接调用 `probe` · `tilth`,始终经过 `ci`。

### 已知陷阱

| 陷阱 | 对策 |
|---|---|
| 以仓库根目录为 scope 直接调用 `tilth` 会让 CPU 失控 (实测 585% CPU · load 139) | 经过 `ci` · scope 用子目录 · 全量扫描用 `CI_ALLOW_HEAVY=1 CI_TIMEOUT=600` |
| probe 在韩语 Markdown 上 panic (SIGABRT) | `ci search` 自动加 `-i '*.md'` 重试 |
| 多词查询被当作 AND,结果为 0 | `ci search` 自动改成 `A OR B` 重试 |
| Python 结构模式结果为 0 (probe 的 bug) | `ci ast` 回退到 ast-grep (需安装 `ast-grep`) |
| Python LSP 是 pylsp (不是 pyright) · 不支持 `call-hierarchy` | `uv tool install python-lsp-server` · 调用方用 `ci sym --callers` |

## 环境要求

- macOS (arm64 · x86_64) 或 Linux。`install.sh` 下载的是 macOS 版 `probe`;在 Linux 上先把 `probe` 0.6.0-rc342 放进 PATH,就会直接使用。
- `curl` · `tar` · `python3`
- 安装 `tilth` 需要 `npx` 或 `cargo`
- 可选: `ast-grep` (`brew install ast-grep` · Python 结构模式回退) · `python-lsp-server` (`uv tool install python-lsp-server` · Python 的 `ci refs`)
- API 密钥 / 账号: 无

## 链接

- [INSTALL.md](INSTALL.md) — 给智能体的安装说明
- [skill/SKILL.md](skill/SKILL.md) — 智能体技能
- [skill/scripts/install.sh](skill/scripts/install.sh) — 安装脚本
- [AI Feature Pack 目录](../../README.zh-CN.md)
