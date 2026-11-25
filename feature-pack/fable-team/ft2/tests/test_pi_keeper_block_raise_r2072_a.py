"""r2072 a — 사례 12개만 돈다(변이·같음 대조 = 짝 b·c · 정의는 같은 폴더 keeper_block_raise_r2072.py 한 곳).

r2526 쪼개기: 원 파일(test_pi_keeper_block_raise_r2072.py) 단독 83초 = 사례 25 + 변이 27 + 같음 대조 13 + 실 바퀴 17 + 잠금 1.
논리 사례 id(함수명 · 매개변수 id)는 원 파일과 같다 — 파일 경로만 다르다(대응표 = keeper_split_case_ids_r2526.py).
r2526 ③ ⑦ — 이 파일이 도는 동안 SIGTERM handler 를 건다(끊겨도 이 시험이 띄운 그룹만 거둔다).
"""
import pytest

import keeper_block_raise_r2072 as h


@pytest.fixture(autouse=True)
def reap_stubs(tmp_path):
    """r2330 Y2 + r2526 — 앞: handler 등록 · 뒤: handler 해제 → 띄운 스텁 그룹 거두기(fifo 풀기 · SIGKILL · unlink)."""
    yield from h.reap_stubs_body(tmp_path)


SLICE = ["①lib", "①none", "①path", "②rc9", "②hang", "②cap20", "③", "④", "⑤", "⑥", "⑦", "⑧skip"]


@pytest.mark.parametrize("name", SLICE)
def test_case(name, tmp_path, monkeypatch):
    h.run_case(name, tmp_path, monkeypatch)
