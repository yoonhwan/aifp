"""r2526 반례 ③ ④ ⑥ ⑦ + 변이 M2 M4 M5 — 시험 부모(pytest)가 SIGTERM 으로 끊겨도 시험이 띄운 그룹만 거둔다.

왜: r2499 인수 대조에서 r2072 를 70초에 끊었더니 «block raise» 자식이 부모 없이 1시간 넘게 남았다(r2521 실사건).
     Python 의 SIGTERM 기본 종료는 finally · pytest fixture teardown 을 돌리지 않는다(사전 DA#59 H1).
     그래서 r2072 대역(keeper_block_raise_r2072.py)이 시험이 도는 동안 handler 를 걸고, 신호에서 «이 시험이 띄운 그룹만» 거둔다.

③ 자식 pytest 를 띄워 스텁이 살아 있는 동안 SIGTERM → 3초 안에 pids 그룹 자식 0 · 부모는 신호로 끝남(rc 그대로) · 남의 그룹은 산다
④ 정상 끝 → 남는 자식 0
⑥ ps 실패 → 신호 0 · «판정 불가» rc≠0      ⑦ pids 기록 깨짐 → 신호 0 · «판정 불가» rc≠0
변이 M2 handler 등록 뺌 · M4 argv 확인 없이 그룹 거둠 · M5 기본 동작으로 안 되돌림 → ③ 이 Red
"""
import os
import shutil
import signal
import subprocess
import sys
import time
import types
from pathlib import Path

import pytest

import keeper_block_raise_r2072 as h
import keeper_mutant_apply_r2526 as ap

HERE = Path(__file__).resolve().parent
CHILD = "test_keeper_sigterm_child_r2526.py"
SIGTERM = signal.SIGTERM


