# -*- coding: utf-8 -*-
"""추출 JSON → 마스터 행(10월판 열 구성) + 표준코드 매칭 + 전월(10월) 대비 신규/유지/변경 판정 + 판정 초안.
사용법:
  python -X utf8 -I scripts/admon/diff.py --extract data/admon/extract --prev "<10월.xlsx>" --out data/admon/master-2026-11.csv --summary data/admon/diff-2026-11.csv [--only 미소앤봄의원]
출력 master CSV 열: 병원, 채널·섹션, 상품명, 표준코드, 정가(원), 이벤트가(원), 할인율(%), 표시방식, 조건·비고, 위반 소지, 심각도, 캡처일, 출처, 전월 대비, 정황, 규칙
"""
import sys, os, re, json, csv, argparse, collections
sys.path.insert(0, os.path.dirname(__file__))
import judge as J

CODE_PATTERNS = [  # (표준코드, 정규식) — 구체적인 것 먼저
    ("BTX주름2부위", r"(주름|주름\s*보톡스|톡신).*2\s*부위"),
    ("BTX주름1부위", r"(주름|주름\s*보톡스|톡신).*1\s*부위"),
    ("사각턱BTX", r"(사각)?턱\s*(보톡스|톡신|BTX)|(보톡스|톡신).*사각턱"),
    ("BTX주름1부위", r"주름\s*(보톡스|톡신)(?!.*\d\s*부위)"),  # 부위 수 없는 주름보톡스는 1부위로 본다(10월 관례)
    ("리쥬란2cc", r"리쥬란.*2\s*cc"),
    ("리쥬란1cc", r"리쥬란.*1\s*cc"),
    ("슈링크100", r"슈링크.*\b100\s*샷"),
    ("슈링크300", r"슈링크.*\b300\s*샷"),
    ("울쎄라300", r"울쎄라.*\b300"),
    ("써마지300", r"써마지.*\b300"),
    ("인모드", r"인모드"),
    ("아쿠아필", r"아쿠아필"),
    ("온다", r"온다"),
    ("제모겨드랑이", r"겨드랑이.*제모|제모.*겨드랑이|겨드랑이\s*(1회|\d+회|\d+년권)"),
]

def code_of(name):
    if re.search(r"\+|or", str(name)):  # 묶음(A+B)·선택형은 표준코드 없음(10월 관례)
        return ""
    for code, pat in CODE_PATTERNS:
        if re.search(pat, name, re.I): return code
    return ""

def norm(name):
    s = str(name or "").lower()
    s = re.sub(r"\[[^\]]*\]|\([^)]*\)", " ", s)          # [국산], (팁별도) 제거
    s = re.sub(r"[^\w가-힣]+", "", s)                      # 기호·공백 제거
    return s

def num(v):
    if v is None: return None
    if isinstance(v, (int, float)): return int(v)
    s = str(v).replace(",", "").strip()
    return int(float(s)) if re.match(r"^\d+(\.\d+)?$", s) else None

def load_prev(xlsx):
    import openpyxl
    ws = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)["마스터 데이터"]
    it = ws.iter_rows(values_only=True); hdr = [str(h) for h in next(it)]
    rows = [dict(zip(hdr, r)) for r in it if r and r[0]]
    idx = collections.defaultdict(list)
    for r in rows:
        key = (str(r["병원"]).strip(), str(r.get("표준코드") or "").strip() or norm(r["상품명"]))
        idx[key].append(r)
    return rows, idx

def flatten(ex, rules):
    out = []
    for sec in ex.get("sections", []):
        for it in sec.get("items", []):
            lp, ep = it.get("list_price"), it.get("event_price")
            lp_v, ep_v = num(lp), num(ep)
            dpct = it.get("discount_pct")
            if dpct in (None, "") and lp_v and ep_v and lp_v > 0:
                dpct = None  # 표기된 할인율만 기록(계산하지 않음)
            cond = " · ".join(x for x in [sec.get("common_conditions", ""), it.get("conditions", ""), ("VAT " + it["vat"]) if it.get("vat") else ""] if x)
            row = {
                "병원": ex["clinic"], "채널·섹션": sec.get("section", ""), "상품명": it.get("name", ""),
                "표준코드": code_of(it.get("name", "")),
                "정가(원)": lp_v if lp_v is not None else (lp if lp else "미표기"),
                "이벤트가(원)": ep_v if ep_v is not None else (ep if ep else "확인필요"),
                "할인율(%)": dpct if dpct not in (None, "") else "-",
                "표시방식": it.get("display", ""), "조건·비고": cond,
                "캡처일": ex.get("captured_at", ""), "출처": sec.get("capture", ""),
            }
            j = J.judge(row, rules)
            flags = it.get("flags") or []
            row["위반 소지"] = "[초안] " + j["위반"]
            row["심각도"] = "[초안] " + j["심각도"]
            row["정황"] = "; ".join(j.get("정황", []) + [f for f in flags if f != "중복"])
            row["규칙"] = ",".join(j["규칙"])
            if "확인필요" in flags: row["정황"] = (row["정황"] + "; " if row["정황"] else "") + "확인필요(판독)"
            out.append(row)
    return out

