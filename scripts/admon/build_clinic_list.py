# -*- coding: utf-8 -*-
"""data/admon/clinics.csv → 대상 목록 엑셀.
사용법: python -X utf8 -I scripts/admon/build_clinic_list.py data/admon/clinics.csv <out.xlsx>
서식은 10월판 모니터링 파일 관례(맑은 고딕 9pt, 머리글 진남색 채움·흰 글씨)를 따른다. 수식 없음.
"""
import sys, csv, datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

src, out = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(src, encoding="utf-8")))
cols = ["병원명", "법정동", "도로명주소", "홈페이지", "전문의표기", "이벤트URL", "리뷰수", "포함", "사유", "출처", "기존10곳"]
widths = [22, 9, 40, 40, 26, 48, 20, 7, 48, 34, 9]

F = "맑은 고딕"
hdr_fill = PatternFill("solid", fgColor="1F3A5F")
inc_fill = PatternFill("solid", fgColor="E2EFDA")   # 포함
exc_fill = PatternFill("solid", fgColor="F2F2F2")   # 제외
blk_fill = PatternFill("solid", fgColor="FCE4D6")   # 차단/접속 문제
thin = Side(style="thin", color="BFBFBF")
border = Border(left=thin, right=thin, top=thin, bottom=thin)

wb = Workbook()
ws = wb.active
ws.title = "대상 목록"
inc = sum(r["포함"] == "Y" for r in rows)
ws["A1"] = f"홍대(서교동·동교동) 피부·미용 의원 — 의료광고 모니터링 대상 목록 · 2026년 11월"
ws["A1"].font = Font(name=F, size=12, bold=True)
ws["A2"] = (f"후보 {len(rows)}곳 · 포함 {inc}곳 · 제외 {len(rows)-inc}곳 · 확정 {datetime.date.today():%Y-%m-%d} · "
            "출처: 닥터나우·모두닥·마이닥터 교차 + 각 홈페이지 확인 · 초록=포함, 회색=제외, 주황=자동 접근 차단·접속 문제(목록만 전달)")
ws["A2"].font = Font(name=F, size=9, color="595959")
ws.merge_cells("A1:K1"); ws.merge_cells("A2:K2")

h = 4
for j, c in enumerate(cols, 1):
    cell = ws.cell(row=h, column=j, value=c)
    cell.font = Font(name=F, size=9, bold=True, color="FFFFFF")
    cell.fill = hdr_fill
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = border
    ws.column_dimensions[get_column_letter(j)].width = widths[j - 1]
ws.row_dimensions[h].height = 22

for i, r in enumerate(rows, h + 1):
    issue = any(k in r["사유"] for k in ("차단", "502", "불안정", "접속 불가"))
    fill = inc_fill if r["포함"] == "Y" else exc_fill
    if r["포함"] == "Y" and issue:
        fill = blk_fill
    for j, c in enumerate(cols, 1):
        v = r[c]
        cell = ws.cell(row=i, column=j, value=v)
        cell.font = Font(name=F, size=9, bold=(c == "병원명"))
        cell.fill = fill
        cell.border = border
        cell.alignment = Alignment(vertical="top", wrap_text=(c in ("도로명주소", "전문의표기", "이벤트URL", "사유", "출처")),
                                   horizontal="center" if c in ("법정동", "포함", "기존10곳") else "left")
        if c in ("홈페이지", "이벤트URL") and v.startswith("http"):
            cell.hyperlink = v.split(" ")[0]
            cell.font = Font(name=F, size=9, color="0563C1", underline="single")

ws.freeze_panes = ws.cell(row=h + 1, column=2)
ws.auto_filter.ref = f"A{h}:K{h + len(rows)}"

# 요약 시트
s = wb.create_sheet("요약")
s.column_dimensions["A"].width = 30; s.column_dimensions["B"].width = 10; s.column_dimensions["C"].width = 70
s["A1"] = "구분"; s["B1"] = "곳"; s["C1"] = "의원"
for c in ("A1", "B1", "C1"):
    s[c].font = Font(name=F, size=9, bold=True, color="FFFFFF"); s[c].fill = hdr_fill; s[c].border = border
groups = [
    ("기존 10곳(전부 포함)", [r for r in rows if r["기존10곳"] == "Y"]),
    ("신규 포함", [r for r in rows if r["기존10곳"] != "Y" and r["포함"] == "Y"]),
    ("포함 중 자동 접근 차단·접속 문제(목록만 전달)", [r for r in rows if r["포함"] == "Y" and any(k in r["사유"] for k in ("차단", "502", "불안정"))]),
    ("제외 — 홈페이지 없음", [r for r in rows if r["포함"] == "N" and "홈페이지 없음" in r["사유"]]),
    ("제외 — 기타(접속 불가·타 과목·네트워크)", [r for r in rows if r["포함"] == "N" and "홈페이지 없음" not in r["사유"]]),
]
for i, (name, g) in enumerate(groups, 2):
    s.cell(row=i, column=1, value=name).font = Font(name=F, size=9, bold=True)
    s.cell(row=i, column=2, value=len(g)).font = Font(name=F, size=9)
    s.cell(row=i, column=3, value=", ".join(r["병원명"] for r in g)).font = Font(name=F, size=9)
    for j in range(1, 4):
        s.cell(row=i, column=j).border = border
        s.cell(row=i, column=j).alignment = Alignment(vertical="top", wrap_text=True)

wb.save(out)
print(f"저장: {out} · 대상 목록 {len(rows)}행(포함 {inc})")
