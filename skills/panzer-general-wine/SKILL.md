---
name: panzer-general-wine
description: 在 wine 下啟動 Panzer General (PG-cht.exe，繁中化 Borland Pascal Win95 老遊戲) 的完整解法。當使用者談到「PG」「Panzer General」「裝甲元帥」「256 色才能執行」「exNilPtr」「記憶體不足」「PG 跑不起來」「缺 WING32.dll」等情境觸發。
---

# Panzer General 繁中化版在 wine 啟動的解法

`PG-cht.exe` (Borland Pascal 7 編譯的 1994 Win95 遊戲) 在 wine 下遇到 3 個獨立 issue：256 色檢查、case dispatch nil-deref、cursor wrapper nil-deref。本 skill 記錄完整解法，可在 fresh wine prefix 上直接套用。

## 工作目錄

`/home/anr2/game/Panzer_General/PG-cht-1.2_繁中化_20260519-wine/`（後綴 `-wine` 表示經 wine 11 完整驗證；舊 `20260517` 為 wine 6 時期版本，已 frozen）

關鍵檔：
- `PG-cht.exe` — patched 版本 (有 256 色 bypass + 2 個 nil-deref patch)
- `PG-cht.exe.bak` — 原版（**不可動**，重 patch 用）
- `pgs.dll` — 自製 GDI32 wrapper (256 色 bypass)
- `pgs-src/patch_all.py` — 套用所有 patch 的 script
- `pgs-src/{pgs.c, pgs.def, build.sh}` — pgs.dll source

## 環境需求

| 項目 | 版本 | 為何 |
|---|---|---|
| Ubuntu | 22.04 jammy | 主機 |
| wine | **11.0 (winehq-stable)** | wine 6.0 Pascal SEH 把所有 nil 包成「記憶體不足」對話框看不到真實 EIP；wine 11 直接 page fault 暴露真實 nil-deref 點 |
| mingw-w64 | gcc-mingw-w64-i686 | build pgs.dll (32-bit PE wrapper) |
| 中文字型 | Noto Sans CJK TC (`fonts-noto-cjk-extra` 或 host symlink) | 否則 PG 中文 label 顯示豆腐字 |

## 一鍵啟動流程

```bash
cd /home/anr2/game/Panzer_General/PG-cht-1.2_繁中化_20260519-wine
python3 pgs-src/patch_all.py 1 nohook     # 套用全部 patch (256-color + ret + jne→jmp), 不要 helper hijack

# 變體 A：嵌入式（PG 視窗直接出現在 host desktop 上）
DISPLAY=:1 wine ./PG-cht.exe

# 變體 B：獨立 wine 虛擬桌面視窗（建議；PG + 其餘 explorer 子視窗都被包進一個可拖移的 X window）
DISPLAY=:1 wine explorer /desktop=PG,1280x800 ./PG-cht.exe
```

預期 ~3 秒後出現 PG 主視窗 + 「裝甲元帥遊戲選項」對話框。變體 B 對應的 X window：
- `PG - Wine Desktop` (WM_CLASS `explorer.exe`)
- `裝甲元帥遊戲選項` (WM_CLASS `pg-cht.exe`)

啟動 log 中正常會看到（**不是 error**）：
- `err:winediag:MIDIMAP_drvOpen No software synthesizer midi port found` — 沒裝 fluidsynth/timidity 才有，PG 仍會跑
- `fixme:mcimidi:MIDI_player NIY: SMPTE track start ...` — PG 已進入主迴圈、開始播 BGM 的信號

## 三個 PE patch 解釋

### Patch 1：`GDI32.dll` → `pgs.dll` (256 色 bypass)

PG 啟動先檢查 `GetDeviceCaps(hdc, BITSPIXEL) == 8`，否則跳「裝甲元帥需要 256 色才能執行」對話框退出。

解法：自製 `pgs.dll` 28 個 PE forwarder 透傳 gdi32，只攔截 `GetDeviceCaps` 回 BITSPIXEL=8。原地把 PE 的 import name `GDI32.dll\0` (10 bytes) 改寫為 `pgs.dll\0\0\0`，loader 自然載入 pgs.dll 替代 gdi32。

### Patch 2：`ret @ 0x42b2c0` (跳過 case dispatch)

PG 啟動早期呼叫 fault function 0x42b2c0 (4-way case dispatch)。該 function 每個 case 都對 global `[0x5f518c]` 做 vtable call，但該 global 在 wine 下未被初始化（nil），導致 `mov eax,[eax]` 直接 page fault。

