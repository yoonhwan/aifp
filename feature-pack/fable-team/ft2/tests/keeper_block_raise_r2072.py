"""r2072 ft2 keeper 오래 이어진 줄 → 막힘 장부 올림 시험 (카드 반례 ①~⑨ · 변이 M1~M4 · ⑩ = 기존 keeper 시험 재실행).
r1812 대역(keeper_world_r1812.World · 임시 root · 주입 시계 · tmux·git·mbox 스텁) 재사용 · 장부 = FT_BLOCK_BIN 스텁
(block.sh 인자 규칙 검사 · 인자·FT20_SCAN_ROOT 기록 · rc·stderr·멈춤(fifo 읽기) 바꿈) · 줄 = 바퀴 본문(_round)을 바꿔 keeper.log 로 넣는다.
실 tmux·장부·keeper 상태 0 · sleep 0. 기준판(keeper_block.py 없음) = ③ · ⑥ 첫 칸 Red.
r2330: 스텁이 자기 «pid pgid» 를 <스텁>.pids 에 적고(Y1) · 시험 끝(fixture finally)에 reap_stubs 가 그 그룹을 SIGKILL + fifo 풀기 + unlink 한다(Y2).
같은 그룹(pgid == 내 그룹 또는 ≤1) = 그 pid 만 kill · 내 uid 아닌 pid · 다른 프로세스 번호 재사용 = 신호 0.

r2526 — 이 파일은 사례·변이·거두기 정의만 둔다(시험 함수 0). 시험 파일 셋으로 나눠 단독 70초를 넘기지 않는다:
  a = 사례 12개(test_case) · b = 변이 4개 + test_report_and_lock · c = test_same_without_ledger 5 + test_same_real_round_and_hang.
r2526 반례 ③ ⑦ — SIGTERM(끊김)에서도 정리로 도달하는 handler(install/uninstall · reap_on_signal)를 여기 둔다.
정상 끝은 reap_stubs(fixture) · 끊김은 handler — 둘 다 «이 시험이 띄운 그룹만» 거둔다(argv·uid·pgid 확인 · 판정 실패 = 신호 0).
DA#57 HOLD1 정정(4c01afd74b6) — argv 를 못 읽은 모양(«(Python)»)은 소유 추정 0: 한 개도 안 죽이고 «판정 불가»(신호 0 · rc 3).
"""
import importlib.util
import json
import os
import re
import shutil
import signal
import subprocess
import threading
import time
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location("keeper_world_r1812", str(Path(__file__).with_name("keeper_world_r1812.py")))
kw = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(kw)
World, FT2, T0, _lines, _put = kw.World, kw.FT2, kw.T0, kw._lines, kw._put
NOMASTER = "쪽지 _master 없음 — [긴급] UNKNOWN t1 w1 - accept-only · 접수 1줄 · %d분"
REC = ".pids"   # r2330 Y1 — 스텁이 «pid pgid» 를 적는 자리(<장부 스텁 경로>.pids = 이 시험 tmp_path 아래)
STUB = r'''#!/bin/bash
exec __PY__ - "$0" "$@" <<'PY'
import json, os, sys
me, a = sys.argv[1], sys.argv[2:]
open(me + ".pids", "a").write("%d %d\n" % (os.getpid(), os.getpgid(0)))   # r2330 Y1 — 멈추기 전에 내 pid·그룹을 적는다
def ok():
    if a[:1] != ["raise"] or len(a) < 4 or a[2] not in ("seat", "card", "team") or not all(a[1:4]): return False
    opt, rest = {}, a[4:]
    while rest:
        if len(rest) < 2 or rest[0] not in ("--cause", "--fix", "--period", "--class", "--owner", "--due", "--scope", "--waiter", "--recheck", "--recheck-in"): return False   # r2496 덧칸
        opt[rest[0]], rest = rest[1], rest[2:]
    return bool(opt.get("--cause")) and bool(opt.get("--fix")) and (opt.get("--period") or "0").isdigit()
rc = 0 if ok() else 2
open(me + ".log", "a").write(json.dumps({"argv": a, "root": os.environ.get("FT20_SCAN_ROOT"), "rc": rc}, ensure_ascii=False) + "\n")
if os.path.exists(me + ".fifo"): open(me + ".fifo").read()   # 멈춤 = fifo 읽기(쓰는 쪽이 열 때까지)
if os.path.exists(me + ".err"): sys.stderr.write(open(me + ".err").read())
sys.exit(rc or int(open(me + ".rc").read()) if os.path.exists(me + ".rc") else rc)
PY
'''


