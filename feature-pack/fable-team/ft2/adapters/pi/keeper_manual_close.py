"""ft 2.0 keeper — 사람·팀장이 부르는 닫기 한 명령 (r2401 · 카드 K1~K4 · 사전 DA#56 APPROVE-DESIGN r3).

    python3 core/cli.py keeper --root R --close-seat <석> --verdict <N> --approve "<planner 좌석> #<seq>" --reason "<10자 이상>"

차례 = K1 대상(이름 꼴 ∧ 팀 2.0 전환 ∧ launch intent) → K4 잠금(7초 대기) → K2 승인 대조(원장 행·우편·planner 꼴·자율 모드·긍정 판독·정지)
      → K3 손(장부 판독 → attached → pane Working → dirty → 재개 기록 → kill → park) → 끝 줄 «CLOSED-MANUAL …». 실패한 단계에서 멈추고 rc 로 알린다.
      장부·pane 판독 실패 = rc 9 «판정 불가»(모르면 닫지 않는다 · DA#56 H1·H2).
승인 판정은 새로 쓰지 않는다 — r1865 `keeper_verdict.approved`(planner 원장 행 + 우편 로그) 한 곳 그대로. 여기서 더하는 것은 글자 판독 1개(ⓔ)뿐이다:
원장 행에 «수동 닫기» 가 있고 거절 낱말이 없고 우편 첫 줄 머리가 «[수동 닫기 승인]» — approved 가 "" 를 돌려줘도 여기서 거절한다(덜 닫는 쪽).
재개 기록 = r2281 `keeper_close_old.resume` 그대로(source 칸만 ft2-manual-close · retired_by = 승인 좌석). park = core 공개 동사(cli park) 1회.
부르는 손 = planner master·desk 뿐(hil.md 19행 표준승인 그대로 · 이 파일은 새 권한을 만들지 않는다).
정지(ALL_STOP) 중 = 기록·kill·park 0 — 단 r2419 부터는 «정지 뒤에 새로 뜬 석»(tmux 세션 생성 시각 > ALL_STOP since)만 통과한다(K1).
원장 행은 origin/main(directive-roots.tsv)에 없으면 데이터 루트의 planner 원장 파일에서도 읽는다(K3 ⓑ · 출처 표시 K4 ·
데이터 루트 행일 때는 승인 우편이 그 석을 적어야 한다 K6). 자동 닫기(`keeper_verdict.approved`)는 손 0.

r2440 K1~K6 — ⓪ 장부 판독 뒤 부재 판독(tmux has-session 1회)이 absent 면 «죽은 세션 갈래»(dead_hands)로 간다:
사람 화면·pane·kill 0 · dirty 검사 그대로 · 재개 기록은 세션 생성 시각 대조 없이 그 worktree 의 pi 세션 기록 수로 가른다(0개 = 기록 0 · 2개 이상 = 고친 시각이 가장 늦은 1개) ·
park 직전 부재 재확인 1회 · 끝 줄 꺼리 « · 세션 없음(kill 0)» · park 는 지금 ⑥ 그대로. alive·판정 불가는 지금 손 그대로(줄 글자·rc 같음).

r2503 — ⓔ 거절 판독은 그대로(글자 포함 = REJECT · 덜 닫는 쪽) 두고 REJECT 사유에 자리 칸을 붙인다: «거절 낱말 «X» · 자리 = 원장 행 «…X…»» | «우편 N째 줄».
사람이 그 자리를 보고 낱말을 뺀 승인을 다시 보낸다(실사건 2026-11-23 · 사람 손 왕복 2회). 보내는 쪽 반송 = 1.x comm/mbox_guard.sh 같은 낱말 목록.

r2549 — 닫기 도구 자리(FT_SEAT_CLOSE_BIN)가 빈 셸에서 부른 수동 닫기를 «정지 중» 이 아니라 «REJECT 닫기 도구 자리 없음» rc 2 한 줄로 거절한다(K3 · 승인 대조보다 앞).

r2571 K1 — 쉼으로 이미 적힌 석을 수동 닫기 하면 cli park 가 rc 1 + HOLD «완료 유보» · reason «이미 쉼 = 멱등(쓰기 0)» 를 준다(쉼은 이미 됐다).
  그 답은 실패가 아니다 → PARK-FAILED 줄 0 · state.open 에서 그 석을 지움 · 끝 줄 «park=already»(끝 줄·rc 는 지금 그대로 0).
  result 칸이 HOLD 낱말이 아니거나(REFUSED «접수 거부») 없으면 reason 글자가 같아도 실패로 읽는다(PARK-FAILED rc 7 · state.open 보존).
r2571 K3 — 세션이 이미 없는 석(dead_hands)을 닫은 바로 뒤 keeper 로그 1줄 «LEFT-MANUAL …» = 남은 worktree(있음/없음 1회 판독)와
  명부 행은 이 도구가 치우지 않는다는 안내. 도구가 지우는 것은 0(worktree·가지·명부·keep ref = 사람 손 · git worktree remove 는 안내 글자일 뿐).
  이 줄은 rc 를 바꾸지 않고, 살아 있는 석 갈래·실패로 멈춘 갈래에는 나오지 않는다.
빈 자리 탓에 판정기가 상대 경로 «ft-all-stop.sh» 가 되어 rc 127 → «판정 불가 = 정지» 로 흘러 «정지 중» 이라는 틀린 글이 나가던 것을 막는다(env 값은 부르는 쪽이 준다 · 설치본 경로는 코드에 박지 않는다 K4).
"""
import glob
import importlib.util
import json
import os
import re
import time

