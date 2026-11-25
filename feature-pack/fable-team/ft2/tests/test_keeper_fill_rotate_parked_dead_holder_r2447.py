"""r2447 ft2 keeper 채우기 — 최신 attempt 가 쉼(park) + owner 없음 + 옛 holder 세션 부재면 rotation 으로 다시 채운다 (반례 ①~⑭ · 변이 M1~M6).
대역 = r1913 world(= r1871 world 꼴 · 임시 root·git·가짜 tmux·가짜 record·가짜 launch 는 «실제» launch.seat() 판정) · 코어는 진짜 · 부재 판독은 가짜 tmux 답(has-session rc·err) · 실 tmux·명부·ft2 원장·mbox·설치 0 · sleep 0.
기준판(rotation 안 넘김) = ① Red(바퀴마다 완료 유보 + launch 0). 변이는 사본에서만 · 변이마다 원본으로 같은 사례 1회 더.
"""
import importlib.util, json, shutil  # noqa: E401
from pathlib import Path
import pytest

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("keeper_fill_rotate_r2447_base", str(HERE / "test_keeper_fill_empty_slot_r1913.py"))
fl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fl)
nx, kw, A = fl.nx, fl.kw, fl.A
TEAM, OLD, LATE, GEN = kw.TEAM, "biz-harness-nano-old#0", "biz-harness-nano-late#0", "2"
OLD_TMUX = 'if a[0] == "has-session" and name not in d["alive"]: sys.stderr.write("can\'t find session: %s\\n" % name)'
NEW_TMUX = ('if a[0] == "has-session":\n'
            '    if name in d["alive"]: sys.exit(0)\n'
            '    sys.stderr.write(d.get("err") or "can\'t find session: %s\\n" % name); sys.exit(int(d.get("has_rc", 1)))')


def world(tmp, mp, live=0, cap="4", ft2=kw.FT2):
    """대기 카드 A·B·C(r1913 world) + 부재 판독 답을 정하는 가짜 tmux(has-session rc·err)."""
    w = fl.world(tmp, mp, cap=cap, live=live, ft2=ft2)
    tmux = w.tmp / "bin" / "tmux"
    text = tmux.read_text(encoding="utf-8")
    assert text.count(OLD_TMUX) == 1, "가짜 tmux 부재 판독 줄이 바뀌었다"
    tmux.write_text(text.replace(OLD_TMUX, NEW_TMUX), encoding="utf-8")
    return w


def cli(w, *argv):
    out, rc = w.CLI.run(list(argv) + ["--root", str(w.root), "--team", TEAM])
    assert rc == 0, out
    return out


def seed(w, reason="idle-done", result=False, updated=None):
    """① 꼴 원장 = submit·assign(a1)·deliver → claim(옛 holder · gen 2) → start(gen 2) → park(a1).
    배정 원장은 한 번 올린 꼴(released_at = 지금 · r2111 «원장 풀림»)로 둔다 · updated = 보류 풀림 시각(r2447 K6)."""
    w.work(A)
    cli(w, "claim", "--work", A, "--holder", OLD)
    cli(w, "start", "--work", A, "--holder", OLD, "--gen", GEN)
    if result:   # ⑨ = 착수 → 결과 확정
        cli(w, "result", "--work", A, "--holder", OLD, "--gen", GEN, "--word", "접수 성공")
    cli(w, "park", "--work", A, "--attempt", "a1", "--reason", reason)
    led(w, updated=updated)


def alive(w, *seats):
    d = json.loads(w.tm.read_text(encoding="utf-8"))
    kw._put(w.tm, dict(d, alive=d["alive"] + list(seats)))


def absent_rc(w, rc=None, err=""):
    """부재 판독기 답 — rc 없음 = rc1 «can't find session» · rc 2 = 판정 불가 · err = tmux 오류 글."""
    d = json.loads(w.tm.read_text(encoding="utf-8"))
    d.update({k: v for k, v in (("has_rc", rc), ("err", err)) if v})
    kw._put(w.tm, d)


