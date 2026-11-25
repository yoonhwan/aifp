# r2544 K1 · ft2 설치 h PIN 관문 조각 (r2544 카드 «대상» K1 그대로)
# 쓰는 곳 = ft2 2.1.12 설치 h 195줄의 `[ "$REF" = "$PIN" ] || { …ABORT…; }` 1줄 자리.
# 전제 변수 = PK(팩 리포 절대경로) · REF(팩 tip sha) · PIN(설치 h 가 박은 sha) · 범위 = feature-pack/fable-team
# 판정 = tip 이 PIN 의 후손(ⓐ) ∧ PIN..tip 이 범위 글자를 안 바꿈(ⓑ) → 통과 · 그 밖 = 쓰기 0 · exit 4
if [ "$REF" != "$PIN" ]; then
  git -C "$PK" merge-base --is-ancestor "$PIN" "$REF" || {
    echo "ABORT tip 이 PIN 의 후손 아님(또는 판정 불가) · 쓰기 0" >&2
    exit 4
  }
  git -C "$PK" diff --quiet "$PIN" "$REF" -- feature-pack/fable-team
  case $? in
    0) echo "PIN-AHEAD OK tip $(printf %s "$REF" | cut -c1-10) = PIN $(printf %s "$PIN" | cut -c1-10) + 범위 밖 커밋 $(git -C "$PK" rev-list --count "$PIN..$REF")개" ;;
    1) echo "ABORT PIN 뒤 feature-pack/fable-team 글자 바뀜 → PIN 다시 · 쓰기 0" >&2; exit 4 ;;
    *) echo "ABORT 판정 불가" >&2; exit 4 ;;
  esac
fi
