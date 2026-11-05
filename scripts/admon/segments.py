# -*- coding: utf-8 -*-
"""캡처 PNG(분할본 포함)를 읽기용 조각으로 자른다 — Claude 가 가격을 읽을 때 쓰는 미리보기.
사용법: python -X utf8 -I scripts/admon/segments.py <captures/2026-11/병원명> <out_dir> [--step 2000] [--win 2200] [--width 900] [--only 02,04]
- 같은 캡처의 _p1,_p2… 분할본은 세로로 이어 붙인 뒤 자른다.
- 조각 이름: <캡처번호>_<순번>.png (예: 02_03.png). 겹침(win-step)으로 경계에 걸친 가격을 놓치지 않는다.
- meta.json 의 text 파일(.txt)이 있는 캡처는 목록에 'TEXT' 로 표시한다(이미지 대신 텍스트로 추출 가능).
"""
import sys, os, re, json, argparse
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--step", type=int, default=2000); ap.add_argument("--win", type=int, default=2200)
ap.add_argument("--width", type=int, default=900); ap.add_argument("--only", default="")
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
only = set(a.only.split(",")) if a.only else None
meta = json.load(open(os.path.join(a.src, "meta.json"), encoding="utf-8")) if os.path.exists(os.path.join(a.src, "meta.json")) else {"captures": []}
groups = {}
for f in sorted(os.listdir(a.src)):
    if not f.endswith(".png"): continue
    key = re.sub(r"_p\d+\.png$", "", f).replace(".png", "")
    groups.setdefault(key, []).append(f)
total = 0
for key, files in groups.items():
    num = key[:2]
    if only and num not in only: continue
    ims = [Image.open(os.path.join(a.src, f)) for f in files]
    W = ims[0].size[0]; H = sum(i.size[1] for i in ims)
    full = Image.new("RGB", (W, H), "white"); y = 0
    for im in ims: full.paste(im, (0, y)); y += im.size[1]
    n = 0
    for y0 in range(0, H, a.step):
        n += 1; y1 = min(H, y0 + a.win)
        seg = full.crop((0, y0, W, y1)).resize((a.width, int((y1 - y0) * a.width / W)))
        seg.save(os.path.join(a.out, f"{num}_{n:02d}.png"))
    has_txt = any(c.get("text") for c in meta["captures"] if c.get("file", "").startswith(num))
    print(f"{num} {key[3:40]:40s} {H:6d}px → {n:2d}조각 {'TEXT' if has_txt else ''}")
    total += n
print("조각 합계", total, "→", a.out)
