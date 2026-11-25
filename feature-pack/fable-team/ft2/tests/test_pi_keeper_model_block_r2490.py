"""r2490 ft2 공급자 막힘 → 대체 모델 — ① ~ ⑨ 사례만 돈다(사례·대역 정의는 tests/keeper_model_block_cases_r2490.py 한 곳)."""
import importlib.util
from pathlib import Path
import pytest

FT2 = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("r2490_cases_a", str(FT2 / "tests" / "keeper_model_block_cases_r2490.py"))
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)


@pytest.mark.parametrize("name", list(S.CASES_A))
def test_case(name, tmp_path, monkeypatch):
    S.CASES_A[name](S.world(tmp_path, monkeypatch))
