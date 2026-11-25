"""r2572 ft2 keeper — 배정 원장 «대기»인 카드의 launch-failed 쉼 attempt 에는 날마다 [긴급] 을 다시 보내지 않는다 (카드 r2572-keeper-launch-failed-alert-ledger-wait · 계약 r2572 K1~K7).

골 = 원장 대기 중 미룸 · 판정 줄 보존 · 풀린 바퀴 1통(그날 미알림일 때만) · 처음 실패·다른 사유·원장 판독 실패는 지금 그대로.
사례 = ①대기 중 판정 줄 1·[긴급] 0 ②대기 여러 바퀴 0 ③같은 날 풀림 1통 ④같은 날 재해제 0 ⑤사유 선행 0 ⑥사유 사람 0
      ⑦원장 없음 1통 ⑧원장 깨짐 1통 ⑨처음 실패(park=True) 1통 ⑩다른 사유 코드 1통 ⑪그날 이미 알림 → 풀려도 0 · 다음 날 1통
      ⑫이미 알린 attempt 반복 대기/해제 0 ⑬정지 중 «예정 PARKED» 줄 그대로·[긴급] 0 ⑭원장 사유 = 줄바꿈 제거 · 20자까지
변이 M1~M10(각각 죽어야 함) = 아래 MUTANTS.
대역 = r1812 keeper_world(임시 root · 두 ref · 가짜 tmux) + launch·record 스텁 + 가짜 mbox + 주입 시계 · 실 tmux·실 runtime·실 명부·Slack 0 · sleep 0 · 네트워크 0.
"""
import datetime
import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("keeper_world_r2572", str(HERE / "keeper_world_r1812.py"))
kw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kw)
FT2, T0, TEAM = kw.FT2, kw.T0, kw.TEAM
MBOX = '#!/bin/sh\nprintf "%s\\n" "$*" >> "$0.log"\nif [ "$1" = peek ]; then echo "pending=$(cat "$0.pending" 2>/dev/null || echo 0) scanned=1"; exit 0; fi\n' \
       'echo "STUB $1"\nexit "$(cat "$0.rc" 2>/dev/null || echo 0)"\n'
LS = 'if a[0] == "list-sessions": print("\\n".join(d["alive"])); sys.exit(0)\n'
HAS = ('if a[0] == "has-session" and os.path.exists(st + ".has_rc"):\n'
       '    sys.stderr.write("error connecting to tmux\\n"); sys.exit(int(open(st + ".has_rc").read()))\n')
LAUNCH = '''import json, os, sys
a, me = sys.argv[1:], os.path.abspath(__file__)
open(me + ".log", "a").write(json.dumps(a) + "\\n")
rc = int(open(me + ".rc").read()) if os.path.exists(me + ".rc") else 0
if rc == 0:
    st = os.environ["FAKE_TMUX"]; d = json.load(open(st)); d["alive"].append("biz-harness-nano-%s#0" % a[a.index("--work") + 1][:40]); json.dump(d, open(st, "w"))
print(json.dumps({"result": "접수 성공" if rc == 0 else "복구 필요"}))
sys.exit(rc)
'''
RECORD = '#!/bin/sh\nprintf "%s\\n" "$*" >> "$0.log"\nmkdir -p .fable-team/state/card-assign\nprintf \'{"state": "%s", "seat": "%s"}\' "$3" "$4" > ".fable-team/state/card-assign/$2.json"\n'


def stamp(t):
    return datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%dT%H:%M:%S")


