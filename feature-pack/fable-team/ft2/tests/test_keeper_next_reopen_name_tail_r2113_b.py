"""r2113 b — 변이 9개만 돈다(사례 = 짝 a · 사례·변이 정의는 같은 폴더 keeper_next_reopen_name_tail_r2113.py 한 곳).

r2526 쪼개기: 원 파일 단독 67초 = 사례 27초 + 변이 40초. 변이는 사본에서만 · 변이마다 원본으로 같은 사례 1회 더.
논리 사례 id(함수명 · 매개변수 id)는 원 파일과 같다 — 파일 경로만 다르다(대응표 = keeper_split_case_ids_r2526.py).
"""
import pytest

import keeper_next_reopen_name_tail_r2113 as h

SLICE = ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9"]


@pytest.mark.parametrize("name", SLICE)
def test_mutant(name, tmp_path, monkeypatch):
    old, new, cases = h.MUTANTS[name]
    tree = tmp_path / "m" / "ft2"
    h.shutil.copytree(h.kw.FT2, tree, ignore=h.shutil.ignore_patterns("tests", "__pycache__"))
    text = (tree / h.KN).read_text(encoding="utf-8")
    assert text.count(old) == 1, (name, old)
    (tree / h.KN).write_text(text.replace(old, new), encoding="utf-8")
    for case in cases:
        bad, good = tmp_path / ("bad" + case), tmp_path / ("good" + case)
        bad.mkdir(), good.mkdir()
        with pytest.raises(AssertionError):
            h.run(case, bad, monkeypatch, tree)
        h.run(case, good, monkeypatch)   # 원본으로 같은 사례 1회 더 = PASS
