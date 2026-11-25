"""r2549 ft2 keeper — 닫기 도구 자리(FT_SEAT_CLOSE_BIN)가 빈 셸에서 부른 수동 닫기가 «정지 중» 이 아니라 «닫기 도구 자리 없음» 으로 거절된다.

카드 반례 ①~⑦ · 변이 M1~M4. 무대 = r1812 keeper_world(임시 리포 · 가짜 tmux · 가짜 판정기) + r2401 world(원장·우편·자율 스텁·실 worktree).
실 tmux·실 keeper·실 명부·sleep 0 · 변이는 사본(임시)에서만 돌리고 같은 사례를 원본에서 1회 더 돈다.
빈 자리에서 판정기가 상대 경로 «ft-all-stop.sh» 가 되면 rc 127 → «판정 불가 = 정지» → «정지 중» 이라는 틀린 글이 나갔다(실사건 2026-11-23).
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

KS, KM = "adapters/pi/keeper_settle.py", "adapters/pi/keeper_manual_close.py"
EMPTY = "판정기 자리 없음(FT_SEAT_CLOSE_BIN 빔)"


def _mod(name, alias):
    spec = importlib.util.spec_from_file_location(alias, str(Path(__file__).with_name(name)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


import keeper_world_r1812 as kw   # r2401 시험과 «같은 모듈» 이어야 팩 자리 바꿔 끼우기(pack)가 그 세계에도 걸린다

CL = _mod("test_keeper_close_seat_r2401.py", "r2549_close")


def _load(path, alias):
    spec = importlib.util.spec_from_file_location(alias, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def pack(ft2):
    """r1812 World 의 팩 자리(기본값 = 실제 팩) 를 임시 사본으로 바꿔 끼운다 — 변이 사본에서 같은 사례를 돌리기 위해서만."""
    real = kw.World
    kw.World = lambda tmp, mp: real(tmp, mp, ft2)
    try:
        yield
    finally:
        kw.World = real


def world(tmp, mp, ft2=FT2, **kwarg):
    """r2401 세계 그대로(원장·우편·자율 스텁·실 worktree) — ft2 를 주면 그 사본의 core/cli.py 로 돈다."""
    Path(tmp).mkdir(parents=True, exist_ok=True)   # r2401 world 는 pytest tmp_path 를 전제한다 — 변이 대조용 하위 폴더도 만든다
    with pack(ft2):
        return CL.world(tmp, mp, **kwarg)


def bare(w):
    """닫기 도구 자리도 판정기 자리도 없는 셸 — 실사건의 그 환경."""
    w.env.pop("FT_SEAT_CLOSE_BIN", None)
    w.env.pop("FT2_ALL_STOP_JUDGE", None)


def trap(w):
    """작업 폴더에 «ft-all-stop.sh» 를 깔고 부르면 흔적을 남긴다 — 상대 경로로 주워 가는지 본다(⑦)."""
    log = w.root / "judge-calls.log"
    stub = w.root / "ft-all-stop.sh"
    stub.write_text('#!/usr/bin/env bash\necho "$@" >> "%s"\necho \'{"state": "off", "except": [], "since": null}\'\n' % log,
                    encoding="utf-8")
    stub.chmod(0o755)
    return log


def beside(w):
    """닫기 도구 옆 ft-all-stop.sh = 이 세계의 판정기(off) — close_bin 만 준 셸(②)."""
    path = Path(w.close).parent / "ft-all-stop.sh"
    path.write_text(kw.JUDGE, encoding="utf-8")
    path.chmod(0o755)


def c01(tmp, mp, ft2=FT2):
    """① env 둘 다 없음 + --close-seat → rc 2 · «닫기 도구 자리 없음» · «정지 중» 0 · 판정기 호출 0 · 기록 0 · kill 0."""
    w = world(tmp, mp, ft2)
    log, _ = trap(w), bare(w)
    lines, rc = CL.run(w)
    assert rc == 2, lines
    line = CL.one(lines, "REJECT 닫기 도구 자리 없음")
    assert "FT_SEAT_CLOSE_BIN 이 빔" in line and "launchd com.biz.ft2-keeper" in line, line
    assert [x for x in lines if "정지 중" in x] == [], lines
    assert not log.exists(), log.read_text(encoding="utf-8")
    CL.untouched(w)


def c02(tmp, mp, ft2=FT2):
    """② FT_SEAT_CLOSE_BIN 만 줌(옆에 판정기 off) → 자리 검사 통과 · 지금처럼 닫기 진행(CLOSED-MANUAL rc 0 · kill 1)."""
    w = world(tmp, mp, ft2)
    w.env.pop("FT2_ALL_STOP_JUDGE"), beside(w)
    lines, rc = CL.run(w)
    assert rc == 0, lines
    assert "CLOSED-MANUAL" in CL.one(lines, "CLOSED-MANUAL") and CL.kills(w) == ["=" + CL.S], (lines, CL.kills(w))


def c03(tmp, mp, ft2=FT2):
    """③ FT2_ALL_STOP_JUDGE 만 줌 → 판정은 그 자리로 하고 자리 검사는 통과(닫기 진행 rc 0)."""
    w = world(tmp, mp, ft2)
    w.env.pop("FT_SEAT_CLOSE_BIN")
    lines, rc = CL.run(w)
    assert rc == 0, lines
    assert "CLOSED-MANUAL" in CL.one(lines, "CLOSED-MANUAL") and CL.kills(w) == ["=" + CL.S], (lines, CL.kills(w))


def c04(tmp, mp, ft2=FT2):
    """④ env 줌 + 판정기 rc 1 → 지금 글자 그대로 «판정 불가 … 정지로 봄» · «정지 중» 거절 rc 2 · 기록 0 · kill 0."""
    w = world(tmp, mp, ft2)
    w.env["FT2_FAKE_JUDGE"] = "rc1"
    lines, rc = CL.run(w)
    assert rc == 2, lines
    bad = [x for x in lines if x.startswith("판정 불가") and "ALL_STOP" in x]
    assert len(bad) == 1 and "정지로 봄" in bad[0], lines
    assert "정지 시각 판독 불가" in CL.one(lines, "REJECT 정지 중"), lines
    CL.untouched(w)


def c05(tmp, mp, ft2=FT2):
    """⑤ env 줌 + state stop(정지 전에 뜬 석) → 지금 그대로 «정지 중» 거절(세션 생성 ≤ 정지) · 손 0."""
    w = world(tmp, mp, ft2, stop=True, since=CL.SINCE, born=CL.SINCE)
    lines, rc = CL.run(w)
    assert rc == 2, lines
    assert "세션 생성 %d ≤ 정지 %d" % (CL.SINCE, CL.SINCE) in CL.one(lines, "REJECT 정지 중"), lines
    CL.untouched(w)


def c06(tmp, mp, ft2=FT2):
    """⑥ 데몬 한 바퀴(--once)에서 env 둘 다 없음 → «판정 불가 ALL_STOP 판정 불가(판정기 자리 없음…)» 1줄 · 정지로 봄 · kill·park·fill 0 · 다음 바퀴 0줄."""
    tmp.mkdir(parents=True, exist_ok=True)
    with pack(ft2):
        w = kw.World(tmp, mp)
        w.work("r2549a", team=kw.TEAM, alive=True)   # 닫을 수 있는 석 1개 — 정지로 봄이면 kill 0 이어야 한다
    bare(w)
    k = w.keeper()
    lines = w.round(k)
    bad = [x for x in lines if x.startswith("판정 불가") and "ALL_STOP" in x]
    assert len(bad) == 1 and "판정기 자리 없음" in bad[0] and "정지로 봄" in bad[0], lines
    assert k.halted(kw.TEAM) is True and k.halt_any is True, (k.halt, k.halt_any, lines)   # 정지로 봄
    assert w.tmux("kill-session") == [] and [x for x in lines if x.startswith(("CLOSED", "NEXT"))] == [], lines
    assert len([x for x in w.round(k) if "ALL_STOP 판정 불가" in x]) == 1, lines   # 같은 값 = 다음 바퀴 0줄


def c07(tmp, mp, ft2=FT2):
    """⑦ 작업 폴더에 «ft-all-stop.sh» 라는 파일이 있어도 env 가 비면 그 파일을 부르지 않는다(상대 경로 0 · 호출 0)."""
    tmp.mkdir(parents=True, exist_ok=True)
    seen, stub = tmp / "judge-calls.log", tmp / "ft-all-stop.sh"
    stub.write_text('#!/usr/bin/env bash\necho "$@" >> "%s"\necho \'{"state": "off"}\'\n' % seen, encoding="utf-8")
    stub.chmod(0o755)
    settle = _load(ft2 / KS, "r2549_settle_%d" % id(tmp))
    k = type("K", (), {"env": {}, "close_bin": "", "calls": [],
                       "judge_path": settle.Settling.judge_path, "judge_doc": settle.Settling.judge_doc})()
    k.call = lambda argv, timeout=None: (k.calls.append(argv), (127, "", "no such file"))[1]
    mp.chdir(tmp)
    assert k.judge_path() == "", k.judge_path()
    assert k.judge_doc() == (None, EMPTY), k.judge_doc()
    assert k.calls == [] and not seen.exists(), (k.calls, seen.exists())


CASES = {"①": c01, "②": c02, "③": c03, "④": c04, "⑤": c05, "⑥": c06, "⑦": c07}
IDS = ["c01", "c02", "c03", "c04", "c05", "c06", "c07"]
MUTANTS = {
    "M1": (KM, "    if close_bin_missing(k):", "    if False:   # M1 자리 검사 뺌", "①"),
    "M2": (KS, 'return self.env.get(JUDGE_ENV) or (os.path.join(os.path.dirname(self.close_bin), "ft-all-stop.sh") if self.close_bin else "")',
           'return self.env.get(JUDGE_ENV) or os.path.join(os.path.dirname(self.close_bin or ""), "ft-all-stop.sh")   # M2', "⑦"),
    "M3": (KS, "        if doc is None:\n            self.judge_note(why)\n            return True",
           "        if doc is None:\n            self.judge_note(why)\n            return False   # M3 자리가 비면 정지 아님", "⑥"),
    "M4": (KM, 'return not str(env.get("FT_SEAT_CLOSE_BIN") or "").strip() and not str(env.get(settle.JUDGE_ENV) or "").strip()',
           'return not str(env.get("FT_SEAT_CLOSE_BIN") or "").strip()   # M4 FT2_ALL_STOP_JUDGE 를 안 봄', "③"),
}


@pytest.mark.parametrize("name", list(CASES), ids=IDS)
def test_case(name, tmp_path, monkeypatch):
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
