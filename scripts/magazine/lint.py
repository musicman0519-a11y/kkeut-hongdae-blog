"""의료광고 금지 표현 검사 (docs/magazine-editorial.md "쓰지 않는 표현" 과 같은 목록).

  python -X utf8 -I scripts/magazine/lint.py            # drafts/magazine/column-*.html + kkeut_seo_site/column-*.html
  python -X utf8 -I scripts/magazine/lint.py <파일>...   # 지정 파일만

본문(<div class="kr mt-9 …"> 안)과 제목·요약(title·description)만 검사한다. 걸리면 종료 코드 1.
단어 검사일 뿐이다 — 효과를 단정하는 문장은 사람이(감수에서) 본다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES = [
    ("치료경험담·후기", r"후기|체험담|경험담|만족하셨|만족했다"),
    ("전후 사진", r"전후\s*사진|비포|애프터|before\s*/?\s*after"),
    ("절대·비교 표현", r"최고|최초|최상|1\s*위|유일|완치|완벽|압도적|타\s*의원|다른\s*병원보다"),
    ("부작용 없음·보장", r"부작용\s*(이|은)?\s*없|100\s*%|보장|확실한\s*효과|반드시\s*좋아"),
    ("가격 숫자", r"[0-9][0-9,]*\s*(만\s*)?원(?!장|인|리|칙|료|고|래|심)"),
]


def text_of(html: str) -> str:
    parts = []
    for pat in (r"<title>(.*?)</title>", r'name="description" content="([^"]*)"', r'<div class="kr mt-9 space-y-5[^>]*>(.*?)</div>\n  <div class="mt-12'):
        m = re.search(pat, html, re.S)
        if m:
            parts.append(re.sub(r"<[^>]+>", " ", m.group(1)))
    return "\n".join(parts)


def main(argv: list[str]) -> int:
    files = [Path(a) for a in argv] or sorted((ROOT / "drafts" / "magazine").glob("column-*.html")) + sorted((ROOT / "kkeut_seo_site").glob("column-*.html"))
    total = 0
    for f in files:
        t = text_of(f.read_bytes().decode("utf-8"))
        hits = []
        for name, pat in RULES:
            for m in re.finditer(pat, t, re.I):
                s = max(0, m.start() - 15)
                hits.append(f"  [{name}] …{t[s:m.end() + 15].strip()}…")
        total += len(hits)
        print(f"{f.name}: {len(hits)}건" + ("\n" + "\n".join(hits) if hits else ""))
    print(f"합계 {total}건 / {len(files)}편")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
