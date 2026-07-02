# Pacific General CHT — Domain Glossary

太平洋元帥 (Pacific General, SSI/Mindscape 1997) 繁中化專案的用詞與檔案結構收斂。

## 遊戲身分

- 英文名：Pacific General
- 中文名：太平洋元帥（沿 PG=裝甲元帥、AG=盟軍將軍 的譯名規範）
- 引擎：Win32 GDI + WinG（PACGEN.EXE），與 Panzer/Allied General 同源 5D General 系列末代
- 版本：v1.1（含 v1.1 patch + BJensen no-CD）

## 檔案結構（原始）

| 路徑 | 內容 | 譯 |
|---|---|---|
| `PACGEN.EXE` | 主程式（PE32，含 UI 字串表） | 是（binary patch） |
| `data/PACEQUIP.EQP` + `.TXT` | 裝備資料 + 名稱清單（163+） | 選項（OrigEQP 保留原文） |
| `data/TXT.PFP` | 打包的字表（classes/terrain/nations/…） | 是 |
| `data/CAMPAIGN.BIN` | 戰役結構 | 需分析 |
| `scen/*.TIT` × 33 | 劇本標題（純文字，短） | 是 |
| `scen/*.DES` × 33 | 劇本簡報（純文字，1-3 段） | 是 |
| `scen/*.SCN` × 33 | 二進位劇本 | 內含名稱要看 |
| `scen/*.TST` × 33 | 用途待查（可能是提示） | 待查 |
| `Maps/*.MAP` × 88 | 地圖二進位（可能含地名） | 待查 |
| `bnk/` `stream/` `SMACK/` | 音樂/語音/CG | 否 |

## 譯名規範

- 遵循 PG-cht / AG-cht 建立的譯名（單位名、地形、國別）
- 太平洋戰場專有名詞優先用中文戰史慣用譯（例：中途島、瓜達康納爾、雷伊泰灣）
- 國家：Japan=日本 / America=美國 / Australia=澳洲 / Britain=英國 / China=中國 / Philippines=菲律賓
- 兵種類別：Infantry=步兵、Cavalry=騎兵、Fighter=戰鬥機、Bomber=轟炸機、Naval=艦艇（沿 PG/AG）

## 標記

- `[需查]` = 尚未在原始碼/資料檔中確認位置的字串
- `[原文]` = 決定保留英文（例如裝備型號 F4F Wildcat）
- `[譯待定]` = 譯法尚未收斂，等 review

## Flagged ambiguities

- `PACEQUIP.TXT` 有大量 `I'm dead` — 疑為 placeholder，非玩家可見。**保留原文**。
- Nations 表要看是繁中還是原文——太平洋戰場「大日本帝國」vs「日本」用法要統一。
