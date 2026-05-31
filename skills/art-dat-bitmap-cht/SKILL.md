---
name: art-dat-bitmap-cht
description: >-
  把 SSI/Mindscape 1990s 戰略遊戲 (Allied General 盟軍元帥 / Panzer General 等) UI 上「烤在點陣圖裡」的英文
  (NATION/PURCHASE/PREFERENCES/EXPERIENCE/北非西歐俄羅斯按鈕…) 改成中文。這些字不在 EXE 字串表，而是壓在
  ART/ART.DAT 自訂封存檔的調色盤 RLE 點陣圖內。涵蓋:ART.DAT 索引格式、CPal 調色盤、RLEi 逐列 RLE 編解碼
  (含每列 BE16 rowlen 前綴 + token 文法 + 致命踩雷)、就地回填、去字保底 (保留土黃陰影)、ground-truth 對位、
  標楷體書法字。觸發詞:ART.DAT、RLEi、CPal、bitmap UI 中文化、按鈕中文化、PREFERENCES 偏好設定花屏/排版、
  exMedia、Allied General bmp、烤在圖上的英文。
---

# ART.DAT 點陣圖 UI 中文化 (盟軍元帥 / SSI 同引擎)

UI 上英文若**不在 AG.EXE 字串表**(grep 不到),多半是壓在 `ART/ART.DAT`(~25MB)裡的調色盤點陣圖。
本 skill 是 2026-05-29 完整逆向 + 實機驗證的成果。**格式由反組譯 AG.EXE 解碼程式 (`0x54CF05`) 確認,不是猜的。**

## 0. 一句話流程
解碼目標 RLEi → **去字保底**(只把英文字像素改回原底色,保留陰影) → 蓋中文 → 重編碼(每列加 BE16 rowlen 前綴) → **就地回填**(off+26 起,補零只到 off+size) → 進遊戲實測。工具見 `tools/art-dat/`。