解法：把 function 第一個 byte（0x55 push ebp）改為 0xc3 (ret)，function 直接返回 do-nothing。

### Patch 3：`jne` → `jmp` @ 0x57a9a6 (cursor wrapper bypass)

PG cursor wrapper class @ 0x57a963 呼叫 `SetCursor(...)` 並把返回值（前一個 HCURSOR）存進 `Self.field4`。若 wine 沒設過 cursor，SetCursor 回 NULL → Self.field4 = 0 → PG raise exNilPtr。

解法：把後續的 `cmp [eax+4], 0; jne @@ok`（jne 6 bytes `0f 85 4b 00 00 00`）改為無條件 jmp（`e9 4c 00 00 00 90`）。raise 永遠被跳過。

## 中文字型設定

### 最小設定（PG 對話框繁中能顯示就好）

把系統的 Noto Sans CJK 加進 wine prefix + 設 FontSubstitutes：

```bash
mkdir -p ~/.wine/drive_c/windows/Fonts
ln -sf /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc ~/.wine/drive_c/windows/Fonts/
ln -sf /usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc ~/.wine/drive_c/windows/Fonts/

cat > /tmp/pg-fonts.reg << 'EOF'
REGEDIT4

[HKEY_LOCAL_MACHINE\Software\Microsoft\Windows NT\CurrentVersion\FontSubstitutes]
"Tahoma,136"="Noto Sans CJK TC"
"Tahoma"="Noto Sans CJK TC"
"PMingLiU"="Noto Sans CJK TC"
"PMingLiU,136"="Noto Sans CJK TC"
"MingLiU"="Noto Sans CJK TC"
"MingLiU,136"="Noto Sans CJK TC"
EOF
wine regedit /S /tmp/pg-fonts.reg
```

`136` 是 BIG5_CHARSET。PG 用 Tahoma + Big5 charset，wine 沒匹配字型就豆腐。

### 推薦完整字型（真版 Tahoma + Microsoft corefonts）

只裝 Noto CJK 的話，wine 內部會把所有 Tahoma 請求 redirect 到 Noto；PG 的西文部分也會用 Noto 渲染（不會太醜但不是原始觀感）。要保留西文用真 Tahoma + 繁中 fallback 到 Noto，補裝 winetricks corefonts + tahoma：

```bash
# Ubuntu 22.04 apt 版 winetricks (2021-02-06) 對 wine 11 不相容
# 任何 verb 都會卡在 "wine cmd.exe /c echo '%AppData%' returned empty string"
# 必須直接抓 GitHub 最新版
curl -sSL -o /tmp/winetricks-latest \
  https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks
chmod +x /tmp/winetricks-latest

WINEDLLOVERRIDES="mscoree,mshtml=" /tmp/winetricks-latest --unattended corefonts tahoma
```

裝完 `~/.wine/drive_c/windows/Fonts/` 會有 35 個檔案（含 Tahoma/Arial/Times New Roman/Courier/Verdana/Georgia/Trebuchet/Comic/Impact/Webdings/Andale Mono 全字重 + 兩個 Noto CJK symlink）。

注意：上面那條 `"Tahoma"="Noto Sans CJK TC"` 強制替代規則裝完字型後仍然存在（讓繁中可顯示）。Wine 11 的 fallback 機制理論上能在 substitute 移除後自動處理「西文→真 Tahoma、繁中→Noto」，但繁中化 prefix 製作者刻意保留這條規則。**動之前先測試**。

## 從零升級 wine 6.0 → 11.0 步驟

