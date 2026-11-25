"""r2441 card_stage 옛 complete 가드 시험 (카드 반례 ①~⑯ + DA-impl 58 H1 반례 ⑰⑱ · 변이 M1~M11 · 기준판 Red ① ②).
대역 = keeper_world_r1812(임시 bare biz 원격 main·ops/main-base · 임시 루트 · 임시 팀 원장 · 가짜 tmux) · 카드 = 합성 본문 · 실 BIZ 리포·실 원장·push 0 · sleep 0.
커밋 시각 = 환경 변수 고정(GIT_AUTHOR_DATE·GIT_COMMITTER_DATE) — WAS 09:00 < AT 10:00(원장 done) < LATER 11:00(뒤 판 dispatch) < NEXT 11:30(되돌림 커밋).
⑰⑱ = 커밋에 offset 이 붙은 꼴(+0000) — 로컬 시간대를 TZ=Asia/Seoul 로 고정하고 «같은 순간» 으로 읽는지 본다(DA-impl 58 H1).
판정 = «옛 complete» 사유 2개(K1 카드가 그 뒤에 들어옴 · K2 뒤 판 … 안 끝남) = 판정 불가 1줄 rc 3 · 커밋 0 · push 0. 정상 옮김은 지금과 같은 나무.
기준판 = 이 카드 앞 판(카드 BASE · 가드 0) → ① ② Red.
"""
import importlib.util
import os
import shutil
import subprocess
from pathlib import Path

import pytest

FT2, BASE = Path(__file__).resolve().parents[1], "cb2a12f196d88222d101027864e8100645acae67"   # BASE = 이 세트의 부모(가드 앞 판 = origin/main)
_S = importlib.util.spec_from_file_location("r2441_kw", str(FT2 / "tests" / "keeper_world_r1812.py"))
kw = importlib.util.module_from_spec(_S)
_S.loader.exec_module(kw)
TEAM, MAIN, OPS = kw.TEAM, "main", "ops/main-base"
CARD = "design/harness/indices/%s/%s-x.md"
HEAD = "# 인덱스: %s\n- 상태: 대기\n- 남은 범위: 없음\n"
AT, WAS, LATER, NEXT = kw.NOW, kw.WAS, "2026-11-13T11:00:00", "2026-11-13T11:30:00"
CS, KP = "adapters/pi/card_stage.py", "adapters/pi/keeper.py"


def when(mp, stamp):
    """커밋 시각 = 환경 변수(카드 반례 집합 «커밋 시각은 환경 변수로 고정»)."""
    mp.setenv("GIT_AUTHOR_DATE", stamp), mp.setenv("GIT_COMMITTER_DATE", stamp)


def build(tmp, mp, ft2=None):
    """대역 세계 1개 — 원장 시계 = AT(FT_NOW) · 커밋 시각 = WAS(고정)."""
    return kw.World(tmp, mp, ft2 or FT2)


def bare(w, *a):
    return kw._git(w.tmp, "--git-dir", str(w.tmp / "biz.git"), *a)


def heads(w):
    return {b: bare(w, "rev-parse", b) for b in (MAIN, OPS)}


def names(w):
    return bare(w, "ls-tree", "-r", "--name-only", OPS).splitlines()


def moved_card(w, frm, to, work="r9"):
    """카드 1장을 frm → to 폴더로 옮기는 커밋(D 옛 경로 + A 새 경로 · 본문 그대로)."""
    body = bare(w, "show", OPS + ":" + CARD % (frm, work))
    return commit(w, {CARD % (frm, work): None, CARD % (to, work): body})


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


def run(w, capsys, work="r9", da=None):
    mod = kw._mod(w.ft2 / "adapters" / "pi" / "card_stage.py", "cs2441_%d" % id(w))
    rc = mod.main(["--root", str(w.root), "--team", TEAM, "--work", work] + (["--da", da] if da else []))
    return rc, capsys.readouterr().out.strip()


def stale(w, capsys, why, work="r9", card=None):
    """옛 complete = 판정 불가 1줄 · 커밋 0 · push 0 · 카드 그대로."""
    path = card or CARD % ("대기", work)
    before, body = heads(w), bare(w, "show", OPS + ":" + path)
    rc, out = run(w, capsys, work)
    assert (rc, out) == (3, "판정 불가 옛 complete — " + why), out
    assert heads(w) == before and bare(w, "show", OPS + ":" + path) == body


