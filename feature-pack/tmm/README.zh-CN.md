<div align="center">

# tmm

**在手机上(SSH)挑选、免 attach 预览几十个 tmux 智能体席位并给它们发消息的单屏 TUI**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 每个 tmux 会话显示为一行席位 — 分类 · 是否有智能体在跑 · 状态 · 模型 · 最后消息时间 · 经过时间 · 目录。用模糊过滤缩小范围。
- 把等待你输入的席位(`HUMAN` · `BLOCK` · `STUCK`)放到最上面,出现新的时响终端铃。
- 不 attach 就能预览 pane。`Enter` attach,`C-a d` 分离后回到选择器。
- `^S` 给光标所在席位发消息并确认送达 · `^K` 关闭席位。
- `^D` 已结束会话视图: 从 transcript 中找回因重启或 kill 消失的智能体会话,并用 resume 恢复。
- `^F` fork 把对话交给另一个智能体继续,`^Y` 显示对话记录(transcript)路径。

为 `tmuxc` 启动的 Claude Code · Codex · OMX · OpenCode · Command Code · Pi 席位设计,普通 tmux 会话也能直接用。

## 快速开始

```bash
brew install bash tmux fzf               # 如果没有 (需要 bash 4 以上)
bash feature-pack/tmuxc/install.sh       # 先装必需的 tmuxc 包
bash feature-pack/tmm/install.sh
tmm doctor                               # 检查依赖和环境
tmm                                      # 打开 TUI
```

## 安装

### 交给智能体

对智能体说:"读 `feature-pack/tmm/INSTALL.md` 并安装。"智能体会依次检查前置条件 → 运行 `install.sh` → 设置分类规则 → 验证 → (可选) fork 模型别名 · 手机连接。安装时间 (约1分钟)。

### 手动安装

`install.sh` 做的事:

1. 检查 `bash>=4` · `tmux` · `fzf`(缺少时 exit 2 并提示安装命令)。没有 `tmuxc` 则中止。
2. 把主程序和 libexec 复制到 `~/.tmm/versions/<version>/core/`,更新 `~/.tmm/current` 符号链接。
3. 创建 `~/.local/bin/tmm` 符号链接(已有普通文件会先备份),`~/.local/bin` 不在 PATH 中时写入 `~/.zshrc` / `~/.bashrc`。
4. `~/.zshrc` 里有 `alias tmm=` 时发出警告(alias 会盖住二进制)。
5. `~/.tmm/categories` · `~/.tmm/models` 不存在时复制示例(已存在则保留),并创建 `~/.tmm/forks/`。
6. 用 `tmm doctor` 验证。

```bash
bash feature-pack/tmm/install.sh
tmm doctor
tmm ls | head                          # 状态列显示 ? 时检查 seat-scan 路径 → TMM_SCAN
bash feature-pack/tmm/test/verify.sh   # 在隔离的 tmux socket 上做回归测试 (不碰现有会话)
bash feature-pack/tmm/uninstall.sh     # 卸载 (保留 ~/.tmm/categories)
```

### 分类规则

在 `~/.tmm/categories` 中每行写一条 `glob<TAB>标签`,从上往下第一个匹配生效。没有匹配任何规则的会话,会去掉角色前缀(`TMM_CAT_STRIP`,默认 `FB_ ft-`)后取名字的第一个词(`-` / `_` 之前的 5 个字符)作为标签,所以规则文件里只需写这条规则做不到的事(合并别名 · 统一大小写)。名字只由小写字母 · 数字 · `-` 组成、形如 `<项目>-<团队>-<角色>…` 且第三个词是保留的角色词(master · arch · da · tester · checker · analyst · pm · nano · repro · tool)时,第二个词(团队)就是标签。

```bash
tmux ls -F '#S' | sed 's/#[0-9]*$//' | sort -u     # 查看当前会话前缀列表
```

### 手机连接 (以 Termius 为例)

1. Mac: 系统设置 → 通用 → 共享 → 打开远程登录。
2. 生成专用密钥,把公钥加入 `~/.ssh/authorized_keys`,私钥存进密码管理器,再粘贴到手机 Termius 的 Keychain。
3. 地址: 同一 Wi-Fi 用 `ipconfig getifaddr en0`,在外面用 `tailscale ip -4`(推荐 Tailscale)。
4. Termius 主机: 地址 · 端口 22 · 用户 · 密钥 · **Startup command = `tmm`** — 一连上就打开选择器。
5. 用手机键盘工具栏上的 Ctrl 按 `^S` 等键。tmux prefix 为 `C-a` 时,按 Ctrl → a → d 分离。

