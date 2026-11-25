"""ft2 pi distill-gate r2524 시험 — recv 문턱 뒤 꼬리 예산 tail-line(반례 ①~⑬ · 변이 M1~M8 이 Red 로 잡히는 자리).
node 로 tailLine()·judge()·extension 핸들러만 부른다 · 픽스처 = tmp_path 뿐(임시 HOME · 실 명부·우편함·tmux 0 · FT_SEAT 로 좌석 · sleep 0)."""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

FT2 = Path(__file__).resolve().parents[1]
GATE = Path(os.environ.get("PI_GATE") or FT2 / "adapters" / "pi" / "distill-gate.ts")
NODE = shutil.which("node")
SEAT, CLAUDE = "biz-x-nano#0", "claude-opus-5-5"
BASE = "FT_DISTILL_WARN=330000\nFT_DISTILL_BLOCK=350000\nFT_DISTILL_RECV=280000\nFT_DISTILL_TAIL=12000\n"
T200 = "FT_DISTILL_TIER_200K_MATCH=haiku\nFT_DISTILL_RECV_200K=120000\nFT_DISTILL_WARN_200K=140000\nFT_DISTILL_BLOCK_200K=150000\n"
DRIVER = """
import fs from "node:fs"; const mod = await import(process.env.FT_GATE), req = JSON.parse(fs.readFileSync(0, "utf8"));
const err = [], orig = console.error; console.error = (...a) => err.push(a.map(String).join(" "));
let out;
if (req.op === "ext") { // extension 핸들러 그대로 — 턴 시작 주입 우선순위(⑩)를 본다
  const hs = {}; mod.default({ on: (n, f) => { (hs[n] = hs[n] || []).push(f); } });
  hs.session_start[0]({ reason: "startup" });
  out = req.cases.map((c) => {
    const ctx = { getContextUsage: () => (c.tokens == null ? undefined : { tokens: c.tokens }), model: { id: req.model }, cwd: req.cwd, sessionManager: { getEntries: () => [], getSessionId: () => c.id } };
    const r = hs.before_agent_start[0]({}, ctx) ?? {};
    return { content: r.message?.content ?? null, customType: r.message?.customType ?? null, state: (() => { try { return JSON.parse(fs.readFileSync(`${req.cwd}/.fable-team/state/pi-distill-tail/${process.env.FT_SEAT}.json`, "utf8")); } catch { return null; } })() };
  });
} else {
  out = req.cases.map((c) => c.op === "thr" ? mod.thresholds(req.env, req.cwd, c.model) : c.op === "judge" ? mod.judge({ ...c, cwd: req.cwd, env: req.env, seat: undefined }) : mod.tailLine({ ...c, cwd: req.cwd, env: req.env, seat: undefined }));
}
console.error = orig; process.stdout.write(JSON.stringify({ out, err }));"""

pytestmark = pytest.mark.skipif(NODE is None, reason="node 없음")


def build(tmp, text=BASE):
    root = tmp / "repo"
    (root / ".git").mkdir(parents=True, exist_ok=True)
    (root / ".fable-team").mkdir(exist_ok=True)
    (root / ".fable-team" / "thresholds.env").write_text(text, encoding="utf-8")
    return root


def run(root, cases, env=None, op="tail", model=CLAUDE, proc_env=None, gate=None):
    e = {"FT_SEAT": SEAT, "FT_DISTILL_SAMPLE": str(root.parent / "no-sample")}
    e.update(env or {})
    penv = {"PATH": os.environ["PATH"], "HOME": str(root.parent), "FT_GATE": (gate or GATE).resolve().as_uri()}
    penv.update(proc_env or {})
    proc = subprocess.run([NODE, "--no-warnings", "--input-type=module", "-e", DRIVER], capture_output=True, text=True, timeout=60, env=penv,
                          input=json.dumps({"op": op, "cwd": str(root), "env": e, "model": model, "cases": cases}))
    if proc.returncode != 0:
        pytest.fail(proc.stderr[-800:])
    return json.loads(proc.stdout)


def tail(k, sid="s1", model=CLAUDE):
    return {"tool": "turn", "tokens": k, "model": model, "session": {"id": sid}}


def state(root, seat=SEAT):
    return json.loads((root / ".fable-team" / "state" / "pi-distill-tail" / f"{seat}.json").read_text(encoding="utf-8"))


def test_1_under_budget_no_line_but_crossed_recorded(tmp_path):
    root = build(tmp_path)
    assert run(root, [tail(279000), tail(281000), tail(292000)])["out"] == [None, None, None]
    assert state(root) == {"id": "s1", "crossed": 281000, "announced": -1}


def test_2_same_bucket_twice_zero(tmp_path):
    root = build(tmp_path)
    r = run(root, [tail(281000), tail(294000), tail(295000)])["out"]
    assert r[0] is None and "recv 문턱 뒤 13k" in r[1] and r[2] is None
    assert state(root)["announced"] == 0


def test_3_next_6k_interval_once(tmp_path):
    root = build(tmp_path)
    r = run(root, [tail(281000), tail(300000)])["out"]
    assert r[0] is None and r[1].startswith("[ft2 distill-gate] recv 문턱 뒤 19k")
    assert state(root)["announced"] == 1