def staged(w, capsys, frm="대기", work="r9"):
    """정상 옮김 = STAGED 1줄 · 그 가지에 D 대기 + A 완성 2줄 · 다른 가지 그대로."""
    before = heads(w)
    rc, out = run(w, capsys, work)
    assert rc == 0 and out.startswith("STAGED %s-x %s→완성 " % (work, frm)), out
    got = names(w)
    assert CARD % ("완성", work) in got and CARD % (frm, work) not in got, got
    assert heads(w)[MAIN] == before[MAIN]
    assert bare(w, "rev-parse", OPS + "~1") == before[OPS], out
    return out


def again(w, work, stamp, attempt="a2"):
    """⑩⑮ — 같은 work 의 새 dispatch + complete 1줄. 코어 CLI 는 «이미 완료 기록» 을 거절하므로 원장(덧쓰기 전용)에 직접 쓴다."""
    rec, journal = w.CLI._load("record"), w.CLI._load("journal")
    node, seq = journal.Journal(str(w.runtime()), rec=rec), node_seq(w)
    for kind, extra in (("dispatch", {"intent": {"attempt": attempt}}),
                        ("complete", {"marker": "", "after": attempt})):
        seq += 1
        node.append(rec.build(TEAM, seq, work, attempt, stamp, work, work, kind=kind, holder="h", gen=2, extra=extra))


def node_seq(w):
    rec, journal = w.CLI._load("record"), w.CLI._load("journal")
    return journal.Journal(str(w.runtime()), rec=rec).records()[-1]["seq"]


# ── 사례 ──────────────────────────────────────────────────────────────
def c1(tmp, mp, capsys, ft2=None):   # ① 첫 사건 꼴 — 뒤 판 dispatch 가 done 뒤 · 뒤 판 done 아님 → K2
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="대기", refs=(OPS,))
    w.work("r9", done=True, intent=False, turn=None)
    when(mp, LATER), mp.setenv("FT_NOW", LATER)
    w.work("r9-r2", intent=False, turn=None)
    stale(w, capsys, "뒤 판 r9-r2 안 끝남")


def c2(tmp, mp, capsys, ft2=None):   # ② 되돌림 꼴 — 완성 → 대기 되돌림 커밋이 done 뒤 → K1
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="완성", refs=(OPS,))
    w.work("r9", done=True, intent=False, turn=None)
    when(mp, NEXT)
    moved_card(w, "완성", "대기")
    stale(w, capsys, "카드가 그 뒤에 들어옴")


def c3(tmp, mp, capsys, ft2=None):   # ③ 정상 — 카드 생성 → complete → 착지 줄 → 대기 → 완성
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="대기", refs=(OPS,))
    w.work("r9", done=True, intent=False, turn=None)
    staged(w, capsys)


def c4(tmp, mp, capsys, ft2=None):   # ④ 정상(진행 폴더 꼴) — 대기 → 진행 이동 커밋 → complete → 진행 → 완성
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="대기", refs=(OPS,))
    moved_card(w, "대기", "진행")
    w.work("r9", done=True, intent=False, turn=None)
    staged(w, capsys, frm="진행")


def c5(tmp, mp, capsys, ft2=None):   # ⑤ 뒤 판 work 가 done → K2 안 걸림 → 옮김
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="대기", refs=(OPS,))
    w.work("r9", done=True, intent=False, turn=None)
    when(mp, LATER), mp.setenv("FT_NOW", LATER)
    w.work("r9-r2", done=True, intent=False, turn=None)
    mp.setenv("FT_NOW", AT)
    staged(w, capsys)


def c6(tmp, mp, capsys, ft2=None):   # ⑥ 뒤 판 dispatch 가 done 시각 «앞» → K2 안 걸림 → 옮김
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="대기", refs=(OPS,))
    mp.setenv("FT_NOW", "2026-11-13T09:30:00")
    w.work("r9-r2", intent=False, turn=None)
    mp.setenv("FT_NOW", AT)
    w.work("r9", done=True, intent=False, turn=None)
    staged(w, capsys)


def c7(tmp, mp, capsys, ft2=None):   # ⑦ 이름만 비슷한 work(«r9x» · 꼬리 앞 «-» 없음) → K2 안 걸림 → 옮김
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="대기", refs=(OPS,))
    w.work("r9", done=True, intent=False, turn=None)
    when(mp, LATER), mp.setenv("FT_NOW", LATER)
    w.work("r9x", intent=False, turn=None)
    mp.setenv("FT_NOW", AT)
    staged(w, capsys)


