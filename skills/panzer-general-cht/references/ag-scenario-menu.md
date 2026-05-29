# AG 戰役選單中文化分析與下一步

本文件詳述 AG.EXE 戰役選單(scenario list)為何不能直接翻譯,以及指標重導向(pointer redirection)解法所需資訊。

## 問題

直接翻譯 AG.EXE 戰役名稱表 (Table A/B/C) 會在「選戰役後進入遊戲」時拋 exception。原因:Table B 同時用於 menu 顯示 **和** 進入時的 strcmp lookup。

## Bisection 測試結果 (2026-05-16)

| 組合 | menu 顯示 | 進入 |
|------|----------|------|
| A=eng, B=eng, C=eng, TDB=eng (baseline) | 英文 | OK |
| A=cht, B=eng, C=eng, TDB=eng | **英文**(A 不影響) | OK |
| A=eng, B=cht, C=eng, TDB=eng | 中文 | **exception** |
| A=cht, B=cht, C=eng, TDB=eng | 中文 | exception |
| A=cht, B=cht, C=cht, TDB=cht (全 Chinese) | 中文 | exception |

**結論**:Table B 是 menu 唯一顯示來源,也是 lookup 來源。Table A 顯然未被 menu 或 lookup 使用(可能是其他畫面用)。SCENARIO.TDB 中文化無法解決(可能 lookup 並非 strcmp(menu, TDB),而是其他機制)。

## 三個 Table 結構與 getter

PE 結構參考(AG.EXE):
- ImageBase 0x400000
- .data file 0x1B9200, VA 0x5E8000 → VA = fo + 0x42EE00
- .text file 0x400-0x19C800, RVA 0x1000

### Table A — 0x1C2800-0x1C29E8 (北非戰役?, 39 entries, getter 限 8)

字串排列(file offset / slot):
```
0x1C2800 / 16: Sidi Barrani
0x1C2810 / 12: El Agheila
0x1C281C / 12: Crusader
0x1C2828 / 16: Mersa El Brega
0x1C2838 /  8: Gazala
0x1C2840 /  8: Tripoli
0x1C2848 / 12: El Alamein
0x1C2854 / 13: Cairo
[gap with pointer table at 0x1C2860]
0x1C2880 /  8: Torch
0x1C2888 / 12: Kasserine
0x1C2894 / 12: Mareth Line
0x1C28A0 /  8: Tunis
0x1C28A8 /  8: Sicily
0x1C28B0 /  8: Anzio
0x1C28B8 /  8: Jupiter
0x1C28C0 / 12: Overlord
0x1C28CC /  8: Cobra
0x1C28D4 /  8: Meuse
0x1C28DC /  8: Moselle
0x1C28E4 / 16: To The Rhine
0x1C28F4 /  8: Ruhr
0x1C28FC / 12: Germany
[gap]
0x1C2940 /  8: Finland
0x1C2948 /  8: Pskov
0x1C2950 / 12: Leningrad
0x1C295C /  8: Moscow
0x1C2964 /  8: Vyazma
0x1C296C / 12: Kharkov '42
0x1C2978 / 12: Stalingrad
0x1C2984 /  8: Rostov
0x1C298C / 12: Kharkov '43
0x1C2998 /  8: Dniepr
0x1C29A0 /  8: Korsun
0x1C29A8 /  8: Minsk
0x1C29B0 /  8: Ploesti
0x1C29B8 / 12: Zhitomir
0x1C29C4 / 12: Debrecen
0x1C29D0 / 16: Lake Balaton
0x1C29E0 /  8: Berlin
```

**Pointer table A** at `0x1C2860` (32 bytes, 8 × 4-byte VA),指向 Table A 前 8 名稱(Sidi Barrani 到 Cairo)。

**Getter A** at file `0x956BB`,參考 pointer table @ `0x956E3`(MOV instruction `8B 04 85 60 16 5F 00`):
```
55 8B EC ...                  ; prologue
83 7D FC 08                   ; cmp [ebp-4], 8 (限 8)
0F 8D 30 00 00 00             ; jge +0x30
8B 45 FC                      ; mov eax, [ebp-4]
8B 04 85 60 16 5F 00          ; mov eax, [eax*4 + 0x5F1660] ; load Table A ptr
50                            ; push eax
8B 4D 08                      ; mov ecx, [ebp+8]
E8 74 B2 F6 FF                ; call (thunk-relative)
50                            ; push eax
E8 DA CA F6 FF                ; call (thunk-relative)
```

