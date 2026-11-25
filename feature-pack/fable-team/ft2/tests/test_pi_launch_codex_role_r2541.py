"""ft2 개설 길의 DA 좌석 = codex (r2541 K6 · 반례 ⑨ ⑩ ⑪ · 변이 M6 M7).

계약:
- ⑨ `--role da --dry-run` 의 tmux 명령 = codex 실행 파일 + `-c model_reasoning_effort="low"` + `-c model="gpt-6.1-sol"` +
  `-c service_tier="priority"`. pi 전용 인자(`-e <좌석 도구>` · `--approve` · `--thinking`) 0 · pi 글자 0.
- ⑩ `--role nano` · `--role session --dry-run` 의 tmux 명령 = 지금(pi)과 같은 글자 — 실행 파일 pi · `-e` 좌석 도구 · `--approve` ·
  `--model`/`--thinking` · 첫 본문 동일.
- ⑪ codex 실행 파일을 못 찾는 PATH 에서 `--role da` → «판정 불가» 1줄 · rc2 · git·tmux 0 · pi 로 대신 띄우기 0.
- M6 da 행에서도 pi 를 쓰면 ⑨ Red · M7 codex 못 찾을 때 pi 로 떨어지면 ⑪ Red(사본에서만 고친다).

대역 = test_pi_launch 세계(임시 root · 가짜 git·tmux·pi·codex) · 실 tmux·실 좌석 0 · sleep 0 · 70초 안.
"""
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FT2 = HERE.parent
_spec = importlib.util.spec_from_file_location("r2541_pl", str(HERE / "test_pi_launch.py"))
pl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pl)

LAUNCH = pl.LAUNCH
DA_MODEL, DA_EFFORT = "gpt-6.1-sol", "low"
NANO_MODEL = "opengateway/deepseek/deepseek-v4.1-flash-ultrafast"
CODEX_FLAGS = ["-c", 'model_reasoning_effort="%s"' % DA_EFFORT,
               "-c", 'model="%s"' % DA_MODEL, "-c", 'service_tier="priority"']


def world(tmp, codex=True):
    """격리 세계 1개 — 가짜 bin 에 codex 를 더한다(가짜 프로그램 본문은 pi 와 같다)."""
    root, fake = pl._paths(tmp)
    if codex:
        shutil.copyfile(fake / "pi", fake / "codex")
        (fake / "codex").chmod(0o755)
    pl._runtime(root)
    return root, fake


def dry(root, fake, extra, launcher=LAUNCH):
    out, rc = pl._launch(root, fake, launcher, extra=list(extra) + ["--dry-run"])
    assert rc == 0 and out["dry_run"] is True, out
    return out


def binary_of(argv, flag):
    """`flag` 바로 앞 칸 = tmux 가 돌릴 실행 파일(명령 꼴 = tmux 옵션 · `-e` 쌍 · 실행 파일 …)."""
    return argv[argv.index(flag) - 1]


def case_da_is_codex(tmp, launcher=LAUNCH):
    """⑨ da 행 → codex 실행 파일 + -c 3축 · pi 전용 인자 0 · pi 글자 0."""
    root, fake = world(tmp)
    out = dry(root, fake, ["--role", "da"], launcher)
    argv = out["argv"]["tmux"]
    assert (out["model"], out["effort"]) == (DA_MODEL, DA_EFFORT), out
    assert argv[:5] == ["tmux", "new-session", "-d", "-s", pl.HOLDER], argv[:5]
    assert "--dangerously-bypass-approvals-and-sandbox" in argv, argv
    assert binary_of(argv, "--dangerously-bypass-approvals-and-sandbox") == str(fake / "codex"), argv
    start = argv.index("--dangerously-bypass-approvals-and-sandbox") + 1
    assert argv[start:start + len(CODEX_FLAGS)] == CODEX_FLAGS, argv
    assert argv[start + len(CODEX_FLAGS):] == [argv[-1]], argv   # 뒤에는 첫 본문 1개뿐
    for banned in ("--thinking", "--approve", "-e " + str(FT2 / "adapters" / "pi" / "ft2-seat.ts")):
        assert banned not in argv, (banned, argv)
    assert not any(token == "pi" or token.endswith("/pi") for token in argv), argv
    assert "--thinking" not in argv and "--model" not in argv, argv


