# -*- coding: utf-8 -*-
"""11월판 모니터링 엑셀 생성 (10월판 서식을 그대로 이어받아 병원별 시트·마스터·대시보드·메모·부속 시트를 만든다)
사용법:
  python -X utf8 -I scripts/admon/build_xlsx.py --prev "<10월.xlsx>" --master data/admon/master-2026-11.csv \
      --clinics data/admon/clinics.csv --extract data/admon/extract --captures captures/2026-11 \
      --rules data/admon/rules.csv --out "의료광고_병원별분석_종합_홍대_27개원_2026년11월.xlsx" [--month "2026년 11월"] [--only 미소앤봄의원]
주의: 수식은 셀에 수식 그대로 넣는다(계산값 없음). Excel 이 열 때 계산한다. LibreOffice 가 없어 recalc 검증은 파이썬 재계산(verify)으로 대신한다.
"""
import sys, os, re, csv, json, argparse, collections, datetime
from copy import copy
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as XLImage
from PIL import Image as PILImage

F = "맑은 고딕"
HDR_FILL = PatternFill("solid", fgColor="1F3A5F")
SOFT = PatternFill("solid", fgColor="F7F9FC")
WARN = PatternFill("solid", fgColor="FCE4D6")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
from openpyxl.cell.cell import MergedCell
def put(ws, r, c, v=None):
    """병합된 셀(앵커 아님)에는 쓰지 않는다."""
    cell = ws.cell(r, c)
    if isinstance(cell, MergedCell): return cell
    cell.value = v; return cell

SEV_RANK = {"하": 0, "중": 1, "중~상": 2, "상": 3}
MASTER_COLS = ["병원", "채널·섹션", "상품명", "표준코드", "정가(원)", "이벤트가(원)", "할인율(%)", "표시방식", "조건·비고", "위반 소지", "심각도", "캡처일"]
EXTRA_COLS = ["출처(캡처)", "전월 대비", "정황·확인필요", "적용 규칙"]

def read_csv(p):
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def safe_title(name):
    return re.sub(r"[\[\]:*?/\\]", "_", name)[:31]

def style_row_like(ws, src_row, dst_row, max_col=11):
    for c in range(1, max_col + 1):
        s, d = ws.cell(src_row, c), ws.cell(dst_row, c)
        d.font, d.fill, d.border, d.alignment, d.number_format = copy(s.font), copy(s.fill), copy(s.border), copy(s.alignment), s.number_format
    ws.row_dimensions[dst_row].height = ws.row_dimensions[src_row].height

def strip_draft(v):
    return str(v or "").replace("[초안] ", "")

def make_thumb(src, dst, width=320):
    im = PILImage.open(src); w, h = im.size
    im = im.convert("RGB").resize((width, int(h * width / w)))
    if im.size[1] > 2000: im = im.crop((0, 0, width, 2000))
    im.save(dst, "JPEG", quality=70); return im.size

