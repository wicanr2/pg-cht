# pacgen-cht — 太平洋元帥繁體中文化

*Pacific General (SSI/Mindscape, 1997) — 30 年後的中文化補完*

---

## 目錄

- [序](#序) — 這款遊戲為何 29 年沒有中文版
- [快速開始](#快速開始) — [Linux (wine)](#linuxwine-11) / [Windows 10/11](#windows-10--11) 兩路啟動
- [心得專欄](#心得專欄) — [`docs/`](docs/) 6 篇文章索引
- [技術資料](#技術資料) — 翻譯工具 + string dump + wine 啟動配方
- [進度](#進度) — v0.2 完成度 + AppImage 三層雷解 + 已知限制 (v0.3)
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

**已知限制 (v0.2 → v0.3)**

- **TXT.PFP 未修改**:CHT 版打包後 game 秒 crash。根因:同目錄 `PFPDATA.IDX` (22 KB) 含硬編碼 offset 到 TXT.PFP 各節區起點,中文 Big5 內容改變 byte 長度就撞歪索引。v0.3 需一併 patch PFPDATA.IDX 或用「Big5 padded 到原長度」策略。
- **PACGEN.EXE 未 patch**:UI 字串 (菜單、按鈕、對話框) 仍原文。v0.3 補 length-preserving binary patch。
- **PACEQUIP.EQP/.TXT 未譯**:813 個裝備名仍原文。v0.3 補。

**v0.1 實際 CHT 範圍**

- ✅ 33 個劇本標題 (Big5) — 玩家選劇本時看到「中途島」「瓜達康納爾」「雷伊泰灣」
- ✅ 33 個劇本簡報 (Big5, 原創史實敘述) — 玩家看 briefing 時看到繁中年份/指揮官/戰略意義
- ⚠ 主選單、UI、裝備、天氣、國家、月份等 — 仍英文

## 相關

- [pg-cht](https://github.com/wicanr2/pg-cht) — 裝甲元帥繁中化（1994）
- [ag skill in pg-cht](https://github.com/wicanr2/pg-cht/blob/main/skills/panzer-general-wine/SKILL.md) — 盟軍將軍繁中化（1995）
- Pacific General 官方下載：[panzergeneraldownload.com](https://panzergeneraldownload.com/pacific-general.html)

## 授權

繁中化文字翻譯 / 逆向分析文件 / 打包腳本：MIT
原版遊戲版權屬於 SSI / Mindscape / Ubisoft（現持有者）。本 repo 不含原版遊戲檔案。
