"""r2573 ft2 keeper — 쉼으로 닫힌 뒤 배정 원장에 seat 만 남고 ft2 owner 가 없는 카드를 keeper 가 고르지 않을 때
로그 1줄 «건너뜀 · 다시 여는 법»(NEXT-SKIP … «다시 열기 = …») · 수동 닫기 끝 줄(CLOSED-MANUAL)도 같은 안내.
값 = 그 팀 ft2 state 의 쉼(parked) 행(«-» = 행 없음 · at 글자 = 쉼 시각 · 열쇠 없음 = 미등록) — 재개 줄 종류가 아니다(H1).
카드에 «- 세트:» 증거 줄이 있으면(인수 끝 · 착지 대기) 안내 0줄(H2) · 고르는 판정·재개 조건·ready 차례·why 셈은 지금과 같다.
반례 ①~⑱ · 변이 M1~M11 · M13. 기준판(줄 0) = ① ③ ⑥ ⑦ ⑪ ⑭ ⑮ Red.
⑲(재개 진행/resumed 갈래)는 이 카드가 손대지 않은 자리다 — choose 가 그 카드를 줄 자리 앞에서 continue 로 먼저 뺀다(r2159 그대로).
무대 = r2113 세계(r1871 world · 임시 root·git·가짜 tmux·launch·record · card-assign 원장 json) · 실 tmux·명부·ft2 원장·설치 0 · sleep 0.
겹침 = r2252(재개 줄 참 = 고름 · 조건 그대로) · r2571(같은 keeper_manual_close.py 끝 줄 = park=already · LEFT-MANUAL 보존) ·
착지 순서 r2539 → r2571 → r2573 · 기준 head = r2571 이 착지한 팩 main cdce710bb526.
"""
import importlib.util, json, shutil, tempfile, time, types  # noqa: E401
from pathlib import Path
import pytest

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("keeper_next_r2573_r2113", str(HERE / "keeper_next_reopen_name_tail_r2113.py"))
r13 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r13)
base, kw, hand, card = r13.base, r13.kw, r13.hand, r13.card
S, KN, DAY = "r9927-Skip", "adapters/pi/keeper_next.py", "2026-11-16T"
MC = "adapters/pi/keeper_manual_close.py"
NH = "biz-harness-nano-%s#0" % S
HOW = "다시 열기 ="
SET = "- 세트: %s · 시험: pytest t.py rc=0 · 이슈: 0" % ("cd" * 20)
TELL_OLD = "            assigned.add(stem)\n            assigned_tell(k, team, stem, state)"   # 기준판 대조 = 이 두 줄 뺀 판
FIELDS = ("generations", "owners", "reservations", "deliveries", "done", "reassess_done", "released",
          "owners_recovered", "uncertain", "lanes", "refusals", "reopens", "lifted", "imported",
          "close_receipts", "returned", "parked", "withdrawn")   # core/record.recover_state 투영 칸


def epoch(at):
    return time.mktime(time.strptime(at, "%Y-%m-%dT%H:%M:%S"))


def seat(w, released=None):   # 쉼 뒤 꼴 — 옛 holder 원장 seat 남음(쉼은 ft2 owner 만 푼다) · released = «전달됨» 도 풀린 원장(r2111 꼴)
    body = {"state": "seat", "seat": NH, "since": 1.0, "updated": 1.0}
    kw._put(w.state / "card-assign" / (S + ".json"), body if released is None else dict(body, released_at=released))


def owned(w, at):   # owner 있음 = «배정됨» 이 owner 쪽인 갈래
    run = lambda *a: w.CLI.run(list(a) + ["--root", str(w.root), "--team", "harness"])   # noqa: E731
    for argv in (("submit", "--command", "c-" + S, "--body", "b-" + S, "--work", S),
                 ("assign", "--work", S, "--holder", NH, "--evidence", "v1,v2"), ("deliver", "--work", S)):
        out, rc = run(*argv)
        assert rc == 0, out
    kw._put(w.runtime() / "launch" / ("%s@%s.intent" % (S, out["attempt"])), {"FT2_HOLDER": NH, "state": "opened", "at": at})


