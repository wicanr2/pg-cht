# 12 逆向:word-wrap 繪字模組(第二 CJK hook 目標)

*承 [11-2byte-engine.md](11-2byte-engine.md)。drawString 路徑已 hook 並實機驗證;本文記錄**另一條**繪字路徑 —— word-wrap 模組 `0x4ab000`–`0x4af800` —— 的靜態 RE,供實機驗證後實作第二 hook。VA→file = VA − 0x400c00。*

## 為什麼有第二條路徑

drawString(`0x428312`)畫單行短字串。多行、需斷行的文字(戰鬥內任務簡報 dialog、文字輸入框 label)走 word-wrap 模組:它**自己走 byte、自己排版、直接 `call drawGlyph@0x42817f`**,不經 drawString,所以 drawString hook 蓋不到。

## 模組地圖(反組譯確認)

| 函式 | VA 範圍 | 角色 |
|---|---|---|
| **`0x4ab976`** | 0x4ab976–0x4abf45 | **FILL+MEASURE**。走原字串(`[ebp+8]`)、word-wrap 斷行、把 char+color 寫進 2D grid `0x4e1a60`(char)/`0x4e1ae0`(color),row stride 258。含 prompt 提的所有參考點(0x4ab99e/9a1/9e7、0xaba7e、0xabaaf)。 |
| **`0x4abf46`** | 0x4abf46–0x4ac3b3 | **RENDER**(劇本簡報 dialog)。LOOP2 畫標題(call@0x4ac0f9),**LOOP3 畫段落本體(inner 0x4ac2e9,call@0x4ac36b)= 主 CJK 目標**。 |
| `0x4ae807` | – | 文字輸入 dialog(label + edit buffer,call@0x4ae9ae/0x4aea3e)。 |
| `0x4aeaa0` | – | **純數字**輸入(key filter 0x30–0x39);文字走 drawString,call 只畫游標 `0x5f`。**無 CJK 關聯**。 |
| `0x4af2af` | – | 自由文字輸入(key filter `≥0x20`,可打 CJK);文字走 drawString,call 只畫游標。游標位置預量測對 CJK 會偏 —— 次要 bug。 |

## RENDER 迴圈關鍵指令(主目標 LOOP3)

| 角色 | VA | 指令 |
|---|---|---|
| char read(feeds ch) | 0x4ac346 | `mov dl,[eax+ecx*1+0x4e1a60]` |
| char read(terminator) | 0x4ac2fe | `mov dl,[eax+ecx*1+0x4e1a60]` |
| col advance(要 +2) | 0x4ac382 | `inc BYTE[ebp-0xc]`(`FE 45 F4`) |
| drawGlyph call | 0x4ac36b | — |
| width accumulate | 0x4ac373–0x4ac37e | `add eax,ecx; mov [ebp-0x1c],ax` |

raw 未翻譯 char byte(`edx`,push@0x4ac34d)直接進 drawGlyph 的 `ch`(`[ebp+0x18]`);drawGlyph `shl eax,2` 前**無 mask/truncate**,故 `ch` 可 >255 —— 正好支援傳 dense 碼(與 drawString hook 同理)。

## FILL 迴圈關鍵指令

| 角色 | VA | 指令 |
|---|---|---|
| char read(measure) | 0x4abca0 | `mov dl,[eax+ecx*1]` |
| char read(store) | 0x4abccc | `mov al,[eax+ecx*1]` |
| store char → grid | 0x4abce2 | `mov [ecx+edx*1+0x4e1a60],al` |
| store color → grid | 0x4abcff | `mov [ecx+edx*1+0x4e1ae0],al` |
| col advance | 0x4abd06 | `inc BYTE[ebp-0xc]`(`FE 45 F4`) |
| src cursor advance | 0x4abd09 | `inc WORD[ebp-0x1c]`(`66 FF 45 E4`) |

## 安全性

- **無 signed-load 陷阱**:所有 char byte 讀取皆 zero-extend(`xor reg,reg; mov dl,[...]`),無 `movsx`。~150 個 `movsx` 都是 WORD 座標/flag,不碰字元 byte。
- **控制碼比較全 `<0x81`**:`cmp edx,0x9/0xa/0x20/0x40/0x2a` 皆 equality(`je`/`jne`),lead byte 0x81-0x86(129-134)前向永不衝突。

## 已知風險:backtrack 斷詞(連續 CJK 無空格)

overflow 時 `0x4abd6d`–`0x4abe06` 逐 byte 往回找空格斷行。連續 CJK 無空格 → 走到行首仍找不到 → "word too long" 錯誤路徑(`0x4abdef` → dialog `0x46010f`/`0x4b8350`),**除非** caller 設 hard-wrap flag(bit3 `[ebp+0x14]`,test@0x4abd5e)。此風險**在 hook 前就存在**(自訂碼 DES 進 FILL 即觸發)。

**緩解**:劇本 DES 加手動 `\n` 讓每行 ≤ dialog 寬(FILL 認 `\n`@0x4aba7e 斷行),就不 overflow、不 backtrack。反向的 trail byte(Big5 trail 可含 0x40='@'/0x20)在 backtrack 方向的碰撞也一併避開。

## 建議 hook(兩個 5-byte jmp,乾淨邊界)

1. **FILL `0x4abc93`**(file `0xab093`):覆寫 `8B 45 E4 25 FF`(`mov eax,[ebp-0x1c]` + `and` 頭 2 byte;尾 3 byte 孤立不可達,唯一 inbound `jne@0x4abc7e` 正好落 0x4abc93)。stub:source byte 0x81-0x86 → 讀 trail、算 dense、寫 lead+trail 進 grid[col]/[col+1](color 複製兩格)、col+2、src+2;否則原路徑。都 `jmp 0x4abd0d`。
2. **RENDER `0x4ac2e9`**(file `0xab6e9`):覆寫 `33 C0 8A 45 F4`(`xor eax,eax` + `mov al,[ebp-0xc]`,乾淨邊界無孤立;inbound `je@0x4ac2b7`/`jmp@0x4ac385` 皆落 0x4ac2e9)。stub:重算 col/line、讀 grid;0 → `jmp 0x4ac38a`;lead 0x81-0x86 → 讀 grid[col+1] trail、算 dense、`call drawGlyph(...,font=atlas,ch=dense)`、width accumulate、col+2、`jmp 0x4ac2e9`;否則 fall through 原 0x4ac30d(單 byte ASCII 路徑,自帶 inc/jmp)。

實作時併入 `build_hooked_exe.py` 的 `.cjk` 節(同 drawString hook,nasm 組 stub、絕對立即數免 reloc)。

## 狀態

RE 完成、hook 設計備妥、安全性靜態確認。**未併入出貨 build**:此模組畫的畫面(戰鬥內簡報)在 headless Xvfb 無法可靠導航抵達,依「不出貨未驗證 binary patch」紀律,待實機驗證後啟用。
