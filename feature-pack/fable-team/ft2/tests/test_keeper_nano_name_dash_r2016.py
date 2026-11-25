"""r2016 ft2 keeper 나노 좌석 이름 — stem 앞 40자 · 끝 «-» 지움(1.x ft-nano-spawn.sh _slug 와 같은 규칙) · 빈 값 = 채우기 0 + 경고 1줄.
T1~T3 = 이름 함수 1개(가짜 keeper · 로그만) · T4 = r1913 세계(임시 root·git·가짜 tmux·가짜 record)에서 닫기(close)·새 칸(fill)·띄운 칸 잇기 세 자리가 같은 이름.
실 tmux·명부·ft2 원장·mbox·설치 0 · sleep 0. 변이는 사본에서만 · 원본으로 1회 더(r1913 꼴).
"""
import hashlib, importlib.util, json, shutil  # noqa: E401
from pathlib import Path
import pytest

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("keeper_fill_r2016", str(HERE / "test_keeper_fill_empty_slot_r1913.py"))
fe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fe)
nx, kw = fe.nx, fe.kw
LA = "r9001-" + "a" * 33 + "-with-pi-tail"   # 40번째 글자 = «-»
LB = "r9002-" + "b" * 33 + "-with-pi-tail"
SHORT = "r9003-short-card"
DASH = "-" * 40 + "tail"
LD = "r9004-" + "d" * 26 + "-with-pi-tail-more"   # r2113 A2 — 33번째 글자 = «-»
def want(stem, seat=0):   # r2504 — 석 칸(기본 0 = 점유 근거 0) + r2113 A2 꼬리(40자 넘게 잘리는 stem = 앞 33자 + «-» + sha1(stem) 6자)
    if len(stem) > 40:
        return "biz-harness-nano-%d-%s-%s#0" % (seat, stem[:33].rstrip("-"), hashlib.sha1(stem.encode("utf-8")).hexdigest()[:6])
    return "biz-harness-nano-%d-%s#0" % (seat, stem[:40].rstrip("-"))
class FakeKeeper:
    def __init__(s, owners=None, ls=(0, "")):
        s.lines, s.root, s.state = [], "/nonexistent-r2016", {}   # r2113 A2 — 잘리는 stem 은 원장 seat 을 먼저 읽는다(원장 없음)
        s.owners, s.ls, s.cache, s.tmux = owners or {}, ls, {"@round": {}}, "tmux"   # r2504 — 석 점유 근거 읽기(세션 · ft2 배정)
    def read_json(s, path):
        return {}
    def call(s, argv, timeout=None, retry=0):
        return s.ls + ("",) if isinstance(s.ls, tuple) else (0, s.ls, "")
    def log(s, kind, team="", text=""):
        s.lines.append(" ".join(w for w in (kind, team, text) if w))
def load(ft2):
    spec = importlib.util.spec_from_file_location("ft2_keeper_next_r2016_%d" % id(ft2), str(Path(ft2) / "adapters" / "pi" / "keeper_next.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
def nano(ft2, mp, k, team, stem):   # r2504 — 이름 함수 부름(ft2 state 대역 = k.owners)
    mod = load(ft2)
    mp.setattr(mod, "ft2_state", lambda _k, _team: {"owners": k.owners})
    return mod.nano_name(k, team, stem)
def t1(tmp, mp, ft2):   # T1 40번째 글자 «-» → 끝 «-#0» 0 · «…-with-pi»·«…a#0»
    k = FakeKeeper()
    got = nano(ft2, mp, k, "harness", LA)
    assert got == want(LA) and not got.endswith("-#0") and k.lines == [], (got, k.lines)
    real = "r1618-ctx-plan-claude-quota-sum-with-pi-claude-usage"
    assert nano(ft2, mp, k, "harness", real) == want(real)
    assert nano(ft2, mp, k, "harness", LD) == want(LD) and "--" not in want(LD), want(LD)   # r2113 A2 꼬리 앞 «-» 1개
def t2(tmp, mp, ft2):   # T2 40자 안 stem → 같은 꼴(석 칸 0 + slug 그대로)
    k = FakeKeeper()
    assert nano(ft2, mp, k, "harness", SHORT) == want(SHORT) and k.lines == []
def t3(tmp, mp, ft2):   # T3 앞 40자가 «-» 만 → 이름 없음(채우기 0) + 경고 1줄
    k = FakeKeeper()
    assert not nano(ft2, mp, k, "harness", DASH)
    assert len(k.lines) == 1 and k.lines[0].startswith("경고 harness") and DASH in k.lines[0], k.lines
def t4(tmp, mp, ft2):   # T4 같은 바퀴 닫기 LA · fill LB(띄운 칸 잇기 포함) → 두 석(0 · 1) · 세션 이름 끝 «-#0» 0
    mp.setattr(fe, "A", LA), mp.setattr(fe, "B", LB), mp.setattr(fe, "C", SHORT)
    w = fe.world(tmp, mp, cap="9", live=0, closing=True, ft2=ft2)
    lines = w.round()
    assert "NEXT harness %s -> %s %s" % (nx.W1, LA, want(LA)) in lines and "NEXT harness fill:%s -> %s %s" % (LB, LB, want(LB, 1)) in lines, lines
    alive = json.loads(w.tm.read_text())["alive"]
    assert want(LA) in alive and want(LB, 1) in alive and not any(x.endswith("-#0") for x in alive), alive
    assert nx.ledger(w, LA)["seat"] == want(LA) and nx.ledger(w, LB)["seat"] == want(LB, 1)
CASES = {"T1": t1, "T2": t2, "T3": t3, "T4": t4}
KN = "adapters/pi/keeper_next.py"
OLD = '(stem[:33].rstrip("-"), hashlib'   # r2113 A2 — 잘린 이름 끝 «-» 지움 자리
MUTANTS = {"M1": (OLD, "(stem[:33], hashlib", "T1"),
           "M2a": ('(pick[0], nano_name(k, team, pick[0]))', '(pick[0], "biz-%s-nano-%s#0" % (team, pick[0][:40]))', "T4"),   # 닫기 자리만 옛 꼴
           "M2b": ('nh = then_name(k, team, stem, opened[x])', 'nh = "biz-%s-nano-%s#0" % (team, stem[:40])', "T4"),   # 띄운 칸 잇기 자리만 옛 꼴
           "M2c": ('None, nano_name(k, team, pick[0])', 'None, "biz-%s-nano-%s#0" % (team, pick[0][:40])', "T4")}   # fill 자리만 옛 꼴
@pytest.mark.parametrize("name", list(CASES))
def test_case(name, tmp_path, monkeypatch):
    CASES[name](tmp_path, monkeypatch, kw.FT2)
@pytest.mark.parametrize("name", list(MUTANTS))
def test_mutant(name, tmp_path, monkeypatch):
    old, new, case = MUTANTS[name]
    shutil.copytree(kw.FT2, tree := tmp_path / "m" / "ft2", ignore=shutil.ignore_patterns("tests", "__pycache__"))
    text = (tree / KN).read_text(encoding="utf-8")
    assert text.count(old) == 1, (name, old)
    (tree / KN).write_text(text.replace(old, new), encoding="utf-8")
    [(tmp_path / sub).mkdir() for sub in ("w1", "w2")]
    with pytest.raises(AssertionError):
        CASES[case](tmp_path / "w1", monkeypatch, tree)
    monkeypatch.undo()
    CASES[case](tmp_path / "w2", monkeypatch, kw.FT2)   # 원본으로 같은 사례 1회 더 = PASS
