"""r2465 ft2 keeper — 전팀 정지에 «빼는 팀»(except)을 더한다: 정지 값을 팀마다 주고(K4) 판정기는 1.x `judge --json` 하나만 부른다(K3).

카드 반례 ⑪~⑰ · 변이 M7~M10. 무대 셋:
  · r1812 World(임시 root · 가짜 tmux · 가짜 판정기 `FT2_ALL_STOP_JUDGE` · 주입 시계) — K4 팀별 값 · K3 판정 실패 · ⑯ PAUSED · ⑫ 복구 launch 0
  · r2306 Rig(가짜 subprocess — call 그물을 진짜로 지나간다) — ⑰ 판정기 호출 수 · ⑭′ 시간 초과(상한 7초)
  · r1913 세계(대기 카드 3장 · 가짜 launch 가 실제 배정·전달까지 지난다) — ⑪″ 새 카드 1장 고르기+launch 1 · ⑯ PAUSED 면 새 카드 0
실 tmux·실 명부·실 상태 파일·네트워크 0 · sleep 0. 변이는 사본(임시)에서만 · 변이마다 원본으로 같은 사례 1회 더.
"""
import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

FT2 = Path(__file__).resolve().parents[1]
if str(FT2 / "tests") not in sys.path:
    sys.path.insert(0, str(FT2 / "tests"))
KP, KS, KN = "adapters/pi/keeper.py", "adapters/pi/keeper_settle.py", "adapters/pi/keeper_next.py"


