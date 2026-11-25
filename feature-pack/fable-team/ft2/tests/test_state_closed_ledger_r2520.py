"""ft2 끝난 work 칸 → 닫힌 장부 (카드 r2520 · 사전 DA APPROVE-DESIGN #375618 · 판정문 DA-pre-r2520-codex59-r2).

끝: 끝난 work 가 쌓여도 활성 state.json 크기가 «열린 work 수» 에만 비례한다. 끝난 기록은 지워지지 않고
runtime/closed.<N>.jsonl 에서 조회된다(같은 명령 재접수 · 닫기 영수 대조 · 철회 · 가져온 기록 = 지금과 같은 답).
총량·예약 식은 그대로다(state 가 작아져서 풀린다) · runtime 전체 누적 상한은 이 카드 범위 밖(알려진 한계).

반례 ①~⑩ ① 회수하면 state 가 작아진다 ② 200·2000 끝난 work 에서 state 크기·예약 state 몫이 같다
③ 같은 command 재접수 = 같은 답 · 그 뒤 새 쓰기로 다시 커지지 않는다 ④ 닫기 영수 재조회 = 같은 답
⑤ SIGKILL 3지점(장부 덧붙인 뒤 · checkpoint 뒤 · 조각 삭제 뒤) → 같은 답 · 줄 중복은 1개로 판독
⑥ 열린 work(owners·deliveries)의 칸은 state 에 남는다 ⑦ 첫 설치 꼴(base 에 접힌 닫힌 work)은 여러 바퀴에
나눠 옮기고 매 바퀴 총량 ≤ 한계 ⑧ 깨진 장부 줄 = «복구 필요» · 쓰기 0 ⑨ 회수된 철회 attempt 의 command
재접수 = 새 attempt ⑩ 회수된 import key 재가져오기 = 멱등.

시험 인자 = 후보값(총량 65536 · reserve 4096 · segment 1024 · slack 512 · line 512). 변이 M1~M9 = 제품 자리
1곳(사본 트리) · 크래시 = 자식 프로세스 os._exit(9)(정지점) · 격리 tmp 루트만 · 실 runtime·설치·tmux·press 0 · sleep 0.
"""
import collections
import functools
import importlib.util
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FT2 = os.path.dirname(HERE)
CORE = os.path.join(FT2, "core")
TEAM, EV = "harness", ("v1", "v2")
OK, HOLD, FULL, CORRUPT, RECLAIMED = "접수 성공", "완료 유보", "용량 부족", "복구 필요", "회수 결과"
NANO, NEXT = "biz-harness-nano-r2520#0", "biz-harness-master-r2520#0"
CAPS = dict(total_cap=65536, reserve=4096, segment_cap=1024, state_slack=512, line_max=512)
CHILD_ENV = dict(os.environ, FT2_CLOSED_LEDGER_CHILD="1")


