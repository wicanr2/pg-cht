# Wine 繁中字體 + AppImage 打包歷程

**專案**:Panzer General Win95 繁中化版 (PG-cht v1.2)
**目標**:在 Ubuntu 24.04 Wine 9 環境下,讓 PG-cht.exe 所有中文文字正確顯示(含 menu/對話框/按鈕),並打包成 self-contained AppImage 可獨立分發。
**日期**:2026-05-19

---

## 1. 起始狀態與目標

- 主機:Ubuntu 24.04 LTS、x86_64、無 wine 已裝。
- 目標執行檔:`PG-cht.exe`(PE32, 32-bit Win95 GUI,繁中化 patch 版,字串以 **Big5 byte** 嵌入,主要呼叫的字體名:`Tahoma` / `MS Sans Serif` / `MS Shell Dlg` / `System` / `Courier`)。
- 目標效果:遊戲畫面所有中文字正常顯示,字體粗體;AppImage 可在乾淨 Linux 機器上雙擊執行。

---

## 2. 觀察到的三層字體問題

PG-cht.exe 顯示中文時 `□□` 不是單一原因,實證後拆成三層:

| 層 | 失敗點 | Root cause |
|---|---|---|
| **內文 (TextOutA)** | `1939 波蘭:` 變 `1939 □□:` | Wine ACP 不是 950 / 字體 OS/2.ulCodePageRange1 bit 20 沒標 Big5 / 字體缺 CJK glyph |
| **menu/status/caption** | `(F)□□ (E)□□` | Wine 對 raster `.fon`(`cvgasys.fon`/`sseriff.fon`) 不走 FontSubstitutes,即使 reg 替代了也無效 |
| **應用程式硬呼叫 "Tahoma" 字串** | 對話框內文/按鈕仍 `□□` | Microsoft Tahoma 本身沒 CJK glyph;FontSubstitutes 對部分 charset(0/DEFAULT)wine 不會 fallback |

---

## 3. 解決方案(三層分別處理)

### 3.1 內文中文

```bash
sudo dpkg --add-architecture i386
sudo apt-get install -y wine wine32:i386 wine64 fonts-wqy-microhei fonts-wqy-zenhei winbind cabextract
sudo apt-get install -y fonts-moe-standard-song fonts-cwtex-ming python3-fonttools
sudo locale-gen zh_TW.BIG5     # 確保 zh_TW.Big5 locale 存在
```

WINEPREFIX 設置:

```bash
export WINEPREFIX="$HOME/.wine-pgcht"
export WINEARCH=win32
export WINEDLLOVERRIDES="mscoree,mshtml="    # 跳過 wineboot Mono/Gecko dialog
wineboot --init
```

DPI 與 Codepage(透過 `wine regedit /S`):

```reg
[HKEY_CURRENT_USER\Control Panel\Desktop]
"LogPixels"=dword:00000088                   ; DPI = 136
```

`Codepages=950,950` 由 wineboot 從 `LANG=zh_TW.UTF-8` 自動推導 → ACP=950 (Big5)。

### 3.2 menu / status / caption(關鍵突破)

Wine 對 `MenuFont` / `StatusFont` / `CaptionFont` 等 raster `.fon` 字體的 FontSubstitutes 替代**無效**。必須直接寫 binary `LOGFONTW`(92 bytes)到 `HKCU\Control Panel\Desktop\WindowMetrics`:

腳本見 `tools/write-menufont.py`,核心邏輯:

```python
import struct
def make_logfont(face: str, pt: int, weight: int = 400) -> bytes:
    height = -int(round(pt * 96 / 72))
    head = struct.pack('<lllllBBBBBBBB',
        height, 0, 0, 0, weight,
        0, 0, 0, 1, 0, 0, 0, 0x12)   # lfCharSet = DEFAULT_CHARSET (1)
    name = face.encode('utf-16-le')
    name += b'\x00' * (64 - len(name))
    return head + name
```

要對 `CaptionFont` / `SmCaptionFont` / `MenuFont` / `StatusFont` / `MessageFont` / `IconFont` 各寫一份。**lfFaceName 必須是 Wine 認得到的真實 face**(這裡用 `Tahoma`,因為我們已經把 Tahoma 字體檔本身包了 CJK glyph,見 3.3)。

驗證:用 wine notepad 開 Big5 文字檔,menu bar `檔案(F) 編輯(E) 搜尋(S) 檢視(V) 說明(H)` 應正確顯示。

### 3.3 應用程式硬呼叫 "Tahoma" → 用 merged / Heavy Tahoma 取代

