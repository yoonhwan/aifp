"""r2526 — 쪼갠 시험 파일의 «논리 사례 id» 대응표(고정) + 대조기.

논리 사례 id = 함수명 · 매개변수 id(클래스명 자리 포함) — **파일 경로는 뺀다**(DA#59 «사례 수 보존»).
원 파일(test_*.py) → 나눈 파일(test_*_a/b/c.py) 대응을 여기 한 곳에 못 박고, 대조기가 «실제 pytest 표식» 과 맞춘다.
왜: 파일을 나누면 nodeid 에 새 경로가 붙어 원문 nodeid 집합 비교로는 옮겨간 사례가 차이로 보인다.
빠짐(원 파일에 있는데 나눈 파일 어디에도 없음) · 겹침(같은 논리 id 가 둘 이상) · 덤(나눈 파일에만 있음)을 따로 거절한다.
"""
import importlib.util
from pathlib import Path

TOTAL = 92   # 카드 기준값 — 원 파일 넷의 사례 합

# 원 파일 → {시험 함수: [매개변수 id]} — 쪼개기 전 그대로(고정 · 손으로 고치지 않는다)
ORIGINALS = {
    "test_keeper_launch_detach_r1929.py": {
        "test_case": ["①", "④", "⑤k", "⑧", "⑨", "⑯", "⑰", "⑱", "⑲", "⑤", "⑥", "⑦", "⑬", "⑮", "⑰p"],
        "test_mutant": ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9"],
    },
    "test_keeper_next_reopen_name_tail_r2113.py": {
        "test_case": ["①", "②", "③", "③'", "④", "⑤", "⑥", "⑦", "⑧", "⑧'", "⑧''", "⑩", "⑪"],
        "test_mutant": ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9"],
    },
    "test_keeper_no_lease_close_r2400.py": {
        "test_case": ["①", "①둘째", "②", "③", "④", "⑤", "⑥", "⑥b", "⑥c", "⑦", "⑧", "⑨", "⑩"],
        "test_mutant": ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10"],
    },
    "test_pi_keeper_block_raise_r2072.py": {
        "test_case": ["①lib", "①none", "①path", "②rc9", "②hang", "②cap20", "③", "④", "⑤", "⑥", "⑦", "⑧skip"],
        "test_same_without_ledger": ["③", "④", "⑤", "⑥", "⑦"],
        "test_same_real_round_and_hang": [None],
        "test_report_and_lock": [None],
        "test_mutant": ["M1", "M2", "M3", "M4"],
    },
}

# 나눈 파일 → {시험 함수: [매개변수 id]} (None = 매개변수 없음 = 함수명 하나)
SPLITS = {
    "test_keeper_launch_detach_r1929_a.py": {"test_case": ORIGINALS["test_keeper_launch_detach_r1929.py"]["test_case"]},
    "test_keeper_launch_detach_r1929_b.py": {"test_mutant": ORIGINALS["test_keeper_launch_detach_r1929.py"]["test_mutant"]},
    "test_keeper_next_reopen_name_tail_r2113_a.py": {"test_case": ORIGINALS["test_keeper_next_reopen_name_tail_r2113.py"]["test_case"]},
    "test_keeper_next_reopen_name_tail_r2113_b.py": {"test_mutant": ORIGINALS["test_keeper_next_reopen_name_tail_r2113.py"]["test_mutant"]},
    "test_keeper_no_lease_close_r2400_a.py": {"test_case": ORIGINALS["test_keeper_no_lease_close_r2400.py"]["test_case"]},
    "test_keeper_no_lease_close_r2400_b.py": {"test_mutant": ["M1", "M2", "M3", "M4", "M5"]},
    "test_keeper_no_lease_close_r2400_c.py": {"test_mutant": ["M6", "M7", "M8", "M9", "M10"]},
    "test_pi_keeper_block_raise_r2072_a.py": {"test_case": ORIGINALS["test_pi_keeper_block_raise_r2072.py"]["test_case"]},
    "test_pi_keeper_block_raise_r2072_b.py": {"test_mutant": ["M1", "M2", "M3", "M4"], "test_report_and_lock": [None]},
    "test_pi_keeper_block_raise_r2072_c.py": {"test_same_without_ledger": ["③", "④", "⑤", "⑥", "⑦"],
                                              "test_same_real_round_and_hang": [None]},
}

