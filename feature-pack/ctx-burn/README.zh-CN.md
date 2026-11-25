<div align="center">

# ctx-burn

**只读审计工具:用你自己日志里的数字和图表,显示本地 AI 编程智能体消耗了多少上下文**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 智能体每一轮都会重新发送 **整段对话 + 自动加载的记忆 + 工具定义**。`ctx-burn` 从本地会话日志测量这部分成本(权重:缓存读取 `0.1x` · 缓存重写 `2x` · 输出 `5x`)。
- 自动发现已安装和正在运行的运行时:`claude` · `codex` · `pi` · `opencode` 细到 token 用量;`hermes` · `openclaw` · `commandcode` 只看自动加载文件大小和运行中的进程数。
- 用图表给出缓存全量重写占比 · 每次请求的平均上下文 · 超过 4KB 的自动加载文件 · 蒸馏的盈亏平衡轮数 · 启动预算(重新蒸馏 vs 续接)。
- `--request` 拆解一份捕获的请求体,查看工具定义的大小。
- 同包一起安装 `ctx-time`(墙钟时间花在哪里) · `ctx-window`(对话窗口用在哪里) · `ctx-share`(协调占比和周换算看板)。
- `--json` 输出姊妹工具 `ctx-plan` 读取的契约 `ctx.v1` 块。不写设置和文件 · 不联网 · 不需要 API 密钥。

## 快速开始

```bash
git clone https://github.com/yoonhwan/aifp.git
cd aifp/feature-pack/ctx-burn
bash install.sh            # 在 ~/.local/bin 建符号链接 (ctx-burn + ctx-waste alias)

cd ~/my-project
ctx-burn                   # 最近 3 小时 · 当前目录
ctx-burn --lang ko         # 韩语输出 (默认英语)
```

## 安装

### 交给智能体

对智能体说 "Read feature-pack/ctx-burn/INSTALL.md and install it",或把下面这段原样粘贴到 Claude Code · Codex · Pi · OpenCode 等编程智能体里,它会自己完成安装 · 运行 · 解读结果。工具是只读的,运行是安全的。

```text
Install and run ctx-burn on this project, then explain the output.
https://github.com/yoonhwan/aifp/tree/main/feature-pack/ctx-burn

1. Clone the repo and run feature-pack/ctx-burn/install.sh (creates ~/.local/bin/ctx-burn).
2. Run `ctx-burn --hours 6` in this project root. Use `--lang ko` if I speak Korean.
3. From the output, report only these: cache full-rewrite share, average context per request,
   and the top 3 auto-loaded files over 4KB.
4. If full rewrite is above 20%, find the cause from local logs (resume size, sessions starting
   together, account switching) and show the evidence line.
5. If auto-loaded files are over 4KB, propose moving them out of the auto-load path with a 1KB digest.
6. Ask me before changing any setting. The tool itself is read-only, so running it is safe.
```

### 手动安装

`install.sh` 只在 `~/.local/bin` 建符号链接:`ctx-burn` · `ctx-waste`(`ctx-burn` 的永久 alias) · `ctx-share` · `ctx-time` · `ctx-window`。出现 `command not found` 说明 `~/.local/bin` 不在 PATH 里。

```bash
CTX_BURN_BIN_DIR="$HOME/bin" bash install.sh   # 更换安装目录 (旧名 CTX_WASTE_BIN_DIR 也会读取)
export PATH="$HOME/.local/bin:$PATH"           # 不在 PATH 时加到 shell rc
bash uninstall.sh                              # 卸载 — 只删符号链接
```

`uninstall.sh` 删除 `ctx-burn` · `ctx-waste` · `ctx-time` · `ctx-window` 符号链接。不动会话日志和设置。

## 用法

### 读懂输出

| 段 | 显示内容 | 看点 |
|---|---|---|
| `[0]` 运行时环境 | 每个运行时的已安装 · 运行中 · 会话数 · 最后时间 · 数据类型 | 无需配置,自动发现 |
| `[1]` 自动加载记忆 | 每次请求都要付费的文件及其 token 数 | `!` = 超过 4KB 的文件。大的规则文件移到按需打开的位置,只留 1KB 摘要 |
| `[2]` 消耗结构 | 缓存全量重写 · 缓存读取等的加权占比 | 全量重写超过 20% 就是头号嫌疑。重写 1 次 = 普通请求 20 次的成本 |
| `[3]` 每次请求的上下文 | 平均 · 最大 token | 平均超过 200k = 对话已长到窗口尽头,蒸馏没有生效 |
| 蒸馏的盈亏平衡 | 重启成本 · 每轮节省 · 盈亏平衡轮数 | 每个会话的轮数超过盈亏平衡点,就该更频繁地蒸馏 |
| 启动预算 | 根据闸门 · 固定 prefix · 交接大小,对比重新开始 vs 续接的剩余空间和重写成本 | 比窗口大小更关键的是"会话开始时留给对话的份额"。用 `--gate` · `--resume-caps`(逗号分隔)调整 |

