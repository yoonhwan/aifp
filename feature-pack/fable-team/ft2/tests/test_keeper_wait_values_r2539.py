"""r2539 keeper 대기 값 5분 — 반례 ①~㉒ · 변이 M1~M20 (카드 design/harness/indices/대기/r2539-keeper-wait-values-5min-close-rest-lock-open.md).

대역 = 실 모듈(adapters/pi) + 임시 root(tmp_path) + 주입 시계 · 실 tmux · 실 프로세스 종료 · 실 쪽지 · 실 state 0 · sleep 0 · 70초 안.
값 표 = keeper(닫기 재시도 300 · git 쉼 300 · 죽은 잠금 300) · keeper_report(손 닫기 후보 600) · keeper_launch(이어 열기 600) ·
keeper_settle(임자 가름 300 · 접수만 300 · 열린 턴 600 = 질문 창) · keeper_stall(멈춤 판정 600) · transition_watch(카드 전이 600 · 600 · 600).
손잡이 = 값마다 env 1개 · 정수 60 ~ 600(그 아래·글자·빈 값 = 새 기본 · 600 초과 = 600 으로 자름 · K12·H1) · keeper 가 바퀴 시작에 읽는다.
★열린 턴은 어떤 값에서도 닫히지 않는다★ — look() 은 WORKING·UNKNOWN 만 내고 kill·park 은 부르는 쪽 몫이다(K9 · ⑮~⑱).
"""
import importlib.util
import os
import shutil
import time
from pathlib import Path

import pytest

PI = Path(__file__).resolve().parents[1] / "adapters" / "pi"
TEAM, SEAT = "harness", "biz-harness-nano-r9001#0"
CHAIN = [(100, 1, 0.0, "zsh"), (101, 100, 0.0, "npm"), (102, 101, 0.0, "node"), (103, 102, None, "pi")]
NAMES = ("keeper", "keeper_block", "keeper_report", "keeper_launch", "keeper_settle", "keeper_stall", "transition_watch",
         "keeper_manual_close", "keeper_close")


def load(pi=PI, tag="r2539"):
    """모듈 묶음 — 변이는 사본 트리(pi)에서 다시 읽어야 사례가 변이 판을 본다."""
    got = {}
    for name in NAMES:
        spec = importlib.util.spec_from_file_location("%s_%s_%s" % (tag, name, id(pi)), str(Path(pi) / (name + ".py")))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        got[name] = module
    return got


M = load()


class Clock:
    def __init__(s, t=1794000000.0):
        s.t = t

    def __call__(s):
        return s.t


def keeper(tmp, m=M, clock=None, **env):
    clock = clock or Clock()
    return m["keeper"].Keeper(str(tmp), env=dict({"HOME": str(tmp / "home")}, **env), now=clock)


def chain(cpu=0.0):
    return [(pid, ppid, cpu if c is None else c, cmd) for pid, ppid, c, cmd in CHAIN]


def logbo(k, kind):
    return [x for x in k.lines if x.startswith(kind)]


# ── ① 닫기 재시도 5분 · ③ git 쉼 창 ─────────────────────────────────────────────
def c01(tmp, m=M):
    k = keeper(tmp, m)
    k.state["held"] = {SEAT: 1000.0}
    clock = Clock(1000.0)
    k.now = clock
    for age, want in ((0, True), (299, True), (300, False), (301, False)):
        clock.t = 1000.0 + age
        assert k.retry_wait(SEAT) is want, (age, want)
    k.env["FT2_CLOSE_RETRY_S"] = "601"   # 손잡이 상한 600(H1) — 600 으로 잘린다
    for age, want in ((599, True), (601, False)):
        clock.t = 1000.0 + age
        assert k.retry_wait(SEAT) is want, (age, want)
    wait = m["keeper"].wait_env
    assert wait({"FT2_CLOSE_RETRY_S": "10"}, "FT2_CLOSE_RETRY_S", 300, 600) == 300      # 60 아래 = 새 기본
    assert wait({"FT2_CLOSE_RETRY_S": "100000"}, "FT2_CLOSE_RETRY_S", 300, 600) == 600   # 600 초과 = 600 으로 자름


