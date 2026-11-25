"""r2490 ft2 공급자 막힘 → 대체 모델 → 작업 재개 — 사례·대역 한 곳(계약 K1~K9 · 반례 ① ~ ⑯). 시험 파일 셋이 나눠 쓴다.

대역 = r1812 세계(임시 git·가짜 tmux·가짜 ps·가짜 쪽지 · 주입 시계) + 가짜 계정 정지 판정기(ft-acct-pause.sh · rc 파일).
세션 jsonl = 이 파일이 쓴다(오류 칸·바깥 timestamp). ⑯ 만 «가짜 pi + new-session 을 실제로 돌리는 가짜 tmux» 로
실제 launch.py 를 돌린다(잔액 0 흉내 → 자동 전환 → 나노 재개 1턴). sleep 0 · 실 tmux·pi·판정기 0.
기준판(팩 origin/main · 표식·대체 없음) = ① ①b ② Red. 변이 M1~M13 = test_pi_keeper_model_block_mut_r2490.py · mut2.
"""
import datetime, importlib.util, json, os, shutil, subprocess, sys  # noqa: E401
from pathlib import Path

FT2 = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("r1812_world_for_r2490", str(FT2 / "tests" / "keeper_world_r1812.py"))
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)
W, M, T0 = "w1", 60, B.T0
SONNET, NANO = "claude-sonnet-5-5", "opengateway/deepseek/deepseek-v4.1-flash-ultrafast"
JUDGE = r"""#!/bin/sh
# r2490 가짜 계정 정지 판정기 — 부르는 꼴은 진짜와 같다(status --check <P> | status --check --agent <A>).
a="$3"
[ "$a" = "--agent" ] && a="pi"
rc=$(awk -v k="$a" '$1==k{print $2}' "$FAKE_JUDGE_SRC" 2>/dev/null | head -1)
[ -z "$rc" ] && rc=$(awk -v k="*" '$1=="*"{print $2}' "$FAKE_JUDGE_SRC" 2>/dev/null | head -1)
[ -z "$rc" ] && rc=0
case "$rc" in
  3) printf 'PAUSED %s until_hhmm=0000 round=x\n' "$a" ;;
  4) printf 'ERROR pause x\n' ;;
  *) printf 'OK pause=none\n' ;;
esac
exit "$rc"
"""
# ⑯ 가짜 pi — argv 의 --model 로 갈린다: deepseek 면 실사건 402 오류 턴 · 소넷이면 정상 assistant 턴.
FAKE_PI = r'''#!__PY__
import datetime, json, os, sys
a = sys.argv[1:]
model = a[a.index("--model") + 1] if "--model" in a else ""
now = float(os.environ["FAKE_PI_NOW"])   # 주입 시계(이 세계의 FT_NOW 는 ISO 글)
ts = datetime.datetime.fromtimestamp(now, datetime.timezone.utc).isoformat().replace("+00:00", "Z")
box = os.path.join(os.environ["FT2_PI_SESSIONS"], "--%s--" % os.getcwd().strip("/").replace("/", "-"))
os.makedirs(box, exist_ok=True)
msg = ({"role": "assistant", "stopReason": "error", "errorMessage": '402 {"type":"insufficient_quota","code":"insufficient_balance"}'}
       if "deepseek" in model else {"role": "assistant", "stopReason": "stop"})
log = os.path.join(box, "s.jsonl")
open(log, "w", encoding="utf-8").write('{"type":"session"}\n' + json.dumps({"type": "message", "timestamp": ts, "message": msg}) + "\n")
os.utime(log, (now, now))
'''
# ⑯ 가짜 tmux — r1812 대역 + new-session 이 실제로 pi argv 를 돌린다(그래야 «재개 1턴» 이 실측된다).
TMUX2 = r'''#!__PY__
import json, os, subprocess, sys
st, a = os.environ["FAKE_TMUX"], sys.argv[1:]
d = json.load(open(st)) if os.path.exists(st) else {"alive": [], "pane": {}}
open(st + ".log", "a").write(json.dumps(a) + "\n")
name = (a[a.index("-t") + 1].lstrip("=").rstrip(":") if "-t" in a else a[a.index("-s") + 1] if "-s" in a else "")
if a[0] == "new-session":
    env, i = dict(os.environ), 1
    while i < len(a) and a[i].startswith("-"):     # 실제 tmux 처럼 값 있는 옵션(-s·-c·-e)만 먹고 처음 비옵션에서 명령이 시작된다
        w = a[i]
        if w in ("-s", "-c", "-e") and i + 1 < len(a):
            if w == "-e":
                key, _, val = a[i + 1].partition("=")
                env[key] = val
            i += 2
            continue
        i += 1
    cmd = a[i:]
    d["alive"] = sorted(set(d["alive"] + [name]))
    d.setdefault("pane", {})[name] = "\u276f "
    d.setdefault("path", {})[name] = a[a.index("-c") + 1]
    json.dump(d, open(st, "w"))
    if cmd:
        subprocess.run(cmd, cwd=a[a.index("-c") + 1], env=env, capture_output=True, timeout=25)
    sys.exit(0)
if a[0] == "kill-session":
    d["alive"] = [x for x in d["alive"] if x != name]
    json.dump(d, open(st, "w"))
    sys.exit(0)
if a[0] == "list-sessions":
    sys.stdout.write("".join(x + "\n" for x in d["alive"]))
    sys.exit(0)
if a[0] == "capture-pane":
    sys.stdout.write(d.get("pane", {}).get(name, ""))
    sys.exit(0)
if a[0] == "show-environment":
    sys.exit(0 if name in d["alive"] else 1)
if a[0] == "has-session":
    if name in d["alive"]:
        sys.exit(0)
    sys.stderr.write("can't find session: %s\n" % name)
    sys.exit(1)
if a[0] == "display-message":
    if "#{session_id}" in a[-1]:
        sys.stdout.write("$1\t%d\n" % (int(os.environ.get("FT_NOW") or 0)))
        sys.exit(0)
    if "#{session_path}" in a[-1]:
        sys.stdout.write(d.get("path", {}).get(name, "") + "\n")
        sys.exit(0 if name in d["alive"] else 1)
    t = a[a.index("-t") + 1]
    sys.stdout.write("0\n" if "#{session_attached}" in a[-1] and t.endswith(":") else "\n")
    sys.exit(0 if name in d["alive"] else 1)
sys.exit(0 if name in d["alive"] else 1)
'''
BADT = '#!/bin/sh\n[ "$1" = "list-sessions" ] && exit 1\nexec "$FAKE_TMUX_BIN" "$@"\n'   # ⑪d 생존 판독 실패(list-sessions rc1)
# ⑪d — tmux 서버가 아직 없음: «no server running» 은 판독 실패가 아니라 «세션 0»(새 탐침을 열 수 있다)
NOSERVER = ('#!/bin/sh\nif [ "$1" = "list-sessions" ]; then echo "no server running on /tmp/tmux-501/default" >&2; exit 1; fi\n'
            'exec "$FAKE_TMUX_BIN" "$@"\n')