def world(tmp, mp, ft2=FT2, ledger=True):
    w = World(tmp, mp, ft2)
    w.block = tmp / "bin" / "block"
    _put(w.block, STUB.replace("__PY__", kw.sys.executable)), w.block.chmod(0o755)
    w.env.pop("FT_CRITICAL_OFF", None)
    if ledger:
        w.env["FT_BLOCK_BIN"] = str(w.block)
    ENGAGED.append(w)   # r2330 Y2 — 이 시험이 띄운 스텁은 시험 끝에서 거둔다
    return w


ENGAGED = []   # r2330 — 이번 시험의 World(스텁 기록·fifo) 목록


def _procs():
    """이 기계 프로세스 표 — (pid, ppid, pgid, uid, argv) · ps 실패 = 빈 표(판정 불가 = 신호 0)."""
    try:
        p = subprocess.run(["ps", "-axo", "pid=,ppid=,pgid=,uid=,command="], capture_output=True, text=True, timeout=7)
    except (OSError, subprocess.SubprocessError):
        return []
    rows = []
    for line in (p.stdout if not p.returncode else "").splitlines():
        f = line.split(None, 4)
        if len(f) == 5 and all(x.isdigit() for x in f[:4]):
            rows.append((int(f[0]), int(f[1]), int(f[2]), int(f[3]), f[4]))
    return rows


def read_pairs(rec):
    """기록 파일 엄격 판독 — «pid pgid» 두 정수 줄만 정상 · 그 밖은 (None, «판정 불가» 1줄)(r2526 반례 ⑦).

    거두기(reap)는 관대하게 읽어도 되지만, 신호 길은 «내 것인가» 를 판정해야 하므로 깨진 기록을 조용히 넘기지 않는다.
    """
    pairs = []
    for line in _lines(str(rec)):
        f = line.split()
        if not f:
            continue
        if len(f) != 2 or not f[0].isdigit() or not f[1].isdigit():
            return None, "pids 기록 깨짐(«pid pgid» 아님): %s" % line[:60]
        pairs.append((int(f[0]), int(f[1])))
    return pairs, None


def owned_row(argv, tmp):
    """이 시험이 띄운 것이 **분명한가** — argv 에 이 시험 tmp 가 있을 때만 참. 추정 0.

    r2526 ③ — 기록 파일에 섞인 남의 그룹(시험 밖 sleep 대역)은 argv 가 읽히고 tmp 가 없으므로 **신호 0**.
    DA#57 HOLD1(4c01afd74b6) — argv 를 못 읽은 모양(«(Python)»)을 소유로 추정하지 않는다.
    pid·pgid·uid 가 맞아도 번호 재사용을 배제할 수 없다 → 그 칸은 argv_unknown 이 «판정 불가» 로 닫는다(신호 0).
    """
    return tmp in argv


def argv_unknown(argv):
    """ps 가 argv 를 못 읽은 모양(«(Python)» · «(정지)» 등 괄호 하나) — 소유를 추정할 수 없다."""
    return argv.startswith("(") and argv.endswith(")")