```bash
# 1. 修 WineHQ repo codename (focal→jammy)
sudo bash -c 'cat > /etc/apt/sources.list.d/winehq-jammy.sources << EOF
Types: deb
URIs: https://dl.winehq.org/wine-builds/ubuntu
Suites: jammy
Components: main
Architectures: amd64 i386
Signed-By: /etc/apt/keyrings/winehq-archive.key
EOF
rm -f /etc/apt/sources.list.d/winehq-focal.sources'

# 2. 移除舊 wine
sudo apt remove -y wine wine64 wine32 libwine fonts-wine
sudo apt purge -y "wine-stable*" libwine:i386 wine-stable-i386:i386

# 3. 裝新 wine — *先 dry-run*，否則 apt 解依賴可能反咬移除新裝的 wine
#    踩過的雷：先前裝 ScummVM 編譯依賴 (libsdl2-dev 等) 時 jackd1↔jackd2 衝突
#    讓 apt 把 winehq-stable / wine-stable / wine-stable-i386 連帶 Remove 掉
sudo apt update
sudo apt-get install -s libjack-jackd2-dev winehq-stable wine-stable wine-stable-i386 wine-stable-amd64   # 看 Remove 清單
sudo apt-get install -y libjack-jackd2-dev winehq-stable wine-stable wine-stable-i386 wine-stable-amd64   # 確認乾淨後

# 4. 備份 + 重建 prefix (wine 6 prefix 與 wine 11 不相容)
cp -a ~/.wine ~/.wine.bak-$(date +%Y%m%d)
rm -rf ~/.wine
WINEDLLOVERRIDES="mscoree,mshtml=" wineboot --init   # 跳過 Mono/Gecko installer dialog

# 4b. 永久禁用 wineboot mono/gecko 提示（每次新 prefix 都要做一次，否則對話框會跳出來卡 winetricks）
wine reg add 'HKCU\Software\Wine\DllOverrides' /v mscoree /d '' /f
wine reg add 'HKCU\Software\Wine\DllOverrides' /v mshtml  /d '' /f
# 等同手寫 user.reg：
#   [Software\\Wine\\DllOverrides]
#   "mscoree"=""
#   "mshtml"=""
# 注意：系統 mono (libmono-*) 與 wine-mono 是完全不同的東西，互不衝突
#       wine-stable 套件本身不依賴 mono

# 5. 裝字型 (上面那段)

# 6. 跑 PG
cd /home/anr2/game/Panzer_General/PG-cht-1.2_繁中化_20260519-wine
python3 pgs-src/patch_all.py 1 nohook
DISPLAY=:1 wine ./PG-cht.exe
```

## 畫面放大 / DPI 調整

PG 用 WinG 把 256-color 8-bit DIB 直接 blit 到 client area，**wine 自動 stretch DIB 到 PG window size**。「放大 PG 畫面」= 改變 wine 計算 PG window size 的依據。

**Wine 對 DPI 的行為（實測 wine 11, monitor 1920×1200）**：

| 設定 | PG 主視窗 size | 備註 |
|---|---|---|
| DPI 96 (default) | 1545×871 | 預設 |
| DPI 120 | **1425×803** | **比預設還小！** wine 11 對 120 DPI 處理 nonlinear |
| DPI 144 | 2318×1306 | 精確 1.5×，但超出 1920×1200 約 200px |

**Wine 虛擬桌面 reg key**：
- `HKCU\Software\Wine\Explorer\Desktop` = `"Default"` → 用 default desktop
- `HKCU\Software\Wine\Explorer\Desktops\Default` = `"1920x1200"`
- 用 app 名稱當 reg key (例如 `"PG"="800x600"`) **wine 11 會忽略**，只認 `"Default"`

**設定 DPI 144 + 全螢幕桌面 reg**：
```
[HKEY_CURRENT_USER\Control Panel\Desktop]
"LogPixels"=dword:00000090

[HKEY_CURRENT_USER\Software\Wine\Explorer]
"Desktop"="Default"

[HKEY_CURRENT_USER\Software\Wine\Explorer\Desktops]
"Default"="1920x1200"
```

**結論**：對 PG 這種 fixed-pixel 256-color 老遊戲，**wine 沒有等同 Windows「Display Scaling 200%」一鍵放大整個遊戲畫面的功能**。三條實際路徑：
1. wine DPI 設定 — 對 PG 主視窗 size 有影響但 nonlinear (DPI 144 = 1.5×，DPI 120 反而縮)
2. 手動拖 PG 主視窗邊框 — 若 PG 視窗可 resize，wine 會 redraw stretch 到新尺寸
3. X11 全螢幕 zoom (`xrandr --scale 0.8`) 或 window manager 內 zoom — 影響所有 X app

## 中文字型注意

字型 symlink + FontSubstitutes 設好後 PG 主視窗標題、對話框標題（「裝甲元帥(中文版)」「裝甲元帥遊戲選項」）會正確顯示中文。但 PG **遊戲內畫面文字**（地圖標籤、單位資訊）是 PG 自己用 WinG 繪到 256-color DIB 內的點陣字（不走系統字型），不受 FontSubstitutes 影響。

## Debug 工具：找下一個 nil-deref

若 PG 又卡新 nil-deref，用 `patch_all.py` 的 helper hijack 模式抓 caller IP：

```bash
python3 pgs-src/patch_all.py 1   # N=1, 帶 helper hijack
# 跑 PG，出現「nil」對話框顯示 "#N IP=XXXXXXXX"
# 該 IP 是 helper 第 N 次被 call (filter arg2 == exNilPtr) 的 return addr
# 反組譯該 IP 前 5 bytes (= call helper) 找 nil-check 來源
```

