<div align="center">

# mcp-manager

**在不输出机密配置值的前提下,查看、停用、重新启用和精简 Claude Code 与 Codex MCP 服务器的本地工具。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 只按名称列出 Claude Code 与 Codex 的 MCP 服务器(已启用 · 已停用)。不输出配置值。
- 停用单个 MCP 服务器,也可以重新启用。每次修改前都会留下备份,便于还原。
- 只保留给定列表(`--keep`)中的服务器,其余一次性全部停用(prune)。
- 已停用服务器的配置片段保存在 `~/.agents/state/mcp-manager/disabled/` 下。
- 会修改内容的命令默认是 dry-run。只有加上 `--apply` 才会写文件。

## 快速开始

```bash
# 在仓库根目录
feature-pack/mcp-manager/core/bin/mcp-manager list --format human
feature-pack/mcp-manager/core/bin/mcp-manager disable stitch --runtime claude --dry-run
```

## 安装

如果交给智能体,可以说"读 `feature-pack/mcp-manager/INSTALL.md` 并安装"。目前这是在仓库内原地运行的工具,无需另外安装。

```bash
feature-pack/mcp-manager/core/bin/mcp-manager list --format human
```

如需在 shell 中直接用名称调用,把它加入 PATH(在仓库根目录)。

```bash
export PATH="$PWD/feature-pack/mcp-manager/core/bin:$PATH"
mcp-manager list --format human
```

## 用法

### 命令

| 命令 | 作用 |
|---|---|
| `mcp-manager list` | 各运行时已启用 · 已停用的服务器名称 |
| `mcp-manager disable <server>` | 停用单个服务器并保存其配置片段 |
| `mcp-manager enable <server>` | 重新启用已保存的服务器 |
| `mcp-manager prune --keep a,b,c` | 停用所有不在 `--keep` 中的服务器(必须提供 `--keep`) |

```bash
mcp-manager list --format human
mcp-manager disable stitch --runtime claude --dry-run
mcp-manager disable stitch --runtime codex --dry-run
mcp-manager prune --runtime claude --keep context,filesystem,think --dry-run
mcp-manager prune --runtime codex --keep filesystem,node_repl,serena,think --dry-run
```

### 选项

| 选项 | 取值 | 默认值 |
|---|---|---|
| `--runtime` | `list`: `all` · `claude` · `codex` / 其他: `claude` · `codex` (也接受 `claude-code` · `codex-cli`) | `list` = `all` · 其他 = `codex` |
| `--dry-run` · `--apply` | 只显示计划的修改 · 实际写入 | `--dry-run` |
| `--format` | `human` · `json` | `human` |
| `--home` | 代替主目录使用的路径 | 用户主目录 |
| `--keep` | 逗号分隔的服务器名称(仅 `prune`) | 无 |

退出码:0 = 成功 · 2 = 参数错误或无法处理的请求(例如没有已保存的片段) · 1 = 文件读写错误。

### 涉及的文件

- Codex:`~/.codex/config.toml`
- Claude Code:修改 `~/.claude.json`,并读取 MCP 映射 `~/.claude/.mcp.json` · `~/.claude/mcp.json`。
- 保存 · 备份:`~/.agents/state/mcp-manager/`(`disabled/<runtime>/` · `backups/<runtime>/`)
- 只有加上 `--apply` 才会写入这些文件。

## 环境要求

- Python 3.12 及以上(仅用标准库 · `typing.override` · `tomllib`)
- bash(`core/bin/mcp-manager` 启动脚本)
- API 密钥 / 账号:无

## 链接

- [INSTALL.md](INSTALL.md)
- [AI Feature Pack 目录](../../README.zh-CN.md)
