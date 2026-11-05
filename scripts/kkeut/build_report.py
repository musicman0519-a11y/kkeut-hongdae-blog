# -*- coding: utf-8 -*-
"""끗한의원 마케팅 분석표 빌더.
사용법: python -X utf8 -I scripts/kkeut/build_report.py --month 2026-10 --data data/kkeut/2026-10 --out <xlsx>
입력: data/<월>/sales-<월>.csv (sales_load.py), channel-<월>.csv, unni-events-<월>.csv, sources.csv, summary-<월>.csv(요약 시트 헤드라인)
모든 집계는 엑셀 수식(SUMIFS·COUNTIFS·AVERAGEIFS·INDEX/MATCH·IFERROR). 가정값은 '입력_가정' 노란 칸.
"""
import csv, argparse, collections, datetime, os
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import DataBarRule

FONT = "맑은 고딕"
thin = Side(style="thin", color="BFBFBF"); BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
HEAD = PatternFill("solid", fgColor="1F4E78"); SUB = PatternFill("solid", fgColor="DDEBF7"); INPUT = PatternFill("solid", fgColor="FFFF00")
NOTE = PatternFill("solid", fgColor="F2F2F2"); KPI = PatternFill("solid", fgColor="E2EFDA")
WON = '#,##0;(#,##0);"-"'; PCT = '0.0%;(0.0%);"-"'; NUM = '#,##0;(#,##0);"-"'; DEC = '#,##0.0;(#,##0.0);"-"'

def f(size=10, bold=False, color="000000"): return Font(name=FONT, size=size, bold=bold, color=color)
def read(path):
    with open(path, encoding="utf-8-sig", newline="") as fh: return list(csv.DictReader(fh))
def to_num(v):
    if v is None or v == "": return None
    try: return float(v) if "." in str(v) else int(v)
    except ValueError: return v

