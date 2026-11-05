#!/usr/bin/env bash
# 메인 배너 v2: AI 생성 원본(1080p mp4) → 웹용 1920x660 영상(MP4, WebM) + 포스터(JPG)
# 사용법 (프로젝트 루트, Git Bash):
#   bash scripts/make-banner.sh banner-src/kling_01.mp4 [--loop] [--offset PX] [--fps 24] [--out DIR]
#   --loop      정→역 재생을 이어 붙여 끊김 없는 반복(길이 2배). 시작·끝 프레임이 같은 원본이면 불필요
#   --offset    세로 자르기 위치 보정(px, 1080 기준). 음수=위로, 양수=아래로. 기본 0(가운데)
#   --fps       출력 fps. 기본 24
#   --out       출력 폴더. 기본 kkeut_seo_site/assets/banner (테스트는 다른 폴더로)
# 출력: DIR/{main.mp4, main.webm, poster.jpg}  (목표: MP4 ≤ 3MB, WebM ≤ 2.5MB, 포스터 ≤ 200KB)
# v1(GIF 변환)은 scripts/make-banner-v1.sh 에 보관.
set -euo pipefail
cd "$(dirname "$0")/.."

SRC="${1:?원본 mp4 경로를 주세요}"; shift
LOOP=0; OFFSET=0; FPS=24; OUT="kkeut_seo_site/assets/banner"
while [ $# -gt 0 ]; do
  case "$1" in
    --loop) LOOP=1 ;;
    --offset) OFFSET="$2"; shift ;;
    --fps) FPS="$2"; shift ;;
    --out) OUT="$2"; shift ;;
    *) echo "알 수 없는 옵션: $1" >&2; exit 1 ;;
  esac; shift
done
mkdir -p "$OUT"

W=1920; H=660
# 폭 1920 으로 맞춘 뒤 세로 가운데(±offset) 660 을 자른다. 원본 비율이 16:9 면 위아래 210px 씩 잘림.
VF="scale=${W}:-2:flags=lanczos,crop=${W}:${H}:0:(ih-${H})/2+${OFFSET},fps=${FPS},format=yuv420p"
if [ "$LOOP" = 1 ]; then
  # 정방향 + 역방향(첫 프레임 중복 제거) 이어 붙이기 → 처음과 끝이 같은 그림이 되어 반복 시 튀지 않음
  FILTER="[0:v]${VF},split[a][b];[b]reverse,trim=start_frame=1,setpts=PTS-STARTPTS[r];[a][r]concat=n=2:v=1:a=0[v]"
  MAP=(-filter_complex "$FILTER" -map "[v]")
else
  MAP=(-vf "$VF")
fi

# 1) MP4 (H.264, 무음, 모바일 호환, moov 앞으로)
ffmpeg -y -loglevel error -i "$SRC" -an "${MAP[@]}" \
  -c:v libx264 -profile:v high -level 4.1 -crf 20 -preset slow -movflags +faststart "$OUT/main.mp4"
# 2) WebM (VP9, 무음)
ffmpeg -y -loglevel error -i "$SRC" -an "${MAP[@]}" \
  -c:v libvpx-vp9 -b:v 0 -crf 30 -deadline good -cpu-used 2 -row-mt 1 "$OUT/main.webm"
# 3) 포스터 = 변환된 MP4 의 첫 프레임 (영상과 정확히 같은 자르기)
ffmpeg -y -loglevel error -i "$OUT/main.mp4" -vframes 1 -q:v 3 "$OUT/poster.jpg"
# 포스터가 200KB 를 넘으면 품질을 낮춰 다시 뽑는다
for q in 5 7 9; do
  [ "$(stat -c %s "$OUT/poster.jpg")" -le 204800 ] && break
  ffmpeg -y -loglevel error -i "$OUT/main.mp4" -vframes 1 -q:v "$q" "$OUT/poster.jpg"
done

echo "생성 결과 ($OUT):"
ls -l "$OUT" | awk 'NR>1{printf "  %-12s %8.0f KB\n", $9, $5/1024}'
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,nb_frames -of default=nw=1 "$OUT/main.mp4"
