"""r2490 변이 표 M1 ~ M12(M8b · M8c · M8d · M11 · M12 포함) — 시험 파일 둘이 나눠 쓴다(한 파일 70초 상한).

카드 변이 표와 사례 대응: M1→①b · M2→④ · M3→⑤ · M4→⑥ · M5→⑦ · M6→⑧ · M7→⑨ · M8→⑩ · M8b→⑪b ·
M8c→⑪b⑪c · M8d→⑪c⑪d · M9→⑫ · M10→⑭ · M11→⑬⑯ · M12→⑬b. 사례 정의는 test_pi_keeper_model_block_r2490.py 한 곳.
"""
import importlib.util, shutil  # noqa: E401
from pathlib import Path

FT2 = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("r2490_cases_for_mut", str(FT2 / "tests" / "keeper_model_block_cases_r2490.py"))
T = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T)   # 사례·대역 정의 = 한 곳
BLOCK, STALL = "adapters/pi/model_block.py", "adapters/pi/keeper_stall.py"
_SE, _RE = "adapters/pi/keeper_stall_error.py", "adapters/pi/keeper_stall.py"
MUTANTS = {
    # M1 BLOCKED 낱말에서 새 낱말(402 · insufficient 계열 · billing)을 뺌 → RATELIMITED 낱말(quota)만 남는다
    "M1": (_SE, 'BLOCK = ("402", "insufficient_balance", "insufficient_quota", "billing")', "BLOCK = ()", T.c1b),
    # M2 UNAVAILABLE 을 BLOCKED 로 봄
    "M2": (_SE, 'return any(w in text for w in BLOCK) or any(w in text for w in dict(ERRORS)["RATELIMITED"])',
           'return kind in ("UNAVAILABLE", "RATELIMITED", "UNKNOWN")', T.c4),
    # M3 15분 창 없음
    "M3": (BLOCK, "or got[1] is None or k.now() - got[1] >= WINDOW_S", "or got[1] is None", T.c5),
    # M4 대체 표 행이 없을 때 다른 역할 모델로 엶
    "M4": (BLOCK, '        if not swap:                                        # K5 대체 표에 행이 없음\n            return None, {}, "대체 표에 행 없음(%s)" % item["model"]',
           '        if not swap:\n            swap = models().role_defaults()["session"][0]', T.c6),
    # M5 대체의 대체를 따라감
    "M5": (BLOCK, "        if read(root, target):                              # K5 대체의 대체 0",
           "        if False:                                          # K5 대체의 대체 0", T.c7),
    # M6 막힘 동안 바퀴마다 쪽지
    "M6": (BLOCK, '            if not row or row.get("phase") != "blocked":', "            if True:", T.c8),
    # M7 탐침 없이 바로 원래 모델로 전부 엶
    "M7": (BLOCK, "            elif probe_seat(root, [team], alive) is None:", "            elif True:", T.c9),
    # M8 탐침 성공을 안 보고 표식 유지
    "M8": (BLOCK, "    if ok and got is None:                             # ㉠", "    if False:                                          # ㉠", T.c10),
    # M8b 탐침이 비BLOCKED 로 끝나면 표식을 지움(끝남 확인을 성공으로 봄)
    "M8b": (BLOCK, '    if row.get("probe"):\n        write(k.root, provider_name, dict(row, probe=""))',
            "    clear(k.root, provider_name)", T.c11b),
    # M8c 끝남 확인 뒤에도 probe 칸을 안 비움(재탐침 0)
    "M8c": (BLOCK, '    if row.get("probe"):\n        write(k.root, provider_name, dict(row, probe=""))', "    pass", T.c11c),
    # M8d 살아 있는 탐침의 probe 칸을 비움(원래 모델 2석)
    "M8d": (BLOCK, '    if row.get("probe") != holder:                     # ㉣ 살아 있는 탐침 — probe 칸만 채운다(새 탐침 0)\n        write(k.root, provider_name, dict(row, probe=holder))',
            '    write(k.root, provider_name, dict(row, probe=""))', T.c11d),
    # M13 탐침 생존 판독 실패를 «0석» 으로 봄(원래 모델 탐침을 새로 연다 · 원래 모델 2석)
    "M13": (BLOCK, "            if alive is None:                               # K8 — 생존 판독 실패 = 새 탐침 0(원래 모델로 열지 않는다)",
            "            if False:", T.c11d),
    # M9 게이트가 표식만 보고 무관 공급자 정지도 통과
    "M9": (BLOCK, '    if not provider_name or not read(k.root, provider_name):\n        return False\n    return bool(fallback(model))',
           "    return bool(marked(k.root))", T.c12),
    # M10 판정기 손상을 «막힘» 으로 봄
    "M10": (BLOCK, "        if rc == 3 or found:", "        if rc in (3, 4) or found:", T.c14),
    # M11 대체로 새 카드는 열되 막힌 좌석을 재배정하지 않음(15분 대기)
    "M11": (STALL, "        if not self.guard(team, work, holder, rows):  # pane 일하는 표시 = 재배정 0",
            "        if k.now() - at < self.stall_s or not self.guard(team, work, holder, rows):", T.c13),
    # M12 표식 없이도 오류 턴 holder 를 바로 재배정
    "M12": (_RE, '''        if kind != "UNAVAILABLE":
            return self.blocked(team, work, holder, key, at, text, rows) if E.blocked(kind, text) else None''',
            '''        if True:   # M12 — 표식 없이도 오류 턴 holder 를 바로 재배정
            attempt = key.rsplit("@", 1)[1]
            intent = k.read_json(os.path.join(projection.runtime_path(k.root, team), "launch", "%s@%s.intent" % (work, attempt)))
            self.reassign(team, work, attempt, holder, intent.get("worktree"), intent, rows)
            return True''', T.c13b),
}


def run(name, tmp_path, monkeypatch):
    """사본에서 그 변이를 만들고 같은 사례를 1회 돌린다(Red) → 원본으로 1회 더(PASS)."""
    rel, old, new, case = MUTANTS[name]
    tree = copy(tmp_path)
    text = (tree / rel).read_text(encoding="utf-8")
    assert text.count(old) == 1, (name, rel, old[:60])
    (tree / rel).write_text(text.replace(old, new), encoding="utf-8")
    for sub in ("w1", "w2"):
        (tmp_path / sub).mkdir()
    try:
        case(T.world(tmp_path / "w1", monkeypatch, tree))   # 사본 = Red
    except AssertionError:
        pass
    else:
        raise AssertionError("%s — 사본이 Red 가 아니다" % name)
    case(T.world(tmp_path / "w2", monkeypatch))             # 원본으로 같은 사례 1회 더 = PASS


def copy(tmp):
    """이 팩의 사본 1개(tests·__pycache__ 뺌) — 변이마다 새로 뜬다."""
    tree = Path(tmp) / "m" / "ft2"
    if not tree.exists():
        shutil.copytree(FT2, tree, ignore=shutil.ignore_patterns("tests", "__pycache__"))
    return tree
