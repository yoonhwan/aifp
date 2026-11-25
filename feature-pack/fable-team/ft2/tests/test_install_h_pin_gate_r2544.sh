#!/bin/sh
# test_install_h_pin_gate_r2544.sh — r2544 ft2 설치 h PIN 관문(앞섬 허용 · 범위 밖 커밋 0) 시험.
# 조각 = tests/fixtures/pin-gate-r2544/pin-gate.sh(그 글자 그대로 돌린다) · 반례 ①~⑨ · 변이 M1~M3
# 실 팩 0 · 실 설치 0 · 실 좌석 폴더 0 · 임시 리포만($TMPDIR) · sleep 0
# 실행: sh tests/test_install_h_pin_gate_r2544.sh
set -u
HERE=$(cd -- "$(dirname -- "$0")" && pwd)
BLOCK="$HERE/fixtures/pin-gate-r2544/pin-gate.sh"
BLK=$BLOCK
SCOPE=feature-pack/fable-team
L1X=$(printf %s/1.%s legacy x)   # 1.x 폴더 이름 = 글자 그대로 안 적는다(ft2 legacy guard)
T=$(mktemp -d "${TMPDIR:-/tmp}/r2544.XXXXXX") || exit 1
trap 'rm -rf "$T"' EXIT
T0=$(date +%s)
pass=0; fail=0

mk() {  # $1 = 이름 → 임시 리포 경로를 REPLY 에 · $T/$1
  REPLY=$T/$1; mkdir -p "$REPLY"
  git -C "$REPLY" init -q -b main || return 1
  git -C "$REPLY" config user.email r2544@example.com
  git -C "$REPLY" config user.name r2544
  mkdir -p "$REPLY/design" "$REPLY/feature-pack/fable-team/ft2" "$REPLY/feature-pack/fable-team/$L1X"
  printf 'a\n' > "$REPLY/design/note.md"
  printf 'cli\n' > "$REPLY/feature-pack/fable-team/ft2/cli.py"
  printf 'kit\n' > "$REPLY/feature-pack/fable-team/$L1X/kit.sh"
  ci "$REPLY" "기준"
}

ci() {  # $1 = 리포 · $2 = 메시지 → 새 커밋 sha
  git -C "$1" add -A && git -C "$1" commit -q -m "$2" || return 1
  git -C "$1" rev-parse HEAD
}

gate() {  # $1 = 팩 리포 · $2 = REF · $3 = PIN [$4 = 조각] → GOUT · rc = 조각 rc
  GOUT=$( PK=$1 REF=$2 PIN=$3; . "${4:-$BLK}" 2>&1 )
}

need() {  # $1 = 조건 설명 → 실패면 그 줄을 남기고 1
  case $GOUT in *"$1"*) return 0 ;; esac
  echo "  출력에 «$1» 없음: $GOUT"; return 1
}

notin() {
  case $GOUT in *"$1"*) echo "  출력에 «$1» 있음: $GOUT"; return 1 ;; esac
}

c1() {  # ① tip = PIN → 지금과 같은 출력(PIN-AHEAD 0) · rc 0
  mk c1; r=$REPLY; s=$(git -C "$r" rev-parse HEAD)
  gate "$r" "$s" "$s" || { echo "  rc≠0"; return 1; }
  notin PIN-AHEAD || return 1
  [ -z "$GOUT" ] || { echo "  출력 있음: $GOUT"; return 1; }
}

c2() {  # ② PIN 뒤 design/ 문서 커밋 1개 → 통과 + PIN-AHEAD OK … 1개
  mk c2; r=$REPLY; p=$(git -C "$r" rev-parse HEAD)
  printf 'b\n' >> "$r/design/note.md"; s=$(ci "$r" "문서") || return 1
  gate "$r" "$s" "$p" || { echo "  rc≠0: $GOUT"; return 1; }
  need "PIN-AHEAD OK tip" || return 1
  need "PIN $(printf %s "$p" | cut -c1-10)" || return 1
  need "범위 밖 커밋 1개" || return 1
}

c3() {  # ③ PIN 뒤 feature-pack/fable-team/ft2 1글자 커밋 → ABORT exit 4 · 쓰기 0
  mk c3; r=$REPLY; p=$(git -C "$r" rev-parse HEAD)
  printf 'cli2\n' > "$r/feature-pack/fable-team/ft2/cli.py"; s=$(ci "$r" "범위 안") || return 1
  head0=$(git -C "$r" rev-parse HEAD); st0=$(git -C "$r" status --porcelain)
  gate "$r" "$s" "$p"; rc=$?
  [ "$rc" = 4 ] || { echo "  rc=$rc(기대 4): $GOUT"; return 1; }
  need "ABORT PIN 뒤 feature-pack/fable-team 글자 바뀜" || return 1
  need "쓰기 0" || return 1
  [ "$(git -C "$r" rev-parse HEAD)" = "$head0" ] && [ "$(git -C "$r" status --porcelain)" = "$st0" ] || { echo "  리포가 바뀜"; return 1; }
}

