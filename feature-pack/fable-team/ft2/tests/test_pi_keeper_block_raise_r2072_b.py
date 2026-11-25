"""r2072 b — 변이 M1~M4 + 잠금/보고 바퀴만 돈다(사례 = 짝 a · 정의는 같은 폴더 keeper_block_raise_r2072.py 한 곳).

r2526 쪼개기: 원 파일 단독 83초 = 사례 25 + 변이 27 + 같음 대조 13 + 실 바퀴 17 + 잠금 1.
변이는 사본에서만 · 변이마다 원본으로 같은 사례 1회 더 = PASS(⑤ 변이 그물이 살아 있음).
논리 사례 id(함수명 · 매개변수 id)는 원 파일과 같다 — 파일 경로만 다르다(대응표 = keeper_split_case_ids_r2526.py).
"""
import shutil

import pytest

import keeper_block_raise_r2072 as h


@pytest.fixture(autouse=True)
def reap_stubs(tmp_path):
    """r2330 Y2 + r2526 — 앞: handler 등록 · 뒤: handler 해제 → 띄운 스텁 그룹 거두기(fifo 풀기 · SIGKILL · unlink)."""
    yield from h.reap_stubs_body(tmp_path)


SLICE = ["M1", "M2", "M3", "M4"]


@pytest.mark.parametrize("name", SLICE)
def test_mutant(name, tmp_path, monkeypatch):
    old, new, label = h.MUTANTS[name]
    tree = tmp_path / "m" / "ft2"
    shutil.copytree(h.FT2, tree, ignore=shutil.ignore_patterns("tests", "__pycache__"))
    rel = tree / "adapters" / "pi" / "keeper_block.py"
    text = rel.read_text(encoding="utf-8")
    assert text.count(old) == 1, (name, old)
    rel.write_text(text.replace(old, new), encoding="utf-8")
    for sub in ("w1", "w2"):
        (tmp_path / sub).mkdir()
    with pytest.raises(AssertionError):
        h.ALL[label](h.world(tmp_path / "w1", monkeypatch, tree))
    h.ALL[label](h.world(tmp_path / "w2", monkeypatch))   # 원본으로 같은 사례 1회 더 = PASS


def test_report_and_lock(tmp_path, monkeypatch):
    h.run_report_and_lock(tmp_path, monkeypatch)