def sleep(w, at, reason="idle-done"):
    """ft2 state 의 쉼(parked) 행 = 이 갈래에 남은 까닭(가짜 state). at None = 행 없음(= 지난 쉼을 새 dispatch 가 끝낸 꼴).
    journal fold 가 parked 를 다시 만들지 않도록 checkpoint(journal_base)로 굳힌다 — 임시 루트 안에서만."""
    path = w.runtime() / "state.json"
    st = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"schema": 1, "revision": 0, "pending": [], "attempts": {}}
    proj = {name: st.get(name) for name in FIELDS if st.get(name)}
    rows = dict(proj.get("parked") or {})
    if at is None:
        rows.pop(S, None)
    else:
        rows[S] = {"attempt": None, "at": at, "reason": reason, "released": []}
    proj["parked"] = rows
    last = (w.journal() or [{"seq": 0}])[-1]["seq"]
    st["journal_base"] = {"upto": last, "count": max(st.get("revision", 0), last), "proj": proj}
    kw._put(path, st)


def pick(w, k):   # 바퀴의 fetch 자리 = 루트 리포 fetch 1회(카드 읽기 = origin/main) → choose 1회 · 같은 keeper = 기억(assigned_seen) 이어짐
    kw._git(w.root, "fetch", "-q", "origin")
    before = len(k.lines)
    getattr(k, "cache", {}).clear()   # 바퀴(프로세스)마다 새로 = once 캐시를 다음 바퀴로 끌고 가지 않는다
    got = w.K.closing.keeper_next.choose(k, "harness")
    return (got or [None])[0], k.lines[before:]


def told(lines):   # «건너뜀 · 다시 여는 법» 1줄 — 이 카드 것만
    return [x for x in lines if x.startswith("NEXT-SKIP harness %s 건너뜀" % S) and HOW in x]


def notes(w):   # [다음 없음] 쪽지 줄(r1871 세계 우편 로그)
    return [x for x in kw._lines(str(w.mbox) + ".log") if "[다음 없음]" in x]


def c1(w, mp):   # ① 원장 seat · owner 0 · parked idle-done · 재개 줄 0 → NEXT-SKIP 1줄(글자 = K1) · 고른 카드 0
    seat(w), card(w, S), sleep(w, DAY + "11:05:00")
    got, lines = pick(w, w.keeper())
    assert got is None and len(told(lines)) == 1 and "쉼 idle-done" in told(lines)[0], (got, lines)


def c2(w, mp):   # ② ① 을 두 바퀴 → 줄 1(둘째 바퀴 0)
    hand(w, S, DAY + "10:50:00", holder=NH), seat(w), card(w, S), sleep(w, DAY + "11:05:00")
    k = w.keeper()
    got, first = pick(w, k)
    got2, second = pick(w, k)
    assert got is None and got2 is None and len(told(first)) == 1 and told(second) == [], (first, second)


def c3(w, mp):   # ③ ① 뒤 다시 쉼(parked at 바뀜) → 줄 1 더
    hand(w, S, DAY + "10:50:00", holder=NH), seat(w), card(w, S), sleep(w, DAY + "11:05:00")
    k = w.keeper()
    got, first = pick(w, k)
    sleep(w, DAY + "12:10:00")
    got, lines = pick(w, k)
    assert got is None and len(told(first)) == 1 and len(told(lines)) == 1, (got, first, lines)


def c4(w, mp):   # ④ owner 있음 → 줄 0 · 고름 0(이 갈래 아님)
    owned(w, DAY + "10:50:00"), seat(w), card(w, S), sleep(w, DAY + "11:05:00")
    got, lines = pick(w, w.keeper())
    assert got is None and told(lines) == [], (got, lines)


def c5(w, mp):   # ⑤ «- 재개:» 줄이 intent 시각 뒤 → 열림 · 줄 0
    hand(w, S, DAY + "10:50:00", holder=NH), seat(w), card(w, S, "- 재개: " + DAY + "16:28:00"), sleep(w, DAY + "11:05:00")
    got, lines = pick(w, w.keeper())
    assert got == S and told(lines) == [], (got, lines)


def c6(w, mp):   # ⑥ 카드에 «- 세트: <40hex> · 시험: … rc=0 · 이슈: 0» 줄 → 줄 0(착지 대기 = 전이 감시 몫)
    hand(w, S, DAY + "10:50:00", holder=NH), seat(w), card(w, S, SET), sleep(w, DAY + "11:05:00")
    got, lines = pick(w, w.keeper())
    assert got is None and told(lines) == [], (got, lines)


def c7(w, mp):   # ⑦ 원장 seat · parked 행 없음 → 줄 1(«쉼 기록 없음»)
    seat(w), card(w, S)
    got, lines = pick(w, w.keeper())
    assert got is None and len(told(lines)) == 1 and "쉼 기록 없음" in told(lines)[0], (got, lines)


