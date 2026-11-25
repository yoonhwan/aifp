"""r2498 keeper 관문 좁힘 — 근거 없는 석 «1석» 은 그 석만 정원 1칸으로 세고 남은 칸으로 다음 카드를 연다 (카드 반례 ①~⑦ · 변이 M1~M4).
대역 = r2400 시험 세계(r2055 settle 대역 · 임시 root · 가짜 tmux·mbox·gh·ps·pane · 실 tmux·Slack 0 · sleep 0(시계 = 주입 w.t)) 그대로.
«열림» = keeper_next.gates 참(r2400 ⑥ 과 같은 자리) · 좁힘 줄 = NEXT-NARROW 1줄.
기준판(2.1.6 keeper_next.py · 근거 없는 석 1 = 팀 통째 0) = ① ⑤ Red(좁힘 갈래·글이 아예 없다) · ⑥ ⑦ Red(앞 바퀴에 NEXT-NARROW 가 없어 전제부터 어긋난다) · ②③④ 양성 회귀(구판에서도 초록 = 지금 글 그대로).
변이는 사본에서만 · 변이마다 원본으로 같은 사례 1회 더.
"""
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("r2498_world", str(Path(__file__).with_name("keeper_no_lease_close_r2400.py")))
r = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r)
TEAM, kw = r.TEAM, r.kw


def rounds(w, k, n):
    """n바퀴 — 돌려준 줄 = 이번에 돈 바퀴 것만(keeper.lines 는 상주 누적이라 앞 줄은 잘라 낸다)."""
    cut = len(k.lines)
    for _ in range(n):
        r.rnd(w, k, dt=30)
    return k.lines[cut:]


def c1(tmp, mp, ft2=kw.FT2):   # ① 근거 없는 석 1 · 정원 8 중 산 석 3(그 석 포함) → NEXT-NARROW 1줄 · 다음 카드 열림
    w = r.world(tmp, mp, ft2, cap="8")
    r.switch(w, "true")   # 스위치 꺼짐 = 그 석은 닫히지 않고 남는다(실사건의 석)
    r.orphan(w, "r2498a")   # 근거 없음 = 관문이 세는 석
    r.orphan(w, "r2498b", age=100)   # 방금 활동 = 근거 있는 석
    r.orphan(w, "r2498c", age=100)
    k = w.keeper()
    lines = rounds(w, k, 3)   # 3바퀴째 b2f 관문이 지난 바퀴 «근거 없는 석» 을 본다
    assert r.t.has(lines, "NEXT-NARROW", TEAM, "근거 없는 석 1 — 그 석만 · 정원 3 / 8"), lines
    assert not r.t.has(lines, "NEXT-HOLD", TEAM, "근거 없는 석"), lines
    assert r.kn(k).gates(k, TEAM) is True, lines


def c2(tmp, mp, ft2=kw.FT2):   # ② 근거 없는 석 1 · 정원 가득(2 / 2 · 그 석 포함) → 지금과 같은 «나노 2 / 상한 2» NEXT-HOLD · NEXT-NARROW 0줄
    w = r.world(tmp, mp, ft2, cap="2")
    r.switch(w, "true")
    r.orphan(w, "r2498d", holder_alive=True)   # 그 석 + 그 work 의 holder = 2칸 = 정원
    k = w.keeper()
    lines = rounds(w, k, 3)
    assert r.t.has(lines, "NEXT-HOLD", TEAM, "나노 2 / 상한 2 — 다음 카드 0"), lines
    assert not r.t.has(lines, "NEXT-NARROW"), lines
    assert r.kn(k).gates(k, TEAM) is None, lines


def c3(tmp, mp, ft2=kw.FT2):   # ③ 근거 없는 석 2 → «NEXT-HOLD 근거 없는 석 2 — 다음 카드 0»(지금과 같은 글) · NEXT-NARROW 0줄
    w = r.world(tmp, mp, ft2, cap="8")
    r.switch(w, "true")
    r.orphan(w, "r2498i")
    r.orphan(w, "r2498j")
    k = w.keeper()
    lines = rounds(w, k, 3)
    assert r.t.has(lines, "NEXT-HOLD", TEAM, "근거 없는 석 2 — 다음 카드 0"), lines
    assert not r.t.has(lines, "NEXT-NARROW"), lines
    assert r.kn(k).gates(k, TEAM) is None, lines


def c4(tmp, mp, ft2=kw.FT2):   # ④ 근거 없는 석 0 → 지금과 바이트 같은 로그(«나노 2 / 상한 2» 그대로 · NEXT-NARROW 0줄)
    w = r.world(tmp, mp, ft2, cap="2")
    r.switch(w, "true")
    r.orphan(w, "r2498k", age=100, holder_alive=True)   # 활동 = 근거 있음 → 관문이 안 센다(정원은 2칸 그대로 찬다)
    k = w.keeper()
    lines = rounds(w, k, 3)
    assert r.t.has(lines, "NEXT-HOLD", TEAM, "나노 2 / 상한 2 — 다음 카드 0"), lines
    assert not r.t.has(lines, "NEXT-NARROW"), lines


