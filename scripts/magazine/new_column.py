"""매거진 초안 변환기: drafts/magazine/src/<slug>.md → drafts/magazine/column-<slug>.html + entries.json

  python -X utf8 -I scripts/magazine/new_column.py            # src 전부 변환
  python -X utf8 -I scripts/magazine/new_column.py <slug>...  # 지정한 것만

원고 형식(마크다운 일부만):
  ---
  title: 제목
  category: guide            (concern | guide | care | first-visit | note)
  concerns: pigment, dry     (고민 태그 slug, 0~2개)
  treatments: toning.html    (시술 파일명, 0~2개)
  related: toning.html|토닝·색소 시술 보기   (하단 버튼, 생략하면 index.html#menu|시술메뉴 보기)
  date: 2026. 11.
  summary: 목록에 보일 요약(60~110자)
  seotitle: (선택) <title>; 생략하면 "제목 | 홍대 끗 한의원 원장 칼럼"
  seodesc:  (선택) description; 생략하면 summary + 꼬리말
  ---
  ## 소제목
  문단. 빈 줄로 구분. [글](링크) 와 **굵게** 만 지원.

템플릿은 사이트의 column-jemo-shaving.html(그때그때 읽음) → 공통 블록이 사이트와 같다.
"""
from __future__ import annotations

import json
import re
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build as B  # noqa: E402

ROOT = B.ROOT
SRC = ROOT / "drafts" / "magazine" / "src"
OUT = ROOT / "drafts" / "magazine"
TEMPLATE = B.SITE / "column-jemo-shaving.html"
TAIL = " 홍대 끗 한의원 원장 칼럼. 홍대·합정·신촌 피부 시술, 끗 한의원."


def parse(md: str) -> tuple[dict, str]:
    m = re.match(r"---\n(.*?)\n---\n(.*)$", md, re.S)
    assert m, "머리말(---) 없음"
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    for k in ("title", "category", "date", "summary"):
        assert meta.get(k), f"머리말 {k} 없음"
    meta["concerns"] = [x.strip() for x in meta.get("concerns", "").split(",") if x.strip()]
    meta["treatments"] = [x.strip() for x in meta.get("treatments", "").split(",") if x.strip()]
    return meta, m.group(2).strip()


def inline(t: str) -> str:
    t = escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2" class="underline">\1</a>', t)
    return t


def body_html(body: str) -> str:
    out = []
    for block in re.split(r"\n\s*\n", body):
        block = block.strip()
        if not block:
            continue
        if block.startswith("## "):
            out.append(f'<h2 class="kr text-[21px] font-bold !mt-10">{inline(block[3:])}</h2>')
        elif block.startswith("- "):
            items = "".join(f"<li>{inline(ln[2:].strip())}</li>" for ln in block.splitlines() if ln.startswith("- "))
            out.append(f'<ul class="list-disc pl-5 space-y-1.5">{items}</ul>')
        else:
            out.append("<p>" + inline(block).replace("\n", "<br>") + "</p>")
    return "\n".join(out)


def _sub1(text: str, pattern: str, repl, what: str) -> str:
    text, n = re.subn(pattern, repl if callable(repl) else (lambda m: repl), text, count=1, flags=re.S)
    assert n == 1, f"템플릿에서 {what} 을 못 찾음({n}개)"
    return text


def render(slug: str, meta: dict, body: str, d: dict, template: str) -> str:
    assert meta["category"] in d["_cats"], f"{slug}: 모르는 카테고리"
    for c in meta["concerns"]:
        assert c in d["_cons"], f"{slug}: 모르는 고민 태그 {c}"
    for t in meta["treatments"]:
        assert t in d["_trts"], f"{slug}: 모르는 시술 {t}"
    file = f"column-{slug}.html"
    url = f"{B.BASE_URL}/{file}"
    seotitle = meta.get("seotitle") or f'{meta["title"]} | 홍대 끗 한의원 원장 칼럼'
    seodesc = meta.get("seodesc") or (meta["summary"] + TAIL)
    rel_href, _, rel_name = (meta.get("related") or "index.html#menu|시술메뉴 보기").partition("|")
    post = {"slug": slug, **{k: meta[k] for k in ("title", "category", "concerns", "treatments", "date", "summary")}}

    t = template
    t = _sub1(t, r"<title>.*?</title>", f"<title>{escape(seotitle)}</title>", "title")
    t = _sub1(t, r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{escape(seodesc, quote=True)}">', "description")
    t = _sub1(t, r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">', "canonical")
    t = _sub1(t, r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{escape(seotitle, quote=True)}">', "og:title")
    t = _sub1(t, r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{escape(seodesc, quote=True)}">', "og:description")
    t = _sub1(t, r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">', "og:url")
    t = _sub1(t, r"<!-- mg:cat -->\n.*?<!-- /mg:cat -->", f"<!-- mg:cat -->\n{B.frag_cat(d, post)}\n<!-- /mg:cat -->", "mg:cat")
    t = _sub1(t, r"<h1([^>]*)>.*?</h1>", lambda m: f'<h1{m.group(1)}>{escape(meta["title"])}</h1>', "h1")
    t = _sub1(t, r"<!-- mg:byline -->\n.*?<!-- /mg:byline -->", f"<!-- mg:byline -->\n{B.frag_byline(d, post)}\n<!-- /mg:byline -->", "mg:byline")
    t = _sub1(t, r'(<div class="kr mt-9 space-y-5 text-\[15\.5px\] leading-\[1\.95\] text-black/80">).*?(</div>\n  <div class="mt-12 flex flex-wrap gap-3">)',
              lambda m: m.group(1) + "\n" + body_html(body) + "\n  " + m.group(2), "본문")
    t = _sub1(t, r'<a href="[^"]*" class="rounded-xl bg-\[#1a1a1a\][^>]*>[^<]*</a>',
              lambda m: re.sub(r'href="[^"]*"', f'href="{rel_href}"', re.sub(r">[^<]*</a>$", f">{escape(rel_name)}</a>", m.group(0))), "관련 시술 버튼")
    t = _sub1(t, r"<!-- mg:next -->\n.*?<!-- /mg:next -->", "<!-- mg:next -->\n<!-- /mg:next -->", "mg:next")
    return t


def main(argv: list[str]) -> int:
    d = B.load()
    template = TEMPLATE.read_bytes().decode("utf-8").replace("\r\n", "\n")
    assert "\r\n" not in template
    files = sorted(SRC.glob("*.md"))
    if argv:
        files = [SRC / f"{s}.md" for s in argv]
    entries = []
    for f in files:
        slug = f.stem
        meta, body = parse(f.read_text(encoding="utf-8"))
        html = render(slug, meta, body, d, template)
        (OUT / f"column-{slug}.html").write_bytes(html.encode("utf-8"))
        entries.append({"slug": slug, **{k: meta[k] for k in ("title", "category", "concerns", "treatments", "date", "summary")}})
        text = re.sub(r"<[^>]+>", "", body_html(body))
        chars = len(re.sub(r"\s", "", text))
        h2 = len(re.findall(r"^## ", body, re.M))
        links = ("index.html#booking" in body, any(t in body for t in meta["treatments"]) if meta["treatments"] else None)
        print(f"{slug}: 본문 {chars}자(공백 제외), h2 {h2}개, 예약 링크 {links[0]}, 시술 링크 {links[1]}, 개인차 문장 {'개인차' in body}")
    if not argv:
        (OUT / "entries.json").write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"entries.json: {len(entries)}편")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