def kill_pairs(w, pairs, table=None):
    """기록된 «pid pgid» 만 거둔다 — 반환 = («죽인 수», «판정 불가» 사유 또는 None).

    killpg 는 그 그룹에 이 시험 tmp_path 를 argv 에 단 프로세스가 있을 때만.
    같은 그룹(pgid == 내 그룹 또는 ≤1)이면 그 pid 만 kill(같은 묶음 시험·pytest 를 죽이지 않음) · 내 uid 아닌 pid · 이미 죽은 pid · 번호 재사용 = 신호 0.
    argv 에 이 시험 tmp 가 없는 프로세스(기록에 섞인 남의 그룹) = 신호 0.
    ps 실패(⑥) · argv 판독 불가(HOLD1) = **한 개도 안 죽이고** «판정 불가» — 신호 0 · 부르는 쪽이 rc≠0 으로 끝낸다.
    """
    if not pairs:
        return 0, None
    table = _procs() if table is None else table
    if not table:
        return 0, "ps 판독 실패 — 소유 판정 불가"
    tmp, mine, unknown = str(w.tmp), [], 0
    for pid, pgid in pairs:
        row = [r for r in table if r[0] == pid]
        if not row or row[0][3] != os.getuid() or row[0][2] != pgid:
            continue
        if argv_unknown(row[0][4]):   # HOLD1 — 읽을 수 없는 argv 로 소유를 추정하지 않는다
            unknown += 1
            continue
        if not owned_row(row[0][4], tmp):   # r2526 ③ — 기록에 섞인 남의 그룹 = 신호 0
            continue
        mine.append((pid, pgid))
    if unknown:
        return 0, "argv 판독 불가 %d건 — 소유 판정 불가(신호 0)" % unknown
    killed = 0
    for pid, pgid in mine:
        group = pgid if pgid > 1 and pgid != os.getpgrp() and [r for r in table if r[2] == pgid and tmp in r[4]] else 0
        try:
            if group:
                os.killpg(group, signal.SIGKILL)
            else:
                os.kill(pid, signal.SIGKILL)
            killed += 1
        except OSError:   # 이미 죽음(ProcessLookupError) = 정상
            pass
    return killed, None


def reap(w):
    """r2330 Y2 — 이 시험이 띄운 스텁을 거둔다: fifo 풀기 → 기록된 «pid pgid» SIGKILL → unlink(성공·실패·예외 전부).

    정상 끝 길이다. 판정 실패(ps 실패 · 기록 깨짐)는 조용히 신호 0 — 판정을 바꾸지 않는다.
    """
    fifo = Path(str(w.block) + ".fifo")
    try:
        if fifo.exists():
            release(fifo)
        pairs, why = read_pairs(Path(str(w.block) + REC))
        if pairs:
            kill_pairs(w, pairs)
        fifo.unlink(missing_ok=True)
    except Exception:   # 거두기는 곁가지 — 시험 판정을 바꾸지 않는다
        pass


def reap_on_signal(w):
    """r2526 반례 ③ ⑦ — 신호 길: 읽어서 내 것인지 판정한 뒤에만 fifo 를 풀고 그룹을 거둔다. 반환 = «판정 불가» 사유 또는 None.

    기록이 깨졌거나 ps 판독이 실패하면 **아무것도 건드리지 않고**(fifo 도 신호도) 사유를 돌려준다(⑦ · ⑥).
    """
    pairs, why = read_pairs(Path(str(w.block) + REC))
    if pairs is None:
        return why
    _killed, why = kill_pairs(w, pairs)
    if why:
        return why
    fifo = Path(str(w.block) + ".fifo")
    try:
        if fifo.exists():
            release(fifo)
    except Exception:
        pass
    return None


