"""r2563 card_stage 닫힌 장부 done 시각 시험 (카드 r2563 · 사전 DA APPROVE-DESIGN da-codex#57 #379664 · 판정문 DA-pre-r2563-codex57-20261124.md).

끝: r2520 이 끝난 work 의 칸을 닫힌 장부(runtime/closed.<N>.jsonl)로 옮긴 뒤에도 card_stage 가 그 work 의
done 시각을 읽어, 착지 끝난 옛 카드를 traceback 없이 완성 폴더로 옮긴다. 못 읽으면 «판정 불가» 1줄이다.
대역 = keeper_world_r1812(임시 bare biz 원격 · 임시 루트 · 임시 팀 원장 · 가짜 tmux) · 실 BIZ·실 원장·push 0 · sleep 0.
회수 = 코어 그대로(Journal._closed_rows · ClosedLedger.append · Journal.write_state) — 장부 파일을 손으로 쓰지 않는다.
  예외 = ⑤ 반례 ⑧(state·장부 공존)만 손으로 장부 1줄을 더한다: 실제 회수는 state 칸을 지우므로 공존 입력이 안 나온다.
사례 = ① 회수된 work 옮김 · ② 회수된 work 이미 완성 · ③④ 회수된 뒤 판 done 인식(K2·mark) · ⑤ state 우선(반례 ⑧) ·
  ⑥ done 행이 dict 아님 · ⑦ 빈 done 시각 · ⑧ 회수 전 work 글자 불변 · ⑨ done 없음 갈래 보존.
변이 = X1~X5 · 각각 다른 사례가 죽인다(사전 DA H1 = 중복 변이 0 · 독립 Red).
기준판 = 이 세트의 부모(BASE) → ① 은 Red(KeyError traceback) · ⑧ 은 글자 그대로 초록.
"""
import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest

FT2, BASE = Path(__file__).resolve().parents[1], "1ba96c2697d362b114ae611ef8dfbc7e66567d5e"
_S = importlib.util.spec_from_file_location("r2563_kw", str(FT2 / "tests" / "keeper_world_r1812.py"))
kw = importlib.util.module_from_spec(_S)
_S.loader.exec_module(kw)
TEAM, MAIN, OPS = kw.TEAM, "main", "ops/main-base"
CARD = "design/harness/indices/%s/%s-x.md"
HEAD = "# 인덱스: %s\n- 상태: 대기\n- 남은 범위: 없음\n"
AT, MID, LATER = kw.NOW, "2026-11-13T10:30:00", "2026-11-13T11:00:00"
CS = "adapters/pi/card_stage.py"
FIELDS = ("done", "released", "reassess_done", "owners_recovered", "deliveries", "generations")


def build(tmp, mp, ft2=None):
    """대역 세계 1개 — 원장 시계 = AT(FT_NOW) · 커밋 시각 고정(keeper_world 기본)."""
    return kw.World(tmp, mp, ft2 or FT2)


def bare(w, *a):
    return kw._git(w.tmp, "--git-dir", str(w.tmp / "biz.git"), *a)


def heads(w):
    return {b: bare(w, "rev-parse", b) for b in (MAIN, OPS)}


def names(w):
    return bare(w, "ls-tree", "-r", "--name-only", OPS).splitlines()


def when(mp, stamp):
    mp.setenv("GIT_AUTHOR_DATE", stamp), mp.setenv("GIT_COMMITTER_DATE", stamp)


def commit(w, files):
    """biz 대역(ops/main-base) 커밋 1개 — files = {경로: 본문 | None(삭제)} · 시각 = 지금 env 값(고정)."""
    seed = w.tmp / "seed-biz"
    for rel, body in files.items():
        path = seed / rel
        path.unlink() if body is None else kw._put(path, body)
    kw._git(seed, "add", "-A")
    kw._git(seed, "-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", "x")
    kw._git(seed, "push", "-q", "origin", OPS)
    return kw._git(seed, "rev-parse", "HEAD")


def node(w):
    """이 세계의 팀 원장(코어 그대로) — 회수·장부 확인용."""
    rec, journal = w.CLI._load("record"), w.CLI._load("journal")
    return journal.Journal(str(w.runtime()), rec=rec)


