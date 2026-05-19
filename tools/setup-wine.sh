#!/usr/bin/env bash
# Panzer General 繁中化版 wine 環境一鍵設定
#   * 安裝 wine (含 32-bit i386)
#   * 建立 32-bit WINEPREFIX (~/.wine-pgcht)
#   * 設定 DPI = 136
#   * 不直接執行遊戲,留給後續步驟驗證

set -euo pipefail

GAME_DIR="$(cd "$(dirname "$0")" && pwd)"
PREFIX="${WINEPREFIX_OVERRIDE:-$HOME/.wine-pgcht}"
DPI="${DPI_OVERRIDE:-136}"

echo "[1/4] 安裝 wine 套件 (需要 sudo)"
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install -y \
    wine wine32:i386 wine64 \
    fonts-wqy-microhei fonts-wqy-zenhei \
    winbind cabextract

echo "[2/4] 建立 32-bit WINEPREFIX: ${PREFIX}"
export WINEPREFIX="${PREFIX}"
export WINEARCH=win32
export WINEDEBUG=-all
if [ ! -d "${PREFIX}" ] || [ ! -f "${PREFIX}/system.reg" ]; then
    rm -rf "${PREFIX}"
    wineboot --init
    # 等 wineboot 完成
    wineserver -w || true
else
    echo "    prefix 已存在,跳過初始化"
fi

echo "[3/4] 設定 DPI = ${DPI}"
DPI_HEX=$(printf '%08x' "${DPI}")
REG_FILE="$(mktemp --suffix=.reg)"
cat > "${REG_FILE}" <<EOF
REGEDIT4

[HKEY_CURRENT_USER\\Control Panel\\Desktop]
"LogPixels"=dword:${DPI_HEX}

[HKEY_CURRENT_CONFIG\\Software\\Fonts]
"LogPixels"=dword:${DPI_HEX}
EOF
wine regedit "${REG_FILE}"
wineserver -w || true
rm -f "${REG_FILE}"

echo "[4/4] 驗證設定"
echo "    WINEPREFIX = ${PREFIX}"
echo "    WINEARCH   = win32"
wine --version
echo
echo "已寫入的 LogPixels:"
grep -A1 -i 'Control Panel\\\\Desktop' "${PREFIX}/user.reg" | grep -i 'LogPixels' || \
  grep -B1 -A3 LogPixels "${PREFIX}/user.reg" | head -20

cat <<MSG

完成。後續驗證執行遊戲請跑:

  cd "${GAME_DIR}"
  WINEPREFIX="${PREFIX}" WINEARCH=win32 WINEDEBUG=-all wine ./PG-cht.exe

MSG