# ── ② HELD-SEAT 막힘 줄 = 재관측이면 first 를 잇는다 ────────────────────────────
def hold(text="s1 rc 3 닫기 실패"):
    return [("HELD-SEAT", "seats-t1", text)]


def c02(tmp, m=M):
    kb = m["keeper_block"]
    key = kb.same("HELD-SEAT", "seats-t1", hold()[0][2])
    seen = kb.remember({}, hold(), 0)
    assert seen[key]["first"] == 0
    assert kb.remember(seen, [], 299)[key]["first"] == 0            # 관측 없는 바퀴 299초 = 수명 안
    assert kb.remember(seen, hold(), 745)[key]["first"] == 0        # 745초에 다시 관측 = first 를 잇는다(DA#60 H1)
    assert kb.remember(seen, hold(), 1300)[key]["first"] == 0       # 바퀴가 길게 서도 그대로
    assert kb.remember(kb.remember({}, hold(), 0), [], 599) != {}   # 관측 없는 바퀴 599초 = 수명 안(300 + 300 = 600)
    assert kb.remember(kb.remember({}, hold(), 0), [], 601) == {}   # 601초 = 지운다
    assert kb.remember(kb.remember({}, hold(), 0, 600), [], 601, 600) == {}   # RETRY_S=600 이어도 수명은 600(900 아님 · H1)
    assert kb.remember(kb.remember({}, hold(), 0, 60), [], 361, 60) == {}      # 수명 = min(60 + 300, 600) = 360
    other = [("판정 불가", "t1", "w1 1")]
    okey = kb.same("판정 불가", "t1", "w1 1")
    assert kb.remember(kb.remember({}, other, 0), [], 400) == {}          # HELD-SEAT 아닌 종류 = 지금 차례(300초)
    assert kb.remember(kb.remember({}, other, 0), other, 400)[okey]["first"] == 400   # 새 first(잇기 0)


# ── ④⑤⑥⑦㉒ 죽은 바퀴 잠금 = pid 대조 ─────────────────────────────────────────
def locked(tmp, m, age, content, body=None, **env):
    """잠금 하나를 만들고 한 바퀴 — body(k) 반환 = 이번 바퀴 결과(잠금 안에서 읽는다)."""
    k = keeper(tmp, m, **env)
    os.makedirs(k.dir, exist_ok=True)
    lock = Path(k.dir) / "keeper.lock"
    lock.write_text(content, encoding="utf-8")
    at = time.time() - age
    os.utime(lock, (at, at))
    return k, lock, k.locked(lambda: (body or (lambda kk: "바퀴 돎"))(k))


def c03(tmp, m=M):
    pid = str(os.getpid())
    pidnow = lambda kk: (Path(kk.dir) / "keeper.lock").read_text(encoding="utf-8").strip()
    k, lock, out = locked(tmp / "a", m, 301, "999999\n", body=pidnow)   # ④ 나이 301 · pid 죽음 = 지우고 바퀴 돈다
    assert out == pid and logbo(k, "STALE-LOCK") and "5분 넘은 잠금" in " ".join(k.lines), k.lines
    k, lock, out = locked(tmp / "b", m, 301, pid + "\n")     # ⑤ pid 살아 있음 = 지우지 않는다
    assert out is None and lock.read_text(encoding="utf-8").strip() == pid and logbo(k, "LOCK-LIVE"), k.lines
    k, lock, out = locked(tmp / "c", m, 299, "999999\n")     # ⑥ 299초 = 지금과 같다(SKIP)
    assert out is None and logbo(k, "SKIP") and lock.read_text(encoding="utf-8").strip() == "999999", k.lines
    pidnow = lambda kk: (Path(kk.dir) / "keeper.lock").read_text(encoding="utf-8").strip()
    k, lock, out = locked(tmp / "d", m, 301, "", body=pidnow)   # ⑦ 빈 파일 = 옛 판 잠금 = 지운다 · 이 바퀴 pid 를 적는다
    assert out == pid, k.lines
    k, lock, out = locked(tmp / "e", m, 301, "999999\n", FT2_LOCK_STALE_S="600")   # ㉒ 손잡이 600 = 아직 안 지운다
    assert out is None and lock.read_text(encoding="utf-8").strip() == "999999", k.lines


