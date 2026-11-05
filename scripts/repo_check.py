"""커밋 전 점검: 올리면 안 되는 파일·내용이 추적/스테이징에 섞였는지 본다.

  python -X utf8 -I scripts/repo_check.py        # 추적 파일 + 스테이징 전부 검사, 걸리면 종료 코드 1

경로 규칙(금지): data/kkeut/, captures/, data/admon/extract/, 루트의 xlsx·pdf·zip·gif·docx·pptx·ai, 매출·환자·계약 이 든 파일명, .serve.log
내용 규칙(금지): 깃허브·OpenAI·AWS 토큰 모양, 'password=' 류 실제 값
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH_RULES = [
    ("환자 정보 폴더", r"^data/kkeut/"),
    ("경쟁 의원 캡처", r"^captures/"),
    ("모니터링 추출 원자료", r"^data/admon/extract/|^data/admon/master-|^data/admon/diff-"),
    ("민감 파일명", r"매출|환자|계약|세무|견적|리뷰"),
    ("금지 확장자", r"\.(xlsx|xls|pdf|zip|gif|mp4|webm|ai|psd|docx|pptx|log)$"),
    ("파이썬 캐시", r"__pycache__/"),
]
CONTENT_RULES = [
    ("깃허브 토큰", r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    ("OpenAI 류 키", r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    ("AWS 키", r"\bAKIA[0-9A-Z]{16}\b"),
    ("비밀값 대입", r"(?i)(password|passwd|secret|api_key)\s*[=:]\s*['\"][^'\"\n]{6,}['\"]"),
]
SELF = "scripts/repo_check.py"  # 규칙 문자열 자체가 걸리지 않게 자기 자신은 내용 검사에서 뺀다
TEXT_EXT = {".html", ".css", ".js", ".py", ".json", ".md", ".csv", ".svg", ".xml", ".txt", ".sh"}


def git_files() -> list[str]:
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    return [f for f in out.decode("utf-8").split("\0") if f]


def main() -> int:
    files = git_files()
    bad: list[str] = []
    for f in files:
        for name, pat in PATH_RULES:
            if re.search(pat, f):
                bad.append(f"[{name}] {f}")
        p = ROOT / f
        if f != SELF and p.suffix.lower() in TEXT_EXT and p.exists() and p.stat().st_size < 5_000_000:
            try:
                t = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for name, pat in CONTENT_RULES:
                m = re.search(pat, t)
                if m:
                    bad.append(f"[{name}] {f}: …{m.group(0)[:12]}…")
    total = sum((ROOT / f).stat().st_size for f in files if (ROOT / f).exists())
    print(f"검사한 파일 {len(files)}개, 합계 {total / 1_000_000:.1f}MB")
    if bad:
        print("올리면 안 되는 것:")
        print("\n".join("  " + b for b in bad))
        return 1
    print("통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
