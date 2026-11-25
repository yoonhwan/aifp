"""r2535 park 유휴 5분 — 카드 반례 ①~⑳ · 변이 M1~M15 (카드 design/harness/indices/대기/r2535-nano-hands-zero-close-before-land.md).

대역 = keeper_world_r1812(임시 root · 두 ref · 가짜 tmux) + 닫는 사례만 실 임시 nano worktree(clone · push) + 가짜 mbox(`peek --rows`).
실 tmux · 실 프로세스 종료 · 실 쪽지 0 · sleep 0(시계 = 주입 w.t) · 70초 안 · 시험 1개 = 한 사례(변이는 그 사례가 Red 인지까지).
기준판(팩 origin/main 8d8128b0 · PARK_IDLE 3600) = ① ③④⑤⑦⑧⑨⑬⑭⑮⑯⑰⑲⑳ 이 Red · ②⑥⑩⑫ 는 지금 길 그대로(양성 회귀).
★r2596 뒤 = PARK_IDLE 600★ — 5분 기대값을 고쳐 적은 사례 = ①②③④⑤⑨⑭⑰⑱(좌석 나이 301→571 = 두 바퀴 끝 601초 · ② 는 301초 그대로 = 5분에 안 닫힌다) 과 ① 의 «무활동 5분»→«10분» · 판정 글자·케이스 수는 그대로.
"""
import datetime
import importlib.util
import json
import os
import shutil
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("keeper_world_r2535", str(Path(__file__).with_name("keeper_world_r1812.py")))
kw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kw)
FT2, T0, TEAM, IDLE_PANE = kw.FT2, kw.T0, kw.TEAM, "✻ Brewed for 3s\n❯ "
KS = "adapters/pi/keeper_settle.py"
NOTE = "adapters/pi/keeper_park_note.py"
MBOX = ('#!/bin/sh\nprintf "%s\\n" "$*" >> "$0.log"\n'
        'if [ "$1" = peek ] && [ "$3" = "--rows" ]; then n=$(cat "$0.pending" 2>/dev/null || echo 0); '
        'echo "pending=$n scanned=1 lineage=0"; [ "$n" = 0 ] || cat "$0.rows" 2>/dev/null; exit 0; fi\n'
        'if [ "$1" = peek ]; then echo "pending=$(cat "$0.pending" 2>/dev/null || echo 0) scanned=1"; exit "$(cat "$0.peekrc" 2>/dev/null || echo 0)"; fi\n'
        'echo "STUB $1"\nexit "$(cat "$0.rc" 2>/dev/null || echo 0)"\n')
CHAIN = [(100, 1, 0.0, "zsh"), (101, 100, 0.0, "npm"), (102, 101, 0.0, "node"), (103, 102, None, "pi"), (200, 1, 2.0, "other")]


def world(tmp, mp, ft2=FT2):
    """임시 root · 가짜 tmux·mbox · 주입 시계 · 손잡이 없음(= PARK_IDLE 600 · r2596)."""
    w = kw.World(tmp, mp, ft2)
    kw._put(w.mbox, MBOX), w.mbox.chmod(0o755)
    w.env.update(HOME=str(tmp / "home"), FT2_TEAM_NANO_MAX="8", FT2_MAILBOX_DIR=str(tmp / "comm"), FT2_SEAT_RESUME_DIR=str(tmp / "resume"),
                 GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="core.quotepath", GIT_CONFIG_VALUE_0="false")
    w.env.pop("FT2_PARK_IDLE_S", None)
    w.enable()
    return w


def card(w, work, **opt):
    """카드 1장 — main ref 한 곳만(양쪽 ref 는 시험 시간만 두 배 · keeper 는 어느 ref 든 읽는다)."""
    opt.setdefault("refs", ("main",))
    return w.card(work, **opt)


def git(cwd, *a):
    return kw._git(cwd, *a)


