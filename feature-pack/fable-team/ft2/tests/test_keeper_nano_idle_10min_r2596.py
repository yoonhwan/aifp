"""r2596 나노 닫힘 10분 — 카드 반례 ①~⑨ · 변이 M1~M5 (카드 design/harness/indices/대기/r2596-nano-idle-close-10min.md).

끝 = 일반 쉼 길(settle_alive → look → park())에서 턴이 끝난 나노를 닫기 전에 기다리는 무활동 시간이 5분(300초)에서 10분(600초)이 된다.
착지가 끝난 좌석의 닫기(keeper_close · DONE_IDLE 300)와 정원이 꽉 찼고 급한 카드가 있을 때 자리를 비우는 닫기(urgent_park · DONE_IDLE 300)는 5분 그대로다.

대역 = keeper_world_r1812(임시 root · 가짜 tmux · 가짜 mbox) + r2535 사례 파일의 세계·좌석·한 바퀴 도구를 그대로 import.
실 tmux · 실 프로세스 종료 · 실 쪽지 0 · sleep 0(시계 = 주입 w.t) · 70초 안 · 시험 1개 = 한 사례(변이는 그 사례가 Red 인지까지).
기준판(팩 origin/main 1e8a4b4e · PARK_IDLE 300) = ① ③ 이 Red(5분에 닫힘) · 나머지 7 은 지금 길 그대로(양성 회귀).
"""
import importlib.util
import os
import shutil
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("nano_idle_cases_r2596", str(Path(__file__).with_name("test_keeper_park_idle_5min_r2535.py")))
cases = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cases)
FT2, KS, TEAM, world, card, nano, two, has, sent, park_log, unread, landed = (
    cases.FT2, cases.KS, cases.TEAM, cases.world, cases.card, cases.nano, cases.two, cases.has, cases.sent, cases.park_log,
    cases.unread, cases.landed)
kw = cases.kw


def settle(w, tag):
    """이 세계의 keeper_settle 판 — 값·손잡이를 직접 본다(변이 사본 트리에서도 같은 자리)."""
    return kw._mod(w.ft2 / KS, "%s_%d" % (tag, id(w)))


def notes(w):
    """«[자리 비움]» 쪽지 통 수."""
    return [x for x in sent(w) if "자리 비움" in x]


# ── ① 5분(301초)에 안 닫힌다 ────────────────────────────────────────────────────
def c01(w):   # ① 일반 쉼 길 · 301초(옛 문턱 + 1) · CPU idle 2회 → WORKING · 닫기 0 · «자리 비움» 0통(기준판 = PARKED · Red)
    card(w, "r9701")
    nano(w, "r9701", age=301)
    lines = two(w)
    assert has(lines, "WORKING harness r9701") and not w.tmux("kill-session"), lines
    assert not park_log(w) and not notes(w), (park_log(w), notes(w))


def c02(w):   # ② 601초(두 바퀴 끝) → PARKED(idle-done) + «[자리 비움]» 1통 · 로그 1줄 · 무활동 10분
    card(w, "r9702")
    nano(w, "r9702", age=571)
    lines = two(w)
    assert has(lines, "PARKED harness r9702", "idle-done") and len(w.tmux("kill-session")) == 1, lines
    assert w.kinds("parked") == 1, lines
    got = notes(w)
    assert len(got) == 1 and "무활동 10분" in got[0] and "head " in got[0], got
    log = park_log(w)
    assert len(log) == 1 and "«자리 비움»" in log[0] and "무활동 10분" in log[0], log


# ── ③④ 값·손잡이 ──────────────────────────────────────────────────────────────
def c03(w):   # ③ PARK_IDLE = 600 · 손잡이 없음·빈 값·글자·범위 밖 = 600(기준판 = 300 · Red)
    ks = settle(w, "r2596_c3")
    assert ks.PARK_IDLE == 600, ks.PARK_IDLE
    for env in ({}, {"FT2_PARK_IDLE_S": ""}, {"FT2_PARK_IDLE_S": "abc"}, {"FT2_PARK_IDLE_S": "10"}, {"FT2_PARK_IDLE_S": "9999"}):
        assert ks.park_idle(env) == 600, (env, ks.park_idle(env))
    assert ks.park_idle({"FT2_PARK_IDLE_S": "600"}) == 600   # 손잡이 = 기본값과 같은 값도 그대로 듣는다
    assert ks.park_idle({"FT2_PARK_IDLE_S": "60"}) == 60     # 하한 그대로(범위 안이면 값이 이긴다)


def c04(w):   # ④ 손잡이 FT2_PARK_IDLE_S = 300 → 301초에 닫힌다(손잡이는 새 기본값을 이긴다)
    card(w, "r9704")
    nano(w, "r9704", age=301)
    w.env["FT2_PARK_IDLE_S"] = "300"
    lines = two(w)
    assert has(lines, "PARKED harness r9704", "idle-done") and len(w.tmux("kill-session")) == 1, lines


# ── ⑤~⑧ 손 0 (착지 길 · 미읽음 관문 · 열린 턴 · 다른 값) ───────────────────────────
def c05(w):   # ⑤ 착지 끝 좌석 · 310초 → 닫힘 그대로(keeper_close 의 DONE_IDLE 300 · PARK_IDLE 을 안 본다)
    card(w, "r9705")
    landed(w, "r9705")
    lines = two(w)
    assert len(w.tmux("kill-session")) == 1, lines
    assert not [x for x in lines if "PARKED" in x and "r9705" in x], lines   # 착지 길 = park 줄 0 · 닫기만


