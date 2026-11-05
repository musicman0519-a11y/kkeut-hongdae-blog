"""kkeut_admin.html 의 칼럼 템플릿(buildPage)을 scripts/theme/*.html 과 같게 맞춘다 (멱등).

  python -X utf8 -I scripts/sync_admin_template.py          # 적용
  python -X utf8 -I scripts/sync_admin_template.py --check  # 바뀌는지만 보고

템플릿은 JS 템플릿 리터럴 안에 있으므로 `</script>` 는 `<\\/script>` 로 쓴다. 블록 파일에 `${` 나 백틱이 있으면 중단한다.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_theme import HEAD_START, OLD_HEAD_START, BODY_OPEN, blocks  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ADMIN = ROOT / "kkeut_admin.html"


def esc(s: str) -> str:
    assert "${" not in s and "`" not in s, "블록에 템플릿 리터럴 충돌 문자(${ 또는 `)가 있음"
    return s.replace("</script>", "<\\/script>")


def sync(text: str) -> str:
    head, header, footer = (esc(x) for x in blocks())
    a = text.index("function buildPage(d) {")
    b = text.index("</html>", a)
    b = text.index("`;", b) + len("`;")
    t = text[a:b]
    i = t.find(HEAD_START)
    if i < 0:
        i = t.index(OLD_HEAD_START)
    j = t.index("</head>", i)
    t = t[:i] + head + t[j:]
    bo = t.index(BODY_OPEN) + len(BODY_OPEN)
    if not t.startswith(header, bo):
        n = t.index("</header>\n", bo) + len("</header>\n") if t.startswith("<header", bo) else t.index("</nav>\n", bo) + len("</nav>\n")
        t = t[:bo] + header + t[n:].lstrip("\n")
    f = t.index("<footer")
    t = t[:f] + footer + "`;"
    return text[:a] + t + text[b:]


def main(argv: list[str]) -> int:
    raw = ADMIN.read_bytes()
    crlf = b"\r\n" in raw
    text = raw.decode("utf-8").replace("\r\n", "\n")
    out = sync(text)
    out_b = (out.replace("\n", "\r\n") if crlf else out).encode("utf-8")
    if out_b == raw:
        print("kkeut_admin.html: 변경 없음")
        return 0
    if "--check" in argv:
        print("kkeut_admin.html: 바뀜(저장 안 함)")
        return 1
    ADMIN.write_bytes(out_b)
    print("kkeut_admin.html: 템플릿 동기화 저장")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
