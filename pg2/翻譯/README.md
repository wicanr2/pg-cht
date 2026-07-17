# 《裝甲元帥2》資料檔繁中翻譯

PG2 可翻譯純文字資料檔(UI / 地形 / 裝備 / 指揮官 / 劇本地名)的繁中翻譯源與套用工具。中文化採寄生**法語槽**,最終檔名為 `*.fra`;本目錄存**翻譯源(glossary)+ 可重生腳本**,不含遊戲資料本體(依 repo「不含遊戲本體」原則,master 檔由 glossary + 使用者原檔在本機重生)。

## 檔案

- **`glossary.tsv`** —— 翻譯源(唯一真相),2086 筆唯一字串,欄位 `檔類 / original / zh_tw / 來源備註`。改譯名就改這裡。
- **`apply_translations.py`** —— 讀原始 `Panzer2/*.TXT` + `glossary.tsv` → 產各檔繁中 master(UTF-8),保留結構 / 座標 / 行數 / CRLF+DOS EOF;SCENARIO 302 檔批次。
- **`extract_scenario.py`** —— 從 SCENARIO/*.TXT 抽唯一可譯字串(建 glossary 用)。
- **`build_size_report.py`** + **`size_report.tsv`** —— 估算 dense 2-byte 編碼後各檔大小 vs 上限。

## 涵蓋率(唯一字串 100% 已譯)

| 檔 | 原始行數 | 唯一字串 | 主要來源 |
|---|---|---|---|
| GUI97.TXT | 440 | 405 | 自譯(UI/選單/國名/軍語,對齊三部曲慣例) |
| MISC.TXT | 27 | 27 | 自譯(地形/戰鬥標籤) |
| EQUIP97.TXT | 586 | 388 | 對齊三部曲 93、自譯 268、待查 27 |
| NAMES.TXT | 400 | 400 | 沿用 [`../歷史百科/NAMES-姓名庫.tsv`](../歷史百科/NAMES-姓名庫.tsv)(行序 400/400 零誤差) |
| SCENARIO/*.TXT | 5137(53 檔) | 866 | 對齊百科 66、WebSearch 查證 94、自譯 352、待複核 341、船艦/番號照抄 13 |

## 譯名對齊來源

- **裝備**:`pacgen/docs/knowledge-base/equipment-crossgame-consistency.md` + `equipment-{panzer,allied}-general.md`(虎式/豹式/獵虎/虎王/喀秋莎等沿用三部曲統一名)。
- **地名/戰役**:[`../歷史百科/戰役.tsv`](../歷史百科/戰役.tsv)(色當/卡昂/庫斯克/澤洛高地…)。
- **軍語/國名**:三部曲既有慣例。

## 大小:無超限

57 檔全 OK。最大 EQUIP97 = 6562 bytes(上限 64KB)、NAMES 3021(32KB)、SCENARIO 最大 1621(各 32KB)。餘裕大。

## 待複核 / 潤稿項目(第一版已標註,不影響落地)

1. **SCENARIO 13 筆船艦/番號原文照抄**:`Scharnhorst`/`Tirpitz`(百科已有 沙恩霍斯特號/提爾必茲號)、Tribal 級驅逐艦(Nubian/Sikh/Somali/Zulu/Punjabi)、義艦、`41 Cdo`、`Recon/16` 等——是否改譯待定。
2. **EQUIP97 27 筆待查**:純口徑數字砲種依上下文推定,精確砲種建議對 `.EQP` 二進位驗證;`Coelion`/`MCG-5`/`Pz 633`/`Skoda` 型號來源不確定保留原文。
3. **SCENARIO 341 筆待複核**:東線/匈牙利冷僻村莊機械音譯,備註欄逐筆標可疑點(如 `Abostag`疑 Apostag)。
4. **術語統一**:StuG 家族「三號自走砲 / 三號突擊砲」混用待統一;雪曼/謝爾曼擇一。「炮→砲」已訂正 7 筆;GUI97「Air Defense」雙義已按行 override。

## 第二輪:戰役簡報散文([`briefings/`](briefings/))

第一輪只譯 53 個「地名清單」檔;第二輪補完 `SCENARIO/` 其餘 **249 個未譯散文檔**——45 個 `*I.TXT` / `DTR*` / `GE*` / `RU*` / `UK*` / `US*` 的戰役簡報與勝敗分支文字(落敗 / 小勝 / 大勝 / 輝煌勝利各分支)+ 各獨立劇本開場白 + 6 條戰役總入口。

- **軍事簡報語氣**:德軍「Herr General」→將軍閣下、「Herr Feldmarschall」→元帥閣下(隨劇情升遷)、蘇軍「Comrade」→同志、英美「Commander」→指揮官。
- **結構 byte-exact 保留**(CRLF/LF、DOS 0x1A EOF、行數、縮排),自動化結構 diff 對 249 檔 0 誤差。
- **249/249 完成**、471 行實質內容全譯;人名 / 地名對齊 [`../歷史百科/戰役.tsv`](../歷史百科/戰役.tsv) 與第一輪 glossary。
- 檔案:[`briefings/briefings_glossary.tsv`](briefings/briefings_glossary.tsv)(382 行原↔譯)、`charset_full.txt`(**合併完整字集 1,579 唯一漢字**,供 atlas 重建)、`size_report_briefings.tsv`(無超限,最大 393 bytes vs 32KB)、pipeline 腳本。
- 待複核:`Fedoroloka`(GE62I,近克林某地,暫音譯費多羅洛卡)、`Red Octobrists`(RU60L,蘇聯風味玩笑,暫譯紅色十月支隊)。

## 後續(建置階段)

最終 **dense 2-byte 編碼** + 輸出 `*.fra` 由字型/EXE 建置階段做(見 [`../中文化規劃.md`](../中文化規劃.md) §7):收集 glossary 全 zh 字集 → 建 CJK atlas + dense 映射 → 重編碼各 master → 輸出 `GUI97.fra` / `EQUIP97.fra` / `MISC.fra` / `NAMES.fra` / `SCENARIO/*.fra`。