def c04(tmp, m=M):
    mc, k = m["keeper_manual_close"], keeper(tmp, m)
    os.makedirs(k.dir, exist_ok=True)
    lock = Path(k.dir) / "keeper.lock"
    lock.write_text("999999\n", encoding="utf-8")   # ⑧ 수동 닫기도 같은 규칙 — pid 가 적힌 잠금
    at = time.time() - 301
    os.utime(lock, (at, at))
    assert mc.lock(k, wait=0.2) == str(lock) and lock.read_text(encoding="utf-8").strip() == str(os.getpid())
    os.unlink(str(lock))
    lock.write_text(str(os.getpid()) + "\n", encoding="utf-8")
    os.utime(lock, (at, at))
    assert mc.lock(k, wait=0.1) is None   # pid 살아 있음 = 나이 무관 유지(바퀴 0)


# ── ⑨ 손 닫기 후보 10분 ───────────────────────────────────────────────────────
def report_at(tmp, m, age, **env):
    clock = Clock(10_000.0)
    k = keeper(tmp, m, clock=clock, **env)
    k.state["open"] = {SEAT: {"team": TEAM, "since": clock.t - age}}
    k.skip, k.sent = set(), []
    k.probe = lambda seat: "alive"
    k.alerts = k.flush = lambda: None
    k.notify = lambda team, key, body: k.sent.append(body) or True
    return m["keeper_report"].Reporting.report(k), k.sent


def c05(tmp, m=M):
    line, sent = report_at(tmp / "a", m, 601)
    assert line.startswith("손 닫기 후보 1") and sent and "10분 넘게" in line, (line, sent)
    line, sent = report_at(tmp / "b", m, 599)
    assert line.startswith("손 닫기 후보 0") and not sent, (line, sent)
    line, sent = report_at(tmp / "c", m, 601, FT2_OPEN_REPORT_S="1800")   # 상한 600 초과 = 600 으로 잘린다(H1)
    assert line.startswith("손 닫기 후보 1") and sent, (line, sent)
    line, sent = report_at(tmp / "d", m, 599, FT2_OPEN_REPORT_S="601")     # 601 = 600 으로 잘림 → 599 는 아직 후보 0
    assert line.startswith("손 닫기 후보 0") and not sent, (line, sent)


# ── ⑩ 이어 열기 문턱 10분 ────────────────────────────────────────────────────
def c06(tmp, m=M):
    kl, k = m["keeper_launch"], keeper(tmp, m)
    got = {"at": "2026-11-13T10:00:00"}
    base = kl.time.mktime(kl.time.strptime(got["at"], "%Y-%m-%dT%H:%M:%S"))
    for age, want in ((599, True), (601, False)):
        k.now = (lambda a: (lambda: base + a))(age)
        assert kl.fresh(k, got) is want, age
    k.env["FT2_OPEN_STALE_S"] = "900"   # 상한 600 초과 = 600 으로 잘린다(H1)
    k.now = lambda: base + 599
    assert kl.fresh(k, got) is True
    k.now = lambda: base + 601
    assert kl.fresh(k, got) is False


# ── ⑪ 임자 가름 5분 ──────────────────────────────────────────────────────────
def c07(tmp, m=M):
    cwd = tmp / "shared"
    cwd.mkdir(parents=True, exist_ok=True)
    sessions = tmp / "home" / ".pi" / "agent" / "sessions" / ("--%s--" % str(cwd).strip("/").replace("/", "-"))
    sessions.mkdir(parents=True, exist_ok=True)
    log = sessions / "s.jsonl"
    log.write_text('{"type": "session"}\n', encoding="utf-8")
    k = keeper(tmp, m)
    k.seat_path = lambda seat: str(cwd)
    k.seat_born = lambda seat: 0
    k.alive_sessions = lambda: ["biz-harness-arch-a#0", "biz-harness-arch-b#0"]
    for age, want in ((299, None), (301, str(log))):
        os.utime(log, (k.now() - age, k.now() - age))
        assert k.seat_log("biz-harness-arch-a#0") == want, (age, want)


