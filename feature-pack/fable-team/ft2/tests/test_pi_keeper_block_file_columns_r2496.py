"""r2496 ft2 keeper — 막힘 장부에 오르는 행이 갈래(class)·범위(scope) 칸을 갖고, 0줄인 바퀴는 전문 파일을 0바이트로 쓴다.
반례 ⑬(오래된 줄 0 = 전문 0바이트 · 오래된 줄 1 = 지금과 같은 글) · 변이 M9(전문 파일을 안 씀 → ⑬ Red) · 칸 = keeper 3종(판정 불가 · NEXT-HOLD · FILL-WAIT).
실 장부·실 keeper 상태 0 — settle() 을 가짜 keeper(k)와 장부 스텁으로 직접 부른다(바퀴·tmux·우편함 0 · sleep 0).
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "adapters" / "pi" / "keeper_block.py"
FAIL = []
T = Path(tempfile.mkdtemp(prefix="r2496-keeper-"))
STUB = T / "block-stub.sh"
STUB.write_text(
    "#!/usr/bin/env bash\n"
    "exec python3 - \"$@\" <<'PY'\n"
    "import json, os, sys\n"
    "open(os.environ['R2496_LOG'], 'a').write(json.dumps({'argv': sys.argv[1:]}, ensure_ascii=False) + '\\n')\n"
    "PY\n", encoding="utf-8")
STUB.chmod(0o755)


def load(path=SRC, name="kb"):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class K:   # settle() 이 보는 keeper 의 최소 면
    def __init__(self, root, now=1000, state=None, cap=8):
        self.root, self.dir, self.state, self.at = str(root), str(root), state or {}, now
        self.fa = type("fa", (), {"INTAKE_CAP": cap})()
        self.env = dict(os.environ, FT_BLOCK_BIN=str(STUB), R2496_LOG=str(T / "calls.log"))

    def now(self):
        return self.at

    def log(self, *a, **k):
        return None


def check(name, fn):
    try:
        fn()
        print("  OK   " + name)
    except AssertionError as e:
        FAIL.append(name)
        print("  FAIL %s — %s" % (name, e))


def ledger(mod, k):
    return mod.Ledger(k.root, k.env)


def case_empty_file():
    """⑬ — 오래된 줄 0(기억에 죽은 줄만) → 전문 파일 0바이트(⑧ 실사건: «NEXT-HOLD 50분째» 가 남지 않는다)."""
    root = T / "e1"
    root.mkdir()
    k = K(root, now=100000)
    (root / "blockseen.json").write_text(json.dumps({json.dumps(["NEXT-HOLD", "t1", "남은 일 0/8"], ensure_ascii=False):
                                                     {"first": 0, "last": 100, "text": "남은 일 0/8"}}), encoding="utf-8")
    (root / "blocks-latest.txt").write_text("50분째\tNEXT-HOLD\tt1\t남은 일 0/8\n", encoding="utf-8")
    mod = load()
    mod.settle(k, ledger(mod, k), [])
    assert (root / "blocks-latest.txt").read_text(encoding="utf-8") == "", "전문 파일이 0바이트가 아니다"


def case_long_line():
    """⑬ — 오래된 줄 1 → 지금과 같은 글(«N분째\t종류\t라벨\t글»)."""
    root = T / "e2"
    root.mkdir()
    k = K(root, now=1000)
    mod = load()
    for t in (1000, 1250, 1500, 1650):   # 바퀴마다 다시 봄(ALIVE_S 300 안) → first 1000 · last 1650 = 10분 넘음
        k.at = t
        mod.settle(k, ledger(mod, k), [("판정 불가", "t1", "쪽지 _master 없음")])
    got = (root / "blocks-latest.txt").read_text(encoding="utf-8")
    assert got.startswith("10분째\t판정 불가\tt1\t쪽지 _master 없음"), got


def case_columns():
    """keeper 3종 = 칸만 채운다 — class(판정 불가·FILL-WAIT = ㉱ · NEXT-HOLD = ㉰) · scope team · period 150 그대로."""
    root = T / "e3"
    root.mkdir()
    (T / "calls.log").unlink(missing_ok=True)
    k = K(root, now=1000)
    mod = load()
    rows_in = [("판정 불가", "t1", "쪽지 _master 없음"), ("NEXT-HOLD", "t1", "다음 카드 없음")]
    for t in (1000, 1250, 1500, 1650):
        k.at = t
        mod.settle(k, ledger(mod, k), rows_in)
    rows = [json.loads(x) for x in (T / "calls.log").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 2, rows
    for r in rows:
        a = r["argv"]
        cls = a[a.index("--class") + 1]
        assert a[a.index("--scope") + 1] == "team" and a[a.index("--period") + 1] == "150", a
        assert cls == ("㉰" if "NEXT-HOLD" in a[1] else "㉱"), a


def case_m9():
    """변이 M9 — 전문 파일 쓰기를 뺀 사본 → ⑬ Red(«50분째» 가 남는다)."""
    src = SRC.read_text(encoding="utf-8")
    line = '    write(os.path.join(k.dir, "blocks-latest.txt"), "".join(lines))'
    assert line in src, "M9 닻 없음"
    mut = T / "keeper_block_mut.py"
    mut.write_text(src.replace(line, "    pass  # M9"), encoding="utf-8")
    root = T / "e4"
    root.mkdir()
    (root / "blocks-latest.txt").write_text("50분째\tNEXT-HOLD\tt1\t남은 일 0/8\n", encoding="utf-8")
    k = K(root, now=100000)
    mod = load(mut, "kb_mut")
    mod.settle(k, ledger(mod, k), [])
    assert (root / "blocks-latest.txt").read_text(encoding="utf-8") != "", "변이가 초록(⑬ 이 잡는다)"


def main():
    print("r2496 keeper — 전문 파일 · 칸")
    check("⑬ 오래된 줄 0 = 전문 0바이트", case_empty_file)
    check("⑬ 오래된 줄 1 = 지금과 같은 글", case_long_line)
    check("keeper 3종 = class·scope 칸", case_columns)
    check("M9 전문 파일을 안 씀 — 변이 Red", case_m9)
    shutil.rmtree(T, ignore_errors=True)
    print("결과: OK=%d FAIL=%d" % (4 - len(FAIL), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
