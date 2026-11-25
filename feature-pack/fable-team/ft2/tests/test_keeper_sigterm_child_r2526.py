"""r2526 자식 시나리오 — r2072 장부 스텁(block raise)을 띄워 fifo 로 멈춰 둔 채 부모의 SIGTERM 을 기다린다.

부모 = test_keeper_reap_on_sigterm_r2526.py 가 R2526_CHILD=1 · R2526_READY=<경로> 를 주고 띄운다.
보통 실행(R2526_CHILD 없음)에서는 skip — 0초.
기억(blockseen.json)에 «10분 이어진 한 줄» 을 심어 1바퀴로 장부 raise(스텁 호출)까지 간다 — 10바퀴 대신.
"""
import json
import os
import re
import threading
import time
from pathlib import Path

import pytest

import keeper_block_raise_r2072 as h


@pytest.fixture(autouse=True)
def reap_stubs(tmp_path):
    """r2526 — handler 등록 · 끝나면 해제 → 띄운 스텁 그룹 거두기."""
    yield from h.reap_stubs_body(tmp_path)


def seed(w):
    """기억에 «first = now-600 · last = now» 한 줄 — 이 바퀴(now)에 바로 장부 raise 가 걸린다."""
    now = h.T0 + 600
    key = json.dumps(["판정 불가", "t1", re.sub(r"\d+", "N", h.NOMASTER % 600)], ensure_ascii=False)
    d = h.kdir(w)
    d.mkdir(parents=True, exist_ok=True)
    (d / "blockseen.json").write_text(json.dumps({key: {"first": now - 600, "last": now, "text": h.NOMASTER % 600}}, ensure_ascii=False), encoding="utf-8")


def test_owned_stub_alive_until_sigterm(tmp_path, monkeypatch):
    """③ ⑦ ⑥ 의 자식 판 — 스텁을 멈춰 세워 두고 «pid pgid» 를 기록한 뒤 ready 를 내고 신호를 기다린다."""
    if os.environ.get("R2526_CHILD") != "1":
        pytest.skip("r2526 자식 시나리오 — 부모가 SIGTERM 을 보내는 판에서만 돈다")
    w = h.world(tmp_path, monkeypatch)
    seed(w)
    os.mkfifo(str(Path(str(w.block) + ".fifo")))   # 스텁이 여기서 멈춘다(쓰는 쪽이 열 때까지)
    threading.Thread(target=lambda: h.at(w, 600, [("판정 불가", "t1", h.NOMASTER % 600)]), daemon=True).start()
    rec = Path(str(w.block) + h.REC)
    end = time.monotonic() + 20
    while time.monotonic() < end and not h.read_pairs(rec)[0]:
        time.sleep(0.02)
    assert h.read_pairs(rec)[0], "스텁이 «pid pgid» 를 안 적었다"
    Path(os.environ["R2526_READY"]).write_text("ready\n", encoding="utf-8")
    time.sleep(30)   # 부모가 SIGTERM 을 보내면 handler 가 거둔다 — 안 오면 여기서 실패
    raise AssertionError("SIGTERM 없이 30초가 지났다")


def test_normal_stub_reaped_locally(tmp_path, monkeypatch):
    """④ 의 자식 판 — 스텁을 한 번 띄우고(멈추지 않음) 정상 끝난다. 거두기는 fixture 몫(끝나고 자식 0)."""
    if os.environ.get("R2526_NORMAL") != "1":
        pytest.skip("r2526 자식 시나리오 — 부모가 «정상 끝» 을 보는 판에서만 돈다")
    w = h.world(tmp_path, monkeypatch)
    seed(w)
    h.at(w, 600, [("판정 불가", "t1", h.NOMASTER % 600)])   # fifo 없음 = 스텁이 바로 끝난다
    rec = Path(str(w.block) + h.REC)
    assert h.read_pairs(rec)[0], "스텁이 «pid pgid» 를 안 적었다"
    Path(os.environ["R2526_PIDS_OUT"]).write_text(rec.read_text(encoding="utf-8"), encoding="utf-8")   # pytest 가 basetemp 를 걷어도 부모가 본다
    Path(os.environ["R2526_READY"]).write_text("ready\n", encoding="utf-8")
