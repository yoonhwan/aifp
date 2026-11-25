"""r2571 ft2 keeper — 수동 닫기가 «이미 쉼 = 멱등» HOLD(rc 1)를 성공으로 읽고(state.open 에서 그 석 지움 · PARK-FAILED 0 · 끝 줄 park=already),
세션 없는 석을 닫은 바로 뒤에 남은 worktree·명부 행을 «사람 손» 1줄(LEFT-MANUAL)로 알린다(도구 삭제 0 · rc 불변).

카드 반례 ①~⑭ · 변이 M1~M9. 무대 = r2440 시험의 world(임시 리포 2쌍 · 가짜 tmux · 실 worktree · 실 core cli · r2440 석 이름)를
이 파일이 그대로 불러 쓴다(같은 무대를 두 번 짜지 않는다 · 이 파일이 재는 것은 손 규칙뿐).
「이미 쉼」 답은 가짜가 아니다 — core 에 같은 attempt 를 한 번 미리 park 해서 만든다(HOLD «완료 유보» rc 1 = 실답).
가짜 답은 그 밖의 실패 갈래(REFUSED «접수 거부» · result 칸 없음 · reason 이 다른 HOLD)뿐이다.
① ⑨ 판독 하나만 예외: worktree 폴더가 이미 없는 석은 ③ dirty 판독이 먼저 멈추므로(⑪ 과 같은 갈래) «없음» 글자는 helper 하나로 잰다.
"""
import contextlib
import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

FT2 = Path(__file__).resolve().parents[1]
if str(FT2 / "tests") not in sys.path:
    sys.path.insert(0, str(FT2 / "tests"))

import keeper_world_r1812 as kw   # noqa: E402  (r1812 세계 대역 — r2440 시험과 «같은 모듈» 이어야 팩 자리 바꿔 끼우기가 걸린다)

TARGET = kw.FT2                   # 쓰는 팩(변이 시험만 임시 사본으로 바꾼다)
HOLD, REFUSED = "완료 유보", "접수 거부"
ALREADY = "이미 쉼 = 멱등"
ATTEMPT = "a1"


