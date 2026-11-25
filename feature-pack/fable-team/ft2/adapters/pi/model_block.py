"""ft 2.0 공급자 막힘 표식 · 대체 모델 (r2490 · K1 ~ K8 중 표식·판정·대체 결정).

한 곳에서 판정하고(keeper 바퀴당 1회 · sweep) 한 곳에서 쓴다(launch 의 좌석 열기 · route).
표식 = <데이터 루트>/.fable-team/state/model-block/<공급자>.json 1개 · 쓰는 이 = keeper 뿐(sweep).
`probe` 단계(K8)는 같은 표식의 phase 칸이다 — 표식 파일은 늘 1개다.

계약: K1 감지(ⓐ 계정 정지 판정기 rc3 · ⓑ 15분 안 BLOCKED 오류 턴) · K2 BLOCKED 낱말(keeper_stall_error.BLOCK) ·
K3 표식·로그 MODEL-BLOCK·쪽지 2통(처음 참이 된 바퀴 1회) · K4 대체 결정(launch 가 부른다) · K5 닫힌 쪽(대체 0 사유) ·
K6 다음 카드 게이트 · K8 풀림(탐침 1석 → MODEL-UNBLOCK). K7(깨움 0 · 재배정 1회)은 keeper_stall.py 몫.
"""
import glob
import importlib.util
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
FT2 = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(".fable-team", "state", "model-block")
WINDOW_S = 900          # K1 ⓑ — 오류 시각이 지금부터 15분 안
HEAD = 80               # K3 쪽지에 넣는 오류 글 머리
STAMP = "%Y-%m-%dT%H:%M:%S"
UNSURE = "판정 불가 대체 0"


def _load(rel, alias):
    spec = importlib.util.spec_from_file_location(alias, os.path.join(FT2, rel))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ERR = _load(os.path.join("adapters", "pi", "keeper_stall_error.py"), "ft2_model_block_err")
_MODELS = {}


def models():
    """tools/models.py 1회 로드(표 읽기 = 읽기만 · 쓰기 0)."""
    if "m" not in _MODELS:
        _MODELS["m"] = _load(os.path.join("tools", "models.py"), "ft2_model_block_models")
    return _MODELS["m"]


def provider(model):
    """모델 id → 공급자(provider-of-model.tsv 첫 일치) · 표에 없음 = None(지어내기 0)."""
    base = models().base_model(model or "")
    return next((name for pattern, name in models().rows("provider-of-model.tsv") if re.search(pattern, base)), None)


def fallback(model):
    """모델 id → 대체 모델(model-fallback.tsv) · 행이 없음 = None(= 대체 표에 행 없음 · K5)."""
    return dict(models().rows("model-fallback.tsv")).get(models().base_model(model or ""))


def role_model(role):
    """역할 → 기본 모델 | None(역할 표에 없음 · 다른 역할 행으로 대신하지 않는다)."""
    item = models().role(role) if role else None
    return item and item["model"]


def folder(root):
    return os.path.join(root, STATE)


def path(root, provider_name):
    return os.path.join(folder(root), provider_name + ".json")


def read(root, provider_name):
    """표식 1개 | None(없음·깨짐). 깨진 표식은 없는 것으로 보지 않는다 — phase 칸으로 거른다."""
    try:
        with open(path(root, provider_name), encoding="utf-8") as fh:
            row = json.load(fh)
    except (OSError, ValueError):
        return None
    return row if isinstance(row, dict) else None


