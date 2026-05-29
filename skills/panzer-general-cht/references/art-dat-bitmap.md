# ART.DAT 點陣圖中文化 (Allied General / 盟軍元帥)

把 UI 上「烤在圖片裡」的英文（NATION / PURCHASE / PREFERENCES / EXPERIENCE …）改成中文。
這些字**不在 AG.EXE 字串表**，而是壓在 `ART/ART.DAT` (25 MB) 裡的調色盤點陣圖。
本文件記錄 2026-05-29 逆向出的封存格式、RLE 編解碼、與重繪工作流程。**這是用反組譯 AG.EXE 解碼程式確認的，不是猜的。**

## 1. ART.DAT 封存格式

```
0x00  4 bytes  00 00 00 00
0x04  4 bytes  "Indx"
0x08  4 bytes  BIG-ENDIAN u32 = index_end (例: 0x4B92)
0x0E  ...      16-byte 索引項，直到 index_end
```
索引項 (16 bytes)：`[name:4][type:4][offset:BE u32][size:BE u32]`
- **所有多 byte 數字都是 big-endian**（遊戲讀時會 byte-swap；這是找解碼程式的指紋）。
- type：`CPal`(調色盤) / `RLEi`(影像) / `Vers` / `Indx`。
- 名稱是 4-byte 代碼（如 `pYon` `aXOp` `amSn`），**不是 .bmp 檔名**。
- 統計：1208 項 = 987 RLEi + 219 CPal。

### CPal（調色盤）
資料從 chunk `off+22` 起，每色 8 bytes：`[idx:BE u16][R][R][G][G][B][B]` → RGB = (byte0, byte2, byte4)。
（每通道 byte 重複一次。一個 CPal 常含 >256 色含明暗 ramp，渲染只取 idx 0-255。）

### RLEi（影像）chunk 佈局
```
off+0   "RLEi"
off+4   BE u32 chunk_size   (index_size = 8 + chunk_size)
off+8   name(4)
off+12  palette_name(4)     ← 指向某個 CPal
off+16  00 00 00 00
off+20  BE u16  W
off+22  BE u16  H
off+26  影像資料開始（逐列）
```
（off+24..25 是第一列的長度前綴的前身/header 殘留；實務上資料指標 = off+26。）

## 2. RLE 編碼（逐列 row-based）★關鍵★

**每一列都是獨立區塊，前面有 2-byte BIG-ENDIAN 長度前綴**：
```
[BE16 rowlen][token...]    rowlen = 2 + token_bytes
```
- 解碼器用 `rowlen` 在列間 seek（cursor += rowlen）。
- 像素 token 從 `cursor + 2` 開始解，**解到該列滿 W 個像素為止**（W-driven，不是 rowlen-driven）。
- token 文法（control byte `c`）：
  | c | 動作 | 後續 | 像素數 |
  |---|---|---|---|
  | `0xFF` | 透明/跳過 n（保留背景，不寫） | 1 byte: n | n |
  | `0x80`–`0xFE`（高位元 set） | literal：複製接下來 `c & 0x7F` 個 raw byte | n=c&0x7F 個 byte | n |
  | `0x01`–`0x7F`（高位元 clear） | run：輸出 `c` 份同色 | 1 byte: 顏色 | c |
- **`0xFF` 是特例（在高位元判斷之前），不是 literal-127**。所以 literal 長度上限 = 126（編碼器**絕不可吐 0xFF/0x00 當 control byte**，否則花屏）。
- run 顏色 byte 在 count 之後。
- 一個 token 不跨列：每列 token 總和必須剛好 = W。

**遊戲解碼程式位置**（AG.EXE，ImageBase 0x400000，.text VA = file_off + 0xC00）：
- 列解碼 token loop：`0x54CF05`–`0x54D18D`
- 列 seek（讀 BE16 rowlen）：`0x54CE40`
- chunk init（存 W/H/stream ptr）：`0x54CC42`
- 還有一個 remap 變體（`obj+0x133` flag set 時把每像素過 256-byte 轉換表 `obj+0x24`），token 結構相同。

