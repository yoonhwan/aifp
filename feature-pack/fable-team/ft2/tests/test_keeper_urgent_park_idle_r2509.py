"""r2509 ft2 keeper — ① 긴급 카드 줄 꼴이 틀려도 그 바퀴에 팀장이 알고(하루 1통) ② 칸이 다 차 있으면 손 놓고 기다리는 나노 1석을 그 바퀴에 쉼으로 돌려 다음 fill 이 긴급 카드를 연다 (반례 ①~⑰ · 변이 M1~M14).
대역 = r1812 세계(임시 root·git 리포·가짜 tmux·가짜 ps·가짜 mbox) + 가짜 launch·record · project 대역(접수 용량 숫자) · 임시 루트만 · 실 tmux·명부·ft2 원장·mbox·설치 0 · sleep 0 · 시험 1개 70초 안.
기준판 = ①③⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰ Red. 변이는 사본에서만 · 원본으로 1회 더.
r2557 — 사례 19칸(33초)과 변이 14칸(29초)을 한 파일에서 돌리면 62.5초로 70초 경계에 걸려, 변이만 자매 파일
`test_keeper_urgent_park_idle_mutants_r2509.py` 로 옮겼다(칸 수·단언 글자 그대로 · 파일마다 45초 안).
"""
import importlib.util, json, os, sys  # noqa: E401
from pathlib import Path
import pytest

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("keeper_world_r1812", str(HERE / "keeper_world_r1812.py"))
kw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kw)
FT2, TEAM = kw.FT2, "harness"
U, V, G = "r9501-u", "r9502-v", "r9503-g"   # U·V = 긴급 카드 · G = 일반 카드
S1, S2 = "r9401-a", "r9402-b"   # 나노 일(쉼 후보) · SD = 완료 난 일(완료 포함 판정용)
SD = "r9403-c"
URGENT, NO, BAD = "- 긴급: 예\n", "- 긴급: 아니오\n", "- 긴급: 예 — 설명\n"
LS = 'if a[0] == "list-sessions": print("\\n".join(d["alive"])); sys.exit(0)\n'
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
CARD = "# 인덱스: %s\n%s- 상태: 대기\n- 대상: 팩 feature-pack/ft2/x.py\n- 대기 사유: 없음\n- 배정: 없음\n"


def world(tmp, mp, cards=None, cap="8", ft2=FT2):
    """세계 = r1812 대역 + 가짜 tmux(list-sessions)·launch·record · 나노 상한 cap · 카드 루트 표 harness 행 · 카드 {stem: 머리 줄}."""
    w = kw.World(tmp, mp, ft2)
    b = tmp / "bin"
    tm = kw.TMUX.replace("__PY__", sys.executable)
    i = tm.index('if a[0] == "kill-session"')
    kw._put(b / "tmux", tm[:i] + LS + tm[i:])
    kw._put(b / "launch.py", LAUNCH), kw._put(b / "record", RECORD), (b / "record").chmod(0o755)
    w.env.update(FT2_KEEPER_LAUNCH=str(b / "launch.py"), FT2_CARD_ASSIGN_BIN=str(b / "record"), HOME=str(tmp / "home"), FT2_TEAM_NANO_MAX=cap,
                 GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="core.quotepath", GIT_CONFIG_VALUE_0="false")   # 가짜 HOME = 실 ~/.claude 문턱 읽기 0
    kw._put(w.state / "directive-roots.tsv", "harness\t.\torigin/main\tdesign/harness/indices\n")
    w.commit("biz", {"design/harness/indices/대기/%s.md" % s: CARD % (s, head) for s, head in (cards or {}).items()}, "main")
    w.enable()
    return w


def keeper(w, mp, capacity):
    """project 가 돌려줄 접수 용량(숫자 또는 dict = 시험이 직접 바꾼다) · 다른 동사는 진짜 core 로 · 쉼(park rc0)이면 용량 1 줄음(③⑪ 실사슬)."""
    k = w.keeper()
    nx_cli = type(k).close.__globals__["keeper_next"].cli   # keeper_next 사본(cli 모듈도 사본)
    ks_cli = type(k).look.__globals__["cli"]                # keeper_settle 사본(park·project 부름)
    calls = []
    book = {"n": capacity} if isinstance(capacity, int) else capacity

    def run(argv, real=nx_cli.run):
        calls.append(argv[0])
        if argv[0] == "project":
            return {"result": "접수 성공", "team": TEAM, "capacity": book["n"], "remaining": book["n"]}, 0
        out = real(argv)
        if argv[0] == "park" and out[1] == 0 and not book.get("held"):   # held = 쉼이 용량을 안 놓는 세계(⑰)
            book["n"] -= 1
        return out
    mp.setattr(nx_cli, "run", run), mp.setattr(ks_cli, "run", run)
    return k, calls, book