def _mod(name, alias):
    spec = importlib.util.spec_from_file_location(alias, str(Path(__file__).with_name(name)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kw = _mod("keeper_world_r1812.py", "r2465_world")
co = _mod("test_keeper_stop_close_done_r2421.py", "r2465_close")
RG = _mod("test_keeper_round_60s.py", "r2465_rig")
FL = _mod("test_keeper_fill_empty_slot_r1913.py", "r2465_fill")
TEAM, PLANNER, SINCE = kw.TEAM, "planner", 1794000500


class Rig(RG.Rig):
    """r2549 — Rig 는 판정기를 run() 가로채기(argv[2] == «judge»)로만 돌린다. boot env 에 자리 값이 없으면
    keeper 가 «판정기 자리 없음» 으로 판정기를 부르지 않아 이 시험대가 통째로 빈 자리 길로 빠진다(회귀 3건) —
    판정기·닫기 도구 자리를 대역 값으로 준다(단언·skip 은 그대로 · 갈래만 원래 꼴로 돌아온다)."""

    def boot(s):
        super().boot()
        s.k.env.update(FT_SEAT_CLOSE_BIN="/fake/ft-seat-close.sh", FT2_ALL_STOP_JUDGE="/fake/ft-all-stop.sh")


def world(tmp, mp, ft2=kw.FT2, two=True):
    """팀 둘(harness · planner) — teams() 는 ft20-switch/<팀>.json ∧ runtime 이 있는 팀만 본다(일 1건씩 접수)."""
    tmp.mkdir(parents=True, exist_ok=True)
    w = kw.World(tmp, mp, ft2)
    w.env["FT2_SEAT_RESUME_DIR"] = str(tmp / "resume")
    for team in ((TEAM, PLANNER) if two else (TEAM,)):
        w.enable(team)
        w.work("r2465" + ("a" if team == TEAM else "b"), team=team)
    return w


def stop(w, except_=None):
    """정지 상태 파일 — 가짜 판정기가 이 파일을 읽어 judge --json 을 낸다(keeper 는 파일을 직접 읽지 않는다)."""
    body = {"since": SINCE, "reason": "시험"}
    if except_:
        body["except"] = list(except_)
    kw._put(w.state / "ALL_STOP.json", body)


def record(k, calls):
    """fill(다음 카드)·sweep(승계)를 기록으로 바꾼다 — 무거운 손은 안 부른다(정지 판정 자체는 진짜 코드)."""
    nx = k.close.__globals__["keeper_next"]
    nx.fill = lambda kk, team: (calls.append(("fill", team)), None)[1]
    k.succeed.sweep = lambda team, proj, rows: calls.append(("sweep", team))


def fills(calls):
    return [c for c in calls if c[0] == "fill"]


# ── ⑪ K4 — 팀 a 는 진행 · 팀 b 는 정지 ────────────────────────────────────
def fill_world(tmp, mp, ft2):
    """대기 카드 3장 · 가짜 launch 가 실제 배정·전달까지 지난다(새 카드 1장 고르기 = NEXT 줄 + launch.log)."""
    return FL.world(tmp, mp, ft2=ft2)


def c11c(tmp, mp, ft2=kw.FT2):
    """⑪″ 실제 fill 길 — 정지(except harness) 면 새 카드 1장 + launch 1(배정 원장 seat) · 정지(except 없음) 면 NEXT·launch 0."""
    w = fill_world(tmp / "a", mp, ft2)
    stop(w, except_=[TEAM])
    lines = w.round()
    first = [x for x in lines if x.startswith("NEXT %s fill:" % TEAM)]
    assert len(first) == 1 and len(FL.nx.launched(w)) == 1, (first, FL.nx.launched(w), lines)
    assert FL.nx.ledger(w, FL.A).get("state") == "seat", FL.nx.ledger(w, FL.A)
    w2 = fill_world(tmp / "b", mp, ft2)
    stop(w2)
    lines2 = w2.round()
    assert [x for x in lines2 if x.startswith("NEXT %s fill:" % TEAM)] == [] and FL.nx.launched(w2) == [], lines2


def c11(tmp, mp, ft2=kw.FT2):
    """⑪ 정지(except harness): harness = fill(새 카드)·sweep 있음 · planner = 둘 다 0 · 팀 밖 값 = 한 팀이라도 정지(닫힌 쪽)."""
    w = world(tmp / "w", mp, ft2)
    w.enable()
    calls = []
    k = w.keeper()
    record(k, calls)
    stop(w, except_=[TEAM])
    lines = w.round(k)
    assert ("fill", TEAM) in calls and ("sweep", TEAM) in calls, (calls, lines)
    assert ("fill", PLANNER) not in calls and ("sweep", PLANNER) not in calls, (calls, lines)
    assert k.halted(TEAM) is False and k.halted(PLANNER) is True
    assert k.halt is True and k.halt_any is True and k.stop_except == {TEAM}, (k.halt, k.halt_any, k.stop_except)
    assert k.halt_clean is True, lines


def c11b(tmp, mp, ft2=kw.FT2):
    """⑪′ 판정기에 except 칸이 없으면 지금 그대로 — 두 팀 다 fill 0 · sweep 0(기준판 전팀 정지)."""
    w = world(tmp / "w", mp, ft2)
    w.enable()
    calls = []
    k = w.keeper()
    record(k, calls)
    stop(w)
    lines = w.round(k)
    assert calls == [], (calls, lines)
    assert k.halted(TEAM) is True and k.halted(PLANNER) is True


# ── ⑫ K4 — 정지 팀의 복구 launch 0 ────────────────────────────────────────
def c12(tmp, mp, ft2=kw.FT2):
    """⑫ 정지 팀의 복구 launch 자리(resume_wait) = 호출 0 · except 팀은 그 자리를 지나간다(쪽지 정지 때는 정지 팀도 지나갔다)."""
    w = world(tmp / "w", mp, ft2)
    k = w.keeper()
    stop(w, except_=[TEAM])
    k.halt_any = k.stopped()
    seen = []
    kl = k.resume_wait.__globals__["kl"]
    real = kl.resume_state
    kl.resume_state = lambda kk, base, intent: (seen.append(base), "")[1]
    try:
        k.halt = k.halted(PLANNER)
        assert k.resume_wait(PLANNER, "r9001", "a1", {}) == "" and seen == []
        k.halt = k.halted(TEAM)
        k.resume_wait(TEAM, "r9002", "a1", {})
    finally:
        kl.resume_state = real
    assert seen and seen[0].endswith("/launch/r9002@a1"), seen


# ── ⑬ K4 — 꺼짐 = 기준판 진행 · 정지(except 없음) = 기준판 전팀 정지 ──────
def c13(tmp, mp, ft2=kw.FT2):
    """⑬ 꺼짐 → 두 팀 fill · 정지(except 없음) → 두 팀 fill 0 · 정지(except harness) → harness 만 fill."""
    w = world(tmp / "w", mp, ft2)
    w.enable()
    calls = []
    k = w.keeper()
    record(k, calls)
    w.round(k)
    assert sorted(fills(calls)) == [("fill", TEAM), ("fill", PLANNER)], calls
    calls.clear()
    stop(w)
    w.round(k)
    assert calls == [], calls
    calls.clear()
    stop(w, except_=[TEAM])
    w.round(k)
    assert fills(calls) == [("fill", TEAM)], calls


# ── ⑭ K3 — 판정기 실패 = 전 팀 정지 + «판정 불가» 1줄 ─────────────────────
@pytest.mark.parametrize("mode", ["rc1", "notjson", "unknown"])
def c14(tmp, mp, ft2=kw.FT2, mode="rc1"):
    """⑭ 판정기 rc1 · JSON 아님 · 모르는 state → 전 팀 정지 + «판정 불가» 1줄 · fill 0 · 두 번째 바퀴 0줄."""
    w = world(tmp / ("w-" + mode), mp, ft2)
    w.env["FT2_FAKE_JUDGE"] = mode   # Keeper.__init__ 이 env 를 복사한다 — keeper 를 만들기 «전»에 건다
    calls = []
    k = w.keeper()
    record(k, calls)
    lines = w.round(k)
    bad = [x for x in lines if x.startswith("판정 불가") and "ALL_STOP" in x]
    assert len(bad) == 1 and "정지로 봄" in bad[0], lines
    assert calls == [] and k.halted(TEAM) is True and k.halted(PLANNER) is True, (calls, lines)
    lines2 = w.round(k)   # k.lines 는 바퀴 사이 누적 — 같은 줄이 2개가 되면 ⑭(다음 바퀴 0줄) 위반
    assert len([x for x in lines2 if "ALL_STOP 판정 불가" in x]) == 1, lines2


def c14b(tmp, mp, ft2=kw.FT2):
    """⑭′ 판정기가 7초를 넘기면(Rig 가 TimeoutExpired 로 흉내 — sleep 0) 그 바퀴는 전 팀 정지 + «판정 불가» 1줄 · 다음 바퀴 0줄."""
    tmp.mkdir(parents=True, exist_ok=True)
    w = Rig(tmp, None if ft2 == kw.FT2 else ft2)
    w.teams, w.works = ["t1", "t2"], {"t1": ["w1"], "t2": ["w2"]}
    w.judge_raw = ("T", "")   # "T" = 상한에서 끊김(TimeoutExpired)
    lines = w.round()
    assert w.judge_s == [7.0], w.judge_s   # 판정기 호출 상한 = 7초(K3)
    assert w.k.halt_any is True and w.k.halted("t1") and w.k.halted("t2"), lines
    assert [x for x in lines if x.startswith("판정 불가") and "ALL_STOP" in x], lines
    lines2 = w.round()
    assert len([x for x in lines2 if "ALL_STOP 판정 불가" in x]) == 1, lines2


# ── ⑮ K3 — hard = 전 팀 정지 · halt_clean 거짓(정지 중 닫기 0) ────────────
def c15(tmp, mp, ft2=kw.FT2):
    """⑮ 판정기 hard → 전 팀 정지 · halt_clean 거짓 · 착지 나노가 있어도 «예정» 줄(닫지 않는다) · stop 은 halt_clean 참."""
    w = co.world(tmp / "w", mp, ft2)
    co.started(w, "r9465")
    kw._put(w.state / "ALL_STOP.json", "{깨짐")
    k = w.keeper()
    lines = w.round(k)
    assert co.killed(w) == [] and w.kinds("close_receipt") == 0, lines
    assert [x for x in lines if "예정" in x], lines
    assert k.halt_clean is False and k.halted(TEAM) is True, lines
    w2 = co.world(tmp / "b" / "w", mp, ft2)
    co.started(w2, "r9466")
    stop(w2)
    k2 = w2.keeper()
    w2.round(k2)
    assert k2.halt_clean is True


# ── ⑯ K5 — except 팀이라도 PAUSED 가 이긴다 ───────────────────────────────
def c16(tmp, mp, ft2=kw.FT2):
    """⑯ 정지(except harness) ∧ harness 에 PAUSED → 실제 fill 도 새 카드 0(표식이 이긴다) · except 팀이라도 표식 없으면 정지 아님."""
    w = fill_world(tmp / "a", mp, ft2)
    stop(w, except_=[TEAM])
    kw._put(w.state / ("%s-tick" % TEAM) / "PAUSED", "")
    lines = w.round()
    assert [x for x in lines if x.startswith("NEXT %s fill:" % TEAM)] == [] and FL.nx.launched(w) == [], lines
    w2 = world(tmp / "b", mp, ft2)
    k = w2.keeper()
    stop(w2, except_=[TEAM])
    k.halt_any = k.stopped()
    nx = k.close.__globals__["keeper_next"]
    assert nx.prereq_mute(k, TEAM) is False   # except 팀 = 정지 아님
    kw._put(w2.state / ("%s-tick" % TEAM) / "PAUSED", "")
    assert nx.prereq_mute(k, TEAM) is True     # 표식이 이긴다
    assert nx.prereq_mute(k, PLANNER) is True  # 정지 팀


# ── ⑰ K3 — 판정기 호출 수 = 바퀴당 1회 ───────────────────────────────────
def c17(tmp, mp, ft2=kw.FT2):
    """⑰ 팀 3 · 판정기 호출 1회/바퀴 · 다음 바퀴 또 1회(팀 수와 무관)."""
    tmp.mkdir(parents=True, exist_ok=True)
    w = Rig(tmp, None if ft2 == kw.FT2 else ft2)
    w.teams, w.works = ["t1", "t2", "t3"], {t: ["w1"] for t in ("t1", "t2", "t3")}

    def judge_calls(calls):
        return [c for c in calls if len(c) > 2 and c[2] == "judge"]
    w.round()
    assert len(judge_calls(w.calls)) == 1, w.calls
    before = len(w.calls)
    w.round()
    assert len(judge_calls(w.calls[before:])) == 1, w.calls[before:]


def c17b(tmp, mp, ft2=kw.FT2):
    """⑰′ 두 팀 · 판정 stop(except t2) — t1 정지(fill 0) · t2 진행(fill 1) · 판정기 호출은 여전히 1회."""
    tmp.mkdir(parents=True, exist_ok=True)
    w = Rig(tmp, None if ft2 == kw.FT2 else ft2)
    w.teams, w.works = ["t1", "t2"], {"t1": ["w1"], "t2": ["w2"]}
    w.judge = {"state": "stop", "except": ["t2"], "since": SINCE, "why": "시험"}
    w.round()
    assert [d for d in w.done if d[0] == "fill"] == [["fill", "t2"]], w.done
    assert len([c for c in w.calls if len(c) > 2 and c[2] == "judge"]) == 1, w.calls


CASES = {"⑪": c11, "⑪′": c11b, "⑪″": c11c, "⑫": c12, "⑬": c13, "⑭": c14, "⑭′": c14b, "⑮": c15, "⑯": c16,
         "⑰": c17, "⑰′": c17b}
IDS = ["c11", "c11b", "c11c", "c12", "c13", "c14", "c14b", "c15", "c16", "c17", "c17b"]
MUTANTS = {
    "M7": (KP, "        return bool(self.halt_any) and str(team) not in self.stop_except",
           "        return bool(self.halt_any)   # M7 except 를 안 봄 = 전 팀 정지", "⑪"),
    "M8": (KP, "        return bool(self.halt_any) and str(team) not in self.stop_except",
           "        return bool(self.halt_any) and not self.stop_except   # M8 except 가 있으면 전 팀 진행", "⑫"),
    "M9": (KS, "        if doc is None:\n            self.judge_note(why)\n            return True",
           "        if doc is None:\n            self.judge_note(why)\n            return False   # M9 판정 실패를 «꺼짐» 으로", "⑭"),
    "M10": (KP, "        return bool(self.halt_any) and str(team) not in self.stop_except",
            "        return bool(self.stopped()) and str(team) not in self.stop_except   # M10 팀마다 판정기", "⑰"),
}


@pytest.mark.parametrize("name", list(CASES), ids=IDS)
def test_case(name, tmp_path, monkeypatch):
    if name == "⑭":   # ⑭ 는 세 꼴(rc1 · JSON 아님 · 모르는 state)을 모두 돈다
        for mode in ("rc1", "notjson", "unknown"):
            CASES[name](tmp_path / mode, monkeypatch, mode=mode)
        return
    CASES[name](tmp_path, monkeypatch)


@pytest.mark.parametrize("name", list(MUTANTS))
def test_mutant(name, tmp_path, monkeypatch):
    rel, old, new, case = MUTANTS[name]
    tree = tmp_path / "m" / "ft2"
    shutil.copytree(FT2, tree, ignore=shutil.ignore_patterns("tests", "__pycache__", ".pytest_cache"))
    text = (tree / rel).read_text(encoding="utf-8")
    assert text.count(old) == 1, (name, old)
    (tree / rel).write_text(text.replace(old, new), encoding="utf-8")
    with pytest.raises(AssertionError):
        CASES[case](tmp_path / "m" / "w", monkeypatch, tree)
    CASES[case](tmp_path / "o" / "w", monkeypatch)   # 원본 대조 = 같은 사례가 원본에서는 통과
