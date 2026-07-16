#!/usr/bin/env bash
# =============================================================================
# make_pg_intro.sh — 裝甲元帥 (Panzer General, SSI 1994) 繁中化推廣片
#
# make_pacgen_intro.sh 的兄弟版(同結構:titlecard / slide / endcard 函式、
# docker 合成 --cpus=2 靜態圖+fade 不用 zoompan、設計 token 段、HOST_UID chown、--inner)。
# 產出 ~60s 720p H.264 mp4,分鏡照 pg-cht/docs/video-plan.md「影片 1:裝甲元帥 60 秒」:
#   標題卡 → 戰役選擇 → 繁中史實簡報 → 劇本列表 → 六角格戰場 → 兵種特寫 → 結尾卡
#
# 素材鐵則 (rulebook/93):配樂用「原版遊戲音訊」,不自產、不罐頭。
#   本片配樂 = MUSIC/TRACK0.MID(PG Win95 標準 MIDI 標題/主選單曲),
#   離線用 fluidsynth + FluidR3_GM.sf2 算成 wav(見 game-promo-video-ffmpeg 的 MIDI 段)。
#   IP:MIDI 旋律版權屬 SSI/Mindscape/Ubisoft — 個人/內部可,公開上傳前需評估授權。
#
# 工程實務照 skill game-promo-video-ffmpeg:
#   ffmpeg / ImageMagick / fluidsynth 全在 docker(image: pg-video:latest)。
#   靜態圖 + fade,不用 zoompan。--cpus=2 / -preset veryfast / -threads 2。
#
# 用法:
#   bash make_pg_intro.sh              # 主機模式:備素材 + 起 docker 合成
#   (內部)bash make_pg_intro.sh --inner # 容器內合成(勿手動呼叫)
# 可覆寫:MUS_DIR / SS_DIR / OUT / DOCKER_IMG
# =============================================================================
set -eu

W=1280; H=720; FPS=25
DOCKER_IMG="${DOCKER_IMG:-pg-video:latest}"

# ---- 設計 token(PG 專屬:鋼鐵灰 + 德軍暗紅/黑鐵漸層 + 銅框,硬派軍事感)----------
# theme「鋼鐵與暗紅」— 與太平洋片(海藍鎏金)刻意不同色系
BG_DEEP='#0a0c0e'   # 黑鐵(漸層深端 / 卡片底)
BG_MID='#2b333a'    # 槍鐵灰(漸層淺端)
BLOOD='#9c2117'     # 德軍暗紅(accent / 副標)
BLOODSH='#4a0f0a'   # 暗紅浮雕陰影
BRASS='#c69a3a'     # 遊戲 UI 銅金(標題 / 框線)
BRASSSH='#6b4e15'   # 銅金浮雕陰影
STEEL='#d7dde3'     # 鋼白(英文副標)
IRON='#93a0aa'      # 鐵灰(年份 / 註記)
CREAM='#ece3cc'     # 字幕米白
FT='/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'    # 標題(粗黑,配硬派)
FB='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'     # 字幕 / 內文