### Table B — 0x1C2A2C-0x1C2BB4 (主要 scenario 顯示, 39 entries, getter 處理全部 39)

與 Table A 同 39 個名稱,順序相同。

**Pointer table B** at `0x1C2BB8` (39 × 4 = 156 bytes)。

**Getter B** at file `0x941E5`,參考 pointer table @ `0x94211`(`8B 04 85 B8 19 5F 00`):
```
55 8B EC ...                  ; prologue
... 83 F8 27                  ; cmp eax, 0x27 (39 limit)
0F 8D 37 00 00 00             ; jge +0x37
0F BF 45 FC                   ; movsx eax, word [ebp-4]
8B 04 85 B8 19 5F 00          ; mov eax, [eax*4 + 0x5F19B8] ; load Table B ptr
50                            ; push eax
8B 4D 08                      ; mov ecx, [ebp+8]
E8 46 C7 F6 FF                ; call
50                            ; push eax
E8 AC DF ...                  ; call
```

### Table C — 0x1C2C54-0x1C2C77 (戰役起點, 3 entries)

```
0x1C2C54 / 16: Sidi Barrani  (北非)
0x1C2C64 /  8: Torch         (西歐)
0x1C2C6C / 12: Finland       (東線)
```

**Pointer table C** at `0x1C2C78` (3 × 4 = 12 bytes)。

**Getter C** at file 附近 `0x94812`(`8B 04 85 78 1A 5F 00`):
```
... 8B 45 08                  ; mov eax, [ebp+8]
8B 04 85 78 1A 5F 00          ; mov eax, [eax*4 + 0x5F1A78] ; load Table C ptr
50                            ; push eax
8D 85 A0 FB FF FF             ; lea eax, [ebp-0x460]
50                            ; push eax
E8 B2 E6 F6 FF                ; call
```

## 下一步建議手法

### 方案 A:PG 式完整指標重導向

1. **保留原英文 Table B**不動於 `0x1C2A2C-0x1C2BB4`(供 strcmp lookup)
2. **在 .data 安全 NUL 區寫 Big5 副本** — 用 `scripts/find_safe_space.ps1` 找
3. **加新 pointer table B'** 指向 Big5 副本(放於另一 NUL 區)
4. **新 Chinese getter 函式** 於 .text padding(INT3 區或 0xCC 連續區)
5. **找 getter B (0x941E5) 的所有 callers**:
   - getter B 透過 thunk 被呼叫(thunk 區可能在 `0x964` 或 `0x21D0` 附近的 E9 跳板)
   - 找出所有 E8 call 跳板的位置
   - 對每個 caller bisection:測試 display 還是 lookup
6. **顯示 callers** → 改 call 新 Chinese getter
7. **lookup callers** → 維持原 getter

### 方案 B:利用 Table A(可能更簡單)

Table A 目前未被任何已知路徑使用,但 getter A(0x956BB)存在,且 pointer table A 內有 8 entries。

可能性:
- Table A 是「死代碼」或未實作功能 → 翻譯無用
- Table A 是某子畫面(e.g., Campaign overview)的資料源 → 翻譯只影響該畫面
- Table A 是 lookup 的 secondary 源 → 翻譯不影響顯示

**先實驗**:把 Table A 各 entry 完整翻譯為中文,進遊戲走訪每個畫面,觀察是否有中文出現於某處。若出現,定位用途。

### 方案 C:Hook CreateFile / strcmp(進階)

DLL injection 攔截 strcmp,將 Chinese 還原為 English 後再比對。超出本 skill 範圍。

## thunk 區資訊

AG.EXE 內部呼叫透過 thunk 表(E9 JMP rel32 連續排列):
- 0x964 起連續 E9 jmp 跳板
- 0x21D0 起另一段 E9 跳板
- 直接 E8 call 從 .text 任意處 → thunk → E9 → 真實函式

要找某函式 (e.g., 0x941E5) 的 callers:
1. 先掃所有 E9 跳板,計算 target,看哪些 thunk 指向 0x941E5
2. 對找到的 thunk 位置(thunk_fo),計算 thunk_va,再掃 .text 內 E8 callers 計算 target=thunk_va

## 還原狀態(2026-05-16 結束時)

- AG.EXE Tables A, B, C 全 revert 回英文(防 exception)
- SCENARIO.TDB 全 revert 回英文
- AG.EXE 其他翻譯(UI、戰役描述、字體)仍保留中文化