N=1 catches 註冊 exNilPtr class (init 階段，非真實 nil)。N=2 開始是真實 raise，視 PG 狀態而異。

## 關鍵 PE 位址 (PG-cht.exe ImageBase 0x400000)

| 位址 | 用途 |
|---|---|
| 0x55a2fa | helper raise function (487 inline nil-check 都 call 它) |
| 0x5e8ea8 | "exNilPtr" 字串 |
| 0x5f9534 | IAT MessageBoxA |
| 0x5f9574 | IAT wsprintfA |
| 0x5f9590 | IAT SetCursor |
| 0x5f943c | IAT ExitProcess |
| 0x456cc6 | 31802 bytes cc-padding (code cave for thunk) |
| 0x42b2c0 | fault function (case dispatch nil) — Patch 2 |
| 0x57a9a6 | jne in cursor wrapper — Patch 3 |
| 0x1cad76 | file offset of "GDI32.dll" import name — Patch 1 |

## Windows 端打包陷阱：缺 `WING32.dll`

玩家回報（待驗證）：在 Windows 上跑打包後的 PG-cht，啟動時提示缺 `WING32.dll`。

**原因**：PG 是 1994 Win95 遊戲，用 Microsoft **WinG** (Windows Games) library 把 8-bit 256-color DIB 高速 blit 到螢幕。WinG runtime 僅在 Windows 95 預裝；Win98 之後（含 NT/2000/XP/7/10/11）**沒內建**。在 wine 下不會踩到這個問題，因為 wine 自己有實作 wing32 stub（`~/.wine/drive_c/windows/system32/wing32.dll` 等）。但 **wine 的 wing32.dll 不能拿去 Windows 跑**（不是 Microsoft 原版 binary，ABI 行為不一致）。

**檔案清單**（一套 WinG runtime 至少要包含這些）：
- `wing32.dll` — 32-bit WinG API（PG 直接 link 的）
- `wing.dll` — 16-bit WinG（可能 PG-cht 不需要，但通常一起打包）
- `wingdib.drv` — DIB driver
- `wingde.dll` / `wingpal.wnd` — palette helper

**兩條打包路徑**：

| 路徑 | 優點 | 缺點 |
|---|---|---|
| **A. 隨 PG-cht 打包 DLL** | 玩家解壓即跑、零安裝 | 散布 Microsoft binary 灰色地帶（WinG 1996 release 早已 abandonware） |
| **B. 提供 WinG runtime installer 連結** | 乾淨、玩家裝一次 = 全機可用 | 多一步、Microsoft 官方下載連結早已下架 |

**A 的具體做法**：把 4 個 DLL 跟 `PG-cht.exe` 放同一目錄，Windows loader 會先在 .exe 同層找 DLL，找到就不再去 system32。**不需動 Windows 系統**。

**WinG runtime 來源**（皆為 1996 Microsoft 原始 release）：
- WinG 1.0 SDK `wing10.zip` (含 `wing32.dll`) — 早年微軟官方下載早已 404，需從 archive.org / WinWorld 等保存站台抓
- 注意需要的是 **WinG 1.0**（PG-cht 用這個版本），不是 DirectX 早期 release 內附的 stub

**待驗證**（尚未實測）：
1. 把 wine prefix 內的 `wing32.dll` 拿到 Windows 跑 → 大概率失敗，wine 的版本是 wrapper
2. 從 1996 Win95 SDK 取出 wing32.dll 放在 PG-cht.exe 同目錄 → 應該可行，但需實機測試 (尤其在 Windows 10/11)
3. 是否還要附 `wing.dll` (16-bit)：PG-cht.exe 是 PE32 32-bit，應該不必，但要實機 confirm

**收到玩家回報時要問清楚**：
- Windows 版本（7/10/11）
- 完整錯誤訊息（"Cannot find DLL: WING32.DLL" vs "ordinal 5 not found in WING32.DLL"）— 後者代表已有但版本不對
- 玩家有沒有額外裝 DirectX 或其他 WinG-bundled 軟體

## 還原為 baseline (只 256 色 bypass)

```bash
python3 -c "
data=bytearray(open('PG-cht.exe.bak','rb').read())
m=data.find(b'GDI32.dll\\x00')
data[m:m+10]=b'pgs.dll\\x00\\x00\\x00'
open('PG-cht.exe','wb').write(data)"
```

如此 PG-cht.exe 跟 `.bak` 唯一差別是 import name 10 bytes，所有「裝甲元帥致命錯誤」對話框都會回來，但「需 256 色」對話框消失。