def c8(tmp, mp, capsys, ft2=None):   # ⑧ 들어온 커밋 조회 실패(가짜 git rc 128) → 판정 불가 1줄 · 커밋 0
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="대기", refs=(OPS,))
    w.work("r9", done=True, intent=False, turn=None)
    git = shutil.which("git")
    kw._put(tmp / "bin" / "git", '#!/bin/sh\ncase "$*" in *" log "*) exit 128;; esac\nexec "%s" "$@"\n' % git)
    (tmp / "bin" / "git").chmod(0o755), mp.setenv("PATH", "%s:%s" % (tmp / "bin", os.environ["PATH"]))
    before = heads(w)
    rc, out = run(w, capsys)
    assert (rc, out) == (3, "판정 불가 git log rc 128"), out
    assert heads(w) == before


def c9(tmp, mp, capsys, ft2=None):   # ⑨ done 뒤 카드 «내용만» 고친 커밋(세트 줄) → K1 안 걸림 → 옮김
    w = build(tmp, mp, ft2)
    sha = w.land_sha()
    w.card("r9", sha, stage="대기", refs=(OPS,))
    w.work("r9", done=True, intent=False, turn=None)
    when(mp, NEXT)
    commit(w, {CARD % ("대기", "r9"): HEAD % "r9" + "- 착지: %s\n- 세트: 시험 1개 rc=0\n" % sha})
    staged(w, capsys)


def c10(tmp, mp, capsys, ft2=None):   # ⑩ ② 뒤 같은 work 재dispatch + 새 complete(done > 되돌림) → K1 지남 → 옮김
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="완성", refs=(OPS,))
    w.work("r9", done=True, intent=False, turn=None)
    when(mp, NEXT)
    moved_card(w, "완성", "대기")
    again(w, "r9", "2026-11-13T11:40:00")
    staged(w, capsys)


def c11(tmp, mp, capsys, ft2=None):   # ⑪ keeper 바퀴 — 사유 뒤 다음 날 바퀴 · 지문·표식 같음 → 시도 0 · 카드 바뀌면 1회
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="대기", refs=(OPS,))
    w.work("r9", done=True, intent=False, turn=None)
    when(mp, LATER), mp.setenv("FT_NOW", LATER)
    w.work("r9-r2", intent=False, turn=None)
    mp.setenv("FT_NOW", AT)
    key = TEAM + "|r9"
    k1, lines = round_of(w)
    row = k1.state["staging"][key]
    assert len(row) > 2 and len(row[3]) == 2 and any("옛 complete" in x for x in lines), (row, lines)   # 지문 + 원장 표식
    got = row[3]
    w.t += 86400
    k2, lines = round_of(w)
    assert k2.state["staging"][key][3] == got and not any("r9 " in x and "옛 complete" in x for x in lines), lines   # 다음 날 = 시도 0
    when(mp, NEXT)
    commit(w, {CARD % ("대기", "r9"): HEAD % "r9" + "- 세트: 카드 고침\n"})   # 카드가 바뀜 = 다시 1회
    w.t += 86400
    k3, lines = round_of(w)
    assert any("r9 " in x and "옛 complete" in x for x in lines) and k3.state["staging"][key][3][0] != got[0], (k3.state.get("staging"), lines)


def c12(tmp, mp, capsys, ft2=None):   # ⑫ 짝 표로 고른 남의 카드도 고른 카드 경로로 K1(② 와 같은 판정)
    w = build(tmp, mp, ft2)
    when(mp, NEXT)
    other = CARD % ("대기", "other")
    commit(w, {other: HEAD % "other" + "- 착지(r9): %s\n" % w.land_sha()})
    kw._put(w.runtime() / "cards.tsv", "r9\t%s\n" % (CARD % ("대기", "other")))
    w.work("r9", done=True, intent=False, turn=None)
    stale(w, capsys, "카드가 그 뒤에 들어옴", card=other)


def c13(tmp, mp, capsys, ft2=None):   # ⑬ 원장 판독 실패(투영 결과 OK 아님) → 판정 불가 · 커밋 0(지금 글자 그대로)
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="대기", refs=(OPS,))
    w.work("r9", done=True, intent=False, turn=None)
    kw._put(w.runtime() / "tmp" / "state.json.tmp", "{}")
    before = heads(w)
    rc, out = run(w, capsys)
    assert (rc, out) == (3, "판정 불가 projection 복구 필요"), out
    assert heads(w) == before


