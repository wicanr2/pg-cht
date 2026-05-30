---
name: wing-portable-sfx
description: 接續 1994-1996 年 WinG-based Win9x 遊戲在現代 Windows 10/11 上的相容性處理 + 包成單檔 portable .exe 的工作。當使用者提到 WinG / WING32.DLL、「WinG Installation Error」對話框、Panzer General / SimCity 2000 / Civilization II / Master of Magic II / Lode Runner 等 1990s WinG 遊戲在 Win10/11 跑不動或畫面花掉、字型在高 DPI 螢幕變粗/糊(同 EXE 換資料夾粗細不一)、要切換 256 色相容模式、想加 GDIDPISCALING/DPIUNAWARE 旗標、想擺脫 HKCU AppCompat registry shim、把舊遊戲整包成單一可雙擊 portable .exe (放隨身碟)、7-Zip SFX (7z.sfx) 自製、icon stamping、UTF-8 BOM 編碼問題時都觸發。也涵蓋同類 Win9x 16-bit thunk-failed PE binary patch、只用系統內建工具 (7z + PowerShell P/Invoke) 不裝任何第三方 tool 製作 self-extractor 的技術。
---

# WinG-based Win9x Game Portable Packaging

接續 2026-05-17 在 D:\03_game_tmp\PG-cht-1.2_繁中化_20260517 + D:\03_game_tmp\_sfx_build 完成的「PG-cht.exe 自含啟動 + 單檔 SFX」工作的技術知識。**先讀完此 SKILL.md 再決定動手**;可重用腳本在 `scripts/`。

## 兩個合在一起的技術主題

### A. WinG-based 遊戲在現代 Windows 上的相容性

**症狀**:1994-1996 年代用 WinG 1.0 API (`WING32.DLL`) 的遊戲在 Win10/11 上:
- 畫面整片花掉 / 黑畫面 — 桌面是 32 bpp 但 WinG 預期 8-bit palettized DIB
- 啟動時跳「WinG Installation Error」MessageBox(每次都跳)
- 或者 process 直接 0xC0000142 (`STATUS_DLL_INIT_FAILED`) 死掉

**症狀根因**:
- WinG 1.0 是 1994 年寫的,所有 surface 都是 8-bit palettized,且會 thunk 到 16-bit `WING.DLL` 取得最大效能
- 64-bit Windows 沒有 16-bit 子系統,thunk16 init 必然失敗
- WinG 的「自我安裝路徑檢查」預期 DLL 住在 `C:\Windows\System` (Win9x 16-bit system dir),不認得 SysWOW64 → 跳 dialog
- 32 bpp 桌面下 WinG palette 無效 → 畫面花
- Win10/11 內附的 `C:\Windows\SysWOW64\WING32.DLL` 是 Microsoft 12,800-byte build (與 System32 / System 副本同一個檔案,SHA256 `bb1f552e25...`),exports 完整,有 fallback dispatch path 但仍會跳 dialog

### B. 用系統內建工具做單檔 SFX

**目標**:把整包遊戲 (含 patched DLL、launcher、資料夾結構) 打成單一 `.exe`,雙擊跳 prompt → 解壓到使用者選的位置 → 自動跑遊戲。**不裝 NSIS / Inno / rcedit / Resource Hacker / 任何第三方 tool**,只用 Windows 內建 + 7-Zip 內附的 stub。

## 完整解法 (三步驟)

### Step 1: WING32.DLL 2-byte patch

從 `C:\Windows\SysWOW64\WING32.DLL` 複製出來 (是 32-bit DLL,系統 redirect 規則決定),套這個 patch:

| file offset | 原值 | 改成 | 意義 |
|---|---|---|---|
| 0xA55 | `75 11` (jnz +0x11) | `90 90` (nop nop) | path-check 失敗時 jump 到 dialog 區段 → 改成永遠 fall through 走 success path return 1 |

效果:WinG 內部 "self-install 路徑檢查" 永遠視為通過,不呼叫 MessageBoxA;dispatch table 維持預設,所有 WinG export 透過內部 dispatch indirection 走正常路徑,遊戲畫面完全可用。

