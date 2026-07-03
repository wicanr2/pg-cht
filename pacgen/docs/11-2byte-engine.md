# 11 逆向:2-byte CJK 繪字引擎 — 讓閉源 EXE 顯示可讀中文

*承 [08-tfont-re.md](08-tfont-re.md) 的 font RE。08 判定「8×8 點陣是硬牆」——**該判定的前提(glyph 永遠 8×8)已被推翻**。本文記錄如何在無原始碼下,讓 PACGEN.EXE 用 16×16 點陣顯示任意中文。*

## 結論(先講)

主選單「開始戰役」等 UI 字串已在實機顯示為清晰 16×16 中文(見 `2byte-hook-SUCCESS-menu.png`),非亂碼。手法:**改 font 檔把字高從 8 升到 16 + 在 EXE 尾端追加一個 `.cjk` 節,內含一段繪字迴圈 hook 與 531 字中文 atlas,把自訂 2-byte 碼導向 atlas glyph**。原版 EXE 僅被覆寫繪字迴圈起點的 5 個 byte,其餘全在新節。

## 推翻 08 的「8×8 硬牆」

08 的判定鏈是:繪字管線畫 8 pixel 高 → 中文塞不進 8×8 → 不可讀。第三步是對的,但**第一步錯**。靜態 RE 繪字核心 `drawGlyph`(VA `0x42817f`)發現字高並非硬編:

```asm
428220  mov  esi,[ebp+0x14]   ; esi = font base
428223  mov  edx,[esi+8]      ; edx = [font+8] = HEIGHT  ← 從 font header 讀,非 immediate
...
4282ed  ... blit 迴圈,外圈 row 數 = edx
```

字高是 runtime 從 font header offset `0x08` 讀的。把 `TFONT1.DAT` header 的 `0x08` 改成 16、每個 glyph 補到 16 列,繪字管線就畫 16 高,**EXE 一行不動**。實測:原版 EXE 配 height-16 的 font 檔,ASCII 正常放大顯示,不 crash。16×16 對中文足夠 —— atlas proof 全 531 字(含灣/艦/龍/鐵/體)清晰可辨。

## 繪字管線(靜態 RE,已對齊資料檔驗證)

三個函式構成短字串繪製鏈:

| VA | 函式 | 作用 |
|---|---|---|
| `0x428312` | `drawString(dest,x,y,font,str,xlat)` | 逐 byte 迴圈 |
| `0x42817f` | `drawGlyph(dest,x,y,font,ch,xlat)` | 查表 + blit 單字 |
| `0x42814c` | `getHeight(font)` = `[font+8]` | 字高存取器 |

`drawString` 迴圈(cdecl,arg 在 `[ebp+8..0x1c]`):

```asm
42831c  mov esi,[ebp+0x18]    ; esi = 字串指標
42831f  mov edi,[ebp+0xc]     ; edi = 筆 X
428322  movzx eax,byte [esi]  ; ← 讀當前字元 byte(HOOK 點)
        push xlat; push eax(ch); push font; push y; push edi(x); push dest
428333  call 0x42817f         ; drawGlyph
        add esp,0x18
42833b  add edi,eax           ; 筆 X += 回傳的前進寬度
42833d  inc esi               ; 字串++
42833e  cmp byte [esi],0      ; NULL 終止測試
428341  jne 0x428322          ; 迴圈
```

glyph 查表(在 `drawGlyph` 內):`glyph = font + read_u32(font + 0x10 + ch*4)`,寬度 = `[glyph]`,blit 走 xlat 調色盤重映射(`0xff` = 透明)。**零 GDI 繪字**(無 `TextOutA`/`CreateFontA` import),所以全部文字都經此管線 —— wine 字型代換無效,只能改 font + hook。

37 個 `drawString` 呼叫點涵蓋選單/按鈕/兵種/裝備等短字串;多行簡報/對話框走另一個 word-wrap 模組(`0x4ab000`–`0x4af800`,直接 call drawGlyph),需第二 hook(見 P4)。

## 自訂 dense 2-byte 編碼(不走裸 Big5)

需要 2-byte 才能定址 >256 字(全遊戲 531 個不重複中文)。選**自訂 dense 編碼**而非 Big5:

