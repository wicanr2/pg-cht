---
name: retro-directdraw-hires-cjk
description: 把「只有 EXE、無原始碼」的閉源 DirectDraw exclusive-fullscreen 老遊戲(1990s Win95/98)拉高內部畫布解析度,讓 CJK 中文能用 24×24 點陣清晰顯示(而非被 8×8 bitmap font 塞成亂碼)。用 RE + binary patch 實現,非改常數。當使用者談到「老遊戲中文糊掉/亂碼」「8×8 點陣字塞不下中文」「DirectDraw 老遊戲拉高解析度」「拉高畫布 CJK」「SetDisplayMode patch」「present stretch」「閉源 EXE 中文化字型太小」等情境觸發。實證於 Pacific General (SSI 1997)。
---

# retro-directdraw-hires-cjk — 閉源 DirectDraw 老遊戲拉高畫布支援 CJK

## 這個 skill 解決什麼(跟其他的區隔)

| 資源 | 場景 | 手法 |
|---|---|---|
| **本 skill** | **閉源 EXE**、DirectDraw exclusive fullscreen、8×8 bitmap font 塞不下中文 | **RE + binary patch** 拉高畫布 + font 高解析 |
| rule `81-retro-cjk-hires-canvas` | **有原始碼**的 remake (openxcom / freesynd / 1oom 皆開源) | 改 `SCREEN_W/H` 常數 + nearest scale |
| skill `panzer-general-wine` | 老遊戲在 wine 下**啟動**(256 色、exNilPtr) | wine prefix + shim.dll + registry |
| skill `art-dat-bitmap-cht` | UI 文字**烤在點陣圖檔**裡 (ART.DAT) | 解碼/重繪/回填 RLE 點陣圖 |

**核心區隔**:rule 81 是「有源碼改常數」的通則;本 skill 是它在**沒有源碼、只有 EXE**時的落地 —— 拉高畫布的每一個常數/呼叫點都要**反組譯定位 + hex patch**,而非改一行 `#define`。

## 為什麼需要拉高畫布(第一性原理)

老 DirectDraw 遊戲的字型常是 **8×8 單 byte 點陣**(`TFONT1.DAT` 之類)。第一性事實:

1. **8×8 格子物理上塞不下可讀中文**。中文平均 10+ 筆畫,8×8=64 pixel 連「灣」「鑫」都糊成黑塊。拉丁字母筆畫少(2-4),8×8 剛好;中文不行。
2. **single-byte 定址 256 slot** 裝不下常用中文(遊戲 UI 上千不同字)。
3. **就算改成 Big5 2-byte lookup,8×8 仍糊** —— 治了「找得到字」治不了「看得清字」。
4. **判斷遊戲是否零 GDI 繪字**:查 import 有無 `TextOutA`/`DrawTextA`/`CreateFontA`。全無 = 所有文字走自訂 bitmap font,wine 字型代換無效,只能拉高畫布。

正解(rule 81 的維度轉換):拉高內部畫布(640×480 → 1280×960),底圖 pixel art 用 nearest 放大保持銳利,CJK 用 24×24 畫在放大後的畫布。

## font 格式逆向(Pacific General TFONT1.DAT 實證,可靠)

自訂點陣字型格式解剖:

```
Header 16 bytes:
  0x00  版本字串 "1."
  0x04  glyph 數 = 256 (single-byte 定址)
  0x08  glyph 高 = 8 pixel
  0x0c  最大 index = 255
Offset table (0x10 起, 256 × 4 bytes):
  glyph[ch] 資料 offset = read_u32(0x10 + ch*4)
Glyph 資料 (每個):
  [4 bytes] width (little-endian)
  [width × 8 bytes] bitmap, 1 byte/pixel (0x00 背景 / 0xff 前景)
```

render 驗證:'A' width=7 → 4+7×8=60 bytes;把 pixel 逐 row 印 `#`/`.` 應看到可辨字形。這確認格式理解正確,也確認 height=8 是硬牆(塞不下中文)。

## RE 流程(閉源 EXE,依序做)

### Step 1:定位 SetDisplayMode(單一控制點)—— 已驗證

DirectDraw 設解析度走 `IDirectDraw::SetDisplayMode(w, h, bpp)`,vtable offset **0x54**。靜態找 `push bpp; push height; push width; call [vtable+0x54]`。

