"""r2518 변이 M1~M6 — 사본 ft2 에서만 · 변이마다 원본으로 같은 사례 1회 더(반대 결과 대조).
자매 = test_keeper_runtime_reclaim_r2518.py(반례 ①~⑧ · 70초 나눔).

M1 keeper 가 reclaim 을 안 부름 → ④ Red · M2 닫힘 판정에서 complete 를 끝 줄로 안 셈 → ① Red ·
M3 complete 뒤 start 도 닫힘으로 봄 → ② Red · M4 회수 실패에도 ops.jsonl 비움 → ⑤ Red ·
M5 막힘을 바퀴마다 올림 → ⑥ Red · M6 거절 글에서 총량 뺌 → ⑦ Red.
"""
import importlib.util
import shutil
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("r2518_cases", str(Path(__file__).with_name("test_keeper_runtime_reclaim_r2518.py")))
T = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T)
FT2 = Path(T.FT2)
SWEEP = "        self.reclaim.sweep(self.order)"
LAST = 'rec["kind"] in ("result", "complete")'
KEEP = ('        if [rec for rec in rows if rec["kind"] in ("start", "effect") and rec["seq"] > last]:\n'
        '            return "끝 뒤 start·effect"')
M1 = ("adapters/pi/keeper.py", [(SWEEP, "        pass")])
M2 = ("core/journal.py", [(LAST, 'rec["kind"] in ("result",)')])
M3 = ("core/journal.py", [(KEEP, "        if False:\n            return \"\"")])
M4 = ("core/journal.py", [("        try:\n            return self._reclaim(state)",
                          "        try:\n            self._empty_ops()\n            return self._reclaim(state)")])
M5 = ("adapters/pi/keeper_reclaim.py", [("        if ((memory.get(team) or {}).get(\"works\") or []) == names:",
                                        "        if False:")])
M6 = ("core/journal.py", [('"총량 %d + 예약 k=%d 필요 %d > 한계 %d" % (total, k, needed, limit)',
                          '"예약 k=%d 필요 %d > 한계 %d" % (k, needed, limit)')])
# 정정1(DA#57) 넷 — 새 단언이 실제로 물게 한다
M7 = ("adapters/pi/keeper_reclaim.py", [('len(removed), out.get("bodies") or 0, usage, node.usage(), cap)',
                                        'len(removed), out.get("bodies") or 0, usage, usage, cap)')])   # 남은 총량 = 회수 전
M8 = ("core/journal.py", [('for rec in self._kept(seg, state) if rec["kind"] != "import"}',
                          'for rec in seg if rec["kind"] != "import"}')])                            # 막힘에 철회 accept 포함
M9 = ("core/journal.py", [('raise self.rec.WriterRefused(\n                    "용량 부족", "회수 checkpoint — 총량 %d + 필요 %d > 한계 %d" % (total, need, limit))',
                          'raise self.rec.WriterRefused("용량 부족", "회수 checkpoint 가 내부 한계를 넘는다")')])   # checkpoint 글에 세 수 뺌
M10 = ("adapters/pi/keeper_reclaim.py", [("        if not raised:", "        if False:")])              # 장부 실패도 기억
MUTANTS = {"M1": M1, "M2": M2, "M3": M3, "M4": M4, "M5": M5, "M6": M6,
           "M7": M7, "M8": M8, "M9": M9, "M10": M10}
CASE = {"M1": T.c4, "M2": T.c1, "M3": T.c2, "M4": T.c5, "M5": T.c6, "M6": T.c7,
        "M7": T.c9, "M8": T.c3, "M9": T.c5, "M10": T.c6}


def mutant(tmp_path, mp, pair, case):
    """사본 ft2 의 변이(그 파일 1곳) → 그 사례 FAIL · 원본으로 같은 사례 1회 더 = 통과(반대 결과 대조)."""
    name, pairs = pair
    tree = tmp_path / "m" / "ft2"
    shutil.copytree(FT2, tree, ignore=shutil.ignore_patterns("tests", "__pycache__"))
    text = (tree / name).read_text(encoding="utf-8")
    for old, new in pairs:
        assert text.count(old) == 1, (name, old)
        text = text.replace(old, new)
    (tree / name).write_text(text, encoding="utf-8")
    (tmp_path / "mut").mkdir()
    with pytest.raises(AssertionError):
        case(tmp_path / "mut", mp, ft2=tree)
    (tmp_path / "orig").mkdir()
    case(tmp_path / "orig", mp, ft2=FT2)


@pytest.mark.parametrize("name", list(MUTANTS))
def test_mutant(name, tmp_path, monkeypatch):
    mutant(tmp_path, monkeypatch, MUTANTS[name], CASE[name])
