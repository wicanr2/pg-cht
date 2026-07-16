#!/usr/bin/env bash
# =============================================================================
# make_pacgen_intro.sh — 太平洋元帥 (Pacific General, SSI 1997) 繁中化推廣片
#
# 產出 ~45s 720p H.264 mp4,分鏡照 pg-cht/docs/video-plan.md「影片 3」:
#   開場卡 → Splash 主選單 → 選劇本 → 劇本簡報 → 戰報/天氣 → 結尾卡
#
# 素材鐵則 (rulebook/93):配樂一律用「原版遊戲音訊」,不自產、不罐頭。
#   本片配樂 = stream/10.MUS(遊戲標題曲;PACGEN.EXE 硬編 "%s10.mus" 於
#   "DJ - Repeat playing title theme" 旁,gameplay 音樂才用泛用 "%d.mus")。
#   .MUS = 無檔頭 raw PCM,s16le / 22050Hz / stereo(取樣率見 MEL/SMK 檔頭 0x5622)。
#
# 工程實務照 skill game-promo-video-ffmpeg:
#   - ffmpeg / ImageMagick 全在 docker(image: pacgen-video:latest),不污染系統。
#   - 靜態圖 + fade,不用 zoompan(避免幀數爆炸)。--cpus=2 / -preset veryfast / -threads 2。
#
# 用法:
#   bash make_pacgen_intro.sh              # 主機模式:備素材 + 起 docker 合成
#   (內部)bash make_pacgen_intro.sh --inner  # 容器內合成(勿手動呼叫)
#
# 可用環境變數覆寫:STREAM_DIR / OUT / DOCKER_IMG
# 有界:全前景、固定秒數、無 sentinel、不開 GUI viewer。
# =============================================================================
set -eu

W=1280; H=720; FPS=25
DOCKER_IMG="${DOCKER_IMG:-pacgen-video:latest}"

# ---- 設計 token(換片只改這段;取自遊戲 logo 鎏金 + 太平洋海藍)-------------
BG_DEEP='#08182e'   # 深海夜藍(漸層深端 / 卡片底)
BG_LITE='#1a3a5a'   # 海洋藍(漸層淺端)
GOLD='#f0c060'      # PACIFIC GENERAL logo 金
GOLDSH='#8a6a1e'    # 金字浮雕陰影
CREAM='#f2ead2'     # 字幕米白
WHITE='#f0f0f0'
STEEL='#a0c0e0'     # 鋼藍副標
FT='/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'    # 標題(粗黑,配軍事硬派)
FB='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'     # 字幕 / 內文