# ── r2526 — SIGTERM(끊김)에서도 정리로 도달하는 handler ────────────────────────────────
# DA#59 H1: SIGTERM 의 Python 기본 종료는 finally · pytest fixture teardown 을 돌리지 않는다.
#   → 시험이 도는 동안 handler 를 걸어 두고, 신호를 받으면 «이 시험이 띄운 그룹만» 거둔 뒤 기본 동작으로 되돌려 같은 신호를 다시 올린다(부모는 신호로 끝난다 = rc 그대로).
# 소유 판정은 reap 과 같은 표(내 uid · pgid 일치 · argv 에 이 시험 tmp) — 남의 그룹(시험 밖 sleep 대역)·pytest 자기 그룹은 대상이 아니다.
# 판정 불가(기록 깨짐 · ps 실패) = 신호 0 · «판정 불가» 1줄 · rc≠0(UNDECIDABLE).
HANDLED = (signal.SIGTERM, signal.SIGINT)
_OLD = {}
UNDECIDABLE = 3   # r2526 ⑦ — 소유 판정 실패로 끝났을 때의 rc


def _on_signal(signum, _frame):
    bad = []
    for w in list(ENGAGED):
        why = reap_on_signal(w)
        if why:
            bad.append(why)
    if bad:
        os.write(2, ("판정 불가 r2526 — %s · 신호 0\n" % bad[0]).encode())
        uninstall()
        os._exit(UNDECIDABLE)
    uninstall()
    os.kill(os.getpid(), signum)   # 기본 동작 복원 뒤 같은 신호 = 부모는 신호로 끝난다


def install():
    """이 시험이 도는 동안 SIGTERM·SIGINT handler 를 건다(이미 걸었으면 그대로)."""
    if _OLD:
        return
    for sig in HANDLED:
        _OLD[sig] = signal.getsignal(sig)
        signal.signal(sig, _on_signal)


def uninstall():
    """정상 끝 — handler 를 원래대로 되돌린다(다른 시험 · pytest 기본 동작을 건드리지 않는다)."""
    while _OLD:
        sig, old = _OLD.popitem()
        signal.signal(sig, old)


def reap_stubs_body(tmp):
    """시험 하나의 앞뒤 — 앞: ENGAGED 비우고 handler 등록 · 뒤: handler 해제 → 띄운 스텁 그룹 거두기.

    각 시험 파일이 autouse fixture 로 감싼다(fixture 는 이 파일이 아니라 시험 파일에 있어야 pytest 가 autouse 로 본다).
    """
    _ = tmp
    ENGAGED.clear()
    install()
    try:
        yield
    finally:
        uninstall()
        while ENGAGED:
            reap(ENGAGED.pop())


def calls(w):
    return [json.loads(x) for x in _lines(str(w.block) + ".log")]


def at(w, t, rows=(), real=False):
    """주입 시계 T0+t 에 바퀴 1회 · rows = 이 바퀴에 찍을 (종류, 팀, 글) · real = 원래 바퀴 본문도 돈다 → 이 바퀴 장부 호출."""
    w.t = T0 + t
    (Path(str(w.block) + ".log")).unlink(missing_ok=True)
    k = w.keeper()
    body = k._round
    def fake():
        for kind, team, text in rows:
            k.log(kind, team, text)
        return body() if real else None
    k._round = fake
    w.lines = w.round(k)
    return calls(w)


def kdir(w):
    return w.state / "ft2-keeper"


def snapshot(w):
    """⑧ 불변 칸 — 그날 jsonl · state.json 바이트 · tmux·mbox·닫기 스텁 기록."""
    d = kdir(w)
    jl = sorted(d.glob("*.jsonl"))
    logs = [_lines(str(p) + ".log") for p in (w.tm, w.mbox, w.close)]
    return [_lines(p) for p in jl], (d / "state.json").read_bytes() if (d / "state.json").exists() else b"", logs


