"""r2400 a — 사례 13개만 돈다(변이 = 짝 b·c · 사례·대역 정의는 같은 폴더 keeper_no_lease_close_r2400.py 한 곳).

r2526 쪼개기: 원 파일(test_keeper_no_lease_close_r2400.py) 단독 73초 = 사례 30초 + 변이 43초.
논리 사례 id(함수명 · 매개변수 id)는 원 파일과 같다 — 파일 경로만 다르다(대응표 = keeper_split_case_ids_r2526.py).
"""
import pytest

import keeper_no_lease_close_r2400 as h

SLICE = ["①", "①둘째", "②", "③", "④", "⑤", "⑥", "⑥b", "⑥c", "⑦", "⑧", "⑨", "⑩"]


@pytest.mark.parametrize("name", SLICE)
def test_case(name, tmp_path, monkeypatch):
    h.CASES[name](tmp_path / name, monkeypatch)
