<div align="center">

# obsidian-cli

**让智能体用 CLI 查看、搜索、创建、修改、删除和移动 Obsidian 库(Markdown 笔记)中的笔记**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 查看: 列出库中的文件和文件夹,读取笔记内容。
- 搜索: 按笔记名模糊搜索、搜索笔记内容。
- 创建: 新建笔记(不存在的文件夹会一并创建),打开每日笔记。
- 修改: 覆盖、追加(append)、查看 / 修改 / 删除 frontmatter 键。
- 删除与移动: 删除笔记;移动或重命名笔记时自动更新 wikilink。
- 智能体也可以直接用 `read` / `write` / `edit` 工具修改 `.md` 文件,Obsidian 会察觉变化。

## 快速开始

```bash
brew install yakitrak/yakitrak/obsidian-cli
obsidian-cli set-default "my-vault"
obsidian-cli create "Projects/my-note" --content "# My note"
obsidian-cli print "Projects/my-note"
```

## 安装

### 交给智能体

对智能体说:"读取 `feature-pack/obsidian-cli/INSTALL.md` 并安装。" 安装时间约3分钟。智能体会询问库的名称。

### 手动安装

```bash
# 1. 安装 CLI — v0.2.3 或更高
brew install yakitrak/yakitrak/obsidian-cli
obsidian-cli --version

# 2. 设置默认库 — Obsidian 记录的库列表在这个文件中
cat ~/Library/Application\ Support/obsidian/obsidian.json
obsidian-cli set-default "my-vault"
obsidian-cli print-default

# 3. 技能 — 如果已有 OpenClaw 官方 obsidian 技能,则无需复制
ls /opt/homebrew/lib/node_modules/openclaw/skills/obsidian/SKILL.md
mkdir -p ~/.openclaw/workspace/skills/obsidian/
cp skill/SKILL.md ~/.openclaw/workspace/skills/obsidian/SKILL.md
```

4. 参照 `config/tools-section.md`,在 OpenClaw 工作区的 `TOOLS.md` 中加入 Obsidian CLI 一节(二进制路径、默认库、主要命令)。
5. 可选: 在 Obsidian 应用中开启 Daily notes(Core plugin)。推荐的 Community plugin 有 Dataview、Templater、Calendar(`obsidian/setup.md`)。
6. 运行 `test/verify.md` 中的 CRUD 测试。所有步骤 exit code 都为 0 即安装完成。

## 用法

### 命令

| 命令 | 作用 |
|---|---|
| `obsidian-cli set-default "<vault>"` · `print-default [--path-only]` | 设置 · 查看默认库 |
| `obsidian-cli list ["<folder>"]` | 列出库根目录或某个文件夹 |
| `obsidian-cli print "<note>"` | 读取笔记 |
| `obsidian-cli search "<query>"` · `search-content "<query>"` | 名称模糊搜索 · 内容搜索(交互式) |
| `obsidian-cli create "<note>" --content "<text>" [--open]` | 新建笔记(自动创建文件夹) |
| `obsidian-cli create "<note>" --content "<text>" --overwrite` · `--append` | 覆盖 · 追加 |
| `obsidian-cli daily` | 创建 · 打开每日笔记 |
| `obsidian-cli frontmatter "<note>" --print` | 查看 frontmatter |
| `obsidian-cli frontmatter "<note>" --edit --key <k> --value <v>` · `--delete --key <k>` | 修改 frontmatter · 删除键 |
| `obsidian-cli move "<old>" "<new>"` | 移动 · 重命名 + 更新 wikilink |
| `obsidian-cli delete "<note>"` | 删除 |
| `obsidian-cli open "<note>"` | 在 Obsidian 应用中打开 |

### 使用要点

- `search` 和 `search-content` 是交互式的,在智能体环境中无法运行。请用 `grep -r` 或 `list` + `print`。
- 移动笔记务必用 `move` 而不是 `mv`。`mv` 会破坏 wikilink。
- 不要写死库路径,用 `print-default --path-only` 获取。
- 不要动 `.obsidian/` 文件夹(设置和插件冲突)。
- 批量修改大量笔记时,直接编辑文件比 CLI 更快。

### 故障排除

| 现象 | 原因 | 解决 |
|---|---|---|
| `brew: command not found` | 未安装 Homebrew | 安装 Homebrew |
| `Cannot find note in vault` | 未设置默认库 · 笔记路径错误 | 检查 `set-default`,路径中去掉 `.md` |
| `search-content` 不工作 | 非交互式环境 | `grep -r` 或 `list` + `print` |
| 新建的笔记在 Obsidian 中看不到 | iCloud 同步延迟 | 等几秒后在应用中刷新 |
| URI handler 错误 | Obsidian 应用未运行 | 启动应用后重试 |

## 环境要求

- 操作系统: macOS
- Homebrew
- Obsidian 应用(URI handler)· 至少一个库
- API 密钥 / 账号: 无

## 链接

- [INSTALL.md](INSTALL.md) — 面向智能体的安装说明
- [skill/SKILL.md](skill/SKILL.md) — OpenClaw 技能
- [config/tools-section.md](config/tools-section.md) — 要加入 `TOOLS.md` 的一节
- [obsidian/setup.md](obsidian/setup.md) — Obsidian 应用设置
- [test/verify.md](test/verify.md) — 验证安装的 CRUD 测试
- [AI Feature Pack 目录](../../README.zh-CN.md)