def case_lib(w):
    """① lib — FT_BLOCK_BIN 스텁 · raise 1회 = 인자 그대로 1회 · FT20_SCAN_ROOT = root · 원인 160자 · 첫 줄만."""
    kb = kw._mod(w.ft2 / "adapters" / "pi" / "keeper_block.py", "kb_%d" % id(w))
    args = ["ft2-keeper:HELD", "team", "t1", "--cause", "c1", "--fix", "f1", "--period", "150"]
    kb.Ledger(str(w.root), w.env).raise_(*args)
    got = calls(w)
    assert [c["argv"] for c in got] == [["raise"] + args] and got[0]["root"] == str(w.root), got
    Path(str(w.block) + ".log").unlink()
    kb.Ledger(str(w.root), w.env).raise_("ft2-keeper:HELD", "team", "t1", "--cause", "가" * 200, "--fix", "f1")
    assert calls(w)[0]["argv"][5] == "가" * 160
    Path(str(w.block) + ".log").unlink()
    kb.Ledger(str(w.root), w.env).raise_("ft2-keeper:HELD", "team", "t1", "--cause", "첫줄\n둘째", "--fix", "f1")
    assert calls(w)[0]["argv"][5] == "첫줄"


def case_none(w):
    """① 장부 없음(FT_BLOCK_BIN 없음 ∧ root 에 block.sh 없음) · FT_CRITICAL_OFF=1 → 장부 호출 0 · 예외 0.
    r2496 ⑬ — «전문 파일» 은 장부 도구 유무와 무관하게 이 바퀴 값으로 덮인다(오래된 «NEXT-HOLD 50분째» 가 남지 않게) → 0줄이면 0바이트."""
    for off in (False, True):
        if off:
            w.env["FT_BLOCK_BIN"], w.env["FT_CRITICAL_OFF"] = str(w.block), "1"
        for t in range(0, 721, 60):
            assert at(w, t + (2000 if off else 0), [("판정 불가", "t1", NOMASTER % t)]) == []
        assert not (kdir(w) / "blockseen.json").exists()
        latest = kdir(w) / "blocks-latest.txt"   # r2496 ⑬ · r2072 는 «파일 없음» 을 봤다 → 이제 «0바이트» 를 본다(장부 없이도 전문은 이 바퀴 값)
        assert latest.exists() and latest.read_text(encoding="utf-8") == ""


def case_default_path(w):
    """① 기본 자리 = <root>/.fable-team/state/ft20-r1483-watch/block.sh(FT_BLOCK_BIN 없음)."""
    w.env.pop("FT_BLOCK_BIN")
    dst = w.state / "ft20-r1483-watch" / "block.sh"
    _put(dst, w.block.read_text(encoding="utf-8"))
    w.block = dst
    for t in range(0, 601, 60):
        got = at(w, t, [("판정 불가", "t1", NOMASTER % t)])
    assert len(got) == 1 and got[0]["root"] == str(w.root), got


def case_rc9(w):
    """② 스텁 rc 9 + stderr 글 → 예외 0 · keeper 출력·로그에 그 글 0."""
    Path(str(w.block) + ".rc").write_text("9")
    Path(str(w.block) + ".err").write_text("STDERR-NOISE-2072\n")
    for t in range(0, 601, 60):
        got = at(w, t, [("판정 불가", "t1", NOMASTER % t)])
    assert len(got) == 1
    assert not any("STDERR-NOISE" in x for x in w.lines)
    assert not any("STDERR-NOISE" in x for p in kdir(w).glob("*.jsonl") for x in _lines(p))


def release(fifo):
    try:
        os.close(os.open(str(fifo), os.O_WRONLY | os.O_NONBLOCK))
    except OSError:
        pass


def hang_round(w, t, rows, real=False):
    """멈춘 스텁 바퀴 1회 — 9초 안에 안 끝나면 fifo 를 열어 풀고 FAIL(M4)."""
    fifo = Path(str(w.block) + ".fifo")
    os.mkfifo(str(fifo))
    box, start = {}, time.monotonic()
    th = threading.Thread(target=lambda: box.update(got=at(w, t, rows, real)))
    th.start()
    th.join(9)
    alive = th.is_alive()
    while th.is_alive():
        release(fifo)
        th.join(0.5)
    release(fifo)
    fifo.unlink()
    assert not alive and time.monotonic() - start < 9, "장부 멈춤 상한 없음"
    return box["got"]


