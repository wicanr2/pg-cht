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

## 待做

- **P4**:word-wrap 模組(0x4ab000–0x4af800)第二 hook → 劇本簡報/對話框中文。
- **P5**:PACEQUIP + 劇本 TIT/DES 轉碼套用;ASCII baseline 對齊 CJK(vpos);排版溢出檢查;打包。

## 產出檔案(靜態,可靠)

- 繪字管線:`drawString 0x428312` / `drawGlyph 0x42817f` / height `[font+8]`。
- hook 點:VA `0x428322`(file `0x27722`),覆寫 `0f b6 06 ff 75` → `e9 <rel>`。
- 新節:`.cjk` RVA `0x203000`,stub `0x603000`,atlas `0x603100`。
- 方法論 skill:[`retro-directdraw-hires-cjk`](../../skills/retro-directdraw-hires-cjk/SKILL.md)(本案是其「font 2-byte 路徑」的完整落地)。