def c06(w):   # ⑥ 601초 · 막는 미읽음 1통 → UNKNOWN mail-pending · 닫기 0(관문 그대로 · r2535 K2)
    card(w, "r9706")
    holder, _ = nano(w, "r9706", age=571)
    unread(w, holder)
    lines = two(w)
    assert has(lines, "UNKNOWN harness r9706", "mail-pending") and not w.tmux("kill-session"), lines


def c07(w):   # ⑦ 열린 턴(toolUse) — 301초 WORKING · 605초 waiting-input(질문 창 TURN_OPEN_IDLE 600 그대로)
    card(w, "r9707")
    card(w, "r9708")
    nano(w, "r9707", age=301, turn="toolUse", light=True)
    nano(w, "r9708", age=575, turn="toolUse", light=True)
    lines = two(w)
    assert has(lines, "WORKING harness r9707", "jsonl-active"), lines
    assert has(lines, "UNKNOWN harness r9708", "waiting-input") and [x for x in sent(w) if "waiting-input" in x], lines


def c08(w):   # ⑧ 손 0 값 — DONE_IDLE · SHARE_IDLE · ACCEPT_IDLE · TURN_OPEN_IDLE · WAIT_S · PARK_MIN/MAX · keeper_report OPEN_S
    ks = settle(w, "r2596_c8")
    assert (ks.DONE_IDLE, ks.SHARE_IDLE, ks.ACCEPT_IDLE) == (300, 300, 300), (ks.DONE_IDLE, ks.SHARE_IDLE, ks.ACCEPT_IDLE)
    assert (ks.TURN_OPEN_IDLE, ks.WAIT_S, ks.DAY) == (600, 600, 86400), (ks.TURN_OPEN_IDLE, ks.WAIT_S, ks.DAY)
    assert (ks.PARK_MIN, ks.PARK_MAX) == (60, 3600), (ks.PARK_MIN, ks.PARK_MAX)
    rep = kw._mod(w.ft2 / "adapters" / "pi" / "keeper_report.py", "r2596_rep_%d" % id(w))
    assert rep.OPEN_S == 600, rep.OPEN_S


# ── ⑨ 긴급 자리 확보 길은 5분 그대로 ─────────────────────────────────────────────
def c09(w):   # ⑨ 정원 참 · 급한 카드 → 자리 비우기(urgent_park · DONE_IDLE 300) — 301초에 1석 쉼 · «[자리 비움]» 0통
    card(w, "r9709")
    holder, _ = nano(w, "r9709", age=301)
    k = w.keeper()
    assert k.urgent_park(TEAM, "r9709") == holder, k.lines
    assert len(w.tmux("kill-session")) == 1 and w.kinds("parked") == 1, k.lines
    assert not notes(w) and not park_log(w), (notes(w), park_log(w))   # r2509 길은 intent 없이 park_seat = «자리 비움» 0통(쪽지 통 수 기록)


CASES = {"c01": c01, "c02": c02, "c03": c03, "c04": c04, "c05": c05, "c06": c06, "c07": c07, "c08": c08, "c09": c09}

MUTANTS = {   # 카드 변이 M1~M5 — (파일, 바꿀 줄, 바꾼 줄, Red 여야 하는 사례)
    "M1": (KS, "PARK_IDLE, WAIT_S, DAY = 600, 600, 86400", "PARK_IDLE, WAIT_S, DAY = 300, 600, 86400", c01),
    "M2": (KS, "    return got if PARK_MIN <= got <= PARK_MAX else PARK_IDLE",
           "    return got if PARK_MIN <= got <= PARK_MAX else 300", c03),   # 손잡이 없을 때만 옛 값
    "M3": (KS, "SHARE_IDLE, ACCEPT_IDLE = 300, 300", "SHARE_IDLE, ACCEPT_IDLE = 600, 300", c08),
    "M4": (KS, "DONE_IDLE = 300                             # 카드 착지",
           "DONE_IDLE = 600                             # 카드 착지", c05),   # 착지 길까지 10분으로
    "M5": (KS, "            if self.look(team, work, attempt, holder, age, stop, idle_s=DONE_IDLE, short=True) != \"REST\":",
           "            if self.look(team, work, attempt, holder, age, stop, idle_s=self.park(), short=True) != \"REST\":", c09),   # 긴급 길까지 10분으로
}


@pytest.mark.parametrize("name", list(CASES))
def test_case(name, tmp_path, monkeypatch):
    CASES[name](world(tmp_path, monkeypatch))


@pytest.mark.parametrize("name", list(MUTANTS))
def test_mutant(name, tmp_path, monkeypatch):
    rel, old, new, case = MUTANTS[name]
    tree = tmp_path / "m" / "ft2"
    shutil.copytree(FT2, tree, ignore=shutil.ignore_patterns("tests", "__pycache__"), copy_function=os.link)   # 하드링크 = 변이 5개 복사 시간 줄임
    text = (tree / rel).read_text(encoding="utf-8")
    assert text.count(old) == 1, (name, old)
    mut = tree / (Path(rel).stem + ".mut.py")   # 하드링크 사본이라 원본을 덮지 않는다 = 새 이름에 쓰고 바꿔치기
    mut.write_text(text.replace(old, new), encoding="utf-8")
    os.replace(mut, tree / rel)
    with pytest.raises(AssertionError):   # 변이 = Red 한 번(같은 사례의 초록은 사례가 본다)
        case(world(tmp_path / "w1", monkeypatch, tree))