Pacific General 實證:VA `0x40cdf8`(`push 8`/`push 0x1e0`(480)/`push 0x280`(640)/`call [eax+0x54]`),唯一呼叫點。

**地基實驗(生死線,已驗證)**:patch 兩個 push 到目標解析度(1280×960),跑遊戲。實測 window 變 1280×960、**不 crash** → A1 可行。若 crash 表示 surface 建立跟 mode 綁太死。

### Step 2:動態 trace 確認 present 機制(關鍵,別靠靜態猜)—— 已驗證

**靜態猜 vtable offset 會出錯**(0x14 在不同 COM 介面是 Blt / SetEntries / 別的)。用動態:

```bash
WINEDEBUG=+ddraw wine explorer /desktop=X,WxH ./GAME.EXE >log 2>&1
grep -a 'surface1_Blt' log | grep -av null    # present Blt + dst/src rect
grep -a 'SetDisplayMode\|CreateSurface' log
grep -ac 'Lock'  log                           # 有無 Lock (區分機制)
```

判讀:每幀穩定重複 `Blt dst_rect(0,0)-(w-1,h-1) src=back_buffer flags DDBLT_WAIT` = **present 是 DirectDraw Blt**(可 StretchBlt);大量 `Lock`/`Unlock` = 可能軟體 copy(改 stride,較難)。

Pacific General 實證:6976 行 trace 確認 present = DirectDraw Blt(`dst_rect(0,0)-(639,479) src=back buffer DDBLT_WAIT`),**否定了曾誤判的「Lock+copy」**。教訓:vtable offset 歧義一定用動態 trace 破。

### Step 3:找 present Blt 的尺寸來源

present Blt 用 `DDBLT_WAIT`(flags `0x1000000`)。靜態指紋搜:

```python
import re
for m in re.finditer(rb'\x68\x00\x00\x00\x01', exe):  # push 0x1000000
    print(hex(m.start()-0x400+0x401000))
```

通常唯一一處。往上找建 `RECT{0,0,w,h}` 的 stack mov + `call [reg+0x14]`(Blt vtable);再往上找 caller,present 尺寸常是 caller push 的立即數。

Pacific General 定位(靜態,待與動態最終交叉確認):present Blt 疑在函式 `0x40d640` 一帶,尺寸由 caller `0x40d5b0` push(`0x40d5eb`/`0x40d5f0` 的 640/480),dst=primary 全域 `0x4e6518`。

## Phase 1:present stretch(畫面放大填滿)

最省力的成果 —— **改極少處讓 DirectDraw 硬體 StretchBlt**:

1. SetDisplayMode → 目標解析度
2. present blit 的 **dst 尺寸 → 目標解析度,src 保持原尺寸** → DirectDraw 自動 stretch(nearest = crisp)

Pacific General 候選 patch(4 個 word,SetDisplayMode + present caller 尺寸 640×480 → 1280×960)。⚠ **此 Phase 1 stretch 的最終畫面驗證需在乾淨 session 重跑確認**(SetDisplayMode 地基與 present=Blt 機制已確認,但 4-word 完整 stretch 的畫面成果尚未在無干擾環境定案)。

### ⚠ dst/src rect 共用陷阱

若 present Blt 的 dst_rect 和 src_rect **指向同一個 RECT struct**(`lea eax,[rect]; push` 兩次同位址),直接改 RECT 會讓 **src 也變大 → 從小 back buffer 讀越界 → 畫面壞**。解法擇一:
- **改 caller push 的尺寸**(若 present 用傳入尺寸建 dst rect,src 另從 surface desc 讀)
- dst_rect 設 **NULL**(用整個 dst surface)+ src_rect 保留小尺寸;但 wine 某些版本 dst=NULL+src_rect 不 stretch 只放左上,需實測(Pacific General 實測 dst=NULL 只修好 stride mismatch、未 stretch)
- 分離兩個 RECT(EXE stack 空間常不夠放第二個 16-byte RECT)

### present 多層陷阱

present 常是多層:`render buffer → 中間 640×480 surface → primary`。改錯層只修好 stride mismatch 不 stretch。確認你改的 Blt 的 **dst 是 primary**(對照 CreateSurface 的 `DDSCAPS_PRIMARYSURFACE` 全域)。