**驗證**:
- Pre-patch SHA256:`BB1F552E2525E784B61D2FE0CA23F3402ADEC05AA5F92F4C1DFBEA3966A84CBB`
- Post-patch SHA256:`EDD26762E7DFD37C5A4306698C77D1A0C4C1F7E734946B3B82C534FAC13065F6`
- 用 `scripts/patch_wing32.py <path>`(含 SHA256 sanity 與 .bak 備份)

**禁區**:**絕對不要 NOP `0xA9B` 的 `call MessageBoxA`** — 我試過。MessageBoxA 內部會 pump messages,間接釋放 DllMain loader lock,跳過會 0xC0000142 死掉。要動就動上游的 jnz。

### Step 2: 自含式啟動器 (.cmd)

```cmd
@echo off
setlocal
cd /d "%~dp0"
set "__COMPAT_LAYER=GDIDPISCALING DPIUNAWARE 256COLOR"
PG-cht.exe %*
endlocal
```

`__COMPAT_LAYER` env var 等效於 Properties → Compatibility 勾選的相容旗標,可**空白分隔多個 layer**,但**單行程作用域、不寫 registry**。
- `256COLOR` = "Reduced color mode" 8-bit(WinG palette 必備)。
- `GDIDPISCALING DPIUNAWARE` = "高 DPI 設定 → 覆寫縮放:系統" + DPI-unaware。

**★高 DPI 螢幕字型變粗/糊的坑(2026-05-30, Allied General 踩到)**:
只給 `256COLOR`、缺 DPI 兩個旗標時,在高 DPI 桌面上 Windows 會對遊戲 GDI 文字做 DPI 虛擬化放大 → 筆畫糊成**粗體**(戰場/選單文字尤其明顯)。加上 `GDIDPISCALING DPIUNAWARE` 走乾淨 bitmap 路徑保留原始細筆畫 → crisp。
- 症狀極具迷惑性:同一份 EXE + 同一份資料檔,A 資料夾粗、B 資料夾細 → **元兇不是檔案,是兩個 EXE 路徑各自的 `HKCU\...\AppCompatFlags\Layers` 旗標不同**(用內建相容性對話框「切 256 色」只會寫進 `256COLOR`,不帶 DPI)。先查 registry Layers 再懷疑字型/資產。
- **實測確認 `__COMPAT_LAYER` env var 認 DPI 旗標**(`GDIDPISCALING`/`DPIUNAWARE`,非只認 `256COLOR`)→ 用 .cmd 啟動器即可純可攜帶齊三旗標,毋須 registry。
- 若改走 registry(非可攜)：完整值是 `~ GDIDPISCALING DPIUNAWARE 256COLOR`;`reg add "HKCU\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" /v "<full path>\X.EXE" /t REG_SZ /d "~ GDIDPISCALING DPIUNAWARE 256COLOR" /f`。

**為什麼用 .cmd 不寫 HKCU registry**:
- registry shim 綁絕對路徑 — 遊戲搬位置就失效
- 跨機器/USB 不能用
- 寫 SFX/AppImage 包進去無法傳給 child process

**比較**:
- `start "" PG-cht.exe %*` — async,cmd window 立刻關。**不要用在 SFX 內部 launcher** — SFX 會以為 RunProgram 已結束,把解壓檔案清掉,遊戲還在跑就 crash
- `PG-cht.exe %*` (無 start) — sync,cmd 等遊戲關才退出。**SFX 內部用這個**
- `start /WAIT "" PG-cht.exe %*` — 兩者妥協,但 cmd window 還在

### Step 3: 7-Zip SFX 三段 concat

```
最終 .exe = 7z.sfx (stamped icon) + config.txt (UTF-8 BOM + CRLF) + payload.7z
```

**用系統內附 7-Zip 18.01 (C:\Program Files\7-Zip\):**
- `7z.exe` — 壓縮
- `7z.sfx` — GUI installer-style stub(預設 195072 bytes)

**Config 範例**(`UTF-8 BOM + CRLF` 必備):
```
;!@Install@!UTF-8!
Title="..."
BeginPrompt="..."
ExtractPathTitle="..."
ExtractDialogText="..."
Progress="yes"
Directory="..."
RunProgram="PG-cht.cmd"
;!@InstallEnd@!
```

**壓縮指令**:
```powershell
& "C:\Program Files\7-Zip\7z.exe" a -t7z -m0=lzma2 -mx=9 -ms=on -mfb=64 -md=64m -mqs=on -mmt=on payload.7z stage\*
```

