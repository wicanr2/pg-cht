# 01 心得：讓 1997 年的 DirectDraw 遊戲在 wine 11 上復活

*這一篇寫給 Linux 玩家 —— 或者，寫給每個曾經覺得「這遊戲太老 wine 應該沒問題」然後被打臉的人。*

## 定案配方

```bash
export WINEPREFIX=~/.wine-pacgen        # 任何 win32 prefix
export WINEARCH=win32
export WINEDLLOVERRIDES="mscoree,mshtml="
export WINEDEBUG=-all

cd "/path/to/Pacific General"
wine explorer /desktop=PACGEN,640x480 PACGEN.EXE
```

就這樣。**沒有 DLL override、沒有 EXE patch、沒有 no-CD crack。**

## 為什麼那條指令長這樣？三個坑一路踩

### 坑 1：直接 `wine PACGEN.EXE` 會偷走你的主機解析度

第一次跑，遊戲進去了 —— 然後整個 X 桌面被強制切成 640×480，工作列擠成一團，多螢幕的第二螢幕全變黑。

原因：**PACGEN.EXE 用的是 DirectDraw exclusive fullscreen mode**。1997 年的 SSI 遊戲全都這樣寫 —— 不管當時你螢幕多大，遊戲搶下 primary surface 切成 640×480 就開跑，退出時再切回來。90 年代 CRT 螢幕切模式只是慢一點，2026 年 LCD/OLED 主機做同一件事：xrandr 被外力 override，桌面環境要花好幾秒才反應過來。

kill 掉遊戲後，用這條救回來：

```bash
PRIMARY=$(xrandr | awk '/ connected primary/{print $1; exit}')
xrandr --output "$PRIMARY" --mode 1920x1200   # 換成你原本的
```

### 坑 2：加了 `explorer /desktop=PACGEN,1024x768` — 純藍屏 20 秒

以為虛擬桌面就解決了，隨手選個 1024×768。結果：Wine Desktop 出現，純藍色，20 秒沒任何遊戲畫面。

用 `xwininfo -root -tree` 看真相：

```
0x4400005 (has no name): ("pacgen.exe" "pacgen.exe")  1x1+0+0
```

**遊戲視窗只有 1×1 像素。**

原因：DirectDraw exclusive fullscreen 想要 640×480 的 primary surface。虛擬桌面給了 1024×768，尺寸不匹配，DDraw 建立 primary 失敗、fallback 到 1×1 window。遊戲進了 message loop 但沒東西可畫。

### 坑 3：正確的虛擬桌面大小

把 desktop 從 1024×768 改成 **640×480，剛剛好**。DirectDraw primary surface = 虛擬桌面 = 640×480，三者對齊，畫面出來。

```bash
wine explorer /desktop=PACGEN,640x480 PACGEN.EXE
```

## 這一路走過的排除路徑

一開始被幾個假訊號帶偏，記錄在這裡讓後來的人少踩：

| 假訊號 | 誤診 | 真相 |
|---|---|---|
| 直接跑會 crash @ eip=0x41544144 ('ATAD') | 以為是 mss32.dll (Miles Sound System) 出錯 | 是沒有 virtual desktop 導致 DDraw 掛掉，crash 位置只是 handler 讀到損毀 vtable |
| 加 `smackw32=b` (built-in) 感覺穩定 | 以為 Smacker video codec 有問題 | 純巧合，真正的 fix 還是 virtual desktop |
| 藍屏懷疑 CD check 卡住 | 靜態分析找到 CD-check 迴圈 @ VA 0x40c847 (見 [CD-check RE 筆記](../docs/re-cd-check.md)) | CD 檢查其實通過（pacintro.smk 在當前目錄），黑屏純粹是 window size 問題 |

## 相關檔案

- [BJensen no-CD patcher](../../太平洋元帥/Pacific General/BJensen_PacGen_NoCD.exe) — 13KB Borland DOS 工具，2001 年由 BJensen 發布。**在 wine 下不需要用它**（CD 檢查會自動過），但保留在 game dir 供 Windows 玩家使用（見 [modern Windows](02-modern-windows.md)）。
- [wine-launch.md](../docs/wine-launch.md) — 更技術的一手筆記
- CD-check 靜態分析：xref 於 file offset `0xbc4f`，字串 `smack\pacintro.smk` @ file `0xca8ac` (VA `0x4cc4ac`)

## 給 CHT AppImage 打包者的備忘

當我把這款遊戲包成 AppImage（比照裝甲元帥、盟軍將軍的做法），AppRun 應該這樣寫：

```bash
# 只需要虛擬桌面 640x480,無需 patch
exec "$WINELOADER" explorer /desktop=PACGEN,640x480 ./PACGEN.EXE "$@"
```

DPI 不用調（遊戲用 DDraw 直接畫 pixel art，不吃 GDI DPI 值）。虛擬桌面大小可以透過 env 覆蓋讓玩家自己拉更大 —— 但**必須整數倍**（640×480、1280×960、1920×1440），非整數倍會出現 nearest-neighbor 縮放不均勻。