def c8(w, mp):   # ⑧ 재개 줄 꼴 깨짐 → 지금의 «판정 불가» 1줄 + K1 줄 1(둘 다 값 바뀔 때만)
    hand(w, S, DAY + "10:50:00", holder=NH), seat(w), card(w, S, "- 재개: 어제쯤"), sleep(w, DAY + "11:05:00")
    got, lines = pick(w, w.keeper())
    bad = [x for x in lines if x.startswith("판정 불가") and "재개 줄 꼴" in x]
    assert got is None and len(bad) == 1 and len(told(lines)) == 1, (got, lines)


def c9(w, mp):   # ⑨ 원장 reason 이 막는 값(정지) ∧ seat 아님 → 지금과 같음(K1 줄 0)
    hand(w, S, DAY + "10:50:00", holder=NH), card(w, S), sleep(w, DAY + "11:05:00")
    kw._put(w.state / "card-assign" / (S + ".json"), {"state": "none", "reason": "정지", "since": 1.0, "updated": 1.0})
    got, lines = pick(w, w.keeper())
    assert got is None and told(lines) == [], (got, lines)


def c11(w, mp):   # ⑪ 쉼 사유에 줄바꿈 · 200자 → 20자 · 한 줄
    hand(w, S, DAY + "10:50:00", holder=NH), seat(w), card(w, S), sleep(w, DAY + "11:05:00", "idle\n" + "가" * 200)
    got, lines = pick(w, w.keeper())
    one = told(lines)
    assert len(one) == 1 and "\n" not in one[0] and ("가" * 15) in one[0] and ("가" * 16) not in one[0], (got, one)


def c14(w, mp):   # ⑭ ⑦ 을 두 바퀴 → 첫 바퀴 1줄 · 둘째 바퀴 0줄(기억 값 «-»)
    seat(w), card(w, S)
    k = w.keeper()
    got, first = pick(w, k)
    got2, second = pick(w, k)
    assert got is None and got2 is None and len(told(first)) == 1 and told(second) == [], (first, second)
    assert k.state["assigned_seen"]["harness|" + S] == "-", k.state["assigned_seen"]


def c15(w, mp):   # ⑮ parked 없음 → at 생김 → 다시 없음 → 없음 그대로 = 바퀴마다 1 · 1 · 1 · 0줄(합 3)
    seat(w), card(w, S)
    k, counts = w.keeper(), []
    for at in (None, DAY + "11:05:00", None, None):   # 4바퀴: 행 없음 → 쉼 → 없음 → 없음
        sleep(w, at)
        counts.append(len(told(pick(w, k)[1])))
    assert counts == [1, 1, 1, 0], counts


def c12(w, mp):   # ⑫ 수동 닫기 park=done 끝 줄 = 기준판(r2571 착지 판) 글자 + 안내 꼬리 · rc 0
    mod = module(w.ft2)
    assert mod.REOPEN_HOW == " · " + HOW + " " + w.K.closing.keeper_next.REOPEN_HOW, mod.REOPEN_HOW
    for hands_path, probes in ((False, ("absent",)), (True, ("alive", "absent"))):
        got, left, tree = closed(mod, K(w.tmp, probes), hands_path, "done", mp)
        assert len(got) == 1 and got[0].endswith(mod.REOPEN_HOW) and (HOW + " ") in got[0], (hands_path, got)
        assert len(left) == (0 if hands_path else 1), (hands_path, left)


def c13(w, mp):   # ⑬ 수동 닫기 park 실패(rc ≠ 0) → PARK-FAILED 줄 · 안내 0 · CLOSED-MANUAL 0 · rc 7
    mod, k = module(w.ft2), K(w.tmp, ("alive",))
    mp.setattr(mod.cli, "run", lambda argv: ({"result": "접수 거부", "reason": "테스트"}, 1))
    k.proj_of = lambda team: {"result": "접수 성공", "works": {}}
    tree, who = tempfile.mkdtemp(), "biz-harness-nano-x#0"
    mp.setattr(mod.endings, "latest", lambda k, team: {"w-" + S: ("a1", who)})
    rc = mod.hands(k, "harness", "w-" + S, "a1", {"worktree": tree}, who, "2222222222.222222", "biz-planner-master-0#1", "380700", "idle-done")
    bad = [x for x in k.lines if x.startswith("PARK-FAILED")]
    assert rc == 7 and len(bad) == 1 and HOW not in bad[0], (rc, k.lines)
    assert [x for x in k.lines if x.startswith("CLOSED-MANUAL")] == [], k.lines