def _put(path, body):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(body if isinstance(body, str) else json.dumps(body), encoding="utf-8")


def _lines(path):
    return Path(str(path)).read_text(encoding="utf-8").splitlines() if Path(str(path)).exists() else []


def _exe(path, body):
    _put(path, body), Path(path).chmod(0o755)
    return str(path)


def world(tmp, mp, ft2=None):
    """r1812 세계 + 카드 루트 표 + 가짜 판정기(rc 는 judge 파일) + CLOSE-NEXT 열림 · ft2 = 변이 사본(없으면 이 팩)."""
    w = B.World(tmp, mp, ft2 or FT2)
    w.mp = mp
    _put(w.state / "directive-roots.tsv", "harness\t.\torigin/main\tdesign/*/indices\n")
    _exe(Path(w.close).parent / "ft-acct-pause.sh", JUDGE)
    # 세계 bin(가짜 tmux 가 있는 자리)을 PATH 앞에 둔다 — keeper 의 재배정이 부르는 launch 도 «tmux» 를 PATH 로 찾기 때문이다.
    # 격리(오빠 지시 · master #373730·#373774): 실 tmux 가 불릴 때도 전용 소켓(-L 과 같은 자리)만 보게 TMUX_TMPDIR 을 임시로 두고,
    # «tmux» 가 가짜로 풀리는지 여기서 단언한다 — 아니면 실 tmux 로 나가 운영 좌석을 만든다(그때는 시험이 즉시 Red).
    w.env["PATH"] = str(Path(w.close).parent) + os.pathsep + w.env["PATH"]
    w.env["TMUX_TMPDIR"] = str(tmp / "tmux-socket")
    Path(w.env["TMUX_TMPDIR"]).mkdir(parents=True, exist_ok=True)
    for _var in ("TMUX", "TMUX_PANE"):   # 좌석 안에서 실 tmux 가 불리면 $TMUX 소켓으로 직행한다(legacy r957 실측) — 세계에서는 끊는다
        w.env.pop(_var, None)
    assert "TMUX" not in w.env and "TMUX_PANE" not in w.env, "좌석 소켓이 세계 env 에 남아 있다"
    got = shutil.which("tmux", path=w.env["PATH"]) or ""
    assert got and Path(got).resolve() == Path(w.env["FT_TMUX"]).resolve(), "가짜 tmux 가 PATH 에 없다 — 실 tmux 로 나간다: %r" % got
    w.judge = tmp / "judge.txt"
    w.env["FAKE_JUDGE_SRC"] = str(w.judge)
    w.enable()
    return w


