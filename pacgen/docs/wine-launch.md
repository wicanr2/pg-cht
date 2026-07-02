# PACGEN.EXE 在 wine 下啟動記錄

## 定案配方

```bash
export WINEPREFIX=~/.wine-pacgen        # 任何 win32 prefix
export WINEARCH=win32
export WINEDLLOVERRIDES="mscoree,mshtml="
export WINEDEBUG=-all
cd /path/to/Pacific\ General
wine explorer /desktop=PACGEN,640x480 PACGEN.EXE
```

無需 DLL override、無需 exe patch、無需 fake CD drive。

## 走過的雷

| 症狀 | 誤診 | 實際 |
|---|---|---|
| PACGEN 啟動後 crash @ eip=0x41544144 ('ATAD') | mss32 問題 | 不用 virtual desktop 就會 crash |
| Wine Desktop 純藍屏 20 秒 | 遊戲卡 CD 檢查 | virtual desktop 大小不對(1024x768),遊戲 640x480 fullscreen 收縮成 1x1 |
| 直接跑 `wine PACGEN.EXE` (無 explorer)搶主機解析度到 640x480 | Xrandr bug | 遊戲用 DDraw exclusive fullscreen mode 改主機模式 |

## 關鍵洞察

DirectDraw exclusive fullscreen mode 下,遊戲會嘗試把「主機主要顯示 mode」切成 640x480。加 `explorer /desktop=NAME,640x480` **正好匹配**這個目標解析度,虛擬桌面把 DDraw primary surface 包起來,主機螢幕不被搶。

用 1024x768 或其他不匹配的解析度會失敗 — 遊戲要 640x480 拿不到,退到 1x1 fallback。

## 靜態分析(CD-check,備用資訊)

CD 檢查在 VA `0x40c847` - `0x40c8d8`(file `0xbc47` - `0xbcd8`):

- 字串 `smack\pacintro.smk` 在 file `0xca8ac` (VA `0x4cc4ac`)
- xref 於 file `0xbc4f` (PUSH imm)
- 迴圈掃 A-Z 檢查 `%c:\smack\pacintro.smk`
- 卡關對話框 @ VA `0x40c8a6` (call MessageBox)

**目前不需要 patch** — CD 檢查在 wine 下若 pacintro.smk 於 pwd 存在就通過(具體機制:也許 `MessageBox` 被 wine 短路,也許遊戲 fall-through 到 pwd)。

若未來要做 CD-check bypass:
- 簡潔 patch: `mov [ebp-0x2c], 0x2e` @ 0x40c861 (原 `mov [ebp-0x2c], 0`)
- 需驗證 0x4b8530 對假 drive char 的處理

## 恢復解析度(踩雷用)

若不小心讓遊戲搶主機解析度:
```bash
PRIMARY=$(xrandr | grep " connected primary" | awk '{print $1}')
xrandr --output "$PRIMARY" --mode 1920x1200
```

或當場 `pkill -9 PACGEN.EXE` — wine 通常會還原。