# 나눈 파일 → 원 파일 — 이름 꼴 «원이름_<a|b|c>.py» 에서 «_a» 만 뗀다(추측 0)
OWNER = {split: split[:-len("_a.py")] + ".py" for split in SPLITS}


def logical(func, pid):
    """논리 사례 id — 매개변수 없으면 함수명만."""
    return func if pid is None else "%s[%s]" % (func, pid)


def declared(splits=None):
    """대응표가 말하는 나눈 파일별 논리 id 집합."""
    return {name: {logical(f, p) for f, ids in funcs.items() for p in ids}
            for name, funcs in (SPLITS if splits is None else splits).items()}


def actual(tests_dir):
    """그 폴더의 나눈 시험 파일이 **실제로** 도는 논리 id 집합 — pytest 표식(parametrize)을 그대로 읽는다."""
    out = {}
    for name in SPLITS:
        path = Path(tests_dir) / name
        spec = importlib.util.spec_from_file_location("r2526_ids_" + name[:-3], str(path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        got = set()
        for attr, val in vars(mod).items():
            if not attr.startswith("test_") or not callable(val) or getattr(val, "__module__", None) != mod.__name__:
                continue
            pids = [None]
            for mark in getattr(val, "pytestmark", []):
                if getattr(mark, "name", "") == "parametrize":
                    pids = list(mark.args[1])
            got |= {logical(attr, p) for p in pids}
        out[name] = got
    return out


def problems(tests_dir, originals=None, splits=None):
    """대조 — 빈 목록 = 통과. 사유는 앞머리로 종류를 가른다: «빠짐» «겹침» «덤» «합» «원본남음»."""
    originals = ORIGINALS if originals is None else originals
    splits = SPLITS if splits is None else splits
    have = actual(tests_dir) if tests_dir else declared(splits)
    bad = []
    table = {n: {logical(f, p) for f, ids in funcs.items() for p in ids} for n, funcs in splits.items()}
    for name, want in table.items():   # 표 ↔ 실제 파일
        for lid in sorted(want - have.get(name, set())):
            bad.append("빠짐 %s %s — 표에 있는데 파일에 없다" % (name, lid))
        for lid in sorted(have.get(name, set()) - want):
            bad.append("덤 %s %s — 파일에 있는데 표에 없다" % (name, lid))
    seen = {}
    for name, got in have.items():
        for lid in got:
            seen.setdefault((OWNER.get(name), lid), []).append(name)
    for (orig, lid), where in sorted(seen.items(), key=lambda kv: (str(kv[0]), kv[1])):
        if len(where) > 1:
            bad.append("겹침 %s %s — %s" % (orig, lid, " · ".join(sorted(where))))
    for orig, funcs in originals.items():   # 원 파일 ↔ 나눈 파일 합
        want = {logical(f, p) for f, ids in funcs.items() for p in ids}
        got = {lid for (o, lid), where in seen.items() if o == orig for _ in where}
        for lid in sorted(want - got):
            bad.append("빠짐 %s %s — 나눈 파일 어디에도 없다" % (orig, lid))
        for lid in sorted(got - want):
            bad.append("덤 %s %s — 원 파일에 없던 사례" % (orig, lid))
    total = sum(len(v) for v in have.values())
    if total != TOTAL:
        bad.append("합 %d — 기준값 %d" % (total, TOTAL))
    if tests_dir:
        for orig in originals:
            if (Path(tests_dir) / orig).exists():
                bad.append("원본남음 %s — 쪼갠 뒤 원 파일이 남아 같은 사례가 두 번 돈다" % orig)
    return bad
