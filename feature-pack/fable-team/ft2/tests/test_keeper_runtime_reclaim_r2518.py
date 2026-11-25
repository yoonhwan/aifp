"""r2518 ft2 runtime 총량 회수 — keeper 가 스스로 덜어낸다(반례 ①~⑧ · 변이 M1~M6).

2026-11-23 실사건: keeper 닫기 영수 4건이 매 바퀴 «용량 부족 · 예약 k=3 필요 2321880 > 한계 8388607» 로
거절됐는데, reclaim 을 부르는 곳이 core/cli.py 동사뿐이라 keeper 는 한 번도 덜어내지 않았다(reclaim 호출 0).
글만 보면 «필요 < 한계» 인데 거절 = 총량 6119239 가 글에 없었다. 그 4줄 = 시작 상태다.

반례 = 카드 동결본 ①~⑧ 그대로. ⑨(회수 도중 SIGKILL 2지점)는 기존 contracts/cap case_02 ·
tests/test_core_journal_cap.py ⓒ 가 그대로 덮는다(회귀 = 기준판 통과). 변이 M1~M6 = 자매 파일
test_keeper_runtime_reclaim_r2518_mut.py(사본 트리 · 원본 대조).

대역 = 임시 폴더만(실 runtime·실 tmux·실 명부 0 · sleep 0) · keeper 사례는 tests/keeper_world_r1812.World.
"""
import fcntl
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
FT2 = os.path.dirname(HERE)
CORE = os.path.join(FT2, "core")
sys.path.insert(0, HERE)
from keeper_world_r1812 import World   # noqa: E402 — keeper 대역(임시 리포·가짜 tmux·주입 시계)

TEAM, EV = "harness", ("v1", "v2")
OK, FULL, BUSY, RECLAIMED = "접수 성공", "용량 부족", "BUSY", "회수 결과"
CAPS = dict(total_cap=65536, reserve_bytes=4096, segment_cap=1024, state_slack=512, line_max=512)
BIG, SMALL = 65536, 512      # keeper 사례: 총 cap 을 실제 파일 크기 위/아래로 잡아 「절반」 문턱을 만든다


def _dispatch(ft2=FT2):
    """코어 Dispatch 1개 — 사본 트리(변이)도 같은 자리에서 읽는다(입구·예외 클래스 동일성)."""
    path = os.path.join(str(ft2), "core", "dispatch.py")
    spec = importlib.util.spec_from_file_location("r2518_dispatch_%d" % abs(hash(path)), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _node(root, ft2=FT2):
    """팀 runtime 1곳 — 시험 인자(작은 cap)를 journal 에 직접 건다."""
    node = _dispatch(ft2).Dispatch(str(root), TEAM)
    node.rs.capacity = 1000                           # pending 상한에 먼저 걸리지 않게(총량을 채운다)
    for key, value in CAPS.items():
        setattr(node.rs.journal, key, value)
    return node


def _rs(node):
    return node.rs


def _runtime(node):
    return node.rs.runtime


def _state(node):
    rs = node.rs
    return rs.journal.rec.recover_state(rs.journal.state(), rs.records())


def _usage(node):
    return node.rs.journal.usage()


def _files(node):
    rs, out = node.rs, {}
    for base, _dirs, names in os.walk(rs.runtime):
        for name in names:
            full = os.path.join(base, name)
            out[os.path.relpath(full, rs.runtime)] = os.path.getsize(full)
    return out


def _ops(node):
    path = os.path.join(_runtime(node), "ops.jsonl")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line)["op"] for line in handle if line.strip()]


def _closed_names(node):
    return [os.path.basename(path) for _num, path in node.rs.journal.closed()]


def _close(node, work):
    """닫힌 work(result 로 끝) — 접수 → 배정 → 실행권 → 결과 → 전달 → 완료."""
    holder = "h" + work.lower()
    assert node.rs.submit("c-" + work, "x" * 24, work=work).result == OK
    assert node.assign(work, holder, evidence=EV).result == OK
    assert node.ex.claim(work, holder).result == OK
    assert node.ex.result(work, holder, _gen(node, work), OK).result == OK
    assert node.deliver(work, "a1").result == OK
    assert node.complete(work, "a1").result == OK


def _gen(node, work):
    """지금 실행권 세대 — claim 이 올린 값(시험은 claim 뒤에 결과를 쓴다)."""
    return ((_state(node).get("owners") or {}).get(work) or {}).get("gen") or 1


