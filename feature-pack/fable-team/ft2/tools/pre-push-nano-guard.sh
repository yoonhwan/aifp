#!/bin/sh
# r1900 pre-push 나노 가드 — 나노 좌석(env FT2_HOLDER·FT_SEAT_NAME 에 -nano-)의 main·ops/main-base push 를 거부한다.
# r2383 — 나노 가지도 본다: 바뀐 파일에 feature-pack/fable-team/ft2/ 가 있으면 그 로컬 sha 의 ft2 를 풀어
#   tools/legacy_guard.py 를 1회(7초 · 재시도 1) 돌린다. rc 1 = PUSH_DENIED · 판정 불가 = PUSH_DENIED · ft2 안 바뀜 = 검사 0.
# r2511 — 가지 push 의 실행 비트를 legacy_guard 앞에서 본다: 새 100755(A 000000→100755 · M 100644→100755)가
#   ⓐ 새 tests/test_*.sh(D2 분류기 r1866 과 같은 식)도 ⓑ 카드 «- 대상» 줄의 «실행 파일:» 도 아니면
#   PUSH_DENIED 실행 비트 <경로> + 고칠 명령 1줄 · rc 1. 카드 0개·2개 이상·못 읽음 = 예외 0(닫힌 쪽)
#   · 판정 불가(git 실패·7초 넘김) = ref 마다 새로 보고 늘 rc 1(legacy_guard 줄은 남기되 통과로 새지 않는다).
# r2558 — 물려받은 실행 비트는 세지 않는다(계약 design/harness/CONTRACT-r2558-push-guard-boundary-ref-state-20261123.md).
#   경계 = `git rev-list --boundary <local_sha> --not <있는 ref 들>` 의 `-` 줄뿐 · 후보 1개는 «경계 가운데 하나라도
#   그 경로가 이미 100755» 일 때만 물려받음(inherit_755 는 경계를 끝까지 돈다 · ls-tree 실패 1개면 판정 불가).
#   ref 상태는 ref_state 1개가 rev-parse «<ref>^{commit}» rc 로만 가른다: 0 정상 · 1 부재 · 그 밖 조회 오류.
#   있어야 하는 ref(있는 가지 = remote_sha · 새 가지 = origin/main)의 부재 = 판정 불가 «ref 없음» · 없어도 되는
#   ref 부재 = --not 에서만 뺀다 · 조회 오류 = 판정 불가 «rev-parse <ref> rc=» · 경계 0개 = 거절.
# stdin(ref 줄)만 읽는다 · 저장·재생은 부르는 훅 몫 · 착지 = master · --no-verify 는 건너뜀(실수 방지 장치 · 권한 통제 아님).
seat=""
for s in "${FT2_HOLDER:-}" "${FT_SEAT_NAME:-}"; do
  case "$s" in *-nano-*) seat="$s"; break ;; esac
done
[ -n "$seat" ] || { cat >/dev/null; exit 0; }
ZERO="0000000000000000000000000000000000000000"
FT2_DIR="feature-pack/fable-team/ft2"
TMP=""
cleanup() { [ -n "$TMP" ] && rm -rf "$TMP"; TMP=""; }   # r2383 K5: 임시 폴더는 어떤 길로 끝나도 지운다
trap cleanup EXIT INT TERM HUP
card_only() {   # r1999: ops/main-base 면제 = 커밋 1개(부모 = remote_sha) · 파일 1개 */indices/*.md · 지운 줄 0 → 0 · 아니면 1 · git 실패 = 2
  case "$1 $2" in *0000000000000000000000000000000000000000*) return 1 ;; esac
  p=$(git rev-parse "$1^@" </dev/null 2>/dev/null) || return 2
  [ "$p" = "$2" ] || return 1   # r1999-mut:parent
  n=$(git -c core.quotePath=false diff --no-renames --numstat "$2" "$1" </dev/null 2>/dev/null) || return 2
  IFS="$(printf '\t')" read -r a d f x <<EOF