---

# ✅ 2026-05-29 完成記錄(PG 式 caller-level 拆分)

## 結論

AG 戰役選單 39 條地名中文化已成功。用戶實測:menu 顯示中文 + 點選任何戰役(含 Germany / 德國本土)都能正常進入。

## 關鍵發現:Table B 不是直接被讀,而是有 3 個 .text 訪問點

| Function | VA | File | 用途 |
|---|---|---|---|
| **getter B** (lookup 主搜尋) | 0x494DE5 | 0x941E5 | `mov eax, [eax*4 + 0x5F19B8]`,**loop search** style:接收 search key,iterate 39 ptrs strcmp 找 match,return i+1 |
| **Function 1** (2-arg) | 0x494E4F | 0x9424F | `mov eax, [eax*4 + 0x5F19B4]`(1-based),0 個 caller(dead code) |
| **Function 2** (純 getter) | 0x495528 | 0x94928 | `mov eax, [eax*4 + 0x5F19B4]`(1-based)+ 直接 return,**10 個 callers**,**這才是 menu display 真正路徑** |

之前的分析卡在「Table B getter (0x941E5) 是 lookup 不可能是 display」直到搜尋 1-based base `0x5F19B4`(原本只搜 `0x5F19B8`)才發現 Function 2。

## Caller 分類(Function 2 thunk @ VA 0x4032A1 的 10 個 E8 callers)

| # | File | VA | Pre-pattern | Post-pattern | 類型 |
|---|---|---|---|---|---|
| 1 | 0x12B1C | 0x41371C | wrapper 函式內 | `83 C4 04; E9 +0; epilogue` | wrapper(**dead — 0 個上層 caller**) |
| 2 | 0x57C39 | 0x458839 | `push imm32; movsx eax, [ebp]; inc; push` | `50; LEA buffer; 50; E8 strcpy` | **display** |
| 3 | 0x598E2 | 0x45A4E2 | `0F BF 80 DE 04 00 00 40 50`(struct +0x4DE) | `50; mov eax, [reg+0x413]; 50` | **lookup** |
| 4 | 0x59BAE | 0x45A7AE | 同上 | 同上 | **lookup** |
| 5 | 0x5A0E5 | 0x45ACE5 | 同上 | 同上 | **lookup** |
| 6 | 0x5A27E | 0x45AE7E | 同 caller 3 prefix | `50; LEA buffer; 50; E8 strcpy; var=2` | **display** |
| 7 | 0x5A43C | 0x45B03C | 同 caller 3 prefix | 同 caller 6 | **display** |
| 8 | 0x679EB | 0x4685EB | `8B 45 BC 50` (local var) | `50; push imm32 0x5EFE5C ("委任: %s"); ...` | display(被 revert,可能 scenario-load 路徑) |
| 9 | 0x67B9E | 0x46879E | 同 caller 8 (同 function @ 0x46830C) | strcpy + var=3 | display(被 revert) |
| 10 | 0x67BF3 | 0x4687F3 | 同 caller 8 (同 function @ 0x46830C) | strcpy + var=4 | display(被 revert) |

**最終最小集合:只需 redirect 3 個 callers (2, 6, 7) 中文化即達成 menu 中文 + 全戰役可進入**。caller 1 (dead)、caller 8/9/10 (在 click handler function @ 0x46830C 內,redirect 會引發 exception)維持英文 thunk。

## Patch 完整明細

### 1. Table A 39 條地名 → Big5(已於前段完成)
- file `0x1C2800-0x1C29E8`,各 slot 寫入中文,保留 Sub-A1 ptr table @ `0x1C2860` 與 Sub-A2 ptr table @ `0x1C2908` 不動
- 內含 8 個 slot=8B 的短 slot,音譯被迫截斷(Pskov→普斯科、Vyazma→維亞茲、Rostov→羅斯托、Ploesti→普洛耶)

### 2. 新 pointer table B' @ file `0x1BFE4C` (VA `0x5EEC4C`),156 bytes
- 39 個 4-byte LE VA,指向 Table A 中文字串(0x5F1600 起連續,中段跳過 Sub-A1/Sub-A2 ptr 區)
- 1-based 取用時 base = `0x5EEC48`(= 0x5EEC4C - 4)

