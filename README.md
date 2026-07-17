# SSI 5D General 系列繁體中文化 — 裝甲元帥 / 盟軍元帥 / 太平洋元帥 / 裝甲元帥2

這個 repo 收錄 SSI「5D General」六角格戰棋系列四款作品的繁體中文化:《裝甲元帥》(Panzer General, 1994)、《盟軍元帥》(Allied General, 1995)、《太平洋元帥》(Pacific General, 1997)、《裝甲元帥2》(Panzer General II, 1997)。每款都在現代環境(Ubuntu Wine / Windows 10-11)跑通,並打包成 Linux AppImage 與 Windows 單檔分發格式。

本 repo 不含遊戲本體(版權所有)、已配置的 WINEPREFIX、最終 AppImage / SFX / zip 二進位,只放可重做的腳本、構建材料、技術文件、截圖。

---

## 系列導覽

| 作品 | 年份 | 狀態 | Linux | Windows | 主要文件 |
|---|---|---|---|---|---|
| [裝甲元帥 (Panzer General)](#裝甲元帥-panzer-general) | 1994 | ✅ 完成 | ✅ AppImage | ✅ SFX / zip | 本文件 [裝甲元帥](#裝甲元帥-panzer-general) 章 + [WINE-FONT-SETUP.md](WINE-FONT-SETUP.md) |
| [盟軍元帥 (Allied General)](#盟軍元帥-allied-general) | 1995 | ✅ 完成 | ✅ AppImage(2 變體) | ✅ zip(2 變體) | [docs/allied-general.md](docs/allied-general.md) |
| [太平洋元帥 (Pacific General)](#太平洋元帥-pacific-general) | 1997 | ✅ 完成 | ✅ AppImage | ✅ zip | [pacgen/README.md](pacgen/README.md) |
| [裝甲元帥2 (Panzer General II)](#裝甲元帥2-panzer-general-ii-開發中) | 1997 | 🔨 開發中 | 🔨 wine PoC 到主選單 | — 未開始 | [pg2/README.md](pg2/README.md) |

---

## 共用資源

- **[dist-manifest.md](pacgen/docs/knowledge-base/dist-manifest.md)** — 三部曲(PG/AG/PacGen)最終發佈套件(4 版本 × 2 平台,另加 PG 含過場影片完整版)的檔名、大小、md5 校驗清單;二進位本身不進 repo,集中於建置機本地 `dist-all/`。
- **[docs/scenarios/](docs/scenarios/)** — PG/AG/PacGen 三作共 110 個劇本的歷史背景中文簡介,含逐劇本戰役分支路線圖(勝敗進哪個戰場、聲望門檻)。
- **[docs/development-cost.md](docs/development-cost.md)** — 用 COCOMO Basic 模型反推傳統開發方式需要的人月投入,並與 2026 AI-agent 工具棧的實際投入對照。
- **[WINE-FONT-SETUP.md](WINE-FONT-SETUP.md)** — Wine 環境三層字體問題(內文 / menu-caption / 應用硬呼叫字體)的完整解法,PG/AG/PacGen 共用。
- **[docs/video-plan.md](docs/video-plan.md)** — 三作宣傳短片(45-60 秒)的分鏡與素材規劃。

---

## 裝甲元帥 (Panzer General)

把 SSI 1994 Win95 老遊戲 *Panzer General*(繁中化 patch 版,`PG-cht.exe`)在現代環境(Ubuntu 24.04 Wine 9 / Windows 10/11)跑通,並分別打包成兩種 self-contained 單檔分發格式:

- **Linux AppImage** (366 MB) — Ubuntu 22.04+ 雙擊即跑,免裝 wine
- **Windows 7-Zip SFX** (~12 MB) — Windows 10/11 雙擊即跑,免裝 .NET / 任何 runtime

本 repo 不含 **遊戲本體**(版權所有)、**已配置 WINEPREFIX**(857 MB)、**最終 AppImage**(366 MB)、**最終 SFX .exe**,只放可重做的 **腳本、構建材料、技術文件、截圖**。

### 成果

| 項目 | 結果 |
|---|---|
| Wine 環境跑通 PG-cht.exe | ✅ Ubuntu 24.04 + wine 9.0 + 32-bit prefix |
| 全部中文正確顯示 | ✅ menu/對話框/按鈕/標題,字體 Source Han Sans Heavy(weight 900,粗體) |
| Self-contained Linux AppImage | ✅ 366 MB,Ubuntu 22.04+ 同等 GLIBC 環境免裝 wine 即跑 |
| Self-contained Windows SFX | ✅ ~12 MB,Win10/11 雙擊即跑,無 WinG 對話框、不寫 registry shim |
| 完整技術文件 + 構建腳本 + 領域知識 skill | ✅ 見以下目錄 |

> 原時序 6 張對照截圖已從 repo 中移除以縮小體積,僅留說明文字於 `docs/01-symptom-screenshots.md`;另補 3 張最終成果實機畫面於下方。

### 成果截圖(AppImage 實機)

完整修復後從 AppImage 啟動的 PG-cht.exe,中文(menu / 對話框 / 按鈕 / 戰役名)全部正常顯示為粗體。

| 畫面 | 內容 |
|---|---|
| ![戰役選擇對話框](docs/screenshots/00_screenshot.png) | **1939 戰役選擇對話框** — 視窗標題 `裝甲元帥(中文版)`、menu `(F)檔案 (E)編輯`、左側 1941 系列戰役按鈕、中央劇本說明 + 歐洲地圖背景,皆中文粗體。 |
| ![完整劇本列表](docs/screenshots/01_screenshot.png) | **完整劇本列表 grid** — 38 個戰役按鈕(波蘭 / 華沙 / 挪威 / 低地國 / 法國 / 海獅 / 北非 / 阿拉曼 / 高加索 / …),配合中央劇本說明對話框,證實所有戰役名稱字串都正確覆蓋。 |
| ![戰場六角格畫面](docs/screenshots/02_screenshot.png) | **進入戰場後的六角格戰術畫面** — menu `(F)檔案 (E)編輯 (G)遊戲 (V)演算`、部隊單位、地圖渲染,確認遊戲主迴圈中文亦無 □□。 |

### 快速使用

#### 方式 A1:跑現成 AppImage (Linux,若你已有 `PanzerGeneral-x86_64.AppImage`)

```bash
chmod +x PanzerGeneral-x86_64.AppImage
./PanzerGeneral-x86_64.AppImage
```

第一次啟動約 30 秒(解 prefix + 遊戲到 `~/.local/share/PanzerGeneral/`),後續秒開。

#### 方式 A2:跑現成 SFX (Windows,若你已有 `PanzerGeneralCHT-1.2-portable.exe`)

雙擊 `.exe` → 跳出對話框「即將解壓並啟動 Panzer General」→ 選解壓位置 → 解壓完自動啟動。

第一次解壓 ~12 MB → ~42 MB 大概 3-5 秒,主視窗「裝甲元帥遊戲選項」7 秒內出現。下次只要從解壓資料夾跑 `PG-cht.cmd` 即可。

#### 方式 B:從零重做整個環境

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

#### 方式 C:Windows 原生 + 自製 SFX (Win10 / 11)

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

### 三層字體問題(摘要,完整見 [`WINE-FONT-SETUP.md`](WINE-FONT-SETUP.md))

| 層 | 失敗點 | 解法 |
|---|---|---|
| **內文 (TextOutA)** | Wine ACP 不是 950 / 字體沒標 CP950 / 字體缺 CJK glyph | `LANG=zh_TW.UTF-8` 推導 ACP=950 + 字體 `OS/2.ulCodePageRange1` 補 bit 20 |
| **menu/status/caption** | Wine 對 raster `.fon` 不走 FontSubstitutes | 直接寫 binary LOGFONTW(92 bytes)到 `HKCU\Control Panel\Desktop\WindowMetrics` |
| **應用硬呼叫 Tahoma** | Microsoft Tahoma 沒 CJK glyph | 覆蓋 `tahoma.ttf` 為「Source Han Sans Heavy + 改名 Tahoma + fontRev=32767.99」 |

兩個關鍵雷:
1. Wine 同 face name 多個檔時按 `head.fontRevision` 大者勝(**與路徑無關**) → 自己改的字體要拉到 32767.99
2. AppImage 內 `/usr/bin/wine` 原版 `wine-stable` script hardcode `/usr/lib/wine/wine` 絕對路徑 → 重寫成相對路徑

### Windows 端的三個踩坑(摘要,完整見 [`windows-sfx/README.md`](windows-sfx/README.md))

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

### 環境

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

### 已知限制

**Linux/AppImage:**
- AppImage 鎖定 GLIBC 2.39+(Ubuntu 24.04 編譯的 wine),舊 distro 可能跑不起來
- 最終粗體版西文也用 Source Han Sans Heavy 黑體(非 Microsoft Tahoma 細緻字形)。要回細體版可重跑 `tools/merge-tahoma.py`
- 工作目錄含中文時 wine 會因 `LC_CTYPE` 解碼失敗;AppRun 已把遊戲解到純 ASCII 路徑避開
- 不打包 Mono / Gecko(`WINEDLLOVERRIDES=mscoree,mshtml=` 跳過)

**⚠️ WSL / new-WoW64-only wine 跑不起來(PG 與 AG 同崩,2026-05-31 實測):**
- 在 **WSL (Ubuntu 22.04/24.04)** 用 `winehq-stable` 跑 `PG-cht.exe` 或姊妹作 `AG.EXE`,thread-start 立刻 crash。`WINEDEBUG=+seh` 看到:
  - AG → `EXCEPTION_ACCESS_VIOLATION addr=0x005CB003`、PG → `addr=0x005C8010`
  - 共同指紋:崩潰 VA = `ImageBase + .rdata/DebugDir 起點`(**不是** entry point);`edx` = 該 exe 的 entry VA(已算好卻沒進去);`eax=ebx=0x7ffd1000`(TEB);fault 寫 NULL。
- **根因**:WSL 的 `winehq-stable` 是 **new-WoW64-only build**——`/opt/wine-stable/bin/wine` 是 64-bit ELF、**沒有 `wine-preloader`**,所有 32-bit exe 都走 wow64 thunk,沒有真 32-bit 執行路徑(`WINEARCH=win32` 也躲不掉)。這個 wow64 thread-start 對 1994–96 老 PE(有 `IMAGE_DEBUG_DIRECTORY`/FPO、`.bss` filesize=0)會把控制權送到 `.rdata` 開頭當 code 跑 → 撞 write-to-NULL。
- **反證(與遊戲/patch 無關)**:PG 套完整 nil-deref patch 後在 WSL **仍崩同一位址**;AG 的 Lite 版與完整版 AG.EXE **byte-identical**,WSL 同崩、但 Lite 的 AppImage 在實機真 32-bit wine 能跑。
- **解法**:用**真 32-bit wine**(要有 `wine-preloader`)——即本 repo AppImage 構建用的 Ubuntu 24.04 + Wine 9.0(`wine32:i386`)。判斷一台 wine 是否安全:`file "$(command -v wine)"` 要是 32-bit / 或同目錄有 `wine-preloader`;純 64-bit ELF 且無 preloader = wow64-only = 本雷,別在這台浪費時間。

**Windows/SFX:**
- WING32.DLL patch 只驗證過 Microsoft 12800-byte build (SHA256 `bb1f552e25...`)。其他來源的 WING32.DLL 可能 offset 不同,`patch_wing32.py` 有 SHA256 sanity 會擋下
- SFX 是 installer-style 不是 temp-style — 存檔保留在使用者選的解壓資料夾,不會自動清。要 temp 行為改用 `7zSD.sfx` (modSFX) 但存檔會丟
- 沒包 code signing,Windows SmartScreen 第一次跑可能跳「未知發行者」警告 (按「其他資訊 → 仍要執行」)

---

## 盟軍元帥 (Allied General)

*Allied General*(SSI 1995,與 Panzer General **同引擎**)的繁體中文化。針對社群「Lite v1.1」重打包版(`AG.EXE` 2,167,611 bytes),完成 EXE 字串、資料檔、**烤在點陣圖裡的 UI**、開頭畫面標題全面中文化,並修掉重打包者藏的簽名。

**完整技術細節**(遊戲簡介、中文化開頭畫面、完成項目、點陣圖 UI 中文化工作流、陣營主題 bug 連鎖、踩雷紀錄)搬到 **[`docs/allied-general.md`](docs/allied-general.md)**。快速預覽:

- ![盟軍元帥 中文化開頭畫面](docs/screenshots/ag_splash_zh.png)
- 完成項目:EXE UI 字串 + 任務簡報 + PANZEQUP.EQP 裝備名 + MAPNAMES.STR 城市名 + **烤在點陣圖裡的 UI**(共用按鈕、購買面板、戰損統計表,盟/德/俄三主題各一套變體) + 移除重打包者簽名
- 三大技術難點:RLEi 逐列 RLE 編解碼、陣營 theme classify bug、狀態列指標重導向 padding 洩漏
- 兩個 skill:[`art-dat-bitmap-cht`](skills/art-dat-bitmap-cht/SKILL.md)(點陣圖 UI)、[`panzer-general-cht`](skills/panzer-general-cht/SKILL.md)(EXE 字串)

---

## 太平洋元帥 (Pacific General)

*Pacific General* (SSI/Mindscape 1997,5D General 系列末代)的繁中化與現代環境跑通指南。歷代三大誌 1997 從沒為這款寫過中文專欄;本節是 29 年後的補完。

**完整內容都在 [`pacgen/`](pacgen/) 子目錄**:

- [`pacgen/README.md`](pacgen/README.md) — 專案總覽 + 進度表(2-byte CJK 繪字引擎讓閉源 EXE 顯示中文、AppImage 首次啟動三層雷全解)
- [`pacgen/docs/`](pacgen/docs/) — 12 篇中文化心得專欄
- [`pacgen/tools/`](pacgen/tools/) — TXT.PFP unpack/pack + glossary apply + 2-byte CJK 引擎建置腳本
- [`pacgen/translations/`](pacgen/translations/) — 33 個劇本 TIT/DES + glossary + TXT.PFP 中譯

**已 ship**:AppImage 715 MB(wine-11 內建 + DDraw fix + wineserver kill trick)+ Windows zip 353 MB,首次啟動 40 秒內主選單。字型從「8×8 點陣塞不下中文」的硬牆,突破為 **2-byte 私有編碼 + 16×16 CJK atlas** 繪字引擎(閉源 EXE 僅被動 5 個 byte),主選單 / 劇本標題 / 簡報畫面實機顯示中文,詳見 [`pacgen/docs/11-2byte-engine.md`](pacgen/docs/11-2byte-engine.md)。

---

## 裝甲元帥2 (Panzer General II) 〔開發中〕

《裝甲元帥2》(Panzer General II,SSI 1997)是 5D General 家族第四款,目標同樣是繁中化並在 Linux(AppImage)+ 現代 Windows 跑通。本章節目前為**研究 + 規劃 + 逆向工程攻堅**階段,尚未進入實作建置。

**現況**:PG2 是全新 Visual C++ / DirectDraw 引擎,與 PG1/AG 的 Borland Pascal 5D 引擎**不同源**,但畫面內點陣字與太平洋元帥同族;中文化採**寄生法語槽**(語言 ID 單 byte patch,開機直接進中文,已 wine PoC 驗證)+ 點陣字 **route C**(字高從 8 拉到 16、2-byte 私有編碼 hook,技術路徑已 PoC 綠燈);資料檔(UI / 地形 / 裝備 / 劇本地名)已 100% 完成翻譯;指揮官姓名庫已完成音譯與史實考證;Windows 打包所需 DLL 已完成盤點;**尚未開始**實際的 EXE patch 建置與封裝。

### 文件索引

| 文件 | 內容 |
|---|---|
| [`pg2/README.md`](pg2/README.md) | 專案總覽、引擎差異一句話結論、現況表 |
| [`pg2/中文化規劃.md`](pg2/中文化規劃.md) | 完整技術規劃:檔案結構、雙管線文字機制實測、字型 / 編碼 / 解析度方案、跨平台可跑性實測、§7 語言槽 + 字型雙閘門 RE 攻堅結論(PoC) |
| [`pg2/歷史百科/README.md`](pg2/歷史百科/README.md) | 歷史百科總覽、內容原則、標註慣例 |
| [`pg2/歷史百科/將領.md`](pg2/歷史百科/將領.md) | PG2 各戰役對應的真實歷史指揮官,德/蘇/英/美/芬蘭共 12 篇條目 |
| [`pg2/歷史百科/戰役.md`](pg2/歷史百科/戰役.md) | 五條戰役線、53 個劇本歷史背景考證,含架空(what-if)分支獨立說明 |
| [`pg2/歷史百科/戰役.tsv`](pg2/歷史百科/戰役.tsv) | 53 個劇本結構化清單:所屬戰役 / 順序 / 英文標題 / 中譯 / 日期 / 真實或架空 / 簡介 |
| [`pg2/歷史百科/NAMES-姓名庫.tsv`](pg2/歷史百科/NAMES-姓名庫.tsv) | `NAMES.TXT` 400 個姓氏的逐筆音譯與真實人物考證備註 |
| [`pg2/翻譯/README.md`](pg2/翻譯/README.md) | 資料檔翻譯總覽、涵蓋率、待複核項目 |
| [`pg2/翻譯/glossary.tsv`](pg2/翻譯/glossary.tsv) | 翻譯源唯一真相,2,086 筆唯一字串(UI / 地形 / 裝備 / 指揮官 / 劇本地名) |
| [`pg2/windows-dll盤點.md`](pg2/windows-dll盤點.md) | `PANZER2.EXE` 相依 DLL 盤點,Windows 打包最小集與相容風險(DirectPlay / DirectDraw) |
| [`pg2/evidence/`](pg2/evidence/) | wine 實測截圖:640×480×8 抵達標題畫面、DirectDraw 切模式失敗案例 |

---

## 目錄結構

```
pg-cht/
├── README.md                       # 你正在看的這份(系列導覽 + 四作專章)
├── WINE-FONT-SETUP.md              # 三層字體問題 + 解法詳解
│
├── docs/                           # 系列共用文件
│   ├── allied-general.md           # 盟軍元帥 (AG) 完整中文化技術文件
│   ├── development-cost.md         # COCOMO 開發成本估算 + AI 工具棧壓縮倍率
│   ├── video-plan.md               # 三作宣傳短片分鏡規劃
│   ├── 01-symptom-screenshots.md   # □□ → 正常 → 粗體 → AppImage 時序敘事
│   ├── screenshots/                # PG 3 張成果截圖 + AG 前後對照 5 張
│   ├── video/                      # 宣傳片素材(字幕等)
│   └── scenarios/                  # 三作 110 個劇本歷史簡介 + 戰役分支路線圖
│       ├── README.md               # 索引與譯名規範
│       ├── pg.md / ag.md / pacgen.md               # 三作劇本歷史簡介(逐劇本)
│       ├── pg-scenarios.tsv / ag-scenarios.tsv / pacgen-scenarios.tsv
│       ├── campaign-routes-pg.md / -ag.md / -pacgen.md  # 戰役分支路線圖
│       ├── campaign-mod-playbook.md    # 戰役改造方法論(從 Kursk mod 萃取)
│       └── kursk-mod-ag.md             # issue #4:AG 蘇軍路線加 Kursk 劇本
│
├── pacgen/                         # 太平洋元帥中文化子專案(獨立 README + docs)
│   ├── README.md                   # 進度表 + 2-byte CJK 繪字引擎
│   ├── CONTEXT.md                  # 譯名 glossary
│   ├── docs/                       # 12 篇心得專欄 + wine 啟動配方 + knowledge-base/
│   ├── tools/                      # pfp_split/pack + 2-byte 引擎建置 + apply_glossary + dump_pe_strings
│   └── translations/               # 33 劇本 TIT/DES + TXT.PFP 中譯
│
├── pg2/                             # 裝甲元帥2 中文化子專案(開發中,研究 + 規劃階段)
│   ├── README.md                   # 專案總覽 + 現況表
│   ├── 中文化規劃.md                # 完整技術規劃 + §7 RE 攻堅結論(PoC)
│   ├── windows-dll盤點.md           # PANZER2.EXE 相依 DLL 盤點
│   ├── 歷史百科/                    # 真實歷史指揮官 + 戰役背景考證
│   │   ├── README.md, 將領.md, 戰役.md, 戰役.tsv, NAMES-姓名庫.tsv
│   ├── 翻譯/                        # 資料檔翻譯源 + 套用工具
│   │   ├── README.md, glossary.tsv, apply_translations.py, extract_scenario.py, build_size_report.py
│   └── evidence/                   # wine 實測截圖(標題畫面、DirectDraw 障礙)
│
├── tools/                          # 全系列共用工具
│   ├── setup-wine.sh               # 一鍵裝 wine + 建 prefix + DPI=136
│   ├── merge-tahoma*.py             # 字型 merge (v1 細體 / v2 粗體)
│   ├── replace-tahoma.py           # 覆蓋字型進 prefix
│   ├── rename-fonts.py             # 改 face name (mingliu/pmingliu/simsun 別名)
│   ├── write-menufont.py           # binary LOGFONTW 改 menu/caption
│   ├── scenarios_to_md.py          # 劇本 TSV → MD 轉換(docs/scenarios/ 用)
│   ├── fontforge.Dockerfile        # docker fontforge 環境
│   ├── art-dat/                    # AG ART.DAT (RLEi 點陣圖 UI 中文化)
│   └── video/                      # 宣傳片素材錄製 (Xvfb + wine + ffmpeg x11grab)
│       ├── capture_pacgen.sh       # PacGen 主選單/劇本畫面自動錄影
│       └── make_pg_intro.sh / make_ag_intro.sh / make_pacgen_intro.sh / make_pacgen_video.sh
│
├── appimage/                       # PG Linux AppImage 構建材料
│   ├── README.md, AppRun, *.desktop, *.png
│   ├── wine-portable.sh            # 取代 /usr/bin/wine (原版 hardcode 路徑)
│   ├── wineserver-portable.sh, wineserver-dispatcher.sh
│   └── build.sh                    # 一鍵打包 .AppImage
│
├── windows-sfx/                    # PG Windows 7-Zip SFX 構建材料
│   ├── README.md                   # SFX 設計筆記 + WING32 patch 原理
│   ├── patch_wing32.py             # 對 WING32.DLL 套 2-byte patch (suppress dialog)
│   ├── PG-cht.cmd                  # 自含啟動器 (__COMPAT_LAYER=256COLOR)
│   ├── stamp_icon.ps1, build_sfx.ps1
│   └── Remove-256Color-Shim.reg
│
└── skills/                         # 領域知識 skill (Claude Code agent 可 invoke)
    ├── panzer-general-cht/SKILL.md      # PG/AG EXE 字串 + 資料檔中文化 (含 AG runtime)
    ├── panzer-general-wine/SKILL.md     # wine 啟動 (PG pgs.dll 256 色 bypass + AG shim)
    ├── art-dat-bitmap-cht/SKILL.md      # AG ART.DAT RLEi 點陣圖 UI 中文化
    ├── retro-directdraw-hires-cjk/SKILL.md  # DirectDraw 8×8 點陣字 CJK route C(PacGen/PG2 共用)
    └── wing-portable-sfx/SKILL.md       # Windows 原生 + SFX 打包 (WING32 patch)
```

> `dist-all/`(最終發佈套件二進位)不進 git,只存在建置機本地;清單見 [共用資源](#共用資源) 的 dist-manifest.md。

---

## License

腳本與文件:MIT(僅限本 repo 的原創部分)
遊戲本體:SSI / Mindscape 版權,**未包含於此 repo**
教育部標準宋體:中華民國教育部
Source Han Sans:Adobe / Google,SIL Open Font License 1.1
Microsoft Tahoma:Microsoft Corporation(由使用者自備)