def nh(stem, seat=0, gen=0):   # r2504 — 석 칸 + 세대
    return "biz-%s-nano-%d-%s#%d" % (TEAM, seat, stem[:40], gen)


def nano(w, work, idle=400, done=False, pane="✻ Brewed for 3s\n❯ ", turn="stop"):
    """나노 1석 = 일 1개 + 살아 있는 세션 + 그 세션 jsonl(무활동 idle초 · 마지막 줄 turn) · 일 폴더도 만든다(intent 주소)."""
    seat = w.work(work, done=done, alive=True, pane=pane, turn=turn)
    tree = str(w.tmp / "wt" / work)
    Path(tree).mkdir(parents=True, exist_ok=True)
    log = Path(w.env["FT2_PI_SESSIONS"]) / ("--%s--" % tree.strip("/").replace("/", "-")) / "s.jsonl"
    os.utime(log, (w.t - idle, w.t - idle))
    return seat


def parked(w):
    return [r["work"] for r in w.journal() if r["kind"] == "parked"]


def accepted(w, work):
    return [r["work"] for r in w.journal() if r["kind"] == "accept" and r["work"] == work]


def told(w):
    return [x for x in kw._lines(str(w.mbox) + ".log") if "긴급 줄 꼴 틀림" in x]


def c1(w, mp):   # ① «- 긴급: 예 — 설명» → [긴급] 1통(틀린 줄·고칠 꼴) · 같은 날 다음 바퀴 0
    nano(w, S1)
    k, calls, book = keeper(w, mp, 7)
    w.round(k), w.round(k)   # 같은 날 두 바퀴 = 1통
    got = told(w)
    assert len(got) == 1 and "«- 긴급: 예 — 설명»" in got[0] and "- 긴급: 예" in got[0], (got, k.lines)
    assert [x for x in k.lines if x.startswith("NOTIFIED")], k.lines
    w.t += 86400   # 날이 바뀌면 그 카드도 다시 1통(열쇠 = 날짜|urgent-form|팀|카드)
    w.round(k)
    assert len(told(w)) == 2, (told(w), k.lines)


def c2(w, mp):   # ② «- 긴급: 예» · «- 긴급: 아니오» → 0통
    nano(w, S1)
    k, calls, book = keeper(w, mp, 7)
    w.round(k)
    assert told(w) == [], (told(w), k.lines)


def c3(w, mp):   # ③ 접수 8/8 · 긴급 · 유휴 400·500초 2석 → 더 오래 쉰 1석만 쉼 · 다음 바퀴 긴급 열림
    nano(w, S1, idle=400), nano(w, S2, idle=500)
    k, calls, book = keeper(w, mp, 8)
    w.round(k)
    assert parked(w) == [S2] and "submit" not in calls, (parked(w), calls, k.lines)   # 더 오래 쉰 석 · 그 바퀴 새 열기 0
    assert any(x.startswith("URGENT-PARK") and " 접수 8 → 7" in x for x in k.lines), k.lines
    w.round(k)
    assert accepted(w, U) == [U], (accepted(w, U), k.lines)   # 다음 fill 이 긴급 카드에 그 칸을 쓴다


def c4(w, mp):   # ④ 접수 8/8 · 일반 카드만 → 쉼 0
    nano(w, S1)
    k, calls, book = keeper(w, mp, 8)
    w.round(k)
    assert parked(w) == [] and not any(x.startswith("URGENT-PARK") for x in k.lines), k.lines


def c5(w, mp):   # ⑤ 긴급 · 모든 나노 턴 진행 중(stopReason toolUse) → 쉼 0 · FILL-WAIT 그대로
    nano(w, S1, turn="toolUse")   # pane 글자 0 + tmuxc 판독 실패 = 2차 판독(rest ×2) 길
    kw._put(str(w.tm) + ".tmuxc_rc", "1")
    k, calls, book = keeper(w, mp, 8)
    w.round(k)   # 2차 판독 표본 1개(pending)
    w.t += 30   # 표본 2개 · 간격 30초 = 쉼
    w.round(k)
    assert parked(w) == [] and any(x.startswith("FILL-WAIT") for x in k.lines), k.lines