def world(tmp, mp, cards=None, ft2=FT2, nano_max="0", roster=None):
    """임시 세계 1개 — 가짜 tmux(list-sessions · has-session rc 주입) · 가짜 launch·record·mbox · 카드 루트 표 · 팀 켜기."""
    w = kw.World(tmp, mp, ft2)
    b = tmp / "bin"
    tm = kw.TMUX.replace("__PY__", sys.executable)
    i = tm.index('if a[0] == "kill-session"')
    kw._put(b / "tmux", tm[:i] + LS + HAS + tm[i:])
    kw._put(w.mbox, MBOX), w.mbox.chmod(0o755)
    kw._put(b / "launch.py", LAUNCH), kw._put(b / "record", RECORD), (b / "record").chmod(0o755)
    kw._put(b / "gh", "#!/bin/sh\necho '[]'\n"), (b / "gh").chmod(0o755)
    w.env.update(FT2_KEEPER_LAUNCH=str(b / "launch.py"), FT2_CARD_ASSIGN_BIN=str(b / "record"), FT2_GH=str(b / "gh"),
                 HOME=str(tmp / "home"), FT2_TEAM_NANO_MAX=nano_max, FT2_MAILBOX_DIR=str(tmp / "comm"),
                 FT2_SEAT_RESUME_DIR=str(tmp / "resume"), GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="core.quotepath",
                 GIT_CONFIG_VALUE_0="false")
    kw._put(w.state / "directive-roots.tsv", "harness\t.\torigin/main\tdesign/harness/indices\n")
    kw._put(w.state / "ft20-switch" / (TEAM + ".json"), "{}")
    w.runtime().mkdir(parents=True, exist_ok=True)
    if cards:
        w.commit("biz", {"design/harness/indices/대기/%s.md" % s: "# 인덱스: %s\n- 배정: 없음\n- 상태: 대기\n" % s for s in cards}, "main")
    if roster:
        kw._put(w.root / ".fable-team" / "seats-harness.json", roster)
    w.enable()
    return settle(w)


def settle(w):
    """r1929 keeper 는 launch 를 기다리지 않는다 → 한 «바퀴» = 띄운 가짜 launch 가 끝날 때까지 기다렸다가 같은 keeper 로 다시."""
    base = w.round

    def round(k=None):
        k, more = k or w.keeper(), True
        while more:
            k.cache.pop("launching", None)
            base(k)
            more = k.cache.pop("spawned", [])
            [p.wait(25) for p in more]
        return k.lines

    w.round = round
    return w


def rnd(w, dt=0, k=None):
    """한 바퀴 — 시계 dt 초 앞으로 · 반환 = 로그 줄."""
    w.t += dt
    return w.round(k)


def seat(w, work, state="failed", at=None, step="git add", reason="worktree 가 이미 있음", done=False):
    """나노 1석 = 접수 → 배정 → 전달 · launch intent(state·at·step·reason) · 세션 0(부재)."""
    holder = "biz-%s-nano-%s#0" % (TEAM, work)
    steps = [["submit", "--command", "c-" + work, "--body", "본문-" + work, "--work", work],
             ["assign", "--work", work, "--holder", holder, "--evidence", "v1,v2", "--resources", "R-" + work],
             ["deliver", "--work", work]] + ([["complete", "--work", work, "--attempt", "a1"]] if done else [])
    for argv in steps:
        out, rc = w.CLI.run(argv + ["--root", str(w.root), "--team", TEAM])
        assert rc == 0, out
    kw._put(w.state / "ft20-switch" / (TEAM + ".json"), "{}")
    body = {"FT2_HOLDER": holder, "state": state, "at": at or stamp(w.t), "base": "origin/main", "step": step, "reason": reason}
    kw._put(w.runtime() / "launch" / ("%s@a1.intent" % work), body)
    return holder


def park(w, work, reason="launch-failed", attempt="a1"):
    """core park 1회 — 정상 꼴 쉼 줄(launch-failed)을 세계에 만든다 · keeper 가 이 줄을 보고 «이미 쉼» 길로 간다."""
    out, rc = w.CLI.run(["park", "--work", work, "--attempt", attempt, "--reason", reason, "--root", str(w.root), "--team", TEAM])
    assert rc == 0, out


def assigned(w, work, state="waiting", reason="정지"):
    """배정 원장 1장 — 도구가 쓰는 자리 그대로(.fable-team/state/card-assign/<카드>.json)."""
    kw._put(w.state / "card-assign" / (work + ".json"), {"state": state, "seat": "", "reason": reason, "since": w.t})


def released(w, work, reason="풀림"):
    assigned(w, work, "none", reason)


