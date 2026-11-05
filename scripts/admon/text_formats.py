# -*- coding: utf-8 -*-
"""사이트별 텍스트 덤프 파서 (innerText 형식이 text_to_extract.py 의 기본 패턴과 다른 곳)
사용법: python -X utf8 -I scripts/admon/text_formats.py <format> <clinic> <captured_at> <out.json> <section>=<txt>[=<png>] ...
format:
  beautylounge : 블록 '시술 정보' 구분 · '이름 / 가격원(~) / 기존가 : N원 / (옵션: 3cc / 240,000원 …) / 조건(택1) / …'
  ppeum        : '11월 메인 : … / 이름 / ▶ 이벤트 기간 : … / NN% 이벤트가정가(붙어 있음)'
"""
import sys, re, json, os

WON = re.compile(r"^([\d,]{3,})\s*원\s*(~)?$")
BASE = re.compile(r"^기존가\s*:\s*([\d,]{3,})\s*원")
def n(s): return int(s.replace(",", ""))

def parse_beautylounge(text):
    lines = [l.strip() for l in text.splitlines()]
    # 섹션 머리글([BEAUTY PICK 3] 등)과 '시술 정보' 블록
    blocks, cur, group = [], [], ""
    for l in lines:
        if re.match(r"^\[.*\]$", l): group = l
        if l == "시술 정보":
            if cur: blocks.append((group, cur))
            cur = []; continue
        if l: cur.append(l)
    if cur: blocks.append((group, cur))
    items = []
    for group, b in blocks:
        # 첫 가격줄의 바로 앞 비공백 줄 = 상품명
        pi = next((i for i, l in enumerate(b) if WON.match(l)), None)
        if pi is None or pi == 0 or b[pi - 1].startswith("["):
            # 머리글 블록(BEAUTY PICK: 이름/가격 반복)
            k = 0
            while k < len(b) - 1:
                if WON.match(b[k + 1]) and not WON.match(b[k]) and not BASE.match(b[k]) and not b[k].startswith("["):
                    nm = (b[k - 1] + " " + b[k]) if b[k].startswith("(") and k > 0 else b[k]
                    items.append(mk(nm, "미표기", n(WON.match(b[k + 1]).group(1)), group, "", False))
                    k += 2
                else: k += 1
            continue
        name = b[pi - 1]; m = WON.match(b[pi]); ep = n(m.group(1)); tilde = bool(m.group(2))
        lp = "미표기"; cond = []; opts = []
        rest = b[pi + 1:]
        for i, l in enumerate(rest):
            bm = BASE.match(l)
            if bm: lp = n(bm.group(1)); continue
            if l.startswith("조건"):
                cond.append(l + (" " + rest[i + 1] if i + 1 < len(rest) else "")); continue
            if i + 1 < len(rest) and WON.match(rest[i + 1]) and not WON.match(l) and len(l) <= 24 and not l.startswith("기존가")                and re.search(r"(\d\s*(cc|CC|회|샷|vial|시린지|부위|줄|분|kj|KJ|u|U|cm|㎠)|국산|수입|뉴라미스|쥬비덤|레스틸렌|벨로테로|프리미엄|독일산)", l):
                opts.append((l, n(WON.match(rest[i + 1]).group(1))))
        base = mk(name, lp, ep, group, " · ".join(cond), tilde)
        items.append(base)
        for on, ov in opts:
            if ov != ep:
                items.append(mk(f"{name} {on}", "미표기", ov, group, " · ".join(cond), False, note="옵션 단가"))
    return items

def mk(name, lp, ep, group, cond, tilde, note=""):
    disp = "정가+할인가" if isinstance(lp, int) else "가격만"
    return {"name": name, "list_price": lp, "event_price": ep, "discount_pct": None, "display": disp + ("(시작가 ~)" if tilde else ""),
            "unit": "", "vat": "", "conditions": ((f"[{group}] " if group else "") + cond).strip(), "flags": [], "note": note or "텍스트 추출"}

