"""r2503 ft2 keeper — REJECT 승인 줄의 «자리 칸»(걸린 낱말 + 자리) · 카드 ①②③ + 변이 M1·M3.

판독은 그대로다(글자 포함 = 거절 · 덜 닫는 쪽). 더하는 것은 REJECT 사유 1줄의 자리뿐 — 사람이 그 자리를 보고 낱말을 빼서 다시 보낸다.
① 거절 낱말이 «우편» 에만 있으면 자리 = «우편 N째 줄» ② «원장 행» 에만 있으면 자리 = «원장 행 «…조각…»»(우편 자리로 적으면 Red)
③ 둘 다 있으면 원장 행 자리(고르는 차례 = 코드 검사 차례 그대로) · ④ 거절 낱말 0 = 지금 그대로 닫힌다(자리 칸이 정상 승인을 막지 않는다).
대역 = r2401 시험 세계(keeper_world_r1812 · 임시 리포·가짜 tmux·실 core/cli 갈래) 한 곳을 그대로 다시 쓴다(정의 중복 0).
"""
import importlib.util
import shutil
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FT2 = HERE.parent
_spec = importlib.util.spec_from_file_location("r2503_base", str(HERE / "test_keeper_close_seat_r2401.py"))
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)   # 세계·run·one·untouched = r2401 파일 한 곳(사본 정의 0)

N, SEQ, MAIL = B.N, B.SEQ, B.MAIL
QUIET = "- **%s** %%s #%s 수동 닫기 나노 1석(자율 ON A18) · 유휴" % (N, SEQ)          # 거절 낱말 0
ROW_BAD = "- **%s** %%s #%s 수동 닫기 나노 1석(자율 ON A18) · keeper 거절 낱말 오판 rc2" % (N, SEQ)
MAIL_BAD = "[수동 닫기 승인] %s\n%s 1석 정리 · 유휴\n목적 = 빈 자리 첫 나노 · DRIFT 거절이면 거절 줄 1줄" % (B.W, B.W)   # 거절 = 3째 줄
WORD = "거절 낱말 «거절»"


def test_case01_우편_자리(tmp_path, monkeypatch):
    """① 원장 행은 깨끗하고 우편 3째 줄에 «거절» → REJECT 승인 rc 2 · 사유에 «거절 낱말 «거절» · 자리 = 우편 3째 줄» · 손 0."""
    w = B.world(tmp_path, monkeypatch, row=QUIET, mail=MAIL_BAD)
    lines, rc = B.run(w)
    assert rc == 2, lines
    line = B.one(lines, "REJECT 승인")
    assert WORD + " · 자리 = 우편 3째 줄" in line, line
    B.untouched(w)


def test_case02_원장_행_자리(tmp_path, monkeypatch):
    """② 우편은 깨끗하고 원장 행에 «거절» → 사유에 «자리 = 원장 행 «…거절 낱말 오판 rc2»» · 우편 자리로 적으면 Red · 손 0."""
    w = B.world(tmp_path, monkeypatch, row=ROW_BAD, mail=MAIL)
    lines, rc = B.run(w)
    assert rc == 2, lines
    line = B.one(lines, "REJECT 승인")
    assert WORD + " · 자리 = 원장 행 «" in line, line
    assert "오판 rc2»" in line, line                      # 조각이 그 자리 글자를 보인다(눈으로 찾게)
    assert "우편" not in line, line                        # 원장 행 거절을 우편 자리로 적지 않는다
    B.untouched(w)


def test_case03_둘_다_있으면_원장_행_먼저(tmp_path, monkeypatch):
    """③ 원장 행·우편 둘 다 «거절» → 자리 = 원장 행(검사 차례 그대로 · 고르는 차례가 흔들리지 않는다) · rc 2 · 손 0."""
    w = B.world(tmp_path, monkeypatch, row=ROW_BAD, mail=MAIL_BAD)
    lines, rc = B.run(w)
    assert rc == 2, lines
    line = B.one(lines, "REJECT 승인")
    assert WORD + " · 자리 = 원장 행 «" in line and "우편" not in line, line
    B.untouched(w)


def test_case04_낱말_없으면_지금대로_닫힌다(tmp_path, monkeypatch):
    """④ 거절 낱말 0 → 자리 칸이 정상 승인을 막지 않는다(CLOSED-MANUAL rc 0 · kill 1 · 재개 기록 1)."""
    w = B.world(tmp_path, monkeypatch, row=QUIET, mail=MAIL)
    lines, rc = B.run(w)
    assert rc == 0 and "CLOSED-MANUAL" in B.one(lines, "CLOSED-MANUAL"), lines
    assert B.kills(w) == ["=" + B.S] and B.rec(w) is not None


MUTANTS = {
    # M1 자리 칸을 안 붙임 → ①② Red(사유에 자리가 없다 · 2개)
    "M1": ('"긍정 판독 · 거절 낱말 «%s» · 자리 = %s" % (w, where) if w else ""', '"긍정 판독 · 거절 낱말 «%s»" % w if w else ""', 2),
    # M3 원장 행 거절을 우편 자리로 적음 → ② Red(자리 = 우편 0째 줄 · ① 은 우편 자리라 그대로 통과 · 1개)
    "M3": ('            return w, "원장 행 «%s»" % row_piece(body, w)',
           '            return w, "우편 %d째 줄" % mail_line(mail, w)', 1),
}


def copy(tmp):
    """이 팩의 사본 1개(tests·__pycache__ 뺌) — 변이마다 새로 뜬다(r2490 과 같은 꼴)."""
    tree = Path(tmp) / "m" / "ft2"
    shutil.copytree(FT2, tree, ignore=shutil.ignore_patterns("tests", "__pycache__"))
    return tree


def run_case(name, tmp, mp, ft2=None):
    """그 변이에서 ①② 를 1회 돌린다 — 하나라도 Red 면 그 수만큼 센다.
    ft2 사본을 쓰는 길 = kw.World 의 ft2 칸(r2401 world 는 kw.World 를 그대로 부른다 · 기본값은 정의 시점에 묶여 있다)."""
    red, real = 0, B.kw.World
    for i, case in enumerate((test_case01_우편_자리, test_case02_원장_행_자리)):
        sub = tmp / ("%s-%d" % (name, i))
        sub.mkdir()
        if ft2 is not None:
            B.kw.World = lambda t, m, _f=ft2, **rest: real(t, m, ft2=_f, **rest)   # noqa: E731
        try:
            case(sub, mp)
        except AssertionError:
            red += 1
        finally:
            B.kw.World = real
    return red


@pytest.mark.parametrize("name", ["M1", "M3"])
def test_mutant(name, tmp_path, monkeypatch):
    """변이 사본 = Red · 원본 = PASS(사본이 초록이면 그 변이는 안 걸린 변이다)."""
    old, new, want = MUTANTS[name]
    tree = copy(tmp_path)
    path = tree / "adapters" / "pi" / "keeper_manual_close.py"
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1, (name, old[:60])
    path.write_text(text.replace(old, new), encoding="utf-8")
    assert run_case(name, tmp_path, monkeypatch, tree) == want, "%s — 사본 Red 수가 카드와 다르다" % name
    assert run_case(name + "-orig", tmp_path, monkeypatch) == 0
