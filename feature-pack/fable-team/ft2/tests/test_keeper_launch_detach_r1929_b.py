"""r1929 b — 변이 9개만 돈다(사례 = 짝 a · 사례·변이 정의는 같은 폴더 keeper_launch_detach_r1929.py 한 곳).

r2526 쪼개기: 원 파일 단독 54초 = 사례 20초 + 변이 34초. 변이는 사본에서만 · 변이마다 원본으로 같은 사례 1회 더.
논리 사례 id(함수명 · 매개변수 id)는 원 파일과 같다 — 파일 경로만 다르다(대응표 = keeper_split_case_ids_r2526.py).
"""
import pytest

import keeper_launch_detach_r1929 as h

SLICE = ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9"]


@pytest.mark.parametrize("name", SLICE)
def test_mutant(name, tmp_path, monkeypatch):
    rel, old, new, case = h.MUTANTS[name]
    h.shutil.copytree(h.FT2, tree := tmp_path / "m" / "ft2", ignore=h.shutil.ignore_patterns("tests", "__pycache__"))
    text = (tree / rel).read_text(encoding="utf-8")
    assert text.count(old) == 1, (name, old)
    (tree / rel).write_text(text.replace(old, new), encoding="utf-8")
    [(tmp_path / sub).mkdir() for sub in ("w1", "w2")]
    with pytest.raises(AssertionError):
        h.run(case, tmp_path / "w1", monkeypatch, tree)
    h.run(case, tmp_path / "w2", monkeypatch)   # 원본으로 같은 사례 1회 더 = PASS
