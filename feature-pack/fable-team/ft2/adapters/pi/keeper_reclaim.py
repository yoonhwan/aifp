"""r2518 ft2 keeper — 바퀴마다 팀 runtime 총량을 보고, 절반을 넘으면 회수(reclaim)를 스스로 부른다.

2026-11-23 실사건: keeper 닫기 영수 4건이 매 바퀴 «용량 부족 · 예약 k=3 필요 2321880 > 한계 8388607» 로
거절됐는데, 회수(reclaim)를 부르는 곳이 core/cli.py 동사뿐이라 keeper 는 한 번도 덜어내지 않았다.

sweep(teams) = 바퀴 1회 · 팀마다
  · 총량 < 총 cap / 2 = 부르지 않는다(회수 호출 0) · ≥ 절반 = 1회
  · 잠금 점유 = BUSY 1줄 · 그 밖 실패 = «판정 불가» 1줄 · 예외는 바퀴 밖으로 내보내지 않는다
  · 덜어내기가 막히면 막는 work 이름·사유를 1줄에 올리고, 총량 ≥ 3/4 이면 막힘 장부에 1건
    (같은 집합 = 다시 올리지 않는다 · 기억 = state/ft2-keeper/reclaim-blocked.json)
core 손 0 — Journal 공개 면(usage·total_cap·reclaim)만 부른다. 상한 7초(장부 도구 1회) · 출력 버림.
"""
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FT2 = os.path.dirname(os.path.dirname(HERE))
HALF, QUARTER3, NAMES = 2, 4, 3      # 총량 ×2 ≥ 총 cap = 회수 1회 · 총량 ×4 ≥ 총 cap ×3 = 4분의 3 · 로그 이름 3개


def _load(path, alias):
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


journal = _load(os.path.join(FT2, "core", "journal.py"), "ft2_keeper_reclaim_journal")
projection = _load(os.path.join(FT2, "core", "projection.py"), "ft2_keeper_reclaim_projection")
block = _load(os.path.join(HERE, "keeper_block.py"), "ft2_keeper_reclaim_block")


class Reclaim:
    """팀 runtime 회수 1바퀴 — keeper 가 부른다(잠금·장부·기억은 여기서 닫는다)."""

    def __init__(self, k):
        self.k = k
        self.path = os.path.join(k.dir, "reclaim-blocked.json")   # 막는 work 집합 기억(같은 집합 재올림 0)

    def sweep(self, teams):
        ledger = block.Ledger(self.k.root, self.k.env)
        for team in teams:
            try:
                self.one(team, ledger)
            except Exception:   # noqa: BLE001 — 회수 결함이 바퀴를 세우지 않는다(반례 ④ 예외 0)
                self.k.log("판정 불가", team, "runtime 회수 실패")

    def one(self, team, ledger):
        runtime = projection.runtime_path(self.k.root, team)
        if not os.path.isdir(runtime):
            return
        node = journal.Journal(runtime)                  # ops 콜백 0 = keeper 는 흔적을 안 남긴다
        usage = node.usage()
        if usage * HALF < node.total_cap:
            return                                       # 절반 미만 = 회수 호출 0
        out, cap = node.reclaim(), node.total_cap
        if out.get("result") != "회수 결과":
            self.k.log("RUNTIME-RECLAIM", team, "%s · %s · 총량 %d/%d" % (
                out.get("result"), out.get("reason") or "-", usage, cap))
            return
        blocked = out.get("blocked") or {}
        removed = out.get("reclaimed") or []
        if not removed and not blocked:
            return                                       # 덜어낸 것도 막힌 것도 0 = 줄 0(매 바퀴 같은 줄 0)
        line = "회수 %d조각 · 본문 %d · 총량 %d → %d · 한계 %d" % (
            len(removed), out.get("bodies") or 0, usage, node.usage(), cap)   # 정정1 = 회수 «뒤» 총량
        if blocked:
            line += " · 막는 work %d" % len(blocked)
            shown = sorted(blocked)[:NAMES]
            line += " = " + " ".join("%s(%s)" % (name, blocked[name]) for name in shown)
            if len(blocked) > NAMES:
                line += " 외 %d" % (len(blocked) - NAMES)
        self.k.log("RUNTIME-RECLAIM", team, line)
        if blocked and usage * QUARTER3 >= cap * 3:
            self.raise_once(ledger, team, blocked, usage, cap)

    def raise_once(self, ledger, team, blocked, usage, cap):
        """총량 3/4 넘고 막혔다 = 막힘 장부 1건 · 등록 성공한 집합만 기억(같은 집합 0건 · 정정4)."""
        names = sorted(blocked)
        memory = self.k.read_json(self.path)
        if ((memory.get(team) or {}).get("works") or []) == names:
            return
        first = names[0]
        raised = ledger.raise_("ft2-runtime-reclaim", "team", team,
                               "--cause", "runtime 총량 %d/%d · 끝난 조각을 못 덜어냄 — 막는 work %d (%s %s)" % (
                                   usage, cap, len(names), first, blocked[first]),
                               "--fix", "끝난 work 닫기·잘못 열린 조각 정리 — 판정 = keeper RUNTIME-RECLAIM 줄",
                               "--period", "150", "--class", "㉱", "--scope", "team")
        if not raised:
            return                                       # 장부 없음·실패·중단 = 기억 0(다음 바퀴 다시 올린다)
        memory[team] = {"works": names, "at": self.k.stamp()}
        try:
            os.makedirs(self.k.dir, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(memory, ensure_ascii=False, sort_keys=True))
        except OSError:
            pass                                         # 기억 못 씀 = 다음 바퀴 다시 올림(바퀴 결과 불변)
