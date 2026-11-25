"""r2400 b — 변이 M1~M5 만 돈다(사례 = 짝 a · 정의는 같은 폴더 keeper_no_lease_close_r2400.py 한 곳).

r2526 쪼개기: 원 파일 단독 73초 = 사례 30초 + 변이 43초 → 변이도 둘로 나눈다(b = M1~M5 · c = M6~M10).
변이는 사본에서만 · 변이마다 원본으로 같은 사례 1회 더.
논리 사례 id(함수명 · 매개변수 id)는 원 파일과 같다 — 파일 경로만 다르다(대응표 = keeper_split_case_ids_r2526.py).
"""
import pytest

import keeper_no_lease_close_r2400 as h

SLICE = ["M1", "M2", "M3", "M4", "M5"]


@pytest.mark.parametrize("name", SLICE)
def test_mutant(name, tmp_path, monkeypatch):
    rel, old, new, case = h.MUTANTS[name]
    pack = tmp_path / "ft2mut"
    h.shutil.copytree(h.kw.FT2, pack, ignore=h.shutil.ignore_patterns("tests", "__pycache__"))
    path = pack / "adapters" / "pi" / rel
    body = path.read_text(encoding="utf-8")
    assert body.count(old) == 1, (name, body.count(old))
    path.write_text(body.replace(old, new, 1), encoding="utf-8")
    with pytest.raises(AssertionError):
        h.CASES[case](tmp_path / (name + "-mut"), monkeypatch, pack)
    h.CASES[case](tmp_path / (name + "-ok"), monkeypatch)   # 변이마다 원본으로 같은 사례 1회 더
