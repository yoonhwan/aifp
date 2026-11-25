"""r2562 ft2 keeper — 오빠 답으로 닫힌 물음이 남긴 재개 요청 파일(state/card-resume/<stem>@<q_ts>.json)이
탓 카드 좌석을 다시 연다(K4 · K5). 카드 «- 재개:» 줄과 같은 자리에서 판정하고, 요청 파일 때문에 열 때만 RESUME-ANSWER 1줄.

사례
  ① 요청 at 이 최신 attempt intent 뒤 → 고름 · launch 1 · RESUME-ANSWER 1줄(반례 ① · K5)
  ② 요청 at 이 intent 앞 → 건너뜀 · «전달됨» · RESUME-ANSWER 0줄(반례 ④)
  ③ 착지 14:05 · 요청 13:00 → 건너뜀 · «이미 착지»(반례 ⑧)
  ④ 재개 줄 08:30 + 요청 08:45(둘 다 intent 09:00 앞) → 건너뜀 = 늦은 쪽으로 판정(반례 ⑦)
  ④' 재개 줄 10:30 + 요청 08:00 → 카드 줄(늦은 쪽)로 열림 · RESUME-ANSWER 0줄(카드 줄로 열리면 0줄 · K5)
  ⑤ 요청 파일 0바이트 → 그 파일만 버림 + «판정 불가» 1줄 · 재개 0 · 둘째 바퀴 같은 줄 0(반례 ⑥)
  ⑥ 이름만 .json.tmp.* 인 임시 파일 → 요청으로 읽지 않음(반례 ⑱ 앞 절)
  ⑦ 같은 요청으로 두 바퀴 → RESUME-ANSWER 합계 1줄(값이 바뀔 때만)
  ⑧ 요청 둘(08:00 · 10:00) · intent 09:00 → at 최댓값(10:00)으로 고름 · launch 1

대역 = r2111 세계(임시 root·git·가짜 tmux·launch·record · launch/<work>@<att>.intent · card-assign 원장 json).
실 tmux·명부·ft2 원장·우편함·설치 0 · sleep 0.
"""
import importlib.util, json, shutil, time  # noqa: E401
from pathlib import Path
import pytest

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("keeper_next_r2562_r2113", str(HERE / "keeper_next_reopen_name_tail_r2113.py"))
r13 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r13)
base, kw, hand = r13.base, r13.kw, r13.hand
S, KN, DAY = "r2562-Ans", "adapters/pi/keeper_next.py", "2026-11-24T"
Q, KEY, REPLY = "1795446397.092069", "r2562-ans", "1795474243.991329"


def card(w, stem=S, *heads):   # r2113 와 같은 꼴 — 표식 줄 1개(- 배정: 없음)
    w.commit("biz", {"design/harness/indices/대기/%s.md" % stem: "# 인덱스: %s\n- 배정: 없음\n%s- 상태: 대기\n" % (stem, "".join(h + "\n" for h in heads))}, "main")


def req(w, at, stem=S, q=Q, **bad):   # K3 가 남기는 요청 글 그대로
    obj = {"card": stem, "q_ts": q, "reply_ts": REPLY, "key": KEY, "at": at}
    obj.update(bad)
    path = w.state / "card-resume" / ("%s@%s.json" % (stem, q))
    kw._put(path, obj)
    return path


def skip(lines, why, stem=S):
    return [x for x in lines if x.startswith(("NEXT-SKIP harness %s" % stem, "판정 불가 harness %s" % stem)) and why in x]


def answer_lines(lines, stem=S):
    return [x for x in lines if x.startswith("RESUME-ANSWER harness %s" % stem)]


def c1(w, mp):   # ① 요청 at 10:00 > intent 09:00 → 고름 · launch 1 · RESUME-ANSWER 1줄
    hand(w, S, DAY + "09:00:00")
    card(w)
    req(w, DAY + "10:00:00")
    lines = w.round()
    assert base.launched(w) == [S], lines
    assert len(answer_lines(lines)) == 1 and skip(lines, "전달됨") == [], lines


def c2(w, mp):   # ② 요청 at 08:00 < intent 09:00 → 건너뜀 · «전달됨» · RESUME-ANSWER 0줄
    hand(w, S, DAY + "09:00:00")
    card(w)
    req(w, DAY + "08:00:00")
    lines = w.round()
    assert base.launched(w) == [] and len(skip(lines, "전달됨")) == 1 and answer_lines(lines) == [], lines


def c3(w, mp):   # ③ 착지 14:05 · 요청 13:00 → 건너뜀(착지 시각 뒤가 아님)
    sha = r13.landed_sha(w, mp, DAY + "14:05:00")
    hand(w, S, DAY + "09:00:00")
    card(w, S, "- 착지: " + sha)
    req(w, DAY + "13:00:00")
    lines = w.round()
    assert base.launched(w) == [] and skip(lines, "이미 착지"), lines


