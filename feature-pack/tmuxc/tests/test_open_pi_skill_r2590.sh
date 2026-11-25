#!/usr/bin/env bash
# test_open_pi_skill_r2590.sh — r2590 «tmuxc open --pi-skill» 계약 시험.
#   카드: design/harness/indices/대기/r2590-tmuxc-pi-skill-args-passthrough.md
#   원칙(하드 룰 22): 시험 1개 70초 · sleep 0 · 실제 tmux 세션 0 — --dry-run 출력만 본다.
#   칸: ① 차례대로 붙는다 ② 옵션 없으면 기준판과 같은 글자 ③ pi 아닌 agent 거부
#       ④ 없는 경로 거부 ⑤ SKILL.md 없는 폴더 거부 ⑥ 값 없는 --pi-skill 거부
#       ⑦ 빈칸 든 경로도 한 인자 ⑧ SKILL.md 파일 직접 ⑨ --model/--effort 와 공존
#       변이 M1~M5(각각 죽어야 함)
set -uo pipefail
export LC_ALL=C

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")" && pwd)"
PKG="$(cd -- "$HERE/.." && pwd)"
TMUXC="$PKG/core/bin/tmuxc"
[ -f "$TMUXC" ] || { echo "FAIL tmuxc 없음: $TMUXC"; exit 1; }

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); printf 'ok   %s\n' "$*"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL %s\n' "$*"; }

T="$(mktemp -d "${TMPDIR:-/tmp}/r2590.XXXXXX")" || exit 1
trap 'rm -rf "$T"' EXIT

# ── 픽스처 ────────────────────────────────────────────────────────────────────
repo="$T/repo"
mkdir -p "$repo"
git -C "$repo" init -q 2>/dev/null || true
skA="$T/skills-a"; skB="$T/skills-b"; sp="$T/skill dir"
mkdir -p "$skA" "$skB" "$sp"
: > "$skA/SKILL.md"; : > "$skB/SKILL.md"; : > "$sp/SKILL.md"
nofile="$T/skills-x"; mkdir -p "$nofile"
name="r2590probe"

cmd_of() { sed -n 's/^command=//p' <<<"$1" | head -1; }
# open 은 pi --session-id 를 매번 새로 뽑는다(실측) — 그 값만 가리고 글자를 대조한다(카드 ②).
mask_sid() { sed -E 's/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/<SID>/g' <<<"$1"; }

# ── 칸 ①~⑨ (도구 경로를 받는다 — 변이 사본에 같은 칸을 돌린다) ─────────────────
c1() {  # ① --pi-skill 둘 → «--no-skills --skill A --skill B» 차례대로 1번
  local out
  out="$("$1" open "$repo" --name "$name" --agent pi --pi-skill "$skA" --pi-skill "$skB" --dry-run 2>&1)" || return 1
  local c; c="$(cmd_of "$out")"
  [[ "$c" == *"--no-skills --skill $skA --skill $skB"* ]] || return 1
  local n; n="$(tr ' ' '\n' <<<"$c" | grep -c '^--no-skills$')"
  [[ "$n" == 1 ]]
}

c2() {  # ② 옵션 없음 → 기준판 command= 줄과 같은 글자(session-id 값만 가린다)
  local base="${TMUXC_BASELINE:-$HOME/.tmuxc/versions/0.4.12/core/bin/tmuxc}"
  [[ -x "$base" ]] || return 2
  local cur out; out="$("$1" open "$repo" --name "$name" --agent pi --dry-run 2>&1)" || return 1
  cur="$(mask_sid "$(cmd_of "$out")")"
  local ref refout; refout="$("$base" open "$repo" --name "$name" --agent pi --dry-run 2>&1)" || return 1
  ref="$(mask_sid "$(cmd_of "$refout")")"
  [[ -n "$cur" && "$cur" == "$ref" ]] || return 1
  [[ "$cur" != *"--no-skills"* ]]
}

c3() {  # ③ agent 가 pi 가 아님 → 거부 rc≠0 · 세션 0
  local out rc
  out="$("$1" open "$repo" --name "$name" --agent claude --pi-skill "$skA" --dry-run 2>&1)"; rc=$?
  [[ "$rc" -ne 0 ]] || return 1
  [[ "$out" == *"--pi-skill 은 --agent pi 에서만"* ]] || return 1
  ! tmux has-session -t "$name" >/dev/null 2>&1
}

c4() {  # ④ 없는 경로 → 거부
  local out rc
  out="$("$1" open "$repo" --name "$name" --agent pi --pi-skill "$T/nope" --dry-run 2>&1)"; rc=$?
  [[ "$rc" -ne 0 && "$out" == *"경로가 없다"* ]]
}

c5() {  # ⑤ SKILL.md 없는 폴더 → 거부
  local out rc
  out="$("$1" open "$repo" --name "$name" --agent pi --pi-skill "$nofile" --dry-run 2>&1)"; rc=$?
  [[ "$rc" -ne 0 && "$out" == *"SKILL.md 가 없다"* ]]
}

