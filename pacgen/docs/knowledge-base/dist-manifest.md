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
| PG2 | — | 原始 | AppImage | `PanzerGeneral2-x86_64.AppImage` | 811M | `e4081bdbbd97ec5f6d296767571115bd` |
| PG2 | — | 原始 | Windows | `PanzerGeneral2-windows.zip` | 437M | `fc461dff5092eb5d77b7ec25d20668a2` |

> **PG2《裝甲元帥2》繁中版(2026-07-18,已完成)**:5D General 家族**第四款**,全新 VC++/DirectDraw 引擎(與 PG1/AG 不同源),非「三部曲」但同 repo。中文化走**英文(預設)槽注入中文**(開機即中文、無語言 patch)+ 自建 **2-byte CJK 引擎**(atlas 1,582 glyph 烤進 EXE `.cjk` 節、drawStringCore + word-wrap 兩繪字路徑 hook + 5 個 ctype classifier 截斷修正)。全部 UI / 地形 / 裝備 / 指揮官 / **302 個劇本地名 + 戰役簡報散文**已中文化。AppImage 沿用 **PacGen DirectDraw 配方**(gdi renderer + GrabFullscreen + `wineserver -k` + `explorer /desktop=PG2,640x480`),wine 實測全綠:主選單 / 戰役+劇本清單全中文 / 戰役簡報中文散文 / 可玩地圖 + 中文單位資訊。Windows zip 含 `dplayx.dll`(DirectX redist 原生版,230400 bytes,md5 `4c5a47e4…`,import 現代 Windows 皆可解)+ 6 個隨遊戲 DLL + `裝甲元帥2.cmd`(256COLOR 相容層)+ 使用說明。**真機 Windows 未驗**(僅 wine smoke + dplayx import 靜態確認);深度遊玩未跑。細節見 [`../../pg2/中文化規劃.md`](../../pg2/中文化規劃.md)。

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