def owner_add(k):   # ④ owner 가 남은 꼴(쉼이 아니다 — 다른 실행자가 rotation 으로 실행권을 받은 원장)
    out = type(k).close.__globals__["keeper_next"].dispatch.Dispatch(k.root, TEAM).ex.claim(A, LATE, rotation=True)
    assert out.result == "접수 성공", out


def uncertain_mark(k):   # ⑥ 미확정 표식이 있는 꼴(코어 공개 API — 원장 줄이 남는다)
    out = type(k).close.__globals__["keeper_next"].dispatch.Dispatch(k.root, TEAM).ex.mark_uncertain(A, OLD, int(GEN), "착수 뒤 결과 미확정")
    assert out.result == "완료 유보", out


def led(w, updated=None, state="none", released=True):
    """배정 원장 1장 — released_at = 전달된 attempt 를 풀어 주는 시각(r2111) · updated = 채우기 보류 풀림 시각(r2447 K6)."""
    kw._put(w.state / "card-assign" / (A + ".json"),
            {"state": state, "updated": w.t if updated is None else updated, "released_at": w.t if released else 0})


def hold(w, at=None):   # 채우기 보류 목록에 A(r1913 꼴 «시각|사유»)
    p = w.state / "ft2-keeper" / "state.json"
    s = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    s.setdefault("fill_hold", {})["%s|%s" % (TEAM, A)] = (w.t - 100) if at is None else at
    kw._put(p, s)


def held(w):
    p = w.state / "ft2-keeper" / "state.json"
    return json.loads(p.read_text(encoding="utf-8")).get("fill_hold") or {}


def keeper(w, mp):
    """가짜 cli.run — fill 이 부른 argv 전부를 남긴다(rotation 인자 판독용 · 실제 실행은 그대로)."""
    k = w.keeper()
    cli_mod = type(k).close.__globals__["keeper_next"].cli
    calls = []

    def run(argv, real=cli_mod.run):
        calls.append(list(argv))
        return real(argv)

    mp.setattr(cli_mod, "run", run)
    return k, calls


def kn(k):
    return type(k).close.__globals__["keeper_next"]


def rot(k):
    return kn(k).rotate_parked(k, TEAM, A)


def assign_of(calls):
    return [c for c in calls if c and c[0] == "assign" and A in c]


def launched(w, work=None):
    got = [json.loads(x) for x in kw._lines(str(w.tmp / "bin" / "launch.py") + ".log")]
    got = [c[c.index("--work") + 1] for c in got]
    return got if work is None else [x for x in got if x == work]


def rotate_lines(lines):
    return [x for x in lines if x.startswith("FILL-ROTATE")]


def held_line(lines):
    return [x for x in lines if x.startswith("HELD-NEXT harness fill %s assign" % A)]


def c1(w, mp):     # ① 실사건 꼴 = 쉼 + 옛 holder 부재 → rotation 배정 · 새 attempt · deliver · launch 1
    seed(w)
    k, calls = keeper(w, mp)
    assert rot(k) == (True, OLD)
    lines = w.round(k)
    assert "FILL-ROTATE harness %s 옛 holder %s 부재" % (A, OLD) in rotate_lines(lines), lines
    assert "NEXT harness fill:%s -> %s %s" % (A, A, nx.nh(A)) in lines, lines
    assert [nx.count(w, x, A) for x in ("dispatch", "deliver")] == [2, 2], w.journal()
    assert "--rotation" in assign_of(calls)[0] and nx.ledger(w, A) == {"state": "seat", "seat": nx.nh(A)}
    assert launched(w, A) == [A] and nx.nh(A) in json.loads(w.tm.read_text(encoding="utf-8"))["alive"]


def c2(w, mp):     # ② 옛 holder 세션이 살아 있음 → rotation 0 · 보류 1 · launch 0
    seed(w), alive(w, OLD)
    k, _ = keeper(w, mp)
    assert rot(k) == (False, "")
    lines = w.round(k)
    assert held_line(lines) and "완료 유보" in held_line(lines)[0], lines
    assert rotate_lines(lines) == [] and launched(w, A) == [] and nx.count(w, "dispatch", A) == 1


