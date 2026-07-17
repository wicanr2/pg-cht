# pg2 — 《裝甲元帥2》(Panzer General II, SSI 1997)繁中化子專案

5D General 家族的**第四款**(繼 PG1《裝甲元帥》、AG《盟軍元帥》、PacGen《太平洋元帥》)。目標:繁中化並在 **Linux(AppImage)+ 現代 Windows** 跑。

本目錄目前為**研究 + 規劃 + RE 攻堅(兩閘門已 PoC 綠)**,尚未進實作建置。

**實作決策(2026-07-17)**:目標 exe = `PANZER2.EXE`(2D)、寄生**法語槽 + 開機直接進中文**(單 byte patch `0xa32a0` `09→0C`,wine PoC 已證)、字型走 **route C GO**(drawGlyph `0x41b033`、字高 `[font+8]`、主 hook `0x43e699`)、地名全譯、指揮官名上網查證。詳 [中文化規劃.md](中文化規劃.md) §7。

## 一句話結論

PG2 是**全新 VC++/DirectDraw 引擎**(與 PG1/AG 的 Borland Pascal 5D 引擎**不同源**),但畫面內文字用的**自訂點陣字與 PacGen 同族**。文字分三塊:純文字資料檔(直接改)、GDI 對話框(換字型)、DirectDraw 點陣字(需 CJK 字庫 + 2-byte hook,沿用 PacGen route C)。`PANZER2.EXE` 已實測在 wine 11 下**可跑到主選單**。

## 檔案

- **[中文化規劃.md](中文化規劃.md)** —— 完整技術盤點、雙管線文字機制實測、字型 / 編碼 / 解析度方案、wine 可跑性實測、里程碑 / 風險 / 參考。全篇標 `[已實測]`/`[推定]`/`[未探索]`。
- `evidence/` —— wine 實測截圖證據:
  - `wine-titlescreen-640x480x8.png` —— 原生 640×480×8 下抵達 **PANZER GENERAL II 標題畫面**(顏色錯亂為 8-bit 調色盤擷取假影,非故障)
  - `wine-ddraw-init-failed.png` —— 桌面尺寸不符時的「DirectDraw Init FAILED」全螢幕切模式障礙

## 現況(2026-07)

| 核心問題 | 結論 |
|---|---|
| 文字怎麼畫 | 雙管線:GDI 對話框(23 DIALOG)+ DirectDraw 點陣字(FONTPG/FRA/GRM,fra/grm = PacGen TFONT 同族)[已實測] |
| 字串在哪 | GUI97/MISC/EQUIP97/NAMES/SCENARIO*.TXT(純文字)+ EXE `.rsrc` DIALOG + ENGLISH.DLL STRINGTABLE [已實測] |
| 編碼 | 資料檔 8-bit clean(法/德版證明容忍高位元組);管線 B 用 dense 2-byte 私有編碼、管線 A 用 Big5 [已實測支撐] |
| 解析度 | 640×480 8bpp 256 色;8×8 點陣塞不下中文 → route C 拉字高至 16 [已實測] |
| 能不能跑 | wine 11 下抵達主選單 ✅;障礙 = 全螢幕切模式 + 256 色調色盤(皆本 repo 既有解法可借)[已實測] |

## 邊界

本 repo 不含遊戲本體(版權所有)、已配置 WINEPREFIX、最終 AppImage / SFX,只放可重做的腳本、構建材料、技術文件、截圖。
