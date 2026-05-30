# PG 資料檔格式手冊

## BDB*.BRF — 任務簡報

**位置**:`DATA2\BDB0001.BRF` ~ `BDB0177.BRF`(177 個檔案)

**格式**:
```
offset  size  description
0x000   4     paragraph count (uint32 LE)
0x004   200   paragraph[0] (null-padded ASCII / Big5)
0x0CC   200   paragraph[1]
0x194   200   paragraph[2]
...
```

每個段落最多 199 chars + 1 NUL,可儲存約 99 個 Big5 字。

**參考翻譯**:全部 177 檔案、413 段落已翻譯(共 39,644 英文 chars)。備份在 `DATA2\backup_orig\`。

**注意**:3 個檔案(BDB0158、BDB0159、BDB0176)原本只有一個空格,翻譯時填 0 即可。

**翻譯範例**:
```
BDB0001.BRF paragraph 0:
EN: Your first mission in operation Fall Weiss, the conquest of Poland, is to capture the key cities of Kutno and Lodz by September 10th.
CN: 您在「白色行動」中的首次任務 — 征服波蘭 — 必須在 9 月 10 日前佔領庫特諾與羅茲兩座關鍵城市。
```

---

## MAPNAMES.STR — 地形與地名資料庫

**位置**:`DATA\MAPNAMES.STR`(31,402 bytes)

**格式**:
```
offset  size  description
0x000   2     entry count (uint16 LE) = 1570
0x002   20    entry[0]   ("Clear")
0x016   20    entry[1]   ("Coast")
...
```

每 entry 為 20 bytes,可裝 19 個 ASCII char 或 9 個 Big5 字(+NUL)。

**索引語義**:
| Index | 內容 |
|-------|------|
| 0-13 | 地形類型(Clear/Coast/Ocean/Port/River/Mountain/Airfield/Swamp/City/Rough/Forest/Desert/Fortification/Bocage) |
| 14-1569 | 城市/地名(按戰役分組,有 `mapnames` 等分隔符) |

**已翻譯**:
- entries 0-13:全部地形 → 平原/海岸/海洋/港口/河流/山地/機場/沼澤/城市/崎嶇/森林/沙漠/防禦工事/灌木林
- entries 14+:314 個著名地名(首都、大城、戰場、D-Day 海灘、主要河川)

**安全性**:Index-based 存取,exe 內 0 個 hardcoded 字串比對。可自由翻譯。

**保留項目**(切勿翻譯):
- entries 25 = `d`(單字元)、139 = `f`、1208 = `j` 等可能是檔案格式分隔符
- entries 1231 = `???`、1251 = `??` 等

---

## TACMAP.TGF — 戰術地圖標籤

**位置**:`DATA\TACMAP.TGF`(1,348 bytes)

**格式**:9 個標籤 from offset `0x0283` with stride `0x14`(20 bytes)

**已翻譯**:
| Offset | EN | CN |
|--------|-----|-----|
| 0x0283 | name | 名稱 |
| 0x0297 | move column | 移動類型 |
| 0x02AB | road | 道路 |
| 0x02BF | river | 河流 |
| 0x02D3 | nation | 國家 |
| 0x02E7 | owner | 所屬 |
| 0x02FB | airport/port | 機場/港口 |
| 0x030F | entrench | 構工 |
| 0x0323 | initiative | 主動 |

---

## PANZEQUP.EQP — 裝備資料庫

**位置**:`DATA\PANZEQUP.EQP`(21,902 bytes)

**格式**:
```
offset  size  description
0x000   2     entry count (uint16 LE) = 438
0x002   50    entry[0]  (name 20 bytes + stats 30 bytes)
0x034   50    entry[1]
...
```

每 entry 前 20 bytes 為名稱(ASCII / Big5),後 30 bytes 為遊戲屬性(攻擊力/裝甲/移動力 等二進位數值)。

**已翻譯**:163 / 438 條

**★icon/圖號欄位 = stats[22](記錄內 offset 42 = name20+22),file offset = `2 + entry*50 + 42`★(2026-05-30 反推確認)**:
- 外型相近的單位**共用同號**(PzIVG 與 PzIVF2 同號、JagdPz IV/48 與 /70 同號 → 可用「同號=同 sprite」驗證此欄就是 icon)。
- **PG 與 AG 共用同一套 sprite bank**:438 筆裡 437 筆此 byte 與 PG-cht 逐 byte 相同 → 改 AG icon 時可拿 **PG 同 index 那格的值當正解**。
- 範例修正:AG「四號自走砲」(entry 66,即 PG StuG IV) icon = `0x4D`(錯,指到別的圖,玩家看到錯外型)→ 改 `0x2D`(PG 同格 StuG IV 的正確 sprite)。全 438 筆中**只有這一筆**此欄與 PG 不同 → 異常即 bug。
- 其餘有差的 stats byte(stats[1/2/5/12/21])是 AG 自己的數值平衡,**不要動**。

**翻譯策略**:
- **保留**:歷史型號代碼(BF109e/PzIVH/T-34/85/Sherman 變體 等)— 玩家熟悉度高
- **翻譯**:通用詞、著名命名單位、ship types、國別前綴 + 兵種詞

範例:
| EN | CN |
|----|-----|
| Tiger I | 虎式 I |
| Panther D | 豹式 D |
| JagdPanther | 獵豹 |
| Nashorn | 犀牛 |
| Wespe | 黃蜂 |
| Katyusha BM13 | 喀秋莎 BM13 |
| Volkssturm | 國民突擊隊 |
| GB Inf 39 | 英步兵 39 |
| US Para 43 | 美傘兵 43 |
| ST Cavalry | 蘇騎兵 |

---

## SCENARIO.TDB / ARROW.TDB / FLAG.TDB / PNTINFO.TDB — **不可翻譯**

ASCII 文字資料庫,以戰役名稱(`Anvil`、`Anzio`、`Barbarossa`、`Berlin`、`Kursk` 等)作為**主鍵**。翻譯這些檔案會導致:
- 戰役樹分支邏輯失敗
- 圖像資產 lookup 失敗(箭頭、旗幟、地圖)
- 進入戰役時拋 `hException`

**範例(SCENARIO.TDB 結構)**:
```
.0001 0.00000038.
.Anvil                    .anziow  .Ardennes                 .Market-Garden  ...
.Anzio                    .berlin  .????                     .D-Day          ...
```

格式:`.scenario_name(20-byte field).short_id.next_on_loss.next_on_draw.next_on_win.next_on_major_win.scores.`

---

## SCENSTAT.BIN

**位置**:`DATA\SCENSTAT.BIN`(7,000 bytes)

含戰役名稱(全大寫 POLAND/WARSAW/NORTH AFRICA 等),用於統計/存檔比對。**風險高**,目前未翻譯。

---

## .SCN 戰役檔(SCENARIO\GAME001.SCN ~ GAME038.SCN)

**內容**:純二進位遊戲資料(單位位置、勝利條件、地圖 ID),僅含內部 token 與檔案路徑(`..\dat\map01.stm` 等)。**無玩家可讀文字**,**不翻譯**。

---

## COMBATA.DAT / ART.DAT / *.MDT / SOUNDS.DAT 等大型 archive

二進位資源包(影像 RLE、調色盤、音效)。**無內嵌簡報文字**。

---

## DATA 資料夾編碼相關檔案

- `MPENCODE.MDT`(501KB)、`SMENCODE.MDT`(41KB):編碼/壓縮資料,非文字
- `MAPCONV.STG`(499 bytes):只含一個內部路徑字串,不翻譯
