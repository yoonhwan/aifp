<div align="center">

# fable-team

**fable-team ft 2.0 소스 — 좌석 · 쪽지 · 발주 코어, 계약, Slack · Codex · Pi 어댑터와 골 닫기 흐름을 폴더 하나 = 책임 하나로 나눠 둡니다.**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- `ft2/` 에 ft 2.0 의 새 뼈대가 있습니다. 2.0 활성 소스는 이 폴더 안에서만 씁니다.
- 좌석 · 쪽지 · 발주 같은 공통 코어는 실행 환경 차이를 모릅니다. 환경마다 다른 부분은 어댑터(Slack · Codex · Pi)가 맡습니다.
- 카드 · 계약 · 시험 대응표의 계약 정의와 모델 표가 `ft2/contracts/` 에 있습니다.
- `goal-close/` 는 큰 골을 조건 칸으로 나눠 한 칸씩 닫는 흐름 1개와 규칙 6줄을 담은 모듈입니다.
- `legacy_guard.py` 는 `ft2/` 가 1.x 도구를 실행 · import · source 하지 않는지 검사합니다.

## 빠른 시작

```bash
# 리포 루트에서 — ft2/ 자기검사 (0 = 위반 0)
python3 feature-pack/fable-team/ft2/tools/legacy_guard.py
```

## 설치

이 팩 폴더에는 `INSTALL.md` 가 없습니다. 공개 사본에 있는 것은 ft 2.0 소스와 `goal-close/` 모듈이고, 여기에 적힌 설치 절차는 없습니다. 1.x 하네스는 공개 사본에 들어 있지 않습니다. 리포를 받아 이 폴더의 파일을 그 자리에서 읽고, 검사기는 위 «빠른 시작» 처럼 그 자리에서 돌립니다.

## 사용법

### 폴더 책임

폴더 하나 = 책임 하나입니다.

| 폴더 | 책임 |
|---|---|
| `ft2/core/` | 좌석 · 쪽지 · 발주 같은 2.0 공통 코어. 실행 환경 차이를 모릅니다 |
| `ft2/contracts/` | 카드 · 계약 · 시험 대응표의 2.0 계약 정의 |
| `ft2/contracts/models/` | 모델 표 3개(model-scope · model-fallback · provider-of-model) 정본 자리 — `tools/models.py` 가 읽습니다 |
| `ft2/adapters/slack/` | Slack 수신 · 발행 어댑터 |
| `ft2/adapters/codex/` | Codex 실행 어댑터 |
| `ft2/adapters/pi/` | Pi 실행 어댑터 · 좌석 열기(`launch.py`) |
| `ft2/doctor/` | 설치 · 환경 진단 |
| `ft2/tools/` | 검사기 · 보조 도구 |
| `ft2/tests/` | ft2 시험 |

### legacy_guard

`ft2/` 의 어떤 파일도 1.x 경로 · 도구를 실행 · import · source 하지 않아야 합니다. 검사 패턴은 1.x 경로 · 도구 자리 5종(목록 = [ft2/README.md](ft2/README.md)), 검사 확장자는 `.py` `.sh` `.ts` `.js` `.json` 입니다. `*.md` 는 산문이라 허용합니다. 코드 파일의 주석도 검사합니다.

```bash
python3 feature-pack/fable-team/ft2/tools/legacy_guard.py          # ft2/ 자기검사
python3 feature-pack/fable-team/ft2/tools/legacy_guard.py <폴더>   # 다른 트리 검사
```

| 종료 코드 | 뜻 |
|---|---|
| `0` | 위반 0 |
| `1` | 위반 있음(`<파일>:<줄>: <패턴>` 1줄씩) |
| `2` | 사용법 · 경로 오류 |

한계: 문자열 검사라 동적으로 조립한 경로는 못 잡습니다. 그런 경로는 리뷰에서 봅니다.

### goal-close

큰 골을 조건 N칸으로 나누고, 칸 하나를 좌석 하나가 기획부터 닫기까지 끌고 갑니다: 기획 → 구현(시험 Red → Green · PR) → DA 판정 → 설치본에서 검증 → 다음 날 모니터 → 닫기.

| 파일 | 내용 |
|---|---|
| `00-flow.md` | 흐름 1개와 규칙 6줄 |
| `10-cell.md` | 골 파일 칸과 칸 규칙 |
| `20-situations.md` · `30-direct.md` | 상황별 처리 · 팀장을 거치지 않는 길 |
| `40-conduct.md` | 지침과 없앨 특징 |
| `roles/` | 역할별 글(`arch` · `da` · `master` · `nano`) |
| `phrases.tsv` · `MODULE.json` | 문구 표 · 모듈 판(`gc-1.3`)과 파일별 sha256 |

## 요구사항

- Python 3(`legacy_guard.py` · 표준 라이브러리만)
- API 키 · 계정: 없음(`legacy_guard.py` 기준)
- 어댑터를 돌리는 데 필요한 것은 이 폴더 문서에 적혀 있지 않습니다.

## 링크

- [ft2/README.md](ft2/README.md) — ft 2.0 폴더 책임과 1.x 의존 금지
- [goal-close/00-flow.md](goal-close/00-flow.md) — 골 닫기 흐름
- [AI Feature Pack 목록](../../README.ko.md)
