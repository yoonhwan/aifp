"""r2499 — ft2 시험 전부에 tmux 격리를 기본값으로 건다. 카드 r2499 · 사전 DA APPROVE-DESIGN(DA#59 r2 · 동결 4556da9b2e3).

㉠ 기본 환경 격리: 시험 프로세스의 os.environ 을 물려받는 tmux 호출은 PATH 맨 앞 가짜 tmux(rc0 · 출력 0 · 기록).
㉡ 종료 시 잔류 검출: 시험 임시 폴더를 cwd 로 가진 운영 세션이 남아 있으면 «실 tmux 세션 남음 <이름>» 으로 실패.
표식 `real_tmux` = 실 바이너리를 부르는 시험(가짜를 PATH 에서 뺀다 · 소켓은 여전히 임시 · 운영 서버 0).

왜: 2026-11-23 09:26 운영 tmux 에 biz-harness-nano-w1#1 이 재발했다(변이 시험이 call 대역을 빠뜨림 · cwd = pytest 임시 폴더).
그 세션이 «근거 없는 석» 으로 팀의 나노 열기를 60분 멈췄다. 시험은 이제 운영 서버에 닿지 못하고, 닿아 남기면 그 시험이 실패한다.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tmux_isolation_r2499 as iso  # noqa: E402

MARK = "real_tmux"
_REAL_TMUX = iso.real_bin()   # 가짜를 PATH 에 넣기 «전»(conftest import 시점) — 표식 시험의 skipif 가 이 값을 본다
os.environ["FT2_REAL_TMUX"] = _REAL_TMUX or ""


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", MARK + ": 실 tmux 바이너리를 부른다(임시 소켓 · 운영 서버 0). r2499")


@pytest.fixture(scope="session", autouse=True)
def tmux_isolation(tmp_path_factory: pytest.TempPathFactory):
    """세션 하나 = 격리 한 벌. 끝나면 마지막 잔류 검사를 하고, 남았으면 이 판의 rc 를 0 으로 두지 않는다(DA#57 H1 ①)."""
    state = iso.isolate(tmp_path_factory.getbasetemp())
    yield state
    fails, lines = iso.report(state)
    for line in lines:
        print(f"{iso.TAG} {line}", file=sys.stderr)
    iso.restore(state)
    if fails:   # 시험 하나가 이미 잡았어도 여기서 한 번 더 — 마지막 시험 뒤에 남은 것도 초록으로 끝나지 않는다
        pytest.fail(lines[0], pytrace=False)


@pytest.fixture(autouse=True)
def _tmux_real_marker(request: pytest.FixtureRequest, tmux_isolation, monkeypatch: pytest.MonkeyPatch):
    """표식 시험 = 가짜 tmux 를 PATH 에서 뺀다(실 바이너리 · 소켓은 임시 → 운영 0)."""
    if request.node.get_closest_marker(MARK):
        monkeypatch.setenv("PATH", tmux_isolation["path_before"])
        monkeypatch.setenv("FT2_REAL_TMUX", tmux_isolation["real"] or "tmux")
    yield


@pytest.fixture(autouse=True)
def _tmux_residual(tmux_isolation):
    """㉡ — 시험 하나가 끝날 때마다 운영 세션을 다시 읽어 «시험 임시 폴더를 cwd 로 가진» 세션이 있으면 그 시험을 실패시킨다.

    스로틀 없이 매 시험(한 번 ≈ 5ms). 스로틀이 있으면 마지막 시험이 남긴 잔류를 세션 끝이 잡고 rc 가 0 으로 남았다(DA#57 H1).
    """
    yield
    fails, lines = iso.report(tmux_isolation)
    for line in lines:
        print(f"{iso.TAG} {line}", file=sys.stderr)
    if fails:
        pytest.fail(lines[0], pytrace=False)


@pytest.fixture
def real_tmux_bin(tmux_isolation) -> str:
    """실 tmux 절대 경로가 필요한 시험용 — 없으면 «판정 불가» 로 skip(결과 그대로)."""
    if not tmux_isolation["real"]:
        pytest.skip("판정 불가 tmux 없음")
    return tmux_isolation["real"]