```
dense index i  →  lead = 0x81 + i//94,  trail = 0xA1 + i%94   (兩 byte 皆 ≥0x80)
hook 反推:      dense = (lead-0x81)*94 + (trail-0xA1)
```

- **兩 byte 皆 ≥0x80** → 任何檢查 ASCII/控制碼的程式碼都不會誤判。
- **純算術、無查表** → hook 只是一個 multiply-add,塞得進任何小空間。
- 代價是字串要重編碼,但 patch 本來就從 glossary 重新產生,**零額外成本**。531 字 → lead 只用 `0x81`–`0x86`。

因為 dense 碼與 Big5 同樣是 **2 byte/字**,先前 v0.3–v0.6 的 byte-length-preserving patch 全部沿用,offset/pad 不變。

## Atlas 做成 mini-TFONT

關鍵簡化:atlas 不自訂格式,而是做成**與 `drawGlyph` 相容的 TFONT**(header height=16 + 531-entry offset table + `[width][16×16 px]` glyph)。於是 hook 偵測到 lead byte 後,只要**呼叫原本的 `drawGlyph`,傳 `font=atlas, ch=dense`** —— blit 邏輯完全復用,不必自己重寫像素搬移。

## Hook:追加 `.cjk` 節

`.text` 無可用 code cave(掃描 0 個 ≥16 byte 空段,節尾僅 55 byte 餘裕),故**追加新節**:

```
新節 .cjk  RVA 0x203000 (VA 0x603000, = 舊 SizeOfImage), Chars = CODE|EXEC|READ
  0x603000  stub(98 byte)
  0x603100  atlas_font.dat(531 字, 140200 byte)
PE header:NumberOfSections 6→7, SizeOfImage 0x203000→0x226000, 追加 40-byte 節表項
```

固定 base 的 EXE(preferred base 0x400000,relocation 等同 no-op),故 stub 內的絕對立即數(`push 0x603100`)無需 reloc。

stub 邏輯(`0x428322` 覆寫成 `jmp 0x603000`;迴圈 back-edge 本來就跳 `0x428322`,每輪自然進 stub):

```asm
603000  movzx eax,byte [esi]     ; 重讀字元
        cmp al,0x81 / jb .ascii
        cmp al,0x86 / ja .ascii   ; lead 僅 0x81-0x86
        ; dense = (al-0x81)*94 + ([esi+1]-0xA1)
        movzx ebx,al; sub ebx,0x81; imul ebx,ebx,94
        movzx eax,byte [esi+1]; sub eax,0xA1; add eax,ebx
        push xlat; push eax(dense); push 0x603100(atlas); push y; push edi; push dest
        call 0x42817f            ; drawGlyph(... font=atlas, ch=dense)
        add esp,0x18; add edi,eax; add esi,2   ; 消耗 2 byte
        jmp 0x42833e             ; 回終止測試
.ascii: push xlat; push eax; push font(原); push y; push edi; push dest
        call 0x42817f; add esp,0x18; add edi,eax; inc esi
        jmp 0x42833e
```

原 `movzx`(3 byte)+ 下條 push 的頭 2 byte 被 `e9 rel32` 蓋掉;被孤立的尾 byte 不可達(stub 跳去 `0x42833e`,永不回 `0x428327`)。

## Pipeline(可重現)

```
tools/build_atlas.py        蒐集全專案中文 → atlas_font.dat + charmap.json(自訂碼)
tools/reencode_patches.py   Big5 patch → 自訂碼(2byte↔2byte 長度守恆)
tools/font_rebuild.py       TFONT1.DAT height 8→16(ASCII glyph 補高)
tools/build_hooked_exe.py   nasm 組 stub + 追加 .cjk 節 + patch 繪字迴圈起點
tools/apply_2byte_pfp.py    自訂碼 patch 套進 TXT.PFP(size 守恆)
tools/xvfb_launch_shot.sh   隔離 Xvfb :95 全螢幕啟動 + 截圖(不用 explorer /desktop)
```

## 驗證(feedback loop)

隔離 Xvfb `:95`(絕不碰使用者 `:1`)、fresh hardlink workdir、原版 checksum 全程守恆。啟動配方關鍵:**直接 `wine PACGEN.EXE` 全螢幕**,不用 `explorer /desktop`(後者讓 DDraw 不落在可截圖的 framebuffer)。主選單 hover 頂左按鈕,label bar 顯示「開始戰役」四字 16×16 清晰中文(`2byte-hook-SUCCESS-label.png`)。

