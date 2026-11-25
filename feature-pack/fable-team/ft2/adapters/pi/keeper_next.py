"""ft 2.0 keeper 다음 카드 (r1871 · keeper_close.close 가 닫기 영수 자리에서 부른다 · 코어 손 0).
고르기(읽기만) = 팀 카드 루트(directive-roots.tsv) 대기/ 카드 중 원장 seat·막힌 사유·ft2 owner 없음 → 긴급 → 우선 높음 → since 순 1장.
잇기 = submit → 최초이자 유일한 영수 1회(next·새 holder·evidence) → launch → record · 복구 = 저장 next·holder 로만 launch·record 를
«각각» 맞춘다(새 고르기 0 · handled 는 그 뒤) · 고를 카드 0 일 때만 팀장 [다음 없음] 1통(하루·팀 1키).
r1929 launch = 기다리지 않는다(keeper_launch · 띄우고 다음 바퀴에 의도를 읽어 잇기)."""
import glob, hashlib, importlib.util, json, os, re, sys, time  # noqa: E401

HERE = os.path.dirname(os.path.abspath(__file__))
FT2, GIT_S, PENALTY_S = os.path.dirname(os.path.dirname(HERE)), 25, 7   # r2073 판정기 호출 7초(하드 룰 12)
OK, BLOCK, NONE = "접수 성공", ("정지", "석", "선행", "DA", "사람"), "[다음 없음]"
BLOCKED = "막힘"   # r2361 reconcile 복구 갈래가 «띄우지 않음» 을 알리는 값(fill 이 그 항목을 이 바퀴 셈에서 뺀다 · K5)
URGENT, HIGH = re.compile(r"- 긴급:\s*예\s*$"), re.compile(r"- 우선(?:순위)?:\s*높음")
URGENT_NO = re.compile(URGENT.pattern.replace("예", "아니오"))   # r2509 K1 — «아니오» 꼴 = r2482 lint KEEPER_EMERG_NO 와 같은 정규식(URGENT 의 «예» 자리만 · 새 정규식 0)
REF = re.compile(r"(?<![A-Za-z0-9_])r(\d+)(?![0-9])")   # r2027 카드 참조 r<번호>
MONTH = re.compile(r"/아카이브/\d{4}-\d{2}")   # DA R1 월별 아카이브(루트 뒤 꼬리)
QTS = re.compile(r"[0-9]+\.[0-9]{6}$")   # r2562 K4 — 요청 파일 이름 뒤 칸(질문 ts) · ft_desk_reply_wake.TS 와 같은 꼴
RESUME = re.compile(r"- 재개: (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}) · PR #(\d+) · head ([0-9a-f]{7,40}) · 가지 (\S+)")   # r2159 진행/ 카드 재개 줄(goal-close 재개 구 예시와 같은 꼴)
GH_S, GHREPO = 7, re.compile(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?/?$")   # r2159 gh 7초 + 재시도 1(하드 룰 12)
MOVED = ("완성", "완성후", "아카이브")   # r2114 A1 대기에서 옮겨진 카드 단계(짝 표 대기 경로 = 줄 0)
WAIT = "- 대기 사유:"   # r2205 O2 대기 사유 표식 줄 머리(값이 풀기 값이 아니면 막음)
MARK, SHELL = ("사람", "정지", "DA", "lint", "면제대기", "선행"), ("- 상태: 대기(NEW_CARD_HOLD", "- 대기(NEW_CARD_HOLD")   # r2093 S1 껍데기 표식 줄 두 꼴   # r2058 L9 — 카드 «- 배정: 대기(<사유> · …)» 의 막는 사유(새 표식 · «석» 은 여기 없다)
def prereq(lines, where):
    """r2027 카드 본문 선행 막힘 = "" · "선행" · "선행불명"(판정 불가) · where = {번호: 카드가 있는 폴더 집합}.
    반환 = (판정, 까닭) — 까닭은 선행불명일 때만 찬다(`번호 참조 없음` · `루트에 없는 번호 r<a> r<b> …` · 없는 번호 전부·번호 순 · I2·I3).
    r2058 L9 — «- 배정: 대기(<사유> · 시각)» 의 사유가 사람·정지·DA·lint·면제대기·선행 이면 그 사유 그대로 막는다(«대기(석» 은 새 표식이 아니다).
    r2395 K1 — «- 배정:» 줄도 «- 대기 사유:» 줄도 없는 카드 = "표식없음"(판정 근거 0 · 나노 열기 0)."""
    if any(x.startswith(SHELL) for x in lines):   # r2093 S1 — 두 표식 줄이 있을 때만(«- 배정: 대기(» 사유와 따로 · MARK 손 0 · DA R1)
        return "껍데기", ""
    if not any(x.startswith(("- 배정", WAIT)) for x in lines):   # r2395 K1 — 표식 두 줄이 다 없으면 판정 불가(«대기 사유 «사전 DA 전»» 글자만 있는 카드가 열리던 자리 · 값 꼴은 안 본다)
        return "표식없음", ""
    mark = next((x[len("- 배정: 대기("):].split(" · ")[0].strip().rstrip(")").strip() for x in lines if x.startswith("- 배정: 대기(")), "")
    if mark in MARK:
        return mark, ""   # ① 카드 배정 줄(원장·owner 를 본 뒤의 자리)
    wait = next((x[len(WAIT):].strip() for x in lines if x.startswith(WAIT)), "")
    if wait and not wait.startswith(("없음", "충족", "—", "-", "0")):
        return "대기사유", wait   # r2205 O2·O3 — 배정 대기 뒤·선행 앞 · 까닭 = 그 값(NEXT-SKIP 기억)
    val = next((x.split(":", 1)[1].strip() for x in lines if x.startswith("- 선행:")), "")
    if not val or val.startswith(("없음", "충족", "0", "—", "-")):
        return "", ""   # ② r1941 없음·충족·0·— = 막지 않음(주인이 고친 줄)
    nums = REF.findall(val)
    seen = [where.get(n, set()) for n in nums]
    if not seen:
        return "선행불명", "번호 참조 없음"   # ④ r 참조 없는 글
    if any(s & {"대기", "진행"} for s in seen):
        return "선행", ""   # ③ 안 끝난 참조
    if all(s & {"완성", "완성후", "아카이브"} for s in seen):
        return "", ""   # 끝난 참조
    miss = sorted({n for n in nums if not where.get(n)}, key=int)   # I2 없는 번호는 전부(첫 번호만 적지 않는다 · 번호 순)
    return "선행불명", "루트에 없는 번호 " + " ".join("r" + n for n in miss or sorted(set(nums), key=int))   # 루트에 없는 참조 = 판정 불가
def _load(name):
    spec = importlib.util.spec_from_file_location("ft2_keeper_next_" + name, os.path.join(FT2, "core", name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
cli, dispatch = _load("cli"), _load("dispatch")
_kl = importlib.util.spec_from_file_location("ft2_keeper_next_launch", os.path.join(HERE, "keeper_launch.py"))
kl = importlib.util.module_from_spec(_kl)
_kl.loader.exec_module(kl)
_lp = importlib.util.spec_from_file_location("ft2_keeper_next_plan", os.path.join(HERE, "launch_plan.py"))
lp = importlib.util.module_from_spec(_lp)   # r2030 짝 표 대기 카드(mapped_cards) = 발주문·sparse 와 같은 함수
_lp.loader.exec_module(lp)
_mb = importlib.util.spec_from_file_location("ft2_keeper_next_model_block", os.path.join(HERE, "model_block.py"))
mb = importlib.util.module_from_spec(_mb)   # r2490 K6 — 계정 정지 게이트가 읽는 표식·대체 표(읽기만)
_mb.loader.exec_module(mb)
def ft2_state(k, team):
    try:
        return dispatch.Dispatch(k.root, team).ex._state_records()[0]
    except ValueError:
        return None
def once(k, key, read):
    """r1969 바퀴 캐시 — 같은 바깥 읽기 = 바퀴당 1회(팀 사이 공유) · keeper._round 가 열고 닫음(바퀴 밖 = 캐시 0) · kill·launch 뒤 ls 버림(keeper.call)."""
    got, fn = k.cache.get("@round"), read if callable(read) else lambda: k.call(read)
    return fn() if got is None else got[key] if key in got else got.setdefault(key, fn())
NANO_SEAT = re.compile(r"^biz-(?P<team>[a-z0-9]+)-nano-(?P<k>\d+)-(?P<slug>[^#]+)#(?P<gen>\d+)$")   # r2504 나노 이름 석 칸 꼴

def seat_of(name):
    """r2504 — 나노 이름 → (석, 세대) · 옛 꼴(석 칸 없음)·다른 꼴 = None."""
    got = NANO_SEAT.match(name) if isinstance(name, str) else None
    return (int(got.group("k")), int(got.group("gen"))) if got else None

def slug_of(name):
    """r2504 — 나노 이름 → slug(석 칸·세대를 뗀 가운데) · 옛 꼴(석 칸 없음) = slug 그대로 · 나노 이름 아님 = "".
    이름겹침 판독은 slug 로 본다 — 석 칸·세대가 붙어도 같은 카드는 같은 slug(옛 꼴로 떠 있는 세션도 겹침으로 센다)."""
    if not isinstance(name, str) or "#" not in name:
        return ""
    base, _, gen = name.rpartition("#")
    if not gen.isdigit():
        return ""
    got = re.match(r"^biz-[a-z0-9]+-nano-(?:(\d+)-)?(.+)$", base)
    return got.group(2) if got else ""

def seat_used(k, team):
    """r2504 — 이 팀 나노 석 점유 근거 = 산 세션 ∨ 배정 holder(ft2 owners) → ({석: 그 석의 최대 세대}, 사유).
    사유 = "" 이면 두 근거를 다 읽었다 · 아니면 «판독 실패» 글자(그 바퀴는 이름을 안 짓는다 · 빈 점유와 구분 · DA H1).
    예약 파일 0(master 결정 B · keeper 바퀴 잠금 안에서 이름 짓기와 assign 이 직렬) · 배정 전에 죽은 바퀴 = 근거 0(석 안 쥔다) ·
    같은 바퀴 두 장 = 앞 카드의 배정 holder 가 근거(assign 이 곧바로 owners 를 쓴다)."""
    names, why = set(), ""
    try:
        rc, out, _ = once(k, "ls", [k.tmux, "list-sessions", "-F", "#{session_name}"])
    except (AttributeError, OSError, TypeError, ValueError):
        rc, out = -1, ""
    if rc != 0:
        why = "tmux list-sessions rc %s" % rc   # 판독 실패 = 빈 점유가 아니다(DA H1 · 이 바퀴 이름 짓기 0)
    else:
        names |= set((out or "").split())
    try:
        st = ft2_state(k, team)
    except (AttributeError, OSError, TypeError, ValueError):
        st = None
    if st is None:
        why = why or "ft2 state 판독 실패"
    else:
        for row in (st.get("owners") or {}).values():
            if isinstance(row, dict) and isinstance(row.get("holder"), str):
                names.add(row["holder"])
    head, seen = "biz-%s-nano-" % team, {}
    for name in names:
        got = seat_of(name) if name.startswith(head) else None
        if got:
            seen[got[0]] = max(seen.get(got[0], -1), got[1])
    for seat, gen in seen.items():   # 세대 장부 — 배정 근거에서 본 이름만 남긴다(닫힌 석의 세대도 남아 다음 이름이 +1)
        key, book = "%s|%d" % (team, seat), seat_book(k)
        if isinstance(book.get(key), int):
            book[key] = max(book[key], gen)
        else:
            book[key] = gen
    return seen, why

def seat_book(k):
    """r2504 — 석 세대 장부(state["nano_seat"] · 팀|석 → 지금까지 본 최대 세대) · state 없는 keeper(가짜) = 휘발 딕셔너리(기억 0)."""
    state = getattr(k, "state", None)
    book = state.setdefault("nano_seat", {}) if isinstance(state, dict) else {}
    return book if isinstance(book, dict) else {}

def node(k, team, why, stem):
    """r2504 — 석을 못 읽어 이름을 안 지은 바퀴의 «판정 불가» 1줄(팀·사유가 바뀔 때만 · 같은 바퀴 되풀이 0)."""
    state = getattr(k, "state", None)
    book = state.setdefault("seat_seen", {}) if isinstance(state, dict) else {}
    text = (why or "")[:60]
    if not isinstance(book, dict) or book.get(team) == text:
        return None
    book[team] = text
    return k.log("판정 불가", team, "%s 나노 이름 — 석 점유 근거 판독 실패(%s) · 이 바퀴 이름 짓기·assign 0" % (stem, text))

def assigned(k, team, stem):
    """r2504 — 이 카드에 이미 지어진 이름 = 원장 seat → ft2 배정 holder · 없으면 "" · 판독 실패 = None(이름 짓기 0)."""
    led = ledger(k, stem)
    if not isinstance(led, dict):
        return None   # 원장 판독 실패 = «없음» 이 아니다(DA H1)
    if led.get("state") == "seat" and isinstance(led.get("seat"), str) and led["seat"]:
        return led["seat"]
    try:
        st = ft2_state(k, team)
    except (AttributeError, OSError, TypeError, ValueError):
        st = None
    if st is None:
        return None
    row = ((st.get("owners") or {}).get(stem)) or {}
    got = row.get("holder") if isinstance(row, dict) else None
    return got if isinstance(got, str) else ""

def nano_name(k, team, stem):
    """r2016 나노 좌석 이름 = stem 앞 40자 · 끝 «-» 지움(1.x ft-nano-spawn.sh _slug 와 같은 규칙) · 빈 값 = None + 경고 1줄(지어내기 0).
    r2113 A2 — 40자 넘게 잘리는 stem = 앞 33자(끝 «-» 지움) + «-» + sha1(stem) 앞 6자(후속 카드와 겹침 0).
    r2208 O2 — 셈한 이름은 소문자(좌석 이름 문법) · sha1 꼬리는 원래 stem · 원장 seat 이름은 그대로(O3).
    r2504 — 석 칸 + 세대: `biz-<팀>-nano-<석K>-<slug>#<세대N>` · 석 K = 점유 근거(seat_used) 밖 가장 작은 수 · 세대 = 그 석의 최대 + 1.
    이미 지은 이름(원장 seat · 배정 holder)이 있으면 그대로 돌려준다 — 소비자(재개 · 충돌 · 닫기 · 채우기)는 이 함수로 같은 값을 읽는다.
    판독 실패(원장 · ft2 state · tmux) = None + «판정 불가» 1줄 — 빈 점유로 세지 않고 그 바퀴는 이름을 안 짓는다(DA H1 · 채우기 0)."""
    held = assigned(k, team, stem)
    if held is None:
        return node(k, team, "원장·ft2 state 판독 실패", stem)
    if held:
        return held
    cut = stem[:40].rstrip("-")
    if len(stem) > 40 and cut:
        cut = stem[:33].rstrip("-") and "%s-%s" % (stem[:33].rstrip("-"), hashlib.sha1(stem.encode("utf-8")).hexdigest()[:6])
    if not cut:
        return k.log("경고", team, "%s 나노 이름 빈 값 — 그 카드 0" % stem)
    used, why = seat_used(k, team)
    if why:
        return node(k, team, why, stem)
    seat = 0
    while seat in used:
        seat += 1
    key, top = "%s|%d" % (team, seat), used.get(seat, -1)
    book = seat_book(k).get(key)
    return "biz-%s-nano-%d-%s#%d" % (team, seat, cut.lower(), (max(top, book) if isinstance(book, int) else top) + 1)
def ledger(k, stem):
    return k.read_json(os.path.join(k.root, ".fable-team", "state", "card-assign", stem + ".json"))
def skip_landed(k, team, stem):
    """r2058 L5 — 착지 판독(바퀴 캐시 · 카드당 1회) 참 = fill·닫기 뒤 pick 둘 다 고르지 않는다 · `NEXT-SKIP` 1줄(값이 바뀔 때만)."""
    landed = once(k, ("landed", team, stem), lambda: k.landing(team, stem))
    yes = bool(landed[0]) and not landed[2]
    val = yes or (landed[2] if str(landed[2] or "").startswith("판정 불가") else False)   # r2262 C2 기억 값 셋 = 착지 · 판정 불가 사유 전문 · 거짓
    book, key = k.state.setdefault("next_skip", {}), "%s|%s" % (team, stem)
    if book.get(key) != val:
        book[key] = val
        if yes:
            k.log("NEXT-SKIP", team, "%s 이미 착지 — 카드 정리 필요" % stem)
        elif val:
            k.log("NEXT-SKIP", team, "%s 착지 판정 불가(%s) — 이 바퀴 보류" % (stem, val[:40]))
    return yes
def landed_hold(k, team, stem):
    """r2262 C1 — 착지 판독(같은 바퀴 캐시) 사유가 «판정 불가» 로 시작 = block «판정 불가»(이 바퀴만 · 원장 쓰기 0 · [다음 없음] 0) · 그 밖 = ""."""
    return "판정 불가" if str(once(k, ("landed", team, stem), lambda: k.landing(team, stem))[2] or "").startswith("판정 불가") else ""
def noleft(k, team, alive):
    """r2400 K5 — 지난 바퀴에 «근거 없는 석» 으로 남은 좌석(이제 없는 세션 · 활동이 돌아온 석은 뺀다 · 사라진 다음 바퀴 = 관문 열림).
    하나라도 있으면 harness master [긴급] 하루 1통(석 이름 · 갈래) → r2498 1석은 그 석만 정원 1칸으로 세고 열기 계속 · 2석부터 다음 카드 0."""
    got = {}
    for seat, row in ((k.state.get("noleft") or {}).get(team) or {}).items():
        files = [p for p in (row.get("files") or ()) if os.path.isfile(p)]
        age = k.now() - max(map(os.path.getmtime, files)) if files else None
        if seat in alive and (age is None or age >= int(row.get("idle") or 0)):   # K1 다시 참 = 아직 근거 없음
            got[seat] = row.get("why") or "갈래 불명"
    if not got:
        return 0
    k.notify("harness", "noleft|%s|%s" % (team, k.stamp()[:10]),   # 받는 곳 = harness master(카드 K5 · 팀 아님)
             "[긴급] ft2 keeper %s 근거 없는 석 %d석 — 닫지 못했다 · %s · 사람 손 필요(%s)"
             % (team, len(got), "그 석만 세움 · 열기 계속" if len(got) == 1 else "다음 나노 열기 0",
                " · ".join("%s %s" % (s, w) for s, w in list(got.items())[:2])))
    return len(got)
def guard(k, team):
    """r2509 K2 — gates 의 앞 절반(켜기 전·팀 정지·spawn·계정 정지·근거 없는 석). 반환 = (통과, 근거 없는 석 수 n) — n 은 r2498 좁힘 줄(gates)이 쓴다.
    통과 = True · 막힘 = False 또는 로그 줄(값 None) · 로그·판독은 gates 그대로(한 함수 = 두 부름이 같은 값을 본다).
    나노 정원 판독은 뒤 절반(gates 끝) — 쉼 판정(spare)은 관문 다음에 정원을 따로 본다."""
    st = os.path.join(k.root, ".fable-team", "state")
    if not os.path.exists(os.path.join(k.root, ".fable-team", "teams", team, "CLOSE-NEXT.enabled")) or os.path.lexists(os.path.join(st, "%s-tick" % team, "PAUSED")):
        return False, 0
    for name, tool, args, on in (("SPAWN_HOLD", "spawn-hold", [str(k.read_json(os.path.join(st, "SPAWN_HOLD")).get("verdict"))], 0), ("ACCT_PAUSE", "acct-pause", ["--agent", "pi"], 3)):
        rc = once(k, tool, ["bash", os.path.join(os.path.dirname(k.close_bin or ""), "ft-%s.sh" % tool), "status", "--check"] + args)[0] if os.path.lexists(os.path.join(st, name)) else 3 - on
        if rc == on and name == "ACCT_PAUSE" and mb.gate_open(k, team, "nano"):   # r2490 K6 — 기본 모델 공급자에 표식 ∧ 대체가 정해짐 = 다음 카드 연다(표식 줄은 keeper 가 이미 냈다)
            continue
        if rc != 3 - on:   # 끔 = hold rc3 · acct rc0 — 유효·판정 불가 = 0
            return k.log("NEXT-HOLD", team, "%s %s rc %s — 다음 카드 0" % (name, "유효" if rc == on else "판정 불가", rc)), 0
    rc, out, _ = once(k, "ls", [k.tmux, "list-sessions", "-F", "#{session_name}"])   # r1969 바퀴당 1회 · 여는 중 합집합은 부를 때마다
    alive = set(out.split()) if rc == 0 else set()
    n = noleft(k, team, alive) if alive else 0   # r2498 그 석 이름 = biz-<팀>-nano-* 라 아래 live 에 이미 1칸으로 세어진다(정원에 더하지 않는다)
    if n > 1:   # r2400 K5 — 둘 이상 = 닫는 길이 고장났다는 신호 = 그 팀 열기 통째 0(지금과 같은 글)
        return k.log("NEXT-HOLD", team, "근거 없는 석 %d — 다음 카드 0" % n), 0
    return True, n
def nano_cap(k, team):
    """r2509 — 나노 상한 문자열(env > thresholds · r1860 순서) · 못 정함 = ""(gates 가 판정 불가 1줄)."""
    home = os.path.join(k.env.get("HOME") or os.path.expanduser("~"), ".claude", "fable-team", "thresholds.env")
    files = [p for p in (os.path.join(k.root, ".fable-team", "thresholds.env"), home, os.path.join(HERE, "thresholds.env.sample")) if os.path.isfile(p)]
    return (k.env.get("FT2_TEAM_NANO_MAX") or next((x.split("=", 1)[1].strip() for p in files for x in open(p, encoding="utf-8") if x.startswith("FT2_TEAM_NANO_MAX=")), "")).strip()
def nano_live(k, team):
    """r2509 — 쉼 판정(spare)이 쓰는 «지금 이 팀 나노 석 수» · 셈은 gates 안 그 줄과 같은 한 줄(r2498 시험 변이 M2 가 gates 안 줄을 본다) · list-sessions 실패 = None."""
    rc, out, _ = once(k, "ls", [k.tmux, "list-sessions", "-F", "#{session_name}"])
    alive = set(out.split()) if rc == 0 else set()
    return sum(x.startswith("biz-%s-nano-" % team) for x in alive | k.cache.get("launching", set())) if rc == 0 else None
def gates(k, team):
    """참 = 다음 카드 칸이 열림 · 거짓 = 0(켜기 전·팀 정지·spawn·계정 정지·나노 상한 · 판정 불가 포함).
    r2509 — 앞 반쪽 = guard(같은 값·같은 줄) · 반환 = guard 가 낸 그대로(True·False·None — 로그 줄은 None)."""
    got, n = guard(k, team)   # r2498 좁힘 줄이 쓰는 n = guard 가 센 근거 없는 석 수
    if got is not True:
        return got
    cap = nano_cap(k, team)
    if not (cap.isascii() and cap.isdigit()):   # R3 — 못 정함 = 새 실행 0(임의 기본값 0)
        return k.log("판정 불가", team, "나노 상한 FT2_TEAM_NANO_MAX 못 정함(%r · env·thresholds.env) — 다음 카드 0" % cap[:20])
    rc, out, _ = once(k, "ls", [k.tmux, "list-sessions", "-F", "#{session_name}"])   # r1969 바퀴당 1회 · 여는 중 합집합은 부를 때마다
    alive = set(out.split()) if rc == 0 else set()
    live = sum(x.startswith("biz-%s-nano-" % team) for x in alive | k.cache.get("launching", set())) if rc == 0 else None   # r1929 여는 중 = 1칸
    k.fa.observe(k.root, "나노 정원", team, live, int(cap), "다음 카드")   # r1886 ⓑ 열림·NEXT-HOLD 둘 다
    if live is not None and live < int(cap):
        if n:   # r2498 좁힘 — 근거 없는 석 1개는 정원 1칸만 쥐고 남은 칸으로 다음 카드를 연다(멈춤의 범위를 석 1개로 줄인다)
            k.log("NEXT-NARROW", team, "근거 없는 석 1 — 그 석만 · 정원 %s / %s" % (live, cap))
        return True
    return k.log("NEXT-HOLD", team, "나노 %s / 상한 %s — 다음 카드 0" % (live, cap))
def penalty_seen(k, team, val):
    """r2073 P6·P7 — 값이 바뀔 때만 1줄 · 기억은 keeper 상태 파일(state["penalty_seen"][팀]) · val = "" 열림 · "hold" 재개 전 · "rc <값>" 판정 불가."""
    book = k.state.setdefault("penalty_seen", {})
    if book.get(team, "") == val:   # 같은 값 = 줄 0(재기동해도 상태 파일에 남아 있다)
        return not val
    if val:
        book[team] = val
        k.log("NEXT-HOLD" if val == "hold" else "판정 불가", team,
              "PENALTY_STOP 재개 전 — 다음 카드 0" if val == "hold" else "PENALTY_STOP 판독 %s — 다음 카드 0" % val)
        return False
    book.pop(team, None)   # 기억에 있던 팀이 풀렸다 = 이때만 1줄
    k.log("NEXT-OPEN", team, "PENALTY_STOP 풀림")
    return True
def penalty_open(k, team):
    """r2073 P1·P2 — 참 = 새 카드를 넣어도 됨. state/PENALTY_STOP 없음 = 참(판정기 호출 0) · 있음 = ft-penalty.sh check <팀>
    rc 0 = 참 · rc 3 = 거짓 · 그 밖(rc 1·2 · 도구 없음 · 시간 초과) = 거짓 + 판정 불가. 판정기는 1.x ft_penalty.py 한 곳이 한다(JSON 직접 풀기 0)."""
    if not os.path.exists(os.path.join(k.root, ".fable-team", "state", "PENALTY_STOP")):
        return penalty_seen(k, team, "")
    judge = k.env.get("FT2_PENALTY_BIN") or os.path.join(os.path.dirname(k.close_bin or ""), "ft-penalty.sh")
    rc = once(k, ("penalty", team), lambda: penalty_rc(k, judge, team))   # 팀당 바퀴 1회
    return penalty_seen(k, team, "" if rc == 0 else "hold" if rc == 3 else "rc %s" % rc)
def penalty_rc(k, judge, team):
    """판정기 1회 = rc(k.call 은 실패·시간 초과를 None 으로 준다) · 판정기는 FT_ROOT 로 루트를 받는다."""
    outer, k.env = k.env, dict(k.env, FT_ROOT=k.root)
    try:
        return k.call(["bash", judge, "check", team], PENALTY_S)[0]
    finally:
        k.env = outer
def new_card_hold(k, team):
    """r2101 H1~H5 — 새 카드 보류 설정 1개(state/NEW_CARD_HOLD.json) · 참 = 카드 고르기 두 곳(fill pick·닫기 뒤 pick)만 막힌다.
    판독 = 바퀴당 1회(once · 팀 사이 공유) · 없음 = 거짓(열림) · 있음 = 참 + 팀마다 `NEW-CARD-HOLD <reason> · until <until>` 1줄(값이 바뀔 때만) ·
    깨짐(빈 파일·JSON 아님·reason 없음) = 참 + `판정 불가` 1줄. gates()·ALL_STOP·팀 PAUSED·팀장 개설은 안 본다(H7·H8)."""
    got = once(k, "new-card-hold", lambda: hold_read(k, os.path.join(k.root, ".fable-team", "state", "NEW_CARD_HOLD.json")))
    book = k.state.setdefault("new_card_hold_seen", {})
    val = "" if got is None else "깨짐" if isinstance(got, str) else "|".join(got)
    if book.get(team, "") == val:   # 같은 값 = 줄 0(재기동해도 상태 파일에 남아 있다)
        return bool(val)
    if not val:   # 기억에 있던 팀이 풀렸다 = 이때만 1줄
        book.pop(team, None)
        k.log("NEW-CARD-OPEN", team)
        return False
    book[team] = val
    if isinstance(got, str):
        k.log("판정 불가", team, "NEW_CARD_HOLD 판독 불가(빈 파일·JSON 아님·reason 없음) — 새 카드 0")
    else:
        k.log("NEW-CARD-HOLD", team, "%s · until %s" % got)
    return True
def hold_read(k, path):
    """H1·H2 판독 1회 — 없음 = None · 있음 = (reason, until) · 깨짐 = "깨짐"(추측 채움 0)."""
    if not os.path.lexists(path):
        return None
    data, reason = k.read_json(path), ""
    if isinstance(data.get("reason"), str):
        reason = data["reason"].strip()
    if not reason:   # 빈 파일·JSON 아님(read_json = {})·reason 없음
        return "깨짐"
    return reason, str(data.get("until") or "").strip() or "-"
def cards(k, team, unread=None, resume=True):
    """({stem: [긴급, 높음, 대상 줄들, 선행 막힘, 기억 값, 재개 줄들(r2113)]}, 루트 행) · 판독 실패 = 사유 문자열 (git 2회 · 작업 트리 0) · resume=False = progress 0(r2267 휴면 길)."""
    try:
        with open(os.path.join(k.root, ".fable-team", "state", "directive-roots.tsv"), encoding="utf-8") as fh:
            rows = [x.rstrip("\n").split("\t") for x in fh if not x.startswith("#") and len(x.split("\t")) >= 4]
    except (OSError, UnicodeError):
        rows = []
    r = next((x for x in rows if x[0] == team), None) or next((x for x in rows if x[0] == "*"), None)
    if not r:
        return "카드 루트 표 행 없음"
    raw, r = r[3], [r[0], os.path.join(k.root, r[1]), r[2], r[3].replace("*", team)]   # r1969 raw git = (리포·ref·표 행 루트) 바퀴당 1회 · 팀 걸러내기는 따로
    rc, names, err, rc2, heads = once(k, ("cards", r[1], r[2], raw), lambda: k.git(r[1], "ls-tree", "-r", "--name-only", r[2], "--", raw.split("*")[0] if "*" in raw else raw + "/")   # r2027 루트 전체 = 선행 참조 폴더
                                      + k.git(r[1], "grep", "-I", "-E", r"^- (긴급|우선|대상|선행|배정|대기 사유:|재개:|세트:|상태: 대기\(NEW_CARD_HOLD|대기\(NEW_CARD_HOLD)", r[2], "--", ":(glob)%s/대기/*" % raw, ":(glob)%s/진행/*.md" % raw)[:2])   # r2159 진행/ = 재개·대상 줄만 씀
    if rc != 0 or rc2 not in (0, 1):
        return "카드 루트 git rc %s/%s %s" % (rc, rc2, err[:60])
    mine = r[3] + "/대기"
    found = {os.path.basename(p)[:-3]: [False, False, [], [], None, [], [], False] for p in names.splitlines() if p.endswith(".md") and os.path.dirname(p) == mine}   # r2573 H2 — 8번째 칸 = «- 세트:» 증거 줄 있음(인수 끝·착지 대기 = 안내 0줄)
    where, prog = {}, {}
    for p in (x for x in names.splitlines() if x.endswith(".md") and (os.path.dirname(os.path.dirname(x)) == r[3] or x.startswith(r[3] + "/") and MONTH.fullmatch(os.path.dirname(x)[len(r[3]):]))):
        m = re.match(r"r(\d+)(?![0-9])", os.path.basename(p))   # DA R1 · 아카이브/<YYYY-MM>/ = 아카이브
        where.setdefault(m.group(1), set()).add("아카이브" if os.path.dirname(os.path.dirname(p)) != r[3] else os.path.basename(os.path.dirname(p))) if m else None
    for path, _, line in (x[len(r[2]) + 1:].partition(":") for x in heads.splitlines()):
        row = found.get(os.path.basename(path)[:-3]) if os.path.dirname(path) == mine else None
        if row is not None:
            row[0], row[1] = row[0] or bool(URGENT.match(line)), row[1] or bool(HIGH.match(line))
            row[2] += [line] if line.startswith("- 대상") else []
            row[3] += [line] if line.startswith(("- 선행", "- 배정", WAIT) + SHELL) else []
            row[5] += [line] if line.startswith("- 재개:") else []   # r2113 A1
            row[7] = row[7] or bool(SET_SHOW.search(line))   # r2573 H2 — 카드 머리 «- 세트: <40hex> · 시험: … rc=0 · 이슈: 0» 줄
            row[6] += [line] if line.startswith("- 긴급") else []   # r2509 K1 꼴 검사용 «- 긴급:» 줄 그대로
        elif os.path.dirname(path) == r[3] + "/진행" and line.startswith(("- 재개:", "- 대상")):
            prog.setdefault(path, []).append(line)   # r2159 진행/ 카드 = 재개·대상 줄만(나머지 줄 버림)
    mapped(k, team, found, where, set() if unread is None else unread)   # r2030 짝 표 대기 카드(팀 폴더 밖 포함)
    for row in found.values():
        val = next((x.split(":", 1)[1].strip() for x in row[3] if x.startswith("- 선행:")), "")   # I1 기억에 넣을 선행 값 그대로
        verdict, why = prereq(row[3], where)
        row[3], row[4] = verdict, {"val": val, "why": why}   # row[4] = I1·I6 기억 값
    prog = prog if resume else {}   # 빈 prog = progress 첫 줄에서 {}(gh·resume_seen 0)
    r.append(progress(k, team, r, found, prog))
    return found, r
def resume_line(line):
    """r2159 진행/ 카드 재개 줄 → (시각, PR 번호, head sha, 가지) · 꼴 아님·없는 날짜 = None."""
    m = RESUME.fullmatch(line.strip())
    try:
        return m.groups() if m and time.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S") else None
    except ValueError:
        return None
def resume_say(k, team, stem, why, part="pr"):
    """r2159 T2 — 재개 막힘 사유 1줄(값이 바뀔 때만 · keeper 상태 파일) → 막힌 사유 낱말("" = 열림)."""
    book, key = k.state.setdefault("resume_seen", {}), "%s|%s|%s" % (team, stem, part)   # part = PR 대조(pr) · 열기 막음(open) 기억 따로
    if why and book.get(key) != why:
        k.log("판정 불가" if why.startswith("판정 불가") else "NEXT-SKIP", team, "%s 재개 건너뜀 — %s" % (stem, why))
    book[key] = why
    return why.split(" ", 1)[0] if not why.startswith("판정 불가") else "판정 불가"   # r2262 변이 M2 대상 글자와 겹침 0
def progress(k, team, r, found, prog):
    """r2159 T1·T2 — 진행/ 카드 중 «- 재개:» 줄 있는 정렬 첫 장 1장만 PR 대조(바퀴 캐시) → {stem: (리포, headRefOid 40자, 재개 시각)} · 그 카드 = found 후보.
    prog = cards 의 raw grep(바퀴 1회 · r1969) 중 진행/ 카드 재개·대상 줄 · 재개 줄 없는 진행/ 카드 = 버림 · 대기/ 에 같은 stem = 0 · 막힘 = {} + 1줄(resume_say)."""
    path = min((p for p, v in prog.items() if os.path.basename(p)[:-3] not in found and any(x.startswith("- 재개:") for x in v)), default=None)
    if path is None:
        return {}
    back, lines = [x for x in prog[path] if x.startswith("- 재개:")], [x for x in prog[path] if x.startswith("- 대상")]
    stem, got, place = os.path.basename(path)[:-3], resume_line(back[-1]), target(k, r, lines)
    why = ("재개 줄 꼴 깨짐 %r — 고칠 꼴 «- 재개: YYYY-MM-DDTHH:MM:SS · PR #<N> · head <sha> · 가지 <headRefName>»" % back[-1][:60] if not got
           else "대상 팩·BIZ 둘 다" if place is None else "")
    oid, why = once(k, ("progress-pr", team, path, back[-1]), lambda: pr_head(k, place[0], got)) if not why else (None, why)
    if resume_say(k, team, stem, why):
        return {}
    found[stem] = [False, False, lines, "", {"val": "", "why": ""}, back, [], False]
    return {stem: (place[0], oid, got[0])}
def pr_head(k, repo, got):
    """(시각, PR 번호, head, 가지) → (headRefOid 40자, "") · 막힘 = (None, 사유) — PR 닫힘·머지됨·가지 다름·head 바뀜·gh 판정 불가."""
    url = k.git(repo, "config", "--get", "remote.origin.url")[1].strip()
    slug = GHREPO.search(url)
    rc, out, _ = k.call([k.env.get("FT2_GH") or "gh", "pr", "list", "-R", slug.group(1) if slug else url, "--head", got[3], "--state", "all", "--limit", "5",
                         "--json", "number,state,headRefOid,headRefName"], GH_S, retry=1)
    try:
        prs = json.loads(out) if rc == 0 else None
    except ValueError:
        prs = None
    if not isinstance(prs, list):
        return None, "판정 불가 gh pr list rc %s" % rc
    pr = next((p for p in prs if isinstance(p, dict) and str(p.get("number")) == got[1]), None)
    oid = str((pr or {}).get("headRefOid") or "")
    if pr is None or pr.get("state") != "OPEN":
        return None, "PR #%s %s" % (got[1], pr.get("state") if pr else "가지 %s 에 없음" % got[3])
    if pr.get("headRefName") != got[3]:
        return None, "가지 다름 %s ≠ %s" % (pr.get("headRefName"), got[3])
    if not (re.fullmatch(r"[0-9a-f]{40}", oid) and oid.startswith(got[2])):
        return None, "head 바뀜 %s ≠ %s" % (oid[:10], got[2])
    return oid, ""
def resumed(k, team, stem, led, at, works, state, owners, done):
    """r2159 T1·T2 — 재개 진행/ 카드 막힘 낱말("" = 연다) · 옛 seat·새 이름 세션 = k.probe · 시각 ≤ intent · 기존 worktree dirty · 대소문자 겹침(clash)."""
    old = led.get("seat") if led.get("state") == "seat" and isinstance(led.get("seat"), str) else ""
    why = "배정됨 ft2 owner" if stem in owners else "끝남 ft2 done" if works & set(done) else ""
    for seat in ([] if why else sorted({old, nano_name(k, team, stem) or ""} - {""})):
        seen = k.probe(seat)
        why = why or ("" if seen == "absent" else "이름겹침 %s 살아 있음" % seat if seen == "alive" else "판정 불가 %s" % seen)
    return resume_say(k, team, stem, why or intent_after(k, team, works, state, at) or dirty(k, team, stem), "open") or clash(k, team, stem)
def intent_after(k, team, works, state, at):
    """⑪ 재개 시각 ≤ 그 work 의 attempt intent 시각(started 먼저 · 없으면 at · 같은 로컬 꼴) = 막음 · 못 읽음 = 판정 불가."""
    mark = time.mktime(time.strptime(at, "%Y-%m-%dT%H:%M:%S"))
    for w, a in ((w, a) for w in sorted(works) for a in (state.get("deliveries") or {}).get(w) or []):
        got = k.read_json(os.path.join(kl.projection.runtime_path(k.root, team), "launch", "%s@%s.intent" % (w, a)))
        try:
            t = float(got["started"]) if "started" in got else time.mktime(time.strptime(got.get("at"), "%Y-%m-%dT%H:%M:%S"))
        except (TypeError, ValueError):
            return "판정 불가 intent %s@%s 시각 못 읽음" % (w, a)
        if t >= mark:
            return "재개시각 %s ≤ intent %s@%s" % (at, w, a)
    return ""
def dirty(k, team, stem):
    """⑦ 그 work 의 기존 worktree(teams/<팀>/worktrees/<stem>@*) 중 git status 가 빈 줄 아님 = 막음 · 못 읽음 = 판정 불가."""
    for tree in sorted(p for p in glob.glob(glob.escape(os.path.join(k.root, ".fable-team", "teams", team, "worktrees", stem)) + "@*") if os.path.isdir(p)):
        rc, out, _ = k.git(tree, "status", "--porcelain")
        if rc != 0 or out.strip():
            return "판정 불가 worktree %s git status rc %s" % (os.path.basename(tree), rc) if rc != 0 else "worktree %s 깨끗하지 않음 %d줄" % (os.path.basename(tree), len(out.splitlines()))
    return ""
def mapped(k, team, found, where, unread):
    """r2030 짝 표 대기 카드 → found 후보(같은 stem 1개) · 그 카드 indices 의 완성·완성후·아카이브(월별 포함) 참조 → where(DA R2).
    짝 work ≠ 카드 stem(별칭) = 후보 0 + 1줄(DA R1 · 별칭 기동 지원 0) · 판독 실패 = 지금 길 + 1줄."""
    mc = lp.mapped_cards(k.root, team)
    if isinstance(mc, str):
        unread.add("*")   # r2210 O5 짝 표 판독 실패 = 빠진 카드를 «사라짐» 으로 보지 않는다
        return once(k, ("map-log", team), lambda: k.log("경고", team, "%s — 팀 폴더 대기 카드만" % mc))
    for work, (repo, ref, path) in sorted(mc.items()):
        stem, idx = os.path.basename(path)[:-3], lp.WAIT.match(path).group(1)
        if work != stem:
            once(k, ("map-alias", team, work), lambda: k.log("경고", team, "짝 표 별칭 — keeper 후보 0 %s" % work))
            continue
        if stem in found:
            continue
        rc3, text, _ = once(k, ("mapped", repo, ref, path), lambda: k.git(repo, "show", "%s:%s" % (ref, path)))
        rc4, names, _ = once(k, ("mapped-tree", repo, ref, idx), lambda: k.git(repo, "ls-tree", "-r", "--name-only", ref, "--", idx + "/"))
        if rc3 != 0 and rc4 == 0 and any(os.path.basename(p) == stem + ".md" and moved_to(p, idx) in MOVED for p in names.splitlines()):
            continue   # r2114 A1 옮겨진 카드 = 후보 0 · 줄 0
        if rc3 != 0 or rc4 != 0:   # r2114 A2 (팀 · 경로)마다 값이 바뀔 때만 1줄(keeper 상태 파일 · 재기동해도 다시 찍지 않음)
            book, key, val = k.state.setdefault("map_seen", {}), "%s|%s" % (team, path), "%s/%s" % (rc3, rc4)
            if book.get(key) != val:
                book[key] = val
                k.log("판정 불가", team, "짝 표 카드 %s:%s git rc %s/%s — 건너뜀" % (ref, path, rc3, rc4))
            unread.add(stem)   # r2210 O5
            continue
        heads = [x for x in text.splitlines() if re.match(r"- (긴급|우선|대상|선행|배정|재개:|대기 사유:)", x) or x.startswith(SHELL)]
        found[stem] = [any(URGENT.match(x) for x in heads), any(HIGH.match(x) for x in heads), [x for x in heads if x.startswith("- 대상")], [x for x in heads if x.startswith(("- 선행", "- 배정", WAIT) + SHELL)],
                       None, [x for x in heads if x.startswith("- 재개:")], [x for x in heads if x.startswith("- 긴급")]]   # r2113 A1 · r2509 K1 꼴 검사용 «- 긴급:» 줄 그대로
        for p in (x for x in names.splitlines() if x.endswith(".md")):
            m, stage = re.match(r"r(\d+)(?![0-9])", os.path.basename(p)), "아카이브" if MONTH.fullmatch(os.path.dirname(p)[len(idx):]) else os.path.basename(os.path.dirname(p)) if os.path.dirname(os.path.dirname(p)) == idx else ""
            where.setdefault(m.group(1), set()).add(stage) if m and stage in ("완성", "완성후", "아카이브") else None
def moved_to(p, idx):
    """r2114 A1 indices 안 경로 p 의 단계 폴더 이름 · 아카이브/<YYYY-MM>/ = 아카이브 · 그 밖 = ""(mapped where 갈래와 같은 꼴)."""
    return "아카이브" if MONTH.fullmatch(os.path.dirname(p)[len(idx):]) else os.path.basename(os.path.dirname(p)) if os.path.dirname(os.path.dirname(p)) == idx else ""
def delivered(k, team, stem, works, state, led):
    """r2111 A1 — stem·짝 work 에 전달된 attempt 가 있으면 원장 풀림(state none ∧ released_at > 최신 attempt intent 시각) 뒤에만 고른다.
    시각 = intent started(epoch) 먼저 · 없으면 at(로컬) · 하나라도 못 읽음 = «판정 불가» · 줄은 값이 바뀔 때만 1줄."""
    deliveries, returned = state.get("deliveries") or {}, state.get("returned") or {}   # r2118 B1 반환된 최신 attempt = 풀림(w 의 전달 전부 뺄) · B2 dict 아님·낡음 = 그대로
    gone = {w for w, got in returned.items() if isinstance(got, dict) and got.get("attempt") == (deliveries.get(w) or [None])[-1]}
    sent = [(w, a) for w in sorted(set(works) - gone) for a in deliveries.get(w) or []]
    if not sent:
        return ""
    times = []
    for w, a in sent:
        got = k.read_json(os.path.join(kl.projection.runtime_path(k.root, team), "launch", "%s@%s.intent" % (w, a)))
        try:
            times.append(float(got["started"]) if "started" in got else time.mktime(time.strptime(got.get("at"), "%Y-%m-%dT%H:%M:%S")))
        except (TypeError, ValueError):
            pass
    last = max(times) if len(times) == len(sent) else None
    rel = led.get("released_at") if isinstance(led.get("released_at"), (int, float)) else 0
    why = "" if last is not None and led.get("state") == "none" and rel > last else "판정 불가" if last is None else "전달됨"
    book, key, val = k.state.setdefault("delivered_seen", {}), "%s|%s" % (team, stem), "%s|%s" % (why, " ".join("%s@%s" % x for x in sent))
    if why and book.get(key) != val:
        k.log("NEXT-SKIP" if why == "전달됨" else why, team, "%s 건너뜀 — %s(%s)%s" % (stem, why, " ".join("%s@%s" % x for x in sent),
              " · 원장 풀림 뒤 다시 고름 · 풀기 = ft-card-assign record %s waiting <사유> → clear <사유>" % stem if why == "전달됨" else " intent started·at 못 읽음"))
    book[key] = val
    return why
def card_resume_dir(k):   # r2562 K3·K4 — 답으로 닫힌 물음이 남기는 재개 요청 폴더(루트 state 옆 · 나노는 읽기만)
    return os.path.join(k.root, ".fable-team", "state", "card-resume")


def answer_request(k, team, stem, state):   # r2562 K4 — 카드의 요청 파일(<stem>@<q_ts>.json) 가운데 꼴 맞는 것의 at 최댓값 → (at, obj) · 없음 = (None, None)
    """꼴 검사 = JSON dict ∧ card = 파일 이름 stem ∧ q_ts = 파일 이름 뒤 칸 ∧ at 꼴. 어긋난 파일 = 그 파일만 버리고 «판정 불가» 1줄(값이 바뀔 때만).
    남은 임시 파일(*.json.tmp.*)은 이름 꼴에서 걸러지므로 요청으로 읽지 않는다."""
    head = stem + "@"
    d = card_resume_dir(k)
    try:
        names = sorted(n for n in os.listdir(d) if n.startswith(head) and n.endswith(".json"))
    except OSError:
        return None, None
    ok, bad = [], []
    for n in names:
        q = n[len(head):-len(".json")]
        if not QTS.fullmatch(q):
            bad.append(n)
            continue
        try:
            with open(os.path.join(d, n), encoding="utf-8") as fh:
                obj = json.load(fh)
        except (OSError, ValueError):
            bad.append(n)
            continue
        if not isinstance(obj, dict) or obj.get("card") != stem or obj.get("q_ts") != q:
            bad.append(n)
            continue
        try:
            ok.append((time.mktime(time.strptime(str(obj.get("at") or ""), "%Y-%m-%dT%H:%M:%S")), obj))
        except ValueError:
            bad.append(n)
    book, key = k.state.setdefault("answer_seen", {}), "%s|%s" % (team, stem)
    if bad and book.get(key) != " ".join(bad):
        book[key] = " ".join(bad)
        k.log("판정 불가", team, "%s 재개 요청 꼴 아님 — 버림: %s" % (stem, " ".join(bad)))
    elif not bad:
        book.pop(key, None)
    return max(ok, key=lambda x: x[0]) if ok else (None, None)

def reopen(k, team, stem, back, works, state):
    """r2113 A1 — 카드 머리 마지막 «- 재개: <로컬 YYYY-MM-DDTHH:MM:SS>» 이 ⓐ 최신 attempt intent 시각 ∧ ⓑ 착지 sha committer 시각보다 뒤 = 참(«전달됨»·«착지» 로 막지 않음).
    r2562 K4 — 오빠 답으로 닫힌 물음의 요청 파일도 같은 자리(요청 at 최댓값과 재개 줄 가운데 늦은 쪽) · 두 줄 디 늦은 쪽 1번.
    줄 없음·요청 없음 = 거짓(읽기 0) · 꼴 깨짐·착지 시각 못 읽음 = 거짓 + «판정 불가» 1줄(값이 바뀔 때만) · intent 시각 못 읽음 = 거짓(줄은 delivered).
    r2562 K5 — 요청 파일 때문에 참이 될 때 keeper 로그 1줄 «RESUME-ANSWER»(값이 바뀔 때만 · 카드 줄로 열리면 0줄)."""
    req_at, req = answer_request(k, team, stem, state)
    if not back and req_at is None:
        return False
    val, why, book, key = (back[-1].split(":", 1)[1].strip() if back else ""), "", k.state.setdefault("reopen_seen", {}), "%s|%s" % (team, stem)
    at = None
    if back:
        try:
            at = time.mktime(time.strptime(val, "%Y-%m-%dT%H:%M:%S"))   # DA #318934 R2 — 값 전체가 꼴(뒤 문구 버리기 0)
        except ValueError:
            at, why = None, "재개 줄 꼴 깨짐 %r — 고칠 꼴 «- 재개: YYYY-MM-DDTHH:MM:SS»" % val[:30]
    from_req = req_at is not None and (at is None or req_at >= at)   # 반례 ⑦ — 둘 다 있으면 늦은 쪽 1번
    at = req_at if from_req else at
    for w, a in ((w, a) for w in sorted(works) for a in (state.get("deliveries") or {}).get(w) or []) if at else ():
        got = k.read_json(os.path.join(kl.projection.runtime_path(k.root, team), "launch", "%s@%s.intent" % (w, a)))
        try:
            t = float(got["started"]) if "started" in got else time.mktime(time.strptime(got.get("at"), "%Y-%m-%dT%H:%M:%S"))
            if t >= at:
                return False
        except (TypeError, ValueError):
            return False
    landed = once(k, ("landed", team, stem), lambda: k.landing(team, stem)) if at else (None, None, "")
    if landed[0]:   # DA #318934 R1 — 미도달 등 사유가 있어도 착지 sha 가 있으면 그 시각을 읽는다(못 읽음 = 막음 그대로)
        out = next((o for repo in (k.pack, k.root) for rc, o, _ in [k.git(repo, "log", "-1", "--format=%ct", landed[0])] if rc == 0), "").strip()
        end = int(out) if out.isdigit() else None
        why = "" if end is not None else "착지 %s committer 시각 못 읽음" % landed[0][:10]
        at = None if end is None or end >= at else at
    if why and book.get(key) != why:
        k.log("판정 불가", team, "%s %s — 재개 없이 기존 막음 그대로" % (stem, why))
    book[key] = why
    if at is not None and from_req:   # r2562 K5 — 요청 파일 때문에 다시 여는 바퀴만 1줄(카드 줄로 열리면 0줄 · 값이 바뀔 때만)
        rbook, rkey = k.state.setdefault("resume_answer_seen", {}), "%s|%s" % (team, stem)
        stamp = "%s|%s|%s" % (req.get("q_ts"), req.get("reply_ts"), req.get("key"))
        if rbook.get(rkey) != stamp:
            rbook[rkey] = stamp
            k.log("RESUME-ANSWER", team, "%s 오빠 답 재개 — q_ts %s reply_ts %s key %s" % (stem, req.get("q_ts"), req.get("reply_ts"), req.get("key")))
    return at is not None
def clash(k, team, stem):
    """r2111 A2 — nano_name 과 대소문자만 다른 세션이 살아 있으면 «이름겹침» · list-sessions 실패 = «판정 불가» · 줄은 값이 바뀔 때만 1줄.
    r2113 A2b — 40자 넘게 잘리는 stem 은 옛 40자 이름과 대소문자 무시하고 같은 세션(글자 그대로 포함)도 «이름겹침».
    r2504 — 겹침 판독 기준 = slug(석 칸·세대 뗌) · 석이 달라도 같은 카드 slug 면 겹침(옛 꼴로 떠 있는 세션 포함)."""
    nh, (rc, out, _) = nano_name(k, team, stem), once(k, "ls", [k.tmux, "list-sessions", "-F", "#{session_name}"])
    olds0 = {"biz-%s-nano-%s#0" % (team, stem[:40].rstrip("-"))} if len(stem) > 40 and stem[:40].rstrip("-") else set()
    olds = {x.lower() for x in olds0}
    slug = slug_of(nh).lower()   # r2504 — 석 칸·세대가 달라도 같은 slug = 이름겹침(옛 꼴 세션 포함)
    other = "" if rc != 0 or not nh else next((x for x in out.split() if x.lower() in olds or x != nh and slug and slug_of(x).lower() == slug), "")
    why = "판정 불가" if rc != 0 else "이름겹침" if other else ""
    book, key, val = k.state.setdefault("clash_seen", {}), "%s|%s" % (team, stem), "%s|%s" % (why, other)
    told = bool(nh) or why == "이름겹침"   # r2504 — 이름이 없으면 nano_name 이 이미 «판정 불가» 1줄(같은 사유 두 줄 0)
    if why and told and book.get(key) != val:
        k.log("NEXT-SKIP" if other else why, team, "%s 건너뜀 — %s" % (stem, "이름겹침 %s 살아 있음(새 이름 %s)" % (other, nh) if other else "tmux list-sessions rc %s" % rc))
    book[key] = val
    return why
def target(k, r, lines):
    """(리포, base) — 팩·feature-pack/ = 팩 origin/main · 없음 = 루트 리포·표 ref · 팩·BIZ 둘 다 = None."""
    pack, biz = any("팩" in x or "feature-pack/" in x for x in lines), any("BIZ" in x for x in lines)
    return None if pack and biz else (k.pack, "origin/main") if pack else (r[1], r[2])
def pairs(k, team):
    """r1887 짝 표 {work: [경로]} → {카드 stem: 짝 work 집합} · 판독 실패 = 짝 0(stem 만) · choose 와 r2188 release 가 같이 부른다."""
    cmap, pair = k.cardmap(team), {}
    for work, paths in (cmap.items() if isinstance(cmap, dict) else ()):
        for p in paths:
            pair.setdefault(os.path.basename(p)[:-3], set()).add(work)
    return pair
def ended(stem, pair, done):
    """r1887 «끝남» = stem·짝 work 중 하나가 done · r2188 ⓕ choose 와 보류 지움이 같은 판정."""
    return "끝남" if stem in done or pair.get(stem, set()) & set(done) else ""
def release(k, team):
    """r2188 H1 — 그 팀 fill 보류 중 풀린 것을 지우고 남은 stem 집합 · 원장 쓰기 0(keeper 상태만).
    풀림 = ⓐ 원장 updated > 보류 시각(r1939 값 = 시각 또는 «시각|사유») ⓑ stem·짝 work done(ended) · ft2 state 판독 실패 = ⓑ 0."""
    held = k.state.setdefault("fill_hold", {})
    mine = [x for x in held if x.split("|")[0] == team]
    state = ft2_state(k, team) if mine else None
    pair, done = pairs(k, team) if state is not None else {}, (state or {}).get("done") or {}
    for x in mine:
        stem = x.split("|", 1)[1]
        if (ledger(k, stem).get("updated") or 0) > float(str(held[x]).split("|")[0]):
            held.pop(x)
        elif state is not None and ended(stem, pair, done):
            held.pop(x)
            k.log("FILL-HOLD-DROP", team, "%s 끝남" % stem)
    return {x.split("|", 1)[1] for x in held if x.split("|")[0] == team}
def held_choose(k, team):
    """r2188 H2 — 닫기 영수 고르기 = 채우기와 같은 보류 목록(release)을 skip 으로(보류 카드 다시 고르기 0).
    그 팀 보류 0 = 풀 것도 건널 것도 없다 → 옛 꼴 choose(k, team) 그대로(2인자로 바꿔 끼운 choose 도 그대로 · r1886 c4)."""
    if not any(x.split("|")[0] == team for x in k.state.get("fill_hold") or {}):
        return choose(k, team)
    return choose(k, team, release(k, team))
REOPEN_HOW = ("카드에 «- 재개: <시각> · PR #<번호> · head <40자> · 가지 nano/<work>» 한 줄"
              "(원장이 남아 있으면 ft-card-assign-watch.sh record <카드> clear <사유>)")   # r2573 K2 — 다시 여는 법 한 벌(keeper_manual_close.py 끝 줄 안내와 같은 글자 · 순환 import 0 이라 사본)
ASSIGNED_SHOW = 20   # r2573 H1 — 안내 줄의 쉼 사유 = 한 줄 20자(줄바꿈·200자를 눌러 적는다)
SET_SHOW = re.compile(r"- 세트:\s*[0-9a-f]{40}\s*·\s*시험:.+\src=0\s*·\s*이슈:\s*0\s*$")   # r2573 H2 — 인수 끝·착지 대기 카드의 증거 줄(keeper_endings.SETLINE 과 같은 꼴)
def sleep_show(state, stem):
    """r2573 H1 — 그 팀 ft2 state 의 쉼(parked) 행 → (기억 값, 안내 글자).
    기억 값 = «-»(parked 행 없음) 이거나 그 행의 «at» 글자 = 열쇠 없음과 다른 세 값(DA H1 · 카드 머리 «- 재개:» 줄 종류가 아니다).
    안내 글자 = «쉼 <사유 정규화 20자>» · 행이 없거나 사유가 비면 «쉼 기록 없음»."""
    row = (state.get("parked") or {}).get(stem) if isinstance(state, dict) else None
    row = row if isinstance(row, dict) else {}
    why = " ".join(str(row.get("reason") or "").split())[:ASSIGNED_SHOW]
    return str(row.get("at") or "").strip() or "-", ("쉼 " + why if why else "쉼 기록 없음")
def assigned_tell(k, team, stem, state):
    """r2573 K1·K2 — 원장 seat ∧ ft2 owner 0 ∧ 재개 줄이 안 열어 준 카드 = «건너뜀 · 다시 여는 법» 1줄.
    값(ft2 state 의 parked 행)이 바뀔 때만 1줄(기억 = keeper 상태 파일 assigned_seen · 열쇠 없음 → «-» → at 전환에만 · 이 갈래를 떠난 카드 키는 choose 끝에서 지운다).
    고르는 판정·재개 조건은 안 바꾼다(줄만 더한다 · ready 차례·why 셈·[다음 없음] 그대로)."""
    book, key = k.state.setdefault("assigned_seen", {}), "%s|%s" % (team, stem)
    val, why = sleep_show(state, stem)
    if book.get(key) != val:
        book[key] = val
        k.log("NEXT-SKIP", team, "%s 건너뜀 — 원장 배정됨(원장 좌석 표시 · ft2 owner 0 · %s) · 다시 열기 = %s"
              % (stem, why, REOPEN_HOW))
    return val
def choose(k, team, skip=frozenset(), tell=True):   # r2509 tell=False = 이 자리는 [다음 없음] 쪽지 0(쉼 판정 spare 몫)
    """(stem, 리포, base) · skip = fill 보류 stem(r1913 «보류») · 고를 카드 0 = None(그때만 [다음 없음] 1통) · 판독 실패 = None(쪽지 0)."""
    unread, waits = set(), set()   # r2210 이 바퀴 판독 실패 짝 표 카드 · 대기사유로 막힌 카드
    got, state = cards(k, team, unread), ft2_state(k, team)
    if isinstance(got, str) or state is None:
        return k.log("판정 불가", team, "다음 카드 고르기 %s — 다음 카드 0" % (got if isinstance(got, str) else "ft2 state"))
    pair = pairs(k, team)   # r1887 짝 표
    (found, r), done, why, ready = got, state.get("done") or {}, {}, []
    owners = {s for s in found if ({s} | pair.get(s, set())) & set(state.get("owners") or {})}   # stem·짝 work 중 owner 있음
    names, ends, assigned = {}, set(), set()   # r2182 N1·N2 {사유: [(카드, 원장이 먼저 막음)]} · r2254 끝남 ∧ 재개 줄 카드 · r2573 이 바퀴 «배정됨(owner 0)» 카드
    res = r[4] if len(r) > 4 else {}   # r2159 재개 진행/ 카드(progress)
    for stem, row in sorted(found.items()):
        urgent, high, lines, pre, seen, back = row[:6]   # r2509 K1 — 7번째 칸 = «- 긴급:» 줄 그대로(꼴 검사용) · r2573 H2 — 8번째 칸 = «- 세트:» 증거 줄 있음
        show_set = row[7] if len(row) > 7 else False
        led = ledger(k, stem)
        if stem in res:   # r2159 T1·T2 — 원장 seat·착지·전달됨·r2113 재개 대신 resumed · base = PR head 40자
            block = resumed(k, team, stem, led, res[stem][2], {stem} | pair.get(stem, set()), state, owners, done) or ("팩낡음" if res[stem][0] in k.stale else "")
            ready.append(((True, True, led.get("since") or 0), stem) + res[stem][:2]) if not block else why.update({block: why.get(block, 0) + 1})   # 재개 카드 = 긴급·우선 읽기 0
            continue
        own = led.get("state") != "seat" and stem not in owners and led.get("reason") in BLOCK   # r2182 ⓗ 배정됨이 먼저면 원장 표시 0
        block = "배정됨" if led.get("state") == "seat" or stem in owners else led.get("reason") if led.get("reason") in BLOCK else pre   # r2027 ⑤ 원장·카드 둘 중 하나
        if block == "배정됨" and stem not in owners and reopen(k, team, stem, back, {stem} | pair.get(stem, set()), state):   # r2252 O1 쉼 뒤 남은 원장 seat ∧ owner 0 ∧ 재개 줄 참
            block = led.get("reason") if led.get("reason") in BLOCK else pre   # «배정됨» 만 건너뜀(원장 사유·카드 막힘은 그대로)
        elif block == "배정됨" and stem not in owners and not show_set:   # r2573 K1·K2·H2 — 이 갈래만 줄이 없었다: «건너뜀 · 다시 여는 법» 1줄(값이 바뀔 때만 · «- 세트:» 증거 줄이 있는 착지 대기 카드는 0줄 · 재개 조건·고르는 판정 0)
            assigned.add(stem)
            assigned_tell(k, team, stem, state)
        shell = k.state.setdefault("shell_seen", [])   # r2093 S2 — 껍데기 건너뜀 1줄(카드마다 1회 · keeper 상태 파일)
        shell += [k.log("NEXT-SKIP", team, "%s 건너뜀 — NEW_CARD_HOLD 껍데기" % stem) or "%s|%s" % (team, stem)] if pre == "껍데기" and "%s|%s" % (team, stem) not in shell else []
        if block == "대기사유":   # r2205 O4 — 값이 바뀔 때만 1줄(keeper 상태 파일 {팀|stem: 값} · prereq_seen 꼴)
            book, key = k.state.setdefault("wait_seen", {}), "%s|%s" % (team, stem)
            waits.add(stem)
            if book.get(key) != seen["why"]:
                book[key] = seen["why"]
                k.log("NEXT-SKIP", team, "%s 건너뜀 — 대기 사유 줄 · 풀기 = «- 대기 사유: 없음»" % stem)
        if pre == "표식없음":   # r2395 K2 — 값이 바뀔 때만 1줄(기억 = keeper 상태 파일 · prereq_seen 꼴 · 지우기 0: 카드가 고쳐져도 그대로)
            book, key = k.state.setdefault("marker_seen", {}), "%s|%s" % (team, stem)
            if book.get(key) != "표식없음":
                book[key] = "표식없음"
                k.log("NEXT-SKIP", team, "%s 건너뜀 — 표식 줄 없음 · «- 배정: 없음» 또는 «- 대기 사유: 없음» 한 줄 필요" % stem)
        if pre == "선행불명":   # I1·I2 — 값·까닭이 바뀔 때만 1줄(기억 = keeper 상태 파일 · 재기동해도 다시 찍지 않는다 · DA 310229)
            book, key = k.state.setdefault("prereq_seen", {}), "%s|%s" % (team, stem)
            if book.get(key) != seen:
                book[key] = seen
                k.log("판정 불가", team, "%s 선행 줄 판독 불가(%s) — 건너뜀 · 고칠 꼴 «- 선행: 없음» 또는 «- 선행: r<번호>»" % (stem, seen["why"]))
        block = block or ("보류" if stem in skip else ended(stem, pair, done))   # r1887 stem·짝 work done
        if block == "끝남" and back:   # r2254 O1 끝난 work 카드의 재개 줄 = NEXT-SKIP 1줄(값이 바뀔 때만 · wait_seen 꼴) · block·reopen 호출 0 그대로
            dw, done_book, key = min(w for w in {stem} | pair.get(stem, set()) if w in done), k.state.setdefault("done_skip_seen", {}), "%s|%s" % (team, stem)
            got = "%s@%s" % (dw, done[dw].get("attempt") if isinstance(done[dw], dict) else done[dw])
            val = ends.add(stem) or "%s|%s" % (" ".join(back), got)   # 값 = 재개 줄들 · done attempt
            if done_book.get(key) != val:
                done_book[key] = val
                k.log("NEXT-SKIP", team, "%s 건너뜀 — 끝남(ft2 done %s) · 재개 줄 무시 · 끝난 work 는 같은 이름으로 다시 안 열림 · 새 work 이름으로 손 발주" % (stem, got))
        back = not block and reopen(k, team, stem, back, {stem} | pair.get(stem, set()), state)   # r2113 A1 재개 줄(없거나 막힌 카드 = 읽기 0)
        block = block or ("재개" if back else "")   # r2113 A1 — 재개 줄 = «착지» 판독 건너뜀(바로 아래에서 푼다)
        block = block or ("착지" if skip_landed(k, team, stem) else "")   # r2058 L5 착지 카드 = 다시 넣지도 닫기 뒤 다음으로도 고르지 않는다
        block = block or landed_hold(k, team, stem)   # r2262 C1
        block = "" if block == "재개" else block
        place = None if block else target(k, r, lines)
        if not block and place is None:
            block = k.log("판정 불가", team, "%s 대상 팩·BIZ 둘 다 — 건너뜀" % stem) or "대상"
        block = block or ("팩낡음" if place[0] in k.stale else "")   # r1963 낡은 팩 base 로 나노 열기 0(이 바퀴 보류 · BIZ 대상 카드는 그대로)
        block = block or ("재개" if back else "")   # r2113 A1 — 재개 줄 = «전달됨» 판독 건너뜀(바로 아래에서 푼다)
        block = block or delivered(k, team, stem, {stem} | pair.get(stem, set()), state, led)   # r2111 A1
        block = "" if block == "재개" else block
        block = block or clash(k, team, stem)   # r2111 A2
        ready.append(((not urgent, not high, led.get("since") or 0), stem) + place) if not block else why.update({block: why.get(block, 0) + 1}) or names.setdefault(block, []).append((stem, own))
    book = k.state.setdefault("wait_seen", {})   # r2210 O2·O3·O4·O5 — 위 found 를 다 본 뒤: 그 팀 키 중 대기사유 막힘이 아니게 됐거나 사라진 카드를 지운다(판독 실패 카드 = 그대로)
    for key in [x for x in book if x.partition("|")[0] == team and x.partition("|")[2] not in waits and (x.partition("|")[2] in found or not unread & {x.partition("|")[2], "*"})]:
        book.pop(key, None)   # r2210 (prereq 변이 M40 의 글자와 겹치지 않게)
    gone = k.state.setdefault("done_skip_seen", {})   # r2254 O3 — 끝남 ∧ 재개 줄이 아니게 됐거나 사라진 카드 키 지움(판독 실패 카드 = 그대로 · wait_seen 꼴)
    for key in [x for x in gone if x.partition("|")[0] == team and x.partition("|")[2] not in ends and (x.partition("|")[2] in found or not unread & {x.partition("|")[2], "*"})]:
        gone.pop(key, None)
    abook = k.state.setdefault("assigned_seen", {})   # r2573 K2 — 이 갈래를 떠난 카드 키 지움(다시 들어오면 1줄 · 판독 실패 카드 = 그대로 · wait_seen 꼴)
    for key in [x for x in abook if x.partition("|")[0] == team and x.partition("|")[2] not in assigned and (x.partition("|")[2] in found or not unread & {x.partition("|")[2], "*"})]:
        abook.pop(key, None)
    if why.get("팩낡음"):
        k.log("판정 불가", team, "다음 카드 보류 %d장 · 팩 fetch 실패" % why["팩낡음"])
    prereq_tell(k, team, {s: row[4] for s, row in found.items() if row[3] == "선행불명"})   # I4~I8 · 고를 카드가 있든 없든 간다
    if ready or why.get("팩낡음") or why.get("판정 불가"):   # 보류뿐이면 [다음 없음] 쪽지 0 · r2111 판정 불가 = 쪽지 0
        return min(ready)[1:] if ready else None
    none_tell(k, team, "%s %s · 배정 없는 카드 0 · 막힌 사유별 %s" % (NONE, team, " ".join("%s %d" % kv for kv in sorted(why.items())) or "0"), names) if tell else None
NAMES, NONE_CAP = True, 3   # r2182 N1 이름 싣기 · N3 팀당 하루 [다음 없음] 상한(옛 열쇠 1통 포함 · ⓖ)
FIX = " · 원장이 카드 줄과 다르면: bash .fable-team/bin/ft-card-assign-watch.sh record <카드> clear <사유>"
def none_tell(k, team, head, names):
    """r2182 [다음 없음] 1통 — 기준 글 + 사유마다 이름순 3장(«(원장)» · «외 n») + 원장 카드가 있으면 풀기 꼴 1칸.
    열쇠 = <날짜>|next-none|<팀>|<지문>(막힌 목록 전체 · 이름순 · ⓕ) · 같은 날 같은 지문 = 0 · 팀당 하루 NONE_CAP 통."""
    key = "%s|next-none|%s" % (k.stamp()[:10], team)
    rows = sorted((b, s, own) for b, got in names.items() for s, own in got)
    fp = hashlib.sha1(repr(rows).encode("utf-8")).hexdigest()[:12]
    to = k.recipients(team)[0]   # r2266 C2 (팀, 받는 좌석)마다 마지막 지문 · 같으면 날 무관 0통
    mk, mem = "%s|%s" % (team, to), k.state.setdefault("none_seen", {})
    if team in k.skip or mem.get(mk) == fp:
        return
    if sum(x == key or x.startswith(key + "|") for x in k.state.get("sent") or {}) >= NONE_CAP:
        if k.state.setdefault("none_mute", {}).get(team) != fp:   # r2266 C2 상한 뒤 지문 바뀜 = 로그 1줄(쪽지 0) · 같은 지문 = 0
            k.state["none_mute"][team] = fp
            k.log("NEXT-NONE-MUTE", team, "하루 %d통 상한 뒤 지문 %s · 쪽지 0" % (NONE_CAP, fp))
        return
    part = {}
    for b, s, own in rows:
        part.setdefault(b, []).append(s + ("(원장)" if own else ""))
    tell = " / ".join("%s %s%s" % (b, " · ".join(cut[:3]), " 외 %d" % (len(cut) - 3) if len(cut) > 3 else "") for b, cut in part.items())
    body = head + (" · 막힌 카드 " + tell if NAMES and tell else "") + (FIX if any(own for _, _, own in rows) else "")
    if k.notify(team, "%s|%s" % (key, fp), body):   # r2266 C2 도착 확인 · stand_in 쌓음만 기억(실패 · 받는 곳 없음 · defer = 0)
        mem[mk] = fp
def prereq_mute(k, team):
    """P1 묵음 — 이 팀의 정지(r2465 K4: k.halted(team) · 제외 팀은 정지 아님) · 팀 PAUSED(state/<팀>-tick/PAUSED) · 새 카드 보류(NEW_CARD_HOLD.json · 깨짐 포함) 중 하나라도 참.
    판정 자리 = prereq_tell 안 1곳(부르는 쪽 앞 조건이 나중에 바뀌어도 새지 않게 하는 방어 · 설계 P1). r2465 K5 — PAUSED 는 except 보다 세다."""
    st = os.path.join(k.root, ".fable-team", "state")
    return bool(k.halted(team)) or os.path.lexists(os.path.join(st, "%s-tick" % team, "PAUSED")) or new_card_hold(k, team)

def prereq_path(k, team):
    """P4 목록 파일 자리 = <root>/.fable-team/state/ft2-keeper/prereq-<팀>.txt(팀마다 1개 · 일반 파일)."""
    return os.path.join(k.dir, "prereq-%s.txt" % team)

def prereq_list(k, team, unread, changed):
    """P4 — prereq_tell 이 불린 바퀴에 (지문이 바뀌었거나 목록 파일이 없으면) 원자 쓰기(tmp → replace) · 빈 묶음이면 지운다 · 파일 있고 지문 그대로 = 손 0.
    첫 줄 = `# 관측 <시각> · <n>장`(마지막으로 고른 바퀴의 값) · 그 아래 줄마다 `<카드>\\t<선행 값>\\t<까닭>` 이름순 · 3장 이하도 쓴다.
    파일 없이 지문만 있는 상태 = 옛 판이 만든 상태(판 올림 승계 · DA 312085 반례) — 그 바퀴에 한 번 만든다(지문이 같아도)."""
    path = prereq_path(k, team)
    if not unread:   # 빈 묶음 = 지운다
        if os.path.lexists(path):
            os.unlink(path)
        return
    if not changed and os.path.lexists(path):   # 지문 그대로 · 파일 있음 = 쓰지도 지우지도 않는다(P0 · ㊵바·㊵사)
        return
    os.makedirs(k.dir, exist_ok=True)
    body = "# 관측 %s · %d장\n" % (k.stamp(), len(unread)) + "".join("%s\t%s\t%s\n" % (s, v["val"], v["why"]) for s, v in sorted(unread.items()))
    with open(path + ".tmp", "w", encoding="utf-8") as fh:
        fh.write(body)
    os.replace(path + ".tmp", path)

def prereq_body(k, team, unread):
    """P3 본문 = 3장까지는 지금 글 그대로 · 3장을 넘으면 «전체 목록 <경로>» 칸 하나를 붙인다(I5 가 바뀌는 곳 · P8)."""
    head = "[다음 막힘] %s 선행 줄을 못 읽는 카드 %d장: %s" % (team, len(unread), " · ".join(sorted(unread)[:3]))
    tail = " · 전체 목록 %s" % prereq_path(k, team) if len(unread) > 3 else ""
    return head + tail + " · 고칠 꼴 «- 선행: 없음» 또는 «- 선행: r<번호>»"

def prereq_tell(k, team, unread):
    """I4~I8 + P1~P6 — 선행불명 기억 치우기 + 묶음 지문·전이 번호 + 팀장 [다음 막힘] 1통(마지막으로 전한 묶음과 다를 때만).
    unread = {카드: {"val": 선행 값, "why": 까닭}} · 기억 셋은 모두 keeper 상태 파일 키다(재기동해도 이어진다 · I9) ·
    P0 = 이 함수가 불린 바퀴에만 손 · P1 묵음 = 전팀 정지·팀 PAUSED·새 카드 보류 중이면 쪽지 0(now·목록 파일은 고친다) ·
    P4 목록 파일 = 지문이 바뀐 바퀴에만 · P5 팀장 없음 = 쪽지 대신 PREREQ-WAIT 1줄 · P6 순서 = 빔 → P1 → P5 → I8."""
    book = k.state.setdefault("prereq_seen", {})
    for key in [x for x in book if x.split("|")[0] == team and x.split("|")[1] not in unread]:   # I4 선행불명이 아니게 되거나 대기에서 사라짐
        book.pop(key)
    fp = hashlib.sha1("\n".join("%s\t%s\t%s" % (s, v["val"], v["why"]) for s, v in sorted(unread.items())).encode("utf-8")).hexdigest()[:12] if unread else ""   # I6 묶음 지문
    now, told, prev = k.state.setdefault("prereq_now", {}), k.state.setdefault("prereq_told", {}), k.state.setdefault("prereq_now", {}).get(team) or {}
    n = prev.get("n") if prev.get("fp", "") == fp else (prev.get("n") or 0) + 1   # I7 전이 번호 = 묶음이 바뀔 때마다 +1
    now[team] = {"fp": fp, "n": n}
    wait = k.state.setdefault("prereq_wait", {})   # P5 기억 = 마지막으로 보류한 묶음 지문(새 키 1개 · 옛 판은 읽지 않는다)
    prereq_list(k, team, unread, prev.get("fp", "") != fp)   # P4 — 바뀐 바퀴에만 쓰기·지우기(보류 바퀴 = 마지막 관측값 그대로)
    if not fp:   # I7 지금 묶음이 비면 told·보류 기억을 비우고 목록 파일을 지운다
        told.pop(team, None)
        wait.pop(team, None)
        return
    if prereq_mute(k, team):   # P1 — 묵음 = 쪽지 0(told 그대로 · now·목록 파일은 위에서 고친다)
        return
    to, stand = k.recipients(team)   # P5 팀장 판독 = keeper 쪽지 받는 곳 차례 그대로(그 팀 _master → _desk → harness _master)
    if not to or stand:   # P5 팀장 없음 = 쪽지 대신 PREREQ-WAIT 1줄(묶음에 쌓지 않는다)
        if wait.get(team) != fp:   # 묶음 지문이 바뀔 때만 1줄(보류 중 되풀이 0)
            wait[team] = fp
            k.log("PREREQ-WAIT", team, "팀장 없음 — 선행 줄 쪽지 보류 %d장 · 목록 %s" % (len(unread), prereq_path(k, team)))
        return
    wait.pop(team, None)   # 팀장이 선 바퀴 = 보류 기억 지움(그 묶음은 I8 로 나간다)
    if told.get(team) == fp:   # I8 마지막으로 전한 묶음 그대로 = 보내지 않는다
        return
    ok = k.notify(team, "prereq|%s|%s|%s" % (team, fp, n), prereq_body(k, team, unread))
    if ok:   # I8 성공(rc 0·도착 확인)일 때만 told 를 바꾼다 · 실패·넘김(defer)은 그대로
        told[team] = fp


def wake_read(k, team):
    """r2267 W1~W3 — 휴면 팀 선행 판정만(cards 1회 · fill·stage·close·원장·팀 쪽지·gh·fetch 0) · 기억 = wake_seen[팀]{카드: 판정} ·
    앞 판독에서 선행/선행불명(또는 풀림)이던 카드가 "" = 풀림 · 처음 보는 팀·카드 = 기억만 · 풀림 묶음(이름순) ≥ 1 → k.wake(planner 1통 · 같은 열쇠 0)."""
    got = cards(k, team, resume=False)   # 사전 DA H1 — 휴면 길 = progress(재개 줄 → gh · resume_seen) 0
    if isinstance(got, str):
        return
    book = k.state.setdefault("wake_seen", {})
    prev = book.get(team)
    book[team] = {s: "풀림" if row[3] == "" and prev and prev.get(s) in ("선행", "선행불명", "풀림") else row[3] for s, row in got[0].items()}
    if freed := sorted(s for s, v in book[team].items() if v == "풀림"):
        k.wake(team, freed)


def seen_no_receipt(k, team, work, attempt, stem, done):
    """r2350 K1·K2 — 이미 영수한 사건(close_receipts 1행 = seen)을 다시 영수하지 않을 조건.
    참 = 다음 카드 칸 표식(teams/<팀>/CLOSE-NEXT.enabled · 이미 읽은 ft2_state 밖 = 추가 판독 0 · DA#44 B1·권함) ∧
    (영수 키 done(close:<팀>:keeper:<일>@<시도>) ∨ 다음 빔). 거짓 = 영수 뒤 배정·전달이 아직(core _resume 갈래 1·2) 또는 표식 없음
    = 지금처럼 core 영수 1회. core 는 그 두 갈래를 안 끝낸 일로 보고 실제로 쓴다 — 갈래 1 = _chain(배정+전달)·갈래 2 = _deliver ·
    그래서 건너뛰면 다음 카드가 안 열린다. 반면 참 갈래(전달 완료·다음 빔)의 core 는 journal 만 다시 읽고 쓰기 0 이라 느리기만 했다(b2c 55초 실사건)."""
    mark = os.path.join(k.root, ".fable-team", "teams", team, "CLOSE-NEXT.enabled")
    if not os.path.exists(mark):
        return False
    return not stem or "close:%s:keeper:%s@%s" % (team, work, attempt) in done

def close(k, team, work, attempt, holder, gen):
    """닫기 영수 1회(지금 자리) + 다음 카드. 반환 = 영수 결과. r2101 H3 = 새 카드 보류면 이 고르기만 멈춘다(영수·이어 잇기 그대로).
    r2350 K1·K2 = 이미 영수한 사건이면 core 영수 0 · 로그 «RECEIPT-SEEN» 1줄 · 곧장 reconcile(바퀴 예산을 안 먹는다)."""
    choose = held_choose   # r2188 H2 채우기와 같은 보류 목록 · 아래 고르기 줄은 글자 그대로(r1871 M5 · 벌점 M63 변이가 그 줄을 찾는다)
    book = ft2_state(k, team) or {}   # 영수·done 판독 1회(추가 판독 0)
    seen = (book.get("close_receipts") or {}).get("keeper:%s@%s" % (work, attempt))
    pick = None
    if seen is None and not new_card_hold(k, team):
        pick = choose(k, team) if gates(k, team) and penalty_open(k, team) else None
        pick = pick if pick and nano_name(k, team, pick[0]) else None   # r2016 빈 이름 = submit 전 그 카드 0
        if pick:
            out, rc = cli.run(["submit", "--command", "keeper-next-" + pick[0], "--body", "카드 " + pick[0], "--work", pick[0], "--root", k.root, "--team", team])
            k.fa.remaining(k.root, team, out.get("result"), "카드 " + pick[0])   # r1886 ⓐ keeper submit
            pick = pick if rc == 0 or "재부여 0" in str(out.get("reason")) else k.log("판정 불가", team, "%s submit %s" % (pick[0], out.get("result")))
        stem, nh = (pick[0], nano_name(k, team, pick[0])) if pick else (None, None)
    elif seen is not None:
        stem, nh = seen.get("next"), seen.get("holder")
    else:   # 새 카드 보류(H3) = 다음 카드 없음 · 영수는 그대로 쓴다
        stem, nh = None, None
    if seen is not None and seen_no_receipt(k, team, work, attempt, stem, book.get("done") or {}):
        k.log("RECEIPT-SEEN", team, "%s -> %s" % (work, "%s %s" % (stem, nh) if stem else NONE))   # 재접수와 같은 뜻 · 쓰기 0
        if not stem:   # K2 — 다음 없음 = handled 만(«재접수» mark 와 같은 끝 · reconcile 0)
            k.state["handled"]["%s|%s@%s" % (team, work, attempt)] = k.stamp()
            return None
        return reconcile(k, team, work, attempt, stem, nh, None)   # K1·K4 — 끝냄 표시 = reconcile 그대로(handled 쓰기 자리 손 0)
    if not stem:
        return k.receipt(team, work, attempt, holder, gen)
    out = k.receipt(team, work, attempt, holder, gen, next_work=stem, next_holder=nh, evidence=dispatch.Dispatch.REQUIRED_EVIDENCE, mark=False)
    if out.result == OK and out.next == stem or "재접수" in out.reason:
        reconcile(k, team, work, attempt, stem, nh, pick if seen is None else None)
    elif out.result == "접수 거부" and seen is None:   # 거부 = 쓰기 0 → 지금처럼 () 영수 1회
        return k.receipt(team, work, attempt, holder, gen)
    return out
def capacity_left(k, team):
    """r2509 — 접수 용량 셈 한 판독(project · r2055 work 단위·쉼 제외) → int · project 판독 실패 = None."""
    out, _ = cli.run(["project", "--root", k.root, "--team", team])
    n = out.get("capacity", out.get("remaining")) if out.get("result") == OK else None
    return n if type(n) is int else None
def intake_open(k, team):
    """r1939 거짓 = 접수 남은 일 ≥ 상한(fill 0 · FILL-WAIT 는 값이 바뀔 때만 1줄) · project 판독 실패 = 참(submit 이 판정).
    r2509 — 바퀴당 1회(한 바퀴에 쉼 판정과 fill 이 같은 값을 본다 · 판독·기억 규칙은 그대로)."""
    return once(k, ("intake", team), lambda: _intake_open(k, team))
def _intake_open(k, team):
    n, seen = capacity_left(k, team), k.state.setdefault("fill_wait", {})
    if n is None:
        return True
    if n < k.fa.INTAKE_CAP:   # 정상값 = 기억 해제(8→7→8 = 다시 1줄)
        seen.pop(team, None)
        return True
    if seen.get(team) != n:
        seen[team] = n
        k.log("FILL-WAIT", team, "남은 일 %d/%d — fill 0 · 다음 바퀴" % (n, k.fa.INTAKE_CAP))
    return False
def urgent_form(k, team):
    """r2509 K1 — 대기 카드 머리의 «- 긴급:» 줄이 keeper 꼴(URGENT «예» · «아니오» 단독)이 아니면 그 팀 master 에 [긴급] 1통.
    막힘 판정(gates · intake_open) 앞에서 매 바퀴 · 열쇠 = 날짜|urgent-form|팀|카드(하루 1통) · 발신 성공 뒤에만 기록(실패 = 다음 바퀴 다시) · 꼴 정본 = keeper 상수(새 정규식 0) · 반환 = 이번 바퀴 보낸 통수."""
    got = cards(k, team)
    if isinstance(got, str):
        return 0
    told = 0
    for stem, row in sorted(got[0].items()):
        bad = next((x.strip() for x in (row[6] if len(row) > 6 else ()) if not (URGENT.match(x.strip()) or URGENT_NO.match(x.strip()))), None)
        if bad is None:
            continue
        key = "%s|urgent-form|%s|%s" % (k.stamp()[:10], team, stem)
        ok = k.notify(team, key, "[긴급] ft2 keeper %s 카드 %s 긴급 줄 꼴 틀림 — keeper 가 못 읽는다 · 틀린 줄 «%s» · 고칠 꼴 «- 긴급: 예»" % (team, stem, bad[:60]))
        if not ok and str((k.state.get("sent") or {}).get(key) or "").startswith("fail|"):
            (k.state.get("sent") or {}).pop(key, None)   # r2509 ⑮ — 발신 실패는 열쇠 0(다음 바퀴 다시 1통 · 그날 재시도 0 지문을 쓰지 않는다)
        told += 1 if ok else 0
    return told
def park_open(k, team):
    """r2509 ⑬ — 쉼을 낸 긴급 카드가 아직 안 닫혔으면 그 이름(그 팀 둘째 쉼 0) · 닫혔으면 기억을 지우고 "".
    안 닫힘 = 원장 done 아님(대기·진행·쉼) ∨ 원장 seat · ft2 state 판독 실패 = 기억 그대로(모르면 쉼 0)."""
    book = k.state.setdefault("urgent_park", {})
    card = book.get(team) or ""
    if not card:
        return ""
    st = ft2_state(k, team)
    if st is None:
        return card
    if card not in (st.get("done") or {}) or ledger(k, card).get("state") == "seat":
        return card
    book.pop(team, None)
    k.log("URGENT-PARK", team, "%s 쉼 기억 풀림 — 그 카드가 닫혔다(다음 긴급 카드부터 다시 1석)" % card)
    return ""
def spare(k, team):
    """r2509 K2 — 고를 URGENT 카드가 있고 ∧ (접수 상한 참 ∨ 나노 정원 참) 이면 이 팀 나노 1석을 기존 park_seat 길로 쉼.
    문턱 = «턴 끝 ∧ 유휴 ≥ DONE_IDLE 300초 ∧ 막는 미읽음 0»(keeper_settle.look 짧은 문턱 판독 그대로) · 가장 오래 쉰 석 1개 · 바퀴·팀 1석.
    ㉠ 후보 가르기 = 접수 상한 막힘이면 record.capacity() 목록(투영 holders 의 works = 완료 아님 owner)에 든 work 의 석만 · 나노 정원만 막힘이면 live 유휴 석(완료 포함) · 두 상한이 동시에 차도 접수 필터를 건다(DA#57 지적).
    ㉢ 쉼 뒤 capacity·live 를 다시 읽어 막힌 쪽(둘 다 참이면 둘 다)이 실제로 줄었을 때만 urgent_park 기억 확정(안 줄면 기억 0 + 1줄) · K3 추가 용량 0(상한·intake_open·submit 판정 그대로).
    K4 손 0: 일하는 나노 · URGENT 정규식 · 고르기 순서 · INTAKE_CAP · FT2_TEAM_NANO_MAX · 정지 · spawn · 계정 조건(정지 중이면 0). 반환 = 쉼을 낸 석 이름 또는 ""."""
    if guard(k, team)[0] is not True:   # ⑨ 팀 PAUSED · SPAWN_HOLD · ACCT_PAUSE · 근거 없는 석 · 꺼짐 = 쉼 0
        return ""
    cap = nano_cap(k, team)
    live = nano_live(k, team) if cap.isascii() and cap.isdigit() else None
    if live is None:
        return ""   # 판정 불가 = 손 0(gates 가 1줄)
    nano_full = live >= int(cap)   # 접수 판독은 «고를 긴급 카드가 있다» 를 확인한 뒤(아래) — 정원만 참이고 긴급 0 이면 project 부름 0
    if not nano_full and intake_open(k, team):
        return ""   # ⑧ 칸이 남음 = 지금 고르기 그대로
    if park_open(k, team):
        return ""   # ⑬ 그 긴급 카드가 아직 안 닫혔다 = 둘째 쉼 0
    got = cards(k, team)
    if isinstance(got, str) or not any((row or [False])[0] for row in got[0].values()):
        return ""   # ④⑭ 고를 긴급 카드 0(꼴 틀린 긴급 줄은 URGENT 가 아니라 여기서 걸린다 — 알림만)
    pick = choose(k, team, tell=False)
    if not pick or not (got[0].get(pick[0]) or [False])[0]:
        return ""   # 긴급 카드는 있지만 고를 수 있는 것이 그 긴급이 아님(막힘·우선 카드) = 쉼 0
    full = not intake_open(k, team)   # DA#57 지적 — 두 상한이 동시에 차도 접수 보유 후보 필터를 건다(정원만 참 ∧ 긴급 0 이면 위에서 이미 0)
    keep = None
    if full:   # ⑯⑰ ㉠ — 접수 상한이 막힌 때는 capacity 를 쥔 석만(완료 석은 그 목록에 없다)
        proj = k.proj_of(team) if hasattr(k, "proj_of") else {}
        keep = {w for row in ((proj.get("holders") or {}) if proj.get("result") == OK else {}).values() for w in (row.get("works") or ())}
        if not keep:
            return ""
    before, live_before = capacity_left(k, team), live
    seat = k.urgent_park(team, pick[0], keep)
    if not seat:
        return ""   # 턴 안 끝남 · 유휴 300초 미만 · 막는 미읽음 · 쉼 거부(정지) = 0
    cap2, live2 = capacity_left(k, team), nano_live(k, team)   # kill 이 바퀴 ls 캐시를 버렸다 = 다시 읽은 값
    sides = [("접수", before, cap2, full), ("나노", live_before, live2, nano_full)]   # 막힌 쪽(둘 다 참이면 둘 다)만 본다
    stuck = ["%s %s" % (name, was) for name, was, now, on in sides if on and not (now is not None and was is not None and now < was)]
    if stuck:   # ⑰ ㉢ — 막힌 쪽 값이 안 줄었다 = 기억 0 + 1줄(다음 바퀴 다른 후보)
        k.log("URGENT-PARK", team, "%s — %s 쉼 뒤 %s 그대로 — 기억 0" % (pick[0], seat, " · ".join(stuck)))
        return ""
    k.state.setdefault("urgent_park", {})[team] = pick[0]
    k.log("URGENT-PARK", team, "%s — %s 쉼 · %s" % (pick[0], seat, " · ".join("%s %s → %s" % (name, was, now) for name, was, now, on in sides if on)))
    return seat
def rotate_parked(k, team, stem):
    """r2447 K1 — 채우기 배정에 rotation 을 넘길 조건 하나(원장 줄 · state owner · 옛 holder 부재 판독).
    참 = (True, 옛 holder) · 거짓 = (False, "") → 지금 그대로 rotation 인자 없이 보낸다(K2).
    조건 = ⓐ 최신 attempt 가 쉼(parked · 사유 launch-failed 아님) ⓑ 그 work owner 없음 ⓒ 쉼 줄 옛 holder 세션 부재(abs)
    · 미착수(착수 기록 0)·결과 확정 뒤 쉼은 코어가 완료 유보를 돌려주지 않으므로 rotation 0(K4 · ⑧ ⑨)."""
    rows = [r for r in k.rows_of(team) if r.get("work") == stem]
    last = max([r.get("seq") or 0 for r in rows if r.get("kind") == "result"] or [0])   # core _hold 와 같은 기준
    if not any(r.get("kind") == "start" and (r.get("seq") or 0) > last for r in rows):
        return False, ""                                       # K4 — 미착수·결과 확정 = rotation 0
    st = ft2_state(k, team) or {}
    parked = ([r for r in rows if r.get("kind") == "parked"] or [{}])[-1]   # 원장 쉼 줄(state 줄에는 holder 칸이 없다)
    disp = ([r.get("attempt") for r in rows if r.get("kind") == "dispatch"] or [None])[-1]
    if stem in (st.get("owners") or {}) or not parked or parked.get("attempt") != disp or parked.get("reason") == "launch-failed":
        return False, ""                                       # ⓐ 쉼(launch-failed 아님) · ⓑ owner 없음
    old = str(parked.get("holder") or "")
    if not old or k.probe(old) != "absent":
        return False, ""                                       # ⓒ 부재 — 살아 있음·판독 불가 = rotation 0
    return True, old

def fill(k, team):
    """r1913 빈 나노 칸 1장 = gates→choose→submit→assign→deliver→reconcile · 실패 = 1줄 + fill_hold(원장 쓰기 0 · 그 stem 재시도 0) · 풀림 = 원장 updated > 보류 시각."""
    held, opened = k.state.setdefault("fill_hold", {}), k.state.setdefault("fill_open", {})
    mine, blocked = [x for x in opened if x.split("|")[0] == team], set()
    for x in mine:   # r1929 띄운 열기 잇기 · 그 바퀴 새 fill 0
        stem = x.split("|", 1)[1]
        nh = then_name(k, team, stem, opened[x])   # r2208 O5 띄운 때 이름(다시 셈 0)
        blocked.add(x) if nh and reconcile(k, team, "fill:" + stem, opened[x], stem, nh, None) == BLOCKED else None
        opened.pop(x) if "%s|fill:%s@%s" % (team, stem, opened[x]) in k.state["handled"] else None
    mine = [x for x in mine if x not in blocked]   # r2361 K5 — 막힌 항목은 이 바퀴 셈 밖(팀 새 fill 을 막지 않음 · fill_open 에 남아 다음 바퀴 다시 판정)
    if mine:
        return None
    release(k, team)   # r2188 H1 풀림 한 함수(원장 updated · 끝난 일) · 아래 choose 의 보류 집합 = 남은 보류
    if new_card_hold(k, team):   # r2101 H3 — 보류 = 새 카드 고르기만 멈춘다(위 이어 열기·settle·닫기는 그대로)
        return None
    urgent_form(k, team)   # r2509 K1 — 막힘 판정(gates · intake_open) 앞에서 매 바퀴 · 꼴 틀린 «- 긴급:» 줄 = 팀장 [긴급] 1통(하루 1)
    pick = intake_open(k, team) and choose(k, team, {x.split("|", 1)[1] for x in held if x.split("|")[0] == team}) if gates(k, team) and penalty_open(k, team) else None
    if not pick:
        spare(k, team)   # r2509 K2 — 나노 정원·접수 상한이 막혀 못 열었을 때만 · 이 바퀴는 쉼만(칸은 다음 fill 이 긴급 먼저 쓴다)
        return None
    stem, attempt, nh = pick[0], None, nano_name(k, team, pick[0])
    if not nh:   # r2016 빈 이름 = 채우기 0(경고 1줄은 nano_name)
        return None
    rot, old = rotate_parked(k, team, stem)   # r2447 K1 — 쉼 + owner 없음 + 옛 holder 부재 = rotation 배정
    for verb, args, ok in (("submit", ["--command", "keeper-next-" + stem, "--body", "카드 " + stem], "재부여 0"),
            ("assign", ["--holder", nh, "--evidence", ",".join(dispatch.Dispatch.REQUIRED_EVIDENCE)], "\0"),
            ("deliver", ["--mode", "intent"], "전달 의도 없음")):
        if verb == "assign" and rot:
            args = args + ["--rotation", "true"]   # r2447 K1 — 쉼 + owner 없음 + 옛 holder 부재일 때만
        out, rc = cli.run([verb, "--work", stem, "--root", k.root, "--team", team] + args + (["--attempt", attempt] if verb == "deliver" and attempt else []))
        if verb == "submit":
            k.fa.remaining(k.root, team, out.get("result"), "카드 " + stem)   # r1886 ⓐ fill submit 도 같은 줄
            if out.get("result") == "용량 부족":   # r1939 project·submit 경합 = 보류·쪽지 0 · 다음 바퀴 다시
                return k.log("FILL-WAIT", team, "%s submit 용량 부족 — 보류 0 · 다음 바퀴" % stem)
        attempt = out.get("attempt") if verb == "assign" else attempt
        if rc != 0 and ok not in str(out.get("reason")):
            k.log("HELD-NEXT", team, "fill %s %s rc %s %s %s" % (stem, verb, rc, out.get("result"), str(out.get("reason"))[:60]))
            held["%s|%s" % (team, stem)] = k.now()   # 보류 시각 = 풀림 기준(keeper state · 바퀴마다 저장)
            held.update({x: "%s|%s" % (held[x], out.get("result")) for x in held if x == "%s|%s" % (team, stem)})   # r1939 새 꼴 «시각|사유»
            return k.notify(team, "%s|fill-hold|%s|%s" % (k.stamp()[:10], team, stem), "[다음 막힘] ft2 keeper fill %s %s %s — 같은 카드 자동 재시도 0 · 원장을 손보면 다시 시도" % (stem, verb, out.get("result"))) and None
        if verb == "assign" and rot:
            k.log("FILL-ROTATE", team, "%s 옛 holder %s 부재" % (stem, old))   # K5 — rotation 을 넘긴 배정만 1줄
    reconcile(k, team, "fill:" + stem, attempt, stem, nh, pick)
    opened.update({} if "%s|fill:%s@%s" % (team, stem, attempt) in k.state["handled"] else {"%s|%s" % (team, stem): attempt})
def then_name(k, team, stem, attempt):
    """r2208 O5 — 띄운 열기 잇기 이름 = 띄운 때 이름(ft2 state owners[stem].holder · assign 이 씀 core/dispatch.py:171) · 다시 셈 0.
    state 판독 실패 = «판정 불가 · 다음 바퀴»(줄은 값이 바뀔 때만) · owner 없음 = 그 열기 닫기(handled · HELD-NEXT «복구 필요» 1줄 · 새 나노 0 · DA #330593)."""
    st, book, key = ft2_state(k, team), k.state.setdefault("then_seen", {}), "%s|%s" % (team, stem)
    if st is None:
        if book.get(key) != "state":
            k.log("판정 불가", team, "fill:%s 띄운 때 이름 못 읽음(state 판독 실패) — 다음 바퀴" % stem)
        book[key] = "state"
        return None
    book.pop(key, None)
    nh = ((st.get("owners") or {}).get(stem) or {}).get("holder")
    if isinstance(nh, str) and nh:
        return nh
    k.state["handled"]["%s|fill:%s@%s" % (team, stem, attempt)] = k.stamp()
    return k.log("HELD-NEXT", team, "fill:%s -> %s 띄운 때 이름 owner 없음 · 복구 필요" % (stem, stem))
def recov_skip(k, team, stem):
    """r2361 K1·K2 — 복구 launch 직전 카드 판정(row[3] = choose 가 건너뛰는 값) 1회 · 막힘이면 그 판정을 돌려준다("" = 통과).
    줄은 (stem, 판정) 이 바뀔 때만(기억 = keeper 상태 파일 reconcile_seen · wait_seen 과 따로) · 풀리면 그 키를 지운다."""
    got = cards(k, team)
    pre = "" if isinstance(got, str) or stem not in got[0] else got[0][stem][3]
    book, key = k.state.setdefault("reconcile_seen", {}), "%s|%s" % (team, stem)
    if not pre:   # 판정 "" = 풀림(카드 없음 = 판정 추가 0 · 지금 길)
        book.pop(key, None)
        return ""
    if book.get(key) != pre:
        why = got[0][stem][4].get("why") or ""
        k.log("RECONCILE-SKIP", team, "%s %s%s" % (stem, pre, " · " + why[:60] if why else ""))
    book[key] = pre
    return pre


def reconcile(k, team, work, attempt, stem, nh, pick):
    """launch(세션 없음) · record(원장 ≠ seat) 를 따로 맞춘다 · 실패 = 단계 + «복구 필요» 1줄(재시도 0) · 그 뒤 handled."""
    seen, led = k.probe(nh), ledger(k, stem)
    if seen not in ("absent", "alive"):
        return k.log("판정 불가", team, "%s -> %s %s %s — 다음 바퀴" % (work, stem, nh, seen))
    need = (seen == "absent", (led.get("state"), led.get("seat")) != ("seat", nh))
    def done(kind, text):   # handled = 두 단계를 맞춘 뒤 또는 «복구 필요» 뒤에만
        return k.state["handled"].update({"%s|%s@%s" % (team, work, attempt): k.stamp()}) or k.log(kind, team, "%s -> %s %s%s" % (work, stem, nh, text))
    if need[0]:
        if pick is None and not gates(k, team):   # R2 — 복구 launch 직전 현재 가드 · 막힘 = handled 0(허용 뒤 같은 사건 재개)
            return None
        if pick is None and recov_skip(k, team, stem):   # r2361 K1 — 복구 launch 도 새 고르기와 같은 카드 판정(row[3])
            return BLOCKED
        place = pick[1:] if pick else (lambda g: None if isinstance(g, str) or stem not in g[0] else g[1][4][stem][:2] if stem in g[1][4] else target(k, g[1], g[0][stem][2]))(cards(k, team))   # r2159 재개 = PR head
        if place and place[0] in k.stale:   # r1963 복구 launch 도 낡은 팩 base 로는 안 연다(handled 0 · 다음 바퀴)
            return k.log("판정 불가", team, "%s -> %s 다음 카드 보류 · 팩 fetch 실패" % (work, stem))
        argv = [sys.executable, k.env.get("FT2_KEEPER_LAUNCH") or os.path.join(HERE, "launch.py"), "--root", k.root, "--team", team, "--work", stem, "--repo", place[0], "--base", place[1], "--role", "nano"] if place else None
        att = (((ft2_state(k, team) or {}).get("deliveries") or {}).get(stem) or [None])[-1]
        spot = os.path.join(kl.projection.runtime_path(k.root, team), "launch", "%s@%s" % (stem, att))
        if place and "repo:" + place[0] in k.cache.setdefault("launching", set()) and not any(os.path.exists(spot + x) for x in (".intent", ".owner")):   # r1967 ① 같은 리포 새 열기 = 바퀴당 1개 · 나머지 다음 바퀴(여는 중 = 1칸)
            return kl.busy(k, team, nh, "LAUNCH-WAIT", "같은 리포 열기 1개 · 다음 바퀴") and None
        why = kl.launching(k, team, stem, att, nh, argv)
        k.cache.setdefault("launching", set()).add("repo:" + place[0]) if why is True and place else None   # 여는 중 셈과 같은 수명(바퀴마다 새로 · 나노 칸 셈 밖 글자)
        if why:   # r1929 True = 이번 바퀴 끝(handled 0) · 문자열 = «복구 필요»
            return None if why is True else done("HELD-NEXT", " launch %s · 복구 필요" % why)
    if need[1]:
        rc, text, err = k.call(["bash", k.env.get("FT2_CARD_ASSIGN_BIN") or os.path.join(os.path.dirname(k.close_bin or ""), "ft-card-assign-watch.sh"), "record", stem, "seat", nh], GIT_S)
        if rc != 0:
            return done("HELD-NEXT", " record rc %s %s · 복구 필요" % (rc, (text or err).strip()[:80]))
    done("NEXT", "")
