<div align="center">

# agent-cli

**一个功能包同时提供 AI 编码智能体 CLI 的安装与对比指南,以及把任务非交互地交给另一个模型的委派框架。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 指导你安装、认证并对比 Claude Code · Codex · Gemini · OpenCode · Cursor Agent · Pi 这 6 种 CLI。
- 在当前会话里非交互地调用另一个模型来干活,让它自主运行,并用 `resume` 接着往下做。
- 注入角色(DA · designer · architect),让被委派的模型立刻有明确的职责。
- 让另一个模型对某个模型的产出做对抗式验证(author 与 review 分开)。
- 把同一个任务交给多个提供商,互相 cross-check。
- 可以与 oh-my-\* · baton · tmuxc 等上层框架联动(可选)。没装就会被忽略,非交互委派、角色和 resume 不依赖它们也能用。

## 快速开始

```bash
# 在仓库根目录: 检查操作系统和现在能用的 CLI
bash feature-pack/agent-cli/scripts/detect-env.sh
# 安装技能之后(见安装一节): 让 codex 以 DA 角色做验证,再接着追问
bash ~/.claude/skills/agent-cli/scripts/resume_chain.sh codex DA "对这个 diff 做对抗式验证" "把发现的问题按优先级整理"
```

## 安装

### 让智能体安装

对智能体说:

```text
读取 feature-pack/agent-cli/INSTALL.md 并安装
```

### 手动安装

```bash
mkdir -p ~/.claude/skills/agent-cli/references ~/.claude/skills/agent-cli/scripts
cp SKILL.md            ~/.claude/skills/agent-cli/SKILL.md
cp references/*.md     ~/.claude/skills/agent-cli/references/
cp scripts/*.sh        ~/.claude/skills/agent-cli/scripts/
chmod +x ~/.claude/skills/agent-cli/scripts/*.sh
```

- 上面的命令在 `feature-pack/agent-cli/` 目录内执行。如果是 OpenClaw 等其他智能体,只需把技能路径改成它的约定。`SKILL.md` 可以单独阅读。
- 建议先运行 `bash scripts/detect-env.sh`。它会区分 macOS · Linux · WSL,并一次性输出现在能用的 CLI、未安装 CLI 的安装提示和 WSL 注意事项。
- 如果智能体有 TOOLS.md(或同类目录),把 `config/tools-section.md` 的内容追加进去。
- OpenCode 的默认模型是 `opencode/deepseek-v4-flash-free`。想换的话,设置 `export OPENCODE_MODEL=<provider/model>` (列表: `opencode models`)。
- Pi 用 `export PI_MODEL=<provider/model>` 更换默认模型。请先用 `pi auth check --provider <provider> --json` 确认认证。注入技能用 `--skill`,限制工具用 `--tools`。

### 验证安装

```bash
bash ~/.claude/skills/agent-cli/scripts/selftest.sh   # 在隔离或可信的文件夹里运行
```

同时对照 `test/verify.md` 里的检查清单。

## 用法

### 支持的 CLI

| CLI | 非交互 | 自动运行 | resume |
|-----|--------|---------|--------|
| Claude Code | `claude -p` | `--dangerously-skip-permissions` | `--resume <sid>` |
| Codex | `codex exec` | `--full-auto` ⎮ `--yolo` | `codex exec resume --last` |
| Gemini | `gemini -p` | `--approval-mode yolo` | `--resume <session_id>` |
| OpenCode | `opencode run` | 默认无需批准 | `-s <sid>` / `-c` |
| Cursor Agent | `cursor-agent -p` | `-f` / `--force` | `--resume <chatId>` |
| Pi | `pi -p` | `--tools <allowlist>` (没有批准提示) | `--session-id <sid>` / `--session <sid>` |

- Aider 和 Amp 只作为参考说明(`references/install-and-compare.md`)。
- 会话中,像「让 codex 对这个 PR 做 DA 对抗式验证」「用 Gemini 对这个设计做 cross-check」「resume 刚才的会话继续追问」这样的请求会自动触发它。

### 委派与 resume

```bash
bash ~/.claude/skills/agent-cli/scripts/resume_chain.sh codex DA "对这个 diff 做对抗式验证" "把发现的问题按优先级整理"

# 如果要固定 Claude 的模型和 effort
CLAUDE_MODEL=<model-id> CLAUDE_EFFORT=high \
bash ~/.claude/skills/agent-cli/scripts/resume_chain.sh claude DA \
  "对这个改动做对抗式验证" \
  "只再告诉我一次最终是否批准"
```

