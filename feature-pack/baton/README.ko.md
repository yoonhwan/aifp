<div align="center">

# baton

**어느 에이전트가 시작한 작업이든 다음 에이전트가 그대로 이어받도록 worktree · 작업 메모리 · archive 를 한 그릇에 모읍니다**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- Claude Code · Codex · Gemini · OpenCode · Hermes 가 같은 그릇 `.baton/handoff/`(`PLAN.md` · `JOURNAL.md` · `CURRENT.md` · `NEXT.md`)에 결과를 쌓습니다. 다음 세션은 어느 에이전트든 이 그릇을 읽고 이어 갑니다.
- worktree 를 만들고 정리합니다. 만들 때 포트 할당 · 심볼릭 링크 · 메모리 초기화를 하고, 끝나면 archive 에 보관합니다.
- archive 는 git 으로 추적합니다. push 하면 다른 머신에서도 지난 결정을 검색할 수 있고, 오래된 archive 는 30일 기준으로 정리합니다.
- `BATON_TMUX_ENABLE=true` 이면 worktree 마다 tmux 세션을 만듭니다. 노트북을 닫아도 세션이 남고, 다른 에이전트나 휴대폰 SSH 로 attach 해 이어 갑니다.
- main / master 루트에서는 plan · save · resume · finish 를 거부합니다. phase 는 worktree 안에만 둡니다.
- 일 자체(plan 인터뷰 · 코딩 · 리뷰 · 시험)는 하지 않습니다. 외부 하네스(superpowers · OMX · OMC 등)에 맡기고 결과만 그릇에 쌓습니다.

## 빠른 시작

```bash
git clone https://github.com/yoonhwan/aifp
bash aifp/feature-pack/baton/install.sh   # 인터뷰형 설치
export BATON_TMUX_ENABLE=true             # 선택 — worktree 마다 tmux 세션

# 에이전트 안에서 — main 루트
/baton:wt-create my-task
cd .worktrees/my-task

# worktree 안에서
/baton:plan my-task     # 선택 — 큰 작업만
# ... 외부 하네스로 작업 ...
/baton:save             # 멈출 때 handoff 저장
/baton:finish           # phase 완료
/baton:wt-clean         # 정리 + archive 보관
```

다음 세션에서는 어느 에이전트든 그 worktree 로 들어가 `/baton:resume` 을 부르거나 «이어서» · `go` · `continue` 라고 말하면 `NEXT.md` 를 읽고 이어 갑니다.

## 설치

### 에이전트에게 맡기기

에이전트에게 «`feature-pack/baton/INSTALL.md` 를 읽고 설치해 줘» 라고 하면 됩니다. 설치 시간은 약 3분입니다.

### 직접 설치

```bash
bash feature-pack/baton/install.sh        # 인터뷰형 설치
export PATH="$HOME/.baton/current/bin:$PATH"   # ~/.zshrc 또는 ~/.bashrc 에 추가
~/.baton/current/bin/baton doctor         # 검증
bash feature-pack/baton/uninstall.sh      # 제거
```

`install.sh` 가 하는 일:

1. 설치된 에이전트를 찾습니다(Claude Code · Gemini CLI · OpenCode · Hermes).
2. core 를 `~/.baton/versions/<version>/` 에 복사하고 `~/.baton/current` 링크를 겁니다(여러 버전 공존).
3. 에이전트마다 등록합니다.

| 에이전트 | 등록하는 것 |
|---|---|
| Claude Code | `~/.claude/commands/baton/` 명령 · `~/.claude/skills/baton/SKILL.md` 링크 · `~/.claude/settings.json` hook |
| Gemini CLI | `~/.gemini/commands/baton/` TOML · `~/.gemini/settings.json` hook |
| OpenCode | `~/.config/opencode/commands/baton/` · plugins |
| Hermes | `~/.hermes/plugins/baton.py` |
| Codex · OpenClaw | 수동 등록 안내를 출력 |

4. 어느 hook 에 어떤 baton 작업을 걸지 묻습니다(추천 값 자동 선택 가능).

`settings.json` 은 `settings.json.baton-backup` 으로 백업한 뒤 합칩니다. 제거해도 프로젝트 안의 `.baton/` 은 사용자 데이터라 남기므로 직접 지웁니다.

## 사용법

### 명령

| 명령 | 하는 일 |
|---|---|
| `/baton:wt-create <name>` | worktree + 포트 + 심볼릭 링크 + 메모리 초기화 |
| `/baton:plan <id>` | phase 계획(`PLAN.md` · `phase.json`) — worktree 안에서만 |
| `/baton:save` | handoff 를 바로 저장(`CURRENT.md` 는 paused, `NEXT.md` 갱신) |
| `/baton:resume` | `NEXT.md` 를 출력하고 이어 감 |
| `/baton:finish` | phase 완료 + wt-clean 제안 |
| `/baton:wt-clean [path] [--merged]` | worktree 정리 + archive 보관 |
| `/baton:status` | phase + 활성 worktree(tmux 세션 포함) |
| `/baton:hotfix-mode [finish]` | main 에서 바로 hotfix(lite mode · 메모리 끔) |
| `/baton:digest <topic>` | 여러 세션의 컨텍스트를 파일 하나로 압축 |
| `/baton:migrate [--dry-run] [path]` | 기존 worktree 를 sidecar 구조로 옮김 |
| `/baton:help` | 흐름을 ASCII 그림으로 출력 |
| `/baton:install` · `/baton:doctor` · `/baton:upgrade` | 설치 · 진단 · 새 버전 설치 |
| `/baton:archive list` | 최근 30일 archive |
| `/baton:archive search <query> [--global]` | 메타 + 내용 검색 |
| `/baton:archive show <id>` | 상세 |
| `/baton:archive extract <id>` · `close <id>` | 임시 폴더로 풀기 · 그 폴더 정리 |
| `/baton:archive prune [--dry-run] [--days N]` | 기한 지난 archive 정리 |

