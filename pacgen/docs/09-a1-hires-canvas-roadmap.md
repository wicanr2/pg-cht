# 09 A1 路線圖:拉高內部畫布支援 24×24 CJK

*rule 81(retro CJK hi-res canvas)在**只有 EXE**的閉源遊戲上的落地路線。*

> ⚠️ **狀態聲明**:本文件先前版本含一段「present stretch 已用動態 trace 確認、4-word patch 讓畫面放大」的結論。那些是在一個 tool 輸出不穩、截圖無法可靠判讀的 session 期間產生的,**未能在乾淨環境定案,已全部移除**。以下只保留**純靜態反組譯**得出的可靠事實 + 概念規劃。所有涉及「跑起來看畫面」的結論,都標為**待乾淨環境重新驗證**。

## 為什麼走 A1

見 [08-tfont-re.md](08-tfont-re.md):TFONT1.DAT 是 8×8 點陣字,物理上塞不下可讀中文。rule 81 正解 = 拉高內部畫布(640×480 → 更高)、底圖 nearest scale、CJK 用 24×24 畫在放大畫布。

## 靜態偵察(可靠,純 objdump / capstone)

### SetDisplayMode 是單一控制點

```asm
0x40cdf8  push 8         ; bpp = 8 (256 色 paletted)
0x40cdfa  push 0x1e0     ; height = 480
0x40cdff  push 0x280     ; width = 640
0x40ce11  call [eax+0x54]; IDirectDraw::SetDisplayMode(640,480,8)
```

**單一呼叫點**(file offset `0x40cdfa` height / `0x40cdff` width)。這是純靜態反組譯,可靠。

### 解析度常數 / stride 靜態掃描

capstone 掃 .text 的立即數與 pattern 次數(純靜態,可靠):

| pattern | 次數 | 意義 |
|---|---|---|
| `IDirectDraw::SetDisplayMode` 呼叫 | 1 | 解析度設定單點 |
| back buffer size `307200` (640×480) | 5 | malloc / clear 候選 |
| `×5 << 7` (=×640, `shl reg,7`) | 9 | stride 計算候選(含非 stride ×128) |
| `push 640` | 2 | surface 建立參數 |
| dword `640` 全部 | 30 | 含常數比較 / 邊界 |
| dword `480` 全部 | 27 | 同上 |

**判斷**:解析度/stride 相關常數**可枚舉**(個位到數十處),非海量散布 → 拉高畫布是「有限工程」而非「無源碼下無限大」。**但這只是掃描計數;哪些是真 stride、present 走 Blt 還是 Lock+copy,都需下面的動態驗證才能定案。**

## 待乾淨環境驗證的關鍵問題(先前臆測已作廢)

以下問題**必須**用穩定的 wine + 可靠截圖環境重新做,不能靠先前 session 的結論:

1. **改 SetDisplayMode 到目標解析度後,遊戲是否 crash?** (地基生死線)
2. **present 機制是 DirectDraw Blt 還是 Lock + software copy?** — 用 `WINEDEBUG=+ddraw` trace 判讀,別靠靜態猜 vtable offset
3. **present 到 primary 的尺寸/rect 從哪來?** — 是硬編立即數還是讀 surface desc
4. **拉高 mode 後畫面是正確放大、還是 stride mismatch / 只填左上?** — 需可靠截圖判讀

> 這些每一題先前都有過「答案」,但都在不可靠環境產生,**一律重做**。方法見 skill [`retro-directdraw-hires-cjk`](../../skills/retro-directdraw-hires-cjk/SKILL.md) 的 RE 流程。

## 概念路線圖(未實作,方向規劃)

| Phase | 目標 | 里程碑 |
|---|---|---|
| **P0** | SetDisplayMode 定位(✅ 靜態完成)+ 改 mode 是否 crash(待驗證) | 改 mode 不 crash |
| **P1** | present 機制確認 + 讓畫面放大填滿目標解析度 | 畫面 crisp 放大 |
| **P2** | 底圖 pixel art(SHP.PFP)nearest ×2 | 原版畫面 2× crisp |
| **P3** | **font 換 24×24 + Big5 2-byte lookup**(繪字管線 VA `0x474000`-`0x47b000`) | **中文清晰可讀** |
| **P4** | 座標 / 滑鼠命中區 ×2 映射(minimap 等 raw widget 單獨處理) | UI 可互動對位 |
| **P5** | 整合 + 打包 AppImage / Windows zip | ship |

**P3 是讓所有已完成的 Big5 CHT(119 UI + 33 劇本 + 裝備名)從亂碼變可讀中文的臨門一腳**,也是 A1 對中文化最直接的價值。

## 下一步(從乾淨環境起)

1. 改 SetDisplayMode 到目標解析度,fresh source hardlink 測試是否 crash(P0 生死線)
2. `WINEDEBUG=+ddraw` trace 確認 present 機制(Blt vs Lock+copy)
3. 據 present 機制決定放大手法(StretchBlt dst_rect / software copy stride / 底圖 blit ×2)
4. 每步用可靠截圖判讀里程碑,不接受無法確認的結果

## 產出檔案

- font 格式 + 繪字管線 RE:[08-tfont-re.md](08-tfont-re.md)(靜態,可靠)
- SetDisplayMode patch 點:file `0x40cdfa`(height) / `0x40cdff`(width)(靜態,可靠)
- 方法論 skill:[`retro-directdraw-hires-cjk`](../../skills/retro-directdraw-hires-cjk/SKILL.md)