def _mod(name, alias):
    spec = importlib.util.spec_from_file_location(alias, str(Path(__file__).with_name(name)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CL = _mod("test_keeper_manual_close_dead_seat_r2440.py", "r2571_world")   # world·run·tree·상수 그대로
S, W, N, SEQ, REASON, TEAM, DESK = CL.S, CL.W, CL.N, CL.SEQ, CL.REASON, CL.TEAM, CL.DESK
TAIL = " · 세션 없음(kill 0)"
HOW = (" · 다시 열기 = 카드에 «- 재개: <시각> · PR #<번호> · head <40자> · 가지 nano/<work>» 한 줄"
       "(원장이 남아 있으면 ft-card-assign-watch.sh record <카드> clear <사유>)")   # r2573 — 끝 줄 꼬리 = 다시 여는 법(수동 닫기 끝 줄에도 같은 안내)


@contextlib.contextmanager
def pack(ft2):
    """r2440 world 가 보는 팩 자리(TARGET)를 잠시 바꿔 끼운다 — 변이 사본에서 같은 사례를 돌리기 위해서만."""
    old = CL.TARGET
    CL.TARGET = ft2
    try:
        yield
    finally:
        CL.TARGET = old


def world(tmp, mp, ft2=None, **kwarg):
    """r2440 세계 그대로 — ft2 를 주면 그 사본의 core/cli.py 로 돈다."""
    Path(tmp).mkdir(parents=True, exist_ok=True)
    with pack(ft2 or TARGET):
        return CL.world(tmp, mp, **kwarg)


def module(ft2=None):
    """이 시험 대상 모듈(팩 자리) — in-process 로 park 답·state.open 을 재려고 직접 부른다."""
    path = Path(ft2 or TARGET) / "adapters" / "pi" / "keeper_manual_close.py"
    spec = importlib.util.spec_from_file_location("ft2_manual_r2571_%d" % abs(hash(str(path))), str(path))
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def opened(w):
    """keeper 데몬이 그 석을 «열어 둔» 상태(state.open)를 만든다 — 지우는지 보려고 넣는다."""
    keeper = w.keeper()
    keeper.state["open"][S] = {"team": TEAM, "since": 1}
    return keeper


def close(keeper, approve=None, reason=REASON, mod=None):
    return (mod or module()).run(keeper, S, N, approve or ("%s #%s" % (DESK, SEQ)), reason)


def fake_park(mp, mod, result=None, reason="", rc=1):
    """cli park 답 1개를 갈아 끼운다 — 모듈이 직접 load 한 cli 사본이라 world 의 CLI 호출에는 걸리지 않는다."""
    ans = {} if result is None else {"result": result}
    ans["reason"] = reason
    mp.setattr(mod.cli, "run", lambda argv: (dict(ans), rc))
    return mod


def prepark(w):
    """core 에 같은 attempt 를 한 번 쉼으로 적는다 → 다음 park 는 HOLD «이미 쉼 = 멱등(쓰기 0)» rc 1(실답 · 가짜 0)."""
    out, rc = w.CLI.run(["park", "--work", W, "--attempt", ATTEMPT, "--reason", "idle-done",
                         "--root", str(w.root), "--team", TEAM])
    assert out.get("result") == "접수 성공" and rc == 0, out
    return out


def one(lines, head):
    got = [x for x in lines if x.startswith(head)]
    assert len(got) == 1, lines
    return got[0]


def none_of(lines, head):
    assert [x for x in lines if x.startswith(head)] == [], lines


def end_line(park, tail=TAIL):
    return "CLOSED-MANUAL %s %s 판정 %s %s #%s park=%s reason=%s%s%s" % (TEAM, S, N, DESK, SEQ, park, REASON, tail, HOW)   # r2573 — 꼬리에 «다시 열기» 안내


def left_line(tree, seen="남음"):
    return ("LEFT-MANUAL %s %s 판정 %s · worktree %s %s · 명부 행 = 이 도구 손 0 · "
            "치우기 = 사람 손(git worktree remove %s)" % (TEAM, S, N, tree, seen, tree))


def park_failed(w, result, why, attempt=ATTEMPT):
    """r2440 기준판과 «바이트 같은» PARK-FAILED 줄 — 이 줄의 글자를 이 카드가 바꾸지 않았다는 핀."""
    return ("PARK-FAILED %s %s 판정 %s 사유 «manual-close: 판정 %s %s» · park 거절 %s %s · 세션은 이미 닫힘 · "
            "손으로: python3 core/cli.py park --work %s --attempt %s --reason idle-done --root %s --team %s"
            % (TEAM, S, N, N, REASON, result, why[:60], W, attempt, w.root, TEAM))


def files(folder):
    """폴더 안 파일 이름→바이트(지우기 0 을 «바이트 그대로»로 잰다 · 없어진 폴더 = None)."""
    base = Path(folder)
    if not base.is_dir():
        return None
    return {str(p.relative_to(base)): p.read_bytes() for p in sorted(base.rglob("*")) if p.is_file()}


def c01(tmp, mp):
    """① 세션 없는 석 · park 답 = HOLD «이미 쉼 = 멱등(쓰기 0)» rc 1 → rc 0 · CLOSED-MANUAL 1줄 «park=already» · PARK-FAILED 0 · state.open 에 그 석 없음."""
    w = world(tmp, mp)
    prepark(w)                                        # 기준판 = rc 7(PARK-FAILED) → Red
    keeper = opened(w)
    rc = close(keeper)
    assert rc == 0, keeper.lines
    assert one(keeper.lines, "CLOSED-MANUAL") == end_line("already"), keeper.lines
    none_of(keeper.lines, "PARK-FAILED")
    assert S not in keeper.state["open"], keeper.state["open"]
    assert w.kinds("parked") == 1, w.journal()        # 이미 쉼 답에 새 parked 줄 0(미리 적은 1줄 그대로)


def c02(tmp, mp):
    """② 살아 있는 석 · 같은 답 → rc 0 · «park=already» · kill 1(손 순서 그대로)."""
    w = world(tmp, mp, alive=True)
    prepark(w)
    keeper = opened(w)
    rc = close(keeper)
    assert rc == 0, keeper.lines
    assert one(keeper.lines, "CLOSED-MANUAL") == end_line("already", ""), keeper.lines
    assert CL.calls(w, "kill-session") == [["kill-session", "-t", "=" + S]], keeper.lines
    assert S not in keeper.state["open"], keeper.state["open"]


def c03(tmp, mp):
    """③ park 답 = REFUSED «낡은 attempt = 쉼 거절(쓰기 0)» → rc 7 · PARK-FAILED 줄이 기준판과 바이트 같음 · state.open 그대로."""
    w = world(tmp, mp)
    keeper = opened(w)
    mod = fake_park(mp, module(), REFUSED, "낡은 attempt = 쉼 거절(쓰기 0)")
    rc = close(keeper, mod=mod)
    assert rc == 7, keeper.lines
    assert one(keeper.lines, "PARK-FAILED") == park_failed(w, REFUSED, "낡은 attempt = 쉼 거절(쓰기 0)"), keeper.lines
    none_of(keeper.lines, "CLOSED-MANUAL")
    assert S in keeper.state["open"], keeper.state["open"]


def c04(tmp, mp):
    """④ REFUSED «완료 기록» · «결과 미확정» → rc 7 · CLOSED-MANUAL 0 · state.open 그대로."""
    for i, why in enumerate(("완료 기록 = 쉼 거절(쓰기 0)", "결과 미확정 = 쉼 거절(쓰기 0)")):
        w = world(Path(tmp) / ("a%d" % i), mp)
        keeper = opened(w)
        mod = fake_park(mp, module(), REFUSED, why)
        rc = close(keeper, mod=mod)
        assert rc == 7 and one(keeper.lines, "PARK-FAILED") == park_failed(w, REFUSED, why), keeper.lines
        none_of(keeper.lines, "CLOSED-MANUAL")
        assert S in keeper.state["open"], keeper.state["open"]


def c05(tmp, mp):
    """⑤ HOLD 인데 reason 이 다른 글(«잠금 대기») → rc 7(result = HOLD 만 보고 성공으로 읽으면 죽는다)."""
    w = world(tmp, mp)
    keeper = opened(w)
    mod = fake_park(mp, module(), HOLD, "잠금 대기")
    rc = close(keeper, mod=mod)
    assert rc == 7 and one(keeper.lines, "PARK-FAILED") == park_failed(w, HOLD, "잠금 대기"), keeper.lines
    assert S in keeper.state["open"], keeper.state["open"]


def c06(tmp, mp):
    """⑥ park 성공 → «park=done»(기준판과 같은 줄 · 회귀)."""
    w = world(tmp, mp)
    keeper = opened(w)
    rc = close(keeper)
    assert rc == 0 and one(keeper.lines, "CLOSED-MANUAL") == end_line("done"), keeper.lines
    assert S not in keeper.state["open"], keeper.state["open"]


def c07(tmp, mp):
    """⑦ 답에 result 칸 없음 · rc 1 → rc 7(result 를 못 읽으면 성공으로 읽으면 죽는다)."""
    w = world(tmp, mp)
    keeper = opened(w)
    mod = fake_park(mp, module(), None, "낡은 attempt = 쉼 거절(쓰기 0)")
    rc = close(keeper, mod=mod)
    assert rc == 7 and one(keeper.lines, "PARK-FAILED") == park_failed(w, None, "낡은 attempt = 쉼 거절(쓰기 0)"), keeper.lines
    assert S in keeper.state["open"], keeper.state["open"]


def c08(tmp, mp):
    """⑧ 세션 없는 석 · 성공 → 끝 줄 다음 줄 = LEFT-MANUAL 1줄(worktree 경로 · «남음») · worktree 폴더와 명부(intent·원장) 바이트 그대로."""
    w = world(tmp, mp)
    tree = CL.tree(w)
    kw._put(tree / "keep.txt", "남겨 둘 파일\n")
    CL.git(tree, "add", "-A"), CL.git(tree, "commit", "-qm", "worktree keep")   # 남겨 둠 = dirty 아님(⑪ 과 다른 갈래)
    before, intent, ledger = files(tree), files(w.runtime() / "launch"), files(w.root / "design")
    keeper = opened(w)
    rc = close(keeper)
    assert rc == 0, keeper.lines
    lines = [x for x in keeper.lines if x.startswith(("CLOSED-MANUAL", "LEFT-MANUAL"))]
    assert lines == [end_line("done"), left_line(str(tree))], keeper.lines
    assert files(tree) == before and files(w.runtime() / "launch") == intent and files(w.root / "design") == ledger, keeper.lines


def c09(tmp, mp):
    """⑨ worktree 폴더가 이미 없음 → «없음» · 이 줄이 rc 를 바꾸지 않는다(판독 1줄 · 폴더 안 만짐)."""
    w = world(tmp, mp)
    keeper = w.keeper()
    gone = Path(tmp) / "이미-없는-worktree"
    assert module().left_manual(keeper, TEAM, S, N, {"worktree": str(gone)}) is None, keeper.lines
    assert keeper.lines == [left_line(str(gone), "없음")], keeper.lines
    assert not gone.exists(), keeper.lines


def c10(tmp, mp):
    """⑩ 살아 있는 석 → LEFT-MANUAL 0줄(살아 있는 갈래는 사람 손 안내를 내지 않는다)."""
    w = world(tmp, mp, alive=True)
    keeper = opened(w)
    rc = close(keeper)
    assert rc == 0 and one(keeper.lines, "CLOSED-MANUAL") == end_line("done", ""), keeper.lines
    none_of(keeper.lines, "LEFT-MANUAL")


def c11(tmp, mp):
    """⑪ 세션 없는 석이 dirty(rc 8) · park 실패(rc 7)로 멈춤 → LEFT-MANUAL 0줄."""
    w = world(tmp, mp, dirty=True)
    keeper = opened(w)
    rc = close(keeper)
    assert rc == 8 and "미커밋 변경 있음" in one(keeper.lines, "REJECT dirty"), keeper.lines
    none_of(keeper.lines, "LEFT-MANUAL")
    w2 = world(Path(tmp) / "b", mp)
    keeper2 = opened(w2)
    mod = fake_park(mp, module(), REFUSED, "완료 기록 = 쉼 거절(쓰기 0)")
    assert close(keeper2, mod=mod) == 7, keeper2.lines
    none_of(keeper2.lines, "LEFT-MANUAL")


def c12(tmp, mp):
    """⑫ ① 의 꼴(이미 쉼) 뒤에도 LEFT-MANUAL 1줄 — 끝 줄 바루 다음 줄."""
    w = world(tmp, mp)
    prepark(w)
    keeper = opened(w)
    assert close(keeper) == 0, keeper.lines
    lines = [x for x in keeper.lines if x.startswith(("CLOSED-MANUAL", "LEFT-MANUAL"))]
    assert lines == [end_line("already"), left_line(str(CL.tree(w)))], keeper.lines


def c13(tmp, mp):
    """⑬ result = REFUSED(«접수 거부») 인데 reason 이 «이미 쉼 = 멱등(쓰기 0)» · rc 1 → rc 7 · PARK-FAILED 1줄 · CLOSED-MANUAL 0 · state.open 그대로."""
    w = world(tmp, mp)
    keeper = opened(w)
    mod = fake_park(mp, module(), REFUSED, "이미 쉼 = 멱등(쓰기 0)")
    rc = close(keeper, mod=mod)
    assert rc == 7 and one(keeper.lines, "PARK-FAILED") == park_failed(w, REFUSED, "이미 쉼 = 멱등(쓰기 0)"), keeper.lines
    none_of(keeper.lines, "CLOSED-MANUAL")
    assert S in keeper.state["open"], keeper.state["open"]


def c14(tmp, mp):
    """⑭ 답에 result 칸이 없고 reason 만 «이미 쉼 = 멱등(쓰기 0)» · rc 1 → rc 7 · PARK-FAILED 1줄 · state.open 그대로."""
    w = world(tmp, mp)
    keeper = opened(w)
    mod = fake_park(mp, module(), None, "이미 쉼 = 멱등(쓰기 0)")
    rc = close(keeper, mod=mod)
    assert rc == 7 and one(keeper.lines, "PARK-FAILED") == park_failed(w, None, "이미 쉼 = 멱등(쓰기 0)"), keeper.lines
    assert S in keeper.state["open"], keeper.state["open"]


CASES = {"①": c01, "②": c02, "③": c03, "④": c04, "⑤": c05, "⑥": c06, "⑦": c07,
         "⑧": c08, "⑨": c09, "⑩": c10, "⑪": c11, "⑫": c12, "⑬": c13, "⑭": c14}


def test_case01_이미_쉼_답을_성공으로(tmp_path, monkeypatch):
    c01(tmp_path, monkeypatch)


def test_case02_이미_쉼_살아_있는_석(tmp_path, monkeypatch):
    c02(tmp_path, monkeypatch)


def test_case03_낡은_attempt_거절(tmp_path, monkeypatch):
    c03(tmp_path, monkeypatch)


def test_case04_완료_미확정_거절(tmp_path, monkeypatch):
    c04(tmp_path, monkeypatch)


def test_case05_HOLD_다른_reason(tmp_path, monkeypatch):
    c05(tmp_path, monkeypatch)


def test_case06_park_성공_회귀(tmp_path, monkeypatch):
    c06(tmp_path, monkeypatch)


def test_case07_result_칸_없음(tmp_path, monkeypatch):
    c07(tmp_path, monkeypatch)


def test_case08_LEFT_MANUAL_한_줄_삭제_0(tmp_path, monkeypatch):
    c08(tmp_path, monkeypatch)


def test_case09_worktree_폴더_없음(tmp_path, monkeypatch):
    c09(tmp_path, monkeypatch)


def test_case10_살아_있는_석_안내_0(tmp_path, monkeypatch):
    c10(tmp_path, monkeypatch)


def test_case11_멈춘_갈래_안내_0(tmp_path, monkeypatch):
    c11(tmp_path, monkeypatch)


def test_case12_이미_쉼_뒤_안내_1줄(tmp_path, monkeypatch):
    c12(tmp_path, monkeypatch)


def test_case13_REFUSED_에_이미_쉼_reason(tmp_path, monkeypatch):
    c13(tmp_path, monkeypatch)


def test_case14_result_없이_이미_쉼_reason(tmp_path, monkeypatch):
    c14(tmp_path, monkeypatch)


MUTANTS = {
    # 이름: (바꿀 글, 바꾼 글, 잡히는 사례)
    "M1": ("    if rc != 0 and not already(out):",
           "    if rc != 0 and str((out or {}).get(\"result\") or \"\") != HOLD:", ("⑤",)),      # HOLD 면 reason 안 봄
    "M2": ("    if rc != 0 and not already(out):",
           "    if rc != 0 and False:", ("③", "④")),                                            # REFUSED 도 성공
    "M3": ("    k.state.get(\"open\", {}).pop(seat, None)\n    return (\"already\" if rc else \"done\"), 0",
           "    if rc == 0:\n        k.state.get(\"open\", {}).pop(seat, None)\n    return (\"already\" if rc else \"done\"), 0", ("①",)),   # already 갈래가 state.open 안 지움
    "M4": ("    if rc != 0 and not already(out):", "    if rc != 0:", ("①",)),                  # already 갈래가 PARK-FAILED 도 찍음
    "M5": ("    return k.log(\"CLOSED-MANUAL\", team, \"%s 판정 %s %s #%s park=%s reason=%s%s%s\" % (seat, n, seat_ok, seq, park, reason, note, REOPEN_HOW)) or 0",
           "    left_manual(k, team, seat, n, intent)\n"
           "    return k.log(\"CLOSED-MANUAL\", team, \"%s 판정 %s %s #%s park=%s reason=%s%s%s\" % (seat, n, seat_ok, seq, park, reason, note, REOPEN_HOW)) or 0", ("⑩",)),  # 살아 있는 석에도 안내
    "M6": ("    if rc:                                                 # ③ 그대로(미커밋·판독 실패 = REJECT dirty)\n        return k.log(\"REJECT dirty",
           "    if rc:                                                 # ③ 그대로(미커밋·판독 실패 = REJECT dirty)\n        left_manual(k, team, seat, n, intent)\n        return k.log(\"REJECT dirty", ("⑪",)),  # 멈춘 갈래에도 안내
    "M7": ("    path = str((intent or {}).get(\"worktree\") or \"\")\n    left = \"남음\" if path and os.path.isdir(path) else \"없음\"",
           "    path = str((intent or {}).get(\"worktree\") or \"\")\n"
           "    __import__(\"shutil\").rmtree(path, ignore_errors=True)\n"
           "    left = \"남음\" if path and os.path.isdir(path) else \"없음\"", ("⑧",)),           # 도구가 worktree 를 지움
    "M8": ("    return str((out or {}).get(\"result\") or \"\") == HOLD and str((out or {}).get(\"reason\") or \"\").startswith(ALREADY)",
           "    return str((out or {}).get(\"result\") or \"\") == HOLD or \"result\" not in (out or {})", ("⑦",)),   # result 를 못 읽으면 성공
    "M9": ("    return str((out or {}).get(\"result\") or \"\") == HOLD and str((out or {}).get(\"reason\") or \"\").startswith(ALREADY)",
           "    return str((out or {}).get(\"reason\") or \"\").startswith(ALREADY)", ("⑬", "⑭")),   # result 조건을 빼고 reason 글만 봄
}


def test_변이_M1_M9_각각_죽는다(tmp_path, monkeypatch):
    """변이마다 사본에서 그 사례가 Red 여야 한다(M1→⑤ · M2→③④ · M3→① · M4→① · M5→⑩ · M6→⑪ · M7→⑧ · M8→⑦ · M9→⑬⑭)."""
    global TARGET
    for name, (old, new, picked) in sorted(MUTANTS.items()):
        base = tmp_path / ("m" + name[1:])
        shutil.copytree(kw.FT2, base, ignore=shutil.ignore_patterns("tests", "__pycache__"))
        path = base / "adapters" / "pi" / "keeper_manual_close.py"
        text = path.read_text(encoding="utf-8")
        assert text.count(old) == 1, (name, text.count(old))
        path.write_text(text.replace(old, new), encoding="utf-8")
        TARGET = base
        try:
            for j, key in enumerate(picked):
                with pytest.raises(AssertionError):
                    CASES[key](base / ("c%d" % j), monkeypatch)
        finally:
            TARGET = kw.FT2
    (tmp_path / "ok").mkdir(exist_ok=True)
    CASES["①"]((tmp_path / "ok"), monkeypatch)


def test_0_회귀_기준판_같은_파일_두_시험(tmp_path, monkeypatch):
    """회귀 핸들 = r2440·r2549 시험이 이 팩에서 같은 rc 로 통과(이 카드가 그 파일을 건드리지 않았다)."""
    for name in ("test_keeper_manual_close_dead_seat_r2440.py", "test_keeper_manual_close_no_close_bin_r2549.py"):
        assert (kw.FT2 / "tests" / name).is_file(), name