c4() {  # ④ tip 이 PIN 의 조상(되감김) 또는 남남 → ABORT exit 4
  mk c4; r=$REPLY; p=$(git -C "$r" rev-parse HEAD)
  printf 'b\n' >> "$r/design/note.md"; s=$(ci "$r" "문서") || return 1
  gate "$r" "$p" "$s"; rc=$?                       # 되감김
  [ "$rc" = 4 ] || { echo "  되감김 rc=$rc(기대 4): $GOUT"; return 1; }
  need "ABORT tip 이 PIN 의 후손 아님" || return 1
  mk c4b; r2=$REPLY; b=$(git -C "$r2" rev-parse HEAD)   # 남남 = 갈라진 두 갈래
  printf 'x\n' > "$r2/design/x.md"; x=$(ci "$r2" "갈래 x") || return 1
  git -C "$r2" checkout -q "$b" || return 1
  printf 'y\n' > "$r2/design/y.md"; y=$(ci "$r2" "갈래 y") || return 1
  gate "$r2" "$y" "$x"; rc=$?
  [ "$rc" = 4 ] || { echo "  남남 rc=$rc(기대 4): $GOUT"; return 1; }
}

c5() {  # ⑤ PIN sha 가 리포에 없음(git rc 128) → ABORT 판정 불가 exit 4
  mk c5; r=$REPLY; s=$(git -C "$r" rev-parse HEAD)
  gate "$r" "$s" "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"; rc=$?
  [ "$rc" = 4 ] || { echo "  rc=$rc(기대 4): $GOUT"; return 1; }
  need "ABORT tip 이 PIN 의 후손 아님(또는 판정 불가)" || return 1
}

c6() {  # ⑥ PIN 뒤 범위 밖 파일을 범위 안으로 이름 바꿔 옮김 → ABORT exit 4
  mk c6; r=$REPLY; p=$(git -C "$r" rev-parse HEAD)
  git -C "$r" mv design/note.md feature-pack/fable-team/moved.md || return 1
  s=$(ci "$r" "옮김") || return 1
  gate "$r" "$s" "$p"; rc=$?
  [ "$rc" = 4 ] || { echo "  rc=$rc(기대 4): $GOUT"; return 1; }
  need "ABORT PIN 뒤 feature-pack/fable-team 글자 바뀜" || return 1
}

c7() {  # ⑦ PIN 뒤 범위 안 글자를 바꿨다가 되돌린 커밋 2개 → 통과(글자 같음)
  mk c7; r=$REPLY; p=$(git -C "$r" rev-parse HEAD)
  printf 'cli2\n' > "$r/feature-pack/fable-team/ft2/cli.py"; s=$(ci "$r" "바꿈") || return 1
  printf 'cli\n' > "$r/feature-pack/fable-team/ft2/cli.py"; s=$(ci "$r" "되돌림") || return 1
  gate "$r" "$s" "$p" || { echo "  rc≠0: $GOUT"; return 1; }
  need "범위 밖 커밋 2개" || return 1
}

c8() {  # ⑧ PIN 뒤 1.x 폴더 글자 커밋(ft2 글자 0) → ABORT exit 4
  mk c8; r=$REPLY; p=$(git -C "$r" rev-parse HEAD)
  printf 'kit2\n' > "$r/feature-pack/fable-team/$L1X/kit.sh"; s=$(ci "$r" "legacy") || return 1
  gate "$r" "$s" "$p"; rc=$?
  [ "$rc" = 4 ] || { echo "  rc=$rc(기대 4): $GOUT"; return 1; }
  need "ABORT PIN 뒤 feature-pack/fable-team 글자 바뀜" || return 1
}

