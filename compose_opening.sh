#!/usr/bin/env bash
# Compose the promo: real-footage hook (verticalised 16:9) + generated animation body.
#   usage: ./compose_opening.sh [source.mp4]
# Requires build/anim_body.mp4 (animation-only master) and build/captions_open.ass.
set -euo pipefail
FF="tools/_ff/ffmpeg-9.0.2-essentials_build/bin/ffmpeg.exe"
SRC="${1:-C:/Users/acer/Downloads/Phone_on_road_to_terminal_ce2d537e.mp4}"

OPENER_LEN=3.6   # seconds of the source used as the hook
BODY_SKIP=3.0    # skip the synthetic hook in the animation master
TOTAL=45.0

"$FF" -y -hide_banner -loglevel error \
  -i "$SRC" -ss "$BODY_SKIP" -i build/anim_body.mp4 \
  -f lavfi -i anullsrc=r=44100:cl=stereo \
  -filter_complex "[0:v]trim=0:${OPENER_LEN},setpts=PTS-STARTPTS,fps=30,split=2[a][b];\
[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=45,eq=brightness=-0.10:saturation=0.85[bg];\
[b]scale=1040:-2,pad=1048:593:4:4:color=0x223040[fg];\
[bg][fg]overlay=16:620,subtitles=build/captions_open.ass:fontsdir=fonts,fade=t=in:st=0:d=0.35[open];\
[1:v]fps=30,scale=1080:1920,setsar=1[body];\
[open][body]concat=n=2:v=1,format=yuv420p[v]" \
  -map "[v]" -map 2:a -shortest -t "$TOTAL" \
  -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -r 30 -c:a aac -b:a 128k \
  t3code_promo_45s.mp4
echo "ok -> t3code_promo_45s.mp4 (${TOTAL}s)"