# =============================================================================
# 容器內合成模式
# =============================================================================
if [ "${1:-}" = "--inner" ]; then
  SS="${SS:-/ss}"; MID="${MID:-/mid}"; OUTDIR="${OUTDIR:-/out}"
  OUTFILE="${OUTFILE:-PanzerGeneral-promo.mp4}"
  T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT

  [ -f "$FT" ] || FT="$FB"
  [ -f "$FB" ] || { echo "缺 CJK 字型"; exit 1; }
  SF=/usr/share/sounds/sf2/FluidR3_GM.sf2
  [ -f "$SF" ] || SF=/usr/share/sounds/sf2/TimGM6mb.sf2

  # ---- 卡片 -----------------------------------------------------------------
  titlecard(){ # $1 out
    convert -size ${W}x${H} "radial-gradient:#39424a-${BG_DEEP}" \
      -font "$FT" -gravity center \
      -fill "$BLOODSH" -pointsize 104 -annotate +4-64 '裝甲元帥' \
      -fill "$BRASS"   -pointsize 104 -annotate +0-68 '裝甲元帥' \
      -font "$FB" \
      -fill "$STEEL"   -pointsize 44 -annotate +0+22 'PANZER GENERAL' \
      -fill "$IRON"    -pointsize 24 -annotate +0+82 '1994   SSI  ·  五星上將戰棋系列元祖' \
      -fill "$BLOOD"   -pointsize 30 -annotate +0+168 '繁體中文化  ·  三十年後的補完' \
      -fill "$BRASS"   -stroke "$BRASS" -strokewidth 1 -draw "line 470,470 810,470" \
      "$1"; }

  endcard(){ # $1 out
    convert -size ${W}x${H} "radial-gradient:#39424a-${BG_DEEP}" \
      -font "$FT" -gravity center \
      -fill "$BLOODSH" -pointsize 60 -annotate +3-137 '五星上將系列的元祖，' \
      -fill "$BRASS"   -pointsize 60 -annotate +0-140 '五星上將系列的元祖，' \
      -fill "$BLOODSH" -pointsize 60 -annotate +3-57  '終於說中文了。' \
      -fill "$BRASS"   -pointsize 60 -annotate +0-60  '終於說中文了。' \
      -font "$FB" \
      -fill "$STEEL"  -pointsize 25 -annotate +0+36 '波蘭 · 巴巴羅薩 · 阿拉曼 · 市場花園 · 柏林 — 劇本名全繁中' \
      -fill "$CREAM"  -pointsize 23 -annotate +0+80 'Linux AppImage · Windows portable · 已 ship' \
      -fill "$IRON"   -pointsize 25 -annotate +0+168 'github.com/wicanr2/pg-cht  ·  Panzer General  ·  1994 SSI' \
      "$1"; }

  # ---- slide 版面(4:3 截圖 → 保持比例,不拉伸變形)-------------------------
  slide_fit(){ # $1 out  $2 img  $3 caption  —— 貼齊(fit)置中 + 槽鐵側幕 + 底部字幕條
    convert -size ${W}x${H} "gradient:${BG_MID}-${BG_DEEP}" "$T/bg.png"
    convert "$2" -resize 1180x600 "$T/sc.png"
    convert "$T/bg.png" "$T/sc.png" -gravity center -geometry +0-18 -composite \
      -fill "#000000aa" -draw "rectangle 0,652 ${W},${H}" \
      -font "$FB" -fill "$CREAM" -gravity south -pointsize 32 -annotate +0+18 "$3" "$1"; }

  slide_frame(){ # $1 out  $2 img  $3 caption  —— 銅框置中(較小)+ 底部字幕條
    convert -size ${W}x${H} "gradient:${BG_MID}-${BG_DEEP}" "$T/bg.png"
    convert "$2" -resize 1120x536 -bordercolor "$BRASS" -border 3 "$T/sc.png"
    convert "$T/bg.png" "$T/sc.png" -gravity north -geometry +0+28 -composite \
      -fill "#000000aa" -draw "rectangle 0,650 ${W},${H}" \
      -font "$FB" -fill "$BRASS" -gravity south -pointsize 32 -annotate +0+18 "$3" "$1"; }

  kb(){ # $1 png  $2 mp4  $3 secs  —— 靜態 + 淡入淡出(不用 zoompan)
    local fo; fo=$(awk "BEGIN{printf \"%.2f\", $3-0.6}")
    ffmpeg -y -loglevel error -loop 1 -i "$1" -t "$3" -r $FPS \
      -vf "fade=t=in:st=0:d=0.6,fade=t=out:st=$fo:d=0.6,format=yuv420p" \
      -threads 2 -c:v libx264 -preset veryfast -pix_fmt yuv420p "$2"; }

  # ---- 從全圖裁「重點特寫」(加變化、湊足 60s)------------------------------
  echo "== 裁特寫 =="
  convert "$SS/00_screenshot.png" -crop 520x80+170+186 +repage "$T/crop_brief.png"
  convert "$SS/02_screenshot.png" -crop 560x430+270+270 +repage "$T/crop_battle.png"

  # ---- 分鏡(總長 7+9+9+10+9+9+8 = 61s)------------------------------------
  echo "== 卡片 / slide 生成 =="
  titlecard   "$T/p0.png"
  slide_fit   "$T/p1.png" "$SS/00_screenshot.png" '1994 · SSI · 五星上將系列的元祖 — 戰役選擇全繁中'
  slide_fit   "$T/p2.png" "$T/crop_brief.png"     '五大戰役 · 每個劇本 · 原創繁中史實簡報'
  slide_fit   "$T/p3.png" "$SS/01_screenshot.png" '劇本名全繁體中文 · 海獅 · 阿拉曼 · 市場花園 · 巴巴羅薩'
  slide_fit   "$T/p4.png" "$SS/02_screenshot.png" '六角格戰場 · 回合 / 名聲 / 天氣 / 補給全中文'
  slide_frame "$T/p5.png" "$T/crop_battle.png"    '中文兵種 · 步兵 / 戰車 / 火砲 / 俯衝轟炸機'
  endcard     "$T/p6.png"

  echo "== 影格化 (fade) =="
  kb "$T/p0.png" "$T/v0.mp4" 7
  kb "$T/p1.png" "$T/v1.mp4" 9
  kb "$T/p2.png" "$T/v2.mp4" 9
  kb "$T/p3.png" "$T/v3.mp4" 10
  kb "$T/p4.png" "$T/v4.mp4" 9
  kb "$T/p5.png" "$T/v5.mp4" 9
  kb "$T/p6.png" "$T/v6.mp4" 8

  echo "== concat =="
  : > "$T/list.txt"
  for v in v0 v1 v2 v3 v4 v5 v6; do echo "file '$T/$v.mp4'" >> "$T/list.txt"; done
  ffmpeg -y -loglevel error -f concat -safe 0 -i "$T/list.txt" \
    -threads 2 -c:v libx264 -preset veryfast -pix_fmt yuv420p "$T/silent.mp4"

  echo "== 抽原版標題曲 TRACK0.MID (fluidsynth + FluidR3_GM) =="
  fluidsynth -ni -g 0.5 -F "$T/bgm.wav" "$SF" "$MID/TRACK0.MID" >/dev/null 2>&1

  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$T/silent.mp4")
  FO=$(awk "BEGIN{printf \"%.2f\", $DUR-3}")
  echo "== 鋪配樂 + 輸出 (dur=${DUR}s) =="
  mkdir -p "$OUTDIR"
  ffmpeg -y -loglevel error -i "$T/silent.mp4" -i "$T/bgm.wav" \
    -filter_complex "[1:a]atrim=0:$DUR,afade=t=in:st=0:d=1.5,afade=t=out:st=$FO:d=3,aformat=sample_rates=44100:channel_layouts=stereo[a]" \
    -map 0:v -map "[a]" -threads 2 \
    -c:v libx264 -preset veryfast -pix_fmt yuv420p -c:a aac -b:a 192k \
    -shortest -movflags +faststart "$OUTDIR/$OUTFILE"

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
PGROOT="$(cd "$REPO/.." && pwd)"           # Panzer_General

