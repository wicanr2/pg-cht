# 《裝甲元帥2》Windows 打包 DLL 盤點

目標:PG2 中文版在**現代 Windows(10/11)**雙擊即跑。本文盤點 `PANZER2.EXE`(中文化目標,2D 版)的相依 DLL,分類「隨遊戲附帶 / 系統內建 / 中文化新增」,列出必須進 zip 的檔與相容風險。

**方法**:直接解析各 PE 的 import 目錄(`scratchpad/pe_imp.py`),非靠猜測。標註 **[已測]** = import table 實際讀出;**[待實測]** = 需真機現代 Windows 驗。ImageBase `0x400000`。

---

## 1. PANZER2.EXE 相依鏈 [已測]

**靜態 import(載入期必須全部解析,缺一則 EXE 起不來):**

```
PANZER2.EXE
├─ 系統:KERNEL32 USER32 GDI32 comdlg32 ole32 DDRAW WSOCK32 WINMM DPLAYX
├─ mss32.dll        (Miles 音效,隨遊戲)
├─ smackw32.DLL     (Smacker 過場影片,隨遊戲)
└─ clubdll.dll      (SSI 線上俱樂部,隨遊戲)── 靜態鏈:
      └─ GAMECHAT.dll ── chatsock.dll
              └─ 系統:WINSPOOL.DRV COMCTL32 SHELL32 ADVAPI32 GDI32 comdlg32 USER32 KERNEL32 WSOCK32
```

> 注意:`clubdll→gamechat→chatsock` 這條**線上對戰**鏈雖是離線遊玩用不到的功能,但因是 `PANZER2.EXE` 的**靜態** import(非 delay-load),三個 DLL 在載入期就必須存在,否則 loader 直接報錯。→ **三個都要隨包**。

**動態載入(LoadLibrary,非載入期 import):**
- `english.dll`:語言 DLL(僅十餘條錯誤訊息字串),由 INI `[language] dll=english.dll` 鍵在執行期載入。中文化維持寄生法語槽但 INI 仍指 `english.dll`(見 [`中文化規劃.md`](中文化規劃.md) §7),避免「Cannot Load Language .DLL」→ **要隨包**。

**PANZER2.EXE 不 import `msvcrt`** [已測]:VC++ 靜態鏈 CRT,故 `MSVCRT20/40/MSVCRT.DLL` 非 EXE 或遊玩 DLL 所需(掃 clubdll/gamechat/chatsock/mss32/smackw32 均不 import msvcrt),推測是安裝程式(`MSRUN32.EXE`/`reg.exe`)時代的執行期,**遊玩包可省**。

---

## 2. 分類與「是否隨包」總表

| DLL | 來源 | 現代 Windows 有? | 隨包? | 說明 |
|---|---|---|---|---|
| **mss32.dll** | 隨遊戲 | ✗ | **✔ 必須** | Miles Sound System,靜態 import |
| **smackw32.dll** | 隨遊戲 | ✗ | **✔ 必須** | Smacker 影片,靜態 import |
| **clubdll.dll** | 隨遊戲 | ✗ | **✔ 必須** | 靜態 import,缺則 EXE 不載入 |
| **gamechat.dll** | 隨遊戲 | ✗ | **✔ 必須** | clubdll 靜態鏈 |
| **chatsock.dll** | 隨遊戲 | ✗ | **✔ 必須** | gamechat 靜態鏈 |
| **english.dll** | 隨遊戲 | ✗ | **✔ 必須** | LoadLibrary 動態載;錯誤訊息字串 |
| ddraw.dll | 系統 | ✔(相容層) | ✘(見風險) | DirectDraw;256 色全螢幕有相容問題 |
| **dplayx.dll** | 系統(舊) | **✗ 預設無** | **✔ 必須(僅 Windows 包)** | DirectPlay,靜態 import。**決定隨包**避免缺 DLL;AppImage 不放(wine 自帶) |
| kernel32 / user32 / gdi32 | 系統 | ✔ | ✘ | 標準系統 |
| comdlg32 / ole32 / winmm | 系統 | ✔ | ✘ | 標準系統 |
| wsock32 / advapi32 / shell32 | 系統 | ✔ | ✘ | 標準系統 |
| comctl32 / winspool.drv | 系統 | ✔ | ✘ | 標準系統(gamechat 鏈用) |
| msvcrt.dll | 隨遊戲/系統 | ✔(系統版) | ✘(可選附) | 現代 Windows 內建;遊玩非必需 |
| msvcrt20.dll / msvcrt40.dll | 隨遊戲 | ✗ | ✘ | 舊 VC 執行期,推測僅安裝程式用 |
| winsock.dll | 隨遊戲 | — | ✘ | 16-bit Winsock,EXE 用的是 32-bit wsock32(系統);不需 |

---

## 3. 必須進 zip 的檔(遊玩最小集)[已測]

中文化目標 `PANZER2.EXE`(已 patch:語言 byte + `.cjk` 節 + hook)加以下 **7 個隨附 DLL**(Windows 包):

