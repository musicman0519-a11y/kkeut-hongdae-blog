"""끗 매거진 목록 생성기.

data/magazine/posts.json 을 읽어 사이트 HTML 안의 표시 영역
<!-- mg:이름 --> … <!-- /mg:이름 --> 만 다시 쓴다. 마커 밖은 건드리지 않는다.

  python -X utf8 -I scripts/magazine/build.py          # 생성·저장
  python -X utf8 -I scripts/magazine/build.py --check  # 바뀔 파일만 보고(저장 안 함), 바뀌면 종료 코드 1

규칙: 파일별 줄바꿈(LF/CRLF) 보존, 두 번 돌려도 결과 같음, 마커 쌍이 정확히 1개가 아니면 그 파일은 건너뛰고 종료 코드 1.
생성 마크업은 브랜드 색 클래스(brandorange/rose)를 쓰지 않는다 — 테마 치환과 독립이어야 하므로.
"""
from __future__ import annotations

import json
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "kkeut_seo_site"
DATA = ROOT / "data" / "magazine" / "posts.json"


# ---------- 데이터 ----------
def load() -> dict:
    d = json.loads(DATA.read_text(encoding="utf-8"))
    cats = {c["slug"]: c for c in d["categories"]}
    cons = {c["slug"]: c for c in d["concerns"]}
    trts = {t["file"]: t for t in d["treatments"]}
    seen = set()
    for p in d["posts"]:
        assert p["slug"] not in seen, f"slug 중복: {p['slug']}"
        seen.add(p["slug"])
        assert p["category"] in cats, f"{p['slug']}: 모르는 카테고리 {p['category']}"
        for c in p.get("concerns", []):
            assert c in cons, f"{p['slug']}: 모르는 고민 태그 {c}"
        for t in p.get("treatments", []):
            assert t in trts, f"{p['slug']}: 모르는 시술 {t}"
        assert (SITE / f"column-{p['slug']}.html").exists(), f"{p['slug']}: 칼럼 파일 없음"
    d["_cats"], d["_cons"], d["_trts"] = cats, cons, trts
    # 최신 순(날짜 문자열 내림차순, 같으면 JSON 순서)
    d["_posts"] = sorted(d["posts"], key=lambda p: p["date"], reverse=True)
    return d


# ---------- 조각 ----------
TAB_ON = "rounded-full bg-black text-white px-4 py-1.5"
TAB_OFF = "rounded-full border border-black/15 px-4 py-1.5 hover:border-black ease-rt"
CHIP = "inline-block rounded-full border border-black/15 px-2.5 py-0.5 text-[11.5px] text-black/60"


def cats_with_posts(d: dict) -> list[dict]:
    """글이 1편 이상인 카테고리만, JSON 순서대로."""
    have = {p["category"] for p in d["_posts"]}
    return [c for c in d["categories"] if c["slug"] in have]


def chips(d: dict, p: dict) -> str:
    names = [d["_cons"][c]["name"] for c in p.get("concerns", [])]
    if not names:
        return ""
    spans = "".join(f'<span class="{CHIP}">{escape(n)}</span>' for n in names)
    return f'        <p class="mt-2 flex flex-wrap gap-1.5">{spans}</p>\n'


def list_item(d: dict, p: dict) -> str:
    cat = d["_cats"][p["category"]]
    tags = " ".join(p.get("concerns", []))
    lines = [
        f'      <li class="py-7" data-tags="{tags}"><a href="column-{p["slug"]}.html" class="group block">',
        f'        <p class="text-[12px] text-black/55 font-semibold">{escape(cat["name"])}</p>',
        f'        <h3 class="kr mt-1 text-[20px] font-bold group-hover:underline ease-rt">{escape(p["title"])}</h3>',
        f'        <p class="kr mt-2 text-[14px] text-black/55 leading-relaxed">{escape(p["summary"])}</p>',
    ]
    c = chips(d, p)
    if c:
        lines.append(c.rstrip("\n"))
    lines.append(f'        <p class="mt-2 text-[12px] text-black/35">{escape(p["date"])} · {escape(cat["name"])}</p>')
    lines.append("      </a></li>")
    return "\n".join(lines)