def recover(w):
    """r2520 회수 꼴 그대로 — 끝난 work 칸을 닫힌 장부로 옮기고 state checkpoint 에서 뺀다(_reclaim 과 같은 순서).

    checkpoint(base.proj·base.closed) → _closed_rows(장부 줄·뺀 state) → ClosedLedger.append(fsync) → write_state.
    """
    rec, journal = w.CLI._load("record"), w.CLI._load("journal")
    node_ = node(w)
    records, state = node_.records(), node_.state()
    upto = records[-1]["seq"] if records else 0
    base = dict(state.get("journal_base") or {})
    folded = rec.recover_state(state, records)
    receipts = dict(base.get("receipts") or {})
    receipts.update({r["command"]: r["attempt"] for r in records if r["kind"] == "accept"})
    work_state = dict(state, journal_base={"upto": upto, "count": (base.get("count") or 0) + len(records),
                                           "receipts": receipts,
                                           "proj": {name: folded.get(name) or {} for name in journal.PROJ_FIELDS}})
    rows, out, _size = node_._closed_rows(work_state, records, upto, 10 ** 6)
    assert rows, "회수할 끝난 work 가 없다"
    node_.ledger.index()
    node_.ledger.append(rows)
    node_.write_state(out)
    return {row["key"] for row in rows if row["k"] == "work"}


def done_keys(w):
    node_ = node(w)
    return sorted(node_.rec.recover_state(node_.state(), node_.records()).get("done") or {})


def run(w, capsys, work="r9", da=None, ft2=None):
    mod = kw._mod((ft2 or w.ft2) / "adapters" / "pi" / "card_stage.py", "cs2563_%d" % id(w))
    rc = mod.main(["--root", str(w.root), "--team", TEAM, "--work", work] + (["--da", da] if da else []))
    return rc, capsys.readouterr().out.strip()


def staged(w, capsys, frm="대기", work="r9"):
    """정상 옮김 = STAGED 1줄 · 그 가지에 D 옛 카드 + A 완성 카드 · 다른 가지 그대로."""
    before = heads(w)
    rc, out = run(w, capsys, work)
    assert rc == 0 and out.startswith("STAGED %s-x %s→완성 " % (work, frm)), out
    got = names(w)
    assert CARD % ("완성", work) in got and CARD % (frm, work) not in got, got
    assert heads(w)[MAIN] == before[MAIN]
    assert bare(w, "rev-parse", OPS + "~1") == before[OPS], out
    return rc, out


# ── 사례 ──────────────────────────────────────────────────────────────
def c1(tmp, mp, capsys, ft2=None):   # ① 회수된 work — done 시각을 닫힌 장부에서 읽어 옮긴다(traceback 0)
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="대기", refs=(OPS,))
    w.work("r9", done=True, intent=False, turn=None)
    assert recover(w) == {"r9"} and "r9" not in done_keys(w), done_keys(w)          # 회수 확인(state 칸 없음)
    assert node(w).ledger.work("r9") is not None, "장부에 없다"
    return staged(w, capsys)


def c2(tmp, mp, capsys, ft2=None):   # ② 회수된 work · 카드가 이미 완성 폴더 = NOOP rc 0(traceback 0)
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="완성", refs=(OPS,))
    w.work("r9", done=True, intent=False, turn=None)
    recover(w)
    before = heads(w)
    rc, out = run(w, capsys)
    assert (rc, out) == (0, "NOOP r9 이미 완성"), out
    assert heads(w) == before


def c3(tmp, mp, capsys, ft2=None):   # ③ 회수된 뒤 판 work 가 done = K2 «뒤 판 … 안 끝남» 아님 → 옮김(M3)
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="대기", refs=(OPS,))
    w.work("r9", intent=False, turn=None)                                  # r9 = 열린 work(회수 대상 아님)
    when(mp, LATER), mp.setenv("FT_NOW", LATER)
    w.work("r9-r2", done=True, intent=False, turn=None)                    # 뒤 판 dispatch + done(11:00)
    mp.setenv("FT_NOW", AT)
    assert recover(w) == {"r9-r2"} and "r9-r2" not in done_keys(w), done_keys(w)    # 뒤 판만 장부로
    w.CLI.run(["complete", "--work", "r9", "--attempt", "a1", "--root", str(w.root), "--team", TEAM])
    return staged(w, capsys)                                               # 장부의 뒤 판 done 을 못 보면 판정 불가


