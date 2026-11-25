"""r2526 — 변이 넣기 한 길. 사본 파일에서 «바꿀 글» 1개를 «새 글» 로 바꾼다.

정확히 1번 나와야 한다(여러 번·0번 = 변이 대상이 움직였다 = «변이 넣기 실패»).
⑤ «변이 사례를 하나 골라 소스를 고치지 않은 채 돌리면 그대로 통과하고, 변이를 넣으면 Red» 의 넣기 쪽을 여기 한 곳에 둔다.
M3 변이 = 이 함수를 아무것도 안 하는 꼴로 바꿈 → 변이 검사가 Red 를 못 내고 터진다(= 그물이 살아 있다는 증거).
"""
from pathlib import Path


def swap(path, old, new, name=""):
    """사본 파일 1개에서 «바꿀 글» → «새 글». 여러 번·0번 나오면 «변이 넣기 실패» 로 터진다."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    got = text.count(old)
    assert got == 1, "변이 넣기 실패 %s %s — 바꿀 글이 %d번 나온다" % (name, p.name, got)
    p.write_text(text.replace(old, new), encoding="utf-8")
