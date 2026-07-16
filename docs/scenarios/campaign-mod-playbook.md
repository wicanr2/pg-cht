# 5D 引擎戰役改造 playbook（經驗萃取,面向全戰役大改）

這份文件把 [Kursk 移植（issue #4）](kursk-mod-ag.md) 學到的機制與技法萃取成可重用流程,供日後**大幅改造整個戰役**(重排分支、增刪劇本、換地圖、重新設計戰役線)參考。適用 SSI 5D 引擎的《裝甲元帥》(PG)、《盟軍元帥》(AG);《太平洋元帥》(PacGen) 是不同世代(二進位 CAMPAIGN.BIN),部分不適用。

標註慣例:**[已證]** = Kursk 一役實作/實機驗證過;**[推定]** = 由已證機制外推、大改前需再驗;**[未探索]** = 尚無資料。

## 1. 先建測試迴圈(全案樞紐)

沒有本機測試迴圈就無法驗證正確性,任何改造都是盲改。

- **[已證] AG 本機 wine render 法**:系統 wine 11 + **AG 自己的 WINEPREFIX**(AppImage 自帶的、或 portable 目錄配對的,**不可借用別作的 prefix**)+ `wine explorer /desktop=AG,1024x768 ./AG.EXE`,DISPLAY 深度 8(256 色)。AG.EXE 需 256 色 shim(import `GDI32→shim.dll`)+ `WING32.DLL`,兩者散布包已含。
  - 早期黑畫面的坑:借用了別作(PacGen)的 prefix → 換成 AG 自帶 prefix 即正常。
  - 起 AG 要時間(prefix 解壓 + 載入),截圖前留 ~40s。liveness:`setsid timeout NN wine …`,清程序用 `pkill -x`(見第 6 節)。
- **[推定] PG 同法**:PG-cht.exe 已是 patch 版(256 色 + 兩個 nil-deref patch),AppImage 直接可跑。
- **驗證分兩層**:①**實機**(能載入、render、玩一回合不崩)②**機制**(反組譯/parse 確認 EXE 表與 TDB 鏈正確)。逐關玩通常不切實際(見第 5 節),機制驗證是合理替代。

## 2. 核心機制:劇本名 → 檔案 → 分支

### 2a. 名稱→SCN 解析(AG.EXE Table B)[已證]
AG 不靠 TDB 位置,而是 AG.EXE 內硬編**英文劇本名表 + strcmp getter**:
- 英文名陣列 @file `0x1C2A2C`(39 名,campaign 設計序)、pointer table @`0x1C2BB8`。
- campaign getter B @VA `0x494DE5`(file `0x941E5`):傳入劇本名 → strcmp 迴圈遍歷指標 → 回 1-based index → 引擎載入 `SCENARIO/GAME{index:03d}.SCN`。cap `cmp eax,0x27`(=39)@file `0x94201`。
- 另有兩個 display getter(Function1 @`0x9425C`、Function2 @`0x94935`)共用同一 base pointer(`0x5F19B8`/`0x5F19B4`)。
- 完整 Table A/B/C + getter 分析見 [`../../skills/panzer-general-cht/references/ag-scenario-menu.md`](../../skills/panzer-general-cht/references/ag-scenario-menu.md)。

### 2b. 中文戰術選單名表 B'（與英文 Table B 不同!）[已證]
- 中文名 pointer @file `0x1BFEE8` → Big5 字串 @`0x1BFEF0`;戰術 grid loop bound `cmp eax,0x27` @file `0x57a94`。
- 這條決定「戰術選單」能不能單獨選到某劇本、顯示什麼中文名。**與 campaign 用的英文 Table B 是兩套**,要各自處理。

### 2c. SCENARIO.TDB(分支 + 聲望)[已證]
- 純文字、`.` 分欄、CRLF 分記錄,**139-byte/記錄**:`.<名25>.<painting8>.<大勝名25>.<小勝名25>.<落敗名25>.<wcnt4><timo4><dvps4><mvps4><lspr4>.`。
- header 含 count 欄(`.00010.00000039.` 的 `00000039`)。記錄**字母序**排列。
- **分支用劇本名引用**(非編號),所以改分支只要改名字串;painting 欄是簡報畫 base(可借用相近地圖如 `karkov`)。
- 逐作已 dump:[campaign-routes-pg/ag/pacgen.md](campaign-routes-ag.md)。

### 2d. SCN 檔與單位相容 [已證/部分推定]
- **[已證]** SCN 地圖內嵌(無外部 .stm 檔;`..\dat\*.stm` 只是 SCN 內 logical name)。移植一關 = 搬整個 `GAME###.SCN`。
- **[已證]** PG↔AG **raw copy 可行**:兩作 `PANZEQUP.EQP` 都 437 records × 50-byte、offset 一致、**單位 ID 排序完全相同**,故 SCN 內以 ID 引用的單位天然對到同一單位。SCN 檔頭 magic 後 2 bytes 位元組序相反(AG=(X,08)、PG=(08,X)),但不影響 AG 載入。
- **[推定/警示]** 地形 tile ID 若某作不同會花屏;每關移植後要實機看地圖是否連貫。
- **[未探索]** PacGen SCN 是不同世代(EQP 812 單位、不同格式),**不可**與 PG/AG raw 互換。

## 3. 改造技法

### 加一個劇本(Kursk 已證流程)
1. 取得/建出 AG 格式 `GAME{N}.SCN`(N=既有數+1)。可從 PG raw copy(單位相容時)或用編輯器原生建。
2. **AG.EXE 擴英文 Table B**:原 pointer[39] 位置常被鄰接資料佔用 → **把整個 pointer table 搬到 free `.data`**(Kursk 用 VA `0x5EED00`/file `0x1BFF00`),複製舊指標 + 加新的指向新英文字串;**repoint 全部 base 參照**(getter B + Function1 + Function2);**bump getter cap** `0x27`→`0x28`。
3. **擴中文名表 B'** + bump 戰術 grid loop bound(讓戰術選單顯示 + 可選)。
4. **SCENARIO.TDB**:count +1;插新記錄(字母序);把上一關的 大勝/小勝(或指定結果)改指新關。
5. 兩變體同步(見第 6 節 hardlink 注意)。

### 改分支 / 重排戰役線
- 純改 SCENARIO.TDB 名字串即可(不動 EXE),前提是所有目標劇本名都已在 Table B。**新劇本名必須先進 Table B 才能被 campaign 解析**,否則 `page fault`(見第 6 節崩潰特徵)。

### 移植地圖
- PG→AG:單位排序相容時可 raw copy。跨到 PacGen 不行。
- 原生重建:用社群編輯器(第 7 節)在 AG 格式內畫,最穩但費工。

## 4. 大改整個戰役的 playbook

要「重做整條/多條戰役線、增刪多關」時,除上述單關流程,額外要處理:

1. **審計所有依賴劇本數(39)的常數/陣列** **[部分推定]**:已知至少兩個 `cmp eax,0x27`(campaign getter @`0x94201`、戰術 grid @`0x57a94`)。大改前**反組譯全面搜 `83 f8 27`(cmp eax,0x27)與 `27`/`0x27` 相關 immediate**,把每個「場景數上限」都找齊 bump;可能還有:選單分頁、存檔 slot 陣列、Function1/2 迴圈邊界等。漏一個 → 越界崩潰。
2. **戰術選單 UI 容量** **[推定]**:目前 4 欄 × 10 列 = 40 格剛好塞滿一頁;要 >40 關,選單無捲動/分頁機制,超出的關可能只能走 campaign(戰術選單看不到)或需改 UI 佈局(較難)。
3. **Table B / pointer table 空間**:搬到 free `.data` 的做法可放大(做更大的表),但要找足夠連續零區;字串也要放進零區。
4. **campaign 起點與戰役槽**:AG 有多條戰役(北非/東線…);改哪條、起點在哪,對照 [campaign-routes-ag.md](campaign-routes-ag.md) 的既有鏈。
5. **聲望與平衡設計**:dvps/mvps/lspr 是設計值;大改要通盤設計,別只抄。
6. **每關都要實機驗**:載入不崩 + 地圖/單位合理;campaign 轉場靠機制驗證(第 1、5 節)。

## 5. 驗證的現實限制 [已證]

- **逐關玩通不可行**:從戰役起點 GUI 玩到中段某關要打十幾場、每場多回合,無法自動化到可靠。
- **存檔不宜盲改跳關**:AG 存檔 `GEN_TEMP.HIS` 含疑似 checksum(8-byte),盲改跳關風險高。
- **替代法(Kursk 用的)**:①戰術選單直接載入該關驗證 SCN 本身 ②反組譯確認 getter 解析得到新名 ③parse 確認 TDB 鏈 —— 三塊獨立驗證 + 「走的是所有既有關共用的同一轉場機制」,殘餘風險低。改造時把「已實機 / 僅機制驗證」誠實標註。

## 6. 踩雷 gotchas

- **`pkill -f "AG.EXE"` 會自殺**:`-f` 比對整條命令列,會匹配到你自己的清理指令 → 連自己一起殺。用 `pkill -x AG.EXE`(精確比對執行檔名)。
- **抓錯 EXE**:`BJensen_PacGen_NoCD.exe`(~13KB)是 NoCD 載入器、無字串/無引擎邏輯;真正引擎是 `AG.EXE` / `PACGEN.EXE`(~1–2MB)。grep 不到字串多半是查錯檔或大小寫。
- **hardlink**:兩個 AG 變體的 `AG.EXE`、`DATA/SCENARIO.TDB` 是共用 inode 的 hardlink(因兩版 byte 相同)。in-place 改會同步兩版——符合「兩版相同」需求;但若要讓某版獨立,先 `cp --remove-destination` 斷開。`GAME###.SCN` 為獨立檔。
- **崩潰特徵**:未接線就載入越界 slot → `page fault read 000000XX at <EIP>`,XX 常等於舊上限(39=0x27)。看到就知道是「某個場景數上限沒 bump」。
- **位元組序**:跨作 SCN 檔頭 magic 後有位元組序差異,但 Kursk 實測不影響 AG 載入;仍建議每關實機看。

## 7. 現成工具與資源 [未全面探索]

- **open-general**(GitHub,JS 重實作 5D 引擎):含 SCN/map/campaign 格式,可作格式規格來源、或寫 parser/emitter 的依據。
- **Luis Guzman 5-Star 通用編輯器**、**peachmountain「5 Star General」**、**Slitherine/Matrix** 論壇:能讀寫 SCN/campaign/map/equipment,適合原生建關或大改。
- 本 repo:選單表分析 [`ag-scenario-menu.md`](../../skills/panzer-general-cht/references/ag-scenario-menu.md)、Kursk 實作 [`kursk-mod-ag.md`](kursk-mod-ag.md)、三作分支 [`campaign-routes-*.md`](campaign-routes-ag.md)。

## 8. 一句話總結

Kursk 一役證明了「本機能測 AG + PG↔AG SCN 可 raw 移植 + Table B 可擴 + TDB 可任意接線」四件事;要大改整個戰役,主要新工作是**把所有『場景數=39』的硬編上限找齊 bump**、**戰術選單 UI 容量**、以及**戰役線的整體設計與逐關實機驗證**。