def case_hang(w):
    """② 스텁이 fifo 읽기에서 멈춤 → 7+2초 안 · 그 바퀴 다음 장부 호출 0."""
    def two(t):
        return [("판정 불가", "t1", NOMASTER % t), ("HELD", "t2", "w2 닫기 보류 %d" % t)]
    for t in range(0, 541, 60):
        assert at(w, t, two(t)) == []
    got = hang_round(w, 600, two(600))
    assert len(got) == 1, got


def case_cap20(w):
    """② 오래 이어진 묶음 25개 → 호출 20회(처음 시각이 이른 순)."""
    for t in range(0, 841, 60):
        rows = [("판정 불가", "t%02d" % i, "x 쪽지 _master 없음 %d" % t) for i in range(min(25, 5 * (t // 60 + 1)))]
        got = at(w, t, rows)
    assert len(got) == 20 and sorted(c["argv"][3] for c in got) == ["t%02d" % i for i in range(20)], got


def case_long(w):
    """③ 10분 넘게 이어진 «판정 불가» → 600초 바퀴에 raise 1회 · 300초 뒤까지 · 301초 뒤 0 · 지워진 뒤 다시 처음부터."""
    for t in range(0, 541, 60):
        assert at(w, t, [("판정 불가", "t1", NOMASTER % t)]) == [], t
    got = at(w, 600, [("판정 불가", "t1", NOMASTER % 600)])
    assert len(got) == 1, got
    a = got[0]["argv"]
    assert a[:4] == ["raise", "ft2-keeper:판정-불가", "team", "t1"] and a[a.index("--period") + 1] == "150", a
    assert a[a.index("--cause") + 1].startswith("판정 불가 1줄 10분 넘게 · 쪽지 _master 없음"), a
    assert ".fable-team/state/ft2-keeper/blocks-latest.txt" in a[a.index("--fix") + 1]
    for t in range(660, 901, 60):
        assert len(at(w, t)) == 1, t
    assert at(w, 900) and at(w, 901) == []
    assert "t1" not in (kdir(w) / "blockseen.json").read_text(encoding="utf-8")
    for t in range(961, 1502, 60):
        assert at(w, t, [("판정 불가", "t1", NOMASTER % t)]) == [], t
    assert len(at(w, 1561, [("판정 불가", "t1", NOMASTER % 1561)])) == 1


def case_other_kinds(w):
    """④ 대상 밖 종류 20분 매 바퀴 → 호출 0 · 기억 0줄 · 전문 0바이트."""
    for t in range(0, 1201, 60):
        rows = [(k, "t1", "w1 %d" % t) for k in ("UNKNOWN", "WORKING", "PARKED", "BG-FETCH")] + [("ROUND", "", "s=%d" % t)]
        assert at(w, t, rows) == [], t
    assert json.loads((kdir(w) / "blockseen.json").read_text(encoding="utf-8")) in ({}, [], {"rows": {}})
    assert (kdir(w) / "blocks-latest.txt").read_bytes() == b""


def case_held_seat(w):
    """⑤ HELD-SEAT 0·600초에만 → 600초 raise · 관측 없는 바퀴 1200초까지 유지 · 1201초 0 / 0초에만 → 0(수명 = r2539 K2 RETRY_S 300 + 300)."""
    line = ("HELD-SEAT", "seats-t1", "s1 rc 3 닫기 실패 — 600초 뒤 다시")
    assert at(w, 0, [line]) == []
    got = at(w, 600, [line])
    assert len(got) == 1 and got[0]["argv"][1:4] == ["ft2-keeper:HELD-SEAT", "team", "seats-t1"], got
    assert len(at(w, 1200)) == 1 and at(w, 1201) == []
    assert at(w, 5000, [line]) == [] and at(w, 5600) == [] and at(w, 6000) == []   # 0초에만 관측 = 처음 시각이 안 늘어 long 0


def case_fill_wait(w):
    """⑥ FILL-WAIT 0초 1줄 + state.fill_wait 에 t1 남음 → 600초 raise 1회 / t1 빠짐 → 301초 뒤 0."""
    _put(kdir(w) / "state.json", {"fill_wait": {"t1": 8}})
    assert at(w, 0, [("FILL-WAIT", "t1", "남은 일 8/8 — fill 0 · 다음 바퀴")]) == []
    for t in range(60, 541, 60):
        assert at(w, t) == [], t
    got = at(w, 600)
    assert len(got) == 1 and got[0]["argv"][1:4] == ["ft2-keeper:FILL-WAIT", "team", "t1"], got
    st = json.loads((kdir(w) / "state.json").read_text(encoding="utf-8"))
    st["fill_wait"].pop("t1")
    _put(kdir(w) / "state.json", st)
    assert len(at(w, 660)) == 1 and at(w, 900) and at(w, 901) == []


def case_groups(w):
    """⑦ t1 판정 불가 3줄(0·60·120초) + HELD 1줄 · 팀 칸 빈 판정 불가 1줄 → raise 3회 · 전문 5줄 오래된 순 / 0 → 0바이트."""
    for t in range(0, 721, 60):
        rows = [("판정 불가", "t1", "%s 쪽지 _master 없음 %d" % (c, t)) for i, c in enumerate("가나다") if t >= 60 * i]
        rows += [("HELD", "t1", "w9 보류 %d" % t), ("판정 불가", "", "git fetch 실패 r %d" % t)]
        got = at(w, t, rows)
    keys = sorted((c["argv"][3], c["argv"][1]) for c in got)
    assert keys == [("keeper", "ft2-keeper:판정-불가"), ("t1", "ft2-keeper:HELD"), ("t1", "ft2-keeper:판정-불가")], got
    t1 = [c["argv"] for c in got if c["argv"][1:4] == ["ft2-keeper:판정-불가", "team", "t1"]][0]
    assert t1[t1.index("--cause") + 1].startswith("판정 불가 3줄 10분 넘게 · 가 쪽지 _master 없음 720"), t1
    full = (kdir(w) / "blocks-latest.txt").read_text(encoding="utf-8").splitlines()
    assert len(full) == 5 and full[-1].split("\t")[1:3] == ["판정 불가", "t1"] and full[-1].startswith("10분째"), full
    assert full[-1].split("\t")[3] == "다 쪽지 _master 없음 720"
    assert at(w, 1100) == [] and (kdir(w) / "blocks-latest.txt").read_bytes() == b""


def case_skip_early(w):
    """⑧ SKIP_TEAMS 판독 실패로 일찍 끝난 바퀴(실 본문) = 그 바퀴 줄을 셈 → 600초 바퀴 raise."""
    (kdir(w) / "SKIP_TEAMS").mkdir(parents=True)
    for t in range(0, 541, 60):
        assert at(w, t, real=True) == [], t
    got = at(w, 600, real=True)
    assert len(got) == 1 and got[0]["argv"][1:4] == ["ft2-keeper:판정-불가", "team", "keeper"], got


CASES = {"③": case_long, "④": case_other_kinds, "⑤": case_held_seat, "⑥": case_fill_wait, "⑦": case_groups}
ALL = {"①lib": case_lib, "①none": case_none, "①path": case_default_path, "②rc9": case_rc9, "②hang": case_hang, "②cap20": case_cap20,
       **CASES, "⑧skip": case_skip_early}


def run_case(name, tmp, mp):
    """사례 1개 — 세계 1개 · 끝나면 마지막 바퀴 호출도 인자 규칙 통과(⑨)."""
    w = world(tmp, mp, ledger=name != "①none")
    ALL[name](w)
    assert all(c["rc"] == 0 for c in calls(w)), calls(w)   # ⑨ 마지막 바퀴 호출도 인자 규칙 통과


def norm(obj, base):
    """임시 폴더 이름(a·b)과 벽시계 칸(ROUND wall·other = 실제 초)을 지운 비교용 글."""
    return re.sub(r"\b(wall|other)=[0-9.]+", r"\1=#", json.dumps(obj, ensure_ascii=False, default=repr).replace(str(base), "@"))


def record(w, sink):
    """⑧ 바퀴마다 keeper 출력 · 불변 칸 · ⑨ 장부 호출을 모은다."""
    real = w.round
    def round_(k=None):
        lines = real(k)
        sink["out"].append(norm((list(lines), snapshot(w)), w.tmp))
        sink["calls"] += calls(w)
        return lines
    w.round = round_


def run_same_without_ledger(name, tmp, mp):
    """⑧ ③~⑦ 각 바퀴 stdout · jsonl · rc · state.json · 바깥 스텁 기록 = «장부 도구 없음» 실행과 같음 · ⑨ 인자 규칙."""
    runs = []
    for sub, ledger in (("a", True), ("b", False)):
        (tmp / sub).mkdir()
        w = world(tmp / sub, mp, ledger=ledger)
        sink = {"out": [], "calls": []}
        record(w, sink)
        if ledger:
            CASES[name](w)
            assert all(c["rc"] == 0 and all(c["argv"]) for c in sink["calls"]), sink["calls"]
            assert bool(sink["calls"]) == (name != "④")
        else:
            try:
                CASES[name](w)   # 장부 없음 = 첫 올림 기대 칸에서 멈춤(④ 는 끝까지)
            except (AssertionError, OSError):   # ④ = 기억 파일 없음
                pass
        runs.append(sink["out"])
    a, b = runs
    assert len(b) >= 2 and a[:len(b)] == b


def run_same_real_round_and_hang(tmp, mp):
    """⑧ 실 바퀴 본문 + 장부 스텁 멈춤 바퀴 = «장부 도구 없음» 과 같음."""
    runs = []
    for sub, ledger in (("a", True), ("b", False)):
        (tmp / sub).mkdir()
        w = world(tmp / sub, mp, ledger=ledger)
        w.work("w1", done=False, alive=True)
        out = []
        for t in range(0, 601, 60):
            rows = [("판정 불가", "t1", NOMASTER % t)]
            if t == 600 and ledger:
                assert len(hang_round(w, t, rows, real=True)) == 1
            else:
                at(w, t, rows, real=True)
            out.append(norm((w.lines, snapshot(w)), w.tmp))
        runs.append(out)
    for x, y in zip(*runs):
        assert x == y


def run_report_and_lock(tmp, mp):
    """⑧ --report 실행 = 장부 호출 0 · 기억·전문 파일 mtime 그대로 / 잠금 파일이 있는 바퀴 = 호출 0 · 같음."""
    w = world(tmp, mp)
    for t in range(0, 601, 60):
        got = at(w, t, [("판정 불가", "t1", NOMASTER % t)])
    assert len(got) == 1
    files = [kdir(w) / "blockseen.json", kdir(w) / "blocks-latest.txt"]
    mt = [p.stat().st_mtime_ns for p in files]
    Path(str(w.block) + ".log").unlink()
    w.t = T0 + 660
    w.keeper().report_once()
    assert calls(w) == [] and [p.stat().st_mtime_ns for p in files] == mt
    lock = kdir(w) / "keeper.lock"
    lock.write_text("")
    before = snapshot(w)
    k = w.keeper()
    assert k.run_once() == 0 and calls(w) == [] and [p.stat().st_mtime_ns for p in files] == mt
    assert k.lines == ["SKIP 앞 바퀴 진행 중(잠금) — 바퀴 0"] and snapshot(w)[1:] == before[1:]
    lock.unlink()


MUTANTS = {   # 이름: (바꿀 글, 새 글, 사례) — keeper_block.py 사본에서만
    "M1": ("LONG_S = 600", "LONG_S = 0", "③"),
    "M2": ('re.sub(r"\\d+", "N", text)', "text", "③"),
    "M3": ("return kind.startswith(\"HELD\") or kind in KINDS", "return True", "④"),
    "M4": ("timeout=LIMIT_S", "timeout=None", "②hang"),
}
