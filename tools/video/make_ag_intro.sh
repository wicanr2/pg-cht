#!/usr/bin/env bash
# =============================================================================
# make_ag_intro.sh — 盟軍元帥 (Allied General, SSI 1995) 繁中化推廣片
#
# make_pacgen_intro.sh / make_pg_intro.sh 的兄弟版(同結構:card / slide / endcard
# 函式、docker 合成 --cpus=2 靜態圖+fade 不用 zoompan、設計 token 段、HOST_UID chown、--inner)。
# 產出 ~60s 720p H.264 mp4,分鏡照 pg-cht/docs/video-plan.md「影片 2:盟軍元帥 60 秒」:
#   標題卡 → Splash → 「連烤死的字都翻了」宣示卡 → 戰損表前後對照 →
#   採購面板前後對照 → 介面按鈕前後對照 → 結尾卡
#
# 素材鐵則 (rulebook/93):配樂用「原版遊戲音訊」,不自產、不罐頭。
#   AG(1995)是 CD-Audio 世代作品 — 安裝檔內【沒有】PG 那種 TRACK*.MID;
#   遊戲資料裡真實存在的原版音訊只有:DATA/WELCOME.WAV(18s 開場)、VOICE/*.WAV(單位語音)、
#   MOVIES/MOVIE1..8(過場動畫 AVI,含 PCM 音軌)。
#   本片配樂 = 原版開場過場 MOVIE1 的管弦樂音軌(AlliedGeneral_v1.1.zip 內
#   "Allied General/MOVIES/MOVIE1",取 13s 起的樂段)= 貨真價實的 AG 原版音訊。
#   ⚠ 可能含原版英文新聞式旁白(intro montage 風格),屬 AG 原作;IP 屬 SSI/Mindscape/Ubisoft
#     — 個人/內部可,公開上傳前需評估授權。
#
# 工程實務照 skill game-promo-video-ffmpeg:ffmpeg / ImageMagick 全在 docker
#   (image: pg-video:latest)。靜態圖 + fade,不用 zoompan。--cpus=2 / veryfast / -threads 2。
#
# 用法:
#   bash make_ag_intro.sh              # 主機模式:備素材(含從 zip 抽 MOVIE1)+ docker 合成
#   (內部)bash make_ag_intro.sh --inner # 容器內合成(勿手動呼叫)
# 可覆寫:SS_DIR / AGZIP / OUT / DOCKER_IMG
# =============================================================================
set -eu

W=1280; H=720; FPS=25
DOCKER_IMG="${DOCKER_IMG:-pg-video:latest}"

# ---- 設計 token(AG 專屬:盟軍鋼藍 + 卡其/橄欖綠 + 銀鉻,取自 splash 銀色 logo + 綠底地圖)---
# theme「鋼藍與橄欖」— 與 PG(槍鐵+暗紅+銅)、太平洋片(海藍鎏金)刻意不同色系
BG_DEEP='#0a1310'   # 暗橄欖黑(漸層深端 / 卡片底)
BG_MID='#20342a'    # 橄欖鋼綠(漸層淺端)
STEELB='#5b83a6'    # 盟軍鋼藍(accent / 副標 / 分隔)
KAKI='#bfa860'      # 卡其金(強調)
OLIVE='#7d8a42'     # 橄欖綠
SILVER='#dfe4e8'    # 銀鉻(標題,呼應 ALLIED GENERAL 銀色浮雕 logo)
SILVERSH='#39434a'  # 銀鉻浮雕陰影
CREAM='#ece7d4'     # 字幕米白
IRON='#9aa6a0'      # 鐵灰(年份 / 註記)
FT='/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'
FB='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'

