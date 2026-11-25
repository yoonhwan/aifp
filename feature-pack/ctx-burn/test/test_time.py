#!/usr/bin/env python3
"""ctx-time 시험 — 카드 ctx-time-waste 의 계약 C1 ~ C7 과 설계 §8 의 16칸(T1 ~ T16) + T17(DA HOLD 1/3 반례).

입력 = 전부 이 시험이 임시 HOME 아래 지어낸 세션 jsonl(pi · codex · claude 꼴) · 실 세션 읽기 0 ·
네트워크 0 · sleep 0. 창은 `--to` 로 고정한다(시각 의존 0).

실행: python3.11 -m pytest feature-pack/ctx-burn/test/test_time.py -q
      python3.11 -m pytest ... -q -k t7   (칸 하나)
변이: CTX_TIME_TOOL=<다른 본체 경로> 로 바꿔 끼운다 (변이가 FAIL 하는지 본다).
"""
import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.abspath(os.path.join(HERE, os.pardir))
TOOL = os.environ.get("CTX_TIME_TOOL") or os.path.join(PKG, "bin", "ctx-time")
BURN = os.path.join(PKG, "bin", "ctx-burn")

END = datetime(2026, 11, 23, 16, 0, 0)          # 창 끝(고정) · 기본 창 = 13:00 ~ 16:00
END_EP = END.timestamp()


def at(h, m=0, s=0):
    """2026-11-23 hh:mm:ss — 창 안 시각."""
    return datetime(2026, 11, 23, h, m, s)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


# ---------------------------------------------------------------- 지어낸 세션 쓰기
def sinfo(t, name):
    return {"type": "session_info", "timestamp": iso(t), "name": name}


def user(t, text="hi"):
    return {"type": "message", "timestamp": iso(t),
            "message": {"role": "user", "content": [{"type": "text", "text": text}]}}


def asst(t, ms, calls=(), text=None, thinking=None, err=None):
    m = {"role": "assistant", "durationMs": ms, "content": []}
    if text:
        m["content"].append({"type": "text", "text": text})
    if thinking:
        m["content"].append({"type": "thinking", "thinking": thinking})
    for cid, name, args in calls:
        m["content"].append({"type": "toolCall", "id": cid, "name": name, "arguments": args})
    if err:
        m["errorMessage"] = err
    return {"type": "message", "timestamp": iso(t), "message": m}


def tool(t, cid, ms, out="ok", name="bash"):
    return {"type": "message", "timestamp": iso(t),
            "message": {"role": "toolResult", "toolCallId": cid, "toolName": name, "durationMs": ms,
                        "content": [{"type": "text", "text": out}]}}


