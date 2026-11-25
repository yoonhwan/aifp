<div align="center">

# rag

**문서를 암호화된 로컬 DB 에 넣고 검색해 근거를 JSON 으로 돌려주는 RAG 엔진 `airag` (CLI `ai-rag`)**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- 원본 · 청크 · 벡터를 암호화된 SQLite(SQLCipher) 한 파일에 저장합니다. 벡터는 sqlite-vec, 키워드는 FTS5.
- 명시적 요청만 처리합니다: `add` · `update` · `delete` · `manage restore`. 폴더 감시 · 스케줄 · 자동 탐색은 없고, 쓰는 쪽 프로젝트가 이벤트를 보냅니다.
- 갱신하면 새 리비전이 생기고 이전 원본 바이트와 과거 검색 결과(manifest)는 남습니다. 삭제한 원본을 되살릴 수 있습니다.
- 처리 프로필(임베딩 + 선택 LLM + 정규화 설정)을 한 번 등록하면 바뀌지 않습니다. LLM 을 붙이면 의미 그룹 · 태그 · 요약 · 영어 번역을 만든 뒤 임베딩합니다.
- 검색 = BM25 + 벡터 + RRF. 결과에서 구조 · 참조 · 의미 연결을 예산(깊이 · 청크 · 토큰 · 바이트) 안에서 넓혀 근거 묶음으로 돌려줍니다.
- 문서 어댑터(`documents` 추가 설치): PDF · DOCX · XLSX · HWP5 · HWPX, 그리고 PNG · JPEG · BMP · TIFF 의 명시적 OCR · 비전 모드.
- 모든 명령은 JSON 응답 하나 `{schema_version, request_id, ok, command, data, error}` 를 냅니다. 백업 · 복원 · 진단도 같은 꼴입니다.
- 엔진은 근거만 돌려줍니다. 최종 답을 쓰는 일은 위에 있는 에이전트 몫입니다.

### 처리 흐름

```text
원본 --[Docling · HWP/HWPX 어댑터 · 대화 어댑터]--> 표준 묶음 (Markdown + 구조 · 앵커)
  --[HybridChunker]--> 청크 --[임베딩 · FTS 발행]--> 인덱스
  --[BM25 + 벡터 + RRF]--> 검색 --[예산 있는 구조 · 의미 확장]--> 근거 (원본 반환 포함)
```

## 빠른 시작

```bash
cd feature-pack/rag
uv sync                                     # .venv 를 만들고 airag 를 설치

head -c 32 /dev/urandom > my.key            # 32바이트 키 — 잃으면 DB 를 못 엽니다
chmod 600 my.key
.venv/bin/ai-rag init my.db --key-fd 3 3< my.key
.venv/bin/ai-rag manage doctor              # 실행 환경 진단
```

## 설치

### INSTALL.md 없음

이 팩에는 아직 `INSTALL.md` 가 없습니다. 에이전트에게 맡길 때는 «`feature-pack/rag/README.md` 와 `pyproject.toml` 을 읽고 설치해 줘» 라고 말하면 아래 직접 설치 단계를 따릅니다.

### 직접 설치

패키지 이름은 `ai-feature-rag`, 진입 명령은 `ai-rag` 입니다(같은 명령의 별칭 `krb-rag` 도 있음).

```bash
cd feature-pack/rag
uv sync                                     # 기본 의존성
uv sync --extra documents                   # PDF · DOCX · XLSX · OCR 어댑터 (docling · easyocr)
uv run pytest                               # 오프라인 시험 (integration 표시 시험은 기본으로 건너뜀)
```

## 사용법

### 명령

| 명령 | 하는 일 |
|---|---|
| `ai-rag init <db>` | 새 암호화 DB 를 만든다 |
| `ai-rag add` · `update` · `delete` | 원본 등록 · 갱신(새 리비전) · 삭제 — `--request-id` 로 같은 요청을 다시 보내도 한 번만 반영 |
| `ai-rag search` | `--collection` · `--query` · `--profile-key` 로 검색 · `--expand` 로 같은 스냅숏에서 확장 |
| `ai-rag expand --manifest-id N` | 지난 검색 결과에서 근거를 넓힌다 (`--max-depth` · `--max-chunks` · `--max-tokens` · `--max-bytes` · `--max-edges`) |
| `ai-rag fetch original` · `source` · `chunk` · `manifest` · `expansion` | 원본 바이트 · 정규화 결과 · 청크 · 과거 검색 · 과거 확장을 다시 꺼낸다 |
| `ai-rag manage profile --config <file>` | 처리 프로필 등록 (JSON 파일: `embedding` · 선택 `llm` · `normalizer`) |
| `ai-rag manage status` · `list` · `show` | 상태 · 목록 · 원본 한 개 보기 |
| `ai-rag manage retry` · `reindex` · `restore` | 실패한 작업 다시 · 다른 프로필로 다시 처리 · 삭제한 원본 되살리기 |
| `ai-rag manage backup` · `restore-backup` | 백업 만들기 · 백업에서 복원 |
| `ai-rag manage doctor` · `verify` | 설치 진단 · DB 검사 |