```bash
ssh-keygen -t ed25519 -f ~/.ssh/mobile_ed25519 -N ''
cat ~/.ssh/mobile_ed25519.pub >> ~/.ssh/authorized_keys
# 在桌面上自测 — 非交互 ssh 的 PATH 很短,所以用 zsh -ilc 包起来
ssh -i ~/.ssh/mobile_ed25519 -o IdentitiesOnly=yes <IP> -t 'zsh -ilc tmm'
```

## 用法

### 一行 = 一个席位

| 列 | 含义 |
|---|---|
| 分类 | 来自 `~/.tmm/categories` 规则,没有则取去掉角色前缀后会话名的第一个词 |
| `●` / `○` | 智能体在运行 / 只有 shell |
| 会话名 | tmux 会话名。随宽度 20–44 格 · 截断时折叠中间,保留末尾的 `#N` |
| `HUMAN` `BLOCK` `STUCK` `IDLE` `BUSY` | seat-scan 判定。HUMAN = 等你输入,BLOCK = 因 API 错误停住,STUCK = 有未提交的输入残留 |
| 模型 | 所用模型的简称(例: `opus5·1m`)。`·1m` = 1M 上下文窗口 |
| `12:33` / `12~33` | 最后消息时间。`:` = 从 Claude 完成标记读取,`~` = 没有标记,取 tmux 最后输出时间 |
| `26m` | 距今经过 (m / h / d) |
| 目录 | pane cwd 的最后一级目录。随宽度 6–28 格 |

排序: `^T` 最近优先(默认 — 最后说话的席位在最上面) · `^W` 等待中的席位置顶后按最近 · `^G` 分类内按最近 · `^H` 只看等待中的席位。

### 按键

| 按键 | 动作 |
|---|---|
| ↑↓ / 输入文字 | 移动光标 / 模糊过滤 (`HUMAN`、会话名的一部分 …) |
| `Enter`(分类栏) · `Esc` / `⌫`(列表,查询为空时) | 切换栏 — 分类栏 ↔ 列表。`→` / `←` 效果相同 |
| `Enter`, `^E`, 双击 | attach。`C-a d` 分离后回到选择器 |
| `^S` | 给光标所在席位发消息 — 加 `[mobile→会话名] …` 前缀 + 2 秒后确认送达。没有智能体的席位会被拦下 |
| `^K` | 关闭席位 (tmux 会话 + 其中的智能体) |
| `^F` | fork — 在新的智能体会话中接着对话 |
| `^Y` | 对话记录索引 — 显示光标所在会话的 transcript 路径 |
| `^H` / `^A` | 只看等待中的席位 / 全部 |
| `^T` / `^W` / `^G` | 最近优先 / 等待优先 / 按分类 |
| `^V` | 隐藏 / 显示分类栏 (隐藏后变成标签栏 — 用 `Tab` / `S-Tab` 切换) |
| `^R` | 重新扫描状态 (忽略缓存 · 保留排序和过滤) |
| `^U` | 预览自动刷新间隔在 1 → 5 → 10 → 15 秒之间循环 |
| `^P` / `^O` | 预览 关 · 开 / 放大 · 缩小 |
| `^D` / `^A` | 已结束会话视图 ↔ 存活席位视图 |
| `^/` | 重画帮助(标题区)。`?` 只是过滤字符 |
| `^X` | 退出 |

### 分屏

- 在 tmux 内,左边是分类栏,右边是会话列表(+ pane 预览)。在分类栏里按 ↑↓,右边列表立刻切换。
- 不带参数运行 `tmm` 时,选择器会在名为 `tmm` 的 tmux 会话中打开 — 调整终端窗口大小也不会让它退出。打开多个窗口时,每个窗口各有自己的选择器(`tmm`, `tmm-2` …)。
- 宽度不足 120 列(手机)时分类栏 11 格,否则 16 格。列表栏达到 120 列时预览在右边,否则在下面。
- 预览先显示最新内容,并裁掉底部的输入框和 statusline,省出手机屏幕。
- `TMM_SPLIT=0` 或在 tmux 外时,使用标签栏布局。

### 已结束会话视图 (`^D`)

列表切换为当前已不在 tmux 中的智能体会话。不论是用 `tmuxc` 启动的还是直接在终端里运行的,只要 transcript 还在就能找到。

