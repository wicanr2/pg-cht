# 三部曲繁中化散布清單(dist-all)

> 本檔記錄最終散布套件的內容與校驗值,方便追蹤與驗證。**二進位檔本身不進 repo**(體積過大),集中放在建置機的本地 `dist-all/`。清單日期:2026-07-09。

## 版本重點(2026-07-09)

- **裝備名跨作品 + 跨變體統一**:每作的兩個發佈變體(原始裝備 / 主版)單位名稱已對齊為同一套統一譯名,細節見 [`equipment-crossgame-consistency.md`](equipment-crossgame-consistency.md)。
- **變體結構**:
  - **PG(裝甲元帥)**:三個 EQP 數值完全相同,無「修改數值」變體;原始裝備 / 繁中化 兩發佈只差命名風格(對齊後 EQP byte 相同)與一個 README。
  - **AG(盟軍元帥)**:真有兩套數值——原始裝備(SSI 原始值,= Lite)與修改數值主版(110 單位重新平衡);兩者名稱皆已統一、各自數值保留。
  - **PacGen(太平洋元帥)**:單一版,v0.2 修正 2-byte CJK 白底 bug + 對話框排版 + 裝備譯名。
- 名稱對齊方式:純名稱欄(EQP 每筆記錄 bytes 0:20)byte 複製,保留數值欄(bytes 20:50),不改任何平衡。

## 套件清單(5 變體 × 2 格式 = 10 檔)

| 遊戲 | 變體 | 數值 | 格式 | 檔名 | 大小 | md5 |
|---|---|---|---|---|---|---|
| PacGen | — | 原始 | AppImage | `PacificGeneral-x86_64.AppImage` | 715M | `0aebfc2714bfee82962833b05e00485c` |
| PacGen | — | 原始 | Windows | `PacificGeneral_CHT_v0.2_20260709-portable.zip` | 353M | `e57a12e3080b06d3927803e22de1225e` |
| PG | 原始裝備 | 原始 | AppImage | `PanzerGeneral-原始裝備-x86_64.AppImage` | 397M | `38acb9f2c6c6ddf56b533bcafba971e0` |
| PG | 原始裝備 | 原始 | Windows | `PG-cht-1.2_原始裝備_20260702-wine.zip` | 17M | `a11cbad2a123a324165516fc7c229ef0` |
| PG | 繁中化 | 原始 | AppImage | `PanzerGeneral-繁中化-x86_64.AppImage` | 397M | `0891bd59b5523b25c0f5c54d36585d63` |
| PG | 繁中化 | 原始 | Windows | `PG-cht-1.2_繁中化_20260519-wine.zip` | 17M | `fe38a1a0d3ed7f61d83d4757483a0e6f` |
| AG | 原始裝備 | 原始 SSI | AppImage | `AlliedGeneral-原始裝備-x86_64.AppImage` | 392M | `b0713ea9bf6c250dd52f425417e765bf` |
| AG | 原始裝備 | 原始 SSI | Windows | `AlliedGeneral_CHT_v1.1_原始裝備_portable_20260702.zip` | 12M | `e1f4a4e20c136ea5b95b03bb7b5e9207` |
| AG | 修改數值 | 重新平衡 | AppImage | `AlliedGeneral-修改數值-x86_64.AppImage` | 392M | `8ae8c04f3f81ac9c8fc481361a407474` |
| AG | 修改數值 | 重新平衡 | Windows | `AlliedGeneral_CHT_v1.1_portable_20260531.zip` | 12M | `3595ddf3b60faf38bf3f86c6c6eb304e` |

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