def _load(name):
    spec = importlib.util.spec_from_file_location("ft2_core_" + name, os.path.join(CORE, name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


intake, dispatch, close_next, withdraw, legacy_import = (
    _load(name) for name in ("intake", "dispatch", "close_next", "withdraw", "legacy_import"))
record, journal = intake.record, intake.journal       # 입구가 쓰는 그 모듈(예외 클래스 동일성)


def _use(ft2=None):
    """그 트리(원본 또는 사본·변이트리)의 모듈로 갈아 끼운다 — 사례는 이 함수를 먼저 부른다."""
    global intake, dispatch, close_next, withdraw, legacy_import, record, journal
    here = os.path.join(str(ft2) if ft2 is not None else FT2, "core")

    def load(name):
        spec = importlib.util.spec_from_file_location("ft2_case_%s_%s" % (
            name, abs(hash(str(ft2)) + hash(os.path.basename(name)))), os.path.join(here, name + ".py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    intake = load("intake")
    record, journal = intake.record, intake.journal
    dispatch, close_next = load("dispatch"), load("close_next")
    withdraw, legacy_import = load("withdraw"), load("legacy_import")


def _rs(node):
    return node if isinstance(node, intake.Intake) else node.rs


def _d(root, on_step=None, **caps):
    """팀 하나(임시 runtime) — 시험 인자를 journal 에 직접 건다(Execution·Dispatch 는 Intake 기본값)."""
    node = dispatch.Dispatch(str(root), TEAM, on_step=on_step)
    rs = _rs(node)
    for key, value in {**CAPS, **caps}.items():
        setattr(rs.journal, {"reserve": "reserve_bytes"}.get(key, key), value)
    rs.capacity = 1000
    return node


def _accept(node, *works):
    for work in works:
        assert node.rs.submit("c-" + work, "x" * 8, work).result == OK
    return node


def _close(node, work, holder=None):
    """닫힌 work — 접수 → 배정 → 결과 → 전달 → 완료(+계약 재평가). 회수 조건 5가드를 만족하는 최소 흐름."""
    holder = holder or work.lower()
    assert _accept(node, work).assign(work, holder, evidence=EV).result == OK
    assert node.ex.result(work, holder, 1, OK).result == OK
    assert node.deliver(work, "a1").result == OK
    assert node.complete(work, "a1").result == OK


def _close_node(root):
    """닫기 영수 도구 — 켜기 표식만 세운다(dry-run 판정은 r1725 시험 몫 · 여기 = 영수 조회 경로)."""
    marker = os.path.join(str(root), ".fable-team", "teams", TEAM, "CLOSE-NEXT.enabled")
    os.makedirs(os.path.dirname(marker), exist_ok=True)
    with open(marker, "w", encoding="utf-8") as handle:
        handle.write("enabled r2520\n")
    return close_next.CloseNext(str(root), TEAM, probe=lambda seat: "absent")


def _state(node):
    rs = _rs(node)
    return rs.journal.rec.recover_state(rs.journal.state(), rs.records())


def _size(node):
    return os.path.getsize(_rs(node).journal.state_path)


def _rows(node):
    """닫힌 장부 줄 전부 — [(N, 줄)] 파일 순서 그대로(중복 줄도 그대로 보인다)."""
    out = []
    for index, path in _rs(node).journal.ledger.files():
        with open(path, encoding="utf-8") as handle:
            out += [(index, json.loads(line)) for line in handle if line.strip()]
    return out


def _drain(node, rounds=12):
    """회수 바퀴 — 더 못 덜 때까지(마지막 조각·열린 work 는 남는다)."""
    outs = []
    for _ in range(rounds):
        out = node.rs.journal.reclaim()
        outs.append(out)
        if not out.get("reclaimed") and not out.get("moved"):
            break
    return outs


def _scenario(root, works=("W1", "W2", "W3", "W4"), **caps):
    node = _d(root, **caps)
    for work in works:
        _close(node, work)
    return node


def case1_state_shrinks(root, ft2=None, **_):
    """① — 끝난 work 4개 회수 → state.json 이 회수 전보다 작다 · 옮긴 work 칸이 state 에서 빠진다."""
    _use(ft2)
    node = _scenario(root)
    before = _size(node)
    outs = _drain(node)
    assert any(out["reclaimed"] for out in outs), outs
    assert _size(node) < before, (_size(node), before)
    moved = {row["key"] for _idx, row in _rows(node) if row["k"] == "work"}
    assert moved, _rows(node)
    state = _state(node)
    assert not (set(state.get("done") or {}) & moved), sorted(set(state["done"]) & moved)
    assert not (set(state.get("deliveries") or {}) & moved), sorted(set(state["deliveries"]) & moved)
    assert len(moved) == len([1 for _idx, row in _rows(node) if row["k"] == "work"]), "장부 work 줄 = 옮긴 수"


def _synthetic(count):
    """끝난 work count 개 + 그 command 줄(accept) — state·journal 을 실제 꼴로 만든다(쓰기 0)."""
    state = {"schema": record.SCHEMA_VERSION, "revision": 0, "pending": [], "attempts": {}}
    state.update({name: {} for name in record.EXTENDED_STATE_FIELDS})
    records = []
    for n in range(1, count + 1):
        work, command = "S%05d" % n, "c-S%05d" % n
        state["done"][work] = {"attempt": "a1", "at": "2026-11-23T00:00:00", "marker": ""}
        state["generations"][work] = 1
        state["deliveries"][work] = ["a1"]
        state["pending"].append(command)
        state["attempts"][command] = 1
        state["journal_base"].setdefault("receipts", {})[command] = "a1"
        records.append(record.build(TEAM, n, command, "a1", "2026-11-23T00:00:00", "bodies/x.body", work))
    state["journal_base"].update({"upto": 0, "count": 0,
                                 "proj": {name: dict(state[name]) for name in journal.PROJ_FIELDS}})
    return state, records


def case2_size_flat_in_finished_count(root, ft2=None, **_):
    """② — 200개와 2000개에서 뺀 state 크기·예약(3) state 몫이 같다(pending · attempts · base.receipts 포함)."""
    _use(ft2)
    runtime = os.path.join(str(root), "runtime")
    os.makedirs(runtime, exist_ok=True)
    node = journal.Journal(runtime, rec=record, **CAPS)
    sizes = []
    for count in (200, 2000):
        state, records = _synthetic(count)
        rows, out, ledger_bytes = node._closed_rows(state, records, 10 ** 6, 10 ** 9)
        assert sorted(rows[0]) == ["k", "key", "row"], rows[0]
        assert not out["done"] and not out["pending"] and not out["attempts"], sorted(out["done"])[:3]
        assert not (out["journal_base"]["receipts"]), sorted(out["journal_base"]["receipts"])[:3]
        assert len(rows) == count * 2, (count, len(rows))          # work 줄 + command 줄
        sizes.append((node.envelope_for(out), ledger_bytes))
    assert sizes[0][0] == sizes[1][0], sizes                       # state 크기가 끝난 수에 비례하지 않는다
    needed = [3 * (node.line_max + size + 3 * (node.line_max + node.state_slack)) for size, _b in sizes]
    assert needed[0] == needed[1] and sizes[0][0] < 4096, (needed, sizes)   # 예약(3) 의 state 몫도 같다 · 고정분


def case3_resubmit_same_command(root, ft2=None, **_):
    """③ — 회수된 work 와 같은 command 재접수 = 지금과 같은 답 · 그 뒤 새 work 1개분만큼만 큰다."""
    _use(ft2)
    node = _scenario(root)
    assert node.rs.lookup("c-W1").attempt == "c-W1#a1"
    _drain(node)
    moved = {row["key"] for _idx, row in _rows(node) if row["k"] == "work"}
    assert "W1" in moved, sorted(moved)
    again = node.rs.submit("c-W1", "x" * 8)
    assert (again.result, again.attempt) == (HOLD, "c-W1#a1"), again
    before = _size(node)
    assert node.rs.submit("fresh-3", "x" * 8, "F3").result == OK
    grew = _size(node) - before
    assert 0 < grew < 1200, grew                                   # 새 work 1개분(끝난 칸 재팽창 0)
    assert "W1" not in (_state(node).get("done") or {})


def case4_close_receipt_lookup(root, ft2=None, **_):
    """④ — 회수된 닫기 영수를 같은 event 로 다시 조회 = 같은 답(재접수 · 쓰기 0) · 새 쓰기로 다시 커지지 않는다."""
    _use(ft2)
    node = _scenario(root)
    first = _close_node(root).receipt(NANO, 1, "W1", "e1", NEXT, EV)
    assert (first.result, first.next, first.written) == (OK, "[다음 없음]", True), first
    _close(node, "W5")                                              # 영수 줄이 든 조각까지 덜어낸다
    _close(node, "W6")
    _drain(node)
    assert [row for _idx, row in _rows(node) if row["k"] == "event"], "영수 줄이 장부로 안 갔다"
    lines, before = len(node.rs.records()), _size(node)
    again = _close_node(root).receipt(NANO, 1, "W1", "e1", NEXT, EV)
    assert (again.result, again.written, "재접수" in again.reason) == (HOLD, False, True), again
    assert len(node.rs.records()) == lines, "재조회 = journal 쓰기 0"
    assert _size(node) == before, "재조회 결과를 state 로 다시 쓰지 않는다"   # M7 자리
    before = _size(node)
    assert node.rs.submit("fresh-4", "x" * 8, "F4").result == OK
    assert _size(node) - before < 1200, _size(node) - before


def case5_crash_points(root, step="reclaim_after_ledger", ft2=None, **_):
    """⑤ — SIGKILL 3지점 → 재기동 회수 뒤 ③④ 같은 답 · 줄 중복은 1개로 판독."""
    _use(ft2)
    node = _scenario(root)
    priors = {command: node.rs.lookup(command).attempt for command in ("c-W1", "c-W2")}
    assert _close_node(root).receipt(NANO, 1, "W1", "e1", NEXT, EV).result == OK
    assert _crash(root, step, ft2).returncode == 9, step
    fresh = _d(root)
    _drain(fresh)
    assert fresh.rs.journal.ledger.work("W1") is not None, step
    for command, attempt in priors.items():
        look = fresh.rs.lookup(command)
        assert look is not None and look.attempt == attempt, (step, command, look)
        assert fresh.rs.submit(command, "x" * 8).result == HOLD, (step, command)
    again = _close_node(root).receipt(NANO, 1, "W1", "e1", NEXT, EV)
    assert (again.result, again.written, "재접수" in again.reason) == (HOLD, False, True), (step, again)
    counts = collections.Counter(row["key"] for _idx, row in _rows(fresh) if row["k"] == "work")
    assert counts and max(counts.values()) <= 2, counts             # 재시도 = 같은 줄 다시 · 판독은 1개


def case6_open_work_cells_stay(root, ft2=None, **_):
    """⑥ — 열린 work(owners · deliveries · done)의 칸은 state 에 남는다(끝난 work 만 옮긴다)."""
    _use(ft2)
    node = _scenario(root)
    assert _accept(node, "W9").assign("W9", "h9", evidence=EV).result == OK
    assert node.complete("W9", "a1").result == OK                   # 배정 줄은 있는데 전달 줄이 없다 = «열림»
    _drain(node)
    state = _state(node)
    assert "W9" in (state.get("done") or {}), sorted(state.get("done") or {})
    assert "W9" in (state.get("generations") or {}), state.get("generations")
    assert "W9" not in {row["key"] for _idx, row in _rows(node) if row["k"] == "work"}, "열린 work 를 장부로 옮겼다"
    assert "W9" not in (state.get("deliveries") or {}), state.get("deliveries")
    assert "W1" not in (state.get("done") or {}), sorted(state.get("done") or {})


def case7_first_install_batches(root, ft2=None, **_):
    """⑦ — base 에 닫힌 work 100개가 이미 접힌 첫 설치 꼴 → 여러 바퀴에 나눠 옮기고 매 바퀴 총량 ≤ 한계."""
    _use(ft2)
    count = 100
    node = _d(root)
    rs = _rs(node)
    state = {"schema": record.SCHEMA_VERSION, "revision": count, "pending": [], "attempts": {}}
    state.update({name: {} for name in record.EXTENDED_STATE_FIELDS})
    proj = {name: {} for name in journal.PROJ_FIELDS}
    for n in range(count):
        work = "S%05d" % n
        proj["done"][work] = {"attempt": "a1", "at": "2026-11-23T00:00:00", "marker": ""}
        proj["generations"][work] = 1
        proj["deliveries"][work] = ["a1"]
    for name in ("done", "generations", "deliveries"):               # 실제 state 꼴 = base 와 top-level 둘 다
        state[name] = dict(proj[name])
    state["journal_base"] = {"upto": 500, "count": count, "receipts": {}, "proj": proj}
    rs.journal.envelope = None
    rs.journal.write_state(state)
    batch = rs.journal._closed_batch.__func__.__globals__          # 모듈 전역(제품 자리) — 바퀴 수를 재려고 좁힌다
    original, batch["CLOSED_BATCH"] = batch["CLOSED_BATCH"], 10
    try:
        rounds, moved = 0, []
        while rounds < 40:
            before = _size(node)
            out = rs.journal.reclaim()
            rounds += 1
            assert out["result"] == RECLAIMED, out
            if not out.get("moved"):
                break
            moved.append(out["moved"])
            assert _size(node) < before, (rounds, _size(node), before)
            assert rs.journal.usage() <= rs.journal._limit(True), (rounds, rs.journal.usage())
    finally:
        batch["CLOSED_BATCH"] = original
    works = [row for _idx, row in _rows(node) if row["k"] == "work"]
    assert len(works) == count, (len(works), count)
    assert len(moved) > 1 and moved[0] < count, (moved, rounds)      # 한 바퀴에 다 옮기지 않는다
    assert not (_state(node).get("done") or {}), sorted(_state(node)["done"])[:3]


def case8_corrupt_ledger(root, ft2=None, **_):
    """⑧ — 닫힌 장부 반 줄 = «복구 필요» 1줄 · 쓰기 0(조용히 건너뛰지 않는다)."""
    _use(ft2)
    node = _scenario(root)
    _drain(node)
    path = _rs(node).journal.ledger.path()
    with open(path, "a", encoding="utf-8") as handle:
        handle.write('{"k": "work", "key": "W9", "row": {')       # 반 줄
    lines = len(node.rs.records())
    out = node.rs.submit("c-fresh8", "x" * 8, "F8")
    assert out.result == CORRUPT, out
    assert len(node.rs.records()) == lines                          # 쓰기 0
    state = _state(node)                                            # 첫 설치 꼴: base 에 접힌 닫힌 work 1개
    state["done"]["S9"] = {"attempt": "a1", "at": "2026-11-23T00:00:00", "marker": ""}
    state["journal_base"]["proj"]["done"]["S9"] = state["done"]["S9"]
    rs = _rs(node)
    rs.journal.envelope = None
    rs.journal.write_state(state)
    before = _size(node)
    assert rs.journal.reclaim()["result"] == CORRUPT               # 옮기기 전에 장부를 판독한다
    assert _size(node) == before and len(rs.records()) == lines     # 회수 쓰기 0


def case9_withdrawn_resubmit(root, ft2=None, **_):
    """⑨ — 회수된 철회 attempt 의 command 재접수 = 지금과 같은 답(새 attempt)."""
    _use(ft2)
    node = _d(root)
    assert node.rs.submit("c-with", "x" * 8).result == OK
    gate = withdraw.Withdraw(str(root), TEAM, **CAPS)
    assert gate.withdraw("c-with", "그만")["result"] == "철회 성공"
    for work in ("W1", "W2", "W3"):
        _close(node, work)
    _drain(node)
    assert [row for _idx, row in _rows(node) if row["k"] == "attempt"], "철회 줄이 장부로 안 갔다"
    assert gate.withdraw("c-with", "그만")["result"] == HOLD, "회수된 철회 = 멱등"
    again = node.rs.submit("c-with", "x" * 8)
    assert (again.result, again.attempt) == (OK, "c-with#a2"), again   # 번호가 되돌아가지 않는다


def case10_import_key(root, ft2=None, **_):
    """⑩ — 회수된 import key 로 다시 가져오기 = 지금과 같은 답(이미 가져옴 · 쓰기 0)."""
    _use(ft2)
    node = _d(root)
    for work in ("W1", "W2", "W3"):
        _close(node, work)
    row = dict(key="card/zz-r2520", body="card/zz-r2520.body", src="x", sha256="0" * 64, bytes=1)
    first = legacy_import.LegacyImport(str(root), TEAM, caps=CAPS).put(row)
    assert (first.result, first.status, first.written) == (OK, "가져옴", True), first
    for work in ("W4", "W5", "W6"):
        _close(node, work)
    _drain(node)
    assert [r for _idx, r in _rows(node) if r["k"] == "import"], "가져오기 줄이 장부로 안 갔다"
    lines = len(node.rs.records())
    again = legacy_import.LegacyImport(str(root), TEAM, caps=CAPS).put(row)
    assert (again.result, again.status, again.written) == (OK, "이미 가져옴", False), again
    assert len(node.rs.records()) == lines


def case11_cross_round_receipt(root, ft2=None, **_):
    """⑪(DA#57 반례) — 영수의 두 work(닫힌 쪽 · next)가 서로 다른 회수 바퀴에 빠져도 영수가 state 에 안 남는다."""
    _use(ft2)
    node = _d(root)
    for work in ("W1", "W2", "W3", "W4"):
        _close(node, work)
    assert node.rs.submit("c-N5", "x" * 8, "N5").result == OK        # 대기 카드 = 다음 work 후보
    first = _close_node(root).receipt(NANO, 1, "W1", "e1", NEXT, EV)
    assert (first.result, first.next) == (OK, "N5"), first            # 영수 → 배정 → 전달까지 이어진다
    _drain(node)                                                     # 1바퀴: 닫힌 쪽(W1)만 빠진다
    state = _state(node)
    assert "W1" not in (state.get("done") or {}), sorted(state.get("done") or {})
    assert "e1" in (state.get("close_receipts") or {}), "next 가 살아 있으면 영수도 살아 있다"
    assert node.rs.journal.ledger.event("e1") is None
    assert node.ex.result("N5", NEXT, 1, OK).result == OK
    assert node.complete("N5", "a1").result == OK
    for work in ("W6", "W7"):                                        # N5 조각을 마지막에서 밀어낸다
        _close(node, work)
    _drain(node)                                                     # 2바퀴: next(N5)가 빠지면 영수도 빠진다
    assert node.rs.journal.ledger.event("e1") is not None, "두 바퀴에 걸친 영수가 state 에 남았다"
    state = _state(node)
    assert "e1" not in (state.get("close_receipts") or {}), sorted(state.get("close_receipts") or {})
    again = _close_node(root).receipt(NANO, 1, "W1", "e1", NEXT, EV)
    assert (again.result, again.written, "재접수" in again.reason) == (HOLD, False, True), again


CASES = {"①": case1_state_shrinks, "②": case2_size_flat_in_finished_count,
         "③": case3_resubmit_same_command, "④": case4_close_receipt_lookup,
         "⑤장부뒤": functools.partial(case5_crash_points, step="reclaim_after_ledger"),
         "⑤체크포인트뒤": functools.partial(case5_crash_points, step="reclaim_after_checkpoint"),
         "⑤조각뒤": functools.partial(case5_crash_points, step="reclaim_after_seg"),
         "⑥": case6_open_work_cells_stay, "⑦": case7_first_install_batches,
         "⑧": case8_corrupt_ledger, "⑨": case9_withdrawn_resubmit, "⑩": case10_import_key,
         "⑪다음바퀴": case11_cross_round_receipt}


def test_cases(tmp_path):
    for name, case in CASES.items():
        case(tmp_path / name)


def _swap_order(text):
    """M3 변이 — «장부 덧붙이기 → state checkpoint» 순서를 state 먼저로 맞바꾼다."""
    start = text.index("            if rows:\n                self.ledger.index()")
    middle = text.index('            self.ops("reclaim_checkpoint")\n', start)
    end = text.index('            self.on_step("reclaim_after_checkpoint")\n', middle) + len(
        '            self.on_step("reclaim_after_checkpoint")\n')
    ledger, state = text[start:middle], text[middle:end]
    return text[:start] + state + ledger + text[end:]


MUTANTS = {
    # M1 회수 때 state 칸을 안 뺌 → ① ② Red
    "M1": ([("core/journal.py", "        moved = set(works)", "        moved = set()")], ("①", "②")),
    # M2 입구 판독이 닫힌 장부를 안 봄 → ③ Red
    "M2": ([("core/intake.py",
             "        closed = self.journal.ledger.command(command)\n        if closed is not None:",
             "        closed = None\n        if closed is not None:")], ("③",)),
    # M3 순서를 state 먼저로 바꿈 → ⑤(checkpoint 뒤) Red
    "M3": ([("core/journal.py", _swap_order)], ("⑤체크포인트뒤",)),
    # M4 열린 work 도 옮김 → ⑥ Red
    "M4": ([("core/journal.py", "            if work.startswith(CLOSED_SYNTHETIC) or work in live_works:",
             "            if work.startswith(CLOSED_SYNTHETIC):"),
            ("core/journal.py", "            if self._closed_why_rows(work, by_work.get(work) or [], state):",
             "            if False:")], ("⑥",)),
    # M5 첫 회수에 예약 검사 없이 한 번에 옮김 → ⑦ Red
    "M5": ([("core/journal.py", "        for batch in (CLOSED_BATCH, 50, 10, 1):", "        for batch in (10 ** 9,):"),
            ("core/journal.py",
             "            if self.usage() + need <= self._limit(True) or (not rows and batch == CLOSED_BATCH):",
             "            if True:")], ("⑦",)),
    # M6 깨진 줄을 건너뜀 → ⑧ Red
    "M6": ([("core/journal.py",
             "                    except (ValueError, KeyError, TypeError) as exc:\n"
             "                        raise self.rec.CorruptStateError(\"닫힌 장부 판독 불가: %s\" % exc)",
             "                    except (ValueError, KeyError, TypeError):\n                        continue")], ("⑧",)),
    # M7 조회 결과를 저장용 state dict 에 합침 → ④ Red
    "M7": ([("core/close_next.py", "            seen, archived = self.rs.journal.ledger.event(event), True",
             "            seen, archived = self.rs.journal.ledger.event(event), True\n"
             "            if seen is not None:\n                self.rs.journal.write_state(dict(\n"
             "                    state, close_receipts=dict(state.get(\"close_receipts\") or {}, **{event: seen})))")],
            ("④",)),
    # M8 pending · attempts · base.receipts 를 안 옮김 → ② Red
    "M8": ([("core/journal.py", "        if commands:", "        if False:")], ("②",)),
    # M10 영수를 이번 바퀴 moved 만 보고 옮김(두 바퀴에 걸친 영수 잔류) → ⑪ Red
    "M10": ([("core/journal.py",
              'if not self._archived(row.get("work"), moved) or not self._archived(row.get("next"), moved):',
              'if row.get("work") not in moved or (row.get("next") is not None and row.get("next") not in moved):')],
            ("⑪다음바퀴",)),
    # M9 event · attempt · import 진입점을 닫힌 장부에 안 이음 → ③ ④ ⑨ ⑩ Red
    "M9": ([("core/journal.py", "        return (self.index().get((kind, key)) or {}).get(\"row\")",
             "        return None")], ("③", "④", "⑨", "⑩")),
}


def _mutant(tmp_path, pairs):
    """사본 트리 1곳 변이 — (파일, 옛 글, 새 글) 또는 (파일, 글→글 함수)."""
    tree = tmp_path / "m" / "ft2"
    shutil.copytree(FT2, tree, ignore=shutil.ignore_patterns("tests", "__pycache__"))
    for rel, old, *rest in pairs:
        text = (tree / rel).read_text(encoding="utf-8")
        if not rest:
            (tree / rel).write_text(old(text), encoding="utf-8")
            continue
        assert text.count(old) == 1, (rel, old)
        (tree / rel).write_text(text.replace(old, rest[0]), encoding="utf-8")
    return tree


def test_mutants_break_their_cases(tmp_path):
    """M1~M9 — 사본 트리 1곳 변이 = 그 사례가 깨진다(원본 같은 사례 = 통과)."""
    for name, (pairs, cases) in MUTANTS.items():
        tree = _mutant(tmp_path / name, pairs)
        broken = {key: False for key in cases}
        for key in cases:
            try:
                CASES[key](tmp_path / name / ("m-" + key), ft2=tree)
            except (AssertionError, IndexError, KeyError, TypeError, ValueError):
                broken[key] = True
        assert all(broken.values()), (name, broken)
        for key in cases:
            CASES[key](tmp_path / name / ("o-" + key))


def _crash(root, step, ft2=None):
    """자식 프로세스가 정지점에서 os._exit(9) — 사본 트리(변이)도 같은 자리에서 죽는다."""
    return subprocess.run([sys.executable, os.path.abspath(__file__), str(root), step, str(ft2 or FT2)],
                          env=CHILD_ENV, capture_output=True, timeout=25)


def _child_main(argv):
    root, step, tree = argv[0], argv[1], argv[2]
    _use(tree)

    def hook(point):
        if point == step:
            os._exit(9)

    _d(root, on_step=hook).rs.journal.reclaim()
    return 0


if __name__ == "__main__" and os.environ.get("FT2_CLOSED_LEDGER_CHILD") == "1":
    sys.exit(_child_main(sys.argv[1:]))