def verdict(w, verdicts):
    """가짜 판정기 rc — 열쇠 = provider 이름 또는 «pi»(게이트가 부르는 --agent pi 꼴) · «*» = 나머지."""
    _put(w.judge, "".join("%s %s\n" % (key, rc) for key, rc in verdicts.items()))


def _repo(path):
    """좌석 worktree 대역 = 진짜 git 리포 1개(HEAD 시각 판독이 «판정 불가» 로 새지 않게)."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "commit", "-q", "--allow-empty", "-m", "x"], check=True, capture_output=True, env=env)
    return str(path)


def _turn(w, tree, at, msg, reason="stop"):
    """세션 마지막 줄 1개 — 오류면 (stopReason error · errorMessage) · 정상이면 stop 낱말. at = 절대 epoch."""
    ts = datetime.datetime.fromtimestamp(at, datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    one = {"type": "message", "timestamp": ts,
           "message": dict({"role": "assistant", "stopReason": "error" if msg else reason}, **({"errorMessage": msg} if msg else {}))}
    path = Path(w.env["FT2_PI_SESSIONS"]) / ("--%s--" % tree.strip("/").replace("/", "-")) / "s.jsonl"
    _put(path, '{"type":"session"}\n' + json.dumps(one) + "\n")
    os.utime(path, (at, at))   # jsonl mtime = 그 턴 시각(«jsonl-active» 로 새지 않게)
    return path


def _blank(w, tree, at):
    """연 뒤 assistant 턴 0 — 세션 머리 줄만(⑪c)."""
    path = Path(w.env["FT2_PI_SESSIONS"]) / ("--%s--" % tree.strip("/").replace("/", "-")) / "s.jsonl"
    _put(path, '{"type":"session"}\n'), os.utime(path, (at, at))


def seat(w, work=W, msg=None, at=None, role="nano", live=True, tree=None):
    """일 1개 + 의도(role 칸 = 실제 launch 가 적는 값) + 세션 마지막 줄(정상 턴 | 오류 턴) · at = 오류가 «몇 초 전» 인가."""
    w.work(work, alive=live, turn=None, holder="biz-harness-nano-%s#0" % work)
    one = w.runtime() / "launch" / ("%s@a1.intent" % work)
    _put(one, dict(json.loads(one.read_text(encoding="utf-8")), role=role))
    tree = _repo(tree or str(w.tmp / "wt" / work))
    return _turn(w, tree, w.t - (60 if at is None else at), msg)


def card(w, work, live=True):
    """카드 1장 = submit·assign·deliver 만(의도는 «열기» 가 만든다)."""
    w.work(work, alive=live, turn=None, intent=False)


def opened(w, work, probe=False, turn=None, at=None, msg=None):
    """좌석이 열렸다 = 의도 1개(tmux 세션 살림 · 진짜 git worktree) + 세션 jsonl(오류 턴 | 정상 턴 | 빈 턴)."""
    tree, holder = _repo(str(w.tmp / "wt" / work)), "biz-harness-nano-%s#0" % work
    row = {"FT2_HOLDER": holder, "state": "opened", "worktree": tree, "role": "nano", "at": "2026-01-01T00:00:00"}
    _put(w.runtime() / "launch" / ("%s@a1.intent" % work), dict(row, **({"probe": True} if probe else {})))
    d = json.loads(w.tm.read_text(encoding="utf-8"))
    d["alive"] = sorted(set(d["alive"] + [holder]))
    d.setdefault("pane", {})[holder] = "✻ Brewed for 3s\n❯ "
    _put(w.tm, d)
    if turn == "blank":
        _blank(w, tree, w.t - (60 if at is None else at))
    elif msg or turn:
        _turn(w, tree, w.t - (60 if at is None else at), msg if msg else None)
    return holder, tree


def killed(w, holder):
    """그 좌석이 «내려갔다» = tmux 세션 없음(재배정이 옛 holder 를 내린 뒤 · ㉢)."""
    d = json.loads(w.tm.read_text(encoding="utf-8"))
    d["alive"] = [x for x in d["alive"] if x != holder]
    _put(w.tm, d)


def marker(w, provider="deepseek"):
    """표식 1개(없으면 빈 칸) — 없는 표식을 «읽기 실패» 가 아니라 «칸 없음» 으로 다룬다(사례는 늘 단언으로 끝난다)."""
    one = w.state / "model-block" / (provider + ".json")
    return json.loads(one.read_text(encoding="utf-8")) if one.exists() else {}


def launch(w, work=W, role="nano"):
    """실제 launch.py --dry-run 1회(쓰기 0) — 좌석이 열릴 argv·모델·의도 칸을 본다."""
    done = subprocess.run([sys.executable, str(w.ft2 / "adapters" / "pi" / "launch.py"), "--root", str(w.root), "--team", "harness",
                           "--work", work, "--role", role, "--dry-run"],
                          env=dict(w.env), capture_output=True, text=True, timeout=25)
    return done.returncode, json.loads(done.stdout or "{}")


def notes(w, head=""):
    return [x for x in _lines(str(w.mbox) + ".log") if x.startswith("send ") and head in x]


def gates(w, team="harness"):
    nx = B._mod(w.ft2 / "adapters" / "pi" / "keeper_next.py", "nx_%d" % id(w))
    k = w.keeper()
    k.cache["@round"] = {}
    return nx.gates(k, team), k.lines


def kinds(lines, head):
    return [x for x in lines if x.startswith(head)]


def _probe(w):
    """⑨~⑪d 입력 — 막힘 표식을 만들고 ⓐ ⓑ 를 둘 다 거짓으로 되돌려 탐침 단계까지 간다."""
    verdict(w, {"*": 0})
    seat(w, msg="402 insufficient_balance", at=180)
    w.round()
    w.t += 2 * 900                        # 오류 턴이 15분 창 밖으로 → ⓑ 거짓(ⓐ 도 0)
    w.round()
    assert marker(w).get("phase") == "probe", marker(w)


### 반례

def c1(w):   # ① 실사건 402 글(quota 낱말 있음) · 3분 전 → 표식 ⓑ · 다음 열기 소넷/medium · 쪽지 2통
    verdict(w, {"*": 0})
    seat(w, msg='402 {"type":"insufficient_quota","code":"insufficient_balance"}', at=180)
    lines = w.round()
    assert kinds(lines, "MODEL-BLOCK harness deepseek"), "\n".join(lines)
    assert marker(w).get("basis") == "ⓑ" and marker(w).get("phase") == "blocked", marker(w)
    assert len(notes(w, "[모델 대체")) == 2, notes(w)
    rc, out = launch(w)
    assert (rc, out.get("model"), out.get("effort")) == (0, SONNET, "medium"), out
    assert out["paths"]["notes"] == {"model": NANO, "model_fallback": SONNET}, out["paths"]["notes"]


def c1b(w):   # ①b «402: The API key is suspended for billing» 뿐(quota 낱말 0) · 3분 전 → ① 과 같음
    verdict(w, {"*": 0})
    seat(w, msg="402: The API key is suspended for billing", at=180)
    lines = w.round()
    assert kinds(lines, "MODEL-BLOCK harness deepseek") and marker(w).get("basis") == "ⓑ", (lines, marker(w))
    assert len(notes(w, "[모델 대체")) == 2 and launch(w)[1].get("model") == SONNET


def c2(w):   # ② 판정기 rc 3(deepseek) · 오류 턴 0 → 표식 ⓐ · 다음 카드 게이트 통과 · 대체 모델로 열림
    verdict(w, {"deepseek": 3, "pi": 3})
    _put(w.state / "ACCT_PAUSE", "{}")
    seat(w)
    assert not [x for x in w.round() if x.startswith("NEXT-HOLD")]   # 이 바퀴는 다음 카드 게이트까지 안 간다(게이트는 따로 부른다)
    assert marker(w).get("basis") == "ⓐ" and marker(w).get("phase") == "blocked", marker(w)
    assert len(notes(w, "[모델 대체")) == 2, notes(w)
    got, glines = gates(w)
    assert got is True, glines                       # 게이트 통과(막는 줄 0)
    assert launch(w)[1].get("model") == SONNET


def c3(w):   # ③ 막힘 없음 → 표식 0 · argv 모델 = 역할 기본값 · 의도 줄 글자 같음(빈 칸)
    verdict(w, {"*": 0})
    seat(w)
    lines = w.round()
    assert not kinds(lines, "MODEL-BLOCK") and not (w.state / "model-block").exists(), lines
    rc, out = launch(w)
    assert (rc, out.get("model"), out.get("effort")) == (0, NANO, "medium"), out
    assert out["paths"]["notes"] == {}


def c4(w):   # ④ 503 «temporarily unavailable» → 표식 0 · r1921 깨움 길 그대로(깨움·대체 0 · BLOCKED 아님)
    E = B._mod(w.ft2 / "adapters" / "pi" / "keeper_stall_error.py", "err_%d" % id(w))
    assert E.blocked("UNAVAILABLE", '{"errormessage": "503 temporarily unavailable"}') is False
    assert E.blocked("UNKNOWN", '{"errormessage": "503 temporarily unavailable"}') is False   # 새 낱말 0 = 막힘 아님
    verdict(w, {"*": 0})
    seat(w, msg="503 temporarily unavailable", at=121)
    lines = w.round()
    assert not kinds(lines, "MODEL-BLOCK") and not (w.state / "model-block").exists(), lines
    assert w.tmux("send-keys"), lines                # r1921 깨움 1회 = 그 길 그대로(대체 0)
    assert launch(w)[1].get("model") == NANO


def c5(w):   # ⑤ 402 지만 16분 전 · 판정기 rc 0 → 표식 0
    verdict(w, {"*": 0})
    seat(w, msg="402 insufficient_balance", at=16 * M)
    lines = w.round()
    assert not kinds(lines, "MODEL-BLOCK") and not (w.state / "model-block").exists(), lines


def c6(w):   # ⑥ 대체 표에 행 없음(표 대역) + 막힘 → 열기 0 · «판정 불가 대체 0» 1줄 · 쪽지는 K3 뿐
    verdict(w, {"*": 0})
    seat(w, msg="402 insufficient_balance", at=180)
    w.round()
    before = len(notes(w, "[모델 대체"))
    tables = w.tmp / "models"
    tables.mkdir()
    for one in (FT2 / "contracts" / "models").glob("*.tsv"):
        body = [x for x in one.read_text(encoding="utf-8").splitlines() if not x.startswith(NANO)]
        _put(tables / one.name, "\n".join(body) + "\n")
    w.env["FT2_MODELS_DIR"] = str(tables)
    rc, out = launch(w)
    assert (rc, out.get("result"), out.get("opened")) == (2, "복구 필요", None), out
    assert out["reason"].startswith("판정 불가 대체 0(") and "대체 표에 행 없음" in out["reason"], out["reason"]
    assert all(x not in str(out.get("paths", {})) for x in ("git", "tmux")), out
    assert len(notes(w, "[모델 대체")) == before, notes(w)


def c7(w):   # ⑦ 대체 모델 공급자(claude)에도 표식 → 열기 0 · «판정 불가 대체 0»(대체의 대체 0)
    verdict(w, {"*": 0})
    seat(w, msg="402 insufficient_balance", at=180)
    w.round()
    _put(w.state / "model-block" / "claude.json", {"provider": "claude", "phase": "blocked", "basis": "ⓑ", "last_error": 0})
    before = len(notes(w, "[모델 대체"))
    rc, out = launch(w)
    assert (rc, out.get("result")) == (2, "복구 필요"), out
    assert "대체 모델 공급자 표식(claude)" in out["reason"], out["reason"]
    assert len(notes(w, "[모델 대체")) == before


def c8(w):   # ⑧ 막힘이 3바퀴 이어짐 → 쪽지 합계 2통 그대로 · MODEL-BLOCK 1줄 그대로
    verdict(w, {"deepseek": 3, "pi": 3})   # 표식이 서는 근거 = 판정기(그래야 세 바퀴 내내 «막힘» 이 참이다)
    _put(w.state / "ACCT_PAUSE", "{}")
    seat(w)
    rounds = [w.round(), w.round(), w.round()]
    assert sum(len(kinds(x, "MODEL-BLOCK harness deepseek")) for x in rounds) == 1, rounds
    assert len(notes(w, "[모델 대체")) == 2, notes(w)


def c9(w):   # ⑨ ⓐ ⓑ 둘 다 거짓 → 탐침 단계 · 다음 열기 2석 중 1석만 원래 모델 · 1석은 대체
    _probe(w)
    card(w, "p3"), card(w, "p4")
    rc, first = launch(w, work="p3")
    assert (rc, first.get("model"), first["paths"]["notes"]) == (0, NANO, {"model": NANO, "probe": True}), first
    opened(w, "p3", probe=True)                      # 첫 탐침이 실제로 열렸다
    rc, second = launch(w, work="p4")
    assert (rc, second.get("model"), second["paths"]["notes"].get("model_fallback")) == (0, SONNET, SONNET), second


def c10(w):   # ⑩ 탐침 좌석에 정상 assistant 턴 → 표식 삭제 · MODEL-UNBLOCK 1줄 · 그다음 열기 = 원래 모델
    _probe(w)
    opened(w, "p2", probe=True, turn="stop", at=30)
    lines = w.round()
    assert not (w.state / "model-block" / "deepseek.json").exists(), marker(w)
    assert len(kinds(lines, "MODEL-UNBLOCK harness")) == 1, lines
    assert len(notes(w, "[모델 대체")) == 3, notes(w)          # K3 2통 + 해제 1통
    assert launch(w)[1].get("model") == NANO


def c11(w):   # ⑪ 탐침 좌석이 다시 402 → 표식 막힘 복귀 · 그다음 열기 = 대체 모델 · 쪽지 추가 0
    _probe(w)
    opened(w, "p2", probe=True, msg="402 insufficient_balance", at=30)
    before = len(notes(w, "[모델 대체"))
    w.round()
    assert marker(w).get("phase") == "blocked" and marker(w).get("probe") == "", marker(w)
    assert len(notes(w, "[모델 대체")) == before, notes(w)
    assert launch(w)[1].get("model") == SONNET


def c11b(w):   # ⑪b 탐침이 503 오류 턴 + 세션 없음(끝남 확인) → 탐침 단계 그대로 · probe 칸 빔 ·
    #             MODEL-PROBE-RETRY 1줄 · 다음 열기 2석 중 1석 새 탐침(원래 모델) · 1석 대체
    _probe(w)
    holder, _ = opened(w, "p2", probe=True, msg="503 temporarily unavailable", at=30)
    killed(w, holder)
    lines = w.round()
    assert marker(w).get("phase") == "probe" and marker(w).get("probe") == "", marker(w)
    assert len(kinds(lines, "MODEL-PROBE-RETRY")) == 1, lines
    assert len(notes(w, "[모델 대체")) == 2, notes(w)          # 쪽지 0
    card(w, "p3"), card(w, "p4")
    assert launch(w, work="p3")[1].get("model") == NANO        # 새 탐침
    opened(w, "p3", probe=True)
    assert launch(w, work="p4")[1].get("model") == SONNET      # 나머지는 대체


def c11c(w):   # ⑪c 살아 있는 탐침 · 연 뒤 16분 assistant 턴 0 → probe 칸 그대로 · 두 열기 다 대체 ·
    #               옛 holder 가 내려간 바퀴에 probe 칸 빔 + MODEL-PROBE-RETRY · 새 탐침 정상 턴 → 표식 삭제
    _probe(w)
    holder, _ = opened(w, "p2", probe=True, turn="blank", at=60)
    card(w, "p3"), card(w, "p4")
    w.t += 16 * M
    lines = w.round()
    assert marker(w).get("probe") == holder and not kinds(lines, "MODEL-PROBE-RETRY"), (marker(w), lines)
    assert (launch(w, work="p3")[1].get("model"), launch(w, work="p4")[1].get("model")) == (SONNET, SONNET)
    killed(w, holder)                                  # 멈춤 규칙이 그 좌석을 재배정해 옛 holder 가 내려갔다
    assert len(kinds(w.round(), "MODEL-PROBE-RETRY")) == 1 and marker(w).get("probe") == ""
    assert launch(w, work="p3")[1].get("model") == NANO   # 다시 연 1석 = 새 탐침
    opened(w, "p3", probe=True, turn="stop", at=10)
    lines = w.round()
    assert not (w.state / "model-block" / "deepseek.json").exists() and len(kinds(lines, "MODEL-UNBLOCK")) == 1


def c11d(w):   # ⑪d 살아 있는 탐침 · 503 오류 턴 → ⑪c 첫 절과 같음(probe 칸 그대로 · 새 탐침 0) ·
    #               생존 판독 rc≠0 → «판정 불가» 1줄 · probe 칸 그대로
    _probe(w)
    holder, _ = opened(w, "p2", probe=True, msg="503 temporarily unavailable", at=16 * M)
    card(w, "p3"), card(w, "p4")
    assert not kinds(w.round(), "MODEL-PROBE-RETRY") and marker(w).get("probe") == holder
    assert launch(w, work="p3")[1].get("model") == SONNET
    bad = _exe(w.tmp / "bin" / "tmux-bad", BADT)
    w.env["FAKE_TMUX_BIN"], keep = str(w.env["FT_TMUX"]), w.env["FT_TMUX"]
    w.env["FT_TMUX"] = bad
    lines = w.round()
    assert len(kinds(lines, "판정 불가 - deepseek 생존 판독 실패")) == 1, lines
    assert marker(w).get("probe") == holder
    rc, out = launch(w, work="p4")                       # 생존 판독 실패 = 새 탐침 0(원래 모델로 열지 않는다)
    assert (rc, out.get("model"), out["paths"]["notes"].get("probe")) == (0, SONNET, None), out
    w.env["FT_TMUX"] = keep
    assert launch(w, work="p4")[1].get("model") == SONNET   # 살아 있는 탐침이 있으니 그대로 대체 모델
    w.env["FT_TMUX"] = _exe(w.tmp / "bin" / "tmux-noserver", NOSERVER)
    rc, out = launch(w, work="p4")                          # «no server running» = 세션 0 → 새 탐침 1석(원래 모델)
    assert (rc, out.get("model"), out["paths"]["notes"].get("probe")) == (0, NANO, True), out
    w.env["FT_TMUX"] = keep


def c12(w):   # ⑫ 계정 정지 유효 · 나노 공급자(deepseek) 표식 0 · 딴 공급자 표식만 있음 → 게이트는 지금 그대로(막힘)
    verdict(w, {"deepseek": 0, "pi": 3})
    _put(w.state / "ACCT_PAUSE", "{}")
    _put(w.state / "model-block" / "claude.json", {"provider": "claude", "phase": "blocked", "basis": "ⓑ", "last_error": 0})
    seat(w)
    got, glines = gates(w)
    assert not got, glines   # k.log 가 None 을 낸다 = 다음 카드 0(기준판과 같은 줄)
    assert kinds(glines, "NEXT-HOLD harness ACCT_PAUSE 유효 rc 3 — 다음 카드 0"), glines


def c13(w):   # ⑬ 표식 있음 · BLOCKED 오류 턴 holder · 진척 0 이 2분 → 깨움 0 · 그 바퀴에 재배정 1회 ·
    #             새 좌석 모델 = 대체 · 같은 꼴에서 pane 에 일하는 표시 있음 → 재배정 0
    verdict(w, {"*": 0})
    seat(w, msg="402 insufficient_balance", at=2 * M)
    before = w.kinds("dispatch")
    lines = w.round()
    assert w.tmux("send-keys") == [], w.tmux("send-keys")
    assert w.kinds("dispatch") == before + 1, (before, w.kinds("dispatch"))
    assert kinds(lines, "HELD-STALL harness w1 새 배정"), lines   # 이 세계는 tmux new-session 대역이 없어 launch 뒤에서 멈춘다
    assert launch(w)[1].get("model") == SONNET
    busy = B.World(w.tmp / "busy", w.mp, w.ft2)                   # pane 에 일하는 표시 = 재배정 0
    busy.enable()
    busy.env["FT2_KEEPER_MBOX"] = str(w.mbox)
    busy.work("w1", alive=True, turn=None, holder="biz-harness-nano-w1#0", pane="✻ Working… (esc to interrupt)")
    _put(busy.runtime() / "launch" / "w1@a1.intent",
         dict(json.loads((busy.runtime() / "launch" / "w1@a1.intent").read_text(encoding="utf-8")), role="nano"))
    _turn(busy, _repo(str(busy.tmp / "wt" / "w1")), busy.t - 2 * M, "402 insufficient_balance")
    _put(busy.state / "model-block" / "deepseek.json", {"provider": "deepseek", "phase": "blocked", "basis": "ⓑ", "last_error": 0})
    more = busy.kinds("dispatch")
    busy.round()
    assert busy.kinds("dispatch") == more and busy.tmux("send-keys") == []


def c13b(w):   # ⑬b 표식 없음 · 오류 턴이 503 인 holder · 진척 0 이 2분 → 재배정 0(지금 멈춤 규칙 그대로)
    verdict(w, {"*": 0})
    seat(w, msg="503 temporarily unavailable", at=2 * M)
    before = w.kinds("dispatch")
    w.round()
    assert w.kinds("dispatch") == before and w.tmux("kill-session") == []


def c14(w):   # ⑭ 판정기 rc 4(손상) + 오류 턴 0 → «판정 불가» 1줄 · 표식 0 · 다음 카드는 지금 게이트 그대로
    verdict(w, {"*": 4})
    _put(w.state / "ACCT_PAUSE", "{}")
    seat(w)
    lines = w.round()
    assert not (w.state / "model-block").exists(), lines
    assert kinds(lines, "판정 불가 - deepseek 판정기 rc 4"), lines
    got, glines = gates(w)
    assert not got and kinds(glines, "NEXT-HOLD harness ACCT_PAUSE 판정 불가 rc 4"), glines


def c15(w):   # ⑮ 회귀 — 막힘 없음: keeper 줄·쪽지·모델·의도 칸이 기준판 그대로(새 줄 0)
    verdict(w, {"*": 0})
    seat(w)
    w.round()
    lines = w.round()
    assert not [x for x in lines if x.startswith(("MODEL-BLOCK", "MODEL-UNBLOCK", "MODEL-PROBE-RETRY", "SLOW-CALL", "판정 불가"))], lines
    assert notes(w, "[모델 대체") == [] and launch(w)[1].get("model") == NANO
    assert not (w.state / "model-block").exists()


def c16(w):   # ⑯ 재현(닫는 증거) — 잔액 0 흉내 → MODEL-BLOCK 1줄 → 재배정 → 새 좌석 소넷 → 정상 턴 1 · 사람 입력 0
    verdict(w, {"*": 0})
    b, t2 = Path(w.env["FT_TMUX"]).parent, w.tmp / "t2"
    _exe(b / "pi", FAKE_PI.replace("__PY__", sys.executable))                                      # 가짜 pi = deepseek 면 402 · 소넷이면 정상 턴
    _exe(t2 / "tmux", TMUX2.replace("__PY__", sys.executable))   # launch 는 PATH 의 «tmux» 를 부른다 · new-session 이 그 pi 를 돈다
    w.env.update(FT_TMUX=str(t2 / "tmux"), FAKE_PI_NOW=str(w.t), PATH=str(t2) + os.pathsep + str(b) + os.pathsep + os.environ["PATH"])
    card(w, W)
    done = subprocess.run([sys.executable, str(w.ft2 / "adapters" / "pi" / "launch.py"), "--root", str(w.root), "--team", "harness",
                           "--work", W, "--role", "nano", "--base", "origin/main"],
                          env=dict(w.env), capture_output=True, text=True, timeout=60)
    first = json.loads(done.stdout or "{}")
    assert done.returncode == 0 and first.get("opened") is True, (done.stdout, done.stderr[-400:])
    seat0 = first["holder"]
    assert not (w.state / "model-block").exists() or marker(w).get("basis"), "첫 좌석은 정상 모델로 열렸다"
    before = w.kinds("dispatch")
    lines = w.round()                                            # 표식 + 재배정(그 바퀴)
    assert len(kinds(lines, "MODEL-BLOCK harness deepseek")) == 1, "\n".join(lines)
    assert w.kinds("dispatch") == before + 1 and w.tmux("send-keys") == []
    news = [a for a in map(json.loads, _lines(str(w.tm) + ".log")) if a[0] == "new-session"]
    assert len(news) == 2, news                                  # 첫 좌석 + 재배정 좌석
    assert news[-1][news[-1].index("--model") + 1] == SONNET, news[-1]
    assert news[-1][news[-1].index("-s") + 1] != seat0, news[-1]   # 새 좌석(옛 holder 아님)
    got = w.tmux("kill-session")
    assert [a[a.index("-t") + 1].lstrip("=").rstrip(":") for a in got] == [seat0], got
    intents = sorted((w.runtime() / "launch").glob("%s@*.intent" % W), key=lambda one: one.stat().st_mtime)
    tree1 = json.loads(intents[-1].read_text(encoding="utf-8"))["worktree"]
    log = Path(w.env["FT2_PI_SESSIONS"]) / ("--%s--" % tree1.strip("/").replace("/", "-")) / "s.jsonl"
    turns = [json.loads(x) for x in _lines(log)]
    assert [x["message"]["stopReason"] for x in turns[1:]] == ["stop"], turns   # 소넷 좌석 첫 정상 턴 1
    assert len(notes(w, "[모델 대체")) == 2, notes(w)


### 사례 표 — 시험 파일 둘이 나눠 쓴다(한 파일 70초 상한)
CASES_A = {"①": c1, "①b": c1b, "②": c2, "③": c3, "④": c4, "⑤": c5, "⑥": c6, "⑦": c7, "⑧": c8, "⑨": c9}
CASES_B = {"⑩": c10, "⑪": c11, "⑪b": c11b, "⑪c": c11c, "⑪d": c11d, "⑫": c12,
           "⑬": c13, "⑬b": c13b, "⑭": c14, "⑮": c15, "⑯": c16}
CASES = dict(CASES_A, **CASES_B)
