# 06 心得:TXT.PFP 就地 patch 的試驗與踩雷 (v0.2 未定案)

*給下一 session 接手 v0.3 TXT.PFP CHT 版套用的人。*

## 起因

v0.1/v0.2 都沒 ship CHT TXT.PFP。使用者觀察遊戲畫面看到英文 `Select Axis Campaign` / `Select Allied Campaign` 出現在戰役選單。這兩條字串位於 `TXT.PFP` section 47 (`Campaign Selection Screen`)。

## 字串定位(已完成)

| 字串 | Byte offset (file) | 原長 | 建議譯 (Big5) | Padding |
|---|---|---|---|---|
| `Select Axis Campaign` | `0x5fdb` | 20 | `選擇軸心戰役` (12 bytes) | + 8 spaces |
| `Select Allied Campaign` | `0x5ff1` | 22 | `選擇盟軍戰役` (12 bytes) | + 10 spaces |

## PFPDATA.IDX 結構 (RE 進行中)

`data/PFPDATA.IDX` (22372 bytes) 是 `TXT.PFP` / `SHP.PFP` / `TIL.PFP` 等 archive 的 section 索引。`EXT.IDX` (112 bytes) 告訴每個 archive 的 entry 範圍。

**推測格式** (每 entry 16 bytes,待完全確認):

```
[4 bytes] cumulative offset (start of this section in TXT.PFP)
[8 bytes] name (null-padded, 例: "CLASSES\0", "TERRAIN\0", ...)
[4 bytes] size (this section's byte length)
```

驗證:
- Entry 1 (CLASSES): offset=0x0, size=0x119
- Entry 2 (TERRAIN): offset=0x119 (= 前一節 size), size=0x1af
- Entry 3 (NATIONS): offset=0x2c8 (= 0x119+0x1af), size=0xc8

## 就地 patch (byte-length preserving) 試驗與更正

**假設**:如果 patch 後每節 byte 長度不變,IDX 內的 offset/size 也不需要動,遊戲讀 section 47 內容還是同一塊記憶體。

**第一輪實測 (誤診)**:CHT dir 套 PFP patch 後 crash,以為是結構問題。

**第二輪隔離實測 (真相)**:用**乾淨 fresh source hardlink dir** 分開測:

| 組合 | 結果 |
|---|---|
| 純源目錄 (all English) | ✅ boot |
| 源 + PFP in-place patch (無 CHT TIT/DES) | ✅ boot |
| 源 + PFP patch + CHT TIT (無 DES) | ✅ boot |
| 源 + PFP patch + CHT TIT + CHT DES | 曾以為 crash |
| 源 + CHT TIT + CHT DES (v0.1 打包時的組合) | ✅ boot |

**第三輪徹底翻案 (v0.3 深挖)**:

| 組合 | 結果 |
|---|---|
| 源 + CHT DES 單獨 (無 PFP, 無 TIT) | ✅ boot |
| 源 + PFP patch + CHT DES (無 TIT) | ✅ boot |
| 源 + PFP patch + CHT TIT + CHT DES (完整三者) | ✅ **boot!** |

**結論(徹底修正)**:**PFP patch / CHT TIT / CHT DES 三者兩兩皆能 boot,三者同時也能 boot**。

前兩輪誤診的根因:
1. 我在 CHT build dir 上做的多輪 patch/revert 累積了不乾淨狀態
2. 測試間隔 wineserver session 髒污 (page fault @ 0x54484320 是隨機記憶體垃圾)
3. 誤把 wine session 髒污歸咎到「檔案內容併用」

**正確做法**:每次測試前 `wineserver -k + sleep 3 + rm -rf /tmp/pg-test-*` 然後 fresh `cp -al` 源目錄再套 patch。這樣測所有組合都能 boot。

## 待驗證假設 (給下 session)

1. **Wine session 髒污**:多次 launch 後 wineserver 累積 stale state,連 baseline (source dir + 原 PFP) 都會偶發 crash。**下 session 用完全 fresh WINEPREFIX 重測 in-place patch**,若同樣 crash 才確定是結構問題。
2. **PFPDATA.IDX 也有 "line count" 或 "line offset table"**:section 47 是 2 行結構,遊戲可能在 IDX 或其他地方存了 line-count,my patch 加了 trailing spaces 但沒改 line count,parser 可能溢位讀。
3. **另有第三索引檔**:除 `PFPDATA.IDX` 與 `EXT.IDX`,可能還有 per-section 內部索引 (line offset table),需再掃 data/ 目錄。
4. **完全放棄 in-place patch**,改走「重算所有 offset + rewrite IDX」路徑 (見下)。

## 替代路徑 (v0.3 選擇)

### 路徑 A:in-place patch (若下 session fresh prefix 驗過真的 struct issue)

放棄。

### 路徑 B:重算 PFPDATA.IDX

1. Unpack TXT.PFP → 74 個 .txt 檔 (已有 `tools/pfp_split.py`)
2. 逐節翻譯成 Big5 (已有 `tools/apply_glossary.py` 半自動)
3. 打包新 TXT.PFP 並計算各節新 size + cumulative offset
4. **重寫 PFPDATA.IDX 內 TXT 段落的 entry** (bytes 0x0 - 0x38a):
   - 保留 8-byte 名稱不變
   - 更新 size 欄位 = 新節長度
   - 更新 offset 欄位 = 累積前面所有節的新長度
5. **EXT.IDX 可能也要更新** (0x38a 這個 TXT 段末位置變了)

### 路徑 C:直接 patch PACGEN.EXE 內字串

若 `Select Axis Campaign` 的顯示點是 EXE 內的 format string,可以在 EXE 的 `.rdata` 直接就地翻譯 (同 PG-cht `pg-cht.exe` 手法)。目前 [pacgen_ui_candidates.tsv](../translations/pacgen_ui_candidates.tsv) 有 356 條 UI 候選待人工複審,若 `Select Axis Campaign` 或其上下文在 EXE 內,可從那邊改。

## 目前狀態 (v0.2)

- 已還原 TXT.PFP 到原版 (sha256 `2927bf04...`,`source` = `CHT build` = `AppDir` = `zip portable`)
- 試驗腳本 (若下 session 要重跑) 在下方

```python
# 就地 patch (byte-length preserving)
import shutil
src = ".../原版 TXT.PFP"
dst = ".../目標"
data = bytearray(open(src, 'rb').read())
patches = [
    (0x5fdb, 20, '選擇軸心戰役'),
    (0x5ff1, 22, '選擇盟軍戰役'),
]
for off, n, zh in patches:
    zb = zh.encode('big5')
    data[off:off+n] = zb + b' ' * (n - len(zb))
open(dst, 'wb').write(bytes(data))
```

## 教訓

1. **wine session state 會累積髒污**,連 baseline 重測都可能不穩,debug 要準備 **fresh WINEPREFIX + fresh Xvfb** 才可靠
2. **byte-length preserving 不夠**:游戲可能有其他索引結構(line count / per-section 內表)沒被覆蓋到
3. `page fault @ 0x54484320` 這種 ASCII-looking 位址常是 "隨機記憶體剛好像字串" 的巧合,**別追字面 pattern**;真正 root cause 是「上一步 parser 讀了什麼並把它當 pointer」
