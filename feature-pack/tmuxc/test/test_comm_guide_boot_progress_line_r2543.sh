#!/usr/bin/env bash
# test_comm_guide_boot_progress_line_r2543.sh — r2543: 부팅 필수 문서 COMM-GUIDE-BOOT.md 에
#   조항 18 «골 진행판 = head -16 GOAL-*.md + tail -5 *.log.tsv» 한 줄이 들어가고, 문서 전체는
#   2048바이트 이하로 남고, 조항 1~17 은 기준판(d809c99c)과 글자 그대로 같다.
#   픽스처 = 문서 파일만 읽는다 · tmux 0 · 실 좌석 0 · sleep 0 · 네트워크 0.
#   변이 대상 지정: BOOT_UNDER_TEST=<사본 경로> · INDEX_UNDER_TEST=<사본 경로>.
set -uo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")" && pwd)"
DOCS="$HERE/../claude-code/skills/tmuxc"
BOOT="${BOOT_UNDER_TEST:-$DOCS/COMM-GUIDE-BOOT.md}"
INDEX="${INDEX_UNDER_TEST:-$DOCS/COMM-GUIDE-INDEX.md}"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
fail=0
ok()  { echo "PASS $1"; }
bad() { echo "FAIL $1"; fail=$((fail+1)); }

[ -f "$BOOT" ] || { echo "FAIL 0 파일 없음: $BOOT"; exit 1; }
[ -f "$INDEX" ] || { echo "FAIL 0 파일 없음: $INDEX"; exit 1; }

# ① 파일 크기 ≤ 2048바이트
bytes="$(wc -c < "$BOOT" | tr -d ' ')"
[ "$bytes" -le 2048 ] && ok "① 크기 ${bytes}B ≤ 2048B" || bad "① 크기 ${bytes}B > 2048B"

# ② «18. » 줄이 정확히 1개이고 head -16 · tail -5 · 진행판 을 모두 가짐
n18="$(grep -cE '^18\. ' "$BOOT")"
line18="$(grep -E '^18\. ' "$BOOT")"
if [ "$n18" = "1" ] && printf '%s' "$line18" | grep -q 'head -16' \
   && printf '%s' "$line18" | grep -q 'tail -5' && printf '%s' "$line18" | grep -q '진행판'; then
  ok "② 18번 줄 1개 · head -16 + tail -5 + 진행판"
else
  bad "② 18번 줄 n=$n18: $line18"
fi

# ③ 조항 1 ~ 17 이 기준판(d809c99c)과 줄마다 같음 — 기준 17줄을 여기 박아 둔다(git 의존 0)
cat > "$T/base17" <<'BASE17'
1. Serena 은퇴 · 탐색=`ci` · grep=로그·문구만 · ci 불가=[긴급] 1통 → 복구까지 rg+Read.
2. 부팅 보고 = 세션명·모델+창·ci 가부 + `adhd=`·`cron=`·`launchd=` → 보고 전 착수 0.
3. 발주=mbox 큐+창 1줄 · 재발주=`ring <좌석> <첫 seq>` · send 반복 0 · 3초 busy 확인.
4. mbox: `send <to> <me> "본문"`(3~5줄) · `recv` · `peek` · `relay` · master 로는 집행·사람판정 2종만.
5. 포맷 `[{from}->{to}] 내용` · 화살표는 ASCII `->`.
6. tmux 폴백(쪽지 불가 시)만 · `-l`/`Enter` 별도 호출 · 3회 도달검증 · 보냈다≠도착했다.
7. 금지: prefix 없음 · agent 미실행 pane send(`pgrep -P`=0) · 작업 중 Escape · `❯` 잔류 글자 Enter.
8. «안 보내고 대기» 금지 — 회신은 send 로 마감 · 하위 좌석 질문툴 금지(→`[HIL]`) · 대기 전 3확인.
9. `i-have-adhd` = master·arch·pm·DA·desk · implementer·tester·checker·analyst 0.
10. press 전 버전정합: 기동 > 최신커밋 · redis keep/flush 명시 · hot reload 불신.
11. 설계=architect → DA 반박 → checker 확인 · 산출물 tracked.
12. cmd 세션이면 «Command Code 특이사항» 절만 추가 Read(부팅 3항 다름).
13. 이름 `biz-<팀>-<역할>-<에이전트>#N` · 발신 전 `ft-harness-info.sh seats` 로 현역 확인.
14. 조회 `ft-harness-info.sh map|rules|seats|requests` · 이슈는 오빠 컨펌 전 착수 0.
15. master 손 = 집행만 · 코드·시안·증거 줄 직접 편집 0(코드=나노·설계=arch).
16. 부팅 턴에 15분 틱 1개 · 틱마다 `[정리]` 1통 = 심박 · 20분 끊기면 `[멈춤]`.
17. 남의 pane `❯` 글자 = 자동완성(근거 0) · 판정은 jsonl·`✻ … done` · 유휴 깨우기=Escape 1회→`ring`.
BASE17
grep -E '^([1-9]|1[0-7])\. ' "$BOOT" > "$T/now17"
if diff -q "$T/base17" "$T/now17" >/dev/null; then
  ok "③ 조항 1 ~ 17 기준판과 diff 0"
