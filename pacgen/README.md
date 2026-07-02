# pacgen-cht — 太平洋元帥繁體中文化

*Pacific General (SSI/Mindscape, 1997) — 30 年後的中文化補完*

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

v0.1 施工中。這是 3-5 個 session 的專案。

- [x] Wine 啟動配方確認
- [x] EXE 字串 dump + 初步 filter
- [x] docs 專欄骨架
- [ ] TXT.PFP 內字表 unpack
- [ ] 33 個劇本 TIT / DES 中譯
- [ ] EXE UI 字串 Big5 length-preserving patch
- [ ] AppImage + Windows zip 打包

## 相關

- [pg-cht](https://github.com/wicanr2/pg-cht) — 裝甲元帥繁中化（1994）
- [ag skill in pg-cht](https://github.com/wicanr2/pg-cht/blob/main/skills/panzer-general-wine/SKILL.md) — 盟軍將軍繁中化（1995）
- Pacific General 官方下載：[panzergeneraldownload.com](https://panzergeneraldownload.com/pacific-general.html)

## 授權

繁中化文字翻譯 / 逆向分析文件 / 打包腳本：MIT
原版遊戲版權屬於 SSI / Mindscape / Ubisoft（現持有者）。本 repo 不含原版遊戲檔案。
