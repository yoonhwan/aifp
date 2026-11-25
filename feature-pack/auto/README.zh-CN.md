<div align="center">

# auto

**智能体只改代码,`uv run` 负责跑实验,再由 stdout 的 JSON 判定 keep 或 discard 的自主实验循环。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 以智能体技能 `/auto` 的形式提供 Karpathy AutoResearch 模式的自主实验循环。
- 智能体只做四步:修改代码 → 运行实验 → 读取 JSON → 判定。
- 基础设施检查和初始化由 `prepare.py` 负责,实验运行和指标输出由 `run_experiment.py` 负责。
- 在 `program.md` 中声明目标(指标、可修改范围、约束),智能体就在该范围内反复迭代。
- 实验记录累积在 `results.tsv` 中,结束后可以生成报告。

## 快速开始

```bash
# 1. 安装技能
mkdir -p ~/.claude/skills/auto/references
cp skill/SKILL.md ~/.claude/skills/auto/SKILL.md
cp skill/references/*.md ~/.claude/skills/auto/references/

# 2. 把模板复制到项目中并创建 uv 环境
mkdir -p your-project/autoresearch
cp config/templates/* your-project/autoresearch/
cd your-project/autoresearch && uv sync

# 3. 按项目需要修改 program.md、prepare.py、run_experiment.py
# 4. 在智能体会话中运行 /auto
```

## 安装

可以直接让智能体执行 "Read feature-pack/auto/INSTALL.md and install it"。手动安装则按 [INSTALL.md](INSTALL.md) 的步骤进行:

1. 把技能文件复制到 `~/.claude/skills/auto/`。
2. 在项目根目录创建 `autoresearch/` 文件夹,复制四个模板(`pyproject.toml`、`prepare.py`、`run_experiment.py`、`program.md`),然后运行 `uv sync`。
3. 在 `program.md` 中写下目标,并按项目修改 `prepare.py` 的 `check_runtime()`、`check_data()`,以及 `run_experiment.py` 的 `RUN_CMD`、`parse_result()`、`TIMEOUT`。
4. 添加 `.gitignore`,避免实验产物混入 git,并确认技能已加载。

```bash
# 追加到 autoresearch/.gitignore
cat >> autoresearch/.gitignore << 'EOF'
.venv/
run.log
results.tsv
upstream/
__pycache__/
EOF

# 确认技能已加载(期望值: version: "3.0.0")
grep "version" ~/.claude/skills/auto/SKILL.md
```

## 用法

### 命令

在智能体会话中运行。

| 命令 | 说明 |
|------|------|
| `/auto` | 开始完整流程(setup → 基线 → 目标 → 自主运行) |
| `/auto setup` | 仅初始化 `autoresearch/` |
| `/auto 2h` | 自主运行 2 小时 |
| `/auto 30m` | 自主运行 30 分钟 |
| `/auto overnight` | 自主运行 8 小时 |
| `/auto resume` | 在已有分支上继续 |
| `/auto report` | 根据 `results.tsv` 生成报告 |
| `/auto update` | 对 `upstream/` 执行 git pull |

### 三层结构

```
Layer 1: uv run prepare.py         (1 次) 基础设施检查 + 初始化
Layer 2: 智能体自主循环                 修改代码 → 运行 → JSON → 判定
Layer 3: uv run run_experiment.py  (每次) 运行测试 → 输出指标
```

### stdout JSON 约定

`run_experiment.py` 只在 stdout 的最后一行输出一行 JSON。其余输出(进度、警告)写入 stderr 或 `run.log`。

```json
{
  "score": 0.004,
  "passed": 13,
  "total": 14,
  "failed": ["case-14"],
  "grade_summary": "13S 1A",
  "flush_e2e_ms": null,
  "status": "ok",
  "duration_s": 187.3
}
```

- `status` 取 `"ok"`、`"crash"`、`"error"` 之一,crash/error 时可能附带 `reason`。`flush_e2e_ms` 是可选项(次要指标)。
- exit 0 = 正常结束:智能体根据 `score` 判定 keep 或 discard。
- exit 1 = 崩溃或基础设施失败:智能体回退或修复后重试(最多 2 次)。

### 各领域示例

| 领域 | primary_metric | RUN_CMD | prepare.py |
|------|---------------|---------|------------|
| ML 训练 | val_bpb | `uv run train.py` | GPU + 数据集检查 |
| STT 质量 | avg_cer | `python3 e2e_test.py --baseline --json` | 服务器 + 浏览器 + 音频 |
| API 延迟 | p99_ms | `pytest tests/perf.py --json` | 服务器 + DB |
| 代码质量 | coverage | `pytest --cov --json` | 依赖检查 |

### 提示

- 写好 `program.md` 是关键。指标、范围和约束决定了智能体的行动边界。
- `prepare.py` 只需运行一次,并且是幂等的,不放心时可以重新运行。
- 每次实验的时间预算控制在 5 分钟以内,才能跑更多实验。
- 在专用分支上工作,每次只改一处,每个区域只改 1 到 2 个文件。
- 智能体不修改 `autoresearch/` 内的基础设施文件,只修改项目源码。

## 环境要求

- macOS 或 Linux
- Python 3.11+
- git
- [uv](https://docs.astral.sh/uv/)
- Claude Code 或兼容的智能体 CLI
- 无需 API 密钥 · 安装时间 (约2分钟)

## 链接

- [INSTALL.md](INSTALL.md) — 安装指南
- [stdout JSON 约定详解](skill/references/run-experiment-contract.md)
- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) — 原始模式
- [AI Feature Pack 目录](../../README.zh-CN.md)