## 實機覆蓋(drawString 路徑,已驗證)

| 畫面 | 內容 | 狀態 |
|---|---|---|
| 主選單按鈕 | 開始戰役 / 開始劇本 / 離開(未翻的維持英文) | ✅ |
| 劇本選擇畫面標題 | 舊金山 / 中途島 / 塔拉瓦 / 菲律賓 1945 … | ✅ |
| 劇本選擇畫面簡報框 | 多行「假想情境:1944 年日軍聯合艦隊…」 | ✅(drawString 逐行,非 word-wrap) |
| 畫面標題列 | 「select 舊金山 1944」(EXE 英文 + 中文標題混排) | ✅ |
| 裝備名(PACEQUIP glossary 命中) | 7 個單位名 | ✅ |

**重要**:劇本選擇畫面的多行簡報框**由 drawString 逐行畫**(若走未 hook 的 word-wrap,自訂碼會變亂碼——實機是正確中文,故確認走 drawString)。

## word-wrap 模組 RE(第二繪字路徑,設計完成、待戰鬥內驗證)

部分對話(戰鬥內任務簡報 dialog、文字輸入框)走另一個 word-wrap 模組(VA `0x4ab000`–`0x4af800`),**不經 drawString**。靜態 RE(見 `docs/12-wordwrap-re.md`)確認它是**兩段式 grid pipeline**:

1. **FILL+MEASURE `0x4ab976`**:逐 byte 讀原字串、做斷行、把 char/color 寫進 2D grid `0x4e1a60`/`0x4e1ae0`(row stride 258)。
2. **RENDER `0x4abf46`**:讀 grid 逐 cell `call drawGlyph@0x4ac36b`。主 CJK 目標迴圈 `0x4ac2e9`。

**已確認安全**:字元 byte 全 zero-extend(無 `movsx`);控制碼比較全 `<0x81`(equality),lead byte `0x81-0x86` 前向不衝突。

**已知風險(未 hook 前就存在)**:overflow 時的 backtrack 斷詞搜尋(`0x4abd6d`)找空格斷行;連續 CJK 無空格 → 可能走 "word too long" 錯誤路徑,除非 caller 設 hard-wrap flag(bit3 `[ebp+0x14]`,`0x4abd5e` test)。緩解:劇本文字加手動 `\n` 讓每行不 overflow。

**hook 設計(兩個 5-byte jmp,乾淨指令邊界)**:
- FILL `0x4abc93`(file `0xab093`,覆寫 `8B 45 E4 25 FF`):lead byte 時寫 2 byte 進 grid、col+2、src+2。
- RENDER `0x4ac2e9`(file `0xab6e9`,覆寫 `33 C0 8A 45 F4`):grid cell 是 lead 時讀下一 cell、算 dense、`call drawGlyph(atlas)`、col+2;否則 fall through 原 ASCII 路徑。

**為何未併入出貨 build**:此路徑的畫面(戰鬥內任務簡報)在 headless Xvfb 下無法可靠導航抵達驗證。依「不出貨未驗證的 binary patch」紀律,設計備妥但**待有實機(人工 playthrough 或可驅動至戰鬥)驗證後再啟用**。屆時把上述兩個 stub 併入 `build_hooked_exe.py` 的 `.cjk` 節(同 drawString hook 手法)。

## 待做

- **word-wrap hook**:實機驗證後啟用(設計已備,見上)。
- **打包**:AppImage(wine bundle,比照 v0.1)+ Windows zip。
- **內容**:裝備 proper noun 全譯、剩餘 UI 字串(Information Screen / Multiplay / Battle Generator …)。

## 產出檔案(靜態,可靠)

- 繪字管線:`drawString 0x428312` / `drawGlyph 0x42817f` / height `[font+8]`。
- hook 點:VA `0x428322`(file `0x27722`),覆寫 `0f b6 06 ff 75` → `e9 <rel>`。
- 新節:`.cjk` RVA `0x203000`,stub `0x603000`,atlas `0x603100`。
- 方法論 skill:[`retro-directdraw-hires-cjk`](../../skills/retro-directdraw-hires-cjk/SKILL.md)(本案是其「font 2-byte 路徑」的完整落地)。
