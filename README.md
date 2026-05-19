# Panzer General (繁中化) — Linux Wine 移植 & AppImage 打包

把 SSI 1994 Win95 老遊戲 *Panzer General*(繁中化 patch 版,`PG-cht.exe`)在 Ubuntu 24.04 Wine 9 環境跑通,並打包成 self-contained AppImage 可獨立分發。

> 本 repo 不含 **遊戲本體**(版權所有)、**已配置 WINEPREFIX**(857 MB)、**最終 AppImage**(366 MB),只放可重做的 **腳本、構建材料、技術文件、截圖**。

---

## 成果

| 項目 | 結果 |
|---|---|
| Wine 環境跑通 PG-cht.exe | ✅ Ubuntu 24.04 + wine 9.0 + 32-bit prefix |
| 全部中文正確顯示 | ✅ menu/對話框/按鈕/標題,字體 Source Han Sans Heavy(weight 900,粗體) |
| Self-contained AppImage | ✅ 366 MB,Ubuntu 22.04+ 同等 GLIBC 環境免裝 wine 即跑 |
| 完整技術文件 + 6 張關鍵截圖 + 8 支腳本 | ✅ 見以下目錄 |

---

## 目錄結構

```
pg-cht/
├── README.md                       # 你正在看的這份
├── WINE-FONT-SETUP.md              # 詳細技術文件(三層字體問題 + 解法)
├── docs/
│   ├── 01-symptom-screenshots.md   # 6 張截圖故事(□□ → 正常 → 粗體 → AppImage)
│   └── screenshots/                # PNG 截圖
├── tools/                          # 字體與 prefix 配置腳本
│   ├── setup-wine.sh               # 一鍵裝 wine + 建 prefix + DPI=136
│   ├── write-menufont.py           # 寫 binary LOGFONTW 改 menu/caption 字體
│   ├── merge-tahoma.py             # v1:Microsoft Tahoma + 教育部宋體 merge(細體)
│   ├── merge-tahoma-bold.py        # v2:Source Han Sans Heavy 改名 Tahoma(粗體,最終採用)
│   ├── replace-tahoma.py           # 把產出的字體覆蓋進 prefix,設 fontRev=32767.99
│   ├── rename-fonts.py             # 改字體 face name(mingliu/pmingliu/simsun 等別名)
│   └── fontforge.Dockerfile        # docker fontforge 環境(複雜字體操作用)
└── appimage/                       # AppImage 構建材料
    ├── README.md                   # AppImage 構建與設計筆記
    ├── AppRun                      # 啟動腳本
    ├── panzer-general.desktop      # XDG entry
    ├── panzer-general.png          # icon
    ├── wine-portable.sh            # 取代 /usr/bin/wine(原版 hardcode 路徑)
    ├── wineserver-portable.sh      # 取代 /usr/bin/wineserver
    ├── wineserver-dispatcher.sh    # 取代 /usr/lib/wine/wineserver
    └── build.sh                    # 一鍵打包 .AppImage
```

---

## 快速使用

### 方式 A:跑現成 AppImage(若你已有 `PanzerGeneral-x86_64.AppImage`)

```bash
chmod +x PanzerGeneral-x86_64.AppImage
./PanzerGeneral-x86_64.AppImage
```

第一次啟動約 30 秒(解 prefix + 遊戲到 `~/.local/share/PanzerGeneral/`),後續秒開。

### 方式 B:從零重做整個環境

```bash
# 1. 裝 wine + 設 DPI = 136 + 建 32-bit prefix
./tools/setup-wine.sh

# 2. 把繁中字體裝進 prefix(教育部標準宋體 + Source Han Sans)
sudo apt-get install -y fonts-moe-standard-song python3-fonttools winetricks
winetricks -q corefonts tahoma cjkfonts        # corefonts + Microsoft Tahoma + CJK fonts

# 3. 三層解法
#    3a. 改 menu/caption 字體(寫 binary LOGFONTW 到 WindowMetrics)
python3 tools/write-menufont.py && wine regedit /S /tmp/pg-cht-menufont.reg

#    3b. 把 tahoma.ttf 換成 Source Han Sans Heavy + CJK + face name=Tahoma + fontRev=32767.99
python3 tools/merge-tahoma-bold.py

#    3c. (可選) 同樣做法 + 鋪 simsun/mingliu/pmingliu 別名
python3 tools/rename-fonts.py

# 4. (可選) 打包成 AppImage
GAME_DIR=/path/to/PG-cht-game/ \
WINEPREFIX=$HOME/.wine-pgcht \
OUTPUT=PanzerGeneral-x86_64.AppImage \
    ./appimage/build.sh
```

---

## 三層字體問題(摘要,完整見 [`WINE-FONT-SETUP.md`](WINE-FONT-SETUP.md))

| 層 | 失敗點 | 解法 |
|---|---|---|
| **內文 (TextOutA)** | Wine ACP 不是 950 / 字體沒標 CP950 / 字體缺 CJK glyph | `LANG=zh_TW.UTF-8` 推導 ACP=950 + 字體 `OS/2.ulCodePageRange1` 補 bit 20 |
| **menu/status/caption** | Wine 對 raster `.fon` 不走 FontSubstitutes | 直接寫 binary LOGFONTW(92 bytes)到 `HKCU\Control Panel\Desktop\WindowMetrics` |
| **應用硬呼叫 Tahoma** | Microsoft Tahoma 沒 CJK glyph | 覆蓋 `tahoma.ttf` 為「Source Han Sans Heavy + 改名 Tahoma + fontRev=32767.99」 |

兩個關鍵雷:
1. Wine 同 face name 多個檔時按 `head.fontRevision` 大者勝(**與路徑無關**) → 自己改的字體要拉到 32767.99
2. AppImage 內 `/usr/bin/wine` 原版 `wine-stable` script hardcode `/usr/lib/wine/wine` 絕對路徑 → 重寫成相對路徑

---

## 環境

- Ubuntu 24.04 LTS、x86_64
- Wine 9.0(`wine` + `wine32:i386` + `wine64` + `libwine:i386`)
- 字體:`fonts-moe-standard-song`、`fonts-noto-cjk`、winetricks `tahoma` + `cjkfonts`
- 工具:`python3-fonttools`、docker(fontforge)、`appimagetool`(從 GitHub releases)

---

## 已知限制

- AppImage 鎖定 GLIBC 2.39+(Ubuntu 24.04 編譯的 wine),舊 distro 可能跑不起來
- 最終粗體版西文也用 Source Han Sans Heavy 黑體(非 Microsoft Tahoma 細緻字形)。要回細體版可重跑 `tools/merge-tahoma.py`
- 工作目錄含中文時 wine 會因 `LC_CTYPE` 解碼失敗;AppRun 已把遊戲解到純 ASCII 路徑避開
- 不打包 Mono / Gecko(`WINEDLLOVERRIDES=mscoree,mshtml=` 跳過)

---

## License

腳本與文件:MIT(僅限本 repo 的原創部分)
遊戲本體:SSI / Mindscape 版權,**未包含於此 repo**
教育部標準宋體:中華民國教育部
Source Han Sans:Adobe / Google,SIL Open Font License 1.1
Microsoft Tahoma:Microsoft Corporation(由使用者自備)
