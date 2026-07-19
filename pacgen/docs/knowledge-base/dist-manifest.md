# 三部曲繁中化散布清單(dist-all)

> 本檔記錄最終散布套件的內容與校驗值,方便追蹤與驗證。**二進位檔本身不進 repo**(體積過大),集中放在建置機的本地 `dist-all/`。清單日期:2026-07-09。

## 版本重點(2026-07-09)

- **裝備名跨作品 + 跨變體統一**:每作的兩個發佈變體(原始裝備 / 主版)單位名稱已對齊為同一套統一譯名,細節見 [`equipment-crossgame-consistency.md`](equipment-crossgame-consistency.md)。
- **變體結構**:
  - **PG(裝甲元帥)**:三個 EQP 數值完全相同,無「修改數值」變體;原始裝備 / 繁中化 兩發佈只差命名風格(對齊後 EQP byte 相同)與一個 README。
  - **AG(盟軍元帥)**:真有兩套數值——原始裝備(SSI 原始值,= Lite)與修改數值主版(110 單位重新平衡);兩者名稱皆已統一、各自數值保留。
  - **PacGen(太平洋元帥)**:單一版,v0.2 修正 2-byte CJK 白底 bug + 對話框排版 + 裝備譯名。
- 名稱對齊方式:純名稱欄(EQP 每筆記錄 bytes 0:20)byte 複製,保留數值欄(bytes 20:50),不改任何平衡。
- **PG Windows 版修正(2026-07-17)**:先前 PG 的 `-wine.zip` 缺 Windows 啟動檔且內含 wine 版 exe(import `pgs.dll`),不能在 Windows 直接跑。改出正式 Windows 包 `PG-cht-1.2_{原始裝備,修改後裝備}_20260717-windows.zip`:Windows 版 exe(`fb8e8920`,import WING32 非 pgs.dll)+ `PG-cht.cmd`(`__COMPAT_LAYER=256COLOR`)+ patch 版 `WING32.DLL`(WinG 對話框抑制)+ `tools/patch_wing32.py` + `README-自含啟動.txt`。兩包 EQP 皆統一名(byte 相同)。AG 的 portable zip 本就含 `AG.cmd`+`shim.dll`+patch 版 `WING32.DLL`,Windows 版已就緒無須修正。
- **散布策略(2026-07-17)**:dist-all 每作只留 **Linux AppImage + Windows zip** 兩式。舊 PG `-wine.zip`(Linux「自帶 wine」、含 pgs.dll,與 AppImage 重疊)已移除。
- **AG 原始裝備數值 = 1995 原版(已核對)**:對 `AlliedGeneral_v1.1/Allied General/DATA/PANZEQUP.EQP`(真原版,md5 `fc90b84a`)全 438 單位 **0 筆數值差異**,名稱為中文。反戰車砲射程(stat byte 12)在原始裝備=0(近戰,原版),修改數值變體=2(可打 2 格,110 筆重新平衡之一)——「德軍 AT 砲射程 2」是修改數值版特徵,非原始裝備。
- **AG 加入 Kursk 庫斯克戰役(issue #4,2026-07-16)**:兩個 AG 變體的東線蘇軍路線都新增第 40 個劇本 Kursk(哈爾科夫'43→庫斯克→第聶伯河),地圖移自 PG、AG.EXE 擴 Table B、SCENARIO.TDB 接線。細節見 [`../../docs/scenarios/kursk-mod-ag.md`](../../docs/scenarios/kursk-mod-ag.md)。下表 4 個 AG 套件的 md5 已更新為含 Kursk 版。

## 套件清單(統一命名,4 版本 × 2 平台 = 8 檔)

命名方案(2026-07-17):`<遊戲>-[變體-]<平台>`。**PG 收成一包**(三份 PG EQP 數值 byte 相同、只有一套數值,無「修改數值」變體,叫兩個變體名不副實);**AG 真有兩變體**(原始裝備 / 修改數值,110 單位數值差異);PacGen 單一版。Linux=AppImage、Windows=zip(含 `.cmd`/`WING32.DLL`/`shim.dll` 等啟動檔)。

| 遊戲 | 變體 | 數值 | 格式 | 檔名 | 大小 | md5 |
|---|---|---|---|---|---|---|
| PacGen | — | 原始 | AppImage | `PacificGeneral-x86_64.AppImage` | 715M | `0aebfc2714bfee82962833b05e00485c` |
| PacGen | — | 原始 | Windows | `PacificGeneral-windows.zip` | 353M | `e57a12e3080b06d3927803e22de1225e` |
| PG | — | 原始 | AppImage | `PanzerGeneral-x86_64.AppImage` | 397M | `0891bd59b5523b25c0f5c54d36585d63` |
| PG | — | 原始 | Windows | `PanzerGeneral-windows.zip` | 17M | `6fd562e5e5d0fcf7e94cc6624baf8e97` |
| AG | 原始裝備 | 原始 SSI | AppImage | `AlliedGeneral-原始裝備-x86_64.AppImage` | 392M | `fe1369937952dcd501b15e121e3b02f9` |
| AG | 原始裝備 | 原始 SSI | Windows | `AlliedGeneral-原始裝備-windows.zip` | 12M | `5ebe60c1e9888668a05bc7a477f7d1b7` |
| AG | 修改數值 | 重新平衡 | AppImage | `AlliedGeneral-修改數值-x86_64.AppImage` | 392M | `e9655b5cf265c3d263f1e44d22f28ac0` |
| AG | 修改數值 | 重新平衡 | Windows | `AlliedGeneral-修改數值-windows.zip` | 12M | `04efdfbe4e81a6e784e8eba5ef5feda6` |
| PG 完整版 | 含影片 | 原始 | AppImage | `PanzerGeneral-完整版-x86_64.AppImage` | 469M | `960f6d2fc0592a61efecca4a7189db2c` |
| PG 完整版 | 含影片 | 原始 | Windows | `PanzerGeneral-完整版-windows.zip` | 89M | `ff3e9983136a7ee490e0360aa9cbfa69` |
| PG2 | — | 原始 | AppImage | `PanzerGeneral2-x86_64.AppImage` | 811M | `13b05b855396c29dccdf540d322f7691` |
| PG2 | — | 原始 | Windows | `PanzerGeneral2-windows.zip` | 437M | `fa38b5aaed6310671570beb207a75622` |

> **PG2《裝甲元帥2》繁中版(2026-07-18,已完成)**:5D General 家族**第四款**,全新 VC++/DirectDraw 引擎(與 PG1/AG 不同源),非「三部曲」但同 repo。中文化走**英文(預設)槽注入中文**(開機即中文、無語言 patch)+ 自建 **2-byte CJK 引擎**(atlas 1,582 glyph 烤進 EXE `.cjk` 節、drawStringCore + word-wrap 兩繪字路徑 hook + 5 個 ctype classifier 截斷修正)。全部 UI / 地形 / 裝備 / 指揮官 / **302 個劇本地名 + 戰役簡報散文**已中文化。AppImage 沿用 **PacGen DirectDraw 配方**(gdi renderer + GrabFullscreen + `wineserver -k` + `explorer /desktop=PG2,640x480`),wine 實測全綠:主選單 / 戰役+劇本清單全中文 / 戰役簡報中文散文 / 可玩地圖 + 中文單位資訊。Windows zip 含 `dplayx.dll`(DirectX redist 原生版,230400 bytes,md5 `4c5a47e4…`,import 現代 Windows 皆可解)+ 6 個隨遊戲 DLL + `裝甲元帥2.cmd`(256COLOR 相容層)+ 使用說明。**真機 Windows 未驗**(僅 wine smoke + dplayx import 靜態確認);深度遊玩未跑。細節見 [`../../pg2/中文化規劃.md`](../../pg2/中文化規劃.md)。
>
> **修正版(2026-07-18,md5 已更新為 AppImage `d61fe12f` / Windows `68fefc86`)**:使用者實機玩到戰場回報當機+空白。第一性原理攻根確認截斷/空白/`(null)` 一族的**共同根源=CRT `_pctype` ctype 表**(高位元組 signed-char 負索引→判非可列印→截斷),改用**指標 repoint 根本解**(`add_ctype_repoint.py`:4-byte 指標改向 + 自造 `.ctyp` 表,**取代先前 5 個 per-site classifier patch**、嚴格超集),一併修好狀態列 `(null)`(sb_3way 三方對照證)、工具列選單、及採購 ctype 家族;另加 `_output` NULL guard(`patch_null_guard.py`)修右鍵資訊 popup 當機(原版引擎既有 NULL-format bug)。EXE=`263bb8e7`。**2x 放大**:wine 虛擬桌面不拉伸(640×480 畫左上補黑)→ **內建 gamescope**(Debian bookworm 3.11.49 + 5 個非驅動 lib,1.8M)做整數 nearest 放大;`PG2_SCALE=2x/3x` opt-in、gamescope 失敗自動退回 1x(headless 已驗 fallback)、預設 1x;真整數放大需真機 GPU+DRI3(未驗)。
>
> **AppImage 生命週期修復(2026-07-18,AppImage md5 → `ece2c12b`)**:使用者回報「換新版 AppImage 但 (null)/採購/當機修了還在」——根因是 **AppRun 只在首次啟動 `cp` 遊戲檔到 `~/.local/share`,之後永不更新**,換新 AppImage 仍跑舊 EXE/舊資料(本機實測使用者跑的是舊 EXE `7a5365d4`,非 repoint `263bb8e7`)。修:`opt/game/` 加內容雜湊 `VERSION` 戳,AppRun 每次比對、不一致就**重同步遊戲檔並保留 `SAVE/`+`USERSCEN/`**(舊使用者無 VERSION → 視為需更新自動補)。**同時修「第二次啟動 BadWindow(X_CreateWindow)」**:already-installed 路徑未清 wine 狀態,第二次接上殘留 wineserver 握著失效 X window id → 崩;修為**每次啟動前對本遊戲 prefix `wineserver -k` 並輪詢等進程真死**再起(只清本遊戲、不誤傷 AG/PacGen 或使用者 :1),實測連續 3 次啟動皆全新 wineserver、0 X-error。**⚠ 此「AppRun 首次 cp 後永不更新」與「不清殘留 wineserver」很可能也是 PG/AG/PacGen 既有 AppImage 的潛在雷,日後重打包宜比照修**。採購畫面單位名空白、真整數 2x、真機 Windows 仍待使用者實機確認。
>
> **次要繪字量測修正 + 2x 設預設(2026-07-18,md5 → AppImage `ceca98dc` / Windows `20aaf894`,EXE `778926f7`)**:使用者實機(repoint 版)回報 3 個邊角——主選單提示飛出畫面、hover 單位狀態列中文名不見、採購名看似擠。第一性原理:**所有次要路徑寬度量測不 2-byte 感知**(measureWidth 28 caller/採購/狀態列置中逐 byte 加 glyphWidth,CJK 一字算 2 個字寬→位置高估錯位)。**一處修**:GWCLAMP stub 改 25 bytes 成 2-byte 感知(負 ch=量測中 CJK byte→回半寬、正 ch=原樣),同時修好提示位置(A)與狀態列單位名置中(C,實測「正規步兵/外籍兵團」)。採購「擠」查明**非 bug**(逐像素與正常文字一致,16px 密+金屬底+放大所致,屬清晰度 polish)。同時 **PG2_SCALE 預設改 2x**(gamescope→1x fallback 保留)。實測:自動更新 263bb8e7→778926f7 保留存檔、連 3 次重啟 0 BadWindow、回歸不退。(AppImage 體積因重打包夾帶 playtest 漂移產物略增,可日後 slim。)
>
> **字級改 14px Noto Medium + 狀態列殘留清框修(2026-07-18,md5 → AppImage `b9b9816d` / Windows `e7b87b10`,EXE `7d3187df`)**:字級對照(12/14/16px × Bold/Medium)使用者選定 **14px Noto Sans CJK Medium**(Bold 在 ≤14px 複雜字如「驅/戰/籍」糊)。同時修狀態列殘留 bug——根因是格子清除 RECT(VA 0x4acd68、每格 15-byte `[left,top,right,bottom]`)只 7px 高(給原生 8px 字設計),CJK 頂端對齊畫到 top+H-1 卻只清到 top+6,縮字不解(12px 仍殘 ~4px);修法是把相關欄位 `bottom` 抬高成 `top+fontH+1`(`patch_status_clear.py`,純資料 patch)。**EXE hash 演進補行**:16px(`778926f7`)→14px Medium(`7d3187df`)。
> - **build 腳本參數化(落回 repo)**:`pg2/build/build_atlas_pg2.py`(atlas H/font/face-index 可調,預設仍 16/Bold/index0 供舊呼叫端相容)、`build_hooked_exe_pg2.py`(WWSTUB 前進/行高改吃 `font_h`,`--font-h` CLI)、`patch_gwclamp_2byte.py`(半寬 `round(H/2)`)、新增 `patch_status_clear.py`(殘留清框修,正式收進 repo)。`make_full_release.py` 重寫為完整參數化正式建置腳本(`PG2_FONT_H` 預設 14、`PG2_FONT_TTF`/`PG2_FONT_INDEX` 可切回 16px/Bold/index0 或任意字級),串起 atlas → 主/word-wrap hook → `_pctype` repoint → NULL guard → 2-byte GWCLAMP → 殘留清框修 6 道 patch。
> - **順手修的既有 bug(非本輪新增,productionize 時發現)**:① `build_atlas_pg2.py` 的 `is_cjk()` 只認 CJK 碼段,漏掉音譯用的 U+00B7(‧),重建 302 檔完整版時在 `MALTA.TXT` 直接炸掉——scratchpad 的 `build_release/tools/` 已有修過的寬版(`>=0x80` 全收),repo 版是舊快照未同步,這次補回並加註解。② atlas 字型 `.ttc` 未指定 face index,PIL 預設 index 0 = **日文**臉(`fontTools` 枚舉 NotoSansCJK-Medium.ttc:0=JP 1=KR 2=SC **3=TC** 4=HK),16px 出貨版與先前 14px 驗證版皆同樣中招;逐字比對 1,582 字僅 3 個標點(。、‧)因日式/中式標點置放慣例不同而有像素差異,已改用 `font_index=3`(繁中臉)。
> - **從 repo 素材重建 = 逐位元組核對**:round-1 譯文(GUI97/MISC/EQUIP97/NAMES + 53 SCENARIO)用 repo `glossary.tsv`+`apply_translations.py` 對乾淨 7z 來源重跑,輸出與既有產物**逐位元組相同**;round-2 簡報散文(249 檔)因中介清單檔 `/tmp/undone_base.txt` 已隨 `/tmp` 清空、無法乾淨重放,沿用既有已驗證輸出(內容未變,僅重跑步驟略過)。重建出的 EXE 與先前已驗證的 14px 參考版相比,**僅 46 bytes 不同、全落在上述 3 個標點字符 glyph 像素內**,其餘(hook / repoint / NULL guard / GWCLAMP / 殘留清框 / 全部 306 個資料檔)逐位元組相同。
> - **實機驗證(自建 Xvfb,無害):** ① 狀態列 hover 6 種不同地名/單位(含「平地(4,9)」→「克林(12,7)」等長短切換)**殘留全消**,底部單位欄同淨。② 戰役清單 14px 完整(最長「卡昂-查恩伍德作戰-奧登河谷」未截)。③ **簡報 word-wrap 仍會截行,誠實回報**:地圖上彈出的「顧問簡報」對話框是**固定像素高的框**(實測約 64px、14px 行高 16px → 只能顯示 ~4 行),249 個簡報散文檔中 44 個開場白(`*I.TXT`)裡有 **30 個(68%)超過 4 行**,超出部分疊在地圖背景上、對比度低難以閱讀,且該框**無捲動**、點一下就整個關閉。此問題**與本輪字級無關**——框高是給原生 8px 英文字設計的固定值,換算 14px 行高只能塞 4 行,換 16px(現行出貨版)行高更高、能塞的行數更少,問題只會更嚴重;14px 是**緩解不是根治**。根治需要另外 RE 這個框背景的呼叫端(不同於 `0x43e955` word-wrap hook 本身),超出本輪範圍,留待後續。④ 65mm 山砲字串在 `EQUIP97.TXT` 確認存在且會走同一條已驗證繪字路徑,但受限本輪測試進度(場景/年代門檻)未在畫面上直接點出;改以「15榴彈砲/10.5榴彈砲/7.5步兵砲/88mm高射砲/37mm反戰車砲」等多個「數字(含小數點).CJK」混排 baseline 佐證,對齊正常。⑤ 全程(含購買/清單/簡報/hover)**0 page fault**。
>
> **簡報框回歸修:簡報專用 wrap/line-count clone(2026-07-19,md5 → AppImage `1d07f270` / Windows `e538417b`,EXE `7d3187df`→`10f63fa0`)**:上一輪 §7.11 誠實記錄的「地圖顧問簡報框塌、多行溢到地圖」查明**不是固定框高、也不是字級問題,而是 §7.9 `_pctype` repoint 的 blast-radius**。實機 A/B 定根(自建 Xvfb wine,西班牙戰役開場「馬德里攻勢」):repoint 前簡報框窄高、整段完整(= repo 英雄截圖 `evidence/pg2-campaign-briefing-cht.png`);repoint 後 CJK 高位元組讀到 `.ctyp` shadow 的 `0x0100`(_ALPHA)→被自動換行器當「不可斷字」→整段擠不斷行→行數暴減→框塌。**關鍵更正**:塌的是**框高**,肇因是**換行/計行函式 countLines `@0x43fdd5`**(其 `0x43ff02`/`0x43ffc5` 兩處讀 `[0x4ba538]`),**不是** measureWidthMultiline `@0x43eba0`(其行數只看 `\n`、與 ctype 無關;先前一版誤診此函式,實機證實對簡報 0 效果、且 `ret` 掉 briefing_open `@0x460f17` 簡報框仍在→非它所繪)。**為何 clone 不全域改**:countLines 有 **19 個 caller**(§7.9 文件說的「採購家族」`0x43ff02/0x43ffc5` 讀取即此函式),全域改會動到其它畫面。故把 countLines 整段(0x43fdd5–0x440051,637 B)clone 進追加的 `.brm` 節、只把其兩處 ctype 表基底改回原表 `0x4ba542`,並**只導向兩個簡報框繪製 caller**(`0x456e01` 於 fn `0x456d32`、`0x457000` 於 fn `0x456efb`)→共用函式與其餘 17 caller 逐 byte 不動、零波及(OLD↔NEW 位元組差 = PE 表頭 + `.brm` 節 + 2 個 caller rel32)。**實機驗證**:西班牙/保衛帝國/西線聖戰 三戰役開場簡報**恢復窄高框、整段完整**、與英雄截圖一致;狀態列「馬德里攻勢/德國 回合 1/天氣:晴朗/12·16·20 回合數」無 `(null)`、置中正確;戰役清單全名不截;AppImage 實機(換 VERSION 觸發重同步、實機拿到新 EXE)briefing 亦窄高完整;全程 **0 page fault**。工具 `pg2/build/patch_briefing_wrapcount_clone.py`,已串為 `make_full_release.py` 第 7 道 patch(atlas→主/word-wrap hook→repoint→NULL guard→2-byte GWCLAMP→殘留清框→**簡報 wrap-count clone**)。EXE 演進補行:14px(`7d3187df`)→簡報回歸修(`10f63fa0`)。
>
> **簡報 12px + 框完整顯示(2026-07-19,md5 → AppImage `13b05b85` / Windows `fa38b5aa`,EXE `10f63fa0`→`dc74e2a9`)**:使用者實機回報西班牙開場簡報**字偏大**、且**只顯示約 7 行後被下緣夾掉**(§7.12 clone 只把塌框長回,但**框高從未與整段文字結尾對照過**——box=countLines×10 對 CJK 仍不足)。修法**只縮簡報、其餘 UI 維持 14px**:簡報走**共用**的 word-wrap 繪字函式 `drawWrappedText @0x43e752`(xref 證實 **11 個 caller**,非簡報專用),故不能換 atlas 縮全部;改**追加 `.b12` 節**(12px atlas 1,582 glyph〔dense 映射與 14px 版相同→資料檔零重編〕+ flag 派發的 WWSTUB),把 word-wrap hook 導向 dispatch、**只包兩個簡報繪框 caller 的繪字呼叫**(`0x456e8d`/`0x45706b`,經 flag trampoline)→僅簡報 12px、其餘 9 個 word-wrap caller 與全部 drawStringCore UI(選單/清單/狀態列/採購/單位資訊)仍 14px。**框完整**:兩個簡報繪框位址(`0x456e1d`/`0x45701c`)的框高倍率由原生 `×10`(8px 字節距)改 `×24`;因 `countLines` 對 CJK 系統性少算行數(word-wrap 分類/量測與 atlas 實繪不同),框高倍率須**與繪字行距(12+2=14)脫鉤**、放大到 24 才保證整段可見(wine 校準:box_pitch 18 剛好、20 偏緊、**24 留裕**;過高只是框下方留白,與原版高框設計〔`evidence/pg2-campaign-briefing-cht.png`〕一致)。工具 `pg2/build/patch_briefing_font12.py`,`make_full_release.py` 第 8 道(`PG2_BRIEF_FONT_H`/`PG2_BRIEF_BOX_PITCH` 可調,預設 12/24;`PG2_BRIEFING12=0` 回退全 14px)。**實機驗證(自建 Xvfb,0 fault)**:西班牙(閃擊戰開場,6 行)結尾「歐洲的領導者。」、蘇聯戰役開場(11 行)結尾「工農紅軍將包圍敵人·迫使他們投降。」**皆整段完整、12px 清楚**;回歸:戰役清單/狀態列(馬德里攻勢·德國 回合 1·天氣:晴朗·12/16/20 回合數)/單位資訊維持 14px 現行外觀、無截斷無殘留;AppImage 換 VERSION 觸發重同步、實機拿到新 EXE `dc74e2a9`、標題正常。EXE 演進補行:簡報回歸修(`10f63fa0`)→簡報 12px+框完整(`dc74e2a9`)。
>
> **採購畫面殘影診斷(2026-07-19,未改 EXE)**:同輪順帶查使用者回報的「採購單位名/徵用標題殘影·重疊」。**分兩機制**:① **格內單位名標籤**(一號戰車D/A/B…)逐像素實測為**全寬(每字 13–14px 前進)+ 正常置放 + 引擎原生 1px emboss 陰影**(與所有 CJK 文字同繪法,drawWrappedText/drawStringCore 反組譯證實 CJK 皆 14px 前進單繪),對照英文版「Pz IID」乾淨;所見「重疊」= 密筆畫 CJK 上的 1px emboss 經 **gamescope 2× 放大**(實機 `gamescope -w 640 -h 480 -W 1280 -H 960`)視覺放大所致,**非繪字 bug**(與 §7.10「採購擠=非 bug」一致)。移除 emboss 會波及全畫面文字、blast radius 大,不宜。② **頂部「徵用」標題殘影**(較重)為真實殘留(底部一條小字殘條),但**受控 640×480 harness 未能重現**(該標題疑為進場捲動橫幅/特定子畫面,非本輪導覽路徑會經過),機制未定、盲修有波及風險。**結論**:標籤非 bug;標題殘影需使用者提供精確重現路徑(哪個子畫面觸發「徵用」標題)才能安全定位繪製/清除函式後對症,本輪**先回報不盲修**(符合「動共用路徑/有 blast radius 疑慮先回報」)。
> **PG 含過場影片完整版(2026-07-17,已完成)**:PG95 CD 版的 39 段過場 FMV(`Movies/*.MOV`,AVI/msvideo1)包進中文化 PG,與基本版並存。**不加字幕**——POC 實測 39 段全為無聲二戰紀錄片 B-roll(無旁白/無畫面英文字),無可翻譯素材;依使用者「有英文語音才字幕」的條件不加。wine 實測全綠:影片經 MCI avivideo + 內建 `msvidc32.dll` 正常播放、啟動**不顯示 wine 虛擬桌面**(遊戲以原生視窗執行,AppRun 直接 `wine PG-cht.exe`)、中文戰役選單可玩。Windows 端影片未上真機驗證(理論可行,MS Video 1 解碼器內建於 Windows)。字幕管線已驗證(原生 292×216 + 不透明黑底粗體,不可放大),日後要加說明字幕可快速補。

## 內部裝備檔校驗(PANZEQUP.EQP,統一名)

| 變體 | 內部 EQP md5 | 說明 |
|---|---|---|
| PG 原始裝備 / 繁中化 | `358703f348da00c4168d666691273c16` | 兩者相同(數值同、名已對齊) |
| AG 原始裝備 | `420af023fece43b0c8250349337cbc90` | SSI 原始數值 + 統一名 |
| AG 修改數值 | `8f9d08679200c8fad3f8868f66912e2e` | 重新平衡數值 + 統一名 |

> PacGen 裝備名走 `data/PACEQUIP.TXT`(自訂 dense 2-byte 編碼),非 `PANZEQUP.EQP`;細節見 [`equipment-pacific-general.md`](equipment-pacific-general.md)。

## 未納入 dist-all 的檔案

- **英文原版基礎包**(建置來源,保留於根目錄):`AlliedGeneral_v1.1.zip`(170M 完整)、`AlliedGeneralLite_v1.1.zip`、`PGWin95_reduced_v1.2.zip`——單位名為英文,非中文化發佈。
- 已移除:各套件的 `*.bak-preunify` / `*.bak-english-eqp` 備份、被取代的舊 AppImage(OrigEQP 舊名版、5/19 與 6/3 過期版)、PacGen v0.1 portable zip。