```
PANZER2.EXE   (中文 patch 版)
mss32.dll  smackw32.dll  clubdll.dll  gamechat.dll  chatsock.dll  english.dll
dplayx.dll    ← 決定隨包(現代 Windows 預設無 DirectPlay,靜態依賴缺則 EXE 不載入)
+ PANZER2.DAT(含 16px FONTFRA)、*.fra 資料檔、SCENARIO/、SOUND/ 等遊戲資料
```

- 其餘系統 DLL(kernel32/user32/gdi32/ddraw/comdlg32/ole32/winmm/wsock32/advapi32/shell32/comctl32…)**不放進包**——現代 Windows 內建。
- **AppImage(Linux)不放 `dplayx.dll`**:wine 有自帶實作,放 native 版反而可能不相容。dplayx 隨包**只針對 Windows zip**。

---

## 4. 相容風險與待實測(現代 Windows)[待實測]

這些不是「缺 DLL」而是「行為相容」,是「能不能在現代 Windows 跑」的真正變數,需真機驗:

1. **DirectPlay(`dplayx.dll`)—— 已定案:隨 Windows 包附帶**:`PANZER2.EXE` 靜態 import 它,但 Windows 8/10/11 **預設不裝** DirectPlay(屬「舊版元件」選用功能)。缺它 → EXE 直接起不來。**決定:把 `dplayx.dll` 放進遊戲目錄一起打包**(Windows 的 DLL 搜尋順序:應用程式目錄優先於系統目錄,且 dplayx 非 KnownDLL,故 local 版會被優先載入),使用者免手動啟用舊版元件。實作待驗:
   - **取得來源**:用與 PG2 同世代、相容的 `dplayx.dll`(如 DirectX 舊版 redist / Win98–XP 版本);確認其**自身 import**(主要 kernel32/user32/advapi32/ole32,皆現代系統有)在現代 Windows 能解析,不再拖出缺檔。
   - **驗證**:真機起遊戲能到主選單(單機戰役),確認單機功能不受影響(對戰功能非本包目標)。
   - **僅 Windows 包**:AppImage(Linux)**不放**此 native DLL——wine 自帶 dplayx 實作,放 native 版反而可能不相容。
2. **DirectDraw 256 色全螢幕(`ddraw.dll`)**:PG2 是 640×480×8bpp exclusive fullscreen,與 AG/PacGen 同類議題。現代 Windows 對 8bpp 全螢幕調色盤支援不佳,且 Win10/11 已移除「256 色」相容性選項。對策(待實測):
   - dgVoodoo2 之類 DirectDraw→Direct3D 包裝(放一份 `ddraw.dll` wrapper 到遊戲目錄);或視窗化 / 相容性模式。
   - 這是「畫面正不正常」的關鍵,不是載入問題;需真機測。
3. **DPI/縮放**:啟動有「Small Fonts / 96 DPI」提示框(EXE 內字串,非致命)。高 DPI 螢幕可能需「停用顯示縮放」相容設定。

---

## 5. 中文化本身不新增任何 DLL [已測/設計]

- CJK 字庫(atlas)烤進 `PANZER2.EXE` 的 `.cjk` 節,**不需外部字型 DLL**。
- 畫面內點陣字走自訂 hook + atlas;GDI 對話框走系統 CJK 字型(現代 Windows 內建),對話框 charset 在 EXE `.rsrc` 設定即可,**不隨包字型**。
- PG2 **不用 WinG** → 不像 PG1 需 `WING32.DLL` + `shim.dll`。故 PG2 的 Windows 包**不需 WinG/shim 這類中文化附加 DLL**。

---

## 6. 與三部曲 Windows 包的差異

| 項目 | PG1《裝甲元帥》 | PG2《裝甲元帥2》 |
|---|---|---|
| 繪圖 | WinG(256 色 DIB) | DirectDraw 8bpp |
| 中文化附加 DLL | `WING32.DLL`(patch)+ `shim.dll`(256 色) | 無(atlas 烤進 EXE) |
| 載入期外部相依風險 | WinG | **DirectPlay(dplayx)** |
| 音效/影片 | — | mss32 + smackw32(隨附) |
| 線上元件相依鏈 | 無 | clubdll→gamechat→chatsock(靜態,必隨包) |

---

## 7. 建議打包結構(待字型/EXE 建置完成後定案)

```
PanzerGeneral2-CHT-windows.zip
└─ Panzer General 2 CHT/
   ├─ PANZER2.EXE            ← 中文 patch 版
   ├─ mss32.dll smackw32.dll clubdll.dll gamechat.dll chatsock.dll english.dll
   ├─ dplayx.dll             ← 隨包(已定案,避免現代 Windows 缺 DirectPlay)
   ├─ (視風險 2 決定是否附 dgVoodoo2 ddraw.dll)
   ├─ PANZER2.DAT *.fra SCENARIO/ SOUND/ SFX/ Smack/ MAP/ …(遊戲資料)
   ├─ 啟動說明.txt(DirectPlay 啟用 / 相容性設定指引)
   └─ (視需要)啟動.cmd(設相容性環境)
```

> DirectPlay 與 DirectDraw 兩項需在真實現代 Windows 上實測後,才能定「隨包 dplayx/ddraw wrapper」還是「引導使用者設定」。Linux AppImage 端由自帶 wine prefix 處理,無此二風險。
