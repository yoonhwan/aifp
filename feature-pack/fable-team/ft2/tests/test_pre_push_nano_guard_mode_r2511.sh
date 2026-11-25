#!/bin/sh
# r2511 pre-push 나노 가드 실행 비트 시험 — 반례 ①~⑫ · 변이 M1~M5.
# 공통 대역 = tests/pre_push_nano_guard_r2383_lib.sh(임시 bare 리포 · 가짜 나노 env) · 카드 대역 = 그 리포 origin/ops/main-base.
# 실 원격 0 · 실 tmux 0 · sleep 0 · FT2_ROOTS_TSV = 빈 파일(실 기계 카드에 기대지 않는다).
# 실행: sh tests/test_pre_push_nano_guard_mode_r2511.sh
. "$(dirname "$0")/pre_push_nano_guard_r2383_lib.sh"

pushm() {   # $1 = d · $2 = FT2_HOLDER 값 · 나머지 = refspec → $1/push.out · rc · roots 명부는 빈 파일로 고정
  d=$1; holder=$2; shift 2
  : > "$d/roots.tsv"
  ( cd "$d/c" && env FT2_HOLDER="$holder" FT_SEAT_NAME= TMPDIR="$d/tmp" GUARD_CALLS="$d/calls" FT2_ROOTS_TSV="$d/roots.tsv" PATH="$d/bin:$PATH" ${EXECP:+"GIT_EXEC_PATH=$EXECP"} git push origin "$@" ) >"$d/push.out" 2>&1
}
x755() {   # $1 = 경로 → 실행 비트 파일 1개(인덱스 모드 = 파일시스템 모드)
  mkdir -p "$(dirname "$1")"
  printf '#!/bin/sh\necho x\n' > "$1"
  chmod 755 "$1"
}
mcard() {   # $1 = d · $2 = 카드 번호 · $3 = «- 대상» 줄 · $4 = 카드 이름 꼬리 → origin/ops/main-base 카드 1장 + 클론 ref
  ( cd "$1/c" || return 1
    if git rev-parse -q --verify refs/remotes/origin/ops/main-base >/dev/null 2>&1; then
      g checkout -q -B "card$2$4" refs/remotes/origin/ops/main-base >/dev/null 2>&1 || return 1
    else
      g checkout -q -b "card$2$4" >/dev/null 2>&1 || return 1
    fi
    mkdir -p design/harness/indices/대기 || return 1
    printf '# 인덱스: r%s-%s\n%s\n' "$2" "$4" "$3" > "design/harness/indices/대기/r$2-$4.md" || return 1
    g add -A >/dev/null 2>&1 && g commit -q -m "카드 r$2-$4" >/dev/null 2>&1 || return 1
    env FT2_HOLDER= FT_SEAT_NAME= git -c user.name=t -c user.email=t@t push -q origin HEAD:refs/heads/ops/main-base >/dev/null 2>&1 || return 1
    g checkout -q - >/dev/null 2>&1 ) >/dev/null 2>&1 || return 1
  g -C "$1/c" fetch -q origin ops/main-base:refs/remotes/origin/ops/main-base >/dev/null 2>&1
}
DENY1='PUSH_DENIED 실행 비트 bin/ft-seat-resolve.py — 고침: git update-index --chmod=-x "bin/ft-seat-resolve.py" && chmod 644 "bin/ft-seat-resolve.py" && git commit -m "[chore] mode 100644"'