def c14(tmp, mp, capsys, ft2=None):   # ⑭ 완료 기록 없는 --da 길 — stage 시각 빈 값 = K1·K2 검사 0 · 이동 + 원장 complete 1회
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="대기", refs=(OPS,))
    w.work("r9", done=False, intent=False, turn=None)
    when(mp, LATER), mp.setenv("FT_NOW", LATER)
    w.work("r9-r2", intent=False, turn=None)   # done 시각이 없으면 이 뒤 판도 K2 대상이 아니다
    mp.setenv("FT_NOW", AT)
    lib = w.root / ".fable-team" / "bin" / "ft-team-lib.sh"
    lib.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(str(kw.OLD / "bin" / "ft-team-lib.sh"), str(lib))
    verdict = tmp / "verdict.md"
    verdict.write_text("# DA 판정\n\n## §1 r9-x — 닫힘 (CLOSE)\n- 닫힘 — r9-x — main `%s`\n" % ("c0" * 20), encoding="utf-8")
    rc, out = run(w, capsys, da="%s#§1" % verdict)
    rows = out.splitlines()
    assert rc == 0 and rows[0].startswith("STAGED r9-x 대기→완성 ") and rows[1] == "원장 complete r9 a1", out
    assert w.kinds("complete") == 1 and CARD % ("완성", "r9") in names(w)


def c15(tmp, mp, capsys, ft2=None):   # ⑮ ② 사유가 장부에 있음 → 새 complete → 다음 날 바퀴 시도 1회 → 옮김(사전 DA H1)
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="완성", refs=(OPS,))
    w.work("r9", done=True, intent=False, turn=None)
    when(mp, NEXT)
    moved_card(w, "완성", "대기")
    key = TEAM + "|r9"
    k1, lines = round_of(w)
    assert k1.state["staging"][key][1] == 1 and any("옛 complete" in x for x in lines), lines
    again(w, "r9", "2026-11-13T11:40:00")
    w.t += 86400
    k2, lines = round_of(w)
    assert key not in k2.state.get("staging", {}) and moved(lines), lines


def c16(tmp, mp, capsys, ft2=None):   # ⑯ ① 사유가 장부에 있음 → 뒤 판 done → 다음 바퀴 시도 1회 → 옮김(사전 DA H1)
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="대기", refs=(OPS,))
    w.work("r9", done=True, intent=False, turn=None)
    when(mp, LATER), mp.setenv("FT_NOW", LATER)
    w.work("r9-r2", intent=False, turn=None)
    key = TEAM + "|r9"
    k1, lines = round_of(w)
    assert k1.state["staging"][key][1] == 1 and any("옛 complete" in x for x in lines), lines
    w.CLI.run(["complete", "--work", "r9-r2", "--attempt", "a1", "--root", str(w.root), "--team", TEAM])
    w.t += 86400
    k2, lines = round_of(w)
    assert key not in k2.state.get("staging", {}) and moved(lines), lines


def c17(tmp, mp, capsys, ft2=None):   # ⑰ 커밋 offset(+0000) — 같은 순간이 로컬 11:30 > done 10:00 → K1(DA-impl 58 H1)
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="완성", refs=(OPS,))
    w.work("r9", done=True, intent=False, turn=None)
    mp.setenv("TZ", "Asia/Seoul")                     # 이 시험의 로컬 시계 = 원장 done 시계와 같은 기준
    when(mp, "2026-11-13T02:30:00+0000")              # = 로컬 2026-11-13T11:30:00(정상 git offset 기록 · 손상 입력 아님)
    moved_card(w, "완성", "대기")
    stale(w, capsys, "카드가 그 뒤에 들어옴")


def c18(tmp, mp, capsys, ft2=None):   # ⑱ 커밋 offset(+0000) 이지만 로컬 09:30 < done 10:00 → K1 안 걸림 → 옮김(⑰ 의 반대쪽 대조)
    w = build(tmp, mp, ft2)
    w.card("r9", w.land_sha(), stage="완성", refs=(OPS,))
    w.work("r9", done=True, intent=False, turn=None)
    mp.setenv("TZ", "Asia/Seoul")
    when(mp, "2026-11-13T00:30:00+0000")              # = 로컬 2026-11-13T09:30:00
    moved_card(w, "완성", "대기")
    staged(w, capsys)


