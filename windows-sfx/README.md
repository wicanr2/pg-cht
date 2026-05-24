# Windows 7-Zip SFX 構建材料

把 Panzer General (繁中化版) + 已 patch 的 `WING32.DLL` + 256-color 啟動器打包成單一 `.exe`，在 Windows 10 / 11 雙擊執行：跳出對話框 → 解壓到使用者選的位置 → 自動啟動遊戲。

**只用系統內建工具：Windows 內附的 7-Zip 18+ + PowerShell 5.1 + Win32 API**，不需 NSIS / Inno Setup / rcedit / Resource Hacker / 任何第三方軟體。

## 為什麼要這個東西

`PG-cht.exe` 用 1994 年的 `WING32.DLL`，現代 Windows (32 bpp 桌面) 上：
- 畫面整片花 — WinG 預期 8-bit palette
- 每次啟動跳「WinG Installation Error」對話框 — WinG self-install 路徑檢查在 SysWOW64 環境下永遠失敗
- 過去靠手動勾 Properties → Compatibility → "Reduced color mode" 或寫 HKCU registry shim 才能跑，**綁絕對路徑、不可攜**

本資料夾的解法是 **bundled, portable, single-file**：所有相容性處理都包進 `.exe`，搬到任何 USB / Windows PC 雙擊就跑。

## 檔案

| 檔案 | 用途 |
|---|---|
| `patch_wing32.py` | 對 `WING32.DLL` 套 2-byte patch (file offset `0xA55` `75 11` → `90 90`)；含 SHA256 sanity 與 `.bak` 備份，idempotent |
| `PG-cht.cmd` | 自含啟動器：`__COMPAT_LAYER=256COLOR` env var (單行程作用域，取代 registry shim) + 啟動 PG-cht.exe |
| `stamp_icon.ps1` | 用 Win32 `UpdateResource` API 把任意 `.ico` 蓋到任意 `.exe` 的 icon 資源 (P/Invoke，不需第三方 tool) |
| `build_sfx.ps1` | 完整流程：stage → 壓 .7z (LZMA2 ultra) → 寫 config.txt (UTF-8 BOM + CRLF) → stamp icon 在 stub 副本 → concat 三段成 `.exe` |
| `Remove-256Color-Shim.reg` | 清掉舊的 HKCU `~ 256COLOR` AppCompat shim（若曾手動設過） |

## 一鍵打包

```powershell
# 預設自動找 D:\03_game_tmp\PG-cht-1.2_繁中化_* 最新版，輸出到本資料夾
powershell -ExecutionPolicy Bypass -File .\build_sfx.ps1

# 或明確指定來源 / 輸出
powershell -ExecutionPolicy Bypass -File .\build_sfx.ps1 `
  -Source D:\03_game_tmp\PG-cht-1.2_繁中化_20260523 `
  -Output D:\03_game_tmp\PanzerGeneralCHT-1.2-portable.exe
```

實測 ~42 MB 遊戲資料 → ~12 MB SFX (29% 壓縮比)，第一次解壓約 3-5 秒，主視窗 7 秒內到「裝甲元帥遊戲選項」。

## WING32.DLL 2-byte patch 原理

WinG 內部「self-install 路徑檢查」函式 (`wing32_complain` @ file offset `0xA66`)：

```asm
; before patch
call check_path           ; returns 0 if OK, nonzero if "wrong dir"
or eax, eax
jnz dialog_path           ; <-- 0xA55: 75 11
mov esi, 1                ; success path
mov eax, esi
ret
dialog_path:
  ... wsprintfA + MessageBoxA ...

; after patch (0xA55: 75 11 -> 90 90)
call check_path
or eax, eax
nop ; nop                  ; <-- 永遠不 branch
mov esi, 1                 ; 一定走 success path
ret
```

Dispatch table 維持預設，所有 WinG export (`WinGBitBlt`/`WinGCreateDC`/...) 透過內部 dispatch indirection 走正常 GDI fallback 路徑，遊戲畫面完全可用。

**禁區**：絕對不要 NOP `0xA9B` 的 `call MessageBoxA`。試過 → `0xC0000142` DllMain init failed。MessageBoxA 內部 pump messages 間接釋放 loader lock，跳過會把 DLL init 卡死。要動就動上游的 `jnz`。

