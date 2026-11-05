"""공통 블록 치환 + 옛 색 클래스 매핑 (ui-restyle 8번).

  python -X utf8 -I scripts/apply_theme.py          # 적용
  python -X utf8 -I scripts/apply_theme.py --check  # 바뀔 파일만 보고, 저장 안 함(바뀌면 종료 코드 1)

대상: kkeut_seo_site/*.html 중 index.html(손으로 관리)·magazine-*.html(build.py 가 columns.html 로 재생성) 제외.
하는 일(각각 멱등):
  1. <head> 의 공통 부분(HEAD_START 부터 </head> 앞까지) → scripts/theme/head.html
  2. <body …> 다음부터 첫 </nav> 까지(옛 상단바·헤더·nav) → scripts/theme/header.html  (이미 새 헤더면 건너뜀)
  3. <footer 부터 끝까지 → scripts/theme/footer.html (+ </body> 앞에 floating.html)
  4. 옛 색 클래스·임의 색 → 새 토큰 (MAP 순서대로)
  5. h1·h2 의 font-extrabold → font-bold (Gowun Batang 은 700 까지)
  6. 시술 페이지의 페이지별 하단 고정 바는 모바일에서 숨김(hidden md:block) — floating.html 의 #quickbar 와 겹치지 않게
줄바꿈은 파일별로 보존한다. 끝나면 build.py 를 돌려 허브 5쪽을 다시 만든다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "kkeut_seo_site"
THEME = ROOT / "scripts" / "theme"
HEAD_START = '<script src="https://cdn.tailwindcss.com">'
BODY_OPEN = '<body class="antialiased">\n'
SKIP: set[str] = set()  # index.html 도 포함(머리말의 페이지별 메타·preload 는 HEAD_START 앞이라 보존됨)

MAP = [  # (정규식, 치환) — 순서 중요(kpinksoft 가 kpink 보다 먼저)
    (r"(?<!\w)brandorange(?!\w)", "rose"),
    (r"(?<!\w)khot(?!\w)", "rose"),
    (r"(?<!\w)kpinksoft(?!\w)", "pinksoft"),
    (r"(?<!\w)kpink(?!\w)", "blush"),
    (r"(?<!\w)kyellow(?!\w)", "kakao"),
    (r"(?<!\w)card(red|blue|teal|navy|magenta|green)(?!\w)", "rose"),
    (r"\[#1a1a1a\]", "ink"),
    (r"\[#03C75A\]", "naver"),
    (r"\[#FBD3DC\]", "pink"),
    (r"\[#4a4a4a\]", "ink/70"),
]
OLD_BAR = 'class="fixed bottom-4 inset-x-0 z-40 px-4"'
NEW_BAR = 'class="fixed bottom-4 inset-x-0 z-40 px-4 hidden md:block"'
# 시술 페이지 하단 바 안의 버튼 3개: 원색(노랑·초록·검정) → 흰 바탕 + 선, 주 행동(시술 선택하기)만 rose
BAR_BUTTONS = [
    ("w-11 h-11 rounded-xl bg-kakao flex flex-col items-center justify-center text-[9px] font-bold",
     "w-11 h-11 rounded-xl bg-white border border-black/15 flex flex-col items-center justify-center text-[9px] font-bold hover:border-rose hover:text-rose ease-rt"),
    ("rounded-xl bg-naver text-white font-semibold text-[14px] px-5 py-3 hover:brightness-110 ease-rt",
     "rounded-xl bg-white border border-black/15 font-semibold text-[14px] px-5 py-3 hover:border-black ease-rt"),
    ("rounded-xl bg-ink text-white font-semibold text-[14px] px-5 py-3 hover:bg-rose ease-rt",
     "rounded-xl bg-rose text-white font-semibold text-[14px] px-5 py-3 hover:brightness-110 ease-rt"),
]


def blocks() -> tuple[str, str, str]:
    head = (THEME / "head.html").read_text(encoding="utf-8")
    header = (THEME / "header.html").read_text(encoding="utf-8")
    footer = (THEME / "footer.html").read_text(encoding="utf-8")
    floating = (THEME / "floating.html").read_text(encoding="utf-8")
    assert footer.count("</body>") == 1
    return head, header, footer.replace("</body>", floating + "</body>")


def transform(text: str, head: str, header: str, footer: str) -> str:
    # 1. head 공통 부분
    i = text.index(HEAD_START)
    j = text.index("</head>", i)
    text = text[:i] + head + text[j:]
    # 2. 상단바·헤더·nav (옛 구조: <body> 다음 ~ 첫 </nav> / 새 구조: <header …> ~ </header>)
    b = text.index(BODY_OPEN) + len(BODY_OPEN)
    if not text.startswith(header, b):
        if text.startswith("<header", b):
            n = text.index("</header>\n", b) + len("</header>\n")
        else:
            n = text.index("</nav>\n", b) + len("</nav>\n")
        rest = text[n:].lstrip("\n")
        text = text[:b] + header + "\n" + rest
    # 3. footer + floating
    f = text.index("<footer")
    text = text[:f] + footer
    # 4. 색 매핑 (head 는 이미 새것이므로 본문에만 영향)
    for pat, rep in MAP:
        text = re.sub(pat, rep, text)
    # 5. h1·h2 굵기
    text = re.sub(r"(<h[12]\b[^>]*?)font-extrabold", r"\1font-bold", text)
    # 6. 페이지별 하단 바는 모바일 숨김 + 버튼 색 낮춤(바 블록 안에서만)
    text = text.replace(OLD_BAR, NEW_BAR)
    s = text.find(NEW_BAR)
    if s >= 0:
        e = text.index("<footer", s)
        bar = text[s:e]
        for old, new in BAR_BUTTONS:
            bar = bar.replace(old, new)
        text = text[:s] + bar + text[e:]
    return text


def fill_nav() -> None:
    """header.html 의 매거진 드롭다운(mg:nav)을 posts.json 기준으로 먼저 채운다 — 빈 드롭다운이 전파되지 않게."""
    sys.path.insert(0, str(Path(__file__).resolve().parent / "magazine"))
    import build as B  # noqa: WPS433
    d = B.load()
    B.apply(THEME / "header.html", {"nav": B.frag_nav(d)}, write=True)


def main(argv: list[str]) -> int:
    check = "--check" in argv
    fill_nav()
    head, header, footer = blocks()
    rc = 0
    changed = 0
    for p in sorted(SITE.glob("*.html")):
        if p.name in SKIP or p.name.startswith("magazine-"):
            continue
        raw = p.read_bytes()
        crlf = b"\r\n" in raw
        text = raw.decode("utf-8").replace("\r\n", "\n")
        try:
            out = transform(text, head, header, footer)
        except ValueError as e:
            print(f"오류: {p.name}: 블록을 못 찾음 ({e})")
            rc = 1
            continue
        out_b = (out.replace("\n", "\r\n") if crlf else out).encode("utf-8")
        if out_b != raw:
            changed += 1
            print(("바뀜(저장 안 함): " if check else "저장: ") + p.name)
            if check:
                rc = 1
            else:
                p.write_bytes(out_b)
    print(f"대상 {changed}개 변경" + (" — 변경 없음" if changed == 0 else ""))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