## Phase 3:font 24×24(中文清晰的關鍵,最重,待實作)

Phase 1 stretch 後 font 仍 `8×8 → 16×16`(糊)。要清晰,font glyph 必須在高解析層以 24×24 畫:

1. 確認 glyph 尺寸來源:繪字管線讀 font header height(可改)還是硬編(反組譯繪字核心,Pacific General 繪字函式群 VA `0x474000`-`0x47b000`,34 處引用 font handle `0x4d637c`)
2. font atlas 換 24×24(TTF → 點陣 subset,見 `build_cjk_font.py`)
3. 繪字 loop patch:認新 glyph 高 + Big5 lead byte(0x81-0xFE)偵測 → 2-byte lookup;ASCII 走原路徑
4. 座標:font 24×24 畫在已放大的高解析畫布

⚠ Phase 3 vs Phase 1 stretch 的張力,兩條整合路徑:
- **A(rule 81 標準)**:back buffer 拉到 1280×960、底圖 blit nearest ×2、font 直接 24×24。工程大(所有繪圖座標 + 底圖 blit ×2)。
- **B(font 半尺寸)**:font 在 640×480 back buffer 畫 12×12,經 present stretch ×2 → 24×24 顯示。省力但 UI 一行字數變少、排版會擠。

## 關鍵陷阱(RE 紀律)

- **wine session 髒污誤導 RE**:多輪 patch/revert/kill 後 wineserver 累積髒狀態,連 baseline 都偶發 crash → 誤判成檔案問題。**每次 fresh source hardlink(`cp -al`)+ `wineserver -k` + fresh 目錄**才可信。
- **`page fault @ ASCII-looking 位址`(如 0x54484320=" CHT")= 隨機記憶體垃圾**,別追字面 pattern;真因是上一步 parser 讀了什麼當 pointer。
- **靜態 vtable offset 歧義** → 動態 `+ddraw` trace 破。
- **原版 EXE 絕不就地改**:實驗全在 `/tmp` 或 `~/` 的 fresh hardlink dir,原版留底。
- **/tmp 會被自動清**:要保留的截圖/log 存 repo 或 `~/`,別留 `/tmp`。

## 工具與手法

- **capstone**(`pip install capstone`)掃指紋:`push 0x1000000`(DDBLT_WAIT)、`call [reg+0x14]`(Blt)、SetDisplayMode 立即數、`push 0x280`/`0x1e0`(640/480)
- **objdump** `-d -M intel -m i386 -j .text --start-address=VA` 反組譯
- **WINEDEBUG=+ddraw** 動態確認 present(靜態撞牆時對症)
- **Xvfb / host :N + explorer /desktop wrapper** 隔離跑 + 截圖(避免搶主機解析度)
- **VA↔file**:PG 系列 `file = VA - 0x401000 + 0x400`(ImageBase 0x400000, .text VA 0x1000 raw 0x400)

## 何時套用 / 何時不

**套用**:閉源 DirectDraw exclusive-fullscreen 老遊戲、8bpp paletted、自訂 bitmap font、中文塞不下、無源碼。

**不套用**:有源碼的 remake(用 rule 81)、走 GDI TextOut(wine 字型代換)、文字烤在點陣圖(art-dat-bitmap-cht)、只要「啟動」不是「拉高」(panzer-general-wine)。

## Reference case

- **Pacific General (SSI/Mindscape 1997)** — 本 skill 實證來源。`pacgen/docs/08-tfont-re.md`(TFONT 8×8 RE + 硬牆判定,可靠)、`09-a1-hires-canvas-roadmap.md`(SetDisplayMode 地基 + present=Blt 動態確認 + Phase 1 路線圖)。**已確認**:font 格式、SetDisplayMode 單點 patch 不 crash、present = DirectDraw Blt。**待乾淨 session 定案**:Phase 1 完整 4-word stretch 的畫面成果、Phase 3 font 24×24。
- 配套:rule `81-retro-cjk-hires-canvas`(有源碼版)、skill `panzer-general-wine`(wine 啟動)、`retro-game-remake`(打包)、字型烘製 `build_cjk_font.py`。
