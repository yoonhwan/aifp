<div align="center">

# tmuxc

**Claude Code · Codex · OMX · OpenCode · Command Code · Pi 에이전트 세션을 tmux 에서 한 명령으로 열고 제어합니다.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- 프로젝트 폴더나 git worktree 에 Claude Code, Codex CLI, OMX, OpenCode, Command Code, Pi 세션을 `tmuxc open` 한 줄로 엽니다.
- 세션마다 역할(`worker` · `orchestrator` · `designer`)을 정해 열 수 있습니다.
- 다른 세션에 메시지를 보내고 화면을 읽습니다(`tmuxc send` · `tmuxc msg` · `tmuxc ask`). verified send / capture 방식으로 표준화되어 있습니다.
- 종료 전에 열린 세션을 스냅샷으로 저장하고, 재부팅 뒤 `tmuxc restore` 로 되살립니다.
- 부모 대화를 건드리지 않고 새 대화로 분기합니다(`tmuxc fork` · 엔진별 네이티브 fork).
- 세션 목록 · 종료 · 정리를 같은 CLI 로 합니다(`tmuxc list` · `kill` · `clean`).

## 빠른 시작

```bash
bash feature-pack/tmuxc/install.sh
tmuxc --help
tmuxc open "$PWD" --name TMUXC_SMOKE --agent codex --role worker --dry-run
```

## 설치

### 에이전트로 설치

에이전트에게 다음과 같이 요청하세요.

```text
feature-pack/tmuxc/INSTALL.md 를 읽고 설치해 줘
```

### 직접 설치

```bash
bash feature-pack/tmuxc/install.sh
```

`install.sh` 가 하는 일:

- `bash` · `git` · `tmux` 가 있는지 확인합니다.
- core 와 Claude Code skill 을 `~/.tmuxc/versions/<version>/` 에 복사하고 `~/.tmuxc/current` 심볼릭 링크를 갱신합니다.
- CLI 를 `~/.local/bin/tmuxc` 로 링크합니다. `~/.local/bin` 이 PATH 에 없으면 `~/.zshrc` 또는 `~/.bashrc` 에 등록합니다.
- Claude Code 가 있으면 `~/.claude/skills/tmuxc` 를 설치본으로 연결합니다.

### 설치 확인

```bash
tmuxc --help
tmuxc list
test -e "$HOME/.claude/skills/tmuxc/SKILL.md"
test -e "$HOME/.claude/skills/tmuxc/COMM-GUIDE.md"
```

### 제거

```bash
bash feature-pack/tmuxc/uninstall.sh
```

제거 스크립트는 `~/.tmuxc` 와 설치본을 가리키는 `~/.local/bin/tmuxc` · `~/.claude/skills/tmuxc` 링크만 지웁니다. 프로젝트 파일과 tmux 세션은 지우지 않습니다.

## 사용법

### 명령

```bash
tmuxc open <path> --name NAME --agent claude|codex|omx|opencode|cmd|pi --role worker|orchestrator|designer [--pi-skill PATH]...
tmuxc wt <worktree-path> --name NAME --prompt "NEXT.md 를 읽고 시작"
tmuxc list
tmuxc ask <name> [lines]              # 세션 화면의 마지막 줄을 읽기 (capture-pane)
tmuxc send <name> "message"           # 세션에 메시지 보내기
tmuxc msg <name> "message"
tmuxc kill <name>
tmuxc clean
tmuxc save [--keep N]                 # 종료 전 전역 세션 스냅샷 ([1m] · effort · session_id 보존)
tmuxc restore [--from latest] [--go]  # 재부팅 후 복원 (스냅샷 우선, --scan 으로 로그 스캔 강제)
tmuxc fork <path> --name NEW (--from LIVE_SESSION | --source ID --agent claude|codex|opencode|cmd|pi) [--model ID] [--ctx 1m] [--effort E] [--prompt TEXT]
```

- claude 가 아닌 좌석(pi · codex · opencode · cmd)은 `open` · `fork` 때 tmux 세션 env 에 `GIT_EDITOR=true` · `GIT_SEQUENCE_EDITOR=true` · `GIT_TERMINAL_PROMPT=0` 이 들어가, git 이 편집기나 입력을 기다리며 멈추지 않습니다. 이미 떠 있는 좌석에는 적용되지 않고 새 좌석부터 적용됩니다.

### Pi 좌석