def write(root, provider_name, row):
    """표식 원자 쓰기(tmp → replace) · keeper 만 부른다."""
    os.makedirs(folder(root), exist_ok=True)
    one = path(root, provider_name)
    with open(one + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(row, fh, ensure_ascii=False, sort_keys=True)
    os.replace(one + ".tmp", one)


def clear(root, provider_name):
    """표식 삭제 — 지웠으면 True(없었으면 False)."""
    try:
        os.unlink(path(root, provider_name))
        return True
    except OSError:
        return False


def marked(root):
    """표식이 있는 공급자 이름 목록."""
    return sorted(os.path.basename(one)[:-5] for one in glob.glob(os.path.join(folder(root), "*.json")))


def junk(root):
    """표식으로 못 읽는 파일(계약 밖 이름) — keeper 가 «판정 불가» 1줄로 알린다(조용한 무시 0)."""
    return sorted(os.path.basename(one) for one in glob.glob(os.path.join(folder(root), "*")) if not one.endswith(".json"))


def runtime(root, team):
    return os.path.join(os.path.abspath(root), ".fable-team", "teams", team, "runtime")


def intents(root, team):
    """그 팀의 열기 의도 1개씩 = (경로, 칸 dict) · 깨진 의도는 뺀다(판독 불가 = 그 좌석 없음)."""
    out = []
    for one in sorted(glob.glob(os.path.join(runtime(root, team), "launch", "*.intent"))):
        try:
            with open(one, encoding="utf-8") as fh:
                row = json.load(fh)
        except (OSError, ValueError):
            continue
        if isinstance(row, dict):
            out.append((one, row))
    return out


def running(row):
    """그 의도가 띄운 좌석의 «지금 도는 모델» — 대체로 열었으면 대체 · 아니면 역할 기본값."""
    return row.get("model_fallback") or row.get("model") or role_model(row.get("role"))


def probe_seats(root, teams):
    """K8 — probe 칸이 선 의도 전부(최근 것부터) → [(팀, holder, worktree, 경로 mtime)]."""
    out = []
    for team in teams:
        for one, row in intents(root, team):
            if row.get("probe") and row.get("state") in ("opening", "opened") and row.get("FT2_HOLDER"):
                try:
                    age = os.path.getmtime(one)
                except OSError:
                    age = 0.0
                out.append((team, row["FT2_HOLDER"], row.get("worktree") or "", age))
    return sorted(out, key=lambda one: one[3], reverse=True)


def probe_seat(root, teams, alive):
    """K8 불변식의 셈 — «살아 있는» 탐침 좌석 1석(의도 probe 칸 ∧ tmux 세션 살아 있음) → (팀, holder, worktree) | None.
    alive = 이 바퀴 세션 이름 집합 · None(판독 불가) = 살아 있는 것으로 보지 않는다(새 탐침 0)."""
    if alive is None:
        return None
    for team, holder, tree, _ in probe_seats(root, teams):
        if holder in alive:
            return team, holder, tree
    return None


def sessions(env=None, binary=None, timeout=7):
    """tmux list-sessions 1회(launch 쪽 — keeper 캐시 밖) → 집합 | None(판독 불가).

    «no server running» = 세션 0(판독 실패 아님 — 서버가 아직 없을 뿐이다). 그 밖의 rc≠0 = None(판독 불가 · 새 탐침 0)."""
    cmd = [binary or (env or {}).get("FT_TMUX") or "tmux", "list-sessions", "-F", "#{session_name}"]
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, env=env)
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode == 0:
        return set(done.stdout.split())
    if "no server running" in ((done.stderr or "") + (done.stdout or "")).lower():
        return set()
    return None


def live(k):
    """이 바퀴 살아 있는 세션 이름 집합(바퀴 1회 읽기 · keeper.cache 공유) | None(판독 불가)."""
    book = k.cache.setdefault("@round", {})
    if "ls" not in book:
        book["ls"] = k.call([k.tmux, "list-sessions", "-F", "#{session_name}"])
    rc, out, _ = book["ls"]
    return set(out.split()) if rc == 0 else None


def evidence(k, provider_name, teams):
    """K1 ⓑ — 그 공급자 모델로 떠 있는 현역 holder 중 마지막 assistant 가 15분 안 BLOCKED 인 첫 1석 → (팀, holder, 시각, 글) | None."""
    alive = live(k)
    if alive is None:
        return None
    for team in teams:
        for _, row in intents(k.root, team):
            holder, tree = row.get("FT2_HOLDER"), row.get("worktree") or ""
            if row.get("state") != "opened" or not holder or holder not in alive or provider(running(row)) != provider_name:
                continue
            session = k.stall.session(tree, holder)
            if type(session) is not str:          # None · Unsure(판정 불가) = 근거 0
                continue
            try:
                got = ERR.error_detail(session)
            except OSError:
                continue
            if got is None or not ERR.blocked(got[0], got[2]) or got[1] is None or k.now() - got[1] >= WINDOW_S:
                continue
            return team, holder, got[1], got[2]
    return None


