#!/usr/bin/env bash
# 從現有 WINEPREFIX + 遊戲目錄 + 系統 wine,自動 build self-contained AppImage
#
# 前置:
#   1. 系統已 apt install wine wine32:i386 wine64 libwine libwine:i386
#   2. WINEPREFIX 已配好(字體/reg/...),由本專案 tools/ 一系列腳本完成
#   3. 遊戲目錄已 ASCII symlink 化(避中文路徑 wine LC_CTYPE 問題)
#
# 用法:
#   GAME_DIR=/path/to/PG-cht-game/ \
#   WINEPREFIX=$HOME/.wine-pgcht \
#   OUTPUT=PanzerGeneral-x86_64.AppImage \
#       ./build.sh

set -euo pipefail

GAME_DIR="${GAME_DIR:?需要 GAME_DIR 指向 PG-cht.exe 所在目錄}"
WINEPREFIX="${WINEPREFIX:-$HOME/.wine-pgcht}"
OUTPUT="${OUTPUT:-PanzerGeneral-x86_64.AppImage}"
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d /tmp/pg-appimage.XXXXXX)"
APPDIR="$WORK/PanzerGeneral.AppDir"

cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

echo "[1/6] 建 AppDir 結構"
mkdir -p "$APPDIR"/{usr/bin,usr/lib,usr/share/wine,opt}

echo "[2/6] 複製 wine 套件全部檔案(:i386 + :amd64)"
TMPLIST="$(mktemp)"
dpkg -L wine wine32:i386 wine64 libwine libwine:i386 2>/dev/null | sort -u > "$TMPLIST"
COUNT=0
while IFS= read -r src; do
    [ -f "$src" ] || continue
    case "$src" in
        */doc/*|*/man/*|*/locale/*|*.html|*.gz) continue;;
    esac
    rel="${src#/}"
    mkdir -p "$APPDIR/$(dirname "$rel")"
    cp -P "$src" "$APPDIR/$rel"
    COUNT=$((COUNT+1))
done < "$TMPLIST"
rm -f "$TMPLIST"
echo "    複製 $COUNT 個檔案"

echo "[3/6] 換掉 /usr/bin/wine、wineserver、/usr/lib/wine/wineserver 為 portable script"
rm -f "$APPDIR/usr/bin/wine" "$APPDIR/usr/bin/wineserver" "$APPDIR/usr/lib/wine/wineserver"
rm -rf "$APPDIR/etc/alternatives" 2>/dev/null || true
install -m 755 "$HERE/wine-portable.sh"        "$APPDIR/usr/bin/wine"
install -m 755 "$HERE/wineserver-portable.sh"  "$APPDIR/usr/bin/wineserver"
install -m 755 "$HERE/wineserver-dispatcher.sh" "$APPDIR/usr/lib/wine/wineserver"

echo "[4/6] 把 WINEPREFIX($WINEPREFIX)複製進 AppDir/opt/wine-prefix"
cp -a "$WINEPREFIX" "$APPDIR/opt/wine-prefix"

echo "[5/6] 把遊戲目錄($GAME_DIR)複製進 AppDir/opt/game"
cp -a "$GAME_DIR/." "$APPDIR/opt/game/"

echo "[6/6] AppDir 雜項 + appimagetool 打包"
install -m 755 "$HERE/AppRun"                "$APPDIR/AppRun"
install -m 644 "$HERE/panzer-general.desktop" "$APPDIR/panzer-general.desktop"
install -m 644 "$HERE/panzer-general.png"     "$APPDIR/panzer-general.png"
ln -sf panzer-general.png "$APPDIR/.DirIcon"

if [ ! -x "$HERE/appimagetool" ]; then
    echo "    抓 appimagetool ..."
    wget -q https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage \
         -O "$HERE/appimagetool"
    chmod +x "$HERE/appimagetool"
fi

echo "    AppDir 總大小:$(du -sh "$APPDIR" | cut -f1)"
ARCH=x86_64 "$HERE/appimagetool" --comp zstd "$APPDIR" "$OUTPUT"
ls -lh "$OUTPUT"
echo "完成 → $OUTPUT"
