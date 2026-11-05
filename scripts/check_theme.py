#!/usr/bin/env python
"""UI 재단장 기준선 저장·검사.

사용법 (프로젝트 루트):
  python -X utf8 -I scripts/check_theme.py baseline            # data/theme-baseline.json 저장
  python -X utf8 -I scripts/check_theme.py check [추가.html ...] # 기준선과 비교, 공통 블록 일치 검사

검사 항목: 16페이지 title·description·canonical·og:url·h1·JSON-LD 불변, href 집합이 기준선을 포함,
공통 블록(head 공통부~</nav>, <footer>~끝, 떠 있는 버튼) md5 가 모든 페이지에서 같음, 옛 색 클래스 0개,
sitemap.xml·robots.txt 불변. 추가 html(어드민 발행 파일)도 공통 블록 md5 를 비교한다.
"""
import hashlib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "kkeut_seo_site"
BASE = ROOT / "data" / "theme-baseline.json"
OLD_COLORS = ["brandorange", "cardred", "cardblue", "cardteal", "cardnavy", "cardmagenta", "cardgreen", "kpink", "kpinksoft", "khot", "kyellow"]
VERIFY_FILE = re.compile(r"^(google|naver)[0-9a-f]+\.html$")  # 검색엔진 소유확인 파일은 페이지가 아님
HEAD_START = '<script src="https://cdn.tailwindcss.com">'


def read(p: Path) -> str:
    return p.read_bytes().decode("utf-8").replace("\r\n", "\n")


def md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:10]


def meta(html: str, name: str, attr: str = "name") -> str:
    m = re.search(r'<meta\s+%s="%s"\s+content="([^"]*)"' % (attr, re.escape(name)), html)
    return m.group(1) if m else ""


def text(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def common_blocks(html: str) -> dict:
    """공통 블록 3개의 md5. 페이지별 메타는 HEAD_START 앞에 있으므로 제외된다."""
    i = html.find(HEAD_START)
    j = html.find("</nav>", i)
    head = html[i:j + len("</nav>")] if i >= 0 and j >= 0 else ""
    k = html.find("<footer")
    foot = html[k:] if k >= 0 else ""
    return {"head_nav": md5(head), "footer_end": md5(foot)}


def page_info(p: Path) -> dict:
    h = read(p)
    hrefs = sorted(set(re.findall(r'href="([^"]*)"', h)))
    hrefs = [x for x in hrefs if not x.startswith(("https://cdn.", "https://fonts.", "https://code.iconify"))]
    jsonld = [re.sub(r"\s+", " ", m).strip() for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)]
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
    old = {c: len(re.findall(r"(?<!\w)%s(?!\w)" % c, h)) for c in OLD_COLORS}
    arb = sorted(set(re.findall(r"\[#[0-9a-fA-F]{3,8}\]", h)))
    return {
        "title": text(re.search(r"<title>(.*?)</title>", h, re.S).group(1)) if "<title>" in h else "",
        "description": meta(h, "description"),
        "canonical": (re.search(r'<link rel="canonical" href="([^"]*)"', h) or [None, ""])[1],
        "og_url": meta(h, "og:url", "property"),
        "h1": text(h1.group(1)) if h1 else "",
        "jsonld": jsonld,
        "hrefs": hrefs,
        "old_colors": {k: v for k, v in old.items() if v},
        "arbitrary_colors": arb,
        "blocks": common_blocks(h),
        "crlf": b"\r\n" in p.read_bytes(),
    }


def collect() -> dict:
    pages = {p.name: page_info(p) for p in sorted(SITE.glob("*.html")) if not VERIFY_FILE.match(p.name)}
    return {
        "pages": pages,
        "sitemap_md5": md5(read(SITE / "sitemap.xml")),
        "robots_md5": md5(read(SITE / "robots.txt")),
    }


def baseline():
    data = collect()
    BASE.parent.mkdir(parents=True, exist_ok=True)
    BASE.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    n = len(data["pages"])
    old = sum(sum(v["old_colors"].values()) for v in data["pages"].values())
    arb = sorted({c for v in data["pages"].values() for c in v["arbitrary_colors"]})
    print(f"기준선 저장: {BASE} (페이지 {n}, 옛 색 클래스 {old}개, 임의 색 {len(arb)}종)")
    print("임의 색:", " ".join(arb))


def check(extra: list[str]) -> int:
    base = json.loads(BASE.read_text(encoding="utf-8"))
    cur = collect()
    fails: list[str] = []
    ok: list[str] = []
    for name, b in base["pages"].items():
        c = cur["pages"].get(name)
        if not c:
            fails.append(f"{name}: 페이지 없음"); continue
        for key in ("title", "description", "canonical", "og_url", "h1", "jsonld"):
            if b[key] != c[key]:
                fails.append(f"{name}: {key} 변경됨")
        lost = sorted(set(b["hrefs"]) - set(c["hrefs"]))
        if lost:
            fails.append(f"{name}: 사라진 href {lost}")
        if c["old_colors"]:
            fails.append(f"{name}: 옛 색 클래스 남음 {c['old_colors']}")
        if b["crlf"] != c["crlf"]:
            fails.append(f"{name}: 줄바꿈 방식 바뀜")
    blocks = {}
    for name, c in cur["pages"].items():
        for k, v in c["blocks"].items():
            blocks.setdefault(k, {}).setdefault(v, []).append(name)
    for f in extra:
        for k, v in common_blocks(read(Path(f))).items():
            blocks.setdefault(k, {}).setdefault(v, []).append(f"(추가) {f}")
    for k, groups in blocks.items():
        if len(groups) == 1:
            ok.append(f"공통 블록 {k}: 전 페이지 일치")
        else:
            fails.append(f"공통 블록 {k} 불일치: " + " | ".join(f"{h}={len(v)}개({v[0]}…)" for h, v in groups.items()))
    for key in ("sitemap_md5", "robots_md5"):
        (ok if base[key] == cur[key] else fails).append(f"{key}: {'불변' if base[key] == cur[key] else '변경됨'}")
    if not any(c["old_colors"] for c in cur["pages"].values()):
        ok.append("옛 색 클래스: 0개")
    added = sorted({h for n, c in cur["pages"].items() for h in set(c["hrefs"]) - set(base["pages"].get(n, {}).get("hrefs", []))})
    for line in ok:
        print("OK  ", line)
    for line in fails:
        print("FAIL", line)
    if added:
        print("참고: 새로 추가된 href", added)
    print(f"결과: {'통과' if not fails else '실패 ' + str(len(fails)) + '건'}")
    return 0 if not fails else 1


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    if mode == "baseline":
        baseline()
    else:
        sys.exit(check(sys.argv[2:]))
