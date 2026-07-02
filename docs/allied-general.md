# 盟軍元帥 (Allied General) 中文化

*Allied General*(SSI 1995,與 Panzer General **同引擎**)的繁體中文化。針對社群「Lite v1.1」重打包版(`AG.EXE` 2,167,611 bytes),完成 EXE 字串、資料檔、**烤在點陣圖裡的 UI**、開頭畫面標題全面中文化,並修掉重打包者藏的簽名。

### 遊戲簡介 — 經典 Hex-based 戰術骨灰作

作為 SSI 經典神作《裝甲元帥》(Panzer General) 的續作,《盟軍元帥》在 Windows 95 世代將戰場視角切換至盟軍陣營。其核心玩法本質上是一套**具備部隊養成機制的六角格 (Hex-based) 資源調度與戰術模擬系統**。

**核心架構 — 三大 Campaign**:遊戲將歷史戰役拆解為三條獨立邏輯主線,各有不同操作痛點與資源限制:

| 戰線 | 風格 | 痛點 |
|---|---|---|
| **蘇聯線 (Soviet)** | 先防禦後反攻 | 初期(巴巴羅薩行動)以空間換時間,用消耗戰拖延德軍閃電戰;中後期重工業成型後全面壓制 |
| **英國線 (British)** | 長途補給與多軍種協同 | 戰場在北非沙漠與義大利,裝甲基數小,極度依賴海空軍掩護與精準戰線維持 |
| **美國線 (American)** | 強大資源與空權壓制 | 從火炬行動推到德國本土,容錯率最高,後勤與空中火力壓倒性 |

**核心機制與戰術邏輯**:深度不在複雜操作,而在三個底層機制相互堆疊:

1. **核心部隊繼承 (Core Units Instance)** — 關卡結束時倖存部隊攜帶累積經驗值 (Stars) 直接繼承到下一關。玩家真正的核心資產是這群高經驗王牌;**避免王牌因失誤被全滅 (Permadeath) 是貫穿全局的最高原則**。
2. **科技樹演進與動態升級** — 戰役時間軸推進 (1941 → 1945) 解鎖新歷史裝備,可消耗**聲望值 (Prestige)** 升級部隊硬體。範例:輕型 M3 Stuart → 主力 M4 Sherman → 後期抗虎式主力 M26 Pershing。
3. **多兵種協同 (Combined Arms) 與地形限制** — 單一兵種衝鋒極易觸發「遭遇戰 (Rugged Defense)」而崩盤。標準戰術執行鏈:

   > 偵察車 (Recon) 開霧 → 火砲 (Artillery) 間接壓制 → 空軍洗地 → 步兵/裝甲收尾

   城市與密林等地形對裝甲有極高負面修正,須改由步兵近身清理。

**總結 — 核心價值**:成功在於「易學難精 (Easy to learn, hard to master)」。它把複雜的軍事手冊計算隱藏於簡單的攻擊/防禦數值與地形加成公式中。對喜歡沙盤推演、注重部隊養成與最優解戰術布局的玩家,本作奠定了現代回合制策略遊戲(如 *Panzer Corps*)的底層邏輯。

### 中文化後的開頭畫面

在原版 `ALLIED GENERAL` 標誌下,新增**鋼鐵漸層書法風**的「盟軍元帥」(字寬對齊英文、置中其下、套垂直銀灰漸層 + 深色描邊,直接重繪進 `ART\SPLASH.DAT` 的點陣圖):

![盟軍元帥 中文化開頭畫面](screenshots/ag_splash_zh.png)

### 完成項目

