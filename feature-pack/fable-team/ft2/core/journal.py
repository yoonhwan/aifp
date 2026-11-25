"""ft2 코어 journal — segment 회전 · 총량 cap · 회수 (r1584 · PR② 넷째 장).

계약 18줄 줄 18: 미처리는 지우지 않고, 넘치면 «용량 부족» 으로 새 접수를 거절한다. 활성 =
runtime/journal.jsonl(이름 그대로 · 이관 0) · 닫힌 것 = journal.<N>.jsonl. 회전 = append 뒤 활성
크기가 segment cap 에 닿으면 닫고 새 활성(순서 판독 = records). 회수 = base checkpoint → 본문 →
segment(오래된 순) · 잠금 1회 · 멱등. base = state.journal_base {upto,count,proj,receipts} 이고
recover_state 가 base 뒤 suffix 만 접는다. 총량 = runtime 파일 st_size 합 · 한계 = 총 cap −
예약(새 접수) / 총 cap − 1(내부 writer) 이므로 peak ≤ 한계 < 총 cap.
"""

import fcntl
import importlib.util
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
ACTIVE = "journal.jsonl"
CLOSED_PREFIX = "closed."          # r2520: 닫힌 장부 = runtime/closed.<N>.jsonl (한 줄 = 키 1개)
CLOSED_WORK_FIELDS = ("done", "released", "reassess_done", "owners_recovered", "deliveries", "generations")
CLOSED_BATCH = 200                  # 한 바퀴에 옮기는 닫힌 work 최대(r2520 K4 = 나눠 옮긴다 · 반례 ⑦)
CLOSED_SYNTHETIC = ("goal:", "close:")   # work 가 아닌 done 키(골 마감 · 닫기 영수) = 옮기지 않는다
SUBMIT_OPS = ("body_tmp_write", "body_file_fsync", "body_rename", "body_dir_fsync",
              "journal_write", "journal_fsync", "state_write", "receipt")   # 접수 1건의 ops 줄
WRITER_OPS = ("journal_write", "journal_fsync", "state_write")               # 내부 writer 1줄
PROJ_FIELDS = ("generations", "owners", "reservations", "deliveries", "done",
               "reopens", "lifted",   # r1727: reopens·lifted
               "imported",   # r1774: 가져온 기록(F6)
               "returned",   # r1990: 반환(열린 work 라 회수 대상은 아니지만 base 칸도 같은 해석)
               "parked",     # r2055: 쉼(returned 와 같은 해석)
               "withdrawn",  # r1925b: 철회 attempt(회수 뒤에도 같은 command 재접수 판정 유지)
               "reassess_done", "released", "owners_recovered", "uncertain", "close_receipts", "refusals")


