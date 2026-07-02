# 02 心得：在 Windows 10 / 11 上跑 Pacific General

*這一篇寫給不想灌 Linux 的玩家 —— 或者，寫給那些「我明明有正版光碟盒還在」的收藏家。*

## 前置

需要三個檔案（都在 game 目錄）：

1. `PACGEN.EXE`（主程式，976 KB）
2. `PACGEN_v11_Patch.EXE`（v1.1 官方 patch，1997-09）
3. `BJensen_PacGen_NoCD.exe`（社群 no-CD 工具，2001-10，13 KB Borland DOS）

## 步驟

### 步驟 1：套用官方 v1.1 patch

把 `PACGEN_v11_Patch.EXE` 放到 game 目錄旁邊，執行即可。這個 patch 修正原版一些戰役 bug 與 AI 邏輯。**不吃 CD**，直接跑。

*（如果你的 game 檔案是從 v1.1 完整包解壓來的，這步已經內建，跳過。）*

### 步驟 2：拿掉 CD 檢查

Pacific General 原本會找光碟裡的 `smack\pacintro.smk` 播開場。如果你**沒插原版光碟**，遊戲會彈「Please insert CD」對話框然後死循環。

用 `BJensen_PacGen_NoCD.exe`：

```
C:\...\Pacific General> BJensen_PacGen_NoCD.exe

Pacific General v1.1 CD Crack
=============================
> - Apply CD crack
> - Remove CD crack
> - Exit
=============================
Enter Choice: 1
CD Crack successfully applied!
```

**這是修改 PACGEN.EXE 的**，套用前務必備份原版 `PACGEN.EXE.bak`（BJensen 會自動備份，但保險起見自己也留一份）。

### 步驟 3：Windows 10 / 11 相容模式

在 `PACGEN.EXE` 右鍵 → 內容 → 相容性 →

- ☑ 以相容模式執行：**Windows XP (Service Pack 3)**
- ☑ 縮小顯示比例：256 色
- ☑ 停用全螢幕最佳化
- ☑ 以系統管理員身份執行（**可能需要**，取決於 UAC 設定）

如果進遊戲後畫面反而擠成小視窗、或觸控筆游標定位跑掉，把「縮小顯示比例：256 色」取消，改試「640×480 螢幕解析度」。

### 步驟 4：中文顯示

Pacific General 原版 UI 用 Windows 系統字型（Tahoma / MS Sans Serif）。CHT patch 後的 exe 引用 Big5 charset (136) 字體 —— Windows 10/11 預設**沒裝完整 Big5 字型**。

解法之一（推薦）：安裝 [Noto Sans TC](https://fonts.google.com/noto/specimen/Noto+Sans+TC)，然後在 `regedit` 加：

```
[HKEY_LOCAL_MACHINE\Software\Microsoft\Windows NT\CurrentVersion\FontSubstitutes]
"MS Sans Serif,136"="Noto Sans TC"
"Tahoma,136"="Noto Sans TC"
```

解法之二（懶人）：用 Locale Emulator 或 AppLocale 強制 Big5 環境。這樣 Windows 會自動 fallback 到 MingLiU（Windows 10 內建）。

## 如果你有原版光碟

那就更簡單 —— 步驟 2（no-CD）跳過，遊戲直接讀光碟裡的 `smack\pacintro.smk`。**但 Windows 10 / 11 上光碟機讀取速度慢，開場動畫可能會 lag**，這是硬體問題不是遊戲問題。

## 存檔位置

Pacific General 的存檔寫在 **game 目錄下的 `SAVE\`** 子目錄 —— 這是 Win95 時代的慣例，不是 `%APPDATA%`。所以：

- 移動 game 資料夾時記得帶上 `SAVE\`
- Windows 10 / 11 若 game 裝在 `Program Files\` 下，UAC 可能拒絕寫入 → 遊戲存檔失敗**但不彈錯誤**
- 建議把 game 裝在 `C:\Games\Pacific General\` 或桌面下

## 疑難排解

**Q：進遊戲後畫面上下顛倒 / 顏色錯亂**
A：DirectDraw 相容問題。試 dxwnd 或 dgVoodoo2 包裝一層。

**Q：主選單 OK 但進戰役後閃退**
A：先確認你套過 v1.1 patch。v1.0 有多個戰役會在特定回合 crash。

**Q：音樂沒聲音**
A：Miles Sound System (mss32.dll) 在 Windows 10/11 上偶爾出問題。試把 `WING32.DLL` 和 `MSS32.DLL` 從 game 目錄刪掉 —— 有些系統會 fallback 到 built-in 版本；有些系統則是徹底無聲，但至少不 crash。
