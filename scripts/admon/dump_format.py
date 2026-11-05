# -*- coding: utf-8 -*-
"""10월판 모니터링 엑셀의 형식을 문서로 뽑는다.
사용법: python -X utf8 -I scripts/admon/dump_format.py <xlsx> <out_md> <out_codes_csv>
- out_md : 시트별 범위·열 머리글·병합·글꼴·열 너비·수식 수·값 집합
- out_codes_csv : 마스터 데이터의 (표준코드, 대표 상품명 예시, 건수)
"""
import sys, csv, collections
import openpyxl

src, out_md, out_csv = sys.argv[1], sys.argv[2], sys.argv[3]
wb_f = openpyxl.load_workbook(src)                  # 수식 보존
wb_v = openpyxl.load_workbook(src, data_only=True)  # 값

lines = [f"# 10월판 형식 — `{src.split('/')[-1].split(chr(92))[-1]}`", "", "자동 생성: scripts/admon/dump_format.py", ""]

def cell_str(v, w=40):
    return "" if v is None else str(v).replace("\n", " / ")[:w]

for ws in wb_f.worksheets:
    wv = wb_v[ws.title]
    fonts = collections.Counter()
    fills = collections.Counter()
    formulas = 0
    for row in ws.iter_rows():
        for c in row:
            if c.value is None:
                continue
            if isinstance(c.value, str) and c.value.startswith("="):
                formulas += 1
            f = c.font
            fonts[(f.name, f.size, bool(f.bold))] += 1
            if c.fill and c.fill.fgColor and c.fill.fgColor.rgb not in (None, "00000000"):
                fills[str(c.fill.fgColor.rgb)] += 1
    widths = {k: round(v.width, 1) for k, v in ws.column_dimensions.items() if v.width}
    lines += [f"## 시트 `{ws.title}`", "",
              f"- 범위 {ws.dimensions} · 행 {ws.max_row} · 열 {ws.max_column} · 병합 {len(ws.merged_cells.ranges)} · 수식 {formulas}개",
              f"- 글꼴 상위: " + ", ".join(f"{n} {s}pt{' 굵게' if b else ''} ({cnt})" for (n, s, b), cnt in fonts.most_common(4)),
              f"- 채움색 상위: " + (", ".join(f"{k} ({v})" for k, v in fills.most_common(4)) or "없음"),
              f"- 열 너비: " + ", ".join(f"{k}={v}" for k, v in sorted(widths.items())[:14]),
              f"- 병합 예: " + ", ".join(str(r) for r in list(ws.merged_cells.ranges)[:6]),
              "", "앞 행(값 기준):", ""]
    for i, r in enumerate(wv.iter_rows(min_row=1, max_row=min(wv.max_row, 12), values_only=True), 1):
        cells = [cell_str(c) for c in r][:12]
        if any(cells):
            lines.append(f"- r{i}: " + " | ".join(cells))
    if formulas:
        lines += ["", "수식 예:"]
        n = 0
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith("=") and n < 6:
                    lines.append(f"- {c.coordinate}: `{c.value[:90]}`"); n += 1
    lines.append("")

# 마스터 데이터 값 집합 + 표준코드
m = wb_v["마스터 데이터"]
hdr = [cell_str(c) for c in next(m.iter_rows(min_row=1, max_row=1, values_only=True))]
col = {h: i for i, h in enumerate(hdr)}
sets = {k: collections.Counter() for k in ("표시방식", "심각도", "위반 소지", "채널·섹션", "병원")}
codes = collections.defaultdict(lambda: {"n": 0, "ex": set()})
for r in m.iter_rows(min_row=2, values_only=True):
    if not r or r[0] is None:
        continue
    for k in sets:
        if k in col and r[col[k]] is not None:
            sets[k][str(r[col[k]]).strip()] += 1
    code = r[col["표준코드"]] if "표준코드" in col else None
    if code:
        codes[str(code).strip()]["n"] += 1
        if len(codes[str(code).strip()]["ex"]) < 3:
            codes[str(code).strip()]["ex"].add(str(r[col["상품명"]]).strip())

lines += ["## 마스터 데이터 값 집합", "", f"- 열: {hdr}", ""]
for k, cnt in sets.items():
    top = cnt.most_common(12)
    lines.append(f"- **{k}** ({len(cnt)}종): " + ", ".join(f"{v} ({n})" for v, n in top))
lines += ["", f"- 표준코드 {len(codes)}종 (codes.csv 참조)", ""]

with open(out_md, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["표준코드", "건수", "상품명 예시"])
    for code, d in sorted(codes.items(), key=lambda kv: -kv[1]["n"]):
        w.writerow([code, d["n"], " / ".join(sorted(d["ex"]))])
print(f"md: {out_md} ({len(lines)}줄) / codes: {len(codes)}종")