def build_clinic_sheet(wb, tmpl, clinic, ex, master_rows, captures_dir, month, blocked_info):
    name = clinic["병원명"]
    ws = wb.copy_worksheet(tmpl); ws.title = safe_title(name)
    ws["A1"] = f"병원 프로필 — {name} · {month} 업데이트"
    ws["C2"] = f"{name} · {clinic.get('전문의표기') or '전문의 표기 없음'}"
    ws["C3"] = f"{clinic.get('도로명주소', '')} ({clinic.get('법정동', '')})"
    ws["C4"] = f"{clinic.get('홈페이지', '')} · 리뷰 {clinic.get('리뷰수', '-')}"
    secs = ex.get("sections", []) if ex else []
    if blocked_info and not secs:
        ws["C5"] = f"홈페이지 — 자동 접근 차단(HTTP {blocked_info.get('HTTP', '')}) · 캡처 없음 · 목록만 전달"
        ws["C6"] = "미캡처"; ws["C7"] = f"차단 사유: {blocked_info.get('제목', '')} · 수동 캡처를 captures/ 폴더에 넣으면 추출 가능"
    elif not secs:
        ws["C5"] = "홈페이지 — 이벤트 페이지 없음 또는 미추출"; ws["C6"] = ex.get("captured_at", "") if ex else ""; ws["C7"] = "추출 결과 없음"
    else:
        ws["C5"] = f"홈페이지 캡처 {len(secs)}개 섹션: " + " · ".join(s.get("section", "") for s in secs)[:300]
        ws["C6"] = f"{ex.get('captured_at', '')} · 원본: {captures_dir}/{name}/" + (f" · 자동 차단(HTTP {blocked_info.get('HTTP', '')}) → 수동 캡처" if blocked_info else "")
        ws["C7"] = "위반 유형·심각도는 규칙표 기반 [초안] — 검수 후 '[초안]' 표시 삭제. 정황·확인필요 열은 마스터 데이터 참조"
    # 분석표: 섹션당 1행, r13 부터
    first, last_tmpl = 13, 22
    rows_needed = max(len(secs), 1)
    for i in range(rows_needed):
        r = first + i
        if r > last_tmpl: style_row_like(ws, last_tmpl, r)
        put(ws, r, 1, i + 1)
    for r in range(first + rows_needed, last_tmpl + 1):  # 남는 템플릿 행 비우기
        for c in range(1, 12): put(ws, r, c)
    thumbs_dir = os.path.join(captures_dir, "_thumbs"); os.makedirs(thumbs_dir, exist_ok=True)
    by_sec = collections.defaultdict(list)
    for m in master_rows: by_sec[m["채널·섹션"]].append(m)
    for i, s in enumerate(secs):
        r = first + i; items = s.get("items", []); mrows = by_sec.get(s.get("section", ""), [])
        put(ws, r, 2, f"{s.get('section', '')}" + (f"\n({s.get('period')})" if s.get("period") else ""))
        prods = " / ".join(f"{it.get('name', '')} {fmt_price(it)}" for it in items)[:900]
        put(ws, r, 4, prods or "(가격 없는 브랜딩 배너)")
        disp = collections.Counter(it.get("display", "") for it in items if it.get("display"))
        put(ws, r, 5, "·".join(k for k, _ in disp.most_common(2)))
        put(ws, r, 6, "O" if any(isinstance(it.get("list_price"), (int, float)) for it in items) else "X")
        put(ws, r, 7, "O" if any(it.get("discount_pct") not in (None, "") for it in items) else "X")
        labels = collections.OrderedDict()
        for m in mrows:
            for l in strip_draft(m["위반 소지"]).split("·"):
                if l and l != "-": labels[l] = 1
        put(ws, r, 8, "[초안] " + ("·".join(labels) if labels else "-"))
        sev = max((SEV_RANK.get(strip_draft(m["심각도"]), 0) for m in mrows), default=0)
        put(ws, r, 9, {v: k for k, v in SEV_RANK.items()}[sev] if mrows else "")
        notes = [m["정황"] for m in mrows if m.get("정황")]
        chk = sum(1 for it in items if "확인필요" in (it.get("flags") or []) or it.get("event_price") == "확인필요")
        put(ws, r, 10, ("[초안] " + (f"확인필요 {chk}건 · " if chk else "") + ("; ".join(sorted(set(notes)))[:300] if notes else "규칙 적용 결과 외 특이사항 없음")))
        cmp = collections.Counter(m["전월 대비"].split("(")[0] for m in mrows)
        put(ws, r, 11, " · ".join(f"{k} {v}" for k, v in cmp.items()) if mrows else ("신규 편입" if clinic.get("기존10곳") != "Y" else ""))
        for c in range(2, 12): ws.cell(r, c).alignment = Alignment(wrap_text=True, vertical="top")
        cap = s.get("capture")
        src = os.path.join(captures_dir, name, cap) if cap else None
        if src and not os.path.exists(src) and cap:  # 분할 캡처면 첫 조각 사용
            alt = os.path.join(captures_dir, name, cap.replace(".png", "_p1.png"))
            if os.path.exists(alt): src = alt
        if src and os.path.exists(src):
            dst = os.path.join(thumbs_dir, f"{safe_title(name)}_{i+1}.jpg")
            w, h = make_thumb(src, dst)
            img = XLImage(dst); img.width, img.height = w, h
            ws.add_image(img, f"C{r}"); ws.row_dimensions[r].height = min(h * 0.75, 400)
            put(ws, r, 3)
        else:
            put(ws, r, 3, f"(캡처 없음: {cap or '-'})")
    if not secs:
        put(ws, first, 2, "분석 없음"); put(ws, first, 4, ws["C5"].value); put(ws, first, 11, "신규 편입" if clinic.get("기존10곳") != "Y" else "미캡처")
    last = first + rows_needed - 1
    ws["C8"] = f'="총 "&COUNTA(A{first}:A{last})&"건   ·   상 "&COUNTIF(I{first}:I{last},"상")&"   ·   중~상 "&COUNTIF(I{first}:I{last},"중~~상")&"   ·   중 "&COUNTIF(I{first}:I{last},"중")&"   ·   하 "&COUNTIF(I{first}:I{last},"하")'
    return ws, first, last

