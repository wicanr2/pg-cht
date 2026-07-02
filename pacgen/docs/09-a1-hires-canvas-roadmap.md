# 09 A1 路線圖:拉高內部畫布支援 24×24 CJK

*rule 81(retro CJK hi-res canvas)在**只有 EXE**的閉源遊戲上的落地路線。Phase 0 地基已驗證。*

## 為什麼走 A1

見 [08-tfont-re.md](08-tfont-re.md):TFONT1.DAT 是 8×8 點陣字,物理上塞不下可讀中文。rule 81 正解 = 拉高內部畫布(640×480 → 1280×960)、底圖 nearest scale、CJK 用 24×24 畫在放大畫布。

## Phase 0:可行性偵察 + 地基驗證 ✅ 完成

### SetDisplayMode 是單一控制點

```asm
0x40cdf8  push 8         ; bpp = 8 (256 色 paletted)
0x40cdfa  push 0x1e0     ; height = 480
0x40cdff  push 0x280     ; width = 640
0x40ce11  call [eax+0x54]; IDirectDraw::SetDisplayMode(640,480,8)
```

**單一呼叫點**(file offset 0x40cdfa / 0x40cdff)。

### 地基實驗:patch mode → 1280×960

patch 兩個 push(480→960, 640→1280)後:

- ✅ 遊戲**不 crash**,window 從 640×480 變成 **1280×960**
- ✅ back buffer 內容仍在(頂部一條線有像素)
- ⚠️ 但畫面**全擠到頂部一條** — 經典 **stride mismatch**:遊戲用 640 stride 寫 back buffer,DirectDraw 用 1280 stride 讀 → 每行橫向壓縮 + 換行錯位

**結論**:改 mode 可行不 crash(A1 生死線通過)。stride 是核心工作。

### stride / back buffer 偵察數據

| pattern | 次數 | 意義 |
|---|---|---|
| `IDirectDraw::SetDisplayMode` | **1** | 解析度設定,已 patch 驗證 |
| back buffer size `307200` (640×480) | **5** | malloc / clear 點 |
| `×5 << 7` (=×640, `shl reg,7`) | **9** | stride 計算(部分,含非 stride ×128) |
| `push 640` | 2 | surface 建立參數 |
| dword `640` 全部 | 30 | 含常數比較 / 邊界 |
| dword `480` 全部 | 27 | 同上 |

**關鍵判斷**:stride 計算**可枚舉**(~9-30 處),非海量散布。back buffer 5 處。這比「無源碼下無限大」樂觀 — A1 是**紮實但有限的多 session 工程**,非不可能。

## A1 完整路線圖(Phase 1-5)

### Phase 1:back buffer 放大 + stride 修正 —— 中難度(~2-3 session)

1. back buffer malloc 640×480 → 1280×960(5 處 `307200` → `1228800`)
2. stride ×640 → ×1280(~9-30 處 `×5<<7` 逐一 RE 判斷真 stride vs 常數)
3. SetDisplayMode 已 patch
4. **驗證里程碑**:畫面填滿 1280×960 不再擠頂部(即使內容仍 640×480 排版縮在左上)

### Phase 2:底圖 nearest ×2 放大 —— 高難度(~3-5 session)

- pixel art(按鈕、背景、單位圖,存 SHP.PFP)blit 時 nearest ×2
- 找 SHP 解碼 + blit 迴圈,插入 ×2 放大(每 pixel 寫 2×2 塊)
- 座標 ×2(UI 元素定位)
- **驗證里程碑**:原版畫面 crisp 放大到 1280×960,如同 640×480 但 2 倍大

### Phase 3:font 24×24 + Big5 2-byte —— 中難度(~2-3 session)

- 重烤 TFONT1.DAT 成 24×24(或另一 CJK atlas)
- 繪字 loop(VA 0x474000-0x47b000)改認 24 高
- lead byte 0x81-0xFE 偵測 → Big5 2-byte lookup 到 CJK atlas
- ASCII 仍走原 8×8(或同步放大到 16 高配合)
- **驗證里程碑**:中文在放大畫布上 24×24 清晰可讀

### Phase 4:座標映射細節 —— 中難度(~1-2 session)

- 滑鼠命中區 ×2(hit-test 座標)
- minimap / 特殊 raw 座標 widget 單獨處理(rule 81 踩雷:別重複套 mapX/Y)
- 對話框 / 選單 widget 定位

### Phase 5:整合 + 打包測試 —— (~1 session)

- crisp(nearest)版 ship
- 選配 smooth(bilinear)版
- 打包 AppImage + Windows zip

## 總估

**~10-14 session**,各 phase 有明確驗證里程碑(不是黑箱)。Phase 1 完成即見「填滿大畫布」,Phase 2 見「crisp 放大」,Phase 3 見「中文可讀」。

風險:Phase 2(底圖 blit ×2)最重,SHP.PFP 解碼 + blit 迴圈的 RE 深度未知。若 blit 是單一共用函式則可控,若散布則升級難度。

## Phase 0 產出檔案

- font 格式 + 繪字管線 RE:[08-tfont-re.md](08-tfont-re.md)
- SetDisplayMode patch 點:file 0x40cdfa(height) / 0x40cdff(width)
- 地基實驗腳本(patch mode)已驗證於 fresh source hardlink

## 下一步(Phase 1 起點)

1. 反組譯 5 處 `307200` back buffer malloc,確認結構
2. 逐一 RE 9 處 `shl reg,7` 判斷哪些是真 stride
3. patch back buffer + stride,驗證「填滿畫布」里程碑
