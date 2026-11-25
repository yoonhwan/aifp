<div align="center">

# ctx-plan

**承载量工具:由账号组合算出席位 · 峰值会话 · 目标吞吐量,并为目标规模反推所需订阅数**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 姊妹工具 `ctx-burn` 测量"用了多少",`ctx-plan` 模拟"能承载多少"。两者 **只通过一个 JSON 契约(`ctx.v1`)** 连接。
- `--capacity`:由账号组合(`--accounts 5x:N,ultra:N`)输出 pool 表 · 4 行模拟 · 2 行目标模型。
- `--inventory`:检查 19 个 0 级固定常量(订阅数 · 周限额等),输出"0 级问题 N 项" · 所需账号反推 · 基准线 A。
- `--need K:N`:由目标规模(并发会话 · 会话 · 团队 · 并发目标)反推所需 Ultra / 5x 数量。
- `--scales`:按一组减少浪费的倍率重新计算。
- 不读会话日志,也不读真实 HOME。输入只有 `ctx-burn --json` 的输出和一个常量文件 · 不写入 · 不联网。

## 快速开始

```bash
git clone https://github.com/yoonhwan/aifp.git
cd aifp/feature-pack/ctx-plan
bash install.sh                                 # ~/.local/bin/ctx-plan

cp accounts.env.example /tmp/accounts.env       # 常量文件 — 每台机器各自填值
ctx-burn --hours 168 --json > /tmp/burn.json    # 需要 ctx-burn 包

CTX_PLAN_CAP_FILE=/tmp/accounts.env ctx-plan --from /tmp/burn.json --inventory   # 检查 0 级常量
ctx-plan --from /tmp/burn.json --inv-file /tmp/accounts.env --capacity --accounts 5x:5,ultra:5
ctx-plan --from /tmp/burn.json --inv-file /tmp/accounts.env --need concurrent:40
```

## 安装

### 交给智能体

本包没有 `INSTALL.md`。对智能体说 "Read feature-pack/ctx-plan/README.md and install it",它就能按下面的手动安装步骤进行。常量文件的值由人来填。

### 手动安装

`install.sh` 只建一个符号链接 `~/.local/bin/ctx-plan`。它不决定常量文件放在哪里 — 由调用方通过 `--inv-file` 或 `CTX_PLAN_CAP_FILE` 传入。

```bash
bash install.sh                                 # ~/.local/bin/ctx-plan
CTX_PLAN_BIN_DIR="$HOME/bin" bash install.sh    # 更换安装目录
cp accounts.env.example /path/to/accounts.env   # 样例 — 值为空,不填会以"0 级问题"停止
bash uninstall.sh                               # 卸载 — 只删符号链接
```

## 用法

### 模式

| 模式 | 输出 |
|---|---|
| (无) | 表头 3 行 — 契约 · 轴定义 · 常量文件路径 + 一行 pool |
| `--inventory` | 检查 19 个 0 级常量 · "0 级问题 N 项" · 2 行目标模型(并发目标 · 目标/周 · 空闲/不足团队) · 所需账号反推 · 基准线 A |
| `--capacity` | pool 表(只列存在的 pool) · 4 行模拟 · 2 行目标模型 |
| `--need K:N` | `concurrent:N` · `sessions:N` · `teams:N` · `goals:N`(N 个并发目标) → 所需 Ultra / 5x 数量 · `goals` 还会输出所需账号块 · N 超过 `FT_GOAL_PARALLEL_MAX` 时不削减,只给一行提示(rc 0) |
| `--scales 1.0,0.9,…` | 减少浪费的倍率列表(默认 4 个值 = 实测 · -10% · -20% · -30%) |

### 选项

| 选项 | 默认值 | 含义 |
|---|---|---|
| `--from FILE\|-` | stdin | `ctx-burn --json` 的输出 |
| `--inv-file FILE` | (见下方顺序) | 固定常量文件 |
| `--accounts 5x:N,ultra:N` | 无 | `--capacity` 计算席位 · 峰值用的账号组合 |
| `--wk-5x N` / `--wk-ultra N` | 630 / 2520 | 周限额锚点(加权 M) — 文件里有值时以文件为准 |
| `--c5h-5x N` | 60 | 5x 的 5 小时窗口锚点 |
| `--target-util F` | 0.85 | 每周目标使用率(运营策略) |
| `--seats-per-team N` | 4 | 每个团队的会话数 |
| `--hours-per-week N` | 40 | 单个会话每周的小时数 |
| `--teams-per-goal N` | 3 | 同时投入一个目标的团队数 |
| `--team-hours-per-goal N` | 8 | 一个团队在一个目标上停留的小时数 |

### 常量文件

