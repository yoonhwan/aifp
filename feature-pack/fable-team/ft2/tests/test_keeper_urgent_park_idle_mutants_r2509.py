"""r2557 — `test_keeper_urgent_park_idle_r2509.py` 변이 14칸(M1~M14)만 옮긴 자매 파일.

까닭: 사례 19칸(33초) + 변이 14칸(29초) = 한 파일 62.5초로 70초 경계에 걸렸다. 파일을 가르면 각각 45초 안에 끝난다.
사례·대역·변이 정의는 `test_keeper_urgent_park_idle_r2509.py` 한 곳에 있다(사례 = 그 파일이 돈다 · 여기는 사본을 만들어 1칸씩 깬다).
변이 1칸 = ft2 사본(copytree) + 그 변이가 잡는 사례가 FAIL.
"""
import importlib.util
import shutil
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("urgent_park_idle_cases_r2509", str(Path(__file__).with_name("test_keeper_urgent_park_idle_r2509.py")))
cases = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cases)
world, CASES, FT2, _round = cases.world, cases.CASES, cases.FT2, cases._round


KN, KS = "adapters/pi/keeper_next.py", "adapters/pi/keeper_settle.py"
MUTANTS = {
    "M1": (KN, [('if not (URGENT.match(x.strip()) or URGENT_NO.match(x.strip()))', "if False")], "①"),
    "M2": (KN, [('"%s|urgent-form|%s|%s" % (k.stamp()[:10], team, stem)', '"urgent-form|%s|%s" % (team, stem)')], "①"),
    "M3": (KN, [("    if isinstance(got, str) or not any((row or [False])[0] for row in got[0].values()):\n", "    if isinstance(got, str):\n"),
                ("    if not pick or not (got[0].get(pick[0]) or [False])[0]:\n", "    if not pick:\n")], "④"),
    "M4": (KS, [("self.look(team, work, attempt, holder, age, stop, idle_s=DONE_IDLE, short=True)", 'self.look(team, work, attempt, holder, age, "stop", idle_s=DONE_IDLE, short=True)')], "⑤"),   # r2535 = 길 표식 인자 판
    "M5": (KS, [("idle_s=DONE_IDLE, short=True) != \"REST\"", "idle_s=0, short=True) != \"REST\"")], "⑥"),
    "M6": (KS, [("code = self.mail_gate(team, work, holder, idle_s, short=short) if short else \"\"", "code = self.mail_gate(team, work, holder, idle_s, short=short) if False else \"\"")], "⑦"),   # r2535 K2 로 값 비교를 인자로 바꾼 판(관문 뺌 = 같은 뜻)
    "M7": (KS, [('            return holder if self.park_seat(team, work, attempt, holder, "idle-done", "긴급 %s 자리 · 유휴 %d초" % (card, age), alive=True, done=False) == "PARKED" else ""', '            self.park_seat(team, work, attempt, holder, "idle-done", "긴급 %s 자리 · 유휴 %d초" % (card, age), alive=True, done=False)')], "③"),
    "M8": (KN, [("    if guard(k, team)[0] is not True:   # ⑨", "    if False:   # ⑨")], "⑨"),
    "M9": (KN, [("    if park_open(k, team):\n", "    if False:\n")], "⑬"),
    "M10": (KN, [('        if not ok and str((k.state.get("sent") or {}).get(key) or "").startswith("fail|"):', "        if False:")], "⑮"),
    "M11": (KN, [("    if n < k.fa.INTAKE_CAP:   # 정상값", "    if True:   # 정상값")], "⑫"),
    "M12": (KN, [("    if full:   # ⑯⑰ ㉠", "    if False:   # ⑯⑰ ㉠")], "⑯"),
    "M13": (KN, [("    sides = [(\"접수\", before, cap2, full)", "    sides = [] or [(\"접수\", before, cap2, False)")], "⑰"),
    "M14": (KN, [('    full = not intake_open(k, team)   # DA#57', '    full = False   # DA#57')], "⑯b")}   # DA#57 지적 — 두 상한 동시 참에 접수 보유 후보 필터 뺌



@pytest.mark.parametrize("name", list(MUTANTS))
def test_mutant(name, tmp_path, monkeypatch):
    rel, pairs, case = MUTANTS[name]
    shutil.copytree(FT2, tree := tmp_path / "m" / "ft2", ignore=shutil.ignore_patterns("tests", "__pycache__"))
    text = (tree / rel).read_text(encoding="utf-8")
    for old, new in pairs:
        assert text.count(old) == 1, (name, old)
        text = text.replace(old, new)
    (tree / rel).write_text(text, encoding="utf-8")
    w = world(tmp_path / "w", monkeypatch, CASES[case][1].get("cards"), CASES[case][1].get("cap", "8"), ft2=tree)
    w.round = _round(w)
    with pytest.raises(AssertionError):
        CASES[case][0](w, monkeypatch)
