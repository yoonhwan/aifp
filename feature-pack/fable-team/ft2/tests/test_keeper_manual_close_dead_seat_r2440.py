"""r2440 ft2 keeper — 수동 닫기(`keeper --close-seat`)가 tmux 세션이 이미 없는 석을 닫는다 · 카드 반례 ①~⑭ · 변이 M1~M7.

까닭 = 죽은 석은 `display-message #{session_attached}` 가 rc 0 빈 줄이라 «unknown · 0» 이 되고, 손의 ① 관문이 «free 아님 = 거절» 이라
닫는 손이 없다(11-22 15:22 cfo 실사건 · rc 4). 부재 판독기(has-session 1회)가 absent 를 내면 죽은 세션 갈래로 간다.

대역 = r1812 keeper_world(실제 core 장부 · 가짜 tmux · 임시 리포) + 이 파일이 덮어쓴 가짜 tmux(has-session 의 출력·rc·재확인 뒤 alive 를 정한다) +
실제 git worktree 1개(intent worktree · 재개 기록 요건) + planner 판정 원장(origin/main) + 우편 로그 + 자율 모드 스텁.
실 tmux·실 원장·sleep 0. 부르는 길 = 실제 `core/cli.py keeper --close-seat …`(⑪⑫ 만 in-process 로 판독을 가짜로 바꾼다).
사례 묶음과 변이 묶음을 가른 까닭 = 시험 1개 70초 안(변이는 사본 1개 + 사례 1~2개).
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import keeper_world_r1812 as kw

TEAM, W = kw.TEAM, "r2440"
S = "biz-harness-nano-r2440-t#0"
OTHER = "biz-harness-nano-r2440-other#1"
DESK = "biz-planner-desk-pi#7"
N, SEQ, UUID = "4600", "12345", "0b9e2c1a-7d4f-4e21-9a3b-5c6d7e8f9012"
REASON = "판정 원장 행 · tmux 세션이 죽은 ft2 나노 1석 정리"
IDLE = "✻ Brewed for 3s\n❯ "
ROW = "- **%s** %%s #%s 수동 닫기 나노 1석(r2440 · 자율 ON A18) · 유휴" % (N, SEQ)
MAIL = "[수동 닫기 승인] %s\n%s 1석 정리 · 유휴" % (W, W)
SINCE = 1793990000                                    # ⓐ ALL_STOP since(⑬ · 죽은 석 = 세션 생성 시각 판독 불가)
TAIL = " · 세션 없음(kill 0)"                            # K5 끝 줄 꼬리 덧말
HOW = (" · 다시 열기 = 카드에 «- 재개: <시각> · PR #<번호> · head <40자> · 가지 nano/<work>» 한 줄"
       "(원장이 남아 있으면 ft-card-assign-watch.sh record <카드> clear <사유>)")   # r2573 — 끝 줄 꼬리에 더하는 «다시 여는 법»(계기가 §park=already 도)
TARGET = kw.FT2                                       # 쓰는 팩(변이 시험만 사본으로 바꾼다)
CASE = "①"                                            # 변이 시험의 사례 표시(아래 CASES 키)

# 가짜 tmux 덮개 — has-session 만 가로채 «can't find session»·«no server running»·rc·재확인 뒤 alive 를 정한다(그 밖 동사 = r1812 대역 그대로).
WRAP = r'''#!__PY__
import json, os, sys
st, a = os.environ["FAKE_TMUX"], sys.argv[1:]
name = sys.argv[-1].lstrip("=").rstrip(":")
d = json.load(open(st))
if a[:1] == ["has-session"]:
    log = st + ".log"
    seen = sum(1 for x in open(log) if '"has-session"' in x) + 1 if os.path.exists(log) else 1
    open(log, "a").write(json.dumps(a) + "\n")
    flip = d.get("has_flip")                      # 이 번호부터 alive 로 답한다(⑨ 재확인에서 그새 살아남)
    if name in d["alive"] or (flip and seen >= int(flip)):
        sys.exit(0)
    sys.stderr.write(d.get("has_err") or ("can't find session: %s\n" % name))
    sys.exit(int(d.get("has_rc", 1)))
os.execv(sys.executable, [sys.executable, os.environ["FAKE_TMUX_REAL"]] + a)
'''


def git(cwd, *a):
    return kw._git(cwd, *a)


def tree(w):
    return w.root / ".fable-team" / "teams" / TEAM / "worktrees" / (W + "@a1")


def world(tmp, mp, ft2=None, alive=False, att=0, pane=IDLE, files=1, dirty=False, latest=S, flip=None,
          has_rc=1, has_err="", stop=False, since=None, seat=S, row=ROW, mail=MAIL):
    """일 1개 = submit→assign(seat)→deliver · intent(seat) · 실제 worktree · pi jsonl files개 · tmux 세션은 기본 «죽음».
    alive=True = 지금과 같은 길(③④) · has_rc·has_err = has-session 답(① rc1 «can't find session» · ② rc1 «no server running» · ⑤ 그 밖)."""
    w = kw.World(tmp, mp, ft2=ft2 or TARGET)
    for key, val in (("user.email", "t@t"), ("user.name", "t"), ("commit.gpgsign", "false")):
        git(w.root, "config", key, val)
    kw._put(w.state / "ft20-switch" / (TEAM + ".json"), "{}")
    git(w.root, "worktree", "add", "-q", "--detach", str(tree(w)), git(w.root, "rev-parse", "HEAD"))
    steps = [["submit", "--command", "c-" + W, "--body", "b", "--work", W], ["assign", "--work", W, "--holder", seat, "--evidence", "v1,v2"],
             ["deliver", "--work", W]]
    if latest != seat:
        steps += [["assign", "--work", W, "--holder", OTHER, "--evidence", "v1,v2"], ["deliver", "--work", W]]
    for argv in steps:
        out, rc = w.CLI.run(argv + ["--root", str(w.root), "--team", TEAM])
        assert rc == 0, out
    kw._put(w.runtime() / "launch" / ("%s@a1.intent" % W), {"FT2_HOLDER": seat, "state": "opened", "worktree": str(tree(w)), "at": "2026-01-01T00:00:00"})
    folder = Path(w.env["FT2_PI_SESSIONS"]) / ("--%s--" % str(tree(w)).strip("/").replace("/", "-"))
    for i in range(files):
        log = folder / ("2026-11-01_%s.jsonl" % (UUID if i == 0 else "x%d" % i))
        kw._put(log, '{"type": "session", "id": "%s"}\n' % UUID), os.utime(log, (w.t - 3600 + i * 600, w.t - 3600 + i * 600))
    if dirty:
        kw._put(tree(w) / "wip.txt", "미커밋 1개\n")
    kw._put(w.root / "design" / "teams" / "planner" / "VERDICTS-planner-24-r2440.md", "# 판정 원장\n" + (row % seat) + "\n")
    git(w.root, "add", "-A"), git(w.root, "commit", "-qm", "ledger")
    git(w.root, "update-ref", "refs/remotes/origin/main", "HEAD")
    kw._put(w.root / ".fable-team" / "comm" / "mailbox.log.jsonl", json.dumps({"seq": SEQ, "from": DESK, "to": seat, "body": mail}, ensure_ascii=False) + "\n")
    stub = os.path.join(w.root, ".fable-team", "bin", "ft-autonomy.sh")
    kw._put(stub, "#!/bin/sh\necho on\n"), Path(stub).chmod(0o755)
    if stop:
        kw._put(w.state / "ALL_STOP.json", {"reason": "정지"} if since is None else {"reason": "정지", "since": since})
    d = json.loads(w.tm.read_text(encoding="utf-8"))
    d.update(alive=[seat] if alive else [], pane={seat: pane}, att={seat: att}, has_rc=has_rc, has_err=has_err)
    if flip:
        d["has_flip"] = flip
    kw._put(w.tm, d)
    real = Path(w.env["FT_TMUX"]).with_suffix(".real")
    kw._put(real, kw.TMUX.replace("__PY__", sys.executable)), real.chmod(0o755)
    kw._put(w.env["FT_TMUX"], WRAP.replace("__PY__", sys.executable)), Path(w.env["FT_TMUX"]).chmod(0o755)
    w.env["FAKE_TMUX_REAL"] = str(real)
    w.rs = tmp / "resume"
    w.env["FT2_SEAT_RESUME_DIR"] = str(w.rs)
    return w


def run(w, seat=S, n=N, approve=None, reason=REASON):
    """실제 CLI 갈래 = `core/cli.py keeper --close-seat …` → (줄 목록, rc)."""
    done = subprocess.run([sys.executable, str(w.ft2 / "core" / "cli.py"), "keeper", "--root", str(w.root), "--close-seat", seat,
                           "--verdict", n, "--approve", approve or ("%s #%s" % (DESK, SEQ)), "--reason", reason],
                          capture_output=True, text=True, env=w.env, cwd=str(w.root), timeout=70)
    return [x for x in done.stdout.strip().splitlines() if x], done.returncode


def mc():
    """이 시험 대상 모듈(TARGET 팩) — ⑪⑫ 는 in-process 로 장부 판독을 가짜로 바꿔 잰다."""
    path = Path(TARGET) / "adapters" / "pi" / "keeper_manual_close.py"
    spec = importlib.util.spec_from_file_location("ft2_manual_r2440", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def calls(w, verb):
    return w.tmux(verb)


def attached_calls(w):
    return [a for a in w.tmux("display-message") if "#{session_attached}" in a[-1]]


def rec(w):
    path = w.rs / (S + ".json")
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def one(lines, head):
    got = [x for x in lines if x.startswith(head)]
    assert len(got) == 1, lines
    return got[0]


def no_touch(w):
    """닫는 손 0 = kill 0 · 재개 기록 0 · park 0."""
    assert calls(w, "kill-session") == [] and rec(w) is None, (calls(w, "kill-session"), rec(w))
    assert w.kinds("parked") == 0, w.journal()


def untouched(w):
    """죽은 석 갈래의 손 0 = no_touch + 사람 화면 판독 0(K2)."""
    no_touch(w)
    assert attached_calls(w) == [], w.tmux("display-message")


def owned(w):
    """park 1 = core 장부에서 그 일 owner 가 풀렸다(r2401 ① 과 같은 판독)."""
    proj, prc = w.CLI.run(["project", "--root", str(w.root), "--team", TEAM])
    row = (proj.get("holders") or {}).get(S) or {}
    assert prc == 0 and row.get("free") is True and W not in json.dumps(row, ensure_ascii=False), proj.get("holders")


def case01(tmp, mp):
    """① 실사건 꼴: rc 0 · 끝 줄 «CLOSED-MANUAL … park=done … 세션 없음(kill 0)» · kill 0 · capture-pane 0 · 사람 화면 판독 0 · 기록 1 · park 1."""
    w = world(tmp, mp)
    lines, rc = run(w)
    assert rc == 0, lines
    assert one(lines, "CLOSED-MANUAL") == "CLOSED-MANUAL %s %s 판정 %s %s #%s park=done reason=%s%s%s" % (TEAM, S, N, DESK, SEQ, REASON, TAIL, HOW), lines
    assert calls(w, "kill-session") == [] and calls(w, "capture-pane") == [] and attached_calls(w) == [], lines
    doc = rec(w)
    assert doc["name"] == S and doc["retired_by"] == DESK and doc["binding"]["source"] == "ft2-manual-close", doc
    owned(w)


def case02(tmp, mp):
    """② tmux 서버 없음(has-session rc1 «no server running») → ① 과 같은 결과."""
    w = world(tmp, mp, has_err="no server running on /tmp/tmux-501/default\n")
    lines, rc = run(w)
    assert rc == 0, lines
    assert one(lines, "CLOSED-MANUAL").endswith("park=done reason=%s%s%s" % (REASON, TAIL, HOW)), lines
    assert calls(w, "kill-session") == [] and rec(w) is not None, lines
    owned(w)


def case03(tmp, mp):
    """③ 세션 살아 있음(has-session rc0) · 사람 화면 0 → 지금 손 그대로 = kill 1 · 끝 줄 덧말 없음(기준판과 같은 줄)."""
    w = world(tmp, mp, alive=True)
    lines, rc = run(w)
    assert rc == 0, lines
    assert one(lines, "CLOSED-MANUAL") == "CLOSED-MANUAL %s %s 판정 %s %s #%s park=done reason=%s%s" % (TEAM, S, N, DESK, SEQ, REASON, HOW), lines
    assert calls(w, "kill-session") == [["kill-session", "-t", "=" + S]], lines
    assert rec(w) is not None, lines
    owned(w)


def case05(tmp, mp):
    """⑤ tmux 판정 불가(rc2 · 또는 rc1 다른 글자) + 사람 화면 못 읽음 → REJECT attached rc 4 · 기록 0 · park 0(기준판과 같음)."""
    for i, extra in enumerate(({"has_rc": 2}, {"has_err": "error connecting to /tmp/tmux-501/default (No such file or directory)\n"})):
        w = world(Path(tmp) / ("a%d" % i), mp, **extra)
        lines, rc = run(w)
        assert rc == 4 and one(lines, "REJECT attached").startswith("REJECT attached %s %s 판정 %s · unknown · 0" % (TEAM, S, N)), lines
        no_touch(w)


def case06(tmp, mp):
    """⑥ 죽은 세션 + worktree 미커밋 → REJECT dirty rc 8 · 기록 0 · kill 0 · park 0(③ dirty 검사 그대로)."""
    w = world(tmp, mp, dirty=True)
    lines, rc = run(w)
    assert rc == 8 and "미커밋 변경 있음" in one(lines, "REJECT dirty"), lines
    untouched(w)


def case07(tmp, mp):
    """⑦ 죽은 세션 + pi 세션 기록 0개 → rc 0 · 재개 기록 0 · park 1 · 끝 줄 덧말."""
    w = world(tmp, mp, files=0)
    lines, rc = run(w)
    assert rc == 0 and one(lines, "CLOSED-MANUAL").endswith("park=done reason=%s%s%s" % (REASON, TAIL, HOW)), lines
    assert rec(w) is None, lines
    owned(w)


def case09(tmp, mp):
    """⑨ 첫 판독 absent → park 직전 재확인에서 alive → REJECT kill … 부재 확인 없음 rc 6 · park 0 · kill 0."""
    w = world(tmp, mp, flip=2)
    lines, rc = run(w)
    assert rc == 6 and "부재 확인 없음(alive)" in one(lines, "REJECT kill"), lines
    assert calls(w, "kill-session") == [] and w.kinds("parked") == 0, lines


CASES = {"①": case01, "②": case02, "③": case03, "⑤": case05, "⑥": case06, "⑦": case07, "⑨": case09}


def test_case01_실사건_꼴_죽은_석_닫기(tmp_path, monkeypatch):
    case01(tmp_path, monkeypatch)


def test_case02_tmux_서버_없음(tmp_path, monkeypatch):
    case02(tmp_path, monkeypatch)


def test_case03_살아_있는_세션은_지금_그대로(tmp_path, monkeypatch):
    case03(tmp_path, monkeypatch)


def test_case04_살아_있는_세션_사람_화면(tmp_path, monkeypatch):
    """④ 세션 살아 있음 · 사람 화면 1 → «REJECT attached» rc 4(기준판과 같음) · kill 0 · 기록 0 · park 0."""
    w = world(tmp_path, monkeypatch, alive=True, att=1)
    lines, rc = run(w)
    assert rc == 4 and one(lines, "REJECT attached").endswith("attached 1 · 손 0"), lines
    no_touch(w)


def test_case05_tmux_판정_불가(tmp_path, monkeypatch):
    case05(tmp_path, monkeypatch)


def test_case06_죽은_세션_미커밋(tmp_path, monkeypatch):
    case06(tmp_path, monkeypatch)


def test_case07_죽은_세션_기록_0개(tmp_path, monkeypatch):
    case07(tmp_path, monkeypatch)


def test_case08_죽은_세션_기록_2개(tmp_path, monkeypatch):
    """⑧ 죽은 세션 + pi 세션 기록 2개 → 고친 시각이 가장 늦은 파일(x1)로 재개 기록 1 · rc 0."""
    w = world(tmp_path, monkeypatch, files=2)
    lines, rc = run(w)
    assert rc == 0, lines
    doc = rec(w)
    assert doc["uuid"] == "x1" and doc["jsonl"].endswith("2026-11-01_x1.jsonl") and doc["binding"]["source"] == "ft2-manual-close", doc
    owned(w)


def test_case09_재확인에서_살아남(tmp_path, monkeypatch):
    case09(tmp_path, monkeypatch)


def test_case10_최신_holder_아님(tmp_path, monkeypatch):
    """⑩ 죽은 세션 + 이 석이 최신 holder 아님 → park=none · rc 0(지금 규칙)."""
    w = world(tmp_path, monkeypatch, latest=OTHER)
    lines, rc = run(w)
    assert rc == 0 and one(lines, "CLOSED-MANUAL").endswith("park=none reason=%s%s%s" % (REASON, TAIL, HOW)), lines
    assert w.kinds("parked") == 0, w.journal()


def test_case11_장부_판독_실패(tmp_path, monkeypatch):
    """⑪ 장부 판독 실패 → REJECT 장부 rc 9 · 부재 판독 호출 0."""
    w = world(tmp_path, monkeypatch)
    module = mc()
    monkeypatch.setattr(module.endings, "latest", lambda *a: None)
    keeper = w.keeper()
    rc = module.run(keeper, S, N, "%s #%s" % (DESK, SEQ), REASON)
    assert rc == 9 and "장부 판독 실패" in one(keeper.lines, "REJECT 장부"), keeper.lines
    assert calls(w, "has-session") == [] and calls(w, "kill-session") == [] and rec(w) is None, keeper.lines


def test_case12_승인_줄이_틀림(tmp_path, monkeypatch):
    """⑫ 승인 줄이 틀림(#다른 seq) → 승인 관문 거절 rc 2 · 부재 판독 호출 0."""
    w = world(tmp_path, monkeypatch)
    keeper = w.keeper()
    rc = mc().run(keeper, S, N, "%s #99999" % DESK, REASON)
    assert rc == 2 and one(keeper.lines, "REJECT 승인"), keeper.lines
    assert calls(w, "has-session") == [] and calls(w, "kill-session") == [] and rec(w) is None, keeper.lines


def test_case13_정지_중_죽은_석(tmp_path, monkeypatch):
    """⑬ 정지 중 + 죽은 세션 → 지금처럼 거절(«세션 생성 시각 판독 불가») · park 0 · kill 0."""
    w = world(tmp_path, monkeypatch, stop=True, since=SINCE)
    lines, rc = run(w)
    assert rc == 2 and "세션 생성 시각 판독 불가" in one(lines, "REJECT 정지 중"), lines
    untouched(w)


def test_case14_회귀_기존_수동_닫기_사례(tmp_path, monkeypatch):
    """⑭ 회귀 — r2401·r2419 의 대표 사례 4개를 같은 팩에서 그대로 돌린다(살아 있는 석 길 · 사람 화면 · 정지) = 기준판과 같은 결과."""
    spec = importlib.util.spec_from_file_location("ft2_r2401_cases", str(Path(__file__).with_name("test_keeper_close_seat_r2401.py")))
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    for i, name in enumerate(("test_case01_소유있는_ft2나노_닫기", "test_case07_사람_화면과_일하는_중",
                              "test_case13_장부_판독_실패", "test_r2419_case01_정지_뒤에_뜬_석은_닫는다")):
        (tmp_path / ("r%d" % i)).mkdir(exist_ok=True)
        getattr(old, name)(tmp_path / ("r%d" % i), monkeypatch)


MUTANTS = {
    # 이름: (바꿀 글, 바꾼 글, 잡히는 사례)
    "M1": ("    if k.probe(seat) == \"absent\":\n        return dead_hands(k, team, work, seat, n, seat_ok, seq, reason, note, latest, intent)\n",
           "", ("①", "②")),                                    # 죽은 세션 갈래를 뗌 = 기준판 Red
    "M2": ("    if k.probe(seat) == \"absent\":", "    if k.probe(seat) != \"alive\":", ("⑤",)),   # 판정 불가도 죽은 세션으로 읽음
    "M3": ("    if rc:                                                 # ③ 그대로(미커밋·판독 실패 = REJECT dirty)",
           "    if rc and False:                                       # ③ 그대로(미커밋·판독 실패 = REJECT dirty)", ("⑥",)),   # dirty 검사 뗌
    "M4": ("    after = k.probe(seat)                                   # K4 — park 직전 부재 판독 1회 더(그새 살아났으면 닫지 않는다)",
           "    after = \"absent\"                                       # K4 — park 직전 부재 판독 1회 더(그새 살아났으면 닫지 않는다)", ("⑨",)),  # 재확인 뗌
    "M5": ("    k.call([k.tmux, \"kill-session\", \"-t\", \"=\" + seat])      # ⑤ 세션만 닫기 → 부재 확인",
           "    pass                                                   # ⑤ 세션만 닫기 → 부재 확인", ("③",)),   # 살아 있는 석도 kill 건너뜀
    "M6": ("    if not logs:\n        return \"\"", "    if not logs:\n        return \"jsonl 0개\"", ("⑦",)),   # 기록 0개를 거절로 읽음
    "M7": ("    park, rc = parked(k, team, work, seat, n, reason, latest)   # ⑥ 지금 규칙 그대로",
           "    park, rc = \"none\", 0                                        # ⑥ 지금 규칙 그대로", ("①",)),   # 죽은 갈래 park 뗌
}


@pytest.mark.parametrize("name", list(MUTANTS))
def test_mutant(name, tmp_path, monkeypatch):
    """변이 1칸 = ft2 사본에서 깬다: 잡는 사례가 FAIL · 원본(TARGET 팩)에서 같은 사례 1회 PASS(양성)."""
    global TARGET
    old, new, picked = MUTANTS[name]
    base = tmp_path / "base"
    shutil.copytree(kw.FT2, base, ignore=shutil.ignore_patterns("tests", "__pycache__"))
    text = (base / "adapters" / "pi" / "keeper_manual_close.py").read_text(encoding="utf-8")
    assert text.count(old) == 1, (name, text.count(old))
    (base / "adapters" / "pi" / "keeper_manual_close.py").write_text(text.replace(old, new), encoding="utf-8")
    TARGET = base
    try:
        for i, c in enumerate(picked):
            (tmp_path / ("m%d" % i)).mkdir(exist_ok=True)
            with pytest.raises(AssertionError):
                CASES[c](tmp_path / ("m%d" % i), monkeypatch)
    finally:
        TARGET = kw.FT2
    (tmp_path / "ok").mkdir(exist_ok=True)
    CASES[picked[0]](tmp_path / "ok", monkeypatch)