- `resume_chain.sh` 调用 Claude 时,会把 `CLAUDE_MODEL` 和 `CLAUDE_EFFORT` 环境变量原样传过去。

### 脚本

| 脚本 | 作用 |
|---|---|
| `scripts/detect-env.sh` | 区分操作系统 · 列出现在能用的 CLI · 安装提示 · WSL 注意事项 |
| `scripts/selftest.sh` | 一次性检查 6 种 CLI 的非交互 · 自动运行 · resume(带超时和日志) |
| `scripts/test_opencode.sh` | 单独检查 OpenCode(自动发现模型) |
| `scripts/resume_chain.sh` | 角色 + 多轮 resume 的链式调用 |
| `scripts/cloud-dataset-batch.sh` | 用 cloud session credits 批量生成训练 · 标注数据并取回 |

### 云端额度批处理

Claude 的 cloud session credits(与订阅分开发放的额度)只在 cloud session 里扣除。本地 CLI 或经过代理的调用不会扣。`scripts/cloud-dataset-batch.sh` 在没有仓库也没有代码的空文件夹里启动 cloud session,结束后取回(teleport),只提取回答里输出的 JSONL,并累积成数据集。

```bash
bash scripts/cloud-dataset-batch.sh --task lexicon --lang ko,ja,th --count 300 --batch 25 --parallel 3 --budget 20
bash scripts/cloud-dataset-batch.sh --task label   --lang ko --labels work,tech,legal,daily,billing,other --count 200
bash scripts/cloud-dataset-batch.sh --task doc     --lang ko --count 4 --batch 4 --parallel 1 --budget 1   # 小批量试跑
```

| task | 生成的数据 |
|---|---|
| `lexicon` | 语言学词典条目(lemma · pos · IPA · gloss · 例句 · register) |
| `parallel` | 平行语料(src / tgt · domain) |
| `label` | 分类标注(text · label · rationale)。用 `--labels` 固定标签集合 |
| `qa` | 语言学习问答(level · topic) |
| `doc` | 长文档章节(每行 520 字)。用于大量消耗额度 |
| `free` | 自由格式 |

- 输出: `<out>/data.jsonl`(批次之间去重并重新编 `id`) · `<out>/run-*/index.tsv`(会话与条数的台账) · `ledger.json`(额度增减)
- 实测: 每个会话约 25 条记录,每条记录约 $0.03,并行 2 到 4 可以扩展。
- 注意: cloud credits 有到期日,请在到期前用完,并用 `--budget` 设置支出上限。大量重复生成可能被判定为账号滥用,请生成你真正会用的数据。

### 安全

- 自动运行的标志(dangerous / full-auto / yolo / force)会去掉人工批准这道关。只在隔离或可信的工作区里使用。
- 被委派的 CLI 各自需要认证。本包不会注入凭据。
- 把委派的结果当作不可信输入,在主会话里审查后再使用。

## 环境要求

- 支持环境: macOS · Linux · WSL
- `perl` 和 `python3` — macOS 自带。WSL 或 Ubuntu 没有的话: `sudo apt install -y perl python3`
- 6 种智能体 CLI 里至少有 1 个在 PATH 中,并已完成该 CLI 自身的认证。未安装的 CLI 会被自动跳过。
- WSL: OAuth 会在 Windows 浏览器中打开(可以手动复制粘贴 URL)。cursor-agent 可能不存在(自动 SKIP)。请在 `~/` 目录内工作。
- 仅云端额度批处理: `~/.headroom/claude-credit.sh`(ccx / ccxt) · `claude` 2.1.310 或更高版本 · tmux

## 链接

- [INSTALL.md](INSTALL.md) — 面向智能体的安装说明
- [SKILL.md](SKILL.md) — 技能定义
- [references/per-cli.md](references/per-cli.md) — 各 CLI 的非交互 · 自动运行 · resume 详情
- [references/install-and-compare.md](references/install-and-compare.md) — 安装 · 认证 · 对比
- [references/personas.md](references/personas.md) — DA · designer · architect 角色
- [AI Feature Pack 目录](../../README.zh-CN.md)