def test_4_reload_same_session_continues(tmp_path):
    root = build(tmp_path)
    run(root, [tail(281000), tail(294000)])
    assert run(root, [tail(294000)])["out"] == [None]  # ④ 같은 대화 재적재 = 같은 구간 두 번 0
    assert "19k" in run(root, [tail(300000)])["out"][0]


def test_5_successor_seat_own_file(tmp_path):
    root = build(tmp_path)
    assert run(root, [tail(281000)])["out"] == [None]
    assert run(root, [tail(294000)], env={"FT_SEAT": "biz-x-nano#1"})["out"] == [None]  # 후계 = 자기 파일 새로 적는다
    assert state(root)["crossed"] == 281000 and state(root, "biz-x-nano#1")["crossed"] == 294000


def test_12_new_conversation_discards_old_crossed(tmp_path):
    root = build(tmp_path)
    run(root, [tail(320000, "old"), tail(326000, "old")])
    assert state(root)["crossed"] == 320000
    assert run(root, [tail(281000, "new")])["out"] == [None]
    assert state(root) == {"id": "new", "crossed": 281000, "announced": -1}
    assert "13k" in run(root, [tail(294000, "new")])["out"][0]  # 332k 로 밀리지 않는다


def test_13_no_session_id_undecidable(tmp_path):
    root = build(tmp_path)
    res = run(root, [tail(294000, ""), tail(295000, "")])
    assert res["out"] == [None, None]
    assert sum("판정 불가 tail" in line for line in res["err"]) == 1
    assert not (root / ".fable-team" / "state" / "pi-distill-tail").exists()


def test_6_tail_key_unreadable_keeps_other_judgement(tmp_path):
    root = build(tmp_path, BASE.replace("FT_DISTILL_TAIL=12000\n", ""))
    bare = tmp_path / "gate"  # 어댑터 옆 샘플이 없는 사본 = TAIL 을 어디서도 못 읽는 자리
    bare.mkdir()
    shutil.copy(GATE, bare / "distill-gate.ts")
    res = run(root, [tail(294000), {"op": "judge", "tool": "bash", "command": "bash .fable-team/comm/mbox.sh recv " + SEAT, "tokens": 285000, "model": CLAUDE}], gate=bare / "distill-gate.ts")
    assert res["out"][0] is None and res["out"][1]["rule"] == "recv-gate"
    assert sum("판정 불가 tail" in line for line in res["err"]) == 1


def test_7_tail_zero_knob(tmp_path):
    root = build(tmp_path)
    assert run(root, [tail(281000), tail(400000)], env={"FT_DISTILL_TAIL": "0"})["out"] == [None, None]
    assert not (root / ".fable-team" / "state" / "pi-distill-tail").exists()


def test_8_tier_tail_key(tmp_path):
    root = build(tmp_path, BASE + T200 + "FT_DISTILL_TAIL_200K=5000\n")
    r = run(root, [tail(121000, model="claude-haiku-4-5"), tail(126000, model="claude-haiku-4-5")])["out"]
    assert r[0] is None and "recv 문턱 뒤 5k" in r[1]


def test_9_no_usage_turn_skipped(tmp_path):
    root = build(tmp_path)
    assert run(root, [{"tool": "turn", "tokens": None, "model": CLAUDE, "session": {"id": "s1"}}, tail(294000)])["out"][0] is None
    assert state(root)["crossed"] == 294000


def test_10_warn_line_wins_same_turn(tmp_path):
    root = build(tmp_path)
    res = run(root, [{"tokens": 281000, "id": "s1"}, {"tokens": 332000, "id": "s1"}, {"tokens": 333000, "id": "s1"}], op="ext",
              proc_env={"FT_SEAT": SEAT, "FT_DISTILL_SAMPLE": str(tmp_path / "no-sample")})
    assert res["out"][0]["content"] is None
    assert res["out"][1]["customType"] == "ft2-distill-gate" and "경고선" in res["out"][1]["content"]  # ⑩ warn-line 만
    assert res["out"][2]["customType"] == "ft2-distill-gate-tail"  # 억제한 꼬리는 다음 턴에 남는다


def test_10b_first_crossing_above_warn_recorded(tmp_path):
    root = build(tmp_path)  # DA#57 HOLD1 #376292 — 첫 관측이 warn 선 위여도 넘은 자리는 warn 반환 전에 적는다
    res = run(root, [{"tokens": 331000, "id": "s1"}, {"tokens": 343000, "id": "s1"}], op="ext",
              proc_env={"FT_SEAT": SEAT, "FT_DISTILL_SAMPLE": str(tmp_path / "no-sample")})
    assert res["out"][0]["customType"] == "ft2-distill-gate"  # ⑩ 첫 턴 = warn-line 만
    assert res["out"][0]["state"] == {"id": "s1", "crossed": 331000, "announced": -1}  # 331k 가 넘은 자리(343k 아님)
    assert res["out"][1]["customType"] == "ft2-distill-gate-tail"  # 331k + 12k = 343k → tail 1번
    assert res["out"][1]["state"]["announced"] == 0


def test_11_not_ft_seat_noop(tmp_path):
    root = build(tmp_path)
    env = {"FT_SEAT": "", "TMUX_PANE": ""}
    assert run(root, [tail(294000)], env=env)["out"] == [None]
    assert not (root / ".fable-team" / "state" / "pi-distill-tail").exists()
