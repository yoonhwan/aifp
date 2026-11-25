"""ft 2.0 keeper — r2055 settle() 한 길 (keeper.py 가 섞어 쓴다 · 설계 design/harness/DESIGN-r2055-seat-settle-one-path.md r8).

좌석마다 판정 1개 = LANDED(착지 끝) · PARKED(끝남 ∧ 남길 것 안전 → kill + core park) · WORKING(손 0) · UNKNOWN(kill 0 + [긴급]).
«일하나» 는 tmuxc 규칙을 같은 값으로 쓴다(UC12 CPU 문턱·간격 · pane_descendant_pids 깊이 8 · cmd_clean 셸 목록).
★CPU idle 단독은 유휴·닫기 근거 0★ — 유휴 = jsonl 무활동 ≥ 문턱 ∧ CPU idle 2회(셸만 남은 pane 은 CPU 무관).
문턱 = PARK_IDLE 600초(손잡이 FT2_PARK_IDLE_S 60~3600 · 3600 = 옛 동작 · r2596 오빠 11-24 «나노 닫힘 5분 > 10분») · 카드 착지 끝 좌석의 닫기 길만 DONE_IDLE 300초(설계 DESIGN-pA r4 · 계약 A1·A2).
★길 표식은 값이 아니라 인자다★(r2535 K2) — `landed=True` = 착지 좌석 닫기 길(미읽음 관문 · 안 닫힌 턴 = WORKING) · `landed=False` = park 길(막는 미읽음은 unsafe 몫).
★열린 턴의 시계는 따로★(r2535 K4 · r2539 K8) — 셞만 아님 ∧ 마지막 줄 stop 아님(None 포함)이면 park 길 시계가 TURN_OPEN_IDLE(= WAIT_S 600초 · 손잡이 FT2_TURN_WAIT_S 60~900)다(마지막 줄을 못 읽은 None 은 waiting-input 갈래에 들지 않는다).
좌석 앞 미읽음은 «닫힌 꼴 마감 쪽지» 만 빼고 나머지는 막는다(A5~A8).
정지(.fable-team/state/ALL_STOP.json · 판정 = 1.x `ft-all-stop.sh judge --json` 한 줄 · r2465) 중 = 판정·[긴급]·«예정» 줄만 · kill·park·깨움·fill 0.
★원장 대기 중의 launch-failed 는 [긴급] 을 미룬다★(r2572 K1~K7) — 배정 원장(state/card-assign/<카드>.json) state 가 waiting 인 카드의 «이미 쉼인» attempt 만 · 판정 줄은 남기고 꼬리에 «원장 대기(<원장 사유 20자>) — [긴급] 미룸» 을 붙인다 · 미룰 때 지문 날짜를 안 적어 풀린 첫 바퀴에 그날 미알림일 때만 1통.
"""
import datetime
import glob
import importlib.util
import json
import os
import re

PARK_IDLE, WAIT_S, DAY = 600, 600, 86400   # 유휴 문턱 10분(r2596 · 오빠 11-24 «나노 닫힘 5분 > 10분으로 늘리자» · 앞 값 300 = r2535 K1 · 손잡이 FT2_PARK_IDLE_S) · 질문 창 10분(r2539 K8 · 손잡이 FT2_TURN_WAIT_S 60~600)
PARK_MIN, PARK_MAX = 60, 3600               # K1 손잡이 범위 — 정수 60~3600 만 듣는다 · 그 밖·빈 값 = PARK_IDLE
SHARE_IDLE, ACCEPT_IDLE = 300, 300   # r2539 K7·H1 — 앞 값 3600·3600 → 5분(손잡이 FT2_SHARE_IDLE_S · FT2_ACCEPT_IDLE_S · 범위 60~600)
TURN_OPEN_IDLE = WAIT_S   # r2539 K8·H1 — 열린 턴의 닫기 시계 = 질문 창 한 값(손잡이 FT2_TURN_WAIT_S 60~600)
DONE_IDLE = 300                             # 카드 착지 끝 좌석의 짧은 유휴 문턱(설계 DESIGN-pA r4 §3 · 계약 A1)
ROLE_CELLS = ("_master", "_arch", "_desk")   # A6② 마감을 밝힐 수 있는 명부 역할 칸
CLOSED_MAIL = re.compile(r"^\[마감(?: #\d+)?\] 할 일 0(?: · 착지 [0-9a-f]{7,40})?$")   # A6① 닫힌 꼴 한 줄
LAUNCH_FAILED = "launch-failed"   # r2058 L3 — 끝 사유 낱말 · opening 멈춤 문턱 OPEN_STALE = 아래 keeper_launch 값(r2252 O0 한 값)
ASSIGN_WAIT = ("waiting",)   # r2572 K1 — 배정 원장(state/card-assign/<카드>.json) «대기» state 값(사유 = 정지·사람·선행·lint·DA·석·면제대기 모두 같은 «대기»)
CPU_IDLE, CPU_GAP, CPU_DEPTH = 0.3, 30, 8   # tmuxc UC12 %cpu < 0.3 · 표본 간격 ≥ 30초 · pane_descendant_pids 깊이 8
SAMPLE_KEEP = 600                           # r2284 C2 pane2 표본 장부 수명(잰 지 600초 안 = 남김 · 표본 수명이라 5분 기준 밖 · r2539)
CPU_SAMPLE_MAX = 3600                       # r2354 K1 cpu 표본 절대 수명 — 방문 간격과 무관하게 이보다 오래된 표본만 새로 잼
JUDGE_S = 7.0                                # r2465 K3 — 판정기 호출 상한 7초 · 재시도 0(사전 DA#58 · 카드 K3)
JUDGE_ENV = "FT2_ALL_STOP_JUDGE"            # r2465 — 판정기 자리 바꿔 끼우기(시험 대역 · 기본 = 닫기 도구(close_bin) 옆 ft-all-stop.sh)
SHELLS = ("zsh", "bash", "fish")            # tmuxc cmd_clean
KINDS = ("nano", "master", "arch", "da", "desk", "tester", "pm", "qa", "orch", "temp")   # S1 명부 role 칸 = 좌석 종류 낱말
BUSY = re.compile("Working|[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]")
NAME = re.compile(r"biz-[a-z0-9]+(?:-[A-Za-z0-9._]+)+#\d+")
NEXT = {"waiting-input": "팀장이 질문 창에 답", "dirty": "나노에게 커밋·push 요청", "unpushed": "나노에게 push 요청",
        "shell-only-unsafe": "워크트리 확인 뒤 손 정리", "owner-orphan": "owner·intent 대조 뒤 손 park",
        "session-absent": "산출 가지 확인 → 인수 또는 반환",   # r2069 A1 — 산출 push·result 뒤 닫힌 좌석 꼴
        LAUNCH_FAILED: "원인 고친 뒤 원장 갱신 → fill 재시도 · 필요 없으면 return 또는 카드 끝 표식",
        "accept-only": "거두기(r1925 길) 또는 배정", "roster-outside": "명부 등록 또는 손 정리", "name-bad": "세션 이름 확인",
        "tmuxc-mismatch": "tmuxc·settle 판정 대조"}


HERE = os.path.dirname(os.path.abspath(__file__))
FT2 = os.path.dirname(os.path.dirname(HERE))


def _load(path, alias):
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cli = _load(os.path.join(FT2, "core", "cli.py"), "ft2_keeper_settle_cli")
PROJ = cli._load("projection")
endings = _load(os.path.join(HERE, "keeper_endings.py"), "ft2_keeper_settle_endings")
roster = _load(os.path.join(HERE, "launch_roster.py"), "ft2_keeper_settle_roster")   # A6② 명부 경로 = 행 E 한 함수
note = _load(os.path.join(HERE, "keeper_park_note.py"), "ft2_keeper_settle_park_note")   # r2535 K6 쪽지 + K7 재개 세기
kl = _load(os.path.join(HERE, "keeper_launch.py"), "ft2_keeper_settle_launch")   # r2252 O0 이어 열기 한 판정(launching 과 같은 함수)
OPEN_STALE = kl.OPEN_STALE   # r2058 L6 opening 멈춤 문턱 = r2252 O0 이어 열기 문턱(한 값 · r2539 K6 600초 · 손잡이 FT2_OPEN_STALE_S 60~900)