def nano(w, work, res="", alive=True, state="opened", turn="stop", age=7200, pane=IDLE_PANE, light=False, dirty=False, push=True,
         body=None, holder=None, files=None):
    """나노 1석 = 접수 → 배정 → 전달 · worktree(light = 폴더만 · 그 밖 = clone·커밋·push) · intent · Pi jsonl(mtime = 시계 − age).
    turn = "stop" | "toolUse" | "broken"(마지막 줄 깨짐 = stop None) | None(jsonl 없음)."""
    holder, res = holder or "biz-%s-nano-%s#0" % (TEAM, work), res or "R-" + work
    for argv in (["submit", "--command", "c-" + work, "--body", body or "본문-" + work, "--work", work],
                 ["assign", "--work", work, "--holder", holder, "--evidence", "v1,v2", "--resources", res],
                 ["deliver", "--work", work]):
        out, rc = w.CLI.run(list(argv) + ["--root", str(w.root), "--team", TEAM])
        assert rc == 0, out
    kw._put(w.state / "ft20-switch" / (TEAM + ".json"), "{}")
    path, base = w.tmp / "wt" / work, git(w.tmp / "seed-biz", "rev-parse", "main")
    path.mkdir(parents=True, exist_ok=True)
    if not light:
        git(w.tmp, "clone", "-q", str(w.tmp / "biz.git"), str(path))
        for k, v in (("user.email", "t@t"), ("user.name", "t"), ("commit.gpgsign", "false")):
            git(path, "config", k, v)
        git(path, "checkout", "-q", "-b", "nano/" + work)
        kw._put(path / "x.txt", work), git(path, "add", "-A"), git(path, "commit", "-q", "-m", "x")
        for rel in files or {}:
            kw._put(path / rel, files[rel]), git(path, "add", "-A"), git(path, "commit", "-q", "-m", rel)
        git(path, "push", "-q", "origin", "nano/" + work) if push else None
        kw._put(path / "dirty.txt", "d") if dirty else None
    intent = {"FT2_HOLDER": holder, "state": state, "at": "2026-01-01T00:00:00", "base": "origin/main", "base_sha": base, "worktree": str(path)}
    kw._put(w.runtime() / "launch" / ("%s@a1.intent" % work), intent)
    if turn is not None:
        last = "{깨짐" if turn == "broken" else json.dumps({"type": "message", "message": {"role": "assistant", "stopReason": turn}})
        jsonl = Path(w.env["FT2_PI_SESSIONS"]) / ("--%s--" % str(path).strip("/").replace("/", "-")) / "s.jsonl"
        kw._put(jsonl, '{"type": "session"}\n' + last + "\n")
        os.utime(jsonl, (w.t - age, w.t - age))
    d = json.loads(w.tm.read_text(encoding="utf-8"))
    d["alive"], d["pane"][holder] = d["alive"] + ([holder] if alive else []), pane
    kw._put(w.tm, d)
    return holder, path


def rnd(w, cmd="pi", cpu=0.0, dt=0, clean=None):
    """한 바퀴 — 시계 dt 초 · pane 명령·ps 표(사슬 끝 %cpu) 주입 · tmuxc clean 대역 · 반환 = 로그 줄."""
    w.t += dt
    alive = json.loads(w.tm.read_text(encoding="utf-8"))["alive"]
    shells = alive if os.path.basename(cmd) in ("zsh", "bash", "fish") else []
    kw._put(str(w.tm) + ".clean", "".join(x + "\n" for x in shells) if clean is None else clean)
    k = w.keeper()
    k.pane_info = lambda seat: (100, cmd)
    k.ps_rows = lambda: [(p, pp, cpu if c is None else c, n) for p, pp, c, n in CHAIN]
    return w.round(k)


def two(w, dt=0, **kv):
    """CPU idle 판정 = 표본 2개 · 간격 30초."""
    return rnd(w, dt=dt, **kv) + rnd(w, dt=dt + 30, **kv)


def has(lines, *words):
    return [x for x in lines if all(word in x for word in words)]


def sent(w):
    return [x for x in kw._lines(str(w.mbox) + ".log") if x.startswith("send")]


def park_log(w):
    p = w.root / ".fable-team" / "state" / "ft2" / "submit-park.log"
    return p.read_text(encoding="utf-8").splitlines() if p.exists() else []


