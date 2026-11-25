<div align="center">

# memory-system

**OpenClaw 에이전트에 3층 기억 구조를 세팅합니다 — 워크스페이스 메모리 파일, 세컨드브레인 Obsidian 볼트, 볼트 전체를 찾는 메모리 검색(NotebookLM 은 선택).**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- 에이전트가 대화 · 결정 · 교훈을 장기기억 `MEMORY.md` 와 데일리 노트 `memory/YYYY-MM-DD.md` 에 쌓습니다.
- Obsidian 볼트에 폴더 구조(Daily · News-Links · Meetings · People · Projects · Reference · Ideas · Archive 등)와 `HOME.md` · 인덱스 노트를 만듭니다.
- 볼트 전체를 에이전트의 메모리 검색 범위에 넣습니다(`extraPaths` · OpenAI 임베딩 · 파일 변경 감시).
- 데일리 노트와 `MEMORY.md` 를 볼트 `Daily/` 에 미러합니다(심볼릭 링크 또는 주기 복사).
- 뉴스 링크는 노트로, 대화 기록은 인물 프로필로 쌓습니다.
- 선택: `nlm` CLI 로 볼트 문서를 NotebookLM 소스로 넣고 소스 기반 Q&A 를 합니다.

## 빠른 시작

```bash
# 1) OpenClaw 에이전트에게: "feature-pack/memory-system/INSTALL.md 를 읽고 설치해줘"
# 2) 설치가 끝나면 확인
ls ~/.openclaw/workspace/MEMORY.md
obsidian-cli print-default
```

## 설치

에이전트에게 맡기려면 «`feature-pack/memory-system/INSTALL.md` 를 읽고 설치해줘» 라고 말하세요. `INSTALL.md` 는 OpenClaw 에이전트가 읽고 스스로 설치하는 프롬프트입니다. `{{PLACEHOLDER}}` 를 만나면 에이전트가 사용자에게 물어서 채웁니다.

| 자리표시 | 뜻 | 기본값 |
|---|---|---|
| `{{OC_WORKSPACE}}` | OpenClaw 워크스페이스 경로 | `~/.openclaw/workspace` |
| `{{VAULT_PATH}}` | Obsidian 볼트 절대 경로 | — |
| `{{VAULT_NAME}}` | Obsidian 볼트 이름(폴더 이름) | — |

설치 차례: ① 워크스페이스 메모리 파일 ② 볼트 폴더 구조 + obsidian-cli ③ 메모리 검색 통합 ④ `TOOLS.md` 에 Obsidian 항목 ⑤ 데일리 메모리 미러 ⑥ NotebookLM 연동(선택) ⑦ 설치 검증. 손으로 할 때 핵심 명령은 아래와 같습니다.

```bash
brew install yakitrak/yakitrak/obsidian-cli
obsidian-cli set-default "my-vault"
# openclaw.json 을 고친 뒤 설정 반영
openclaw gateway restart
```

## 사용법

### 3층 구조

| 층 | 무엇 | 자리 |
|---|---|---|
| 1 · 워크스페이스 메모리 | 장기기억(큐레이션) + 데일리 노트(원본 로그) | `MEMORY.md` · `memory/*.md` |
| 2 · Obsidian 볼트 | 데일리 미러 · 링크 노트 · 대화 기록 · 인물 프로필 | `Daily/memory/` · `News-Links/` · `Meetings/` · `People/` |
| 3 · NotebookLM(선택) | 소스 기반 Q&A | `nlm` CLI |

### 세션 규칙

- 세션을 시작하면 `exec("ls memory/")` 로 파일 목록을 보고, 오늘 · 어제 데일리 노트를 읽습니다. 메인 세션이면 `MEMORY.md` 도 읽습니다.
- `read("memory")` 처럼 폴더를 통째로 읽지 않습니다(EISDIR 오류). 파일을 하나씩 읽습니다.
- 데일리 노트에 개인정보 · API 키를 적지 않습니다. `MEMORY.md` 는 그룹 채팅에서 불러오지 않습니다.
- 데일리 노트의 중요한 내용은 주기적으로 `MEMORY.md` 로 옮겨 정리합니다.

### 메모리 검색 설정

`openclaw.json` 에 넣는 설정입니다. `OPENAI_API_KEY` 가 OpenClaw 환경 변수나 설정에 있어야 합니다.

```json
{
  "agents": {
    "defaults": {
      "memorySearch": {
        "enabled": true,
        "sources": ["memory", "sessions"],
        "extraPaths": ["{{VAULT_PATH}}"],
        "provider": "openai",
        "model": "text-embedding-3-small",
        "sync": { "watch": true, "watchDebounceMs": 1500 },
        "query": {
          "hybrid": { "enabled": true, "vectorWeight": 0.7, "textWeight": 0.3, "candidateMultiplier": 4 }
        }
      }
    }
  }
}
```

### NotebookLM

`notebooklm` 팩이 있어야 하는 선택 단계입니다. 없으면 건너뜁니다.

```bash
nlm notebook create "my-vault Knowledge Base"
nlm source add <notebook-id> --file "<vault-path>/HOME.md"
nlm chat query <notebook-id> "이 프로젝트에서 가장 중요한 결정은?"
```

### 문제 해결

- 메모리 검색에 볼트 파일이 안 나오면: `extraPaths` 의 볼트 절대 경로 · `watch: true` · OpenAI API 키를 확인하고 `openclaw gateway restart` 를 돌립니다. 볼트가 크면 인덱싱에 수 분 ~ 수십 분이 걸릴 수 있습니다.
- obsidian-cli 가 볼트를 못 찾으면: `obsidian-cli set-default` 를 다시 돌리고, Obsidian 앱에서 그 볼트를 한 번 이상 열었는지 봅니다.
- iCloud 볼트는 심볼릭 링크가 동기화되지 않을 수 있습니다. 그때는 주기 복사(rsync)로 미러합니다.
- NotebookLM 인증이 안 되면 `notebooklm` 팩의 인증 단계를 봅니다(Chrome 필요).

## 요구사항

- macOS(Apple Silicon 또는 Intel)
- OpenClaw 설치 + 실행 중
- Obsidian 앱 · obsidian-cli(Homebrew)
- API 키 · 계정: OpenAI API 키(임베딩 `text-embedding-3-small`) · 선택: `nlm` CLI 와 Google 계정(NotebookLM)
- 설치 시간: 약 15분

## 링크

- [INSTALL.md](INSTALL.md)
- [skill/SKILL.md](skill/SKILL.md) — 에이전트 스킬
- [obsidian/setup.md](obsidian/setup.md)
- [test/verify.md](test/verify.md)
- [notebooklm 팩](../notebooklm/)
- [AI Feature Pack 목록](../../README.ko.md)