# ── ⑬⑭⑮⑯⑰⑱ 열린 턴 = 알림만 · 닫기 0 ────────────────────────────────────────
def looking(tmp, m, clock, cpu=0.0, idle_seed=True):
    k = keeper(tmp, m, clock=clock)
    k.tmuxc_status, k.pane_info = (lambda s: "clean"), (lambda s: (100, "pi"))
    k.ps_rows = lambda: chain(cpu)
    k.park = lambda: 300
    k.verdict = lambda *a: "WORKING " + " ".join(str(x) for x in a[3:])   # kill·park 0(판정 줄만)
    k.unknown_seat = lambda team, work, attempt, holder, code, why="": "UNKNOWN " + code
    if idle_seed:
        k.state.setdefault("cpu", {})[SEAT] = {"at": clock() - 30, "cpu": 0.0, "first": clock() - 30, "pane_pid": 100}
    return k


def c08(tmp, m=M):
    clock = Clock(5000.0)
    k = looking(tmp / "a", m, clock)
    assert k.look(TEAM, "w", "a1", SEAT, 599, "toolUse").startswith("WORKING"), "599초 = 아직 문턱 안"
    assert k.look(TEAM, "w", "a1", SEAT, 601, "toolUse") == "UNKNOWN waiting-input"    # ⑭
    k = looking(tmp / "b", m, clock)
    assert k.look(TEAM, "w", "a1", SEAT, 599, None).startswith("WORKING")
    assert k.look(TEAM, "w", "a1", SEAT, 601, None) == "UNKNOWN turn-open"            # ⑬
    k = looking(tmp / "c", m, clock, cpu=2.0)
    assert k.look(TEAM, "w", "a1", SEAT, 601, "toolUse").startswith("WORKING")        # ⑮ CPU busy = 근거 0
    assert k.look(TEAM, "w", "a1", SEAT, 3601, None).startswith("WORKING")
    k = looking(tmp / "d", m, clock, idle_seed=False)
    assert k.look(TEAM, "w", "a1", SEAT, 601, None).startswith("WORKING")             # ⑯ 표본 1개 = 아직 idle 아님
    assert k.look(TEAM, "w", "a1", SEAT, 601, "toolUse").startswith("WORKING")        # CPU 표본 1개 = 알림 0(M14)
    k = looking(tmp / "e", m, clock)
    assert k.look(TEAM, "w", "a1", SEAT, 10, "toolUse").startswith("WORKING")         # ⑰ jsonl 이 늘었다
    k = looking(tmp / "f", m, clock)
    got = k.look(TEAM, "w", "a1", SEAT, 7200, "toolUse", landed=True)                 # ⑱ 착지 좌석의 안 닫힌 턴
    assert got.startswith("WORKING") and got != "REST", got                            # 닫기 0(kill·park 0)
    assert k.look(TEAM, "w", "a1", SEAT, 601, "stop") == "REST"                        # 턴이 끝난 좌석 = 지금 길 그대로


# ── ⑲ 멈춤 판정 10분 ────────────────────────────────────────────────────────
def c09(tmp, m=M):
    stall = m["keeper_stall"].Stall
    k = keeper(tmp, m)
    got = stall(k)
    assert (got.stall_s, got.after_s) == (600, 600)
    k.env["FT2_KEEPER_STALL_S"] = "601"
    assert stall(k).stall_s == 600          # 600 초과 = 600 으로 잘린다(H1)
    k.env["FT2_KEEPER_STALL_S"] = "900"
    assert stall(k).stall_s == 600          # 옛 값 900 도 600 으로 잘린다
    k.env["FT2_KEEPER_STALL_S"] = "10"
    assert stall(k).stall_s == 600          # 60 아래 = 새 기본