def c6(w, mp):   # ⑥ 유휴 200초 → 쉼 0
    nano(w, S1, idle=200)
    k, calls, book = keeper(w, mp, 8)
    w.round(k)
    assert parked(w) == [], k.lines


def c7(w, mp):   # ⑦ 유휴 400초인데 막는 미읽음 1 → 쉼 0
    nano(w, S1)
    kw._put(str(w.mbox) + ".pending", "1")
    k, calls, book = keeper(w, mp, 8)
    w.round(k)
    assert parked(w) == [], k.lines


def c8(w, mp):   # ⑧ 칸 남음(7/8) → 쉼 0 · 지금 고르기
    nano(w, S1)
    k, calls, book = keeper(w, mp, 7)
    w.round(k)
    assert parked(w) == [] and accepted(w, U) == [U], (parked(w), accepted(w, U), k.lines)


def c9(w, mp):   # ⑨ 팀 PAUSED · SPAWN_HOLD → 쉼 0
    kw._put(w.state / "harness-tick" / "PAUSED", "판정 1 · 2026-11-14T09:00:00 · 시험용 팀 정지 표식\n")
    nano(w, S1)
    k, calls, book = keeper(w, mp, 8)
    w.round(k)
    assert parked(w) == [], k.lines


def c9s(w, mp):   # ⑨s SPAWN_HOLD 표식(판정 불가 = 관문 거짓) → 쉼 0
    kw._put(w.state / "SPAWN_HOLD", {"verdict": 0})
    nano(w, S1)
    k, calls, book = keeper(w, mp, 8)
    w.round(k)
    assert parked(w) == [], k.lines


def c10(w, mp):   # ⑩ 나노 정원만 참(접수 남음 2/8) → ③ 과 같은 쉼 1석
    nano(w, S1)
    k, calls, book = keeper(w, mp, 2)   # 접수 남음 · 나노 1/1 = 정원만 참
    w.round(k)
    assert parked(w) == [S1] and any(x.startswith("URGENT-PARK") and " 나노 1 → 0" in x for x in k.lines), k.lines


def c11(w, mp):   # ⑪ ③ 뒤 다음 바퀴 = project → submit → assign → launch 까지 그 긴급 카드가 감(접수 7/8)
    nano(w, S1, idle=400), nano(w, S2, idle=500)
    k, calls, book = keeper(w, mp, 8)
    w.round(k)
    w.round(k)
    disp = [r.get("holder") for r in w.journal() if r["kind"] == "dispatch" and r["work"] == U]
    assert accepted(w, U) == [U] and disp == [nh(U)] and book["n"] == 7, (accepted(w, U), disp, book, k.lines)
    assert [json.loads(x)[json.loads(x).index("--work") + 1] for x in kw._lines(str(w.tmp / "bin" / "launch.py") + ".log")] == [U], k.lines


def c12(w, mp):   # ⑫ ③ 뒤 같은 바퀴에 일반 카드만 남아도 쉼 추가 0 · 추가 용량 0(긴급 우회 0)
    nano(w, S1, idle=400), nano(w, S2, idle=500)
    k, calls, book = keeper(w, mp, 8)
    w.round(k)
    book["n"] = 8   # 같은 바퀴에 일반 카드만 남아도 · 다음 바퀴도 가득
    w.round(k)
    assert parked(w) == [S2] and not accepted(w, U) and not accepted(w, G), (parked(w), accepted(w, U), accepted(w, G), k.lines)   # 쉼 1 · 열기 0(추가 용량 0)


def c13(w, mp):   # ⑬ ③ 의 긴급이 아직 안 닫힘 · 둘째 긴급 대기 · 유휴 나노 있음 → 쉼 0
    nano(w, S1, idle=400), nano(w, S2, idle=500)
    k, calls, book = keeper(w, mp, 8)
    w.round(k)
    book["n"] = 8   # 다음 바퀴 다시 가득(그 긴급은 아직 안 열렸다)
    w.round(k)
    assert parked(w) == [S2] and k.state.get("urgent_park") == {TEAM: U}, (parked(w), k.state.get("urgent_park"), k.lines)


def c14(w, mp):   # ⑭ 꼴 틀린 긴급(①) → 쉼 0(알림만)
    nano(w, S1)
    k, calls, book = keeper(w, mp, 8)
    w.round(k)
    assert parked(w) == [] and len(told(w)) == 1, (parked(w), told(w), k.lines)