### 3. 新 Chinese getter @ file `0xC5C0` (VA `0x40D1C0`),27 bytes
INT3 padding 區寫入:
```
55 8B EC 53 56 57            ; prologue (clone Function 2)
0F BF 45 08                  ; movsx eax, word [ebp+8]
8B 04 85 48 EC 5E 00         ; mov eax, [eax*4 + 0x5EEC48]   ← 新 B' 1-based base
E9 00 00 00 00               ; jmp +0
5F 5E 5B C9 C3               ; epilogue
```

### 4. Caller redirect(只 3 個)
| Caller VA | File | Old rel32 (to thunk 0x4032A1) | New rel32 (to 0x40D1C0) |
|---|---|---|---|
| 0x458839 | 0x57C39 | `E8 63 AA FA FF` | `E8 82 49 FB FF` |
| 0x45AE7E | 0x5A27E | `E8 1E 84 FA FF` | `E8 3D 23 FB FF` |
| 0x45B03C | 0x5A43C | `E8 60 82 FA FF` | `E8 7F 21 FB FF` |

### 5. 不動
- Function 2 (0x94928) 本身:讀英文 Table B `0x5F19B4`,7 個 callers (1, 3, 4, 5, 8, 9, 10) 仍走原 thunk → 英文,lookup 完整
- getter B (0x941E5)、Function 1 (0x9424F):未動
- Table B 字串區 (0x1C2A2C-0x1C2BB4) 與 Table B ptr table (0x1C2BB8) :未動,持續供 lookup 用
- Tables C、SCENARIO.TDB:未動

## 失敗的中間嘗試(教訓)

1. **第一次嘗試 in-place patch Function 2 base** (`B4 19 5F 00` → `48 EC 5E 00`):全 10 callers 都拿中文。menu 中文 ✓ 但點選 Germany exception(callers 3/4/5 lookup 拿中文 strcmp 失敗)→ 已 revert
2. **第二次嘗試 7 個 display callers (1+2+6+7+8+9+10) redirect**:menu 中文 + 點選 Germany 仍 exception(callers 8/9/10 在 click handler function 內,redirect 引發 lookup 失敗)→ 將 8/9/10 revert
3. **最終最小集合 2+6+7**:menu 中文 ✓ + 全戰役可進入 ✓

## 對未來類似工作的通用準則(PG 經驗 + AG 補強)

1. **先搜 1-based base 與 0-based base 兩種 pattern**:同一指標表常有兩個 .text 引用基址(`base` 和 `base-4`),漏搜會誤判 display path 不存在
2. **post-context 分類比 pre-context 更可靠**:`50; mov eax, [reg+OFFSET]; push` 是 strcmp 風(lookup);`50; LEA buf; push; E8 (strcpy)` 或 `50; push imm32_fmt; ...` 是 display
3. **同 function 內多個 callers 一起判斷**:enclosing function 找到後檢查整段 function 的行為,單看 caller 個別 prefix 易誤判
4. **PG 式 default 英文 + 顯示用 caller 改中文**:比 default 中文 + lookup 改英文更安全(lookup callers 通常多於 display,改少數安全)
5. **每次只改最小集合,逐個 caller 試**:bisection 時保守地一次只 redirect 1-2 個 callers,測試後再擴充

## 任務簡報(briefing)真實位置(2026-05-29 補充)

- 0x1BD0E8 起 39 段「短描述」 = scenario menu 上顯示的一句話(已中文化)
- **長 briefing(scenario 進入時顯示的整段內容)在 `.rsrc` section,UTF-16LE 編碼**,從 `0x1D5E38` 起,39 段(順序與 0x1BD0E8 同序)
- 例:Anzio briefing `The Allies face stiff resistance from German troops in Italy...` 在 `0x1D6E0E`
- 我們之前 byte search 用 ASCII pattern `73 74 69 66 66` ('stiff') 都 0 hit,因為 UTF-16LE 是 `73 00 74 00 69 00 66 00 66 00`,要用 wide pattern 才搜得到
- SCN 檔(SCENARIO\GAME###.SCN)**不含** briefing — 只含 scenario 內部資料 + tacmap/stm/mapconv 路徑 + 短名 key,**0 條長 ASCII**
- 翻譯時用 UTF-16LE Big5 codepoint(注意:不是 raw Big5 byte,要用 Unicode codepoint),例:「灣」 = U+6E7E → bytes `7E 6E`(LE)。每中文字 2 bytes,1:1 替換 2 個 ASCII 字。
- 計算 slot:每 briefing 是 wide string + NUL wide(`00 00`),中文版要 ≤ 原英文 wide chars 數(因為都 2 bytes/字)