HERE = os.path.dirname(os.path.abspath(__file__))
FT2 = os.path.dirname(os.path.dirname(HERE))
LOCK_S = 7.0                                   # K4 — keeper 바퀴 잠금 대기(하드 룰 12: 7초 1회 · 재시도 0)
MIN_REASON = 10                                # K1 — 사유 ≥ 10자
SEAT = re.compile(r"biz-([a-z0-9]+)-nano-[A-Za-z0-9._-]+#[0-9]+")
PLANNER = re.compile(r"biz-planner-(master|desk)-")
MANUAL, HEAD = "수동 닫기", "[수동 닫기 승인]"     # K2 ⓔ — 원장 행 낱말 · 우편 첫 줄 머리
REFUSE = ("아니오", "거절", "보류", "반려", "철회")   # K2 ⓔ — 거절 낱말(이유 글에 섞여도 거절 = 덜 닫는 쪽) · 낱말 목록은 1.x 보내는 쪽 판정기와 같다(r2503)
PLACE = 12                                      # K2 ⓔ 자리 칸 — 원장 행 조각의 낱말 앞뒤 글자 수(r2503)
AUTO = re.compile(r"A[0-9]+")                  # K2 ⓒ 자율 ON = 원장 행의 자율 사건 번호
HOLD, ALREADY = "완료 유보", "이미 쉼 = 멱등"    # r2571 K1 — core HOLD 낱말(dispatch.HOLD) · dispatch._park 의 «같은 attempt 가 이미 쉼» reason 머리
PARK = "idle-done"                              # K3 ⑥ core 공개 동사(cli park)의 쉼 사유 낱말 — core 는 idle-done·launch-failed 만 받는다(dispatch.park · 어긴 사유 = 접수 거부)
                                                #   그래서 «manual-close: 판정 <N> <사유>» 는 core 에 넘기지 않고 CLOSED-MANUAL·PARK-FAILED 줄에 남긴다(core 무수정 = 카드 «park 는 core 공개 동사 그대로»).
REOPEN_HOW = (" · 다시 열기 = 카드에 «- 재개: <시각> · PR #<번호> · head <40자> · 가지 nano/<work>» 한 줄"
              "(원장이 남아 있으면 ft-card-assign-watch.sh record <카드> clear <사유>)")   # r2573 K5 — 끝 줄 꼬리(keeper_next.REOPEN_HOW 와 같은 글자 · 순환 import 0 이라 사본)
OPPA = re.compile(r"오빠[\s«»\"'“”]*네[\s«»\"'“”]*[0-9]{10}\.[0-9]{6}")   # K2 ⓒ 자율 OFF = «오빠 네 <Slack ts>» 한 덩어리(«오빠» 와 ts 따로 = 승인 아님)
MODE = ("on", "off", "tamper")
LOCAL_SRC = "데이터 루트(main 미착지)"             # K4 — 데이터 루트 원장 행으로 닫았을 때 끝 줄 꼬리(출처 표시)
BOUND = r"[\w#-]"                              # K6 · 원장 행 석 이름 경계(«…#1» ≠ «…#10» · keeper_verdict 와 같은 글자)


def _load(path, alias):
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


verdict_mod = _load(os.path.join(HERE, "keeper_verdict.py"), "ft2_manual_verdict")
close_old_mod = _load(os.path.join(HERE, "keeper_close_old.py"), "ft2_manual_close_old")
settle = _load(os.path.join(HERE, "keeper_settle.py"), "ft2_manual_settle")
endings = _load(os.path.join(HERE, "keeper_endings.py"), "ft2_manual_endings")
cli = _load(os.path.join(FT2, "core", "cli.py"), "ft2_manual_cli")