def frag_tabs(d: dict, current: str = "") -> str:
    """카테고리 탭. current 는 활성 탭 slug(매거진 홈은 '')."""
    tabs = [("", "전체", "columns.html")] + [(c["slug"], c["name"], c["file"]) for c in cats_with_posts(d)]
    out = []
    for s, n, f in tabs:
        on = s == current
        cls = TAB_ON if on else TAB_OFF
        cur = ' aria-current="page"' if on else ""
        out.append(f'    <a href="{f}" class="{cls}"{cur}>{escape(n)}</a>')
    return "\n".join(out)


def frag_list(d: dict) -> str:
    return "\n".join(list_item(d, p) for p in d["_posts"])


CHIP_OFF = "rounded-full border border-black/15 px-3 py-1 text-black/60 hover:border-black ease-rt"


def frag_chips(d: dict) -> str:
    """고민 태그 칩 8개 + 전체. 거르기는 페이지의 인라인 JS(해시 #tag=slug)가 한다."""
    out = [f'    <a href="#" data-tag="" class="{CHIP_OFF}">전체</a>']
    out += [f'    <a href="#tag={c["slug"]}" data-tag="{c["slug"]}" class="{CHIP_OFF}">{escape(c["name"])}</a>' for c in d["concerns"]]
    return "\n".join(out)


def frag_urls(d: dict) -> str:
    """sitemap: 글 있는 허브 + 칼럼 전부."""
    files = [c["file"] for c in cats_with_posts(d)] + [f"column-{p['slug']}.html" for p in d["_posts"]]
    return "\n".join(f"  <url><loc>{BASE_URL}/{f}</loc></url>" for f in files)


# ---------- 허브 페이지(파일 전체 생성) ----------
BASE_URL = "https://hongdaekkeutclinic.com"
EMPTY_NOTE = (
    '      <li class="py-12 text-center text-[14px] text-black/45 kr">준비 중인 카테고리입니다. '
    '<a href="columns.html" class="underline">전체 글 보기</a></li>'
)


def _sub1(text: str, pattern: str, repl: str, what: str) -> str:
    text, n = re.subn(pattern, lambda m: repl, text, count=1, flags=re.S)
    assert n == 1, f"허브 템플릿(columns.html)에서 {what} 을 못 찾음"
    return text


