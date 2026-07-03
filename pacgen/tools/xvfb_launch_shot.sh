#!/bin/bash
# WORKING harness (P0 solved): direct fullscreen launch on ISOLATED Xvfb :95.
# NEVER touches user's :1. Key fix: NO `explorer /desktop` — that broke DDraw capture.
#   usage: launch.sh <workdir> <out.png> [wait_secs]
set -u
WORKDIR="${1:-/home/anr2/pgfont95}"
SHOT="${2:-/tmp/shot.png}"
WAIT="${3:-28}"
export DISPLAY=:95
export WINEPREFIX=/home/anr2/.wine-pacgen-test
export WINEARCH=win32
export WINEDEBUG=-all

# ensure isolated Xvfb :95 is up
if ! pgrep -f 'Xvfb :95' >/dev/null; then
  rm -f /tmp/.X95-lock /tmp/.X11-unix/X95 2>/dev/null
  Xvfb :95 -screen 0 640x480x24 >/tmp/xvfb95.log 2>&1 &
  sleep 2
fi

wineserver -k 2>/dev/null; sleep 1
cd "$WORKDIR" || exit 3
wine PACGEN.EXE >/tmp/wine95.log 2>&1 &
WPID=$!
sleep "$WAIT"
import -display :95 -window root "$SHOT" 2>/dev/null
sync
wineserver -k 2>/dev/null; sleep 1
kill "$WPID" 2>/dev/null
COLORS=$(convert "$SHOT" -format '%k' info: 2>/dev/null)
echo "shot -> $SHOT ($(stat -c%s "$SHOT" 2>/dev/null)B, colors=$COLORS)  [colors>2 = real render]"
