"""r2401 ft2 keeper — 사람·팀장이 부르는 닫기 1개(`keeper --close-seat`) · 카드 반례 ①~⑪.
r2419 — 정지(ALL_STOP) 중에도 «정지 뒤에 새로 뜬 석»은 닫힌다(K1) · 승인 원장 행은 origin/main → 없으면 데이터 루트
planner 원장 파일에서도 읽고(K3 ⓑ · 출처 표시 K4) 데이터 루트 행일 때는 승인 우편이 그 석을 적어야 한다(K6) · 카드 반례 ①~⑰.
대역 = r1812 keeper_world(실제 core 장부 · 가짜 tmux · 임시 리포) + BIZ 대역 clone 안의 실제 git worktree 1개(intent worktree · 재개 기록 요건) +
planner 판정 원장(origin/main) + 우편 로그 + 자율 모드 스텁(<root> 의 `bin/ft-autonomy.sh` · 자율 모드 판독 자리). 실 tmux·실 명부·실 원장·sleep 0.
부르는 길 = 실제 `core/cli.py keeper --close-seat …`(①) · 나머지도 같은 갈래(⑩ 만 park 손을 가짜로 바꾼다 · ⑪ 은 잠금 대기를 1초로 줄여 잰다).
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import keeper_world_r1812 as kw

TEAM, W = kw.TEAM, "r2401"
S = "biz-harness-nano-r2401-t#0"
OTHER = "biz-harness-nano-r2401-other#1"
DESK, ARCH, MASTER = "biz-planner-desk-pi#7", "biz-harness-arch-pi#5", "biz-harness-master-pi#9"
N, SEQ, UUID = "4500", "12345", "0b9e2c1a-7d4f-4e21-9a3b-5c6d7e8f9012"
REASON = "판정 원장 행 · 유휴 ft2 나노 1석 정리"
IDLE, BUSY_PANE = "✻ Brewed for 3s\n❯ ", "⠋ Working...\n"
ROW = "- **%s** %%s #%s 수동 닫기 나노 1석(r2401 · 자율 ON A18) · 유휴" % (N, SEQ)
MAIL = "[수동 닫기 승인] %s\n%s 1석 정리 · 유휴" % (W, W)


def mc():
    """이 시험 대상 모듈(사본 = 팩 그대로) — ⑩⑪ 은 in-process 로 손을 바꿔 잰다."""
    path = kw.FT2 / "adapters" / "pi" / "keeper_manual_close.py"
    spec = importlib.util.spec_from_file_location("ft2_manual_r2401", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(cwd, *a):
    return kw._git(cwd, *a)


def tree(w):
    return w.root / ".fable-team" / "teams" / TEAM / "worktrees" / (W + "@a1")


def world(tmp, mp, mode="on", row=ROW, mail=MAIL, mail_from=DESK, dirty=False, pane=IDLE, att=0, files=1,
          latest=S, rows=None, stop=False, since=None, born=0, ledger_file="VERDICTS-planner-24-r2401.md",
          local=(), seat=S, seq=SEQ):
    """일 1개 = submit→assign(seat)→deliver · (latest ≠ seat 면 seat 뒤에 다른 석 배정) · intent(seat) · 실제 worktree · pi jsonl files개.
    r2419 — since·born = ALL_STOP since 와 그 석 tmux 세션 생성 시각 · ledger_file·local = 데이터 루트 원장 파일(main 미착지)."""
    w = kw.World(tmp, mp)
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
        kw._put(log, '{"type": "session", "id": "%s"}\n' % UUID), os.utime(log, (w.t - 3600, w.t - 3600))
    if dirty:
        kw._put(tree(w) / "wip.txt", "미커밋 1개\n")
    ledger = (row % seat) if row else ""
    if ledger_file:
        kw._put(w.root / "design" / "teams" / "planner" / ledger_file, "# 판정 원장\n" + (rows if rows is not None else ledger + "\n"))
    git(w.root, "add", "-A"), git(w.root, "commit", "-qm", "ledger")
    git(w.root, "update-ref", "refs/remotes/origin/main", "HEAD")
    for name, body in local:   # r2419 — 커밋 뒤에 쓴다 = 데이터 루트에만 있고 origin/main 에는 없다
        kw._put(w.root / "design" / "teams" / "planner" / name, body)
    kw._put(w.root / ".fable-team" / "comm" / "mailbox.log.jsonl", json.dumps({"seq": seq, "from": mail_from, "to": seat, "body": mail}, ensure_ascii=False) + "\n")
    stub = os.path.join(w.root, ".fable-team", "bin", "ft-autonomy.sh")
    kw._put(stub, "#!/bin/sh\necho %s\n" % mode), Path(stub).chmod(0o755)
    if stop:
        kw._put(w.state / "ALL_STOP.json", {"reason": "정지"} if since is None else {"reason": "정지", "since": since})
    d = json.loads(w.tm.read_text(encoding="utf-8"))
    d.update(alive=[seat], pane={seat: pane}, att={seat: att}, born={seat: born})
    kw._put(w.tm, d)
    w.rs = tmp / "resume"
    w.env["FT2_SEAT_RESUME_DIR"] = str(w.rs)
    return w


def run(w, seat=S, n=N, approve=None, reason=REASON):
    """실제 CLI 갈래 = `core/cli.py keeper --close-seat …` → (줄 목록, rc)."""
    done = subprocess.run([sys.executable, str(w.ft2 / "core" / "cli.py"), "keeper", "--root", str(w.root), "--close-seat", seat,
                           "--verdict", n, "--approve", approve or ("%s #%s" % (DESK, SEQ)), "--reason", reason],
                          capture_output=True, text=True, env=w.env, cwd=str(w.root), timeout=70)
    return [x for x in done.stdout.strip().splitlines() if x], done.returncode


def kills(w):
    return [a[-1] for a in w.tmux("kill-session")]


def rec(w):
    path = w.rs / (S + ".json")
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def one(lines, head):
    """그 머리로 시작하는 줄 1개(아니면 빈 글)."""
    got = [x for x in lines if x.startswith(head)]
    assert len(got) == 1, lines
    return got[0]


def untouched(w):
    """손 0 = kill 0 · 재개 기록 0 · park 0."""
    assert kills(w) == [] and rec(w) is None, (kills(w), rec(w))


HOW = (" · 다시 열기 = 카드에 «- 재개: <시각> · PR #<번호> · head <40자> · 가지 nano/<work>» 한 줄"
       "(원장이 남아 있으면 ft-card-assign-watch.sh record <카드> clear <사유>)")   # r2573 — 끝 줄 꼬리 = 다시 여는 법


def test_case01_소유있는_ft2나노_닫기(tmp_path, monkeypatch):
    """① 원장 행 ∧ 우편 ∧ 자율 on → 재개 기록 1 · kill 1 · park 1 · CLOSED-MANUAL … park=done rc 0 · project 에 owner 0."""
    w = world(tmp_path, monkeypatch)
    lines, rc = run(w)
    assert rc == 0, lines
    assert one(lines, "CLOSED-MANUAL") == "CLOSED-MANUAL %s %s 판정 %s %s #%s park=done reason=%s%s" % (TEAM, S, N, DESK, SEQ, REASON, HOW), lines
    assert kills(w) == ["=" + S]
    doc = rec(w)
    assert doc["name"] == S and doc["retired_by"] == DESK and doc["binding"]["source"] == "ft2-manual-close", doc
    proj, prc = w.CLI.run(["project", "--root", str(w.root), "--team", TEAM])
    row = (proj.get("holders") or {}).get(S) or {}
    assert prc == 0 and row.get("free") is True and W not in json.dumps(row, ensure_ascii=False), proj.get("holders")   # 그 일 owner 0
    assert (w.root / ".fable-team" / "teams" / TEAM / "runtime").is_dir()   # 장부 리포 살아 있음(지움 0)


def test_case02_대상_판정(tmp_path, monkeypatch):
    """② dispatch 밖 석 = park=none rc 0 / master 석 = REJECT 대상 아님 / intent 없는 나노 꼴 석 = REJECT 대상 아님 intent 없음."""
    w = world(tmp_path, monkeypatch, latest=OTHER)
    lines, rc = run(w)
    assert rc == 0 and "park=none" in one(lines, "CLOSED-MANUAL"), lines
    assert kills(w) == ["=" + S]
    w2 = world(tmp_path / "b", monkeypatch)
    lines, rc = run(w2, seat=MASTER)
    assert rc == 2 and "REJECT 대상 아님" in one(lines, "REJECT 대상 아님"), lines
    untouched(w2)
    lines, rc = run(w2, seat="biz-harness-nano-ghost#0")
    assert rc == 2 and "intent 없음" in one(lines, "REJECT 대상 아님"), lines
    assert kills(w2) == [] and rec(w2) is None


def test_case03_승인_대조_원장과_우편(tmp_path, monkeypatch):
    """③ 원장에 없는 판정 · 행은 있으나 다른 석 · 행에 «무효» · 우편 from ≠ 승인 좌석 → 모두 REJECT 승인 rc 2 · 손 0."""
    w = world(tmp_path, monkeypatch, mode="off")
    lines, rc = run(w)                                  # 자율 off ∧ «오빠 네» 없음 = 승인 아님
    assert rc == 2 and "REJECT 승인" in one(lines, "REJECT 승인"), lines
    untouched(w)
    w = world(tmp_path / "b", monkeypatch, mode="off", row="- **%s** %%s #%s 수동 닫기 오빠 네 1795000000.000000" % (N, SEQ))
    lines, rc = run(w, approve="%s #99999" % DESK)      # 원장 행에 #seq 없음
    assert rc == 2 and "REJECT 승인" in one(lines, "REJECT 승인"), lines
    untouched(w)
    w = world(tmp_path / "c", monkeypatch, rows="- **%s** %s #%s 수동 닫기 다른석 (무효)" % (N, OTHER, SEQ))
    lines, rc = run(w)
    assert rc == 2 and "REJECT 승인" in one(lines, "REJECT 승인"), lines
    untouched(w)
    w = world(tmp_path / "d", monkeypatch, mail_from=ARCH)
    lines, rc = run(w)
    assert rc == 2 and "REJECT 승인" in one(lines, "REJECT 승인"), lines
    untouched(w)


def test_case04_planner가_아닌_승인_좌석(tmp_path, monkeypatch):
    """④ 원장·우편 맞고(우편 from = 그 좌석) 승인 좌석만 biz-harness-master 석(planner 아님) → REJECT 승인 rc 2 · 손 0."""
    w = world(tmp_path, monkeypatch, mail_from=MASTER)
    lines, rc = run(w, approve="%s #%s" % (MASTER, SEQ))
    assert rc == 2 and "REJECT 승인" in one(lines, "REJECT 승인"), lines
    untouched(w)


def test_case05_자율_모드_대조(tmp_path, monkeypatch):
    """⑤ 자율 on ∧ A<N> 없음 / off ∧ «오빠» 만 / off ∧ «오빠 네 <ts>» = 진행 / mode 판독 실패 / ★고정 반례★ / on ∧ «보류» / 우편 머리 «[닫기 문의]»."""
    w = world(tmp_path, monkeypatch, row="- **%s** %%s #%s 수동 닫기 나노 1석(자율 판정)" % (N, SEQ))
    lines, rc = run(w)
    assert rc == 2 and "REJECT 승인" in one(lines, "REJECT 승인"), lines
    untouched(w)
    w = world(tmp_path / "b", monkeypatch, mode="off", row="- **%s** %%s #%s 수동 닫기 오빠가 승인함" % (N, SEQ))
    lines, rc = run(w)
    assert rc == 2, lines
    untouched(w)
    w = world(tmp_path / "c", monkeypatch, mode="off", row="- **%s** %%s #%s 수동 닫기 오빠 네 1795000000.000000" % (N, SEQ))
    lines, rc = run(w)
    assert rc == 0 and "park=" in one(lines, "CLOSED-MANUAL"), lines   # 자율 off 여도 «오빠 네 <ts>» = 승인
    w = world(tmp_path / "d", monkeypatch, mode="bogus")
    lines, rc = run(w)
    assert rc == 2 and "자율 모드 판독 실패" in one(lines, "REJECT 승인"), lines
    untouched(w)
    w = world(tmp_path / "e", monkeypatch, mode="off", row="- **%s** %%s #%s 오빠 아니오 1795000000.000000 닫기 거절" % (N, SEQ),
              mail="%s 닫기 거절" % W)
    lines, rc = run(w)
    assert rc == 2 and "REJECT 승인" in one(lines, "REJECT 승인"), lines   # ★DA#56 고정 반례★ 기록 0 · kill 0
    untouched(w)
    w = world(tmp_path / "f", monkeypatch, row="- **%s** %%s #%s 수동 닫기 나노 1석(자율 ON A18) · 보류" % (N, SEQ))
    lines, rc = run(w)
    assert rc == 2 and "REJECT 승인" in one(lines, "REJECT 승인"), lines
    untouched(w)
    w = world(tmp_path / "g", monkeypatch, mail="[닫기 문의] %s\n닫아도 되나요" % W)
    lines, rc = run(w)
    assert rc == 2 and "REJECT 승인" in one(lines, "REJECT 승인"), lines
    untouched(w)


def test_case06_정지_중(tmp_path, monkeypatch):
    """⑥ ALL_STOP 켜짐 ∧ ①의 승인 그대로 → REJECT 정지 중 rc 2 · kill 0 · 기록 0."""
    w = world(tmp_path, monkeypatch, stop=True)
    lines, rc = run(w)
    assert rc == 2 and one(lines, "REJECT 정지 중"), lines
    assert "kill 0" in one(lines, "REJECT 정지 중")
    untouched(w)


def test_case07_사람_화면과_일하는_중(tmp_path, monkeypatch):
    """⑦ attached 1 → rc 4 · pane Working → rc 4 · 둘 다 손 0."""
    w = world(tmp_path, monkeypatch, att=1)
    lines, rc = run(w)
    assert rc == 4 and "REJECT attached" in one(lines, "REJECT attached"), lines
    untouched(w)
    w = world(tmp_path / "b", monkeypatch, pane=BUSY_PANE)
    lines, rc = run(w)
    assert rc == 4 and "REJECT busy" in one(lines, "REJECT busy"), lines
    untouched(w)


def test_case08_미커밋(tmp_path, monkeypatch):
    """⑧ intent worktree 에 미커밋 1 → REJECT dirty rc 8 · 기록 0 · kill 0."""
    w = world(tmp_path, monkeypatch, dirty=True)
    lines, rc = run(w)
    assert rc == 8 and "REJECT dirty — [wip] 커밋 먼저" in one(lines, "REJECT dirty"), lines
    untouched(w)


def test_case09_재개_기록_요건(tmp_path, monkeypatch):
    """⑨ intent worktree 폴더 jsonl 0개·2개 → rc 5 · 기록 0 · kill 0."""
    for name, files in (("a", 0), ("b", 2)):
        w = world(tmp_path / name, monkeypatch, files=files)
        lines, rc = run(w)
        assert rc == 5 and one(lines, "REJECT 재개 기록"), lines
        assert kills(w) == [] and rec(w) is None


def test_case10_park_실패(tmp_path, monkeypatch):
    """⑩ park 를 가짜로 실패 → rc 7 · «PARK-FAILED» 줄에 손으로 부를 park 명령 1줄 · 세션은 이미 닫힘."""
    w = world(tmp_path, monkeypatch)
    module = mc()
    module.cli.run = lambda argv: ({"result": "접수 거부", "reason": "결과 미확정 = 쉼 거절(쓰기 0)"}, 1)
    keeper = w.keeper()
    rc = module.run(keeper, S, N, "%s #%s" % (DESK, SEQ), REASON)
    assert rc == 7, keeper.lines
    line = one(keeper.lines, "PARK-FAILED")
    assert "python3 core/cli.py park --work %s --attempt a1 --reason idle-done --root %s" % (W, w.root) in line, line
    assert "manual-close: 판정 %s" % N in line, line
    assert kills(w) == ["=" + S] and rec(w) is not None      # 세션은 이미 닫힘(재개 기록 먼저)


def test_case11_잠금_BUSY(tmp_path, monkeypatch):
    """⑪ keeper 잠금 잡힌 채 → «BUSY» rc 3 · 손 0(대기는 1초로 줄여 잰다 · 값 = LOCK_S 7.0)."""
    w = world(tmp_path, monkeypatch)
    module = mc()
    assert module.LOCK_S == 7.0
    lock = w.root / ".fable-team" / "state" / "ft2-keeper" / "keeper.lock"
    kw._put(lock, ""), os.utime(lock, None)   # 지금 시각 = 산 잠금(10분 넘으면 keeper.locked 처럼 지운다)
    keeper = w.keeper()
    rc = module.run(keeper, S, N, "%s #%s" % (DESK, SEQ), REASON, wait=1.0)
    assert rc == 3 and keeper.lines and keeper.lines[-1].startswith("BUSY"), keeper.lines
    assert lock.exists() and kills(w) == [] and rec(w) is None     # 남의 잠금을 지우지 않는다


def test_case12_pane_판독_실패(tmp_path, monkeypatch):
    """⑫ DA#56 H1 — capture-pane rc 1 = 일하는지 모른다 → rc 9 · 기록 0 · kill 0 · CLOSED-MANUAL 0(고정 = DA 5f13c297 반례)."""
    w = world(tmp_path, monkeypatch)
    keeper = w.keeper()
    real = keeper.call
    keeper.call = lambda argv, timeout=None, retry=0: ((1, "", "capture failed") if argv[1] == "capture-pane"
                                                       else real(argv, timeout=timeout, retry=retry))
    rc = mc().run(keeper, S, N, "%s #%s" % (DESK, SEQ), REASON)
    assert rc == 9 and "capture-pane rc=1" in one(keeper.lines, "REJECT pane 판독"), keeper.lines
    untouched(w)