**v1 (細體版)**:把使用者提供的 Microsoft Tahoma(西文)用 `fontTools.merge` 與 `MoeStandardSong.ttf`(教育部標準宋體,有 CJK)合成,結果 face name 仍叫 `Tahoma`,西文用原 Tahoma 字形,CJK fallback 到宋體。

**v2 (粗體版,最終採用)**:從 cjkfonts 裝的 `sourcehansans.ttc` 取 idx=20 (Source Han Sans Heavy, weight 900),用 `pyftsubset` 拆出獨立 OTF(只留需要的 codepoint),改 family name 為 `Tahoma`、`fontRevision=32767.99`、`OS/2.ulCodePageRange1` 補 CP950 bit,覆蓋進 prefix 的 `tahoma.ttf` 與 `tahomabd.ttf`。

```python
# tools/merge-tahoma-bold.py 核心
python3 -m fontTools.subset sourcehansans.ttc \
    --font-number=20 \
    --output-file=shs_heavy.otf \
    --unicodes="U+3000-303F,U+3100-312F,U+3300-33FF,U+4E00-9FFF,U+F900-FAFF,U+FF00-FFEF,U+20-7E" \
    --no-hinting --no-layout-closure
# 然後用 fontTools 改 face name 為 Tahoma + fontRev=32767.99,寫進 prefix
```

**Trade-off**:v2 西文也用 SHS Heavy 黑體,失去 Microsoft Tahoma 細緻字形。對遊戲老 UI 可接受。

### 3.4 兩個關鍵雷

1. **Wine 字體優先級**:同 face name 多個檔案時,Wine 按 `head.fontRevision` 數值大者勝,**與路徑無關**。`/usr/share/wine/fonts/tahoma.ttf`(Microsoft 版,rev=13333)會蓋過 prefix 內的低 rev 版。解法:`fontTools` 設 `t["head"].fontRevision = 32767.99`(16.16 Fixed 上限)。
2. **fontforge `changeWeight` 對複雜 CJK 有 outline overlap bug**:加粗後部分字會缺 glyph 變 `□□`。改用「字體本身就是 Heavy」(SHS Heavy weight 900)避開。

---

## 4. 啟動指令(無 AppImage 時)

```bash
# 1. 用純 ASCII symlink 避開中文路徑(LC_CTYPE 問題的折衷)
ln -sfn /home/anr2/game/PG-cht-1.2_繁中化_20260519-wine /tmp/pg-cht

# 2. 啟動
cd /tmp/pg-cht
WINEPREFIX="$HOME/.wine-pgcht" WINEARCH=win32 WINEDEBUG=-all \
  WINEDLLOVERRIDES="mscoree,mshtml=" LANG=zh_TW.UTF-8 \
  wine ./PG-cht.exe
```

---

## 5. 環境瘦身(prefix 842 MB → 597 MB)

實作過程留下大量冗餘字體,實際只需 `tahoma.ttf` + corefonts:

```bash
F="$WINEPREFIX/drive_c/windows/Fonts"
rm -f "$F/sourcehansans.ttc" "$F/unifont.ttf" \
      "$F/mingliu.ttf" "$F/pmingliu.ttf" "$F/simsun.ttf" "$F/nsimsun.ttf" \
      "$F/system.ttf" "$F/ssserife.ttf"   # 共 ~250 MB
rm -rf "$WINEPREFIX/drive_c/windows/Microsoft.NET"      # 跳過了,沒實際用
rm -rf "$WINEPREFIX/drive_c/windows/mono"
rm -rf "$HOME/.cache/winetricks"
```

剩 597 MB(其中 `drive_c/windows/system32` 524 MB 是 wine fake DLL,全部必要不能砍)。

---

## 6. AppImage 打包(self-contained)

### 6.1 結構

```
PanzerGeneral.AppDir/
├── AppRun                          # 啟動腳本
├── panzer-general.desktop          # XDG
├── panzer-general.png              # icon
├── usr/
│   ├── bin/ wine, wineserver       # patched portable script
│   ├── lib/wine/ wine, wine64, wineserver32, wineserver64
│   ├── lib/{i386,x86_64}-linux-gnu/wine/
│   │   ├── i386-unix/ x86_64-unix/   # wine .so loader-side
│   │   └── i386-windows/ x86_64-windows/   # PE32 fake DLL
│   └── share/wine/
├── opt/
│   ├── wine-prefix/                # 預配置好的 prefix
│   └── game/                       # PG-cht.exe + DATA/ART/...
```

### 6.2 兩個必須 patch 的雷

**雷 1**:`/usr/bin/wine` 是 symlink 鏈(`wine → /etc/alternatives/wine → wine-stable`),`cp -P` 會留 symlink 但 alternatives target 不在 AppDir 內。用 `cp -L` 解開,或重寫 portable script。

