#!/bin/sh
# r2558 pre-push 나노 가드 «물려받은 실행 비트» 시험 — 반례 ①~⑯ · 변이 M1~M8.
# 계약 = design/harness/CONTRACT-r2558-push-guard-boundary-ref-state-20261123.md(표 15칸 · 시험 이름 = 표의 번호).
# 끝 = 나노 손이 새로 붙인 100755 만 막고, 경계(rev-list --boundary 의 «-» 줄 = 이미 원격에 있는 부모)가 원래
# 가진 100755 는 세지 않는다 · 경계는 원격 ref 끝이 아니고(⑥) ref 조회 오류는 부재로 삼키지 않는다(⑩⑬).
# 공통 대역 = tests/pre_push_nano_guard_r2383_lib.sh(임시 bare 리포 · 가짜 나노 env) · 실 원격 0 · sleep 0
# · FT2_ROOTS_TSV = 빈 파일(실 기계 카드에 기대지 않는다).
# 실행: sh tests/test_pre_push_nano_guard_mode_inherit_r2558.sh
. "$(dirname "$0")/pre_push_nano_guard_r2383_lib.sh"

pushm() {   # $1 = d · $2 = FT2_HOLDER 값 · 나머지 = refspec → $1/push.out · rc · roots 명부는 빈 파일로 고정
  d=$1; holder=$2; shift 2
  : > "$d/roots.tsv"
  ( cd "$d/c" && env FT2_HOLDER="$holder" FT_SEAT_NAME= TMPDIR="$d/tmp" GUARD_CALLS="$d/calls" FT2_ROOTS_TSV="$d/roots.tsv" PATH="$d/bin:$PATH" ${EXECP:+"GIT_EXEC_PATH=$EXECP"} git push origin "$@" ) >"$d/push.out" 2>&1
}
push_deny() {   # $1 = d · $2 = FT2_HOLDER 값 · $3 = 그 가지 이름 · 나머지 = refspec → 계약 §5 단언을 한 곳에서 지난다
  # ⓐ push rc ≠ 0 · ⓑ 임시 원격의 그 가지 끝이 안 바뀜 · ⓒ PUSH_DENIED 줄 있음(고정 글자는 부르는 칸이 더 본다)
  d=$1; holder=$2; br=$3; shift 3
  pb=$(git -C "$d/remote.git" rev-parse -q --verify "refs/heads/$br" </dev/null 2>/dev/null)
  pushm "$d" "$holder" "$@"; prc=$?
  pa=$(git -C "$d/remote.git" rev-parse -q --verify "refs/heads/$br" </dev/null 2>/dev/null)
  [ "$prc" != 0 ] || { echo "  rc=0(거절 칸이 통과로 샘)"; return 1; }
  [ "$pb" = "$pa" ] || { echo "  원격 $br 끝이 바뀌었다(${pb:-없음} → ${pa:-없음})"; return 1; }
  grep -qF "PUSH_DENIED" "$d/push.out" || { echo "  $(why "$d")"; return 1; }
  return 0
}
x755() {   # $1 = 경로(상대) → 실행 비트 파일 1개(인덱스 모드 = 파일시스템 모드)
  mkdir -p "$(dirname "$1")"
  printf '#!/bin/sh\necho x\n' > "$1"
  chmod 755 "$1"
}
main755() {   # $1 = d · $2 = 경로 → 원격 main 에 실행 비트 파일 1개(나노 손 아님 · 홀더 없음 = 가드 통과) + 추적 ref 갱신
  ( cd "$1/c" && g checkout -q main && x755 "$2" && g add -A && g commit -q -m "main 755" \
    && env FT2_HOLDER= FT_SEAT_NAME= git push -q origin HEAD:main \
    && g fetch -q origin main:refs/remotes/origin/main ) >/dev/null 2>&1
}
base755() {   # $1 = d · $2 = 경로 → 원격 ops/main-base 에 실행 비트 파일 1개 + 추적 ref 갱신
  ( cd "$1/c" && g checkout -q -b base755 && x755 "$2" && g add -A && g commit -q -m "base 755" \
    && env FT2_HOLDER= FT_SEAT_NAME= git push -q origin HEAD:refs/heads/ops/main-base \
    && g fetch -q origin ops/main-base:refs/remotes/origin/ops/main-base ) >/dev/null 2>&1
}
wrap_lstree() {   # $1 = d · $2 = rc → git 의 ls-tree 만 그 rc 로(나머지 하위명령 그대로) — DA#59 조건 2 재현
  mkdir -p "$1/exec"
  printf '#!/bin/sh\nunset GIT_EXEC_PATH\ncase "$*" in *"ls-tree"*) exit %s ;; esac\nexec "%s" "$@"\n' "$2" "$REAL_GIT" > "$1/exec/git"
  chmod +x "$1/exec/git"
}
wrap_lstree_sha() {   # $1 = d · $2 = 걸 경계 sha · $3 = rc → ls-tree 가 그 경계를 볼 때만 그 rc 로 — 반례 ⑮
  mkdir -p "$1/exec"
  printf '#!/bin/sh\nunset GIT_EXEC_PATH\ncase "$*" in *"ls-tree %s "*) exit %s ;; esac\nexec "%s" "$@"\n' "$2" "$3" "$REAL_GIT" > "$1/exec/git"
  chmod +x "$1/exec/git"
}
wrap_revlist() {   # $1 = d · $2 = rc → git 의 rev-list(--boundary 경계 조회)만 그 rc 로 — 반례 ⑦
  mkdir -p "$1/exec"
  printf '#!/bin/sh\nunset GIT_EXEC_PATH\ncase "$*" in *"rev-list"*) exit %s ;; esac\nexec "%s" "$@"\n' "$2" "$REAL_GIT" > "$1/exec/git"
  chmod +x "$1/exec/git"
}
wrap_revparse() {   # $1 = d · $2 = 걸 ref 글자 · $3 = rc → rev-parse 가 그 글자를 볼 때만 그 rc 로 — 반례 ⑩⑬
  mkdir -p "$1/exec"
  printf '#!/bin/sh\nunset GIT_EXEC_PATH\ncase "$*" in *"rev-parse"*"%s"*) exit %s ;; esac\nexec "%s" "$@"\n' "$2" "$3" "$REAL_GIT" > "$1/exec/git"
  chmod +x "$1/exec/git"
}

