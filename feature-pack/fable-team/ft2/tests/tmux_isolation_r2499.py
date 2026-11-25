"""r2499 시험 tmux 격리 도우미 — tests/conftest.py 가 시험 전부에 자동으로 걸고, 시험(test_tmux_isolation_r2499.py)이 직접 부른다.

보장 2개만 (카드 r2499 · DA#59 H2):
㉠ 기본 환경 격리 — 시험 프로세스의 os.environ 을 물려받는 tmux 호출은 PATH 맨 앞 «가짜 tmux» 로 간다(rc0 · 출력 0 · 호출 기록).
   가짜를 지나친 호출(절대 경로 · `real_tmux` 표식 시험)은 TMUX_TMPDIR 이 시험 임시 폴더라 따로 선 서버로 간다.
   TMUX·TMUX_PANE 은 지운다 — 좌석 안에서 부르면 $TMUX 소켓(운영)으로 직행한다(r2490 실측).
㉡ 종료 시 잔류 검출 — 시험 임시 폴더를 cwd 로 가진 운영 세션(기본 소켓)이 남아 있으면 «실 tmux 세션 남음 <이름>» 으로 실패.

못 잡는 꼴(알려진 한계) — 도중 접촉(열었다 닫음 · `-S <운영 소켓>` 지정 · env 를 새로 만들어 PATH 와 TMUX_TMPDIR 을 버림).
앞뒤 세션 목록이 같다는 것은 운영 미접촉의 증거가 아니다(DA#59 H2). 임시 서버에 남은 세션은 kill 하지 않는다(WARN 만).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TAG = "TMUX-ISOLATION"
FAKE = '#!/bin/sh\n[ -n "${FT2_TMUX_FAKE_LOG:-}" ] && printf \'%s\\n\' "$*" >> "$FT2_TMUX_FAKE_LOG"\nexit 0\n'
DROP = ("TMUX", "TMUX_PANE", "TMUX_TMPDIR")


def real_bin(path: str | None = None) -> str | None:
    """가짜를 PATH 에 넣기 «전» 의 실 tmux 절대 경로 — 없으면 None(판정 불가)."""
    return shutil.which("tmux", path=path or os.environ.get("PATH"))


def ops_sessions(binary: str | None) -> tuple[dict[str, str], str | None]:
    """운영(기본 소켓) 세션 {이름: cwd} — (세션, 문제). 문제 = «판정 불가 …» 1줄(tmux 없음·목록 못 읽음)."""
    if not binary:
        return {}, "판정 불가 tmux 없음 — 잔류 검출 못 함"
    env = {k: v for k, v in os.environ.items() if k not in DROP}
    try:
        r = subprocess.run([binary, "list-sessions", "-F", "#{session_name}\t#{pane_current_path}"],
                           capture_output=True, text=True, env=env, timeout=7)
    except (OSError, subprocess.TimeoutExpired) as e:
        return {}, f"판정 불가 운영 tmux 목록 못 읽음({e.__class__.__name__})"
    if r.returncode == 0:
        out = {}
        for line in r.stdout.splitlines():
            name, _, cwd = line.partition("\t")
            if name:
                out[name] = cwd
        return out, None
    if "no server running" in r.stderr:
        return {}, None
    return {}, f"판정 불가 운영 tmux 목록 못 읽음(rc={r.returncode} · {r.stderr.strip()[:120]})"


def under(cwd: str, roots: list[str]) -> bool:
    if not cwd:
        return False
    real = os.path.realpath(cwd)
    return any(real == os.path.realpath(r) or real.startswith(os.path.realpath(r) + os.sep) for r in roots if r)


def residual(sessions: dict[str, str], roots: list[str]) -> list[tuple[str, str]]:
    """시험 임시 폴더를 cwd 로 가진 운영 세션 = 잔류. [(이름, cwd)]"""
    return sorted((n, c) for n, c in sessions.items() if under(c, roots))


def messages(sessions: dict[str, str], roots: list[str], before: dict[str, str]) -> tuple[list[str], list[str]]:
    """(실패 줄들, 경고 줄들) — 실패 = 잔류 · 경고 = cwd 가 시험 임시 폴더 밖인 새 세션(동시 좌석일 수 있음)."""
    fails = [f"실 tmux 세션 남음 {n} (cwd={c})" for n, c in residual(sessions, roots)]
    news = [n for n in sessions if n not in before]
    warns = [f"시험 밖 tmux 세션 열림: {n} (cwd={sessions[n]})" for n in news if (n, sessions[n]) not in residual(sessions, roots)]
    return fails, warns


def isolate(base: str | Path) -> dict:
    """㉠ — 가짜 tmux 를 PATH 맨 앞에, TMUX_TMPDIR = 시험 임시 폴더, TMUX·TMUX_PANE 삭제. 되돌릴 값도 함께 돌려준다."""
    base = Path(os.path.realpath(str(base)))
    before_bin = real_bin()
    fake_dir = base / "tmux-fake-bin"
    # 소켓 폴더는 «짧은» /tmp 아래 — 유닉스 소켓 경로 상한(sun_path 104바이트)에 pytest 임시 폴더 경로가 걸린다(실측: File name too long).
    sock = Path(tempfile.mkdtemp(prefix="r2499-tmux-", dir="/tmp"))
    fake_dir.mkdir(parents=True, exist_ok=True)
    fake = fake_dir / "tmux"
    fake.write_text(FAKE, encoding="utf-8")
    fake.chmod(0o755)
    keep = {k: os.environ.get(k) for k in (*DROP, "FT2_TMUX_FAKE_LOG", "PATH")}
    os.environ["PATH"] = str(fake_dir) + os.pathsep + (os.environ.get("PATH") or "")
    os.environ["TMUX_TMPDIR"] = str(sock)
    os.environ["FT2_TMUX_FAKE_LOG"] = str(base / "tmux-fake.log")
    for k in ("TMUX", "TMUX_PANE"):
        os.environ.pop(k, None)
    state = {"base": str(base), "real": before_bin, "fake": str(fake), "fake_dir": str(fake_dir),
             "log": os.environ["FT2_TMUX_FAKE_LOG"], "sock": str(sock), "keep": keep,
             "path_before": keep["PATH"] or ""}
    state["before"], state["problem"] = ops_sessions(before_bin)
    return state


def restore(state: dict) -> None:
    """env 되돌리기 + 임시 소켓 정리 — 남은 세션이 있으면 WARN 1줄만(kill 0 · 하드 룰 2), 비었으면 폴더만 지운다."""
    for k, v in state["keep"].items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    left = iso_sessions(state["sock"], state.get("real"))
    if left:
        print(f"{TAG} WARN 임시 소켓에 세션 {len(left)} 남음(그대로 둠 · kill 0): {', '.join(sorted(left))}", file=sys.stderr)
    else:
        shutil.rmtree(state["sock"], ignore_errors=True)


def fake_calls(state: dict) -> list[str]:
    p = Path(state["log"])
    return p.read_text(encoding="utf-8").splitlines() if p.exists() else []


def if_stub(tmp: Path, script: str) -> str:
    """시험용 tmux 대역 — 잔류 검출·«판정 불가» 갈래를 운영 서버 없이 고정한다."""
    p = Path(tmp) / ("tmux-stub-%d" % os.getpid())
    p.write_text(script, encoding="utf-8")
    p.chmod(0o755)
    return str(p)


def server_sessions(sock_dir: str, name: str, cwd: str, binary: str | None) -> tuple[str, bool]:
    """임시 소켓에 세션 1개(실 tmux 일 때만) — (안내 1줄, 만들었나)."""
    if not binary:
        return "판정 불가 tmux 없음", False
    env = {k: v for k, v in os.environ.items() if k not in ("TMUX", "TMUX_PANE")}
    env["TMUX_TMPDIR"] = sock_dir
    r = subprocess.run([binary, "new-session", "-d", "-s", name, "-c", cwd, "sleep 30"],
                       capture_output=True, text=True, env=env, timeout=25)
    return (r.stderr or r.stdout).strip(), r.returncode == 0


def kill_iso_session(sock_dir: str, name: str, binary: str | None) -> None:
    """임시 소켓의 그 세션만 닫는다 — kill-server 0(하드 룰 2)."""
    if not binary:
        return
    env = {k: v for k, v in os.environ.items() if k not in ("TMUX", "TMUX_PANE")}
    env["TMUX_TMPDIR"] = sock_dir
    subprocess.run([binary, "kill-session", "-t", "=" + name], capture_output=True, text=True, env=env, timeout=7)


def iso_sessions(sock_dir: str, binary: str | None) -> dict[str, str]:
    """임시 소켓 쪽 세션 목록 — 격리가 실제로 선 서버로 갔는지 본다."""
    if not binary:
        return {}
    env = {k: v for k, v in os.environ.items() if k not in ("TMUX", "TMUX_PANE")}
    env["TMUX_TMPDIR"] = sock_dir
    r = subprocess.run([binary, "list-sessions", "-F", "#{session_name}\t#{pane_current_path}"],
                       capture_output=True, text=True, env=env, timeout=7)
    out = {}
    for line in (r.stdout or "").splitlines():
        name, _, cwd = line.partition("\t")
        if name:
            out[name] = cwd
    return out


def report(state: dict) -> tuple[int, list[str]]:
    """시험 끝 1회 검사 — (실패 수, 찍을 줄들). 못 읽으면 «판정 불가» 1줄 · 결과 그대로."""
    sessions, problem = ops_sessions(state.get("real"))
    if problem:
        return 0, [problem]
    fails, warns = messages(sessions, [state["base"]], state.get("before") or {})
    return len(fails), [f"WARN {w}" for w in warns] + list(fails)


if __name__ == "__main__":  # 손으로 돌릴 때 = 지금 env 그대로 1회 검사(좌석 안 디버깅)
    st = {"base": sys.argv[1], "real": real_bin(), "sock": sys.argv[1], "before": {}}
    n, lines = report(st)
    print("\n".join(f"{TAG} {x}" for x in lines) or f"{TAG} PASS 잔류 0")
    sys.exit(1 if n else 0)