$n
EOF
  case "$a" in ''|*[!0-9]*) return 1 ;; esac
  [ "$d" = 0 ] || return 1   # r1999-mut:del
  [ -z "$x" ] && [ "$(printf '%s\n' "$n" | wc -l)" -eq 1 ] && case "$f" in */indices/*.md) return 0 ;; esac; return 1
}
need_tmp() {   # r2511: 임시폴더 1회(실패 = 1) · 모드 검사와 legacy_guard 가 같이 쓴다 · 지우기는 trap
  [ -n "$TMP" ] && return 0
  TMP=$(mktemp -d 2>/dev/null) || TMP="$(mktemp -d -t nanoguard 2>/dev/null)"
  [ -n "$TMP" ]
}
TAB=$(printf '\t')
MODE_TESTSH='(^|/)tests/test_[^/]*\.sh$'   # r2511 ⓐ = 착지 D2 분류기의 새 시험 sh 통과 식(r1866)과 같은 글자
ROOTS=${FT2_ROOTS_TSV:-$HOME/.claude/fable-team/roots.tsv}
data_root() {   # r2511 K2 «데이터 루트» → stdout = 경로 · rc 1 = 없음. push 리포에 origin/ops/main-base 가 있으면 그 리포 · 없으면 roots.tsv 순서로 그 ref 가 있는 첫 리포(나노 팩 가지 push 도 BIZ 카드를 본다)
  top=$(git rev-parse --show-toplevel </dev/null 2>/dev/null)
  if [ -n "$top" ] && git -C "$top" rev-parse -q --verify refs/remotes/origin/ops/main-base >/dev/null 2>&1; then printf '%s\n' "$top"; return 0; fi
  [ -r "$ROOTS" ] || return 1
  while IFS="$TAB" read -r name path st ref mail lock; do
    case "$name" in ''|'#'*) continue ;; esac
    [ -n "$path" ] || continue
    git -C "$path" rev-parse -q --verify refs/remotes/origin/ops/main-base >/dev/null 2>&1 || continue
    printf '%s\n' "$path"; return 0
  done < "$ROOTS"
  return 1
}
card_list() {   # r2511 K2: $1 = 카드 번호 · $2 = 데이터 루트 → stdout = «실행 파일:» 경로 1줄씩 · rc 1 = 카드 0개/2개 이상·칸 없음 · 2 = 못 읽음(닫힌 쪽)
  r=$1; top=$2
  files=$(git -C "$top" -c core.quotePath=false ls-tree -r --name-only origin/ops/main-base -- design </dev/null 2>/dev/null) || return 2
  hit=""; n=0
  for f in $files; do
    case "$f" in design/*/indices/*/"r$r"-*.md) hit=$f; n=$((n + 1)) ;; esac
  done
  [ "$n" = 1 ] || return 1
  txt=$(git -C "$top" show "origin/ops/main-base:$hit" </dev/null 2>/dev/null) || return 2
  line=$(printf '%s\n' "$txt" | grep -Em 1 '^[[:space:]]*[-*][[:space:]]*대상[[:space:]]*[:：(]')
  [ -n "$line" ] || return 1
  rest=$(printf '%s\n' "$line" | sed -n 's/.*실행 파일:[[:space:]]*//p')
  [ -n "$rest" ] || return 1
  k=0
  for tok in $(printf '%s\n' "$rest" | tr '·' '\n'); do
    tok=$(printf '%s' "$tok" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^`//' -e 's/`$//')
    case "$tok" in *[!A-Za-z0-9._/-]*) break ;; esac
    case "$tok" in */*) ;; *) break ;; esac
    printf '%s\n' "$tok"; k=$((k + 1))
  done
  [ "$k" -gt 0 ]
}
ref_state() {   # r2558 계약 §2: $1 = ref → 표준출력 = rc(0 = 정상(커밋으로 풀림) · 1 = 부재 · 그 밖 = 조회 오류) · 출력 글자는 읽지 않는다
  git rev-parse -q --verify "$1^{commit}" </dev/null >/dev/null 2>&1
  echo $?
}
inherit_755() {   # r2558 계약 C3: $1 = 경로 · 나머지 = 경계 커밋 → 0 = 하나라도 100755(물려받음) · 1 = 전부 아님 · 2 = ls-tree 판정 불가
  ip=$1; shift; iv=1
  for ir in "$@"; do
    il=$(git ls-tree "$ir" -- "$ip" </dev/null 2>/dev/null) || return 2   # 끝까지 돈다: 첫 100755 에서 바로 돌아가지 않는다
    case "$il" in 100755[[:space:]]*) iv=0 ;; esac
  done
  return "$iv"
}
mode_run() {   # r2511 K1·K3: $1 = local_sha · $2 = remote_sha · $3 = remote_ref(가지를 이름 · 나노는 HEAD:<가지> 로 밀어 local_ref 가 HEAD 다) → $TMP/mode.$1.out 에 줄 · 표준출력 = rc(0 통과·1 거절·2 git 판정 불가)
  sha=$1; ref=$3; out="$TMP/mode.$1.out"; : > "$out"
  bndrefs=""   # r2558 계약 §4 ①: 세 ref 를 ref_state 로만 묻는다(diff 앞 · `&&`·`||` 로 rc 를 버리는 줄 0)
  case "$2" in "$ZERO") req=origin/main ;; *) req=$2 ;; esac   # 있어야 하는 ref = 있는 가지 remote_sha · 새 가지 origin/main
  for br in "$2" origin/main origin/ops/main-base; do
    case "$br" in ''|"$ZERO") continue ;; esac
    case " $bndrefs " in *" $br "*) continue ;; esac
    k=$(ref_state "$br")
    case "$k" in
      0) bndrefs="$bndrefs $br" ;;
      1) [ "$br" = "$req" ] || continue   # 없어도 되는 ref 부재 = --not 에서만 뺀다
         printf '판정 불가 나노 가드 mode ref 없음 %s\n' "$br" >> "$out"; echo 2; return ;;
      *) printf '판정 불가 나노 가드 mode rev-parse %s rc=%s\n' "$br" "$k" >> "$out"; echo 2; return ;;
    esac
  done
  [ -n "$bndrefs" ] || { printf '판정 불가 나노 가드 mode ref 없음 (경계 ref 0)\n' >> "$out"; echo 2; return; }
  base=$2
  if [ "$2" = "$ZERO" ]; then
    base=$(git merge-base "$1" origin/main </dev/null 2>/dev/null); k=$?
    [ "$k" = 0 ] && [ -n "$base" ] || { printf '판정 불가 나노 가드 mode git rc=%s\n' "${k:-1}" >> "$out"; echo 2; return; }
  fi
  rows=$(git -c core.quotePath=false diff --raw --no-renames --no-abbrev "$base" "$1" </dev/null 2>/dev/null); k=$?
  [ "$k" = 0 ] || { printf '판정 불가 나노 가드 mode git rc=%s\n' "$k" >> "$out"; echo 2; return; }
  [ -n "$rows" ] || { echo 0; return; }
  printf '%s\n' "$rows" > "$TMP/mode.$sha.raw"
  : > "$TMP/mode.$sha.skip"
  while IFS= read -r row; do
    IFS="$TAB" read -r meta path <<EOF
$row
EOF
    set -- $meta
    om=${1#:}; nm=$2; st=$5
    case "$st $om $nm" in "A 000000 100755"|"M 100644 100755") ;; *) continue ;; esac
    if [ "$st" = A ] && printf '%s\n' "$path" | grep -Eq "$MODE_TESTSH"; then continue; fi
    printf '%s\n' "$path" >> "$TMP/mode.$sha.skip"
  done < "$TMP/mode.$sha.raw"
  [ -s "$TMP/mode.$sha.skip" ] || { echo 0; return; }
  bnd=""   # r2558 DA HOLD H1: 경계 = 원격 ref 끝이 아니라 나노 손 커밋의 «이미 원격에 있는 부모»(rev-list --boundary)
  if [ -n "$bndrefs" ]; then
    git rev-list --boundary "$sha" --not $bndrefs </dev/null > "$TMP/mode.$sha.bnd" 2>/dev/null; k=$?
    [ "$k" = 0 ] || { printf '판정 불가 나노 가드 mode rev-list rc=%s\n' "$k" >> "$out"; echo 2; return; }
    bnd=$(sed -n 's/^-//p' "$TMP/mode.$sha.bnd")
  fi
  bn=${ref#refs/heads/}; num=""
  case "$bn" in nano/r*) num=${bn#nano/r}; num=${num%%-*} ;; esac
  case "$num" in ''|*[!0-9]*) num="" ;; esac
  allow=""; ar=1
  if [ -n "$num" ] && top=$(data_root) && allow=$(card_list "$num" "$top"); then ar=0; fi
  [ "$ar" = 0 ] || printf '판정 불가 나노 가드 mode 카드 예외 0(%s)\n' "$([ "$ar" = 1 ] && echo '카드 0개 또는 2개 이상·칸 없음' || echo '카드 못 읽음')" >> "$out"
  bad=0
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    [ "$ar" = 0 ] && printf '%s\n' "$allow" | grep -Fxq -e "$p" && continue
    if [ -n "$bnd" ]; then   # r2558: 경계에서 이미 100755 = 물려받음 = 나노 손 아님(세지 않는다)
      inherit_755 "$p" $bnd; ih=$?
      if [ "$ih" = 2 ]; then
        printf '판정 불가 나노 가드 mode ls-tree %s\n' "$p" >> "$out"
        echo 2; return
      fi
      [ "$ih" = 0 ] && continue
    fi
    printf 'PUSH_DENIED 실행 비트 %s — 고침: git update-index --chmod=-x "%s" && chmod 644 "%s" && git commit -m "[chore] mode 100644"\n' "$p" "$p" "$p" >> "$out"
    bad=$((bad + 1))
  done < "$TMP/mode.$sha.skip"
  [ "$bad" = 0 ] && { echo 0; return; }
  echo 1
}
mode_bounded() {   # r2511 K3: 7초 상한 1회 · $1 = local_sha · $2 = remote_sha · $3 = remote_ref → 표준출력 = rc(0·1·2·124)
  mode_run "$1" "$2" "$3" > "$TMP/mode.$1.rc" 2>/dev/null &
  pid=$!
  ( sleep 7; kill -9 "$pid" 2>/dev/null ) </dev/null >/dev/null 2>&1 & wd=$!
  wait "$pid"; k=$?
  kill "$wd" 2>/dev/null; wait "$wd" 2>/dev/null
  case "$k" in
    0) k=$(head -1 "$TMP/mode.$1.rc" 2>/dev/null); case "$k" in 0|1|2) echo "$k" ;; *) echo 2 ;; esac ;;
    124|137|143) printf '판정 불가 나노 가드 mode 시간 rc=124\n' >> "$TMP/mode.$1.out"; echo 124 ;;
    *) echo 2 ;;
  esac
}
need_guard() {   # r2383 K4: $1 = local_sha · $2 = remote_sha → 0 = ft2 바뀜 · 1 = 안 바뀜 · 2 = 판정 불가
  base=$2
  case "$2" in "$ZERO") base=$(git merge-base "$1" origin/main </dev/null 2>/dev/null) || return 2 ;; esac
  [ -n "$base" ] || return 2
  files=$(git -c core.quotePath=false diff --no-renames --name-only "$base" "$1" </dev/null 2>/dev/null) || return 2
  case "$files" in *"$FT2_DIR"*) return 0 ;; esac
  return 1
}
guard_rc() {   # $1 = local_sha → $TMP/g.<sha>.out 에 위반 줄 · 표준출력 = rc(0·1·2 · 124 시간 · 125 풀기 · 127 python)
  sha=$1; dir="$TMP/g.$sha"; out="$TMP/g.$sha.out"
  if [ ! -d "$dir" ]; then   # r2383 K4: 풀기는 sha 마다 1회(재시도는 같은 나무를 다시 쓴다) · 지우기는 trap
    mkdir -p "$dir" 2>/dev/null || { printf 'mkdir 1\n' > "$TMP/fail.$sha"; echo 125; return; }
    git archive "$sha" "$FT2_DIR" > "$TMP/g.$sha.tar" 2>/dev/null; arc=$?   # r2383 K5: 두 rc 를 따로 본다(파이프 rc 가리기 0)
    if [ "$arc" != 0 ]; then printf 'archive %s\n' "$arc" > "$TMP/fail.$sha"; echo 125; return; fi
    tar -x -f "$TMP/g.$sha.tar" -C "$dir" 2>/dev/null; trc=$?
    if [ "$trc" != 0 ]; then rm -rf "$dir"; printf 'tar %s\n' "$trc" > "$TMP/fail.$sha"; echo 125; return; fi
  fi
  [ -f "$dir/$FT2_DIR/tools/legacy_guard.py" ] || { printf 'archive 1\n' > "$TMP/fail.$sha"; echo 125; return; }
  : > "$out"
  left=7   # r2383 K4: 한 sha 의 합 상한 = 14초(7초 × 재시도 1) — 남은 시간만 준다
  if [ -n "${guard_t0:-}" ]; then
    left=$((14 - $(date +%s) + guard_t0))
    [ "$left" -gt 7 ] && left=7
    [ "$left" -lt 1 ] && left=1
  fi
  python3 "$dir/$FT2_DIR/tools/legacy_guard.py" "$dir/$FT2_DIR" >"$out" 2>/dev/null &
  pid=$!
  ( sleep "$left"; kill -9 "$pid" 2>/dev/null ) </dev/null >/dev/null 2>&1 & wd=$!
  wait "$pid"; rc=$?
  kill "$wd" 2>/dev/null; wait "$wd" 2>/dev/null
  case "$rc" in 124|137|143) echo 124 ;; *) echo "$rc" ;; esac
}
guard_once() {   # r2383 K4·F2: 같은 local_sha 는 guard 1회(결과를 $TMP/cache.<sha> 에 둔다) · 7초 넘김만 1회 더
  cache="$TMP/cache.$1"
  if [ -f "$cache" ]; then cat "$cache"; return; fi
  guard_t0=$(date +%s)
  rc=$(guard_rc "$1")
  case "$rc" in
    124|126|127)
      rc=$(guard_rc "$1") ;;
  esac
  printf '%s\n' "$rc" > "$cache"
  printf '%s\n' "$rc"
}
rc=0
while read -r local_ref local_sha remote_ref remote_sha; do
  case "$remote_ref" in
    refs/heads/main|refs/heads/ops/main-base)
      if [ "$remote_ref" = refs/heads/ops/main-base ]; then card_only "$local_sha" "$remote_sha"; k=$?; else k=1; fi
      [ "$k" = 0 ] && continue
      [ "$k" = 2 ] && echo "판정 불가 나노 가드 git rev-parse·diff 실패($remote_ref) rc=1" >&2
      echo "PUSH_DENIED 나노 좌석 $seat 의 $remote_ref push — 착지 = master" >&2
      rc=1 ;;
    *)
      case "$local_sha" in "$ZERO") continue ;; esac   # r2383 F1: 가지 지우는 push = 검사 0
      if ! need_tmp; then   # r2511: 실행 비트 검사가 먼저다(legacy_guard 앞) — 임시폴더 없으면 판정 불가로 닫는다
        echo "판정 불가 나노 가드 mode 임시폴더 rc=1" >&2
        echo "PUSH_DENIED 나노 좌석 $seat 의 $remote_ref push — 실행 비트 판정 불가" >&2
        rc=1; continue
      fi
      m=$(mode_bounded "$local_sha" "$remote_sha" "$remote_ref")   # r2511 DA HOLD1 ②: ref 마다 새로 판정(캐시 0 = 다른 ref·base 재사용 0)
      case "$m" in 2|124) m=$(mode_bounded "$local_sha" "$remote_sha" "$remote_ref") ;; esac
      mf=0
      case "$m" in
        0) ;;   # 검사 줄 0 또는 전부 통과
        1) cat "$TMP/mode.$local_sha.out" >&2; rc=1; continue ;;
        2) cat "$TMP/mode.$local_sha.out" >&2; mf=1 ;;   # 판정 불가 = legacy_guard 줄도 남기되 통과면 여기서 닫는다(DA HOLD1 ①)
        *) cat "$TMP/mode.$local_sha.out" >&2
           echo "PUSH_DENIED 나노 좌석 $seat 의 $remote_ref push — 실행 비트 판정 불가" >&2
           rc=1; continue ;;
      esac
      need_guard "$local_sha" "$remote_sha"; k=$?
      if [ "$mf" = 1 ] && [ "$k" = 1 ]; then   # 실행 비트 판정 불가 + ft2 안 바뀜 = 여기서 닫는다
        echo "PUSH_DENIED 나노 좌석 $seat 의 $remote_ref push — 실행 비트 판정 불가" >&2
        rc=1; continue
      fi
      [ "$k" = 1 ] && continue   # ft2 안 바뀜 = guard 0회
      if [ "$k" = 2 ]; then
        echo "판정 불가 나노 가드 legacy_guard merge-base rc=1" >&2
        echo "PUSH_DENIED 나노 좌석 $seat 의 $remote_ref push — legacy_guard 판정 불가" >&2
        rc=1; continue
      fi
      if ! need_tmp; then
        echo "판정 불가 나노 가드 legacy_guard 임시폴더 rc=1" >&2
        echo "PUSH_DENIED 나노 좌석 $seat 의 $remote_ref push — legacy_guard 판정 불가" >&2
        rc=1; continue
      fi
      g=$(guard_once "$local_sha")
      case "$g" in
        0) [ "$mf" = 1 ] && { echo "PUSH_DENIED 나노 좌석 $seat 의 $remote_ref push — 실행 비트 판정 불가" >&2; rc=1; }
           continue ;;
        1) n=$(grep -c . "$TMP/g.$local_sha.out" 2>/dev/null)
           first=$(grep -m 1 . "$TMP/g.$local_sha.out" 2>/dev/null)
           echo "PUSH_DENIED legacy_guard 위반 ${n}건 — 첫 줄: $first" >&2
           rc=1 ;;
        *) stage=실행
           case "$g" in
             124) stage=시간 ;;
             127) stage=python ;;
             125) [ -f "$TMP/fail.$local_sha" ] && read -r stage g < "$TMP/fail.$local_sha" ;;
           esac
           echo "판정 불가 나노 가드 legacy_guard $stage rc=$g" >&2
           echo "PUSH_DENIED 나노 좌석 $seat 의 $remote_ref push — legacy_guard 판정 불가" >&2
           rc=1 ;;
      esac ;;
  esac
done
exit $rc