PPEUM = re.compile(r"^(\d{1,2})%\s*([\d,]{5,})$")
def parse_ppeum(text):
    lines = [l.strip() for l in text.splitlines()]
    items = []; group = ""; name = ""; period = ""
    for l in lines:
        if re.match(r"^11월 (메인|1\+1|1회 체험가)", l): group = l; continue
        m = PPEUM.match(l)
        if m and name:
            pct = int(m.group(1)); digits = m.group(2).replace(",", "")
            # 이벤트가와 정가가 붙어 있음: 할인율로 분리 (ep ≈ lp*(1-pct/100))
            best = None
            for cut in range(4, len(digits) - 3):
                ep, lp = int(digits[:cut]), int(digits[cut:])
                if lp > ep and abs(round((1 - ep / lp) * 100) - pct) <= 1:
                    best = (ep, lp); break
            if best:
                items.append({"name": name, "list_price": best[1], "event_price": best[0], "discount_pct": pct, "display": "%+정가+할인가", "unit": "", "vat": "", "conditions": (f"[{group}] " if group else "") + period, "flags": [], "note": "텍스트 추출"})
            else:
                items.append({"name": name, "list_price": "확인필요", "event_price": "확인필요", "discount_pct": pct, "display": "%+정가+할인가", "unit": "", "vat": "", "conditions": (f"[{group}] " if group else "") + period, "flags": ["확인필요"], "note": f"붙은 숫자 {m.group(2)} 분리 실패"})
            name = ""; period = ""; continue
        if l.startswith("▶ 이벤트 기간"): period = l.replace("▶ ", ""); continue
        if l in ("시술 담기", "") or l.startswith("11월 메인") : continue
        if not name and not PPEUM.match(l) and len(l) < 60: name = l
        elif name and not period and not PPEUM.match(l) and len(l) < 60: name = l  # 직전 줄이 이름
    return items


MAY = re.compile(r"([^:：💙]{2,80}?)\s*[:：]\s*([\d,]{4,})\s*원")
def parse_maypure(text):
    items = []
    for part in re.split(r"💙", text):
        head = part.split("｜")[0].strip()[:30] if "｜" in part[:60] else ""
        for m in MAY.finditer(part):
            name = m.group(1).strip()
            name = re.sub(r"^(단독 시술|패키지|페이스 단독 시술|컷슬린 인젝션 패키지|바디 인모드|스킨부스터 패키지|추가 옵션|추가)\s*", "", name)
            name = re.sub(r"^[^가-힣A-Za-z0-9]+", "", name)
            if len(name) > 40: name = re.split(r"[.。]\s*|니다\s+|입니다\s*", name)[-1].strip()
            name = re.sub(r"^(단독 시술|패키지|페이스 단독 시술|컷슬린 인젝션 패키지|바디 인모드|스킨부스터 패키지|추가 옵션|추가)\s*", "", name).strip()
            if len(name) < 2: continue
            items.append({"name": name, "list_price": "미표기", "event_price": n(m.group(2)), "discount_pct": None, "display": "가격만", "unit": "", "vat": "", "conditions": (f"[{head}] " if head else "") + "11월 첫째 주 혜택(전 지점)", "flags": [], "note": "텍스트 추출(홈 본문)"})
    return items


VELYB = re.compile(r"^(\d{1,2})%\s*([\d,]{3,})\s*원\s*([\d,]{3,})\s*원$")
def parse_velyb(text, branch="홍대점"):
    lines = [l.strip() for l in text.splitlines()]
    items = []; i = 0
    while i < len(lines):
        m = VELYB.match(lines[i])
        if m:
            # 위로 거슬러: 상품명(바로 위 비공백), 그 위 설명, 섹션명, 기간, 지점
            ctx = [l for l in lines[max(0, i - 12):i] if l]
            name = ctx[-1] if ctx else ""
            sec = next((l for l in ctx[-5:-1] if not l.endswith("까지") and not l.endswith("점") and len(l) <= 20 and "♥" not in l), "")
            period = next((l for l in ctx if l.endswith("까지")), "")
            br = next((l for l in ctx if l.endswith("점")), "")
            if br and br != branch: i += 1; continue
            items.append({"name": name, "list_price": n(m.group(3)), "event_price": n(m.group(2)), "discount_pct": int(m.group(1)), "display": "%+정가+할인가", "unit": "", "vat": "", "conditions": (f"[{sec}] " if sec else "") + period, "flags": [], "note": "텍스트 추출 · " + br})
        i += 1
    return items