# =============================================================================
# 容器內合成模式
# =============================================================================
if [ "${1:-}" = "--inner" ]; then
  SHOT="${SHOT:-/shots}"; STREAM="${STREAM:-/stream}"; OUTDIR="${OUTDIR:-/out}"
  OUTFILE="${OUTFILE:-PacificGeneral-promo.mp4}"
  T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT

  # 字型存在性檢查(skill 雷 #5)
  [ -f "$FT" ] || FT="$FB"
  [ -f "$FB" ] || { echo "缺 CJK 字型"; exit 1; }

  # ---- 版面函式 -------------------------------------------------------------
  titlecard(){ # $1 out
    convert -size ${W}x${H} "radial-gradient:#16375e-${BG_DEEP}" \
      -font "$FT" -gravity center \
      -fill "$GOLDSH" -pointsize 96 -annotate +4-66 '太平洋元帥' \
      -fill "$GOLD"   -pointsize 96 -annotate +0-70 '太平洋元帥' \
      -font "$FB" \
      -fill "$WHITE"  -pointsize 40 -annotate +0+18 'PACIFIC GENERAL' \
      -fill "$STEEL"  -pointsize 24 -annotate +0+78 '1997   SSI / Mindscape  ·  從未中文化過' \
      -fill "$GOLD"   -pointsize 30 -annotate +0+165 '繁體中文化  ·  29 年後的補完' \
      "$1"; }

  endcard(){ # $1 out
    convert -size ${W}x${H} "radial-gradient:#16375e-${BG_DEEP}" \
      -font "$FT" -gravity center \
      -fill "$GOLDSH" -pointsize 62 -annotate +3-137 '他說沒有中文版。' \
      -fill "$GOLD"   -pointsize 62 -annotate +0-140 '他說沒有中文版。' \
      -fill "$GOLDSH" -pointsize 62 -annotate +3-57  '現在有了。' \
      -fill "$GOLD"   -pointsize 62 -annotate +0-60  '現在有了。' \
      -font "$FB" \
      -fill "$WHITE"  -pointsize 26 -annotate +0+34 '33 個劇本全繁中 · 硫磺島 · 中途島 · 瓜達康納爾 · 雷伊泰灣' \
      -fill "$CREAM"  -pointsize 23 -annotate +0+80 'Linux AppImage + Windows portable · 已 ship' \
      -fill "$STEEL"  -pointsize 26 -annotate +0+165 'github.com/wicanr2/pg-cht  ·  pacgen  ·  v0.2' \
      "$1"; }

  slide_frame(){ # $1 out  $2 screenshot  $3 caption  —— 金框置中 + 底部字幕條
    convert -size ${W}x${H} "gradient:${BG_LITE}-${BG_DEEP}" "$T/bg.png"
    convert "$2" -resize x600 -bordercolor "$GOLD" -border 3 "$T/sc.png"
    convert "$T/bg.png" "$T/sc.png" -gravity north -geometry +0+16 -composite \
      -fill "#00000099" -draw "rectangle 0,652 ${W},${H}" \
      -font "$FB" -fill "$CREAM" -gravity south -pointsize 32 -annotate +0+20 "$3" "$1"; }

  slide_full(){ # $1 out  $2 screenshot  $3 caption  —— 貼齊高度 + 海藍側幕 + 下三分之一字幕
    convert -size ${W}x${H} "gradient:${BG_DEEP}-#040a14" "$T/bg.png"
    convert "$2" -resize ${W}x${H} "$T/sc.png"
    convert "$T/bg.png" "$T/sc.png" -gravity center -composite \
      -fill "#000000aa" -draw "rectangle 0,650 ${W},${H}" \
      -font "$FB" -fill "$GOLD" -gravity south -pointsize 32 -annotate +0+20 "$3" "$1"; }

  kb(){ # $1 png  $2 mp4  $3 secs  —— 靜態 + 淡入淡出(不用 zoompan!skill 雷 #1)
    local fo; fo=$(awk "BEGIN{printf \"%.2f\", $3-0.6}")
    ffmpeg -y -loglevel error -loop 1 -i "$1" -t "$3" -r $FPS \
      -vf "fade=t=in:st=0:d=0.6,fade=t=out:st=$fo:d=0.6,format=yuv420p" \
      -threads 2 -c:v libx264 -preset veryfast -pix_fmt yuv420p "$2"; }

  # ---- 分鏡(照 video-plan 影片 3;總長 6+8+8+8+6+9 = 45s)-------------------
  echo "== 卡片 / slide 生成 =="
  titlecard   "$T/p0.png"
  slide_full  "$T/p1.png" "$SHOT/menu.png"     '沙灘 · 火砲 · 戰艦 — 1997 年 SSI 的太平洋戰棋'
  slide_frame "$T/p2.png" "$SHOT/scenario.png" '33 個劇本 · 劇本名全繁體中文'
  slide_frame "$T/p3.png" "$SHOT/briefing.png" '每個劇本 · 原創繁中史實簡報'
  slide_full  "$T/p4.png" "$SHOT/weather.png"  '回合畫面已中文化'
  endcard     "$T/p5.png"

  echo "== 影格化 (fade) =="
  kb "$T/p0.png" "$T/v0.mp4" 6
  kb "$T/p1.png" "$T/v1.mp4" 8
  kb "$T/p2.png" "$T/v2.mp4" 8
  kb "$T/p3.png" "$T/v3.mp4" 8
  kb "$T/p4.png" "$T/v4.mp4" 6
  kb "$T/p5.png" "$T/v5.mp4" 9

  echo "== concat =="
  : > "$T/list.txt"
  for v in v0 v1 v2 v3 v4 v5; do echo "file '$T/$v.mp4'" >> "$T/list.txt"; done
  ffmpeg -y -loglevel error -f concat -safe 0 -i "$T/list.txt" \
    -threads 2 -c:v libx264 -preset veryfast -pix_fmt yuv420p "$T/silent.mp4"

  echo "== 抽原版標題曲 10.MUS (raw PCM s16le/22050/stereo) =="
  ffmpeg -y -loglevel error -f s16le -ar 22050 -ac 2 -i "$STREAM/10.MUS" -t 46 "$T/title.wav"

  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$T/silent.mp4")
  FO=$(awk "BEGIN{printf \"%.2f\", $DUR-3}")
  echo "== 鋪配樂 + 輸出 (dur=${DUR}s) =="
  mkdir -p "$OUTDIR"
  ffmpeg -y -loglevel error -i "$T/silent.mp4" -i "$T/title.wav" \
    -filter_complex "[1:a]atrim=0:$DUR,afade=t=in:st=0:d=1.5,afade=t=out:st=$FO:d=3,aformat=sample_rates=44100:channel_layouts=stereo[a]" \
    -map 0:v -map "[a]" -threads 2 \
    -c:v libx264 -preset veryfast -pix_fmt yuv420p -c:a aac -b:a 192k \
    -shortest -movflags +faststart "$OUTDIR/$OUTFILE"

  # 把 root 產出的檔權限交還給呼叫者(docker 內為 root)
  [ -n "${HOST_UID:-}" ] && chown "${HOST_UID}:${HOST_GID:-$HOST_UID}" "$OUTDIR/$OUTFILE" 2>/dev/null || true

  echo "OK inner -> $OUTDIR/$OUTFILE"
  exit 0
