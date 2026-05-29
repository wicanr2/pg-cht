# PG-cht.exe PE 結構與 Patch 全紀錄

## PE 基本資訊

| 欄位 | 值 |
|------|-----|
| Image base | `0x400000` |
| Entry point RVA | `0x191016` |
| 檔案大小 | 1,984,512 bytes |
| Big5 編碼 | codepage 950(GDI 直接渲染) |

## Section 對照表

| Section | VA (RVA) | Raw offset | Size | 翻譯用途 |
|---------|----------|------------|------|---------|
| .text | `0x001000` | `0x000400` | `0x199C58` | 程式碼,內含 109 個 strcmp 指標引用,**預設不動** |
| .bss | `0x19B000` | (no raw) | `0x02C5BC` | 未初始化,無翻譯關係 |
| .rdata | `0x1C8000` | `0x19A200` | `0x01F541` | C++ RTTI / const data,通常不動 |
| .data | `0x1E8000` | `0x1B9800` | `0x10BE8` | **主要字串區**,所有資料字串都在這 |
| .idata | `0x1F9000` | `0x1CA400` | `0x0120A` | Import 表 |
| .rsrc | `0x1FB000` | `0x1CB800` | `0x010D6` | Resource |
| .reloc | `0x1FD000` | `0x1CCA00` | `0x16C2E` | 基底重定位 |

## VA / file offset 轉換公式

```
.data 區內:
  VA          = file_offset + 0x42E800
  file_offset = VA - 0x42E800

.text 區內:
  VA          = file_offset + 0x400C00
  file_offset = VA - 0x400C00
```

PowerShell:
```powershell
function FileOffToVA_data($fo) { return 0x400000 + 0x1E8000 + ($fo - 0x1B9800) }
function VAToFileOff_data($va) { return $va - 0x400000 - 0x1E8000 + 0x1B9800 }
function FileOffToVA_text($fo) { return 0x400000 + 0x1000 + ($fo - 0x400) }
```

## 已完成 .text 修補(共 13 處)

| File offset | 原始 byte | 改為 | 用途 |
|-------------|-----------|------|------|
| `0x32F4` ~ `0x330E` | `CC CC ...` (INT3) | 27 bytes 新 getter 函式 | 讀英文 Table B 副本 |
| `0x108AD-0x108B0` | rel32 to `0x12C4` thunk | rel32 to `0x32F4` | lookup caller → 英文 |
| `0xCC03C-0xCC03F` | rel32 to `0x12C4` | rel32 to `0x32F4` | lookup caller → 英文 |
| `0xCC1EF-0xCC1F2` | rel32 to `0x12C4` | rel32 to `0x32F4` | lookup caller → 英文 |
| `0xCC244-0xCC247` | rel32 to `0x12C4` | rel32 to `0x32F4` | lookup caller → 英文 |
| `0xF0D28-0xF0D2B` | rel32 to `0x12C4` | **保留**(走 0x12C4 → 原 Chinese getter) | **顯示 caller** |
| `0xF2B7C-0xF2B7F` | rel32 to `0x12C4` | rel32 to `0x32F4` | 中立 → 英文 |
| `0xF2E47-0xF2E4A` | rel32 to `0x12C4` | rel32 to `0x32F4` | 中立 → 英文 |
| `0xF337D-0xF3380` | rel32 to `0x12C4` | rel32 to `0x32F4` | 中立 → 英文 |
| `0xF3515-0xF3518` | rel32 to `0x12C4` | rel32 to `0x32F4` | 中立 → 英文 |
| `0xF36F8-0xF36FB` | rel32 to `0x12C4` | rel32 to `0x32F4` | 中立 → 英文 |

**注意**:三個原始操作數 `0xDC4F`(`28 92 5E 00`)、`0xDC9A`(`24 92 5E 00`)、`0xE19B`(`24 92 5E 00`)維持指向 Chinese Table B,因為 caller redirection 已經解決問題,這三個運算元保持原樣即可。

## 新 getter 函式(file offset 0x32F4)

