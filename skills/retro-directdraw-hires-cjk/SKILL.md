---
name: retro-directdraw-hires-cjk
description: 把「只有 EXE、無原始碼」的閉源 DirectDraw exclusive-fullscreen 老遊戲(1990s Win95/98)拉高內部畫布解析度,讓 CJK 中文能用 24×24 點陣清晰顯示(而非被 8×8 bitmap font 塞成亂碼)。用 RE + binary patch 實現,非改常數。當使用者談到「老遊戲中文糊掉/亂碼」「8×8 點陣字塞不下中文」「DirectDraw 老遊戲拉高解析度」「拉高畫布 CJK」「SetDisplayMode patch」「present 放大」「閉源 EXE 中文化字型太小」等情境觸發。方法論實證於 Pacific General (SSI 1997) 進行中。
---

# retro-directdraw-hires-cjk — 閉源 DirectDraw 老遊戲拉高畫布支援 CJK

> ⚠️ **本 skill 是方法論框架。** 具體遊戲的「present 走 Blt 還是 Lock+copy」「哪個 VA 是 present」「改幾處讓畫面放大」等**結論**,一律要在**乾淨、可靠的 wine + 截圖環境**當場做出來,不要照抄任何「先前得出的具體答案」。方法可靠,結論要現做現驗。

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

1. **8×8 格子物理上塞不下可讀中文**。中文平均 10+ 筆畫,8×8=64 pixel 連「灣」「鑫」都糊成黑塊;拉丁字母筆畫少,8×8 剛好。
2. **single-byte 定址 256 slot** 裝不下常用中文。
3. **就算改成 Big5 2-byte lookup,8×8 仍糊** —— 治了「找得到字」治不了「看得清字」。
4. **判斷遊戲是否零 GDI 繪字**:查 import 有無 `TextOutA`/`DrawTextA`/`CreateFontA`。全無 = 所有文字走自訂 bitmap font,wine 字型代換無效,只能拉高畫布。

正解(rule 81 的維度轉換):拉高內部畫布,底圖 pixel art 用 nearest 放大保持銳利,CJK 用 24×24 畫在放大後的畫布。

## font 格式逆向(純靜態,可靠)

自訂點陣字型格式解剖(以 Pacific General TFONT1.DAT 為例,靜態確認):

```
Header 16 bytes:  版本字串 / glyph 數(256) / glyph 高(8) / 最大 index(255)
Offset table (0x10 起, 256 × 4 bytes): glyph[ch] 資料 offset = read_u32(0x10 + ch*4)
Glyph 資料: [4 bytes width][width × height bytes bitmap, 1 byte/pixel 0x00背景/0xff前景]
```

render 驗證:取一個 ASCII glyph 逐 row 印 `#`/`.`,應看到可辨字形 → 確認格式理解正確,也確認 height(常 8)是硬牆。**這是純靜態 RE,可靠。**

## RE 流程(閉源 EXE,依序做 —— 方法可靠,結論當場驗)

### Step 1:靜態定位 SetDisplayMode

DirectDraw 設解析度走 `IDirectDraw::SetDisplayMode(w, h, bpp)`,vtable offset **0x54**。靜態找 `push bpp; push height; push width; call [vtable+0x54]`,通常唯一呼叫點。搜 height/width 立即數(如 640=0x280 / 480=0x1e0)交叉定位。**這步純靜態,可靠。**

### Step 2:改 mode 是否 crash(生死線,當場驗)

fresh source hardlink + patch 兩個 push 到目標解析度,跑遊戲:
- 不 crash → A1 可行,繼續
- crash → surface 建立跟 mode 綁太死,A1 風險高

⚠ 這步要看遊戲跑起來,**當場用可靠環境驗**,別信任任何「先前說不 crash」的結論。

### Step 3:動態確認 present 機制(關鍵,別靠靜態猜 vtable)

**靜態猜 vtable offset 會出錯**(0x14 在不同 COM 介面是 Blt / SetEntries / 別的)。用動態:

```bash
WINEDEBUG=+ddraw wine explorer /desktop=X,WxH ./GAME.EXE >log 2>&1
grep -a 'surface1_Blt' log | grep -av null    # present Blt + dst/src rect
grep -a 'SetDisplayMode\|CreateSurface' log     # surface 尺寸
grep -ac 'Lock' log                             # 有無 Lock (區分機制)
```

判讀:每幀穩定重複 `Blt dst_rect(0,0)-(w-1,h-1) src=back_buffer flags DDBLT_WAIT` = present 走 **DirectDraw Blt**(可能 StretchBlt);大量 `Lock`/`Unlock` = 可能 **software copy**(改 stride,較難)。⚠ 這是**當場 trace 判讀的方法**,不是預設答案。

### Step 4:找 present 尺寸來源

若 present 走 Blt,用 `DDBLT_WAIT`(flags `0x1000000`)當靜態指紋:

```python
import re
for m in re.finditer(rb'\x68\x00\x00\x00\x01', exe):  # push 0x1000000
    print(hex(m.start()-0x400+0x401000))
```

往上找建 `RECT{0,0,w,h}` 的 stack mov + `call [reg+0x14]`(Blt vtable);再往上找 caller,present 尺寸常是 caller push 的立即數。定位後**再用動態 trace 交叉確認**才算數。

## 放大手法(依 present 機制選,當場驗證每一步)

### 若 present 走 DirectDraw Blt