def c3(w, mp):     # ③ 부재 판독 불가(rc 2) → rotation 0 · 보류 1 · launch 0
    seed(w), absent_rc(w, rc=2)
    k, _ = keeper(w, mp)
    assert rot(k) == (False, "")
    lines = w.round(k)
    assert held_line(lines) and rotate_lines(lines) == [] and launched(w, A) == []


def c4(w, mp):     # ④ 최신 attempt 가 쉼이 아님(owner 가 남음) → rotation 0 · 지금 동작
    seed(w)
    k, _ = keeper(w, mp)
    owner_add(k)
    assert rot(k) == (False, "")
    lines = w.round(k)
    assert rotate_lines(lines) == [] and launched(w, A) == [] and nx.count(w, "dispatch", A) == 1


def c5(w, mp):     # ⑤ 쉼 사유 launch-failed → rotation 0 · 지금 동작
    seed(w, reason="launch-failed")
    k, calls = keeper(w, mp)
    assert rot(k) == (False, "")
    lines = w.round(k)
    assert rotate_lines(lines) == [] and launched(w, A) == [] and nx.count(w, "dispatch", A) == 1
    assert "--rotation" not in assign_of(calls)[0]


def c6(w, mp):     # ⑥ 미확정 표식이 있는 일 + ① 꼴 → 보류 1 · launch 0(코어 판정 그대로)
    seed(w)
    k, _ = keeper(w, mp)
    uncertain_mark(k)
    assert rot(k) == (True, OLD)   # 조건은 참 — 막는 것은 코어 미확정 표식(K3)
    lines = w.round(k)
    assert held_line(lines) and rotate_lines(lines) == [] and launched(w, A) == []
    assert nx.count(w, "dispatch", A) == 1


def c7(w, mp):     # ⑦ 효과 의도 뒤 결과 없음 + 쉼 + 부재 → 완료 유보 그대로 · launch 0
    seed(w)
    cli(w, "effect", "--work", A, "--holder", OLD, "--gen", GEN, "--effect", "시험 효과")
    k, _ = keeper(w, mp)
    lines = w.round(k)
    assert held_line(lines) and "완료 유보" in held_line(lines)[0], lines
    assert rotate_lines(lines) == [] and launched(w, A) == [] and nx.count(w, "dispatch", A) == 1


def c8(w, mp):     # ⑧ 새 카드(착수 기록 0) → rotation 인자 없음 · launch 1(회귀)
    k, calls = keeper(w, mp)
    lines = w.round(k)
    assert "NEXT harness fill:%s -> %s %s" % (A, A, nx.nh(A)) in lines, lines
    assert assign_of(calls) and "--rotation" not in assign_of(calls)[0]
    assert rotate_lines(lines) == [] and launched(w, A) == [A]


def c9(w, mp):     # ⑨ 착수 → 결과 확정 → 쉼 → 채우기 = rotation 없이 통과
    seed(w, result=True)
    k, calls = keeper(w, mp)
    assert rot(k) == (False, "")
    lines = w.round(k)
    assert assign_of(calls) and "--rotation" not in assign_of(calls)[0], calls
    assert rotate_lines(lines) == [] and launched(w, A) == [A] and nx.count(w, "dispatch", A) == 2


def c10(w, mp):    # ⑩ ① 꼴 + 이미 보류 + 배정 원장 updated 가 보류 시각보다 뒤 → 그 바퀴에 풀리고 ① 길
    seed(w), hold(w), led(w, updated=1.0)
    w.t = w.t + 60
    led(w, updated=w.t)
    k, _ = keeper(w, mp)
    lines = w.round(k)
    assert rotate_lines(lines) and held(w) == {} and launched(w, A) == [A], lines


def c11(w, mp):    # ⑪ ⑩ 에서 배정 원장을 안 올림 → 채우기 0(보류 유지 · K6)
    seed(w, updated=1.0), hold(w)
    k, calls = keeper(w, mp)
    lines = w.round(k)
    assert [c for c in calls if A in c] == [] and rotate_lines(lines) == [] and launched(w, A) == []
    assert "%s|%s" % (TEAM, A) in held(w)