def team_of(seat):
    """K1 — biz-<팀>-nano-<stem>#N 이면 그 팀 · 아니면 ""(그 밖 이름 = 대상 아님)."""
    m = SEAT.fullmatch(seat or "")
    return m.group(1) if m else ""


def switched(k, team):
    """K1 — 그 팀이 2.0 으로 전환됐나(state/ft20-switch/<팀>.json · ft-index-move·ft-nano-spawn 이 세우는 표식)."""
    return os.path.isfile(os.path.join(k.root, ".fable-team", "state", "ft20-switch", team + ".json"))


def close_bin_missing(k):
    """r2549 K3 — 닫기 도구 자리(FT_SEAT_CLOSE_BIN)와 판정기 자리(FT2_ALL_STOP_JUDGE)가 둘 다 빈가.

    빈 채로 부르면 판정기가 상대 경로가 되어 rc 127 → «판정 불가 = 정지» 로 흘러 «정지 중» 이라는 틀린 글이 나간다.
    승인 대조·판정기 호출 앞에서 멈추고 붙일 env 값을 밝힌다(설치본 경로는 코드에 박지 않는다 · K4)."""
    env = getattr(k, "env", None) or {}
    return not str(env.get("FT_SEAT_CLOSE_BIN") or "").strip() and not str(env.get(settle.JUDGE_ENV) or "").strip()


def target(k, seat):
    """K1 — (팀, work, attempt, intent, "") · 아니면 ("", "", "", {}, 사유). intent = FT2_HOLDER 가 이 석인 가장 늦은 1개."""
    team = team_of(seat)
    if not team:
        return "", "", "", {}, "이름 꼴 아님(biz-<팀>-nano-<stem>#N)"
    if not switched(k, team):
        return "", "", "", {}, "팀 %s 2.0 전환 아님(keeper 자동 닫기 몫)" % team
    got = [(str(it.get("at") or ""), work, attempt, it) for work, attempt, it in endings.intents(k, team)
           if isinstance(it, dict) and it.get("FT2_HOLDER") == seat]
    if not got:
        return "", "", "", {}, "intent 없음(손으로 연 좌석 = planner 수동 닫기 몫)"
    _, work, attempt, intent = max(got, key=lambda x: (x[0], x[1], x[2]))
    return team, work, attempt, intent, ""


def lock(k, wait=LOCK_S):
    """K4 — keeper 바퀴 잠금을 wait 초까지 기다려 잡는다 → 잠금 경로 · 못 잡음 = None(그때는 손 0).
    r2539 K4 — 죽은 잠금 판정은 keeper.locked 와 같은 규칙(k.stale_lock): 나이 > 문턱 ∧ pid 죽음·못 읽음 만 지운다 · pid 살아 있음 = 나이 무관 유지."""
    os.makedirs(k.dir, exist_ok=True)
    path = os.path.join(k.dir, "keeper.lock")
    end = time.monotonic() + max(0.0, wait)
    while True:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            try:
                if k.stale_lock(path)[0]:   # 죽은 바퀴 잠금 = keeper.locked 와 같은 규칙으로 지우고 다시
                    os.unlink(path)
                    continue
            except OSError:
                continue
            if time.monotonic() >= end:
                return None
            time.sleep(0.1)
            continue
        with os.fdopen(fd, "w", encoding="utf-8") as fh:   # r2539 K4 — 산 표식 = pid 1줄
            fh.write("%d\n" % os.getpid())
        return path


def autonomy(k):
    """K2 ⓒ — 1.x bin/ft-autonomy.sh mode 1회(7초) → on|off|tamper · 못 읽음·그 밖 값 = ""(REJECT)."""
    path = os.path.join(k.root, ".fable-team", "bin", "ft-autonomy.sh")
    if not os.path.isfile(path):
        path = os.path.join(os.path.dirname(FT2), "legacy", "1.x", "harness", "bin", "ft-autonomy.sh")
    rc, out, _ = k.call(["bash", path, "mode"])
    word = (out or "").strip()
    return word if rc == 0 and word in MODE else ""


