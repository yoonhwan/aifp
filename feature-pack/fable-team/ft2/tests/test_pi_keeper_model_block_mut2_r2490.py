"""r2490 변이 M8b · M8c · M8d · M13 · M9 · M10 · M11 · M12 — 탐침 한살이와 재배정 갈래."""
import importlib.util
from pathlib import Path
import pytest

FT2 = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("r2490_mutants_b", str(FT2 / "tests" / "keeper_model_block_mutants_r2490.py"))
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)
NAMES = ["M8b", "M8c", "M8d", "M13", "M9", "M10", "M11", "M12"]


@pytest.mark.parametrize("name", NAMES)
def test_mutant(name, tmp_path, monkeypatch):
    M.run(name, tmp_path, monkeypatch)