def park_idle(env):
    """K1 손잡이 — FT2_PARK_IDLE_S 정수 60~3600 만 듣는다 · 그 밖·빈 값 = PARK_IDLE(600) · 3600 을 주면 옛 동작."""
    try:
        got = int(str((env or {}).get("FT2_PARK_IDLE_S", "")).strip())
    except (AttributeError, TypeError, ValueError):
        return PARK_IDLE
    return got if PARK_MIN <= got <= PARK_MAX else PARK_IDLE


def descendants(rows, root, depth=CPU_DEPTH):
    """tmuxc pane_descendant_pids 와 같은 규칙 — root 부터 너비 우선 depth 단(root 포함)."""
    kids, out, level = {}, [], [root]
    for pid, ppid, _cpu, _cmd in rows:
        kids.setdefault(ppid, []).append(pid)
    for _ in range(depth):
        if not level:
            break
        out += level
        level = [kid for pid in level for kid in kids.get(pid, [])]
    return out


def long_seat(holder):
    """r2135 — holder 이름 역할 토큰(«biz-<팀>-» 뒤 첫 낱말 · close protected_ok 와 같은 셈)이 nano 아님 = 장기 좌석 · holder 없음 = 아님(지금 길)."""
    return bool(holder) and not (holder.startswith("biz-") and (holder.split("-") + ["", ""])[2] == "nano")


def working(pane):
    """A13 pane 일함 근거 — 끝 12줄 · 입력줄(❯ · ›) 뒤 글자 = 근거 0(고스트) · Working · esc to interrupt · 스피너."""
    rows = [x for x in pane.rstrip("\n").splitlines()[-12:] if not x.lstrip().startswith(("❯", "›"))]
    return any(BUSY.search(x) or "esc to interrupt" in x for x in rows)


