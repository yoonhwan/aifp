<div align="center">

# obsidian-cli

**에이전트가 Obsidian 볼트(Markdown 노트)를 CLI 로 조회 · 검색 · 생성 · 수정 · 삭제 · 이동하게 합니다**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ko.md) 의 팩입니다. 팩은 서로 독립이라 필요한 것만 설치하면 됩니다.

## 무엇을 하나요

- 조회: 볼트의 파일 · 폴더 목록을 보고 노트 내용을 읽습니다.
- 검색: 노트 이름 퍼지 검색 · 노트 내용 검색.
- 생성: 노트를 만들고(없는 폴더는 함께 만듦) 데일리 노트를 엽니다.
- 수정: 덮어쓰기 · 덧붙이기(append) · frontmatter 조회 · 수정 · 키 삭제.
- 삭제 · 이동: 노트를 지우고, 옮기거나 이름을 바꾸면 위키링크를 자동으로 고칩니다.
- 에이전트가 `.md` 파일을 `read` / `write` / `edit` 도구로 바로 고쳐도 됩니다. Obsidian 이 변경을 알아챕니다.

## 빠른 시작

```bash
brew install yakitrak/yakitrak/obsidian-cli
obsidian-cli set-default "my-vault"
obsidian-cli create "Projects/my-note" --content "# My note"
obsidian-cli print "Projects/my-note"
```

## 설치

### 에이전트에게 맡기기

에이전트에게 «`feature-pack/obsidian-cli/INSTALL.md` 를 읽고 설치해 줘» 라고 하면 됩니다. 설치 시간은 약 3분입니다. 에이전트가 볼트 이름을 묻습니다.

### 직접 설치

```bash
# 1. CLI 설치 — v0.2.3 이상
brew install yakitrak/yakitrak/obsidian-cli
obsidian-cli --version

# 2. 기본 볼트 지정 — Obsidian 이 아는 볼트 목록은 이 파일에 있음
cat ~/Library/Application\ Support/obsidian/obsidian.json
obsidian-cli set-default "my-vault"
obsidian-cli print-default

# 3. 스킬 — OpenClaw 공식 obsidian 스킬이 있으면 복사하지 않음
ls /opt/homebrew/lib/node_modules/openclaw/skills/obsidian/SKILL.md
mkdir -p ~/.openclaw/workspace/skills/obsidian/
cp skill/SKILL.md ~/.openclaw/workspace/skills/obsidian/SKILL.md
```

4. `config/tools-section.md` 를 보고 OpenClaw 워크스페이스의 `TOOLS.md` 에 Obsidian CLI 절(바이너리 경로 · 기본 볼트 · 주요 명령)을 더합니다.
5. 선택: Obsidian 앱에서 Daily notes(Core plugin)를 켭니다. 추천 Community plugin 은 Dataview · Templater · Calendar 입니다(`obsidian/setup.md`).
6. `test/verify.md` 의 CRUD 시험을 돌립니다. 모든 단계가 exit code 0 이면 설치 끝입니다.

## 사용법

### 명령

| 명령 | 하는 일 |
|---|---|
| `obsidian-cli set-default "<vault>"` · `print-default [--path-only]` | 기본 볼트 지정 · 확인 |
| `obsidian-cli list ["<folder>"]` | 볼트 루트 또는 폴더 목록 |
| `obsidian-cli print "<note>"` | 노트 읽기 |
| `obsidian-cli search "<query>"` · `search-content "<query>"` | 이름 퍼지 검색 · 내용 검색(인터랙티브) |
| `obsidian-cli create "<note>" --content "<text>" [--open]` | 노트 만들기(폴더 자동 생성) |
| `obsidian-cli create "<note>" --content "<text>" --overwrite` · `--append` | 덮어쓰기 · 덧붙이기 |
| `obsidian-cli daily` | 데일리 노트 만들기 · 열기 |
| `obsidian-cli frontmatter "<note>" --print` | frontmatter 보기 |
| `obsidian-cli frontmatter "<note>" --edit --key <k> --value <v>` · `--delete --key <k>` | frontmatter 수정 · 키 삭제 |
| `obsidian-cli move "<old>" "<new>"` | 옮기기 · 이름 바꾸기 + 위키링크 갱신 |
| `obsidian-cli delete "<note>"` | 지우기 |
| `obsidian-cli open "<note>"` | Obsidian 앱에서 열기 |

### 사용 요령

- `search` · `search-content` 는 인터랙티브라 에이전트 환경에서는 안 돕니다. `grep -r` 이나 `list` + `print` 를 씁니다.
- 노트를 옮길 때는 `mv` 대신 꼭 `move` 를 씁니다. `mv` 는 위키링크를 깨뜨립니다.
- 볼트 경로를 박아 넣지 말고 `print-default --path-only` 로 받아 씁니다.
- `.obsidian/` 폴더는 건드리지 않습니다(설정 · 플러그인 충돌).
- 많은 노트를 한꺼번에 고칠 때는 CLI 보다 파일을 바로 고치는 편이 빠릅니다.

### 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| `brew: command not found` | Homebrew 없음 | Homebrew 설치 |
| `Cannot find note in vault` | 기본 볼트 미지정 · 노트 경로 오류 | `set-default` 확인, 경로에서 `.md` 빼기 |
| `search-content` 가 안 됨 | 비인터랙티브 환경 | `grep -r` 또는 `list` + `print` |
| 만든 노트가 Obsidian 에 안 보임 | iCloud 동기화 지연 | 몇 초 기다린 뒤 앱에서 새로고침 |
| URI handler 오류 | Obsidian 앱이 꺼져 있음 | 앱을 켜고 다시 시도 |

## 요구사항

- OS: macOS
- Homebrew
- Obsidian 앱(URI handler) · 볼트 1개 이상
- API 키 · 계정: 없음

## 링크

- [INSTALL.md](INSTALL.md) — 에이전트용 설치 안내
- [skill/SKILL.md](skill/SKILL.md) — OpenClaw 스킬
- [config/tools-section.md](config/tools-section.md) — `TOOLS.md` 에 더할 절
- [obsidian/setup.md](obsidian/setup.md) — Obsidian 앱 설정
- [test/verify.md](test/verify.md) — 설치 검증 CRUD 시험
- [AI Feature Pack 목록](../../README.ko.md)
