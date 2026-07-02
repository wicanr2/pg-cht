# 08 逆向:TFONT1.DAT 點陣字型格式 + 繪字管線

*路徑 A(改 font 支援中文)的逆向成果與技術判斷。*

## 一句話結論

**TFONT1.DAT 是 8×8 單 byte 點陣字型**。8 pixel 高的格子**物理上塞不下可讀中文**(中文最少 12×12,理想 16×16)。即使完美 patch 繪字管線支援 Big5 2-byte,中文也會糊成一團無法辨識。這是路徑 A 的**根本硬牆**,非 patch 技巧能繞過。

## 格式完全解析(已完成)

### Header(16 bytes)

| offset | bytes | 意義 |
|---|---|---|
| 0x00 | `31 2e 00 00` | 版本字串 "1." |
| 0x04 | `00 01 00 00` | glyph 數 = 256(single byte 定址) |
| 0x08 | `08 00 00 00` | glyph 高 = **8 pixel** |
| 0x0c | `ff 00 00 00` | 最大 index = 255 |

### Offset table(0x10 起,256 × 4 bytes = 1024 bytes)

每個 entry 是該 glyph 資料在檔內的絕對 offset(little-endian uint32)。glyph 資料從 0x410 起。

```
glyph[ch] 資料 offset = read_u32(0x10 + ch*4)
glyph[ch] 資料大小     = offset[ch+1] - offset[ch]
```

### Glyph 資料(每個)

```
[4 bytes] width (little-endian uint32)
[width × 8 bytes] bitmap, 1 byte / pixel (0x00 = 背景, 0xff = 前景)
```

驗證:'A' width=7 → 4 + 7×8 = 60 bytes ✓;space width=4 → 4 + 4×8 = 36 bytes ✓

render 'A' (row-major, 8 row):
```
###..##
##....#
#..##..
#..##..
#......
#..##..
#..##..
#######
```

glyph 寬度分布:最小 4(空白/窄字)、最大 **8**。全部 ≤ 8×8。

## 繪字管線(定位完成)

### Font loader — VA `0x411aad`

```asm
0x411abe  push 0x4ce9a8        ; "%stfont1.dat" format string
0x411ac7  call 0x4b7fc0        ; sprintf 組路徑
0x411ad3  call 0x43b02f        ; open file
0x411b18  call 0x4b5eb0        ; load
0x411b20  mov  ds:0x4d637c, eax ; 存 font handle 到全域
```

font handle 全域:`0x4d637c`(主 font)。另有 `0x4d6380` / `0x5d45c0` / `0x5e21b0` 等多個 font handle,但遊戲目錄只有一個 TFONT1.DAT — 疑同檔多次載入或不同縮放。

### 繪字函式群 — VA `0x474000`–`0x47b000`

34 處引用 font handle `0x4d637c`,集中在此區。核心 blit 用 offset table 逐 char 定位 glyph、blit width×8 到 back buffer。

### Font handle NULL 檢查 — VA `0x4623b0`

多個 font handle 的 assert(`call 0x46a059` 檢查非 NULL,NULL 則報 `GetCurrentFont() = NULL in dlgout.c`)。

## 為什麼 8×8 是硬牆(第一性原理)

1. **中文筆畫密度**:一個中文字平均 10+ 筆畫。8×8 = 64 pixel 格,連「鑫」「灣」這種字的筆畫都畫不開,糊成黑塊。拉丁字母筆畫少(2-4),8×8 剛好;中文不行。
2. **single-byte 定址**:256 slot 裝不下常用中文(遊戲 UI 就用了上千不同字)。要擴充成 2-byte 定址得改 loader + offset table + 繪字 loop。
3. **改了定址仍糊**:就算 patch 成 Big5 2-byte lookup,glyph 還是只有 8×8 空間 — 治了「找得到字」治不了「看得清字」。

## 前進選項評估

### 選項 A1:拉高內部畫布(rule 81 正解)—— 極難

rule 81(retro CJK hi-res canvas)的標準解:拉高引擎內部畫布(640×480 → 1280×960)、底圖 nearest scale、CJK 用 24×24 畫在放大畫布。

**但**:rule 81 適用於**有原始碼**的 remake(openxcom / freesynd / 1oom 皆開源,改 `SCREEN_W/H` 常數即可)。本遊戲**只有 EXE**、DirectDraw exclusive fullscreen、大量硬編碼 640×480 座標。要拉高畫布得 patch:
- DirectDraw primary surface 建立(640×480 → 目標)
- 所有 blit 座標映射
- 繪字管線改用 24×24 CJK glyph
- 滑鼠命中區映射

工程量等同**在無源碼下重寫繪圖引擎**,數十 session,成功率不確定。

### 選項 A2:patch loader 支援 Big5 + 8×8 中文 —— 可做但無意義

patch 繪字 loop 偵測 Big5 lead byte、組 2-byte 查擴充 glyph table。技術可行,但**中文仍 8×8 糊到不可讀**,做了等於白做。

### 選項 B:GDI 路徑中文 + bitmap 路徑保英文(混合)—— ❌ 不存在

**已否決**。查 PACGEN.EXE import:

| GDI 繪字函式 | 有無 |
|---|---|
| `TextOutA` | ❌ |
| `DrawTextA` | ❌ |
| `ExtTextOutA` | ❌ |
| `CreateFontA` / `CreateFontIndirectA` | ❌ |
| `GetTextExtentPoint32A` | ❌ |
| `SetTextColor` | ✅(孤立,DirectDraw 相關,非繪字管線) |

遊戲**零 Windows GDI 繪字** — 所有文字(含 dialog、TIT/DES、主選單、裝備、戰場)**全走 tfont1.dat 8×8 bitmap font**。

**重要更正**:v0.1 假設「TIT/DES 走 GDI 顯示中文正常」是**錯的**。TIT/DES 也走 8×8 bitmap font,一定亂碼。使用者回報「文字還是亂碼」證實此點。**選項 B 無任何 GDI 路徑可用。**

### 選項 C:接受技術現實,UI 保英文,交付「能跑的英文原版 + 中文文件」

- 遊戲本體保英文(bitmap font 硬牆)
- 價值改放在:**能在現代 Linux/Windows 跑**(wine 三層雷已解)+ **完整中文攻略/劇本/裝備文件**(docs/ 已有)
- 誠實標示「遊戲內文字受 8×8 點陣字型限制無法中文化」

## 逆向工具

```python
# 解析 TFONT1.DAT
import struct
data = open('TFONT1.DAT','rb').read()
n = struct.unpack('<I', data[4:8])[0]      # 256
h = struct.unpack('<I', data[8:12])[0]     # 8
offs = [struct.unpack('<I', data[0x10+i*4:0x14+i*4])[0] for i in range(n)] + [len(data)]
def glyph(ch):
    o = offs[ch]; w = struct.unpack('<I', data[o:o+4])[0]
    px = data[o+4:o+4+w*h]
    return w, h, px  # px[row*w+col], 0x00/0xff
```

## 判定

8×8 bitmap font 是這款遊戲中文化的**物理性根本障礙**。RE 已把 font 格式與繪字管線完全解出,但格子尺寸決定了:**無拉高畫布(選項 A1,無源碼下極難)則遊戲內中文不可讀**。

建議與使用者確認方向:投入 A1 大工程 / 接受 C 現實 / 先驗證 B 是否有 GDI 路徑可用。
