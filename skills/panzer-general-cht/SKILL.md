---
name: panzer-general-cht
description: 接續或擴充 SSI Panzer General / Allied General Win95 系列繁體中文化工作的領域知識。當使用者提到 Panzer General、PG-cht.exe、Allied General、AG.EXE、裝甲元帥、盟軍將軍、PG/AG 中文化、修改 BDB 簡報/PANZEQUP 裝備/MAPNAMES 地形或城市名/TACMAP 標籤/SCENARIO.TDB 戰役樹/.SCN 戰役檔,或要新增/還原/修正任何資產翻譯時觸發。也適用於同類 PE 二進位 hex patching 任務 — 特別是當字串同時作為 UI 顯示與 strcmp lookup key 必須拆分顯示路徑與比對路徑的情況(指標重導向 + .text caller bisection 技術)。
---

# Panzer General / Allied General 中文化專案知識

接續 2026 年 5 月完成的 SSI 戰略遊戲系列繁中化工作。**先讀完此 SKILL.md 確認專案現況**,再決定下一步;細節文件在 `references/`。

## 支援的遊戲

| 遊戲 | 目錄 | 主執行檔 |
|------|------|---------|
| Panzer General Win95 | `D:\03_game_tmp\PGWin95_reduced_v1.2\PG_v1.2\` | `PG-cht.exe` (1,984,512 bytes) |
| Allied General Lite v1.1 | `D:\03_game_tmp\AlliedGeneralLite_v1.1\AlliedGeneral_v1.1\` | `AG.EXE` (2,167,611 bytes) |

兩款遊戲同引擎,DATA 結構大半相同(`MAPNAMES.STR`、`TACMAP.TGF` 兩遊戲位元組完全相同 — 可直接共用譯文);`PANZEQUP.EQP` 內容不同;`AG.EXE` 沒有 `DATA2\BDB*.BRF`(AG 無獨立簡報檔,戰役描述存於 EXE 內 0x1BD0E8 起 + 長 briefing 在 .rsrc UTF-16LE)。

## AG.EXE 版本指紋(本 skill 所對應的具體 EXE 識別)

本 skill 的所有 hex offsets 都針對下述 EXE。換版本(同 SSI 出 NWC 出其他 v1.0 patch / Lite v1.2 / GOG re-release 等)時要重做 caller bisection。

| 識別欄位 | 值 |
|---|---|
| 檔案大小 | 2,167,611 bytes |
| MD5 (AG.EXE.bak) | `45C7E04FBDF71113FD8E8B2B746980B9`(原 SSI 英文 — 對照基準) |
| PE COFF timestamp | `0x3134E395` = 1996-02-29 07:21:57 UTC |
| Linker version | Microsoft Visual C++ 2.55(VC++ 4.0 SP2 era) |
| VS_VERSION_INFO resource | **無**(SSI 沒寫 PE 標準 version 資源,.NET `Get-Item .VersionInfo` 全空) |
| README.TXT 第一行 | `Allied General V1.0 Read Me File 12/3/95 (c) 1995, Strategic Simulations, Inc. A Mindscape Company` |
| Lite 重新打包標記 | 目錄名 `AlliedGeneralLite_v1.1`(community / fan re-pack,EXE 本體與 SSI 原版相同) |
| .text section | file `0x400-0x19C800` (RVA 0x1000) |
| .rdata | file `0x19C800-0x1B9200` |
| .data | file `0x1B9200-0x1D1400` (VA = fo + 0x42EE00) |
| .idata | file `0x1D1400-0x1D2800` |
| **.rsrc** | file `0x1D2800-0x1F9C00` (160 KB,**含 39 段長 briefing UTF-16LE**) |
| .reloc | file `0x1F9C00-0x210200` |

**驗證對應同 EXE**:`Get-FileHash -Algorithm MD5 AG.EXE` 比對。若 hash 不同但 size 與 PE timestamp 都一致 → 多半就是同版有後續 patch,部分 offset 可能仍對得上;若 size 不同 → 視為不同版本,本 skill offsets 不適用。

## 專案概況

| 項目 | 路徑 |
|------|------|
| 遊戲根目錄 | `D:\03_game_tmp\PGWin95_reduced_v1.2\PG_v1.2\` |
| 主要可執行檔(中文版) | `PG-cht.exe` (1,984,512 bytes) |
| 原始英文版 | `PG.exe` (2,167,298 bytes,大小不同) |
| 原始翻譯者 | Chun-Yu Wang (wicanr2@gmail.com) **— 即本 skill 使用者本人** |

**重要備份位置**(改動前務必確認備份存在):

PG:
- `PG-cht.exe.bak`(根目錄,也在 `backup\` 鏡像一份)
- `DATA2\backup_orig\BDB*.BRF`(所有 177 個簡報原始檔)
- `DATA\MAPNAMES.STR.bak` / `TACMAP.TGF.bak` / `PANZEQUP.EQP.bak`

AG (同目錄結構):
- `AG.EXE.bak`
- `DATA\MAPNAMES.STR.bak` / `TACMAP.TGF.bak` / `PANZEQUP.EQP.bak` / `SCENARIO.TDB.bak` / `MAPCONV.STG.bak` / `SCENSTAT.BIN.bak`

## 已完成翻譯總覽 — PG

| 資源 | 數量 | 位置/方式 |
|------|------|---------|
| UI 字串 | 230 條 | PG-cht.exe 內原地翻譯(slot 內) |
| 戰役名稱(顯示) | 38 個 | **指標重導向**(見下方技術說明) |
| 地形類型 | 14 條 | MAPNAMES.STR entries 0-13 |
| 城市/地名 | 314 個 | MAPNAMES.STR entries 14+(著名地名) |
| 戰術地圖標籤 | 9 條 | TACMAP.TGF |
| 任務簡報 | 413 段 / 177 檔 | DATA2\BDB*.BRF |
| 裝備名稱 | 163 條 | PANZEQUP.EQP(保留型號代碼如 BF109e/T-34) |
| 戰略地圖提示 | 2 段 | PG-cht.exe 內 |

## 已完成翻譯總覽 — AG (2026-05-16 完成)

AG Lite v1.1 已含部分中文化(PANZEQUP 95% 中文),本次補完 UI 與資料檔:

| 資源 | 數量 | 位置/方式 |
|------|------|---------|
| UI 字串 | **499 條** | AG.EXE 內原地翻譯(179 PG 譯文 + 310 AG 專屬 phase 2 + 6 phase 3 + 4 extra) |
| 主選單按鈕 | 6 條 | Open/Scenarios/E-Mail/Start/Campaigns/Scenarios → 開啟/戰術/郵件/開始/戰役列表/戰術列表 |
| 地形類型/城市名 | 14+314 條 | MAPNAMES.STR(直接複製 PG 翻譯版,兩遊戲位元組完全相同) |
| 戰術地圖標籤 | 9 條 | TACMAP.TGF(直接複製 PG 版) |
| 裝備名稱 | **100%** | PANZEQUP.EQP(Lite v1.1 原 425 條 + 補 RESERVED/FPO Bren Ca + 11 條 BF109/110/ME/HE/DO 系列) |
| 戰役描述 | 33 段 | AG.EXE 內(0x1BD10C 起,220-byte slots) |
| 字體 | 26 處 Arial→Tahoma | 與 PG 一致(避免 Big5 字體偏小問題) |
| 任務簡報 | N/A | AG 無獨立簡報檔(資料已內嵌於 EXE) |

**AG 累計變動**:AG.EXE 13,321 bytes、PANZEQUP.EQP 105 bytes、MAPNAMES.STR 2,639 bytes。

**AG 戰役選單 39 條地名(2026-05-29 完成)**:用 PG 式 caller-level 拆分。新 ptr table B' @ `0x1BFE4C`、新 Chinese getter @ `0xC5C0` (VA `0x40D1C0`),只 3 個 display callers (`0x57C39`/`0x5A27E`/`0x5A43C`) redirect 走 Chinese getter,其餘 7 個 callers 與 Function 2 本身維持英文 — menu 中文 + 全戰役可進入(實測 Germany 通過)。完整 patch 細節與失敗嘗試教訓見 `references/ag-scenario-menu.md` 章節「2026-05-29 完成記錄」。

## PG-cht.exe 本次修正 (2026-05-16)

- 修正原譯者 Chun-Yu Wang 的 Tohama → Tahoma 拼字錯誤(7 處 Arial 改 Tahoma 中,6 處誤拼為 Tohama,1 處正確)— 6 處 typo 已修正

## 關鍵技術:指標重導向(Pointer Redirection)

**問題**:某些字串同時用於 UI 顯示 **和** .text 程式碼內的 strcmp lookup key。直接翻成 Big5 會讓 strcmp 失敗,導致進入戰役時拋 `hException`(`未知錯誤 exTrue`)。

**典型受害字串**:戰役名稱陣列 `0x1BAC48-0x1BAEEC`(38 條:1943 East、Berlin (East)、North Africa、Barbarossa、Sealion Plus 等)— 從 .text 有 109 個指標引用。

**解法步驟**(以戰役名稱為例):
1. **保留原英文字串**不動於 `0x1BAC48-0x1BAEEC`(供 .text 內嵌 `MOV EAX, offset_string` 比對使用)
2. **在 .data 安全區寫 Big5 副本** — 已用 `0x1C8C69-0x1C8D88`(363 bytes 0 靜態引用區)
3. **複製英文指標表副本** — 已置於 `0x1BA7B8`(152 bytes,Table B 38 個 entry 的英文指標複本)
4. **修改原指標表 Table B** `0x1BAA28` → 指向 Big5 副本
5. **在 .text padding 寫新 getter 函式** — 已置於 `0x32F4`(27 bytes,讀 0x1BA7B8 英文副本)
6. **bisection 找到「顯示用 caller」**(只 1 個)讓它走原 Chinese getter,其他 9 個 lookup callers 改 call 新英文 getter

**目前 10 個 caller 的最終配置**(見 `references/exe-patches.md`):
- `0xF0D27` → 原 Chinese getter(顯示路徑)
- `0x108AC` 等 9 個 → 新英文 getter(lookup 路徑)

## 三個我必須記住的「禁區」

1. **PG `0x1BAC48-0x1BAEEC`、AG SCENARIO.TDB 內的戰役/地點名**(Sidi Barrani / El Alamein / Anzio / Berlin 等):**絕不**原地翻譯。同時用於 strcmp lookup,改動會破壞 .text 引用與 SCN/STM 檔名對應。
2. **SCENARIO.TDB / ARROW.TDB / FLAG.TDB / PNTINFO.TDB**:**絕不**翻譯。內含戰役名作為 ASCII key,改動會破壞資產 lookup。
3. **PE .text section** `0x400-0x19A1FF`:預設不動。只有指標重導向解法中經授權的 operand patch 與 padding 區內的新函式才可改。
4. **SCN 內 `..\dat\*.stm`、`..\dat\mapconv.stg` 等路徑字串**:絕不翻譯,是檔案路徑。
5. **AG.EXE 內 `MpEncode.mdt` / `SmEncode.mdt` / `Panic.sav` / `TargCur.cur`**:檔名,絕不翻譯。

## 何時讀什麼

| 場景 | 讀這個 |
|------|--------|
| 需要 PE 結構、VA/file offset 轉換、安全 padding 區清單、現有 patches 完整列表 | `references/exe-patches.md` |
| 修改 BDB/PANZEQUP/MAPNAMES/TACMAP/SCENARIO.TDB 等資料檔 | `references/file-formats.md` |
| 找符合風格的翻譯詞彙(國名/兵種/動作) | `references/translation-conventions.md` |
| **AG 戰役選單中文化(指標重導向待做)** | `references/ag-scenario-menu.md` |
| 套用 patch 的 PowerShell 樣板程式 | `scripts/` |

## 操作流程

### 新增翻譯前

1. 確認改的字串**不在禁區清單**(見上)
2. 用 Grep 搜尋 PG-cht.exe.bak 看該字串在 .text 是否有 hardcoded 引用:
   ```powershell
   # 搜尋 VA 0x5EXXXX 在 .text 是否被引用
   ```
3. 若**有** .text hardcoded 引用 → 必須用指標重導向手法(見上)
4. 若**無** → 可原地翻譯(index-based 存取,安全)

### 套用翻譯後

1. 檢查檔案大小與原備份一致
2. Big5 解碼讀回確認字串完整
3. 請使用者實際進遊戲驗證

### 還原步驟

```powershell
# 還原 exe
Copy-Item "D:\03_game_tmp\PGWin95_reduced_v1.2\PG_v1.2\PG-cht.exe.bak" "D:\03_game_tmp\PGWin95_reduced_v1.2\PG_v1.2\PG-cht.exe" -Force
# 還原所有 BDB
Get-ChildItem "D:\03_game_tmp\PGWin95_reduced_v1.2\PG_v1.2\DATA2\backup_orig\BDB*.BRF" | ForEach-Object {
  Copy-Item $_.FullName "D:\03_game_tmp\PGWin95_reduced_v1.2\PG_v1.2\DATA2\$($_.Name)" -Force
}
# 還原 MAPNAMES / TACMAP / PANZEQUP
$d = "D:\03_game_tmp\PGWin95_reduced_v1.2\PG_v1.2\DATA"
Copy-Item "$d\MAPNAMES.STR.bak" "$d\MAPNAMES.STR" -Force
Copy-Item "$d\TACMAP.TGF.bak" "$d\TACMAP.TGF" -Force
Copy-Item "$d\PANZEQUP.EQP.bak" "$d\PANZEQUP.EQP" -Force
```

## 常見潛在 expansion 方向

- **更多城市翻譯**:MAPNAMES.STR 還有 ~1240 個未翻譯地名(冷門小鎮)。entries 14+ 都是 index-based 安全翻譯。
- **戰役起始點翻譯**:`0x1C6038` 的 5-entry 表(1939/1941 East/West/1943 East/West)用相同指標重導向手法
- **戰術 UI 標籤**:檢查 ART.DAT 內可能的字串資源
- **裝備細節**:目前保留型號代碼,如需強化,可改翻譯如 "Tiger I" → "虎式 I" 的形式(已有 163 條範本)

## 編碼注意事項

- 所有中文字串以 **Big5 (codepage 950)** 編碼,而非 UTF-8。`[System.Text.Encoding]::GetEncoding(950)` 是正確的編碼器。
- 翻譯字串的 byte 長度必須 ≤ slot 容量 − 1(留 NUL 終止子)
- 一個 Big5 字 = 2 bytes;ASCII 字 = 1 byte
- Big5 leading byte 範圍 0xA1-0xFE;trailing byte 0x40-0x7E 或 0xA1-0xFE
- 不會碰巧產生 `%` (0x25) 字元,所以 printf format string 安全

## 預期觸發場景

當使用者:
- 提到 Panzer General、PG、Allied General、AG、裝甲元帥、盟軍將軍、PG-cht.exe、AG.EXE
- 要修改 BDB 簡報、戰役名、裝備、城市、地形名稱
- 看到遊戲內顯示英文要求中文化
- 進戰役出現 `未知錯誤 exTrue` 或類似 exception
- 想做類似 PE 二進位 hex patching 而需要拆分「顯示」與「lookup」路徑時(本 skill 的指標重導向手法可廣泛適用)

## AG 專案速查 (2026-05-16)

AG.EXE PE 結構(與 PG 相同 ImageBase 0x400000,但 section 位移不同):
- `.text` file `0x400-0x19C800` (RVA 0x1000)
- `.rdata` file `0x19C800-0x1B9200` (RVA 0x1CB000)
- `.data` file `0x1B9200-0x1D1400` (RVA 0x1E8000)
- `.data` VA = file_offset + `0x42EE00`

AG 翻譯 workspace 暫存檔(可重用為下次 AG 工作的起點):
- `workspace_ag_ui_strings.txt` — 全部 544 條 AG.EXE UI 字串清單
- `workspace_pg_dict.txt` — PG 英文→Big5 字典(206 條)
- `workspace_ag_patches.txt` — phase 1 (179 條,從 PG 直接套用)
- `workspace_ag_patches2.txt` — phase 2 (454 條 AG 專屬翻譯)
- `workspace_ag_patches3.txt` — phase 3 (6 條清理)
- `workspace_ag_extras.txt` — 主選單按鈕 + extra UI(10 條)
- `workspace_ag_panzequp_residual.txt` — PANZEQUP 13 條補譯
- `workspace_ag_scenarios.txt` — 81 條戰役名(目前已 revert,留作下次重做指標重導向時參考)

## AG 戰役選單問題(2026-05-16 進行中)

**現況**:戰役選單顯示英文。直接翻譯會 exception。已驗證 bisection 結果:

| 表 | 位置 | 用途 | .text getter | 索引範圍 |
|---|---|---|---|---|
| Table A | `0x1C2800-0x1C29E8` (39 entries) | **未用(顯示+lookup 都不是)** | `0x956BB` ref @ `0x956E3` | 0-7(只用前 8) |
| Table B | `0x1C2A2C-0x1C2BB4` (39 entries) | **menu 顯示 AND lookup 來源** | `0x941E5` ref @ `0x94211` | 0-38(全部) |
| Table C | `0x1C2C54-0x1C2C77` (3 entries) | 戰役起點(N.Africa/W.Europe/E.Front) | unknown ref @ `0x94812` | 0-2 |

**Bisection 證據**:
- A=cht, B=eng, C=eng, TDB=eng → 顯示英文,無 exception → menu 不讀 A
- A=cht, B=cht → exception,顯示中文 → menu 讀 B
- A=eng, B=cht, TDB=eng → exception
- A=cht, B=cht, TDB=cht(全 Chinese)→ exception(TDB 中文化無法救)

**結論**:Table B 同時用於 menu 顯示 + 進入戰役時 strcmp lookup。需 PG 式指標重導向手法。

**SCENARIO.TDB 格式**(141 bytes/record × 39 records,header 18 bytes):
- 0x12: `.` separator
- 0x13-0x2B: NAME (25 bytes, ASCII 空格填充)
- 0x2C: `.` 0x2D-0x34: SCNFILE (8 bytes, e.g. "anziow  ")
- 0x35: `.` 0x36-0x4E: DWIN branch (25 bytes)
- 0x4F: `.` 0x50-0x68: MWIN branch (25 bytes)
- 0x69: `.` 0x6A-0x82: LOSS branch (25 bytes)
- 0x83-0x9C: 5×4-byte numbers (turns/delays)
- 0x9D-0x9E: CRLF
- Sentinel branches:DWIN/MWIN/LOSS/???? 絕不翻譯

**下次接續工作**:
1. 還原狀態:Tables A+B+C、SCENARIO.TDB 已 revert 回英文
2. 要 Chinese 顯示,需:
   - 找出 `0x941E5` getter 透過 thunk(0x964/0x21D0 區域 E9 跳板)的所有 caller
   - 每個 caller 是 display 還是 lookup,bisection 個別測試
   - 顯示用 caller → 改 call 新 Chinese getter(讀 Table A 或新 Big5 區)
   - lookup 用 caller → 維持 call 原 getter(讀 Table B 英文)
3. 詳見 `references/ag-scenario-menu.md`

## AG 字體設定發現

- 原 AG.EXE 用 `Arial` (26 處,slot 8 bytes)
- 原 PG.exe 也用 Arial,**Chun-Yu Wang 譯時改為 Tahoma**(7 處,其中 6 處誤拼為 Tohama)
- Big5 中文在 Tahoma 顯示為新細明體(系統替代),比直接用 細明體 更大更清楚
- AG 本次跟隨 PG 改法:`Arial` → `Tahoma` 26 處(slot 8 fit:6+NUL=7 bytes ✓)

## SCN 檔內 scenario 名

每個 GAME###.SCN 內含小寫 scenario name(例如 `'sidi barrani'` at 0x1EB,對應 SCENARIO.TDB 的 SCNFILE 短名)。這是 scenario internal key,可能參與 lookup。本次未動。