def unread(w, seat, body="안녕"):
    """막는 미읽음 1통 — `peek --rows` 머리줄 + 줄 1개."""
    kw._put(Path(str(w.mbox) + ".pending"), "1")
    kw._put(Path(str(w.mbox) + ".rows"), json.dumps({"seq": 1, "ts": kw.NOW, "from": "M-" + TEAM, "to": seat, "body": body}, ensure_ascii=False) + "\n")


def ahead(w, path, work):
    """원격 가지를 로컬 HEAD 위로 — main 에 커밋 하나 얹고 그 가지에 main 병합."""
    w.commit("biz", {"m-%s.txt" % work: work}, "main")
    m = w.tmp / ("mrg-" + work)
    git(w.tmp, "clone", "-q", str(w.tmp / "biz.git"), str(m))
    for k, v in (("user.email", "t@t"), ("user.name", "t"), ("commit.gpgsign", "false")):
        git(m, "config", k, v)
    git(m, "checkout", "-q", "-B", "nano/" + work, "origin/nano/" + work)
    git(m, "merge", "-q", "--no-ff", "-m", "main 병합", "origin/main")
    git(m, "push", "-q", "origin", "nano/" + work)
    git(path, "fetch", "-q", "origin")


def landed(w, work, **opt):
    """착지 끝 좌석 = 팩 구현 커밋 + «- 착지:» 줄이 있는 완성 카드."""
    card(w, work, sha=w.land_sha(), stage="완성")
    return nano(w, work, age=310, **opt)


def c1(w):   # ① 나노 · 턴 끝 · clean · HEAD = origin 가지 · 601초(두 바퀴 끝) · CPU idle 2회 → PARKED + «자리 비움» 1통 + 로그 1줄
    card(w, "r9601")
    nano(w, "r9601", age=571)
    lines = two(w)
    assert has(lines, "PARKED harness r9601", "idle-done") and len(w.tmux("kill-session")) == 1, lines
    assert w.kinds("parked") == 1, lines
    got = [x for x in sent(w) if "자리 비움" in x]
    assert len(got) == 1 and "무활동 10분" in got[0] and "head " in got[0], got
    log = park_log(w)
    assert len(log) == 1 and "«자리 비움»" in log[0] and "무활동 10분" in log[0], log
    assert (w.root / ".fable-team" / "state" / "ft2" / "submit-park.log").stat().st_mode & 0o777 == 0o644


def c2(w):   # ② 같은 좌석 301초 → WORKING(닫기 0 · 쪽지 0 · 로그 0 · r2596 뒤 = 5분에 안 닫힌다)
    card(w, "r9602")
    nano(w, "r9602", age=301, turn="stop")
    lines = rnd(w, cmd="zsh")
    assert has(lines, "WORKING harness r9602") and not w.tmux("kill-session") and not park_log(w), lines
    assert not [x for x in sent(w) if "자리 비움" in x]


def c3(w):   # ③ 601초 · 미커밋 1줄 → kill 0 · [긴급] dirty
    card(w, "r9603")
    nano(w, "r9603", age=571, dirty=True)
    lines = two(w)
    assert has(lines, "UNKNOWN harness r9603", "dirty") and not w.tmux("kill-session"), lines
    assert [x for x in sent(w) if "dirty" in x], sent(w)


def c4(w):   # ④ 601초 · push 안 한 커밋 → kill 0 · [긴급] unpushed
    card(w, "r9604")
    _, path = nano(w, "r9604", age=571, push=False)
    lines = two(w)
    assert has(lines, "UNKNOWN harness r9604", "unpushed") and not w.tmux("kill-session"), lines


def c5(w):   # ⑤ 원격 가지 head = 로컬 HEAD 위에 main 병합 커밋 → PARKED
    card(w, "r9605")
    _, path = nano(w, "r9605", age=571)
    ahead(w, path, "r9605")
    lines = two(w)
    assert has(lines, "PARKED harness r9605", "idle-done") and len(w.tmux("kill-session")) == 1, lines