def c16(w, mp):   # ⑯ 수동 닫기 «이미 쉼 = 멱등» 답(park=already) → 끝 줄 = r2571 착지 판 글자 + 안내 꼬리 · rc 0
    mod = module(w.ft2)
    for hands_path, probes in ((False, ("absent",)), (True, ("alive", "absent"))):
        got, left, tree = closed(mod, K(w.tmp, probes), hands_path, "already", mp)
        assert len(got) == 1 and got[0].endswith(mod.REOPEN_HOW) and "park=already" in got[0], (hands_path, got)


def c17(w, mp):   # ⑰ 세션 없는 석 성공(done · already 각각) → CLOSED-MANUAL(꼬리) 바로 다음 줄 = LEFT-MANUAL 1줄 · r2571 판과 바이트 같음
    mod = module(w.ft2)
    for park in ("done", "already"):
        got, left, tree = closed(mod, K(w.tmp, ("absent",)), False, park, mp)
        assert len(got) == 1 and len(left) == 1 and HOW not in left[0], (park, got, left)
        assert left[0] == ("LEFT-MANUAL harness biz-harness-nano-x#0 판정 2222222222.222222 · worktree %s 남음 · "
                           "명부 행 = 이 도구 손 0 · 치우기 = 사람 손(git worktree remove %s)" % (tree, tree)), left


def c18(w, mp):   # ⑱ 고를 카드 0(① 카드만) → [다음 없음] 글자·횟수와 why 셈이 기준판과 같음 · NEXT-SKIP 1줄
    hand(w, S, DAY + "10:50:00", holder=NH), seat(w), card(w, S), sleep(w, DAY + "11:05:00")
    got, lines = pick(w, w.keeper())
    assert got is None and len(told(lines)) == 1, (got, lines)
    one = notes(w)
    assert len(one) == 1 and "막힌 사유별 배정됨 1 · 막힌 카드 배정됨 %s" % S in one[0], one   # why 셈 = 사유별 1(기준판과 같다)


CASES = {"1": c1, "2": c2, "3": c3, "4": c4, "5": c5, "6": c6, "7": c7, "8": c8, "9": c9,   # id = 카드 반례 번호(ASCII)
         "11": c11, "12": c12, "13": c13, "14": c14, "15": c15, "16": c16, "17": c17, "18": c18}
MUTANTS = {
    "M1": ('        k.log("NEXT-SKIP", team, "%s 건너뜀 — 원장 배정됨(원장 좌석 표시 · ft2 owner 0 · %s) · 다시 열기 = %s"\n              % (stem, why, REOPEN_HOW))',
           "        pass", ("1",)),   # K1 줄 뺌
    "M2": ('    if book.get(key) != val:\n        book[key] = val\n        k.log("NEXT-SKIP", team, "%s 건너뜀 — 원장 배정됨',
           '    if True:\n        book[key] = val\n        k.log("NEXT-SKIP", team, "%s 건너뜀 — 원장 배정됨', ("2",)),   # 기억 대조 뺌(바퀴마다)
    "M3": ("    val, why = sleep_show(state, stem)", "    val, why = stem, sleep_show(state, stem)[1]", ("3",)),   # 기억 값을 카드 이름만으로
    "M4": ('        elif block == "배정됨" and stem not in owners and not show_set:', '        elif block == "배정됨" and not show_set:', ("4",)),   # owner 있어도 줄
    "M5": (" and not show_set", "", ("6",)),   # «- 세트:» 줄 대조 뺌
    "M6": ("            assigned_tell(k, team, stem, state)", "            assigned_tell(k, team, stem, state)\n            block = \"\"", ("1",)),   # 줄을 내면서 block 을 풂
    "M8": ("            block = led.get(\"reason\") if led.get(\"reason\") in BLOCK else pre   # «배정됨» 만 건너뜀(원장 사유·카드 막힘은 그대로)",
           "            block = led.get(\"reason\") if led.get(\"reason\") in BLOCK else pre\n            assigned_tell(k, team, stem, state)", ("5",)),   # reopen 참인 바퀴에도 줄
    "M9": ('    if book.get(key) != val:\n        book[key] = val\n        k.log("NEXT-SKIP", team, "%s 건너뜀 — 원장 배정됨',
           '    if book.get(key) != val:\n        book[key] = val if val != "-" else None\n        k.log("NEXT-SKIP", team, "%s 건너뜀 — 원장 배정됨', ("14", "15")),   # «쉼 기록 없음» 을 미등록과 같은 값으로
    "M13": ("            assigned.add(stem)", '            why.update({"배정됨": why.get("배정됨", 0) + 1})\n            assigned.add(stem)', ("18",)),
}


