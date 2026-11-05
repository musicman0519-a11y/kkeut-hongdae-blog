"""첫 화면 배너 사진 넣기 (메인 히어로 / FIND YOUR CARE).

  python -X utf8 -I scripts/theme/banner_photo.py <원본 사진> --slot hero [--focus "65% center"]
  python -X utf8 -I scripts/theme/banner_photo.py <원본 사진> --slot find [--focus "center 30%"]

하는 일: 리사이즈(확대 없음) → WebP(+모바일용 작은 판) + JPG 폴백을 assets/home/ 에 저장(크기 상한에 맞춰 품질 조절)
       → index.html 의 해당 자리를 <picture data-slot="…"> 로 바꾼다(이미 바꿨으면 그 블록을 다시 쓴다 — 멱등).
       히어로는 preload 링크도 함께 갱신한다. 마크업은 #hero·#find 의 그림 한 곳씩만 건드린다.
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "kkeut_seo_site"
HOME = SITE / "assets" / "home"
INDEX = SITE / "index.html"

SLOTS = {
    # 이름: (파일 이름, 데스크톱 최대 폭, 모바일 폭, WebP 상한 KB, 모바일 상한 KB)
    "hero": ("hero", 1920, 960, 120, 60),
    "find": ("find", 1280, 0, 100, 0),
}


def encode(im: Image.Image, fmt: str, limit_kb: int) -> bytes:
    """상한에 맞을 때까지 품질을 낮춰 인코딩. 상한 0 이면 품질 82 고정."""
    q = 82
    while True:
        buf = io.BytesIO()
        if fmt == "webp":
            im.save(buf, "WEBP", quality=q, method=6)
        else:
            im.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
        data = buf.getvalue()
        if not limit_kb or len(data) <= limit_kb * 1024 or q <= 40:
            return data
        q -= 6


def resize(im: Image.Image, width: int) -> Image.Image:
    if width <= 0 or im.width <= width:
        return im
    return im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)


def save_variants(src: Path, slot: str) -> dict:
    name, w_desk, w_mob, lim, lim_m = SLOTS[slot]
    im = Image.open(src)
    if im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im.convert("RGBA"), mask=im.convert("RGBA").split()[-1])
        im = bg
    else:
        im = im.convert("RGB")
    out = {}
    d = resize(im, w_desk)
    (HOME / f"{name}.webp").write_bytes(encode(d, "webp", lim)); out["webp"] = (f"{name}.webp", d.size)
    (HOME / f"{name}.jpg").write_bytes(encode(resize(im, min(w_desk, 1600)), "jpg", 0)); out["jpg"] = (f"{name}.jpg", resize(im, min(w_desk, 1600)).size)
    if w_mob:
        m = resize(im, w_mob)
        (HOME / f"{name}-m.webp").write_bytes(encode(m, "webp", lim_m)); out["mobile"] = (f"{name}-m.webp", m.size)
    return out


def hero_markup(files: dict, focus: str) -> str:
    w, h = files["jpg"][1]
    return (
        '<picture data-slot="hero">\n'
        f'    <source type="image/webp" media="(max-width: 767px)" srcset="assets/home/{files["mobile"][0]}">\n'
        f'    <source type="image/webp" srcset="assets/home/{files["webp"][0]}">\n'
        f'    <img src="assets/home/{files["jpg"][0]}" alt="" width="{w}" height="{h}" fetchpriority="high" decoding="async" class="absolute inset-0 w-full h-full object-cover" style="object-position: {focus}">\n'
        "  </picture>"
    )


def find_markup(files: dict, focus: str, alt: str) -> str:
    w, h = files["jpg"][1]
    return (
        '<picture data-slot="find">\n'
        f'      <source type="image/webp" srcset="assets/home/{files["webp"][0]}">\n'
        f'      <img src="assets/home/{files["jpg"][0]}" alt="{alt}" width="{w}" height="{h}" loading="lazy" decoding="async" class="w-full h-full object-cover" style="object-position: {focus}">\n'
        "    </picture>"
    )


def replace_slot(html: str, slot: str, markup: str, legacy_src: str) -> str:
    pat = re.compile(r'<picture data-slot="%s">.*?</picture>' % slot, re.S)
    if pat.search(html):
        return pat.sub(lambda m: markup, html, count=1)
    legacy = re.compile(r'<img src="assets/home/%s"[^>]*>' % re.escape(legacy_src))
    n = len(legacy.findall(html))
    assert n >= 1, f"index.html 에서 {slot} 자리(<img src=assets/home/{legacy_src}>)를 못 찾음"
    return legacy.sub(lambda m: markup, html, count=1)


def replace_preload(html: str, files: dict) -> str:
    links = (
        f'<link rel="preload" as="image" href="assets/home/{files["mobile"][0]}" media="(max-width: 767px)" fetchpriority="high">\n'
        f'<link rel="preload" as="image" href="assets/home/{files["webp"][0]}" media="(min-width: 768px)" fetchpriority="high">\n'
    )
    html, n = re.subn(r'(<link rel="preload"[^>]*assets/home/[^>]*>\n)+', links, html, count=1)
    assert n == 1, "preload 링크를 못 찾음"
    return html


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--slot", choices=SLOTS, required=True)
    ap.add_argument("--focus", default=None, help='object-position, 예: "65%% center"')
    ap.add_argument("--alt", default="끗 한의원 원장")
    a = ap.parse_args()
    files = save_variants(Path(a.src), a.slot)
    raw = INDEX.read_bytes()
    html = raw.decode("utf-8")
    if a.slot == "hero":
        html = replace_slot(html, "hero", hero_markup(files, a.focus or "70% center"), "kkeut-left.jpg")
        html = replace_preload(html, files)
    else:
        html = replace_slot(html, "find", find_markup(files, a.focus or "center 30%", a.alt), "kkeut-right.jpg")
    if html.encode("utf-8") != raw:
        INDEX.write_bytes(html.encode("utf-8"))
    for k, (fn, size) in files.items():
        print(f"{k}: {fn} {size[0]}x{size[1]} {(HOME / fn).stat().st_size // 1024}KB")
    print(f"index.html: {a.slot} 자리 갱신")
    return 0


if __name__ == "__main__":
    sys.exit(main())
