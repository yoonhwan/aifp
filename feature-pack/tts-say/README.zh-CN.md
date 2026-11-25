<div align="center">

# tts-say

**把 macOS `say` 和 ElevenLabs `sag` 合并成一个命令 `tts-say` 的 TTS CLI**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 朗读文字(`tts-say "文字"`) · 也接受 stdin 管道(`echo "文字" | tts-say`)。
- 保存为音频文件(`tts-say speak -o out.mp3 "文字"`)。
- 自动选择引擎 — 设置了 `ELEVENLABS_API_KEY` 就用 `sag`,否则用 macOS `say`。
- 把默认引擎 · 声音 · 选项存进 config,每次自动套用。
- 列出各引擎的声音(`tts-say voices`)。
- 用于智能体和脚本的语音提醒: `pytest && tts-say "测试通过"`。

## 快速开始

```bash
# 在包目录下: 把 CLI 复制到 PATH
cp skill/scripts/tts-say ~/.local/bin/tts-say
chmod +x ~/.local/bin/tts-say

# 第一次发声 (没装 sag 时用 macOS say 朗读)
tts-say "Build finished"
```

## 安装

### 交给智能体

对智能体说:"读 `feature-pack/tts-say/INSTALL.md` 并安装。"智能体会依次安装 `sag`(可选) → 设置 ElevenLabs API 密钥(可选) → 复制 CLI → 写入默认 config → 安装技能 → 验证,并询问 API 密钥 · 安装路径 · 默认声音。安装时间 (约3分钟)。

### 手动安装

```bash
# 1. 安装 sag (可选 · ElevenLabs 高质量声音)
brew install steipete/tap/sag
export ELEVENLABS_API_KEY="<your-key>"   # 写进 ~/.zshrc

# 2. 把 CLI 复制到 PATH (在包目录下)
cp skill/scripts/tts-say ~/.local/bin/tts-say
chmod +x ~/.local/bin/tts-say

# 3. 默认 config
tts-say config set default_engine auto
tts-say config set say.voice Yuna
tts-say config set sag.model_id eleven_multilingual_v2
tts-say config set sag.lang ko

# 4. 安装技能 (OpenClaw 工作区)
cp -r skill/ ~/.openclaw/workspace/skills/tts-say/

# 5. 验证
tts-say --help
tts-say config show
tts-say voices --engine say
```

- 使用 OpenClaw 时,把 `config/tools-section.md` 的内容追加到工作区的 `TOOLS.md`(可选)。
- 如果 `~/.local/bin` 不在 PATH 中,用 `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc` 加进去。

`INSTALL.md` 会询问的值及默认值:

| 占位符 | 含义 | 默认值 |
|---|---|---|
| `{{ELEVENLABS_API_KEY}}` | ElevenLabs API 密钥(没有则只用 `say`) | 无 |
| `{{TTS_INSTALL_PATH}}` | CLI 安装路径 | `~/.local/bin/tts-say` |
| `{{DEFAULT_ENGINE}}` | 默认引擎 | `auto` |
| `{{SAG_DEFAULT_VOICE}}` | `sag` 默认声音 | 从 `tts-say voices --engine sag` 列表中选 |
| `{{OPENCLAW_SKILLS_PATH}}` | 技能安装路径 | `~/.openclaw/workspace/skills` |
| `{{OPENCLAW_WORKSPACE}}` | 工作区路径 | `~/.openclaw/workspace` |

## 用法

```bash
# 朗读 (使用 config 默认值)
tts-say "Build finished"

# 指定引擎
tts-say speak --engine say --voice Yuna "Hello"
tts-say speak --engine sag --voice Aria --lang ko "Hello"

# 保存为文件
tts-say speak -o /tmp/alert.mp3 "Alert"

# 声音列表
tts-say voices --engine say
tts-say voices --engine sag --search korean --limit 10

# config
tts-say config show
tts-say config set sag.speed 1.1
tts-say config unset say.rate
tts-say config example-env
tts-say config path

# 构建 · 测试提醒
npm run build && tts-say "Build OK" || tts-say "Build failed"
```

### 子命令

| 命令 | 作用 |
|---|---|
| `tts-say "text"` · `tts-say speak [选项] "text"` | 朗读 · 保存为文件 |
| `tts-say voices [--engine say\|sag] [--search X] [--limit N]` | 声音列表(不带 `--engine` 时列出可用的两个引擎) |
| `tts-say config {show\|set\|unset\|example-env\|path}` | 管理 config(`~/.config/tts-say/config.json`) |

### `speak` 选项

| 选项 | 引擎 | 含义 |
|---|---|---|
| `--engine {auto,say,sag}` | 两者 | 强制指定引擎 |
| `--voice`, `-v` | 两者 | 声音名称或 ID |
| `--output`, `-o` | 两者 | 把音频保存为文件 |
| `--say-rate` | say | 每分钟词数 |
| `--model-id` | sag | ElevenLabs 模型 |
| `--lang` | sag | 语言代码(ko, en …) |
| `--speed` | sag | 速度倍率 |
| `--stability` | sag | 声音稳定度 0–1 |
| `--style` | sag | 风格强度 0–1 |
| `--similarity` | sag | 声音相似度 0–1 |
| `--speaker-boost` | sag | 提升清晰度 |
| `--no-play` | sag | 不播放(只存文件) |

与引擎不匹配的选项会被静默忽略。

### 引擎和选项的决定顺序

- 引擎: `--engine` 选项 → config 中的 `default_engine` → 自动(有 API 密钥用 `sag`,否则用 `say`)。
- 选项: 命令参数 → config 默认值(`tts-say config set …`) → 引擎内置默认值。
- 用点号路径修改 config: `tts-say config set sag.stability 0.6`。
- 模型 · 发音技巧 · v3 音频标签(`[whispers]` 等) · 声音搜索见 [skill/references/engines.md](skill/references/engines.md)。

### 故障排查

| 症状 | 原因 | 解决 |
|---|---|---|
| `tts-say: command not found` | 不在 PATH 中 | 检查 `echo $PATH`,加入 `~/.local/bin` |
| `sag: command not found` | 未安装 `sag` | `brew install steipete/tap/sag` |
| `ELEVENLABS_API_KEY not set` | 缺少环境变量 | 在 `~/.zshrc` 加上 export 后 `source ~/.zshrc` |
| `voice "X" not found` | 声音名称错误 | 用 `tts-say voices --engine sag` 确认 |
| `say` 读不出韩语 | 未安装声音 | 在 系统设置 > 辅助功能 > 朗读内容 中下载韩语声音 |

## 环境要求

- macOS(内置 `say`)
- Python 3.10+
- 可选: `sag`(`brew install steipete/tap/sag`) + ElevenLabs API 密钥(`ELEVENLABS_API_KEY`) — 没有也能只用 `say` 工作。

## 链接

- [INSTALL.md](INSTALL.md) — 面向智能体的安装说明
- [skill/SKILL.md](skill/SKILL.md) — 智能体技能
- [skill/references/engines.md](skill/references/engines.md) — 各引擎的选项和模型
- [cli/install.md](cli/install.md) — 只安装 CLI
- [AI Feature Pack 目录](../../README.zh-CN.md)
