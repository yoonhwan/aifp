<div align="center">

# agent-cli

**AI 코딩 에이전트 CLI 의 설치 · 비교 가이드와, 다른 모델에 비대화로 일을 넘기는 위임 하네스를 한 팩으로 제공합니다.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- Claude Code · Codex · Gemini · OpenCode · Cursor Agent · Pi 6종 CLI 의 설치 · 인증 · 비교를 안내합니다.
- 지금 쓰는 세션 안에서 다른 모델을 비대화로 불러 일을 맡기고, 자율 실행시키고, `resume` 으로 이어 갑니다.
- 페르소나(DA · designer · architect)를 주입해 위임받은 모델에 바로 역할을 줍니다.
- 한 모델이 만든 결과를 다른 모델이 적대적으로 검증합니다(author ↔ review 분리).
- 같은 작업을 여러 프로바이더에 던져 cross-check 합니다.
- oh-my-\* · baton · tmuxc 같은 상위 하네스와 연계할 수 있습니다(선택). 설치돼 있지 않으면 무시되고, 비대화 위임 · 페르소나 · resume 은 그것 없이도 동작합니다.

## 빠른 시작

```bash
# 저장소 루트에서: OS 와 지금 쓸 수 있는 CLI 확인
bash feature-pack/agent-cli/scripts/detect-env.sh
# 스킬을 설치한 뒤(설치 절 참고): codex 에 DA 페르소나로 검증을 맡기고 이어서 묻기
bash ~/.claude/skills/agent-cli/scripts/resume_chain.sh codex DA "이 diff 를 적대적으로 검증해 줘" "지적을 우선순위로 정리해 줘"
```

## 설치

### 에이전트로 설치

에이전트에게 다음과 같이 요청하세요.

```text
feature-pack/agent-cli/INSTALL.md 를 읽고 설치해 줘
```

### 직접 설치

```bash
mkdir -p ~/.claude/skills/agent-cli/references ~/.claude/skills/agent-cli/scripts
cp SKILL.md            ~/.claude/skills/agent-cli/SKILL.md
cp references/*.md     ~/.claude/skills/agent-cli/references/
cp scripts/*.sh        ~/.claude/skills/agent-cli/scripts/
chmod +x ~/.claude/skills/agent-cli/scripts/*.sh
```

- 위 명령은 `feature-pack/agent-cli/` 안에서 실행합니다. OpenClaw 같은 다른 에이전트라면 스킬 경로만 그 규약에 맞춥니다. `SKILL.md` 는 단독으로 읽어도 됩니다.
- 먼저 `bash scripts/detect-env.sh` 를 돌리면 macOS · Linux · WSL 을 구분해 지금 쓸 수 있는 CLI 와 미설치 CLI 의 설치 힌트, WSL 주의사항을 한 번에 보여 줍니다.
- 에이전트 TOOLS.md(또는 같은 역할의 카탈로그)가 있으면 `config/tools-section.md` 내용을 추가합니다.
- OpenCode 기본 모델은 `opencode/deepseek-v4-flash-free` 이고, 다르면 `export OPENCODE_MODEL=<provider/model>` 로 바꿉니다(목록: `opencode models`).
- Pi 는 기본 모델을 `export PI_MODEL=<provider/model>` 로 바꿉니다. 먼저 `pi auth check --provider <provider> --json` 으로 인증을 확인하세요. 스킬 주입은 `--skill`, 도구 제한은 `--tools` 입니다.

### 설치 확인

```bash
bash ~/.claude/skills/agent-cli/scripts/selftest.sh   # 격리했거나 신뢰하는 폴더에서 실행
```

`test/verify.md` 의 체크리스트도 함께 확인합니다.

## 사용법

### 지원하는 CLI

| CLI | 비대화 | 자동 실행 | resume |
|-----|--------|---------|--------|
| Claude Code | `claude -p` | `--dangerously-skip-permissions` | `--resume <sid>` |
| Codex | `codex exec` | `--full-auto` ⎮ `--yolo` | `codex exec resume --last` |
| Gemini | `gemini -p` | `--approval-mode yolo` | `--resume <session_id>` |
| OpenCode | `opencode run` | 기본값이 무승인 | `-s <sid>` / `-c` |
| Cursor Agent | `cursor-agent -p` | `-f` / `--force` | `--resume <chatId>` |
| Pi | `pi -p` | `--tools <allowlist>` (승인 프롬프트 없음) | `--session-id <sid>` / `--session <sid>` |

- Aider 와 Amp 는 참고로만 다룹니다(`references/install-and-compare.md`).
- 세션 중에는 "이 PR 을 codex 로 DA 적대 검증" · "이 설계를 제미나이로 cross-check" · "아까 세션을 resume 해서 후속 질문" 같은 요청으로 자동 발동합니다.

### 위임과 resume