def judge(k, provider_name):
    """K1 ⓐ — 1.x 판정기 status --check <P> 1회(부작용 0) · rc 3 만 «유효 정지» · 그 밖(0·4·None)은 거짓.

    부르는 자리 = state/ACCT_PAUSE 가 있을 때만(keeper_next.gates 와 같은 문) — 한 번도 정지가 없던 root 에서
    없는 도구를 바퀴마다 부르지 않는다(그때 rc 127 «판정 불가» 줄도 0)."""
    if not os.path.lexists(os.path.join(k.root, ".fable-team", "state", "ACCT_PAUSE")):
        return 0
    tool = os.path.join(os.path.dirname(k.close_bin or ""), "ft-acct-pause.sh")
    return k.call(["bash", tool, "status", "--check", provider_name])[0]


def providers(k):
    """판정할 공급자 = 역할 기본표의 공급자 ∪ 표식이 있는 공급자(풀림을 아무도 안 보게 두지 않는다)."""
    found = set(marked(k.root))
    try:
        found |= {p for row in models().role_defaults().values() for p in [provider(row[0])] if p}   # r2541: 행 = (모델·effort·실행기·fast)
    except (OSError, ValueError):
        pass                                  # 표 손상 = 표식 있는 공급자만(판정 불가 1줄은 sweep 몫)
    return sorted(found)


def routes(provider_name):
    """그 공급자를 기본으로 쓰는 역할들 → «역할 = 대체 모델» 글(쪽지·로그 1구)."""
    try:
        table = models().role_defaults()
    except (OSError, ValueError):
        return ""
    return " · ".join("%s = %s" % (role, fallback(row[0]) or "대체 표 행 없음")
                      for role, row in sorted(table.items()) if provider(row[0]) == provider_name)


def announce(k, team, provider_name, text, basis):
    """K3 — 막힘이 처음 참이 된 바퀴: 로그 MODEL-BLOCK 1줄 + 팀장·planner 팀장 앞 쪽지 1통씩(같은 막힘 = 0)."""
    body = "[모델 대체] %s 막힘(%s) → %s" % (provider_name, (text or basis)[:HEAD], routes(provider_name) or "역할 표 못 읽음")
    day = k.stamp()[:10]
    k.log("MODEL-BLOCK", team or "-", "%s 막힘 근거 %s%s — %s" % (provider_name, basis, " " + text[:HEAD] if text else "", routes(provider_name)))
    for target in (team, "planner"):
        if target:
            k.notify(target, "%s|model-block|%s|%s" % (day, provider_name, target), body)
    return body


def sweep(k):
    """K1 · K3 · K8 — keeper 바퀴당 1회: 공급자마다 막힘을 판정하고 표식을 쓰거나 탐침 단계로 넘긴다."""
    teams = k.teams()
    for provider_name in providers(k):
        row = read(k.root, provider_name)
        rc = judge(k, provider_name)
        if rc not in (0, 3):                            # 값이 바뀔 때만 1줄(r2266 같은 값 묵음 · 바퀴마다 같은 줄 0)
            book = k.state.setdefault("block_judge", {})
            if book.get(provider_name) != str(rc):
                book[provider_name] = str(rc)
                k.log("판정 불가", "-", "%s 판정기 rc %s — ⓐ 거짓(ⓑ 만으로 판정)" % (provider_name, rc))
        else:
            k.state.setdefault("block_judge", {}).pop(provider_name, None)
        found = evidence(k, provider_name, teams)
        if row and row.get("phase") == "probe" and rc != 3 and not found:
            watch(k, provider_name, row, teams)          # K8 — 탐침 좌석 1석의 턴을 본다
            continue
        if rc == 3 or found:
            team, seat, at, text = found if found else (teams[0] if teams else "", "", 0, "")
            basis = "ⓑ" if found else "ⓐ"
            if not row or row.get("phase") != "blocked":
                write(k.root, provider_name, {"provider": provider_name, "since": k.stamp(), "basis": basis, "probe": "",
                                              "team": team, "seat": seat, "last_error": at or 0, "phase": "blocked"})
                announce(k, team, provider_name, text, basis)
            elif found and at and at > (row.get("last_error") or 0):
                write(k.root, provider_name, dict(row, last_error=at, seat=seat, team=team, probe=""))
            continue
        if row is not None:                              # ⓐ ⓑ 둘 다 거짓 = 탐침 단계(K8 · 새 쪽지 0)
            write(k.root, provider_name, dict(row, phase="probe", probe=""))