def _closed_by_complete(node, work):
    """result 없이 complete 로 끝난 work(실측 «result 없는 complete 28» 꼴) — start 뒤 complete."""
    holder = "h" + work.lower()
    assert node.rs.submit("c-" + work, "x" * 24, work=work).result == OK
    assert node.assign(work, holder, evidence=EV).result == OK
    gen = node.ex.claim(work, holder).gen
    assert node.ex.start(work, holder, gen).result == OK
    assert node.deliver(work, "a1").result == OK
    assert node.complete(work, "a1").result == OK


def _accept_only(node, work):
    """접수만 한 work(배정 전) — 철회할 수 있는 유일한 꼴(withdraw 는 배정·전달 전 attempt 만)."""
    assert node.rs.submit("c-" + work, "x" * 24, work=work).result == OK


def _open(node, work):
    """열린 work(done 없음) — 접수 → 배정까지만."""
    assert node.rs.submit("c-" + work, "x" * 24, work=work).result == OK
    assert node.assign(work, "h" + work.lower(), evidence=EV).result == OK


def _append(node, work, kind):
    """journal 에 줄 1개를 직접 붙인다 — 완료 뒤 start·effect(실측 1건) 꼴은 제품 동사로 못 만든다."""
    rs = node.rs
    rec = rs.journal.rec.build(TEAM, (rs.records()[-1]["seq"] if rs.records() else 0) + 1, work, work,
                              "2026-11-23T00:00:00", work, work=work, kind=kind, holder=work, gen=1)
    rs.journal.append(rec)
    return rec


def _withdraw(node, work):
    """접수 철회(철회된 attempt 의 accept·withdraw 줄 = 닫힌 줄 · r1925b R1) — 철회가 회수를 막으면 안 된다."""
    rs = node.rs
    rows = [rec for rec in rs.records() if rec.get("kind") == "accept" and rec.get("work") == work]
    assert rows, work
    rec = rs.journal.rec.build(TEAM, rs.records()[-1]["seq"] + 1, rows[-1]["command"], rows[-1]["attempt"],
                              "2026-11-23T00:00:00", "손 놓음", work=work, kind="withdraw",
                              extra={"why": "손 놓음", "moved": rows[-1].get("body")})
    rs.journal.append(rec)
    return rec


def _settle(node, prefix="T"):
    """마지막 닫힌 조각 뒤에 활성 줄을 남긴다 — 닫힌 work 로만(막는 work 0)."""
    rs = node.rs
    for n in range(6):
        tops = [max(rec["seq"] for rec in rs.journal._records_of(path)) for _num, path in rs.journal.closed()]
        records = rs.records()
        if not tops or records[-1]["seq"] > max(tops):
            return
        _closed_by_complete(node, "%s%d" % (prefix, n))


def _fill_closed(node, maker, target, prefix):
    """maker 로 닫힌 조각을 target 개까지 채운다(조각 경계 = 회전)."""
    rs = node.rs
    while len(rs.journal.closed()) < target:
        maker(node, "%s%d" % (prefix, len(rs.journal.closed())))


def _seg_works(seg):
    return {rec.get("work") if isinstance(rec.get("work"), str) else None
            for rec in seg if rec["kind"] != "import"}


def _old_closed(work, records, state):
    """고치기 전 닫힘 판정(끝 줄 = result 뿐) — ⑧ 대조용 기준판(파일 손 0)."""
    rows = [rec for rec in records if rec.get("work") == work]
    done = (state.get("done") or {}).get(work)
    if done is None and work in (state.get("lifted") or {}):
        return True
    if done is None or work in (state.get("owners") or {}) or work in (state.get("uncertain") or {}):
        return False
    if (done or {}).get("marker") == "required" and work not in (state.get("reassess_done") or {}):
        return False
    last = max([rec["seq"] for rec in rows if rec["kind"] == "result"] or [0])
    sent = {(rec.get("work"), rec.get("attempt")) for rec in rows if rec["kind"] == "deliver"}
    return (not [rec for rec in rows if rec["kind"] in ("start", "effect") and rec["seq"] > last]
            and all((work, rec.get("attempt")) in sent for rec in rows if rec["kind"] == "dispatch"))