MW = re.compile(r"^(\d+(?:\.\d+)?)\s*만원$")
MWB = re.compile(r"^(\d+(?:\.\d+)?)\s*만원\s*(\d{1,2})%\s*↓?$")
def parse_lizon(text):
    lines = [l.strip() for l in text.splitlines()]
    items, buf, sec, seen = [], [], "", set()
    i = 0
    while i < len(lines):
        l = lines[i]
        m = MW.match(l)
        if m:
            ep = int(round(float(m.group(1)) * 10000)); lp = "미표기"; pct = None
            if i + 1 < len(lines) and MWB.match(lines[i + 1]):
                b = MWB.match(lines[i + 1]); lp = int(round(float(b.group(1)) * 10000)); pct = int(b.group(2)); i += 1
            body = [x for x in buf if x]
            notes = [x for x in body if x.startswith("※")]; body = [x for x in body if not x.startswith("※")]
            if len(body) >= 3 and re.search(r"(이벤트|스페셜|패키지|프로그램|런칭|BEST|TOP)\s*$", body[0]) and "＋" not in body[0] and "+" not in body[0]:
                sec = body[0]; body = body[1:]
            name = body[0] if body else ""; desc = " · ".join(body[1:] + notes)
            key = (name, ep)
            if name and key not in seen:
                seen.add(key)
                items.append({"name": name, "list_price": lp, "event_price": ep, "discount_pct": pct, "display": ("%+정가+할인가" if pct is not None else "가격만") + "(만원 단위)", "unit": "", "vat": "", "conditions": (f"[{sec}] " if sec else "") + desc, "flags": [], "note": "텍스트 추출"})
            buf = []; i += 1; continue
        if l in ("시술 예약하기", "이벤트 시술명", "*VAT별도"): buf = []; i += 1; continue
        buf.append(l); i += 1
        if len(buf) > 6: buf = buf[-6:]
    return items


def parse_uni(text):
    """유앤아이: '섹션 / 정가원 / 이벤트가원 / 상품명' 순서(이름이 가격 뒤에 온다)"""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    items = []; seen = set()
    for i in range(len(lines) - 3):
        a, b = WON.match(lines[i + 1]), WON.match(lines[i + 2])
        if a and b and not WON.match(lines[i]) and not WON.match(lines[i + 3]):
            sec, name = lines[i], lines[i + 3]
            if name in ("더보기", "이벤트 전체보기 +") or len(name) < 3: continue
            key = (name, n(b.group(1)))
            if key in seen: continue
            seen.add(key)
            items.append({"name": name, "list_price": n(a.group(1)), "event_price": n(b.group(1)), "discount_pct": None, "display": "정가+할인가", "unit": "", "vat": "", "conditions": f"[{sec}]", "flags": [], "note": "텍스트 추출"})
    return items

PARSERS = {"beautylounge": parse_beautylounge, "ppeum": parse_ppeum, "maypure": parse_maypure, "velyb": parse_velyb, "lizon": parse_lizon, "uni": parse_uni}

def main():
    fmt, clinic, captured_at, out = sys.argv[1:5]
    ex = json.load(open(out, encoding="utf-8")) if os.path.exists(out) else {"clinic": clinic, "captured_at": captured_at, "sections": []}
    for spec in sys.argv[5:]:
        parts = spec.split("="); section, txt = parts[0], parts[1]
        cap = parts[2] if len(parts) > 2 else os.path.basename(txt).replace(".txt", ".png")
        text = open(txt, encoding="utf-8").read()
        items = PARSERS[fmt](text)
        vat = "별도" if re.search(r"VAT\s*별도|부가세\s*별도", text) else ""
        for it in items: it["vat"] = vat
        ex["sections"] = [s for s in ex["sections"] if s["section"] != section]
        ex["sections"].append({"capture": cap, "section": section, "period": "", "common_conditions": "VAT 별도" if vat else "", "items": items})
        print(f"  {section}: {len(items)}개")
    json.dump(ex, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장:", out, "상품", sum(len(s["items"]) for s in ex["sections"]))

if __name__ == "__main__":
    main()
