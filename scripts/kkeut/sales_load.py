# -*- coding: utf-8 -*-
"""매출자료(세무) xlsx 의 '거래 상세' 를 정규화 CSV 로 바꾸고 요약 시트와 검산한다.
사용법: python -X utf8 -I scripts/kkeut/sales_load.py <매출자료.xlsx> <out.csv> [--salt 문자열]
출력 열: 월, 결제일, 요일, 환자키(해시), 수납자, 결제수단, 결제수단_분해, 합계, 환불액, 상태, 회원권충전, 충전전용, 충전금액, 회원권사용, 실수납, 회계매출, 비고
 - 합계 = 거래 행 금액(회원권 잔액으로 낸 것 포함). 회원권사용 = 결제수단이 회원권 충전금/포인트인 행의 합계.
 - 실수납 = 합계 − 회원권사용 (카드·현금·페이로 실제 들어온 돈, 회원권 충전 포함) → 요약의 '총 수납'.
 - 회계매출 = 합계 − 충전금액 (회원권 충전은 선수금이라 제외, 회원권 사용은 포함) → 요약의 '총 매출'.
 - 충전전용 = 행 전체가 회원권 충전인 행(요약의 결제 건수에서 제외됨).
 - 환자명은 버리고 환자ID 는 salt 를 붙여 SHA-256 앞 10자리로 바꾼다(결과 파일에 개인정보 없음).
 - 회원권충전: 비고에 '회원권 충전' 이 있으면 Y. 충전금액은 비고의 금액(없으면 합계 전액).
"""
import sys, csv, hashlib, re, datetime, argparse
import openpyxl

WD = ["월", "화", "수", "목", "금", "토", "일"]

def num(v):
    try: return float(v or 0)
    except (TypeError, ValueError): return 0.0

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("xlsx"); ap.add_argument("out"); ap.add_argument("--salt", default="kkeut-2026")
    a = ap.parse_args()
    wb = openpyxl.load_workbook(a.xlsx, read_only=True, data_only=True)
    rows = list(wb["거래 상세"].iter_rows(values_only=True)); hdr = [str(h) for h in rows[0]]
    out = []
    for r in rows[1:]:
        d = dict(zip(hdr, r))
        if not d.get("결제일시"): continue
        dt = datetime.datetime.strptime(str(d["결제일시"])[:16], "%Y-%m-%d %H:%M")
        memo = str(d.get("비고") or "")
        charge = "Y" if "회원권 충전" in memo else "N"
        m = re.search(r"회원권 충전\s*([\d,]+)원", memo)
        charge_amt = float(m.group(1).replace(",", "")) if m else (num(d["합계"]) if charge == "Y" else 0.0)
        method = str(d.get("결제수단") or "")
        base = re.sub(r"\s*\(\d+건\)", "", method).strip()
        used_pay = base.split(" + ")[0] in ("회원권 충전금", "회원권 포인트")
        out.append({
            "월": dt.strftime("%Y-%m"), "결제일": dt.strftime("%Y-%m-%d"), "요일": WD[dt.weekday()],
            "환자키": hashlib.sha256(f"{a.salt}:{d.get('환자ID')}".encode()).hexdigest()[:10],
            "수납자": str(d.get("수납자") or ""), "결제수단": method, "결제수단_분해": base.split(" + ")[0],
            "합계": int(num(d["합계"])), "환불액": int(num(d["환불액"])),
            "상태": str(d.get("상태") or ""), "회원권충전": charge,
            "충전전용": "Y" if memo.startswith("회원권 충전(선수금") else "N", "충전금액": int(charge_amt),
            "회원권사용": int(num(d["합계"])) if used_pay else 0,
            "실수납": 0 if used_pay else int(num(d["합계"])),
            "회계매출": int(num(d["합계"]) - charge_amt), "비고": memo,
        })
    with open(a.out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)

    # 검산: 요약 시트 값과 대조
    summ = {}
    for r in wb["매출 요약(세무)"].iter_rows(values_only=True):
        if r and r[0] and r[1] not in (None, ""): summ[str(r[0]).strip()] = r[1]
    charge = sum(x["충전금액"] for x in out); used = sum(x["회원권사용"] for x in out)
    cash = sum(x["실수납"] for x in out); acct = sum(x["회계매출"] for x in out)
    n_pay = sum(1 for x in out if x["충전전용"] == "N")
    checks = [("총 수납 (환불 차감 전)", cash), ("총 매출", acct), ("회원권 충전액", charge), ("회원권 사용 매출", used), ("결제 건수", n_pay)]
    ok = True
    for k, v in checks:
        ref = num(summ.get(k)); flag = "OK" if abs(ref - v) < 1 else "MISMATCH"; ok &= flag == "OK"
        print(f"{flag:8s} {k:22s} 계산 {v:>14,.0f}  요약 {ref:>14,.0f}")
    refund = sum(x["환불액"] for x in out)
    print(f"참고     환불(거래 행 기준) {refund:,.0f} · 요약 세무 환불(처리일 기준) {num(summ.get('환불')):,.0f} · 회계 환불 {num(summ.get('환불/취소')):,.0f} — 기준이 달라 일치하지 않음(헤드라인은 요약 값 사용)")
    print(f"행 {len(out)} · 고유 환자 {len({x['환자키'] for x in out})} → {a.out}")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