## 三個關鍵雷（被解掉了）

### 1. Icon 必須先 stamp 在 7z.sfx stub 副本上，再 concat

Win32 `UpdateResource()` API 把 PE image size 當 EOF，**會截掉 appended overlay**。第一次嘗試 stamp 在合併好的 12 MB SFX exe 上 → 變成 196 KB，payload 全沒了。

正解：先複製 `C:\Program Files\7-Zip\7z.sfx` 到別處，對副本 stamp icon，**再**做三段 concat：

```
stamped 7z.sfx + config.txt (UTF-8 BOM + CRLF) + payload.7z = output.exe
```

### 2. `.ps1` 必須 UTF-8 BOM

PowerShell 5.1 (Windows PowerShell) 讀 `.ps1` 沒 BOM 時用系統 ANSI codepage (cp950 Big5 / cp936 GBK / cp932 SJIS 視 locale 而定)，腳本內含的中文檔名字面值 (`README-繁中化.txt` 等) 會 garbled，SFX 漏包檔案。

本資料夾的 `build_sfx.ps1` 已加 BOM。如果你 fork 後修改，記得保持 BOM。

### 3. SFX `config.txt` 必須 UTF-8 BOM + CRLF

開頭固定 `;!@Install@!UTF-8!`，缺 BOM 或用 LF (Unix) 行尾 → 7z.sfx 把整個 config 當 binary 略過，預設值生效（沒有 RunProgram、沒有 Title）。

`build_sfx.ps1` 動態產生 config.txt 時已正確處理 BOM + CRLF。

## 用法 (使用者端)

```
1. 雙擊 PanzerGeneralCHT-1.2-portable.exe
2. 跳出對話框「即將解壓並啟動 Panzer General」→ 按「是」
3. 選擇解壓位置（建議 USB / 任意資料夾，會建 PG-cht-1.2/ 子資料夾）
4. 等 3-5 秒解壓
5. 自動跑 PG-cht.cmd → 主視窗「裝甲元帥遊戲選項」7 秒內出現
6. 存檔保留在解壓資料夾 (installer-style，非 temp-style)
```

下次只要從解壓資料夾跑 `PG-cht.cmd` 就行，不必每次都重解 SFX。

## 偵錯小抄

| 症狀 | 原因 | 處理 |
|---|---|---|
| `0xC0000142` 立刻死 | WING32.DLL patch 失敗 / 沒套到 | 確認 SHA256 = `edd26762e7df...` |
| 「WinG Installation Error」對話框跳出來 | bundled WING32.DLL 是原版未 patch | `python patch_wing32.py <gamedir>\WING32.DLL` |
| 主視窗開了但畫面花 | `__COMPAT_LAYER=256COLOR` 沒套到 | 確認用 `PG-cht.cmd` 啟動而非直接點 `PG-cht.exe` |
| SFX 解壓後 RunProgram 沒跑 | config.txt 不是 UTF-8 BOM + CRLF | 用 hex viewer 看開頭應是 `EF BB BF` |
| SFX 大小變 196 KB | icon stamp 用在合併後的 exe | 重跑 — stamp 在 stub 副本，再 concat |
| Build script 漏包中文檔名檔案 | .ps1 沒 BOM，子 PowerShell 用 cp950 讀 | 補 BOM 重存 |

## 同類技術可套用範圍

本資料夾的 patch + bundle 流程適用任何 1994-1996 年 **WinG-based** 老遊戲，例如：

- SimCity 2000 Special Edition (Maxis, 1995)
- Civilization II (MicroProse, 1996)
- Master of Magic II (SSI, 1996，未發行 demo)
- Lode Runner: The Legend Returns (Sierra, 1994)

都會有同樣的「WinG Installation Error」+ 256-color 需求。

更廣義地：任何 Win9x 16-bit thunk-failed PE 二進位的 dialog suppression patch，都可用同一個 `jnz → nop` 手法。

## 關聯

- 全套技術知識：[`../skills/wing-portable-sfx/SKILL.md`](../skills/wing-portable-sfx/SKILL.md)
- Linux/Wine 對應路徑：[`../appimage/`](../appimage/) + [`../skills/panzer-general-wine/`](../skills/panzer-general-wine/)
- 中文化本身的知識：[`../skills/panzer-general-cht/`](../skills/panzer-general-cht/)
