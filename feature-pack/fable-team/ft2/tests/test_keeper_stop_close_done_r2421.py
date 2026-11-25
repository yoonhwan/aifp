"""r2421 ft2 keeper — 전팀 정지(ALL_STOP) 중에도 일이 끝난 좌석 3자리는 닫는다(카드 반례 ①~⑫ · 변이 M1~M9).

대상 3자리 = 착지 근거가 참인 나노(keeper_close 148행 갈래 · K1) · 후계가 받은 옛 나노(keeper_close_old one · K2) ·
후계 [레디] 를 받은 옛 역할 좌석(keeper_close retire_seat · K2b). 셋 다 재개 기록 먼저 → kill/close_bin → 완료 영수만(다음 카드 0).
대역 = keeper_world_r1812.World(실 core 장부 · 가짜 tmux · 주입 시계) + r2281 world(승계 옛 나노 · 실제 worktree 2개) +
test_keeper_round_60s.Rig(r2306 과 같은 손 · 가짜 subprocess.run — call 그물을 진짜로 지나간다).
실 tmux·실 명부·실 seat-resume·네트워크 0 · sleep 0. 기준판(갈래 없음) = ① ⑤ ⑥ Red · 변이는 사본에서만 + 변이마다 원본으로 같은 사례 1회 더.
시험 이름 = c01~c12 · c10b/c10c(⑩ 갈래) — 반례 번호는 각 함수 첫 줄에 그대로 적는다.
기존 시험 회귀(⑪)는 이 파일 안에서 다시 돌리지 않는다 — 파일 하나가 70초를 넘으면 70초 상한 러너가 rc 124 로 자른다.
⑪ 은 legacy_guard rc0 만 보고, 기존 9파일 재실행은 완료 보고의 «기준판 대조» 줄에 파일별 초로 적는다.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

FT2 = Path(__file__).resolve().parents[1]
if str(FT2 / "tests") not in sys.path:
    sys.path.insert(0, str(FT2 / "tests"))
TEAM, UUID = "harness", "0b9e2c1a-7d4f-4e21-9a3b-5c6d7e8f9012"
IDLE, STOP = "✻ Brewed for 3s\n❯ ", {"reason": "정지"}
DONE, SEAT, NEW, CLOSE = "· 정지 중 닫기", "biz-t1-arch-x#0", "biz-t1-arch-x#1", "/r2421/ft-seat-close.sh"
KP, KC, KO, KS = ("adapters/pi/keeper.py", "adapters/pi/keeper_close.py",
                  "adapters/pi/keeper_close_old.py", "adapters/pi/keeper_settle.py")


def _mod(name, alias):
    spec = importlib.util.spec_from_file_location(alias, str(Path(__file__).with_name(name)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kw = _mod("keeper_world_r1812.py", "r2421_world")
CO = _mod("test_pi_keeper_close_old_r2281.py", "r2421_closeold")
RG = _mod("test_keeper_round_60s.py", "r2421_rig")


def world(tmp, mp, ft2=kw.FT2):
    """r1812 World + 재개 기록 폴더를 임시로(실 ~/.claude/state/seat-resume 쓰기 0)."""
    tmp.mkdir(parents=True, exist_ok=True)
    w = kw.World(tmp, mp, ft2)
    w.env["FT2_SEAT_RESUME_DIR"] = str(tmp / "resume")
    return w


def started(w, work, pane=IDLE, age=7200, turn="stop", sha=True, card=True):
    """착지 줄 참(sha=False = 착지 줄 없음) 나노 1석(alive) — intent worktree 를 keeper roots 안으로 옮기고 Pi jsonl 1개(무활동 age초)."""
    w.enable()
    if card:
        w.card(work, w.pack_sha() if sha else None)
    holder = w.work(work, done=True, alive=True, pane=pane, turn=turn)
    tree = w.root / ".fable-team" / "teams" / TEAM / "worktrees" / ("%s@a1" % work)
    tree.mkdir(parents=True, exist_ok=True)
    kw._put(w.runtime() / "launch" / ("%s@a1.intent" % work),
            {"FT2_HOLDER": holder, "state": "opened", "worktree": str(tree), "at": "2026-01-01T00:00:00"})
    log = Path(w.env["FT2_PI_SESSIONS"]) / ("--%s--" % str(tree).strip("/").replace("/", "-")) / ("2026-11-13T00-00-00-000Z_%s.jsonl" % UUID)
    rows = [{"type": "session"}, {"type": "model_change", "modelId": "opus-5-5"},
            {"type": "message", "message": {"role": "assistant", "stopReason": turn}}]
    kw._put(log, "".join(json.dumps(x) + "\n" for x in rows))
    os.utime(log, (w.t - age, w.t - age))
    return holder


def halt(w, body=None):
    """정지 상태 — r1812 World 는 상태 파일(가짜 판정기가 읽는다) · r2465 부터 Rig 는 판정기 값(w.judge)으로 세운다."""
    root = w.state if isinstance(w.state, Path) else w.root / ".fable-team" / "state"
    kw._put(root / "ALL_STOP.json", body if isinstance(body, str) else json.dumps(STOP if body is None else body))
    if hasattr(w, "judge"):   # Rig — 파일을 읽는 코드가 없다(판정기 대역이 유일한 입력)
        w.judge = ({"state": "hard", "except": [], "since": None, "why": "깨짐"} if isinstance(body, str)
                   else {"state": "stop", "except": [], "since": 1794000500, "why": "시험"})


def resume_rec(w, seat):
    path = Path(w.env["FT2_SEAT_RESUME_DIR"]) / (seat + ".json")
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def killed(w):
    return [a[-1] for a in w.tmux("kill-session")]


def stopline(lines):
    return [x for x in lines if x.endswith(DONE)]


def kcmod(k):
    return k.close.__globals__["keeper_next"]   # keeper_close 모듈의 keeper_next(다음 카드 길)


# ── ①~④ K1 — 착지 나노 ────────────────────────────────────────────────────
def c1(tmp, mp, ft2=kw.FT2):
    w = world(tmp, mp, ft2)
    holder = started(w, "r9421")
    halt(w)
    lines = w.round()
    doc = resume_rec(w, holder)
    assert killed(w) == ["=" + holder] and w.kinds("close_receipt") == 1, lines
    assert doc and doc["name"] == holder and doc["uuid"] == UUID and doc["retired_by"] == holder, doc
    assert doc["binding"]["source"] == "ft2-keeper-stop-close", doc
    assert [x for x in stopline(lines) if x.startswith("CLOSED-")], lines
    assert not [x for x in lines if x.startswith("예정 LANDED")], lines


def c2(tmp, mp, ft2=kw.FT2):
    w = world(tmp, mp, ft2)
    started(w, "r9422")
    halt(w)
    kw._put(w.env["FT2_SEAT_RESUME_DIR"], "폴더 자리에 일반 파일")   # 재개 기록 쓰기 실패 대역
    lines = w.round()
    assert killed(w) == [] and w.kinds("close_receipt") == 0, lines
    assert [x for x in lines if x.startswith("판정 불가") and "재개 기록" in x], lines


def c3(tmp, mp, ft2=kw.FT2):
    w = world(tmp, mp, ft2)
    holder = started(w, "r9423")
    halt(w)
    k = w.keeper()
    calls, kc, real = [], kcmod(k), kcmod(k).close
    kc.close = lambda kk, *a: (calls.append(a), real(kk, *a))[1]
    lines = w.round(k)
    state = kc.ft2_state(k, TEAM) or {}
    assert calls == [] and killed(w) == ["=" + holder] and w.kinds("close_receipt") == 1, (calls, lines)
    assert (state.get("close_receipts") or {}).get("keeper:r9423@a1", {}).get("next") is None, state.get("close_receipts")


def c4(tmp, mp, ft2=kw.FT2):
    w = world(tmp, mp, ft2)
    started(w, "r9424", age=60)   # 유휴 문턱(300초) 안
    halt(w)
    lines = w.round()
    assert killed(w) == [] and w.kinds("close_receipt") == 0 and not stopline(lines), lines


# ── ⑤ K2 — 후계가 받은 옛 나노(승계) ───────────────────────────────────────
def c5(tmp, mp, ft2=kw.FT2):
    tmp.mkdir(parents=True, exist_ok=True)
    w = CO.world(tmp, mp, ft2)
    halt(w)
    lines = w.round()
    doc = CO.rec(w)
    assert CO.kills(w) == ["=" + CO.S] and [x for x in stopline(lines) if x.startswith("CLOSED-SUCCEEDED")], lines
    assert not [x for x in lines if x.startswith("예정 CLOSED-SUCCEEDED")], lines
    assert doc and doc["uuid"] == CO.UUID and doc["retired_by"] == CO.H, doc


# ── ⑥⑦⑧ K2b·K3 — retire_seat + call 그물 ─────────────────────────────────
def rig(tmp, ft2=kw.FT2, ready=True, idle=True, stopped=True):
    """r2306 과 같은 손 — 명부 1좌석(역할 arch · 후계 있음) · 단계는 스텁 · close_bin 호출은 진짜 call 그물을 지난다."""
    tmp.mkdir(parents=True, exist_ok=True)
    w = RG.Rig(tmp, None if ft2 == kw.FT2 else ft2)
    k = w.k
    w.verdicts = []
    del k.retired   # Rig 손잡이 → 진짜 retired()
    k.close_bin = CLOSE
    k.teams, k.alive_sessions = (lambda: []), (lambda: {SEAT})
    k.rosters = lambda: [("/r2421/seats-t1.json", {SEAT: {"_replaced_by": NEW, "role": "arch"}})]
    k.closed_seats, k.outsiders = (lambda: set()), (lambda alive, known: None)
    k.seat_kind, k.seat_turn = (lambda seat, row: "arch"), (lambda seat: ())
    k.ready_seen, k.keep_gate = (lambda new, seat: ready), (lambda seat, new, alive: "")
    k.look, k.idle = (lambda *a: "REST"), (lambda *a: idle)
    k.verdict = lambda *a: (w.verdicts.append(a[:5]), True)[1]
    if stopped:
        halt(w)
    return w


def closers(w):
    return [c for c in w.calls if c[:2] == ["bash", CLOSE]]


def c6(tmp, mp, ft2=kw.FT2):
    w = rig(tmp, ft2)
    lines = w.round()
    assert w.k.halt and w.k.halt_clean and closers(w), lines
    assert [x for x in stopline(lines) if x.startswith("CLOSED-SEAT seats-t1")], lines
    assert not [a for a in w.verdicts if a[3] == "예정 LANDED"], w.verdicts


def c7(tmp, mp, ft2=kw.FT2):
    w = rig(tmp, ft2, ready=False)
    lines = w.round()
    assert closers(w) == [] and [a for a in w.verdicts if a[3:5] == ("WORKING", "ready-wait")], (w.verdicts, lines)
    assert not stopline(lines), lines


def c8(tmp, mp, ft2=kw.FT2):
    """⑧ K3 — 범위 안 = 정확한 두 꼴(kill-session 그 석 · retire close_bin 꼴)만 통과. 실행파일·추가 옵션을 바꾸면 막힌다(DA#56 H1 고정)."""
    k = rig(tmp, ft2).k
    k.halt, k.halt_clean = True, True
    retire = ["bash", CLOSE, SEAT, "--reason", "retire -> x", "--seats", "/r2421/seats-t1.json", "--defer-press"]
    assert k.call([k.tmux, "kill-session", "-t", "=" + SEAT])[0] is None   # 범위 밖 kill = 막힘
    with k.stop_close_scope(SEAT):
        assert k.call([k.tmux, "kill-session", "-t", "=" + SEAT])[0] == 0   # 범위 안 그 석 = 통과
        assert k.call([k.tmux, "kill-session", "-t", "=" + SEAT, "-a"])[0] is None   # H1ⓐ 추가 옵션(-a = 다른 세션까지) = 막힘
        assert k.call([k.tmux, "kill-session", "-t", "=biz-t1-arch-y#0"])[0] is None   # 다른 석 = 막힘
        assert k.call([k.tmux, "send-keys", "-t", "=" + SEAT + ":", "x"])[0] is None   # send-keys = 범위 안도 막힘
        assert k.call([sys.executable, "launch.py"])[0] is None   # 새 열기 = 범위 안도 막힘
        assert k.call([sys.executable, CLOSE, SEAT])[0] is None   # H1ⓑ close_bin 을 다른 실행파일로 = 막힘
        assert k.call(["bash", CLOSE, "biz-t1-arch-y#0", "--reason", "x", "--seats", "s", "--defer-press"])[0] is None   # close_bin 다른 석 = 막힘
        assert k.call(["bash", CLOSE, SEAT])[0] is None   # retire 꼴 아님(옵션 0) = 막힘
        assert k.call(retire)[0] == 0   # retire 꼴 그대로 = 통과
        with k.stop_close_scope("biz-t1-arch-y#0"):   # 중첩 = 안 값
            assert k.stop_close == "biz-t1-arch-y#0"
            assert k.call([k.tmux, "kill-session", "-t", "=" + SEAT])[0] is None
            with pytest.raises(RuntimeError):
                with k.stop_close_scope("biz-t1-arch-z#0"):
                    raise RuntimeError()
            assert k.stop_close == "biz-t1-arch-y#0"   # 예외에도 앞 값 복구
        assert k.stop_close == SEAT   # 중첩 끝 = 앞 값 복구
    assert k.stop_close == "" and k.call([k.tmux, "kill-session", "-t", "=" + SEAT])[0] is None
    assert k.halt   # halt 값은 안 바꾼다


# ── ⑨⑩⑫ K4·K5 ────────────────────────────────────────────────────────────
def c9(tmp, mp, ft2=kw.FT2):
    """⑨ 착지 근거가 없으면(카드 있음 · 착지 줄 0 / 끝(superseded) 카드) 정지 중에도 지금 결과 그대로(kill 0 · 영수 0)."""
    w = world(tmp, mp, ft2)
    holder = started(w, "r9429", sha=False)   # NOLINE
    halt(w)
    lines = w.round()
    assert killed(w) == [] and w.kinds("close_receipt") == 0 and not stopline(lines), lines
    assert [x for x in lines if holder in x and "착지 줄 없음" in x], lines
    w2 = world(tmp / "b" / "w", mp, ft2)   # 끝(superseded) 카드 = ending 길(K4 끝=손 0) → «예정 LANDED» 그대로
    w2.card("r9439", None, stage="아카이브")
    held = started(w2, "r9439", card=False)
    halt(w2)
    lines2 = w2.round()
    assert killed(w2) == [] and w2.kinds("close_receipt") == 0, lines2
    assert [x for x in lines2 if x.startswith("예정 LANDED") and held in x], lines2


def c10(tmp, mp, ft2=kw.FT2):
    w = world(tmp, mp, ft2)
    holder = started(w, "r9430")   # 정지 아님 = 같은 입력에서 지금 길(kill + keeper_next.close)
    lines = w.round()
    assert killed(w) == ["=" + holder] and w.kinds("close_receipt") == 1 and not stopline(lines), lines


def c10b(tmp, mp, ft2=kw.FT2):
    tmp.mkdir(parents=True, exist_ok=True)
    w = CO.world(tmp, mp, ft2)   # 정지 아님 = 옛 나노 지금 길(덧말 0)
    CO.closed(w, w.round())


def c10c(tmp, mp, ft2=kw.FT2):
    w = rig(tmp, ft2, stopped=False)   # 정지 아님 = retire 지금 길(덧말 0)
    lines = w.round()
    close = [x for x in lines if x.startswith("CLOSED-SEAT seats-t1")]
    assert close and not [x for x in close if x.endswith(DONE)], lines


def c12(tmp, mp, ft2=kw.FT2):
    w = world(tmp, mp, ft2)
    started(w, "r9432")
    halt(w, "{깨짐")   # halt True · 정상 정지 근거 False
    lines = w.round()
    assert killed(w) == [] and w.kinds("close_receipt") == 0, lines
    assert [x for x in lines if x.startswith("예정 LANDED")], lines


# ── ⑪ 회귀 — legacy_guard rc0 ──────────────────────────────────────────────
# 기존 시험 재실행(r2055 3파일 · r2401 · keeper_close·close_old·retire)은 이 파일 안에서 돌리지 않는다 —
# 파일 하나가 70초를 넘으면 70초 상한 러너가 rc 124 로 자른다. 완료 보고의 «기준판 대조» 줄에 파일별 초로 적는다.
def c11(tmp, mp, ft2=kw.FT2):
    got = subprocess.run([sys.executable, str(FT2 / "tools" / "legacy_guard.py")], capture_output=True, text=True, timeout=70)
    assert got.returncode == 0, got.stdout[-1500:] + got.stderr[-500:]


CASES = {"①": c1, "②": c2, "③": c3, "④": c4, "⑤": c5, "⑥": c6, "⑦": c7, "⑧": c8, "⑨": c9,
         "⑩": c10, "⑩ⓑ": c10b, "⑩ⓒ": c10c, "⑪": c11, "⑫": c12}
IDS = ["c01", "c02", "c03", "c04", "c05", "c06", "c07", "c08", "c09", "c10", "c10b", "c10c",
       "c11", "c12"]
MUTANTS = {
    "M1": (KC, '        if seen == "alive" and self.halt and not stop:', '        if seen == "alive" and self.halt:', "①"),
    "M2": (KC, "            if stop and not self.stop_close_resume(team, work, holder, intent):",
           "            if stop and not (self.stop_close_resume(team, work, holder, intent) or True):", "②"),
    "M3": (KC, "        elif stop:   # r2421 K1 — 정지 중 = 완료 영수만(다음 카드 고르기 0 · submit·next_work·reconcile 0)\n            self.receipt(team, work, attempt, holder, gen)",
           "        elif stop:\n            keeper_next.close(self, team, work, attempt, holder, gen)", "③"),
    "M4": (KO, "        stop = k.halt and k.halt_clean   # r2421 K2·K5 — 정상 정지 근거가 있으면 닫는다",
           "        stop = False   # M4", "⑤"),
    "M5": (KC, "        stop = self.halt and self.halt_clean   # r2421 K2b·K5 — 정상 정지 근거가 있으면 닫는다",
           "        stop = False   # M5", "⑥"),
    "M6": (KP, '        if argv == [self.tmux, "kill-session", "-t", "=" + seat]:', '        if argv[:2] == [self.tmux, "kill-session"]:', "⑧"),
    "M7": (KP, "        prev, self.stop_close = self.stop_close, seat\n        try:\n            yield\n        finally:\n            self.stop_close = prev",
           "        prev, self.stop_close = self.stop_close, seat\n        yield\n        self.stop_close = prev", "⑧"),
    "M8": (KC, "        stop = self.halt and self.halt_clean and bool(landed_close or wide)",
           "        stop = self.halt and self.halt_clean", "⑨"),
    "M9": (KS, "        self.halt_clean, self.stop_except, self.stop_since = False, set(), None",
           "        self.halt_clean, self.stop_except, self.stop_since = True, set(), None", "⑫"),
}


@pytest.mark.parametrize("name", list(CASES), ids=IDS)
def test_case(name, tmp_path, monkeypatch):
    CASES[name](tmp_path, monkeypatch)


@pytest.mark.parametrize("name", list(MUTANTS))
def test_mutant(name, tmp_path, monkeypatch):
    rel, old, new, case = MUTANTS[name]
    tree = tmp_path / "m" / "ft2"
    shutil.copytree(FT2, tree, ignore=shutil.ignore_patterns("tests", "__pycache__"))
    text = (tree / rel).read_text(encoding="utf-8")
    assert text.count(old) == 1, (name, old)
    (tree / rel).write_text(text.replace(old, new), encoding="utf-8")
    with pytest.raises(AssertionError):
        CASES[case](tmp_path / "m" / "w", monkeypatch, tree)
    CASES[case](tmp_path / "o" / "w", monkeypatch)   # 원본 대조 = 같은 사례가 원본에서는 통과(반대 결과)