LZMA2 ultra + solid archive + qsort,~42 MB 遊戲資料可壓到 ~12 MB (29%)。

**合併指令**:
```powershell
cmd /c "copy /b 7z-stamped.sfx + config.txt + payload.7z output.exe"
```

## 三個我必須記住的踩坑(都踩過了)

### 1. Icon 必須先 stamp 在 7z.sfx stub 副本上,再 concat

Win32 `UpdateResource()` API 把 PE image size 當 EOF,**會截掉 appended overlay**。也就是說:
- ✗ 對「合併好的 12 MB SFX exe」call UpdateResource → 變成 196 KB,payload 全沒了
- ✓ 先複製 `7z.sfx` 到別處,對副本 stamp icon,**再**做三段 concat → OK

### 2. PowerShell 腳本檔案本身必須 UTF-8 BOM

`Write` tool 預設無 BOM。PowerShell 5.1 (Windows PowerShell) 讀 .ps1 沒 BOM 時用系統 ANSI codepage (cp950 Big5 / cp936 GBK / cp932 SJIS 視 locale 而定),所以腳本內含的中文檔名/字串字面值 (`README-繁中化.txt` 等) 會 garbled,SFX 漏包檔案。

**Fix**:`build_sfx.ps1` 存檔後立刻補 BOM:
```powershell
$content = [System.IO.File]::ReadAllBytes($path)
$bom = [byte[]](0xEF,0xBB,0xBF)
[System.IO.File]::WriteAllBytes($path, $bom + $content)
```

### 3. SFX config.txt 必須 UTF-8 BOM + CRLF

config.txt 開頭固定要 `;!@Install@!UTF-8!`,如果缺 BOM 或用 LF (Unix line ending),7z.sfx 把整個 config 當 binary 略過,結果預設值生效(沒有 RunProgram、沒有 Title 等)。

**Fix**:
```powershell
$crlf = $configText -replace "`r?`n", "`r`n"
$bom  = [byte[]](0xEF,0xBB,0xBF)
[System.IO.File]::WriteAllBytes($config, $bom + [System.Text.Encoding]::UTF8.GetBytes($crlf))
```

### 4. BOM 是看「誰要讀檔」決定的,規則剛好相反

整理一下因為這次踩到三種:

| 檔案 | Reader | 要不要 BOM? |
|---|---|---|
| `.ps1` | PowerShell 5.1 (Windows PowerShell) | **要**。沒 BOM 預設用 ANSI codepage 讀,中文字面值會 garbled |
| `.ps1` | PowerShell 7+ (pwsh) | 不要也 OK(預設 UTF-8),但加了也相容 |
| `config.txt` for 7z.sfx | 7z.sfx stub | **要 BOM + CRLF**,不然 config 被略過 |
| `SKILL.md` | Claude 的 skill loader | **絕對不要 BOM**。YAML frontmatter 解析器需要 `---` 在 byte 0,加了 BOM 整個 frontmatter 解析失敗,description 變成 `---` |
| `.py` | Python 3.x | BOM 可有可無(Python 3 預設 UTF-8 開檔且容忍 BOM) |

實作上:打包用的 `build_sfx.ps1` 必須是 UTF-8 BOM(編譯期);它輸出的 `config.txt` 必須是 UTF-8 BOM(runtime 給 7z.sfx 讀);但這個 SKILL.md 是純 UTF-8 不加 BOM。同一份工作流產生的東西,對「BOM 是否該存在」的答案三種不同。

## Bundled scripts

| script | 用途 |
|---|---|
| `scripts/patch_wing32.py` | 套 WING32.DLL 2-byte patch (含 SHA256 sanity + .bak 備份,可雙向偵測「已 patched」狀態,idempotent) |
| `scripts/build_sfx.ps1` | 完整 stage → 壓 .7z → 寫 config → stamp icon → concat 流程 (含上述三個踩坑全處理)。**已含 UTF-8 BOM** |
| `scripts/stamp_icon.ps1` | 獨立的 icon stamper,給其他 .exe 用 (不限於 SFX)。**用前需 `powershell -ExecutionPolicy Bypass`** |

## 操作流程速查

### 給 X 遊戲套這套(X = SimCity 2000 / Civ II / 其他 WinG game)

