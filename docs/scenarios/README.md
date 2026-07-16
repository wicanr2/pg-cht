# 三作劇本歷史索引

SSI 5D General 系列三作(裝甲元帥 1994 / 盟軍將軍 1995 / 太平洋元帥 1997)所有劇本的**歷史背景中文簡介**。

## 讀者路徑

想快速看某作全部劇本 → 讀 MD:

- **[裝甲元帥 pg.md](pg.md)** — 38 個劇本,按 開戰 / 東線 / 西線 / 架空 分節
- **[盟軍將軍 ag.md](ag.md)** — 39 個劇本,按 北非 / 南歐 / 西歐 / 東線 分節
- **[太平洋元帥 pacgen.md](pacgen.md)** — 33 個劇本,按 開戰 / 南方作戰 / 反攻 / 教學 / 架空 分節

想看**戰役分支路線**(每張地圖大勝 / 小勝 / 落敗各進哪個戰場、獲得多少聲望)→ 讀:

- **[裝甲元帥 campaign-routes-pg.md](campaign-routes-pg.md)** — 38 劇本,抽自 `SCENARIO.TDB`
- **[盟軍元帥 campaign-routes-ag.md](campaign-routes-ag.md)** — 39 劇本,抽自 `SCENARIO.TDB`(分支最完整)
- **[盟軍元帥 Kursk mod kursk-mod-ag.md](kursk-mod-ag.md)** — issue #4:AG 蘇軍路線加入第 40 個劇本 Kursk 庫斯克(哈爾科夫'43→庫斯克→第聶伯河),含素材相容性、AG.EXE Table B 擴充、TDB 接線與驗證
- **[太平洋元帥 campaign-routes-pacgen.md](campaign-routes-pacgen.md)** — 二進位 `CAMPAIGN.BIN` 解碼;分支 + 聲望 + **節點→劇本名對照全解**(日方 / 盟方兩條戰役各 13 關,經 PACGEN.EXE 劇本檔名陣列 + DEBUG.TXT 玩局紀錄交叉驗證)

想做程式處理(表格 / 過濾 / 統計)→ 讀 TSV:

- [pg-scenarios.tsv](pg-scenarios.tsv) / [ag-scenarios.tsv](ag-scenarios.tsv) / [pacgen-scenarios.tsv](pacgen-scenarios.tsv)
- 欄位: `scen year zh_name era brief_zh`

## 內容原則

- **原創繁中歷史敘述**,基於公共領域二戰史實(維基百科、正式軍史著作)寫成
- **不直譯 SSI 版權簡報**,是我方的原創史實整理
- 譯名遵循台灣軍事史學界慣用(參見 [`pacgen/docs/05-中文化依據.md`](../../pacgen/docs/05-中文化依據.md)):
  - 地名:阿拉曼、瓜達康納爾、雷伊泰灣(不用大陸簡譯)
  - 戰役:巴巴羅薩、大君主、火炬(從英/俄原名音譯)
  - 指揮官:隆美爾、朱可夫、蒙哥馬利、山本五十六(通用譯)

## 兩份 pipeline

- **TSV → MD** 由 [`tools/scenarios_to_md.py`](../../tools/scenarios_to_md.py) 產出,按 era 欄自動分節
- 想改 era 分類就編 TSV 的 `era` 欄,再重跑 script

## 待補

- 每個劇本的**勝負條件、關鍵單位、常見戰術**(pg-cht / ag-cht 內部已有部分,尚未彙整)
- ~~劇本樹狀圖(哪個劇本贏了進哪個)~~ → 已補:見上方 `campaign-routes-*.md`(PG/AG/PacGen 三作皆完成;PacGen 節點→劇本名已由 PACGEN.EXE 檔名陣列 + DEBUG.TXT 交叉驗證解出)
- 系列跨作連動(PG 1945 未打 → AG 1945;某些場景重疊)