class Settling:
    parked_failed = frozenset()   # r2058 L1 — 이 팀·work·attempt 가 launch-failed 쉼인가(keeper.team_round 가 채운다)
    def alive_seats(self):
        """r2354 K1 «그 좌석 세션이 없어짐» 판독 — 바퀴 캐시 ls 칸(keeper_next.once · release_block 과 같은 칸 · 바퀴당 1회 · 표본별 호출 0).
        세션 이름 집합 · ls rc 1 ∧ «no server running» = 빈 집합 · 그 밖 rc≠0(tmux 실패) = None(판정 불가 = 지움 0)."""
        got = self.cache.setdefault("@round", {})
        if "ls" not in got:
            got["ls"] = self.call([self.tmux, "list-sessions", "-F", "#{session_name}"])
        rc, out, err = got["ls"]
        return set(out.split()) if rc == 0 else set() if "no server running" in err else None

    def fresh_samples(self):
        """바퀴 시작 표본 정리(1회) — cpu 표본은 좌석 판(alive_seats 대조 · pane_pid 는 cpu() 가 대조 · CPU_SAMPLE_MAX)으로만 지운다. pane2 는 지금대로 SAMPLE_KEEP.
        arch #308380 영구 pending 0 을 지키려고 600초 지움 → 방문 간격 > 600초 팀에서 거꾸로 영구 pending → 좌석 판 대조로 바꿈(r2354 K1)."""
        prev, self.state["round_at"] = self.state.get("round_at"), self.now()
        now = self.state["round_at"]
        alive = self.alive_seats()   # 바퀴 캐시 ls 1회(표본 수와 무관)
        dead = self.state.setdefault("cpu", {})
        for seat in [x for x, v in dead.items() if not isinstance(v, dict) or (alive is not None and x not in alive) or now - v.get("at", 0) > CPU_SAMPLE_MAX]:
            dead.pop(seat)
        book = self.state.setdefault("pane2", {})
        for seat in [x for x, v in book.items() if not isinstance(v, dict) or (prev is None or v.get("at", 0) < prev) and now - v.get("at", 0) > SAMPLE_KEEP]:
            book.pop(seat)

    def judge_path(self):
        """r2465 K3 — 판정기 자리 = FT2_ALL_STOP_JUDGE(시험·대체) 또는 닫기 도구(close_bin) 옆 ft-all-stop.sh.

        설치본 경로를 코드에 박지 않는다(legacy guard · 갈래는 gates() 의 «close_bin 옆 ft-*.sh» 와 같은 규칙).
        r2549 K1 — 둘 다 비면 빈 값 그대로(«ft-all-stop.sh» 상대 경로를 만들지 않는다 · 그 이름의 남의 파일을 부르지 않는다)."""
        return self.env.get(JUDGE_ENV) or (os.path.join(os.path.dirname(self.close_bin), "ft-all-stop.sh") if self.close_bin else "")

    def judge_doc(self):
        """r2465 K3 — 판정기 1회(7초 · 재시도 0) → (doc, "") 아니면 (None, 사유) · 상태 파일을 직접 읽지 않는다.

        r2549 K2 — 자리가 비면(FT2_ALL_STOP_JUDGE 도 close_bin 도 빔) 부르지 않고 (None, «판정기 자리 없음(FT_SEAT_CLOSE_BIN 빔)»).
        stopped() 는 지금 그대로 «판정 불가 = 정지» 로 답한다(데몬 길은 닫힌 쪽 그대로 · 줄 글자만 사유를 밝힌다)."""
        path = self.judge_path()
        if not path:
            return None, "판정기 자리 없음(FT_SEAT_CLOSE_BIN 빔)"
        rc, out, err = self.call(["bash", path, "judge", "--json"], timeout=JUDGE_S)
        if rc != 0:
            return None, "judge rc=%s%s" % (rc, "" if rc is not None else " · " + (err or "실행 실패")[:80])
        try:
            doc = json.loads(out.strip() or "")
        except ValueError:
            return None, "JSON 아님"
        if not isinstance(doc, dict) or doc.get("state") not in ("off", "stop", "hard"):
            return None, "state 모르는 값"
        return doc, ""

    def judge_note(self, why):
        """«판정 불가 … 정지로 봄» 1줄 — 값이 같으면 다음 바퀴 0줄(⑧) · 판정이 시원해지면 기억을 지운다."""
        prev = self.state.get("all_stop_bad")
        if not why:
            self.state.pop("all_stop_bad", None)
            return
        if prev == why:
            return
        self.state["all_stop_bad"] = why
        self.log("판정 불가", text="ALL_STOP 판정 불가(%s) — 정지로 봄" % why)

    def stopped(self):
        """r2465 K3 — keeper 는 바퀴마다 1회 `judge --json` 을 부른다(바퀴 캐시 · 팀 수와 무관).

        off = 진행 · stop = 정지(self.halt_clean 참 · except 에 든 팀은 제외 = self.stop_except) ·
        hard·호출 실패·JSON 아님·모르는 state = 전 팀 정지 + «판정 불가» 1줄(halt_clean 거짓 = 정지 중 닫기 0 · ⑮).
        r2421 K5 — 정상 정지 근거(self.halt_clean)는 state 가 stop 일 때만 참이다(깨짐·hard = 거짓)."""
        self.halt_clean, self.stop_except, self.stop_since = False, set(), None
        doc, why = self.judge_doc()
        if doc is None:
            self.judge_note(why)
            return True
        state = doc.get("state")
        if state == "off":
            self.judge_note("")
            return False
        self.judge_note("" if state == "stop" else "hard")
        if state != "stop":  # hard = 전 팀 정지 · halt_clean 은 거짓 그대로
            return True
        self.halt_clean = True
        self.stop_since = doc   # r2465 — 수동 닫기(r2419 since)가 이 값을 쓴다(상태 파일 직접 읽기 0)
        self.stop_except = {x for x in doc.get("except") or [] if isinstance(x, str) and x}
        return True

    def ps_rows(self):
        """[(pid, ppid, %cpu, comm)] 바퀴당 1회(ps 1번 · 7초) · 실패 = None."""
        got = self.cache.setdefault("@round", {})
        if "ps" not in got:
            rc, out, _ = self.call(["ps", "-A", "-o", "pid=,ppid=,pcpu=,comm="])
            rows = []
            for line in out.splitlines() if rc == 0 else ():
                cells = line.split(None, 3)
                try:
                    rows.append((int(cells[0]), int(cells[1]), float(cells[2]), cells[3] if len(cells) > 3 else ""))
                except (ValueError, IndexError):
                    continue
            got["ps"] = rows if rc == 0 else None
        return got["ps"]

    def pane_info(self, seat):
        """(pane_pid, pane_current_command) · 못 읽음 = None."""
        rc, out, _ = self.call([self.tmux, "display-message", "-p", "-t", "=" + seat + ":", "#{pane_pid}\t#{pane_current_command}"])
        pid, tab, cmd = out.strip().partition("\t")
        return (int(pid), cmd) if rc == 0 and tab and pid.isdigit() else None

    def cpu(self, seat, info):
        """busy | idle(표본 2개 이상 · 간격 ≥ 30초 · 모두 < 0.3) | pending | unknown — 바퀴당 표본 1개 · 직전 표본 = state.cpu."""
        rows = self.ps_rows() if info else None
        if rows is None:
            return "unknown"
        mine, pid = set(descendants(rows, info[0])), info[0]   # r2354 K1 표본마다 pane_pid 를 적는다(표본별 tmux 0 · DA#45 H1)
        load, book, now = sum(c for _pid, _pp, c, _cmd in rows if _pid in mine), self.state.setdefault("cpu", {}), self.now()
        if load >= CPU_IDLE:
            book[seat] = {"at": now, "cpu": load, "pane_pid": pid}
            return "busy"
        prev = book.get(seat) or {}
        same = prev.get("pane_pid") == pid   # pane_pid 칸 없는 옛 표본 = 다른 판(첫 표본부터 · r2354 K1)
        first = prev.get("first", prev.get("at")) if same and prev.get("cpu", CPU_IDLE) < CPU_IDLE else None
        book[seat] = {"at": now, "cpu": load, "first": now if first is None else first, "pane_pid": pid}
        return "idle" if first is not None and now - first >= CPU_GAP else "pending"

    def pi_turn(self, intent):
        """(jsonl 무활동 초, 마지막 줄 stopReason) · 파일 없음 = (None, None).
        r2135 L1 — 장기 좌석 holder = 좌석 jsonl(seat_log) 한 파일에서 나이·마지막 줄 · 나노 = 일 worktree 폴더(지금 길)."""
        holder = intent.get("FT2_HOLDER") or ""
        if long_seat(holder):   # r2135 L1
            newest = self.seat_log(holder)
            if not newest:
                return None, None
            why = self.last_line(newest)
        else:
            why = self.pi_last_turn(intent)
            if why.startswith(("세션 파일 없음", "intent 시각 없음")):
                return None, None
            sessions = self.env.get("FT2_PI_SESSIONS") or os.path.expanduser("~/.pi/agent/sessions")
            folder = os.path.join(sessions, "--%s--" % (intent.get("worktree") or "").strip("/").replace("/", "-"))
            newest = max((os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".jsonl")), key=os.path.getmtime)
        stop = "stop" if not why else why.rpartition("/")[2] if why.startswith("마지막 줄") else None
        return self.now() - os.path.getmtime(newest), stop

    def with_why(self, tail, work):
        why = getattr(self, "why", "") if work != "-" else ""
        return tail if not why or why in tail else " · ".join(x for x in (tail, why) if x)

    def verdict(self, team, work, seat, word, code, tail=""):
        """판정 1줄 — 같은 좌석·같은 (판정, 사유) 반복 로그 0 · UNKNOWN 은 바퀴마다 셈(ROUND unknown=N)."""
        self.unknown += word == "UNKNOWN"
        tail = self.with_why(tail, work)   # 착지 판정 사유 = 꼬리 끝
        two = self.cache.get("@round", {}).get("two", {}).get(seat)   # A13 2차로 내려간 좌석
        tail = " · ".join(x for x in (tail, two) if x) if two and two not in tail else tail
        key, book = "%s|%s|%s" % (team, work, seat), self.state.setdefault("verdict", {})
        if book.get(key) != [word, code]:
            book[key] = [word, code]
            self.log(word, team, " ".join(x for x in (work, seat, code) if x) + (" · " + tail if tail else ""))
        return word

    def alert(self, team, work, attempt, seat, code, tail=""):
        tail = self.with_why(tail, work)
        """UNKNOWN [긴급] 1통 — 지문 (team, work, attempt, reason) 하루 1회 · 새 사유·새 attempt = 즉시 · 전송 실패도 그날 지문(r2065 E3·E4 · 재시도 0 · 상한 밖이면 다음 바퀴)."""
        sig, day = "%s|%s|%s|%s" % (team, work, attempt, code), self.stamp()[:10]
        book = self.state.setdefault("alerts", {})
        if book.get(sig) == day:
            return
        body = "[긴급] UNKNOWN %s %s %s %s%s · 다음 수 %s" % (team, work, seat, code, " · " + tail[:80] if tail else "", NEXT.get(code, "판독 확인"))
        if self.notify(team, "unknown|%s|%s" % (day, sig), body):
            book[sig] = day

    def unknown_seat(self, team, work, attempt, seat, code, tail=""):
        self.verdict(team, work, seat, "UNKNOWN", code, tail)
        self.alert(team, work, attempt, seat, code, tail)
        return "UNKNOWN"

    def unknown_line(self, team, work, code, text):
        """좌석 칸 없는 UNKNOWN 줄(옛 HELD 자리 · 호출자가 같은 사유 반복을 거름) + [긴급] 1통(지문 하루 1회) · ROUND unknown 셈."""
        self.unknown += 1
        self.log("UNKNOWN", team, text)
        self.alert(team, work, "-", "-", code, text)

    def settle_nano(self, team, work, attempt, holder, row, why):
        """착지 판정 밖 나노 1석 → 판정 1개(LANDED 는 호출자 몫) · why = 착지 판정 사유(모든 판정 줄 꼬리 끝에 남김).
        r2058 — launch-failed 끝 = 쉼 + 판정 UNKNOWN(흐름만 PARKED) · opening 멈춤(OPEN_STALE 넘음 ∧ 잇는 중 아님 ∧ owner 남음) = 같은 길."""
        self.why = why or ""
        done, owner = bool(row.get("done")), row.get("owner")
        raw = self.read_json(os.path.join(PROJ.runtime_path(self.root, team), "launch", "%s@%s.intent" % (work, attempt)))
        seen = self.probe(holder)
        key = "%s|%s|%s|%s" % (team, work, attempt, holder)   # r2214 O1a 처음 absent 본 시각 키(attempt 포함 = 새 attempt 는 다시 셈)
        first = self.state.setdefault("absent_since", {}).pop(key, None)   # session-absent 갈래 밖 바퀴 = 지움
        opening = bool(owner) and raw.get("state") == "opening"   # L6 — 여는 중인 열기(잇는 중·문턱 안쪽 = 손 0)
        stalled = opening and self.opening_stale(raw) and not self.launching_now(team, work)
        if seen == "absent":
            if done:
                return self.verdict(team, work, holder, "PARKED", "session-absent", why)
            if (team, work, attempt) in self.parked_failed:   # L1·L3 이미 launch-failed 쉼 = 같은 판정 유지 · park 다시 0
                return self.failed_end(team, work, attempt, holder, raw, why, park=False)
            if owner and raw.get("state") in ("failed", "closed"):   # 반쪽(r1968·r1973 꼴) = 세션 0 · owner 남음
                wait = self.resume_wait(team, work, attempt, raw)   # r2252 O3 이어 열기 자리 = 쉼 미룸
                if wait:
                    return self.verdict(team, work, holder, "WORKING", wait, self.failed_tail(raw))
                return self.failed_end(team, work, attempt, holder, raw, why, park=True)
            if stalled:   # L6 — 여는 중에 멈춘 열기(세션 부재 = rc1 «can't find session» 로 확인) = L3 과 같은 길
                return self.failed_end(team, work, attempt, holder, raw, why, park=True)
            if opening:   # L6 — 문턱 안쪽·잇는 중 열기 = 손 0 · [긴급] 0(아직 판정할 수 없다)
                return self.verdict(team, work, holder, "WORKING", "launch-joining" if self.launching_now(team, work) else "launch-pending", "opening %d분" % self.opening_age(raw))
            if owner and not raw and self.launch_waiting(team, work, attempt):   # r2366 미룬 열기(같은 리포 열기 1개) = 손 0
                wait = self.launch_wait(key, first)
                if wait:
                    return self.verdict(team, work, holder, "WORKING", wait, "열기 미룸 · fill_open 같은 attempt")
            word = self.unknown_seat(team, work, attempt, holder, "owner-orphan" if owner else "session-absent", why)
            if not owner:   # r2214 session-absent 만(owner-orphan = 팀장 park 몸)
                self.absent_release(team, work, holder, key, first)
            return word
        if seen != "alive":
            if stalled:   # L6 — tmux 조회 실패 = «부재» 가 아니다(판정 불가 1줄 · park 0)
                return self.log("판정 불가", team, "%s %s opening %d분 좌석 판독 불가 %s — park 0" % (work, holder, self.opening_age(raw), seen))
            return self.unknown_seat(team, work, attempt, holder, "tmux-error", seen)
        intent = endings.intent(self, team, work, attempt, holder)
        if not intent.get("worktree") or not os.path.isdir(intent["worktree"]):   # 새 꼴(worktree 칸 없음·폴더 없음)
            return self.unknown_seat(team, work, attempt, holder, "intent-bad", "worktree %r" % intent.get("worktree"))
        return self.settle_alive(team, work, attempt, holder, intent, done, why)

    def park(self):
        """K1 손잡이 값 — FT2_PARK_IDLE_S(정수 60~3600) · 그 밖·빈 값 = PARK_IDLE(600) · 3600 = 옛 동작 · 바퀴당 1회."""
        book = self.cache.setdefault("@round", {})
        if "park" not in book:
            book["park"] = park_idle(self.env)
        return book["park"]

    def look(self, team, work, attempt, holder, age, stop, wait="jsonl-active", idle_s=None, landed=False, short=None):
        """A13 한 판독(설계 §13) → "REST"(쉼 · 닫기 판독 통과) 또는 판정 낱말(줄은 여기서 냄) — 모든 닫기 길 공용.
        1차 = tmuxc clean(shell-only) + CPU(후손 pid) + jsonl 나이 · pane 글자 0 · 2차(pane 끝 12줄) = 그 좌석 1차를 못 세운 때만.
        판독 실패 = WORKING 아님(probe-fail · session-none = UNKNOWN [긴급]) · age·stop = jsonl 무활동 초·마지막 줄(파일 없음 = None).
        idle_s = 유휴 문턱(PARK_IDLE 600초 기본 · 착지 좌석만 DONE_IDLE 300초 · A2). 짧은 문턱은 «막는 미읽음 0» 도 함께 본다(A1).
        r2535 K2 — «길» 은 값(idle_s)이 아니라 인자로 받는다 · landed=True = 착지 좌석 닫기 길(열린 턴도 WORKING) ·
        short = 짧은 문턱 길(미읽음 관문을 본다 · `--rows` 먼저) 이고 기본 = landed · r2509 긴급 쉼 길은 short=True 만 준다."""
        idle_s = self.park() if idle_s is None else idle_s
        short = landed if short is None else short
        status, info = self.tmuxc_status(holder), self.pane_info(holder)
        shell = status == "shell"   # 1차 성립 = clean rc0 ∧ raw pane_pid ∧ ps ∧ 세션 파일(clean 은 list-panes 실패를 rc0 빈 출력으로 삼킴 · arch #308361)
        miss = "tmuxc 없음·실패" if status is None else "pane_pid 판독 실패" if info is None else "ps 판독 실패" if self.ps_rows() is None else ""
        miss = miss or ("세션 파일 없음" if age is None else "")
        self.cache.setdefault("@round", {}).setdefault("first", {})[holder] = not miss   # kill 직전 가드가 tmuxc-mismatch 를 가름
        if miss:
            pane = self.pane2(holder)
            two = " · 판독 2차(%s)" % miss
            if pane is None:
                return self.unknown_seat(team, work, attempt, holder, "probe-fail", "1차 %s · capture 실패" % miss)
            if pane == "busy":
                return self.verdict(team, work, holder, "WORKING", "pane-working", "Working" + two)
            if age is None:   # 닫기에 필요한 jsonl 무활동을 못 잼
                return self.unknown_seat(team, work, attempt, holder, "session-none", "pi 세션 파일 없음" + two)
            if pane == "pending":
                return self.verdict(team, work, holder, "WORKING", "pane-pending", "쉼 표본 1개" + two)
            cpu = "idle"   # 2차 쉼 ×2 = CPU idle ×2 자리
            self.cache["@round"].setdefault("two", {})[holder] = two[3:]   # 닫기 판정 줄 꼬리 «판독 2차(<사유>)»(verdict 가 붙임)
        else:
            cpu = "unknown" if shell else self.cpu(holder, info)
        if cpu == "busy":
            return self.verdict(team, work, holder, "WORKING", "cpu-busy")
        open_turn = not shell and stop != "stop"   # 열린 턴 = 셞만 아님 ∧ 마지막 줄 stop 아님(None 포함 · r2535 K4)
        if open_turn and not landed:   # K4 — 열린 턴의 park 시계는 TURN_OPEN_IDLE(= WAIT_S 600초 · r2539 K8)
            turn_s = self.wait("FT2_TURN_WAIT_S", TURN_OPEN_IDLE, 600)   # 한 값 = 질문 창 과 닫기 시계
            if stop is not None and age is not None and age >= turn_s and cpu == "idle":   # 질문 창 · None 은 이 갈래에 들지 않는다(DA#59 H1)
                return self.unknown_seat(team, work, attempt, holder, "waiting-input", "마지막 줄 %s · 무활동 %d분" % (stop, age // 60))
            idle_s = turn_s
        idle = age is not None and age >= idle_s and (shell or cpu == "idle")   # CPU 단독 = 근거 0
        if not idle:
            return self.verdict(team, work, holder, "WORKING", wait if age is None or age < idle_s else "cpu-" + cpu)
        if open_turn:
            if landed:   # A1 — 착지 좌석의 안 닫힌 턴 = 아직 일하는 중(문턱이 짧을 뿐 · ㉙나)
                return self.verdict(team, work, holder, "WORKING", wait, "마지막 줄 %s" % stop)
            return self.unknown_seat(team, work, attempt, holder, "turn-open", "마지막 줄 %s" % stop)
        code = self.mail_gate(team, work, holder, idle_s, short=short) if short else ""   # A1·A5~A8 — 짧은 문턱 길(착지 · 긴급 쉼)은 «막는 미읽음 0» 도 본다
        if code:   # r2535 — 사유 재조회도 같은 길 표식으로(인자 빠지면 다른 길로 다시 읽어 판정 줄이 흔들린다)
            return self.unknown_seat(team, work, attempt, holder, code, "미읽음 판독 --rows")
        self.cache["@round"].setdefault("shell", {})[holder] = shell
        return "REST"

    def seat_path(self, seat):
        """tmux #{session_path} · 바퀴당 좌석 1회 · 못 읽음 = ""."""
        book = self.cache.setdefault("@round", {}).setdefault("spath", {})
        if seat not in book:
            rc, out, _ = self.call([self.tmux, "display-message", "-p", "-t", "=" + seat + ":", "#{session_path}"])
            book[seat] = out.strip() if rc == 0 and out.strip().startswith("/") else ""
        return book[seat]

    def seat_born(self, seat):
        """tmux #{session_created}(좌석 시작 epoch 초) · 못 읽음 = None."""
        rc, out, _ = self.call([self.tmux, "display-message", "-p", "-t", "=" + seat + ":", "#{session_created}"])
        return float(out.strip()) if rc == 0 and out.strip().isdigit() else None

    def seat_turn(self, seat):
        """장기 좌석(intent 없음) jsonl 나이(arch #308361 Q1) · 마지막 줄 판독 0(stop 으로 봄) · 못 정함 = (None, None) → 한 판독 2차·session-none.
        ① 재개 기록 seat-resume/<세션명>.json 의 jsonl 칸(파일 실재할 때만 · mtime = 나이)
        ② 없으면 session_path 의 pi(`--<cwd>--`)·claude(projects/<cwd `/`·`.` → `-`>) 폴더 최신 *.jsonl = 상한 — 무활동 ≥ PARK_IDLE = 그 나이 ·
        더 최근 ∧ 같은 session_path 에 살아 있는 biz 세션 2개 이상 = 누구 것인지 못 가름(None) · 혼자 쓰는 폴더 = 그 나이 · jsonl 0 = None."""
        log = self.seat_log(seat)
        return (self.now() - os.path.getmtime(log), "stop") if log else (None, None)

    def seat_log(self, seat):
        """seat_turn 의 jsonl 1개(경로) · 못 정함 = None — 규칙 = seat_turn 독스트링 ①② 그대로(r2135 L1 가 같은 파일로 나이·마지막 줄을 읽음)."""
        home = self.env.get("HOME") or os.path.expanduser("~")
        doc = self.read_json(os.path.join(self.env.get("FT2_SEAT_RESUME_DIR") or os.path.join(home, ".claude", "state", "seat-resume"), seat + ".json"))
        log = str(doc.get("jsonl") or "") if isinstance(doc, dict) else ""
        if log and os.path.isfile(log) and self.resume_ok(seat):   # R2 검증을 통과한 기록만(칸이 있다는 것만으로 0)
            return log
        cwd, born = self.seat_path(seat), self.seat_born(seat)
        if not cwd or born is None:
            return None
        pi = self.env.get("FT2_PI_SESSIONS") or os.path.join(home, ".pi", "agent", "sessions")
        claude = self.env.get("FT2_CLAUDE_PROJECTS") or os.path.join(home, ".claude", "projects")
        files = glob.glob(os.path.join(pi, "--%s--" % cwd.strip("/").replace("/", "-"), "*.jsonl")) + glob.glob(os.path.join(claude, re.sub(r"[/.]", "-", cwd), "*.jsonl"))
        times = {f: t for f, t in zip(files, map(os.path.getmtime, files)) if t >= born}   # 좌석 시작(session_created) 뒤에 쓰인 jsonl 만
        if not times:
            return None
        log = max(times, key=times.get)
        if self.now() - times[log] < self.wait("FT2_SHARE_IDLE_S", SHARE_IDLE, 600) and sum(1 for x in self.alive_sessions() if x.startswith("biz-") and self.seat_path(x) == cwd) >= 2:
            return None
        return log

    def pane2(self, holder):
        """2차 판독 — capture-pane 끝 12줄(입력줄 ❯·› 뒤 글자 = 근거 0) Working·esc to interrupt·스피너 = busy · 없음 표본 2개(간격 ≥ 30초) = rest · 1개 = pending · capture 실패 = None."""
        rc, pane, _ = self.call([self.tmux, "capture-pane", "-p", "-t", "=" + holder + ":"])
        if rc != 0:
            return None
        book, now = self.state.setdefault("pane2", {}), self.now()
        if working(pane):
            book.pop(holder, None)
            return "busy"
        first = book.setdefault(holder, {"first": now})["first"]
        book[holder]["at"] = now
        return "rest" if now - first >= CPU_GAP else "pending"

    def opening_age(self, intent):
        """L6 — intent at 부터 지난 분(못 읽음 = 0)."""
        try:
            return max(int((self.now() - datetime.datetime.strptime(str(intent.get("at")), "%Y-%m-%dT%H:%M:%S").timestamp()) // 60), 0)
        except ValueError:
            return 0

    def opening_stale(self, intent):
        """L6 — intent at(로컬 naive) 부터 OPEN_STALE 초 넘음 · 시각 못 읽음 = 거짓(손 0) · r2539 K12 손잡이."""
        try:
            return self.now() - datetime.datetime.strptime(str(intent.get("at")), "%Y-%m-%dT%H:%M:%S").timestamp() >= self.wait("FT2_OPEN_STALE_S", OPEN_STALE, 600)
        except ValueError:
            return False

    def absent_release(self, team, work, holder, key, first):
        """r2214 O1·O2·O4·O5 — session-absent(owner·done 없음)이 OPEN_STALE 넘게 이어지면 1.x 배정 원장 seat 를 1회 푼다 → 다음 fill 새 attempt.
        상태 칸 absent_since{팀|work|attempt|holder: 초}(verdict 책과 같은 keeper 상태 파일 = 재기동 뒤 이어짐) · absent_unsure{팀|work|holder: 사유}."""
        now = self.now()
        first = self.state["absent_since"][key] = now if first is None else first   # O1a 첫 absent 바퀴 = 시각만
        if now - first < self.wait("FT2_OPEN_STALE_S", OPEN_STALE, 600):   # r2539 K6·K12 손잡이
            return
        if self.halt:   # r2214 O3 정지 중 풀기 0(call 그물은 bash 를 막지 않음 · 시각은 그대로)
            return
        led = self.assign_ledger(work)
        if led.get("state") != "seat" or led.get("seat") != holder:   # O1d·O4 다른 좌석·풀린 원장 = 손 0
            return
        why = self.release_block(holder)
        if not why:   # O2 원장 도구 1회(fill 과 같은 경로 · 7초 · 재시도 0)
            rc, _, _ = self.call(["bash", self.env.get("FT2_CARD_ASSIGN_BIN") or os.path.join(os.path.dirname(self.close_bin or ""), "ft-card-assign-watch.sh"),
                                  "record", work, "clear", "seat", "--seat", holder])
            why = "" if rc == 0 else "원장 풀기 rc %s" % rc
        book, mark = self.state.setdefault("absent_unsure", {}), "%s|%s|%s" % (team, work, holder)
        if not why:
            book.pop(mark, None)
            return self.log("RELEASED", team, "%s %s · 원장 풀림 · 다음 fill 새 attempt" % (work, holder))
        if book.get(mark) != why:   # O5 같은 사유 반복 줄 0
            book[mark] = why
            self.log("판정 불가", team, "%s %s 원장 풀기 0 · %s" % (work, holder, why))

    def release_block(self, holder):
        """r2214 O1b·O1c — 풀기 앞 tmux 확인 · "" = 풀어도 됨 · 그 밖 = 판정 불가 사유(probe 반환 꼴은 그대로 · err 는 여기서 가름)."""
        rc, _, err = self.call([self.tmux, "has-session", "-t", "=" + holder])
        if rc != 1 or "can't find session" not in err:   # O1b 서버 없음·소켓 어긋남 = 한꺼번에 풀림 막음
            return "tmux 서버 없음" if "no server running" in err else "tmux has-session rc %s %s" % (rc, err)
        got = self.cache.setdefault("@round", {})   # keeper_next.once 와 같은 바퀴 캐시 칸(ls)
        rc, out, _ = got["ls"] if "ls" in got else got.setdefault("ls", self.call([self.tmux, "list-sessions", "-F", "#{session_name}"]))
        if rc != 0:
            return "tmux list-sessions rc %s" % rc
        other = next((x for x in out.splitlines() if x != holder and x.casefold() == holder.casefold()), "")   # O1c r2208 대문자 stem 꼴
        return "대소문자만 다른 세션 %s" % other if other else ""

    def resume_wait(self, team, work, attempt, intent):
        """r2252 O3 — keeper_launch.resume_state(launching 과 한 판정) → "" = 지금 길(failed_end) · launch-resumable · launch-resuming(예약 pid 살아 있음 = 900초 검사 0).
        정지 중 = ""(failed_end 의 «예정» 줄 그대로 · ⑩) · 예약 pid 죽음 = ""(1회 소진 · r2058 L3)."""
        if self.halt:
            return ""
        seen = kl.resume_state(self, os.path.join(PROJ.runtime_path(self.root, team), "launch", "%s@%s" % (work, attempt)), intent)
        return "launch-" + seen if seen else ""

    def launching_now(self, team, work):
        """L6 — fill_open(잇는 중)에 있는 열기인가(그 열기는 손 0)."""
        return ("%s|%s" % (team, work)) in (self.state.get("fill_open") or {})

    def launch_waiting(self, team, work, attempt):
        """r2366 K2 — 그 열기가 지금 attempt 로 fill_open 에 남았나(keeper_next.fill 이 띄운 열기 · handled 되면 빠진다).
        다른 attempt·없음 = 지금 그대로 owner-orphan(새 attempt 는 다시 센다)."""
        return (self.state.get("fill_open") or {}).get("%s|%s" % (team, work)) == attempt

    def launch_wait(self, key, first):
        """r2366 K1·K1b — keeper 가 띄우기를 다음 바퀴로 미룬 열기 = 첫 absent 시각을 남기고(settle_nano 221행 pop 탓 · 안 넣으면
        바퀴마다 첫 바퀴) OPEN_STALE 안이면 «launch-wait» · 넘으면 "" = 지금 그대로 owner-orphan(늦게 울림 · 안 울림 0)."""
        now = self.now()
        first = self.state.setdefault("absent_since", {})[key] = now if first is None else first
        return "launch-wait" if now - first < self.wait("FT2_OPEN_STALE_S", OPEN_STALE, 600) else ""

    def failed_tail(self, intent):
        """L3·L6 판정 줄 꼬리 — intent step · reason 앞 80자 / opening <분>분."""
        if intent.get("state") == "opening":
            return "opening %d분" % self.opening_age(intent)
        return "%s · %s" % (intent.get("step") or "-", str(intent.get("reason") or "-")[:80])

    def assign_ledger(self, work):
        """r2572 K2 — 배정 원장 한 장(state/card-assign/<카드>.json)을 읽는 한 길 — absent_release 와 ledger_wait 이 같이 쓴다(경로 조립 사본 0).
        못 읽음·깨짐 = 빈 dict(부르는 쪽이 «대기 아님» 으로 가른다)."""
        return self.read_json(os.path.join(self.root, ".fable-team", "state", "card-assign", (work or "-") + ".json"))

    def ledger_wait(self, work):
        """r2572 K1·K5 — 배정 원장이 «대기»로 적어 둔 카드인가(카드 이름 = work = 원장 파일 이름).
        대기면 그 사유(줄바꿈·연속 공백 1칸 · 20자) · 아니면 "" = 지금 길([긴급] 그대로 · K5 · 판독 실패를 대기로 보지 않는다)."""
        doc = self.assign_ledger(work)
        if doc.get("state") not in ASSIGN_WAIT:
            return ""
        why = " ".join(str(doc.get("reason") or "-").split())[:20].strip()
        return why or "-"

    def failed_end(self, team, work, attempt, holder, intent, why, park):
        """r2058 L3·L4·L6 — launch-failed 끝 = 쉼 1회(멱등) + 판정 UNKNOWN 1개 · «PARKED … launch-failed» 줄 0.
        흐름 표시는 «PARKED» = L4(그 work 에 stall 깨움·재배정·hold 검사 0) · [긴급] 지문 = (team·work·attempt·launch-failed) 하루 1회.
        r2572 K2·K3·K4 — 이미 launch-failed 쉼인 attempt(park=False)의 [긴급] 은 배정 원장 «대기»인 바퀴에 미룬다(판정 줄은 남기고 꼬리에 «원장 대기(<사유 20자>) — [긴급] 미룸» · 지문 장부에 날짜 0).
        풀린 바퀴에 그날 아직 안 알렸으면 1통 · 그날 이미 알렸으면 0통(하루 1회 지문 우선). 처음 실패한 바퀴(park=True)는 원장과 무관하게 지금과 같다(K4)."""
        if self.halt:   # 정지 중 = kill·park 0 · «예정» 줄만
            return self.verdict(team, work, holder, "예정 PARKED", LAUNCH_FAILED, "정지 중 kill·park 0")
        if park:
            out, rc = cli.run(["park", "--work", work, "--attempt", attempt, "--reason", LAUNCH_FAILED, "--root", self.root, "--team", team])
            if rc != 0:
                return self.unknown_seat(team, work, attempt, holder, "park-refused", "%s %s" % (out.get("result"), str(out.get("reason", ""))[:60]))
        # r2572 K2·K3 — 원장 대기 중 = [긴급] 0 · 판정 줄은 «원장 대기(<사유>) — [긴급] 미룸» 꼬리와 함께 남는다 · 지문 날짜 0(풀린 바퀴에 1통)
        wait = "" if park else self.ledger_wait(work)
        if wait:
            self.verdict(team, work, holder, "UNKNOWN", LAUNCH_FAILED, "%s · 원장 대기(%s) — [긴급] 미룸" % (self.failed_tail(intent), wait))
            return "PARKED"
        self.unknown_seat(team, work, attempt, holder, LAUNCH_FAILED, self.failed_tail(intent))
        return "PARKED"

    def settle_alive(self, team, work, attempt, holder, intent, done, why):
        note.reopen(self, team, work, holder, intent)   # r2535 K7 — «자리 비움» 을 낸 좌석·카드가 다시 살아 있는 첫 바퀴에 1줄
        got = self.look(team, work, attempt, holder, *self.pi_turn(intent))
        if got != "REST":
            return got
        if long_seat(holder):   # r2135 L2 — 장기 좌석 = 쉼이어도 kill·park 0 · [긴급] 0(close protected_ok 꼴)
            return self.verdict(team, work, holder, "WORKING", "protected", "나노만 닫는다 · kill·park 0")
        shell = self.cache["@round"]["shell"][holder]
        bad = self.unsafe(team, work, holder, intent, done)
        if bad:
            return self.unknown_seat(team, work, attempt, holder, "shell-only-unsafe" if shell else bad, why)
        return self.park_seat(team, work, attempt, holder, "idle-done", ("shell-only · " if shell else "") + why, alive=True, done=done, intent=intent)

    def unsafe(self, team, work, seat, intent, done):
        """남길 것 안전 = 사유 "" · clean ∧ (HEAD = origin 같은 가지 ∨ base 위 커밋 0 ∨ HEAD 를 품은 origin 가지) ∧ 미수신 쪽지 0 ∧ 미확정·효과 표식 0."""
        tree = intent["worktree"]
        rc, out, _ = self.git(tree, "status", "--porcelain")
        if rc != 0 or out.strip():
            return "git-error" if rc != 0 else "dirty"
        branch = self.git(tree, "rev-parse", "--abbrev-ref", "HEAD")[1].strip()
        rc, heads, _ = self.git(tree, "rev-parse", "HEAD", "refs/remotes/origin/" + branch)
        if not (rc == 0 and len(set(heads.split())) == 1):
            base = str(intent.get("base_sha") or "")
            if not base or self.git(tree, "rev-list", "--count", base + "..HEAD")[:2] != (0, "0\n"):
                rc, held, _ = self.git_local(tree, "for-each-ref", "--count=1", "--contains", "HEAD", "refs/remotes/origin")   # r2260 O1 — HEAD 를 품은 origin 가지 1개 = 안전(detached · 로컬 ref 만 · fetch 0)
                if rc != 0 or not held.strip():
                    return "git-error" if rc != 0 else "unpushed"
        code = self.mail_gate(team, work, seat, self.park())   # A5~A8 — 미읽음 판독(빼는 마감 쪽지 밖은 막는다 · r2535 park 문턱 · park 길은 short=False)
        if code:
            return code
        ex = cli._load("dispatch").Dispatch(self.root, team).ex
        state, records = ex._state_records()
        hold = ex._hold(state, records, work, (state.get("generations") or {}).get(work, 0), rotation=True)
        return "uncertain" if hold is not None and not done else ""

    def close_senders(self, team):
        """A6② 마감을 밝힐 수 있는 좌석 = 그 팀 명부의 역할 칸(_master · _arch · _desk) 지금 값 · 바퀴당 1회 · 명부 못 읽음 = 빈 집합(막음)."""
        book = self.cache.setdefault("@round", {}).setdefault("senders", {})
        if team not in book:
            path = roster.roster_path(self.root, team)
            rows = self.read_json(path) if path else None
            book[team] = {rows[c] for c in ROLE_CELLS if isinstance(rows.get(c), str) and rows.get(c)} if isinstance(rows, dict) else set()
        return book[team]

    def closed_form(self, body):
        """A6① 닫힌 꼴 — `골좌표:` 줄과 빈 줄을 뺀 나머지가 정확히 1줄 · 그 줄 전체가 `[마감 #N] 할 일 0`(+ ` · 착지 <hex>` 하나).
        자유 글은 안 본다(DA r2·r3 반례 — 부분 문자열로는 «일이 없다» 를 확정할 수 없다)."""
        lines = [x.strip() for x in str(body or "").splitlines() if x.strip() and not x.strip().startswith("골좌표:")]
        return len(lines) == 1 and bool(CLOSED_MAIL.match(lines[0]))

    def mail_rows(self, seat, short=False):
        """A4·A5 peek 읽기(읽기만 · mark 0 · recv 0) — (pending, [쪽지 dict], 사유 "") · 사유 = mail-unknown.
        rows_first(=short) = `peek --rows` 한 번(짧은 문턱 길 · 새 mbox 전제) · 아니면 먼저 `peek` 으로 pending 만 보고 0 이 아니면 `--rows` 로 내용을 읽는다(옛 mbox 호환).
        줄 0 ∧ pending > 0 = 옛 mbox(--rows 모름) → pending 만 돌려주고 부르는 쪽이 막는다 · 0 < 줄 수 ≠ pending = mail-unknown."""
        head, out = None, ""
        if not short:
            rc, out, _ = self.call(["bash", self.mbox, "peek", seat])
            got = re.search(r"pending=(\d+)", out or "")
            if rc != 0 or not got:
                return None, [], "mail-unknown"
            if not int(got.group(1)):
                return 0, [], ""
        rc, out, _ = self.call(["bash", self.mbox, "peek", seat, "--rows"])
        if rc != 0:
            return None, [], "mail-unknown"
        lines = []
        for line in (out or "").splitlines():
            if head is not None and line.lstrip().startswith("{"):
                lines.append(line)
            elif head is None and line.strip():
                head = line
        got = re.search(r"pending=(\d+)", head or "")
        if not got:
            return None, [], "mail-unknown"
        n, docs = int(got.group(1)), []
        for line in lines:
            try:
                doc = json.loads(line)
            except ValueError:
                return n, [], "mail-unknown"
            if not isinstance(doc, dict) or not isinstance(doc.get("body"), str):
                return n, [], "mail-unknown"
            docs.append(doc)
        if not docs:
            return n, [], "mail-pending" if n else ""   # 옛 mbox = 지금처럼 1통이라도 막는다
        if len(docs) != n:
            return n, [], "mail-unknown"
        return n, docs, ""

    def mail_verdict(self, team, seat, idle_s, short=False):
        """A6·A7 — 미읽음 전부가 «빼는 마감 쪽지» 일 때만 통과("" + 꼬리) · 한 통이라도 막으면 mail-pending · 판독 실패 = mail-unknown.
        short = 짧은 문턱 길(r2535 K2 길 표식 · 착지 좌석 닫기 길 · r2509 긴급 쉼 길) — `peek --rows` 를 바로 부를지 가른다."""
        n, docs, bad = self.mail_rows(seat, short=short)
        if bad:
            return bad, ""
        senders, now, skip = self.close_senders(team), self.now(), []
        for doc in docs:
            try:
                age = now - datetime.datetime.strptime(str(doc.get("ts")), "%Y-%m-%dT%H:%M:%S").timestamp()
            except ValueError:
                return "mail-pending", ""
            if not self.closed_form(doc.get("body")) or not senders or doc.get("from") not in senders or age < idle_s:
                return "mail-pending", ""
            skip.append((doc, age))
        if not skip:
            return "", ""
        seqs = [str(doc.get("seq")) for doc, _ in sorted(skip, key=lambda x: str(x[0].get("seq")))[:3]]
        return "", "미읽음 마감 %d통 제외(seq %s · 가장 오래된 %d분)" % (len(skip), " ".join(seqs), max(age for _, age in skip) // 60)

    def mail_gate(self, team, work, seat, idle_s, short=False):
        """A5~A8 — 미읽음 사유 1개(통과 = "") · 빼는 n통 꼬리는 판정 줄 꼬리로(round 장부 two · close 가 따로 읽는다) · 좌석·문턱당 1회.
        쪽지는 큐에 그대로 둔다(keeper 가 mark·recv 하지 않는다 · A8)."""
        book = self.cache.setdefault("@round", {}).setdefault("mail", {})
        if (seat, idle_s, bool(short)) not in book:
            book[(seat, idle_s, bool(short))] = self.mail_verdict(team, seat, idle_s, short=short)
        code, tail = book[(seat, idle_s, bool(short))]
        if tail:
            self.cache["@round"].setdefault("two", {})[seat] = tail
        return code

    def parked_tail(self, seat):
        """A8 근거 줄 꼬리(빼는 미읽음 n통) — 판정 줄 밖(CLOSED-SESSION 같은 행동 줄)이 이 값을 읽는다 · 없음 = ""."""
        mail = self.cache.get("@round", {}).get("mail") or {}
        return mail.get((seat, DONE_IDLE, True), ("", ""))[1] or mail.get((seat, self.park(), False), ("", ""))[1]

    def park_seat(self, team, work, attempt, holder, reason, tail, alive, done, intent=None):
        """PARKED 실행 — 정지 중 = «예정 PARKED» 1줄 · 아니면 kill(살아 있으면) → park 1줄(done 0 일 때만) · 실패 = UNKNOWN."""
        if self.halt:
            return self.verdict(team, work, holder, "예정 PARKED", reason, "정지 중 kill·park 0")
        if alive:
            if not self.idle(team, work, holder, attempt):   # kill 직전 가드(마지막 확인 1회)
                return "WORKING"
            if self.held_attached(team, work, holder):
                return "UNKNOWN"
            self.call([self.tmux, "kill-session", "-t", "=" + holder])
            seen = self.probe(holder)
            if seen != "absent":
                return self.unknown_seat(team, work, attempt, holder, "kill-failed", seen)
            self.state["open"].pop(holder, None)
        if not done:
            out, rc = cli.run(["park", "--work", work, "--attempt", attempt, "--reason", reason, "--root", self.root, "--team", team])
            if rc != 0:
                return self.unknown_seat(team, work, attempt, holder, "park-refused", "%s %s" % (out.get("result"), out.get("reason", "")[:60]))
        word = self.verdict(team, work, holder, "PARKED", reason, tail)
        if intent is not None:   # r2535 K6·K7 — 닫은 바퀴에 «[자리 비움]» 1통 + submit-park.log 1줄(착지 길 닫기에는 안 부른다)
            note.parked(self, team, work, holder, intent)
        return word

    def nano_seats(self, team):
        """r2509 — 이 팀 나노 자리 [(work, attempt, holder)] = 최신 dispatch 1줄씩 · holder 이름이 나노 꼴인 것만(장기 좌석·팀장 석 0)."""
        latest = {}
        for rec in self.rows_of(team):
            if rec.get("kind") == "dispatch" and rec.get("work"):
                latest[rec["work"]] = (rec.get("attempt"), rec.get("holder"))
        return [(work, attempt, holder) for work, (attempt, holder) in sorted(latest.items())
                if isinstance(holder, str) and holder.startswith("biz-%s-nano-" % team) and not long_seat(holder)]

    def urgent_park(self, team, card, keep=None):
        """r2509 K2 — 긴급 카드 자리 만들기: 이 팀 나노 중 «턴 끝 ∧ 유휴 ≥ DONE_IDLE ∧ 막는 미읽음 0» 한 석을 가장 오래 쉰 순으로 골라 기존 park_seat 길로 쉼.
        keep = 접수 상한이 막힌 때 고를 work 집합(㉠ · None = 살아 있는 유휴 석 아무나 · 완료 포함) · 반환 = 쉼을 낸 석 이름 또는 ""(쉼 0).
        판독 = look(짧은 문턱) 그대로 — 판정 줄·[긴급] 은 settle 의 한 길과 같은 기억을 쓰므로 같은 석에 두 번 나지 않는다."""
        alive = self.alive_seats()
        if alive is None:   # tmux 판독 불가 = 손 0
            return ""
        seats = {}
        for work, attempt, holder in self.nano_seats(team):
            if holder not in alive or (keep is not None and work not in keep):
                continue
            intent = endings.intent(self, team, work, attempt, holder)
            age, stop = self.pi_turn(intent) if intent.get("worktree") else (None, None)
            if age is None:   # 세션 파일 0 = 판독 근거 0(유휴 문턱 판정은 look 한 곳 — 짧은 문턱 DONE_IDLE)
                continue
            seats[holder] = (work, attempt, age, stop)
        for holder, (work, attempt, age, stop) in sorted(seats.items(), key=lambda kv: -kv[1][2]):   # 가장 오래 쉰 순
            if self.look(team, work, attempt, holder, age, stop, idle_s=DONE_IDLE, short=True) != "REST":   # r2509 긴급 쉼 길 = 짧은 문턱 길(미읽음 관문 그대로)
                continue   # 턴 안 끝남 · 막는 미읽음 · 판독 실패 = 이 석 0(다음 후보)
            return holder if self.park_seat(team, work, attempt, holder, "idle-done", "긴급 %s 자리 · 유휴 %d초" % (card, age), alive=True, done=False) == "PARKED" else ""   # 쉼 사유 낱어 = 코어가 받는 둘 중 하나(idle-done · 계약 그대로) · 까닭은 근거 줄에
        return ""

    def wide_landed(self, team, work, intent, done):
        """A7 착지 근거 넓힘 — (원장 done ∧ 카드 완성 폴더) ∨ 가지 커밋 전부 base 에 있음(git cherry 전부 −) · 가지 이름 무관 · 못 채움 = ""."""
        cards = self.resolve_card(team, work)[0]
        if done and not isinstance(cards, str) and any("/indices/완성/" in path for _, path in cards):
            return "done-card-완성"
        tree, base = intent.get("worktree") or "", intent.get("base") or ""
        if not (tree and base and os.path.isdir(tree)):
            return ""
        rc, out, _ = self.git(tree, "cherry", base, "HEAD")
        lines = out.split() and out.splitlines()
        return "cherry-all-in-base" if rc == 0 and lines and all(x.startswith("-") for x in lines) else ""

    def accept_only(self, team, rows):
        """⑪ accept 만(dispatch 0) · ACCEPT_IDLE 넘음 · 의무 장부에 남음 → UNKNOWN accept-only 1개(work 단위)."""
        state = PROJ.record.recover_state(PROJ.journal.Journal(PROJ.runtime_path(self.root, team), rec=PROJ.record).state(), rows)
        left, sent, first = set(PROJ.record.remaining(state, rows)), {r.get("work") for r in rows if r["kind"] == "dispatch" and isinstance(r.get("work"), str)}, {}
        for rec in rows:
            if rec["kind"] == "accept" and rec["command"] in left and isinstance(rec.get("work"), str) and rec["work"] not in sent:   # ㉕ work 가 str 아님 = work 없는 접수(core record.remaining·capacity 규칙)
                first.setdefault(rec["work"], rec)
        for work, rec in sorted(first.items()):
            try:
                age = self.now() - datetime.datetime.strptime(rec["at"], "%Y-%m-%dT%H:%M:%S").timestamp()
            except ValueError:
                continue
            if age >= self.wait("FT2_ACCEPT_IDLE_S", ACCEPT_IDLE, 600):   # r2539 K7 — 접수만 있는 일 문턱 5분
                n = sum(1 for r in rows if r["kind"] == "accept" and r.get("work") == work and r["command"] in left)
                self.unknown_seat(team, work, rec["attempt"], "-", "accept-only", "접수 %d줄 · %d분" % (n, age // 60))

    def tmuxc_status(self, seat):
        """tmuxc 상태 칸(agent | shell | None) — tmuxc UC6 `clean`(읽기만 · 바퀴당 1회 · 7초) 출력 = shell-only 세션 · 그 밖 = agent ·
        tmuxc 없음·실패 = None(대조 0) · 경로 = FT2_TMUXC 또는 ~/.local/bin/tmuxc."""
        got = self.cache.setdefault("@round", {})
        if "tmuxc" not in got:
            tool = self.env.get("FT2_TMUXC") or os.path.join(self.env.get("HOME") or os.path.expanduser("~"), ".local", "bin", "tmuxc")
            rc, out, _ = self.call([tool, "clean"]) if os.access(tool, os.X_OK) else (None, "", "")
            got["tmuxc"] = set(out.splitlines()) - {""} if rc == 0 else None
        return None if got["tmuxc"] is None else "shell" if seat in got["tmuxc"] else "agent"

    def ready_seen(self, new, old):
        """후계 [레디] 영수 = 우편함(mailbox.jsonl · mailbox.log.jsonl)에 from new · to old · «[레디] new <- old» 줄 · 바퀴당 1회 읽기."""
        got = self.cache.setdefault("@round", {})
        if "ready" not in got:
            comm, pairs = self.env.get("FT2_MAILBOX_DIR") or os.path.join(self.root, ".fable-team", "comm"), set()
            for name in ("mailbox.jsonl", "mailbox.log.jsonl"):
                try:
                    with open(os.path.join(comm, name), encoding="utf-8", errors="replace") as fh:
                        rows = [json.loads(x) for x in fh if "[레디]" in x]
                except (OSError, ValueError):
                    continue
                pairs |= {(r.get("from"), r.get("to")) for r in rows if isinstance(r, dict)
                          and str(r.get("body", "")).startswith("[레디] %s <- %s" % (r.get("from"), r.get("to")))}
            got["ready"] = pairs
        return (new, old) in got["ready"]

    def resume_ok(self, seat):
        """hil.md 검증된 재개 기록 = seat-resume/<세션명>.json(ft-seat-retire) · name 같음 · codex 아님 · 작업 폴더가 keeper roots 안 ·
        대화 결속 = jsonl 칸이 실제 파일 ∧ 파일 이름이 uuid 로 끝남 ∧ 담긴 폴더 = 그 cwd 의 세션 폴더(pi `--<cwd>--` · claude `/`·`.` → `-`)."""
        home = self.env.get("HOME") or os.path.expanduser("~")
        doc = self.read_json(os.path.join(self.env.get("FT2_SEAT_RESUME_DIR") or os.path.join(home, ".claude", "state", "seat-resume"), seat + ".json"))
        cwd, uuid, log = str(doc.get("cwd") or ""), str(doc.get("uuid") or ""), str(doc.get("jsonl") or "")
        if doc.get("name") != seat or not uuid or doc.get("engine") == "codex" or not any((cwd + "/").startswith(r + "/") for r in self.roots()):
            return False
        folders = ("--%s--" % cwd.strip("/").replace("/", "-"), re.sub(r"[/.]", "-", cwd))
        return os.path.isfile(log) and os.path.basename(log).endswith(uuid + ".jsonl") and os.path.basename(os.path.dirname(log)) in folders

    def roots(self):
        """S1 keeper roots(FETCH_TARGETS 와 같은 표 · BIZ root · 팩) — 있는 폴더만 · 중복 0."""
        both = (self.root, self.pack)
        return [r for i, r in enumerate(both) if r and os.path.isdir(r) and r not in both[:i]]

    def rosters(self):
        """S1 모든 roots 의 명부 [(경로, 행 dict)] · 바퀴당 1회."""
        got = self.cache.setdefault("@round", {})
        if "rosters" not in got:
            paths = [p for r in self.roots() for p in sorted(glob.glob(os.path.join(r, ".fable-team", "seats*.json")))]
            got["rosters"] = [(p, rows) for p in paths for rows in [self.read_json(p)] if isinstance(rows, dict)]
        return got["rosters"]

    def seat_kind(self, seat, row):
        """S1 좌석 종류 = 명부 role 칸(종류 낱말일 때) · 상태 낱말(stop-ready 등)·칸 없음 = 이름 셋째 토큰."""
        role = row.get("role") if isinstance(row, dict) else None
        return role if role in KINDS else (seat.split("-") + ["", ""])[2]

    def bound(self, seat, new):
        """S2 이름 바뀐 승계 결속 = 명부 seat._replaced_by == new ∧ new._replaces == seat(어느 roots 명부든)."""
        rows = {}
        for _, got in self.rosters():
            rows.update({key: val for key, val in got.items() if isinstance(val, dict)})
        return (rows.get(seat) or {}).get("_replaced_by") == new and (rows.get(new) or {}).get("_replaces") == seat

    def keep_gate(self, seat, new, alive):
        """S2 닫기 자격 — 계보(base#N · 이름 바뀐 승계는 양방향 결속 ∧ 후계 생존일 때만 새 세대로 셈) 순번 1 = keep-recent · 순번 2 = 검증된 재개 기록 있을 때만 · 그 밖 keep-last-2 · 3 이상 = 자격 있음("")."""
        base, _, n = seat.rpartition("#")
        newer = {x for x in alive if x.rpartition("#")[0] == base and x.rpartition("#")[2].isdigit() and n.isdigit() and int(x.rpartition("#")[2]) > int(n)}
        newer |= {new} if new and new in alive and new.rpartition("#")[0] != base and self.bound(seat, new) else set()
        if not newer:
            return "keep-recent"
        if len(newer) == 1 and not self.resume_ok(seat):
            return "keep-last-2"
        return ""

    def closed_seats(self):
        """ft2 close 영수가 있는 좌석 이름(모든 팀 state.close_receipts) · 바퀴당 1회."""
        got = self.cache.setdefault("@round", {})
        if "closed" not in got:
            seats = set()
            for team in self.teams():
                try:
                    state = cli._load("dispatch").Dispatch(self.root, team).ex._state_records()[0]
                except ValueError:
                    continue
                seats |= {row.get("seat") for row in (state.get("close_receipts") or {}).values()}
            got["closed"] = seats
        return got["closed"]

    def outsiders(self, alive, known):
        """S1·S3 — 살아 있는 biz-* 중 어느 명부·최신 dispatch·나노 이름에도 없는 세션 = UNKNOWN roster-outside · 이름 lint 실패 = name-bad · kill 0."""
        scope = getattr(self, "orphan_scope", set())   # 이 바퀴 고아 길(endings.orphans)이 판정한 팀 · 정지 중 = 빈 집합(고아 꼴도 여기서 판정)
        for seat in sorted(x for x in alive if x.startswith("biz-") and x not in known and not ((m := endings.ORPHAN.fullmatch(x)) and m.group(1) in scope)):
            team = (seat.split("-") + [""])[1]
            if team in self.skip:   # r1835 K2 — 제외 팀 좌석 = 손 0
                continue
            self.unknown_seat(team, "-", "-", seat, "roster-outside" if NAME.fullmatch(seat) else "name-bad")