**雷 2**:`wine-stable` script 內 hardcode `/usr/lib/wine/wine`(absolute path),AppImage mount 在 `/tmp/.mount_xxx/` 跑時找不到。重寫成 `$(dirname $0)/../lib/wine/wine` 相對路徑:

```sh
#!/bin/sh -e
DIR="$(dirname "$(readlink -f "$0")")"
APPDIR_ROOT="$(readlink -f "$DIR/../..")"
wine32="$APPDIR_ROOT/usr/lib/wine/wine"
wine64="$APPDIR_ROOT/usr/lib/wine/wine64"
# ... pick wineloader
exec "$wine" "$@"
```

`wineserver` script(及 `/usr/lib/wine/wineserver` dispatcher)同樣處理。

**雷 3**:`dpkg -L libwine` 預設只列 `:amd64`,要 `dpkg -L libwine:i386` 才列出 i386 套件的檔案(含 `i386-unix/ntdll.so`,32-bit wine 啟動必需)。

### 6.3 AppRun 設計

第一次啟動把 prefix + 遊戲 copy 到 `~/.local/share/PanzerGeneral/`(讓存檔 / 設定可持久),之後直接用該位置 wine 跑。完整 AppRun 見 `appimage-build/PanzerGeneral.AppDir/AppRun`。

### 6.4 打包

```bash
cd /home/anr2/game/appimage-build
./tools/appimagetool --comp zstd PanzerGeneral.AppDir PanzerGeneral-x86_64.AppImage
# 輸出:PanzerGeneral-x86_64.AppImage  366 MB
```

(`mksquashfs` 在 Ubuntu 24.04 不支援 `xz`,只能 `zstd`。)

### 6.5 測試

```bash
rm -rf ~/.local/share/PanzerGeneral    # 模擬第一次啟動
./PanzerGeneral-x86_64.AppImage
```

第一次啟動約 30 秒(解壓 prefix + game 到 user data dir),後續啟動秒開。

---

## 7. 最終配置 / 輸出

| 項目 | 大小 | 位置 |
|---|---|---|
| AppImage(self-contained) | 366 MB | `appimage-build/PanzerGeneral-x86_64.AppImage` |
| WINEPREFIX(瘦身後) | 597 MB | `~/.wine-pgcht/`(系統版),AppImage 內也有 |
| Tahoma 字體(Heavy + CJK) | 5.3 MB × 2 | `<WINEPREFIX>/drive_c/windows/Fonts/tahoma.ttf` & `tahomabd.ttf` |
| 遊戲本體 | 43 MB | `PG-cht-1.2_繁中化_20260519-wine/` |

字體鏈條:`Tahoma` face 在 wine 內由 `tahoma.ttf`(Source Han Sans Heavy + CJK 改名 Tahoma)提供,涵蓋 26000+ glyph、weight 700/900、含 Big5/GBK codepage 標記。

---

## 8. 相關腳本與資源

| 檔案 | 用途 |
|---|---|
| `setup-wine.sh` | 一鍵安裝 wine + i386 多架構 + 建立 prefix + 設 DPI=136 |
| `tools/write-menufont.py` | 寫 binary LOGFONTW 到 WindowMetrics(menu/status/caption 改 Tahoma) |
| `tools/merge-tahoma.py` | v1 細體:Microsoft Tahoma + MoE 宋體 merge |
| `tools/merge-tahoma-bold.py` | v2 粗體:Source Han Sans Heavy + CJK subset → 改名 Tahoma |
| `tools/replace-tahoma.py` | 把產出的字體覆蓋進 prefix,設 fontRev=32767.99 |
| `appimage-build/PanzerGeneral.AppDir/AppRun` | AppImage 啟動腳本 |
| `appimage-build/PanzerGeneral.AppDir/usr/bin/wine` | Portable wine wrapper(取代 wine-stable) |
| `appimage-build/PanzerGeneral.AppDir/usr/bin/wineserver` | Portable wineserver dispatcher |
| `appimage-build/PanzerGeneral-x86_64.AppImage` | 最終輸出(366 MB) |

---

## 9. 未解 / 已知限制

- AppImage 鎖定 GLIBC 2.39+(Ubuntu 24.04 編譯的 wine + libs),舊 distro 可能跑不起來。
- 西文字形使用 Source Han Sans Heavy(非 Microsoft Tahoma)。要回 v1 細體版可重跑 `merge-tahoma.py`。
- 工作目錄含中文(`繁中化`)時 wine 會因 `LC_CTYPE` 解碼失敗;AppRun 已把遊戲解到純 ASCII 路徑避開。
- 不打包 Mono / Gecko(`WINEDLLOVERRIDES=mscoree,mshtml=` 跳過),如果遊戲未來要 .NET 元件需補回。
