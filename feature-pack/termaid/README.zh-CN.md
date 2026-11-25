<div align="center">

# termaid

**在终端里直接绘制 Mermaid 图的 CLI `termaid-render` 和智能体技能**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 读取 Mermaid 语法,在终端输出带样式的图(用 lipgloss 上色、加边框、加粗)。
- flowchart(`graph LR/TD`) — 节点形状(box · diamond · round · cylinder)、subgraph、边标签。
- sequence diagram — participant、同步与异步箭头、`loop` · `alt/else` 块。
- 基本支持 class · state · ER 图。
- 输入可以是 stdin 管道(`echo '...' | termaid-render`)或文件(`termaid-render diagram.mmd`)。
- 装上技能后,智能体在讨论设计、讲解架构时会自己画图。

## 快速开始

```bash
# 获取源码 · 打构建补丁 · 构建 · 放进 PATH
git clone https://github.com/MKlolbullen/termaid.git ~/scripts/termaid
cd ~/scripts/termaid
mv internal/tui/builder.go internal/tui/builder.go.wip 2>/dev/null || true
sed -i '' 's/return NewBuilder(catalogueNames()), nil/return errView(fmt.Errorf("workflow builder not yet available")), nil/' internal/tui/menu.go 2>/dev/null || true
go build -o termaid-render ./cmd/render/
cp termaid-render /opt/homebrew/bin/termaid-render

# 第一张图
echo 'graph LR
  A[Client] --> B{Auth?}
  B -->|yes| C[Service]
  B -->|no| D[401]' | termaid-render
```

## 安装

### 交给智能体

对智能体说:"读 `feature-pack/termaid/INSTALL.md` 并安装。"智能体会依次检查 Go → clone 源码 → 打构建补丁 → 构建 → 安装到 PATH → 安装技能 → 验证。安装时间 (约2分钟)。

### 手动安装

1. clone 源码(已存在则 `git pull`)。
2. 打构建补丁(必需)。上游的 `internal/tui/builder.go` 无法编译,需要移开,并从 `internal/tui/menu.go` 删掉对 `NewBuilder` 的引用 — 即"快速开始"里的 `mv` · `sed` 两行。
3. 用 `go build -o termaid-render ./cmd/render/` 构建,再复制到 PATH。
4. 把技能复制到 Claude Code 的技能路径并验证。

```bash
# 安装技能 (在包目录下)
mkdir -p ~/.claude/skills/termaid/
cp skill/SKILL.md ~/.claude/skills/termaid/

# 验证
which termaid-render && echo "OK" || echo "FAIL"
termaid-render --help

# 修改源码后重新构建
cd ~/scripts/termaid && go build -o termaid-render ./cmd/render/ && cp termaid-render /opt/homebrew/bin/
```

`INSTALL.md` 会询问的路径及默认值:

| 占位符 | 含义 | 默认值 |
|---|---|---|
| `{{TERMAID_SOURCE_PATH}}` | 源码存放路径 | `~/scripts/termaid` |
| `{{TERMAID_INSTALL_PATH}}` | 二进制安装路径 | `/opt/homebrew/bin/termaid-render` |
| `{{CLAUDE_SKILLS_PATH}}` | Claude 技能路径 | `~/.claude/skills` |

## 用法

```bash
# 流程图 (stdin 管道 — 最常见的用法)
echo 'graph LR
  A[Client] --> B{Auth?}
  B -->|yes| C[Service]
  B -->|no| D[401]' | termaid-render

# 时序图
echo 'sequenceDiagram
  C ->> S : POST /login
  S -->> C : 200 OK' | termaid-render

# 从文件
termaid-render workflow.mmd

# 帮助
termaid-render --help
```

### 支持的图

| 类型 | 关键字 | 支持 |
|---|---|---|
| Flowchart | `graph TD/LR`, `flowchart` | O |
| Sequence | `sequenceDiagram` | O |
| Class | `classDiagram` | O |
| State | `stateDiagram-v2` | O |
| ER | `erDiagram` | O |
| Gantt | `gantt` | X (仅代码块) |

- 节点: `[box]` · `(round)` · `{diamond}` · `[(cylinder)]` · `((circle))`
- 箭头(sequence): `->>` 同步 · `-->>` 异步 · `-x` 失败

### 智能体何时使用

- 讨论设计(架构 · API 设计 · DB schema)、讲解系统结构或代码流程,以及"画成图"之类的请求。
- 关键字: "diagram" · "chart" · "sequence" · "flow" · "architecture" · "mermaid" · "termaid",以及对应的韩语说法。
- 简单的代码修改 · 简短提问 · 代码块已经足够时不使用。
- 图保持简短 — 超过 20 行或节点达到 10 个时拆开。

### 故障排查

| 症状 | 原因 | 解决 |
|---|---|---|
| `termaid-render: command not found` | 不在 PATH 中 | `cp termaid-render /opt/homebrew/bin/` |
| `go: command not found` | 未安装 Go | `brew install go` |
| `builder.go compile error` | 上游代码未完成 | 检查构建补丁 |
| `yaml unmarshal error` | TUI 的 `init()` panic | 只构建 `cmd/render/`(绕过 TUI) |

## 环境要求

- macOS
- Go 1.22+ (`go version` · 没有就 `brew install go`)
- API 密钥 / 账号: 无

## 链接

- [INSTALL.md](INSTALL.md) — 面向智能体的安装说明
- [skill/SKILL.md](skill/SKILL.md) — 智能体技能
- [cli/install.md](cli/install.md) — 只安装 CLI
- [termaid 上游源码](https://github.com/MKlolbullen/termaid)
- [AI Feature Pack 目录](../../README.zh-CN.md)
