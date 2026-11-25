"""r2557 — `test_done_seat_short_idle.py` 사례 27칸 중 뒤 13칸(㉙거~㉙도)만 도는 자매 파일.

까닭: 사례 27칸이 한 파일에서 66.7초로 70초 경계에 걸렸다. 앞 14칸은 원본 파일이 돌고, 이 파일은 뒤 13칸을 돈다
(칸 수 14 + 13 = 27 · 단언 글자 그대로). 사례·대역·변이 정의는 `test_done_seat_short_idle.py` 한 곳에 있다.
"""
import importlib.util
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("done_seat_cases_pB", str(Path(__file__).with_name("test_done_seat_short_idle.py")))
cases = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cases)
world, CASES, B_NAMES = cases.world, cases.CASES, cases.B_NAMES


@pytest.mark.parametrize("name", [n for n in CASES if n in B_NAMES])
def test_case(name, tmp_path, monkeypatch):
    CASES[name](world(tmp_path, monkeypatch))
