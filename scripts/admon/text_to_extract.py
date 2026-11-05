# -*- coding: utf-8 -*-
"""가격이 텍스트로 렌더링된 페이지의 innerText 덤프 → 추출 JSON 섹션.
사용법: python -X utf8 -I scripts/admon/text_to_extract.py <clinic> <captured_at> <out.json> <section_name>=<txt_path>[=<capture_png>] ...
텍스트 패턴(로바에 등 Next.js 상품형): 상품명 / (설명 0~2줄) / 정가 / 이벤트가 / '시술예약'  또는  상품명 / 정가 / 이벤트가 '~' (가격표)
판정 규칙: 숫자 줄이 2개면 정가+할인가, 1개면 가격만.
"""
import sys, re, json, os

NUM = re.compile(r"^\s*([\d,]{3,})\s*원?\s*(~)?\s*$")
PCT = re.compile(r"^\s*(\d{1,2})\s*%\s*$")
STOP = {"시술예약", "이용약관", "VAT 별도", "상시 이벤트", "장바구니 담기", "이벤트/시술 예약하기", "시술 선택", "이벤트"}
HEADERS = re.compile(r"^(PETIT|SPECIAL|SKIN|LIFTING|BODY|1DAY [^\n]+|[가-힣A-Z ]{2,20}\s*이벤트|[A-Z]{3,12})$")

def parse_blocks(text):
    lines = [re.sub(r"\s*자세히 보기\s*->?\s*$", "", l.strip()) for l in text.splitlines()]
    items, buf, group = [], [], ""
    blank_before = False
    i = 0
    while i < len(lines):
        l = lines[i]
        if not l:
            # 빈 줄: 다음 내용 줄이 숫자가 아니면 카드가 끝난 것 → 버퍼 비움
            j = i + 1
            while j < len(lines) and not lines[j]: j += 1
            if j < len(lines) and NUM.match(lines[j]): blank_before = True
            i += 1; continue
        if l in STOP:
            buf = []; i += 1; continue
        m = NUM.match(l)
        if m:
            nums = [m]; pct = None
            j = i + 1
            while j < len(lines) and (NUM.match(lines[j]) or PCT.match(lines[j])):
                if PCT.match(lines[j]): pct = int(PCT.match(lines[j]).group(1))
                else: nums.append(NUM.match(lines[j]))
                j += 1
            if buf:
                if blank_before:  # 카드형(이름 / (설명) / 빈줄 / 가격): 마지막 '짧은 줄'을 이름으로
                    cands = [k for k, l in enumerate(buf) if (len(l) <= 26 or l.startswith("[")) and not re.search(r"[.。]", l) and not l.startswith("#")]
                    k = cands[-1] if cands else len(buf) - 1
                    name = buf[k]; desc = " · ".join(buf[k + 1:])
                else: name = buf[0]; desc = " · ".join(buf[1:]) if len(buf) > 1 else ""
                vals = [int(n.group(1).replace(",", "")) for n in nums]
                tilde = any(n.group(2) for n in nums)
                if len(vals) >= 2: lp, ep, disp = vals[0], vals[1], "정가+할인가"
                else: lp, ep, disp = "미표기", vals[0], "가격만"
                if pct is not None and len(vals) >= 2: disp = "%+정가+할인가"
                items.append({"name": name, "list_price": lp, "event_price": ep, "discount_pct": pct, "display": disp + ("(시작가 ~)" if tilde else ""),
                              "unit": "", "vat": "", "conditions": (("[" + group + "] ") if group else "") + desc, "flags": [], "note": "텍스트 추출"})
            buf = []; blank_before = False; i = j; continue
        if HEADERS.match(l) and not buf:
            group = l; i += 1; continue
        buf.append(l); i += 1
        if len(buf) > 6: buf = buf[-6:]
    return items

def main():
    clinic, captured_at, out = sys.argv[1], sys.argv[2], sys.argv[3]
    ex = json.load(open(out, encoding="utf-8")) if os.path.exists(out) else {"clinic": clinic, "captured_at": captured_at, "sections": []}
    for spec in sys.argv[4:]:
        parts = spec.split("=")
        section, txt = parts[0], parts[1]
        cap = parts[2] if len(parts) > 2 else os.path.basename(txt).replace(".txt", ".png")
        text = open(txt, encoding="utf-8").read()
        # 메뉴·푸터 제거: 첫 'VAT 별도' 또는 '전체 (' 이후부터 '이용약관' 전까지
        start = max(text.find("VAT 별도"), text.find("전체\n("))
        body = text[start:] if start > 0 else text
        body = body.split("이용약관")[0]
        period = ""
        mp = re.search(r"(\d{4}년 \d{1,2}월 \d{1,2}일 \(\d{2}:\d{2}\) ~ \d{4}년 \d{1,2}월 \d{1,2}일 \(\d{2}:\d{2}\))", text)
        if mp: period = mp.group(1)
        elif "상시 이벤트" in body: period = "상시"
        items = parse_blocks(body)
        vat = "별도" if "VAT 별도" in text else ""
        for it in items: it["vat"] = vat
        ex["sections"] = [s for s in ex["sections"] if s["section"] != section]
        ex["sections"].append({"capture": cap, "section": section, "period": period, "common_conditions": ("VAT 별도" if vat else ""), "items": items})
        print(f"  {section}: {len(items)}개 (기간 {period or '-'})")
    json.dump(ex, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장:", out, "섹션", len(ex["sections"]), "상품", sum(len(s["items"]) for s in ex["sections"]))

if __name__ == "__main__":
    main()