class F:
    """임시 HOME 하나 + 그 안의 세션 폴더."""

    def __init__(self):
        self.root = tempfile.mkdtemp(prefix="ctx-time-test-")
        self.home = os.path.join(self.root, "home")
        os.makedirs(self.home)

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write(self, rel, lines, mtime):
        p = os.path.join(self.home, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            for line in lines:
                f.write((line if isinstance(line, str) else json.dumps(line, ensure_ascii=False)) + "\n")
        if mtime is not None:
            os.utime(p, (mtime, mtime))
        return p

    def pi(self, folder, fname, lines, mtime=None):
        return self._write(".pi/agent/sessions/%s/%s" % (folder, fname), lines, mtime)

    def codex(self, fname, lines, mtime=None):
        return self._write(".codex/sessions/2026/11/23/%s" % fname, lines, mtime)

    def claude(self, name, lines=()):
        return self._write(".claude/projects/-tmp-x/%s" % name, list(lines), None)

    def run(self, *args, rc=0, tool=TOOL):
        env = dict(os.environ, HOME=self.home)
        p = subprocess.run([sys.executable, tool] + [str(a) for a in args],
                           capture_output=True, text=True, env=env)
        assert p.returncode == rc, "rc=%d (기대 %d)\n[stdout]\n%s\n[stderr]\n%s" % (
            p.returncode, rc, p.stdout, p.stderr)
        return p

    def js(self, *args):
        p = self.run("--json", "--no-html", "--to", "%d" % END_EP, *args)
        return json.loads(p.stdout)

    def files(self):
        out = []
        for base, _dirs, names in os.walk(self.home):
            for n in names:
                out.append(os.path.join(base, n))
        return sorted(out)


# 지어낸 한 세션 — 235초 벽시계(LLM 35 · 시험 80 · 유휴 120 · 사이 0) · 70초 넘는 명령 1개
def plain(f, folder="--tmp-x--", fname="2026-11-23T13-00-00-000Z_a.jsonl",
          name="biz-harness-nano-x#0", mtime=None):
    lines = [sinfo(at(13, 1), name),
             user(at(13, 1)),
             asst(at(13, 1, 20), 20000, [("c1", "bash", {"command": "pytest -q"})]),
             tool(at(13, 2, 40), "c1", 80000),
             asst(at(13, 2, 50), 10000),
             user(at(13, 4, 50)),
             asst(at(13, 4, 55), 5000)]
    return f.pi(folder, fname, lines, mtime if mtime is not None else at(13, 4, 56).timestamp())


# ---------------------------------------------------------------- T1 갈래 셈
def test_t1_categories():
    f = F()
    try:
        plain(f)
        d = f.js()
        assert len(d["sessions"]) == 1, d["sessions"]
        s = d["sessions"][0]
        assert s["wall"] == 235, s["wall"]
        assert s["llm"] == 35, s["llm"]
        assert s["tool"] == {"시험": 80}, s["tool"]
        assert s["idle"] == 120, s["idle"]
        assert s["other"] == 0, s["other"]
        assert s["turns"] == 2 and s["ncalls"] == 1 and s["nllm"] == 3
        assert s["seat"] == "biz-harness-nano-x#0" and s["role"] == "nano"
        t = d["totals"]
        assert t["wall"] == 235 and t["llm"] == 35 and t["tool"]["시험"] == 80
    finally:
        f.cleanup()


# ---------------------------------------------------------------- T2 --seat
def test_t2_seat():
    f = F()
    try:
        plain(f, "--a--", "2026-11-23T13-10-00-000Z_a.jsonl", "pack-ft-arch-pi#1",
              at(13, 10).timestamp())
        plain(f, "--b--", "2026-11-23T13-20-00-000Z_b.jsonl", "biz-ops-nano-x#0",
              at(13, 20).timestamp())
        d = f.js("--seat", "^aifp-")
        assert [s["seat"] for s in d["sessions"]] == ["pack-ft-arch-pi#1"], d["sessions"]
        d2 = f.js()
        assert len(d2["sessions"]) == 2
    finally:
        f.cleanup()


# ---------------------------------------------------------------- T3 --role
def test_t3_role():
    f = F()
    try:
        plain(f, "--a--", "2026-11-23T13-10-00-000Z_a.jsonl", "pack-ft-arch-pi#1",
              at(13, 10).timestamp())
        plain(f, "--b--", "2026-11-23T13-20-00-000Z_b.jsonl", "biz-ops-nano-x#0",
              at(13, 20).timestamp())
        d = f.js("--role", "nano")
        assert [s["seat"] for s in d["sessions"]] == ["biz-ops-nano-x#0"], d["sessions"]
        assert d["sessions"][0]["role"] == "nano"
    finally:
        f.cleanup()


# ---------------------------------------------------------------- T4 --hours
def test_t4_hours():
    f = F()
    try:
        # 창 안 파일 · 절반의 줄이 창 밖(12:10 · 창 = 13:00 ~ 16:00)
        lines = [sinfo(at(13, 1), "biz-harness-nano-x#0"),
                 user(at(12, 10)),
                 asst(at(12, 20), 5000),
                 user(at(13, 1)),
                 asst(at(13, 1, 20), 20000),
                 tool(at(13, 2, 40), "c1", 80000),
                 asst(at(13, 2, 50), 10000)]
        f.pi("--in--", "2026-11-23T13-00-00-000Z_a.jsonl", lines, at(13, 3).timestamp())
        # 창 밖 파일(11:00)
        f.pi("--out--", "2026-11-23T11-00-00-000Z_b.jsonl", lines, at(11, 0).timestamp())
        d = f.js("--hours", "3")
        assert len(d["sessions"]) == 1, d["sessions"]
        s = d["sessions"][0]
        # 창 안 줄만: user 13:01 · llm 20 · tool(80) · llm 10 · 그 밖 = 13:02:50-13:01:00=110
        assert s["start"] == at(13, 1).timestamp(), s["start"]
        assert s["llm"] == 30, s["llm"]
        assert s["tool"] == {"그 밖 bash": 80}, s["tool"]
        assert s["wall"] == 110 and s["other"] == 0, (s["wall"], s["other"])
    finally:
        f.cleanup()


# ---------------------------------------------------------------- T5 --max-sessions
def test_t5_max_sessions():
    f = F()
    try:
        for i in range(3):
            plain(f, "--s%d--" % i, "2026-11-23T13-1%d-00-000Z_s%d.jsonl" % (i, i),
                  "biz-harness-nano-s%d#0" % i, at(13, 10 + i).timestamp())
        d = f.js("--max-sessions", "2")
        assert len(d["sessions"]) == 2, d["sessions"]
        assert {s["seat"] for s in d["sessions"]} == {"biz-harness-nano-s2#0", "biz-harness-nano-s1#0"}
        assert d["sample"]["sessions_dropped"] == 1
        out = f.run("--no-html", "--to", "%d" % END_EP, "--max-sessions", "2", "--lang", "ko").stdout
        assert "표본 줄임: 세션 1개 빠짐(상한 2개)" in out, out
    finally:
        f.cleanup()


# ---------------------------------------------------------------- T6 --max-mb
def test_t6_max_mb():
    f = F()
    try:
        pad = "x" * 900_000
        for i in range(2):
            lines = [sinfo(at(13, 1), "biz-harness-nano-m%d#0" % i), {"type": "pad", "text": pad},
                     user(at(13, 1)), asst(at(13, 1, 20), 20000),
                     tool(at(13, 2, 40), "c9", 80000), asst(at(13, 2, 50), 10000)]
            f.pi("--m%d--" % i, "2026-11-23T13-1%d-00-000Z_m%d.jsonl" % (i, i), lines,
                 at(13, 10 + i).timestamp())
        d = f.js("--max-mb", "1.5")
        assert len(d["sessions"]) == 1, [s["seat"] for s in d["sessions"]]
        assert d["sample"]["mb_dropped"] == 1, d["sample"]
        assert d["sample"]["read_bytes"] <= int(1.5 * 1048576) + 65536, d["sample"]
        out = f.run("--no-html", "--to", "%d" % END_EP, "--max-mb", "1.5", "--lang", "ko").stdout
        assert "표본 줄임: 세션 1개 빠짐(읽기 상한" in out, out
    finally:
        f.cleanup()


# ---------------------------------------------------------------- T7 내용 유출 0
MARK = ["ZZUSER", "ZZMODEL", "ZZTHINK", "ZZOUT", "ZZCMD", "ZZERR", "ZZPATH"]


def test_t7_no_content_leak():
    f = F()
    try:
        lines = [sinfo(at(13, 1), "biz-harness-nano-x#0"),
                 user(at(13, 1), "ZZUSER 표식"),
                 asst(at(13, 1, 20), 20000, [("c1", "bash", {"command": 'printf "%s" "ZZCMD"'})],
                      text="ZZMODEL 글", thinking="ZZTHINK 생각"),
                 tool(at(13, 2, 40), "c1", 80000, out="ZZOUT 출력"),
                 asst(at(13, 3), 4000, [("c2", "read", {"path": "/tmp/ZZPATH"})]),
                 tool(at(13, 3, 30), "c2", 3000, out="ZZOUT 2", name="read"),
                 asst(at(13, 4), 2000, err="402 ZZERR boom"),
                 user(at(13, 5)),
                 asst(at(13, 5, 10), 1000)]
        f.pi("--leak--", "2026-11-23T13-00-00-000Z_a.jsonl", lines, at(13, 6).timestamp())
        js = f.run("--json", "--no-html", "--to", "%d" % END_EP).stdout
        ko = f.run("--no-html", "--to", "%d" % END_EP, "--lang", "ko").stdout
        f.run("--to", "%d" % END_EP, "--out", os.path.join(f.root, "o"))
        page = open(os.path.join(f.root, "o", "seat-time.html"), encoding="utf-8").read()
        for text, where in ((js, "json"), (ko, "터미널"), (page, "html")):
            for mark in MARK:
                assert mark not in text, "%s 에 %s 가 나왔다" % (where, mark)
        assert "printf" not in ko and "printf" not in js
        assert d_long(js) == 1, "70초 넘은 명령 1개"
    finally:
        f.cleanup()


def d_long(js_text):
    return len(json.loads(js_text)["sessions"][0]["long"])


# ---------------------------------------------------------------- T8 오류 갈래
def test_t8_error_category():
    f = F()
    try:
        lines = [sinfo(at(13, 1), "biz-harness-nano-x#0"),
                 user(at(13, 1)),
                 asst(at(13, 1, 30), 30000, err="402 ZZERR boom"),
                 asst(at(13, 2, 30), 20000, err="connection reset ZZERR"),
                 user(at(13, 3)),
                 asst(at(13, 3, 10), 10000)]
        f.pi("--err--", "2026-11-23T13-00-00-000Z_a.jsonl", lines, at(13, 4).timestamp())
        d = f.js()
        s = d["sessions"][0]
        assert s["errs"] == {"402": 1, "그 밖": 1}, s["errs"]
        assert s["nerr"] == 2 and s["err"] == 50, (s["nerr"], s["err"])
        assert "ZZERR" not in f.run("--json", "--no-html", "--to", "%d" % END_EP).stdout
    finally:
        f.cleanup()


# ---------------------------------------------------------------- T9 codex
def test_t9_codex():
    f = F()
    try:
        lines = [
            {"timestamp": iso(at(14, 0)), "type": "session_meta",
             "payload": {"type": "session_meta", "cwd": "/Users/x/Project/Agent/pack-ft-nano-cx#0"}},
            {"timestamp": iso(at(14, 0)), "type": "event_msg",
             "payload": {"type": "task_started", "started_at": 1}},
            {"timestamp": iso(at(14, 0, 5)), "type": "event_msg",
             "payload": {"type": "item_completed", "item": {"type": "CommandExecution",
                                                            "command": ["pytest", "-q"],
                                                            "duration": {"secs": 5, "nanos": 0}}}},
            {"timestamp": iso(at(14, 0, 7)), "type": "event_msg",
             "payload": {"type": "item_completed", "item": {"type": "CommandExecution",
                                                            "command": ["git", "status"],
                                                            "duration": {"secs": 2, "nanos": 0}}}},
            {"timestamp": iso(at(14, 0, 30)), "type": "event_msg",
             "payload": {"type": "task_complete", "duration_ms": 30000}},
        ]
        f.codex("rollout-2026-11-23T14-00-00-cx.jsonl", lines, at(14, 0, 31).timestamp())
        d = f.js()
        s = d["sessions"][0]
        assert s["seat"] == "pack-ft-nano-cx#0", s["seat"]
        assert s["role"] == "nano", s["role"]
        assert s["tool"] == {"시험": 5, "git": 2}, s["tool"]
        assert s["turns"] == 1 and s["ncalls"] == 2
        assert s["llm"] == 23, s["llm"]          # 턴 30초 − 명령 7초
        assert s["wall"] == 30 and s["other"] == 0, (s["wall"], s["other"])
        assert d["sessions"][0]["kinds"]["pytest"][0] == 1
    finally:
        f.cleanup()


# ---------------------------------------------------------------- T10 빠짐 줄
def test_t10_claude_omitted():
    f = F()
    try:
        f.claude("aaa.jsonl", ['{"type":"assistant","timestamp":"2026-11-23T14:00:00Z"}'])
        p = f.run("--no-html", "--to", "%d" % END_EP, "--lang", "ko", rc=0)
        assert "빠짐: claude" in p.stdout, p.stdout
        d = f.js()
        assert d["sessions"] == [], d["sessions"]
        assert d["omitted"] == ["claude", "codex:model_error_retry"]
    finally:
        f.cleanup()


# ---------------------------------------------------------------- T11 쓰기 범위
def test_t11_writes():
    f = F()
    try:
        plain(f)
        before = f.files()
        f.run("--to", "%d" % END_EP, "--no-html")
        assert f.files() == before, f.files()
        out = os.path.join(f.root, "o")
        f.run("--to", "%d" % END_EP, "--out", out)
        assert sorted(os.listdir(out)) == ["seat-time.html"], os.listdir(out)
        # json 도 파일을 만들지 않는다
        f.run("--json", "--no-html", "--to", "%d" % END_EP)
        assert sorted(os.listdir(out)) == ["seat-time.html"], os.listdir(out)
    finally:
        f.cleanup()


# ---------------------------------------------------------------- T12 --split
def test_t12_split():
    f = F()
    try:
        # 13:00 user · 13:00:20 llm 20s · 13:01:40 tool pytest 80s · 13:01:50 llm 10s(턴 끝)
        # 유휴 120s → 13:03:50 user · 13:03:50 llm 5s(턴 끝) · 13:04:00 tool sleep 90s · 13:05:30 llm 5s
        lines = [sinfo(at(13, 0), "biz-harness-nano-x#0"),
                 user(at(13, 0)),
                 asst(at(13, 0, 20), 20000, [("c1", "bash", {"command": "pytest -q"})]),
                 tool(at(13, 1, 40), "c1", 80000),
                 asst(at(13, 1, 50), 10000),
                 user(at(13, 3, 50)),
                 asst(at(13, 3, 55), 5000, [("c2", "bash", {"command": "sleep 90"})]),
                 tool(at(13, 5, 25), "c2", 90000),
                 asst(at(13, 5, 30), 5000)]
        f.pi("--split--", "2026-11-23T13-00-00-000Z_a.jsonl", lines, at(13, 6).timestamp())
        p = f.run("--to", "%d" % END_EP, "--split", iso(at(13, 2)), "--no-html", "--lang", "ko")
        d = f.js("--split", iso(at(13, 2)))
        b, a = d["split"]["before"], d["split"]["after"]
        # 앞: 13:00 ~ 13:01:50 = LLM 30 · 시험 80 · 벽 110
        assert b["llm"] == 30 and b["tool"] == {"시험": 80} and b["wall"] == 110, b
        assert b["long_count"] == 1 and b["kinds"]["pytest"][2] == 1
        assert b["kinds"]["pytest"][0] == 1 and b["kinds"]["pytest"][2] == 1
        # 뒤: 13:03:50 ~ 13:05:30 = LLM 10 · sleep 90 · 벽 100
        assert a["llm"] == 10 and a["tool"] == {"sleep 대기": 90} and a["wall"] == 100, a
        assert a["long_count"] == 1
        assert a["kinds"]["sleep"][0] == 1
        assert "→" in p.stdout, p.stdout
    finally:
        f.cleanup()


# ---------------------------------------------------------------- T13 ctx-burn --time
def test_t13_ctx_burn_time():
    f = F()
    try:
        plain(f)
        a = f.run("--no-html", "--to", "%d" % END_EP, "--lang", "ko").stdout
        b = f.run("--time", "--no-html", "--to", "%d" % END_EP, "--lang", "ko", tool=BURN).stdout
        assert a == b, "ctx-burn --time 출력이 ctx-time 과 다르다"
        # --time 없는 ctx-burn 은 ctx-burn 본체 그대로
        c = f.run("--hours", "3", "--project", f.root, tool=BURN, rc=0).stdout
        assert "ctx-burn" in c.splitlines()[0] or "ctx-burn" in c[:200], c[:300]
        assert "ctx-time" not in c, "--time 없는 출력에 ctx-time 문구가 섞였다"
    finally:
        f.cleanup()


# ---------------------------------------------------------------- T14 --max-scan
def test_t14_max_scan():
    f = F()
    try:
        # 최근 15개 파일 · 오래된 5개만 창 안 세션(이름 순서 = 만든 시각)
        for i in range(10):
            lines = [sinfo(at(15, 0, i), "biz-harness-nano-new%d#0" % i),
                     user(at(15, 0, i)), {"type": "pad", "text": "x"}]
            f.pi("--new%d--" % i, "2026-11-23T15-0%d-00-000Z_n%d.jsonl" % (i % 10, i), lines,
                 at(15, 0, i).timestamp())
        for i in range(5):
            plain(f, "--old%d--" % i, "2026-11-23T13-0%d-00-000Z_o%d.jsonl" % (i, i),
                  "biz-harness-nano-old%d#0" % i, at(13, 1 + i).timestamp())
        d = f.js("--max-scan", "10")
        assert d["sample"]["scan_cut"] == 5, d["sample"]
        assert d["sessions"] == [], [s["seat"] for s in d["sessions"]]
        out = f.run("--no-html", "--to", "%d" % END_EP, "--max-scan", "10", "--lang", "ko").stdout
        assert "훑기 줄임: 파일 5개" in out, out
    finally:
        f.cleanup()


# ---------------------------------------------------------------- T15 이름 조회 예산
def test_t15_name_budget():
    f = F()
    try:
        pad = "x" * 65_200   # 이름 줄이 앞 64KB 끝에 오게
        for i in range(400):
            lines = [{"type": "pad", "text": pad}, sinfo(at(13, 1), "biz-other-seat-%03d#0" % i),
                     user(at(13, 1)), asst(at(13, 1, 20), 20000),
                     asst(at(13, 2, 50), 10000)]
            f.pi("--n%03d--" % i, "2026-11-23T13-00-%02d-000Z_n%03d.jsonl" % (i % 60, i), lines,
                 at(13, 1).timestamp())
        d = f.js("--seat", "^zzz", "--max-mb", "1")
        assert d["sessions"] == [], d["sessions"]
        assert d["sample"]["name_unseen"] == 397, d["sample"]
        assert d["sample"]["read_bytes"] <= 1048576, d["sample"]
        # 0.2MB(3개) 에서 멈춘다 = 이름 몫 = 1MB / 5
        assert d["sample"]["read_bytes"] == 3 * 65536, d["sample"]
        out = f.run("--no-html", "--seat", "^zzz", "--max-mb", "1", "--lang", "ko",
                    "--to", "%d" % END_EP).stdout
        assert "이름 조회 줄임: 후보 397개" in out, out
    finally:
        f.cleanup()


# ---------------------------------------------------------------- T16 long · kinds 값
def test_t16_long_and_kinds():
    f = F()
    try:
        lines = [sinfo(at(13, 0), "biz-harness-nano-x#0"),
                 user(at(13, 0)),
                 asst(at(13, 1, 11), 71000, [("c1", "bash", {"command": "pytest -q tests"})]),
                 tool(at(13, 2, 31), "c1", 71000),
                 asst(at(13, 2, 41), 10000, [("c4", "bash", {"command": "pytest -q tests/test_a.py"})]),
                 tool(at(13, 2, 51), "c4", 30000),
                 asst(at(13, 3, 21), 50000, [("c2", "bash",
                                              {"command": "timeout 300 make x; sleep 5"})]),
                 tool(at(13, 6, 41), "c2", 200000),
                 asst(at(13, 8, 11), 90000, [("c3", "bash",
                                              {"command": "make build", "timeout": 600})]),
                 tool(at(13, 9, 41), "c3", 90000),
                 asst(at(13, 9, 50), 9000)]
        f.pi("--lk--", "2026-11-23T13-00-00-000Z_a.jsonl", lines, at(13, 10).timestamp())
        s = f.js()["sessions"][0]
        longs = sorted(s["long"], key=lambda x: x["sec"])
        assert [x["sec"] for x in longs] == [71, 90, 200], longs
        assert longs[0]["cat"] == "시험" and longs[0]["band"] is None
        assert "pytest" in longs[0]["kinds"]
        assert longs[1]["cat"] == "그 밖 bash" and longs[1]["band"] == "301 ~ 600초"
        assert longs[1]["kinds"] == [], longs[1]
        assert longs[2]["cat"] == "sleep 대기" and longs[2]["band"] == "141 ~ 300초"
        assert set(longs[2]["kinds"]) == {"sleep", "timeout 을 붙인 명령"}, longs[2]
        k = s["kinds"]
        assert k["pytest"] == [2, 101.0, 1, 71.0], k["pytest"]   # 최장 71 · 합 101(최장≠합)
        assert k["sleep"] == [1, 200.0, 1, 200.0], k["sleep"]
        assert k["timeout 을 붙인 명령"] == [1, 200.0, 1, 200.0]
        assert k["잡은 상한 141 ~ 300초"] == [1, 200.0, 1, 200.0]
        assert k["잡은 상한 301 ~ 600초"] == [1, 90.0, 1, 90.0]
        assert s["tool"]["sleep 대기"] == 200.0 and s["tool"]["그 밖 bash"] == 90.0
        assert s["tool"]["시험"] == 101.0
    finally:
        f.cleanup()


# ---------------------------------------------------------------- T17 예약 뒤 자란 로그 (DA HOLD 1/3 · 2/3 반례)
def load_tool():
    """본체를 모듈로 읽는다 — 시험 파일이 부르는 본체와 같은 파일(CTX_TIME_TOOL 도 따른다)."""
    loader = importlib.machinery.SourceFileLoader("ctx_time_under_test", TOOL)
    spec = importlib.util.spec_from_loader("ctx_time_under_test", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


class ReadSpy:
    """본체가 여는 파일을 감싸 «실제로 읽은 위치»(tell)를 잰다 — 상한을 넘겨 읽었는지 본다."""

    def __init__(self):
        self.tell = []
        self._open = open

    def install(self, tool):
        spy = self

        class Wrapped:
            def __init__(self, fh):
                self._fh = fh

            def __enter__(self):
                return self._fh

            def __exit__(self, *a):
                spy.tell.append(self._fh.tell())
                self._fh.close()
                return False

            def __getattr__(self, name):
                return getattr(self._fh, name)

        def fake_open(path, mode="r", *a, **k):
            return Wrapped(spy._open(path, mode, *a, **k))

        tool.open = fake_open
        return fake_open

    def uninstall(self, tool):
        tool.__dict__.pop("open", None)


def test_t17_growth_after_reserve():
    f = F()
    try:
        path = plain(f)
        reserved = os.path.getsize(path)          # pick 이 장부에 예약한 크기
        tool = load_tool()

        # 고른 뒤 로그가 2MB 자란다(반례: 52B 파일 · 1MB 예산 · 그 뒤 2MB append)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(user(at(13, 50)), ensure_ascii=False) + "\n")
            fh.write('{"type": "pad", "text": "' + "x" * 2_000_000 + '"}\n')
        assert os.path.getsize(path) > 2_000_000
        os.utime(path, (at(13, 4, 56).timestamp(), at(13, 4, 56).timestamp()))   # 창 안 mtime 은 그대로

        spy = ReadSpy()
        spy.install(tool)
        try:
            lines, got, truncated = tool.read_lines(path, reserved)
        finally:
            spy.uninstall(tool)
        assert truncated is True, "예약한 크기에서 멈추지 않았다"
        assert got <= reserved, (got, reserved)
        assert spy.tell and max(spy.tell) <= reserved, ("상한을 넘겨 읽었다", spy.tell, reserved)
        assert sum(len(x.encode()) for x in lines) <= reserved
        # 자란 부분(사용자 줄 · pad)은 파싱에도 안 들어간다
        rows = tool.parse_pi(lines, 0, END_EP)
        assert len(rows) == 6, len(rows)
        assert all(r[0] < at(13, 50).timestamp() for r in rows)

        # 줄바꿈이 없는 2MB 한 줄 — 잘린 조각은 줄로 쓰지 않는다
        one = os.path.join(f.root, "oneline.jsonl")
        with open(one, "wb") as fh:
            fh.write(b"x" * 2_000_000)
        spy = ReadSpy()
        spy.install(tool)
        try:
            lines, got, truncated = tool.read_lines(one, 52)
        finally:
            spy.uninstall(tool)
        assert lines == [] and got <= 52 and truncated is True, (lines, got, truncated)
        assert spy.tell and max(spy.tell) <= 52, ("한 줄에서도 상한을 넘겼다", spy.tell)

        # 장부도 실제로 읽은 바이트를 넘지 않는다
        d = f.js()
        assert d["sample"]["read_truncated"] == 0      # 이 실행은 이미 자란 파일을 예약했다
        assert d["sample"]["read_bytes"] <= 65536 + os.path.getsize(path), d["sample"]

        # 잘렸을 때 알림 1줄 — 읽기 함수만 잘림을 내도록 바꿔 끼워 본다
        real = tool.read_lines
        tool.read_lines = lambda p, cap: (real(p, cap)[0], cap, True)
        out = io.StringIO()
        old = sys.argv
        os.environ["HOME"] = f.home
        try:
            for argv, into in ((["--json", "--no-html", "--to", "%d" % END_EP], None),
                               (["--no-html", "--lang", "ko", "--to", "%d" % END_EP], out)):
                sys.argv = [TOOL] + argv
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    assert tool.main() == 0
                if into is None:
                    assert json.loads(buf.getvalue())["sample"]["read_truncated"] == 1
                else:
                    into.write(buf.getvalue())
        finally:
            sys.argv = old
            tool.read_lines = real
        assert "읽기 잘림: 세션 1개는 예약한 크기에서 멈춤" in out.getvalue(), out.getvalue()
    finally:
        f.cleanup()
