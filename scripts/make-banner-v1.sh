#!/usr/bin/env bash
# 메인 배너 GIF → 웹용 영상(MP4, WebM) + 포스터(JPG) 변환
# 사용법 (프로젝트 루트에서, Git Bash):  bash scripts/make-banner.sh
# 입력: ./메인 배너 활용.gif (2390x821, 29프레임, 10fps)
# 출력: kkeut_seo_site/assets/banner/{main.mp4, main.webm, poster.jpg}
set -euo pipefail
cd "$(dirname "$0")/.."

SRC="메인 배너 활용.gif"
OUT="kkeut_seo_site/assets/banner"
W=1920   # 출력 폭. 높이는 비율(2390:821)대로 계산 후 짝수로 맞춤(H.264 요구사항)
mkdir -p "$OUT"

# 공통 영상 필터: 10fps 유지, 폭 1920, 높이 자동(짝수)
VF="fps=10,scale=${W}:-2:flags=lanczos"

# 1) MP4 (H.264, 무음, 모바일 호환 yuv420p, 빠른 시작을 위해 moov 앞으로)
ffmpeg -y -loglevel error -i "$SRC" -an -vf "$VF" \
  -c:v libx264 -profile:v high -level 4.0 -pix_fmt yuv420p -crf 23 -preset slow \
  -movflags +faststart "$OUT/main.mp4"

# 2) WebM (VP9, 무음)
ffmpeg -y -loglevel error -i "$SRC" -an -vf "$VF" \
  -c:v libvpx-vp9 -pix_fmt yuv420p -b:v 0 -crf 33 -row-mt 1 "$OUT/main.webm"

# 3) 포스터 = 첫 프레임 JPG (품질 80)
ffmpeg -y -loglevel error -i "$SRC" -vframes 1 -vf "scale=${W}:-2:flags=lanczos" \
  -q:v 4 "$OUT/poster.jpg"

echo "생성 결과:"
ls -l "$OUT" | awk 'NR>1{printf "  %-12s %8.0f KB\n", $9, $5/1024}'