def moved(lines):
    return any(x.startswith("CARD-STAGE") and " r9 " in x and "대기→완성" in x for x in lines)


def round_of(w):
    k = w.keeper()
    return k, w.round(k)


CASES = {"①": c1, "②": c2, "③": c3, "④": c4, "⑤": c5, "⑥": c6, "⑦": c7, "⑧": c8,
         "⑨": c9, "⑩": c10, "⑪": c11, "⑫": c12, "⑬": c13, "⑭": c14, "⑮": c15, "⑯": c16,
         "⑰": c17, "⑱": c18}


@pytest.mark.parametrize("label", list(CASES))
def test_case(label, tmp_path, monkeypatch, capsys):
    CASES[label](tmp_path / "w", monkeypatch, capsys)


def base_tree(tmp):
    """기준판(가드 앞 판) ft2 사본 — git archive BASE:feature-pack/fable-team/ft2."""
    out = tmp / "base" / "ft2"
    out.mkdir(parents=True)
    top = subprocess.run(["git", "-C", str(FT2), "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=25, check=True).stdout.strip()
    tar = subprocess.run(["git", "-C", top, "archive", BASE + ":feature-pack/fable-team/ft2"], capture_output=True, timeout=25, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(out)], input=tar, timeout=25, check=True)
    return out


@pytest.mark.parametrize("label", ["①", "②"])
def test_base_red(label, tmp_path, monkeypatch, capsys):
    """기준판 = 가드 0 → ① ② 는 옛 complete 를 못 보고 옮긴다(이 시험의 ASSERT 가 깨진다)."""
    with pytest.raises(AssertionError):
        CASES[label](tmp_path / "w", monkeypatch, capsys, base_tree(tmp_path))


@pytest.mark.parametrize("label", ["③", "④"])
def test_base_green(label, tmp_path, monkeypatch, capsys):
    """기준판도 정상은 옮긴다 — 가드가 정상 옮김을 막지 않는다는 대조(같은 나무)."""
    CASES[label](tmp_path / "w", monkeypatch, capsys, base_tree(tmp_path))


MUTANTS = {
    "M1": ([(CS, "if when > at:", "if False:")], "②"),
    "M2": ([(CS, 'if (sent.get(name) or "") > at and not done.get(name):', "if False:")], "①"),
    "M3": ([(CS, " and not done.get(name):", ":")], "⑤"),
    "M4": ([(CS, 'if (sent.get(name) or "") > at and', "if (sent.get(name) or \"\") > \"\" and")], "⑥"),
    "M5": ([(CS, '    for name in (n for n in names if n != work and n.startswith(work + "-")):   # K2',
            '    for name in (n for n in names if n != work and n.startswith(work)):   # K2')], "⑦"),
    "M6": ([(CS, '"--diff-filter=AR", ', "")], "⑨"),
    "M7": ([(CS, '    when = run(biz, "log", "-1", "--diff-filter=AR", "--format=%cd", "--date=format-local:" + WHEN_FMT, pin, "--", old).strip()\n'
                 "    if not WHEN.match(when):", "    when = at   # 변이 = git 실패를 통과로 읽음\n    if False:")], "⑧"),
    "M8": ([(KP, '"진행 카드 ", STALE)', '"진행 카드 ")')], "⑪"),
    "M9": ([(CS, "    if not at:   # K3", "    if False:   # K3")], "⑭"),
    "M10": ([(KP, "return got + [self.cs.mark(self.root, team, work)]", "return got")], ("⑮", "⑯")),
    "M11": ([(CS, '"--date=format-local:"', '"--date=format:"')], "⑰"),   # DA-impl 58 H1 — 커밋 offset 을 버리면 UTC 커밋이 done 앞으로 읽힌다
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


@pytest.mark.parametrize("name,label", [(n, c) for n, (_p, cs) in MUTANTS.items() for c in ([cs] if isinstance(cs, str) else cs)])
def test_mutant(name, label, tmp_path, monkeypatch, capsys):
    """변이 = 사본에서만 · 그 사례가 깨진다 → 원본으로 같은 사례 1회 더 = 통과(반대 결과 대조)."""
    pairs, _labels = MUTANTS[name]
    (tmp_path / "w").mkdir()
    with pytest.raises(AssertionError):
        CASES[label](tmp_path / "w" / "m", monkeypatch, capsys, mutant_tree(tmp_path, pairs))
    CASES[label](tmp_path / "w" / "orig", monkeypatch, capsys)