def c4(tmp, mp, capsys, ft2=None):   # ④ 원장 표식(mark)·done 표가 회수된 뒤 판을 «끝남» 으로 센다(기억 값 = 재시도 판단)
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="대기", refs=(OPS,))
    w.work("r9", intent=False, turn=None)
    when(mp, LATER), mp.setenv("FT_NOW", LATER)
    w.work("r9-r2", done=True, intent=False, turn=None)
    mp.setenv("FT_NOW", AT)
    recover(w)
    cs = kw._mod((ft2 or FT2) / "adapters" / "pi" / "card_stage.py", "cs2563_ledger_%d" % id(w))
    done, _sent, plus = cs.ledger(str(w.root), TEAM)
    assert done.get("r9-r2") == LATER and "r9-r2" in plus, (done, plus)
    assert cs.mark(str(w.root), TEAM, "r9").endswith("r9-r2:1"), cs.mark(str(w.root), TEAM, "r9")
    return None


def c5(tmp, mp, capsys, ft2=None):   # ⑤ 반례 ⑧ state·장부 공존 + 다른 시각 → state 시각이 이긴다(M4)
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="완성", refs=(OPS,))
    w.work("r9", done=True, intent=False, turn=None)                        # done = AT(10:00) · state
    node_ = node(w)
    node_.ledger.index()
    node_.ledger.append([{"k": "work", "key": "r9", "row": {"done": {"at": LATER, "attempt": "a1"}}}])   # 같은 work = 장부 11:00
    when(mp, MID), mp.setenv("FT_NOW", AT), commit(w, {CARD % ("완성", "r9"): None, CARD % ("대기", "r9"): HEAD % "r9" + "- 착지: %s\n" % w.land_sha()})
    before, body = heads(w), bare(w, "show", OPS + ":" + CARD % ("대기", "r9"))
    rc, out = run(w, capsys)                                              # 장부 시각(11:00)을 쓰면 K1 을 놓친다
    assert (rc, out) == (3, "판정 불가 옛 complete — 카드가 그 뒤에 들어옴"), out
    assert heads(w) == before and bare(w, "show", OPS + ":" + CARD % ("대기", "r9")) == body


def c6(tmp, mp, capsys, ft2=None):   # ⑥ done 행이 dict 아님 → «판정 불가» 1줄 · traceback 0 · 쓰기 0
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="대기", refs=(OPS,))
    w.work("r9", intent=False, turn=None)
    node_ = node(w)
    node_.ledger.index()
    node_.ledger.append([{"k": "work", "key": "r9", "row": {"done": "closed"}}])
    before = heads(w)
    rc, out = run(w, capsys)
    assert (rc, out) == (3, "판정 불가 done 시각 꼴 틀림 'closed'"), out
    assert heads(w) == before


def c7(tmp, mp, capsys, ft2=None):   # ⑦ 빈 done 시각 → «판정 불가» 1줄(빈 시각으로 옛 complete 가드를 끄지 않는다)
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="대기", refs=(OPS,))
    w.work("r9", intent=False, turn=None)
    node_ = node(w)
    node_.ledger.index()
    node_.ledger.append([{"k": "work", "key": "r9", "row": {"done": {"at": "", "attempt": "a1"}}}])
    before = heads(w)
    rc, out = run(w, capsys)
    assert (rc, out) == (3, "판정 불가 done 시각 꼴 틀림 ''"), out
    assert heads(w) == before


def c8(tmp, mp, capsys, ft2=None):   # ⑧ 회수 전 work — 출력·rc 글자 불변(기준판과 같은 글자)
    w = build(tmp, mp, ft2 or FT2)
    w.card("r9", w.land_sha(), stage="대기", refs=(OPS,))
    w.work("r9", done=True, intent=False, turn=None)
    return staged(w, capsys)