def fmt_price(it):
    lp, ep = it.get("list_price"), it.get("event_price")
    s = ""
    if isinstance(lp, (int, float)): s += f"{int(lp):,}→"
    s += f"{int(ep):,}원" if isinstance(ep, (int, float)) else str(ep or "")
    if it.get("discount_pct") not in (None, ""): s += f"({it['discount_pct']}%)"
    return s

def write_master(ws, rows):
    hdr_style = [copy(ws.cell(1, c).font) for c in range(1, 13)], [copy(ws.cell(1, c).fill) for c in range(1, 13)]
    if ws.max_row > 1: ws.delete_rows(2, ws.max_row)
    for j, c in enumerate(EXTRA_COLS, 13):
        cell = ws.cell(1, j, c); cell.font, cell.fill = copy(ws.cell(1, 12).font), copy(ws.cell(1, 12).fill)
        cell.alignment, cell.border = copy(ws.cell(1, 12).alignment), copy(ws.cell(1, 12).border)
        ws.column_dimensions[get_column_letter(j)].width = [26, 34, 34, 14][j - 13]
    for i, r in enumerate(rows, 2):
        vals = [r.get(c, "") for c in MASTER_COLS] + [r.get("출처", ""), r.get("전월 대비", ""), r.get("정황", ""), r.get("규칙", "")]
        for j, v in enumerate(vals, 1):
            if j in (5, 6, 7) and isinstance(v, str) and re.match(r"^\d+$", v): v = int(v)
            cell = put(ws, i, j, v); cell.font = Font(name=F, size=9); cell.alignment = Alignment(vertical="top", wrap_text=j in (3, 9, 10, 14, 15))
            if j in (5, 6) and isinstance(v, int): cell.number_format = "#,##0"
            if "확인필요" in str(v) and j in (5, 6, 15): cell.fill = WARN
    ws.auto_filter.ref = f"A1:{get_column_letter(12 + len(EXTRA_COLS))}{max(len(rows) + 1, 2)}"
    ws.freeze_panes = "C2"