def test_case13_장부_판독_실패(tmp_path, monkeypatch):
    """⑬ DA#56 H2 — endings.latest = None(장부 판독 실패) → rc 9 · park=none 성공 0 · kill 0(소유 없음 확정 불가)."""
    w = world(tmp_path, monkeypatch)
    module = mc()
    monkeypatch.setattr(module.endings, "latest", lambda *a: None)
    keeper = w.keeper()
    rc = module.run(keeper, S, N, "%s #%s" % (DESK, SEQ), REASON)
    assert rc == 9 and "장부 판독 실패" in one(keeper.lines, "REJECT 장부"), keeper.lines
    untouched(w)


# ── r2419 — 정지 중 수동 닫기(정지 뒤에 뜬 석) + 데이터 루트 원장(main 미착지) ─────────────────────────────
SINCE, LATE = 1793990000, 1793990001          # ALL_STOP since · 그 뒤에 뜬 석의 tmux 세션 생성 시각
#   값이 1793996400(= 세계의 pi jsonl mtime)보다 작아야 한다 — r2281 C4 재개 기록 요건(jsonl mtime ≥ session_created)을 건드리지 않는다
LOCAL_FILE = "VERDICTS-planner-225-20261104.md"
MAIL_S = "[수동 닫기 승인] %s\n%s %s 1석 정리 · 유휴" % (W, W, S)   # K6 — 우편이 닫을 석 이름을 적은 꼴
S1 = "biz-harness-nano-r2401-t#1"            # ⑯⑰ — 같은 work 의 지금 석(앞 석 = S «…#0»)


