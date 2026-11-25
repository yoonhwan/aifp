<div align="center">

# tts-say

**A TTS CLI that puts macOS `say` and ElevenLabs `sag` behind one command, `tts-say`**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Reads text aloud (`tts-say "text"`) · also takes a stdin pipe (`echo "text" | tts-say`).
- Saves audio to a file (`tts-say speak -o out.mp3 "text"`).
- Picks the engine for you — `sag` when `ELEVENLABS_API_KEY` is set, otherwise macOS `say`.
- Stores your default engine, voice and options in a config file and applies them every time.
- Lists the voices of each engine (`tts-say voices`).
- Voice notifications for agents and scripts: `pytest && tts-say "tests passed"`.

## Quick start

```bash
# from the pack folder: copy the CLI to PATH
cp skill/scripts/tts-say ~/.local/bin/tts-say
chmod +x ~/.local/bin/tts-say

# first sound (reads with macOS say when sag is not installed)
tts-say "Build finished"
```

## Install

### Let your agent do it

Tell your agent: "Read `feature-pack/tts-say/INSTALL.md` and install it." The agent installs `sag` (optional) → sets the ElevenLabs API key (optional) → copies the CLI → writes the default config → installs the skill → verifies, and asks you for the API key, install path and default voice. Install time (~3 min).

### Manual install

```bash
# 1. install sag (optional · high-quality ElevenLabs voices)
brew install steipete/tap/sag
export ELEVENLABS_API_KEY="<your-key>"   # put this in ~/.zshrc

# 2. copy the CLI to PATH (from the pack folder)
cp skill/scripts/tts-say ~/.local/bin/tts-say
chmod +x ~/.local/bin/tts-say

# 3. default config
tts-say config set default_engine auto
tts-say config set say.voice Yuna
tts-say config set sag.model_id eleven_multilingual_v2
tts-say config set sag.lang ko

# 4. install the skill (OpenClaw workspace)
cp -r skill/ ~/.openclaw/workspace/skills/tts-say/

# 5. verify
tts-say --help
tts-say config show
tts-say voices --engine say
```

- If you use OpenClaw, append `config/tools-section.md` to the workspace `TOOLS.md` (optional).
- If `~/.local/bin` is not on your PATH, add it with `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc`.

Values that `INSTALL.md` asks for, with defaults:

| Placeholder | Meaning | Default |
|---|---|---|
| `{{ELEVENLABS_API_KEY}}` | ElevenLabs API key (without it, only `say` is used) | none |
| `{{TTS_INSTALL_PATH}}` | CLI install path | `~/.local/bin/tts-say` |
| `{{DEFAULT_ENGINE}}` | default engine | `auto` |
| `{{SAG_DEFAULT_VOICE}}` | default `sag` voice | pick from `tts-say voices --engine sag` |
| `{{OPENCLAW_SKILLS_PATH}}` | skill install path | `~/.openclaw/workspace/skills` |
| `{{OPENCLAW_WORKSPACE}}` | workspace path | `~/.openclaw/workspace` |

## Usage

```bash
# speak (uses config defaults)
tts-say "Build finished"

# pick the engine
tts-say speak --engine say --voice Yuna "Hello"
tts-say speak --engine sag --voice Aria --lang ko "Hello"

# save to a file
tts-say speak -o /tmp/alert.mp3 "Alert"

# list voices
tts-say voices --engine say
tts-say voices --engine sag --search korean --limit 10

# config
tts-say config show
tts-say config set sag.speed 1.1
tts-say config unset say.rate
tts-say config example-env
tts-say config path

# build / test notification
npm run build && tts-say "Build OK" || tts-say "Build failed"
```

### Subcommands

| Command | What it does |
|---|---|
| `tts-say "text"` · `tts-say speak [options] "text"` | speak · save to a file |
| `tts-say voices [--engine say\|sag] [--search X] [--limit N]` | list voices (without `--engine`: both engines that are available) |
| `tts-say config {show\|set\|unset\|example-env\|path}` | manage the config (`~/.config/tts-say/config.json`) |

### `speak` options

| Option | Engine | Meaning |
|---|---|---|
| `--engine {auto,say,sag}` | both | force an engine |
| `--voice`, `-v` | both | voice name or ID |
| `--output`, `-o` | both | save audio to a file |
| `--say-rate` | say | words per minute |
| `--model-id` | sag | ElevenLabs model |
| `--lang` | sag | language code (ko, en …) |
| `--speed` | sag | speed multiplier |
| `--stability` | sag | voice stability 0–1 |
| `--style` | sag | style exaggeration 0–1 |
| `--similarity` | sag | voice similarity 0–1 |
| `--speaker-boost` | sag | clarity boost |
| `--no-play` | sag | do not play (file only) |

Options that do not match the engine are ignored silently.

### How the engine and options are chosen

- Engine: the `--engine` option → `default_engine` in the config → auto (`sag` when the API key is set, otherwise `say`).
- Options: command arguments → config defaults (`tts-say config set …`) → the engine's built-in defaults.
- Edit the config with dot paths: `tts-say config set sag.stability 0.6`.
- Models, pronunciation tips, v3 audio tags (`[whispers]` and others) and voice search are in [skill/references/engines.md](skill/references/engines.md).

### Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `tts-say: command not found` | not on PATH | check `echo $PATH`, add `~/.local/bin` |
| `sag: command not found` | `sag` not installed | `brew install steipete/tap/sag` |
| `ELEVENLABS_API_KEY not set` | environment variable missing | add the export to `~/.zshrc`, then `source ~/.zshrc` |
| `voice "X" not found` | wrong voice name | check with `tts-say voices --engine sag` |
| no Korean speech from `say` | voice not installed | download a Korean voice in System Settings > Accessibility > Spoken Content |

## Requirements

- macOS (`say` is built in)
- Python 3.10+
- Optional: `sag` (`brew install steipete/tap/sag`) + an ElevenLabs API key (`ELEVENLABS_API_KEY`) — without them it works with `say` alone.

## Links

- [INSTALL.md](INSTALL.md) — install guide for the agent
- [skill/SKILL.md](skill/SKILL.md) — agent skill
- [skill/references/engines.md](skill/references/engines.md) — per-engine options and models
- [cli/install.md](cli/install.md) — install the CLI only
- [AI Feature Pack catalog](../../README.md)