def rebuild_dashboard(ws, clinic_sheets, master_count, month, captured_note, codes):
    """① 병원별 요약 행을 N개로, ②·④ 수식을 새 마스터 범위로 다시 쓴다."""
    n_old = 10; n_new = len(clinic_sheets); k = n_new - n_old
    if k:
        shifted = [m for m in ws.merged_cells.ranges if m.min_row >= 16]
        for m in shifted: ws.unmerge_cells(str(m))
        if k > 0:
            ws.insert_rows(16, k)
            for i in range(k): style_row_like(ws, 15, 16 + i)
        else:
            ws.delete_rows(16 + k, -k)
        for m in shifted:
            ws.merge_cells(start_row=m.min_row + k, start_column=m.min_col, end_row=m.max_row + k, end_column=m.max_col)
    ws["A1"] = f"홍대 의료광고 모니터링 대시보드 — {n_new}개 의원 · {month} 업데이트 · 형평성 소명(방어) · 가격 벤치마크 · 협회 제출용"
    ws["A2"] = f"일괄 신고용 아님 · {captured_note} · 위반 유형·심각도는 규칙표 기반 [초안](검수 전)"
    ws["A4"] = f"① 병원별 요약 ({n_new}개 의원)"
    for i, (name, sheet, first, last, clinic, note) in enumerate(clinic_sheets):
        r = 6 + i; q = f"'{sheet}'"
        put(ws, r, 1, name); put(ws, r, 2, clinic.get("전문의표기", "")[:40]); put(ws, r, 3, clinic.get("도로명주소", "")[:30])
        put(ws, r, 4, note[:120])
        put(ws, r, 5, f"=COUNTA({q}!A{first}:A{last})"); put(ws, r, 6, f'=COUNTIF({q}!I{first}:I{last},"상")')
        put(ws, r, 7, f'=COUNTIF({q}!I{first}:I{last},"중~~상")'); put(ws, r, 8, f'=COUNTIF({q}!I{first}:I{last},"중")')
        put(ws, r, 9, "[작성 필요] 핵심 발견 한 줄"); put(ws, r, 10, clinic.get("_캡처일", "")); put(ws, r, 11, clinic.get("리뷰수", "")[:12])
        for c in range(1, 12): ws.cell(r, c).font = Font(name=F, size=9, bold=(c == 1))
    tot = 6 + n_new
    put(ws, tot, 1, "합계")
    for c, L in zip(range(5, 9), "EFGH"): put(ws, tot, c, f"=SUM({L}6:{L}{tot-1})")
    put(ws, tot, 10, f"=COUNTA('마스터 데이터'!A2:A{master_count+1})")
    base = 18 + k
    ws.cell(base, 1, f"② 위반 유형별 집계 — 마스터 데이터 상품 {master_count}행 기준 ({n_new}개 의원 합산 · {month}) ※ [초안] 판정 기준 · 월별 표본 수가 달라 비율로 비교")
    for i, key in enumerate(["유인", "불명확", "불일치", "전후", "과장"]):
        r = base + 2 + i
        put(ws, r, 2, f"=SUMPRODUCT(--ISNUMBER(SEARCH(\"{key}\",'마스터 데이터'!J2:J{master_count+1})))")
        put(ws, r, 3, f"=B{r}/COUNTA('마스터 데이터'!A2:A{master_count+1})"); ws.cell(r, 3).number_format = "0.0%"
    sec3 = 26 + k
    ws.cell(sec3, 1, f"③ 지역 관행 확증표 — 유형별 해당 의원 ({n_new}곳 중 · {month} 기준) [작성 필요 — 10월 라벨 유지, 곳 수·의원명은 마스터 데이터 필터로 확인 후 기입]")
    for r in range(sec3 + 2, sec3 + 15):
        if ws.cell(r, 1).value:
            put(ws, r, 2, "[작성 필요]"); put(ws, r, 3, "[작성 필요]")
    sec4 = 42 + k
    ws.cell(sec4, 1, f"④ 시술별 가격 벤치마크 ({month} 이벤트가 · 표준코드 매칭) ※ 용량·구성·조건 상이 — 단순 비교 주의 · 끗한의원 가격 병기는 [작성 필요]")
    put(ws, sec4 + 1, 1, "표준코드"); put(ws, sec4 + 1, 2, "건수"); put(ws, sec4 + 1, 3, "최저 이벤트가"); put(ws, sec4 + 1, 4, "최고 이벤트가"); put(ws, sec4 + 1, 5, "참고 (끗한의원 이벤트가 병기)")
    for i, code in enumerate(codes):
        r = sec4 + 2 + i
        if i >= 12: style_row_like(ws, sec4 + 2, r)
        put(ws, r, 1, code)
        put(ws, r, 2, f"=COUNTIF('마스터 데이터'!D2:D{master_count+1},A{r})")
        put(ws, r, 3, f"=IFERROR(_xlfn.MINIFS('마스터 데이터'!F2:F{master_count+1},'마스터 데이터'!D2:D{master_count+1},A{r}),\"-\")")
        put(ws, r, 4, f"=IFERROR(_xlfn.MAXIFS('마스터 데이터'!F2:F{master_count+1},'마스터 데이터'!D2:D{master_count+1},A{r}),\"-\")")
        put(ws, r, 5, "[작성 필요]")
        for c in (3, 4): ws.cell(r, c).number_format = "#,##0"
    for r in range(sec4 + 2 + len(codes), sec4 + 16):
        for c in range(1, 12): put(ws, r, c)
    foot = sec4 + 16
    ws.cell(foot, 1, f"※ {month} 업데이트: 캡처 원본은 captures/ 폴더(병원별), 추출 JSON 은 data/admon/extract/, 판정 규칙은 '규칙표' 시트. '확인필요' 시트의 셀은 캡처와 대조 후 확정할 것.")

