"""r2503 낱말 목록 같음 — ft2 keeper(2.x 판독)와 1.x 보내는 쪽 판정기가 «같은» 거절 낱말·같은 머리를 쓴다(카드 변이 M7·①).

한쪽만 고치면 여기서 Red 다: 1.x 가 먼저 반송하는 낱말과 2.x 가 REJECT 하는 낱말이 갈라지면 승인 쪽지가 조용히 통과하거나 엉뚱하게 반송된다.
목록은 카드대로 5개 고정(손 0) — 늘리거나 줄이려면 두 파일과 이 시험을 함께 고친다. 사본 변이(1개 뺌)도 1회 돌려 이 시험이 그 변이를 잡는지 잰다.
"""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
FT2 = HERE.parent
JUDGE = FT2.parent / "legacy" / "1.x" / "harness" / "comm" / "mbox_close_approve_refuse.py"   # 팩 1.x 라이브 판(정본 = legacy 1.x 사본)
WANT = ("아니오", "거절", "보류", "반려", "철회")                                             # 카드 «거절 낱말 5개 목록은 손 0»


def mod(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def keeper():
    return mod(FT2 / "adapters" / "pi" / "keeper_manual_close.py", "r2503_keeper_words")


def test_낱말_목록과_머리가_같다():
    """2.x REFUSE == 1.x REFUSE == 카드 5개 · 2.x HEAD == 1.x HEAD(«[수동 닫기 승인]»)."""
    k, j = keeper(), mod(JUDGE, "r2503_judge_words")
    assert tuple(k.REFUSE) == WANT == tuple(j.REFUSE), (k.REFUSE, j.REFUSE)
    assert k.HEAD == j.HEAD == "[수동 닫기 승인]"


def test_변이_M7_낱말_하나_빼면_갈라진다(tmp_path):
    """M7 — 1.x 사본에서 «철회» 를 빼면 목록이 갈라진다(이 시험이 그 변이를 잡는다 = Red)."""
    text = JUDGE.read_text(encoding="utf-8")
    old, new = '"아니오", "거절", "보류", "반려", "철회"', '"아니오", "거절", "보류", "반려"'
    assert text.count(old) == 1, old
    path = tmp_path / "judge_M7.py"
    path.write_text(text.replace(old, new), encoding="utf-8")
    assert tuple(mod(path, "r2503_judge_m7").REFUSE) != tuple(keeper().REFUSE)


def test_판정기_한_줄_계약():
    """판정기 단위 계약 — 대상 아님·낱말 없음 = 통과, 셋째 줄 낱말 = 사유 1줄(«낱말» + «자리 = 우편 N째 줄»)."""
    j = mod(JUDGE, "r2503_judge_unit")
    head = "[수동 닫기 승인] biz-harness-nano-r2503-t#0"
    assert j.reason("%s\nr2503 1석 정리 · 유휴\n" % head) == ""
    assert j.reason("[진행] 거절 낱말이 있는 일반 쪽지\n") == ""            # 머리 밖 쪽지는 건드리지 않는다
    assert j.reason("%s\nr2503 1석 정리 · 유휴\n목적 = DRIFT 거절이면 거절 줄 1줄" % head) == (
        "수동 닫기 승인에 거절 낱말 «거절» · 자리 = 우편 3째 줄 — 낱말을 빼고 다시 보내라(keeper 가 승인으로 안 읽는다)")