def normal(path):
    """정상 종료 assistant 턴(pi stop 낱말) — K8 탐침 성공 판정(오류 칸 0)."""
    recs = [r for r in ERR.records(path) or () if r["message"].get("role") == "assistant"][-1:]
    return bool(recs) and recs[0]["message"].get("stopReason") in ("stop", "end_turn", "max_tokens") \
        and not ERR.is_error(recs[0]["message"])


def watch(k, provider_name, row, teams):
    """K8 탐침 한살이 — 끝은 넷뿐이다.

    ㉠ 첫 정상 assistant 턴 → 표식 삭제 · MODEL-UNBLOCK 1줄 + 쪽지 1통
    ㉡ BLOCKED 오류 턴 → 막힘 단계로 복귀 · probe 칸 비움 · 쪽지 0
    ㉢ 정상 턴 없이 «끝남이 확인됨»(세션 없음 · 옛 holder 내려감) → 탐침 단계 유지 · probe 칸 비움 · MODEL-PROBE-RETRY 1줄 · 쪽지 0
    ㉣ 살아 있는데 판정이 없음(비BLOCKED 오류 턴 · 턴 0) → probe 칸 그대로(새 탐침 0) · 그 좌석은 지금 멈춤 규칙에 맡긴다
    생존 판독 실패 = «판정 불가» 1줄 · probe 칸 그대로."""
    alive = live(k)
    if alive is None:
        return self_quiet(k, provider_name, "생존 판독 실패")
    taken = probe_seat(k.root, teams, alive)
    holder = row.get("probe") or ""
    if taken is None:                                  # 살아 있는 탐침 0 = ㉢(끝남 확인) 또는 아직 연 적 없음
        stale = probe_seats(k.root, teams)
        gone = holder or (stale[0][1] if stale else "")
        return retire(k, provider_name, row, gone) if gone else None
    team, holder, tree = taken
    session = k.stall.session(tree, holder)
    if type(session) is not str:
        return self_quiet(k, provider_name, "탐침 좌석 %s 세션 판독 불가" % holder)   # 판정 불가 · probe 칸 그대로
    if not os.path.isfile(session):
        return retire(k, provider_name, row, holder)   # 세션 파일 없음 = 끝남 확인(㉢)
    try:
        ok, got = normal(session), ERR.error_detail(session)
    except OSError:
        return self_quiet(k, provider_name, "탐침 좌석 %s 세션 파일 못 읽음" % holder)
    if ok and got is None:                             # ㉠
        clear(k.root, provider_name)
        k.log("MODEL-UNBLOCK", team, "%s 풀림 — 탐침 좌석 %s 정상 턴" % (provider_name, holder))
        k.notify(team, "%s|model-unblock|%s|%s" % (k.stamp()[:10], provider_name, team),
                 "[모델 대체 해제] %s 풀림 — 탐침 좌석 %s 정상 턴 → 원래 모델로 연다(%s)" % (provider_name, holder, routes(provider_name)))
        return
    if got is not None and ERR.blocked(got[0], got[2]):   # ㉡ 막힘 복귀(쪽지 0)
        write(k.root, provider_name, dict(row, phase="blocked", probe="", last_error=got[1] or 0))
        return
    if row.get("probe") != holder:                     # ㉣ 살아 있는 탐침 — probe 칸만 채운다(새 탐침 0)
        write(k.root, provider_name, dict(row, probe=holder))