def c6(w):   # ⑥ pane Working · CPU busy → WORKING
    card(w, "r9606")
    card(w, "r9607")
    nano(w, "r9606", age=3600, pane="⠋ Working (3s)")
    nano(w, "r9607", age=3600)
    lines = two(w, cpu=0.8)   # CPU busy = 유휴 근거 아님(둘 다 WORKING)
    assert has(lines, "WORKING harness r9606") and has(lines, "WORKING harness r9607", "cpu-busy"), lines
    assert not w.tmux("kill-session") and w.kinds("parked") == 0, lines


def c7(w):   # ⑦ 열린 턴(toolUse) · CPU idle · 301초 · 869초 → 둘 다 WORKING · [긴급] 0(r2539 뒤 = 599초 까지 WORKING)
    card(w, "r9608")
    card(w, "r9609")
    nano(w, "r9608", age=301, turn="toolUse", light=True)
    nano(w, "r9609", age=569, turn="toolUse", light=True)   # 두 바퀴 끝 599초 = 아직 문턱 안
    lines = two(w)
    assert has(lines, "WORKING harness r9608", "jsonl-active") and has(lines, "WORKING harness r9609", "jsonl-active"), lines
    assert not w.tmux("kill-session") and not sent(w), (lines, sent(w))


def c8(w):   # ⑧ 열린 턴 · 601초(두 바퀴 끝) · CPU idle → waiting-input [긴급](r2539 문턱 600)
    card(w, "r9610")
    nano(w, "r9610", age=575, turn="toolUse", light=True)
    lines = two(w)
    assert has(lines, "UNKNOWN harness r9610", "waiting-input") and [x for x in sent(w) if "waiting-input" in x], lines


def c9(w):   # ⑨ 막는 미읽음 1통 → 닫기 0(지금 글자 그대로 = mail-pending)
    card(w, "r9611")
    holder, _ = nano(w, "r9611", age=571)
    unread(w, holder)
    lines = two(w)
    assert has(lines, "UNKNOWN harness r9611", "mail-pending") and not w.tmux("kill-session"), lines


def c10(w):   # ⑩ arch 좌석 무활동 2시간 → kill · park 0
    card(w, "r9612")
    holder, _ = nano(w, "r9612", age=7200, holder="biz-%s-arch-r9612#0" % TEAM)   # 실 worktree = M13 이면 닫히는지까지 본다
    w.resume(holder, uuid="u-r9612")
    log = Path(w.env["FT2_PI_SESSIONS"]) / ("--%s--" % str(w.root).strip("/").replace("/", "-")) / "2026-11-01_u-r9612.jsonl"
    kw._put(log, '{"type": "session"}\n' + json.dumps({"type": "message", "message": {"role": "assistant", "stopReason": "stop"}}) + "\n")
    os.utime(log, (w.t - 7200, w.t - 7200))
    lines = two(w)
    assert not w.tmux("kill-session") and w.kinds("parked") == 0 and not park_log(w), lines


def c11(w):   # ⑪ 착지 끝 좌석 — 미읽음 관문 · 열린 턴 = WORKING(판정 줄이 지금과 글자까지 같다 · K2)
    card(w, "r9613")
    card(w, "r9614")
    card(w, "r9615")
    nano(w, "r9613", age=571)   # 기준: 착지 0 좌석은 그냥 닫힌다(PARKED · r2596 뒤 = 601초) — 아래 두 좌석이 관문을 본다
    landed(w, "r9614")
    unread(w, "biz-%s-nano-r9614#0" % TEAM)
    landed(w, "r9615", turn="toolUse")
    lines = two(w)
    assert has(lines, "UNKNOWN harness r9614", "mail-pending") and not [x for x in w.tmux("kill-session") if "r9614" in x[2]], lines
    assert has(lines, "WORKING harness r9615", "landed-wait") and not [x for x in w.tmux("kill-session") if "r9615" in x[2]], lines