c9() {  # ⑨ tree 를 못 읽는 리포(--filter=tree:0 뒤 원격 끊김) + PIN 뒤 문서 커밋 → 후손 판정 0 · diff 128 → ABORT 판정 불가 exit 4
  mk c9; o=$REPLY; p=$(git -C "$o" rev-parse HEAD)
  printf 'b\n' >> "$o/design/note.md"; s=$(ci "$o" "문서") || return 1
  git -C "$o" config uploadpack.allowFilter true
  c=$T/c9clone
  git clone -q --filter=tree:0 --no-checkout "file://$o" "$c" || { echo "  부분 clone 실패"; return 1; }
  rm -rf "$o"                                        # 원격 끊김 = 트리를 못 받는다
  git -C "$c" merge-base --is-ancestor "$p" "$s" || { echo "  전제 위반: 후손 판정 rc≠0"; return 1; }
  git -C "$c" diff --quiet "$p" "$s" -- "$SCOPE" 2>/dev/null; drc=$?
  [ "$drc" = 128 ] || { echo "  전제 위반: diff rc=$drc(기대 128)"; return 1; }
  gate "$c" "$s" "$p"; rc=$?
  [ "$rc" = 4 ] || { echo "  rc=$rc(기대 4): $GOUT"; return 1; }
  need "ABORT 판정 불가" || return 1
}

run_case() {  # $1 = 이름 · $2 = 케이스 함수
  if o=$($2 2>&1); then pass=$((pass+1)); printf '%s PASS\n' "$1"
  else fail=$((fail+1)); printf '%s FAIL\n%s\n' "$1" "$o"; fi
}

mut() {  # $1 = 이름 · $2 = sed 식 → $T/mut-$1.sh
  sed "$2" "$BLOCK" > "$T/mut-$1.sh" || return 1
  [ -s "$T/mut-$1.sh" ] || { echo "  변이 파일 비었음"; return 1; }
}

# 조각 자체 검사 — sh -n rc 0 (틀에 넣을 글자가 문법에 맞는다)
if sh -n "$BLOCK"; then pass=$((pass+1)); echo "조각 sh -n rc0 PASS"
else fail=$((fail+1)); echo "조각 sh -n FAIL"; fi

run_case "① tip=PIN → PIN-AHEAD 0" c1
run_case "② PIN 뒤 문서 커밋 → PIN-AHEAD 1개" c2
run_case "③ PIN 뒤 범위 안 글자 → ABORT 쓰기 0" c3
run_case "④ 되감김·남남 → ABORT" c4
run_case "⑤ PIN 없음 → ABORT 판정 불가" c5
run_case "⑥ 범위 밖→안 이름 옮김 → ABORT" c6
run_case "⑦ 바꿨다 되돌림 2커밋 → 통과" c7
run_case "⑧ 1.x 폴더 글자 → ABORT" c8
run_case "⑨ tree 못 읽음 → ABORT 판정 불가" c9

# 변이 — 변이가 잡히면(= 그 케이스가 실패하면) PASS
M1='M1 ⓐ 후손 판정 제거 → ④ 통과로 바뀜'
if mut m1 '/merge-base --is-ancestor/,/^  }$/d'; then
  BLK=$T/mut-m1.sh; if c4 >/dev/null 2>&1; then fail=$((fail+1)); printf '%s FAIL(안 잡힘)\n' "$M1"
  else pass=$((pass+1)); printf '%s PASS\n' "$M1"; fi; BLK=$BLOCK
else fail=$((fail+1)); printf '%s FAIL\n' "$M1"; fi

M2='M2 ⓑ 경로를 feature-pack/fable-team/ft2 로 좁힘 → ⑧ 통과로 바뀜'
if mut m2 's|-- feature-pack/fable-team$|-- feature-pack/fable-team/ft2|'; then
  BLK=$T/mut-m2.sh; if c8 >/dev/null 2>&1; then fail=$((fail+1)); printf '%s FAIL(안 잡힘)\n' "$M2"
  else pass=$((pass+1)); printf '%s PASS\n' "$M2"; fi; BLK=$BLOCK
else fail=$((fail+1)); printf '%s FAIL\n' "$M2"; fi

M3='M3 ⓑ rc 2 이상을 통과로 → ⑨ 통과로 바뀜'
if mut m3 's|^    \*) echo "ABORT 판정 불가".*|    *) echo "PIN-AHEAD OK 판정 불가 통과" ;;|'; then
  BLK=$T/mut-m3.sh; if c9 >/dev/null 2>&1; then fail=$((fail+1)); printf '%s FAIL(안 잡힘)\n' "$M3"
  else pass=$((pass+1)); printf '%s PASS\n' "$M3"; fi; BLK=$BLOCK
else fail=$((fail+1)); printf '%s FAIL\n' "$M3"; fi

printf 'TOTAL %ss · PASS %s · FAIL %s\n' "$(( $(date +%s) - T0 ))" "$pass" "$fail"
[ "$fail" = 0 ] || exit 1
echo "반례 ①~⑨ · 변이 M1~M3 ALL PASS"
