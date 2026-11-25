"""r2562 반례 ⑱ — 요청 글을 쓰는 도중 죽음(주입 = 임시 파일 반쯤 쓴 뒤) → 요청 이름 파일 0 · 장부 열린 채 →
같은 close 다시 → 유효 요청 1개 · 닫힘 · keeper attempt 합 1. 그리고 요청 이름에 깨진 파일을 손으로 둠 → close rc 1 · 장부 열린 채.

이 파일이 재는 것(카드 반례 ⑱ 그대로 · 다른 입력 아님)
  ① 주입 = 임시 파일 반쯤 쓴 뒤 os._exit(9) → 이름 파일(<stem>@<q_ts>.json) 0개 · 임시 파일만 남음 · 장부 state=open
  ② 같은 close 다시(제품 그대로) → 요청 1개 · 칸(card·q_ts·reply_ts·key·at 꼴) 맞음 · 장부 closed manual:answered
  ③ keeper 1바퀴 = 고름 · attempt 합 1 · 둘째 바퀴 attempt 그대로 1(요청 at 이 이미 시작한 intent 앞이 아니라 뒤)
  ④ 요청 이름에 깨진 파일을 손으로 둔 뒤 close → rc 1 · 장부 열린 채

죽는 변이(제품 코드는 반례가 Red 일 때만 고친다 — 여기서는 두 변이만 실측)
  M17 = 요청을 이름 파일에 바로 씀(임시 파일 → 옮기기 뺌) → ① 에서 이름 파일이 반쯤 생겨 ② 가 rc1 · 장부 열린 채 = Red
  M18 = 있는 요청을 검사 없이 두고 닫음 → ④ 가 rc0 · 닫힘 = Red

대역 = r2111 세계(임시 root·git·가짜 tmux·launch·record) + 1.x close 도구(같은 임시 root 의 state 를 쓴다).
실 tmux·명부·ft2 원장·우편함·설치 0 · sleep 0.
"""
import importlib.util, json, os, shutil, subprocess, sys, time  # noqa: E401
from pathlib import Path
import pytest

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("keeper_next_r2562_crash_r2113", str(HERE / "keeper_next_reopen_name_tail_r2113.py"))
r13 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r13)
base, kw = r13.base, r13.kw
S, DAY = "r2562-crash-card", "2026-11-24T"
Q, KEY, REPLY = "1795446397.092069", "r2562-crash", "1795474243.991329"


def legacy_bin() -> Path:   # 1.x 라이브 bin(제품 그대로)
    return kw.OLD / "bin"


def copy_tool(dst: Path, m17: bool = False, m18: bool = False) -> Path:   # 대역 사본 = 크래시 주입(+변이)
    dst.mkdir(parents=True, exist_ok=True)
    for name in ("ft_desk_reply_wake.py", "ft_desk_reply_thread.py"):
        shutil.copy2(legacy_bin() / name, dst / name)
    p = dst / "ft_desk_reply_thread.py"
    t = p.read_text(encoding="utf-8")
    old = "        with open(tmp, \"w\", encoding=\"utf-8\") as fh:\n            fh.write(body + \"\\n\")\n            fh.flush()\n            os.fsync(fh.fileno())\n"
    assert t.count(old) == 1, "크래시 주입 자리 없음"
    t = t.replace(old, "        with open(tmp, \"w\", encoding=\"utf-8\") as fh:\n            fh.write(body[: max(1, len(body) // 2)])\n            fh.flush()\n            os._exit(9)   # 주입 = 부분 쓰기 도중 죽음\n", 1)
    if m17:   # 이름 파일에 바로 씀(임시 파일 → 옮기기 뺌)
        o17 = "    tmp = d / (\"%s@%s.json.tmp.%d\" % (stem, q, os.getpid()))"
        assert t.count(o17) == 1, "M17 자리 없음"
        t = t.replace(o17, "    tmp = final", 1)
    if m18:   # 있는 요청을 검사 없이 두고 닫음
        o18 = "    if final.exists():\n        return _resume_existing(final, stem, q)"
        assert t.count(o18) == 1, "M18 자리 없음"
        t = t.replace(o18, "    if final.exists():\n        return 0, \"\"", 1)
    p.write_text(t, encoding="utf-8")
    return dst / "ft_desk_reply_wake.py"


def ledger(w) -> Path:
    return w.state / "desk-reply-wait.jsonl"


def open_row(w) -> None:   # 답 대기 장부 1줄(카드 칸 · 답 알림이 이미 와 notified_ts = reply_ts)
    ledger(w).write_text(json.dumps({"q_ts": Q, "kind": "question", "key": KEY, "card": S, "at": 1794301443, "deadline": 1794387843,
                                     "state": "open", "notified_ts": REPLY}, ensure_ascii=False) + "\n", encoding="utf-8")


def row_state(w) -> str:
    rows = [json.loads(x) for x in ledger(w).read_text(encoding="utf-8").splitlines() if x.strip()]
    return rows[0].get("state") if rows else "없음"