| 按键 · 标记 | 含义 |
|---|---|
| `◌` | 已结束 |
| 徽标 | 在哪里找到的: `SNAP` = `tmuxc save` 快照(保存时的 argv 原样) · `CC` Claude · `CDX` Codex · `CMD` Command Code · `OC` OpenCode |
| `^]` / `^\` | 时间窗口每次扩大 / 缩小 12 小时 (初始为最近 12 小时 · 按 transcript 的 mtime 判断) |
| `^L` | 显示同一谱系的所有代 (默认只显示最新一代) |
| `^T` / `^W` / `^G` | 最近优先 / SNAP 优先 / 按分类 |
| `Enter` | 恢复 — 在原 cwd 创建 tmux 会话,用 `--resume <session_id>` 重新启动智能体并 attach |
| `^B` | 选择恢复模式 — 进入时所有可见行都已勾选,用空格切换勾选,再按一次 `^B` 只恢复勾选的 (每批 5 个并行 · 不 attach) |

- 预览显示该会话最后一条 user / assistant 消息。
- 恢复所用模型: SNAP 时用快照 argv 原样,否则用 transcript 的 `model` + `--effort high`。Claude 不是 fable 系列时加上 1M 窗口(`[1m]`)。
- Pi 会话在有 `tmuxc save` 快照时恢复。`--scan` 只支持 Claude · Codex。
- 此视图中不能用 `^S`(消息)。请先恢复。

### fork (`^F` · `tmm fork`)

把存活或已结束会话的对话转到另一个智能体 · 模型上继续(例如遇到速率限制时)。原对话不会被改动。

- 同一引擎 = `tmuxc fork` 原生分支 — 完整历史保留,新的 conversation id。
- 不同引擎 = `tmuxc open` 新会话 + 上下文注入 — 把 transcript 路径和最近对话摘录(`~/.tmm/forks/<时间>-<来源>.md`)作为提示词交给它。
- 在 `^F` 中选好名字 · 智能体(claude / codex / opencode / cmd) · 模型(fzf 搜索)后,创建完成并回到选择器。默认名字把来源的 `#N` 改成 `#N+1`。任何一步都可用 `^C` 取消。
- 模型别名 = `~/.tmm/models`(用户的 · 优先) + `~/.tmm/models.generated`(`tmm models refresh` 生成)。OpenCode 的 `--model` 前缀就是网关,由 `TMM_MODELS_PROVIDER`(默认 `openrouter`)选择 — `opencode/` = zen,`openrouter/` = OpenRouter。
- Claude 不是 fable 系列时自动加 `--ctx 1m`。

```bash
# --dry-run 只打印命令 (无副作用)
tmm fork my-app-dev#1 --agent codex --model <alias> --dry-run
tmm fork my-app-dev#1 --agent claude --model sonnet --attach     # 同引擎原生 fork
tmm models refresh                                    # 在线列表 → ~/.tmm/models.generated
TMM_MODELS_PROVIDER=opencode tmm models refresh opencode
tmm models find <query>                               # 搜索别名 · 模型 id
```

### 对话记录索引 (`^Y` · `tmm idx`)

- `^Y` 在屏幕上显示光标所在会话的 `agent · session_id · cwd · transcript · match`(按任意键返回)。用来直接告诉智能体"之前的对话在这个文件里"。
- `tmm idx NAME|SID` 在 CLI 中输出同样的信息 · `--path` = 只输出路径 · `--json` = JSON。
- `match`: `exact`(名字精确匹配) · `cwd`(按 cwd) · `fallback`(存活会话最近活跃的文件)。

### 自动刷新

| 层 | 内容 | 默认间隔 |
|---|---|---|
| pane | 只重画光标所在席位的预览 | 1 秒 (`^U` 在 1/5/10/15 之间切换 · `TMM_AUTO_PREVIEW`) |
| 全部席位 | 重新计算状态 · 最后时间 · 排序 | 固定 20 秒 (`TMM_AUTO`) |

attach 期间暂停,`C-a d` 分离后恢复。刷新后光标仍跟着你在看的席位,过滤条件也保留。

### CLI 子命令

```bash
tmm                 # TUI
tmm --auto N        # TUI,预览每 N 秒自动刷新 (0=off)
tmm ls [PAT]        # 文本列表 (过滤)
tmm h               # 只看 HUMAN/BLOCK/STUCK 席位
tmm p NAME [N]      # pane 最近 N 行
tmm s NAME "msg"    # 发消息 (防护 + 送达确认)
tmm a NAME [-i]     # attach (-i: 固定桌面窗口大小)
tmm kill NAME [--yes]                 # 关闭席位
tmm ss              # seat-scan 原始输出
tmm save            # tmuxc save (需要 tmuxc)
tmm doctor          # 检查依赖和环境
tmm menu            # 没有 fzf 时的数字菜单
tmm dead [PAT] [--since H] [--all]    # 已结束会话列表
tmm dp NAME|SID [N]                   # 已结束会话最后 N 行对话
tmm restore NAME [--dry-run]          # 恢复 1 个已结束会话 → attach
tmm restore-all [--since H] [--dry-run] [--yes]   # 恢复时间窗口内全部 (不 attach)
tmm idx NAME|SID [--json|--path]      # transcript 路径
tmm fork SRC --agent AG --model M [--name N] [--cwd C] [--effort E] [--ctx 1m] [--prompt P] [--dry-run] [--attach]
tmm models [AG]                       # fork 模型别名列表
tmm models refresh [AG...]            # 从在线列表更新生成文件
tmm models find QUERY                 # 搜索别名 · 模型 id
```

