<div align="center">

# auto

**에이전트는 코드만 고치고, `uv run` 이 실험을 돌리고, stdout JSON 으로 keep/discard 를 판정하는 자율 실험 루프.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- Karpathy AutoResearch 패턴의 자율 실험 루프를 에이전트 스킬 `/auto` 로 제공합니다.
- 에이전트의 일은 4단계입니다: 코드 수정 → 실험 실행 → JSON 읽기 → 판정.
- 인프라 확인과 셋업은 `prepare.py`, 실험 실행과 metric 출력은 `run_experiment.py` 가 맡습니다.
- `program.md` 에 목표(metric · 수정 범위 · 제약)를 선언하면 에이전트가 그 범위 안에서 반복합니다.
- 실험 기록은 `results.tsv` 에 쌓이고, 끝나면 리포트를 만들 수 있습니다.

## 빠른 시작

```bash
# 1. 스킬 설치
mkdir -p ~/.claude/skills/auto/references
cp skill/SKILL.md ~/.claude/skills/auto/SKILL.md
cp skill/references/*.md ~/.claude/skills/auto/references/

# 2. 프로젝트에 템플릿 복사 + uv 환경 만들기
mkdir -p your-project/autoresearch
cp config/templates/* your-project/autoresearch/
cd your-project/autoresearch && uv sync

# 3. program.md, prepare.py, run_experiment.py 를 프로젝트에 맞게 고친다
# 4. 에이전트 세션에서 /auto 를 실행한다
```

## 설치

에이전트에게 "Read feature-pack/auto/INSTALL.md and install it" 이라고 맡기면 됩니다. 직접 설치하려면 [INSTALL.md](INSTALL.md) 의 순서를 따릅니다.

1. 스킬 파일을 `~/.claude/skills/auto/` 에 복사합니다.
2. 프로젝트 루트에 `autoresearch/` 폴더를 만들고 템플릿 4개(`pyproject.toml` · `prepare.py` · `run_experiment.py` · `program.md`)를 복사한 뒤 `uv sync` 를 실행합니다.
3. `program.md` 에 목표를 쓰고, `prepare.py` 의 `check_runtime()` · `check_data()` 와 `run_experiment.py` 의 `RUN_CMD` · `parse_result()` · `TIMEOUT` 을 프로젝트에 맞게 고칩니다.
4. 실험 산출물이 git 에 섞이지 않게 `.gitignore` 를 추가하고 스킬이 로드됐는지 확인합니다.

```bash
# autoresearch/.gitignore 에 추가
cat >> autoresearch/.gitignore << 'EOF'
.venv/
run.log
results.tsv
upstream/
__pycache__/
EOF

# 스킬 로드 확인 (기대값: version: "3.0.0")
grep "version" ~/.claude/skills/auto/SKILL.md
```

## 사용법

### 명령

에이전트 세션에서 실행합니다.

| 명령 | 설명 |
|------|------|
| `/auto` | 전체 플로우 시작 (setup → 베이스라인 → 목표 → 자율주행) |
| `/auto setup` | `autoresearch/` 초기화만 |
| `/auto 2h` | 2시간 자율주행 |
| `/auto 30m` | 30분 자율주행 |
| `/auto overnight` | 8시간 자율주행 |
| `/auto resume` | 기존 브랜치에서 이어서 |
| `/auto report` | `results.tsv` 기반 리포트 생성 |
| `/auto update` | `upstream/` git pull |

### 3층 구조

```
Layer 1: uv run prepare.py         (1회) 인프라 체크 + 셋업
Layer 2: 에이전트 자율 루프          코드 수정 → run → JSON → 판정
Layer 3: uv run run_experiment.py  (매회) 테스트 실행 → metric 출력
```

### stdout JSON 계약

`run_experiment.py` 는 stdout 의 마지막 줄에 JSON 한 줄만 출력합니다. 나머지 출력(진행 상황 · 경고)은 stderr 또는 `run.log` 로 갑니다.

```json
{
  "score": 0.004,
  "passed": 13,
  "total": 14,
  "failed": ["case-14"],
  "grade_summary": "13S 1A",
  "flush_e2e_ms": null,
  "status": "ok",
  "duration_s": 187.3
}
```

- `status` 는 `"ok"` · `"crash"` · `"error"` 중 하나이고, crash/error 일 때 `reason` 이 붙을 수 있습니다. `flush_e2e_ms` 는 선택 항목(secondary metric)입니다.
- exit 0 = 정상 종료: 에이전트가 `score` 로 keep/discard 를 판정합니다.
- exit 1 = 크래시 또는 인프라 실패: 에이전트가 되돌리거나 고쳐서 다시 시도합니다(최대 2회).

### 도메인별 예시

| 도메인 | primary_metric | RUN_CMD | prepare.py |
|--------|---------------|---------|------------|
| ML 학습 | val_bpb | `uv run train.py` | GPU + 데이터셋 체크 |
| STT 품질 | avg_cer | `python3 e2e_test.py --baseline --json` | 서버 + 브라우저 + 오디오 |
| API 레이턴시 | p99_ms | `pytest tests/perf.py --json` | 서버 + DB |
| 코드 품질 | coverage | `pytest --cov --json` | 의존성 체크 |

### 팁

- `program.md` 를 잘 쓰는 것이 핵심입니다. metric · scope · constraints 가 에이전트의 행동 범위를 정합니다.
- `prepare.py` 는 한 번만 실행하면 되고 멱등이라 불안하면 다시 돌려도 됩니다.
- 실험당 시간 예산은 5분 이내로 잡아야 실험을 많이 돌릴 수 있습니다.
- 전용 브랜치에서 돌리고, 한 번에 한 가지만, 한 영역 1~2파일만 고칩니다.
- `autoresearch/` 안의 인프라 파일은 에이전트가 고치지 않습니다. 프로젝트 소스만 고칩니다.

## 요구사항

- macOS 또는 Linux
- Python 3.11+
- git
- [uv](https://docs.astral.sh/uv/)
- Claude Code 또는 호환 에이전트 CLI
- API 키 불필요 · 설치 시간 (~2분)

## 링크

- [INSTALL.md](INSTALL.md) — 설치 가이드
- [stdout JSON 계약 상세](skill/references/run-experiment-contract.md)
- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) — 원본 패턴
- [AI Feature Pack 카탈로그](../../README.ko.md)