def close(w, tool: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "FT_ROOT": str(w.root), "FT_DESK_REPLY_LEDGER": str(ledger(w)), "FT_NOW": str(w.t)}   # 세계의 가짜 시계(ISO)를 epoch 로
    return subprocess.run([sys.executable, str(tool), "--close", KEY, "--reason", "answered"], cwd=str(w.root), env=env,
                          capture_output=True, text=True, timeout=60)


def req_dir(w) -> Path:
    return w.state / "card-resume"


def names(w) -> list:
    return sorted(p.name for p in req_dir(w).glob("*.json")) if req_dir(w).is_dir() else []


def valid(w) -> dict:
    o = json.loads((req_dir(w) / ("%s@%s.json" % (S, Q))).read_text(encoding="utf-8"))
    time.strptime(str(o.get("at")), "%Y-%m-%dT%H:%M:%S")
    return o


def attempts(w) -> int:
    return sum(1 for r in w.journal() if r.get("kind") == "accept" and r.get("work") == S)


def card(w):   # 표식 줄 1개(- 배정: 없음) — keeper 가 고를 수 있게
    w.commit("biz", {"design/harness/indices/대기/%s.md" % S: "# 인덱스: %s\n- 배정: 없음\n- 상태: 대기\n" % S}, "main")


def crash(w, tmp: Path, **mut: bool) -> subprocess.CompletedProcess:
    tool = copy_tool(tmp / "crash", **mut)
    return close(w, tool)


def flight_ok(w, tmp: Path, m17: bool = False) -> None:   # 반례 ⑱ 본 줄 — 주입 → 같은 close → keeper attempt 합 1
    card(w)
    open_row(w)
    r = crash(w, tmp, m17=m17)
    assert r.returncode == 9, (r.returncode, r.stdout, r.stderr)                 # 주입이 실제로 죽었다
    assert names(w) == [] and row_state(w) == "open", (names(w), row_state(w))   # 요청 이름 파일 0 · 장부 열린 채
    assert any(".tmp." in p.name for p in req_dir(w).iterdir()), list(req_dir(w).iterdir())

    r = close(w, legacy_bin() / "ft_desk_reply_wake.py")   # 같은 close 다시 = 제품 그대로
    assert r.returncode == 0, (r.stdout, r.stderr)
    o = valid(w)
    assert (o["card"], o["q_ts"], o["reply_ts"], o["key"]) == (S, Q, REPLY, KEY), o
    assert names(w) == ["%s@%s.json" % (S, Q)] and row_state(w) == "closed", (names(w), row_state(w))
    assert any(".tmp." in p.name for p in req_dir(w).iterdir()), list(req_dir(w).iterdir())   # 크래시가 남긴 임시 파일은 그대로(지우기 0) — 아래 keeper 바퀴가 그걸 요청으로 안 읽는 것을 함께 잰다

    lines = w.round()   # keeper 1바퀴 = 고름
    assert base.launched(w) == [S] and attempts(w) == 1, (base.launched(w), attempts(w), lines)
    assert len([x for x in lines if x.startswith("RESUME-ANSWER harness %s" % S)]) == 1, lines
    more = r13.r11.again(w)   # 둘째 바퀴 = 더 안 엶(요청 at 이 시작한 intent 앞)
    assert attempts(w) == 1 and base.launched(w) == [S], (attempts(w), base.launched(w), more)


def test_partial_write_then_same_close(tmp_path, monkeypatch):
    flight_ok(base.world(tmp_path, monkeypatch, {}, ft2=kw.FT2), tmp_path)


def test_mutant_m17_direct_final_name_dies(tmp_path, monkeypatch):   # 이름 파일에 바로 씀 → ① 에서 반쯤 쓴 이름 파일
    w = base.world(tmp_path / "w", monkeypatch, {}, ft2=kw.FT2)
    with pytest.raises(AssertionError):
        flight_ok(w, tmp_path, m17=True)


def test_mutant_m18_close_without_check_dies(tmp_path, monkeypatch):   # 깨진 이름 파일을 손으로 두고 close
    w = base.world(tmp_path, monkeypatch, {}, ft2=kw.FT2)
    card(w)
    open_row(w)
    req_dir(w).mkdir(parents=True, exist_ok=True)
    (req_dir(w) / ("%s@%s.json" % (S, Q))).write_text("", encoding="utf-8")   # 반쯤 쓴 요청을 손으로 둠
    r = close(w, legacy_bin() / "ft_desk_reply_wake.py")
    assert r.returncode == 1 and row_state(w) == "open", (r.returncode, r.stdout, r.stderr, row_state(w))   # 제품 = 열린 채
    tool = copy_tool(tmp_path / "m18", m18=True)
    (req_dir(w) / ("%s@%s.json" % (S, Q))).write_text("", encoding="utf-8")
    r = close(w, tool)
    assert (r.returncode, row_state(w)) == (0, "closed"), (r.returncode, row_state(w))   # M18 = 검사 없이 닫음 = Red