`init` 을 뺀 DB 명령은 `--db <db>` 와 `--key-fd <fd>` 를 받습니다.

### 예시

```bash
K="--db my.db --key-fd 3"

# 1) 처리 프로필 등록 — 응답 data 의 profile_key 를 받아 둔다
.venv/bin/ai-rag manage profile $K --config profile.json 3< my.key

# 2) 텍스트 원본 등록
.venv/bin/ai-rag add $K --request-id req-1 --collection notes --source-key note-1 \
  --text "hello" --profile-key <profile_key> 3< my.key

# 3) 검색 — 응답의 manifest_id 로 나중에 expand · fetch manifest
.venv/bin/ai-rag search $K --collection notes --query "hello" \
  --profile-key <profile_key> --top-k 5 3< my.key
```

`profile.json` 의 `embedding` 에는 `provider`(`lmstudio` 또는 `openai-compatible`) · `endpoint` · `model` · `revision` · `dimension` · `tokenizer_revision`(고정한 커밋 · 태그)을 넣습니다. 전체 항목은 [src/airag/embeddings.py](src/airag/embeddings.py) 의 `EmbeddingSpaceConfig`, LLM 항목은 [src/airag/llm_enrichment.py](src/airag/llm_enrichment.py) 의 `ChatCompletionConfig` 에 있습니다. 파이썬에서 직접 부르는 예는 [examples/explicit_consumer.py](examples/explicit_consumer.py) 입니다.

### 키 다루기

- 키는 32바이트 원시 값이고 `--key-fd` 로 열린 파일 설명자에서만 읽습니다. 명령줄 인자 · 로그에 키가 나오지 않습니다.
- macOS Keychain 에서 키를 읽는 기능은 아직 없습니다.

### 알려진 한계

- 벡터 검색은 전수 비교(O(N))입니다. ANN 성능이나 한국어 키워드 검색 품질은 검증했다고 말하지 않습니다.
- XLSX 의 재계산 · array/data-table 수식, 보호 · 배포용 HWP, DOCX 의 비트맵 밖 DrawingML 자동 렌더링은 지원하지 않습니다.
- HWP/HWPX 앵커는 섹션 · 문단 · 표 기준입니다(렌더링 쪽 번호 없음).
- 문서 안 그림은 추출 · 보존하지만 비전 처리를 자동으로 돌리지 않습니다.
- 모델 가중치 리비전은 자동으로 증명하지 않습니다. 운영자가 적은 값과 실행 중 fingerprint 를 따로 둡니다.

## 요구사항

- Python 3.13 이상 3.15 미만 · `uv` 0.10.0 이상
- 임베딩 서버: OpenAI 호환 `/v1/embeddings` (LM Studio 등)
- 선택: OpenAI 호환 chat 서버 (LLM 전처리)
- 선택: HWP5 문서 = `java` + 로컬 hwplib jar (문서 어댑터 설정 `hwp_classpath`)
- API 키 · 계정: 엔진 자체는 없음

## 링크

- [docs/README.md](docs/README.md) — 문서 안내 (한국어)
- [docs/PLAN.md](docs/PLAN.md) — 구현 계획 · 검증 기록 · 지원 한계 (한국어)
- [docs/DECISIONS.md](docs/DECISIONS.md) — 설계 결정 기록 (한국어)
- [examples/explicit_consumer.py](examples/explicit_consumer.py) — 쓰는 쪽 이벤트 어댑터 예시
- [rag-consumer](../rag-consumer/README.ko.md) — 이 엔진에 대화 기록을 넣는 짝 팩
- [AI Feature Pack 목록](../../README.ko.md)