```bash
bash ~/.claude/skills/agent-cli/scripts/resume_chain.sh codex DA "이 diff 를 적대적으로 검증해 줘" "지적을 우선순위로 정리해 줘"

# Claude 모델과 effort 를 고정하려면
CLAUDE_MODEL=<model-id> CLAUDE_EFFORT=high \
bash ~/.claude/skills/agent-cli/scripts/resume_chain.sh claude DA \
  "이 변경을 적대적으로 검증해 줘" \
  "최종 승인 여부만 다시 말해 줘"
```

- `resume_chain.sh` 는 Claude 를 부를 때 `CLAUDE_MODEL` 과 `CLAUDE_EFFORT` 환경 변수를 그대로 넘깁니다.

### 스크립트

| 스크립트 | 하는 일 |
|---|---|
| `scripts/detect-env.sh` | OS 구분 · 지금 쓸 수 있는 CLI · 설치 힌트 · WSL 주의 |
| `scripts/selftest.sh` | 6종의 비대화 · 자동 실행 · resume 을 한 번에 점검(타임아웃 · 로그 포함) |
| `scripts/test_opencode.sh` | OpenCode 단독 점검(모델 자동 탐색) |
| `scripts/resume_chain.sh` | 페르소나 + 여러 번 resume 하는 체인 |
| `scripts/cloud-dataset-batch.sh` | cloud session credits 로 학습 · 라벨링 데이터를 대량 생성하고 회수 |

### 클라우드 크레딧 배치

Claude cloud session credits(구독과 별도로 지급되는 크레딧)는 cloud session 에서만 차감됩니다. 로컬 CLI 나 프록시를 거친 호출로는 차감되지 않습니다. `scripts/cloud-dataset-batch.sh` 는 저장소와 코드 없이 빈 폴더에서 cloud session 을 띄우고, 끝나면 회수(teleport)해서 답변에 찍힌 JSONL 만 뽑아 데이터셋으로 쌓습니다.

```bash
bash scripts/cloud-dataset-batch.sh --task lexicon --lang ko,ja,th --count 300 --batch 25 --parallel 3 --budget 20
bash scripts/cloud-dataset-batch.sh --task label   --lang ko --labels work,tech,legal,daily,billing,other --count 200
bash scripts/cloud-dataset-batch.sh --task doc     --lang ko --count 4 --batch 4 --parallel 1 --budget 1   # 소량 시험
```

| task | 만드는 데이터 |
|---|---|
| `lexicon` | 언어학 사전 항목(lemma · pos · IPA · gloss · 예문 · register) |
| `parallel` | 병렬 말뭉치(src / tgt · domain) |
| `label` | 분류 라벨링(text · label · rationale). `--labels` 로 라벨 집합을 고정 |
| `qa` | 언어 학습 Q/A(level · topic) |
| `doc` | 장문 문서 섹션(520자/줄). 대량 소진용 |
| `free` | 자유 형식 |

- 출력: `<out>/data.jsonl`(배치 사이 중복 제거 + `id` 재부여) · `<out>/run-*/index.tsv`(세션 · 건수 원장) · `ledger.json`(크레딧 증감)
- 실측: 세션 1개당 레코드 25건 수준, 레코드당 약 $0.03, 병렬 2~4 로 확장.
- 주의: cloud credits 에는 만료일이 있어 그 전에 써야 하고, `--budget` 으로 지출 상한을 겁니다. 대량 반복 생성은 계정 어뷰징으로 판정될 수 있으니 실제로 쓸 데이터를 만드세요.

### 안전

- 자동 실행 플래그(dangerous / full-auto / yolo / force)는 사람의 승인 게이트를 없앱니다. 격리했거나 신뢰하는 워크스페이스에서만 쓰세요.
- 위임 CLI 는 각자의 인증이 필요합니다. 이 팩은 자격증명을 넣어 주지 않습니다.
- 위임 결과는 신뢰할 수 없는 입력으로 취급하고, 본 세션에서 검토한 뒤 쓰세요.

## 요구사항

- 지원 환경: macOS · Linux · WSL
- `perl` · `python3` — macOS 에는 기본 내장입니다. WSL · Ubuntu 에 없으면 `sudo apt install -y perl python3`
- 6종 중 최소 1개의 에이전트 CLI 가 PATH 에 있고, 그 CLI 자체 인증이 끝나 있어야 합니다. 설치되지 않은 CLI 는 자동으로 건너뜁니다.
- WSL: OAuth 는 Windows 브라우저로 열립니다(URL 을 직접 복사해 붙여 넣을 수 있음). cursor-agent 가 없을 수 있고(자동 SKIP), 작업은 `~/` 안에서 하세요.
- 클라우드 크레딧 배치만: `~/.headroom/claude-credit.sh`(ccx / ccxt) · `claude` 2.1.310 이상 · tmux

## 링크

- [INSTALL.md](INSTALL.md) — 에이전트용 설치 안내
- [SKILL.md](SKILL.md) — 스킬 정의
- [references/per-cli.md](references/per-cli.md) — CLI 별 비대화 · 자동 실행 · resume 상세
- [references/install-and-compare.md](references/install-and-compare.md) — 설치 · 인증 · 비교
- [references/personas.md](references/personas.md) — DA · designer · architect 페르소나
- [AI Feature Pack 카탈로그](../../README.ko.md)