## 1. ART.DAT 封存格式
```
0x00  4  00 00 00 00
0x04  4  "Indx"
0x08  4  BIG-ENDIAN u32 = index_end (例 0x4B92)
0x0E ..  16-byte 索引項,直到 index_end
```
索引項(16B):`[name:4][type:4][offset:BE u32][size:BE u32]`
- **所有多 byte 數字皆 big-endian**(遊戲讀時 byte-swap;找解碼程式的指紋)。
- type:`CPal`(調色盤)/`RLEi`(影像)/`Vers`/`Indx`。
- name 是 4-byte 代碼(`pYon` `aXOp` `andp`…),**不是 .bmp 檔名**——要靠尺寸/渲染縮圖目視定位。
- **`size` = 整個 chunk 長度(含 8-byte `RLEi`+size header)。chunk_end = `off + size`**(不是 off+8+size!見踩雷#3)。
- 1208 項 = 987 RLEi + 219 CPal(AG 版本)。

## 2. CPal 調色盤
資料 @ `off+22`,每色 8 bytes:`[idx:BE u16][R][R][G][G][B][B]` → RGB=(byte0,byte2,byte4)(每通道重複)。一個 CPal 常 >256 色含明暗 ramp,渲染取 idx 0-255。

## 3. RLEi 影像 chunk + RLE 編碼 ★核心★
```
off+0   "RLEi"
off+4   BE u32 chunk_size (index size = 8+chunk_size)
off+8   name(4)
off+12  palette_name(4)   ← 指向某 CPal
off+16  00 00 00 00
off+20  BE u16 W
off+22  BE u16 H
off+26  逐列資料開始        ← stream 起點
```
**每一列 = `[BE16 rowlen][token...]`,rowlen = 2 + token_bytes**(含這 2 個前綴 byte)。
解碼器用 rowlen 在列間 seek(`cur += rowlen`),token 從 `cur+2` 解,**解到該列滿 W 像素為止**(W 驅動,非 rowlen 驅動)。

token 文法(control byte `c`):
| c | 動作 | 後續 | 像素 |
|---|---|---|---|
| `0xFF` | 透明/跳過 n(保留背景,不寫) | 1B: n | n |
| `0x80`-`0xFE` (高位元) | literal:複製 `c&0x7F` 個 raw byte | n 個 byte | n |
| `0x01`-`0x7F` | run:`c` 個同色 | 1B: 顏色 | c |
- `0xFF` 在高位元判斷**之前**特例處理,不是 literal-127。
- run 顏色 byte 在 count **之後**。一個 token 不跨列。

**遊戲解碼程式**(AG.EXE,ImageBase 0x400000,.text VA = file_off + 0xC00):
列解碼 token loop `0x54CF05`–`0x54D18D`;列 seek(讀 BE16 rowlen)`0x54CE40`;chunk init `0x54CC42`。另有 remap 變體(`obj+0x133` flag 把每像素過 256-byte 轉換表),token 結構相同。

## 4. ★致命踩雷(務必遵守)★
1. **編碼器 literal ≤126、run ≤127,絕不吐 control byte = `0x00`/`0x7E`/`0x7F`/`0xFE`/`0xFF`**。原始檔 literal 上限 125。吐 0xFF(literal 剛好 127)→ 遊戲當透明 → 整片花屏。(資料 byte 可含 0xFF 無妨,只限 control 位。)
2. **每列必加 BE16 rowlen 前綴**。漏了 → 第一列後 desync。我曾把 rowlen 誤讀成 token(如 `00 d2` 其實 rowlen=210)。
3. **chunk_end = `off + size`,不是 `off + 8 + size`**。補零超過 off+size 會蓋掉**下一個 chunk 的 "RLEi/CPal" header** → `exMedia` 錯誤。就地回填只能寫/補零到 off+size。
4. **round-trip 過 ≠ 遊戲認得**。寬鬆解碼器能 round-trip 自己的輸出,但遊戲解碼器更嚴。**唯一定案法 = 反組譯遊戲解碼程式**(capstone 5.x:`CS_ARCH_X86, CS_MODE_32`)。
5. 解碼是**列獨立 + W 驅動**;每列 token 必須剛好 = W 像素。

## 5. 就地回填(不改索引)
解碼器讀完 H 列就停,chunk 尾多餘 bytes 忽略。重編碼 stream(含 rowlen 前綴)≤ `(off+size)-(off+26)` 即可原地覆寫 off+26 起、補零到 off+size。中文比英文短一定塞得下。ART.DAT 大小不變最安全。備份 `ART.DAT.bak`。

## 6. ★去字保底(保留陰影底色)★
金條/按鈕底是**土黃色帶陰影(漸層)**,不是單一色。**整塊平塗單色會破壞質感**(我曾錯填 idx 71 亮邊色,正確金條本體是 idx 138 土黃)。正解:
- 逐列:`bg_row = 該列非暗像素的眾數`;把該列「暗像素(英文字)」改成 `bg_row`。→ 保留每列自己的明暗(頂亮邊/本體/底陰影漸層),只去掉文字。
- 金條垂直結構範例(EXP 條):y100 頂亮(139)、y101 高光(71)、y102-112 土黃本體(138)+文字(180)、y113 底陰影(110)。只去本體列的文字,別碰亮邊/陰影。
- 綠色面板(idx 38)是平色,可直接平塗 idx 38。

## 6b. 同畫面有多個陣營主題變體 → 自動極性 + 整列填底
同一對話框常有盟/德/俄三版(如 SETTINGS = `abjd`盟綠底亮字 / `g[jd`德金底深字 / `rkjd`俄灰底),layout 相同但**配色不同**。一套寫死的偵測會壞掉。robust 做法:
- **綠/面板標籤:自動極性** — bg=區域眾數;同時找「比底亮 >45」與「比底暗 >45」兩群,**取像素多的那群**當文字(盟軍亮字 vs 德軍深字自動適應)。
- **金/灰標題條:整列填底去字** — 文字列 = 該列與底色對比像素 ≥4 的列;把**整列填回該列眾數底色**(不論字深淺,連灰底灰字也清掉);再蓋中文。比「只recolor暗像素」穩(灰字 lum>90 抓不到)。
- 標題條的去字範圍要夠寬涵蓋整個英文(俄版 SETTINGS 比盟版寬,窄範圍會殘留 SE…GS)。
- 工具實作見 `tools/art-dat/example_settings_dialog.py`(detext_band + label 自動極性)。

## 6c. 小對話按鈕(取消/確定 等)→ 密度法去字 + 保留內框 + 小字粗體
共用對話按鈕(OK/CANCEL/BELAY/UPGRADE/PURCHASE/NEXT/PREVIOUS,各 3 陣營×2 狀態,~90×23)有**金邊 + 內框矩形(如 OK 鈕黑框、`[ ]`)+ 漸層底**。`paintlib.paint` 的**整塊矩形平塗**會把內框與漸層蓋成一片土黃(使用者抱怨「左右蓋到框、上下土黃太多」)。robust 做法:
- **來源取自 `ART.DAT.bak`**(乾淨英文),de-text 後 patch 回現行檔(offsets 相同)。**切勿**在已中文化的現行圖上反覆重跑(會累積殘影)。
- **只處理 `x∈[INSET, W−INSET]`(INSET≈8)** → 自動排除金邊與**內框直線**(它們在邊緣,落在 INSET 外)。
- **逐列暗度分類**:`density(y)=該列在 x 範圍內遠離底色的像素比例`。只在 **density 10%~55% 的列(文字列)** 去字;**density >55% 的列 = 邊框/內框橫線 → 整列跳過保留**;<10% 視為空白列略過。→ 內框完整保留。
- 去字 = 把文字列內「遠離底色」像素改回**該列底色眾數**(保留漸層),非整塊單色。
- **字色自動偵測**(文字列遠離底色像素的眾數)當蓋字色 → 德軍紅字 / 奶油深字 / 俄灰底淺字各自正確。
- **小字用微軟正黑體粗體 `msjhbd.ttc`**(本身粗體、小字清晰);**標楷體 kaiu + stroke 在小字會糊成黑團**(踩過雷)。**固定字級**(如 13)求一致,別用動態縮放(各鈕偵測帶高不同會大小不一)。置中於按鈕中心 / 文字帶中心。
- 工具範例見 `tools/art-dat/example_dialog_buttons.py`。已完成 12 CANCEL→取消 + 15 OK→確定(代碼見 §10)。

## 7. 對位 = ground-truth 量測(別用肉眼猜!)
肉眼讀 2x 縮圖的座標**極易錯**(我連錯數次:把 x84 的 Supply 猜成 x155)。正解:
- **投影法**:在生成區掃「文字色 vs 底色」的列/欄密度,取密集帶 → 原文精確 bbox。
- 中文畫在**與原英文完全相同的 bbox/位置/字高**(原文不會被遊戲的 overlay sprite 蓋到)。
- **overlay 陷阱**:對話框背景圖上,遊戲會疊「數值框/儀表/按鈕」sprite。畫進背景的字若延伸到 sprite 區會被蓋(看似被切)。→ 字要待在原英文所在的安全區(如金條本體),別往下溢。
- CANCEL/OK 等是**獨立按鈕 bitmap**,不在對話框背景圖內 → 要改那些按鈕 chunk,不是背景。

## 8. 字型
- **小標籤(<14px slot)**:微軟正黑體粗體 `msjhbd.ttc`,遮罩門檻 mask=80-82(小字清晰)。MingLiU <12px 無內嵌點陣會碎。
- **★小字清晰度:抗鋸齒(AA)遠勝 bi-level★(2026-05-30)**:小型 CJK 標籤(戰損兵種名/購買面板)用硬門檻 bi-level(只 ink/bg 兩值)在 ~10-13px 會糊。正解:把 glyph 灰階**覆蓋率 cov(0-255)映到「底色↔ink 漸層」**,每階找最近調色盤 idx → 平滑清晰。實作:`ramp=[nearest(blend(bg_rgb,ink_rgb,c/255)) for c in range(256)]`;paint 時 `if cov>=24: rows[y][x]=ramp[cov]`。ink 取**原英文字最深的色**(更黑更清楚);短名(2 字)空間夠可放大字級(15px)。代價:漸層像素降低 RLE 壓縮率,re-encode 後務必 `assert stream≤space`(實測戰損/購買都仍塞得下)。工具範例 `_ag_analyze/cn_classnames2.py`(`ramp_for`/`nearest`)。
- **按鈕/標題要雍容華貴的書法感**:標楷體 `kaiu.ttf`(DFKai-SB,毛筆楷書),size 16-20,mask 128。可選筆畫膨脹(PIL MaxFilter)做「渾厚」。
- 真**草書**(于右任風)需第三方標準草書 TTF,Windows 無內建。
- 字級對齊原英文字高;置中可用 `cxover`/`yoff` 微調(標題置中於對話框中心 W/2,標頭下移約 +2px 置中於金條)。

## 9. 工具(`tools/art-dat/`,需 python3 + Pillow + capstone)
- `artlib.py`:`load` / 索引 parse / `parse_pal` / `decode_rle_v2` / `encode_stream_v2` / `patch_inplace_v2`(全部 v2 = 正確 rowlen-prefix 格式 + 安全 token cap + off+size 邊界)。
- `paintlib.py`:`Screen` class(autobox 偵測 + paint + commit + preview)。
- `example_pyon_preferences.py`:PREFERENCES 偏好設定(de-text 保底 + ground-truth 對位 + 小字)。
- `example_campaign_buttons.py`:戰場按鈕 北非/西歐/俄羅斯(標楷體 + 強制深字 idx69)。
- `example_dialog_buttons.py`:共用對話按鈕 取消/確定(§6c 密度法保留內框 + 微軟正黑體粗體;來源取自 .bak)。

## 10. 已完成座標(AG 盟軍元帥)
- `pYon` 334×450 = **PREFERENCES 偏好設定**(標題/經驗×2/聲望×2/補給/天氣/顯示部隊強度/顯示隱藏單位/顯示對手移動,全中文 + de-text 保底)。
- `andp/anSn`=北非、`awhp/awWn`=西歐、`arxp/argn`=俄羅斯(各普通+高亮兩態,148×37,標楷體)。
- `sR`c`(0x73526063) 139×18 = SCENARIO SELECTION → 戰術選擇。
- **SETTINGS 設定畫面 231×298 三版**:`abjd`(0x61626a64 盟)、`g[jd`(0x675b6a64 德)、`rkjd`(0x726b6a64 俄)。設定/音量/靜音/記錄遊戲歷程/顯示六角格邊界/戰鬥動畫/隱藏桌面(自動極性 + 整列去字)。
- ORG TABLE 記事本 = `alzs/gezs/ruzs`(272×430,易與 SETTINGS 混淆,別搞錯)。
- 640×480 那 42 張是過場場景照,非 UI。
- **戰場按鈕 6 顆(`anSn/andp/awWn/awhp/argn/arxp`)改用密度法 de-text**(從 .bak 取原圖,只填文字帶,保留奶油漸層 + 俄版紅塊 + 虛線內框 + 金邊),標楷體。
- **共用對話按鈕 取消/確定(§6c 完成,2026-05-30)**:CANCEL→取消 = `cNQn cNbp agJ1 agJ2 adf1 adf2 aLQn aLbp gEQn gEbp rUQn rUbp`;OK→確定 = `dUfn daip gLcn gLtp g\`Sn g\`dp g]Xn g]ip okdn okup r_Vn r\`Sn r\`dp r]Xn r]ip`(微軟正黑體粗體 size 13,密度法保留內框)。
- **全量補完共用按鈕(67 chunk,2026-05-30)**:PURCHASE→購買、EXIT→離開、NEXT→下頁、PREVIOUS→上頁、UPGRADE→升級、BELAY→撤回、APPROVED→核准、DENIED→否決(判定條 `ge_p`/`al_p`/`geWn`/`ruWn`/`ru_p`/`alWn`,紅綠高對比用 §6b 整列填底去字)。診斷法:`tools/art-dat/diag_buttons.py`/`diag2.py`(比對英文原版 vs 目標找「未改=仍英文」chunk + render 縮圖總表逐一判讀)。`kcoy`(0x6b636f79) 是有人畫的 Claude 圖示彩蛋,**勿動**。
- **★戰損統計對話框 `aRon`(0x61526f6e,448×441)= 整張背景圖,連表格線/單位剪影/18 兵種名全烤在裡面★(2026-05-30)**:左右上角 LOSSES→戰損(標楷體);表內 18 兵種名(步兵/戰車/偵察/砲兵/反戰車/防空砲/對空防禦/防禦工事/戰鬥機 | 戰術轟炸機/水平轟炸機/潛艇/驅逐艦/主力艦/陸運/空運/海運/航空母艦)用投影法量格線(豎 x=26/109/164/218/316、9 橫列 ROWH≈32.2)逐 cell 去字 + 微軟正黑體粗體 size13、左對齊原英文起點(左欄 x33/右欄 x226)、長 5 字名縮排塞欄寬不溢格線。德/俄變體 `gRon`/`gSjR` 上角是銀色把手裝飾、**無 LOSSES**。
  - **★關鍵教訓:這些兵種名是烤在 bitmap、不是 EXE 字串★**。EXE 內 set2(@`0x1C7F83`,步兵/戰車…)那組同名中文字串是**別的畫面**用的,改字串對戰損表完全無效;一定要改 `aRon` 點陣圖。判斷法:翻字串後重開遊戲若該處仍英文 → 就是 bitmap。
  - 去字踩雷:dense 文字列的 per-row mode 會翻成 ink 色 → 殘留虛線;改用 cell-global 羊皮紙底 + 只取淺色 grain pool 填回才乾淨。
  - **★戰損對話框有 3 陣營變體(同購買面板)★(2026-05-31)**:`aRon`(盟,角落有 LOSSES→戰損)、`rRon`(0x72526f6e 俄,角落有 LOSSES→戰損)、`gRon`(0x67526f6e 德)+`gSjR`(0x67536a52 德另一態)= 德版上角是**銀色把手裝飾無 LOSSES**,只需做 18 兵種名。修 theme bug(見 panzer-general-cht §1)後才會顯示對應陣營變體 → 三套都要做。各 chunk **palette/底色不同,bbox/INK 須各自投影量**(rRon 的 LOSSES 比 aRon 低約 20px,沿用 aRon bbox 會殘留)。
- **購買部隊畫面 `ajSn`(0x616a536e,636×456)= 整張全螢幕背景圖(2026-05-30)**:右側金牌資訊面板 5 標籤全烤在裡面 — UNIT SLOTS FREE→剩餘編制、CORE→核心、AUXILIARY→輔助、YOUR PRESTIGE→您的聲望、TOTAL COST→總花費(runtime 疊數字 0/2,核心/輔助需維持原 CORE/AUXILIARY 欄位 x 對齊)。微軟正黑體粗體 + AA(§8),gold idx138↔ink idx69 自動偵測深字,上兩列受 11px 行距限用 9-10px、下兩列空間大用 13px,去字用 gold grain pool 回填保留金漸層。stream 221144≤space 292422。**同屬 bitmap 非字串**(EXE 只有 runtime 用的 Core/Auxiliary/Prestige 小寫字)。
- 未做:CAMPAIGN SELECTION 標題(疑合成背景)、NEIN/JAWOHL 等其他共用按鈕。
- **★「OK」鈕不是 bitmap → 是 GDI 字串★**:戰損等對話框底部 OK 窮舉 ART.DAT 找不到對應英文 bitmap → 實為 EXE 內 12 個 `OK` GDI 字串(4-byte slot),已指標重導向→確定(詳見 skill `panzer-general-cht` ag-ui-runtime.md §7)。**教訓:點陣圖找不到的 UI 英文,回頭查 EXE 字串(GDI 即時繪字)**。

## 11. 適用範圍
此 ART.DAT(Indx/CPal/RLEi + 逐列 rowlen-prefix RLE)格式為 SSI/Mindscape 1990s 同引擎共用,Panzer General / Allied General 等皆適用(換遊戲要重新確認 chunk 偏移與 W/H,RLE 文法相同)。

## 12. 在開頭畫面 (SPLASH.DAT) 加鋼鐵漸層中文標題 (2026-05-30)
`ART\SPLASH.DAT` **非 Indx 格式**(檔頭 `Vers Vers…`,無中央索引),但主圖是單一 RLEi、**內部 RLE 格式與 ART.DAT 完全相同**,可用同一套 `decode_rle_v2`/`patch_inplace_v2`:自建 entry `e_rlei=[b"sjbh",b"RLEi",0x1a38,<BE32 size@0x1a3c>,0]`、`e_cpal=[<palname>,b"CPal",0x0e,<size@0x12>,0]`(palname 在 RLEi off+12,本片為 `7e715c68`)。`chunk_end=off+size`(=0x4cfa6,在 file 結尾前;尾端 ~50B 是別的結構勿碰)。re-encode 整張 640×480 + 補零到邊界即可就地回填(我方 v2 encoder 比原檔省,slack ~37KB)。
**加「盟軍元帥」對齊英文 GENERAL 風格**(自然、不突兀):
- 量原英文 `GENERAL` bbox:銀色高亮像素(`max(rgb)>110 且 max-min<55 且 lum>120`)在 y160-256 的範圍 → 取寬度與水平中心。
- 中文字寬縮到 ≈ GENERAL 寬、置中其下方(本片 size≈54、y270-317)。
- **垂直鋼鐵漸層**:由上到下 RGB stops 例:`(255,255,255)→(232,232,236)→(176,176,186)→(150,150,160)→(214,214,222 反光帶)→(120,120,130)→(96,96,104)`;逐列依 t=(y-ty0)/h 取色 → 每色找調色盤**最近 idx**(歐氏距離)上到字遮罩像素。
- **深色描邊**:遮罩 `MaxFilter(5)` 膨脹後、非字身處填暗 idx(≈最近 (20,20,24)),字身再蓋漸層 → 立體感。字型用微軟正黑體粗體。
- 工具:`tools/art-dat/example_splash_title.py`;成品預覽 `screenshots/splash_zh.png`。