| 類別 | 內容 |
|---|---|
| EXE UI 字串 | menu / 對話框 / 按鈕 / 狀態列(Big5 就地翻譯 + RT_MENU/RT_DIALOG/RT_STRING) |
| 任務簡報 | RT_STRING 全中文,並修正兩個致命踩雷:**尾端空格 padding 造成換行大空洞**、**空字串(wLen=0)導致組字器回顯重複** |
| 回合/開戰畫面 | 天氣(晴朗/陰天/下雨/下雪)、地面(乾/泥濘/結冰)、陣營(盟軍/軸心)、月份(一~十二月) |
| 裝備名稱 | `PANZEQUP.EQP` 全中文 + 縮短(國名 1 字、刪重複英文機名;如 `美國 野馬 P51B Mustg` → `美野馬 P51B`) |
| 城市/地形/戰術標籤 | `MAPNAMES.STR`(1553/1570)、`TACMAP.TGF`(與 PG 共用) |
| **點陣圖 UI(烤在圖上)** | PREFERENCES / SETTINGS(盟德俄三版)/ 戰役按鈕 / 共用按鈕(取消·確定·購買·離開·下頁·上頁·升級·撤回·核准·否決)/ **購買部隊金牌面板(盟德俄 3 變體)** / **戰損統計表(盟德俄 3 變體 + 18 兵種名)** — 全靠逆向 `ART.DAT` 的 RLEi 編解碼重繪;小字改用**抗鋸齒**渲染求清晰 |
| 狀態列/對話框按鈕(GDI 字串) | 油料·彈藥·戰壕值·主動…、OK→確定(指標重導向)、Cancel→取消 / Yes→是 / No→否(就地翻) |
| 開頭畫面 | 加「盟軍元帥」鋼鐵漸層標題(見上) |
| **修正陣營主題(theme)bug** | 戰鬥介面 + 購買畫面 + 戰損表共用 theme 全域,蘇/德場景顯示錯主題。**真根因 = classify 比對的戰役名表被前一次翻譯就地改成中文,但場景 lookup 名仍英文 → 永不命中 → 全部落同一主題**;另有更早一次「配色 fix」把 switch 改反方向(因 classify 已壞而休眠未爆)。修法 = classify 表重指英文副本(顯示維持中文)+ switch 改回原始。實機定案 theme0=盟/1=德/2=俄 |
| **修正點陣圖洩漏 bug** | 狀態列「戰壕值/確定」指標重導向時,空區選到單位資料標籤表(0x20-stride)的 slot 內 padding,off-by-one 蓋掉前一字串 NUL → 單位面板顯示「油料:戰壕值:%d」亂入。改放真正不被索引的描述區 padding |
| **移除重打包者簽名** | 藏在狀態列(**反向 + XOR 0xFF** 編碼)的 email `raywolf@chuvashia.ru` → 改顯示玩家代號;明文 `kilroy was here.` → `盟軍元帥中文版` |

### 點陣圖 UI 中文化 — 設計概念與前後對照

這是整個專案技術含量最高的部分。**這些英文不在 EXE 字串表裡** —— 它們是「**烤**」在 `ART/ART.DAT`(~25 MB 自訂封存檔)內的**調色盤 RLE 點陣圖**。你 grep 不到、改 EXE 也沒用,只能把那一張張小圖**解碼出來、抹掉英文、重畫中文、再編碼塞回去**。

#### 共用對話按鈕(取消 / 確定 / 購買 / 核准 / 否決 …)

![按鈕 中文化前後](screenshots/ag_buttons_before_after.png)

每顆按鈕是獨立的 RLEi chunk,連金邊、漸層底、內框、紅/綠高對比都要原樣保留 —— **去字只抹文字筆畫、不能平塗單色**,否則質感全毀。

#### 戰損統計表(整張對話框背景圖,連 18 兵種名都烤在裡面)

![戰損表 中文化前後](screenshots/ag_losses_before_after.png)

`LOSSES → 戰損`、`Infantry/Tank/… → 步兵/戰車/…` 全部烤在**同一張 448×441 背景圖**裡(連表格線、單位剪影、羊皮紙紋理都是)。而且**盟 / 德 / 俄各有一套變體**(`aRon`/`gRon`/`rRon`),由陣營主題自動選擇 —— 三套都要逐一重畫。

#### 購買部隊金牌資訊面板

![購買面板 中文化前後](screenshots/ag_purchase_before_after.png)

`UNIT SLOTS FREE → 剩餘編制`、`YOUR PRESTIGE → 您的聲望` … 同樣烤在整張購買畫面背景圖,亦有盟 / 德 / 俄三變體(`ajSn`/`gcSn`/`rpSn`)。

#### 設計概念(重繪工作流)

1. **格式逆向不靠猜** —— ART.DAT = `Indx` 索引 + `CPal` 調色盤 + `RLEi` 影像。RLEi 是**逐列 RLE**(每列 `BE16 rowlen` 前綴 + run/literal/skip token)。整套文法是**反組譯遊戲自己的解碼程式**(`AG.EXE` VA `0x54CF05` 一帶,capstone)逐指令確認的 —— 寬鬆解碼器能 round-trip 自己的輸出,但遊戲解碼器更嚴,差一個 control byte 整片花屏。
2. **去字保底(保留陰影漸層)** —— 金條/面板底是帶陰影的漸層,逐列把「文字暗像素」改回**該列底色眾數**,保留頂亮邊 / 本體 / 底陰影,不平塗單色。
3. **對位用 ground-truth 投影,不用肉眼猜** —— 在生成區掃「文字色 vs 底色」的列/欄密度得到原文精確 bbox;中文畫在與英文**完全相同的位置/字高**,避開遊戲疊上的 sprite。
4. **小字清晰度靠抗鋸齒(AA)** —— 小型 CJK 用 bi-level 硬門檻會糊;把字型 glyph 的**灰階覆蓋率映到「底色↔墨色漸層」**,每階取最近調色盤色,小到 9-10px 也清楚。
5. **就地回填、archive 大小不變** —— 中文比英文短,重編碼的 stream 一定塞得進原 chunk;補零只到 `off+size` 邊界(超過會蓋掉下一個 chunk 的 header → `exMedia` 崩潰)。

