"""r2573 ft2 keeper 변이 — 본 시험(test_keeper_next_assigned_no_owner_skip_line_r2573.py)의 사례를 사본 위에서 죽인다.
M1 줄 뺌 → (1) · M2 기억 대조 뺌 → (2) · M3 기억 값을 카드 이름만으로 → (3) · M4 owner 있어도 줄 → (4) · M5 «- 세트:» 대조 뺌 → (6) ·
M6 줄을 내면서 block 을 풂 → (1) · M7 수동 닫기 안내를 park 실패 줄에도 → (13) · M8 reopen 참인 바퀴에도 줄 → (5) ·
M9 «쉼 기록 없음» 을 미등록과 같은 값으로 → (14)(15) · M10 park=already 끝 줄 꼬리 뺌 → (16) · M11 꼬리를 LEFT-MANUAL 에 → (17) ·
M13 줄을 내면서 why 셈에 더함 → (18). 사례 정의·대역 = 본 파일(중복 0) · 실 tmux·명부·설치 0 · sleep 0.
"""
import importlib.util  # noqa: E401
from pathlib import Path
import pytest

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("keeper_r2573_cases", str(HERE / "test_keeper_next_assigned_no_owner_skip_line_r2573.py"))
t = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(t)
MUTANTS, KN, MC, copy_tree, mutate_manual, pair = t.MUTANTS, t.KN, t.MC, t.copy_tree, t.mutate_manual, t.pair


@pytest.mark.parametrize("name", list(MUTANTS))
def test_mutant(name, tmp_path, monkeypatch):
    old, new, cases = MUTANTS[name]
    tree = copy_tree(tmp_path)
    text = (tree / KN).read_text(encoding="utf-8")
    assert text.count(old) == 1, (name, old, text.count(old))
    (tree / KN).write_text(text.replace(old, new), encoding="utf-8")
    for case in cases:
        pair(tmp_path, case, tree, monkeypatch)


@pytest.mark.parametrize("name,pairing", [("M7", ("[:60], work, attempt, PARK, k.root, team))", "[:60], work, attempt, PARK, k.root, team) + REOPEN_HOW)")),
                                         ("M10", ("reason, note, REOPEN_HOW))", 'reason, note, ""))')),
                                         ("M11", ("% (seat, n, path, left, path))", "% (seat, n, path, left, path) + REOPEN_HOW)"))])
def test_mutant_manual_close(name, pairing, tmp_path, monkeypatch):
    """M7 park 실패 줄에 안내 → (13) Red · M10 park=already 끝 줄 꼬리 뺌 → (16) Red · M11 꼬리를 LEFT-MANUAL 에 → (17) Red."""
    old, new = pairing
    tree, case = copy_tree(tmp_path), {"M7": "13", "M10": "16", "M11": "17"}[name]
    mutate_manual(tree, old, new)
    pair(tmp_path, case, tree, monkeypatch)