else
  bad "③ 조항 1 ~ 17 기준판과 다름"; diff "$T/base17" "$T/now17" | head -6
fi

# ④ 번호 줄 수 = 18 · 번호가 1 ~ 18 로 이어짐
grep -E '^[0-9]+\. ' "$BOOT" | sed -E 's/^([0-9]+)\..*/\1/' > "$T/nums"
seq 1 18 > "$T/want"
if [ "$(wc -l < "$T/nums" | tr -d ' ')" = "18" ] && diff -q "$T/want" "$T/nums" >/dev/null; then
  ok "④ 번호 18줄 · 1 ~ 18 연속"
else
  bad "④ 번호: $(tr '\n' ' ' < "$T/nums")"
fi

# ⑤ 제목(1행)에 «18줄» 이 있고 «17줄» 은 0
title="$(sed -n '1p' "$BOOT")"
if printf '%s' "$title" | grep -q '18줄' && ! printf '%s' "$title" | grep -q '17줄'; then
  ok "⑤ 제목 «18줄» · «17줄» 0"
else
  bad "⑤ 제목: $title"
fi

# ⑥ 3행에 «COMM-GUIDE.md» 와 «COMM-GUIDE-INDEX.md» 가 남음
line3="$(sed -n '3p' "$BOOT")"
if printf '%s' "$line3" | grep -q 'COMM-GUIDE\.md' && printf '%s' "$line3" | grep -q 'COMM-GUIDE-INDEX\.md'; then
  ok "⑥ 3행에 전문 경로 · 절 지도 경로 남음"
else
  bad "⑥ 3행: $line3"
fi

# ⑦ INDEX 3행 · 7행이 «18줄»
i3="$(sed -n '3p' "$INDEX")"; i7="$(sed -n '7p' "$INDEX")"
if printf '%s' "$i3" | grep -q '18줄' && printf '%s' "$i7" | grep -q '18줄'; then
  ok "⑦ INDEX 3행 · 7행 «18줄»"
else
  bad "⑦ INDEX 3행=$i3 / 7행=$i7"
fi

# ⑧ UTF-8(BOM 0) · 끝 개행 정확히 1개 — 마지막 바이트만 보면 개행 2개도 PASS 하므로 끝 2바이트를 본다
head -c 3 "$BOOT" | od -An -tx1 | tr -d ' \n' | grep -q '^efbbbf$' && bad "⑧ BOM 있음" || ok "⑧ BOM 0"
last2="$(tail -c 2 "$BOOT" | od -An -tx1 | tr -d ' \n')"
if [ "${last2:2:2}" != "0a" ]; then
  bad "⑧ 끝 개행 없음 (끝 2바이트=$last2)"
elif [ "${last2:0:2}" = "0a" ]; then
  bad "⑧ 끝 개행 2개 이상 (끝 2바이트=$last2)"
else
  ok "⑧ 끝 개행 정확히 1개 (끝 2바이트=$last2)"
fi
# macOS iconv 가 «Inappropriate ioctl» 로 죽는 환경이 있어 decode 로 본다(엄격 = FB_CROAK)
perl -MEncode -e 'local $/; my $d=<STDIN>; eval { decode("UTF-8",$d,Encode::FB_CROAK); 1 } or exit 1' < "$BOOT" \
  && ok "⑧ UTF-8 유효" || bad "⑧ UTF-8 아님"

echo
[ "$fail" -eq 0 ] && { echo "ALL PASS"; exit 0; } || { echo "FAILED $fail"; exit 1; }