### 设置

| 项目 | 位置 / 变量 | 默认 |
|---|---|---|
| 分类规则 | `~/.tmm/categories` (`TMM_CATEGORIES`) | 安装时复制示例 |
| 分类角色前缀 | `TMM_CAT_STRIP` | `FB_ ft-` (空格分隔) |
| fork 模型别名 | `~/.tmm/models` (`TMM_MODELS`) | 安装时复制示例 · 优先于生成文件 |
| fork 模型生成文件 | `~/.tmm/models.generated` (`TMM_MODELS_GEN`) | 由 `tmm models refresh` 生成 · 不要手改 |
| OpenCode provider | `TMM_MODELS_PROVIDER` | `openrouter` |
| fork 摘录目录 / 消息数 | `~/.tmm/forks/` (`TMM_FORKS`) / `TMM_FORK_EXCERPT_N` | 40 |
| 状态扫描缓存 | `TMM_CACHE_TTL` | 20 秒 (`^R` 忽略缓存) |
| seat-scan 路径 | `TMM_SCAN` | 安装版 `libexec/seat-scan.sh` → `~/.claude/skills/tmuxc/scripts/seat-scan.sh` |
| 预览行数 | `TMM_PREVIEW_LINES` | 40 |
| pane 自动刷新 | `TMM_AUTO_PREVIEW` / `tmm --auto N` / `^U` | 1 秒 · 0 = off |
| 全部席位自动刷新 | `TMM_AUTO` | 20 秒 · 0 = off |
| 新等待席位响铃 | `TMM_BELL` | 1 (0 = 关) |
| 启动画面 | `TMM_TAB` | 1 = 标签视图 · 0 = 列表 |
| 分屏 | `TMM_SPLIT` | 1 (仅在 tmux 内) · 0 = 标签栏 |
| 已结束视图初始窗口 | `TMM_DEAD_SINCE` | 12 (小时) |
| 存活判定余量 | `TMM_LIVE_GRACE` | 90 秒 — 在此时间内写过的 transcript 视为存活 |
| 恢复启动等待 | `TMM_RESTORE_TRIES` | 20 (× 3 秒) |
| 选择恢复批大小 | `TMM_RESTORE_BATCH` | 5 |

### 已知限制 · 故障排查

- 完成标记只有时:分,没有日期。放置超过两天的席位,经过时间可能显示偏小。
- fzf 不会给标题区换行而是直接截断,所以在窄屏手机上标题区后半部分可能看不到。

| 症状 | 处理 |
|---|---|
| 自动刷新不工作 · `^Y` 没反应 | 用 `tmm doctor` 检查 fzf 版本(≥ 0.54)和 `curl` |
| 同引擎 fork 却没有带上历史 | `tmuxc` < 0.4.0 — 重新安装 `tmuxc` |
| fork 模型菜单为空或没有想要的模型 | 重跑 `install.sh`(复制示例)或 `tmm models refresh` → `tmm models find QUERY` |
| OpenCode fork 走了别的网关 | 检查别名前缀 · `TMM_MODELS_PROVIDER=openrouter tmm models refresh` |
| `tmm idx NAME` 显示"没有索引" | 查看 `tmm idx NAME --json` 中的 `match` |
| 恢复后提示"未能确认启动" | 会话仍在 — attach 进去看 pane |

## 环境要求

- macOS 或 Linux
- `bash` ≥ 4 (macOS 自带的 3.2 不行 → `brew install bash`) · `tmux` ≥ 3.2 · `fzf` ≥ 0.54 · `python3` ≥ 3.9 (只用标准库) · `curl`
- `tmuxc` ≥ 0.4.0 (`feature-pack/tmuxc`) — 没有时 `install.sh` 会停止。
- 可选: Tailscale(从外部访问) · 手机上的 SSH 客户端(例: Termius)
- API 密钥 / 账号: 无

## 链接

- [INSTALL.md](INSTALL.md) — 面向智能体的安装说明
- [tmuxc 包](../tmuxc/) — 必需的包
- [test/verify.sh](test/verify.sh) — 回归测试
- [AI Feature Pack 目录](../../README.zh-CN.md)