def retire(k, provider_name, row, holder):
    """㉢ — 탐침 좌석이 정상 턴 없이 끝났다: 표식은 탐침 단계 그대로 · probe 칸 빔 · MODEL-PROBE-RETRY 1줄 · 쪽지 0.
    같은 탐침의 끝남은 한 번만 알린다(다음 바퀴 같은 줄 0 · 새 탐침은 다른 holder 라 다시 1줄)."""
    book = k.state.setdefault("block_probe_retired", {})
    if book.get(provider_name) != holder:
        book[provider_name] = holder
        k.log("MODEL-PROBE-RETRY", row.get("team") or "-",
              "%s 탐침 좌석 %s 끝남 확인 — 새 탐침 1석 연다(표식은 탐침 단계)" % (provider_name, holder))
    if row.get("probe"):
        write(k.root, provider_name, dict(row, probe=""))


def self_quiet(k, provider_name, why):
    """탐침 좌석 판독 실패 = «판정 불가» 1줄(같은 사유가 이어지면 다시 쓰지 않는다 · probe 칸 그대로)."""
    book, value = k.state.setdefault("block_probe_unsure", {}), provider_name
    if book.get(value) == why:
        return
    book[value] = why
    k.log("판정 불가", "-", "%s %s — probe 칸 그대로(새 탐침 0)" % (provider_name, why))

def gate_open(k, team, role="nano"):
    """K6 — 계정 정지가 유효해도 그 팀이 열 역할의 기본 모델 공급자에 표식이 있고 대체가 정해지면 참.

    정지 공급자와 무관한 역할 · 표식 없는 공급자(⑫)는 여기서 거짓 = 지금 게이트 그대로."""
    try:
        model = role_model(role)
        provider_name = provider(model) if model else None
    except (OSError, ValueError):
        return False
    if not provider_name or not read(k.root, provider_name):
        return False
    return bool(fallback(model))


def route(root, item, folder_launch, team, env=None):
    """K4 · K5 — (대체 반영한 item | None, 의도에 더할 칸, 닫힌 쪽 사유).

    표식이 없으면 그대로(③ 의도 줄·argv 글자 같음). 표식이 «탐침» 이고 그 공급자 원래 모델로 살아 있는 탐침이 0석이면
    이번 1석만 원래 모델로 열고 probe 칸을 남긴다(K8 불변식 = 원래 모델 새 좌석 살아 있는 것 1석 이하).
    탐침 생존 판독이 실패하면 새 탐침 0 — 그 열기는 대체 모델로 간다(판정 불가 1줄은 keeper 가 낸다).
    K5 닫힌 쪽 = (None, {}, 사유) → 열기 0 — 대체 표에 행 없음 · 대체 모델 공급자에도 표식 · 표 손상."""
    try:
        provider_name = provider(item["model"])
        if not provider_name:
            return item, {}, ""
        row = read(root, provider_name)
        if not row:
            return item, {}, ""
        if row.get("phase") == "probe":
            alive = sessions(env)
            if alive is None:                               # K8 — 생존 판독 실패 = 새 탐침 0(원래 모델로 열지 않는다)
                pass                                        # 아래 대체 갈래로 내려간다(원래 모델 새 좌석 1석 이하 유지)
            elif probe_seat(root, [team], alive) is None:
                return item, {"model": item["model"], "probe": True}, ""
        swap = fallback(item["model"])
        if not swap:                                        # K5 대체 표에 행이 없음
            return None, {}, "대체 표에 행 없음(%s)" % item["model"]
        target = provider(swap)
        if not target:
            return None, {}, "대체 모델 공급자 불명(%s)" % swap
        if read(root, target):                              # K5 대체의 대체 0
            return None, {}, "대체 모델 공급자 표식(%s)" % target
    except (OSError, ValueError) as exc:                    # 표 손상 = 열기 0(추측 0)
        return None, {}, "표 손상 %s" % str(exc)[:60]
    return dict(item, model=swap, argv=models().launch_argv(swap, item["effort"], item.get("executor", "pi"), item.get("fast", "-"))), {"model": item["model"], "model_fallback": swap}, ""


def _rows(folder_launch):
    """그 팀 열기 의도 폴더의 (경로, 칸) — 탐침 좌석이 이미 있는지 보는 읽기 1회."""
    out = []
    for one in sorted(glob.glob(os.path.join(folder_launch, "*.intent"))):
        try:
            with open(one, encoding="utf-8") as fh:
                out.append((one, json.load(fh)))
        except (OSError, ValueError):
            continue
    return out