c1() {   # ① r2494 재생: 새 bin/ft-seat-resolve.py 100755 · 카드 예외 0 → PUSH_DENIED + 고침 줄 · rc 1
  MK_HOOK=$1; d=$(mk "c1$2") || return 1
  x755 "$d/c/bin/ft-seat-resolve.py"; mkc "$d" "새 실행 파일" || return 1
  pushm "$d" "$NANO" HEAD:refs/heads/nano/r9001-x; rc=$?
  [ "$rc" != 0 ] || { echo "  rc=0"; return 1; }
  grep -qF "$DENY1" "$d/push.out" || { echo "  $(why "$d")"; return 1; }
  grep -qF "판정 불가 나노 가드 mode 카드 예외 0" "$d/push.out" || { echo "  판정 불가 줄 없음"; return 1; }
}
c2() {   # ② 새 tests/test_x.sh 100755 → 통과(분류기 r1866 과 같은 꼴)
  MK_HOOK=$1; d=$(mk "c2$2") || return 1
  x755 "$d/c/tests/test_x.sh"; mkc "$d" "새 시험" || return 1
  pushm "$d" "$NANO" HEAD:refs/heads/nano/r9002-x; rc=$?
  [ "$rc" = 0 ] || { echo "  rc=$rc $(why "$d")"; return 1; }
  if grep -qF "실행 비트" "$d/push.out"; then echo "  실행 비트 줄 있음"; return 1; fi
}
c3() {   # ③ 새 tests/helper.sh 100755 → DENY(분류기와 같음)
  MK_HOOK=$1; d=$(mk "c3$2") || return 1
  x755 "$d/c/tests/helper.sh"; mkc "$d" "보조 스크립트" || return 1
  pushm "$d" "$NANO" HEAD:refs/heads/nano/r9003-x; rc=$?
  [ "$rc" != 0 ] || { echo "  rc=0"; return 1; }
  grep -qF "PUSH_DENIED 실행 비트 tests/helper.sh — 고침:" "$d/push.out" || { echo "  $(why "$d")"; return 1; }
}
c4() {   # ④ 기존 100644 → 100755(M) → DENY
  MK_HOOK=$1; d=$(mk "c4$2") || return 1
  chmod 755 "$d/c/design/harness/note.md"; mkc "$d" "mode 만" || return 1
  pushm "$d" "$NANO" HEAD:refs/heads/nano/r9004-x; rc=$?
  [ "$rc" != 0 ] || { echo "  rc=0"; return 1; }
  grep -qF "PUSH_DENIED 실행 비트 design/harness/note.md — 고침:" "$d/push.out" || { echo "  $(why "$d")"; return 1; }
}
c5() {   # ⑤ 카드 «- 대상» 줄 «실행 파일: bin/x.sh» + 새 bin/x.sh 100755 → 통과
  MK_HOOK=$1; d=$(mk "c5$2") || return 1
  mcard "$d" 9005 '- 대상(쓰기 = 나노 · 팩): bin/x.sh 1곳 · 실행 파일: bin/x.sh · 선행: 없음' a || { echo "  카드 실패"; return 1; }
  x755 "$d/c/bin/x.sh"; mkc "$d" "카드가 지목한 실행 파일" || return 1
  pushm "$d" "$NANO" HEAD:refs/heads/nano/r9005-x; rc=$?
  [ "$rc" = 0 ] || { echo "  rc=$rc $(why "$d")"; return 1; }
}
c6() {   # ⑥ 카드 2장 → 판정 불가 1줄 + ① 과 같은 DENY
  MK_HOOK=$1; d=$(mk "c6$2") || return 1
  mcard "$d" 9006 '- 대상: bin/ft-seat-resolve.py · 실행 파일: bin/ft-seat-resolve.py' a || { echo "  카드1 실패"; return 1; }
  mcard "$d" 9006 '- 대상: bin/other.sh' b || { echo "  카드2 실패"; return 1; }
  x755 "$d/c/bin/ft-seat-resolve.py"; mkc "$d" "카드 2장" || return 1
  pushm "$d" "$NANO" HEAD:refs/heads/nano/r9006-x; rc=$?
  [ "$rc" != 0 ] || { echo "  rc=0"; return 1; }
  [ "$(grep -cF "판정 불가 나노 가드 mode 카드 예외 0" "$d/push.out")" = 1 ] || { echo "  판정 불가 줄 $(grep -cF '카드 예외 0' "$d/push.out")개"; return 1; }
  grep -qF "$DENY1" "$d/push.out" || { echo "  $(why "$d")"; return 1; }
}
c7() {   # ⑦ 100644 새 파일만 → 검사 줄 0 · 지금 그대로
  MK_HOOK=$1; d=$(mk "c7$2") || return 1
  mkdir -p "$d/c/bin"; printf 'x\n' > "$d/c/bin/plain.py"
  mkc "$d" "보통 파일" || return 1
  pushm "$d" "$NANO" HEAD:refs/heads/nano/r9007-x; rc=$?
  [ "$rc" = 0 ] || { echo "  rc=$rc $(why "$d")"; return 1; }
  if grep -qF "실행 비트" "$d/push.out"; then echo "  실행 비트 줄 있음"; return 1; fi
}
c8() {   # ⑧ 나노 아닌 좌석 → 검사 0
  MK_HOOK=$1; d=$(mk "c8$2") || return 1
  x755 "$d/c/bin/ft-seat-resolve.py"; mkc "$d" "새 실행 파일" || return 1
  pushm "$d" "" HEAD:refs/heads/nano/r9008-x; rc=$?
  [ "$rc" = 0 ] || { echo "  rc=$rc $(why "$d")"; return 1; }
  if grep -qF "실행 비트" "$d/push.out"; then echo "  실행 비트 줄 있음"; return 1; fi
}
c9() {   # ⑨ 가지 지우는 push → 검사 0
  MK_HOOK=$1; d=$(mk "c9$2") || return 1
  printf 'x\n' > "$d/c/design/harness/n.md"; mkc "$d" "보통 커밋" || return 1
  pushm "$d" "$NANO" HEAD:refs/heads/nano/y; rc=$?
  [ "$rc" = 0 ] || { echo "  준비 실패 $(why "$d")"; return 1; }
  pushm "$d" "$NANO" :refs/heads/nano/y; rc=$?
  [ "$rc" = 0 ] || { echo "  삭제 rc=$rc $(why "$d")"; return 1; }
  if grep -qF "실행 비트" "$d/push.out"; then echo "  실행 비트 줄 있음"; return 1; fi
}
c10() {   # ⑩ 경로에 공백 → 고침 줄이 따옴표로 감쌈
  MK_HOOK=$1; d=$(mk "c10$2") || return 1
  x755 "$d/c/bin/my tool.sh"; mkc "$d" "공백 경로" || return 1
  pushm "$d" "$NANO" HEAD:refs/heads/nano/r9010-x; rc=$?
  [ "$rc" != 0 ] || { echo "  rc=0"; return 1; }
  grep -qF 'PUSH_DENIED 실행 비트 bin/my tool.sh — 고침: git update-index --chmod=-x "bin/my tool.sh" && chmod 644 "bin/my tool.sh"' "$d/push.out" || { echo "  $(why "$d")"; return 1; }
}

