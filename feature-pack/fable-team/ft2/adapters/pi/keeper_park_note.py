"""ft2 keeper — r2535 K6 «[자리 비움]» 쪽지 + K7 재개 세기 (keeper_settle.park_seat · settle_alive 가 부른다).

K6 = park 길로 닫은 바퀴에 그 팀 master 에 1통 «[자리 비움] <좌석> <카드> head <sha 10자> · 무활동 <분>분 — 정정이 필요하면 재개»
     (같은 좌석 · 같은 head = 1회 · 실패는 keeper 기록에 «미발송» · 착지 길 닫기에는 안 보낸다)
K7 = <루트>/.fable-team/state/ft2/submit-park.log · 일반 파일 0644 — 닫을 때 «자리 비움» 1줄 · «자리 비움» 을 낸 좌석·카드가
     다시 살아 있는 것을 keeper 가 본 첫 바퀴에 «재개» 1줄(시각 · 좌석 · 카드 · 닫을 때 head · 지금 head) ·
     재개 1건 = 1줄 · 쓰기 실패는 keeper 기록 1줄뿐(닫기 · 재개는 그대로 · [긴급] 0).
장부 = keeper state 의 park_note(닫힌 좌석·카드 → 그때 head · 재개 1줄 뒤 지운다) · sent(쪽지 지문 = notify 와 같은 자리).
"""
import os

LOG = os.path.join(".fable-team", "state", "ft2", "submit-park.log")


def path(root):
    """로그 자리 — <루트>/.fable-team/state/ft2/submit-park.log."""
    return os.path.join(root, LOG)


def head(close, intent):
    """그 좌석 워크트리의 HEAD 10자 · 못 읽음 = "-"(닫기·재개는 그대로 · 판정 불가 [긴급] 0)."""
    tree = str(intent.get("worktree") or "")
    if not tree or not os.path.isdir(tree):
        return "-"
    rc, out, _ = close.git(tree, "rev-parse", "HEAD")
    sha = out.strip()
    return sha[:10] if rc == 0 and len(sha) >= 10 else "-"


def line(close, team, text):
    """submit-park.log 1줄(일반 파일 0644) · 쓰기 실패 = keeper 기록 1줄뿐(예외 0 · 닫기·재개 그대로)."""
    full = path(close.root)
    try:
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")
            fh.flush()
            os.fchmod(fh.fileno(), 0o644)
    except OSError as exc:
        close.log("PARK-NOTE", team, "제출 끝 로그 쓰기 실패 %s · %s — 닫기·재개는 그대로" % (os.path.basename(full), type(exc).__name__))
        return False
    return True


def key(team, holder, work):
    return "%s|%s|%s" % (team, holder, work)


def parked(close, team, work, holder, intent):
    """K6 쪽지 1통 + K7 닫기 1줄 — park 길 몫(착지 길 닫기에는 안 부른다)."""
    sha, age = head(close, intent), close.pi_turn(intent)[0] or 0
    line(close, team, "%s · %s · %s · head %s · 무활동 %d분 · «자리 비움»" % (close.stamp(), holder, work, sha, age // 60))
    close.state.setdefault("park_note", {})[key(team, holder, work)] = sha
    nkey = "park|%s|%s|%s" % (team, holder, sha)
    if nkey in close.state.setdefault("sent", {}):   # 같은 좌석 · 같은 head = 1회(sent 장부 = notify 와 같은 자리 · 문자열 열쇠)
        return False
    body = "[자리 비움] %s %s head %s · 무활동 %d분 — 정정이 필요하면 재개" % (holder, work, sha, age // 60)
    if close.notify(team, nkey, body):
        return True
    close.log("미발송", team, "%s %s 자리 비움 쪽지 · head %s" % (work, holder, sha))
    return False


def reopen(close, team, work, holder, intent):
    """K7 재개 1줄 — «자리 비움» 을 낸 좌석·카드가 다시 살아 있는 것을 본 첫 바퀴 · 1건 = 1줄(장부에서 지운다)."""
    book, k = close.state.setdefault("park_note", {}), key(team, holder, work)
    if k not in book:
        return False
    before = book.pop(k)   # 지우는 것이 «1건 = 1줄» 의 근거 — 다음 바퀴에도 1줄 그대로
    line(close, team, "%s · %s · %s · 닫을 때 head %s · 지금 head %s · «재개»" % (close.stamp(), holder, work, before, head(close, intent)))
    return True