c1() {   # ① A1·C1(통과): 이미 올라간 자기 가지에 main 을 merge → main 이 가진 100755 는 세지 않는다(11-23 실사건 1)
  MK_HOOK=$1; d=$(mk "c1$2") || return 1
  ( cd "$d/c" && g checkout -q -b nb && printf 'nb\n' > design/harness/nb.md && g add -A && g commit -q -m nb ) >/dev/null 2>&1 || return 1
  pushm "$d" "$NANO" HEAD:refs/heads/nano/r9101-a; rc=$?
  [ "$rc" = 0 ] || { echo "  준비 push rc=$rc $(why "$d")"; return 1; }
  main755 "$d" bin/main-tool.sh || { echo "  원격 main 755 실패"; return 1; }
  ( cd "$d/c" && g checkout -q nb && g merge -q --no-edit origin/main ) >/dev/null 2>&1 || { echo "  merge 실패"; return 1; }
  pushm "$d" "$NANO" HEAD:refs/heads/nano/r9101-a; rc=$?
  [ "$rc" = 0 ] || { echo "  rc=$rc(물려받은 100755 오탐) $(why "$d")"; return 1; }
  if grep -qF "실행 비트 bin/main-tool.sh" "$d/push.out"; then echo "  물려받은 파일을 나노 손으로 셈"; return 1; fi
}