概念:SetDisplayMode → 目標解析度 + present blit 的 **dst 尺寸 → 目標解析度,src 保持原尺寸** → DirectDraw 自動 StretchBlt(nearest = crisp)。

**⚠ dst/src rect 共用陷阱**:若 present Blt 的 dst_rect 與 src_rect 指向**同一個 RECT**(`lea eax,[rect]; push` 兩次同位址),直接改 RECT 會讓 src 也變大 → 從小 back buffer 讀越界 → 畫面壞。解法擇一,每個都要**當場截圖驗**:
- 改 caller push 的尺寸(若 present 用傳入尺寸建 dst,src 另從 surface desc 讀)
- dst_rect 設 NULL(用整個 dst surface)+ src_rect 保留小尺寸;但 wine 某些版本 dst=NULL+src_rect 可能不 stretch 只放左上,**須實測**
- 分離兩個 RECT(EXE stack 空間常不夠放第二個 16-byte RECT)

**present 多層陷阱**:present 常是多層(`render buffer → 中間 surface → primary`)。改錯層只修好 stride mismatch 不放大。確認你改的 Blt 的 **dst 是 primary**(對照 CreateSurface 的 `DDSCAPS_PRIMARYSURFACE` 全域)。

### 若 present 走 Lock + software copy

改 copy loop:用 Lock 回傳的實際 `lPitch`(surface desc)當 dst stride + nearest ×2(每 src pixel 寫 dst 2×2),而非硬編舊寬度。較繁瑣但可控。

## font 24×24(中文清晰的關鍵,最重)

放大後 font 仍是舊尺寸(8×8 → 放大糊)。要清晰,font glyph 必須在**高解析層以 24×24 畫**:

1. 確認 glyph 尺寸來源:繪字管線讀 font header height(可改)還是硬編(反組譯繪字核心)
2. font atlas 換 24×24(TTF → 點陣 subset,見 `build_cjk_font.py`)
3. 繪字 loop patch:認新 glyph 高 + Big5 lead byte(0x81-0xFE)偵測 → 2-byte lookup;ASCII 走原路徑
4. 座標:font 24×24 畫在已放大的高解析畫布

兩條整合路徑:
- **A(rule 81 標準)**:back buffer 本身拉到高解析、底圖 blit nearest ×2、font 直接 24×24。工程大。
- **B(font 半尺寸)**:font 在原 back buffer 畫 12×12,經放大 ×2 → 24×24 顯示。省力但 UI 一行字數變少、排版會擠。

## 關鍵陷阱(RE 紀律)

- **wine session 髒污誤導 RE**:多輪 patch/revert/kill 後 wineserver 累積髒狀態,連 baseline 都偶發 crash → 誤判成檔案問題。**每次 fresh source hardlink(`cp -al`)+ `wineserver -k` + fresh 目錄**才可信。
- **不穩環境的「成果」不算數**:若 tool 輸出出現污染(命令結果自我重複、pid/log 讀數矛盾)、或截圖無法可靠判讀,**當下所有「跑起來看畫面」的結論一律作廢**,換乾淨環境重做。這是本 skill 的第一守則。
- **`page fault @ ASCII-looking 位址`(如 0x54484320=" CHT")= 隨機記憶體垃圾**,別追字面 pattern。
- **靜態 vtable offset 歧義** → 動態 `+ddraw` trace 破。
- **原版 EXE 絕不就地改**:實驗全在 `/tmp` 或 `~/` 的 fresh hardlink dir,原版留底。**`/tmp` 會被自動清**,要保留的截圖/log 存 repo 或 `~/`。

## 工具與手法

- **capstone**(`pip install capstone`)掃指紋:`push 0x1000000`(DDBLT_WAIT)、`call [reg+0x14]`(Blt)、SetDisplayMode 立即數、`push 0x280`/`0x1e0`(640/480)
- **objdump** `-d -M intel -m i386 -j .text --start-address=VA` 反組譯
- **WINEDEBUG=+ddraw** 動態確認 present(靜態撞牆時對症)
- **Xvfb / host :N + explorer /desktop wrapper** 隔離跑 + 截圖(避免搶主機解析度)
- **VA↔file**:image base 0x400000、.text VA 0x1000 raw 0x400 → `file = VA - 0x401000 + 0x400`

## 何時套用 / 何時不

**套用**:閉源 DirectDraw exclusive-fullscreen 老遊戲、8bpp paletted、自訂 bitmap font、中文塞不下、無源碼。

**不套用**:有源碼的 remake(用 rule 81)、走 GDI TextOut(wine 字型代換)、文字烤在點陣圖(art-dat-bitmap-cht)、只要「啟動」不是「拉高」(panzer-general-wine)。

## Reference case

- **Pacific General (SSI/Mindscape 1997)** — 本 skill 方法論來源,**進行中**。
  - **已靜態確認(可靠)**:`TFONT1.DAT` 8×8 格式(`pacgen/docs/08-tfont-re.md`)、SetDisplayMode 單點靜態定位 VA `0x40cdf8`(`09-a1-hires-canvas-roadmap.md`)、解析度常數 capstone 掃描可枚舉。
  - **待乾淨環境定案(先前結論已作廢)**:改 mode 是否 crash、present 機制(Blt vs Lock+copy)、放大手法、font 24×24。先前在不穩環境得出的「present stretch」具體結論已從路線圖移除,需重做。
- 配套:rule `81-retro-cjk-hires-canvas`、skill `panzer-general-wine`、`retro-game-remake`、字型烘製 `build_cjk_font.py`。
