"""r2072 c — «장부 도구 없음» 같음 대조 5개 + 실 바퀴 멈춤 1개만 돈다(사례 = 짝 a · 정의는 같은 폴더 keeper_block_raise_r2072.py).

r2526 쪼개기: 원 파일 단독 83초 = 사례 25 + 변이 27 + 같음 대조 13 + 실 바퀴 17 + 잠금 1.
논리 사례 id(함수명 · 매개변수 id)는 원 파일과 같다 — 파일 경로만 다르다(대응표 = keeper_split_case_ids_r2526.py).
"""
import pytest

import keeper_block_raise_r2072 as h


@pytest.fixture(autouse=True)
def reap_stubs(tmp_path):
    """r2330 Y2 + r2526 — 앞: handler 등록 · 뒤: handler 해제 → 띄운 스텁 그룹 거두기(fifo 풀기 · SIGKILL · unlink)."""
    yield from h.reap_stubs_body(tmp_path)


SLICE = ["③", "④", "⑤", "⑥", "⑦"]


@pytest.mark.parametrize("name", SLICE)
def test_same_without_ledger(name, tmp_path, monkeypatch):
    h.run_same_without_ledger(name, tmp_path, monkeypatch)


def test_same_real_round_and_hang(tmp_path, monkeypatch):
    h.run_same_real_round_and_hang(tmp_path, monkeypatch)