def _old_dropped(node):
    """고치기 전 규칙이 회수했을 조각 수 — ⑧ 의 «지금 = 얼마» 자리."""
    rs, records = node.rs, node.rs.records()
    state = rs.journal.rec.recover_state(rs.journal.state(), records)
    last, count = (records[-1]["seq"] if records else 0), 0
    for _num, path in rs.journal.closed():
        seg = rs.journal._records_of(path)
        if rs.journal._keep_last(max(rec["seq"] for rec in seg), last):
            break
        works = _seg_works(seg)
        if None in works or not all(_old_closed(work, records, state) for work in works):
            break
        count += 1
    return count


def _small(base_cls, cap):
    """총 cap 만 갈아 끼운 Journal — keeper runtime 이 몇 KB 뿐이라 문턱을 실제 크기로 만든다."""

    class Small(base_cls):
        def __init__(self, runtime, **kwargs):
            kwargs["total_cap"] = cap
            super().__init__(runtime, **kwargs)

    return Small


def _keeper(w, cap=SMALL):
    """keeper 모듈 1개(한 번만 읽는다 — World.K 는 부를 때마다 새 모듈) + 작은 cap Journal."""
    K = w.K
    K.kr.journal.Journal = _small(K.kr.journal.Journal, cap)
    return K, K.Keeper(str(w.root), env=w.env, now=lambda: w.t)


def _block_tool(w, base):
    """막힘 장부 도구 대역 — 부른 인자를 한 줄씩 적는다(kblock.Ledger 가 FT_BLOCK_BIN 을 본다)."""
    log, tool = base / "block.log", base / "block.sh"
    tool.write_text('#!/bin/sh\necho "$@" >> "%s"\n' % log, encoding="utf-8")
    tool.chmod(0o755)
    w.env.update(FT_BLOCK_BIN=str(tool))
    w.env.pop("FT_CRITICAL_OFF", None)
    return log


def _raised(log):
    return [line for line in log.read_text(encoding="utf-8").splitlines() if line.strip()] if log.exists() else []


# ── ① result 없이 complete 로 끝난 work 만 든 닫힌 조각 3개 → 모두 회수 ────────
def c1(base, mp, ft2=FT2):
    node = _node(base, ft2)
    _fill_closed(node, _closed_by_complete, 3, "S")
    _settle(node)
    assert _old_dropped(node) == 0, "기준판이 이미 덜어냈다 = 이 사례가 아니다"
    closed = _closed_names(node)
    assert len(closed) >= 3, closed
    out = _rs(node).journal.reclaim()
    assert out["result"] == RECLAIMED, out
    assert out["reclaimed"] == closed, (out["reclaimed"], closed)


# ── ② complete 뒤 start 가 다시 온 work → 그 조각 보존 ────────────────────────
def c2(base, mp, ft2=FT2):
    node = _node(base, ft2)
    _close(node, "A1")
    _fill_closed(node, _close, 2, "B")
    _append(node, "A1", "start")                 # 완료 뒤 다시 시작(실측 «complete 뒤 start·effect 1»)
    _settle(node, "T2")
    state, records = _state(node), _rs(node).records()
    assert _rs(node).journal._closed_why("A1", records, state) == "끝 뒤 start·effect"
    held = [path for _num, path in _rs(node).journal.closed()
            if any(rec.get("work") == "A1" for rec in _rs(node).journal._records_of(path))]
    assert held, "A1 이 든 조각이 없다"
    out = _rs(node).journal.reclaim()
    assert os.path.basename(held[0]) not in out["reclaimed"], (held, out["reclaimed"])
    assert out["blocked"].get("A1") == "끝 뒤 start·effect", out["blocked"]


# ── ③ done 없는 work 가 첫 조각에 있음 → 회수 0 · 막는 work 이름·사유 ──────────
def c3(base, mp, ft2=FT2):
    node = _node(base, ft2)
    _open(node, "P0")
    _accept_only(node, "X0")
    _withdraw(node, "X0")                        # 철회된 accept = 닫힌 줄 → 막힘 이름에 들어가면 안 된다
    _fill_closed(node, _close, 2, "C")           # P0 이 든 첫 조각을 회전시켜 닫힌 조각으로 만든다
    _settle(node, "T3")
    assert _closed_names(node), "닫힌 조각이 없다(막는 자리 자체가 없다)"
    assert any(row.get("command") == "c-X0" for row in (_state(node).get("withdrawn") or {}).values())
    out = _rs(node).journal.reclaim()
    assert out["result"] == RECLAIMED, out
    assert out["reclaimed"] == [], out["reclaimed"]
    assert out["blocked"].get("P0") == "done 없음", out["blocked"]
    assert "X0" not in out["blocked"], out["blocked"]      # 정정2 — 철회 accept 제외


