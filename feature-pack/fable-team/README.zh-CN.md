<div align="center">

# fable-team

**fable-team ft 2.0 的源码 —— 席位 · 便条 · 派单核心、契约、Slack · Codex · Pi 适配器,以及关闭目标的流程,按"一个文件夹 = 一项职责"划分。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- `ft2/` 存放 ft 2.0 的新骨架。2.0 的现行源码只写在这个文件夹里。
- 席位 · 便条 · 派单等公共核心不感知运行环境的差异。各环境不同的部分由适配器(Slack · Codex · Pi)负责。
- 卡片 · 契约 · 测试对照表的契约定义以及模型表位于 `ft2/contracts/`。
- `goal-close/` 是一个模块,包含一个流程和六条规则,用于把大目标拆成条件格并逐格关闭。
- `legacy_guard.py` 检查 `ft2/` 是否执行 · import · source 了 1.x 的工具。

## 快速开始

```bash
# 在仓库根目录 —— 自检 ft2/ (0 = 无违规)
python3 feature-pack/fable-team/ft2/tools/legacy_guard.py
```

## 安装

本包文件夹里没有 `INSTALL.md`。公开副本中只有 ft 2.0 源码和 `goal-close/` 模块,这里没有写安装步骤。1.x 框架不在公开副本中。克隆仓库后就地阅读本文件夹中的文件,检查工具也像上面"快速开始"那样就地运行。

## 用法

### 文件夹职责

一个文件夹 = 一项职责。

| 文件夹 | 职责 |
|---|---|
| `ft2/core/` | 席位 · 便条 · 派单等 2.0 公共核心。不感知运行环境的差异 |
| `ft2/contracts/` | 卡片 · 契约 · 测试对照表的 2.0 契约定义 |
| `ft2/contracts/models/` | 三张模型表(model-scope · model-fallback · provider-of-model)的正本位置 —— 由 `tools/models.py` 读取 |
| `ft2/adapters/slack/` | Slack 接收 · 发布适配器 |
| `ft2/adapters/codex/` | Codex 运行适配器 |
| `ft2/adapters/pi/` | Pi 运行适配器 · 打开席位(`launch.py`) |
| `ft2/doctor/` | 安装 · 环境诊断 |
| `ft2/tools/` | 检查工具 · 辅助工具 |
| `ft2/tests/` | ft2 测试 |

### legacy_guard

`ft2/` 中的任何文件都不得执行 · import · source 1.x 的路径或工具。检查的模式为 5 类 1.x 路径与工具位置(列表见 [ft2/README.md](ft2/README.md)),检查的扩展名为 `.py` `.sh` `.ts` `.js` `.json`。`*.md` 是说明文字,允许出现。代码文件中的注释也会检查。

```bash
python3 feature-pack/fable-team/ft2/tools/legacy_guard.py          # 自检 ft2/
python3 feature-pack/fable-team/ft2/tools/legacy_guard.py <dir>    # 检查其他目录树
```

| 退出码 | 含义 |
|---|---|
| `0` | 无违规 |
| `1` | 有违规(每条一行 `<文件>:<行>: <模式>`) |
| `2` | 用法或路径错误 |

局限:这是字符串检查,无法发现运行时拼接出的路径。这类路径交给评审来看。

### goal-close

把大目标拆成 N 个条件格,每一格由一个席位从规划一直负责到关闭:规划 → 实现(测试 Red → Green · PR) → DA 评审 → 在已安装环境中验证 → 次日监控 → 关闭。

| 文件 | 内容 |
|---|---|
| `00-flow.md` | 一个流程和六条规则 |
| `10-cell.md` | 目标文件的格子与格子规则 |
| `20-situations.md` · `30-direct.md` | 按情况处理 · 不经过团队负责人的路径 |
| `40-conduct.md` | 行为准则与要去掉的特征 |
| `roles/` | 各角色的说明(`arch` · `da` · `master` · `nano`) |
| `phrases.tsv` · `MODULE.json` | 用语表 · 模块版本(`gc-1.3`)和每个文件的 sha256 |

## 环境要求

- Python 3(`legacy_guard.py` · 只用标准库)
- API 密钥 / 账号:无(针对 `legacy_guard.py`)
- 运行适配器所需的条件,本文件夹的文档中没有写明。

## 链接

- [ft2/README.md](ft2/README.md) —— ft 2.0 文件夹职责与禁止依赖 1.x
- [goal-close/00-flow.md](goal-close/00-flow.md) —— 关闭目标的流程
- [AI Feature Pack 目录](../../README.zh-CN.md)