def main_rows(k, n):
    """K3 ⓐ — planner 원장 행 글자(keeper_verdict.ledger 와 같은 원장·같은 grep·같은 정규식 — 판정은 바꾸지 않고 글자만 읽는다) → (행 목록, 사유).
    사유가 있는 것 = git 실패(rc 2 이상·시간 초과)뿐 — 행 0개는 사유가 아니다(그때는 데이터 루트로 내려간다)."""
    tbl = os.path.join(k.root, ".fable-team", "state", "directive-roots.tsv")
    try:
        with open(tbl, encoding="utf-8") as fh:
            table = [x.rstrip("\n").split("\t") for x in fh if not x.startswith("#") and len(x.split("\t")) >= 4]
    except (OSError, UnicodeError) as exc:
        if not isinstance(exc, FileNotFoundError):
            return "", "원장 못 읽음 · directive-roots"
        table = []
    r = next((x for x in table if x[0] == "planner"), None) or next((x for x in table if x[0] == "*"), ["*", ".", "origin/main"])
    rc, out, err = k.call(["git", "-C", os.path.join(k.root, r[1]), "grep", "-I", "-E", "-e", r"^- \*\*%s\*\*" % n,
                           "-e", r"^\|[[:space:]]*%s[[:space:]]*\|" % n, r[2], "--", verdict_mod.MD_GLOB], verdict_mod.GIT_S)
    if rc not in (0, 1):
        return "", "원장 못 읽음 · git grep rc %s %s" % (rc, err[:80])
    hits = {}
    for path, _, body in (x[len(r[2]) + 1:].partition(":") for x in out.splitlines()):
        row, num = verdict_mod.MD_ROW.match(body), re.search(r"planner-(\d+)-", path)
        if row and num and (row.group(1) or row.group(2)) == n:
            rest = body[row.end():]
            hits.setdefault(int(num.group(1)), []).append(rest.strip() if row.group(1) else "|".join(rest.split("|")[1:]).strip(" |"))
    return (hits[max(hits)] if hits else []), ""


def row_fit(n, seat, seq, body):
    """K3 — 원장 행 글자 대조(석 이름 · 무효·철회 · #seq) · keeper_verdict.ledger 와 같은 규칙·같은 글자 → "" = 맞음."""
    if not verdict_mod.near(BOUND, seat, body):
        return "판정 %s 행에 %s 없음" % (n, seat)
    if verdict_mod.VOID.match(body):
        return "판정 %s 무효·철회" % n
    if not verdict_mod.near("[0-9]", "#" + seq, body):
        return "판정 %s 행에 #%s 없음" % (n, seq)
    return ""


def row_text(k, n):
    """K3 — 그 판정 번호의 원장 행 글자와 출처 → (글, 사유, 출처). ⓐ origin/main 에 정확히 1개면 그 행(출처 "").
    ⓐ 0개 ∧ git rc 0·1 = ⓑ 데이터 루트 파일(번호 가장 큰 것) 1개(출처 LOCAL_SRC) · ⓐ 2개 이상·git 실패 = 지금처럼 거절(main 이 이긴다).
    """
    rows, why = main_rows(k, n)
    if why or len(rows) > 1:
        return "", why or "판정 %s 원장 행 %d개" % (n, len(rows)), ""
    if rows:
        return rows[0], "", ""
    rows, why = verdict_mod.local_rows(k, n)
    if why:
        return "", why, ""
    if len(rows) != 1:
        return "", "데이터 루트 원장 · 판정 %s 원장 행 %d개" % (n, len(rows)), ""
    return rows[0], "", LOCAL_SRC


def mail_text(k, seq):
    """그 seq 우편 1통의 본문(keeper_verdict.mailbox 와 같은 로그·같은 꼴) · 없음·중복·못 읽음 = ""."""
    path = os.path.join(k.root, ".fable-team", "comm", "mailbox.log.jsonl")
    try:
        with open(path, encoding="utf-8") as fh:
            found = [rec for rec in (json.loads(x) for x in fh if seq in x) if isinstance(rec, dict) and str(rec.get("seq")) == seq]
    except (OSError, ValueError):
        return ""
    return str(found[0].get("body") or "") if len(found) == 1 else ""


def row_piece(body, w, span=PLACE):
    """ⓔ 자리 칸(원장 행) — 그 낱말 앞뒤 span 글자 조각 한 줄 · 잘린 쪽은 «…»(고칠 자리를 눈으로 찾게 · 판정은 바꾸지 않는다)."""
    i = body.find(w)
    lo, hi = max(0, i - span), min(len(body), i + len(w) + span)
    return ("…" if lo else "") + body[lo:hi].replace("\n", " ") + ("…" if hi < len(body) else "")


def mail_line(mail, w):
    """ⓔ 자리 칸(우편) — 그 낱말이 처음 나온 줄 번호(1부터) · 0 = 없음."""
    return next((i for i, line in enumerate(mail.splitlines(), 1) if w in line), 0)


def refuse(body, mail):
    """ⓔ — 걸린 낱말과 자리 → (낱말, «원장 행 «조각»»|«우편 N째 줄»). 없으면 ("", "").
    고르는 순서 = 낱말 먼저(REFUSE 차례 그대로 · 카드 «낱말 목록 손 0»), 같은 낱말이면 원장 행 먼저(검사 차례 그대로)."""
    for w in REFUSE:
        if w in body:
            return w, "원장 행 «%s»" % row_piece(body, w)
    for w in REFUSE:
        if w in mail:
            return w, "우편 %d째 줄" % mail_line(mail, w)
    return "", ""