# ── ④ keeper 바퀴: 절반 미만 = 0회 · 절반 이상 = 1회 · 잠금 점유 = BUSY 1줄 ────
def c4(base, mp, ft2=FT2):
    w = World(base / "w", mp, ft2=Path(ft2))
    w.work("W1", done=True)
    w.enable()
    K = w.K
    base_cls = K.kr.journal.Journal
    calls = []

    class Count(_small(base_cls, SMALL)):
        def reclaim(self, state=None):
            calls.append(self.runtime)
            return super().reclaim(state)

    big = _small(base_cls, BIG)                  # 총량 < 절반(64KB 반쪽) = 회수 호출 0
    K.kr.journal.Journal = big
    k = K.Keeper(str(w.root), env=w.env, now=lambda: w.t)
    assert k.run_once() == 0
    assert calls == [], ("총량 < 절반인데 회수를 불렀다", k.lines)
    K.kr.journal.Journal = Count                 # 총량 ≥ 절반(512B 반쪽) = 1회
    k = K.Keeper(str(w.root), env=w.env, now=lambda: w.t)
    assert k.run_once() == 0
    assert len(calls) == 1, (calls, k.lines)
    lock = open(os.path.join(w.runtime(), "writer.lock"), "a+", encoding="utf-8")
    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)   # 잠금 점유 = BUSY 1줄 · 예외 0
    try:
        k = K.Keeper(str(w.root), env=w.env, now=lambda: w.t)
        assert k.run_once() == 0
        busy = [line for line in k.lines if line.startswith("RUNTIME-RECLAIM") and BUSY in line]
        assert len(busy) == 1, k.lines
    finally:
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        lock.close()


# ── ⑤ 회수 성공 = ops.jsonl 0바이트 일반 파일 · 실패 = 그대로 · launch 보존 ────
def c5(base, mp, ft2=FT2):
    node = _node(base / "ok", ft2)
    _close(node, "K1")
    _settle(node, "T5")
    launch = os.path.join(_runtime(node), "launch")
    os.makedirs(launch, exist_ok=True)
    for name in ("a.intent", "b.intent", "c.owner"):
        with open(os.path.join(launch, name), "w", encoding="utf-8") as handle:
            handle.write("x" * 32)
    if not _ops(node):
        _rs(node).journal.ops("probe")
    out = _rs(node).journal.reclaim()
    assert out["result"] == RECLAIMED, out
    assert out["reclaimed"], out["reclaimed"]
    path = os.path.join(_runtime(node), "ops.jsonl")
    assert os.path.isfile(path) and not os.path.islink(path), "ops.jsonl 이 일반 파일이 아니다"
    assert os.path.getsize(path) == 0, "회수 성공인데 흔적이 남았다"
    assert sorted(os.listdir(launch)) == ["a.intent", "b.intent", "c.owner"], "launch 가 지워졌다"
    bad = _node(base / "refuse", ft2)
    _close(bad, "K2")
    _settle(bad, "T5b")
    assert _ops(bad), "실패 대조에 흔적이 없다"
    before = _files(bad)
    bad.rs.journal.total_cap = 1                      # checkpoint 가 내부 한계를 넘는다 = 회수 실패
    refused = bad.rs.journal.reclaim()
    assert refused["result"] == FULL, refused
    found = re.search(r"총량 (\d+) \+ 필요 (\d+) > 한계 (\d+)", refused.get("reason") or "")   # 정정3
    assert found, refused
    total, needed, limit = (int(value) for value in found.groups())
    assert total + needed > limit, (total, needed, limit)
    assert _files(bad) == before, "회수 실패인데 흔적·파일이 바뀌었다"