def _load_record():
    spec = importlib.util.spec_from_file_location("ft2_core_record", os.path.join(_HERE, "record.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def line_bytes(rec):
    """journal 1줄 byte(개행 포함) — 필요량 산정과 실제 쓰기가 같은 함수를 쓴다."""
    return len(json.dumps(rec, ensure_ascii=False, sort_keys=True).encode("utf-8")) + 1


def ops_bytes(names):
    return sum(len(json.dumps({"op": name}, ensure_ascii=False).encode("utf-8")) + 1 for name in names)


def try_lock(path):
    """writer.lock 비차단 시도 — 잡으면 핸들, 점유 중이면 None(기다리지 않는다)."""
    handle = open(path, "a+", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return None
    return handle


def unlock(handle):
    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    handle.close()


def _fsync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _closed_row_bytes(row):
    return len(json.dumps(row, ensure_ascii=False, sort_keys=True).encode("utf-8")) + 1


class ClosedLedger:
    """runtime/closed.<N>.jsonl — 끝난 work·command·event·attempt·import 키 1줄 = 1개(r2520 K3).

    state 는 «닫힌 장부 있음 · 끝 seq»(journal_base.closed) 만 든다. 판독 = 소비자가 가진 키 그대로
    (K2 진입점 4개 · work 1개) · 중복 키는 뒤 줄이 이긴다(크래시 재시도 = 같은 줄 다시).
    반 줄·형 위반은 조용히 건너뛰지 않고 CorruptStateError(«복구 필요» · 쓰기 0)로 올린다(반례 ⑧).
    """

    KINDS = ("work", "cmd", "event", "attempt", "import")

    def __init__(self, runtime, rec=None):
        self.runtime, self.rec, self._cache = os.path.abspath(runtime), rec, None

    def files(self):
        """장부 파일 [(N, path)] N 오름차순 — journal.<N>.jsonl 과 같은 꼴."""
        out = []
        for name in os.listdir(self.runtime):
            stem = name[len(CLOSED_PREFIX):-6] if name.startswith(CLOSED_PREFIX) and name.endswith(".jsonl") else ""
            if stem.isdigit():
                out.append((int(stem), os.path.join(self.runtime, name)))
        return sorted(out)

    def path(self):
        """덧붙일 파일 = 가장 큰 번호(없으면 closed.1.jsonl) — 파일 수를 늘리지 않는다."""
        files = self.files()
        return files[-1][1] if files else os.path.join(self.runtime, CLOSED_PREFIX + "1.jsonl")

    def index(self):
        """(종류, 키) → 줄 사전. 파일 크기가 그대로면 지난 판독을 그대로 쓴다(조회 = 쓰기마다 1번)."""
        signature = tuple((path, os.path.getsize(path)) for _n, path in self.files())
        if self._cache is not None and self._cache[0] == signature:
            return self._cache[1]
        out = {}
        for _n, path in self.files():
            with open(path, encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    try:
                        row = json.loads(line)
                        kind, key = row["k"], row["key"]
                        if kind not in self.KINDS or not isinstance(key, str) or not isinstance(row.get("row"), dict):
                            raise ValueError("닫힌 장부 줄 형 위반")
                    except (ValueError, KeyError, TypeError) as exc:
                        raise self.rec.CorruptStateError("닫힌 장부 판독 불가: %s" % exc)
                    out[(kind, key)] = row
        self._cache = (signature, out)
        return out

    def _get(self, kind, key):
        return (self.index().get((kind, key)) or {}).get("row")

    def work(self, work):
        """끝난 work 의 state 칸(done·generations 등) — 없으면 None."""
        return self._get("work", work)

    def works(self):
        """장부에 있는 끝난 work 이름들 — 투영이 회수 전후 같은 작업 목록을 내는 데 쓴다(r2520)."""
        return sorted(key for (kind, key) in self.index() if kind == "work")

    def command_count(self):
        """장부로 옴긴(command) 수 — 투영 «pending» 이 회수 전후 같은 수가 된다(r2520)."""
        return len([1 for (kind, _key) in self.index() if kind == "cmd"])

    def command(self, command):
        """회수된 command 영수 {attempt, count, work} — Intake._prior_receipt 진입점."""
        return self._get("cmd", command)

    def event(self, event):
        """회수된 닫기 영수 — CloseNext._receipt 진입점."""
        return self._get("event", event)

    def attempt(self, attempt):
        """회수된 철회 attempt — withdraw 진입점."""
        return self._get("attempt", attempt)

    def import_key(self, key):
        """회수된 가져오기 키 — legacy_import 진입점."""
        return self._get("import", key)

    def append(self, rows):
        """덧붙이기 + fsync — state checkpoint «앞»(r2520 K1 순서). 재실행 = 같은 줄 다시(판독은 뒤 줄)."""
        if not rows:
            return 0
        payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
        with open(self.path(), "a", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        _fsync_dir(self.runtime)
        self._cache = None
        return len(payload.encode("utf-8"))


class Journal:
    """팀 runtime 1곳 — 회전·판독·총량 판정·회수·복구를 이 한 곳에서 한다."""

    def __init__(self, runtime, segment_cap=65536, total_cap=8388608, reserve=532480,
                 state_slack=4096, line_max=512, ops=None, on_step=None, rec=None):
        self.runtime, self.segment_cap, self.total_cap = os.path.abspath(runtime), segment_cap, total_cap
        self.reserve_bytes, self.state_slack = max(1, reserve), state_slack
        self.line_max = line_max
        self.ops, self.on_step = ops or (lambda op: None), on_step or (lambda step: None)
        self.rec = rec or _load_record()
        self.active_path = os.path.join(self.runtime, ACTIVE)
        self.state_path = os.path.join(self.runtime, "state.json")
        self.tmp_path = os.path.join(self.runtime, "tmp")
        self.lock_path = os.path.join(self.runtime, "writer.lock")
        self.ops_path = os.path.join(self.runtime, "ops.jsonl")   # r2518 K1: 회수 성공 = 흔적 비움
        self.ledger = ClosedLedger(self.runtime, self.rec)        # r2520: 끝난 work 칸 = 닫힌 장부
        self.envelope, self.cached_state = None, {}

    def _size(self, path):
        return os.path.getsize(path) if os.path.exists(path) else 0

    def _limit(self, internal=False):
        return self.total_cap - (1 if internal else self.reserve_bytes)

    def envelope_for(self, state):
        return len(json.dumps(state, ensure_ascii=False, sort_keys=True).encode("utf-8"))

    def reserve(self, k=1):
        """내부 writer 1호출의 append 상한 k 합산 예약(DA R2-①) — 넘으면 쓰기 전에 «용량 부족»."""
        state, total = self._size(self.state_path), self.usage()
        needed = k * (self.line_max + state + k * (self.line_max + self.state_slack)
                      + ops_bytes(WRITER_OPS))
        limit = self._limit(True)
        if total + needed > limit:                        # r2518 K5: 총량이 없으면 «필요 < 한계» 인데 거절로 읽힌다
            raise self.rec.WriterRefused("용량 부족", "총량 %d + 예약 k=%d 필요 %d > 한계 %d" % (total, k, needed, limit))

    def closed(self):
        """닫힌 segment [(N, path)] N 오름차순."""
        out = []
        for name in os.listdir(self.runtime):
            stem = name[8:-6] if name.startswith("journal.") and name.endswith(".jsonl") else ""
            if stem.isdigit():
                out.append((int(stem), os.path.join(self.runtime, name)))
        return sorted(out)

    def _records_of(self, path):
        out = []
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    self.rec.check(rec)
                except (ValueError, self.rec.RecordError) as exc:
                    raise self.rec.CorruptStateError("journal 판독 불가: %s" % exc)
                out.append(rec)
        return out

    def records(self):
        """닫힌 segment(N 오름차순) + 활성 파일 한 줄 순서 — seq 감소·중복 = CorruptStateError."""
        out = []
        for path in [p for _n, p in self.closed()] + [self.active_path]:
            if not os.path.exists(path):
                continue
            for rec in self._records_of(path):
                if out and rec["seq"] <= out[-1]["seq"]:
                    raise self.rec.CorruptStateError("journal seq 역행·중복: %r <= %r"
                                                     % (rec["seq"], out[-1]["seq"]))
                out.append(rec)
        return out

    def usage(self):
        """runtime 폴더 총량 = 모든 파일 st_size 합(state·segment·ops·bodies·tmp)."""
        return sum(self._size(os.path.join(root, name))
                   for root, _dirs, files in os.walk(self.runtime) for name in files)

    def state(self):
        """state 판독 — tmp/state.json.tmp 가 남아 있으면 «복구 필요»(Journal.recover 로만 푼다)."""
        if os.path.exists(os.path.join(self.tmp_path, "state.json.tmp")):
            raise self.rec.CorruptStateError("state.json.tmp 잔여 = 복구 필요(Journal.recover)")
        self.cached_state = self.rec.read_state_guarded(self.state_path)
        return self.cached_state

    def admits_submit(self, body, rec, envelope):
        """새 접수 필요량 = 본문 + journal 줄 + 새 state + ops 8줄 — 본문 tmp «전» 판정(DA R2)."""
        needed = len(body.encode("utf-8")) + line_bytes(rec) + envelope + ops_bytes(SUBMIT_OPS)
        return self.usage() + needed <= self._limit()

    def _reserve_line(self, rec, envelope):
        """내부 writer 1줄의 필요량 판정 = 줄 + state 몫 + ops 3줄 — 넘으면 쓰기 0(«용량 부족»)."""
        total, limit = self.usage(), self._limit(True)
        needed = line_bytes(rec) + envelope + ops_bytes(WRITER_OPS)
        if total + needed > limit:
            raise self.rec.WriterRefused("용량 부족", "총량 %d + 필요 %d > 한계 %d" % (total, needed, limit))

    def _write_line(self, rec):
        with open(self.active_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            self.ops("journal_write")
            os.fsync(handle.fileno())
        self.ops("journal_fsync")
        _fsync_dir(self.runtime)

    def append(self, rec, envelope=None):
        """내부 writer 1줄 — 총량 판정 → append → 회전. 넘으면 쓰기 0 · WriterRefused(«용량 부족»)."""
        self.rec.check(rec)
        envelope = (envelope if envelope is not None
                    else self._size(self.state_path) + line_bytes(rec) + self.state_slack)
        self._reserve_line(rec, envelope)
        self.envelope = envelope
        self._write_line(rec)
        if self._size(self.active_path) >= self.segment_cap:
            closed = self.closed()
            os.replace(self.active_path, os.path.join(self.runtime,
                                                      "journal.%d.jsonl" % ((closed[-1][0] if closed else 0) + 1)))
            _fsync_dir(self.runtime)
            self.on_step("after_rotate")

    def write_state(self, state):
        """state checkpoint — 예약한 state 몫을 넘으면 tmp 쓰기 «전» 에 «완료 유보»(journal 이 정본)."""
        payload = json.dumps(state, ensure_ascii=False, sort_keys=True)
        size = len(payload.encode("utf-8"))
        if self.envelope is not None and size > self.envelope:
            raise self.rec.WriterRefused("완료 유보", "state 실측 %d > 예약 %d" % (size, self.envelope),
                                         written=True)
        tmp = os.path.join(self.tmp_path, "state.json.tmp")
        with open(tmp, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        self.on_step("state_tmp_written")
        os.replace(tmp, self.state_path)
        _fsync_dir(self.runtime)
        self.ops("state_write")
        self.envelope = None

    def _keep_last(self, top, last):
        """마지막 seq 를 담은 segment 는 회수하지 않는다 — seq 되감김 0(R1 ⑤)."""
        return top >= last

    def _drop(self, path):
        """segment 1개 삭제 — 없는 파일은 건너뛴다(재실행 멱등 · M3)."""
        if not os.path.exists(path):
            return False
        os.unlink(path)
        self.ops("seg_unlink")
        return True

    def _empty_ops(self):
        """r2518 ⑤ — 회수 성공 = 흔적 파일(ops.jsonl)을 0바이트 일반 파일로 비운다(지우기·모양 바꾸기 0)."""
        path = self.ops_path
        if os.path.isfile(path) and not os.path.islink(path):
            with open(path, "w", encoding="utf-8"):
                pass

    def _unlink(self, rel, op):
        full = os.path.join(self.runtime, rel)
        if os.path.exists(full):
            os.unlink(full)
            self.ops(op)

    def reclaim(self, state=None):
        """끝난 segment 만 회수 — base checkpoint → 본문 → segment. 잠금 1회 · 재실행 멱등."""
        lock = try_lock(self.lock_path)
        if lock is None:
            return {"result": "BUSY", "reclaimed": [], "bodies": 0, "reason": "writer.lock 점유"}
        try:
            return self._reclaim(state)
        except self.rec.CorruptStateError as exc:
            return {"result": getattr(exc, "word", "복구 필요"), "reclaimed": [], "bodies": 0,
                    "reason": str(exc)}
        finally:
            unlock(lock)

    def _reclaim(self, state=None):
        records = self.records()
        state = self.rec.recover_state(state or self.state(), records)
        base = dict(state.get("journal_base") or {})
        upto, last = base.get("upto") or 0, (records[-1]["seq"] if records else 0)
        targets, bodies, new_upto = [], [], upto
        withdrawn = state.get("withdrawn") or {}            # r1925b DA2 ⓐ: 철회 attempt 본문 = 옮긴 경로
        blocked = {}
        for _n, path in self.closed():
            seg = self._records_of(path)
            top = max([rec["seq"] for rec in seg] or [0])
            if not top or (top > upto and self._keep_last(top, last)):
                break                                      # 마지막 seq segment = 회수 대상 아님
            if top > upto and not self._segment_closed(seg, records, state):
                blocked = self._blocking(seg, records, state)   # r2518 K4: 막는 work 이름·사유
                break                                      # 열린 work = 보존
            targets.append(path)                           # top ≤ upto = 재실행(멱등) / 닫힌 segment
            new_upto = max(new_upto, top)
            bodies += [(withdrawn.get(rec["attempt"]) or {}).get("body") or rec["body"]
                       for rec in seg if rec["kind"] == "accept" and rec.get("body")]
        live = {rec.get("body") for rec in records if rec["kind"] == "accept" and rec["seq"] > new_upto}
        bodies = [name for name in bodies if name not in live]   # r1925b DA2 ⓑ: 살아 있는 accept 본문은 둔다
        work_state = dict(state)
        if new_upto > upto:
            folded = [rec for rec in records if rec["seq"] <= new_upto]
            proj = self.rec.recover_state(state, folded)
            receipts = dict(base.get("receipts") or {})
            receipts.update({rec["command"]: rec["attempt"] for rec in folded if rec["kind"] == "accept"})
            work_state = dict(state, journal_base={
                "upto": new_upto, "count": (base.get("count") or 0) + len(
                    [rec for rec in folded if rec["seq"] > upto]), "receipts": receipts,
                "proj": {name: proj.get(name) or {} for name in PROJ_FIELDS}})
            if base.get("closed"):
                work_state["journal_base"]["closed"] = dict(base["closed"])
        # r2520 K1: 끝난 work 칸 → 닫힌 장부(덧붙이기 + fsync) → state checkpoint → 본문 → 조각.
        rows, new_state, ledger_bytes = self._closed_batch(work_state, records, new_upto)
        if new_upto > upto or rows:
            size, limit = self.envelope_for(new_state), self._limit(True)
            total = self.usage()
            # DA #280106 ②: transaction 이 state tmp 경계 «전» 에 쓰는 ops·장부 줄까지 예약에 센다.
            need = size + ledger_bytes + ops_bytes(("closed_ledger", "reclaim_checkpoint", "state_write"))
            if total + need > limit:
                raise self.rec.WriterRefused(
                    "용량 부족", "회수 checkpoint — 총량 %d + 필요 %d > 한계 %d" % (total, need, limit))
            if rows:
                self.ledger.index()                    # r2520 ⑧: 덧붙이기 전에 장부 판독(깨진 줄 = 복구 필요 · 쓰기 0)
                self.ledger.append(rows)
                self.ops("closed_ledger")
                self.on_step("reclaim_after_ledger")
            self.ops("reclaim_checkpoint")
            self.envelope = size
            self.write_state(new_state)
            self.on_step("reclaim_after_checkpoint")
        for name in bodies:                                # K1 = 본문 삭제 뒤 · segment 삭제 전
            self._unlink(name, "body_unlink")
        self.on_step("reclaim_after_bodies")
        removed = [os.path.basename(path) for path in targets]
        for idx, path in enumerate(targets):
            if self._drop(path) and idx == 0:
                self.on_step("reclaim_after_seg")          # K2 = 첫 segment 삭제 직후
        _fsync_dir(self.runtime)
        self._empty_ops()                                  # r2518 K1: 같은 잠금 안에서만 · 실패 갈래는 그대로
        return {"result": "회수 결과", "reclaimed": removed, "bodies": len(bodies), "upto": new_upto,
                "blocked": blocked, "moved": len(rows)}

    def _closed_batch(self, state, records, new_upto):
        """장부 줄·뺀 state — 예산이 모자라면 잘라 본다(r2520 K4: 여러 바퀴 분할).

        돌려주는 값 = (줄 목록, 새 state, 장부 바이트). 앞 장부 덧붙이기·state checkpoint 가 함께
        한계 안에 들어야 회수 checkpoint 를 쓴다(반례 ⑦ 매 바퀴 총량 ≤ 한계)."""
        rows, out, size = [], state, 0
        for batch in (CLOSED_BATCH, 50, 10, 1):
            rows, out, size = self._closed_rows(state, records, new_upto, batch)
            need = self.envelope_for(out) + size + ops_bytes(
                ("closed_ledger", "reclaim_checkpoint", "state_write"))
            if self.usage() + need <= self._limit(True) or (not rows and batch == CLOSED_BATCH):
                return rows, out, size
        return rows, out, size

    def _archived(self, work, moved):
        """이번 바퀴에 옮기는 work(moved) 또는 앞 바퀴에 이미 장부로 간 work = «기록이 state 밖».
        r2520 DA#57: 영수의 두 work 가 서로 다른 바퀴에 빠져도 영수가 state 에 남지 않게 두 바퀴를 함께 본다."""
        if work is None or work in moved:
            return True
        return isinstance(work, str) and self.ledger.work(work) is not None

    def _closed_rows(self, state, records, new_upto, limit=CLOSED_BATCH):
        """이번 회수 범위(seq ≤ new_upto)에서 완전히 끝난 work·command 키 → 장부 줄 + 뺌 state(r2520 K1).

        옮기는 칸 = 닫힌 목록 4묶음: ⓐ 닫힌 work 의 CLOSED_WORK_FIELDS ⓑ·ⓒ 끝난 command 의 pending·attempts
        ⓓ journal_base.receipts 그 command 줄 · 짝 칸(close_receipts = event · withdrawn = attempt ·
        imported = import key). 열린 work 칸은 그대로 둔다(반례 ⑥) · 닫힘 판정 = 회수 전 state 그대로
        (닫힘 5가드 재사용 · M4). 뒤 조각에 그 work·attempt·command 줄이 남아 있으면 옮기지 않는다."""
        live = [rec for rec in records if rec["seq"] > new_upto]
        live_works = {rec.get("work") for rec in live if isinstance(rec.get("work"), str)}
        live_commands = {rec["command"] for rec in live}
        live_attempts = {rec.get("attempt") for rec in live}
        accept_commands = {rec["command"] for rec in live if rec["kind"] == "accept"}   # 살아 있는 접수만
        by_work = {}
        for rec in records:
            if isinstance(rec.get("work"), str):
                by_work.setdefault(rec["work"], []).append(rec)
        done = state.get("done") or {}
        works = []
        for work in sorted(done):
            if len(works) >= limit:
                break
            if work.startswith(CLOSED_SYNTHETIC) or work in live_works:
                continue
            if self._closed_why_rows(work, by_work.get(work) or [], state):
                continue                                    # 아직 열린 work = 그대로(M4 · 반례 ⑥)
            works.append(work)
        moved = set(works)
        rows, commands, events = [], set(), set()
        if moved:
            for work in works:
                fields = {name: (state.get(name) or {})[work] for name in CLOSED_WORK_FIELDS
                          if work in (state.get(name) or {})}
                rows.append({"k": "work", "key": work, "row": fields})
            for rec in records:
                if rec["seq"] > new_upto or rec["kind"] != "accept":
                    continue
                if rec.get("work") not in moved or rec["command"] in live_commands:
                    continue
                commands.add(rec["command"])
                rows.append({"k": "cmd", "key": rec["command"],
                             "row": {"attempt": rec.get("attempt"), "work": rec.get("work"),
                                     "count": int((state.get("attempts") or {}).get(rec["command"]) or 0)}})
            for event, row in (state.get("close_receipts") or {}).items():
                row = row or {}
                # r2520 DA#57 반례: 영수의 두 work(닫힌 쪽 · next)가 서로 «다른 회수 바퀴» 에 장부로 가도
                # 영수는 빠져야 한다 — 이번 바퀴 moved 만 보면 한 바퀴에 둘 다 안 오는 영수가 영구 잔류했다.
                if not self._archived(row.get("work"), moved) or not self._archived(row.get("next"), moved):
                    continue                                # 닫힌 쪽·next 중 하나라도 아직 살아 있으면 영수도 살아 있다
                events.add(event)
                rows.append({"k": "event", "key": event, "row": dict(row)})
            for attempt, row in (state.get("withdrawn") or {}).items():
                command = (row or {}).get("command")
                if attempt in live_attempts or command in live_commands:
                    continue
                if command not in commands and command in accept_commands:
                    continue                                # 열린 work 의 command = 철회 기록도 그대로
                rows.append({"k": "attempt", "key": attempt, "row": dict(row or {})})
            for key, row in (state.get("imported") or {}).items():
                seq = (row or {}).get("seq")
                if not isinstance(seq, int) or seq > new_upto:
                    continue
                rows.append({"k": "import", "key": key, "row": dict(row or {})})
        drop = {"close_receipts": {event for event in events},
                "imported": {row["key"] for row in rows if row["k"] == "import"},
                "withdrawn": {row["key"] for row in rows if row["k"] == "attempt"}}
        out = dict(state)
        for name in CLOSED_WORK_FIELDS:
            if moved:
                out[name] = {key: value for key, value in (state.get(name) or {}).items() if key not in moved}
        if events:
            out["done"] = {key: value for key, value in (out.get("done") or {}).items()
                           if not (key.startswith("close:") and key.split(":", 2)[-1] in events)}
        out["close_receipts"] = {key: value for key, value in (state.get("close_receipts") or {}).items()
                                 if key not in drop["close_receipts"]}
        out["imported"] = {key: value for key, value in (state.get("imported") or {}).items()
                           if key not in drop["imported"]}
        out["withdrawn"] = {key: value for key, value in (state.get("withdrawn") or {}).items()
                            if key not in drop["withdrawn"]}
        if commands:
            out["pending"] = [cmd for cmd in state.get("pending") or [] if cmd not in commands]
            out["attempts"] = {cmd: count for cmd, count in (state.get("attempts") or {}).items()
                               if cmd not in commands}
        base = dict(state.get("journal_base") or {})
        if base:
            proj = {}
            for name in PROJ_FIELDS:
                gone = moved if name in CLOSED_WORK_FIELDS else drop.get(name) or set()
                proj[name] = {key: value for key, value in ((base.get("proj") or {}).get(name) or {}).items()
                              if key not in gone}
            base = dict(base, proj=proj,
                        receipts={cmd: att for cmd, att in (base.get("receipts") or {}).items()
                                  if cmd not in commands})
            if rows:                                   # «닫힌 장부 있음 · 끝 seq» 만 — 색인 0(㉮)
                base["closed"] = {"upto": new_upto}
            out["journal_base"] = base
        return rows, out, sum(_closed_row_bytes(row) for row in rows)

    def _segment_closed(self, seg, records, state):
        """그 segment 의 모든 줄이 «닫힌 work» — work 없는 줄(accept work=None)은 늘 열림(보존).
        r1774 R1: import 줄은 닫힌 줄이다(내용 전부가 imported 에 접히고 PROJ_FIELDS 로 남는다).
        r2068: str 아닌 work(Slack 접수 dict)도 work 없는 줄 = 열림.
        r1925b R1: 철회된 attempt 의 accept·withdraw 줄은 닫힌 줄이다(work 는 done 으로 만들지 않는다)."""
        seg = self._kept(seg, state)
        return all(work is not None and self._work_closed(work, records, state)
                   for work in {rec.get("work") if isinstance(rec.get("work"), str) else None for rec in seg
                                if rec["kind"] != "import"})

    def _kept(self, seg, state):
        """철회된 attempt 의 accept·withdraw 줄은 닫힌 줄 — 닫힘 판정과 막힘 이름이 같은 제외를 쓴다(r1925b R1 · r2518 정정1)."""
        withdrawn = state.get("withdrawn") or {}
        return [rec for rec in seg if not (rec["kind"] in ("accept", "withdraw") and rec["attempt"] in withdrawn)]

    def _blocking(self, seg, records, state):
        """r2518 K4 — 이 segment 를 못 닫는 work 이름 → 사유. 회수 0 의 이유가 글에 보인다."""
        out = {}
        names = {rec.get("work") if isinstance(rec.get("work"), str) else None
                 for rec in self._kept(seg, state) if rec["kind"] != "import"}
        for work in sorted(names, key=lambda name: (name is None, name or "")):
            why = "work 없음" if work is None else self._closed_why(work, records, state)
            if why:
                out["-" if work is None else work] = why
        return out

    def _work_closed(self, work, records, state):
        """done + (required 면 reassess_done) + owners·uncertain 없음 + 마지막 result·complete 뒤 start·effect 없음
        + dispatch 의도가 deliver 로 닫힘 (DA R1 ④ · r2518 K2)."""
        return not self._closed_why(work, records, state)

    def _closed_why(self, work, records, state):
        return self._closed_why_rows(work, [rec for rec in records if rec.get("work") == work], state)

    def _closed_why_rows(self, work, rows, state):
        """닫힘 5가드 — 닫혔으면 "" · 아니면 첫 사유(r2518 K4 가 이름과 함께 올린다).

        r2518 K2: 끝 줄 = result 뿐 아니라 complete 도 센다 — start 뒤 complete 로 끝난 work
        (result 없이 닫힌 work)는 지금까지 «열림» 으로 남아 조각을 영영 막았다.
        r2520: state 에서 뺐 뒤에는 닫힌 장부가 닫힘 근거다(state 우선 · 장부는 없을 때만)."""
        done = (state.get("done") or {}).get(work)
        closed = {}
        if done is None:
            closed = self.ledger.work(work) or {}
            done = closed.get("done")
        if done is None and work.startswith("close:"):   # r2520: 영수 키 done 은 장부의 event 줄이 근거다
            done = {"marker": ""} if self.ledger.event(work.split(":", 2)[-1]) is not None else None
        if done is None and work in (state.get("lifted") or {}):   # r1727 R2: 재개가 해제한 휴면 키 = 닫힘(close 줄만)
            return ""
        if done is None:
            return "done 없음"
        if work in (state.get("owners") or {}):
            return "owners 있음"
        if work in (state.get("uncertain") or {}):
            return "uncertain 있음"
        if (done or {}).get("marker") == "required" and work not in (state.get("reassess_done") or {}) \
                and "reassess_done" not in closed:
            return "reassess 미완"
        last = max([rec["seq"] for rec in rows if rec["kind"] in ("result", "complete")] or [0])
        if [rec for rec in rows if rec["kind"] in ("start", "effect") and rec["seq"] > last]:
            return "끝 뒤 start·effect"
        sent = {(rec.get("work"), rec.get("attempt")) for rec in rows if rec["kind"] == "deliver"}
        if not all((work, rec.get("attempt")) in sent for rec in rows if rec["kind"] == "dispatch"):
            return "dispatch 미전달"
        return ""

    def recover(self):
        """state.json.tmp 잔여(크래시) 복구 — 잠금 안에서 tmp 삭제 → recover_state checkpoint.
        복구 쓰기 합 ≤ 예약 · 내부 한계 안. 아니면 쓰기 0 · «용량 부족»(복구 필요 유지)."""
        lock = try_lock(self.lock_path)
        if lock is None:
            return {"result": "BUSY", "written": False, "reason": "writer.lock 점유"}
        try:
            state = self.rec.recover_state(self.rec.read_state_guarded(self.state_path), self.records())
            size = self.envelope_for(state)
            if size + ops_bytes(WRITER_OPS) > self.reserve_bytes or self.usage() + size > self._limit(True):
                return {"result": "용량 부족", "written": False, "revision": state["revision"]}
            self._unlink(os.path.join("tmp", "state.json.tmp"), "recover_unlink")
            self.envelope = None
            self.write_state(state)
            return {"result": "접수 성공", "written": True, "revision": state["revision"]}
        except self.rec.CorruptStateError as exc:
            return {"result": getattr(exc, "word", "복구 필요"), "written": False, "reason": str(exc)}
        finally:
            unlock(lock)
