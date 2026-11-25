"""r2478 keeper 가 연 나노 좌석도 좌석 이름 env(FT_SEAT · FT_SEAT_NAME)를 갖고 떠서 리포 루트 find · grep -r 이 문지기에서 거절된다.

반례 ①~⑥ · 변이 M1~M3 · 좌석 env 는 «tmux 가 세션에 넣는 값» 그대로 만든다 = 부모 프로세스 env(다른 좌석 값이 섞여 있다) +
계획의 `-e` 칸(덮어쓰기) · 판정은 실제 문지기 확장의 on("tool_call") handler 로 부른다(도우미 = seat_env_guard_r2478.py).
격리 = tmp 런타임·tmp 리포 루트·가짜 git·tmux·pi · 실 tmux·실 pi·실 grep·실 find 실행 0 · sleep 0 · 70초 안(파일 8초).
"""
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("seat_env_guard_r2478", str(HERE / "seat_env_guard_r2478.py"))
g = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(g)
NODE, cells, guard_world, run_guard, session_env = g.NODE, g.cells, g.guard_world, g.run_guard, g.session_env
FT2 = HERE.parent
NANO, ROLE, OTHER = "biz-harness-nano-r2478#0", "biz-harness-da-codex#57", "biz-other-seat#9"
NOAUTHUNT = "홈·리포 루트·.fable-team·design·.worktrees·docs 통째 find·grep -r·rg 0 · ci 또는 폴더 지정"   # r2512 넓은 대상·rg 추가

spec = importlib.util.spec_from_file_location("r2478_pl", str(HERE / "test_pi_launch.py"))
pl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pl)


def launcher_of(ft2):
    return Path(ft2) / "adapters" / "pi" / "launch.py"


def world(tmp, holder):
    """팀 런타임 1개 — 배정 주인(holder)이 곧 여는 세션 이름이다(코어 계약)."""
    root, fake = pl._paths(tmp)
    assert pl._cli(root, "submit", "--command", "c-" + pl.WORK, "--body", "본문-" + pl.WORK, "--work", pl.WORK)[1] == 0
    assert pl._cli(root, "assign", "--work", pl.WORK, "--holder", holder, "--evidence", "v1,v2")[1] == 0
    assert pl._cli(root, "deliver", "--work", pl.WORK)[1] == 0
    return root, fake


def dry(root, fake, launcher=pl.LAUNCH, extra=(), env_extra=None):
    out, rc = pl._launch(root, fake, launcher, extra=["--dry-run"] + list(extra), env_extra=env_extra)
    assert rc == 0 and out["dry_run"] is True, out
    return out


def nano_world(tmp, ft2=FT2):
    """나노 계획 1개 + «부모 env 에 다른 좌석 이름» — (루트, 가짜 bin, 부모 env, 계획 tmux argv)."""
    root, fake = world(Path(tmp), NANO)
    parent = pl._env(fake, extra={"FT_SEAT": OTHER, "FT_SEAT_NAME": OTHER})
    tmux = dry(root, fake, launcher_of(ft2), env_extra={"FT_SEAT": OTHER, "FT_SEAT_NAME": OTHER})["argv"]["tmux"]
    return root, fake, parent, tmux


def plan_cells(tmp, ft2=FT2):
    """① nano 계획의 `-e` 칸 = FT_SEAT · FT_SEAT_NAME 각 1개 = 여는 세션 이름 · ⑤ 역할 좌석도 같은 2칸."""
    for holder, role in ((NANO, "nano"), (ROLE, "da")):
        root, fake = world(Path(tmp) / role, holder)
        tmux = dry(root, fake, launcher_of(ft2), extra=["--role", role])["argv"]["tmux"]
        assert tmux[4] == holder, tmux[:6]                                                  # -s <holder> = 같은 값
        assert (cells(tmux, "FT_SEAT"), cells(tmux, "FT_SEAT_NAME")) == ([holder], [holder]), tmux


def intent_cells(tmp, ft2=FT2):
    """② 실제 열기 1회 → 의도 칸 = FT2_* 5개 그대로 · 좌석 이름 2칸은 의도에 없다(argv 에만)."""
    root, fake = world(Path(tmp), NANO)
    out, rc = pl._launch(root, fake, launcher_of(ft2))
    assert (rc, out.get("opened")) == (0, True), out
    got = json.loads(pl._intent(root).read_text(encoding="utf-8"))
    assert [k for k in pl.SEAT_ENV if got.get(k)] == list(pl.SEAT_ENV), got
    assert [k for k in ("FT_SEAT", "FT_SEAT_NAME") if k in got] == [], sorted(got)


def first_line(tmp, ft2=FT2):
    """⑥ 첫 본문에 금지 1구 — 정확히 1번."""
    root, fake = world(Path(tmp), NANO)
    body = dry(root, fake, launcher_of(ft2))["argv"]["tmux"][-1]
    assert body.count(NOAUTHUNT) == 1 and "쪽지 = bash" in body, body
    assert body.index("recv %s" % NANO) < body.index(NOAUTHUNT), body


def parent_cases(tmp, ft2=FT2):
    """④ 부모 env 에 다른 좌석 이름이 있어도 세션 env 의 좌석 이름 = 여는 세션 이름(계획의 `-e` 칸이 이긴다)."""
    _, _, parent, tmux = nano_world(Path(tmp), ft2)
    assert (parent.get("FT_SEAT"), parent.get("FT_SEAT_NAME")) == (OTHER, OTHER), "부모 env 에 다른 좌석을 심지 못했다"
    env = session_env(parent, tmux)
    assert (env.get("FT_SEAT"), env.get("FT_SEAT_NAME")) == (NANO, NANO), (env.get("FT_SEAT"), env.get("FT_SEAT_NAME"))