c2() {   # ② B1: ops/main-base 위 새 가지 → ops/main-base 가 원래 가진 100755 는 세지 않는다(11-23 실사건 2)
  MK_HOOK=$1; d=$(mk "c2$2") || return 1
  base755 "$d" scripts/land.sh || { echo "  원격 ops/main-base 755 실패"; return 1; }
  ( cd "$d/c" && g checkout -q -b nb2 refs/remotes/origin/ops/main-base && printf 'n\n' > design/harness/nb2.md && g add -A && g commit -q -m nb2 ) >/dev/null 2>&1 || return 1
  pushm "$d" "$NANO" HEAD:refs/heads/nano/r9102-b; rc=$?
  [ "$rc" = 0 ] || { echo "  rc=$rc(물려받은 100755 오탐) $(why "$d")"; return 1; }
  if grep -qF "실행 비트 scripts/land.sh" "$d/push.out"; then echo "  ops/main-base 가 가진 실행 비트를 나노 손으로 셈"; return 1; fi
}

c3() {   # ③ ②의 가지에서 나노가 새로 붙인 100755 → 그대로 막는다(물려받은 것만 면제)
  MK_HOOK=$1; d=$(mk "c3$2") || return 1
  base755 "$d" scripts/land.sh || { echo "  원격 ops/main-base 755 실패"; return 1; }
  ( cd "$d/c" && g checkout -q -b nb3 refs/remotes/origin/ops/main-base && x755 bin/nano-new.sh && g add -A && g commit -q -m nb3 ) >/dev/null 2>&1 || return 1
  push_deny "$d" "$NANO" nano/r9103-c HEAD:refs/heads/nano/r9103-c || return 1
  grep -qF "PUSH_DENIED 실행 비트 bin/nano-new.sh — 고침:" "$d/push.out" || { echo "  $(why "$d")"; return 1; }
  if grep -qF "실행 비트 scripts/land.sh" "$d/push.out"; then echo "  물려받은 파일도 같이 셈"; return 1; fi
}

c4() {   # ④ E2: 경계 ls-tree 실패 = 판정 불가(닫힌 쪽) — DA#59 조건 2 · 실패 주입
  MK_HOOK=$1; d=$(mk "c4$2") || return 1
  base755 "$d" scripts/land.sh || { echo "  원격 ops/main-base 755 실패"; return 1; }
  ( cd "$d/c" && g checkout -q -b nb4 refs/remotes/origin/ops/main-base && x755 bin/nano-new.sh && g add -A && g commit -q -m nb4 ) >/dev/null 2>&1 || return 1
  wrap_lstree "$d" 128
  EXECP="$d/exec"; push_deny "$d" "$NANO" nano/r9104-d HEAD:refs/heads/nano/r9104-d || { EXECP=; return 1; }; EXECP=
  grep -qF "판정 불가 나노 가드 mode ls-tree" "$d/push.out" || { echo "  $(why "$d")"; return 1; }
}

c5() {   # ⑤ A1: ①의 가지에서 나노가 새로 붙인 100755 → 물려받은 것은 빼고 그것만 막는다
  MK_HOOK=$1; d=$(mk "c5$2") || return 1
  ( cd "$d/c" && g checkout -q -b nb5 && printf 'nb\n' > design/harness/nb5.md && g add -A && g commit -q -m nb5 ) >/dev/null 2>&1 || return 1
  pushm "$d" "$NANO" HEAD:refs/heads/nano/r9105-e; rc=$?
  [ "$rc" = 0 ] || { echo "  준비 push rc=$rc $(why "$d")"; return 1; }
  main755 "$d" bin/main-tool.sh || { echo "  원격 main 755 실패"; return 1; }
  ( cd "$d/c" && g checkout -q nb5 && g merge -q --no-edit origin/main && x755 bin/nano-own.sh && g add -A && g commit -q -m own ) >/dev/null 2>&1 || { echo "  merge 실패"; return 1; }
  push_deny "$d" "$NANO" nano/r9105-e HEAD:refs/heads/nano/r9105-e || return 1
  grep -qF "PUSH_DENIED 실행 비트 bin/nano-own.sh — 고침:" "$d/push.out" || { echo "  $(why "$d")"; return 1; }
  if grep -qF "실행 비트 bin/main-tool.sh" "$d/push.out"; then echo "  물려받은 파일도 같이 셈"; return 1; fi
}

