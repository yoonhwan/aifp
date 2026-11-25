<div align="center">

# agent-surface-audit

**只读不写、可安全公开的 dry-run 盘点工具,列出智能体技能和 hook 所在的位置。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 列出智能体能看到的技能和 hook 位置:源码包、用户技能根目录、项目 overlay、hook 配置路径。
- 只读取安全的元数据,不读取机密内容。
- 不修改真实的 `~/.claude`、`~/.codex`、`~/.agents`、项目 overlay 设置、symlink、hook、session、log 和 auth 数据。
- 找出重复暴露的风险和损坏的 symlink,并附带回滚命令,提出后续处理建议。
- 输出便于阅读的报告或 JSON,也可以把 JSON 保存到文件。

## 快速开始

```bash
feature-pack/agent-surface-audit/core/bin/agent-surface-audit --dry-run
```

## 安装

本包不会向真实运行环境安装任何东西。它被有意设计为只读,所以直接在 checkout 的位置运行即可。详见 [INSTALL.md](INSTALL.md)。

如果想用 `agent-surface-audit` 这个名字直接调用,把它的 `bin` 目录加入当前 shell 的 `PATH`:

```bash
export PATH="$PWD/feature-pack/agent-surface-audit/core/bin:$PATH"
agent-surface-audit --dry-run
```

做 dry-run 审查期间,不要把本包 symlink 到 `~/.claude`、`~/.codex`、`~/.agents` 或项目 overlay 根目录。后续的安装器应由审查过的报告生成,并包含回滚命令。

## 用法

### 选项

| 选项 | 说明 |
|------|------|
| `--dry-run` | 必需。工具按约定只读,没有此选项不会运行 |
| `--repo-root PATH` | 要检查的仓库 (默认: 当前目录) |
| `--home PATH` | 要检查的主目录 (默认: 你的主目录) |
| `--json PATH` | 同时把 JSON 报告保存到此文件 |
| `--format human\|json` | stdout 的输出格式 |
| `--public-safety` | 只报告公开安全部分 |

### 示例

```bash
agent-surface-audit --dry-run
agent-surface-audit --dry-run --repo-root "$PWD" --home "$HOME" --json report.json
agent-surface-audit --dry-run --format json
agent-surface-audit --dry-run --public-safety --format json
```

### 报告包含的内容

- 公开安全分类
- `feature-pack/*` 下的源码包
- `$HOME/.claude/skills`、`$HOME/.codex/skills`、`$HOME/.agents/skills` 下的用户运行时技能根目录
- `.claude/skills`、`.codex/skills`、`.agents/skills` 下的项目 overlay
- 仅包含 hook 配置路径是否存在的元数据
- 重复暴露的风险和损坏的 symlink
- 后续处理建议和回滚命令
- 被跳过的私有路径(仅按类别)

### 说明

- 检查发现只是报告数据,不是进程失败。只有参数无效或运行时/工具出错时,命令才会返回非 0 的退出码。
- 在实际加载行为得到确认之前,Codex/OMO 的技能暴露位置仍是 `~/.codex/skills`。`~/.agents/skills` 只用于兼容和 overlay。
- 验证脚本位于 `test/` 下(`verify.sh` 和 `verify_manifest_contract.sh`)。

## 环境要求

- `bash`
- `python3` (3.10 或更高 — 代码使用了 `match` 语句)
- `jq` (用于 `test/` 下的验证脚本)
- 无需 API 密钥

## 链接

- [INSTALL.md](INSTALL.md) — 如何就地运行
- [AI Feature Pack 目录](../../README.zh-CN.md)