1. 確認 X.exe import `WING32.DLL`(用 PE viewer 或 grep import table)
2. 從 SysWOW64 複製 WING32.DLL 到遊戲目錄,跑 `python scripts/patch_wing32.py <gamedir>\WING32.DLL`
3. 寫對應 X.cmd launcher(改 exe 名稱即可)
4. 啟動測試 — 應該無 dialog、無 0xC0000142、主視窗應該開
5. 包 SFX:跑 `powershell -ExecutionPolicy Bypass -File scripts/build_sfx.ps1 -Source <gamedir> -Output <out.exe>`(注意改裡面 `$includeFiles` / `$includeDirs` 對應 X 的結構)

### 偵錯小抄

| 症狀 | 原因 | 處理 |
|---|---|---|
| 0xC0000142 立刻死 | WING32.DLL patch 失敗 / 沒套到 | 確認 SHA256 = `edd26762e7...` |
| 「WinG Installation Error」對話框跳出來 | bundled WING32.DLL 是原版未 patch | 重跑 patch script |
| 主視窗開了但畫面花 | `__COMPAT_LAYER=256COLOR` 沒套到 | 確認用 .cmd 啟動而非直接點 .exe;確認 cmd 沒寫成 `start ""` 變 async 後 env var 已釋出 |
| 字型變粗/糊(高 DPI 機),同 EXE 換資料夾粗細不一 | 缺 `GDIDPISCALING DPIUNAWARE`,只有 `256COLOR` | env var 補成 `GDIDPISCALING DPIUNAWARE 256COLOR`;或查 `HKCU\...\AppCompatFlags\Layers` 該 exe 路徑旗標 |
| SFX 解壓後 RunProgram 沒跑 | config.txt 不是 UTF-8 BOM + CRLF | 用 hex viewer 看開頭三 byte 應是 EF BB BF |
| SFX 大小變 196 KB | icon stamp 用在合併後的 exe | 重跑 — stamp 在 stub 副本,再 concat |
| Build script 漏包中文檔名檔案 | .ps1 沒 BOM,子 PowerShell 用 cp950 讀 | 補 BOM 重存 |

## 替代/擴充方向

### 用 modSFX (7zsfx.info) 取代 7-Zip 內附 7z.sfx

若需要 temp-extract-and-cleanup 行為(像 AppImage 一樣不留檔案在磁碟),可下載 `7zSD.sfx`。但會失去存檔持久性 — 遊戲存檔寫在 temp 目錄被清掉。**對需要存檔的遊戲不適合**。

### AppImage (Linux/Wine) 路徑

同套 patched WING32.DLL 在 Wine 下也能用,但 Wine 有 builtin wing32 stub,預設會覆寫 native。要強制用 native 加 `WINEDLLOVERRIDES="wing32=n,b"`。

AppRun 範例:
```bash
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
export WINEPREFIX="${XDG_DATA_HOME:-$HOME/.local/share}/<game>/prefix"
export WINEARCH=win32
export WINEDLLOVERRIDES="wing32=n,b"
[ -d "$WINEPREFIX" ] || wineboot --init
cd "$HERE/usr/share/game"
exec wine <game>.exe "$@"
```

打包:`appimagetool AppDir/ <Game>-x86_64.AppImage`

## 預期觸發場景

- WING32.DLL 任何相關問題(missing / Installation Error / 畫面花)
- Panzer General / SimCity 2000 / Civilization II / Master of Magic II / Lode Runner 等 1994-1996 WinG 遊戲在 Win10/11 跑不動
- 想擺脫 HKCU AppCompat registry shim、做 portable 啟動器
- 把 Win9x 遊戲包成單檔 .exe (USB / 雙擊就跑)
- 7-Zip SFX 製作問題(config 沒生效 / icon 沒換 / 解壓後檔案少)
- PowerShell 腳本中文 garbled(隱含問題:.ps1 沒 BOM)
- 同類 PE 二進位 16-bit thunk-failed patch(WinG 也是這類典型,本 skill 的 jnz→nop 手法可套用到其他類似情境)

## 詞彙約定

- **patch** 不譯,指 binary hex patch
- **stub** 不譯,指 7z.sfx 這種 self-extractor 前置 PE
- **dispatch table** 維持原文(WinG 內部術語)
- **thunk16** 維持原文(Win32→Win16 thunk)
- **overlay** 維持原文(PE 後綴的非 PE 內容,如 SFX payload)
