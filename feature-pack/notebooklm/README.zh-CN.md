<div align="center">

# notebooklm

**在终端中控制 Google NotebookLM 的 `nlm` CLI 与 OpenClaw 技能包。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 基于来源的问答:只根据你上传的文档作答。
- 根据文档生成音频播客和视频概览。
- 生成报告、测验、闪卡等学习资料。
- 深度研究可自动收集并分析网页来源。
- 管理笔记本:创建、删除、共享、设置别名。
- 把 Obsidian 库中的文档用作 NotebookLM 的来源。

## 快速开始

```bash
# 1. 安装
uv tool install notebooklm-mcp-cli

# 2. 认证 (会打开 Chrome)
nlm login

# 3. 使用
nlm notebook list
nlm query notebook <notebook_id> "问题"
```

## 安装

可以直接让智能体执行 "Read feature-pack/notebooklm/INSTALL.md and install it"。手动安装则按 [INSTALL.md](INSTALL.md) 的步骤进行:

1. 用 `uv` 安装 `nlm` CLI(`notebooklm-mcp-cli`)。
2. 用 `nlm login` 登录 Google 账号,并用 `nlm auth status` 确认。会话约保持 20 分钟,过期后重新运行 `nlm login`。
3. 把本包的 `skill/` 文件夹复制到 OpenClaw 工作区的技能文件夹中。
4. 在工作区的 `TOOLS.md` 中添加 NotebookLM 部分(内容见 [INSTALL.md](INSTALL.md))。
5. 可选:设置 Obsidian 联动。
6. 用 `nlm --version`、`nlm auth status`、`nlm notebook list` 确认可以正常工作。

```bash
# 没有 uv 就先安装
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装 CLI 并确认
uv tool install notebooklm-mcp-cli
nlm --version

# 找不到 nlm 时,把 ~/.local/bin 加入 PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc

# 复制技能 (OpenClaw 工作区默认值: ~/.openclaw/workspace)
cp -r skill/ ~/.openclaw/workspace/skills/notebooklm

# 更新
uv tool upgrade notebooklm-mcp-cli
```

## 用法

### 主要命令

```bash
# 笔记本
nlm notebook list
nlm notebook create "名称"
nlm notebook get <notebook_id>
nlm notebook describe <notebook_id>

# 来源
nlm source add <notebook_id> --file <path>
nlm source add <notebook_id> --url <url>
nlm source add <notebook_id> --text "内容" --title "标题"

# 问答
nlm query notebook <notebook_id> "问题"

# 生成
nlm audio create <notebook_id> --confirm
nlm video create <notebook_id> --confirm
nlm report create <notebook_id> --confirm
nlm quiz create <notebook_id> --confirm
nlm flashcards create <notebook_id> --confirm
nlm mindmap create <notebook_id> --confirm
nlm slides create <notebook_id> --confirm

# 研究
nlm research start <notebook_id> "主题" --mode deep
nlm research status <notebook_id>

# 下载
nlm download audio <notebook_id> <artifact_id> -o <path>

# 别名 (用短名称代替 UUID)
nlm alias set myproject <notebook_id>
nlm alias list
```

### 在智能体中做问答

- 智能体始终用 `nlm query notebook`,一问一答。
- 不要使用 `nlm chat start`(REPL 模式),智能体无法控制它。
- 运行 `nlm --ai` 可以查看全部命令的指南。

### Obsidian 联动

这是通过 CLI 上传文件的方式,而不是插件。

```bash
# 创建专用笔记本并设置别名
nlm notebook create "My Obsidian Vault"
nlm alias set vault <notebook_id>

# 把文档作为来源上传
nlm source add vault --file "<path-to-vault>/note.md" --wait

# 提问
nlm query notebook vault "请说明项目的结构"
```

### 故障排除

| 现象 | 解决方法 |
|------|----------|
| `nlm: command not found` | 把 `~/.local/bin` 加入 PATH |
| `uv: command not found` | 安装 uv |
| "Cookies have expired" / "authentication may have expired" | 重新运行 `nlm login` |
| Chrome 打不开 | 安装 Chrome (`brew install --cask google-chrome`) |
| Rate limit 错误 | 会自动重试 3 次。持续失败时请稍等 |
| 添加来源失败 | 确认文件没有超过 NotebookLM 的来源大小限制 |

## 环境要求

- macOS (Apple Silicon 或 Intel)
- Python 3.10+
- Google 账号 (可访问 NotebookLM)
- Chrome 浏览器 (用于认证)
- uv (没有的话安装步骤会装上)

## 链接

- [INSTALL.md](INSTALL.md) — 安装指南
- [Obsidian 联动指南](obsidian/setup.md)
- [AI Feature Pack 目录](../../README.zh-CN.md)