def positive(k, n, seq, body):
    """K2 ⓔ — 긍정 승인 판독 1개: 원장 행 «수동 닫기» ∧ 거절 낱말 0(행·본문) ∧ 우편 첫 줄 머리 «[수동 닫기 승인]» → "" · 아니면 사유.
    r2503 — 거절이면 사유 1줄에 걸린 낱말과 자리(원장 행 조각 · 우편 몇째 줄)를 붙인다(판독은 그대로 · 사람이 낱말을 빼고 다시 보내게)."""
    mail = mail_text(k, seq)
    head = mail.strip().splitlines()[0].strip() if mail.strip() else ""
    if MANUAL not in body:
        return "긍정 판독 · 원장 행에 «%s» 없음" % MANUAL
    if not head.startswith(HEAD):
        return "긍정 판독 · 우편 첫 줄 머리가 «%s» 아님" % HEAD
    w, where = refuse(body, mail)
    return "긍정 판독 · 거절 낱말 «%s» · 자리 = %s" % (w, where) if w else ""


def stop_since(k):
    """K1 — 정지 시각(epoch 초) = r2465 K3 판정기(`ft-all-stop.sh judge --json`)의 since 칸 · 판정 불가·칸 없음 = None(«정지 시각 판독 불가»).

    상태 파일을 직접 읽지 않는다 — keeper 가 이 바퀴에 이미 부른 판정 문서(k.stop_since)가 있으면 그대로 쓰고, 없으면 판정기를 1회 더 부른다."""
    doc = getattr(k, "stop_since", None)
    if not isinstance(doc, dict):
        doc = k.judge_doc()[0] or {}
    got = doc.get("since") if isinstance(doc, dict) else None
    return got if isinstance(got, int) and not isinstance(got, bool) and got > 0 else None


def stopped_ok(k, seat):
    """K1 · ⓓ — 정지 중에 닫아도 되는 석인가 → (사유, 덧말). 사유 "" = 통과.
    통과 = tmux 세션 생성 시각(display-message 1회 · 7초) > since. 그 밖(≤·판독 실패)은 지금처럼 거절(덜 닫는 쪽).
    """
    since = stop_since(k)
    if since is None:
        return "정지 시각 판독 불가", ""
    born = k.seat_born(seat)                             # tmux #{session_created} 1회 · 못 읽음 = None
    if born is None:
        return "세션 생성 시각 판독 불가", ""
    if int(born) <= since:                               # 같으면 거절(정지 전부터 있던 석)
        return "세션 생성 %d ≤ 정지 %d" % (int(born), since), ""
    return "", " · 정지 중 닫기(세션 생성 %d > 정지 %d)" % (int(born), since)


def approval(k, seat, work, n, seat_ok, seq):
    """K2 — (사유, 갈래, 덧말) · ("", "", "") = 승인 맞음. 갈래 = «승인»(rc 2) | «정지 중»(rc 2). 순서 = ⓐ ⓑ ⓒ ⓔ ⓓ.
    덧말 = 끝 줄·keeper 로그 줄 꼬리(r2419 · 정지 중 닫기 K2 · 데이터 루트 원장 K4).
    """
    body, why, src = row_text(k, n)                     # ⓐ 원장 행(main → 없으면 데이터 루트)
    if why:
        return "승인 " + why, "승인", ""
    why = row_fit(n, seat, seq, body)                   # ⓐ 글자 대조(ledger 와 같은 규칙 · 원장이 둘 중 어느 쪽이든 같다)
    if why:
        return "승인 " + ("데이터 루트 원장 · " if src else "") + why, "승인", ""
    why = verdict_mod.mailbox(k, seq, seat_ok, work)    # ⓑ 우편 로그 대조
    if why:
        return "승인 " + why, "승인", ""
    note = " · 원장 = " + src if src else ""            # K4 — 데이터 루트 행일 때만 출처 표시
    if not PLANNER.match(seat_ok):
        return "승인 승인 좌석 %s 는 biz-planner-master·desk 아님(hil.md 19행)" % seat_ok, "승인", ""
    mode = autonomy(k)
    if not mode:
        return "승인 자율 모드 판독 실패", "승인", ""
    if mode == "on" and not AUTO.search(body):
        return "승인 자율 ON · 원장 행에 자율 사건 번호 A<N> 없음", "승인", ""
    if mode != "on" and not OPPA.search(body):
        return "승인 자율 %s · 원장 행에 «오빠 네 <Slack ts>» 없음" % mode.upper(), "승인", ""
    why = positive(k, n, seq, body)
    if why:
        return "승인 " + why, "승인", ""
    if src and not verdict_mod.near(BOUND, seat, mail_text(k, seq)):   # K6 — 데이터 루트 행은 우편이 그 석을 적어야
        return "승인 데이터 루트 원장 · 승인 우편 #%s 에 %s 없음" % (seq, seat), "승인", ""
    if k.stopped():                                     # ⓓ — 정지 중(정지 뒤에 뜬 석만 통과 · K1)
        why, extra = stopped_ok(k, seat)
        if why:
            return why, "정지 중", ""
        note += extra
    return "", "", note


