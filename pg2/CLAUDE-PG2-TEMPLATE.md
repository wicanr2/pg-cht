# PG2 引擎家族 CJK 中文化操作範本

> 本文件是《裝甲元帥2》(Panzer General II, SSI 1997,VC++/DirectDraw「Living Battlefield」引擎)中文化經驗萃取成的**引擎專屬操作手冊**,首要目標兄弟作 = **解放軍之怒(People's General, SSI 1998,同引擎)**。
> 開新專案時可複製本檔成該專案根目錄的 `CLAUDE.md`,依 §0–§9 逐步執行。
>
> 與既有文件的分工:
> - `pg2/中文化經驗-方法論.md` = **通用**閉源 DirectDraw CJK 方法論(跨引擎,PG1/AG/PacGen/PG2 皆適用)。
> - **本檔** = **PG2 引擎專屬**的操作手冊:具體 9 道 patch 鏈 + 每個位址 + 會重演的雷 + 「新 EXE 怎麼重新定位」。體例可執行、命令式、可打勾,不是散文回顧。
>
> 標註慣例:位址皆以 `PANZER2.EXE` ImageBase `0x400000`(DYNAMICBASE=off,固定載入)為準,來源是 `pg2/中文化規劃.md` §7.1–§7.14 與 `pg2/build/*.py` 的逐位元組斷言(build 腳本執行前會 `assert` 原始 bytes,是位址正確性的第二重證據)。**每一個 PG2 專屬位址都標【對新 EXE 重新定位】**——換一顆 EXE,這些十六進位值幾乎必定失效,唯一可靠的是它們代表的**機制**(哪個函式、哪張表、哪種 patch 手法)。

---

## 0. 這份範本怎麼用 / 適用範圍

**適用**:與 PG2 同引擎世代的 SSI「Living Battlefield」VC++/DirectDraw 老遊戲。People's General(1998)是首要目標——同公司(SSI)、同年代(PG2 隔年)、同類回合制戰棋,引擎世代重疊機率高。

**核心紀律(貫穿全文)**:

1. **同引擎 → 機制/手法可移植,但新遊戲是不同 EXE,所有絕對位址會位移。** 本文每一個 PG2 位址都是「上一次在這顆特定 EXE 上量到的結果」,不是通用常數。對新 EXE 動手前,先用 §8 的方法「用 PG2 反組譯當 oracle」在新 EXE 找對應位址(相同 code pattern / 字串 xref / descriptor 表結構 / 繪字函式簽章;必要時動態插樁 backtrace),絕不直接把 PG2 的十六進位值套進新 EXE。
2. **Phase 0 先確認引擎同源,別假設。** 見 §1——import table、建置路徑字串、字型檔逐 byte、英文語言槽,四項全過才進 §2 以後;任一項不過,退回 `retro-directdraw-hires-cjk` 通用方法論重新判定。
3. **哪些可移植 vs 哪些要重做**:
   - **可移植(方法/工程)**:引擎判定法、雙管線文字架構、2-byte CJK 引擎手法(route C)、PE 節追加技巧、ctype repoint 這類「先找共同根源再修」的除錯紀律、打包/AppImage 生命週期修法。
   - **要重做(內容/位址)**:所有絕對位址、hook 點 bytes pattern、GUI 文字 glossary、**歷史百科**——People's General 是現代解放軍 vs 美軍、亞太戰場、現代兵器,和 PG2 的二戰內容**完全不同**,不能套用 PG2 的譯名/百科,只能套用「怎麼做百科」的體例。

---

## 1. Phase 0:引擎確認(動手前必做,別假設「同系列 = 同引擎」)

PG1《裝甲元帥》、AG《盟軍元帥》是 Borland Pascal + WinG;PacGen《太平洋元帥》是 DirectDraw + 自訂 8×8 點陣字;PG2 表面上是「系列第四款」,反組譯卻發現是**全新 VC++ 引擎**。People's General 是否與 PG2 同源,**必須實測,不能因為「同公司隔年作品」就假設**。

### 1.1 import table 判引擎世代

```
PG2 的答案(對照組):
  import MSVCRT.DLL           → VC++ 世代(非 Borland/WinG)
  import DDRAW.dll            → DirectDraw(非 GDI blit)
  import mss32.dll            → Miles Sound System
  import smackw32.dll         → Smacker 影片
  import dplayx.dll           → DirectPlay(連線)
  import clubdll.dll→gamechat.dll→chatsock.dll → SSI ClubSSI 連線元件鏈(靜態,缺一不可載入)
  GDI32 有 CreateFontA/TextOutA/DialogBoxParamA → 存在 GDI 對話框管線(見 §2 管線 A)
```

**對 People's General 做的事**:`pe_imports`(解析 import directory,repo 內對應工具是 `pg2/build/pe_inspect.py` 的模式,可擴充成印 import table)。判讀:
- 有 `MSVCRT*` → VC++ 世代,PG2 手法大機率適用。
- 有 `WinG*` 而非 `DDRAW` → 退回 PG1/AG 的 Borland Pascal 手法(`skills/panzer-general-wine`),本範本不適用。
- 有 `DDRAW.dll` 但**沒有** GDI 文字 API → 全部文字走自訂點陣字,連對話框都要走 route C(比 PG2 更重的工程量)。

### 1.2 建置路徑字串判專案代號

PG2 反組譯 `.rdata` 找到硬編的建置機路徑 `C:\pz97\main\Src\Scenario.c`(專案代號 `pz97` = Panzer 1997)。**對新 EXE 做同樣的事**:`strings PEOPLESGENERAL.EXE | grep -i '\\.c$\|\\.cpp$\|Src\\\\'`,找專案代號與模組劃分——這是免費證據,常見於未 strip 的 1990s 除錯建置。People's General 若沿用同一套建置系統,代號可能是類似 `pg98`/`peo98` 之類(**待建置後實測,別猜**)。

### 1.3 字型檔格式逐 byte 核對

PG2 的答案:`PANZER2.DAT` 內 `FONTPG.DAT`(287KB,英文主字型,`"1.10"` 版、SHP 式多幀格式,較複雜)+ `FONTFRA.DAT`(14KB)/`FONTGRM.DAT`(6KB,法/德,簡單 TFONT)。TFONT 格式:

```
Header 16 bytes: [u32 ver="1.\0\0"][u32 glyph數][u32 glyph高=8][u32 maxidx]
Offset table @0x10 起: glyph數 × 4 bytes(LE)
每 glyph: [u32 width][width×height bytes,1 byte/pixel]
像素慣例: 前景(筆畫)=0x00,背景=0xff(經 xlat 透明表映射)
```

**對新 EXE 做的事**:解包 People's General 的資料封裝檔(格式待查,PG2 是 `<u32 count><u32 magic>` + 395 筆 17-byte 固定記錄,新遊戲的封裝格式**不能假設相同**,先靜態解出目錄結構),抽出候選字型檔,逐 byte 核對 header 是否吻合上述 TFONT 佈局(ver 字串、height 欄位、offset table 起點)。**吻合 → PacGen/PG2 的 route C 工具鏈(`build_atlas_pg2.py`/`build_hooked_exe_pg2.py`)可直接複用,只需重新定位位址**;不吻合 → 需重新逆向字型格式,退回 `retro-directdraw-hires-cjk` 的「font 格式逆向」步驟從頭做。

### 1.4 英文(預設)語言槽確認

PG2 的教訓(§3.1 有完整記錄,此處摘要):**不要假設「非預設語言槽工具鏈好複用」就選它**。PG2 曾規劃寄生法語槽(TFONT 簡單格式,理論上工程最小),PoC 後發現法語字型在該遊戲副本裡未被正確載入 → 全域字型指標野指標 → 首次繪字即崩;最終改走**英文(預設)槽**注入中文,反而更簡單、無需語言 byte patch。

**對 People's General 做的事(判斷順序)**:
1. 反組譯語言選擇邏輯(PG2 是一串 `stricmp` 比對 `"english"/"french"/"german"/"spanish"`),找驅動字型載入與資料檔後綴的**真正全域開關**(PG2 是 `[0x4a44a0]`,不是 INI 讀出來的死變數 `[0x4b4e28]`——**兩套機制要分清楚,只有驅動字型/資源選擇的那個才算數**)。
2. 找該全域變數的**.data 初值**(PG2 file offset `0xa32a0` = `0x09`=LANG_ENGLISH),初值即預設槽。
3. **英文槽優先**:除非有具體理由(如英文槽字型格式过复杂、非英文槽反而更簡單),預設選英文槽注入中文,不必新增語言分支、不必動語言選擇 byte。
4. **PoC 驗證,別憑「檔案存在」假設能載入**:`WINEDEBUG=+file wine PEOPLESGENERAL.EXE` 觀察實際開檔哪個資料檔後綴/哪個字型檔,以此為準,不要只看資料檔是否存在。

---

## 2. 文字管線盤點(雙管線,PG2 的通用架構)

PG2 的文字分兩條獨立管線,People's General 若同引擎,大機率也是這個架構——但**每個管線的位址、呼叫點次數都要對新 EXE 重新盤點**,不要假設數字一樣。

**管線 A:GDI 對話框(視窗層,好處理)**
- 特徵:import `CreateFontA`/`TextOutA`/`GetTextExtentPoint32A`/`DialogBoxParamA`/`LoadStringA`;`.rsrc` 內有 DIALOG template。
- PG2 的答案:23 個 DIALOG + 2 個 ACCELERATOR + 1 ICON,`DialogBoxParamA`×17、`CreateDialogParamA`×2;唯一 `CreateFontA` facename `"Arial"` height `-0x10` charset `0x10`。
- 改法:譯 DIALOG template 文字 + facename 換 CJK 字型 + charset(如 `CHINESEBIG5=136`)。**不需碰渲染邏輯**,是全案最省力的一塊。

**管線 B:遊戲畫面內文字(DirectDraw surface 層,主要工程量)**
- 特徵:純 DirectDraw blit,自訂點陣字,無 GDI 文字呼叫。
- PG2 的答案:語言全域 `[0x4a44a0]` 驅動載入哪個 `.DAT` 字型;8×8 點陣塞不下中文,走 route C(§4)。
- **多繪字路徑各自 hook,是全案最大的隱藏工程量**:PG2 至少有 3 條獨立繪字/量測路徑要各自處理——單行(`drawStringCore`)、word-wrap(`drawWrappedText`)、以及一票「量測寬度算座標」的次要路徑(置中/右對齊/裁剪 view)。對新 EXE 要先枚舉**所有** `TextOutA` 呼叫點以外的自訂繪字函式(用 xref 找 `blit`/`glyph` 類函式的所有 caller),別假設只有一條。

**資料檔管線:loose `*.TXT` 英文槽注入**
- PG2 的答案:`GUI97.TXT`/`MISC.TXT`/`EQUIP97.TXT`/`NAMES.TXT`(頂層)+ `SCENARIO/*.TXT`(302 檔)是 8-bit clean 的純文字檔,parser 容忍高位元組(法/德版重音字證明);直接把 dense 2-byte 編碼寫入英文槽對應檔即可,**不需重打包封裝檔**(這些是 loose 檔,不在 `.DAT` 裡)。
- 對新 EXE 做的事:比照 §1.3 解包封裝檔後,確認哪些文字資料是 loose(直接可寫)、哪些烤在封裝檔內(需要重打包工具,PG2 靠社群 MODGEN/PG2 Mods Clearing House 省下自寫封裝器,People's General 需另找對應社群工具或自寫)。

---

## 3. 翻譯與百科(遊戲專屬,People's General 全換)

**glossary 唯一真相 + apply 腳本體例(可移植)**:PG2 用 `pg2/翻譯/glossary.tsv`(單位/GUI 詞彙)+ `pg2/翻譯/briefings/briefings_glossary.tsv`(簡報散文)兩份 TSV,配 `apply_translations.py`/`apply_briefings.py` 把 UTF-8 譯文母檔轉成 dense 2-byte 編碼寫回英文槽資料檔。**這套「TSV glossary 是唯一真相、母檔 UTF-8、build 時才編碼」的分工可直接搬到 People's General**,新專案建對應的 `翻譯/glossary.tsv` + `apply_translations.py`。

**內容全換,不可套用 PG2 譯名**:People's General 是現代解放軍(PLA)vs 美軍、亞太戰場(參考公開資料:設定橫跨朝鮮半島、南海、台海等亞太熱點)、現代兵器(主戰車、直升機、精確導引武器,非二戰裝備)。PG2 的裝備名/地名/指揮官姓名詞庫**完全不適用**,需重新建立現代軍事術語 glossary。

**百科體例沿用**:`pg2/歷史百科/`(`將領.md`、`戰役.md`、`戰役.tsv`、`NAMES-姓名庫.tsv`)的**體例**——區分「隨機姓名詞庫」(NAMES.TXT 類,按國別分段的通用姓氏,非真人)vs「戰役歷史百科主體」(各劇本的真實背景/現代局勢背景,由戰役帶出)——可套用;**內容全部重寫**,現代題材百科需查證現行局勢與武器系統資料,體例(每戰役一節、真實背景 vs 遊戲虛構分開標注)延續即可。

---

## 4. 自建 2-byte CJK 引擎(route C)

沿用 PacGen/PG2 已驗證的**最小工程路徑**(不動 DirectDraw 畫布,只拉高字高 + 2-byte hook),對新 EXE 重做以下 5 步:

1. **確認字高 memory-read**:反組譯新 EXE 的 drawGlyph,若字高讀自 font header(如 `[font+8]`)即可改檔生效,EXE 邏輯不用動(PG2/PacGen 皆如此;若新 EXE 是 immediate 硬編,需另評估)。
2. **CJK atlas 做成與原生 drawGlyph 相容的 mini-TFONT**:header 16 bytes + offset table + `[width][px]` glyph,**前景 0x00 / 背景 0xff 務必與原生字型逐 pixel 核對後才定**(§6 白底/透明顛倒雷)。
3. **face index 選繁中**:用 PIL/`ImageFont.truetype(ttc, index=N)` 烤 atlas 時**顯式指定 index**——Noto Sans CJK `.ttc`:0=JP、1=KR、2=SC、**3=TC**、4=HK;不指定會預設拿 index 0(日文臉),對純漢字幾乎無差但標點(。、‧)置放慣例錯(§6 雷)。
4. **`is_cjk()` 用 `ord(c) >= 0x80` 全收,不要 CJK 碼段白名單**:漏收音譯人名/地名常用的 U+00B7(間隔號)這類非 CJK 碼段的高位字元,會在含它的檔案編碼時直接炸掉(§6 雷)。
5. **自訂 dense 2-byte 私有編碼(非裸 Big5)**:`dense = (lead-0x81)*94 + (trail-0xA1)`,兩 byte 皆 ≥0x80,hook 純算術無查表,塞得進小 code cave。dense 映射只取決於排序後的字集,與字高/字型無關——**換字級不必重編碼資料檔**(PG2 12px/14px/16px atlas 共用同一份 dense 編碼,是這個性質的直接證明)。
6. **無 code cave 就追加 PE 節**:PG2 命名 `.cjk`(繪字 hook + atlas)、`.ctyp`(ctype repoint 表)、`.brm`(countLines clone)、`.b12`(簡報 12px 副 atlas);固定 base(non-ASLR)的老 EXE,絕對立即數免 reloc,是這套多節擴充手法能成立的前提——**動手前先確認新 EXE 的 `DllCharacteristics` 沒有 `DYNAMICBASE`(0x40)位元**。
7. **多繪字路徑各自 hook**:單行(drawStringCore 類)與 word-wrap(含斷行/量測)是兩種難度完全不同的 hook,word-wrap 因為多了斷行邏輯與兩段 render,**永遠是最後才攻下、最容易踩坑的一條**(PG2 經驗:先用「movsx→movzx 止崩」爭取時間,再回頭做完整 2-byte hook)。

---

## 5.【核心】9 道 patch 鏈(PG2 最終 recipe,`make_full_release.py` 的執行順序)

> 使用者原始大綱稱「8 道」,是 PG2 開發過程中期的計數;最終 `make_full_release.py` 定案為 **9 道 EXE patch**(第 8/9 道分別是簡報 12px 與採購格裁剪修正,原大綱把這兩者合寫在同一條「⑧」裡——本節依實際腳本拆成 9 條逐一列出,不遺漏任何一道)。**每個位址下方都標【對新 EXE 重新定位】**:方法是先在 PG2 反組譯里確認「這個 patch 到底改的是什麼機制」,再到新 EXE 用 §8 的方法找同機制的對應位址,絕不直接抄十六進位值。

### ① atlas(字庫烘焙)
- 腳本:`build/build_atlas_pg2.py`
- 輸出:mini-TFONT atlas(`atlas_font.dat`)+ dense 編碼表(`charmap.json`)
- 參數(PG2 定案值,**新遊戲需重新做字級/字重比較,不要照抄**):H=14px、Noto Sans CJK **Medium**、face_index=**3**(TC)、thresh=96
- 【不對新 EXE 定位,但字級/字重/face index 的「選擇方法」要重做一次】——PG2 走過 16px Bold(index 0=JP,誤用)→ 14px Medium(index 3=TC,定案)的過程,是使用者實機比對多組字級/字重後選定,新遊戲同樣需要一輪字級對照。

### ② 主 hook + word-wrap hook + glyphWidth clamp + ww-safe + 英文槽不 flip 語言 byte
- 腳本:`build/build_hooked_exe_pg2.py`(`--no-lang --gw-clamp --ww-safe --ww-hook --font-h H`)
- 追加 PE 節:`.cjk`(RVA `0x17f000` = stock EXE 的 SizeOfImage,即緊接原映像尾端)

| 子項 | PG2 位址【對新 EXE 重新定位】 | 原始 bytes(assert 用) | 機制 |
|---|---|---|---|
| 主 hook | `0x43e699` | `0f bf 45 f0 8b`(5B)→ `e9` jmp STUB1 | drawStringCore 逐 byte 主繪字迴圈入口;lead byte 判斷→算 dense→call drawGlyph(atlas) |
| ASCII 回接點 | `0x43e6a4` | `cmp eax,0x20` | STUB1 非 CJK 分支跳回此處,原生邏輯零改動 |
| back-edge | `0x43e685` | `inc word[ebp-0x10]` | CJK 分支消耗 2 byte 後跳回的迴圈計數點 |
| drawGlyph | `0x41b033` | `(dest,x,y,font,ch,xlat)` 6-arg cdecl | atlas 繪字呼叫目標 |
| glyphWidth | `0x41b013` | `55 8b ec 53 56`(5B)→ jmp GWCLAMP | 前進寬度量測,見③ |
| word-wrap hook | `0x43e955` | `83 3d 44 a7 4b 00 01`(7B)→ 5B jmp + 2 nop | drawWrappedText 逐 byte 分類/繪字入口,簡報/多行文字路徑 |
| ww ASCII 回接 | `0x43e95c` | `jle 0x43e983`(需先重放原 `cmp`) | WWSTUB 非 CJK 分支 |
| ww back-edge | `0x43e804` | `inc word[ebp-0x1c]` | word-wrap 迴圈計數點 |
| 語言 byte(**不 flip**) | `0xa32a0`(file offset)| `0x09`(LANG_ENGLISH) | 英文槽=預設,`--no-lang` 保持原值,不需 patch 語言選擇 |

- **ww-safe**(範圍 `0x43e7f3`–`0x43ea60`):把該區間所有 `0f be 04 08`(movsx)改 `0f b6 04 08`(movzx),讓高位元組在 word-wrap 迴圈裡不再變負值致崩——這是 word-wrap 完整 2-byte hook 前的**過渡止血**,新遊戲若走同樣的「先止血再攻堅」節奏,此步驟可先做。

### ③ `_pctype` 指標 repoint(第一性原理根本解,取代逐點 ctype patch)
- 腳本:`build/add_ctype_repoint.py`
- 位址【對新 EXE 重新定位】:指標 `0x4ba538`(值 `0x4ba542`,即 CRT `_pctype` 表基底)
- 機制:多個 UI 文字函式(清單標題、戰役選單、狀態列、採購……)用 `movsx`(符號延伸)讀字元 byte 再查 `_pctype[ch]` 判類別;高位元組(0x80–0xFF)被符號延伸成負索引,讀到表格**前方的活字串資料**(不能直接砸),回傳 class 0(非可列印)→ 文字被判定為終止符而截斷/清空。
- 修法:**不覆寫原表**(Chesterton fence——那塊記憶體是活資料),另建 `.ctyp` 新節 `[128 word 負索引 shadow = 0x0100(_ALPHA)][256 word 原表 0x00–0xFF 逐 byte 複製]`,把指標改指向新表正 0 位。正索引(ASCII)行為與原表逐 byte相同,負索引(CJK 高位元組)一律讀到 `_ALPHA`(保留行、非終止符),blast radius 最小。
- **是 5 個以上 per-site classifier patch 的嚴格超集**:PG2 曾先逐一 patch 5 個「byte 級相同的姊妹 classifier」(劇本清單、戰役選單各一),repoint 做完後才發現這 5 個加上狀態列/採購家族**全是同一張表的 caller**,一次 repoint 全部修好。

### ④ `_output` NULL guard(修右鍵資訊 popup 當機,原版引擎既有 bug)
- 腳本:`build/patch_null_guard.py`
- 位址【對新 EXE 重新定位】:`0x48FAD0`(CRT `_output`,`sprintf` 底層實作),原始 6 bytes `81 ec 48 02 00 00`(`sub esp,0x248`)
- 機制:PG2 UI 慣例 `sprintf(buf, name, ...)` 把查表查到的名稱字串**直接當 format 字串**用;某些 hex 間歇性查表回傳 NULL,未加防護的繪字變體呼叫 `sprintf`→`_output` 解參照 NULL → page fault。
- 判斷「是我方引入還是原版既有」的方法:崩潰路徑全是未改引擎碼、我方 patch 全未觸及;引擎自帶 `null string at %d,%d` debug 字串 + 只有一個繪字變體加了 NULL 防護、其餘沒加(「加了一半的防禦」是原開發團隊自己也踩過的強證據)。
- 修法:hook `_output` 入口,arg2(format)為 NULL 就直接 `ret 0`(等同印出空字串);stub 塞進既有 `.cjk` 節的 raw slack,不增檔案大小,非 NULL 路徑零行為改變。

### ⑤ GWCLAMP 2-byte 感知(次要路徑寬度量測修正,一處修好全部量測 caller)
- 腳本:`build/patch_gwclamp_2byte.py`
- 位址【對新 EXE 重新定位】:`0x57f180`(②追加的 `.cjk` 節內、GWCLAMP stub 所在偏移,即 `CJK_RVA + 0x180`)
- 機制:第②步的 gw-clamp 只是把 ch 遮罩成 byte 防崩,仍把 CJK 的 2 個 byte 各自當 1 個字寬去量測(28+ 個 caller:tooltip 定位、狀態列置中、採購對齊……全部高估寬度、位置算錯)。
- 修法(公式):`half = round(H/2)`。glyphWidth 入口收到的 `ch`(signed)若 < 0(量測迴圈 movsx 讀高位元組必為負)→ 直接回傳 `half`;`ch >= 0`(ASCII,或 STUB1 傳入的正值 dense)→ 遮罩成 byte 後跳回原 glyphWidth+5 續行原邏輯。判別依據:唯一傳正值高位 dense 的呼叫者是 STUB1 的 atlas 前進計算,量測迴圈恆為負——正負號是可靠的判別旗標,不需額外參數。

### ⑥ status-bar / 採購標題 清框修正(descriptor 表資料 patch)
- 腳本:`build/patch_status_clear.py`
- 位址【對新 EXE 重新定位】:VA `0x4acd68`(file `0xabb68`),每格 **15-byte** 記錄 `[left,top,right,bottom]`(word),`DEFAULT_FIELDS = [1,2,3,4,5,6,8,9]`
- 機制:重畫文字前先 Blt 背景清除舊字,清除 RECT 高度是照原生 8px 字設計(PG2 實測約 7px);CJK 頂端對齊畫到 `top+H-1`,只清到 `top+6` → 下緣殘影。**縮字不解**(12px 仍殘 ~4px)——是固定幾何問題,非字級問題。
- 修法(公式):`bottom = top + fontH + 1`,純資料 patch,`top`/`left`/`right` 不動。
- **field 9(標題帶)是後補的,別漏**:field 1–8 是狀態列格子,field 9 是採購畫面的置中標題(`drawTextField`)——PG2 第一輪只修了 1–8,漏了 9,導致「切兵種時舊標題殘留、新標題疊字」又當成獨立 bug 花一輪才定根(§6 雷「同機制、多個受害畫面」)。**新遊戲第一次做這個 patch 時,就把所有用同一張 descriptor 表的畫面(不只狀態列)一次枚舉完**,別分批發現。

### ⑦ briefing wrap/line-count clone(countLines 專用複製,修 ③ 的 blast radius)
- 腳本:`build/patch_briefing_wrapcount_clone.py`
- 位址【對新 EXE 重新定位】:源函式 `0x43fdd5`–`0x440051`(637 bytes,含 `push ebp` 頭與 `pop edi;pop esi;pop ebx;leave;ret` 尾),追加 `.brm` 節;clone 內兩處 ctype 讀取 `8b 0d 38 a5 4b 00`(`mov ecx,[0x4ba538]`)→ `b9 42 a5 4b 00 90`(`mov ecx,0x4ba542;nop`,讀**原表**非 repoint 表);**只**改導向 `0x456e01`(於 fn `0x456d32`)與 `0x457000`(於 fn `0x456efb`)兩個簡報框繪製 caller。
- 機制(何時會撞到,新遊戲請直接假設會撞到同款問題):③ 的全域 repoint 讓 CJK 高位元組讀到 `_ALPHA`(可斷字類別),但**換行/計行函式**(算文字框要幾行、框多高)依賴 repoint **前**的行為——CJK 被判「不可斷字」才會逐 byte 允許斷行、撐出多行、框變高;repoint 後 CJK 被判「可斷字元」,整段被當一個不可斷的長 run,行數暴減、框塌陷、文字溢到框外。
- **為何 clone 而非全域改**:此函式有 19 個 caller(狀態列/採購家族的 ctype 讀取就是它),全域把 ctype 讀取改回原表會改到所有用到這個函式的文字框尺寸。**不同 caller 對同一張表需求相反時,正確粒度是 caller-specific clone**,不是回到逐點 patch、也不是二選一的全域值。
- 教訓(寫進 §6):**全域「根本解」上線後,要回歸驗所有共用該機制的畫面**,不能只驗「原本要修的症狀好了」。PG2 案例中,repoint 修好清單/狀態列的同時,弄塌了完全沒被提及過的簡報框——這個回歸是使用者實機玩到才發現的。

### ⑧ 簡報 12px(只縮簡報)+ 框高與實際行距對齊
- 腳本:`build/patch_briefing_font12.py`
- 位址【對新 EXE 重新定位】:
  - 追加 `.b12` 節:12px 副 atlas(dense 映射與主 atlas 相同,資料檔零重編)+ flag-dispatch WWSTUB
  - hook rel32 改向:`0x43e955`(word-wrap 入口,②已 hook 過一次)→ 改導向 `.b12` 內的 dispatch(讀 1-byte flag,0→14px 主 WWSTUB,1→12px 簡報 WWSTUB)
  - 只包 2 個簡報渲染呼叫:`0x456e8d`/`0x45706b`(原呼叫 `0x460193`)→ 改走 flag trampoline(設 flag→call→清 flag)
  - 框高倍率:`0x456e1d`/`0x45701c`(`8d 04 80 03 c0` = `lea eax,[eax+eax*4];add eax,eax`,即 `×10`)→ `imul eax,eax,box_pitch`(`6b c0 <box_pitch> 90 90`)
- 機制:簡報散文走**共用**的 `drawWrappedText`(11 個 caller,經 xref 驗證),不能整體換 atlas 縮小,否則其餘 9 個 caller(顧問提示、訊息框…)也會被縮;用 flag-dispatch 只讓 2 個簡報 caller 走 12px 副 atlas。
- 框高公式:原生 `×10` 是給 8px 字算的行距;CJK 實際 render 行距是 `brief_font_h + 2`(=14 at 12px),但 `countLines` 對 CJK 系統性少算行數(word-wrap 分類/量測 ≠ atlas 實際繪製),**框高倍率須與實際 render 行距脫鉤、取更大值留裕**,PG2 wine 校準:18 剛好、20 偏緊、**24 定案**(過高只是框下方多留白,合原版高框設計)。
- **新遊戲字級校準必經 wine 逐戰役肉眼驗**,box_pitch 沒有可靜態推導的公式,只能對最長的開場簡報反覆調值。

### ⑨ 採購格 CJK 裁切修正(procurement per-cell clip view)
- 腳本:`build/patch_purchase_cell_clip.py`
- 位址【對新 EXE 重新定位】:`0x42c726`(`add eax,0xa` = `83 c0 0a`,3 bytes),立即數 byte 位於 file offset `+2`
- 機制:採購畫面控制繪製法 `0x42c302`(登記在控制陣列 `0x4a1e08`+0x14 的 render callback,是**唯一**登記者)為每格標籤透過 `initView@0x45ecdc` 建一個 clip view,`y1 = cellTop + 0xa`(=2+8,給原生 8px 字算的),14px CJK 被 glyph-blit `@0x41b033` 裁到 `clipY1`,只剩 ~9px。
- 修法(公式):`y1 offset = 2 + FONT_H`(原 `0x0a` = `2+8` 的精確推廣),`y0` 不動(標籤頂端位置不變,只往下多長)。
- **與⑥的 field 9 是同一族(容不下 14px 字的固定幾何值),但是不同機制**:field 9 是「清框太矮」(descriptor 表 bottom 值),⑨ 是「裁剪 view 太矮」(獨立的 clip rect 計算,寫死在 `0x42c302` 這個唯一 caller 裡)——**別因為兩者症狀都在採購畫面就假設是同一處 patch 能一次修好**,PG2 曾把兩者都先誤判為「非 bug / emboss 視覺假象」擱置一輪,靠**動態插樁 backtrace**(hook `0x41b033`/`0x43eda9`,用遊戲自身 IAT 的 `CreateFileA`/`WriteFile` 寫 log)才分開定根,見 §8。

---

## 6.【核心】會重演的雷(同引擎八成再撞,逐條警告 + 對策)

### 6.1 `_pctype` signed-char(movsx)負索引 → CJK 判 class 0 → 截斷/空白/(null)
**現象**:清單標題被截斷成 1–3 字、戰役選單同樣截斷、狀態列顯示 `(null)`、採購單位名空白——表面看是 4 個不相關畫面的 4 個 bug。
**根源**:多處「讀字元查表判類別」的函式用 `movsx` 讀 byte,高位元組(0x80–0xFF)被符號延伸成負索引,越界讀到 CRT `_pctype` 表前方的資料 → class 0 → 被當終止符/不可列印。
**對策**:別打地鼠(逐個畫面各修一次)。第一個症狀出現時就先問「這是不是共用同一張表/同一個函式」;確認是共用表後用**指標 repoint**(不覆寫原表——那是活資料,見 6.2),一次修好所有 caller。**但看 6.3**——全域改也有反例。

### 6.2 Chesterton fence:共用表/共用函式有 blast radius,改前先枚舉全部 caller
`_pctype` 負 shadow 區不是「空白可覆寫記憶體」,是活的錯誤訊息字串;直接填值會砸掉其他功能。**動任何被廣泛共用的表/函式前,先確認這塊記憶體/這條呼叫路徑還有誰在用**——不確定就用指標 repoint(建新表、改指標)而非覆寫原表,是本輪反覆驗證有效的保守解。

### 6.3 全域根本解遇到「不同 caller 需求相反」時要 clone,不要死守全域值
`_pctype` repoint 修好了清單/狀態列/採購,卻**弄壞了完全沒被提及過的簡報框**(countLines 依賴 repoint 前的「錯誤」行為才能正常斷行撐高框)。**動手前枚舉所有 caller**,若有任何 caller 依賴你要改掉的舊行為,正確粒度是 **caller-specific clone**(複製整段函式進新節,只改 clone、只讓需要的 caller 走 clone),不是回到逐點 patch、也不是找一個「兩邊都將就」的折衷全域值(通常不存在)。**驗證紀律**:全域修好後要回歸驗**所有**共用該機制的畫面,不能只驗「原本要修的症狀好了」。

### 6.4 清框/框高/裁剪 view 全按原生 8px 字設計 → CJK 14px 到處被裁/殘留
這是**一整族**同機制不同受害畫面的 bug,PG2 目前已知至少 4 處,新遊戲**幾乎確定會重演**、且幾乎確定**不止 4 處**:
- 狀態列清框 7px(descriptor 表 `bottom` 值)
- 採購標題 field 9 清框 7px(同一張 descriptor 表,漏補的 sibling)
- 簡報框高 `countLines × 10`(原生行距倍率)
- 採購格 clip view `y1 = cellTop + 10`(獨立的 clip rect 計算)

**對策**:字高一旦從 8px 拉高,**先假設所有「先畫框/清背景/裁剪視野」的固定幾何值都是照 8px 算的**,主動去找同類欄位/immediate,不要等使用者一個個回報才修。找法:凡是「畫字前先 Blt 背景清除」或「畫字被裁到某個 view」的函式,反組譯附近找 `+7`/`+8`/`+10` 這類接近原生字高的小立即數,是嫌疑清單。

### 6.5 movsx/movzx 混用,逐函式確認,不能因為兩函式「看起來像」就假設指令一樣
同一份 EXE 裡,「讀一個字元 byte」在不同函式可能用 `movsx`(符號延伸,高位元組變負)或 `movzx`(零延伸,高位元組維持正值)。PG2 至少兩處獨立踩到:①`glyphWidth` 量測用 movsx → 高位元組變負索引 → 查表越界崩潰;②ctype classifier 家族同樣用 movsx → 負索引讀到 shadow 區。**每個「讀字元再查表/判斷」的函式要個別反組譯確認**,不能因為兩個函式表面邏輯像就假設指令選擇一樣。

### 6.6 多臉 `.ttc` 字型未指定 face index → 預設臉可能是錯的語言
`ImageFont.truetype(ttc)` 不指定 `index` 時預設 face 0——Noto Sans CJK 的 face 0 是**日文**(0=JP/1=KR/2=SC/3=TC/4=HK)。對漢字幾乎無差,但標點(。、‧)置放慣例不同(日式左上、中式左下)。**烤 atlas 前用 `fontTools.ttLib.TTCollection` 枚舉,顯式選 index=3(TC)**,烤完逐字比對兩臉差異確認只差標點。

### 6.7 atlas 收字判斷用 `>= 0x80` 全收,不要 CJK 碼段白名單
CJK 碼段白名單(如 `0x4E00–0x9FFF`)會漏掉音譯人名/地名常用的 **U+00B7 間隔號**(落在 Latin-1 區,非 CJK 段),一漏就在含它的檔案編碼時直接拋例外中斷整批 build。用 `ord(c) >= 0x80` 全收進 atlas。

### 6.8 measureWidthMultiline 等次要路徑的 ctype-skip 依賴,別假設只有主繪字路徑需要 hook
量測寬度用的迴圈(置中、右對齊、裁剪座標計算)常常**不**經過主 hook(STUB1/WWSTUB),而是獨立呼叫 `glyphWidth`;主 hook 修好了「畫什麼字」,量測路徑仍可能「量錯字寬」導致座標算錯(§5 ⑤ GWCLAMP 2-byte 感知就是修這族)。判斷法:凡是用量測結果算座標的地方(`x = 錨點 - 寬/2`、`x = 錨點 - 寬`)都是嫌疑點。

### 6.9 靜態歸因先用最小 A/B 實測驗一次,別憑「看似合理」直接動手大改
PG2 案例:交接診斷把簡報框塌陷歸因到 `measureWidthMultiline`(看似合理——它與行數有關),做了 clone 卻**零效果**;`ret` 掉整個 `briefing_open` 函式**框依然在**,才逼出真正的繪製者是另一對函式、真正的行數來源是 `countLines`。**教訓**:看似合理的靜態歸因,動手前用最小 A/B(如「先把懷疑的函式整個跳過,看症狀是否還在」)驗一次,再決定要不要做大範圍的 patch(clone/repoint 這類工程量較大的修法尤其要先驗)。

### 6.10 靜態 emboss vs 裁切/殘留分不清 → 動態插樁 backtrace + 量墨水高度定案
「英文乾淨、中文有陰影/殘影」這個現象**同時符合**「引擎原生 1px emboss 陰影效果」與「清框/裁剪高度不夠留殘影」兩種解釋,單張截圖或靜態反組譯分不清。PG2 曾把兩處真 bug 都先誤判為「非 bug(emboss 視覺效果)」擱置一輪,直到用**動態插樁 backtrace**(hook 繪字函式入口,用遊戲自身 IAT 的 `CreateFileA`/`WriteFile` 寫 log,詳見 §8)才推翻誤判、定根、修復。**判別法**:量測實際墨水高度(被裁的 glyph 露出幾個 pixel row)+ 動態 backtrace 確認繪製路徑,不要只靠肉眼看截圖判斷。

### 6.11 驗證:headless 漏互動玩家路徑,要走正常玩家路徑
Wine + Xvfb headless 截圖驗證能可靠涵蓋「畫面渲染對不對」(選單、清單、簡報文字),但**漏掉兩類 bug**都是使用者實機玩到才回報:右鍵資訊 popup(§5④ NULL guard 修的那個崩潰)、進入採購/升級畫面(headless 自動導航常常進不去)。**出貨前除了 headless 回歸,還要規劃一輪走「正常玩家路徑」的實機測試**(開一場戰役、玩幾回合、點開會被玩家點開的選單/面板)。

### 6.12 對照組要控制變因
判斷某個顯示異常是不是中文化引入的,要**同一關卡、同一 hex 位置**比較英文版 vs 中文版,不能用「可能是載入到不同關卡」這類未經控制變因驗證的推測帶過。三方對照(英文原版 / 中文+舊 patch / 中文+新 patch)缺一,結論就站不住。

### 6.13 DirectDraw 獨占模式 wine 下鍵盤事件進不去
影響錄影/自動化導航——只能純滑鼠路徑,headless 導覽腳本要用滑鼠座標點擊,不能發鍵盤事件。這限制了 headless 能自動涵蓋的畫面範圍(§6.11 的「進不去採購畫面」部分成因)。

---

## 7. 打包 / AppImage 生命週期

### 英文槽注入,不需重打包封裝檔
資料檔是 loose `*.TXT`,直接覆寫英文槽對應檔即可套用 dense 2-byte 編碼,**不需重打包 `.DAT` 封裝檔**(除非新遊戲的目標文字資料本身就烤在封裝檔內,見 §2 資料檔管線判斷)。PG2 唯一一個「若要更完美需要重打包 DAT」的殘留項是 ASCII(8px,來自 `FONTPG.DAT`)與 CJK(14px,來自 `.cjk` atlas)混排時 baseline 不齊——這是 **polish 層級、未執行的選配修法**,不是必要步驟。

### AppImage PacGen DirectDraw 配方(PG2 直接沿用)
- renderer:`gdi`(非 `x11`,PG2 是 8bpp paletted DirectDraw,gdi renderer 避開部分調色盤問題)
- `GrabFullscreen`(wine registry,避免視窗化模式下的顯示異常)
- 啟動前 `wineserver -k` **並輪詢等待進程真正結束**(見本節下方「殘留 wineserver 未清」段)
- `wine explorer /desktop=<GameName>,<W>x<H> ./GAME.EXE`(虛擬桌面包住遊戲視窗)

### VERSION 內容雜湊 → 自動 resync,保留 SAVE/USERSCEN
**AppRun 只在首次啟動 `cp` 遊戲檔到 `~/.local/share/`,之後永不更新**——這是 PG/AG/PacGen/PG2 共用的 AppRun 骨架**既有雷**,換新版 AppImage 覆蓋安裝後,已跑過一次的使用者機器上舊 EXE/舊資料永遠不會被換掉。**修法**:在遊戲檔目錄旁放內容雜湊當版本戳 `VERSION`,AppRun 每次啟動都比對,不一致就重新同步遊戲檔,同時**保留使用者的 `SAVE/`、`USERSCEN/` 等存檔目錄不被覆蓋清空**。沒有 `VERSION` 戳的舊安裝視為需要更新,自動補上。**新遊戲的 AppImage 從一開始就該內建這個機制**,不要等使用者「新版本舊 bug 還在」回報才補。

### 殘留 wineserver 未清 → 第二次啟動 BadWindow 崩潰
同一遊戲第二次啟動(跑完關掉、或崩潰後重開)有機率 `BadWindow (X_CreateWindow)` 崩潰,根因是上一次遺留的 wineserver 沒被清掉,新啟動接上握著失效 X window ID 的殘留 server。**修法**:每次啟動遊戲前對**這個遊戲專屬的** wine prefix 執行 `wineserver -k`,輪詢等待進程真正結束(避免 kill 訊號送出但進程還沒死就接著啟動的 race),再啟動遊戲本體;範圍只清這個遊戲自己的 wineserver,不誤傷同機其他遊戲或使用者自己的 wine 應用。

### gamescope 整數放大 + 1x fallback
PG2 原生 640×480 在現代高解析度螢幕顯示過小,wine 虛擬桌面本身不拉伸;解法是內建 gamescope 做整數 nearest 放大(2×/3×),透過環境變數(如 `PG2_SCALE=2x`)opt-in,**gamescope 啟動失敗時要能自動退回 1x,不能讓「放大失敗」變成「遊戲整個起不來」**。打包時把 fallback 路徑當必測項(headless 環境常常沒有真正 GPU/DRI3,是驗證 fallback 的天然測試場景)。

### Windows zip:`dplayx.dll` + 隨遊戲 DLL + `.cmd` 256COLOR
PG2 靜態 import 鏈(`clubdll→gamechat→chatsock`,連線用但載入期必須存在)+ `mss32.dll`/`smackw32.dll`(音效/影片)+ `english.dll`(動態載入的語言字串 DLL)+ **`dplayx.dll`**(現代 Windows 8/10/11 預設不裝 DirectPlay,靜態 import 缺它 EXE 直接起不來,決定隨包原生 dplayx)。**People's General 若同引擎,大機率有同款靜態 import 鏈,打包前先用 §1.1 的 import table 解析法把整條相依鏈列全**,不要只列表面 import,連 `clubdll→gamechat→chatsock` 這種二階靜態鏈都要跟。`.cmd` 啟動腳本用 `__COMPAT_LAYER=256COLOR` 處理 8bpp 全螢幕相容性(現代 Windows 已移除「256 色」相容性選項)。

---

## 8. 對新 EXE 重新定位位址的方法

**核心原則:PG2 反組譯當 oracle,不是新 EXE 的答案本身。** 用 PG2 已知的「這是什麼機制」去新 EXE 找**同機制**的位址,方法依序:

1. **相同 code pattern**:PG2 每個 hook 點都記錄了原始 bytes(如主 hook `0f bf 45 f0 8b`、glyphWidth 入口 `55 8b ec 53 56`)。在新 EXE 搜尋**功能上等價**的 pattern(不是逐 byte 搜尋 PG2 的 bytes——新 EXE 編譯器/優化選項不同,bytes 幾乎必定不同),而是先反組譯新 EXE 對應區域,確認邏輯結構相同(逐 byte 讀字元、查表判類別、call 繪字函式)後才認定是同一個函式。
2. **字串 xref**:找到已知字串(如錯誤訊息、debug 字串、`.rdata` 裡的建置路徑)在新 EXE 的位置,反查誰引用它,常能定位到相關的處理函式附近。
3. **descriptor 表結構**:PG2 的 status-clear 表是 `[15-byte stride, 4×word RECT]` 的固定格式;在新 EXE 找同樣的重複固定 stride 資料塊(工具:掃描 `.data` 段找周期性重複的 pattern),交叉比對 UI 畫面上實際看到的欄位數量。
4. **繪字函式簽章**:`drawGlyph(dest,x,y,font,ch,xlat)` 這類 6-arg cdecl 簽章,在新 EXE 找呼叫慣例相符(棧平衡量、參數個數)的候選函式,逐一反組譯確認。
5. **動態插樁 backtrace(靜態撞牆時的必要手段,非萬用起手式)**:PG2 §7.14 的方法——用遊戲自身 IAT 裡已存在的 `CreateFileA`/`WriteFile`(不需額外注入 DLL,直接改 EXE 在目標函式入口插入呼叫這兩個既有 IAT 函式的 stub),在目標函式(如 glyph-blit、drawTextField)入口把呼叫棧回溯(return address 鏈)寫進一個 log 檔,實機跑到目標畫面後讀 log 分析真正的 caller 鏈。**這是 §6.9/6.10 兩個「靜態歸因錯了」案例最終定案的方法**——遇到「看似合理但驗證後零效果」或「emboss vs 裁切分不清」時,先做動態插樁,不要繼續加碼做更多靜態猜測的 patch。

**工具盤點(誠實標註,別假裝都在 repo)**:
- `pg2/build/pe_inspect.py`(**repo 內**):解析 PE header/節表,反組譯指定 VA 範圍確認 hook 點 bytes——可直接複用於新 EXE(改 `EXE` 路徑參數)。
- capstone(Python package,`Cs(CS_ARCH_X86, CS_MODE_32)`):PG2 的 clone 類 patch(`patch_briefing_wrapcount_clone.py`)用它做自我核對(外部 call 目標、ctype 讀取位置、跳轉不越界),是可靠的反組譯庫,新專案直接 `pip install capstone`(依環境硬規則走 docker uv venv)。
- `pe_imports.py`/`rsrc.py`/`scan_calls.py`/`xref.py`/`disasm.py`——PG2 中文化規劃.md 附錄列出的**scratchpad 中間檔**,**未進 repo**,新專案需要時重寫(功能明確:PE import 解析、`.rsrc` 資源解析、掃描 `call [IAT]` 呼叫點、交叉引用查找、通用反組譯輸出)。
- 「pgdis」——**待核**:本次盤點未在 repo 或任何文件中找到這個工具名稱,可能是與其他反組譯工具(如 IDA/Ghidra/objdump)混淆,或屬未來待建的工具。新專案若需要專用反組譯前端,直接用 `objdump -d -M intel -m i386` 或 capstone,不必假設有一個叫 pgdis 的既有工具。

---

## 9. 出貨檢查清單(照順序打勾)

- [ ] **引擎確認**:import table(MSVCRT/DDRAW/相依 DLL 鏈)、建置路徑字串、字型格式逐 byte、英文語言槽初值——四項全過。任一項不過,退回 `retro-directdraw-hires-cjk` 通用方法論重判。
- [ ] **字型格式**:確認字高是 memory-read;新遊戲 TFONT/mini-TFONT 結構逐 byte 核對(header/offset table/glyph 佈局/前景背景像素值)。
- [ ] **英文槽 PoC**:`WINEDEBUG=+file` 驗證注入中文後遊戲開檔行為符合預期,無語言 patch、無字型載入野指標崩潰。
- [ ] **atlas**:face index 顯式指定繁中(TC);`is_cjk()` 用 `>=0x80` 全收;字級/字重經使用者實機對照定案。
- [ ] **9 道 patch 逐一重新定位**(對照本文 §5 的機制描述,在新 EXE 找對應位址,不抄十六進位值):
  - [ ] ① atlas 烘焙
  - [ ] ② 主 hook + word-wrap hook + gw-clamp + ww-safe(英文槽不 flip 語言 byte)
  - [ ] ③ ctype 表指標 repoint
  - [ ] ④ `_output`/等價底層格式化函式 NULL guard
  - [ ] ⑤ GWCLAMP 2-byte 感知
  - [ ] ⑥ status-bar / 標題 清框修正(**枚舉所有共用同一張 descriptor 表的畫面**,不要分批發現)
  - [ ] ⑦ 簡報 wrap/line-count clone(**先確認 ③ repoint 是否真的弄壞了簡報框,A/B 驗證再動手**)
  - [ ] ⑧ 簡報專屬字級 + 框高與行距對齊(wine 逐戰役肉眼校準 box_pitch)
  - [ ] ⑨ 採購格(或等價的密集清單畫面)裁剪 view 修正
- [ ] **全畫面 wine 驗**(含右鍵資訊、採購/升級、戰場地圖):headless 截圖回歸 + **正常玩家路徑實機測試**(§6.11),不能只驗 headless。
- [ ] **控制變因回歸**:同關卡同 hex,英文原版 / 中文舊 patch / 中文新 patch 三方對照。
- [ ] **AppImage + Windows zip 打包**:import table 相依鏈(含二階靜態鏈)列全;VERSION 雜湊 resync 機制內建;啟動前 wineserver -k 輪詢;gamescope 1x fallback 驗證。
- [ ] **生命週期修驗證**:模擬「覆蓋安裝新版 AppImage、不刪本機舊安裝」情境,確認新 EXE 真的生效;連續啟動 3 次確認無殘留 wineserver 崩潰。
- [ ] **真機驗**(Windows 實機 + Linux AppImage 實機),尤其 DirectPlay/DirectDraw 相容性(§7 Windows zip 段)。

---

## 10. 分工 / 成本

- **依任務性質選模型**:RE 攻堅(判斷共同根源、決定 patch 策略、字渲染機制樞紐判斷、動態插樁定案)用高階推理模型;機械性工作(解壓、跑既有 script、列 PE 資源、批次改檔、打包)可降級到較便宜的模型。判準:這一步需要「理解與判斷」還是「照既定流程執行」。
- **每完成一輪就 commit + push**:規劃 → RE → 翻譯 → 字型引擎 → EXE patch → 打包,每個階段產出並自我審過後就進版控,不累積一大包改動才一次 commit。二進位大檔(AppImage/zip/DAT)不進 git,只記錄 md5/路徑清單(體例見 `pacgen/docs/knowledge-base/dist-manifest.md`)。
- **背景 subagent 不要設了背景監看就結束**:派長時間跑的背景任務(完整 wine 實機驗證、打包腳本)要確保有人在收工前確認它真的跑完並檢查結果。

---

## 11. 參考

- `pg2/中文化規劃.md` §7.1–§7.14 —— 位址、patch recipe、實測證據的權威來源,本文所有位址皆從此逐一核對。
- `pg2/中文化經驗-方法論.md` —— 通用閉源 DirectDraw CJK 方法論(跨引擎),本文是它在 PG2 引擎上的具體操作化。
- `pg2/build/build_atlas_pg2.py`、`build_hooked_exe_pg2.py`、`add_ctype_repoint.py`、`patch_null_guard.py`、`patch_gwclamp_2byte.py`、`patch_status_clear.py`、`patch_briefing_wrapcount_clone.py`、`patch_briefing_font12.py`、`patch_purchase_cell_clip.py`、`make_full_release.py` —— 9 道 patch 鏈的可執行實作,每支腳本開頭 docstring 含完整機制說明與 RE 佐證,是比本文更細節的第一手來源。
- `pacgen/docs/knowledge-base/dist-manifest.md` —— PG2 段記錄打包版本演進(EXE hash 對照、每輪修復的使用者回報與根因)。
- `pg2/windows-dll盤點.md` —— Windows 打包相依 DLL 盤點方法(靜態 import 解析,非猜測)。
- `pg2/翻譯/`、`pg2/歷史百科/` —— glossary/apply 腳本與百科體例參考(內容不可套用,體例可套用)。
- `skills/retro-directdraw-hires-cjk`(repo 內)/ `~/.claude/knowledge-base/retro-cht/retro-directdraw-hires-cjk/SKILL.md` —— route A/B/C 三條放大手法的方法論框架,本文全程走 route C。
- `skills/panzer-general-wine`(repo 內)/ `~/.claude/knowledge-base/retro-cht/panzer-general-wine/SKILL.md` —— PG1/AG(Borland Pascal 世代)的啟動解法,與本文的 VC++/DirectDraw 世代不同源,僅供對照判斷用。