def tied(w, work):
    """그 work 로 나간 [긴급] 만 센다(다른 알림·하루 정리 줄에 흔들리지 않는다)."""
    return [x for x in kw._lines(str(w.mbox) + ".log") if x.startswith("send") and "[긴급]" in x and work in x]


def has(lines, *words):
    return [x for x in lines if all(word in x for word in words)]


def parked_count(w):
    return sum(1 for rec in w.journal() if rec["kind"] == "parked")


# ① K2 — 대기 중: 판정 줄은 남고 [긴급] 0 · park 다시 0
def c1(w):
    seat(w, "r9701")
    park(w, "r9701")
    assigned(w, "r9701")
    lines = rnd(w)
    assert has(lines, "UNKNOWN harness r9701", "launch-failed", "git add"), lines
    assert has(lines, "원장 대기(정지) — [긴급] 미룸"), lines   # K1 — 정상 실패와 의도한 미룸을 줄로 가른다
    assert tied(w, "r9701") == [], tied(w, "r9701")
    assert parked_count(w) == 1, (parked_count(w), lines)


# ② K2 — 대기 중 여러 바퀴(10분 · 1시간 · 하루) → 계속 0통 (날마다 다시 보내지 않는다)
def c2(w):
    c1(w)
    for dt in (600, 3600, 86400):
        rnd(w, dt=dt)
        assert tied(w, "r9701") == [], (dt, tied(w, "r9701"))


# ③ K3·K6 — 대기 중 미뤘다가 같은 날 풀리면 1통(미루는 동안 지문 장부에 날짜를 적지 않는다)
def c3(w):
    c1(w)
    released(w, "r9701")
    rnd(w, dt=60)
    assert len(tied(w, "r9701")) == 1, tied(w, "r9701")


# ④ K6 — 같은 날 두 번째 풀림은 0통(하루 1회 지문 우선)
def c4(w):
    c3(w)
    assigned(w, "r9701")
    rnd(w, dt=60)
    released(w, "r9701")
    rnd(w, dt=60)
    assert len(tied(w, "r9701")) == 1, tied(w, "r9701")


# ⑤ K1 · M7 — 사유가 «정지» 가 아니어도(선행) 같은 «대기» = 미룸
def c5(w):
    seat(w, "r9705")
    park(w, "r9705")
    assigned(w, "r9705", reason="선행")
    lines = rnd(w)
    assert tied(w, "r9705") == [] and has(lines, "UNKNOWN harness r9705", "launch-failed"), (lines, tied(w, "r9705"))


# ⑥ K1 — 사유 «사람» 도 미룸
def c6(w):
    seat(w, "r9706")
    park(w, "r9706")
    assigned(w, "r9706", reason="사람")
    rnd(w)
    assert tied(w, "r9706") == [], tied(w, "r9706")


# ⑦ K5 · M5 — 원장 없음 = 대기 아님 → 지금처럼 1통
def c7(w):
    seat(w, "r9707")
    park(w, "r9707")
    lines = rnd(w)
    assert len(tied(w, "r9707")) == 1, tied(w, "r9707")
    assert not has(lines, "원장 대기"), lines   # K1 — 대기가 아니면 미룸 꼬리 0


# ⑧ K5 · M5 — 원장이 깨졌다 = 대기 아님(판독 실패를 대기로 보지 않는다) → 1통
def c8(w):
    seat(w, "r9708")
    park(w, "r9708")
    kw._put(w.state / "card-assign" / "r9708.json", '{"state": "waiting"')   # 깨진 JSON
    rnd(w)
    assert len(tied(w, "r9708")) == 1, tied(w, "r9708")


# ⑨ K4 · M3 — 처음 실패한 바퀴(park=True)는 원장 대기여도 지금과 같다 = 1통
def c9(w):
    seat(w, "r9709")
    assigned(w, "r9709")
    lines = rnd(w)
    assert parked_count(w) == 1, lines
    assert len(tied(w, "r9709")) == 1, tied(w, "r9709")