class Sheet:
    def __init__(self, wb, name, widths=None, title=None, sub=None):
        self.ws = wb.create_sheet(name); self.ws.sheet_view.showGridLines = False
        if widths:
            for i, w in enumerate(widths, 1): self.ws.column_dimensions[get_column_letter(i)].width = w
        self.r = 1
        if title:
            self.ws.cell(1, 1, title).font = f(14, True); self.r = 2
            if sub: self.ws.cell(2, 1, sub).font = f(9, False, "595959"); self.r = 3
            self.r += 1
    def section(self, text):
        self.ws.cell(self.r, 1, text).font = f(11, True); self.r += 1
    def header(self, labels):
        for i, l in enumerate(labels, 1):
            c = self.ws.cell(self.r, i, l); c.font = f(10, True, "FFFFFF"); c.fill = HEAD; c.border = BORDER
            c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        self.r += 1
    def row(self, vals, fmts=None, fill=None, bold=False):
        r = self.r
        for i, v in enumerate(vals, 1):
            c = self.ws.cell(r, i, v); c.font = f(10, bold); c.border = BORDER
            c.alignment = Alignment(wrap_text=True, vertical="top")
            if fill: c.fill = fill
            if fmts and i - 1 < len(fmts) and fmts[i - 1]: c.number_format = fmts[i - 1]
        self.r += 1; return r
    def note(self, text):
        c = self.ws.cell(self.r, 1, text); c.font = f(9, False, "595959"); self.r += 1
    def blank(self, n=1): self.r += n

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--month", required=True); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); M = a.month
    sales = read(os.path.join(a.data, f"sales-{M}.csv")); chan = read(os.path.join(a.data, f"channel-{M}.csv"))
    events = read(os.path.join(a.data, f"unni-events-{M}.csv")); sources = read(os.path.join(a.data, "sources.csv"))
    summary = read(os.path.join(a.data, f"summary-{M}.csv"))
    y, mo = map(int, M.split("-")); ndays = (datetime.date(y + (mo == 12), mo % 12 + 1, 1) - datetime.date(y, mo, 1)).days
    label = f"{y}년 {mo}월"
    wb = Workbook(); wb.remove(wb.active)

    # ───────── 입력_매출
    S = Sheet(wb, "입력_매출", [9, 11, 5, 12, 9, 22, 14, 12, 11, 7, 8, 8, 12, 12, 12, 12, 30])
    cols = ["월", "결제일", "요일", "환자키", "수납자", "결제수단", "결제수단_분해", "합계", "환불액", "상태", "회원권충전", "충전전용", "충전금액", "회원권사용", "실수납", "회계매출", "비고"]
    S.header(cols)
    for x in sales:
        S.row([to_num(x[c]) if c in ("합계", "환불액", "충전금액", "회원권사용", "실수납", "회계매출") else x[c] for c in cols],
              [None, None, None, None, None, None, None, WON, WON, None, None, None, WON, WON, WON, WON, None])
    S.ws.freeze_panes = "A2"; n_sales = len(sales); last = n_sales + 1
    C = {c: get_column_letter(i + 1) for i, c in enumerate(cols)}
    def rng(c): return f"입력_매출!${C[c]}$2:${C[c]}${last}"

    # ───────── 입력_환자 (환자별 집계 — 월별)
    pats = collections.OrderedDict()
    for x in sales:
        p = pats.setdefault((x["월"], x["환자키"]), {"건수": 0, "회계매출": 0, "실수납": 0, "충전": "N", "환불": 0})
        if x["충전전용"] == "N": p["건수"] += 1
        p["회계매출"] += int(x["회계매출"]); p["실수납"] += int(x["실수납"]); p["환불"] += int(x["환불액"])
        if x["회원권충전"] == "Y": p["충전"] = "Y"
    plist = sorted(pats.items(), key=lambda kv: -kv[1]["회계매출"])
    P = Sheet(wb, "입력_환자", [9, 12, 8, 14, 14, 12, 8, 8])
    P.header(["월", "환자키", "결제건수", "회계매출", "실수납", "환불액", "회원권충전", "매출순위"])
    rank = 0
    for (m, k), v in plist:
        rank += 1; P.row([m, k, v["건수"], v["회계매출"], v["실수납"], v["환불"], v["충전"], rank], [None, None, NUM, WON, WON, WON, None, NUM])
    P.ws.freeze_panes = "A2"; plast = len(plist) + 1
    def prng(col): return f"입력_환자!${col}$2:${col}${plast}"

    # ───────── 입력_채널
    K = Sheet(wb, "입력_채널", [9, 16, 30, 14, 12, 20, 40, 36])
    K.header(["월", "채널", "지표", "값", "전월값", "기간", "출처", "키(월|채널|지표)"])
    for x in chan:
        r = K.row([x["월"], x["채널"], x["지표"], to_num(x["값"]), to_num(x["전월값"]), x["기간"], x["출처"], None], [None, None, None, NUM, NUM])
        K.ws.cell(r, 8, f'=A{r}&"|"&B{r}&"|"&C{r}')
    K.ws.freeze_panes = "A2"; klast = len(chan) + 1
    def ch(channel, metric, prev=False):
        col = "E" if prev else "D"
        return f'SUMIFS(입력_채널!${col}$2:${col}${klast},입력_채널!$H$2:$H${klast},"{M}|{channel}|{metric}")'

    # ───────── 입력_가정 (노란 칸)
    G = Sheet(wb, "입력_가정", [34, 16, 70], "입력 · 가정값 (노란 칸만 고치면 전체 수식이 따라 바뀝니다)", "출처가 '가정' 인 값은 실측이 아니므로 리포트에 '추정' 으로 표시됩니다.")
    G.header(["항목", "값", "근거 · 출처"])
    assume = [
        ("네이버 예약→내원율", 0.6, PCT, "가정. 예약 474건 중 실제 내원 비율. 내원 경로 데이터 확보 시 실측으로 교체"),
        ("여신티켓 정산율(판매액 대비 병원 수취)", 0.976, PCT, "7월 정산서 PG수수료 2.409% 기준(1−0.02409). 쿠폰·포인트는 예치금으로 정산되어 판매액에 포함된 것으로 가정"),
        ("여신티켓 매출의 차트 수납 포함 여부", "미확인", None, "거래 상세 결제수단에 여신티켓 항목이 없음. 포함이면 귀속 매출을 순매출에 더하지 않는다(이중 계산) — 아래 '합산 여부' 로 제어"),
        ("여신티켓 귀속 매출을 순매출과 합산", "N", None, "Y 로 바꾸면 '채널 합산 매출' 에 더함. 기본 N(순매출은 차트 수납 기준으로만)"),
        ("여신티켓 광고비(월)", 0, WON, "화면 CPA 과금 광고비 0. 월정액·수수료 구조는 미확인 → 확인 후 입력"),
        ("기타 매체비(월)", 0, WON, "블로그·숏폼·해외 채널 등 실비. 미확보 → 0"),
        ("마케팅 운영비(월)", 4000000, WON, "마케팅용역 계약서 1~6개월차 월 400만원(VAT 별도)"),
        ("여신티켓 집계 기간", "2026-10-07~11-03", None, "달력월과 다름(28일). 10월 정산서 확보 시 교체"),
    ]
    arow = {}
    for name, val, fmt, why in assume:
        r = G.row([name, val, why], [None, fmt, None]); G.ws.cell(r, 2).fill = INPUT; arow[name] = f"입력_가정!$B${r}"
    G.blank(); G.section("매출 요약 헤드라인 (차트 프로그램 '매출 요약(세무)' 시트에서 옮김 — 입력)")
    G.header(["항목", "값", "근거 · 출처"])
    srow = {}
    for x in summary:
        r = G.row([x["항목"], to_num(x["값"]), x["출처"]], [None, WON if x["단위"] == "원" else NUM, None]); G.ws.cell(r, 2).fill = INPUT; srow[x["항목"]] = f"입력_가정!$B${r}"
    G.ws.freeze_panes = "A4"

    # ───────── 요약 (월별 열)
    Y = Sheet(wb, "요약", [36, 18, 18, 18, 50], "월간 요약 — 끗한의원", f"기준: 회계 인식 순매출(회원권 사용 포함·충전 제외) 주지표 · 세무 기준 '순 수납' 병기 · 영업일수는 매출이 있는 날 수")
    Y.header(["지표", M, "전월", "증감률", "산식 · 비고"])  # B4 = 월 키("YYYY-MM") — SUMIFS 조건으로 쓰므로 바꾸지 말 것
    yrow = {}
    def yr(name, formula, fmt=WON, note="", bold=False, fill=None):
        r = Y.row([name, formula, None, None, note], [None, fmt, fmt, PCT, None], fill=fill, bold=bold)
        Y.ws.cell(r, 4, f'=IFERROR(IF(C{r}=0,"",B{r}/C{r}-1),"")'); yrow[name] = f"요약!$B${r}"; return r
    Y.section("① 매출");
    yr("총 수납(실제 결제·환불 전)", f"={srow['총 수납 (환불 차감 전)']}", note="세무 기준. 카드·현금·페이 실수납(회원권 충전 포함·회원권 잔액 사용 제외)")
    yr("환불(세무 기준)", f"={srow['환불']}", note="환불 처리일 기준")
    yr("순 수납(세무)", f"={srow['순 수납 (= 총 수납 − 환불)']}", bold=True)
    yr("총 매출(회계)", f"={srow['총 매출']}", note="회원권 충전 제외 · 회원권 사용분 포함")
    yr("환불(회계)", f"={srow['환불/취소']}")
    yr("순매출(회계) ★주지표", f"={srow['순매출 (= 총 매출 − 환불)']}", bold=True, fill=KPI)
    yr("회원권 충전(선수금)", f"={srow['회원권 충전액']}", note="돈은 들어왔지만 매출 아님")
    yr("회원권 사용 매출", f"={srow['회원권 사용 매출']}", note="돈은 안 들어오고 매출 인식")
    yr("회원권 순증(충전−사용)", f"={yrow['회원권 충전(선수금)']}-{yrow['회원권 사용 매출']}", note="양수면 선수금 잔액 증가")
    yr("검산: 거래 상세 실수납 합", f'=SUMIFS({rng("실수납")},{rng("월")},B$4)', note="= 총 수납 이어야 함")
    yr("검산: 거래 상세 회계매출 합", f'=SUMIFS({rng("회계매출")},{rng("월")},B$4)', note="= 총 매출 이어야 함")
    Y.blank(); Y.section("② 환자·건수")
    yr("결제 건수", f'=COUNTIFS({rng("월")},B$4,{rng("충전전용")},"N")', NUM, "회원권 충전만 한 행 제외")
    yr("고유 환자 수", f'=COUNTIFS({prng("A")},B$4)', NUM)
    yr("재방문 환자(월내 2회↑ 결제)", f'=COUNTIFS({prng("A")},B$4,{prng("C")},">=2")', NUM)
    yr("재방문율", f"=IFERROR({yrow['재방문 환자(월내 2회↑ 결제)']}/{yrow['고유 환자 수']},0)", PCT)
    yr("객단가(순매출 ÷ 고유 환자)", f"=IFERROR({yrow['순매출(회계) ★주지표']}/{yrow['고유 환자 수']},0)", WON, bold=True)
    yr("건단가(총 매출 ÷ 결제 건수)", f"=IFERROR({yrow['총 매출(회계)']}/{yrow['결제 건수']},0)")
    yr("회원권 구매 환자 수", f'=COUNTIFS({prng("A")},B$4,{prng("G")},"Y")', NUM)
    yr("영업일수", f"='매출 구조'!$B$40", NUM, "일별 표에서 매출>0 인 날")
    yr("일평균 총 매출", f"=IFERROR({yrow['총 매출(회계)']}/{yrow['영업일수']},0)")
    Y.blank(); Y.section("③ 마케팅 비용·효율")
    yr("네이버 검색광고비", f"={ch('네이버 검색광고','합계_총비용')}")
    yr("여신티켓 광고비", f"={arow['여신티켓 광고비(월)']}", note="가정 칸")
    yr("기타 매체비", f"={arow['기타 매체비(월)']}", note="가정 칸")
    yr("매체비 합계", f"={yrow['네이버 검색광고비']}+{yrow['여신티켓 광고비']}+{yrow['기타 매체비']}", bold=True)
    yr("마케팅 운영비", f"={arow['마케팅 운영비(월)']}")
    yr("총 마케팅비(매체비+운영비)", f"={yrow['매체비 합계']}+{yrow['마케팅 운영비']}", bold=True)
    yr("ROAS(순매출 ÷ 매체비)", f"=IFERROR({yrow['순매출(회계) ★주지표']}/{yrow['매체비 합계']},0)", DEC, "배수. 매체비만")
    yr("ROAS(순매출 ÷ 총 마케팅비)", f"=IFERROR({yrow['순매출(회계) ★주지표']}/{yrow['총 마케팅비(매체비+운영비)']},0)", DEC, "배수. 운영비 포함")
    yr("마케팅비 비중(총 마케팅비 ÷ 순매출)", f"=IFERROR({yrow['총 마케팅비(매체비+운영비)']}/{yrow['순매출(회계) ★주지표']},0)", PCT)
    yr("환자당 마케팅비(총 마케팅비 ÷ 고유 환자)", f"=IFERROR({yrow['총 마케팅비(매체비+운영비)']}/{yrow['고유 환자 수']},0)")
    yr("여신티켓 판매액(별도 기간)", f"={ch('여신티켓','판매액')}", note="10.07~11.03 · 차트 수납 포함 여부 미확인")
    yr("여신티켓 귀속 매출(추정)", f"={yrow['여신티켓 판매액(별도 기간)']}*{arow['여신티켓 정산율(판매액 대비 병원 수취)']}", note="판매액 × 정산율(가정)")
    Y.ws.freeze_panes = "B5"

    # ───────── 매출 구조
    T = Sheet(wb, "매출 구조", [14, 16, 16, 10, 10, 4, 16, 16, 12, 12], "매출 구조 — " + label, "모든 표는 입력_매출 시트의 SUMIFS/COUNTIFS. 금액은 회계매출(회원권 충전 제외·사용 포함)")
    T.section("① 일별"); T.header(["날짜", "회계매출", "실수납", "결제건수", "요일", "", "요일", "평균 회계매출", "일수", "비중"])
    d0 = T.r
    for d in range(1, ndays + 1):
        ds = f"{M}-{d:02d}"; wd = ["월", "화", "수", "목", "금", "토", "일"][datetime.date(y, mo, d).weekday()]
        r = T.row([ds, f'=SUMIFS({rng("회계매출")},{rng("결제일")},A{T.r})', f'=SUMIFS({rng("실수납")},{rng("결제일")},A{T.r})',
                   f'=COUNTIFS({rng("결제일")},A{T.r},{rng("충전전용")},"N")', wd], [None, WON, WON, NUM, None])
    d1 = T.r - 1
    for i, wd in enumerate(["월", "화", "수", "목", "금", "토", "일"]):
        rr = d0 + i
        T.ws.cell(rr, 7, wd).border = BORDER; T.ws.cell(rr, 7).font = f()
        T.ws.cell(rr, 8, f'=IFERROR(AVERAGEIFS($B${d0}:$B${d1},$E${d0}:$E${d1},G{rr},$B${d0}:$B${d1},">0"),0)').number_format = WON
        T.ws.cell(rr, 9, f'=COUNTIFS($E${d0}:$E${d1},G{rr},$B${d0}:$B${d1},">0")').number_format = NUM
        T.ws.cell(rr, 10, f'=IFERROR(SUMIFS($B${d0}:$B${d1},$E${d0}:$E${d1},G{rr})/SUM($B${d0}:$B${d1}),0)').number_format = PCT
        for c in (8, 9, 10): T.ws.cell(rr, c).border = BORDER; T.ws.cell(rr, c).font = f()
    T.row(["합계", f"=SUM(B{d0}:B{d1})", f"=SUM(C{d0}:C{d1})", f"=SUM(D{d0}:D{d1})"], [None, WON, WON, NUM], bold=True)
    T.ws.conditional_formatting.add(f"B{d0}:B{d1}", DataBarRule(start_type="num", start_value=0, end_type="max", color="5B9BD5"))
    # 영업일수는 요약이 참조하는 고정 셀(B40) 에 둔다
    T.ws.cell(40, 1, "영업일수(매출>0)").font = f(10, True); T.ws.cell(40, 2, f'=COUNTIF(B{d0}:B{d1},">0")').number_format = NUM
    T.ws.cell(40, 3, "상위 매출일").font = f(10, True); T.ws.cell(40, 4, f'=INDEX(A{d0}:A{d1},MATCH(MAX(B{d0}:B{d1}),B{d0}:B{d1},0))')
    T.ws.cell(40, 5, f"=MAX(B{d0}:B{d1})").number_format = WON
    T.r = 42; T.section("② 결제수단별 (거래 행 기준 · 합계 금액)"); T.header(["결제수단", "건수", "금액(합계)", "비중", "환불액"])
    m0 = T.r
    for pm in ["카드 수납", "현금 수납", "페이 수납", "회원권 충전금", "회원권 포인트"]:
        T.row([pm, f'=COUNTIFS({rng("결제수단_분해")},A{T.r},{rng("월")},"{M}")', f'=SUMIFS({rng("합계")},{rng("결제수단_분해")},A{T.r},{rng("월")},"{M}")', None,
               f'=SUMIFS({rng("환불액")},{rng("결제수단_분해")},A{T.r},{rng("월")},"{M}")'], [None, NUM, WON, PCT, WON])
    m1 = T.r - 1
    for rr in range(m0, m1 + 1): T.ws.cell(rr, 4, f"=IFERROR(C{rr}/SUM($C${m0}:$C${m1}),0)")
    T.row(["합계", f"=SUM(B{m0}:B{m1})", f"=SUM(C{m0}:C{m1})", f"=SUM(D{m0}:D{m1})", f"=SUM(E{m0}:E{m1})"], [None, NUM, WON, PCT, WON], bold=True)
    T.note("회원권 충전금·포인트 행은 '회원권 사용 매출'(돈이 안 들어온 매출). 복합 결제는 첫 수단으로 분류")
    T.blank(); T.section("③ 수납자별 (회계매출)"); T.header(["수납자", "건수", "회계매출", "비중", "환불액"])
    s0 = T.r
    for st in sorted({x["수납자"] for x in sales}, key=lambda k: -sum(int(x["회계매출"]) for x in sales if x["수납자"] == k)):
        T.row([st, f'=COUNTIFS({rng("수납자")},A{T.r},{rng("월")},"{M}",{rng("충전전용")},"N")', f'=SUMIFS({rng("회계매출")},{rng("수납자")},A{T.r},{rng("월")},"{M}")', None,
               f'=SUMIFS({rng("환불액")},{rng("수납자")},A{T.r},{rng("월")},"{M}")'], [None, NUM, WON, PCT, WON])
    s1 = T.r - 1
    for rr in range(s0, s1 + 1): T.ws.cell(rr, 4, f"=IFERROR(C{rr}/SUM($C${s0}:$C${s1}),0)")
    T.row(["합계", f"=SUM(B{s0}:B{s1})", f"=SUM(C{s0}:C{s1})", f"=SUM(D{s0}:D{s1})", f"=SUM(E{s0}:E{s1})"], [None, NUM, WON, PCT, WON], bold=True)
    T.note("'상담' 은 회원권 충전·사용 처리 담당 표기")
    T.blank(); T.section("④ 결제 금액 분포 (회원권 충전 전용 행 제외 · 합계 기준)"); T.header(["구간", "하한", "상한(미만)", "건수", "비중"])
    b0 = T.r
    for lo, hi, nm in [(0, 10000, "1만원 미만"), (10000, 50000, "1~5만원"), (50000, 100000, "5~10만원"), (100000, 300000, "10~30만원"), (300000, 1000000, "30~100만원"), (1000000, 10**9, "100만원 이상")]:
        T.row([nm, lo, hi, f'=COUNTIFS({rng("합계")},">="&B{T.r},{rng("합계")},"<"&C{T.r},{rng("충전전용")},"N",{rng("월")},"{M}")', None], [None, WON, WON, NUM, PCT])
    b1 = T.r - 1
    for rr in range(b0, b1 + 1): T.ws.cell(rr, 5, f"=IFERROR(D{rr}/SUM($D${b0}:$D${b1}),0)")
    T.row(["합계", None, None, f"=SUM(D{b0}:D{b1})", f"=SUM(E{b0}:E{b1})"], [None, None, None, NUM, PCT], bold=True)
    T.ws.freeze_panes = "A5"

    # ───────── 채널 퍼널
    F = Sheet(wb, "채널 퍼널", [30, 18, 18, 18, 18, 48], "채널 퍼널 — 유입 → 문의 → 예약·판매 → 매출(귀속)", "실측은 흰 칸, 추정은 '추정' 표기. 여신티켓은 집계 기간이 다름(입력_가정 참조)")
    F.header(["단계 / 지표", "네이버 플레이스", "네이버 검색광고", "여신티켓", "합계", "비고"])
    frow = {}
    def fr(name, b, c, d, fmt=NUM, note="", sumit=True, bold=False):
        r = F.row([name, b, c, d, f"=SUM(B{F.r}:D{F.r})" if sumit else None, note], [None, fmt, fmt, fmt, fmt, None], bold=bold); frow[name] = r; return r
    fr("노출수", None, f"={ch('네이버 검색광고','합계_노출수')}", None, note="검색광고 노출(파워링크+플레이스광고)")
    fr("유입 · 클릭", f"={ch('네이버 플레이스','플레이스 유입')}", f"={ch('네이버 검색광고','합계_클릭수')}", f"={ch('여신티켓','클릭수')}", note="플레이스 유입 13,135 안에 검색광고 클릭 일부가 포함될 수 있음")
    fr("문의(스마트콜 · 상담신청+문의)", f"={ch('네이버 플레이스','스마트콜 통화')}", None, f"={ch('여신티켓','상담 신청수')}+{ch('여신티켓','문의')}", note="여신티켓 = 상담 신청 103 + 문의 127")
    fr("예약 · 판매건수", f"={ch('네이버 플레이스','예약·주문 신청')}", None, f"={ch('여신티켓','판매건수')}")
    fr("리뷰 · 후기", f"={ch('네이버 플레이스','리뷰 등록')}", None, f"={ch('여신티켓','후기')}")
    fr("전환율(예약·판매 ÷ 유입·클릭)", f"=IFERROR(B{frow['예약 · 판매건수']}/B{frow['유입 · 클릭']},0)", None, f"=IFERROR(D{frow['예약 · 판매건수']}/D{frow['유입 · 클릭']},0)", PCT, sumit=False)
    fr("비용(매체비)", f"={ch('네이버 검색광고','플레이스광고_총비용')}", f"={ch('네이버 검색광고','파워링크_총비용')}", f"={arow['여신티켓 광고비(월)']}", WON, "플레이스 열 = 플레이스광고 비용, 검색광고 열 = 파워링크 비용")
    fr("유입·클릭당 비용", f"=IFERROR(B{frow['비용(매체비)']}/B{frow['유입 · 클릭']},0)", f"=IFERROR(C{frow['비용(매체비)']}/C{frow['유입 · 클릭']},0)", f"=IFERROR(D{frow['비용(매체비)']}/D{frow['유입 · 클릭']},0)", WON, sumit=False)
    fr("예약·판매당 비용(CPA)", f"=IFERROR(B{frow['비용(매체비)']}/B{frow['예약 · 판매건수']},0)", None, f"=IFERROR(D{frow['비용(매체비)']}/D{frow['예약 · 판매건수']},0)", WON, "여신티켓 광고비 0 이면 0", sumit=False)
    fr("귀속 매출 (추정)", f"=B{frow['예약 · 판매건수']}*{arow['네이버 예약→내원율']}*{yrow['객단가(순매출 ÷ 고유 환자)']}", None,
       f"={ch('여신티켓','판매액')}*{arow['여신티켓 정산율(판매액 대비 병원 수취)']}", WON, "플레이스 = 예약 × 내원율(가정) × 객단가(실측) · 여신티켓 = 판매액 × 정산율(가정)", bold=True)
    fr("귀속 매출 ÷ 순매출", f"=IFERROR(B{frow['귀속 매출 (추정)']}/{yrow['순매출(회계) ★주지표']},0)", None, f"=IFERROR(D{frow['귀속 매출 (추정)']}/{yrow['순매출(회계) ★주지표']},0)", PCT, "여신티켓은 기간이 달라 참고치", sumit=False)
    fr("ROAS(귀속 매출 ÷ 비용)", f"=IFERROR(B{frow['귀속 매출 (추정)']}/(B{frow['비용(매체비)']}+C{frow['비용(매체비)']}),0)", None, f"=IFERROR(D{frow['귀속 매출 (추정)']}/D{frow['비용(매체비)']},0)", DEC, "플레이스 열 = 검색광고 전체 비용 대비", sumit=False)
    F.blank(); F.section("네이버 플레이스 — 전월 대비 (화면의 '지난 기간' 값)")
    F.header(["지표", label, "전월", "증감률", "", "비고"])
    for met in ["플레이스 유입", "예약·주문 신청", "스마트콜 통화", "리뷰 등록"]:
        r = F.row([met, f"={ch('네이버 플레이스', met)}", f"={ch('네이버 플레이스', met, True)}", None, None, ""], [None, NUM, NUM, PCT])
        F.ws.cell(r, 4, f'=IFERROR(B{r}/C{r}-1,"")')
    F.blank(); F.section("네이버 플레이스 — 유입 채널 · 유입 키워드 · 통화 키워드")
    F.header(["항목", "값", "비중", "", "", "비고"])
    u0 = F.r
    for met in ["유입채널_네이버지도", "유입채널_네이버검색", "유입채널_네이버 플레이스광고"]:
        F.row([met.replace("유입채널_", "유입채널 · "), f"={ch('네이버 플레이스', met)}", None], [None, NUM, PCT])
    u1 = F.r - 1
    for rr in range(u0, u1 + 1): F.ws.cell(rr, 3, f"=IFERROR(B{rr}/B{frow['유입 · 클릭']},0)")
    F.note("유입채널 3개 합(13,035)이 유입 13,135 보다 100 적음 — 화면에 안 보이는 기타 채널")
    k0 = F.r
    for met in ["유입키워드_끗한의원", "유입키워드_홍대끗한의원", "유입키워드_끗한의원홍대", "유입키워드_홍대레이저제모", "유입키워드_한의원"]:
        F.row([met.replace("유입키워드_", "유입키워드 · "), f"={ch('네이버 플레이스', met)}", None], [None, NUM, PCT])
    k1 = F.r - 1
    for rr in range(k0, k1 + 1): F.ws.cell(rr, 3, f"=IFERROR(B{rr}/B{frow['유입 · 클릭']},0)")
    F.note("브랜드 키워드(끗한의원 계열) 3,699회 = 유입의 28%. 비브랜드 '홍대레이저제모' 138회")
    for met in ["통화키워드비중_홍대 끗 한의원", "통화키워드비중_홍대 끗한의원", "통화키워드비중_끗한의원", "통화키워드비중_끗한의원 홍대", "통화키워드비중_비립종 레이저 제거 병원"]:
        F.row([met.replace("통화키워드비중_", "통화 키워드 비중 · "), f"={ch('네이버 플레이스', met)}", None], [None, PCT])
    F.ws.freeze_panes = "B5"

    # ───────── 비용·효율 (계약 KPI)
    E = Sheet(wb, "비용·효율", [40, 18, 18, 50], "비용 · 효율 — 계약서 핵심 KPI", "마케팅용역 계약서 '핵심 KPI': 파워링크 전환·CPA / 상위노출 키워드 수 / 플레이스 유입·예약 / 해외 채널 문의 / 채널별 매출 기여")
    E.header(["KPI", label, "전월", "산식 · 비고"])
    def er(name, formula, fmt=NUM, note="", fill=None, inp=False):
        r = E.row([name, formula, None, note], [None, fmt, fmt, None], fill=fill)
        if inp: E.ws.cell(r, 2).fill = INPUT
        return r
    E.section("① 파워링크 전환 · CPA")
    er("파워링크 노출수", f"={ch('네이버 검색광고','파워링크_노출수')}")
    er("파워링크 클릭수", f"={ch('네이버 검색광고','파워링크_클릭수')}")
    er("파워링크 CTR", f"=IFERROR({ch('네이버 검색광고','파워링크_클릭수')}/{ch('네이버 검색광고','파워링크_노출수')},0)", PCT)
    er("파워링크 평균 CPC", f"={ch('네이버 검색광고','파워링크_평균CPC')}", WON)
    er("파워링크 비용", f"={ch('네이버 검색광고','파워링크_총비용')}", WON)
    er("파워링크 전환수(광고시스템 집계)", f"={ch('네이버 검색광고','파워링크_총전환수')}", NUM, "전환 추적이 안 잡혀 0 — 전환 스크립트 설치 필요")
    er("검색광고 전체 비용", f"={ch('네이버 검색광고','합계_총비용')}", WON, "파워링크 + 플레이스광고")
    er("예약당 검색광고비(CPA 대용)", f"=IFERROR({ch('네이버 검색광고','합계_총비용')}/{ch('네이버 플레이스','예약·주문 신청')},0)", WON, "전환 추적 전까지 플레이스 예약을 전환으로 사용")
    er("문의+예약당 검색광고비", f"=IFERROR({ch('네이버 검색광고','합계_총비용')}/({ch('네이버 플레이스','예약·주문 신청')}+{ch('네이버 플레이스','스마트콜 통화')}),0)", WON)
    E.blank(); E.section("② 상위노출 키워드 수 (입력)")
    er("상위노출 키워드 수", None, NUM, "순위 추적 자료 없음 — 입력", inp=True)
    E.blank(); E.section("③ 플레이스 유입 · 예약")
    er("플레이스 유입", f"={ch('네이버 플레이스','플레이스 유입')}")
    er("플레이스 예약·주문", f"={ch('네이버 플레이스','예약·주문 신청')}")
    er("유입→예약 전환율", f"=IFERROR({ch('네이버 플레이스','예약·주문 신청')}/{ch('네이버 플레이스','플레이스 유입')},0)", PCT)
    er("스마트콜 통화", f"={ch('네이버 플레이스','스마트콜 통화')}")
    er("리뷰 등록", f"={ch('네이버 플레이스','리뷰 등록')}", NUM, "전월 136 → 79 (−42%)")
    E.blank(); E.section("④ 해외 채널 문의 (입력)")
    er("샤오홍슈·디엔핑·LINE 문의 수", None, NUM, "자료 없음 — 입력", inp=True)
    E.blank(); E.section("⑤ 채널별 매출 기여 (추정)")
    er("순매출(회계)", f"={yrow['순매출(회계) ★주지표']}", WON)
    er("네이버 플레이스 귀속 매출(추정)", f"='채널 퍼널'!B{frow['귀속 매출 (추정)']}", WON, "예약 × 내원율(가정) × 객단가")
    er("여신티켓 귀속 매출(추정 · 별도 기간)", f"='채널 퍼널'!D{frow['귀속 매출 (추정)']}", WON, "판매액 × 정산율(가정)")
    er("귀속 합계 ÷ 순매출", f"=IFERROR(('채널 퍼널'!B{frow['귀속 매출 (추정)']}+'채널 퍼널'!D{frow['귀속 매출 (추정)']})/{yrow['순매출(회계) ★주지표']},0)", PCT, "100% 초과 시 가정(내원율·정산율) 또는 이중 계산 점검")
    er("ROAS(순매출 ÷ 매체비)", f"={yrow['ROAS(순매출 ÷ 매체비)']}", DEC)
    er("ROAS(순매출 ÷ 총 마케팅비)", f"={yrow['ROAS(순매출 ÷ 총 마케팅비)']}", DEC)
    E.ws.freeze_panes = "B5"

    # ───────── 여신티켓 이벤트
    U = Sheet(wb, "여신티켓 이벤트", [5, 13, 40, 11, 8, 7, 7, 10, 14, 9, 13, 9, 9, 9, 9, 10], "여신티켓 이벤트별 성과 — 2026-10-07 ~ 11-03 (화면 상위 20건)", "출처: 여신티켓 광고관리 화면 2장. 합계 70,805,000 중 캡처된 20건 65,930,600 · 나머지 4,874,400 은 화면 밖")
    U.header(["순위", "이벤트ID", "이벤트명", "업데이트일", "스크랩", "문의", "후기", "클릭수", "판매액", "판매건수", "건당 결제액", "상담 신청", "판매액 비중", "클릭→판매 전환율", "클릭당 판매액", "광고품질"])
    e0 = U.r
    for x in events:
        r = U.row([to_num(x["순위"]), x["이벤트ID"], x["이벤트명"], x["업데이트일"], to_num(x["스크랩"]), to_num(x["문의"]), to_num(x["후기"]), to_num(x["클릭수"]), to_num(x["판매액"]), to_num(x["판매건수"]), to_num(x["판매건당 결제액"]), to_num(x["상담 신청수"]), None, None, None, x["광고품질"]],
                  [NUM, None, None, None, NUM, NUM, NUM, NUM, WON, NUM, WON, NUM, PCT, PCT, WON, None])
        U.ws.cell(r, 13, f"=IFERROR(I{r}/{ch('여신티켓','판매액')},0)"); U.ws.cell(r, 14, f"=IFERROR(J{r}/H{r},0)"); U.ws.cell(r, 15, f"=IFERROR(I{r}/H{r},0)")
    e1 = U.r - 1
    U.row(["", "", "캡처 20건 합계", "", f"=SUM(E{e0}:E{e1})", f"=SUM(F{e0}:F{e1})", f"=SUM(G{e0}:G{e1})", f"=SUM(H{e0}:H{e1})", f"=SUM(I{e0}:I{e1})", f"=SUM(J{e0}:J{e1})", f"=IFERROR(I{e1+1}/J{e1+1},0)", f"=SUM(L{e0}:L{e1})", f"=SUM(M{e0}:M{e1})", f"=IFERROR(J{e1+1}/H{e1+1},0)", f"=IFERROR(I{e1+1}/H{e1+1},0)"],
          [None, None, None, None, NUM, NUM, NUM, NUM, WON, NUM, WON, NUM, PCT, PCT, WON], bold=True)
    U.row(["", "", "화면 합계(기간 전체)", "", f"={ch('여신티켓','스크랩')}", f"={ch('여신티켓','문의')}", f"={ch('여신티켓','후기')}", f"={ch('여신티켓','클릭수')}", f"={ch('여신티켓','판매액')}", f"={ch('여신티켓','판매건수')}", f"={ch('여신티켓','판매건당 결제액')}", f"={ch('여신티켓','상담 신청수')}"],
          [None, None, None, None, NUM, NUM, NUM, NUM, WON, NUM, WON, NUM], fill=SUB)
    U.ws.conditional_formatting.add(f"I{e0}:I{e1}", DataBarRule(start_type="num", start_value=0, end_type="max", color="F4B183"))
    U.blank(); U.section("카테고리별 (이벤트명 키워드로 분류 — 수식)")
    U.header(["", "카테고리", "키워드", "", "", "", "", "클릭수", "판매액", "판매건수", "", "", "판매액 비중"])
    c0 = U.r
    cats = [("제모", ["제모"]), ("리프팅(슈링크·온다·인모드)", ["슈링크", "온다", "인모드"]), ("토닝·색소", ["토닝"]),
            ("관리·스킨부스터(LDM·포텐자·쥬베룩·골드PTT)", ["LDM", "포텐자", "쥬베룩", "골드PTT"]), ("병변·흉터·문신", ["사마귀", "흉터", "문신"])]
    for cat, kws in cats:
        crit = ", ".join(kws)
        def sumk(col): return "=" + "+".join(f'SUMIFS({col}{e0}:{col}{e1},C{e0}:C{e1},"*{k}*")' for k in kws)
        r = U.row(["", cat, crit, None, None, None, None, sumk("H"), sumk("I"), sumk("J"), None, None, None],
                  [None, None, None, None, None, None, None, NUM, WON, NUM, None, None, PCT])
        U.ws.cell(r, 13, f"=IFERROR(I{r}/I{e1+1},0)")
    U.note("이벤트명 키워드(와일드카드) 분류 — 한 이벤트가 두 키워드에 걸리면 중복 집계됨. 정확한 분류는 항목별 매출 자료 확보 후")
    U.ws.freeze_panes = "D5"

    # ───────── 환자 지표
    Q = Sheet(wb, "환자 지표", [40, 18, 18, 50], "환자 지표 — " + label, "입력_환자(환자별 월 집계, 환자키는 해시) 기준. 신규/재진 구분은 자료 없음(제외)")
    Q.header(["지표", label, "전월", "산식 · 비고"])
    qrow = {}
    def qr(name, formula, fmt=NUM, note=""):
        r = Q.row([name, formula, None, note], [None, fmt, fmt, None]); qrow[name] = f"B{r}"; return r
    qr("고유 환자 수", f'=COUNTIFS({prng("A")},"{M}")')
    qr("1회 결제 환자", f'=COUNTIFS({prng("A")},"{M}",{prng("C")},1)')
    qr("2회 이상 결제 환자(월내 재방문)", f'=COUNTIFS({prng("A")},"{M}",{prng("C")},">=2")')
    qr("재방문율", f"=IFERROR({qrow['2회 이상 결제 환자(월내 재방문)']}/{qrow['고유 환자 수']},0)", PCT)
    qr("환자당 평균 결제 건수", f'=IFERROR(SUMIFS({prng("C")},{prng("A")},"{M}")/{qrow["고유 환자 수"]},0)', DEC)
    qr("객단가(회계매출 ÷ 환자)", f'=IFERROR(SUMIFS({prng("D")},{prng("A")},"{M}")/{qrow["고유 환자 수"]},0)', WON)
    qr("환자 1인 최대 회계매출", f'=MAXIFS({prng("D")},{prng("A")},"{M}")'.replace("MAXIFS", "_xlfn.MAXIFS"), WON)
    qr("상위 20% 환자 수", f"=ROUNDUP({qrow['고유 환자 수']}*0.2,0)")
    qr("상위 20% 환자 매출 비중", f'=IFERROR(SUMIFS({prng("D")},{prng("A")},"{M}",{prng("H")},"<="&{qrow["상위 20% 환자 수"]})/SUMIFS({prng("D")},{prng("A")},"{M}"),0)', PCT, "파레토. 매출순위 ≤ 상위 20% 인원")
    qr("상위 10명 매출 비중", f'=IFERROR(SUMIFS({prng("D")},{prng("A")},"{M}",{prng("H")},"<=10")/SUMIFS({prng("D")},{prng("A")},"{M}"),0)', PCT)
    qr("회원권 구매 환자 수", f'=COUNTIFS({prng("A")},"{M}",{prng("G")},"Y")')
    qr("회원권 구매 환자 비중", f"=IFERROR({qrow['회원권 구매 환자 수']}/{qrow['고유 환자 수']},0)", PCT)
    qr("회원권 구매 환자 회계매출 합", f'=SUMIFS({prng("D")},{prng("A")},"{M}",{prng("G")},"Y")', WON, "충전 당일 시술 포함")
    qr("환불 발생 환자 수", f'=COUNTIFS({prng("A")},"{M}",{prng("F")},">0")')
    Q.ws.freeze_panes = "B5"

    # ───────── 자료 출처
    R = Sheet(wb, "자료 출처", [28, 60, 20, 10, 18, 60], "자료 출처 · 확보 상태")
    R.header(["자료", "출처 파일", "기간", "단위", "확보 상태", "비고"])
    for x in sources: R.row([x["자료"], x["출처 파일"], x["기간"], x["단위"], x["확보 상태"], x["비고"]])
    R.note(f"원자료 폴더: data/kkeut/{M}/raw/ · 생성 스크립트: scripts/kkeut/sales_load.py, build_report.py · 생성일 {datetime.date.today()}")

    # ───────── 대시보드 (맨 앞)
    D = Sheet(wb, "대시보드", [30, 20, 20, 20, 20, 20], f"끗한의원 마케팅 분석표 — {label}", "순매출은 회계 인식 기준(회원권 사용 포함·충전 제외). '추정' 은 입력_가정의 가정값에 따름. 생성 " + str(datetime.date.today()))
    wb.move_sheet(D.ws, offset=-(len(wb.sheetnames) - 1))
    D.section("핵심 지표")
    cards = [("순매출(회계)", yrow["순매출(회계) ★주지표"], WON), ("순 수납(세무)", yrow["순 수납(세무)"], WON), ("고유 환자", yrow["고유 환자 수"], NUM), ("객단가", yrow["객단가(순매출 ÷ 고유 환자)"], WON),
             ("재방문율(월내)", yrow["재방문율"], PCT), ("일평균 총 매출", yrow["일평균 총 매출"], WON), ("매체비 합계", yrow["매체비 합계"], WON), ("총 마케팅비", yrow["총 마케팅비(매체비+운영비)"], WON),
             ("ROAS(매체비)", yrow["ROAS(순매출 ÷ 매체비)"], DEC), ("ROAS(총 마케팅비)", yrow["ROAS(순매출 ÷ 총 마케팅비)"], DEC), ("마케팅비 비중", yrow["마케팅비 비중(총 마케팅비 ÷ 순매출)"], PCT), ("환자당 마케팅비", yrow["환자당 마케팅비(총 마케팅비 ÷ 고유 환자)"], WON)]
    for i in range(0, len(cards), 4):
        r = D.r
        for j, (nm, ref, fmt) in enumerate(cards[i:i + 4]):
            c = D.ws.cell(r, 1 + j, nm); c.font = f(9, False, "595959"); c.fill = KPI; c.border = BORDER
            v = D.ws.cell(r + 1, 1 + j, f"={ref}"); v.font = f(14, True); v.number_format = fmt; v.fill = KPI; v.border = BORDER
        D.r += 3
    D.section("채널 퍼널 (유입 → 문의 → 예약·판매 → 귀속 매출)")
    D.header(["단계", "네이버 플레이스", "네이버 검색광고", "여신티켓(10.07~11.03)", "", "비고"])
    for nm in ["유입 · 클릭", "문의(스마트콜 · 상담신청+문의)", "예약 · 판매건수", "비용(매체비)", "귀속 매출 (추정)", "ROAS(귀속 매출 ÷ 비용)"]:
        rr = frow[nm]; fmt = WON if "비용" in nm or "매출" in nm else (DEC if "ROAS" in nm else NUM)
        D.row([nm, f"='채널 퍼널'!B{rr}", f"='채널 퍼널'!C{rr}", f"='채널 퍼널'!D{rr}", None, "추정" if "추정" in nm or "ROAS" in nm else ""], [None, fmt, fmt, fmt])
    D.blank(); D.section("플레이스 전월 대비")
    D.header(["지표", label, "전월", "증감률", "", ""])
    for met in ["플레이스 유입", "예약·주문 신청", "스마트콜 통화", "리뷰 등록"]:
        r = D.row([met, f"={ch('네이버 플레이스', met)}", f"={ch('네이버 플레이스', met, True)}", None], [None, NUM, NUM, PCT]); D.ws.cell(r, 4, f'=IFERROR(B{r}/C{r}-1,"")')
    D.blank(); D.section("핵심 발견 [초안] — 숫자는 시트 수식 참조, 해석은 검토 필요")
    findings = read(os.path.join(a.data, f"findings-{M}.csv")) if os.path.exists(os.path.join(a.data, f"findings-{M}.csv")) else []
    for x in findings:
        r = D.row([x["구분"], x["내용"]], fill=NOTE); D.ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6); D.ws.row_dimensions[r].height = 45
    D.ws.freeze_panes = "A4"

    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if c.font is None or c.font.name != FONT: c.font = Font(name=FONT, size=c.font.size or 10, bold=c.font.bold, color=c.font.color)
    wb.save(a.out)
    print(f"저장: {a.out} · 시트 {len(wb.sheetnames)} · 거래 {n_sales}행 · 환자 {len(plist)}명 · 채널 지표 {len(chan)} · 이벤트 {len(events)}")

if __name__ == "__main__":
    main()