只查两个地方:① `--inv-file FILE` ② `$CTX_PLAN_CAP_FILE`。不会搜索上级目录,也不假定家目录里的某个路径。没有文件时不输出任何表,以 rc 3 + 一行(指向 `--inv-file` · `CTX_PLAN_CAP_FILE` · `install.sh`)结束。

- 输出表头打印读取的路径一行。19 个键 = 订阅 5 · 周限额 4(上限 · 下限) · 模型 5(含并发目标参考值) · 基准线 5。
- 值为空就是"0 级问题",**不会用默认值替代** — 需要它的表会显示"无法计算"。
- 只有两个非契约键的旋钮(`FT_CAP_C5H_5X` · `FT_CAP_HOURS_PER_WEEK`)使用默认值,并在屏幕上标明"默认值(非契约键)"。
- 样例 = [`accounts.env.example`](accounts.env.example)(值为空)。

### 目标模型(参考)

- 一个目标 = 3 个团队同时 × 8 小时 = 24 团队小时 = 96 会话小时 · 并发目标最多 3 个 · 目标/周 = min(可用会话小时 ÷ 96, 3 × 168 ÷ 8)。
- 数字取自常量(`FT_GOAL_PARALLEL_MAX` · `FT_GOAL_TEAMS` · `FT_GOAL_TEAM_HOURS` · `FT_CAP_SEATS_PER_TEAM`)。
- 这只是计算示例,不是运营规则,输出会带"参考 — 非运营规则"标签。超过数值也不会拒绝或削减,只给提示。
- 基准线 A(`FT_BASE_*` 5 个键):常设团队按每队 1 席 × 168h 计,议题 · 目标团队按白天小时 × 7 天 × 每队会话数计。`团队小时/周` 是中间单位,不用于评判成果。

### 坚持的规则

- **下限只有一处** — `FT_CAP_WK_5X_LOW` · `FT_CAP_WK_ULTRA_LOW`。不做"上限 ÷ 3"之类的替代计算,为空就写"无法计算"。
- **标签是"低容量假设 · 高容量假设"** — 不用"乐观 · 保守"(容量小并不保证就是保守的那个)。
- **锚点带状态**(未验证 · 估计 · 需要实测 · 运营策略等)。状态标记还在时,不要凭这个数字决定账号。
- **契约检查** — `plan_input.schema` 不是 `ctx.v1` 时不计算,以 rc 2 + 一行原因停止。
- **模型常量只在一处解析** — 顺序为 `CLI 指定 > 常量文件`,契约键两者都没有就是"无法计算"。来源(`CLI` · `文件` · `无` · `默认值(非契约键)`)打印在表头。
- **样本 0 = 未计算** — 不用 0 填充。rc 仍为 0。

### 输入契约 (ctx.v1)

`ctx-burn --json` 中的 `plan_input`:

```json
{"schema": "ctx.v1", "window_hours": 168,
 "units": {"rate_claude": "weighted_tokens_per_session_hour",
           "w_per_session_hour": "weighted_tokens_per_session_hour",
           "w_total": "weighted_tokens", "ctx_per_req": "tokens"},
 "pools": {"claude": {"req": 0, "usage0": 0, "ctx_per_req": 0.0, "active_hours": 0,
                      "cache_reuse": 0.0, "cache_reuse_of_input": 0.0,
                      "w_per_session_hour": null, "samples": 0, "sessions": 0, "w_total": 0}},
 "rate_claude": null}
```

- `rate_claude` = claude pool 的 **每会话小时加权 token 中位数**(样本 = 请求 20 次以上的会话)。换算为计算预算(M = 百万加权 token)的地方只有一行。`units` 字段让契约自己声明单位。
- `usage0` = 权重为 0 的记录(API 错误),不计入请求率的分母。`unknown` pool = 模型未知,不会并入其他 pool。

### 安全

- 读取:一个 `--from` JSON · 一个常量文件。此外为 0。
- 不写入 · 不联网 · 不直接读会话日志 · 不运行 `ctx-burn`(无 subprocess)。
- 常量文件 **只读**(没有 `--set`)。值由人来填。

## 环境要求

- python3 3.8+ · 仅标准库
- macOS · Linux
- 输入:`ctx-burn --json` 的输出([ctx-burn](../ctx-burn/README.zh-CN.md) 包)
- 已填值的常量文件(从 `accounts.env.example` 复制) · 无需 API 密钥 · 无需网络

## 链接

- [accounts.env.example](accounts.env.example) — 常量文件样例(值为空)
- [docs/plan-cost-table.md](docs/plan-cost-table.md) — Claude Opus 5.5 订阅套餐 vs API 成本(按天)表(韩语)
- [ctx-burn](../ctx-burn/README.zh-CN.md) — 输出 `ctx.v1` 的姊妹工具(测量用量)
- [AI Feature Pack 目录](../../README.zh-CN.md)