# ⑩ M4 — 다른 사유 코드(intent-bad)의 [긴급] 은 원장 대기와 무관하게 지금 그대로
def c10(w):
    w.work("r9710", alive=True)   # worktree 폴더 없음 = intent-bad
    assigned(w, "r9710")
    lines = rnd(w)
    assert has(lines, "UNKNOWN harness r9710", "intent-bad"), lines
    assert len(tied(w, "r9710")) == 1, tied(w, "r9710")


# ⑪ K6 · ⑬ — 그날 이미 1통(첫 실패) → 대기 뒤 풀려도 그날은 0통 · 다음 날 1통
def c11(w):
    c9(w)
    assigned(w, "r9709")
    rnd(w, dt=60)
    released(w, "r9709")
    rnd(w, dt=60)
    assert len(tied(w, "r9709")) == 1, tied(w, "r9709")
    rnd(w, dt=86400)
    assert len(tied(w, "r9709")) == 2, tied(w, "r9709")


# ⑫ K6 · M8 — 이미 알린 attempt 가 다시 대기/해제를 되풀이해도 0통(지문 우선)
def c12(w):
    seat(w, "r9712")
    park(w, "r9712")
    rnd(w)   # 원장 없음 = 1통
    assert len(tied(w, "r9712")) == 1, tied(w, "r9712")
    tails = []
    for _ in range(2):
        assigned(w, "r9712")
        lines = rnd(w, dt=60)
        tails.append(bool(has(lines, "UNKNOWN harness r9712")))   # 판정 줄은 (판정·사유)가 바뀔 때만 남는다(r2058) = 미룬 바퀴는 새 줄 0
        released(w, "r9712")
        rnd(w, dt=60)
    assert tails == [False, False], tails   # 미룸 꼬리 단언 자리 = ①·⑭(그 좌석 첫 UNKNOWN 줄) · 여기서는 반복이 줄을 안 늘린다
    assert len(tied(w, "r9712")) == 1, tied(w, "r9712")


# ⑬ K7 — 전체 정지 중 = «예정 PARKED» 줄만 · [긴급] 0(지금 길 그대로)
def c13(w):
    seat(w, "r9713")
    park(w, "r9713")
    kw._put(w.state / "ALL_STOP.json", {"since": stamp(w.t), "why": "시험"})
    lines = rnd(w)
    assert has(lines, "예정 PARKED harness r9713", "launch-failed", "정지 중 kill·park 0"), lines
    assert tied(w, "r9713") == [], tied(w, "r9713")


# ⑭ K1 — 원장 사유는 줄바꿈을 지우고 20자까지만 꼬리에 적는다
LONG = "사람 확인 대기 ·\n선행 r2046 풀림 필요 · 오빠 답 기다림"


def c14(w):
    seat(w, "r9714")
    park(w, "r9714")
    assigned(w, "r9714", reason=LONG)
    lines = rnd(w)
    want = " ".join(LONG.split())[:20].strip()
    assert want and want != LONG and "\n" not in want, want
    assert has(lines, "UNKNOWN harness r9714", "원장 대기(%s) — [긴급] 미룸" % want), lines
    assert tied(w, "r9714") == [], tied(w, "r9714")


CASES = {"①": c1, "②": c2, "③": c3, "④": c4, "⑤": c5, "⑥": c6, "⑦": c7,
         "⑧": c8, "⑨": c9, "⑩": c10, "⑪": c11, "⑫": c12, "⑬": c13, "⑭": c14}
NEEDS = {"⑩": dict(nano_max="1")}

