"""test_window.py — ctx-window 반례 표(가 ~ 머) 24칸.

임시 HOME 아래 지어낸 pi jsonl 만 쓴다. 실 세션 읽기 0 · 네트워크 0 · sleep 0.
칸 이름은 카드 (내부 문서) §반례 표 그대로다.
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

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.abspath(os.path.join(HERE, os.pardir))
TOOL = os.environ.get("CTX_WINDOW_TOOL") or os.path.join(PKG, "bin", "ctx-window")
BURN = os.path.join(PKG, "bin", "ctx-burn")
TIME_PY = os.path.join(PKG, "bin", "ctx-time")

END = datetime(2026, 11, 23, 16, 0, 0)          # 창 끝(고정) · 기본 창 = 13:00 ~ 16:00
END_EP = END.timestamp()


def at(h, m=0, s=0):
    """2026-11-23 hh:mm:ss — 창 안 시각."""
    return datetime(2026, 11, 23, h, m, s)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


# ---------------------------------------------------------------- 지어낸 pi 줄
def sinfo(t, name):
    return {"type": "session_info", "timestamp": iso(t), "name": name}


def user(t, text="hi"):
    return {"type": "message", "timestamp": iso(t),
            "message": {"role": "user", "content": [{"type": "text", "text": text}]}}


def custom(t, text="[발주 #1] 알림 본문"):
    """알림(custom_message) — 원본의 «초인종» 입력."""
    return {"type": "custom_message", "timestamp": iso(t), "content": text}


def asst(t, inp, calls=(), cr=0, cw=0, text=None, thinking=None, out=0):
    """usage 가 있는 assistant 한 줄 = 턴 1개 · 대화창 = input + cacheRead + cacheWrite."""
    m = {"role": "assistant", "content": [],
         "usage": {"input": inp, "cacheRead": cr, "cacheWrite": cw, "output": out,
                   "totalTokens": inp + cr + cw + out}}
    if text:
        m["content"].append({"type": "text", "text": text})
    if thinking:
        m["content"].append({"type": "thinking", "thinking": thinking})
    for cid, name, args in calls:
        m["content"].append({"type": "toolCall", "id": cid, "name": name, "arguments": args})
    return {"type": "message", "timestamp": iso(t), "message": m}


def result(t, cid, text="ok", name="bash"):
    return {"type": "message", "timestamp": iso(t),
            "message": {"role": "toolResult", "toolCallId": cid, "toolName": name,
                        "content": [{"type": "text", "text": text}]}}


class F:
    """임시 HOME 하나 + 그 안의 세션 폴더."""

    def __init__(self):
        self.root = tempfile.mkdtemp(prefix="ctx-window-test-")
        self.home = os.path.join(self.root, "home")
        os.makedirs(self.home)

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write(self, rel, lines, mtime=None):
        p = os.path.join(self.home, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            for line in lines:
                f.write((line if isinstance(line, str) else json.dumps(line, ensure_ascii=False)) + "\n")
        if mtime is not None:
            os.utime(p, (mtime, mtime))
        return p

    def pi(self, folder, fname, lines, mtime=None, name=None):
        if name:
            lines = [sinfo(at(13, 0), name)] + list(lines)
        return self._write(".pi/agent/sessions/%s/%s" % (folder, fname), lines, mtime)

    def codex(self, fname, lines):
        return self._write(".codex/sessions/2026/11/23/%s" % fname, lines, None)

    def claude(self, name, lines=()):
        return self._write(".claude/projects/-tmp-x/%s" % name, list(lines), None)

    def run(self, *args, rc=0, tool=TOOL, lang="ko"):
        env = dict(os.environ, HOME=self.home, PYTHONDONTWRITEBYTECODE="1")
        argv = [sys.executable, tool] + [str(a) for a in args]
        if lang:
            argv += ["--lang", lang]
        p = subprocess.run(argv, capture_output=True, text=True, env=env)
        assert p.returncode == rc, "rc=%d (기대 %d)\n[stdout]\n%s\n[stderr]\n%s" % (
            p.returncode, rc, p.stdout, p.stderr)
        return p

    def js(self, *args):
        p = self.run("--json", "--no-html", "--to", "%d" % END_EP, *args)
        return json.loads(p.stdout)

    def texts(self, *args):
        """터미널 + html + json 세 곳의 글을 한 덩어리로."""
        out = self.run("--to", "%d" % END_EP, "--out",
                       os.path.join(self.home, ".cache", "w"), *args).stdout
        p = os.path.join(self.home, ".cache", "w", "ctx-window.html")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                out += f.read()
        out += self.run("--json", "--no-html", "--to", "%d" % END_EP, *args).stdout
        return out

    def files(self):
        out = []
        for base, _dirs, names in os.walk(self.home):
            for n in names:
                out.append(os.path.join(base, n))
        return sorted(out)


def load_tool():
    """본체를 모듈로 읽는다 — 시험 파일이 부르는 본체와 같은 파일."""
    loader = importlib.machinery.SourceFileLoader("ctx_window_under_test", TOOL)
    spec = importlib.util.spec_from_loader("ctx_window_under_test", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


class ReadSpy:
    """본체가 여는 파일을 감싸 «실제로 읽은 위치»(tell)를 파일별로 잰다."""

    def __init__(self):
        self.reads = []
        self._open = open

    def install(self, mod):
        spy = self

        class Wrapped:
            def __init__(self, path, fh):
                self.path, self._fh = path, fh

            def __enter__(self):
                return self._fh

            def __exit__(self, *a):
                spy.reads.append((str(self.path), self._fh.tell()))
                self._fh.close()
                return False

            def __getattr__(self, name):
                return getattr(self._fh, name)

        def fake_open(path, mode="r", *a, **k):
            return Wrapped(path, spy._open(path, mode, *a, **k))

        mod.open = fake_open

    def uninstall(self, mod):
        mod.__dict__.pop("open", None)

    def max_tell(self, suffix=None):
        vals = [t for p, t in self.reads if suffix is None or p.endswith(suffix)]
        return max(vals) if vals else 0


def run_main(tool, f, argv):
    """main() 을 이 프로세스에서 돌린다(HOME 만 임시로 바꾼다)."""
    buf = io.StringIO()
    old_argv, old_home = sys.argv, os.environ.get("HOME")
    os.environ["HOME"] = f.home
    try:
        sys.argv = [TOOL] + list(argv)
        with contextlib.redirect_stdout(buf):
            rc = tool.main()
    finally:
        sys.argv = old_argv
        if old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = old_home
    return rc, buf.getvalue()


# ---------------------------------------------------------------- 공통 지어낸 세션
def bell_session(f, folder="--tmp-x--", fname="2026-11-23T13-00-00-000Z_a.jsonl",
                 name="biz-aifp-nano-x#0", bells=(2, 5, 8)):
    """부팅 보고 턴 1개 + 부팅 뒤 10턴(가운데 bells 위치 3턴이 알림 입력)."""
    lines = [sinfo(at(13, 0), name), user(at(13, 0, 1)),
             asst(at(13, 0, 2), 20000),
             asst(at(13, 0, 3), 20000, [("c0", "bash", {"command": "[부팅 보고] 소견"})])]
    for i in range(10):
        t = at(13, 1 + i)
        lines.append(custom(t) if i in bells else user(t))
        lines.append(asst(t, 10000))
    return f.pi(folder, fname, lines, at(13, 20).timestamp())


def bell_turn_session(f, commands, fname="2026-11-23T13-00-00-000Z_a.jsonl",
                      name="biz-aifp-nano-x#0"):
    """부팅 보고 턴 1개 + 알림 입력 1개 → 턴 1개(도구 호출은 넘긴 꼴 그대로)."""
    lines = [sinfo(at(13, 0), name),
             user(at(13, 0, 1), "[발주 #0] 부팅"),
             asst(at(13, 0, 2), 20000, [("c0", "bash", {"command": "[부팅 보고] 소견"})])]
    for i, calls in enumerate(commands):
        t = at(13, 1 + i)
        lines.append(user(t, "[발주 #1] 알림"))
        lines.append(asst(t, 10000, calls))
    return f.pi("--tmp-x--", fname, lines, at(13, 20).timestamp())


# ---------------------------------------------------------------- 가 ~ 머
def notice_line(a, b, path="/tmp/ft-tool-result/x.txt", lines=12, total=900000):
    """통지 줄 1개 — A · B 는 통지가 적는 머리 · 꼬리 바이트 수."""
    return "[결과 상한] 전문 %d바이트%s 중 머리 %d · 꼬리 %d 만 실음 · 전문 = %s" % (
        total, "" if lines is None else " · %d줄" % lines, a, b, path)


def notice(head="", tail="", path="/tmp/ft-tool-result/x.txt", lines=12, old=False, a=None, b=None):
    """W4c 통지 꼴 결과 글 — 머리 + 통지 줄 + 꼬리. A · B 는 실제 utf-8 바이트 수가 기본."""
    hb, tb = head.encode("utf-8"), tail.encode("utf-8")
    mid = notice_line(len(hb) if a is None else a, len(tb) if b is None else b, path,
                      None if old else lines)
    return hb.decode("utf-8") + "\n" + mid + "\n" + tb.decode("utf-8")


def test_ga_no_text_leak():
    """가 — 사용자·모델·생각·도구 결과·명령 줄 글은 세 출력 어디에도 안 나온다."""
    f = F()
    try:
        f.pi("--tmp-x--", "2026-11-23T13-00-00-000Z_a.jsonl",
             [sinfo(at(13, 0), "biz-aifp-nano-x#0"),
              user(at(13, 0, 1), "ZZUSER 알림 [발주 #1]"),
              asst(at(13, 0, 2), 20000, [("c1", "bash", {"command": "ZZCMD echo hi"})],
                   text="ZZMODEL", thinking="ZZTHINK"),
              result(at(13, 0, 3), "c1", "ZZOUT 결과 글"),
              asst(at(13, 0, 4), 21000)],
             at(13, 5).timestamp())
        text = f.texts()
        for word in ("ZZUSER", "ZZMODEL", "ZZTHINK", "ZZOUT", "ZZCMD"):
            assert word not in text, "%s 가 출력에 샜다" % word
    finally:
        f.cleanup()


def test_na_bell_share():
    """나 — 부팅 뒤 10턴 가운데 3턴이 알림 입력 → 몫 3/10 = 30%."""
    f = F()
    try:
        bell_session(f)
        d = f.js()
        w1 = d["totals"]["w1"]
        assert w1["booted_turns"] == 10, w1
        assert w1["bell_turns"] == 3, w1
        assert abs(w1["share"] - 0.3) < 1e-9, w1
        s = d["sessions"][0]
        assert s["turns"] == 12 and s["marked"] is True, s
    finally:
        f.cleanup()


def test_da_marker_after_40():
    """다 — `[발주 #` 가 사용자 글 41자째부터면 알림 턴으로 세지 않는다."""
    f = F()
    try:
        f.pi("--tmp-x--", "2026-11-23T13-00-00-000Z_a.jsonl",
             [sinfo(at(13, 0), "biz-aifp-nano-x#0"),
              user(at(13, 0, 1), "[발주 #0] 부팅"),
              asst(at(13, 0, 2), 20000, [("c0", "bash", {"command": "[부팅 보고] 소견"})]),
              user(at(13, 1), "a" * 40 + "[발주 #1] 늦은 표식"),
              asst(at(13, 1, 5), 10000),
              user(at(13, 2), "a" * 35 + "[발주 #1] 맞는 표식"),
              asst(at(13, 2, 5), 10000)],
             at(13, 5).timestamp())
        w1 = f.js()["totals"]["w1"]
        assert w1["bell_turns"] == 1, w1          # 40자 안에 든 것 하나만
        assert w1["booted_turns"] == 2, w1
    finally:
        f.cleanup()


def test_ra_boot_window():
    """라 — `[부팅 보고]` 호출이 6번째 턴 · 대화창 20k → 46k → W2 = 26k."""
    f = F()
    try:
        lines = [sinfo(at(13, 0), "biz-aifp-nano-x#0")]
        ctxs = [20000, 22000, 24000, 26000, 28000, 30000, 46000]
        calls = {1: [("c1", "bash", {"command": "ls"})],
                 3: [("c2", "bash", {"command": "ls"}), ("c3", "read", {"path": "/x"})],
                 5: [("c4", "bash", {"command": "[부팅 보고] 소견"})]}
        for i, c in enumerate(ctxs):
            lines.append(user(at(13, i, 1)))
            lines.append(asst(at(13, i, 5), c, calls.get(i, [])))
        f.pi("--tmp-x--", "2026-11-23T13-00-00-000Z_a.jsonl", lines, at(13, 10).timestamp())
        d = f.js()
        s, w2 = d["sessions"][0], d["totals"]["w2"]
        assert s["boot_end_turn"] == 6, s              # 부팅 보고 턴 다음 = 처음 «부팅 뒤» 턴
        assert s["boot_end_ctx"] - s["first_ctx"] == 26000, s
        assert s["boot_calls"] == 4, s                 # 부팅 끝까지의 도구 호출 수
        assert w2["max"] == 26000 and w2["median"] == 26000, w2
    finally:
        f.cleanup()


def test_ma_no_boot_report():
    """마 — `[부팅 보고]` 가 없는 30턴 세션 → 부팅 끝 = 0부터 20번째 턴."""
    f = F()
    try:
        lines = [sinfo(at(13, 0), "biz-aifp-nano-x#0")]
        ctxs = [20000 + 1000 * i for i in range(30)]
        for i, c in enumerate(ctxs):
            lines.append(user(at(13, i, 1)))
            lines.append(asst(at(13, i, 5), c, [("c%d" % i, "bash", {"command": "ls"})]))
        f.pi("--tmp-x--", "2026-11-23T13-00-00-000Z_a.jsonl", lines, at(13, 30).timestamp())
        s = f.js()["sessions"][0]
        assert s["boot_end_turn"] == 20, s
        assert s["boot_end_ctx"] - s["first_ctx"] == 20000, s      # turns[20] − turns[0]
        assert s["boot_calls"] == 21, s
    finally:
        f.cleanup()


def test_ba_overflow():
    """바 — 270k → 285k → 301k · 문턱 280k → 넘침 31k · 넘은 세션 1."""
    f = F()
    try:
        lines = [sinfo(at(13, 0), "biz-aifp-nano-x#0")]
        for i, c in enumerate([270000, 285000, 301000]):
            lines.append(user(at(13, i, 1)))
            lines.append(asst(at(13, i, 5), c))
        f.pi("--tmp-x--", "2026-11-23T13-00-00-000Z_a.jsonl", lines, at(13, 5).timestamp())
        d = f.js()
        s, w3 = d["sessions"][0], d["totals"]["w3"]
        assert s["cross_turn"] == 1 and s["overflow"] == 31000, s
        assert w3["crossed"] == 1 and w3["max"] == 31000, w3
    finally:
        f.cleanup()


def test_sa_no_cross():
    """사 — 문턱을 안 넘은 세션만 → «넘은 세션 0» · rc 0."""
    f = F()
    try:
        lines = [sinfo(at(13, 0), "biz-aifp-nano-x#0")]
        for i, c in enumerate([200000, 250000, 260000]):
            lines.append(user(at(13, i, 1)))
            lines.append(asst(at(13, i, 5), c))
        f.pi("--tmp-x--", "2026-11-23T13-00-00-000Z_a.jsonl", lines, at(13, 5).timestamp())
        w3 = f.js()["totals"]["w3"]
        assert w3["crossed"] == 0, w3
        out = f.run("--no-html", "--to", "%d" % END_EP).stdout
        assert "넘은 세션 0" in out, out
    finally:
        f.cleanup()


BODY = notice("h" * 2000, "t" * 2400)   # ① ~ ③ 을 다 지나는 진짜 절단 통지(가운데에 박힘)


def test_a_result_size():
    """아 — 도구 결과 3건 · 셋째가 W4c 에 맞는 절단 통지 + 되읽기 1 → 초과 1건 · 통지 1 · 비율 100%."""
    f = F()
    try:
        lines = [sinfo(at(13, 0), "biz-aifp-nano-x#0"),
                 user(at(13, 0, 1), "hi"),
                 asst(at(13, 0, 2), 20000, [("c1", "bash", {"command": "cat /tmp/ft-tool-result/a"})]),
                 result(at(13, 0, 3), "c1", "a" * 1000),
                 result(at(13, 0, 4), "c1", "b" * 2048),
                 result(at(13, 0, 5), "c1", BODY)]
        f.pi("--tmp-x--", "2026-11-23T13-00-00-000Z_a.jsonl", lines, at(13, 5).timestamp())
        w4 = f.js()["totals"]["w4"]
        assert w4["results"] == 3, w4
        assert w4["over"] == 1, w4
        assert w4["over_bytes"] == len(BODY.encode("utf-8")) - 2048, w4
        assert w4["cap_marks"] == 1, w4
        assert w4["reread"] == 1, w4
        out = f.run("--no-html", "--to", "%d" % END_EP).stdout
        assert "100%" in out, out                       # 되읽기 비율 = 1/1
    finally:
        f.cleanup()


def test_ja_bytes_not_chars():
    """자 — 한글 1,000자(3,000바이트) 결과 → 글자 수가 아니라 바이트로 센다."""
    f = F()
    try:
        lines = [sinfo(at(13, 0), "biz-aifp-nano-x#0"),
                 user(at(13, 0, 1), "hi"),
                 asst(at(13, 0, 2), 20000),
                 result(at(13, 0, 3), "c1", "가" * 1000)]
        f.pi("--tmp-x--", "2026-11-23T13-00-00-000Z_a.jsonl", lines, at(13, 5).timestamp())
        w4 = f.js()["totals"]["w4"]
        assert len("가" * 1000) == 1000 and w4["bytes"] == 3000, w4
        assert w4["over"] == 1 and w4["over_bytes"] == 3000 - 2048, w4
    finally:
        f.cleanup()


def test_cha_no_marker():
    """차 — 표식이 하나도 없는 pi 세션 → W1 · W2 는 «표식 없음» · W3 · W4 는 값."""
    f = F()
    try:
        lines = [sinfo(at(13, 0), "some-plain-pi-session"),
                 user(at(13, 0, 1), "그냥 대화"),
                 asst(at(13, 0, 2), 270000),
                 asst(at(13, 0, 3), 300000),
                 result(at(13, 0, 4), "c1", "x" * 4000)]
        f.pi("--tmp-x--", "2026-11-23T13-00-00-000Z_a.jsonl", lines, at(13, 5).timestamp())
        d = f.js()
        assert d["totals"]["marked_sessions"] == 0, d["totals"]
        assert d["totals"]["w1"]["sessions"] == 0, d["totals"]["w1"]
        assert d["totals"]["w3"]["crossed"] == 1, d["totals"]["w3"]
        assert d["totals"]["w4"]["over"] == 1, d["totals"]["w4"]
        out = f.run("--no-html", "--to", "%d" % END_EP).stdout
        assert "표식 없음" in out, out
    finally:
        f.cleanup()


def test_ka_other_runtimes():
    """카 — codex · claude 세션만 → «빠짐» 줄 · rc 0."""
    f = F()
    try:
        f.codex("rollout-2026-11-23T13-00-00.jsonl",
                [{"timestamp": iso(at(13, 0)), "type": "session_meta", "payload": {"cwd": "/p"}}])
        f.claude("s.jsonl", [{"type": "user", "timestamp": iso(at(13, 1))}])
        out = f.run("--no-html", "--to", "%d" % END_EP).stdout
        assert "빠짐: codex · claude" in out, out
        assert f.js()["sessions"] == []
    finally:
        f.cleanup()


def test_ta_max_mb():
    """타 — 세션 3개(각 2MB) · --max-mb 5 → 2개만 셈 · «표본 줄임» 줄."""
    f = F()
    try:
        pad = "p" * (2_000_000)
        for i in range(3):
            lines = [sinfo(at(13, 0), "biz-aifp-nano-x#%d" % i),
                     user(at(13, 0, 1), "hi"),
                     asst(at(13, 0, 2), 20000),
                     result(at(13, 0, 3), "c1", pad)]
            f.pi("--tmp-x--", "2026-11-23T13-0%d-00-000Z_a.jsonl" % i, lines, at(13, i + 1).timestamp())
        d = f.js("--max-mb", "5")
        assert len(d["sessions"]) == 2, len(d["sessions"])
        out = f.run("--no-html", "--max-mb", "5", "--to", "%d" % END_EP).stdout
        assert "표본 줄임" in out, out
    finally:
        f.cleanup()


def test_pa_bell_shapes():
    """파 — 알림 턴 3개: ① 순수 recv 1개 ② 순수 recv + 다른 명령 ③ 호출 0 → W1a 3 · W1b 1."""
    f = F()
    try:
        bell_turn_session(f, [
            [("c1", "bash", {"command": "bash mbox.sh recv seat#1"})],
            [("c2", "bash", {"command": "bash mbox.sh recv seat#1"}),
             ("c3", "bash", {"command": "pytest -q"})],
            [],
        ])
        w1 = f.js()["totals"]["w1"]
        assert w1["bell_turns"] == 3, w1
        assert w1["pure_recv_turns"] == 1, w1
    finally:
        f.cleanup()


def test_beo_semicolon():
    """버 — 알림 턴 · 호출 1개 = `bash mbox.sh recv seat; pytest -q` → W1a 1 · W1b 0."""
    f = F()
    try:
        bell_turn_session(f, [[("c1", "bash", {"command": "bash mbox.sh recv seat; pytest -q"})]])
        w1 = f.js()["totals"]["w1"]
        assert w1["bell_turns"] == 1, w1
        assert w1["pure_recv_turns"] == 0, w1
    finally:
        f.cleanup()


BAD = [
    "bash mbox.sh recv seat && pytest -q",
    "bash mbox.sh recv seat || pytest -q",
    "bash mbox.sh recv seat & pytest -q",
    "bash mbox.sh recv seat\npytest -q",
    "pytest -q\nbash mbox.sh recv seat",
    "echo hi; bash mbox.sh recv seat",
    "bash mbox.sh recv $(cat x)",
    "bash mbox.sh recv seat `id`",
    "bash mbox.sh recv seat > /tmp/o",
    "bash mbox.sh recv seat | tee /tmp/x",
    "bash mbox.sh send a b 'mbox.sh recv x'",
]
GOOD = [
    "cd /p && bash .fable-team/comm/mbox.sh recv 'seat#1' 2>&1 | tail -40",
    "bash /a/mbox.sh recv seat#1",
    'FT_MBOX_DIR="/a/b" bash /x/mbox.sh recv seat#1 --all 2>&1 | tail -60',
    "bash mbox.sh recv seat --plan | head -n 5",
]


def test_seo_not_pure():
    """서 — 순수 recv 가 아닌 11꼴 → W1a 11 · W1b 0."""
    f = F()
    try:
        bell_turn_session(f, [[("c%d" % i, "bash", {"command": c})] for i, c in enumerate(BAD)])
        w1 = f.js()["totals"]["w1"]
        assert w1["bell_turns"] == 11, w1
        assert w1["pure_recv_turns"] == 0, w1
    finally:
        f.cleanup()


def test_eo_pure():
    """어 — 순수 recv 4꼴(tail -40 · head -n 5 포함) → W1a 4 · W1b 4."""
    f = F()
    try:
        bell_turn_session(f, [[("c%d" % i, "bash", {"command": c})] for i, c in enumerate(GOOD)])
        w1 = f.js()["totals"]["w1"]
        assert w1["bell_turns"] == 4, w1
        assert w1["pure_recv_turns"] == 4, w1
    finally:
        f.cleanup()


def test_jeo_two_calls_and_400():
    """저 — 순수 recv + 다른 도구 호출 1개 / 401자째에 `; pytest` 인 긴 명령 → 둘 다 W1b 0."""
    f = F()
    try:
        long_cmd = "bash mbox.sh recv seat " + "a" * 400 + "; pytest -q"
        assert len(long_cmd) > 400
        bell_turn_session(f, [
            [("c1", "bash", {"command": "bash mbox.sh recv seat#1"}),
             ("c2", "read", {"path": "/x"})],
            [("c3", "bash", {"command": long_cmd})],
        ])
        w1 = f.js()["totals"]["w1"]
        assert w1["bell_turns"] == 2, w1
        assert w1["pure_recv_turns"] == 0, w1
    finally:
        f.cleanup()


def test_cheo_original_cannot_tell():
    """처 — 원본 `kindN["초인종"]` 과 W1a 는 같고(1) W1b 만 0 이다."""
    f = F()
    try:
        bell_turn_session(f, [[("c1", "bash", {"command": "bash mbox.sh recv seat; pytest -q"})]])
        w1 = f.js()["totals"]["w1"]
        assert w1["bell_turns"] == 1 and w1["pure_recv_turns"] == 0, w1
    finally:
        f.cleanup()


def test_ha_growth_tell():
    """하 — 고른 뒤 2MB 자란 세션: tell ≤ 예약 크기 · «읽기 잘림» · W3 에서 뺌."""
    f = F()
    try:
        lines = [sinfo(at(13, 0), "biz-aifp-nano-x#0")]
        for i, c in enumerate([270000, 285000, 301000]):
            lines.append(user(at(13, i, 1)))
            lines.append(asst(at(13, i, 5), c))
        path = f.pi("--tmp-x--", "2026-11-23T13-00-00-000Z_a.jsonl", lines, at(13, 5).timestamp())
        reserved = os.path.getsize(path)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(user(at(13, 50)), ensure_ascii=False) + "\n")
            fh.write('{"type": "pad", "text": "' + "x" * 2_000_000 + '"}\n')
        os.utime(path, (at(13, 5).timestamp(), at(13, 5).timestamp()))

        tool = load_tool()
        spy = ReadSpy()
        spy.install(tool.TIME)
        try:
            got_lines, got, truncated = tool.TIME.read_lines(path, reserved)
        finally:
            spy.uninstall(tool.TIME)
        assert truncated is True, "예약한 크기에서 멈추지 않았다"
        assert got <= reserved and spy.max_tell(path) <= reserved, (got, reserved, spy.reads)
        turns, _res, _marks = tool.parse_window_lines(got_lines, 0, END_EP)
        assert len(turns) == 3, len(turns)                    # 자란 줄은 어느 숫자에도 안 들어간다
        assert turns[-1]["ctx"] == 301000, turns[-1]

        # 잘림을 알리는 줄 + W3 에서 빼기 — 읽기 함수만 잘림을 내도록 바꿔 끼워 본다
        real = tool.TIME.read_lines
        tool.TIME.read_lines = lambda p, cap: (real(p, cap)[0], cap, True)
        try:
            rc, out = run_main(tool, f, ["--no-html", "--to", "%d" % END_EP, "--lang", "ko"])
        finally:
            tool.TIME.read_lines = real
        assert rc == 0, rc
        assert "읽기 잘림: 세션 1개(W3 에서 뺌)" in out, out
        d = f.js()
        assert d["sample"]["read_truncated"] == 0            # 이 실행은 이미 자란 파일을 예약했다
        assert d["totals"]["w3"]["crossed"] == 1, d["totals"]["w3"]
    finally:
        f.cleanup()


def test_geo_oneline():
    """거 — 줄바꿈 없는 2MB 한 줄이 붙은 세션 → tell ≤ 예약 크기 · 그 줄은 버림 · rc 0."""
    f = F()
    try:
        path = f.pi("--tmp-x--", "2026-11-23T13-00-00-000Z_a.jsonl",
                    [sinfo(at(13, 0), "biz-aifp-nano-x#0"),
                     user(at(13, 0, 1), "hi"),
                     asst(at(13, 0, 2), 20000)],
                    at(13, 5).timestamp())
        reserved = os.path.getsize(path)
        with open(path, "ab") as fh:
            fh.write(b"x" * 2_000_000)                      # 줄바꿈 없는 한 줄
        os.utime(path, (at(13, 5).timestamp(), at(13, 5).timestamp()))
        tool = load_tool()
        spy = ReadSpy()
        spy.install(tool.TIME)
        try:
            lines, got, truncated = tool.TIME.read_lines(path, reserved)
        finally:
            spy.uninstall(tool.TIME)
        assert truncated is True and got <= reserved, (got, reserved)
        assert spy.max_tell(path) <= reserved, spy.reads
        assert all(len(x) < 2_000_000 for x in lines), "자란 한 줄이 줄로 들어왔다"
        turns, _r, _m = tool.parse_window_lines(lines, 0, END_EP)
        assert len(turns) == 1, turns
        rc, _out = run_main(tool, f, ["--no-html", "--to", "%d" % END_EP])
        assert rc == 0, rc
    finally:
        f.cleanup()


def test_neo_name_budget():
    """너 — 1MB 세션 5개 · --seat 로 1개만 맞음 → 안 맞는 4개의 tell ≤ 65,536."""
    f = F()
    try:
        pad = "q" * 1_000_000
        paths = {}
        for i in range(5):
            name = "biz-aifp-arch-x#%d" % i if i else "biz-aifp-nano-y#0"
            paths[name] = f.pi("--tmp-x--", "2026-11-23T13-0%d-00-000Z_a.jsonl" % i,
                               [sinfo(at(13, 0), name), user(at(13, 0, 1), "hi"),
                                asst(at(13, 0, 2), 20000), result(at(13, 0, 3), "c1", pad)],
                               at(13, i + 1).timestamp())
        tool = load_tool()
        spy = ReadSpy()
        spy.install(tool.TIME)
        try:
            rc, _out = run_main(tool, f, ["--no-html", "--seat", "nano", "--to", "%d" % END_EP])
        finally:
            spy.uninstall(tool.TIME)
        assert rc == 0, rc
        for name, p in paths.items():
            if name.startswith("biz-aifp-nano"):
                assert spy.max_tell(p) > 65536, ("맞는 세션의 몸을 안 읽었다", spy.reads)
            else:
                assert spy.max_tell(p) <= 65536, ("안 맞는 세션의 몸을 읽었다", p, spy.reads)
    finally:
        f.cleanup()


def test_deo_big_result_skipped():
    """더 — 도구 결과 3MB 세션 · --max-mb 1 → 고르지 않음 · tell ≤ 65,536."""
    f = F()
    try:
        path = f.pi("--tmp-x--", "2026-11-23T13-00-00-000Z_a.jsonl",
                    [sinfo(at(13, 0), "biz-aifp-nano-x#0"), user(at(13, 0, 1), "hi"),
                     asst(at(13, 0, 2), 20000), result(at(13, 0, 3), "c1", "r" * 3_000_000)],
                    at(13, 5).timestamp())
        tool = load_tool()
        spy = ReadSpy()
        spy.install(tool.TIME)
        try:
            rc, out = run_main(tool, f, ["--no-html", "--max-mb", "1", "--to", "%d" % END_EP,
                                         "--lang", "ko"])
        finally:
            spy.uninstall(tool.TIME)
        assert rc == 0, rc
        assert "표본 줄임" in out, out
        assert spy.max_tell(path) <= 65536, ("몸을 읽었다", spy.reads)
    finally:
        f.cleanup()


def test_reo_writes():
    """러 — 한 번 돌린 뒤 bin/ 에 새 파일 0 · --no-html 이면 임시 HOME 에 새 파일 0."""
    f = F()
    try:
        bell_session(f)
        before = set(os.listdir(os.path.join(PKG, "bin")))
        f.run("--to", "%d" % END_EP, "--out", os.path.join(f.home, ".cache", "w"))
        after = set(os.listdir(os.path.join(PKG, "bin")))
        assert after == before, ("bin/ 에 새 파일이 생겼다", after - before)
        assert not os.path.exists(os.path.join(PKG, "bin", "__pycache__"))
        assert os.path.exists(os.path.join(f.home, ".cache", "w", "ctx-window.html"))

        seen = f.files()
        f.run("--no-html", "--to", "%d" % END_EP)
        assert f.files() == seen, ("--no-html 인데 파일이 생겼다", f.files())
    finally:
        f.cleanup()


def test_meo_static():
    """머 — 세션 파일을 여는 `open(` 0줄 · read_lines( 와 pick( 을 부른다(정적 검사)."""
    with open(TOOL, encoding="utf-8") as fh:
        src = fh.read()
    opens = [ln.strip() for ln in src.splitlines() if "open(" in ln and not ln.strip().startswith("#")]
    assert len(opens) == 1, ("open( 이 html 쓰기 하나가 아니다", opens)
    assert "html_path" in opens[0], opens
    assert "read_lines(" in src and "pick(" in src, "ctx-time 본체의 함수를 안 부른다"
    assert "dont_write_bytecode" in src, "__pycache__ 를 막는 줄이 없다"


def test_w6_split_and_html():
    """W6 — `--split` 앞·뒤 두 열 · html 1개 · `--json` 계약(ctx-window.v1)."""
    f = F()
    try:
        bell_session(f)                      # 턴 12개 전부 13:00 ~ 13:20
        split = "%d" % at(14, 0).timestamp()
        d = f.js("--split", split)
        assert d["schema"] == "ctx-window.v1", d["schema"]
        assert d["split"]["before"]["w1"]["booted_turns"] == 10, d["split"]["before"]["w1"]
        assert d["split"]["after"]["w1"]["booted_turns"] == 0, d["split"]["after"]["w1"]
        out = f.run("--split", split, "--to", "%d" % END_EP,
                    "--out", os.path.join(f.home, ".cache", "w")).stdout
        assert "→" in out, out
        html_path = os.path.join(f.home, ".cache", "w", "ctx-window.html")
        assert os.path.getsize(html_path) > 1000
        with open(html_path, encoding="utf-8") as fh:
            assert "ctx-window" in fh.read()
    finally:
        f.cleanup()


def test_keo_cut_notice():
    """커 — ① 새 꼴 ② 옛 꼴 ③ A·B 틀린 인용 ④ 줄 가운데 인용 ⑤ 머리 200자 글자만 → 통지 2건."""
    f = F()
    try:
        quote = notice_line(5, 5, path="/x", lines=12)                 # ③ 이 인용하는 글자
        lines = [sinfo(at(13, 0), "biz-aifp-nano-x#0"), user(at(13, 0, 1), "hi"),
                 asst(at(13, 0, 2), 20000),
                 result(at(13, 0, 3), "c1", notice("가" * 30, "나" * 20)),            # ①
                 result(at(13, 0, 4), "c1", notice("a" * 40, "b" * 10, old=True)),   # ②
                 result(at(13, 0, 5), "c1", "x" * 100 + "\n" + quote + "\n" + "y" * 100),  # ③
                 result(at(13, 0, 6), "c1", "m" * 10 + quote + "\n" + "n" * 10),     # ④
                 result(at(13, 0, 7), "c1", "[결과 상한] 글자만 있는 결과 " + "z" * 300)]  # ⑤
        f.pi("--tmp-x--", "2026-11-23T13-00-00-000Z_a.jsonl", lines, at(13, 5).timestamp())
        w4 = f.js()["totals"]["w4"]
        assert w4["results"] == 5, w4
        assert w4["cap_marks"] == 2, w4          # ① · ② 만
    finally:
        f.cleanup()


def test_teo_byte_not_char():
    """터 — 한글 머리글 뒤에 박힌 통지 → A 가 바이트 수라야 1건(글자 수로 견디면 0 = 변이 FAIL)."""
    f = F()
    try:
        body = notice("가나다", "라마바")        # 머리 9바이트 · 꼬리 9바이트(글자로는 3 · 3)
        assert len("가나다".encode()) == 9 and len("가나다") == 3
        lines = [sinfo(at(13, 0), "biz-aifp-nano-x#0"), user(at(13, 0, 1), "hi"),
                 asst(at(13, 0, 2), 20000), result(at(13, 0, 3), "c1", body)]
        f.pi("--tmp-x--", "2026-11-23T13-00-00-000Z_a.jsonl", lines, at(13, 5).timestamp())
        w4 = f.js()["totals"]["w4"]
        assert w4["cap_marks"] == 1, w4
    finally:
        f.cleanup()


def test_peo_notice_no_leak():
    """퍼 — 통지 줄 경로의 ZZPATH · 머리글 ZZHEAD 가 세 출력 어디에도 0번 · 건수 1."""
    f = F()
    try:
        body = notice("ZZHEAD" + "가" * 30, "꼬리", path="/tmp/ZZPATH/ft-tool-result/x.txt")
        lines = [sinfo(at(13, 0), "biz-aifp-nano-x#0"), user(at(13, 0, 1), "hi"),
                 asst(at(13, 0, 2), 20000), result(at(13, 0, 3), "c1", body)]
        f.pi("--tmp-x--", "2026-11-23T13-00-00-000Z_a.jsonl", lines, at(13, 5).timestamp())
        text = f.texts()
        for word in ("ZZPATH", "ZZHEAD"):
            assert word not in text, "%s 가 출력에 샜다" % word
        assert f.js()["totals"]["w4"]["cap_marks"] == 1
    finally:
        f.cleanup()


def win_session(f, rows, mtime, name="biz-aifp-nano-x#0"):
    """행 시각을 손으로 정한 세션 — 창 자르기를 보려고 mtime 과 행 시각을 떼어 놓는다."""
    return f.pi("--tmp-x--", "2026-11-23T15-00-00-000Z_a.jsonl", [sinfo(at(11, 0), name)] + rows, mtime)


def test_window_cut_rows():
    """W5 (DA HOLD 1/3 반례) — mtime 15시 세션에서 창 13~16시 → 12시 행은 빠진다."""
    f = F()
    try:
        win_session(f, [
            asst(at(12, 0), 100), result(at(12, 0, 5), "c1", "x" * 5000),      # 창 밖(12시)
            asst(at(14, 0), 200), result(at(14, 0, 5), "c2", "yy"),            # 창 안(14시)
        ], at(15, 0).timestamp())
        d = f.js()                                     # --to 16시 · 기본 3시간 = 13 ~ 16시
        s = d["sessions"][0]
        assert s["turns"] == 1, s
        assert s["w4"]["results"] == 1, s["w4"]
        assert s["w4"]["bytes"] == 2 and s["w4"]["over"] == 0, s["w4"]
    finally:
        f.cleanup()


def test_window_edges():
    """W5 경계 — from 과 같은 시각은 넣고 to 와 같은 시각은 뺀다 · 시각 없는 행은 뺀다."""
    f = F()
    try:
        win_session(f, [
            {"type": "message", "message": {"role": "assistant",                 # timestamp 없음
             "usage": {"input": 999999, "cacheRead": 0, "cacheWrite": 0, "output": 0}}},
            asst(at(13, 0), 100), result(at(13, 0, 1), "c1", "a" * 10),          # from 과 같은 시각 = 넣음
            asst(at(16, 0), 200), result(at(16, 0, 1), "c2", "b" * 5000),        # to 와 같은 시각 = 뺀다
            asst(at(15, 59, 59), 300), result(at(15, 59, 59), "c3", "c" * 7),    # 창 끝 1초 전 = 넣음
        ], at(15, 0).timestamp())
        s = f.js()["sessions"][0]
        assert s["turns"] == 2, s                       # 13:00 · 15:59:59 (16:00 · 시각 없음은 빠짐)
        assert s["w4"]["results"] == 2 and s["w4"]["bytes"] == 17, s["w4"]
        assert s["final_ctx"] == 300, s                 # 16시 턴(200)이 섞이지 않았다
    finally:
        f.cleanup()


def test_w1_en_order():
    """영어 W1 줄 — 알림 턴 수가 앞, 부팅 뒤 턴 수가 뒤에 찍힌다(둘을 바꿔 찍던 결함)."""
    f = F()
    try:
        bell_session(f)                                   # 알림 턴 3 · 부팅 뒤 10턴
        out = f.run("--no-html", "--to", "%d" % END_EP, lang="en").stdout
        line = [x for x in out.splitlines() if x.startswith("W1")][0]
        part = line.split("(", 1)[1]
        assert part.startswith("3 bell turns of 10 after boot"), line
        assert line.startswith("W1 bell-turn share:"), line
        ko = f.run("--no-html", "--to", "%d" % END_EP).stdout      # 한글 줄은 그대로
        assert "부팅 뒤 10턴 가운데 알림 턴 3" in ko, ko
    finally:
        f.cleanup()
