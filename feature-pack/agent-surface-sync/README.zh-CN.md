<div align="center">

# agent-surface-sync

**把 `feature-pack/*` 与 `hooks/` 中的共享智能体 surface 以链接方式安装 · 更新到本地运行时目录的工具 — 默认 dry-run。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 读取每个包的 `manifest.json`,把共享 CLI 链接到 `~/.agents/bin`。
- 链接 manifest 标为可安装(`installable`)的运行时技能 · 辅助文件。若该运行时的目录不存在,则跳过。
- 把共享 hook 源 `hooks/` 链接到 `~/.agents/hooks`。
- 若存在 `hooks/manifests/`,把 hook 条目合并到 `~/.claude/settings.json`(Claude Code) · `~/.codex/hooks.json`(Codex)。已有条目会保留。
- 默认 dry-run。只有加上 `--apply` 才会修改,修改前先备份原有内容。

## 快速开始

```bash
# 在仓库根目录 — 只查看计划 (dry-run)
feature-pack/agent-surface-sync/core/bin/agent-surface-sync
# 计划无误后再应用
feature-pack/agent-surface-sync/core/bin/agent-surface-sync --apply --package baton
```

## 安装

如果交给智能体,可以说"读 `feature-pack/agent-surface-sync/INSTALL.md` 并安装"。无需另外安装,在仓库根目录原地运行即可(默认 `--repo-root` 为当前目录)。

```bash
feature-pack/agent-surface-sync/core/bin/agent-surface-sync
```

如需在 shell 中直接用名称调用,把它加入 PATH(在仓库根目录)。

```bash
export PATH="$PWD/feature-pack/agent-surface-sync/core/bin:$PATH"
agent-surface-sync --package baton,tmuxc
```

请在确认 dry-run 输出无误后再使用 `--apply`。

## 用法

### 命令示例

```bash
agent-surface-sync                                   # 所有包 · 所有运行时 dry-run
agent-surface-sync --package baton,tmuxc             # 只处理选定的包
agent-surface-sync --runtime claude-code --format json
agent-surface-sync --apply --package baton           # 实际应用
```

### 选项

| 选项 | 取值 | 默认值 |
|---|---|---|
| `--dry-run` · `--apply` | 只查看计划 · 实际应用 | `--dry-run` |
| `--package` | 逗号分隔的包名 | 所有包 |
| `--runtime` | `all` · `agents` · `claude-code` · `codex-cli` | `all` |
| `--format` | `human` · `json` | `human` |
| `--json` | 同时把报告保存为 JSON 文件的路径 | 无 |
| `--repo-root` | 仓库根目录 | 当前目录 |
| `--home` | 代替主目录使用的路径 | 用户主目录 |

退出码:0 = 成功 · 2 = 参数 · 路径错误 · 1 = 文件读写错误。

### 阅读报告

dry-run 报告列出计划的修改 · 跳过的项目 · 回滚命令。每项修改都带有状态。

| 状态 | 含义 |
|---|---|
| `install` | 新建链接 |
| `relink` | 重新指向原本指向别处的链接 |
| `replace-existing` | 备份不是链接的文件 · 目录,并替换为链接 |
| `merge` | 向 hook 配置文件合并条目 |
| `up-to-date` | 无需修改 |

### 备份与回滚

- 备份保存在 `~/.agents/state/agent-surface-sync/backups/<operation_id>/`。
- 照原样运行报告中的 `rollback` 行(`rm -rf <target> && mv <backup> <target>`)即可恢复原状。

## 环境要求

- Python 3.12 及以上(仅用标准库 · `typing.override`)
- 要链接到的运行时目录:Claude Code = `~/.claude` · Codex = `~/.codex`(缺少的会被跳过)
- API 密钥 / 账号:无

## 链接

- [INSTALL.md](INSTALL.md)
- [AI Feature Pack 目录](../../README.zh-CN.md)