def ledger(k, team):
    """K3 ⓪ — 최신 dispatch 장부 1회 판독. 못 읽음 = 판정 불가(«소유 없음» 확정 0 · DA#56 H2)."""
    latest = endings.latest(k, team)
    return latest, ("장부 판독 실패(endings.latest=None) — 소유 확인 불가" if latest is None else "")


def already(out):
    """r2571 K1 — cli park 답이 «같은 attempt 가 이미 쉼 = 멱등» 인가. rc 는 안 본다(코어는 HOLD 에도 rc 1 을 준다).
    result 가 HOLD 낱말 «완료 유보» 이고 reason 이 «이미 쉼 = 멱등» 으로 시작할 때만 참 — REFUSED(«접수 거부»)·result 칸 없음 = 거짓(⑬ ⑭)."""
    return str((out or {}).get("result") or "") == HOLD and str((out or {}).get("reason") or "").startswith(ALREADY)


def left_manual(k, team, seat, n, intent):
    """r2571 K3 — 세션이 이미 없던 석을 닫은 뒤 «남은 것» 1줄. 지우기 0 = worktree·가지·명부·keep ref 는 사람 손(안내 글자일 뿐).
    경로 = launch intent 의 worktree 글자 · 남음/없음 = os.path.isdir 1회 · 이 줄은 rc 를 바꾸지 않는다(k.log 반환 None)."""
    path = str((intent or {}).get("worktree") or "")
    left = "남음" if path and os.path.isdir(path) else "없음"
    k.log("LEFT-MANUAL", team, "%s 판정 %s · worktree %s %s · 명부 행 = 이 도구 손 0 · 치우기 = 사람 손(git worktree remove %s)"
          % (seat, n, path, left, path))


def parked(k, team, work, seat, n, reason, latest):
    """K3 ⑥ — 이 석이 최신 dispatch holder 이고 일이 done 이 아니면 cli park 1회 → («done»|«none», 0) · 실패 = ("", 7)."""
    attempt, holder = ((latest or {}).get(work) or (None, None))
    if holder != seat or not attempt:
        return "none", 0
    proj = k.proj_of(team) or {}
    works = (proj.get("works") or {}) if proj.get("result") == "접수 성공" else {}
    if (works.get(work) or {}).get("done"):
        return "none", 0
    why = "manual-close: 판정 %s %s" % (n, reason)
    out, rc = cli.run(["park", "--work", work, "--attempt", attempt, "--reason", PARK, "--root", k.root, "--team", team])
    if rc != 0 and not already(out):                        # r2571 K1 — «이미 쉼» HOLD 만 성공으로 읽는다
        k.log("PARK-FAILED", team, "%s 판정 %s 사유 «%s» · park 거절 %s %s · 세션은 이미 닫힘 · 손으로: python3 core/cli.py park --work %s --attempt %s --reason %s --root %s --team %s"
              % (seat, n, why, out.get("result"), str(out.get("reason", ""))[:60], work, attempt, PARK, k.root, team))
        return "", 7
    k.state.get("open", {}).pop(seat, None)
    return ("already" if rc else "done"), 0


def tree_dirty(k, intent):
    """K3 ③ — (0, "") = 깨끗 · (rc, 사유) = 닫지 않는다. 이 명령은 커밋하지 않는다."""
    tree = str(intent.get("worktree") or "")
    rc, dirty, _ = k.git(tree, "status", "--porcelain") if tree else (1, "", "")
    if rc != 0:
        return 8, "worktree 판독 실패"
    return (8, "미커밋 변경 있음") if dirty.strip() else (0, "")


def session_logs(k, intent):
    """K3 — 그 worktree 의 pi 세션 기록 파일들(close_old.resume 과 같은 폴더 규칙 · 세션 생성 시각은 안 본다)."""
    cwd = str(intent.get("worktree") or "")
    sessions = k.env.get("FT2_PI_SESSIONS") or os.path.expanduser("~/.pi/agent/sessions")
    return glob.glob(os.path.join(glob.escape(os.path.join(sessions, "--%s--" % cwd.strip("/").replace("/", "-"))), "*.jsonl"))