SS_DIR="${SS_DIR:-$REPO/docs/screenshots}"
MUS_DIR="${MUS_DIR:-$PGROOT/PG-cht-1.2_原始裝備_20260702-wine/MUSIC}"
OUT="${OUT:-$PGROOT/dist-all/PanzerGeneral-promo.mp4}"
OUT_DIR="$(dirname "$OUT")"; OUT_FILE="$(basename "$OUT")"

# 前置檢查
for f in 00_screenshot.png 01_screenshot.png 02_screenshot.png; do
  [ -f "$SS_DIR/$f" ] || { echo "缺截圖 $SS_DIR/$f"; exit 1; }
done
[ -f "$MUS_DIR/TRACK0.MID" ] || { echo "缺原版配樂 $MUS_DIR/TRACK0.MID"; exit 1; }

# docker image(不存在就建一次:pacgen-video + fluidsynth + FluidR3)
if ! docker image inspect "$DOCKER_IMG" >/dev/null 2>&1; then
  echo "== 建 docker image $DOCKER_IMG(一次性)=="
  BASE=pacgen-video:latest
  docker image inspect "$BASE" >/dev/null 2>&1 || BASE=debian:12-slim
  docker rm -f pgv_build 2>/dev/null || true
  docker run --cpus=2 --name pgv_build "$BASE" bash -c \
    'apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends ffmpeg imagemagick fonts-noto-cjk fonts-noto-cjk-extra fluidsynth fluid-soundfont-gm >/dev/null 2>&1'
  docker commit pgv_build "$DOCKER_IMG" >/dev/null
  docker rm pgv_build >/dev/null
fi

mkdir -p "$OUT_DIR"
echo "== docker 合成 (--cpus=2) =="
docker run --rm --cpus=2 \
  -e SS=/ss -e MID=/mid -e OUTDIR=/out -e OUTFILE="$OUT_FILE" \
  -e HOST_UID="$(id -u)" -e HOST_GID="$(id -g)" \
  -v "$SS_DIR":/ss:ro \
  -v "$MUS_DIR":/mid:ro \
  -v "$OUT_DIR":/out \
  -v "$SCRIPT":/work/make.sh:ro \
  "$DOCKER_IMG" bash /work/make.sh --inner

# 驗證
echo ""
echo "== ffprobe 驗證 =="
ffprobe -hide_banner "$OUT" 2>&1 | grep -E "Duration|Stream #" || true
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null)
SZ=$(du -h "$OUT" | cut -f1)
echo ""
echo "OK: $OUT  (${DUR}s, $SZ)"