# =============================================================================
# 容器內合成模式
# =============================================================================
if [ "${1:-}" = "--inner" ]; then
  SS="${SS:-/ss}"; MUSIC="${MUSIC:-/music}"; OUTDIR="${OUTDIR:-/out}"
  OUTFILE="${OUTFILE:-AlliedGeneral-promo.mp4}"
  T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT

  [ -f "$FT" ] || FT="$FB"
  [ -f "$FB" ] || { echo "缺 CJK 字型"; exit 1; }

  titlecard(){ # $1 out
    convert -size ${W}x${H} "radial-gradient:#2c4438-${BG_DEEP}" \
      -font "$FT" -gravity center \
      -fill "$SILVERSH" -pointsize 104 -annotate +4-64 '盟軍元帥' \
      -fill "$SILVER"   -pointsize 104 -annotate +0-68 '盟軍元帥' \
      -font "$FB" \
      -fill "$STEELB"  -pointsize 44 -annotate +0+22 'ALLIED GENERAL' \
      -fill "$IRON"    -pointsize 24 -annotate +0+82 '1995   SSI  ·  五星上將戰棋系列續作' \
      -fill "$KAKI"    -pointsize 30 -annotate +0+168 '繁體中文化  ·  連點陣圖裡的字都翻了' \
      -fill "$STEELB"  -stroke "$STEELB" -strokewidth 1 -draw "line 470,470 810,470" \
      "$1"; }

  endcard(){ # $1 out
    convert -size ${W}x${H} "radial-gradient:#2c4438-${BG_DEEP}" \
      -font "$FT" -gravity center \
      -fill "$SILVERSH" -pointsize 60 -annotate +3-137 '連烤進點陣圖的英文，' \
      -fill "$SILVER"   -pointsize 60 -annotate +0-140 '連烤進點陣圖的英文，' \
      -fill "$SILVERSH" -pointsize 60 -annotate +3-57  '都換成了中文。' \
      -fill "$SILVER"   -pointsize 60 -annotate +0-60  '都換成了中文。' \
      -font "$FB" \
      -fill "$KAKI"   -pointsize 25 -annotate +0+36 '戰損表 · 採購面板 · 介面按鈕 — 盟 / 德 / 蘇 三主題全套變體' \
      -fill "$CREAM"  -pointsize 23 -annotate +0+80 'Linux AppImage · Windows portable · 已 ship' \
      -fill "$IRON"   -pointsize 25 -annotate +0+168 'github.com/wicanr2/pg-cht  ·  Allied General  ·  1995 SSI' \
      "$1"; }

  dcard(){ # $1 out  $2 line1  $3 line2  —— 左對齊宣示卡(鋼藍縱條),和置中卡明顯不同
    convert -size ${W}x${H} "radial-gradient:#243a2e-${BG_DEEP}" \
      -fill "$STEELB" -draw "rectangle 150,258 164,462" \
      -font "$FT" -gravity northwest \
      -fill "$SILVER" -pointsize 52 -annotate +198+268 "$2" \
      -fill "$KAKI"   -pointsize 52 -annotate +198+352 "$3" \
      "$1"; }

  slide_fit(){ # $1 out  $2 img  $3 caption  —— fit 置中 + 側幕 + 底部字幕條
    convert -size ${W}x${H} "gradient:${BG_MID}-${BG_DEEP}" "$T/bg.png"
    convert "$2" -resize 1180x600 "$T/sc.png"
    convert "$T/bg.png" "$T/sc.png" -gravity center -geometry +0-18 -composite \
      -fill "#000000aa" -draw "rectangle 0,652 ${W},${H}" \
      -font "$FB" -fill "$CREAM" -gravity south -pointsize 32 -annotate +0+18 "$3" "$1"; }

  slide_frame(){ # $1 out  $2 img  $3 caption  —— 卡其框置中(較小)+ 底部字幕條
    convert -size ${W}x${H} "gradient:${BG_MID}-${BG_DEEP}" "$T/bg.png"
    convert "$2" -resize 1120x520 -bordercolor "$KAKI" -border 3 "$T/sc.png"
    convert "$T/bg.png" "$T/sc.png" -gravity north -geometry +0+30 -composite \
      -fill "#000000aa" -draw "rectangle 0,650 ${W},${H}" \
      -font "$FB" -fill "$KAKI" -gravity south -pointsize 32 -annotate +0+18 "$3" "$1"; }

  kb(){ # $1 png  $2 mp4  $3 secs  —— 靜態 + 淡入淡出(不用 zoompan)
    local fo; fo=$(awk "BEGIN{printf \"%.2f\", $3-0.6}")
    ffmpeg -y -loglevel error -loop 1 -i "$1" -t "$3" -r $FPS \
      -vf "fade=t=in:st=0:d=0.6,fade=t=out:st=$fo:d=0.6,format=yuv420p" \
      -threads 2 -c:v libx264 -preset veryfast -pix_fmt yuv420p "$2"; }

  # ---- 分鏡(總長 8+9+7+11+10+8+9 = 62s)-----------------------------------
  echo "== 卡片 / slide 生成 =="
  titlecard   "$T/p0.png"
  slide_fit   "$T/p1.png" "$SS/ag_splash_zh.png"           '1995 · SSI 續作 · 盟 / 蘇 / 英 三線戰役 — 開場即繁中'
  dcard       "$T/p2.png" '連圖上烤死的英文，' '都一格一格換成了中文。'
  slide_fit   "$T/p3.png" "$SS/ag_losses_before_after.png" '戰損表 · 十八種兵種名 · 連點陣圖裡的字都中文化'
  slide_fit   "$T/p4.png" "$SS/ag_purchase_before_after.png" '採購面板 · 剩餘編制 / 您的聲望 / 總花費'
  slide_frame "$T/p5.png" "$SS/ag_buttons_before_after.png"  '介面按鈕 · 逐一中文化(前 → 後對照)'
  endcard     "$T/p6.png"

  echo "== 影格化 (fade) =="
  kb "$T/p0.png" "$T/v0.mp4" 8
  kb "$T/p1.png" "$T/v1.mp4" 9
  kb "$T/p2.png" "$T/v2.mp4" 7
  kb "$T/p3.png" "$T/v3.mp4" 11
  kb "$T/p4.png" "$T/v4.mp4" 10
  kb "$T/p5.png" "$T/v5.mp4" 8
  kb "$T/p6.png" "$T/v6.mp4" 9

  echo "== concat =="
  : > "$T/list.txt"
  for v in v0 v1 v2 v3 v4 v5 v6; do echo "file '$T/$v.mp4'" >> "$T/list.txt"; done
  ffmpeg -y -loglevel error -f concat -safe 0 -i "$T/list.txt" \
    -threads 2 -c:v libx264 -preset veryfast -pix_fmt yuv420p "$T/silent.mp4"

  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$T/silent.mp4")
  need=$(awk "BEGIN{printf \"%.0f\", $DUR+2}")
  echo "== 抽原版過場配樂 MOVIE1 音軌 (13s 起,共 ${need}s) =="
  ffmpeg -y -loglevel error -ss 13 -i "$MUSIC/MOVIE1" -vn -t "$need" -ac 2 -ar 44100 "$T/bgm.wav"

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
# 主機模式:備素材(從 zip 抽 MOVIE1)+ docker 合成
# =============================================================================
SCRIPT="$(readlink -f "$0")"
VIDEO_DIR="$(dirname "$SCRIPT")"
REPO="$(cd "$VIDEO_DIR/../.." && pwd)"     # pg-cht
PGROOT="$(cd "$REPO/.." && pwd)"           # Panzer_General

