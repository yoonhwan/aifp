"""r2526 반례 ② ⑤ + 변이 M1 M3 — 쪼갠 뒤에도 논리 사례 id 가 원 파일과 1:1 이고, 변이 그물이 살아 있는지 본다.

② 원 파일 → 나눈 파일 대응(함수명 · 매개변수 id — 파일 경로 제외) 1:1 · 합 92 · 빠짐 0 · 겹침은 따로 거절 · 덤 0 · 원본남음 0
⑤ 변이는 사본에서만 — 소스를 안 고치면 그대로 통과하고, 변이를 넣으면 Red(그물이 살아 있음)
M1 나눈 파일에서 사례 1개 뺌 → ② Red      M3 변이 넣기를 건너뜀 → ⑤ Red
"""
import importlib.util
import shutil
from pathlib import Path

import pytest

import keeper_mutant_apply_r2526 as ap
import keeper_split_case_ids_r2526 as ids

HERE = Path(__file__).resolve().parent
FT2 = HERE.parent
NOOP = '''"""M3 — 변이 넣기를 건너뛴 사본(아무것도 안 한다)."""
from pathlib import Path


def swap(path, old, new, name=""):
    _ = (Path(path), old, new, name)
'''


def load(path, alias):
    spec = importlib.util.spec_from_file_location(alias, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_case_ids_match_originals():
    """② — 논리 사례 id 대응이 1:1(합 92 · 빠짐 0 · 겹침 0 · 덤 0 · 원본남음 0)."""
    got = ids.problems(HERE)
    assert got == [], "\n".join(got[:20])


def test_duplicate_is_rejected_separately():
    """② 겹침은 따로 거절 — 같은 논리 id 를 두 나눈 파일에 넣으면 «겹침» 사유가 하나 생긴다."""
    splits = dict(ids.SPLITS)
    splits["test_keeper_no_lease_close_r2400_c.py"] = {"test_mutant": ["M6", "M7", "M8", "M9", "M10"], "test_case": ["⑩"]}
    got = ids.problems(None, splits=splits)
    assert any(x.startswith("겹침 test_keeper_no_lease_close_r2400.py test_case[⑩]") for x in got), got


def test_m1_removed_case_is_red(tmp_path):
    """M1 — 나눈 파일에서 사례 1개를 빼면 ② 가 «빠짐» 으로 Red."""
    tree = tmp_path / "m" / "ft2"
    shutil.copytree(FT2, tree, ignore=shutil.ignore_patterns("__pycache__"))
    ap.swap(tree / "tests" / "test_keeper_no_lease_close_r2400_a.py", ', "⑩"', "", "M1")
    got = ids.problems(tree / "tests")
    assert any(x.startswith("빠짐 test_keeper_no_lease_close_r2400_a.py test_case[⑩]") for x in got), got
    assert any(x.startswith("빠짐 test_keeper_no_lease_close_r2400.py test_case[⑩]") for x in got), got
    assert any(x.startswith("합 91") for x in got), got


def net(tmp, monkeypatch, noop=False):
    """⑤ 변이 그물 1회 — 사본에서 변이를 넣으면 그 사례가 Red 인가(True = 못 잡았다 = 그물이 죽었다)."""
    tree = tmp / "m" / "ft2"
    shutil.copytree(FT2, tree, ignore=shutil.ignore_patterns("__pycache__"))
    tests = tree / "tests"
    if noop:
        (tests / "keeper_mutant_apply_r2526.py").write_text(NOOP, encoding="utf-8")
    apply_ = load(tests / "keeper_mutant_apply_r2526.py", "r2526_ap_%d" % id(tmp))
    h = load(tests / "keeper_block_raise_r2072.py", "r2526_h_%d" % id(tmp))
    apply_.swap(tree / "adapters" / "pi" / "keeper_block.py", "LONG_S = 600", "LONG_S = 0", "M1")
    (tmp / "w1").mkdir(parents=True, exist_ok=True)
    try:
        h.ALL["③"](h.world(tmp / "w1", monkeypatch, tree))
    except AssertionError:
        return False   # 변이 = Red — 그물이 잡았다
    return True        # 변이가 통과 — 그물이 못 잡았다


def test_mutant_net_catches(tmp_path, monkeypatch):
    """⑤ — 소스를 안 고치면 통과하고 변이를 넣으면 Red(변이 그물이 살아 있다)."""
    assert not net(tmp_path, monkeypatch)


def test_m3_skipping_apply_turns_net_red(tmp_path, monkeypatch):
    """M3 — 변이 넣기(swap)를 건너뛰면 위 ⑤ 검사가 Red 가 된다(그물이 실제로 넣기에 기대고 있다)."""
    assert net(tmp_path, monkeypatch, noop=True)