```
55 8B EC 53 56 57           ; prologue
0F BF 45 08                 ; movsx eax, word [ebp+8]
8B 04 85 B4 8F 5E 00        ; mov eax, [eax*4 + 0x5E8FB4]  ← 英文 Table B 副本(1-based)
E9 00 00 00 00              ; jmp +0
5F 5E 5B C9 C3              ; epilogue
```

VA = 0x403EF4

## 戰役名稱表配置

| 角色 | 位置 | 內容 |
|------|------|------|
| 原英文字串(lookup keys) | `0x1BAC48-0x1BAEAC` | "1943 West", "Berlin (East)", ... 38 條 + 特殊值(1939, ????, LOSS, MWIN, DWIN)+ .tdb 檔名 |
| 英文指標表副本 | `0x1BA7B8` (152 bytes) | 38 個指標,皆指向上面的英文字串 |
| Big5 字串 | `0x1C8C69-0x1C8D88` (287 bytes used) | 38 條 Big5 戰役名(波蘭、華沙、莫斯科(43) 等) |
| Table A(英文,可能未用) | `0x1BA718` | 38 指標 → 原英文字串 |
| Table B(中文,顯示用) | `0x1BAA28` | 38 指標 → Big5 字串(被 0xF0D27 經 thunk 0x12C4 → getter 0xE18E 讀取) |

## 安全空間清單(.data,未使用且 0 個靜態指標引用)

按大小排序:

| File offset | Size | 狀態 |
|-------------|------|------|
| `0x1C8C69-0x1C8DD3` | 363 | **已用 287 bytes**(Big5 戰役名);剩 76 bytes 可擴充 |
| `0x1C5481-0x1C5597` | 279 | 空閒 |
| `0x1C2C2E-0x1C2D2F` | 258 | 空閒 |
| `0x1BB223-0x1BB2AB` | 137 | 空閒 |
| `0x1BA7B7-0x1BA84F` | 153 | **已用 152 bytes**(英文 Table B 副本);剩 1 byte |
| `0x1C8C69-0x1C8DD3` | (見上) | |
| `0x1BCBBF-0x1BCBFF` | 65 | 空閒 |
| `0x1BC4FE-0x1BC543` | 70 | 空閒 |

## INT3 padding(.text)清單

| File offset | Size | 狀態 |
|-------------|------|------|
| `0x32F4-0x61EF` | 12,028 | **已用首 27 bytes**(新 getter);剩 12,001 bytes 可寫新函式 |
| `0x6BC2-0x6E3F` | 638 | 空閒 |
| `0x8F99-0x96BF` | 1,831 | 空閒 |

## 已翻譯字串列表(主要)

完整清單在備份的 patch 檔 `pg_patches.txt`(若存在於 `C:\Users\原來是個胖仔\AppData\Local\Temp\`)。重要翻譯範例:

| Offset | English | Chinese |
|--------|---------|---------|
| `0x1BBED8` | End Turn | 結束回合 |
| `0x1BC544` | Panzer General | 裝甲元帥(中文版) |
| `0x1C3C20` | Quit Game | 結束遊戲 |
| `0x1C6ADC` | Continue Game | 繼續遊戲 |
| `0x1C5FD0` | Out of Memory | 記憶體不足 |
| `0x1C849C` | Panzer General | 裝甲元帥 |
| `0x1C3A5C` | DEPLOY YOUR TROOPS | 部署您的部隊 |
| `0x1BB7D4` | showing your objectives in bold relief. | 以粗體顯示您的目標. |
| `0x1BB809` | Imagine a map of Europe with big arrows moving around | 想像一張畫滿大箭頭的歐洲地圖 |

## 未翻譯(刻意保留)

- 譯者署名 `By Chun-Yu Wang (wicanr2@gmail.com)`
- 開發者彩蛋:`Jeremy Werner ...`, `Slappy the Lotboy`, `A Message From Bill`, `I love my sweet girl. :-)`
- C runtime 錯誤訊息(`- not enough space for arguments` 等)
- 子系統 callback 標籤(MIDI Callback、Sound Callback、Movie Callback)
- 國名陣列 `0x1BD528+`(可翻譯但已翻譯部分如 美國/英國/捷克/蘇聯)
- Asset 檔名(`Arrow.tdb`、`Flag.tdb`、`Scenario.tdb`、`PntInfo.tdb`)