def vm():
    """keeper_verdict 사본(⑭⑮ — 자동 닫기 승인 판정이 지금 그대로인지)."""
    path = kw.FT2 / "adapters" / "pi" / "keeper_verdict.py"
    spec = importlib.util.spec_from_file_location("ft2_verdict_r2419", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def born_calls(w):
    """가짜 tmux 가 기록한 «세션 생성 시각» 조회 횟수(#{session_created})."""
    return [a for a in w.tmux("display-message") if a and "#{session_created}" in a[-1]]


def local(rows, name=LOCAL_FILE):
    """데이터 루트(워킹트리)에만 있는 원장 파일 1개 — origin/main 에는 없다(main 미착지)."""
    return ((name, "# 판정 원장\n" + "".join(r + "\n" for r in rows)),)


def patched(w, born=None, grep=None):
    """in-process 갈래 — keeper.call 만 바꿔 생성 시각 응답·git grep rc 를 흉내 낸다(나머지는 실제 갈래)."""
    keeper = w.keeper()
    real = keeper.call

    def call(argv, timeout=7, retry=0):
        if born is not None and argv and "#{session_created}" in argv[-1]:
            return born
        if grep is not None and "grep" in argv:
            return grep
        return real(argv, timeout=timeout, retry=retry)
    keeper.call = call
    return keeper, mc().run(keeper, S, N, "%s #%s" % (DESK, SEQ), REASON)


def test_r2419_case01_정지_뒤에_뜬_석은_닫는다(tmp_path, monkeypatch):
    """① 정지 중 ∧ 세션 생성 = since+1 ∧ 승인 맞음 → rc 0 «CLOSED-MANUAL … · 정지 중 닫기(…)» · 기록 1 · kill 1 · park 1."""
    w = world(tmp_path, monkeypatch, stop=True, since=SINCE, born=LATE)
    lines, rc = run(w)
    assert rc == 0, lines
    assert one(lines, "CLOSED-MANUAL") == "CLOSED-MANUAL %s %s 판정 %s %s #%s park=done reason=%s · 정지 중 닫기(세션 생성 %d > 정지 %d)%s" % (
        TEAM, S, N, DESK, SEQ, REASON, LATE, SINCE, HOW), lines
    assert kills(w) == ["=" + S] and rec(w)["name"] == S, (kills(w), rec(w))
    assert born_calls(w), born_calls(w)   # K1 조회 1회(+ r2281 C4 재개 기록이 같은 값을 한 번 더 읽는다)


def test_r2419_case02_정지_전_석은_그대로_거절(tmp_path, monkeypatch):
    """② 세션 생성 = since(같으면 거절) · since-100 → rc 2 «정지 중 · 세션 생성 t ≤ 정지 S» · 기록·kill·park 0."""
    for name, born in (("a", SINCE), ("b", SINCE - 100)):
        w = world(tmp_path / name, monkeypatch, stop=True, since=SINCE, born=born)
        lines, rc = run(w)
        assert rc == 2 and "세션 생성 %d ≤ 정지 %d" % (born, SINCE) in one(lines, "REJECT 정지 중"), lines
        untouched(w)


def test_r2419_case03_세션_생성_시각_판독_실패(tmp_path, monkeypatch):
    """③ 응답 ⓐ rc 1 ⓑ 빈 줄 ⓒ «abc» ⓓ 7초 넘김 → 각각 rc 2 «세션 생성 시각 판독 불가» · kill 0."""
    for name, born in (("a", (1, "", "no session")), ("b", (0, "\n", "")), ("c", (0, "abc\n", "")), ("d", (None, "", "timeout 7000ms"))):
        w = world(tmp_path / name, monkeypatch, stop=True, since=SINCE, born=LATE)
        keeper, rc = patched(w, born=born)
        assert rc == 2 and "세션 생성 시각 판독 불가" in one(keeper.lines, "REJECT 정지 중"), keeper.lines
        untouched(w)


def test_r2419_case04_정지_시각_판독_실패(tmp_path, monkeypatch):
    """④ ALL_STOP.json 이 ⓐ `[]` ⓑ since «x» ⓒ since 칸 없음 ⓓ 깨진 글 → 생성 시각이 뒤여도 rc 2 «정지 시각 판독 불가» · 조회 0회."""
    for name, body in (("a", "[]"), ("b", '{"since": "x"}'), ("c", '{"reason": "정지"}'), ("d", "{")):
        w = world(tmp_path / name, monkeypatch, stop=True, since=SINCE, born=LATE)
        kw._put(w.state / "ALL_STOP.json", body)
        lines, rc = run(w)
        assert rc == 2 and "정지 시각 판독 불가" in one(lines, "REJECT 정지 중"), lines
        untouched(w)
        assert born_calls(w) == [], born_calls(w)


def test_r2419_case05_승인이_틀리면_생성_시각_조회_0회(tmp_path, monkeypatch):
    """⑤ 정지 중 ∧ 세션 생성 = since+1 인데 승인 틀림(ⓐ 원장 행 없음 · ⓔ 거절 낱말 «보류») → REJECT 승인 rc 2 · 생성 시각 조회 0회."""
    w = world(tmp_path / "a", monkeypatch, row=None, ledger_file=None, stop=True, since=SINCE, born=LATE)
    lines, rc = run(w)
    assert rc == 2 and "REJECT 승인" in one(lines, "REJECT 승인") and "데이터 루트 원장 · 파일 없음" in one(lines, "REJECT 승인"), lines
    untouched(w)
    assert born_calls(w) == [], born_calls(w)
    w = world(tmp_path / "b", monkeypatch, stop=True, since=SINCE, born=LATE,
              row="- **%s** %%s #%s 수동 닫기 나노 1석(자율 ON A18) · 보류" % (N, SEQ))
    lines, rc = run(w)
    assert rc == 2 and "REJECT 승인" in one(lines, "REJECT 승인"), lines
    untouched(w)
    assert born_calls(w) == [], born_calls(w)


def test_r2419_case06_정지_아님은_기준판_그대로(tmp_path, monkeypatch):
    """⑥ ALL_STOP 없음 · released → 생성 시각 조회 0회 · 끝 줄에 «정지 중 닫기» 없음 · 기준판과 같은 출력."""
    base = "CLOSED-MANUAL %s %s 판정 %s %s #%s park=done reason=%s%s" % (TEAM, S, N, DESK, SEQ, REASON, HOW)
    for name, body in (("a", None), ("b", '{"reason": "정지", "since": %d, "released": true}' % SINCE)):
        w = world(tmp_path / name, monkeypatch, stop=body is not None, since=SINCE, born=LATE)
        if body is not None:
            kw._put(w.state / "ALL_STOP.json", body)
        lines, rc = run(w)
        assert rc == 0 and one(lines, "CLOSED-MANUAL") == base, lines
        # 그 1회 = r2281 C4 재개 기록(jsonl mtime ≥ session_created)이 읽는 값 — K1 정지 갈래는 조회 0회
        assert len(born_calls(w)) == 1, born_calls(w)


def test_r2419_case07_정지_통과_뒤_손의_거절은_그대로(tmp_path, monkeypatch):
    """⑦ 정지 갈래를 통과해도 K3 손(attached · pane Working · dirty)은 지금과 같은 rc·글로 멈춘다."""
    for name, kw_, head, rc_ in (("a", {"att": 1}, "REJECT attached", 4), ("b", {"pane": BUSY_PANE}, "REJECT busy", 4),
                                 ("c", {"dirty": True}, "REJECT dirty", 8)):
        w = world(tmp_path / name, monkeypatch, stop=True, since=SINCE, born=LATE, **kw_)
        lines, rc = run(w)
        assert rc == rc_ and one(lines, head), lines
        untouched(w)


def test_r2419_case08_데이터_루트_원장으로_닫기(tmp_path, monkeypatch):
    """⑧ main 에 행 0개(git rc 1) · 데이터 루트 파일에 1개 · 우편이 그 석을 적음 → rc 0 · 끝 줄에 «원장 = 데이터 루트(main 미착지)»."""
    w = world(tmp_path, monkeypatch, row=None, mail=MAIL_S, local=local([ROW % S]))
    lines, rc = run(w)
    assert rc == 0, lines
    assert " · 원장 = 데이터 루트(main 미착지)" in one(lines, "CLOSED-MANUAL"), lines
    assert kills(w) == ["=" + S] and rec(w) is not None


def test_r2419_case09_main_행이_이긴다(tmp_path, monkeypatch):
    """⑨ 같은 번호가 main 1개(석 이름 없음 → 거절 꼴) · 데이터 루트 1개(맞는 글) → main 행으로 판정해 거절(데이터 루트로 안 넘어감)."""
    w = world(tmp_path, monkeypatch, rows="- **%s** 2026-11-22 #%s 수동 닫기 다른석" % (N, SEQ), mail=MAIL_S, local=local([ROW % S]))
    lines, rc = run(w)
    assert rc == 2 and "REJECT 승인" in one(lines, "REJECT 승인"), lines
    assert "데이터 루트" not in one(lines, "REJECT 승인"), lines
    untouched(w)


def test_r2419_case10_데이터_루트_거절_갈래(tmp_path, monkeypatch):
    """⑩ 파일 없음 · 행 0개 · 같은 번호 2줄 · 무효 낱말 행 · 석 이름 없음 · #seq 없음 → 각각 rc 2 · 사유에 «데이터 루트 원장» · kill 0."""
    bad = {
        "a": None,
        "b": local(["# 빈 원장"]),
        "c": local([ROW % S, ROW % S]),
        "d": local(["- **%s** (무효) #%s 수동 닫기 %s · 유휴" % (N, SEQ, S)]),
        "e": local(["- **%s** 2026-11-22 #%s 수동 닫기 다른석 · 유휴" % (N, SEQ)]),
        "f": local(["- **%s** 2026-11-22 #99999 수동 닫기 %s · 유휴" % (N, S)]),
    }
    for name, files in bad.items():
        w = world(tmp_path / name, monkeypatch, row=None, mail=MAIL_S, ledger_file=None if files is None else "VERDICTS-planner-24-r2401.md",
                  local=files or ())
        lines, rc = run(w)
        assert rc == 2 and "REJECT 승인" in one(lines, "REJECT 승인"), (name, lines)
        assert "데이터 루트 원장" in one(lines, "REJECT 승인"), (name, lines)
        untouched(w)


def test_r2419_case11_git_실패는_데이터_루트로_안_넘어간다(tmp_path, monkeypatch):
    """⑪ git grep rc 128 · 시간 초과 → «원장 못 읽음» rc 2 · 데이터 루트 파일을 읽지 않음(맞는 행이 있어도)."""
    for name, grep in (("a", (128, "", "fatal: not a valid ref")), ("b", (None, "", "timed out"))):
        w = world(tmp_path / name, monkeypatch, row=None, mail=MAIL_S, local=local([ROW % S]))
        keeper, rc = patched(w, grep=grep)
        assert rc == 2 and "원장 못 읽음" in one(keeper.lines, "REJECT 승인"), keeper.lines
        assert "데이터 루트" not in one(keeper.lines, "REJECT 승인"), keeper.lines
        untouched(w)


def test_r2419_case12_데이터_루트는_번호_가장_큰_파일만(tmp_path, monkeypatch):
    """⑫ 파일 224 · 225 이고 그 판정 행은 224 에만 → 데이터 루트 길은 225 만 읽는다 = 0개 → 거절(main 길이라면 승인했을 입력)."""
    files = local([], "VERDICTS-planner-225-20261104.md") + local([ROW % S], "VERDICTS-planner-224-20261001.md")
    w = world(tmp_path, monkeypatch, row=None, mail=MAIL_S, local=files)
    lines, rc = run(w)
    assert rc == 2 and "데이터 루트 원장 · 판정 %s 원장 행 0개" % N in one(lines, "REJECT 승인"), lines
    untouched(w)


def test_r2419_case13_출처_표시_덧말_둘(tmp_path, monkeypatch):
    """⑬ main 행이면 «원장 = 데이터 루트» 없음 · 데이터 루트 행이면 있음 · 정지 중 + 데이터 루트면 덧말 2개가 함께."""
    w = world(tmp_path / "a", monkeypatch)                                  # main 행
    lines, rc = run(w)
    assert rc == 0 and "원장 = 데이터 루트" not in one(lines, "CLOSED-MANUAL"), lines
    w = world(tmp_path / "b", monkeypatch, row=None, mail=MAIL_S, local=local([ROW % S]), stop=True, since=SINCE, born=LATE)
    lines, rc = run(w)                                                     # 정지 중 + 데이터 루트
    line = one(lines, "CLOSED-MANUAL")
    assert rc == 0 and " · 원장 = 데이터 루트(main 미착지)" in line and " · 정지 중 닫기(세션 생성 %d > 정지 %d)" % (LATE, SINCE) in line, lines


def test_r2419_case14_자동_닫기는_데이터_루트를_안_읽는다(tmp_path, monkeypatch):
    """⑭ 자동 닫기(keeper_verdict.approved)에 main 0개 · 데이터 루트 1개를 주면 지금처럼 승인 아님 · 정지 중 바퀴는 닫기 0."""
    w = world(tmp_path, monkeypatch, row=None, mail=MAIL_S, local=local([ROW % S]), stop=True, since=SINCE)
    assert vm().approved(w.keeper(), N, S, DESK, SEQ, W) == "판정 %s 원장 행 0개" % N
    keeper = w.keeper()
    assert keeper.run_once() == 0 and kills(w) == [], (keeper.lines, kills(w))
    assert keeper.halt is True, keeper.halt


N9, SEQ7, TS = "900", "700", "1795000000.000000"
ROW900 = "- **%s** 2026-11-22 #%s 수동 닫기 %s · 오빠 네 %s" % (N9, SEQ7, S1, TS)   # 데이터 루트에만 있는 판정 행


def mail_with(*seats):
    """⑯⑰ — planner master 가 보낸 «[수동 닫기 승인]» 우편 1통(본문에 적은 석 이름만)."""
    return "[수동 닫기 승인] %s\n%s %s 1석 정리 · 오빠 네 %s" % (W, W, " ".join(seats), TS)


def ahead(tmp, mp, **kw):
    """⑯⑰ 공통 세계 — 같은 work 의 지금 석 «…#1» 을 닫으려는 자리(main 판정 900 행 0개 · 데이터 루트 1줄)."""
    arg = dict(seat=S1, latest=S1, n=None, row=None, seq=SEQ7, mode="off", local=local([ROW900]))
    arg.update(kw)
    return world(tmp, mp, **{k: v for k, v in arg.items() if k != "n"})


def test_r2419_case16_앞_석_승인_우편_재사용은_거절(tmp_path, monkeypatch):
    """⑯ 우편 #700 은 «…#0» 만 적고 닫을 석은 «…#1» · 데이터 루트 행은 «…#1 #700 …» → rc 2 «데이터 루트 원장 · 승인 우편 #700 에 …#1 없음» · 손 0."""
    w = ahead(tmp_path, monkeypatch, mail=mail_with(S))
    lines, rc = run(w, seat=S1, n=N9, approve="%s #%s" % (DESK, SEQ7))
    assert rc == 2, lines
    assert "데이터 루트 원장 · 승인 우편 #%s 에 %s 없음" % (SEQ7, S1) in one(lines, "REJECT 승인"), lines
    untouched(w)
    assert kills(w) == [] and born_calls(w) == [], (kills(w), born_calls(w))


def test_r2419_case17_우편이_그_석을_적으면_정상(tmp_path, monkeypatch):
    """⑰ ⓐ «…#1» 을 적음 → rc 0 + 출처 덧말 ⓑ «…#10» 만 → ⑯ 과 같은 거절 ⓒ «…#0» «…#1» 둘 다 → rc 0 ⓓ 우편은 «…#0» 만인데 같은 행이 main 에 1개 → 기준판 그대로(K6 대조 0)."""
    w = ahead(tmp_path / "a", monkeypatch, mail=mail_with(S1))
    lines, rc = run(w, seat=S1, n=N9, approve="%s #%s" % (DESK, SEQ7))
    assert rc == 0 and " · 원장 = 데이터 루트(main 미착지)" in one(lines, "CLOSED-MANUAL"), lines
    w = ahead(tmp_path / "b", monkeypatch, mail=mail_with(S1 + "0"))
    lines, rc = run(w, seat=S1, n=N9, approve="%s #%s" % (DESK, SEQ7))
    assert rc == 2 and "없음" in one(lines, "REJECT 승인") and "데이터 루트 원장" in one(lines, "REJECT 승인"), lines
    untouched(w)
    w = ahead(tmp_path / "c", monkeypatch, mail=mail_with(S, S1))
    lines, rc = run(w, seat=S1, n=N9, approve="%s #%s" % (DESK, SEQ7))
    assert rc == 0 and " · 원장 = 데이터 루트(main 미착지)" in one(lines, "CLOSED-MANUAL"), lines
    w = ahead(tmp_path / "d", monkeypatch, mail=mail_with(S), local=(), rows=ROW900)   # 같은 행이 main 에도 1개
    lines, rc = run(w, seat=S1, n=N9, approve="%s #%s" % (DESK, SEQ7))
    assert rc == 0 and "원장 = 데이터 루트" not in one(lines, "CLOSED-MANUAL"), lines