# ── ⑳ 카드 전이 알림 10분 + ㉑ 손잡이 범위 ─────────────────────────────────────
def c10(tmp, m=M):
    tw, k = m["transition_watch"], keeper(tmp, m)
    got = tw.limits(k)
    assert (got["ledger"], got["prereq"], got["nano"]) == (600, 600, 600)
    assert got["land"] == 600 and got["reject"] == tw.DAY and got["prog"] == tw.DAY   # 다른 값 그대로
    k.env["FT2_TW_DONE_OPEN_S"] = "60"
    assert tw.limits(k)["ledger"] == 60        # 손잡이 아래 끝
    k.env["FT2_TW_DONE_OPEN_S"] = "3600"
    assert tw.limits(k)["ledger"] == 600       # 옛 값 3600 도 600 으로 잘린다(H1)
    k.env["FT2_TW_DONE_OPEN_S"] = "601"
    assert tw.limits(k)["ledger"] == 600       # 601 = 600 으로 잘림
    k.env["FT2_TW_DONE_OPEN_S"] = "10"
    assert tw.limits(k)["ledger"] == 600       # 60 미만 = 새 기본


def c11(tmp, m=M):
    wait = m["keeper"].wait_env
    table = (("FT2_CLOSE_RETRY_S", 300), ("FT2_GIT_REST_S", 300), ("FT2_LOCK_STALE_S", 300), ("FT2_OPEN_REPORT_S", 600),
             ("FT2_OPEN_STALE_S", 600), ("FT2_SHARE_IDLE_S", 300), ("FT2_ACCEPT_IDLE_S", 300), ("FT2_TURN_WAIT_S", 600),
             ("FT2_KEEPER_STALL_S", 600))
    for name, default in table:
        for above in (600, 900, 1800, 3600):   # 앞 값이 얼마든 상한 = 600
            assert wait({}, name, default, above) == default, name
            assert wait({name: "60"}, name, default, above) == 60, name
            assert wait({name: "599"}, name, default, above) == 599, name
            assert wait({name: "600"}, name, default, above) == 600, name
            assert wait({name: "601"}, name, default, above) == 600, (name, "601")   # 600 으로 잘림(H1)
            assert wait({name: str(above)}, name, default, above) == 600, (name, above)
            for bad in ("10", "abc", "", "  "):
                assert wait({name: bad}, name, default, above) == default, (name, bad)


# ── 값 표 ───────────────────────────────────────────────────────────────────
def c12(tmp, m=M):
    k = m["keeper"]
    assert (k.REST_S, k.STALE_S) == (300, 300)
    assert m["keeper_close"].RETRY_S == 300
    assert m["keeper_report"].OPEN_S == 600
    assert m["keeper_launch"].OPEN_STALE == 600
    ks = m["keeper_settle"]
    assert (ks.SHARE_IDLE, ks.ACCEPT_IDLE, ks.TURN_OPEN_IDLE, ks.WAIT_S) == (300, 300, 600, 600)
    assert ks.SAMPLE_KEEP == 600   # 표본 수명이라 5분 기준 밖
    assert m["keeper_stall"].STALL_S == 600
    tw = m["transition_watch"]
    assert [(row[0], row[3]) for row in tw.ROWS if row[2] in ("FT2_TW_DONE_OPEN_S", "FT2_TW_PREREQ_S", "FT2_TW_NANO_S")] == \
        [("장부 완료 · 카드 열림", 600), ("선행 풀림 미반영", 600), ("진행 · 나노 승계 막힘", 600)]


CASES = {"①": c01, "②": c02, "④⑤⑥⑦㉒": c03, "⑧": c04, "⑨": c05, "⑩": c06, "⑪": c07, "⑬~⑱": c08,
         "⑲": c09, "⑳": c10, "㉑": c11, "값표": c12}
