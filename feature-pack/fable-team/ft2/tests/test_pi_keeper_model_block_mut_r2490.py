"""r2490 변이 M1 ~ M8 — 사본에서만 고치고 변이마다 원본으로 같은 사례를 1회 더 돌린다(사본 = Red · 원본 = PASS)."""
import importlib.util
from pathlib import Path
import pytest

FT2 = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("r2490_mutants_a", str(FT2 / "tests" / "keeper_model_block_mutants_r2490.py"))
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)
NAMES = ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8"]


@pytest.mark.parametrize("name", NAMES)
def test_mutant(name, tmp_path, monkeypatch):
    M.run(name, tmp_path, monkeypatch)