```bash
tmuxc open . --name PI_WORKER --agent pi --role worker --model <provider/model>
tmuxc open . --name PI_REVIEW --agent pi --role orchestrator --effort high
```

- tmuxc 가 `--session-id <uuid>` 를 발급하고 세션 env(`TMUXC_PI_SESSION_ID` · `TMUXC_PI_MODEL` · `TMUXC_PI_THINKING`)에 심습니다. 프로세스 이름이 argv 를 숨겨도 `save` · `restore` 가 정확한 세션을 복구합니다.
- `worker` · `implementer` 는 `read,bash,edit,write,grep,find,ls` 도구를, `orchestrator` · `planner` · `analysis` 는 읽기 전용 도구를 받습니다.
- `--effort` 는 Pi 의 `--thinking` 으로 매핑됩니다.
- `--like <pi-session>` 으로 실행 중인 Pi 의 model · thinking 을 물려받을 수 있습니다.

Pi 좌석에 스킬을 골라 싣는 `--pi-skill`:

```bash
tmuxc open <path> --agent pi --pi-skill ~/.agents/skills/code-intel --pi-skill ~/.agents/skills/tmuxc --dry-run
```

- Pi 의 스킬 자동 발견을 끄고(`--no-skills`), 준 경로만 차례대로 싣습니다.
- 경로는 `SKILL.md` 파일이거나 `SKILL.md` 가 든 폴더입니다. 없으면 만들지 않고 rc≠0 으로 거부합니다.
- `--agent pi` 에서만 받습니다(다른 에이전트면 rc≠0). 옵션을 주지 않으면 명령은 이전과 같습니다.
- `tmuxc fork` · `tmuxc restore` 로 다시 뜨는 좌석에는 이 옵션이 적용되지 않습니다.

### Fork

| 엔진 | 인자 | 비고 |
|---|---|---|
| claude | `--resume <ID> --fork-session` | headroom 래퍼 경유, `[1m]` · effort 승계 |
| codex | `codex fork <ID>` | `-c model=` · `-c model_reasoning_effort=` 통과 |
| opencode | `--session <ID> --fork` | 모델은 세션 env `OPENCODE_CONFIG_CONTENT` 로 전달 |
| cmd | `--resume <ID> --fork-session` | `--model` · `--effort` |
| pi | `--fork <ID> --session-id <NEW>` | `--model` · `--thinking` |

- `--from <라이브 세션>`: 엔진 · 모델 · 대화 id 를 실행 중인 프로세스와 트랜스크립트에서 읽습니다. 같은 엔진끼리만 되고 다른 엔진으로는 못 갑니다.
- `--source <ID> --agent <엔진>`: id 를 직접 지정합니다. 엔진 저장소에 그 id 가 있는지 가능한 범위에서 확인합니다.
- `omx` 는 네이티브 fork 가 없어 대상이 아닙니다.

### 권장 흐름

```bash
# 1) baton handoff 가 있는 worktree 에서 세션을 연다
tmuxc open /path/to/project/.worktrees/my-task --name MY_TASK_ORCH --agent codex --role orchestrator --prompt "AGENTS.md, .baton/handoff/CURRENT.md, .baton/handoff/NEXT.md 를 읽고 시작"

# 2) cairn 에 task / session ref 를 남긴다
cairn link t7 --session-ref MY_TASK_ORCH --execution-ref "tmuxc:MY_TASK_ORCH"

# 3) 진행 상태는 list / ask 로 확인한다
tmuxc list
tmuxc ask MY_TASK_ORCH 80
```

### 함께 쓰는 도구

| 도구 | 역할 |
| --- | --- |
| `baton` | worktree, handoff, archive, memory |
| `cairn` | milestone / task 일정 ledger, session lineage |
| `tmuxc` | 살아 있는 tmux 에이전트 세션의 실행 · 제어 |

## 요구사항

- 필수: `bash` · `git` · `tmux` (macOS: `brew install tmux` · Ubuntu: `sudo apt install tmux`)
- 선택: 열고 싶은 에이전트의 CLI (`claude` · `codex` · `omx` 등)
- 선택: `baton` · `cairn` (함께 쓰는 도구 세트)
- 계정이나 API 키는 tmuxc 자체에는 필요 없습니다. 각 에이전트 CLI 의 인증은 그 CLI 가 따로 요구합니다.

## 링크

- [INSTALL.md](INSTALL.md) — 에이전트용 설치 안내
- [AI Feature Pack 카탈로그](../../README.ko.md)