### main 보호

main / master 루트에서 되는 것은 `wt-create` · `archive list/search` · `status` · `hotfix-mode` 뿐입니다. `plan` · `save` · `resume` · `finish` 는 거부합니다. main 을 더럽히지 않고 phase 는 worktree 에만 둡니다.

### tmux 와 휴대폰 attach

`BATON_TMUX_ENABLE=true` 이면 `wt-create` 가 tmux 세션을 만들고 `tmux attach -t <세션>` 명령을 보여 줍니다. Tailscale 이 있으면 `tailscale ip -4` 와 `$USER` 로 만든 SSH 명령 한 줄도 함께 보여 주므로 Termius · Blink 같은 휴대폰 앱에 붙여 넣으면 됩니다. 세션 안의 에이전트는 `BATON_AGENT` 로 정하고, 없으면 `CODEX_*` · `OMX_SESSION_ID` 는 Codex, `CLAUDE_*` 는 Claude 로 봅니다. macOS 준비(한 번):

```bash
sudo tailscale set --ssh             # Tailscale SSH 켜기
sudo systemsetup -setremotelogin on  # SSH 켜기
sudo pmset -c sleep 0                # 전원 연결 시 잠자기 끄기
```

### Claude Code hook

| hook | baton 이 하는 일 |
|---|---|
| SessionStart | paused 알림 + 환경 검증 + archive 정리 |
| UserPromptSubmit | 사용자 입력을 `JOURNAL.md` 에 바로 추가 |
| PostToolUse | 외부 하네스 사용을 `JOURNAL.md` 에 기록 |
| PreCompact | 백업 dump 지시 |
| SessionEnd | 백업 dump 지시 |

### 외부 하네스

`/baton:plan` 은 쓸 수 있는 하네스 후보를 보여 줍니다. 계획 쪽(`/superpowers:writing-plans` · `$plan` · `/oh-my-claudecode:plan` 등) 결과는 `PLAN.md` 에, 실행 쪽(`/superpowers:executing-plans` · `$autopilot` · `/oh-my-claudecode:autopilot` 등) 결과는 `JOURNAL.md` 에 쌓도록 지시를 넣습니다. 카탈로그 파일은 없고 이름으로 맞춥니다. 추천 값은 `config.json` 의 `harnesses.preferred_plan` 으로 바꿉니다.

### 파일 위치

```
~/.baton/
├── versions/<version>/      # bin · lib · templates · SPEC.md
└── current -> versions/<version>/

<project>/.baton/
├── config.json              # commit
├── version.lock             # commit
└── archive/                 # commit (머신 사이 sync)

<worktree>/.baton/
├── config.json              # 프로젝트 설정 상속
├── phase.json               # commit
├── handoff/                 # gitignore — PLAN · JOURNAL · CURRENT · NEXT
└── session.lock
```

### 흐름 사례

| 사례 | 상황 |
|---|---|
| [plan-first](flows/plan-first.md) | 긴 작업 — plan 부터 |
| [wt-first](flows/wt-first.md) | 가벼운 작업 — worktree 만 바로 |
| [wt-finish](flows/wt-finish.md) | 하나 끝내기 |
| [branch-pivot](flows/branch-pivot.md) | 여러 브랜치로 갈라진 뒤 정리 |
| [abandoned](flows/abandoned.md) | phase 포기 |
| [hotfix-mode](flows/hotfix-mode.md) | main 에서 바로 hotfix |
| [orphan-recovery](flows/orphan-recovery.md) | `.baton/` 손상 복구 |
| [handoff-rollback](flows/handoff-rollback.md) | `handoff/` 손상 시 archive 에서 복원 |

## 요구사항

- OS: macOS · Linux
- 필수: `bash` 4 이상 · `git` 2.30 이상 · `jq` 1.6 이상 · `tar`
- 선택: `ripgrep` · `gh` · tmux(`BATON_TMUX_ENABLE`) · Tailscale(휴대폰 attach)
- API 키 · 계정: 없음

## 링크

- [INSTALL.md](INSTALL.md) — 에이전트용 설치 안내
- [core/SPEC.md](core/SPEC.md) — 다른 에이전트와 맞추는 규칙 4개(handoff 4파일 형식 · `phase.json` 스키마 · worktree 위치와 main 보호 · 포트 할당)
- [flows/_index.md](flows/_index.md) — 흐름 사례 8개
- [docs/MULTI_AGENT_SCENARIOS.md](docs/MULTI_AGENT_SCENARIOS.md) — 여러 에이전트 동시 작업
- 어댑터: [Codex](adapters/codex/INSTRUCTIONS.md) · [Gemini](adapters/gemini/INSTRUCTIONS.md) · [OpenCode](adapters/opencode/INSTRUCTIONS.md) · [Hermes](adapters/hermes/INSTALL.md)
- [cairn](../cairn/README.ko.md) — 함께 쓰는 팩: 일정과 복귀점 원장
- [AI Feature Pack 목록](../../README.ko.md)
- 라이선스: MIT
