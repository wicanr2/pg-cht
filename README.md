# Panzer General (繁中化) — Linux Wine + Windows portable 兩路打包

把 SSI 1994 Win95 老遊戲 *Panzer General*(繁中化 patch 版,`PG-cht.exe`)在現代環境(Ubuntu 24.04 Wine 9 / Windows 10/11)跑通,並分別打包成兩種 self-contained 單檔分發格式:

- **Linux AppImage** (366 MB) — Ubuntu 22.04+ 雙擊即跑,免裝 wine
- **Windows 7-Zip SFX** (~12 MB) — Windows 10/11 雙擊即跑,免裝 .NET / 任何 runtime

> 同引擎的 **《盟軍元帥》(Allied General)** 繁中化(含烤在點陣圖裡的 UI、開頭畫面標題、執行期狀態列)另見下方 [盟軍元帥 (Allied General) 中文化](#盟軍元帥-allied-general-中文化) 專節。

> 本 repo 不含 **遊戲本體**(版權所有)、**已配置 WINEPREFIX**(857 MB)、**最終 AppImage**(366 MB)、**最終 SFX .exe**,只放可重做的 **腳本、構建材料、技術文件、截圖**。

---

## 成果

| 項目 | 結果 |
|---|---|
| Wine 環境跑通 PG-cht.exe | ✅ Ubuntu 24.04 + wine 9.0 + 32-bit prefix |
| 全部中文正確顯示 | ✅ menu/對話框/按鈕/標題,字體 Source Han Sans Heavy(weight 900,粗體) |
| Self-contained Linux AppImage | ✅ 366 MB,Ubuntu 22.04+ 同等 GLIBC 環境免裝 wine 即跑 |
| Self-contained Windows SFX | ✅ ~12 MB,Win10/11 雙擊即跑,無 WinG 對話框、不寫 registry shim |
| 完整技術文件 + 構建腳本 + 領域知識 skill | ✅ 見以下目錄 |

> 原時序 6 張對照截圖已從 repo 中移除以縮小體積,僅留說明文字於 `docs/01-symptom-screenshots.md`;另補 3 張最終成果實機畫面於下方。

---

## 成果截圖(AppImage 實機)

完整修復後從 AppImage 啟動的 PG-cht.exe,中文(menu / 對話框 / 按鈕 / 戰役名)全部正常顯示為粗體。

| 畫面 | 內容 |
|---|---|
| ![戰役選擇對話框](docs/screenshots/00_screenshot.png) | **1939 戰役選擇對話框** — 視窗標題 `裝甲元帥(中文版)`、menu `(F)檔案 (E)編輯`、左側 1941 系列戰役按鈕、中央劇本說明 + 歐洲地圖背景,皆中文粗體。 |
| ![完整劇本列表](docs/screenshots/01_screenshot.png) | **完整劇本列表 grid** — 38 個戰役按鈕(波蘭 / 華沙 / 挪威 / 低地國 / 法國 / 海獅 / 北非 / 阿拉曼 / 高加索 / …),配合中央劇本說明對話框,證實所有戰役名稱字串都正確覆蓋。 |
| ![戰場六角格畫面](docs/screenshots/02_screenshot.png) | **進入戰場後的六角格戰術畫面** — menu `(F)檔案 (E)編輯 (G)遊戲 (V)演算`、部隊單位、地圖渲染,確認遊戲主迴圈中文亦無 □□。 |

---

## 盟軍元帥 (Allied General) 中文化

*Allied General*(SSI 1995,與 Panzer General **同引擎**)的繁體中文化。針對社群「Lite v1.1」重打包版(`AG.EXE` 2,167,611 bytes),完成 EXE 字串、資料檔、**烤在點陣圖裡的 UI**、開頭畫面標題全面中文化,並修掉重打包者藏的簽名。

### 遊戲簡介 — 經典 Hex-based 戰術骨灰作

作為 SSI 經典神作《裝甲元帥》(Panzer General) 的續作,《盟軍元帥》在 Windows 95 世代將戰場視角切換至盟軍陣營。其核心玩法本質上是一套**具備部隊養成機制的六角格 (Hex-based) 資源調度與戰術模擬系統**。

**核心架構 — 三大 Campaign**:遊戲將歷史戰役拆解為三條獨立邏輯主線,各有不同操作痛點與資源限制:

| 戰線 | 風格 | 痛點 |
|---|---|---|
| **蘇聯線 (Soviet)** | 先防禦後反攻 | 初期(巴巴羅薩行動)以空間換時間,用消耗戰拖延德軍閃電戰;中後期重工業成型後全面壓制 |
| **英國線 (British)** | 長途補給與多軍種協同 | 戰場在北非沙漠與義大利,裝甲基數小,極度依賴海空軍掩護與精準戰線維持 |
| **美國線 (American)** | 強大資源與空權壓制 | 從火炬行動推到德國本土,容錯率最高,後勤與空中火力壓倒性 |

**核心機制與戰術邏輯**:深度不在複雜操作,而在三個底層機制相互堆疊:

1. **核心部隊繼承 (Core Units Instance)** — 關卡結束時倖存部隊攜帶累積經驗值 (Stars) 直接繼承到下一關。玩家真正的核心資產是這群高經驗王牌;**避免王牌因失誤被全滅 (Permadeath) 是貫穿全局的最高原則**。
2. **科技樹演進與動態升級** — 戰役時間軸推進 (1941 → 1945) 解鎖新歷史裝備,可消耗**聲望值 (Prestige)** 升級部隊硬體。範例:輕型 M3 Stuart → 主力 M4 Sherman → 後期抗虎式主力 M26 Pershing。
3. **多兵種協同 (Combined Arms) 與地形限制** — 單一兵種衝鋒極易觸發「遭遇戰 (Rugged Defense)」而崩盤。標準戰術執行鏈:

   > 偵察車 (Recon) 開霧 → 火砲 (Artillery) 間接壓制 → 空軍洗地 → 步兵/裝甲收尾

   城市與密林等地形對裝甲有極高負面修正,須改由步兵近身清理。

**總結 — 核心價值**:成功在於「易學難精 (Easy to learn, hard to master)」。它把複雜的軍事手冊計算隱藏於簡單的攻擊/防禦數值與地形加成公式中。對喜歡沙盤推演、注重部隊養成與最優解戰術布局的玩家,本作奠定了現代回合制策略遊戲(如 *Panzer Corps*)的底層邏輯。

### 中文化後的開頭畫面

在原版 `ALLIED GENERAL` 標誌下,新增**鋼鐵漸層書法風**的「盟軍元帥」(字寬對齊英文、置中其下、套垂直銀灰漸層 + 深色描邊,直接重繪進 `ART\SPLASH.DAT` 的點陣圖):

![盟軍元帥 中文化開頭畫面](docs/screenshots/ag_splash_zh.png)

### 完成項目

| 類別 | 內容 |
|---|---|
| EXE UI 字串 | menu / 對話框 / 按鈕 / 狀態列(Big5 就地翻譯 + RT_MENU/RT_DIALOG/RT_STRING) |
| 任務簡報 | RT_STRING 全中文,並修正兩個致命踩雷:**尾端空格 padding 造成換行大空洞**、**空字串(wLen=0)導致組字器回顯重複** |
| 回合/開戰畫面 | 天氣(晴朗/陰天/下雨/下雪)、地面(乾/泥濘/結冰)、陣營(盟軍/軸心)、月份(一~十二月) |
| 裝備名稱 | `PANZEQUP.EQP` 全中文 + 縮短(國名 1 字、刪重複英文機名;如 `美國 野馬 P51B Mustg` → `美野馬 P51B`) |
| 城市/地形/戰術標籤 | `MAPNAMES.STR`(1553/1570)、`TACMAP.TGF`(與 PG 共用) |
| **點陣圖 UI(烤在圖上)** | PREFERENCES / SETTINGS(盟德俄三版)/ 戰役按鈕(北非·西歐·俄羅斯,標楷體)/ 取消·確定(微軟正黑體粗體,密度法保留內框) — 全靠逆向 `ART.DAT` 的 RLEi 編解碼重繪 |
| 開頭畫面 | 加「盟軍元帥」鋼鐵漸層標題(見上) |
| **修正介面 bug** | 戰鬥介面陣營配色顛倒(美/英戰場誤用俄配色)→ 對調 scenario-classify 的 store 值 |
| **移除重打包者簽名** | 藏在狀態列(**反向 + XOR 0xFF** 編碼)的 email `raywolf@chuvashia.ru` → 改顯示玩家代號;明文 `kilroy was here.` → `盟軍元帥中文版` |

### 技術文件(可重做)

- **點陣圖 UI 中文化**(ART.DAT 索引 / CPal 調色盤 / RLEi 逐列 RLE 編解碼 / 去字保底 / 鋼鐵漸層標題):[`skills/art-dat-bitmap-cht/SKILL.md`](skills/art-dat-bitmap-cht/SKILL.md) + `tools/art-dat/`
- **EXE / 資料檔 中文化 + 執行期 UI + 破解者簽名逆向**:[`skills/panzer-general-cht/SKILL.md`](skills/panzer-general-cht/SKILL.md)、[`references/ag-ui-runtime.md`](skills/panzer-general-cht/references/ag-ui-runtime.md)

> 與 PG 相同,本 repo **不含遊戲本體**(版權所有),僅放可重做的腳本 / 技術文件 / 截圖。

### 踩雷紀錄(2026-05-30 事件)

| 事件 | 根因 | 處理 |
|---|---|---|
| **改完 email 後一進戰場就閃退** | 破解者的 email blob(`0x3d15f–0x3d17a`,reversed+XOR0xFF)**尾端 2 byte 與可執行碼重疊** —— 正好是 `call 0x43dda3` 的運算元高位 + 一個 `ret`。原本「整段 28 byte 覆寫」把 call/ret 改成 `0xFF` → 選單能開、**一進關卡執行到該段就崩潰**。 | **只改字串需要的 13 byte**(null + Big5),保留 `0x3d15f/0x3d160` 的 code byte;反組譯確認 `call+ret` 還原。詳見 [`ag-ui-runtime.md` §6](skills/panzer-general-cht/references/ag-ui-runtime.md)。**教訓:cracker 把資料藏進 .text 時常與指令交疊,改之前務必反組譯確認該 byte 不是 code。** |
| **字形與原始 Lite 不同** | 前期跟隨 PG 把字體 face `Arial`→`Tahoma`(26 處);Windows 原生對 Big5 的代換字型因此不同。 | **還原回 `Arial`**(`b"Tahoma"`→`b"Arial\0"`,26 處)。Tahoma 改法是 wine 端 Big5 fallback 用,**Windows 原生保留 `Arial` 即可**。 |
| **256 色才能執行(WinG 老遊戲)** | AG.EXE 啟動檢查 `GetDeviceCaps(BITSPIXEL)==8`,Win10/11 為 32bpp → 跳「需 256 色」對話框退出。 | 本機無編譯器 → **用 Python 手工組 32-bit PE `shim.dll`**:轉發 29 個 GDI32 函式給真 gdi32、只攔 `GetDeviceCaps` 的 BITSPIXEL→回 8;patch AG.EXE import `GDI32.dll`→`shim.dll`。手法同 pg-cht wine 的 `pgs.dll`([`panzer-general-wine`](skills/panzer-general-wine/SKILL.md))。 |

---

## 目錄結構

```
pg-cht/
├── README.md                       # 你正在看的這份
├── WINE-FONT-SETUP.md              # 詳細技術文件(三層字體問題 + 解法)
├── docs/
│   ├── 01-symptom-screenshots.md   # 原 6 張時序截圖的敘事(□□ → 正常 → 粗體 → AppImage)+ 3 張最終成果
│   └── screenshots/                # 3 張最終成果 PNG(00/01/02);原時序 6 張未保留
├── tools/                          # 字體與 prefix 配置腳本
│   ├── setup-wine.sh               # 一鍵裝 wine + 建 prefix + DPI=136
│   ├── write-menufont.py           # 寫 binary LOGFONTW 改 menu/caption 字體
│   ├── merge-tahoma.py             # v1:Microsoft Tahoma + 教育部宋體 merge(細體)
│   ├── merge-tahoma-bold.py        # v2:Source Han Sans Heavy 改名 Tahoma(粗體,最終採用)
│   ├── replace-tahoma.py           # 把產出的字體覆蓋進 prefix,設 fontRev=32767.99
│   ├── rename-fonts.py             # 改字體 face name(mingliu/pmingliu/simsun 等別名)
│   └── fontforge.Dockerfile        # docker fontforge 環境(複雜字體操作用)
├── appimage/                       # Linux AppImage 構建材料
│   ├── README.md                   # AppImage 構建與設計筆記
│   ├── AppRun                      # 啟動腳本
│   ├── panzer-general.desktop      # XDG entry
│   ├── panzer-general.png          # icon
│   ├── wine-portable.sh            # 取代 /usr/bin/wine(原版 hardcode 路徑)
│   ├── wineserver-portable.sh      # 取代 /usr/bin/wineserver
│   ├── wineserver-dispatcher.sh    # 取代 /usr/lib/wine/wineserver
│   └── build.sh                    # 一鍵打包 .AppImage
├── windows-sfx/                    # Windows 7-Zip SFX 構建材料
│   ├── README.md                   # SFX 設計筆記 + WING32 patch 原理
│   ├── patch_wing32.py             # 對 WING32.DLL 套 2-byte patch(suppress dialog)
│   ├── PG-cht.cmd                  # 自含啟動器(__COMPAT_LAYER=256COLOR env var)
│   ├── stamp_icon.ps1              # Win32 UpdateResource P/Invoke icon stamper
│   ├── build_sfx.ps1               # 一鍵打包 .exe(stage→.7z→config→stamp→concat)
│   └── Remove-256Color-Shim.reg    # 清掉舊 HKCU AppCompat shim
└── skills/
    ├── panzer-general-cht/SKILL.md       # PG/AG 中文化領域知識
    ├── panzer-general-wine/SKILL.md      # wine 啟動環境(256 色 bypass via pgs.dll)
    └── wing-portable-sfx/SKILL.md        # Windows 原生 + SFX 打包(WING32 patch + __COMPAT_LAYER)
```

---

## 快速使用

### 方式 A1:跑現成 AppImage (Linux,若你已有 `PanzerGeneral-x86_64.AppImage`)

```bash
chmod +x PanzerGeneral-x86_64.AppImage
./PanzerGeneral-x86_64.AppImage
```

第一次啟動約 30 秒(解 prefix + 遊戲到 `~/.local/share/PanzerGeneral/`),後續秒開。

### 方式 A2:跑現成 SFX (Windows,若你已有 `PanzerGeneralCHT-1.2-portable.exe`)

雙擊 `.exe` → 跳出對話框「即將解壓並啟動 Panzer General」→ 選解壓位置 → 解壓完自動啟動。

第一次解壓 ~12 MB → ~42 MB 大概 3-5 秒,主視窗「裝甲元帥遊戲選項」7 秒內出現。下次只要從解壓資料夾跑 `PG-cht.cmd` 即可。

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

### 方式 C:Windows 原生 + 自製 SFX (Win10 / 11)

```powershell
# 1. 對遊戲目錄裡的 WING32.DLL 套 2-byte patch (suppress "WinG Installation Error")
python windows-sfx\patch_wing32.py <游戲資料夾>\WING32.DLL

# 2. 確認啟動器在遊戲資料夾裡 (預設應該有)
copy windows-sfx\PG-cht.cmd <游戲資料夾>\

# 3. 雙擊 <游戲資料夾>\PG-cht.cmd 驗證能跑 (主視窗 7 秒內到「裝甲元帥遊戲選項」)

# 4. (可選) 打包成單檔 SFX .exe
powershell -ExecutionPolicy Bypass -File windows-sfx\build_sfx.ps1 `
  -Source <游戲資料夾> `
  -Output PanzerGeneralCHT-1.2-portable.exe
```

只依賴 Windows 內附的 7-Zip (`C:\Program Files\7-Zip\`) + PowerShell 5.1 + Win32 API。不需要 NSIS / Inno Setup / rcedit / Resource Hacker。

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

## Windows 端的三個踩坑(摘要,完整見 [`windows-sfx/README.md`](windows-sfx/README.md))

| 問題 | 根因 | 解法 |
|---|---|---|
| 每次啟動跳「WinG Installation Error」對話框 | Win10/11 SysWOW64 中的 `WING32.DLL` (Microsoft 12800-byte build) 內建路徑檢查預期住在 `C:\Windows\System`,在 SysWOW64 永遠認定「裝錯位置」 | 對 `WING32.DLL` 套 file offset `0xA55` 的 2-byte patch:`75 11` (jnz dialog) → `90 90` (nop nop),永遠走 success path。**禁區**:不能直接 NOP `0xA9B` 的 `call MessageBoxA` (會 `0xC0000142` DllMain init failed,MessageBoxA 內部 pump messages 釋放 loader lock,跳過會卡死) |
| 畫面整片花/黑 | 32 bpp 桌面但 WinG 預期 8-bit palette | 啟動器設 `__COMPAT_LAYER=256COLOR` env var (單行程作用域,等效 Properties → "Reduced color mode" 但不寫 registry → 可攜) |
| 7-Zip SFX 打包出來 12 MB 變 196 KB | Win32 `UpdateResource()` 把 PE image size 當 EOF,**會截掉 appended overlay** | Icon 必須先 stamp 在 `7z.sfx` stub 副本上,**再**和 config + payload 三段 concat |

額外 BOM 矩陣 (同一份工作流產生三種檔案,對「BOM 是否該存在」答案各異):

| 檔案 | Reader | BOM? |
|---|---|---|
| `.ps1` | PowerShell 5.1 (Windows PowerShell) | **要**。沒 BOM 預設用 ANSI codepage 讀,中文字面值會 garbled |
| SFX `config.txt` | `7z.sfx` stub | **要 BOM + CRLF**,不然 config 被略過 |
| `SKILL.md` | Claude 的 skill loader | **絕對不要 BOM**。YAML frontmatter 解析器需要 `---` 在 byte 0 |

---

## 環境

**Linux 端 (AppImage 構建):**
- Ubuntu 24.04 LTS、x86_64
- Wine 9.0(`wine` + `wine32:i386` + `wine64` + `libwine:i386`)
- 字體:`fonts-moe-standard-song`、`fonts-noto-cjk`、winetricks `tahoma` + `cjkfonts`
- 工具:`python3-fonttools`、docker(fontforge)、`appimagetool`(從 GitHub releases)

**Windows 端 (SFX 構建):**
- Windows 10 / 11、x64
- 7-Zip 18+(`C:\Program Files\7-Zip\7z.exe` + `7z.sfx`)
- Windows PowerShell 5.1 (內附) 或 PowerShell 7+
- Python 3.x(跑 `patch_wing32.py`,沒 third-party 相依)
- 不需要 NSIS / Inno Setup / rcedit / Resource Hacker

---

## 已知限制

**Linux/AppImage:**
- AppImage 鎖定 GLIBC 2.39+(Ubuntu 24.04 編譯的 wine),舊 distro 可能跑不起來
- 最終粗體版西文也用 Source Han Sans Heavy 黑體(非 Microsoft Tahoma 細緻字形)。要回細體版可重跑 `tools/merge-tahoma.py`
- 工作目錄含中文時 wine 會因 `LC_CTYPE` 解碼失敗;AppRun 已把遊戲解到純 ASCII 路徑避開
- 不打包 Mono / Gecko(`WINEDLLOVERRIDES=mscoree,mshtml=` 跳過)

**Windows/SFX:**
- WING32.DLL patch 只驗證過 Microsoft 12800-byte build (SHA256 `bb1f552e25...`)。其他來源的 WING32.DLL 可能 offset 不同,`patch_wing32.py` 有 SHA256 sanity 會擋下
- SFX 是 installer-style 不是 temp-style — 存檔保留在使用者選的解壓資料夾,不會自動清。要 temp 行為改用 `7zSD.sfx` (modSFX) 但存檔會丟
- 沒包 code signing,Windows SmartScreen 第一次跑可能跳「未知發行者」警告 (按「其他資訊 → 仍要執行」)

---

## License

腳本與文件:MIT(僅限本 repo 的原創部分)
遊戲本體:SSI / Mindscape 版權,**未包含於此 repo**
教育部標準宋體:中華民國教育部
Source Han Sans:Adobe / Google,SIL Open Font License 1.1
Microsoft Tahoma:Microsoft Corporation(由使用者自備)