KS = "adapters/pi/keeper_settle.py"
DEFER = '        wait = "" if park else self.ledger_wait(work)\n        if wait:'
VERDICT = '            self.verdict(team, work, holder, "UNKNOWN", LAUNCH_FAILED, "%s · 원장 대기(%s) — [긴급] 미룸" % (self.failed_tail(intent), wait))\n            return "PARKED"'
WAIT_REASON = '        why = " ".join(str(doc.get("reason") or "-").split())[:20].strip()'
MUTANTS = {   # (파일, 고칠 글자, 새 글자, 반드시 FAIL 이어야 하는 사례)
    "M1": (KS, DEFER, '        if False:', ("①",)),                                    # 원장 대조를 뺀다
    "M2": (KS, VERDICT, '            self.state.setdefault("alerts", {})["%s|%s|%s|%s" % (team, work, attempt, LAUNCH_FAILED)] = self.stamp()[:10]\n'
           + VERDICT, ("③",)),                                                          # 미루면서 지문 장부에 날짜를 적는다
    "M3": (KS, DEFER, '        wait = self.ledger_wait(work)\n        if wait:', ("⑨",)),  # 처음 실패(park=True) 길에도 미룬다
    "M4": (KS, '        self.verdict(team, work, seat, "UNKNOWN", code, tail)\n        self.alert(team, work, attempt, seat, code, tail)',
           '        self.verdict(team, work, seat, "UNKNOWN", code, tail)\n        if not self.ledger_wait(work):\n'
           '            self.alert(team, work, attempt, seat, code, tail)', ("⑩",)),      # 모든 사유에 미룬다
    "M5": (KS, '        if doc.get("state") not in ASSIGN_WAIT:',
           '        if doc.get("state") not in ASSIGN_WAIT and doc:', ("⑦", "⑧")),      # 원장 없음·깨짐을 «대기» 로 본다
    "M6": (KS, VERDICT, '            return "PARKED"', ("①",)),                          # 미룰 때 판정 줄도 안 낸다
    "M7": (KS, WAIT_REASON,
           '        return "정지" if doc.get("reason") == "정지" else ""', ("⑤",)),      # 사유가 정지일 때만 미룬다
    "M8": (KS, DEFER + "\n" + VERDICT,              # 해제를 «전이 전용 열쇠» 로 따로 보낸다 = 기존 날짜 지문 무시(DA H1 이 기각한 길)
           DEFER + '\n            self.state.setdefault("deferred", {})["%s|%s|%s" % (team, work, attempt)] = 1\n' + VERDICT
           + '\n        if self.state.setdefault("deferred", {}).pop("%s|%s|%s" % (team, work, attempt), 0):\n'
           + '            self.notify(team, "release|%s|%s|%s|%s" % (team, work, attempt, self.stamp()[:10]), "[긴급] UNKNOWN %s %s %s release" % (team, work, holder))',
           ("⑫",)),
    "M9": (KS, '"%s · 원장 대기(%s) — [긴급] 미룸" % (self.failed_tail(intent), wait)', 'self.failed_tail(intent)',
           ("①",)),                                                                    # 미룸 꼬리를 안 붙인다(정상 실패와 구별 0)
    "M10": (KS, WAIT_REASON, '        return str(doc.get("reason") or "-")', ("⑭",)),   # 사유 줄바꿈·20자를 안 가린다
}


@pytest.mark.parametrize("name", list(CASES))
def test_case(name, tmp_path, monkeypatch):
    CASES[name](world(tmp_path, monkeypatch, **NEEDS.get(name, {})))


@pytest.mark.parametrize("name", list(MUTANTS))
def test_mutant(name, tmp_path, monkeypatch):
    path, old, new, cases = MUTANTS[name]
    tree = tmp_path / "m" / "ft2"
    shutil.copytree(FT2, tree, ignore=shutil.ignore_patterns("tests", "__pycache__"))
    text = (tree / path).read_text(encoding="utf-8")
    assert text.count(old) == 1, (name, old)
    (tree / path).write_text(text.replace(old, new), encoding="utf-8")
    for i, case in enumerate(cases):
        (tmp_path / ("w%d" % i)).mkdir()
        with pytest.raises(AssertionError):
            CASES[case](world(tmp_path / ("w%d" % i), monkeypatch, ft2=tree, **NEEDS.get(case, {})))
    (tmp_path / "ok").mkdir()   # 원본으로 같은 사례 1회 더 = PASS
    CASES[cases[0]](world(tmp_path / "ok", monkeypatch, **NEEDS.get(cases[0], {})))
