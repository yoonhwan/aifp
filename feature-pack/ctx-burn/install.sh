#!/usr/bin/env bash
# ctx-burn 설치 — ~/.local/bin 에 심링크만 만든다. 되돌리기는 uninstall.sh.
set -euo pipefail

PKG_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="${CTX_BURN_BIN_DIR:-${CTX_WASTE_BIN_DIR:-$HOME/.local/bin}}"

say() { printf '%s\n' "$*"; }

say "▶ ctx-burn 설치"
command -v python3 >/dev/null 2>&1 || { say "  [✗] python3 필요"; exit 2; }
say "  [✓] python3 $(python3 -V 2>&1 | awk '{print $2}')"

mkdir -p "$BIN_DIR"
chmod +x "$PKG_DIR/bin/ctx-burn"
ln -sfn "$PKG_DIR/bin/ctx-burn" "$BIN_DIR/ctx-burn"
say "  [✓] $BIN_DIR/ctx-burn → $PKG_DIR/bin/ctx-burn"
# alias — 옛 이름(ctx-waste)은 영구 유지한다(오빠 승인 #278848). 부르는 쪽 스크립트를 고치지 않는다.
ln -sfn "$PKG_DIR/bin/ctx-burn" "$BIN_DIR/ctx-waste"
say "  [✓] $BIN_DIR/ctx-waste → $PKG_DIR/bin/ctx-burn (alias)"
# ctx-share — 조율 몫·주간 환산 보드(카드 usage-monitor-coord-weekly). 갱신 호출은 ft-board-publish.sh 가 한다.
chmod +x "$PKG_DIR/bin/ctx-share"
ln -sfn "$PKG_DIR/bin/ctx-share" "$BIN_DIR/ctx-share"
say "  [✓] $BIN_DIR/ctx-share → $PKG_DIR/bin/ctx-share"
# ctx-time — 좌석이 어디서 시간을 썼나(카드 ctx-time-waste). ctx-burn --time 도 같은 본체를 부른다.
chmod +x "$PKG_DIR/bin/ctx-time"
ln -sfn "$PKG_DIR/bin/ctx-time" "$BIN_DIR/ctx-time"
say "  [✓] $BIN_DIR/ctx-time → $PKG_DIR/bin/ctx-time"
# ctx-window — 좌석이 대화창을 어디에 썼나(카드 ctx-window-waste). ctx-burn --window 도 같은 본체를 부른다.
chmod +x "$PKG_DIR/bin/ctx-window"
ln -sfn "$PKG_DIR/bin/ctx-window" "$BIN_DIR/ctx-window"
say "  [✓] $BIN_DIR/ctx-window → $PKG_DIR/bin/ctx-window"

case ":$PATH:" in
  *":$BIN_DIR:"*) : ;;
  *) say "  [!] $BIN_DIR 가 PATH 에 없다. 셸 rc 에 추가:"
     say "      export PATH=\"$BIN_DIR:\$PATH\"" ;;
esac

say ""
say "설치 완료. 프로젝트 폴더에서:"
say "  ctx-burn                 # 최근 3시간 감사"
say "  ctx-burn --hours 12      # 12시간"
say "  ctx-burn --json          # 기계 판독 (계약 ctx.v1 · plan_input)"
say "  ctx-time                 # 최근 3시간의 시간 낭비(갈래 · 70초 넘은 명령 · html)"
say "  ctx-time --split '2026-11-23 15:13:38'   # 앞·뒤 비교"
say "  ctx-window               # 대화창을 어디에 썼는가(W1 ~ W4 · html)"
say "  ctx-share                # 조율 몫·주간 환산 보드 (state/usage-monitor/)"
say "용량·구독 산정(--capacity·--inventory·--need)은 ctx-plan 이 한다."