### 踩過的雷（教訓）
1. 一開始從 `off+28` 起、且**忽略每列 rowlen 前綴** → 第一列後 desync 整片花。
2. 把 rowlen 前綴誤讀成 token（如 `00 d2` 其實是 rowlen=210，不是 literal-210）→ 以為有「0x00 長 literal」。
3. 編碼器吐出 literal 長度 127 → control byte = `0xFF` → 遊戲當透明 → 花屏。**務必 literal ≤126、run ≤127、不吐 0x00/0xFF。**
4. 我的寬鬆解碼器能 round-trip 自己的輸出，但遊戲不認 → **round-trip 過不代表格式對；要反組譯遊戲解碼程式才能定案**。

## 3. 就地回填（不必重建索引）
解碼器讀完 H 列就停，**chunk 尾端多餘 bytes 被忽略**。所以只要重新編碼的 stream ≤ 原 chunk 空間 `(off+8+size) - (off+26)`，就能**原地覆寫 + 補零**，不動索引、ART.DAT 大小不變（最安全）。UI 圖重繪後通常更小，輕鬆塞下。

## 4. 重繪工作流程
1. 解碼目標 RLEi → 2D 調色盤索引陣列 + 用 CPal 算 RGB 預覽。
2. **在索引空間重繪**（不要轉 RGB 再轉回，避免色偏）：
   - 自動偵測英文標籤 bbox：在大致區域內，依亮度找出與背景差異大的像素群（亮字 on 暗底 / 暗字 on 亮底）。
   - 取 bbox 內最常見索引 = 背景色；文字像素最常見索引 = 文字色。
   - 擦除：bbox 填背景色。
   - 用 PIL 把中文 render 成遮罩，遮罩 >門檻 的像素設成文字色。
3. **字型**：`msjhbd.ttc`（微軟正黑體粗體）11px、遮罩門檻 80 → 小字清晰。MingLiU 在 <12px 沒內嵌點陣會碎。字級對齊原英文字高以保留排版。
4. 重新編碼（每列加 BE16 rowlen 前綴）→ 原地回填 → 解碼驗證像素一致。
5. **進遊戲實測**（無法靜態驗證遊戲渲染；每張都要看）。
6. 備份 `ART.DAT.bak`。還原：`Copy-Item ART.DAT.bak ART.DAT -Force`。

## 5. 已完成 / 已知座標
- `pYon` 334×450 = **PREFERENCES 偏好設定**（已中文化：偏好設定/經驗×2/聲望×2/補給/天氣/顯示部隊強度/顯示隱藏單位/顯示對手移動/取消/確定）。
- `amSn`/`rvSn`/`gfSn` 508×456 = UPGRADE UNIT 升級畫面（盟/俄/德）。
- `aRon`/`rRon`/`gRon` 448×441 = LOSSES 傷亡畫面（含 Infantry/Tank/… 兵種名烤在圖上）。
- 640×480 那 42 張是過場/劇情場景照，非 UI。
- CAMPAIGN SELECTION 主畫面 + NORTH AFRICA/WESTERN EUROPE/RUSSIA 按鈕 = bitmap（待定位）。
- UI 大寫標籤（NATION/PRIMARY/PURCHASE/PRESTIGE/APPROVED…）全是 bitmap，不在字串表。

## 6. 工具（python + Pillow + capstone，皆系統內建路徑可用）
- `_artlib.py`：load / 索引 parse / `parse_pal` / `decode_rle_v2` / `encode_stream_v2` / `patch_inplace_v2`。
- `_paintlib.py`：`Screen` class，autobox 偵測 + paint（msjhbd 11px）+ commit + preview。
- 反組譯用 capstone 5.0.7：`from capstone import Cs, CS_ARCH_X86, CS_MODE_32`。