def c15(w, mp):   # ⑮ 알림 발신 실패 → 열쇠 0 · 다음 바퀴 다시 1통
    nano(w, S1)
    k, calls, book = keeper(w, mp, 8)
    kw._put(str(w.mbox) + ".rc", "1")
    w.round(k)
    assert len(told(w)) == 1 and not any("urgent-form" in x for x in (k.state.get("sent") or {})), (told(w), k.state.get("sent"), k.lines)
    Path(str(w.mbox) + ".rc").unlink()
    w.round(k)
    assert len(told(w)) == 2, (told(w), k.lines)


def c16(w, mp):   # ⑯ 접수 8/8 · 완료 live 좌석이 유휴 순서 첫째 → 그 석 안 고름 · capacity 를 쥔 석을 고름
    nano(w, SD, idle=900, done=True), nano(w, S1, idle=400)
    k, calls, book = keeper(w, mp, 8)
    w.round(k)
    assert parked(w) == [S1], (parked(w), k.lines)   # 완료 석(더 오래 쉼)이 아니다


def c16b(w, mp):   # ⑯b DA#57 지적 — 접수 8/8 ∧ 나노 정원 2/2 동시에 참 → 그때도 capacity 를 쥔 석만(완료 석 아님)
    nano(w, SD, idle=900, done=True), nano(w, S1, idle=400)
    k, calls, book = keeper(w, mp, 8)
    w.round(k)
    assert parked(w) == [S1], (parked(w), k.lines)   # 완료 석(더 오래 쉼)이 아니라 접수 보유 석
    got = [x for x in k.lines if x.startswith("URGENT-PARK")]
    assert got and " 접수 8 → 7" in got[0] and " 나노 2 → 1" in got[0], (got, k.lines)   # 막힌 쪽 둘 다 줄었다
    assert k.state.get("urgent_park") == {TEAM: U}, k.state.get("urgent_park")


def c17(w, mp):   # ⑰ 쉼 뒤 다시 읽은 capacity 가 그대로 → urgent_park 기억 0 · 1줄
    nano(w, S1)
    k, calls, book = keeper(w, mp, {"n": 8, "held": True})   # 쉼이 용량을 안 놓는 세계
    w.round(k)
    assert parked(w) == [S1] and k.state.get("urgent_park") == {} and any(x.startswith("URGENT-PARK") and "기억 0" in x for x in k.lines), k.lines


CASES = {"①": (c1, {"cards": {U: BAD}, "nano": None}), "②": (c2, {"cards": {U: URGENT, V: NO}}),
         "③": (c3, {"cards": {U: URGENT}}), "④": (c4, {"cards": {U: "- 우선: 높음\n"}}),
         "⑤": (c5, {"cards": {U: URGENT}}), "⑥": (c6, {"cards": {U: URGENT}}), "⑦": (c7, {"cards": {U: URGENT}}),
         "⑧": (c8, {"cards": {U: URGENT}}), "⑨": (c9, {"cards": {U: URGENT}}), "⑨s": (c9s, {"cards": {U: URGENT}}),
         "⑩": (c10, {"cards": {U: URGENT}, "cap": "1"}), "⑪": (c11, {"cards": {U: URGENT}}),
         "⑫": (c12, {"cards": {U: URGENT, G: "- 우선: 높음\n"}}), "⑬": (c13, {"cards": {U: URGENT}}),
         "⑭": (c14, {"cards": {U: BAD}}), "⑮": (c15, {"cards": {U: BAD}}),
         "⑯": (c16, {"cards": {U: URGENT}}), "⑯b": (c16b, {"cards": {U: URGENT}, "cap": "2"}), "⑰": (c17, {"cards": {U: URGENT}})}
@pytest.mark.parametrize("name", list(CASES))
def test_case(name, tmp_path, monkeypatch):
    case, opts = CASES[name]
    w = world(tmp_path, monkeypatch, opts.get("cards"), opts.get("cap", "8"))
    w.round = _round(w)
    case(w, monkeypatch)


def _round(w):
    """r1929 keeper 는 launch 를 기다리지 않는다 → 한 «바퀴» = 띄운 가짜 launch 가 끝날 때까지 기다렸다가 끝(같은 keeper)."""
    base = w.round

    def round(k):
        k.cache.pop("launching", None)   # 여는 중 칸 = 바퀴마다 새로
        base(k)
        [p.wait(25) for p in k.cache.pop("spawned", []) or []]
        return k.lines
    return round