wrap_raw() {   # $1 = d · $2 = rc → git 의 diff --raw 만 그 rc 로(나머지 하위명령 그대로) — DA HOLD1 ① 재현
  mkdir -p "$1/exec"
  printf '#!/bin/sh\nunset GIT_EXEC_PATH\ncase "$*" in *"diff --raw"*) exit %s ;; esac\nexec "%s" "$@"\n' "$2" "$REAL_GIT" > "$1/exec/git"
  chmod +x "$1/exec/git"
}
c11() {   # ⑪ DA HOLD1 ①: git diff --raw 가 두 번 rc 2 · ft2 바뀜 + legacy_guard 0 → 통과 0 · rc 1
  MK_HOOK=$1; d=$(mk "c11$2") || return 1
  printf 'a = 1\n' > "$d/c/feature-pack/fable-team/ft2/a.py"; mkc "$d" "ft2 손" || return 1
  wrap_raw "$d" 2
  EXECP="$d/exec"; pushm "$d" "$NANO" HEAD:refs/heads/nano/r9011-x; rc=$?; EXECP=
  [ "$rc" != 0 ] || { echo "  rc=0(실행 비트 판정 불가가 통과로 샜다)"; return 1; }
  grep -qF "판정 불가 나노 가드 mode git rc=2" "$d/push.out" || { echo "  $(why "$d")"; return 1; }
  grep -qF "PUSH_DENIED" "$d/push.out" || { echo "  $(why "$d")"; return 1; }
}
c12() {   # ⑫ DA HOLD1 ②: 같은 sha 두 ref — 카드 있는 r9012 · 없는 r9013 → r9013 만 DENY(ref 마다 새 판정)
  MK_HOOK=$1; d=$(mk "c12$2") || return 1
  mcard "$d" 9012 '- 대상: bin/x.sh · 실행 파일: bin/x.sh' a || { echo "  카드 실패"; return 1; }
  x755 "$d/c/bin/x.sh"; mkc "$d" "카드 지목 실행 파일" || return 1
  pushm "$d" "$NANO" HEAD:refs/heads/nano/r9012-a HEAD:refs/heads/nano/r9013-b; rc=$?
  [ "$rc" != 0 ] || { echo "  rc=0(카드 없는 ref 가 캐시로 통과)"; return 1; }
  n=$(grep -cF "PUSH_DENIED 실행 비트 bin/x.sh" "$d/push.out")
  [ "$n" = 1 ] || { echo "  거절 줄 ${n}개(기대 1 = r9013 만)"; return 1; }
}

run_case 1 c1
run_case 2 c2
run_case 3 c3
run_case 4 c4
run_case 5 c5
run_case 6 c6
run_case 7 c7
run_case 8 c8
run_case 9 c9
run_case 10 c10
run_case 11 c11
run_case 12 c12

mtest M1 4 '"A 000000 100755"|"M 100644 100755") ;;▸"A 000000 100755") ;;'
mtest M2 3 'MODE_TESTSH='"'"'(^|/)tests/test_[^/]*\.sh$'"'"'▸MODE_TESTSH='"'"'(^|/)tests/[^/]*\.sh$'"'"''
mtest M3 6 '    [ "$ar" = 0 ] && printf '"'"'%s\n'"'"' "$allow" | grep -Fxq -e "$p" && continue▸    continue'
mtest M4 1 "'PUSH_DENIED 실행 비트 %s — 고침:▸'DENY %s — 고침:"
mtest M5 8 '[ -n "$seat" ] || { cat >/dev/null; exit 0; }▸: # 변이 M5'

lib_done "반례 ①~⑫ · 변이 M1~M5"