def c4(w, mp):   # ④ 재개 줄 08:30 · 요청 08:45 · intent 09:00 → 늦은 쪽(08:45)도 앞 → 건너뜀
    hand(w, S, DAY + "09:00:00")
    card(w, S, "- 재개: " + DAY + "08:30:00")
    req(w, DAY + "08:45:00")
    lines = w.round()
    assert base.launched(w) == [] and len(skip(lines, "전달됨")) == 1 and answer_lines(lines) == [], lines


def c4b(w, mp):   # ④' 재개 줄 10:30 · 요청 08:00 · intent 09:00 → 늦은 쪽 = 카드 줄 → 고름(카드 줄을 요청으로 덮지 않는다)
    hand(w, S, DAY + "09:00:00")
    card(w, S, "- 재개: " + DAY + "10:30:00")
    req(w, DAY + "08:00:00")
    lines = w.round()
    assert base.launched(w) == [S] and answer_lines(lines) == [], lines   # 카드 줄로 열림 = RESUME-ANSWER 0줄(K5)


def c5(w, mp):   # ⑤ 0바이트 요청 → 그 파일만 버림 + «판정 불가» 1줄 · 재개 0 · 둘째 바퀴 같은 줄 0(반례 ⑥)
    hand(w, S, DAY + "09:00:00")
    card(w)
    (w.state / "card-resume").mkdir(parents=True, exist_ok=True)
    (w.state / "card-resume" / ("%s@%s.json" % (S, Q))).write_text("", encoding="utf-8")
    lines = w.round()
    assert base.launched(w) == [], lines
    assert len([x for x in lines if x.startswith("판정 불가 harness %s" % S) and "재개 요청" in x]) == 1, lines
    more = r13.r11.again(w)
    assert [x for x in more[len(lines):] if "재개 요청" in x] == [], more


def c6(w, mp):   # ⑥ 임시 파일(이름 꼴 .json.tmp.*) → 요청 아님 · 재개 0 · 판정 불가 0줄
    hand(w, S, DAY + "09:00:00")
    card(w)
    d = w.state / "card-resume"
    d.mkdir(parents=True, exist_ok=True)
    (d / ("%s@%s.json.tmp.%d" % (S, Q, 0xA1))).write_text(json.dumps({"card": S, "q_ts": Q, "at": DAY + "10:00:00"}), encoding="utf-8")
    lines = w.round()
    assert base.launched(w) == [] and [x for x in lines if "재개 요청" in x] == [], lines


def c7(w, mp):   # ⑦ 같은 요청으로 두 바퀴 → RESUME-ANSWER 합계 1줄(값이 바뀔 때만)
    hand(w, S, DAY + "09:00:00")
    card(w)
    req(w, DAY + "10:00:00")
    lines = w.round()
    more = r13.r11.again(w)   # 둘째 바퀴 = 새 keeper 인스턴스(그 바퀴 줄만)
    assert len(answer_lines(lines)) == 1 and answer_lines(more) == [], (lines, more)


def c8(w, mp):   # ⑧ 요청 둘(08:00 · 10:00) · intent 09:00 → at 최댓값으로 판정 = 고름
    hand(w, S, DAY + "09:00:00")
    card(w)
    req(w, DAY + "08:00:00", q="1795446397.000001")
    req(w, DAY + "10:00:00", q="1795446397.000002")
    lines = w.round()
    assert base.launched(w) == [S] and len(answer_lines(lines)) == 1, lines


CASES = {"①": c1, "②": c2, "③": c3, "④": c4, "④'": c4b, "⑤": c5, "⑥": c6, "⑦": c7, "⑧": c8}
MUTANTS = {"M1": ("    if not back and req_at is None:\n", "    if not back:\n", ("①",)),   # 요청 파일 안 봄 = 답 재개 영구 누락
           "M2": ("from_req = req_at is not None and (at is None or req_at >= at)", "from_req = req_at is not None", ("④'",)),   # 카드 줄 무시
           "M3": ("    return max(ok, key=lambda x: x[0]) if ok else (None, None)", "    return min(ok, key=lambda x: x[0]) if ok else (None, None)", ("⑧",))}   # 첫 요청(at 최솟값)으로 판정


def run(name, tmp, mp, ft2=kw.FT2):
    w = base.world(tmp, mp, {}, ft2=ft2)
    CASES[name](w, mp)


@pytest.mark.parametrize("name", list(CASES))
def test_case(name, tmp_path, monkeypatch):
    run(name, tmp_path, monkeypatch)


@pytest.mark.parametrize("name", list(MUTANTS))
def test_mutant(name, tmp_path, monkeypatch):
    old, new, cases = MUTANTS[name]
    tree = tmp_path / "m" / "ft2"
    shutil.copytree(kw.FT2, tree, ignore=shutil.ignore_patterns("tests", "__pycache__"))
    text = (tree / KN).read_text(encoding="utf-8")
    assert text.count(old) == 1, (name, old)
    (tree / KN).write_text(text.replace(old, new), encoding="utf-8")
    for case in cases:
        bad, good = tmp_path / ("bad" + case), tmp_path / ("good" + case)
        bad.mkdir(), good.mkdir()
        with pytest.raises(AssertionError):
            run(case, bad, monkeypatch, tree)
        run(case, good, monkeypatch)   # 원본으로 같은 사례 1회 더 = PASS