def hub_html(d: dict, cat: dict, template: str) -> str:
    """columns.html(렌더된 것)을 템플릿 삼아 카테고리 허브 한 쪽을 만든다."""
    posts = [p for p in d["_posts"] if p["category"] == cat["slug"]]
    title = f'{cat["name"]} | 끗 매거진 — 홍대 끗 한의원'
    desc = f'{cat["desc"]}. 홍대 끗 한의원 원장이 직접 씁니다. 홍대·합정·신촌 피부 시술, 끗 한의원.'
    url = f'{BASE_URL}/{cat["file"]}'
    t = template
    t = _sub1(t, r"<title>.*?</title>", f"<title>{escape(title)}</title>", "title")
    t = _sub1(t, r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{escape(desc, quote=True)}">', "description")
    t = _sub1(t, r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">', "canonical")
    t = _sub1(t, r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{escape(title, quote=True)}">', "og:title")
    t = _sub1(t, r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{escape(desc, quote=True)}">', "og:description")
    crumbs = json.dumps({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "끗 매거진", "item": f"{BASE_URL}/columns.html"},
            {"@type": "ListItem", "position": 2, "name": cat["name"], "item": url},
        ]}, ensure_ascii=False)
    extra = f'<script type="application/ld+json">{crumbs}</script>'
    if not posts:
        extra = '<meta name="robots" content="noindex">\n' + extra
    t = _sub1(t, r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">\n{extra}', "og:url")
    t = _sub1(t, r'<p class="text-\[12px\] tracking-\[0\.2em\] text-black/45">KKEUT MAGAZINE</p>',
              f'<p class="text-[12px] tracking-[0.2em] text-black/45">{escape(cat["en"])}</p>', "영문 라벨")
    t, n = re.subn(r"<h1([^>]*)>끗 매거진</h1>", lambda m: f'<h1{m.group(1)}>{escape(cat["name"])}</h1>', t, count=1)
    assert n == 1, "허브 템플릿(columns.html)에서 h1 을 못 찾음"
    t = _sub1(t, r'<p class="kr text-\[13px\] text-black/45 pb-1 text-right">[^<]*</p>',
              f'<p class="kr text-[13px] text-black/45 pb-1 text-right">{escape(cat["desc"])}</p>', "부제")
    tabs, lst = frag_tabs(d, cat["slug"]), ("\n".join(list_item(d, p) for p in posts) or EMPTY_NOTE)
    t = _sub1(t, r"<!-- mg:tabs -->\n.*?<!-- /mg:tabs -->", f"<!-- mg:tabs -->\n{tabs}\n<!-- /mg:tabs -->", "mg:tabs")
    t = _sub1(t, r"<!-- mg:list -->\n.*?<!-- /mg:list -->", f"<!-- mg:list -->\n{lst}\n<!-- /mg:list -->", "mg:list")
    return t


def write_hubs(d: dict, write: bool) -> list[Path]:
    """허브 5쪽을 (다시) 쓴다. 돌려줌: 바뀐 파일."""
    template = (SITE / "columns.html").read_bytes().decode("utf-8").replace("\r\n", "\n")
    changed = []
    for cat in d["categories"]:
        path = SITE / cat["file"]
        out = hub_html(d, cat, template).encode("utf-8")
        if not path.exists() or path.read_bytes() != out:
            changed.append(path)
            if write:
                path.write_bytes(out)
    return changed


# ---------- 칼럼 한 쪽: 상단 메타 + 다음에 읽을 글 ----------
def frag_cat(d: dict, p: dict) -> str:
    cat = d["_cats"][p["category"]]
    return (f'  <p class="text-[13px] font-semibold text-black/55"><a href="columns.html" class="hover:underline">끗 매거진</a>'
            f' · <a href="{cat["file"]}" class="hover:underline">{escape(cat["name"])}</a></p>')


def frag_byline(d: dict, p: dict) -> str:
    out = [f'  <p class="mt-3 text-[13px] text-black/40">{escape(p["date"])} · {escape(d["author"])} · 의료인 작성</p>']
    cons = p.get("concerns", [])
    if cons:
        spans = "".join(f'<a href="columns.html#tag={c}" class="{CHIP}">{escape(d["_cons"][c]["name"])}</a>' for c in cons)
        out.append(f'  <p class="mt-3 flex flex-wrap gap-1.5">{spans}</p>')
    return "\n".join(out)


def next_posts(d: dict, p: dict, n: int = 3) -> list[dict]:
    """같은 카테고리 → 고민 태그가 겹치는 글 → 그 외 최신 순. 자기 자신 제외."""
    others = [q for q in d["_posts"] if q["slug"] != p["slug"]]
    mine = set(p.get("concerns", []))
    rank = lambda q: (q["category"] != p["category"], not (mine & set(q.get("concerns", []))))
    return sorted(others, key=rank)[:n]


def compact_item(d: dict, q: dict) -> str:
    cat = d["_cats"][q["category"]]
    return (f'      <li class="py-4"><a href="column-{q["slug"]}.html" class="group block">'
            f'<p class="text-[12px] text-black/45">{escape(cat["name"])}</p>'
            f'<p class="kr mt-0.5 text-[16px] font-bold group-hover:underline">{escape(q["title"])}</p></a></li>')


def frag_next(d: dict, p: dict) -> str:
    qs = next_posts(d, p)
    if not qs:
        return ""
    return ('  <div class="mt-14 border-t border-black/10 pt-8">\n'
            '    <p class="text-[12px] tracking-[0.2em] text-black/45">NEXT READ</p>\n'
            '    <ul class="mt-2 divide-y divide-black/10">\n' + "\n".join(compact_item(d, q) for q in qs) + "\n    </ul>\n  </div>")


# ---------- 시술 페이지: 관련 칼럼 ----------
def frag_related(d: dict, file: str, n: int = 3) -> str:
    qs = [p for p in d["_posts"] if file in p.get("treatments", [])][:n]
    if not qs:
        return ""
    return ('<section id="related" class="max-w-[1400px] mx-auto px-4 pb-20">\n'
            '  <div class="max-w-[900px]">\n'
            '    <div class="flex items-end justify-between border-b-2 border-black pb-3">\n'
            '      <h2 class="text-[22px] font-bold tracking-tight">관련 칼럼</h2>\n'
            '      <a href="columns.html" class="text-[13px] font-semibold hover:underline pb-1">끗 매거진</a>\n'
            '    </div>\n'
            '    <ul class="divide-y divide-black/10">\n' + "\n".join(compact_item(d, q) for q in qs) + "\n    </ul>\n  </div>\n</section>")


# ---------- index 표지 ----------
def featured(d: dict) -> list[dict]:
    fs = [p for p in d["_posts"] if p.get("featured")]
    return sorted(fs, key=lambda p: p["featured"])[:2]


def cover_card(d: dict, p: dict, big: bool) -> str:
    cat = d["_cats"][p["category"]]
    t = "text-[24px] md:text-[28px]" if big else "text-[19px]"
    return (f'      <a href="column-{p["slug"]}.html" class="group block rounded-lg bg-black/[0.03] p-6 md:p-8">\n'
            f'        <p class="text-[12px] text-black/55 font-semibold">{escape(cat["name"])}</p>\n'
            f'        <h3 class="kr mt-2 {t} font-bold leading-snug group-hover:underline">{escape(p["title"])}</h3>\n'
            f'        <p class="kr mt-3 text-[14px] text-black/55 leading-relaxed">{escape(p["summary"])}</p>\n'
            f'        <p class="mt-4 text-[12px] text-black/35">{escape(p["date"])}</p>\n'
            f'      </a>')


def frag_cover(d: dict) -> str:
    fs = featured(d)
    if not fs:
        return ""
    cards = [cover_card(d, p, i == 0) for i, p in enumerate(fs)]
    out = ['    <div class="mt-6 grid gap-4 md:grid-cols-5">', '      <div class="md:col-span-3">', cards[0], "      </div>"]
    if len(cards) > 1:
        out += ['      <div class="md:col-span-2">', cards[1], "      </div>"]
    out.append("    </div>")
    return "\n".join(out)


def frag_latest(d: dict, n: int = 6) -> str:
    """표지에 이미 실린 글은 뺀 최신 글. 없으면 영역 숨김."""
    skip = {p["slug"] for p in featured(d)}
    qs = [p for p in d["_posts"] if p["slug"] not in skip][:n]
    if not qs:
        return ""
    return ('    <div class="mt-10 flex items-end justify-between border-b border-black/20 pb-2">\n'
            '      <h3 class="text-[17px] font-bold">최신 글</h3>\n    </div>\n'
            '    <ul class="divide-y divide-black/10">\n' + "\n".join(compact_item(d, q) for q in qs) + "\n    </ul>")


def frag_first(d: dict, n: int = 3) -> str:
    qs = [p for p in d["_posts"] if p["category"] == "first-visit"][:n]
    if not qs:
        return ""
    return ('    <div class="mt-10 rounded-lg border border-black/10 p-6">\n'
            '      <p class="text-[12px] tracking-[0.2em] text-black/45">FIRST VISIT</p>\n'
            '      <h3 class="mt-1 text-[17px] font-bold">처음 방문하신다면</h3>\n'
            '      <ul class="mt-2 divide-y divide-black/10">\n' + "\n".join(compact_item(d, q) for q in qs) + "\n      </ul>\n    </div>")


# ---------- 헤더 드롭다운 ----------
NAV_ITEM = "block px-4 py-2 hover:bg-black/5"


def frag_nav(d: dict) -> str:
    out = [f'            <a href="columns.html" class="{NAV_ITEM}">전체 글</a>']
    out += [f'            <a href="{c["file"]}" class="{NAV_ITEM}">{escape(c["name"])}</a>' for c in cats_with_posts(d)]
    return "\n".join(out)


# 파일 → {마커 이름: 조각 생성 함수}
def targets(d: dict) -> dict[Path, dict[str, str]]:
    t = {
        SITE / "columns.html": {"tabs": frag_tabs(d), "chips": frag_chips(d), "list": frag_list(d)},
        SITE / "sitemap.xml": {"urls": frag_urls(d)},
        SITE / "index.html": {"cover": frag_cover(d), "latest": frag_latest(d), "first": frag_first(d), "nav": frag_nav(d)},
        ROOT / "scripts" / "theme" / "header.html": {"nav": frag_nav(d)},
    }
    for p in d["_posts"]:
        t[SITE / f"column-{p['slug']}.html"] = {"cat": frag_cat(d, p), "byline": frag_byline(d, p), "next": frag_next(d, p)}
    for tr in d["treatments"]:
        t[SITE / tr["file"]] = {"related": frag_related(d, tr["file"])}
    return t


# ---------- 적용 ----------
MARK = "<!-- mg:{name} -->"
ENDMARK = "<!-- /mg:{name} -->"


def apply(path: Path, frags: dict[str, str], write: bool) -> tuple[bool, list[str]]:
    """돌려줌: (바뀌는가, 오류 목록)."""
    raw = path.read_bytes()
    crlf = b"\r\n" in raw
    text = raw.decode("utf-8").replace("\r\n", "\n")
    errors = []
    for name, frag in frags.items():
        a, b = MARK.format(name=name), ENDMARK.format(name=name)
        pat = re.compile(re.escape(a) + r"\n(?:.*?\n)?[ \t]*" + re.escape(b), re.S)
        n = len(pat.findall(text))
        if n != 1:
            errors.append(f"{path.name}: 마커 mg:{name} 이 {n}개 (1개여야 함)")
            continue
        body = f"{a}\n{frag}\n{b}" if frag else f"{a}\n{b}"
        text = pat.sub(lambda m: body, text, count=1)
    if errors:
        return False, errors
    out = text.replace("\n", "\r\n").encode("utf-8") if crlf else text.encode("utf-8")
    changed = out != raw
    if changed and write:
        path.write_bytes(out)
    return changed, []


DRAFTS = ROOT / "drafts" / "magazine"


def publish(slug: str, on: bool) -> None:
    """초안을 사이트에 넣거나(on) 뺀다(off). posts.json 과 파일만 다루고, 생성은 main 이 이어서 한다."""
    data = json.loads(DATA.read_text(encoding="utf-8"))
    posts = [p for p in data["posts"] if p["slug"] != slug]
    target = SITE / f"column-{slug}.html"
    if on:
        src = DRAFTS / f"column-{slug}.html"
        entries = json.loads((DRAFTS / "entries.json").read_text(encoding="utf-8"))
        entry = next((e for e in entries if e["slug"] == slug), None)
        assert src.exists() and entry, f"초안 없음: {slug} (new_column.py 를 먼저)"
        target.write_bytes(src.read_bytes())
        posts.insert(0, entry)
        print(f"publish: {target.name} 복사, posts.json 맨 위에 추가")
    else:
        target.unlink(missing_ok=True)
        print(f"unpublish: {target.name} 삭제, posts.json 에서 제거")
    data["posts"] = posts
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    check = "--check" in argv
    for flag, on in (("--publish", True), ("--unpublish", False)):
        if flag in argv:
            for slug in argv[argv.index(flag) + 1:]:
                if slug.startswith("--"):
                    break
                publish(slug, on)
    d = load()
    rc = 0
    for path, frags in targets(d).items():
        if not path.exists():
            print(f"없음: {path.name}")
            rc = 1
            continue
        changed, errs = apply(path, frags, write=not check)
        for e in errs:
            print("오류:", e)
            rc = 1
        if changed:
            print(("바뀜(저장 안 함): " if check else "저장: ") + path.name)
            if check:
                rc = 1
    for path in write_hubs(d, write=not check):
        print(("바뀜(저장 안 함): " if check else "저장: ") + path.name)
        if check:
            rc = 1
    n_hub = len(d["categories"])
    print(f"글 {len(d['_posts'])}편, 대상 파일 {len(targets(d))}개 + 허브 {n_hub}쪽" + (" — 변경 없음" if rc == 0 and check else ""))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