### ctx-burn 选项

| 选项 | 默认值 | 含义 |
|---|---|---|
| `--lang en\|ko` | `en` | 输出语言 |
| `--runtime auto\|all\|<name>` | `auto` | 要细看的运行时 (`auto` = 所有有数据的) |
| `--hours N` | 3 | 时间窗口(小时) |
| `--project PATH` | 当前目录 | 查找 CLAUDE.md · rules · memory 的项目根目录 |
| `--request FILE` | 无 | 拆解一份捕获的 **请求体** 日志 (工具大小 · `defer_loading`) |
| `--rewrite-tokens N` | 150000 | 算作全量重写的大小 |
| `--budget N` | 250000 | 建议的蒸馏阈值 |
| `--top N` | 6 | 每个运行时的会话行数 |
| `--json` | 关 | 机器可读 · 追加 `ctx-plan` 读取的 `plan_input` 块(契约 `ctx.v1`) |

`--capacity` · `--inventory` · `--need` · `--scales` 不在这里 — 已移到 `ctx-plan`。

### `--request` 与 `--json`

```bash
ctx-burn --request ~/.cli-proxy-api/logs/error-v1-messages-*.log   # 连工具定义大小一起看
ctx-burn --hours 168 --json > /tmp/burn.json                      # 契约 ctx.v1
ctx-plan --from /tmp/burn.json --capacity --accounts 5x:5,ultra:5
```

`--request` 接受任何含 JSON 请求体的文件(也识别 `=== REQUEST BODY ===` 标记)。不用代理可以跳过,其他段独立工作。`--json` 的 `plan_input` 是 `schema: ctx.v1` 契约(`window_hours` · `pools{…}` · `rate_claude`)。`ctx-plan` 拒绝其他 schema。

### ctx-time

`ctx-burn` 测量 **付出了多少**;`ctx-time` 测量墙钟时间 **花在了什么上**。它读取同样的本地会话日志(pi · codex),在终端和一个 html 文件里给出类别 · 超时的命令 · 时间去向。

```bash
ctx-time                                   # 最近 3 小时 · 最多 40 个会话 · 80MB · html
ctx-time --seat 'my-team-' --role arch --hours 14
ctx-time --split '2026-11-23 15:13:38'     # 某一时刻之前 / 之后
ctx-burn --time --role nano                # 通过 ctx-burn 调用同一本体
```

| 选项 | 默认值 | 含义 |
|---|---|---|
| `--seat REGEX` · `--role NAME` | 全部 | 席位(会话)名模式 · 名称中的 `-<role>-` 段 |
| `--hours N` | 3 | 时间窗口(同时作用于文件 mtime 和行 timestamp) |
| `--max-sessions N` · `--max-mb N` · `--max-scan N` | 40 · 80 · 3000 | 采样上限(0 = 不限)。每次截断都会打印一行,不会悄悄删减 |
| `--from` · `--to` · `--split` | — | epoch 或 `YYYY-MM-DD HH:MM[:SS]`(本地时间) |
| `--runtime pi\|codex\|all` | all | |
| `--limit N` | 70 | "超时"阈值(秒) |
| `--out DIR` | `~/.cache/ctx-burn/time` | html 目录 |
| `--no-html` · `--json` · `--lang en\|ko` | — | 关闭 html · 在 stdout 输出契约 `ctx-time.v1` · 语言 |

pi 全面覆盖,codex 覆盖命令和轮次时间。claude 没有逐次调用的耗时,显示为"省略"。

### ctx-window

`ctx-window` 用 pi 会话日志里的 4 个数字,显示对话窗口 **用在了哪里**(先终端,后一个 html 文件)。codex · claude · hermes 显示为跳过。

```bash
ctx-window                                 # 最近 3 小时 · 40 个会话 · 40MB · html
ctx-window --seat 'my-team-' --role arch --hours 14
ctx-window --split '2026-11-23 15:13:38'   # 某一时刻之前 / 之后
ctx-burn --window --lang ko                # 通过 ctx-burn 调用同一本体
```