def c12(w):   # ⑫ 같은 cwd 두 세션 · jsonl 299초 → 임자 모름 · 301초 → 그 나이(SHARE_IDLE 300 · r2539 K7)
    k = w.keeper()
    cwd = str(w.tmp / "shared")
    Path(cwd).mkdir(parents=True, exist_ok=True)
    log = Path(w.env["FT2_PI_SESSIONS"]) / ("--%s--" % cwd.strip("/").replace("/", "-")) / "s.jsonl"
    kw._put(log, '{"type": "session"}\n'), os.utime(log, (w.t - 299, w.t - 299))
    seats = ["biz-%s-arch-a#0" % TEAM, "biz-%s-arch-b#0" % TEAM]
    for seat in seats:   # 같은 cwd 를 쓰는 살아 있는 biz 세션 2개
        kw._put(w.runtime() / "launch" / ("x-%s.intent" % seat[-4:]), {})
        kw._put(w.state / "seat-path.json", {})
    d = json.loads(w.tm.read_text(encoding="utf-8"))
    d["alive"] = d["alive"] + seats
    d["path"] = {seat: cwd for seat in seats}
    d["born"] = {seat: 0 for seat in seats}
    kw._put(w.tm, d)
    assert k.seat_log(seats[0]) is None   # 299초 < SHARE_IDLE 300 = 임자 모름
    os.utime(log, (w.t - 301, w.t - 301))
    assert k.seat_log(seats[0]) == str(log)   # 301초 = 그 나이(임자 가름 끝)


def c13(w):   # ⑬ 접수만 dispatch 0 — 299초 → [긴급] 0 · 301초 → accept-only [긴급](ACCEPT_IDLE 300 · r2539 K7)
    assert w.CLI.run(["submit", "--command", "c-a", "--body", "b", "--work", "r9616", "--root", str(w.root), "--team", TEAM])[1] == 0
    kw._put(w.state / "ft20-switch" / (TEAM + ".json"), "{}")
    w.t = datetime.datetime.strptime(kw.NOW, "%Y-%m-%dT%H:%M:%S").timestamp() + 299
    lines = rnd(w)
    assert not has(lines, "accept-only"), lines
    w.t += 2
    lines = rnd(w)
    assert has(lines, "UNKNOWN harness r9616", "accept-only"), lines


def c14(w):   # ⑭ FT2_PARK_IDLE_S — 3600 = 옛 동작 · 10 · abc = 600(r2596)
    card(w, "r9617")
    nano(w, "r9617", age=301)
    w.env["FT2_PARK_IDLE_S"] = "3600"
    lines = two(w)
    assert not [x for x in w.tmux("kill-session") if "r9617" in x[2]] and has(lines, "WORKING harness r9617"), lines
    card(w, "r9618")
    nano(w, "r9618", age=15)   # =10 은 범위 밖(60 미만) = 600(r2596) → 15초는 아직 안 닫힌다
    w.env["FT2_PARK_IDLE_S"] = "10"
    lines = two(w, dt=60)
    assert has(lines, "WORKING harness r9618") and not [x for x in w.tmux("kill-session") if "r9618" in x[2]], lines
    card(w, "r9619")
    nano(w, "r9619", age=571)
    w.env["FT2_PARK_IDLE_S"] = "abc"
    lines = two(w, dt=60)
    assert has(lines, "PARKED harness r9619") and [x for x in w.tmux("kill-session") if "r9619" in x[2]], lines


def c15(w):   # ⑮ 같은 좌석 · 같은 head 로 두 바퀴 → 쪽지 1통
    note = kw._mod(w.ft2 / NOTE, "ft2_park_note_r2535_mail")
    card(w, "r9619")
    holder, path = nano(w, "r9619", age=301, light=True)
    k, intent = w.keeper(), {"worktree": str(path)}
    assert note.parked(k, TEAM, "r9619", holder, intent) is True
    w.t += 60
    assert note.parked(k, TEAM, "r9619", holder, intent) is False
    assert len([x for x in sent(w) if "자리 비움" in x]) == 1, sent(w)


def c16(w):   # ⑯ «자리 비움» 뒤 같은 좌석 · 카드가 다시 뜸 → 로그 «재개» 1줄 · 다음 바퀴에도 1줄
    note = kw._mod(w.ft2 / NOTE, "ft2_park_note_r2535_reopen")
    card(w, "r9620")
    holder, path = nano(w, "r9620", age=301, light=True)
    k, intent = w.keeper(), {"worktree": str(path)}
    note.parked(k, TEAM, "r9620", holder, intent)
    assert note.reopen(k, TEAM, "r9620", holder, intent) is True
    assert note.reopen(k, TEAM, "r9620", holder, intent) is False
    log = park_log(w)
    assert len(log) == 2 and "«재개»" in log[1] and "닫을 때 head" in log[1] and "지금 head" in log[1], log


