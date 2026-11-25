"""r2504 ft2 나노 이름 석 칸 — 이름 = `biz-<팀>-nano-<석K>-<slug>#<세대N>` · 석 K = 점유 근거(산 세션 ∧ 배정 holder) 밖 가장 작은 수 ·
세대 = 그 석의 최대 + 1(장부 state["nano_seat"]) · 이미 지은 이름(원장 seat · 배정 holder) = 다시 셈 0 · 겹침 판독 = slug.

사례 = G1 이름 꼴 + slug · G2 석 고르기 · G3 석별 세대(장부) · G4 다시 셈 0 · G5 배정 전에 지은 이름은 석을 안 쥔다(예약 파일 0) ·
G6 같은 바퀴 두 장 = 석 2개(세계 = r1913 임시 root·가짜 tmux·가짜 record) ·
G7~G10 판독 실패 ≠ 빈 점유(DA H1): tmux rc≠0 · ft2 state None · 원장 None = 이름 짓기 0 + «판정 불가» 1줄(같은 사유 되풀이 0) · 세계에서 submit·assign 0.
실 tmux·명부·ft2 원장·mbox·설치 0 · sleep 0 · 시험 1개 70초 안.
"""
import importlib.util, json  # noqa: E401
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name, alias):
    spec = importlib.util.spec_from_file_location(alias, str(HERE / name))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def nx(ft2):
    spec = importlib.util.spec_from_file_location("ft2_keeper_next_r2504", str(Path(ft2) / "adapters" / "pi" / "keeper_next.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FakeSeat:
    """이름 함수 대역 — 원장(read_json) · ft2 배정(owners) · tmux 세션(sessions · ls) · 바퀴 캐시.
    broken = "ledger" 면 원장이 None · "state" 면 ft2 state 가 None(판독 실패 재현 · DA H1)."""

    def __init__(s, led=None, owners=None, sessions=(), state=None, ls=(0, ""), broken=""):
        s.led, s.owners, s.sessions, s.state = led or {}, owners or {}, list(sessions), state if state is not None else {}
        s.lines, s.root, s.tmux, s.cache = [], "/nonexistent-r2504", "tmux", {"@round": {}}
        s.ls, s.broken = ls, broken

    def read_json(s, path):
        return None if s.broken == "ledger" else s.led

    def owners_of(s, _team):
        return None if s.broken == "state" else {"owners": s.owners}

    def call(s, argv, timeout=None, retry=0):
        return s.ls[0], "\n".join(s.sessions), ""

    def log(s, kind, team="", text=""):
        s.lines.append(" ".join(x for x in (kind, team, text) if x))
        return None


def wire(mp, mod, k):
    mp.setattr(mod, "ft2_state", lambda _k, team: k.owners_of(team))


def nano(ft2, mp, k, team, stem):
    mod = nx(ft2)
    wire(mp, mod, k)
    return mod.nano_name(k, team, stem)


def g1(tmp, mp, ft2):   # G1 이름 꼴 = 석 칸 + slug(소문자) · seat_of/slug_of 왕복
    mod = nx(ft2)
    got = nano(ft2, mp, FakeSeat(), "harness", "r9501-Short-Card")
    assert got == "biz-harness-nano-0-r9501-short-card#0", got
    assert mod.seat_of(got) == (0, 0) and mod.slug_of(got) == "r9501-short-card", got
    assert mod.seat_of("biz-harness-nano-r9501-short-card#0") is None, "옛 꼴(석 칸 없음) = 석 없음"
    assert mod.slug_of("biz-harness-nano-r9501-short-card#0") == "r9501-short-card", "옛 꼴 slug 는 그대로"


def g2(tmp, mp, ft2):   # G2 석 0·2 점유 → 빈 가장 작은 수 = 1
    k = FakeSeat(sessions=["biz-harness-nano-0-a#0", "biz-harness-nano-2-b#1"])
    got = nano(ft2, mp, k, "harness", "r9502-next")
    assert got == "biz-harness-nano-1-r9502-next#0", got


def g3(tmp, mp, ft2):   # G3 석별 세대 — 장부의 그 석 최대 세대 + 1(석 0 비었고 장부 4 = #5 · 석 1 점유 아님 · 장부 3 = #4)
    free = FakeSeat(state={"nano_seat": {"harness|0": 4}})
    assert nano(ft2, mp, free, "harness", "r9503-gen") == "biz-harness-nano-0-r9503-gen#5", free.state
    seat1 = FakeSeat(sessions=["biz-harness-nano-0-a#0"], state={"nano_seat": {"harness|1": 3}})
    assert nano(ft2, mp, seat1, "harness", "r9504-gen") == "biz-harness-nano-1-r9504-gen#4", seat1.state


def g4(tmp, mp, ft2):   # G4 이미 지은 이름(원장 seat · 배정 holder) = 다시 셈 0
    led = FakeSeat(led={"state": "seat", "seat": "biz-harness-nano-0-old-name#0"}, sessions=["biz-harness-nano-0-old-name#0"])
    assert nano(ft2, mp, led, "harness", "r9504-ledger") == "biz-harness-nano-0-old-name#0"
    owned = FakeSeat(owners={"r9505-owned": {"holder": "biz-harness-nano-3-owned#2", "gen": 2}})
    assert nano(ft2, mp, owned, "harness", "r9505-owned") == "biz-harness-nano-3-owned#2"


def g5(tmp, mp, ft2):   # G5 배정 전에 지은 이름은 석을 안 쥔다 — 근거 0 인 다음 이름도 석 0 · 예약 파일 자리 없음
    first = nano(ft2, mp, FakeSeat(), "harness", "r9506-first")
    later = nano(ft2, mp, FakeSeat(), "harness", "r9507-later")
    assert first == "biz-harness-nano-0-r9506-first#0" and later == "biz-harness-nano-0-r9507-later#0", (first, later)


def g6(tmp, mp, ft2):   # G6 같은 바퀴 두 장 = 석 2개(세계 = r1913 · 가짜 tmux)
    fe = _load("test_keeper_fill_empty_slot_r1913.py", "keeper_r2504_r1913")
    a, b = "r9508-seat-a", "r9509-seat-b"
    mp.setattr(fe, "A", a), mp.setattr(fe, "B", b), mp.setattr(fe, "C", "r9510-seat-c")
    w = fe.world(tmp, mp, cap="9", live=0, closing=True, ft2=ft2)
    lines = w.round()
    alive = json.loads(w.tm.read_text(encoding="utf-8"))["alive"]
    kn = nx(ft2)
    seats = sorted(kn.seat_of(x)[0] for x in alive if kn.slug_of(x) in {a, b})
    assert seats == [0, 1], (seats, alive, lines)


def g7(tmp, mp, ft2):   # G7 tmux 판독 실패(rc 1) = 이름 짓기 0 + «판정 불가» 1줄(빈 점유로 안 센다) · 되풀이 0
    k = FakeSeat(ls=(1, ""))
    assert nano(ft2, mp, k, "harness", "r9511-ls") is None, k.lines
    assert len(k.lines) == 1 and k.lines[0].startswith("판정 불가 harness") and "판독 실패" in k.lines[0], k.lines
    assert nano(ft2, mp, k, "harness", "r9511-ls") is None and len(k.lines) == 1, k.lines   # 같은 사유 = 1줄


def g8(tmp, mp, ft2):   # G8 ft2 state 판독 실패(None) = 이름 짓기 0 + «판정 불가» 1줄
    k = FakeSeat(broken="state")
    assert nano(ft2, mp, k, "harness", "r9512-state") is None, k.lines
    assert len(k.lines) == 1 and "ft2 state 판독 실패" in k.lines[0], k.lines


def g9(tmp, mp, ft2):   # G9 원장 판독 실패(None) = 이름 짓기 0 + «판정 불가» 1줄
    k = FakeSeat(broken="ledger")
    assert nano(ft2, mp, k, "harness", "r9513-ledger") is None, k.lines
    assert len(k.lines) == 1 and "판독 실패" in k.lines[0], k.lines


def g10(tmp, mp, ft2):   # G10 세계 — ft2 state 판독 실패면 판정 불가 1줄 · 그 카드 submit·assign 0(이름을 안 지어 채우기 0)
    fe = _load("test_keeper_fill_empty_slot_r1913.py", "keeper_r2504_r1913_b")
    mp.setattr(fe, "A", "r9514-broken"), mp.setattr(fe, "B", "r9515-broken")
    w = fe.world(tmp, mp, cap="9", live=0, closing=False, ft2=ft2)
    K = w.K
    mp.setattr(K.closing.keeper_next, "ft2_state", lambda _k, _team: None)
    k = K.Keeper(str(w.root), env=w.env, now=lambda: w.t)
    lines = w.round(k)
    assert fe.nx.count(w, "accept", "r9514-broken") == 0 and fe.nx.launched(w) == [], lines
    assert any(x.startswith("판정 불가") and "ft2 state" in x for x in lines), lines   # 판독 실패 = 판정 불가 1줄 · 이름 짓기 전에 멈춘다


CASES = {"G1": g1, "G2": g2, "G3": g3, "G4": g4, "G5": g5, "G6": g6, "G7": g7, "G8": g8, "G9": g9, "G10": g10}
KN = "adapters/pi/keeper_next.py"
MUTANTS = {"M1": ('    key, top = "%s|%d" % (team, seat), used.get(seat, -1)', '    key, top = "%s|%d" % (team, 0), used.get(seat, -1)', ("G3",)),   # 세대 장부 열쇠 = 늘 석 0
           "M2": ("    while seat in used:\n        seat += 1\n", "    pass\n", ("G2",)),   # 점유 근거 무시 = 늘 석 0
           "M3": ("    if held:\n        return held\n", "    if False:\n        return held\n", ("G4",)),   # 다시 셈 0 위반
           "M4": ("    if why:\n        return node(k, team, why, stem)\n", "    if False:\n        return node(k, team, why, stem)\n", ("G7",))}   # 판독 실패를 빈 점유로 셈(DA H1)


def test_cases(monkeypatch, tmp_path):
    for name, case in CASES.items():
        (tmp_path / name).mkdir()
        case(tmp_path / name, monkeypatch, HERE.parent)


def test_mutants(monkeypatch, tmp_path):
    import shutil
    import pytest
    for name, (old_text, new_text, cases) in MUTANTS.items():
        shutil.copytree(HERE.parent, tree := tmp_path / name / "ft2", ignore=shutil.ignore_patterns("tests", "__pycache__"))
        text = (tree / KN).read_text(encoding="utf-8")
        assert text.count(old_text) == 1, (name, old_text)
        (tree / KN).write_text(text.replace(old_text, new_text), encoding="utf-8")
        bad, good = tmp_path / name / "bad", tmp_path / name / "good"
        bad.mkdir(), good.mkdir()
        with pytest.raises(AssertionError):
            [CASES[c](bad, monkeypatch, tree) for c in cases]
        monkeypatch.undo()
        [CASES[c](good, monkeypatch, HERE.parent) for c in cases]   # 원본으로 같은 사례 1회 더 = PASS
