# AppImage 構建材料

把 Panzer General(繁中化版)+ 完整 wine 環境 + 已配置 WINEPREFIX 打包成單一可執行的 `.AppImage`,在 Ubuntu 22.04+ / Debian 12+ 同等 GLIBC 環境雙擊即跑,**不需要使用者先裝 wine**。

## 檔案

| 檔案 | 用途 |
|---|---|
| `AppRun` | AppImage 啟動腳本(掛載到 `/tmp/.mount_xxx/` 後執行) |
| `panzer-general.desktop` | XDG desktop entry |
| `panzer-general.png` | 256×256 icon(從 `PG.ICO` 轉) |
| `wine-portable.sh` | 取代 `/usr/bin/wine`(原版 hardcode `/usr/lib/wine/wine`,不可 portable) |
| `wineserver-portable.sh` | 取代 `/usr/bin/wineserver`,相對 `$APPDIR_ROOT` 找 wineserver32/64 |
| `wineserver-dispatcher.sh` | 取代 `/usr/lib/wine/wineserver`,同樣相對路徑 |
| `build.sh` | 一鍵把 `WINEPREFIX` + 遊戲 + wine 套件 → `.AppImage` |

## 重做 AppImage

```bash
GAME_DIR=/path/to/PG-cht-game/ \
WINEPREFIX=$HOME/.wine-pgcht \
OUTPUT=PanzerGeneral-x86_64.AppImage \
    ./build.sh
```

第一次跑會自動抓 `appimagetool`。產出 `.AppImage` 約 366 MB(zstd squashfs)。

## AppRun 行為

1. 設 `WINELOADER` / `WINESERVER` / `WINEDLLPATH` 指向 AppDir 內 wine binary 與 libs
2. 設 `WINEDLLOVERRIDES="mscoree,mshtml="` 跳過 Mono/Gecko
3. **第一次啟動**把 AppDir 內 prefix + game 複製到 `~/.local/share/PanzerGeneral/`(讓存檔/設定持久)
4. `cd` 到 user game dir 執行 `wine ./PG-cht.exe`

## 三個關鍵雷(被解掉了)

1. `/usr/bin/wine` 是 `alternatives` symlink 鏈,`cp -P` 留 symlink 但 alternatives target 不在 AppDir 內 → 用 `cp -L` 或重寫成相對路徑 portable script
2. `wine-stable` 原版 script 內 hardcode `/usr/lib/wine/wine`(絕對路徑),AppImage 掛到 `/tmp/.mount_xxx/` 跑不通 → 重寫成 `$(dirname $0)/../lib/wine/wine` 相對路徑
3. `dpkg -L libwine` 預設只列 `:amd64`,要 `dpkg -L libwine:i386` 才列出 i386 套件的 `i386-unix/ntdll.so`(32-bit wine 啟動必需) → build.sh 同時帶 i386 與 amd64 套件

完整技術背景見上層 [`WINE-FONT-SETUP.md`](../WINE-FONT-SETUP.md)。