c6() {   # ⑥ H1: 경계(fork 점)는 100644 · 합치지 않은 origin/main 끝은 100755 · 나노가 그 가지에서 새로 붙인 100755 → 막는다
  MK_HOOK=$1; d=$(mk "c6$2") || return 1
  ( cd "$d/c" && g checkout -q -b nb6 ) >/dev/null 2>&1 || return 1
  main755 "$d" design/harness/note.md || { echo "  원격 main 755 실패"; return 1; }
  ( cd "$d/c" && g checkout -q nb6 && chmod 755 design/harness/note.md && g add -A && g commit -q -m own755 ) >/dev/null 2>&1 || return 1
  push_deny "$d" "$NANO" nano/r9106-f HEAD:refs/heads/nano/r9106-f || return 1
  grep -qF "PUSH_DENIED 실행 비트 design/harness/note.md — 고침:" "$d/push.out" || { echo "  $(why "$d")"; return 1; }
}

c7() {   # ⑦ E1: 경계 조회(rev-list --boundary) 실패 = 판정 불가(닫힌 쪽)
  MK_HOOK=$1; d=$(mk "c7$2") || return 1
  base755 "$d" scripts/land.sh || { echo "  원격 ops/main-base 755 실패"; return 1; }
  ( cd "$d/c" && g checkout -q -b nb7 refs/remotes/origin/ops/main-base && x755 bin/nano-new.sh && g add -A && g commit -q -m nb7 ) >/dev/null 2>&1 || return 1
  wrap_revlist "$d" 128
  EXECP="$d/exec"; push_deny "$d" "$NANO" nano/r9107-g HEAD:refs/heads/nano/r9107-g || { EXECP=; return 1; }; EXECP=
  grep -qF "판정 불가 나노 가드 mode rev-list rc=128" "$d/push.out" || { echo "  $(why "$d")"; return 1; }
}

c8() {   # ⑧ A2: 있는 가지 · origin/ops/main-base 없는 리포 — ⓐ 물려받은 100755 만 = 통과 · ⓑ 새 100755 추가 = 거절
  MK_HOOK=$1; d=$(mk "c8$2") || return 1
  ( cd "$d/c" && g checkout -q -b nb8 && printf 'n\n' > design/harness/nb8.md && g add -A && g commit -q -m nb8 ) >/dev/null 2>&1 || return 1
  pushm "$d" "$NANO" HEAD:refs/heads/nano/r9108-a; rc=$?
  [ "$rc" = 0 ] || { echo "  준비 push rc=$rc $(why "$d")"; return 1; }
  main755 "$d" bin/main-tool.sh || { echo "  원격 main 755 실패"; return 1; }
  ( cd "$d/c" && g checkout -q nb8 && g merge -q --no-edit origin/main ) >/dev/null 2>&1 || { echo "  merge 실패"; return 1; }
  pushm "$d" "$NANO" HEAD:refs/heads/nano/r9108-a; rc=$?                        # ⓐ 물려받은 100755 만
  [ "$rc" = 0 ] || { echo "  ⓐ rc=$rc(물려받은 100755 오탐) $(why "$d")"; return 1; }
  if grep -qF "실행 비트 bin/main-tool.sh" "$d/push.out"; then echo "  ⓐ 물려받은 파일을 나노 손으로 셈"; return 1; fi
  ( cd "$d/c" && x755 bin/nano-own.sh && g add -A && g commit -q -m own ) >/dev/null 2>&1 || return 1
  push_deny "$d" "$NANO" nano/r9108-a HEAD:refs/heads/nano/r9108-a || return 1   # ⓑ 새 100755 추가
  grep -qF "PUSH_DENIED 실행 비트 bin/nano-own.sh — 고침:" "$d/push.out" || { echo "  ⓑ $(why "$d")"; return 1; }
  if grep -qF "실행 비트 bin/main-tool.sh" "$d/push.out"; then echo "  ⓑ 물려받은 파일도 같이 셈"; return 1; fi
}