| 数字 | 含义 |
|---|---|
| **W1** 通知轮占比 | 前一条输入是 `custom_message` 或任务指令的轮次的加权成本 ÷ 启动后所有轮次的加权成本 |
| **W2** 启动窗口 | 启动结束那一轮的窗口 − 第一轮,以及其间的工具调用 |
| **W3** 越过闸门之后 | 从窗口首次越过 `--recv-gate` 的那一轮到最后一轮的增长(越过的会话数 · 中位数 · 最大值) |
| **W4** 工具结果大小 | 结果数 · 字节 · 超过 `--result-cap` 的结果 · 截断提示 · 重读比例 |

选项与 `ctx-time` 相同(`--max-mb` 默认 40),另有 `--recv-gate N`(默认 280000 token) · `--result-cap N`(默认 2048 字节) · `--out DIR`(默认 `~/.cache/ctx-burn/window`) · `--json`(契约 `ctx-window.v1`)。行按自身的 `timestamp` 截取(包含 from · 不含 to)。

### ctx-share

`ctx-burn` 测量"用了多少",`ctx-share` 则把"其中协调占多少"和"占周上限的百分之几"写在一张看板上。

```bash
ctx-share                                   # 测量 48 小时窗口并写入看板目录
ctx-share --hours 24 --json                 # 机器可读(不写看板)
ctx-share --now 2026-11-17T13:00:00 --force # 测试 · 重新测量
```

- 协调 / 实现按会话名 `<project>-<team>-<role>[-<tail>]#<N>` 的第三段(角色)区分。没有名字或不符合语法的单独计为"无法归类"。
- 周 % = 窗口内 claude 加权总量换算到一周,再与 `accounts.env` 中的常量(`FT_CAP_WK_5X` · `FT_CAP_WK_ULTRA` · `FT_CAP_TARGET_UTIL`)比较。任一常量为空则不输出 %。
- 在 `--out` 目录写入 `board.md`(给人看) · `last.json`(给机器读) · `samples.tsv`。30 分钟内已测过则跳过并返回 rc 0(`--force` 立即测量)。rc 1 = 无法判定。
- 选项:`--hours N`(48) · `--now ISO` · `--sessions-dir` · `--resume-dir` · `--inv-file` · `--acct-file` · `--out` · `--json` · `--force`。

### 发现问题后怎么改

| 优先级 | 做什么 | 怎么做 |
|---|---|---|
| 1 | 关掉不用的内置工具 | `settings.json` → `env`: `CLAUDE_CODE_DISABLE_ARTIFACT=1`, `CLAUDE_CODE_DISABLE_WORKFLOWS=1` |
| 2 | 精简自动加载规则 | 大文件移到 `~/.claude/guides/`,`rules/` 里只留 1KB 摘要 |
| 3 | 降低蒸馏阈值 | 降到盈亏平衡轮数,通常是平均上下文的 50% |
| 4 | 限制续接上下文 | 交接摘要 + 最后几轮,而不是 500k 的对话 |
| 5 | 错开会话启动 | 不要让 cron · tick 一群在同一分钟启动(jitter) |

### 安全

- **只读。** 不写设置和文件,不发网络请求(`ctx-time` · `ctx-window` 在 `--out` 下写一个 html 文件,`ctx-share` 只写入看板目录)。
- 会话日志留在本地。只读 token 计数器,不读对话正文。
- `ctx-time` · `ctx-window` 只输出数字 · 时间戳 · 固定词 · 席位名 · 会话路径。命令行和错误信息只用来选类别,不会打印。
- 权重(读取 0.1 · 写入 2.0 · 输出 5)按公开价格比例取的 **近似值**。真实的限额公式并未公开,请把数字用于 **相对比较**。

## 环境要求

- python3 3.8+ · 仅标准库(无需 pip 安装)
- macOS · Linux
- 无需 API 密钥 · 账号 · 网络
- 可选:要看工具定义大小,需要含请求体的代理日志(例如 CLIProxyAPI)
- 可选:`ctx-share` 的周 % 需要 `accounts.env` 常量(样例在 `ctx-plan`)

## 链接

- [INSTALL.md](INSTALL.md) — 安装 · 验证 · 卸载 · 故障排查
- [ctx-plan](../ctx-plan/README.zh-CN.md) — 读取 `ctx.v1` 的姊妹工具(承载量 · 所需订阅数)
- [AI Feature Pack 目录](../../README.zh-CN.md)
