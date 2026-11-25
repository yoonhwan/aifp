<div align="center">

# memory-system

**为 OpenClaw 智能体搭建三层记忆结构 —— 工作区记忆文件、作为第二大脑的 Obsidian 库,以及覆盖整个库的记忆搜索(NotebookLM 可选)。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 智能体把对话 · 决定 · 经验积累到长期记忆 `MEMORY.md` 和每日笔记 `memory/YYYY-MM-DD.md` 中。
- 在 Obsidian 库里建立文件夹结构(Daily · News-Links · Meetings · People · Projects · Reference · Ideas · Archive 等),以及 `HOME.md` 和索引笔记。
- 把整个库加入智能体的记忆搜索范围(`extraPaths` · OpenAI 嵌入 · 文件变更监听)。
- 把每日笔记和 `MEMORY.md` 镜像到库的 `Daily/`(符号链接或定期复制)。
- 把新闻链接转成笔记,把对话记录积累为人物档案。
- 可选:用 `nlm` CLI 把库中文档加入 NotebookLM 作为来源,进行基于来源的问答。

## 快速开始

```bash
# 1) 对 OpenClaw 智能体说: "阅读 feature-pack/memory-system/INSTALL.md 并安装"
# 2) 安装完成后检查
ls ~/.openclaw/workspace/MEMORY.md
obsidian-cli print-default
```

## 安装

让智能体来装:对它说"阅读 `feature-pack/memory-system/INSTALL.md` 并安装"。`INSTALL.md` 是供 OpenClaw 智能体阅读并自行完成安装的提示词。遇到 `{{PLACEHOLDER}}` 时,智能体会询问用户并填入答案。

| 占位符 | 含义 | 默认值 |
|---|---|---|
| `{{OC_WORKSPACE}}` | OpenClaw 工作区路径 | `~/.openclaw/workspace` |
| `{{VAULT_PATH}}` | Obsidian 库的绝对路径 | — |
| `{{VAULT_NAME}}` | Obsidian 库名(文件夹名) | — |

安装顺序:① 工作区记忆文件 ② 库文件夹结构 + obsidian-cli ③ 记忆搜索集成 ④ 在 `TOOLS.md` 中加入 Obsidian 条目 ⑤ 每日记忆镜像 ⑥ NotebookLM 集成(可选) ⑦ 安装检查。手动安装的关键命令如下。

```bash
brew install yakitrak/yakitrak/obsidian-cli
obsidian-cli set-default "my-vault"
# 修改 openclaw.json 后使配置生效
openclaw gateway restart
```

## 用法

### 三层结构

| 层 | 内容 | 位置 |
|---|---|---|
| 1 · 工作区记忆 | 长期记忆(整理后) + 每日笔记(原始日志) | `MEMORY.md` · `memory/*.md` |
| 2 · Obsidian 库 | 每日镜像 · 链接笔记 · 对话记录 · 人物档案 | `Daily/memory/` · `News-Links/` · `Meetings/` · `People/` |
| 3 · NotebookLM(可选) | 基于来源的问答 | `nlm` CLI |

### 会话规则

- 会话开始时用 `exec("ls memory/")` 查看文件列表,读取今天 · 昨天的每日笔记。主会话还要读取 `MEMORY.md`。
- 不要像 `read("memory")` 这样整个读取文件夹(EISDIR 错误)。逐个读取文件。
- 每日笔记里不写个人信息 · API 密钥。不要在群聊中加载 `MEMORY.md`。
- 定期把每日笔记中的重要内容整理到 `MEMORY.md`。

### 记忆搜索配置

以下配置写入 `openclaw.json`。需要在 OpenClaw 的环境变量或配置中设置 `OPENAI_API_KEY`。

```json
{
  "agents": {
    "defaults": {
      "memorySearch": {
        "enabled": true,
        "sources": ["memory", "sessions"],
        "extraPaths": ["{{VAULT_PATH}}"],
        "provider": "openai",
        "model": "text-embedding-3-small",
        "sync": { "watch": true, "watchDebounceMs": 1500 },
        "query": {
          "hybrid": { "enabled": true, "vectorWeight": 0.7, "textWeight": 0.3, "candidateMultiplier": 4 }
        }
      }
    }
  }
}
```

### NotebookLM

这是需要 `notebooklm` 包的可选步骤。没有就跳过。

```bash
nlm notebook create "my-vault Knowledge Base"
nlm source add <notebook-id> --file "<vault-path>/HOME.md"
nlm chat query <notebook-id> "这个项目里最重要的决定是什么?"
```

### 故障排查

- 记忆搜索里找不到库中的文件:检查 `extraPaths` 中库的绝对路径 · `watch: true` · OpenAI API 密钥,然后运行 `openclaw gateway restart`。库很大时,建立索引可能需要几分钟到几十分钟。
- obsidian-cli 找不到库:重新运行 `obsidian-cli set-default`,并确认已在 Obsidian 应用中至少打开过一次该库。
- iCloud 库中的符号链接可能不会同步。这时改用定期复制(rsync)来镜像。
- NotebookLM 认证失败:参考 `notebooklm` 包的认证步骤(需要 Chrome)。

## 环境要求

- macOS(Apple Silicon 或 Intel)
- 已安装并运行 OpenClaw
- Obsidian 应用 · obsidian-cli(Homebrew)
- API 密钥 / 账号:OpenAI API 密钥(嵌入 `text-embedding-3-small`) · 可选:`nlm` CLI 和 Google 账号(NotebookLM)
- 安装时间:约 15 分钟

## 链接

- [INSTALL.md](INSTALL.md)
- [skill/SKILL.md](skill/SKILL.md) —— 智能体技能
- [obsidian/setup.md](obsidian/setup.md)
- [test/verify.md](test/verify.md)
- [notebooklm 包](../notebooklm/)
- [AI Feature Pack 目录](../../README.zh-CN.md)