def c5(tmp, mp, ft2=kw.FT2):   # ⑤ 좁힌 바퀴의 [긴급] = 하루 1통 그대로(둘째 바퀴 0통) · 글이 사실대로(«그 석만 세움 · 열기 계속»)
    w = r.world(tmp, mp, ft2, cap="8")
    r.switch(w, "true")
    r.orphan(w, "r2498e")
    k = w.keeper()
    lines = rounds(w, k, 4)   # 같은 날 네 바퀴
    assert r.t.has(lines, "NEXT-NARROW"), lines
    sent = r.urgent(w, "근거 없는 석")
    assert len(sent) == 1, r.t.sent(w)
    assert "그 석만 세움 · 열기 계속" in sent[0] and "다음 나노 열기 0" not in sent[0], sent


def c6(tmp, mp, ft2=kw.FT2):   # ⑥ tmux 목록 못 읽음(alive 빈 값) → 지금과 같음(관문 안 봄 · NEXT-NARROW 0줄 · 정원 여유 = 열림)
    w = r.world(tmp, mp, ft2, cap="8")
    r.switch(w, "true")
    r.orphan(w, "r2498f")
    k = w.keeper()
    lines = rounds(w, k, 3)   # 근거 없는 석 1 = state 에 남는다
    assert r.t.has(lines, "NEXT-NARROW"), lines
    d = json.loads(w.tm.read_text(encoding="utf-8"))
    d["alive"] = []
    kw._put(w.tm, d)
    lines = rounds(w, k, 1)
    assert not r.t.has(lines, "NEXT-NARROW") and not r.t.has(lines, "NEXT-HOLD", TEAM, "근거 없는 석"), lines


def c7(tmp, mp, ft2=kw.FT2):   # ⑦ ①의 석이 다음 바퀴에 사라짐 → NEXT-NARROW 0줄
    w = r.world(tmp, mp, ft2, cap="8")
    r.switch(w, "true")
    seat = r.orphan(w, "r2498g", holder_alive=True)
    k = w.keeper()
    lines = rounds(w, k, 3)
    assert r.t.has(lines, "NEXT-NARROW", TEAM, "근거 없는 석 1 — 그 석만 · 정원 2 / 8"), lines
    d = json.loads(w.tm.read_text(encoding="utf-8"))
    d["alive"] = [x for x in d["alive"] if x != seat]
    kw._put(w.tm, d)
    lines = rounds(w, k, 1)
    assert not r.t.has(lines, "NEXT-NARROW"), lines


CASES = {"①": c1, "②": c2, "③": c3, "④": c4, "⑤": c5, "⑥": c6, "⑦": c7}
MUTANTS = {
    "M1": ("keeper_next.py", "    if n > 1:", "    if n > 2:", "③"),   # 2석도 좁혀 엶
    "M2": ("keeper_next.py", "if rc == 0 else None   # r1929 여는 중 = 1칸", "- n if rc == 0 else None   # r1929 여는 중 = 1칸", "②"),   # 근거 없는 석을 정원에서 뺌
    "M3": ("keeper_next.py", '    if not got:\n        return 0\n    k.notify("harness", "noleft|', '    if not got:\n        return 0\n    if 0:\n        k.notify("harness", "noleft|', "⑤"),   # [긴급] 을 뺌
    "M4": ("keeper_next.py", "    if n > 1:", "    if n:", "①"),   # 좁힘 갈래를 지움(지금 판 = 1석도 팀 통째 0)
}


@pytest.mark.parametrize("name", list(CASES))
def test_case(name, tmp_path, monkeypatch):
    CASES[name](tmp_path / name, monkeypatch)


@pytest.mark.parametrize("name", list(MUTANTS))
def test_mutant(name, tmp_path, monkeypatch):
    rel, old, new, case = MUTANTS[name]
    pack = tmp_path / "ft2mut"
    shutil.copytree(kw.FT2, pack, ignore=shutil.ignore_patterns("tests", "__pycache__"))
    path = pack / "adapters" / "pi" / rel
    body = path.read_text(encoding="utf-8")
    assert body.count(old) == 1, (name, body.count(old))
    path.write_text(body.replace(old, new, 1), encoding="utf-8")
    with pytest.raises(AssertionError):
        CASES[case](tmp_path / (name + "-mut"), monkeypatch, pack)
    CASES[case](tmp_path / (name + "-ok"), monkeypatch)   # 변이마다 원본으로 같은 사례 1회 더