def c9(tmp, mp, capsys, ft2=None):   # ⑨ done 없음 갈래 보존 = REJECT rc 1 · 쓰기 0
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="대기", refs=(OPS,))
    w.work("r9", done=False, intent=False, turn=None)
    before = heads(w)
    rc, out = run(w, capsys)
    assert (rc, out) == (1, "REJECT done 없음 r9"), out
    assert heads(w) == before


CASES = {"①": c1, "②": c2, "③": c3, "④": c4, "⑤": c5, "⑥": c6, "⑦": c7, "⑧": c8, "⑨": c9}


@pytest.mark.parametrize("label", list(CASES))
def test_case(label, tmp_path, monkeypatch, capsys):
    CASES[label](tmp_path / "w", monkeypatch, capsys)


def base_tree(tmp):
    """기준판(이 세트의 부모) ft2 사본 — git archive BASE:feature-pack/fable-team/ft2."""
    out = tmp / "base" / "ft2"
    out.mkdir(parents=True)
    top = subprocess.run(["git", "-C", str(FT2), "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=25, check=True).stdout.strip()
    tar = subprocess.run(["git", "-C", top, "archive", BASE + ":feature-pack/fable-team/ft2"], capture_output=True, timeout=25, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(out)], input=tar, timeout=25, check=True)
    return out


def test_base_red(tmp_path, monkeypatch, capsys):
    """기준판은 회수된 work 의 done 시각을 못 읽어 traceback(KeyError) — 이 시험이 그 자리를 잰다."""
    (tmp_path / "w").mkdir()
    with pytest.raises(KeyError):
        CASES["①"](tmp_path / "w" / "base", monkeypatch, capsys, base_tree(tmp_path))


def test_base_same_text(tmp_path, monkeypatch, capsys):
    """회수 전 work 는 고친 판과 기준판이 같은 글자·같은 rc(옛 길 보존)."""
    (tmp_path / "w").mkdir()
    got = CASES["⑧"](tmp_path / "w" / "new", monkeypatch, capsys)
    old = CASES["⑧"](tmp_path / "w" / "base", monkeypatch, capsys, base_tree(tmp_path))
    def shape(row):   # 커밋 SHA 는 세계마다 다르다 — 글자 꼴(앞머리·낱말 수·rc)만 견준다
        rc, head, sha = row[0], *row[1].rsplit(" ", 1)
        assert len(sha) == 40 and set(sha) <= set("0123456789abcdef"), row
        return rc, head
    assert shape(got) == shape(old), (got, old)


MUTANTS = {
    "X1": ([(CS, "row = done[work] if work in done else closed_done(node).get(work)",
             "row = done[work] if work in done else None")], "①"),
    "X2": ([(CS, "    for name, row in closed_done(node).items():", "    for name, row in {}.items():")], "③"),
    "X3": ([(CS, "row = done[work] if work in done else closed_done(node).get(work)",
             "row = closed_done(node).get(work) or done.get(work)")], "⑤"),
    "X4": ([(CS, "return at if isinstance(at, str) and WHEN.match(at) else None",
             "return at if isinstance(at, str) else None")], "⑦"),
    "X5": ([(CS, 'at = row.get("at") if isinstance(row, dict) else None', 'at = (row or {}).get("at")')], "⑥"),
}


def mutant_tree(tmp, pairs):
    tree = tmp / "m" / "ft2"
    shutil.copytree(FT2, tree, ignore=shutil.ignore_patterns("tests", "__pycache__"))
    for rel, old, new in pairs:
        path = tree / rel
        text = path.read_text(encoding="utf-8")
        assert text.count(old) == 1, (rel, old)
        path.write_text(text.replace(old, new), encoding="utf-8")
    return tree


@pytest.mark.parametrize("name", list(MUTANTS))
def test_mutant(name, tmp_path, monkeypatch, capsys):
    """변이 = 사본에서만 · 그 사례가 깨진다 → 원본으로 같은 사례 1회 더 = 통과(반대 결과 대조)."""
    pairs, label = MUTANTS[name]
    (tmp_path / "w").mkdir()
    with pytest.raises((AssertionError, KeyError, TypeError, AttributeError)):
        CASES[label](tmp_path / "w" / "m", monkeypatch, capsys, mutant_tree(tmp_path, pairs))
    CASES[label](tmp_path / "w" / "orig", monkeypatch, capsys)