def c12(w, mp):    # ⑫ ① 뒤 FILL-ROTATE 1줄 · ②~⑨ 에는 0줄
    for i, (name, opts) in enumerate((("①", {}), ("②", {"alive": OLD}), ("③", {"rc": 2}), ("⑤", {"reason": "launch-failed"}))):
        sub = world(w.tmp / ("w%d" % i), mp)
        seed(sub, **{k: v for k, v in opts.items() if k == "reason"})
        if opts.get("alive"):
            alive(sub, OLD)
        if opts.get("rc"):
            absent_rc(sub, rc=opts["rc"])
        lines = sub.round()
        n = len(rotate_lines(lines))
        assert n == (1 if name == "①" else 0), (name, lines)


def c13(w, mp):    # ⑬ ① 뒤 같은 바퀴·다음 바퀴에 그 work 의 launch 가 2번 나가지 않는다
    seed(w)
    k, _ = keeper(w, mp)
    w.round(k)
    w.round(k)
    assert launched(w, A) == [A] and len(rotate_lines(k.lines)) == 1, k.lines


def c14(w, mp):    # ⑭ 회귀 — r1913 채우기 대표 사례(①·③)를 같은 팩에서 그대로 돌린다
    for i, name in enumerate(("①", "③")):
        (w.tmp / ("r%d" % i)).mkdir(exist_ok=True)
        fl.run(name, w.tmp / ("r%d" % i), mp)


CASES = {"①": c1, "②": c2, "③": c3, "④": c4, "⑤": c5, "⑥": c6, "⑦": c7,
         "⑧": c8, "⑨": c9, "⑩": c10, "⑪": c11, "⑫": c12, "⑬": c13, "⑭": c14}
KN = "adapters/pi/keeper_next.py"
OWNERS = '    if stem in (st.get("owners") or {}) or not parked'
MUTANTS = {   # 이름: (바꿀 글, 바꾼 글, 잡히는 사례)
    "M1": ('    if not old or k.probe(old) != "absent":', '    if not old or False:', "②"),      # 부재 판독을 안 봄
    "M2": ('    if stem in (st.get("owners") or {}) or not parked or parked.get("attempt") != disp or parked.get("reason") == "launch-failed":',
           '    if False:', "④"),                                                                  # 쉼 여부를 안 봄
    "M3": ('        if verb == "assign" and rot:\n            args = args + ["--rotation", "true"]',
           '        if verb == "assign":\n            args = args + ["--rotation", "true"]', "⑧"),             # 늘 rotation 을 넘김
    "M4": ('or parked.get("reason") == "launch-failed":', ':', "⑤"),                              # launch-failed 쉼도 포함
    "M5": ('    if not old or k.probe(old) != "absent":', '    if not old or k.probe(old) == "alive":', "③"),   # 판독 불가를 부재로 봄
    "M6": (OWNERS, '    if not parked', "④"),                                                     # owner 남음을 안 봄
}


@pytest.mark.parametrize("name", list(CASES))
def test_case(name, tmp_path, monkeypatch):
    CASES[name](world(tmp_path / "w", monkeypatch), monkeypatch)


@pytest.mark.parametrize("name", list(MUTANTS))
def test_mutant(name, tmp_path, monkeypatch):
    old, new, case = MUTANTS[name]
    shutil.copytree(kw.FT2, tree := tmp_path / "m" / "ft2", ignore=shutil.ignore_patterns("tests", "__pycache__"))
    text = (tree / KN).read_text(encoding="utf-8")
    assert text.count(old) == 1, (name, old)
    (tree / KN).write_text(text.replace(old, new), encoding="utf-8")
    (tmp_path / "w1").mkdir(), (tmp_path / "w2").mkdir()
    with pytest.raises(AssertionError):
        CASES[case](world(tmp_path / "w1", monkeypatch, ft2=tree), monkeypatch)
    CASES[case](world(tmp_path / "w2", monkeypatch), monkeypatch)   # 원본으로 같은 사례 1회 더 = PASS