c6() {  # ⑥ 값 없이 끝난 --pi-skill → 거부
  local out rc
  out="$("$1" open "$repo" --name "$name" --agent pi --pi-skill 2>&1)"; rc=$?
  [[ "$rc" -ne 0 && "$out" == *"--pi-skill 값 없음"* ]]
}

c7() {  # ⑦ 빈칸 든 경로 → %q 로 한 인자
  local out c; out="$("$1" open "$repo" --name "$name" --agent pi --pi-skill "$sp" --dry-run 2>&1)" || return 1
  c="$(cmd_of "$out")"
  [[ "$c" == *"--skill $(printf '%q' "$sp")"* ]]
}

c8() {  # ⑧ SKILL.md 파일 경로 직접 → 받는다
  local out c; out="$("$1" open "$repo" --name "$name" --agent pi --pi-skill "$skA/SKILL.md" --dry-run 2>&1)" || return 1
  c="$(cmd_of "$out")"
  [[ "$c" == *"--no-skills --skill $skA/SKILL.md"* ]]
}

c9() {  # ⑨ --model · --effort 와 같이 줘도 셋 다 명령에 있다
  local out c
  out="$("$1" open "$repo" --name "$name" --agent pi --model "mdl-x" --effort high --pi-skill "$skA" --dry-run 2>&1)" || return 1
  c="$(cmd_of "$out")"
  [[ "$c" == *"--model mdl-x"* && "$c" == *"--thinking high"* && "$c" == *"--no-skills --skill $skA"* ]]
}

run() {  # run <번호> <설명> <함수>
  if "$3" "$TMUXC"; then pass "$1 $2"; else fail "$1 $2"; fi
}

run ① "pi-skill 둘 → --no-skills --skill A --skill B 차례대로 1번" c1
case "$(c2 "$TMUXC"; echo rc=$?)" in
  *rc=0) pass "② 옵션 없음 → 기준판 command= 줄과 같은 글자(0.4.12)" ;;
  *rc=2) fail "② 기준판 tmuxc 없음 — TMUXC_BASELINE 또는 ~/.tmuxc/versions/0.4.12 필요" ;;
  *) fail "② 옵션 없음 명령이 기준판과 다르다" ;;
esac
run ③ "agent claude + --pi-skill → 거부 rc≠0 · 세션 0" c3
run ④ "없는 경로 → 거부 rc≠0" c4
run ⑤ "SKILL.md 없는 폴더 → 거부 rc≠0" c5
run ⑥ "값 없는 --pi-skill → 거부 rc≠0" c6
run ⑦ "빈칸 든 경로 → 한 인자로 감싸짐" c7
run ⑧ "SKILL.md 파일 직접 → 받는다" c8
run ⑨ "--model·--effort 와 공존" c9

# ── 변이 M1~M5 — 사본을 고쳐 그 칸이 Red 로 뒤집히는지 본다 ────────────────────
mutate() {  # mutate <이름> <python 조각>
  local m="$T/tmuxc-$1"
  cp "$TMUXC" "$m"
  python3 - "$m" "$1" <<'PY'
import sys
p, tag = sys.argv[1], sys.argv[2]
s = open(p, encoding="utf-8").read()
edits = {
    "m1": ('    cmd="$cmd --no-skills"\n', ''),
    "m2": ('  if [[ ${#PI_SKILL_PATHS[@]} -gt 0 ]]; then', '  if true; then'),
    "m3": ('    [[ "$agent" == "pi" ]] || die "--pi-skill 은 --agent pi 에서만 사용 (agent=$agent)"\n', ''),
    "m4": ('        if [[ -d "$sk" ]]; then\n'
           '          [[ -f "$sk/SKILL.md" ]] || die "--pi-skill 폴더에 SKILL.md 가 없다: $sk"\n'
           '        elif [[ ! -f "$sk" ]]; then\n'
           '          die "--pi-skill 경로가 없다: $sk"\n'
           '        fi\n', '        :\n'),
    "m5": ('cmd="$cmd --skill $(printf \'%q\' "$sk")"', 'cmd="$cmd --skill $sk"'),
}
old, new = edits[tag]
assert old in s, f"변이 지점 없음: {tag}"
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
PY
  chmod +x "$m"
  printf '%s' "$m"
}

mut_check() {  # mut_check <이름> <칸번호> <함수>
  local m; m="$(mutate "$1")"
  if "$3" "$m"; then fail "변이 $1 미검출 — $2 가 초록으로 남았다(죽어야 한다)"
  else pass "변이 $1 검출 — $2 Red"; fi
}

mut_check m1 "①" c1
mut_check m2 "②" c2
mut_check m3 "③" c3
mut_check m4 "⑤" c5
mut_check m5 "⑦" c7

echo "---"
if [ "$FAIL" = 0 ]; then echo "ALL PASS"; exit 0; fi
echo "FAILED $FAIL"
exit 1