SS_DIR="${SS_DIR:-$REPO/docs/screenshots}"
AGZIP="${AGZIP:-$PGROOT/AlliedGeneral_v1.1.zip}"
OUT="${OUT:-$PGROOT/dist-all/AlliedGeneral-promo.mp4}"
OUT_DIR="$(dirname "$OUT")"; OUT_FILE="$(basename "$OUT")"

# 前置檢查
for f in ag_splash_zh.png ag_losses_before_after.png ag_purchase_before_after.png ag_buttons_before_after.png; do
  [ -f "$SS_DIR/$f" ] || { echo "缺截圖 $SS_DIR/$f"; exit 1; }
done
[ -f "$AGZIP" ] || { echo "缺原版 AG 安裝檔(取配樂用)$AGZIP"; exit 1; }

# 從原版 zip 抽 MOVIE1(過場動畫,取其原版管弦樂音軌當配樂)
MUSIC_TMP="$(mktemp -d)"
echo "== 從 $AGZIP 抽 Allied General/MOVIES/MOVIE1 =="
unzip -o -j "$AGZIP" 'Allied General/MOVIES/MOVIE1' -d "$MUSIC_TMP" >/dev/null 2>&1 \
  || unzip -o -j "$AGZIP" '*MOVIES/MOVIE1' -d "$MUSIC_TMP" >/dev/null 2>&1
[ -f "$MUSIC_TMP/MOVIE1" ] || { echo "抽 MOVIE1 失敗"; rm -rf "$MUSIC_TMP"; exit 1; }

# docker image
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
  -e SS=/ss -e MUSIC=/music -e OUTDIR=/out -e OUTFILE="$OUT_FILE" \
  -e HOST_UID="$(id -u)" -e HOST_GID="$(id -g)" \
  -v "$SS_DIR":/ss:ro \
  -v "$MUSIC_TMP":/music:ro \
  -v "$OUT_DIR":/out \
  -v "$SCRIPT":/work/make.sh:ro \
  "$DOCKER_IMG" bash /work/make.sh --inner

rm -rf "$MUSIC_TMP"

# 驗證
echo ""
echo "== ffprobe 驗證 =="
ffprobe -hide_banner "$OUT" 2>&1 | grep -E "Duration|Stream #" || true
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null)
SZ=$(du -h "$OUT" | cut -f1)
echo ""
echo "OK: $OUT  (${DUR}s, $SZ)"
