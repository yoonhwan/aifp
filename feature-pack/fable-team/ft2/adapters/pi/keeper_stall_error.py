"""ft 2.0 keeper 멈춤 갈래 — pi 세션 끝 줄 판독과 오류 종류 (r1921 · keeper_stall.py 300줄 상한 → 이 파일로 나눔).

오류 종류 낱말·순서 = 1.x ft_seat_pi_turn.error_state 와 같다(ft2 는 1.x 를 import 하지 않는다 · 표는 이 파일 머리 1곳).
r2490 — 여기에 «BLOCKED»(공급자 막힘) 낱말 표를 더한다. 판독 함수는 error_detail(종류·시각·오류 칸 글) 하나이고
error_turn 은 그 앞 두 칸만 내는 옛 꼴(r1921 그대로)이다.
"""
import datetime, json, re  # noqa: E401

TAIL, AUTH = 262144, ("authentication_failed", "invalid_api_key", "not logged in")
# 출처 = ft_seat_pi_turn.error_state · «connection reset by peer» = 1.x 밖 추가 · r1921
ERRORS = (("LOGGEDOUT", AUTH), ("RATELIMITED", ("rate_limit_error", "quota", "usage limit", "would exceed your account's rate limit")),
          ("UNAVAILABLE", ("econnrefused", "timeout", "socket", "dns", "temporarily unavailable", "overloaded", "connection reset by peer")))
HTTP = re.compile(r"\b(?:503|429)\b")
# r2490 K2 — 공급자 «막힘» 낱말(402 · 잔액 0 · 리밋 결제). 이 낱말이 오류 칸에 있거나 지금 RATELIMITED 낱말뿐이면 BLOCKED 다.
# UNAVAILABLE(503 · 429 · 연결 끊김)과 LOGGEDOUT 은 BLOCKED 가 아니다 — r1921 길 그대로.
BLOCK = ("402", "insufficient_balance", "insufficient_quota", "billing")


def records(path):
    """pi 세션 jsonl 끝 256KB 의 message 줄(바깥 줄 그대로) · 깨진 줄 = None."""
    with open(path, "rb") as fh:
        size = fh.seek(0, 2)
        fh.seek(max(0, size - TAIL))
        raw = fh.read().decode("utf-8", "replace").splitlines()
    rows = []
    for i, line in enumerate(raw):
        try:
            rec = json.loads(line)
        except ValueError:
            if i == 0 and size > TAIL:
                continue
            return None
        if isinstance(rec, dict) and rec.get("type") == "message" and isinstance(rec.get("message"), dict):
            rows.append(rec)
    return rows


def is_error(message):
    return message.get("stopReason") in ("error", "aborted") or "errorMessage" in message or "error" in message


def why(message):
    """오류 칸(errorMessage·error)만 본다 — assistant 본문은 오류 종류의 근거가 아니다."""
    return json.dumps({k: message[k] for k in ("errorMessage", "error") if k in message}).lower()


def error_detail(path):
    """마지막 assistant 가 오류면 (종류, 그 줄 바깥 timestamp epoch | None, 오류 칸 글) · 아니면 None (r2490)."""
    recs = [r for r in records(path) or () if r["message"].get("role") == "assistant"][-1:]
    if not recs or not is_error(recs[0]["message"]):
        return None
    text = why(recs[0]["message"])
    kind = next((n for n, words in ERRORS if any(w in text for w in words) or (n == "UNAVAILABLE" and HTTP.search(text))), "UNKNOWN")
    try:
        return kind, datetime.datetime.fromisoformat(str(recs[0].get("timestamp")).replace("Z", "+00:00")).timestamp(), text
    except ValueError:
        return kind, None, text


def blocked(kind, text):
    """r2490 K2 — BLOCKED = 오류 칸에 새 낱말(402 · insufficient 계열 · billing)이 있거나 지금의 RATELIMITED 낱말뿐인 오류 턴.

    UNAVAILABLE·LOGGEDOUT 은 BLOCKED 가 아니다(지금 길 그대로 · r1921). 낱말 표는 이 파일 머리 1곳(BLOCK · ERRORS)."""
    if kind in ("UNAVAILABLE", "LOGGEDOUT"):
        return False
    return any(w in text for w in BLOCK) or any(w in text for w in dict(ERRORS)["RATELIMITED"])


def error_turn(path):
    """마지막 assistant 가 오류면 (종류, 그 줄 바깥 timestamp epoch | None) · 아니면 None."""
    got = error_detail(path)
    return None if got is None else (got[0], got[1])