fi

# =============================================================================
# 主機模式:備素材 + docker 合成
# =============================================================================
SCRIPT="$(readlink -f "$0")"
VIDEO_DIR="$(dirname "$SCRIPT")"           # pg-cht/tools/video
REPO="$(cd "$VIDEO_DIR/../.." && pwd)"     # pg-cht
DOCS="$REPO/pacgen/docs"
PGROOT="$(cd "$REPO/.." && pwd)"           # Panzer_General

STREAM_DIR="${STREAM_DIR:-$PGROOT/PacificGeneral_CHT_v0.2_20260709-portable/Pacific General CHT/stream}"
OUT="${OUT:-$PGROOT/dist-all/PacificGeneral-promo.mp4}"
OUT_DIR="$(dirname "$OUT")"; OUT_FILE="$(basename "$OUT")"

# 四張 hero 截圖(CJK 已修好)
declare -A SRC=(
  [menu.png]="$DOCS/2byte-hook-SUCCESS-menu.png"
  [scenario.png]="$DOCS/screenshots/2byte-whitebg-FIXED-scenario.png"
  [briefing.png]="$DOCS/screenshots/2byte-whitebg-FIXED-wordwrap-briefing.png"
  [weather.png]="$DOCS/screenshots/2byte-whitebg-FIXED-weather.png"
)

# 前置檢查
[ -f "$STREAM_DIR/10.MUS" ] || { echo "缺原版配樂 $STREAM_DIR/10.MUS"; exit 1; }
SHOTS_TMP="$(mktemp -d)"
for k in "${!SRC[@]}"; do
  [ -f "${SRC[$k]}" ] || { echo "缺截圖 ${SRC[$k]}"; rm -rf "$SHOTS_TMP"; exit 1; }
  cp "${SRC[$k]}" "$SHOTS_TMP/$k"
done

# docker image(不存在就建一次)
if ! docker image inspect "$DOCKER_IMG" >/dev/null 2>&1; then
  echo "== 建 docker image $DOCKER_IMG(一次性)=="
  docker rm -f pgvb_build 2>/dev/null || true
  docker run --cpus=2 --name pgvb_build debian:12-slim bash -c \
    'apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends ffmpeg imagemagick fonts-noto-cjk fonts-noto-cjk-extra >/dev/null 2>&1'
  docker commit pgvb_build "$DOCKER_IMG" >/dev/null
  docker rm pgvb_build >/dev/null
fi

mkdir -p "$OUT_DIR"
echo "== docker 合成 (--cpus=2) =="
docker run --rm --cpus=2 \
  -e SHOT=/shots -e STREAM=/stream -e OUTDIR=/out -e OUTFILE="$OUT_FILE" \
  -e HOST_UID="$(id -u)" -e HOST_GID="$(id -g)" \
  -v "$SHOTS_TMP":/shots:ro \
  -v "$STREAM_DIR":/stream:ro \
  -v "$OUT_DIR":/out \
  -v "$SCRIPT":/work/make.sh:ro \
  "$DOCKER_IMG" bash /work/make.sh --inner

rm -rf "$SHOTS_TMP"

# 驗證
echo ""
echo "== ffprobe 驗證 =="
ffprobe -hide_banner "$OUT" 2>&1 | grep -E "Duration|Stream #" || true
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null)
SZ=$(du -h "$OUT" | cut -f1)
echo ""
echo "OK: $OUT  (${DUR}s, $SZ)"