def case_pi_rows_unchanged(tmp, launcher=LAUNCH):
    """⑩ nano · session 행 = 지금(pi) 글자 그대로 — 첫 본문도 같다."""
    root, fake = world(tmp)
    seen = {}
    for role, model, effort in (("nano", NANO_MODEL, "medium"), ("session", "claude-opus-5-5", "medium")):
        argv = dry(root, fake, ["--role", role], launcher)["argv"]["tmux"]
        approve = argv.index("--approve")
        assert argv[approve - 3] == str(fake / "pi") and argv[approve - 2] == "-e", argv
        assert argv[approve - 1] == str(FT2 / "adapters" / "pi" / "ft2-seat.ts"), argv
        assert argv[-5:-1] == ["--model", model, "--thinking", effort], argv
        assert "--dangerously-bypass-approvals-and-sandbox" not in argv, argv
        assert str(fake / "codex") not in argv, argv
        assert argv.count("-e") == 8, argv   # tmux env 5 + 좌석 이름 2 + 좌석 도구 1(r1905 · r2478)
        seen[role] = argv
    assert seen["nano"][-1] == seen["session"][-1], "같은 일의 첫 본문은 같다"


def case_no_codex(tmp, launcher=LAUNCH):
    """⑪ PATH 에 codex 없음 → «판정 불가» 1줄 · rc2 · 바깥 호출 0 · pi 로 대신 띄우기 0."""
    root, fake = world(tmp, codex=False)
    out, rc = pl._launch(root, fake, launcher, extra=["--role", "da"], env_extra={"PATH": str(fake)})
    assert (out["result"], rc, out.get("step")) == ("복구 필요", 2, "codex 없음"), out
    assert "판정 불가" in out["reason"] and "codex 없음" in out["reason"], out["reason"]
    assert pl._log(fake) == [], "git·tmux 0"
    assert "pi" not in out["reason"], "pi 로 대신 띄우기 0"


def test_09_da_is_codex(tmp_path):
    case_da_is_codex(tmp_path)


def test_10_pi_rows_unchanged(tmp_path):
    case_pi_rows_unchanged(tmp_path)


def test_11_no_codex_no_seat(tmp_path):
    case_no_codex(tmp_path)


MUTANTS = {
    # M6 — 실행기 칸을 무시하고 da 행도 pi 로 띄운다
    "M6": ("adapters/pi/launch_plan.py",
           '    if executor == "codex":\n        return [binary or "codex", "--dangerously-bypass-approvals-and-sandbox"]',
           '    if executor == "codex" and False:\n        return [binary or "codex", "--dangerously-bypass-approvals-and-sandbox"]',
           case_da_is_codex),
    # M7 — codex 를 못 찾으면 pi 로 떨어진다
    "M7": ("adapters/pi/launch_plan.py",
           '''    found = shutil.which("codex" if executor == "codex" else "pi",''',
           '''    found = shutil.which("pi",''',
           case_no_codex),
}


def copy_tree(tmp):
    """이 팩의 사본 1개(tests·__pycache__ 뺌)."""
    tree = Path(tmp) / "m" / "ft2"
    if not tree.exists():
        shutil.copytree(FT2, tree, ignore=shutil.ignore_patterns("tests", "__pycache__"))
    return tree


@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_mutants(name, tmp_path):
    """변이는 사본에서만 — 사본 = Red · 원본 = 같은 사례 1회 더 PASS."""
    rel, old, new, case = MUTANTS[name]
    tree = copy_tree(tmp_path)
    text = (tree / rel).read_text(encoding="utf-8")
    assert text.count(old) == 1, (name, old[:60])
    (tree / rel).write_text(text.replace(old, new), encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    try:
        case(src, tree / "adapters" / "pi" / "launch.py")   # 사본 = Red
    except AssertionError:
        pass
    else:
        raise AssertionError("%s — 사본이 Red 가 아니다" % name)
    ok = tmp_path / "ok"
    ok.mkdir()
    case(ok)                                                 # 원본 = PASS