MUTANTS = {   # 변이 = 사본 트리 한 번 · 그 사례가 Red 여야 한다
    "M1": ("keeper_close.py", "GIT_S, RETRY_S = 25, 300", "GIT_S, RETRY_S = 25, 600", "①"),
    "M2": ("keeper_block.py", '        if kind == "HELD-SEAT" and key in live:', "        if False:", "②"),
    "M19": ("keeper_block.py", "    seat_life = min((RETRY_S if retry_s is None else retry_s) + SEAT_EXTRA_S, SEAT_MAX_S)",
            "    seat_life = (RETRY_S if retry_s is None else retry_s) + SEAT_EXTRA_S", "②"),   # 600 상한 뺌 → 1000초
    "M20": ("keeper_block.py", '        if kind == "HELD-SEAT" and key in live:', "        if key in live:", "②"),
    "M3": ("keeper.py", "REST_S = 300   # r2357 K1", "REST_S = 600   # r2357 K1", "값표"),
    "M4": ("keeper.py", "GIT_S, CALL_S, ROUND_S, STALE_S, FETCH_S = 7, 7, 60, 300, 7",
           "GIT_S, CALL_S, ROUND_S, STALE_S, FETCH_S = 7, 7, 60, 600, 7", "④⑤⑥⑦㉒"),
    "M5": ("keeper.py", "        return (age > self.lock_stale() and (pid is None or not pid_alive(pid))), pid, age",
           "        return (age > self.lock_stale()), pid, age", "④⑤⑥⑦㉒"),
    "M6": ("keeper.py", "        return (age > self.lock_stale() and (pid is None or not pid_alive(pid))), pid, age",
           "        return (age > self.lock_stale() and pid is not None and not pid_alive(pid)), pid, age", "④⑤⑥⑦㉒"),
    "M7": ("keeper_manual_close.py", '            fh.write("%d\\n" % os.getpid())', '            fh.write("")', "⑧"),
    "M8": ("keeper_report.py", "CALL_S, OPEN_S = 7, 600", "CALL_S, OPEN_S = 7, 1800", "⑨"),
    "M9": ("keeper_launch.py", "OPEN_STALE = 600", "OPEN_STALE = 900", "⑩"),
    "M10": ("keeper_settle.py", "SHARE_IDLE, ACCEPT_IDLE = 300, 300", "SHARE_IDLE, ACCEPT_IDLE = 3600, 300", "⑪"),
    "M11": ("keeper_settle.py", "SHARE_IDLE, ACCEPT_IDLE = 300, 300", "SHARE_IDLE, ACCEPT_IDLE = 300, 3600", "값표"),
    "M12": ("keeper_settle.py", "TURN_OPEN_IDLE = WAIT_S", "TURN_OPEN_IDLE = 3600", "⑬~⑱"),
    "M13": ("keeper_settle.py", "PARK_IDLE, WAIT_S, DAY = 600, 600, 86400", "PARK_IDLE, WAIT_S, DAY = 600, 900, 86400", "⑬~⑱"),
    "M14": ("keeper_settle.py", '            if stop is not None and age is not None and age >= turn_s and cpu == "idle":',
            "            if stop is not None and age is not None and age >= turn_s:", "⑬~⑱"),
    "M15": ("keeper_settle.py", "            idle_s = turn_s", '            return "REST"', "⑬~⑱"),
    "M16": ("keeper_stall.py", "STALL_S = 600", "STALL_S = 900", "⑲"),
    "M17": ("transition_watch.py", '("장부 완료 · 카드 열림", "ledger", "FT2_TW_DONE_OPEN_S", 600, "")',
            '("장부 완료 · 카드 열림", "ledger", "FT2_TW_DONE_OPEN_S", 3600, "")', "⑳"),
    "M18": ("transition_watch.py", "            if got[fn] > ABOVE[fn]:", "            if False:", "⑳"),   # 상한 자름 뺌 → 3600 그대로
}


@pytest.mark.parametrize("name", list(CASES))
def test_case(name, tmp_path):
    assert CASES[name](tmp_path) is None


@pytest.mark.parametrize("name", list(MUTANTS))
def test_mutant(name, tmp_path):
    rel, old, new, case = MUTANTS[name]
    tree = tmp_path / "m" / "ft2"
    shutil.copytree(PI.parents[1], tree, ignore=shutil.ignore_patterns("tests", "__pycache__"), copy_function=os.link)   # 하드링크 사본
    pi = tree / "adapters" / "pi"
    mut = pi / rel
    text = mut.read_text(encoding="utf-8")
    assert text.count(old) == 1, (name, old)
    new_path = pi / (Path(rel).stem + ".mut.py")   # 하드링크 원본을 안 덮는다 = 새 이름에 쓰고 바꿔치기
    new_path.write_text(text.replace(old, new), encoding="utf-8")
    os.replace(new_path, mut)
    with pytest.raises(AssertionError):   # 변이 판 = 그 사례가 잡는다
        CASES[case](tmp_path / "m1", load(pi, "mut"))
    assert CASES[case](tmp_path / "o1") is None   # 원본으로 같은 사례 1회 = PASS(대조)