def guard_cases(tmp, ft2=FT2):
    """③ 나노 계획의 `-e` 칸을 세션 env 로 되돌려 실제 handler 로 판정(부모 env 에는 다른 좌석 이름이 들어 있다)."""
    _, _, parent, tmux = nano_world(Path(tmp), ft2)
    ext, repo = guard_world(Path(tmp))
    got = run_guard(tmp, ext, repo, [
        ("grep_root", session_env(parent, tmux), "grep -rl foo ."),                     # ③ 루트 재귀 grep = 거절(나노 갈래)
        ("grep_narrow", session_env(parent, tmux), "grep -rl foo design/harness"),      # ③ 좁힌 폴더 = 통과
        ("find_root", session_env(parent, tmux), "find . -name 'DA-pre-*'"),            # ③ 루트 find = 거절(FT_SEAT_NAME 갈래)
        ("find_narrow", session_env(parent, tmux), "find design/harness -name 'r24*'"), # ③ 좁힌 find = 통과
    ])
    assert (got["grep_root"]["block"], got["find_root"]["block"]) == (True, True), got
    assert (got["grep_narrow"]["block"], got["find_narrow"]["block"]) == (False, False), got
    assert "ci search" in got["grep_root"]["reason"] and "git ls-files" in got["find_root"]["reason"], got
    log = repo / ".fable-team" / "state" / "nano-grep-block.log"
    assert log.is_file() and len([x for x in log.read_text(encoding="utf-8").splitlines() if x.strip()]) == 2, log


def role_case(tmp, ft2=FT2):
    """⑤ 역할 좌석(DA 등 keeper 가 여는 석)은 이름에 nano 가 없어 find 갈래만 켜진다(기존 확장 계약 그대로)."""
    root, fake = world(Path(tmp), ROLE)
    tmux = dry(root, fake, launcher_of(ft2), extra=["--role", "da"])["argv"]["tmux"]
    assert (cells(tmux, "FT_SEAT"), cells(tmux, "FT_SEAT_NAME")) == ([ROLE], [ROLE]), tmux
    ext, repo = guard_world(Path(tmp))
    env = session_env(pl._env(fake), tmux)
    got = run_guard(tmp, ext, repo, [("grep_root", env, "grep -rl foo ."), ("find_root", env, "find . -name x")])
    assert (got["grep_root"]["block"], got["find_root"]["block"]) == (False, True), got


def test_01_plan_cells(tmp_path):
    plan_cells(tmp_path)


def test_02_intent_keeps_five(tmp_path):
    intent_cells(tmp_path)


def test_03_first_body_ban_line(tmp_path):
    first_line(tmp_path)


@pytest.mark.skipif(NODE is None, reason="node 없음 — 문지기 확장 판정 불가")
def test_04_guard_reads_plan_env(tmp_path):
    guard_cases(tmp_path)


@pytest.mark.skipif(NODE is None, reason="node 없음 — 문지기 확장 판정 불가")
def test_05_role_seat_same_cells(tmp_path):
    role_case(tmp_path)


def test_05b_parent_env_loses(tmp_path):
    parent_cases(tmp_path)


SEAT_ENV_LINE = '("FT2_ROOT", "FT2_TEAM", "FT2_WORK", "FT2_HOLDER", "FT2_ATTEMPT"), (root, team, work, holder, attempt)'
NAMES_CELL = "[(key, holder) for key in SEATKEYS]"
MUTANTS = {
    # ③ find Red — FT_SEAT_NAME 칸을 뺀다
    "M1": ("launch_plan.py", NAMES_CELL, "[(key, holder) for key in SEATKEYS if key != \"FT_SEAT_NAME\"]", guard_cases),
    # ④ Red — 석 이름 대신 부모 env 값
    "M2": ("launch_plan.py", NAMES_CELL, "[(key, os.environ.get(key)) for key in SEATKEYS if os.environ.get(key)]", parent_cases),
    # ② Red — 의도 칸이 6개(seat_env 에 좌석 이름을 끼움)
    "M3": ("launch_plan.py", SEAT_ENV_LINE,
           '("FT2_ROOT", "FT2_TEAM", "FT2_WORK", "FT2_HOLDER", "FT2_ATTEMPT", "FT_SEAT"), (root, team, work, holder, attempt, holder)', intent_cells),
}


def _mutant(tmp, name):
    """ft2 사본 1개에서만 고친다 — 사본의 launch.py 가 자기 사본의 launch_plan.py 를 읽는다."""
    filename, needle, replacement, _ = MUTANTS[name]
    dest = Path(tmp) / "mutant" / "feature-pack" / "fable-team" / "ft2"
    shutil.copytree(FT2, dest, ignore=shutil.ignore_patterns("__pycache__"))
    target = dest / "adapters" / "pi" / filename
    text = target.read_text(encoding="utf-8")
    if text.count(needle) != 1:
        raise RuntimeError("%s 치환 0 — needle 불일치" % name)
    target.write_text(text.replace(needle, replacement), encoding="utf-8")
    return dest


@pytest.mark.skipif(NODE is None, reason="node 없음 — 문지기 확장 판정 불가")
@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_06_mutants(tmp_path, name):
    """변이 = 그 사례 빨강 · 같은 사례를 원본으로 1회 더 = 초록."""
    case = MUTANTS[name][3]
    with pytest.raises(AssertionError):
        case(tmp_path / name, _mutant(tmp_path / name, name))
    case(tmp_path / (name + "-orig"))
