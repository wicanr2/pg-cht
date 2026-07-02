#!/usr/bin/env bash
# 錄 Pacific General CHT 主選單 + 劇本選單 headless 影片
# Xvfb + wine + xdotool 送鍵 + ffmpeg x11grab
# 有界:固定秒數後 kill,無 sentinel,不開 GUI viewer

set -u
GAME_DIR="${GAME_DIR:-$HOME/.local/share/PacificGeneral/game}"
WINE="${WINE:-/opt/wine-stable/bin/wine}"
WINEPREFIX="${WINEPREFIX:-$HOME/.wine-pacgen-test}"
SECS="${1:-25}"
DISP=:97
WH=640x480
OUT="${OUT:-/tmp/pacgen_capture.mp4}"

[ -f "$GAME_DIR/PACGEN.EXE" ] || { echo "缺 $GAME_DIR/PACGEN.EXE"; exit 1; }
[ -f "$WINEPREFIX/system.reg" ] || { echo "WINEPREFIX 未初始化: $WINEPREFIX"; exit 1; }

# 清 X 殘留
pkill -9 -f "Xvfb $DISP" 2>/dev/null
sleep 1

# Xvfb
Xvfb $DISP -screen 0 ${WH}x24 -nolisten tcp -nolisten unix >/tmp/xvfb_pacgen.log 2>&1 &
XP=$!
sleep 2

# wine + PACGEN
export WINEPREFIX WINEARCH=win32
export WINEDLLOVERRIDES="mscoree,mshtml="
export WINEDEBUG="-all"
export DISPLAY=$DISP
( cd "$GAME_DIR" && "$WINE" explorer /desktop=PACGEN,640x480 ./PACGEN.EXE ) >/tmp/wine_pacgen.log 2>&1 &
SP=$!

# 等視窗出現 (最多 20s)
for i in $(seq 1 20); do
    W=$(DISPLAY=$DISP xdotool search --name "Pacific General" 2>/dev/null | head -1)
    [ -n "$W" ] && break
    sleep 1
done
[ -z "$W" ] && { echo "遊戲視窗沒出現 in 20s"; kill $XP $SP 2>/dev/null; exit 2; }

# 背景驅動:DDraw exclusive 不吃 xdotool key --window,改用 mousemove+click
# PacGen 主選單 8 按鈕約在 y=250-420, x=250(左), x=380(右)
( C(){ DISPLAY=$DISP xdotool mousemove --sync $1 $2 click 1 2>/dev/null; sleep 0.5; }
  sleep 4       # 4s 停主選單 (rec 0-4s)
  C 250 260     # 左上第一個按鈕 (Play Scenario 通常在這)
  sleep 6       # 4-10s 看子選單
  DISPLAY=$DISP xdotool key Escape 2>/dev/null; sleep 1
  sleep 2       # 10-13s 回主選單
  C 380 260     # 右上第一個按鈕
  sleep 5       # 13-18s 看另一個子選單
  DISPLAY=$DISP xdotool key Escape 2>/dev/null
  sleep 3
) & KP=$!

# ffmpeg 錄影
DISPLAY=$DISP ffmpeg -y -loglevel error -f x11grab -video_size $WH -framerate 25 -i $DISP \
    -t "$SECS" -c:v libx264 -pix_fmt yuv420p -crf 20 "$OUT"

# 收尾
kill $KP 2>/dev/null
kill $SP 2>/dev/null; sleep 1; kill -9 $SP 2>/dev/null
"$WINE" wineserver -k 2>/dev/null || /opt/wine-stable/bin/wineserver -k 2>/dev/null
kill $XP 2>/dev/null; sleep 0.5; kill -9 $XP 2>/dev/null

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null)
echo "OK: $OUT (${DUR}s)"