c9() {   # ⑨ A3: 있는 가지인데 remote_sha 객체가 로컬에 없다(다른 clone 이 1커밋 더 밀고 fetch 안 함) → 판정 불가 «ref 없음»
  MK_HOOK=$1; d=$(mk "c9$2") || return 1
  ( cd "$d/c" && g checkout -q -b nb9 && printf 'n\n' > design/harness/nb9.md && g add -A && g commit -q -m nb9 ) >/dev/null 2>&1 || return 1
  pushm "$d" "$NANO" HEAD:refs/heads/nano/r9109-b; rc=$?
  [ "$rc" = 0 ] || { echo "  준비 push rc=$rc $(why "$d")"; return 1; }
  git clone -q "$d/remote.git" "$d/other" >/dev/null 2>&1 || { echo "  다른 clone 실패"; return 1; }
  ( cd "$d/other" && g checkout -q nano/r9109-b && printf 'o\n' > design/harness/o9.md && g add -A && g commit -q -m other \
    && env FT2_HOLDER= FT_SEAT_NAME= git push -q origin HEAD:refs/heads/nano/r9109-b ) >/dev/null 2>&1 || { echo "  다른 clone push 실패"; return 1; }
  ( cd "$d/c" && x755 bin/nano-new.sh && g add -A && g commit -q -m own ) >/dev/null 2>&1 || return 1
  push_deny "$d" "$NANO" nano/r9109-b HEAD:refs/heads/nano/r9109-b || return 1
  grep -qF "판정 불가 나노 가드 mode ref 없음" "$d/push.out" || { echo "  $(why "$d")"; return 1; }
}

c10() {   # ⑩ A4·C2: ① 꼴(merge 한 있는 가지) + rev-parse 조회 오류를 ref 3개에 하나씩 → 매번 판정 불가(DA#60 반례)
  MK_HOOK=$1; d=$(mk "c10$2") || return 1
  ( cd "$d/c" && g checkout -q -b nb10 && printf 'n\n' > design/harness/nb10.md && g add -A && g commit -q -m nb10 ) >/dev/null 2>&1 || return 1
  pushm "$d" "$NANO" HEAD:refs/heads/nano/r9110-c; rc=$?
  [ "$rc" = 0 ] || { echo "  준비 push rc=$rc $(why "$d")"; return 1; }
  rsha=$(git -C "$d/c" rev-parse HEAD)
  main755 "$d" bin/main-tool.sh || { echo "  원격 main 755 실패"; return 1; }
  ( cd "$d/c" && g checkout -q nb10 && g merge -q --no-edit origin/main && x755 bin/nano-own.sh && g add -A && g commit -q -m own ) >/dev/null 2>&1 || { echo "  merge 실패"; return 1; }
  for tgt in "$rsha" origin/main origin/ops/main-base; do
    wrap_revparse "$d" "$tgt" 128
    EXECP="$d/exec"; push_deny "$d" "$NANO" nano/r9110-c HEAD:refs/heads/nano/r9110-c || { EXECP=; return 1; }; EXECP=
    grep -qF "판정 불가 나노 가드 mode rev-parse" "$d/push.out" || { echo "  $tgt $(why "$d")"; return 1; }
  done
}

c11() {   # ⑪ B2: 새 가지 · origin/ops/main-base 없음 — ⓐ fork 점이 가진 100755 만 = 통과 · ⓑ 새 100755 추가 = 거절
  MK_HOOK=$1; d=$(mk "c11$2") || return 1
  main755 "$d" design/harness/note.md || { echo "  원격 main 755 실패"; return 1; }
  if git -C "$d/c" rev-parse -q --verify refs/remotes/origin/ops/main-base >/dev/null 2>&1; then echo "  임시 리포에 ops ref 가 있다"; return 1; fi
  ( cd "$d/c" && g checkout -q -b nb11 && printf 'n\n' > design/harness/nb11.md && g add -A && g commit -q -m nb11 ) >/dev/null 2>&1 || return 1
  pushm "$d" "$NANO" HEAD:refs/heads/nano/r9111-d; rc=$?                        # ⓐ fork 점 100755 만
  [ "$rc" = 0 ] || { echo "  ⓐ rc=$rc(fork 점 100755 오탐) $(why "$d")"; return 1; }
  if grep -qF "실행 비트 design/harness/note.md" "$d/push.out"; then echo "  ⓐ fork 점이 가진 100755 를 나노 손으로 셈"; return 1; fi
  ( cd "$d/c" && x755 bin/nano-own.sh && g add -A && g commit -q -m own ) >/dev/null 2>&1 || return 1
  push_deny "$d" "$NANO" nano/r9111-d2 HEAD:refs/heads/nano/r9111-d2 || return 1  # ⓑ 새 가지에 새 100755
  grep -qF "PUSH_DENIED 실행 비트 bin/nano-own.sh — 고침:" "$d/push.out" || { echo "  ⓑ $(why "$d")"; return 1; }
  if grep -qF "실행 비트 design/harness/note.md" "$d/push.out"; then echo "  ⓑ fork 점이 가진 100755 도 셈"; return 1; fi
}

