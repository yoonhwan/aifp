<div align="center">

# cairn

**일정과 여러 에이전트 작업의 복귀점을 원장 하나(`.cairn/plan.yaml`)에 적는 CLI**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- 프로젝트 / milestone(start · end) / 태스크(start · due) 일정을 적고, overdue 와 전체 간트(Mermaid)를 보여 줍니다.
- 작업을 나눠 맡길 때(fan-out) 계보를 적습니다: `spawned_from` · `return_to` · `merge_back_to` · `fanout_depth`. session 을 정리하거나 worktree 를 지운 뒤에도 돌아갈 자리가 남습니다.
- 돌아올 때(fan-in) `cairn return` 이 그 노드를 다시 잡고 baton resume 으로 잇습니다.
- baton(기억) · tmuxc(실행) · git 은 읽기만 합니다. cairn 이 직접 쓰는 것은 계획과 복구 메타뿐입니다.
- 모든 쓰기는 한 줄로 직렬화됩니다: lock + atomic write + validate + git commit. 작업 트리가 더러우면 막습니다.
- 한 번 전역 설치하면 어느 프로젝트 폴더에서 실행하든 그 프로젝트의 `.cairn/` 원장을 다룹니다.

## 빠른 시작

```bash
git clone https://github.com/yoonhwan/aifp
bash aifp/feature-pack/cairn/install.sh   # ~/.cairn 전역 설치 + Claude Code 명령 · 스킬 등록
cairn self-test                           # 검증

cd my-app
cairn new-project demo                    # .cairn/plan.yaml 생성
cairn status
```

## 설치

### 에이전트에게 맡기기

Claude Code 에게 «`feature-pack/cairn/INSTALL.md` 를 읽고 `bash feature-pack/cairn/install.sh` 를 실행한 뒤 self-test 와 hook smoke 까지 검증해 줘» 라고 하면 됩니다. Codex 에서는 `bash feature-pack/cairn/install.sh` 를 실행합니다. 설치 시간은 약 2분입니다.

### 직접 설치

```bash
bash feature-pack/cairn/install.sh
export PATH="$HOME/.cairn/current/bin:$PATH"   # 새 셸이 아니면
cairn self-test                                # self-test OK
bash feature-pack/cairn/uninstall.sh           # 제거 — 전역만 지우고 프로젝트 .cairn/ 은 남김
```

`install.sh` 가 하는 일: core 를 `~/.cairn/versions/<version>` 에 복사 · `current` 링크 · `~/.cairn/venv`(ruamel.yaml) · `~/.zshrc` 에 PATH · `~/.cairn/current/hooks/*` · `~/.claude/commands/cairn` · `~/.claude/skills/cairn/SKILL.md` 링크 · `cairn self-test`. 다시 실행해도 안전합니다(새 버전 폴더를 더하고 `current` 를 바꿉니다).

프로젝트마다 git hook 을 겁니다:

```bash
mkdir -p .git/hooks
ln -sfn "$HOME/.cairn/current/hooks/post-merge" .git/hooks/post-merge
ln -sfn "$HOME/.cairn/current/hooks/post-checkout" .git/hooks/post-checkout
```

## 사용법

### 일정 명령

| 명령 | 하는 일 |
|---|---|
| `cairn init` | 프로젝트에 `.cairn` 원장 초기화 |
| `cairn new-project <name>` · `add-milestone <p> <name>` · `add-task <p> <ms> <name> [--days N]` | 만들기 |
| `cairn status` · `show <p>` · `overdue [--today]` | 조회 |
| `cairn render` | 전체 간트(Mermaid) → `.cairn/views/plan.md` |
| `cairn set-status` · `set-date` · `set-priority` | 바꾸기 |

### 복구 명령 (fan-out / fan-in)

| 명령 | 하는 일 |
|---|---|
| `cairn spawn <name> --from <parent>` | 나누기(fan-out) — `spawned_from` · `return_to` · `fanout_depth` 자동 |
| `cairn complete <task> [--force]` | 완료 + `return_to` 를 보여 줌(없으면 막음) |
| `cairn return --to <node>` | 돌아오기(fan-in) — 노드를 다시 잡고 baton resume 으로 이음 |
| `cairn map [--focus] [--render]` | 복구 그래프(recovery-map) Mermaid → termaid |
| `cairn link <node> --execution-ref / --session-ref / --merge-back-to` | hook 이 부르는 메타 기록 |
| `cairn reconcile` | 활성 worktree 와 노드를 대조해 orphan 찾기 |
| `cairn validate` | 원장 무결성 검증 — 끊긴 복구 연결 0 |

task id 는 원장 전체에서 유일합니다(복구 메타가 전역으로 가리키기 때문).

### 자동 진척 hook

`~/.cairn/current/hooks/cairn-auto-progress` 는 검증 통과(`CAIRN_VERIFICATION_STATUS=pass`)를 받으면 기본으로 `.cairn/auto-progress/candidates/` 에 완료 후보만 남깁니다. `CAIRN_AUTO_PROGRESS=apply` 와 `CAIRN_TASK_ID` 를 함께 줄 때만 `cairn complete <task>` 를 실행합니다.

```bash
# 후보만 남김
CAIRN_TASK_ID=t2 CAIRN_VERIFICATION_STATUS=pass \
  "$HOME/.cairn/current/hooks/cairn-auto-progress"

# 원장에 반영
CAIRN_AUTO_PROGRESS=apply CAIRN_TASK_ID=t2 CAIRN_VERIFICATION_STATUS=pass \
  "$HOME/.cairn/current/hooks/cairn-auto-progress"
```

Claude Code 에서는 PostToolUse hook 으로, Codex 에서는 shell hook 이나 tmuxc 세션의 종료 · 검증 단계에서 같은 명령을 부릅니다.

## 요구사항

- OS: macOS · Linux
- 필수: `python3` 3.9 이상 · `git` 2.30 이상 · `ruamel.yaml`(설치 때 `~/.cairn/venv` 에 자동)
- 선택: termaid(`cairn map --render`)
- API 키 · 계정: 없음
- 문제 해결: `cairn: command not found` → 새 셸을 열거나 위 PATH 를 export · `ModuleNotFoundError: ruamel` → `bash install.sh` 다시 실행

## 링크

- [INSTALL.md](INSTALL.md) — 에이전트용 설치 안내
- [docs/cairn-design.md](docs/cairn-design.md) — 설계
- [docs/agent-lifecycle-hook-design.md](docs/agent-lifecycle-hook-design.md) — 에이전트 생애 hook 설계
- [baton](../baton/README.ko.md) — 함께 쓰는 팩: worktree · 작업 메모리 · archive
- [AI Feature Pack 목록](../../README.ko.md)
- 라이선스: MIT
