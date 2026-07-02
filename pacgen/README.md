# pacgen-cht — 太平洋元帥繁體中文化

*Pacific General (SSI/Mindscape, 1997) — 30 年後的中文化補完*

---

## 目錄

- [序](#序) — 這款遊戲為何 29 年沒有中文版
- [快速開始](#快速開始) — [Linux (wine)](#linuxwine-11) / [Windows 10/11](#windows-10--11) 兩路啟動
- [心得專欄](#心得專欄) — [`docs/`](docs/) 6 篇文章索引
- [技術資料](#技術資料) — 翻譯工具 + string dump + wine 啟動配方
- [進度](#進度) — v0.1-v0.6 CHT + AppImage 三層雷解 + A1 拉高畫布 (亂碼根因與正解)
- [相關](#相關) / [授權](#授權)

**深入閱讀路徑**:先看 [`docs/00-序.md`](docs/00-序.md) hero letter → 想直接玩跳 [`docs/01-wine-啟動配方.md`](docs/01-wine-啟動配方.md) / [`docs/02-modern-windows.md`](docs/02-modern-windows.md) → 想懂遊戲檔案結構讀 [`docs/03-遊戲檔案結構.md`](docs/03-遊戲檔案結構.md) / [`docs/04-裝備檔解析.md`](docs/04-裝備檔解析.md) → 想懂譯名為什麼這樣翻讀 [`docs/05-中文化依據.md`](docs/05-中文化依據.md)

---

## 序

那個沒被翻譯的太平洋。1997 年三大誌沒為它寫過專欄、1998 年 SSI 倒了、之後 29 年沒人做過中文化。這個 repo 是**遲到 29 年的回信**。

同時支援 Linux (AppImage / wine) 與 Windows 10 / 11。

**完整心得專欄從 [docs/00-序.md](docs/00-序.md) 開始讀**。

---

## 快速開始

### Linux（wine 11+）

```bash
export WINEPREFIX=~/.wine-pacgen
export WINEARCH=win32
export WINEDLLOVERRIDES="mscoree,mshtml="
cd "/path/to/Pacific General"
wine explorer /desktop=PACGEN,640x480 PACGEN.EXE
```

*為什麼要虛擬桌面 640×480、為什麼不用 DLL override、為什麼直接跑會搶主機解析度 —— 詳見 [01 wine 啟動配方](docs/01-wine-啟動配方.md)。*

### Windows 10 / 11

- 套用 `PACGEN_v11_Patch.EXE` 官方 patch
- 用 `BJensen_PacGen_NoCD.exe` 拿掉 CD 檢查
- `PACGEN.EXE` 右鍵 → 相容性 → Windows XP SP3 相容模式

詳細與疑難排解見 [02 modern Windows](docs/02-modern-windows.md)。

---

## 心得專欄

| # | 篇章 | 主題 |
|---|---|---|
| [00](docs/00-序.md) | 序 | 為什麼 1997 年沒中文版 |
| [01](docs/01-wine-啟動配方.md) | wine 啟動配方 | 三個坑：主機解析度被搶、藍屏 20 秒、1×1 window |
| [02](docs/02-modern-windows.md) | modern Windows | v1.1 patch + no-CD + 相容模式 + 字型 |
| [03](docs/03-遊戲檔案結構.md) | 檔案結構解剖 | data / scen / Maps / bnk / stream / SMACK |
| [04](docs/04-裝備檔解析.md) | 裝備檔解析 | 813 個實際單位、282 個 placeholder、EQP 二進位結構 |
| [05](docs/05-中文化依據.md) | 中文化依據 | 為什麼 Zero 不譯「零戰」、Wildcat 保留原文 |

---

## 技術資料

- `translations/pacgen_exe_strings.tsv` — PACGEN.EXE 全部 ASCII 字串 dump (3813 條)
- `translations/pacgen_ui_candidates.tsv` — filter 過的 UI 翻譯候選 (356 條，待人工複審)
- `tools/dump_pe_strings.py` — PE32 string table dumper（可重跑）
- `tools/filter_ui_strings.py` — CRT-runtime 噪音濾除器
- `docs/wine-launch.md` — wine 啟動一手筆記（含 CD-check 靜態分析）
- `CONTEXT.md` — 譯名與檔案結構收斂

## 進度

**v0.1 完成 (2026-07-02)** — AppImage + Windows zip 已可用。

- [x] Wine 啟動配方確認 (explorer /desktop=PACGEN,640x480)
- [x] EXE 字串 dump + 初步 filter (3813 條 → 356 UI 候選)
- [x] docs 專欄骨架 (00 序 / 01 wine / 02 windows / 03 檔案結構 / 04 裝備檔 / 05 中文化依據)
- [x] TXT.PFP unpack tooling (74 節 byte-perfect roundtrip)
- [x] 33 個劇本 TIT (歷史學界慣用譯) + DES (原創繁中史實敘述)
- [x] AppImage + Windows zip 打包(v0.1)

**AppImage 首次啟動 (v0.2 已解)**

實測 40 秒內完整跑到主選單。三層雷疊在一起,缺一個就掛:

1. Direct3D renderer=gdi (避 P8 palette 崩)
2. X11 Driver GrabFullscreen=Y (DDraw exclusive 抓 X 焦點)
3. **regedit 完立刻 `wineserver -k`** — 讓遊戲用新 registry snapshot 而非 wineboot 舊 session 的

完整解說見 [docs/01-wine-啟動配方.md](docs/01-wine-啟動配方.md) 「AppImage 首次啟動的三層雷」。

**v0.3 增量 (2026-07-02):TXT.PFP in-place patch + 全 CHT ship**

- `Select Axis Campaign` (0x5fdb, 20B) → 「選擇軸心戰役」+ 8 空格
- `Select Allied Campaign` (0x5ff1, 22B) → 「選擇盟軍戰役」+ 10 空格
- **byte-length preserving 策略成立**,PFPDATA.IDX 無需重寫
- **PFP patch + CHT TIT + CHT DES 三者同時 ship**(v0.2.1 的併用 crash 懸念已解:三者組合 fresh source hardlink 測試能穩定 boot,前兩輪誤診根因是我在 CHT build dir 累積的 patch/revert 髒狀態 + wine session 髒污)
- 詳見 [`docs/06-txt-pfp-inplace-patch.md`](docs/06-txt-pfp-inplace-patch.md) 第三輪徹底翻案

**v0.4 / v0.5 (2026-07-02):PFP in-place patch 擴充到 119 條 UI 字串**

自動 pipeline (`tools/build_pfp_patches.py` + `patch_pfp_v2.py`):掃 en/zh 對照,找 Big5 ≤ 原文 byte 長度的行就 patch。v0.4 92 條 + v0.5 補 `glossary_short.tsv` 22 條縮字別名 (月份一~臘、國別美/義、Air→空) 解掉 24 條 too-long → 共 **119 條**。涵蓋兵種 15、地形 13、國別 11、月份 12、主選單/按鈕 6、天氣、Battle Generator。

**v0.6:PACEQUIP 40 條裝備名 in-place patch** (步兵/騎兵/工兵/艦名/日文兵種,byte-preserving,`glossary_equip.tsv`)

**⚠ 亂碼根因 (v0.7 判定):遊戲用 8×8 點陣字型,上述 Big5 patch 在畫面顯示為亂碼**

v0.3-v0.6 的 Big5 patch **資料層寫進去了,但畫面上是亂碼**。根因:遊戲用自訂 `TFONT1.DAT` **8×8 bitmap font**、**零 GDI 繪字** (查 import 無 TextOut/CreateFont),wine 字型代換無效;8×8 格子物理上塞不下可讀中文。詳見 [`docs/08-tfont-re.md`](docs/08-tfont-re.md)。

**🎯 A1 拉高畫布 (rule 81):讓中文能 24×24 清晰顯示的正解**

逆向進度 (只列**純靜態 RE** 的可靠結果;涉及跑起來看畫面的結論一律待乾淨環境驗證):

- **靜態偵察 ✅ 可靠**:`TFONT1.DAT` 格式全解 (8×8, 256 glyph,見 [`docs/08-tfont-re.md`](docs/08-tfont-re.md))、`SetDisplayMode` 單點靜態定位 VA `0x40cdf8`(file `0x40cdfa`/`0x40cdff`)、解析度/stride 常數 capstone 掃描計數可枚舉
- **⏸ 待乾淨環境驗證**:改 mode 是否 crash、present 機制 (DirectDraw Blt 還是 Lock+copy)、放大手法。先前 session 曾有「present stretch」結論,但在不穩環境產生、**已作廢移除**,需重做
- **Phase 3 (未做,最重)**:font 換 24×24 畫在高解析畫布 + Big5 2-byte lookup。**這是讓上述所有 Big5 CHT 從亂碼變可讀中文的臨門一腳**

完整路線圖 [`docs/09-a1-hires-canvas-roadmap.md`](docs/09-a1-hires-canvas-roadmap.md);方法論獨立成 skill [`../skills/retro-directdraw-hires-cjk`](../skills/retro-directdraw-hires-cjk/SKILL.md)。

**目前實際狀態**

- ✅ **資料層**:33 劇本 TIT/DES + 119 條 UI + 40 條裝備名,已 Big5 patch (byte-preserving)
- ⚠ **顯示層**:遊戲內仍顯示亂碼 (8×8 font 硬牆),需 A1 Phase 3 (font 24×24) 才可讀
- ✅ 現代環境跑通 (wine 三層雷解) + AppImage + Windows zip + 完整中文文件 (劇本/裝備/攻略/翻譯原則)

## 相關

- [pg-cht](https://github.com/wicanr2/pg-cht) — 裝甲元帥繁中化（1994）
- [ag skill in pg-cht](https://github.com/wicanr2/pg-cht/blob/main/skills/panzer-general-wine/SKILL.md) — 盟軍將軍繁中化（1995）
- Pacific General 官方下載：[panzergeneraldownload.com](https://panzergeneraldownload.com/pacific-general.html)

## 授權

繁中化文字翻譯 / 逆向分析文件 / 打包腳本：MIT
原版遊戲版權屬於 SSI / Mindscape / Ubisoft（現持有者）。本 repo 不含原版遊戲檔案。