def spawn(tmp, tests_dir=HERE, target=CHILD, mode="CHILD", ps_broken=False):
    """자식 pytest 1개 — 출력은 파일로(파이프 막힘 0) · 새 세션(부모 그룹과 섞이지 않는다).

    ps_broken = 자식의 PATH 맨 앞에 «늘 실패하는 ps» 를 둔다(⑥ — 외부 명령 실패). 대역이 keeper 에 주는 PATH 는 따로라 영향 0.
    """
    out = (tmp / "child.out").open("w")
    env = dict(os.environ, R2526_CHILD="1", R2526_READY=str(tmp / "ready"), R2526_PIDS_OUT=str(tmp / "pids.out"))
    env["R2526_" + mode] = "1"
    env.pop("FT_BLOCK_BIN", None)
    if ps_broken:
        bad = tmp / "psbin-fail"
        bad.mkdir(parents=True, exist_ok=True)
        (bad / "ps").write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        (bad / "ps").chmod(0o755)
        env["PATH"] = str(bad) + ":" + env.get("PATH", "")
    argv = [sys.executable, "-m", "pytest", "-q", "-s", "-p", "no:cacheprovider", "--basetemp=" + str(tmp / "childbase"), target]
    p = subprocess.Popen(argv, cwd=str(tests_dir), env=env, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
    p._r2526_out = out   # noqa: SLF001 — 거두기에서 닫는다
    return p


def tail(p):
    try:
        p._r2526_out.flush()   # noqa: SLF001
        return Path(p._r2526_out.name).read_text(encoding="utf-8", errors="replace")[-400:]   # noqa: SLF001
    except OSError:
        return ""


def only(base, name):
    hits = sorted(Path(base).rglob(name))
    assert len(hits) == 1, (name, hits)
    return hits[0]


def stop(p, limit=6):
    """자식이 스스로 끝나기를 기다린다 — 안 끝나면 kill 하고 «timeout» 을 돌려준다(단언이 Red 가 되게)."""
    try:
        return p.wait(timeout=limit)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait(timeout=5)
        return "timeout"


def gone(pairs, limit):
    end = time.monotonic() + limit
    while time.monotonic() < end:
        live = {r[0] for r in h._procs()}
        if not any(pid in live for pid, _ in pairs):
            return True
        time.sleep(0.05)
    return False


def ready(p, tmp, limit=25):
    end = time.monotonic() + limit
    while time.monotonic() < end:
        if (tmp / "ready").exists():
            return True
        if p.poll() is not None:
            return False
        time.sleep(0.02)
    return False


def scenario(tmp, tests_dir=HERE):
    """③ — 스텁이 살아 있는 동안 부모에 SIGTERM. Red 면 AssertionError."""
    tmp.mkdir(parents=True, exist_ok=True)
    p = spawn(tmp, tests_dir)
    other = subprocess.Popen(["sleep", "300"], start_new_session=True)   # 시험 밖 남의 그룹
    pairs = []
    try:
        assert ready(p, tmp), "자식이 ready 를 안 냈다: %s" % tail(p)
        rec = only(tmp / "childbase", "block.pids")
        pairs = h.read_pairs(rec)[0]
        assert pairs, "스텁이 «pid pgid» 를 안 적었다"
        with rec.open("a", encoding="utf-8") as fh:   # 기록에 섞인 남의 그룹 — argv 가 달라 신호 0 이어야 한다
            fh.write("%d %d\n" % (other.pid, os.getpgid(other.pid)))
        p.send_signal(SIGTERM)
        rc = stop(p)
        assert rc == -SIGTERM, "부모가 신호로 안 끝났다(rc=%r): %s" % (rc, tail(p))
        assert gone(pairs, 3), "pids 그룹 자식이 3초 안에 안 죽었다"
        assert other.poll() is None, "남의 그룹(시험 밖 sleep 대역)이 죽었다"
    finally:
        for proc in (p, other):
            if proc.poll() is None:
                proc.kill()
        while pairs:   # 남은 스텁 정리(판정 실패 판에서도)
            pid, _pgid = pairs.pop()
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        p._r2526_out.close()   # noqa: SLF001


class _Sig:
    """os.kill · os.killpg 를 «호출 기록» 으로 바꾼 대역 — 실제 프로세스 종료 0(DA#57 격리와 같은 수법)."""

    def __init__(self, calls):
        self.calls, self.getuid, self.getpgrp = calls, os.getuid, os.getpgrp

    def kill(self, pid, sig):
        self.calls.append((pid, int(sig)))

    def killpg(self, pgid, sig):
        self.calls.append((pgid, int(sig)))


def test_opaque_argv_is_not_owned(tmp_path, monkeypatch):
    """DA#57 HOLD1 — ps 가 argv 를 못 읽은 모양(«(Python)»)에 pid·pgid·uid 가 다 맞아도 소유 추정 0 = 신호 0 · 판정 불가.

    정정 전에는 이 칸이 신호를 냈다(DA 독립 대역: result [1, null] · signal_calls [[987654, 9]]).
    """
    calls = []
    monkeypatch.setattr(h, "os", _Sig(calls))
    w = types.SimpleNamespace(tmp=tmp_path, block=tmp_path / "bin" / "block")
    got = h.kill_pairs(w, [(987654, 9)], table=[(987654, 1, 9, os.getuid(), "(Python)")])
    assert calls == [], "argv 판독 불가인데 신호를 냈다: %r" % (calls,)
    assert got[0] == 0 and got[1] and "판정 불가" in got[1], got


def test_sigterm_reaps_owned_group_and_spares_others(tmp_path):
    """③ — 부모 pytest 에 SIGTERM → 3초 안에 pids 그룹 자식 0 · 부모는 신호로 끝남 · 남의 그룹은 그대로 산다."""
    scenario(tmp_path)


def test_normal_end_leaves_no_child(tmp_path):
    """④ — r2072 정상 끝 → 남는 자식 0(기록에 적힌 스텁 pid 가 전부 사라진다)."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    p = spawn(tmp_path, target=CHILD + "::test_normal_stub_reaped_locally", mode="NORMAL")
    try:
        assert stop(p, 70) == 0, tail(p)
        pairs = h.read_pairs(tmp_path / "pids.out")[0] or []
        assert pairs and gone(pairs, 3), ("정상 끝인데 자식이 남았다", pairs)
    finally:
        if p.poll() is None:
            p.kill()
        p._r2526_out.close()   # noqa: SLF001


@pytest.mark.parametrize("why", ["corrupt", "ps-fail"])
def test_undecidable_sends_no_signal(why, tmp_path):
    """⑦ ⑥ — pids 기록이 깨졌거나 ps 판독이 실패하면 신호 0 · «판정 불가» 1줄 · rc≠0(자식은 안 거둔다)."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    p = spawn(tmp_path, ps_broken=why == "ps-fail")
    pairs = []
    try:
        assert ready(p, tmp_path), "자식이 ready 를 안 냈다: %s" % tail(p)
        rec = only(tmp_path / "childbase", "block.pids")
        pairs = h.read_pairs(rec)[0]
        if why == "corrupt":
            with rec.open("a", encoding="utf-8") as fh:
                fh.write("깨진 줄\n")
        assert pairs, "스텁이 «pid pgid» 를 안 적었다"
        p.send_signal(SIGTERM)
        rc = stop(p)
        assert rc == h.UNDECIDABLE, "판정 불가 rc 가 아니다(rc=%r): %s" % (rc, tail(p))
        assert "판정 불가" in tail(p), "«판정 불가» 1줄이 없다: %s" % tail(p)
        assert not gone(pairs, 0.2), "판정 불가인데 신호를 보냈다(자식이 죽었다)"
    finally:
        if p.poll() is None:
            p.kill()
        for pid, _pgid in pairs:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        p._r2526_out.close()   # noqa: SLF001


def mutate(tmp, name):
    """이 팩 사본(tests 포함) 1개에서 r2526 handler 를 그 변이로 바꾼다 — 사본에서만 · 넣기는 keeper_mutant_apply_r2526.swap 한 길."""
    tree = tmp / "m" / "ft2"
    shutil.copytree(h.FT2, tree, ignore=shutil.ignore_patterns("__pycache__"))
    old, new = MUTATIONS[name]
    ap.swap(tree / "tests" / "keeper_block_raise_r2072.py", old, new, name)
    return tree / "tests"


MUTATIONS = {
    # M2 handler 등록 뺌 → SIGTERM 이 기본 종료 = 스텁이 남는다
    "M2": ("    if _OLD:\n        return\n    for sig in HANDLED:", "    return\n    for sig in HANDLED:"),
    # M4 argv 확인 없이 그룹을 거둠 → 기록에 섞인 남의 그룹까지 죽는다
    "M4": ("        if not owned_row(row[0][4], tmp):   # r2526 ③ — 기록에 섞인 남의 그룹 = 신호 0\n            continue\n", ""),
    # M5 기본 동작으로 안 되돌림 → 같은 신호가 handler 로 다시 들어와 부모가 신호로 안 끝난다
    "M5": ("    uninstall()\n    os.kill(os.getpid(), signum)", "    os.kill(os.getpid(), signum)"),
}


@pytest.mark.parametrize("name", list(MUTATIONS))
def test_mutant(name, tmp_path):
    """M2 M4 M5 — 사본에서 ③ 이 Red · 원본으로 같은 판 1회 더 = PASS(⑤ 변이 그물이 살아 있음)."""
    with pytest.raises(AssertionError):
        scenario(tmp_path / "mut", mutate(tmp_path, name))
    scenario(tmp_path / "ok")
