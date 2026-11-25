"""r2535 park 유휴 5분 — 변이 M1~M15 (카드 변이 표 · 사례 ①~⑳ 은 test_keeper_park_idle_5min_r2535.py).

사례 파일을 import 해서 그 사례를 **변이 사본 트리에서 한 번** 돌린다 — 변이 하나 = Red 한 번(사례가 실 코드에서 통과하는 것은 사례 파일 몫).
대역 = keeper_world_r1812 · 하드링크 사본(원본 안 덮게 새 이름에 쓰고 바꿔치기) · 실 tmux·실 프로세스 종료·실 쪽지 0 · sleep 0 · 70초 안.
"""
import importlib.util
import os
import shutil
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("park_idle_cases_r2535", str(Path(__file__).with_name("test_keeper_park_idle_5min_r2535.py")))
cases = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cases)
FT2, KS, NOTE = cases.FT2, cases.KS, cases.NOTE
world, c1, c3, c4, c5, c7, c8, c10, c11, c12, c13, c14, c15, c16, c17, c19, c21 = (
    cases.world, cases.c1, cases.c3, cases.c4, cases.c5, cases.c7, cases.c8, cases.c10, cases.c11, cases.c12, cases.c13, cases.c14,
    cases.c15, cases.c16, cases.c17, cases.c19, cases.c21)

MUTANTS = {   # 카드 변이 M1~M15 — (파일, 바꿀 줄, 바꾼 줄, Red 여야 하는 사례)
    "M1": (KS, "PARK_IDLE, WAIT_S, DAY = 600, 600, 86400", "PARK_IDLE, WAIT_S, DAY = 3600, 600, 86400", c1),
    "M2": (KS, "        code = self.mail_gate(team, work, holder, idle_s, short=short) if short else \"\"",
           "        code = self.mail_gate(team, work, holder, idle_s) if idle_s != DONE_IDLE else \"\"", c11),   # r2596 — 값 비교 상대 = DONE_IDLE(DONE_IDLE != PARK_IDLE 이 된 뒤 · 앞 값 PARK_IDLE)
    "M3": (KS, "SHARE_IDLE, ACCEPT_IDLE = 300, 300",
           "SHARE_IDLE, ACCEPT_IDLE = 3600, 300", c12),
    "M4": (KS, "            if age >= self.wait(\"FT2_ACCEPT_IDLE_S\", ACCEPT_IDLE, 600):", "            if age >= WAIT_S:", c13),   # r2602 — 닻 값은 r2539 K7 이 600 으로 바꾼 코드 줄을 따라간다(옛 값 3600 = 닻 0회)
    "M5": (KS, "            idle_s = turn_s", "            idle_s = DONE_IDLE", c7),   # r2596 — 앞 값 PARK_IDLE( PARK_IDLE 600 = TURN_OPEN_IDLE 600 이라 차이 0 )
    "M6": (KS, "            if stop is not None and age is not None and age >= turn_s and cpu == \"idle\":", "            if False:", c8),
    "M7": (KS, "        if rc != 0 or out.strip():", "        if rc != 0:", c3),
    "M8": (KS, "        if not (rc == 0 and len(set(heads.split())) == 1):", "        if False:", c4),
    "M9": (KS, "    return got if PARK_MIN <= got <= PARK_MAX else PARK_IDLE", "    return got", c14),
    "M10": (NOTE, '    nkey = "park|%s|%s|%s" % (team, holder, sha)',
            '    nkey = "park|%s|%s|%s|%s" % (team, holder, sha, close.now())', c15),
    "M11": (NOTE, "    before = book.pop(k)", "    before = book[k]", c16),
    "M12": (NOTE, "    except OSError as exc:", "    except ZeroDivisionError as exc:", c17),
    "M13": (KS, "        if long_seat(holder):   # r2135 L2", "        if False:   # r2135 L2", c10),
    "M14": (KS, "TURN_OPEN_IDLE = WAIT_S   # r2539 K8", "TURN_OPEN_IDLE = WAIT_S * 6   # r2539 K8", c19),
    "M15": (KS, "            if stop is not None and age is not None and age >= turn_s and cpu == \"idle\":",
            "            if age is not None and age >= turn_s and cpu == \"idle\":", c19),
    "M16": (KS, "        code = self.mail_gate(team, work, holder, idle_s, short=short) if short else \"\"",
            "        code = self.mail_gate(team, work, holder, idle_s) if short else \"\"", c21),   # 사유 재조회에 길 표식 빠짐(DA#60 지적 2)
}


@pytest.mark.parametrize("name", list(MUTANTS))
def test_mutant(name, tmp_path, monkeypatch):
    rel, old, new, case = MUTANTS[name]
    tree = tmp_path / "m" / "ft2"
    shutil.copytree(FT2, tree, ignore=shutil.ignore_patterns("tests", "__pycache__"), copy_function=os.link)   # 하드링크 = 변이 15개 복사 시간 줄임
    text = (tree / rel).read_text(encoding="utf-8")
    assert text.count(old) == 1, (name, old)
    mut = tree / (Path(rel).stem + ".mut.py")   # 하드링크 사본이라 원본을 덮지 않는다 = 새 이름에 쓰고 바꿔치기
    mut.write_text(text.replace(old, new), encoding="utf-8")
    os.replace(mut, tree / rel)
    tmp_path.mkdir(parents=True, exist_ok=True)
    with pytest.raises(AssertionError):   # 변이 = Red 한 번(같은 사례의 초록은 사례 파일이 본다)
        case(world(tmp_path / "w1", monkeypatch, tree))
