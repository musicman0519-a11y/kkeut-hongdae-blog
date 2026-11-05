# -*- coding: utf-8 -*-
"""판정 규칙표(rules.csv)를 마스터 행에 적용해 '위반 소지'·'심각도' 초안을 만든다.
사용법:
  판정:  from judge import judge; judge(row_dict, rules) -> {"위반": "...", "심각도": "...", "규칙": [...]}
  검증:  python -X utf8 -I scripts/admon/judge.py --eval <10월.xlsx> [--rules data/admon/rules.csv] [--show 5]
행 필드: 상품명, 채널·섹션, 정가(원), 이벤트가(원), 할인율(%), 표시방식, 조건·비고
"""
import sys, csv, re, argparse, collections

SEV = {"하": 0, "중": 1, "중~상": 2, "상": 3}
SEV_NAME = {v: k for k, v in SEV.items()}
FIELD_MAP = {"상품명": "상품명", "조건": "조건·비고", "섹션": "채널·섹션", "표시방식": "표시방식",
             "이벤트가": "이벤트가(원)", "정가": "정가(원)", "할인율": "할인율(%)"}

def load_rules(path="data/admon/rules.csv"):
    with open(path, encoding="utf-8-sig") as f:
        return [r for r in csv.DictReader(f) if r.get("id")]

def num(v):
    if v is None: return None
    s = str(v).replace(",", "").strip()
    m = re.match(r"^\d+(\.\d+)?$", s)
    return float(s) if m else None

def text_of(row, target):
    parts = []
    for t in target.split("+"):
        t = t.strip()
        if t in FIELD_MAP:
            parts.append(str(row.get(FIELD_MAP[t]) or ""))
    return " ".join(parts)

def rule_hits(row, rule):
    op, val, target = rule["연산"], rule["값"], rule["대상"]
    if op == "regex":
        return re.search(val, text_of(row, target), re.I) is not None
    if op == "lt":
        x = num(row.get("이벤트가(원)")); return x is not None and x < float(val)
    if op == "in":
        x = num(row.get(FIELD_MAP.get(target, target))); return x is not None and str(int(x)) in val.split("|")
    if op == "ratio":
        a, b = num(row.get("정가(원)")), num(row.get("이벤트가(원)"))
        if not a or not b: return False
        lo, hi = map(float, val.split("-")); return lo <= a / b <= hi
    return False

def judge(row, rules):
    hits = [r for r in rules if rule_hits(row, r)]
    if not hits:
        return {"위반": "-", "심각도": "하", "규칙": []}
    cats = collections.OrderedDict(); notes = []
    sev = 0
    for r in hits:
        if r["범주"] == "수정자": continue
        if r["범주"] == "정황": notes.append(r["조문라벨"]); continue
        cats.setdefault(r["범주"], []).append(r["조문라벨"])
        sev = max(sev, SEV[r["심각도"]])
    if not cats:
        return {"위반": "-", "심각도": "하", "규칙": [r["id"] for r in hits], "정황": notes}
    # 격상 규칙: 유인·불명확·불일치 중 두 범주 이상이면 한 단계, VAT별도 + 정가 미표기면 한 단계
    core = {c for c in cats if c in ("유인", "불명확", "불일치", "금품")}
    if len(core) >= 3 and sev >= 1: sev = min(3, sev + 1)  # 세 범주 이상 겹칠 때만 격상
    if any(r["id"] == "N04" for r in hits) and any(r["id"] in ("N01", "N02") for r in hits): sev = min(3, sev + 1)
    labels = []
    for c, ls in cats.items():
        seen = []
        for l in ls:
            if l not in seen: seen.append(l)
        labels.append("·".join(seen))
    return {"위반": "·".join(labels), "심각도": SEV_NAME[sev], "규칙": [r["id"] for r in hits], "정황": notes}

def categories(text):
    v = str(text or ""); c = set()
    for k, p in [("유인", r"유인"), ("불명확", r"불명확"), ("불일치", r"불일치|역산"), ("과장", r"과장|최상급|효능|비교"),
                 ("전후", r"전후"), ("금품", r"금품|경품|사은품|적립")]:
        if re.search(p, v): c.add(k)
    return c or {"-"}

def evaluate(xlsx, rules, show=5):
    import openpyxl
    ws = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)["마스터 데이터"]
    it = ws.iter_rows(values_only=True)
    hdr = [str(h) for h in next(it)]
    rows = [dict(zip(hdr, r)) for r in it if r and r[0]]
    cat_ok = sev_ok = sev_near = 0
    miss = collections.Counter(); examples = []
    for row in rows:
        j = judge(row, rules)
        pc, oc = categories(j["위반"]), categories(row.get("위반 소지"))
        if pc == oc: cat_ok += 1
        else:
            miss[(tuple(sorted(oc)), tuple(sorted(pc)))] += 1
            if len(examples) < show: examples.append((row.get("상품명"), row.get("표시방식"), row.get("조건·비고"), row.get("위반 소지"), j["위반"], row.get("심각도"), j["심각도"]))
        if j["심각도"] == str(row.get("심각도")): sev_ok += 1
        if abs(SEV.get(j["심각도"], 0) - SEV.get(str(row.get("심각도")), 0)) <= 1: sev_near += 1
    n = len(rows)
    print(f"행 {n} · 위반 범주 일치 {cat_ok/n:.1%} · 심각도 일치 {sev_ok/n:.1%} (±1단계 {sev_near/n:.1%})")
    print("불일치 상위:")
    for (o, p), c in miss.most_common(8): print(f"  {c:3d}  원본 {o} → 예측 {p}")
    print("예시:")
    for e in examples: print("  ", [str(x)[:30] for x in e])

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval"); ap.add_argument("--rules", default="data/admon/rules.csv"); ap.add_argument("--show", type=int, default=5)
    a = ap.parse_args()
    rules = load_rules(a.rules)
    if a.eval: evaluate(a.eval, rules, a.show)
