"""r2113 a — 사례 13개만 돈다(변이 = 짝 b · 사례·대역 정의는 같은 폴더 keeper_next_reopen_name_tail_r2113.py 한 곳).

r2526 쪼개기: 원 파일(test_keeper_next_reopen_name_tail_r2113.py) 단독 67초 = 사례 27초 + 변이 40초.
논리 사례 id(함수명 · 매개변수 id)는 원 파일과 같다 — 파일 경로만 다르다(대응표 = keeper_split_case_ids_r2526.py).
"""
import pytest

import keeper_next_reopen_name_tail_r2113 as h

SLICE = ["①", "②", "③", "③'", "④", "⑤", "⑥", "⑦", "⑧", "⑧'", "⑧''", "⑩", "⑪"]


@pytest.mark.parametrize("name", SLICE)
def test_case(name, tmp_path, monkeypatch):
    h.run(name, tmp_path, monkeypatch)