def module(ft2=kw.FT2):   # 시험 대상 = 팩 자리(변이는 사본)
    spec = importlib.util.spec_from_file_location("ft2_manual_r2573_%d" % abs(hash(str(ft2))), str(Path(ft2) / MC))
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def closed(mod, k, hands_path, park, mp):
    """dead_hands(세션 없음 갈래) · hands(살아 있는 갈래). park = («done»|«already»|«none», 0) 대역 · intent worktree = 진짜 임시 폴더(dirty 판독·«남음»)."""
    tree = tempfile.mkdtemp()
    mp.setattr(mod.endings, "latest", lambda k, team: {})
    mp.setattr(mod, "parked", lambda *a: (park, 0))
    args = ("harness", "w-" + S, "biz-harness-nano-x#0", "2222222222.222222", "biz-planner-master-0#1", "380700", "idle-done")
    if hands_path:
        mod.hands(k, args[0], args[1], "a1", {"worktree": tree}, *args[2:], note="")
    else:
        mod.dead_hands(k, args[0], args[1], *args[2:], note="", latest={}, intent={"worktree": tree})
    return [x for x in k.lines if x.startswith("CLOSED-MANUAL")], [x for x in k.lines if x.startswith("LEFT-MANUAL")], tree


class K:   # 수동 닫기 대역 — dead_hands·hands 가 읽는 것만(실 tmux·세션·명부 0)
    def __init__(s, tmp, probes=("absent",)):
        s.lines, s.state, s.tmux, s.root = [], {"open": {}}, "tmux", str(tmp / "root")
        s.env = {"HOME": str(tmp / "home"), "FT2_PI_SESSIONS": str(tmp / "sessions")}
        s.probes, s.close_old = list(probes), types.SimpleNamespace(resume=lambda *a, **kw: "")

    def log(s, kind, team, msg=""):
        s.lines.append(("%s %s %s" % (kind, team, msg)).strip())

    def git(s, cwd, *a):
        return (0, "", "")   # dirty 판독 = 깨끗

    def probe(s, seat):
        return s.probes.pop(0) if s.probes else "absent"

    def attached(s, seat):
        return "free"

    def call(s, argv):
        return (0, "❯ ", "") if argv[1] == "capture-pane" else (0, "", "")

    def read_json(s, path):
        return None

    def resume_ok(s, seat):
        return True


def run(name, tmp, mp, ft2=kw.FT2):
    w = base.world(tmp, mp, {}, ft2=ft2)
    CASES[name](w, mp)


@pytest.mark.parametrize("name", list(CASES))
def test_case(name, tmp_path, monkeypatch):
    run(name, tmp_path, monkeypatch)


def pair(tmp_path, case, ft2, mp):   # 변이 사본 = 사례가 Red · 원본 = 같은 사례 Green(대조)
    bad, good = tmp_path / ("bad" + case), tmp_path / ("good" + case)
    bad.mkdir(), good.mkdir()
    with pytest.raises(AssertionError):
        run(case, bad, mp, ft2=ft2)
    run(case, good, mp)


def copy_tree(tmp_path):
    tree = tmp_path / "m" / "ft2"
    shutil.copytree(kw.FT2, tree, ignore=shutil.ignore_patterns("tests", "__pycache__"))
    return tree


def mutate_manual(tree, old, new, count=1, rel=MC):
    path = tree / rel
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == count, (old, text.count(old))
    path.write_text(text.replace(old, new), encoding="utf-8")


def test_c10_baseline(tmp_path, monkeypatch):   # (10) 같은 입력((1) 카드 + 고를 카드 2장)을 기준판과 대조 — 고른 카드·[다음 없음]·줄 수
    tree = copy_tree(tmp_path)
    mutate_manual(tree, TELL_OLD, "            pass", rel=KN)
    old_dir, new_dir = tmp_path / "old", tmp_path / "new"
    old_dir.mkdir(), new_dir.mkdir()
    picks = []
    for where, ft2 in ((old_dir, tree), (new_dir, kw.FT2)):
        w = base.world(where, monkeypatch, {}, ft2=ft2)
        hand(w, S, DAY + "10:50:00", holder=NH), seat(w, epoch(DAY + "10:51:00")), card(w, S), sleep(w, DAY + "11:05:00")
        card(w, "r9928-Open"), card(w, "r9929-Open")
        got, lines = pick(w, w.keeper())
        picks.append((got, len(told(lines)), notes(w)))
    assert picks[0][0] == picks[1][0] == "r9928-Open" and picks[0][2] == picks[1][2] == [], picks
    assert (picks[0][1], picks[1][1]) == (0, 1), picks   # 다른 것 = NEXT-SKIP 1줄뿐