> **關鍵心法**:遊戲裡找不到對應的 UI 英文,先判斷它是「**EXE 字串(GDI 即時繪字)**」還是「**烤在 ART.DAT 的點陣圖**」—— 翻了 EXE 字串重開仍英文,就是後者。兩者工具鏈完全不同。

#### 陣營主題(theme)系統 — 一個 bug 帶出的連鎖

戰鬥介面、購買畫面、戰損表**共用同一個 theme 全域**(`[0x5f1b34]`,實機定案 `theme0=盟 / 1=德 / 2=俄`),由 `classify`(把當前戰役名對「北非 8 + 西歐 14」兩張表做 `strcmp`)決定。**最隱蔽的 bug**:更早一次翻譯把 classify 比對用的戰役名表**就地翻成中文**,但程式比對時拿的是**英文 lookup 名** → 中文表 vs 英文名**永遠不命中** → 所有場景擠進同一個主題。修法 = 把 classify 表**另存英文副本並重指**(畫面顯示走另一條中文重導向,兩者拆開)。

> **教訓**:`strcmp`/lookup 用的字串表**絕不可原地翻譯**(同 `SCENARIO.TDB` 鐵則)。要顯示中文就用指標重導向另存中文副本,讓 lookup 表保留英文。

### 技術文件(可重做)

- **點陣圖 UI 中文化**(ART.DAT 索引 / CPal 調色盤 / RLEi 逐列 RLE 編解碼 / 去字保底 / 抗鋸齒小字 / 鋼鐵漸層標題):[`skills/art-dat-bitmap-cht/SKILL.md`](../skills/art-dat-bitmap-cht/SKILL.md) + `tools/art-dat/`
- **EXE / 資料檔 中文化 + 執行期 UI + 破解者簽名逆向**:[`skills/panzer-general-cht/SKILL.md`](../skills/panzer-general-cht/SKILL.md)、[`references/ag-ui-runtime.md`](../skills/panzer-general-cht/references/ag-ui-runtime.md)

> 與 PG 相同,本 repo **不含遊戲本體**(版權所有),僅放可重做的腳本 / 技術文件 / 截圖。

### 踩雷紀錄(2026-05-30 事件)

| 事件 | 根因 | 處理 |
|---|---|---|
| **改完 email 後一進戰場就閃退** | 破解者的 email blob(`0x3d15f–0x3d17a`,reversed+XOR0xFF)**尾端 2 byte 與可執行碼重疊** —— 正好是 `call 0x43dda3` 的運算元高位 + 一個 `ret`。原本「整段 28 byte 覆寫」把 call/ret 改成 `0xFF` → 選單能開、**一進關卡執行到該段就崩潰**。 | **只改字串需要的 13 byte**(null + Big5),保留 `0x3d15f/0x3d160` 的 code byte;反組譯確認 `call+ret` 還原。詳見 [`ag-ui-runtime.md` §6](../skills/panzer-general-cht/references/ag-ui-runtime.md)。**教訓:cracker 把資料藏進 .text 時常與指令交疊,改之前務必反組譯確認該 byte 不是 code。** |
| **字形與原始 Lite 不同** | 前期跟隨 PG 把字體 face `Arial`→`Tahoma`(26 處);Windows 原生對 Big5 的代換字型因此不同。 | **還原回 `Arial`**(`b"Tahoma"`→`b"Arial\0"`,26 處)。Tahoma 改法是 wine 端 Big5 fallback 用,**Windows 原生保留 `Arial` 即可**。 |
| **256 色才能執行(WinG 老遊戲)** | AG.EXE 啟動檢查 `GetDeviceCaps(BITSPIXEL)==8`,Win10/11 為 32bpp → 跳「需 256 色」對話框退出。 | 本機無編譯器 → **用 Python 手工組 32-bit PE `shim.dll`**:轉發 29 個 GDI32 函式給真 gdi32、只攔 `GetDeviceCaps` 的 BITSPIXEL→回 8;patch AG.EXE import `GDI32.dll`→`shim.dll`。手法同 pg-cht wine 的 `pgs.dll`([`panzer-general-wine`](../skills/panzer-general-wine/SKILL.md))。 |

