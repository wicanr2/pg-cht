#!/usr/bin/env bash
# 合成 PacGen CHT 40s 宣傳片 (無聲版 v1):
#   opening 卡 (5s) → 實機素材 (20s) → closing 卡 (5s) + 燒中文字幕
#
# 輸入:
#   - /tmp/pacgen_cap2.mp4  實機 20s (capture_pacgen.sh 產)
# 輸出:
#   - dist-all/video/pacgen-cht-intro.mp4
#
# 依賴: imagemagick (convert), ffmpeg
# 有界: 全前景,固定秒數,無 sentinel。

set -u
cd "$(dirname "$0")/../.."
CAP="${CAP:-/tmp/pacgen_cap2.mp4}"
OUT_DIR="dist-all/video"
OUT="$OUT_DIR/pacgen-cht-intro.mp4"
TMP="$(mktemp -d)"
FONT=/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc
W=1280; H=720; FPS=25

[ -f "$CAP" ] || { echo "缺 $CAP,先跑 tools/video/capture_pacgen.sh"; exit 1; }
mkdir -p "$OUT_DIR"

# 色系: 太平洋海洋藍 + 金色副標
GOLD='#f0c060'
WHITE='#f0f0f0'
SUB='#a0c0e0'

echo "== 1/5 opening 卡 =="
convert -size ${W}x${H} \
  gradient:'#0a1e3a-#1a3a5a' \
  -font "$FONT" -gravity center \
  -fill "$GOLD" -pointsize 90 -annotate +0-100 '太平洋元帥' \
  -fill "$WHITE" -pointsize 42 -annotate +0+10 'Pacific General' \
  -fill "$SUB" -pointsize 26 -annotate +0+60 'SSI / Mindscape · 1997' \
  -fill "$GOLD" -pointsize 34 -annotate +0+180 '繁體中文化 v0.2 · 29 年後的補完' \
  "$TMP/opening.png"

echo "== 2/5 closing 卡 =="
convert -size ${W}x${H} \
  gradient:'#0a1e3a-#1a3a5a' \
  -font "$FONT" -gravity center \
  -fill "$GOLD" -pointsize 56 -annotate +0-160 '他說沒有中文版' \
  -fill "$GOLD" -pointsize 56 -annotate +0-90 '現在有了' \
  -fill "$WHITE" -pointsize 28 -annotate +0+30 '33 個劇本繁中: 硫磺島 · 中途島 · 雷伊泰灣 · 瓜達康納爾' \
  -fill "$WHITE" -pointsize 28 -annotate +0+80 'AppImage (Linux) + Windows portable zip 已 ship' \
  -fill "$SUB" -pointsize 30 -annotate +0+180 'github.com/wicanr2/pg-cht/tree/main/pacgen' \
  "$TMP/closing.png"

echo "== 3/5 opening 動畫 (fade in/out 5s) =="
ffmpeg -y -loglevel error -loop 1 -t 5 -i "$TMP/opening.png" \
  -vf "fps=$FPS,format=yuv420p,fade=t=in:st=0:d=0.8,fade=t=out:st=4.2:d=0.8" \
  -c:v libx264 -pix_fmt yuv420p "$TMP/seg_open.mp4"

echo "== 4/5 實機素材 (nearest scale 1.5x + letterbox) =="
# 640x480 素材放大到 960x720 (1.5x nearest, 保留 pixel art),置中 letterbox 到 1280x720
ffmpeg -y -loglevel error -i "$CAP" \
  -vf "scale=960:720:flags=neighbor,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2:color=black,fps=$FPS,format=yuv420p,fade=t=in:st=0:d=0.5,fade=t=out:st=19.3:d=0.7" \
  -an -c:v libx264 -pix_fmt yuv420p "$TMP/seg_cap.mp4"

echo "== 5/5 closing 動畫 (fade in/out 5s) =="
ffmpeg -y -loglevel error -loop 1 -t 5 -i "$TMP/closing.png" \
  -vf "fps=$FPS,format=yuv420p,fade=t=in:st=0:d=0.8,fade=t=out:st=4.2:d=0.8" \
  -c:v libx264 -pix_fmt yuv420p "$TMP/seg_close.mp4"

echo "== concat =="
: > "$TMP/list.txt"
for s in seg_open seg_cap seg_close; do
    echo "file '$TMP/$s.mp4'" >> "$TMP/list.txt"
done
ffmpeg -y -loglevel error -f concat -safe 0 -i "$TMP/list.txt" -c:v libx264 -pix_fmt yuv420p -crf 20 "$TMP/silent.mp4"

# 若有 SRT 就燒進去
SRT="docs/video/pacgen-subtitles.srt"
if [ -f "$SRT" ]; then
    echo "== burn subtitles =="
    ffmpeg -y -loglevel error -i "$TMP/silent.mp4" \
      -vf "subtitles=$SRT:force_style='FontName=Noto Sans CJK TC,FontSize=24,PrimaryColour=&H00f5d020,OutlineColour=&H00000000,Outline=2,MarginV=60'" \
      -c:v libx264 -pix_fmt yuv420p -crf 20 -movflags +faststart "$OUT"
else
    echo "no SRT — output no-subtitle version"
    cp "$TMP/silent.mp4" "$OUT"
fi

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null)
SZ=$(du -h "$OUT" | cut -f1)
echo ""
echo "OK: $OUT (${DUR}s, $SZ)"
rm -rf "$TMP"