def resume_dead(k, seat, seat_ok, intent):
    """K3 — 죽은 세션의 재개 기록 → "" = 통과 · 그 밖 = 사유(rc 5 · 기록 0).
    세션 생성 시각 대조 없이 그 worktree 의 pi 세션 기록 수로 가른다: 0개 = 기록 0 으로 계속 ·
    1개 = 그 파일 · 2개 이상 = 고친 시각이 가장 늦은 1개. 기록 꼴은 r2281 그대로(source 칸만 ft2-manual-close)."""
    logs = session_logs(k, intent)
    if not logs:
        return ""
    log = max(logs, key=os.path.getmtime) if len(logs) > 1 else logs[0]
    uuid = os.path.basename(log)[:-len(".jsonl")].rpartition("_")[2]
    home = k.env.get("HOME") or os.path.expanduser("~")
    folder = k.env.get("FT2_SEAT_RESUME_DIR") or os.path.join(home, ".claude", "state", "seat-resume")
    path, old = os.path.join(folder, seat + ".json"), k.read_json(os.path.join(folder, seat + ".json"))
    if not (isinstance(old, dict) and old.get("name") == seat and old.get("uuid") == uuid):
        rec = {"name": seat, "engine": "pi", "uuid": uuid, "jsonl": log, "cwd": str(intent.get("worktree") or ""),
               "model": close_old_mod.model_of(log), "retired_by": seat_ok, "at": k.stamp(),
               "binding": {"source": "ft2-manual-close", "session": seat, "uuid": uuid, "jsonl": log}}
        try:
            os.makedirs(folder, exist_ok=True)
            with open(path + ".tmp", "w", encoding="utf-8") as fh:
                json.dump(rec, fh, ensure_ascii=False)
            os.replace(path + ".tmp", path)
        except OSError as exc:
            return "쓰기 %s" % type(exc).__name__
    return "" if k.resume_ok(seat) else "검증 실패"


def dead_hands(k, team, work, seat, n, seat_ok, seq, reason, note, latest, intent):
    """K2·K4·K5 — tmux 세션이 이미 없는 석: 사람 화면 판독 0 · pane 판독 0 · kill 0.
    차례 = ③dirty(그대로) → ④재개 기록(생성 시각 없이) → 부재 재확인(park 직전 1회) → ⑥park → ⑦끝 줄 «세션 없음(kill 0)»."""
    rc, why = tree_dirty(k, intent)
    if rc:                                                 # ③ 그대로(미커밋·판독 실패 = REJECT dirty)
        return k.log("REJECT dirty — [wip] 커밋 먼저", team, "%s 판정 %s · %s · 기록 0 · kill 0" % (seat, n, why)) or 8
    why = resume_dead(k, seat, seat_ok, intent)             # ④ 재개 기록 먼저(kill 0 이라도 남긴다)
    if why:
        return k.log("REJECT 재개 기록", team, "%s 판정 %s · %s · 기록 0 · kill 0" % (seat, n, why)) or 5
    after = k.probe(seat)                                   # K4 — park 직전 부재 판독 1회 더(그새 살아났으면 닫지 않는다)
    if after != "absent":
        return k.log("REJECT kill", team, "%s 판정 %s · 부재 확인 없음(%s)" % (seat, n, after)) or 6
    park, rc = parked(k, team, work, seat, n, reason, latest)   # ⑥ 지금 규칙 그대로
    if rc:
        return rc
    k.log("CLOSED-MANUAL", team, "%s 판정 %s %s #%s park=%s reason=%s%s%s" % (seat, n, seat_ok, seq, park, reason, note + " · 세션 없음(kill 0)", REOPEN_HOW))
    return left_manual(k, team, seat, n, intent) or 0      # r2571 K3 — 끝 줄 바로 뒤 «남은 것» 1줄(삭제 0 · rc 불변)


