"""사이트 기준 도메인 바꾸기 (canonical·og:url·sitemap·robots·생성기·어드민 기본값).

  python -X utf8 -I scripts/set_domain.py https://hongdaekkeutclinic.com
  python -X utf8 -I scripts/set_domain.py --show        # 지금 어떤 도메인이 몇 군데 있는지

바꾼 뒤: scripts/magazine/new_column.py(초안 재생성) → scripts/magazine/build.py → check_theme.py baseline(canonical 변경은 의도된 것).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "kkeut_seo_site"
TARGETS = [*SITE.glob("*.html"), SITE / "sitemap.xml", SITE / "robots.txt",
           ROOT / "scripts" / "magazine" / "build.py", ROOT / "kkeut_admin.html"]
URL_RE = re.compile(r"https://(?:[a-z0-9-]+\.)+[a-z]{2,}(?=/|\"|'|\s|$)")


def current_domains() -> dict[str, int]:
    found: dict[str, int] = {}
    for p in TARGETS:
        t = p.read_bytes().decode("utf-8")
        for m in re.findall(r'(?:canonical" href|og:url" content|Sitemap: |<loc>|BASE_URL = |kkeut_site\'\) \|\| )["\']?(https://[^"\'<\s]+)', t):
            host = re.match(r"https://[^/]+", m).group(0)
            found[host] = found.get(host, 0) + 1
    return found


def main(argv: list[str]) -> int:
    if not argv or argv[0] == "--show":
        for k, v in current_domains().items():
            print(f"{k}: {v}곳")
        return 0
    new = argv[0].rstrip("/")
    assert re.fullmatch(r"https://[a-z0-9.-]+", new), "https://도메인 형식으로"
    olds = [h for h in current_domains() if h != new]
    if not olds:
        print("이미 그 도메인입니다")
        return 0
    n_files = 0
    for p in TARGETS:
        raw = p.read_bytes()
        t = raw.decode("utf-8")
        for old in olds:
            t = t.replace(old + "/", new + "/").replace(old + '"', new + '"').replace(old + "'", new + "'")
        if t.encode("utf-8") != raw:
            p.write_bytes(t.encode("utf-8"))
            n_files += 1
    print(f"{', '.join(olds)} → {new}: {n_files}개 파일 수정")
    print("다음: new_column.py → magazine/build.py → check_theme.py baseline")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