def c17(w):   # ⑰ 로그 폴더 쓰기 실패 · 쪽지 실패 → 닫기는 그대로 · keeper 기록 1줄
    card(w, "r9621")
    nano(w, "r9621", age=571)
    kw._put(w.state / "ft2", "폴더 아님")   # submit-park.log 자리를 파일로 막는다
    kw._put(Path(str(w.mbox) + ".rc"), "1")
    lines = two(w)
    assert has(lines, "PARKED harness r9621") and len(w.tmux("kill-session")) == 1, lines
    assert has(lines, "PARK-NOTE", "쓰기 실패") and has(lines, "미발송"), lines


def c18(w):   # ⑱ ALL_STOP 중 → kill 0 · «예정 PARKED»
    kw._put(w.state / "ALL_STOP.json", {"since": 1, "reason": "시험"})
    card(w, "r9622")
    nano(w, "r9622", age=571)
    lines = two(w)
    assert has(lines, "예정 PARKED", "r9622") and not w.tmux("kill-session") and not park_log(w), lines


def c19(w):   # ⑲ 마지막 줄 못 읽음(stop None) · CPU idle — 301·599 WORKING · 601 turn-open [긴급](r2539 문턱 600)
    card(w, "r9623")
    card(w, "r9624")
    card(w, "r9625")
    card(w, "r9626")
    nano(w, "r9624", age=301, turn="broken", light=True)
    lines = two(w)
    assert has(lines, "WORKING harness r9624") and not sent(w), (lines, sent(w))
    nano(w, "r9625", age=449, turn="broken", light=True)   # 두 바퀴 끝 509·599초 = 문턱 안
    lines = two(w, dt=60)
    assert has(lines, "WORKING harness r9625") and not [x for x in sent(w) if "r9625" in x], lines
    nano(w, "r9626", age=541, turn="broken", light=True)   # 첫 바퀴 601초 = 문턱 밖
    lines = two(w, dt=60)
    assert has(lines, "UNKNOWN harness r9626", "turn-open") and [x for x in sent(w) if "r9626" in x], lines


def c20(w):   # ⑳ 열린 턴(toolUse) · CPU idle 아님 · 901 · 3601 → WORKING(기준판과 같다)
    card(w, "r9627")
    card(w, "r9628")
    nano(w, "r9627", age=901, turn="toolUse", light=True)
    nano(w, "r9628", age=3601, turn="toolUse", light=True)
    lines = two(w, cpu=0.8)
    assert has(lines, "WORKING harness r9627", "cpu-busy") and has(lines, "WORKING harness r9628", "cpu-busy"), lines
    assert not w.tmux("kill-session") and not sent(w), (lines, sent(w))


def c21(w):   # ㉑(DA#60 지적 2) 착지 좌석 · 미읽음 1통 · 옛 문(`peek <좌석>`) rc2 → 사유도 착지 길로 다시 읽어 mail-pending
    w.card("r9630", stage="진행")
    landed(w, "r9630")
    unread(w, "biz-%s-nano-r9630#0" % TEAM)
    kw._put(Path(str(w.mbox) + ".peekrc"), "2")   # 옛 문만 실패하는 mbox — 사유 재조회가 길 표식을 잃으면 mail-unknown 이 된다
    lines = two(w)
    assert has(lines, "UNKNOWN harness r9630", "mail-pending") and not w.tmux("kill-session"), lines


CASES = {"c21": c21, "c1": c1, "c2": c2, "c3": c3, "c4": c4, "c5": c5, "c6": c6, "c7": c7, "c8": c8, "c9": c9, "c10": c10, "c11": c11,
         "c12": c12, "c13": c13, "c14": c14, "c15": c15, "c16": c16, "c17": c17, "c18": c18, "c19": c19, "c20": c20}


@pytest.mark.parametrize("name", list(CASES))
def test_case(name, tmp_path, monkeypatch):
    CASES[name](world(tmp_path, monkeypatch))