UNIT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(kj|샷|cc|회|u|유닛|부위|분|줄|만줄|펄스|mm|병|바이알|v)", re.I)
def units_compatible(a, b):
    """용량·회차 토큰(10KJ, 300샷, 2cc…)이 둘 다 있고 서로 다르면 다른 상품."""
    ta = {(float(n), u.lower()) for n, u in UNIT_RE.findall(str(a))}
    tb = {(float(n), u.lower()) for n, u in UNIT_RE.findall(str(b))}
    if ta and tb and not (ta & tb): return False
    return True

def compare(rows, prev_idx):
    summary = collections.Counter()
    for r in rows:
        key = (r["병원"], r["표준코드"] or norm(r["상품명"]))
        cands = prev_idx.get(key) or []
        if not cands and r["표준코드"]:
            cands = prev_idx.get((r["병원"], norm(r["상품명"]))) or []
        cands = [c for c in cands if units_compatible(c["상품명"], r["상품명"])]
        if not cands:
            r["전월 대비"] = "신규"; summary[(r["병원"], "신규")] += 1; continue
        # 같은 코드가 여러 행이면 상품명이 가장 비슷한 것
        p = max(cands, key=lambda c: len(os.path.commonprefix([norm(c["상품명"]), norm(r["상품명"])])))
        ua, ub = set(UNIT_RE.findall(str(p["상품명"])) ), set(UNIT_RE.findall(str(r["상품명"])))
        if bool(ua) != bool(ub):  # 한쪽만 용량·회차가 있으면(시작가 '~' 표기 등) 가격 비교 불가
            r["전월 대비"] = f"비교불가(구성 상이 / 10월 {p['상품명']})"; summary[(r["병원"], "비교불가")] += 1; continue
        pe, pl = num(p.get("이벤트가(원)")), num(p.get("정가(원)"))
        ne, nl = num(r["이벤트가(원)"]), num(r["정가(원)"])
        changes = []
        if pe is not None and ne is not None and pe != ne: changes.append(f"이벤트가 {pe:,}→{ne:,}")
        if pl is not None and nl is not None and pl != nl: changes.append(f"정가 {pl:,}→{nl:,}")
        if (pl is None) != (nl is None): changes.append("정가 표기 " + ("추가" if nl is not None else "삭제"))
        r["전월 대비"] = ("변경(" + ", ".join(changes) + f" / 10월 {p['상품명']}" + ")") if changes else f"유지(10월 {p['상품명']})"
        summary[(r["병원"], "변경" if changes else "유지")] += 1
        if any(c.startswith("정가") for c in changes): r["정황"] = (r["정황"] + "; " if r["정황"] else "") + "정가 월별 변동(불일치 확인필요)"
    return summary

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", default="data/admon/extract"); ap.add_argument("--prev", required=True)
    ap.add_argument("--out", default="data/admon/master-2026-11.csv"); ap.add_argument("--summary", default="data/admon/diff-2026-11.csv")
    ap.add_argument("--rules", default="data/admon/rules.csv"); ap.add_argument("--only")
    a = ap.parse_args()
    rules = J.load_rules(a.rules)
    prev_rows, prev_idx = load_prev(a.prev)
    rows = []
    for fn in sorted(os.listdir(a.extract)):
        if not fn.endswith(".json"): continue
        if a.only and fn[:-5] != a.only: continue
        ex = json.load(open(os.path.join(a.extract, fn), encoding="utf-8"))
        rows += flatten(ex, rules)
    summary = compare(rows, prev_idx)
    # 소멸: 10월에 있었는데 11월 추출에 없는 키(추출된 의원만)
    clinics = {r["병원"] for r in rows}
    seen = {(r["병원"], r["표준코드"] or norm(r["상품명"])) for r in rows}
    gone = [p for p in prev_rows if str(p["병원"]).strip() in clinics and (str(p["병원"]).strip(), str(p.get("표준코드") or "").strip() or norm(p["상품명"])) not in seen]
    cols = ["병원", "채널·섹션", "상품명", "표준코드", "정가(원)", "이벤트가(원)", "할인율(%)", "표시방식", "조건·비고", "위반 소지", "심각도", "캡처일", "출처", "전월 대비", "정황", "규칙"]
    with open(a.out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    with open(a.summary, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["병원", "구분", "건수", "비고"])
        for (h, k), n in sorted(summary.items()): w.writerow([h, k, n, ""])
        for p in gone: w.writerow([p["병원"], "소멸(10월→11월 미확인)", 1, p["상품명"]])
    print(f"마스터 {len(rows)}행 → {a.out} · 요약 → {a.summary}")
    for (h, k), n in sorted(summary.items()): print(f"  {h} {k} {n}")
    print(f"  소멸 후보 {len(gone)}건")
    print(f"  표준코드 매칭 {sum(1 for r in rows if r['표준코드'])}/{len(rows)}")

if __name__ == "__main__":
    main()