c12() {   # ⑫ B3: 새 가지 · origin/main 없음 → 판정 불가 «ref 없음 origin/main»(base 를 못 정한다)
  MK_HOOK=$1; d=$(mk "c12$2") || return 1
  ( cd "$d/c" && g update-ref -d refs/remotes/origin/main && g checkout -q -b nb12 && printf 'n\n' > design/harness/nb12.md && g add -A && g commit -q -m nb12 ) >/dev/null 2>&1 || return 1
  push_deny "$d" "$NANO" nano/r9112-e HEAD:refs/heads/nano/r9112-e || return 1
  grep -qF "판정 불가 나노 가드 mode ref 없음 origin/main" "$d/push.out" || { echo "  $(why "$d")"; return 1; }
}

c13() {   # ⑬ B4: 새 가지 · rev-parse 조회 오류를 origin/main · origin/ops/main-base 에 하나씩 → 판정 불가
  MK_HOOK=$1; d=$(mk "c13$2") || return 1
  ( cd "$d/c" && g checkout -q -b nb13 && printf 'n\n' > design/harness/nb13.md && g add -A && g commit -q -m nb13 ) >/dev/null 2>&1 || return 1
  for tgt in origin/main origin/ops/main-base; do
    wrap_revparse "$d" "$tgt" 128
    EXECP="$d/exec"; push_deny "$d" "$NANO" nano/r9113-f HEAD:refs/heads/nano/r9113-f || { EXECP=; return 1; }; EXECP=
    grep -qF "판정 불가 나노 가드 mode rev-parse" "$d/push.out" || { echo "  $tgt $(why "$d")"; return 1; }
  done
}

c14() {   # ⑭ C1 거절 쪽: merge 커밋 · 두 경계 모두 100644 · 나노가 100755 → 거절
  MK_HOOK=$1; d=$(mk "c14$2") || return 1
  ( cd "$d/c" && g checkout -q -b nb14 && printf 'n\n' > design/harness/nb14.md && g add -A && g commit -q -m nb14 ) >/dev/null 2>&1 || return 1
  pushm "$d" "$NANO" HEAD:refs/heads/nano/r9114-g; rc=$?
  [ "$rc" = 0 ] || { echo "  준비 push rc=$rc $(why "$d")"; return 1; }
  ( cd "$d/c" && g checkout -q main && printf 'main\n' > design/harness/m14.md && g add -A && g commit -q -m m14 \
    && env FT2_HOLDER= FT_SEAT_NAME= git push -q origin HEAD:main \
    && g fetch -q origin main:refs/remotes/origin/main ) >/dev/null 2>&1 || return 1
  ( cd "$d/c" && g checkout -q nb14 && g merge -q --no-edit origin/main && chmod 755 design/harness/note.md && g add -A && g commit -q -m own755 ) >/dev/null 2>&1 || { echo "  merge 실패"; return 1; }
  push_deny "$d" "$NANO" nano/r9114-g HEAD:refs/heads/nano/r9114-g || return 1
  grep -qF "PUSH_DENIED 실행 비트 design/harness/note.md — 고침:" "$d/push.out" || { echo "  $(why "$d")"; return 1; }
}