def hands(k, team, work, attempt, intent, seat, n, seat_ok, seq, reason, note=""):
    """K3 — ⓪장부 ⓠ부재 ①attached ②pane ③dirty ④재개 기록 ⑤kill ⑥park ⑦끝 줄. 실패한 단계에서 멈춘다(뒤 단계 0).
    note = K2·K4 덧말(«정지 중 닫기(…)»·«원장 = 데이터 루트(main 미착지)») — 끝 줄·keeper 로그 줄 꼬리에만 붙는다.
    r2440 K1 — ⓪ 뒤 부재 판독 1회: absent = 죽은 세션 갈래(dead_hands · 사람 화면·pane·kill 0) · alive·판정 불가 = 아래 그대로."""
    latest, why = ledger(k, team)                          # ⓪ 장부를 못 읽으면 소유를 모른다 = 닫지 않는다(DA#56 H2)
    if why:
        return k.log("REJECT 장부", team, "%s 판정 %s · %s · 기록 0 · kill 0" % (seat, n, why)) or 9
    if k.probe(seat) == "absent":
        return dead_hands(k, team, work, seat, n, seat_ok, seq, reason, note, latest, intent)
    seen = k.attached(seat)
    if seen != "free":                                     # ① 사람 화면(못 읽음 = 덜 닫는 쪽)
        return k.log("REJECT attached", team, "%s 판정 %s · %s · 손 0" % (seat, n, seen)) or 4
    rc, pane, _ = k.call([k.tmux, "capture-pane", "-p", "-t", "=" + seat + ":"])
    if rc != 0:                                            # ② pane 판독 실패 = 일하는지 모른다 → 닫지 않는다(DA#56 H1)
        return k.log("REJECT pane 판독", team, "%s 판정 %s · capture-pane rc=%s · 기록 0 · kill 0" % (seat, n, rc)) or 9
    if settle.working(pane):                               # ② 일하는 중 = 못 닫는다(알려진 한계 1)
        return k.log("REJECT busy", team, "%s 판정 %s · pane Working · 손 0" % (seat, n)) or 4
    rc, why = tree_dirty(k, intent)                         # ③ 이 명령은 커밋하지 않는다
    if rc:
        return k.log("REJECT dirty — [wip] 커밋 먼저", team, "%s 판정 %s · %s · 기록 0 · kill 0" % (seat, n, why)) or 8
    why = k.close_old.resume(seat, seat_ok, intent, source="ft2-manual-close")   # ④ 재개 기록 먼저(r2281 그대로)
    if why:
        return k.log("REJECT 재개 기록", team, "%s 판정 %s · %s · 기록 0 · kill 0" % (seat, n, why)) or 5
    k.call([k.tmux, "kill-session", "-t", "=" + seat])      # ⑤ 세션만 닫기 → 부재 확인
    after = k.probe(seat)
    if after != "absent":
        return k.log("REJECT kill", team, "%s 판정 %s · 부재 확인 없음(%s)" % (seat, n, after)) or 6
    park, rc = parked(k, team, work, seat, n, reason, latest)   # ⑥ 소유가 남는 자리 = core park 1회
    if rc:
        return rc
    return k.log("CLOSED-MANUAL", team, "%s 판정 %s %s #%s park=%s reason=%s%s%s" % (seat, n, seat_ok, seq, park, reason, note, REOPEN_HOW)) or 0


def run(k, seat, verdict, approve, reason, wait=LOCK_S):
    """K1 → K4 → K2 → K3 · 반환 = rc(0·2·3·4·5·6·7·8). 줄은 k.log 로 남기고 부르는 쪽(keeper.main)이 그대로 찍는다."""
    hit = verdict_mod.APPROVE.fullmatch((approve or "").strip())
    if not (verdict.isdigit() and hit and len(reason or "") >= MIN_REASON):
        return k.log("REJECT 인자", "", "--verdict <N> --approve \"<planner 좌석> #<seq>\" --reason <10자 이상> 꼴 아님 · 손 0") or 2
    n, (seat_ok, seq) = verdict, hit.groups()
    team, work, attempt, intent, why = target(k, seat)
    if why:
        return k.log("REJECT 대상 아님", "", "%s · %s · 손 0" % (seat, why)) or 2
    if close_bin_missing(k):                            # r2549 K3 — 자리 없음 = 승인 대조·판정기 호출보다 앞
        return k.log("REJECT 닫기 도구 자리 없음", team,
                     "%s 판정 %s · FT_SEAT_CLOSE_BIN 이 빔 · keeper 데몬과 같은 값을 명령 앞에 붙여 다시"
                     "(launchd com.biz.ft2-keeper 의 EnvironmentVariables) · 기록 0 · kill 0" % (seat, n)) or 2
    path = lock(k, wait)
    if path is None:
        return k.log("BUSY", team, "keeper 바퀴 중 — 다시 부르세요 · %s 판정 %s · 손 0" % (seat, n)) or 3
    try:
        why, kind, note = approval(k, seat, work, n, seat_ok, seq)
        if why:
            return k.log("REJECT " + kind, team, "%s 판정 %s · %s · 기록 0 · kill 0" % (seat, n, why)) or 2
        return hands(k, team, work, attempt, intent, seat, n, seat_ok, seq, reason, note)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
