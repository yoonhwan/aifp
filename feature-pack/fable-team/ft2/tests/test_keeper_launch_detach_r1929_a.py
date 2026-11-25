"""r1929 a — 사례 15개만 돈다(변이 = 짝 b · 사례·대역 정의는 같은 폴더 keeper_launch_detach_r1929.py 한 곳).

r2526 쪼개기: 원 파일(test_keeper_launch_detach_r1929.py) 단독 54초 = 사례 20초 + 변이 34초.
논리 사례 id(함수명 · 매개변수 id)는 원 파일과 같다 — 파일 경로만 다르다(대응표 = keeper_split_case_ids_r2526.py).
"""
import pytest

import keeper_launch_detach_r1929 as h

SLICE = ["①", "④", "⑤k", "⑧", "⑨", "⑯", "⑰", "⑱", "⑲", "⑤", "⑥", "⑦", "⑬", "⑮", "⑰p"]


@pytest.mark.parametrize("name", SLICE)
def test_case(name, tmp_path, monkeypatch):
    h.run(name, tmp_path, monkeypatch)