c15() {   # ⑮ C3: 100755 가 아닌 쪽 경계의 ls-tree 만 실패 → 판정 불가(경계를 끝까지 돈다 · 100755 경계가 먼저 와도)
  MK_HOOK=$1; d=$(mk "c15$2") || return 1
  ( cd "$d/c" && g checkout -q -b nb15 && printf 'n\n' > design/harness/nb15.md && g add -A && g commit -q -m nb15 ) >/dev/null 2>&1 || return 1
  pushm "$d" "$NANO" HEAD:refs/heads/nano/r9115-h; rc=$?
  [ "$rc" = 0 ] || { echo "  준비 push rc=$rc $(why "$d")"; return 1; }
  old=$(git -C "$d/c" rev-parse HEAD)
  main755 "$d" bin/main-tool.sh || { echo "  원격 main 755 실패"; return 1; }
  ( cd "$d/c" && g checkout -q nb15 && g merge -q --no-edit origin/main ) >/dev/null 2>&1 || { echo "  merge 실패"; return 1; }
  wrap_lstree_sha "$d" "$old" 128
  EXECP="$d/exec"; push_deny "$d" "$NANO" nano/r9115-h HEAD:refs/heads/nano/r9115-h || { EXECP=; return 1; }; EXECP=
  grep -qF "판정 불가 나노 가드 mode ls-tree bin/main-tool.sh" "$d/push.out" || { echo "  $(why "$d")"; return 1; }
}

c16() {   # ⑯ D1: 있는 가지에 원격과 이어지지 않은 역사(orphan)를 force 로 밀기 → 경계 0개 = 근거 0 → 거절
  MK_HOOK=$1; d=$(mk "c16$2") || return 1
  ( cd "$d/c" && g checkout -q -b nb16 && printf 'n\n' > design/harness/nb16.md && g add -A && g commit -q -m nb16 ) >/dev/null 2>&1 || return 1
  pushm "$d" "$NANO" HEAD:refs/heads/nano/r9116-i; rc=$?
  [ "$rc" = 0 ] || { echo "  준비 push rc=$rc $(why "$d")"; return 1; }
  ( cd "$d/c" && g checkout -q --orphan orph16 && g rm -rq --cached . && x755 bin/orphan-tool.sh && g add bin/orphan-tool.sh && g commit -q -m orphan ) >/dev/null 2>&1 || { echo "  orphan 준비 실패"; return 1; }
  push_deny "$d" "$NANO" nano/r9116-i --force HEAD:refs/heads/nano/r9116-i || return 1
  grep -qF "PUSH_DENIED 실행 비트 bin/orphan-tool.sh — 고침:" "$d/push.out" || { echo "  $(why "$d")"; return 1; }
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
run_case 13 c13
run_case 14 c14
run_case 15 c15
run_case 16 c16

mtest M1 1 '      [ "$ih" = 0 ] && continue▸      : # M1 물려받기 무시'
mtest M2 2 'for br in "$2" origin/main origin/ops/main-base; do▸for br in "$2" origin/main; do'
mtest M3 4 '      if [ "$ih" = 2 ]; then▸      if [ "$ih" = 9 ]; then'
mtest M4 6 "bnd=\$(sed -n 's/^-//p' \"\$TMP/mode.\$sha.bnd\")▸bnd=\$bndrefs"
mtest M5 7 '--not $bndrefs </dev/null▸--not $bndrefs </dev/null || true'
mtest M6 10 "      *) printf '판정 불가 나노 가드 mode rev-parse %s rc=%s\\n' \"\$br\" \"\$k\" >> \"\$out\"; echo 2; return ;;▸      *) continue ;;"
mtest M7 9 'rev-parse -q --verify "$1^{commit}"▸rev-parse -q --verify "$1"'
mtest M8 15 '    case "$il" in 100755[[:space:]]*) iv=0 ;; esac▸    case "$il" in 100755[[:space:]]*) return 0 ;; esac'
mtest M9 8 '      [ "$ih" = 0 ] && continue▸      : # M9 물려받기 무시 → ⑧ ⓐ(물려받은 것만 = 통과) 단언이 잡는다'
mtest M10 11 '  return "$iv"▸  return 0'

lib_done "반례 ①~⑯ · 변이 M1~M10"
