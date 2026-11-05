"""공유 미리보기(og:image) 만들기 + 전 페이지·어드민 템플릿에 메타 태그 넣기 (멱등).

  python -X utf8 -I scripts/theme/og_image.py

- assets/og-image.png: 1200×630, 흰 바탕 가운데 세로형 로고(logo-vertical.svg, 벡터 → PNG). 카카오톡·네이버·페이스북이 쓰는 표준 크기.
- 각 페이지 head 의 og:url 줄 뒤에 og:image / og:image:width / og:image:height / twitter:card 를 넣는다(이미 있으면 그대로).
- kkeut_admin.html 의 buildPage 템플릿에도 같은 줄을 넣는다. 초안은 new_column.py 를 다시 돌려 반영한다.
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

import pymupdf as fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "kkeut_seo_site"
OUT = SITE / "assets" / "og-image.png"
BASE = "https://hongdaekkeutclinic.com"
W, H = 1200, 630
TAGS = (
    f'<meta property="og:image" content="{BASE}/assets/og-image.png">\n'
    f'<meta property="og:image:width" content="{W}">\n'
    f'<meta property="og:image:height" content="{H}">\n'
    '<meta name="twitter:card" content="summary_large_image">\n'
)


def make_image() -> None:
    svg = fitz.open(SITE / "assets" / "logo-vertical.svg")
    page = svg[0]
    target_h = 400
    scale = target_h / page.rect.height
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=True)
    logo = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGBA")
    canvas = Image.new("RGB", (W, H), (255, 255, 255))
    # 아래쪽 얇은 분홍 띠
    canvas.paste((253, 238, 243), (0, H - 14, W, H))
    x = (W - logo.width) // 2
    y = (H - 14 - logo.height) // 2
    canvas.paste(logo, (x, y), logo)
    canvas.save(OUT, "PNG", optimize=True)
    print(f"og-image.png {W}x{H} {OUT.stat().st_size // 1024}KB (로고 {logo.width}x{logo.height})")


def insert_tags(text: str, after_pattern: str) -> tuple[str, bool]:
    if 'property="og:image"' in text:
        return text, False
    m = re.search(after_pattern, text)
    assert m, "og:url 줄을 못 찾음"
    return text[: m.end()] + TAGS + text[m.end():], True


def main() -> int:
    make_image()
    changed = 0
    for p in sorted(SITE.glob("*.html")):
        if re.match(r"^(google|naver)[0-9a-f]+\.html$", p.name):
            continue
        raw = p.read_bytes()
        t, did = insert_tags(raw.decode("utf-8"), r'<meta property="og:url" content="[^"]*">\n')
        if did:
            p.write_bytes(t.encode("utf-8"))
            changed += 1
    admin = ROOT / "kkeut_admin.html"
    raw = admin.read_bytes()
    t, did = insert_tags(raw.decode("utf-8"), r'<meta property="og:url" content="\$\{d\.site\}/\$\{d\.file\}">\n')
    if did:
        admin.write_bytes(t.encode("utf-8"))
        print("kkeut_admin.html 템플릿에 og:image 추가")
    print(f"페이지 {changed}개에 og:image 추가 (나머지는 이미 있음)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