def add_simple_sheet(wb, title, header, rows, widths):
    ws = wb.create_sheet(title)
    for j, h in enumerate(header, 1):
        c = ws.cell(1, j, h); c.font = Font(name=F, size=9, bold=True, color="FFFFFF"); c.fill = HDR_FILL; c.border = BORDER
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(j)].width = widths[j - 1]
    for i, r in enumerate(rows, 2):
        for j, v in enumerate(r, 1):
            c = put(ws, i, j, v); c.font = Font(name=F, size=9); c.border = BORDER; c.alignment = Alignment(vertical="top", wrap_text=True)
    ws.freeze_panes = "A2"
    if rows: ws.auto_filter.ref = f"A1:{get_column_letter(len(header))}{len(rows)+1}"
    return ws

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prev", required=True); ap.add_argument("--master", default="data/admon/master-2026-11.csv")
    ap.add_argument("--clinics", default="data/admon/clinics.csv"); ap.add_argument("--extract", default="data/admon/extract")
    ap.add_argument("--captures", default="captures/2026-11"); ap.add_argument("--rules", default="data/admon/rules.csv")
    ap.add_argument("--out", required=True); ap.add_argument("--month", default="2026년 11월"); ap.add_argument("--only")
    a = ap.parse_args()
    clinics = [c for c in read_csv(a.clinics) if c["포함"] == "Y" and (not a.only or c["병원명"] == a.only)]
    master = read_csv(a.master)
    blocked = {}
    bp = os.path.join(a.captures, "blocked.csv")
    if os.path.exists(bp):
        for b in read_csv(bp): blocked[b["병원명"]] = b
    wb = openpyxl.load_workbook(a.prev)
    tmpl = wb["병원 템플릿(복제용)"]
    keep = {"대시보드", "마스터 데이터", "요약·형평성 메모", "병원 템플릿(복제용)"}
    for n in list(wb.sheetnames):
        if n not in keep: del wb[n]
    clinic_sheets = []; codes = []
    for c in clinics:
        name = c["병원명"]
        exp = os.path.join(a.extract, f"{name}.json")
        ex = json.load(open(exp, encoding="utf-8")) if os.path.exists(exp) else None
        mrows = [m for m in master if m["병원"] == name]
        meta_p = os.path.join(a.captures, name, "meta.json")
        if os.path.exists(meta_p):
            meta = json.load(open(meta_p, encoding="utf-8"))
            c["_캡처일"] = (meta.get("startedAt") or "")[:10]
        ws, first, last = build_clinic_sheet(wb, tmpl, c, ex, mrows, a.captures, a.month, blocked.get(name))
        note = ws["C5"].value or ""
        clinic_sheets.append((name, ws.title, first, last, c, note))
        # 시트 순서: 대시보드, 마스터 바로 뒤에 병원 시트
        wb.move_sheet(ws, offset=-(len(wb.sheetnames) - 2 - len(clinic_sheets)))
    write_master(wb["마스터 데이터"], master)
    for m in master:
        if m.get("표준코드") and m["표준코드"] not in codes: codes.append(m["표준코드"])
    captured_dates = sorted({c.get("_캡처일", "") for c in clinics if c.get("_캡처일")})
    note = f"캡처 {captured_dates[0]}~{captured_dates[-1]} 기준" if captured_dates else "캡처일 미기록"
    rebuild_dashboard(wb["대시보드"], clinic_sheets, len(master), a.month, note, codes)
    memo = wb["요약·형평성 메모"]
    memo["B1"] = f"종합 결론 — 홍대 상권 {len(clinics)}개 의원 · {a.month} [작성 필요] (아래는 10월 원문 보존 — 11월 수치는 대시보드·마스터 데이터 참조)"
    # 부속 시트
    add_simple_sheet(wb, "대상 목록", ["병원명", "법정동", "도로명주소", "홈페이지", "전문의표기", "이벤트URL", "리뷰수", "포함", "사유", "출처", "기존10곳"],
                     [[r[k] for k in ["병원명", "법정동", "도로명주소", "홈페이지", "전문의표기", "이벤트URL", "리뷰수", "포함", "사유", "출처", "기존10곳"]] for r in read_csv(a.clinics)],
                     [22, 9, 36, 36, 24, 40, 16, 7, 40, 30, 9])
    def _blocked_status(b):
        ep = os.path.join(a.extract, f"{b['병원명']}.json")
        if os.path.exists(ep) and json.load(open(ep, encoding="utf-8")).get("sections"):
            return "수동 캡처 제공 → 추출 완료(병원 시트·마스터 데이터 참조)"
        return "목록만 전달 — 직접 캡처를 captures/<병원명>/ 에 넣으면 추출 가능"
    brow = [[b["병원명"], b["URL"], b["HTTP"], b["제목"], b["시각"], _blocked_status(b)] for b in blocked.values()]
    add_simple_sheet(wb, "차단 목록", ["병원명", "URL", "HTTP", "제목/사유", "시각", "처리"], brow, [22, 44, 8, 30, 22, 50])
    add_simple_sheet(wb, "규칙표", ["id", "범주", "조문라벨", "대상", "연산", "값(정규식)", "심각도", "비고"],
                     [[r[k] for k in ["id", "범주", "조문라벨", "대상", "연산", "값", "심각도", "비고"]] for r in read_csv(a.rules)], [6, 8, 24, 16, 8, 50, 8, 44])
    chk = [[m["병원"], m["채널·섹션"], m["상품명"], m["정가(원)"], m["이벤트가(원)"], m.get("정황", ""), m.get("출처", "")] for m in master
           if "확인필요" in (str(m["정가(원)"]) + str(m["이벤트가(원)"]) + str(m.get("정황", "")))]
    add_simple_sheet(wb, "확인필요", ["병원", "섹션", "상품명", "정가", "이벤트가", "정황·사유", "출처 캡처"], chk, [16, 24, 34, 12, 12, 40, 30])
    wb.save(a.out)
    print(f"저장: {a.out} · 병원 시트 {len(clinic_sheets)} · 마스터 {len(master)}행 · 확인필요 {len(chk)}건 · 차단 {len(blocked)}곳 · 시트 {len(wb.sheetnames)}")

if __name__ == "__main__":
    main()