# ── ⑥ 총량 ≥ 3/4 + 막힘 → 막힘 장부 1건 · 같은 집합 둘째 바퀴 = 0건 ────────────
def c6(base, mp, ft2=FT2):
    w = World(base / "w", mp, ft2=Path(ft2))
    tool = base / "block.sh"
    log = _block_tool(w, base)
    node = _node(w.root, ft2)
    _open(node, "P1")
    _fill_closed(node, _close, 2, "M")
    _settle(node, "T6")
    K, k = _keeper(w, _usage(node))                   # 총량 = cap = 3/4 문턱 위
    fail = base / "fail.sh"                           # 장부 도구 실패(rc 3) = 등록 0 → 기억 0(정정4)
    fail.write_text("#!/bin/sh\nexit 3\n", encoding="utf-8")
    fail.chmod(0o755)
    w.env["FT_BLOCK_BIN"] = str(fail)
    k.env["FT_BLOCK_BIN"] = str(fail)               # Keeper 는 env 를 복사해 둔다 — 그 사본을 바꿔야 한다
    k.reclaim.sweep([TEAM])
    assert _raised(log) == [], ("등록이 실패했는데 올렸다", _raised(log))
    memory = Path(w.root) / ".fable-team" / "state" / "ft2-keeper" / "reclaim-blocked.json"
    assert not memory.exists(), "등록 실패인데 기억 파일을 남겼다(다음 바퀴 재시도 차단)"
    k.env["FT_BLOCK_BIN"] = str(tool)                  # 도구 살아남 = 같은 바퀴에 바로 재등록
    k.reclaim.sweep([TEAM])
    first = _raised(log)
    assert len(first) == 1, (first, k.lines)
    assert "ft2-runtime-reclaim" in first[0] and "P1" in first[0], first
    assert memory.exists(), "등록 성공인데 기억을 안 남겼다"
    k.reclaim.sweep([TEAM])
    assert len(_raised(log)) == 1, ("같은 집합인데 다시 올렸다", _raised(log))


# ── ⑦ reserve(3) 거절 글에 총량·필요·한계 세 수 · 총량 + 필요 > 한계 ──────────
def c7(base, mp, ft2=FT2):
    node = _node(base, ft2)
    while _rs(node).submit("p-%d" % len(_rs(node).records()), "x" * 4000).result == OK:
        if len(_rs(node).records()) > 200:
            break
    with pytest.raises(_rs(node).journal.rec.WriterRefused) as caught:
        _rs(node).journal.reserve(3)
    text = str(caught.value)
    found = re.search(r"총량 (\d+) \+ 예약 k=3 필요 (\d+) > 한계 (\d+)", text)
    assert found, text
    total, needed, limit = (int(value) for value in found.groups())
    assert total + needed > limit, (total, needed, limit)


# ── ⑧ 실사건 재생: 앞 조각은 지금 규칙으로 닫힘 · 다섯째에 result 없는 complete ──
def c8(base, mp, ft2=FT2):
    node = _node(base, ft2)
    _fill_closed(node, _close, 4, "N")
    old = _old_dropped(node)
    assert old >= 4, old
    _fill_closed(node, _closed_by_complete, len(_closed_names(node)) + 2, "S")
    _settle(node, "T8")
    assert _old_dropped(node) == old, "기준판 몫이 흔들렸다"
    out = _rs(node).journal.reclaim()
    assert out["result"] == RECLAIMED, out
    assert len(out["reclaimed"]) > 4, out["reclaimed"]
    assert len(out["reclaimed"]) > old, (out["reclaimed"], old)


# ── ⑨(정정1) 회수 성공 로그 = 회수 «뒤» 총량 · 앞뒤 값과 한계가 한 줄에 ──────
def c9(base, mp, ft2=FT2):
    w = World(base / "w", mp, ft2=Path(ft2))
    w.work("W9", done=True)
    w.enable()
    node = _node(w.root, ft2)
    _fill_closed(node, _close, 2, "L")
    _settle(node, "T9")
    before = _usage(node)
    K, k = _keeper(w, before + 2000)                   # checkpoint 몫까지 남기는 cap(절반 문턱 위)
    k.reclaim.sweep([TEAM])
    lines = [line for line in k.lines if line.startswith("RUNTIME-RECLAIM")]
    assert len(lines) == 1, k.lines
    found = re.search(r"총량 (\d+) → (\d+) · 한계 (\d+)", lines[0])
    assert found, lines[0]
    was, left, cap = (int(value) for value in found.groups())
    after = _usage(node)
    assert (was, cap) == (before, before + 2000), (was, cap, before)
    assert left == after and left < was, (left, after, was)   # 남은 총량 = 회수 뒤 실측


CASES = {"1": c1, "2": c2, "3": c3, "4": c4, "5": c5, "6": c6, "7": c7, "8": c8, "9": c9}


@pytest.mark.parametrize("name", list(CASES))
def test_case(name, tmp_path, monkeypatch):
    (tmp_path / "base").mkdir()
    CASES[name](tmp_path / "base", monkeypatch)
