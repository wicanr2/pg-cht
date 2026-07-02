# 三作 CHT 宣傳影片規劃

*給 PG / AG / PacGen 三支 30-60 秒短片的分鏡與素材需求,採 atlantis 專案 (`~/indian_jones/atlantis/scripts/`) 已驗證過的 pipeline。*

## 定位

**不是 gameplay 教學,是「30 年後這遊戲能中文玩了」的告知**。核心情緒:老玩家看到熟悉的 splash 畫面 → 但底下多了中文 → 這是他當年想要卻拿不到的那個東西。

- **長度**:每作 45-60 秒(YouTube Shorts / IG Reels 尺寸兼容,直式或 16:9 皆可)
- **平台**:GitHub repo 首頁嵌入 + YouTube unlisted 連結
- **語言**:繁中字幕,無旁白(第一版);第二版可加 TTS 中文旁白

## Pipeline (三作共用)

三支影片同一套產線,參數換掉即可:

```
Xvfb :98 -screen 0 640x480x24
  ├─→ wine explorer /desktop=GAME,640x480 GAME.EXE
  │     ↑ CHT patched EXE + CHT data files
  │
  ├─→ xdotool 送 mouse click 走完 splash → 選劇本 → briefing → 進戰場 → 移動一格
  │
  ├─→ ffmpeg x11grab 25fps H.264 錄 20-30s 實機素材
  │
  └─→ wine 內建 audio driver 錄音 (PulseAudio null sink 或 pipewire null sink)
      ↑ 或 SDL disk audio (若能 hack wine 走 SDL)

    ↓

make_video.sh:
  ├─→ 開頭卡:黑幕 → 遊戲 logo(中文標題)淡入
  ├─→ 段 1 (10s):實機主選單 slow zoom (Ken Burns)
  ├─→ 段 2 (15s):實機選劇本 → 中文劇本名 highlight
  ├─→ 段 3 (15s):實機 briefing → 中文簡報文字
  ├─→ 段 4 (10s):實機戰場 → 移動 → 攻擊 (可有可無)
  ├─→ 段 5 (10s):結尾卡「他說沒有中文版。現在有了。」
  │              + 三作圖標排一排 + GitHub URL
  │
  └─→ 鋪底:遊戲 iMUSE / MIDI 音樂,fade in/out
```

## 三作分別需求

### 影片 1:裝甲元帥 (Panzer General) — 60 秒

**主題**:1994 年的 Win95 元祖,五年後 5D 系列的起點,終於在 30 年後有繁中版。

| 段 | 秒數 | 畫面 | 字幕 |
|---|---|---|---|
| 開場 | 0-5 | 黑幕 → 「1994 SSI Panzer General」小字打字 → 遊戲 splash 淡入 | (無) |
| 主選單 | 5-15 | 中文主選單 slow zoom 到「新遊戲/戰役/情境/教學/選項/離開」按鈕 | *完整中文主選單* |
| 選戰役 | 15-30 | 巴巴羅薩戰役按鈕 hover → click → 中文戰役簡報 (「1941 年 6 月:德軍 300 萬人分三軍集群入侵蘇聯」) | *38 個戰役全繁中* |
| 進戰場 | 30-45 | 六角格戰場鳥瞰 → 步兵單位資訊面板(中文兵種名 + 中文屬性) | *中文兵種名 / 兵種屬性* |
| 結尾 | 45-60 | 遊戲截圖靜態 → 三作 logo 排一排 → 「pg-cht.github.io / wicanr2/pg-cht」 | *SSI 1994 元祖續作 → AG 1995 → PacGen 1997 都有中文版了* |

**素材需求**(已有):
- CHT AppImage 能跑到主選單 ✅
- 主選單截圖 ✅ (docs/screenshots/00_screenshot.png)
- 六角格戰場截圖 ✅ (docs/screenshots/02_screenshot.png)
- 待補:選戰役 → briefing 頁截圖

**capture 腳本**: `tools/video/capture_pg.sh` (待寫,以 `capture_pacgen.sh` 為模板改 game path)

### 影片 2:盟軍將軍 (Allied General) — 60 秒

**主題**:1995 年續作,盟/蘇/英三線 campaign,重點展示 CHT 的「烤在點陣圖裡的 UI」。

| 段 | 秒數 | 畫面 | 字幕 |
|---|---|---|---|
| 開場 | 0-5 | 中文「盟軍元帥」鋼鐵漸層標題卡動畫 (已有 splash 圖) | *ALLIED GENERAL 1995 → 盟軍元帥 繁中化* |
| 主選單 | 5-12 | 中文主選單 zoom | (中文選單) |
| 前後對照 | 12-30 | **前**:英文戰損表 → **後**:中文戰損表 (docs/screenshots/ag_losses_before_after.png 動態 wipe) | *連圖上烤的字都是中文了* |
| 前後對照 2 | 30-42 | **前**:英文購買面板 → **後**:中文購買面板 (docs/screenshots/ag_purchase_before_after.png) | *盟/德/俄三主題全套變體* |
| 實機戰場 | 42-52 | Barbarossa 戰場中文簡報 → 六角格移動 | *中文戰場* |
| 結尾 | 52-60 | 三作 logo + GitHub URL | *完整技術文件見 [docs/allied-general.md]* |

**素材需求**(已有):
- CHT 開頭畫面截圖 ✅ (docs/screenshots/ag_splash_zh.png)
- 3 張前後對照圖 ✅ (buttons/losses/purchase)
- 待補:AG 主選單 + 戰場 CHT 實機

### 影片 3:太平洋元帥 (Pacific General) — 45 秒

**主題**:1997 年 5D 系列末代,29 年後的補完。強調「這款遊戲從沒中文過」。

| 段 | 秒數 | 畫面 | 字幕 |
|---|---|---|---|
| 開場 | 0-5 | 黑幕 → 「1997 SSI/Mindscape · 從未中文化過」小字打字 → 中文標題卡 | *29 年後的補完* |
| Splash | 5-15 | 實機主選單 (docs/screenshots/pacgen_splash.png,capture_pacgen.sh 已有) | *沙灘 / 火砲 / 戰艦 / v1.1* |
| 選劇本 | 15-25 | Load Game 頁 (Iwo Jima 硫磺島插旗照 + 零戰 + 旭日旗 + 33 個劇本繁中名) | *硫磺島 / 中途島 / 瓜達康納爾 / 雷伊泰灣* |
| 劇本簡報 | 25-35 | Briefing 頁繁中簡報 (「1945-02:美軍第 5 兩棲軍登陸此火山島,栗林忠道中將堅守到底」) | *33 個劇本原創繁中史實敘述* |
| 結尾 | 35-45 | 三作 logo + 「他說沒有中文版。現在有了。」 | *pg-cht/pacgen · v0.2* |

**素材需求**(已有):
- CHT AppImage 主選單截圖 ✅ (/tmp/pg-fixed.png,已在 pacgen/docs 的 hero letter 引用位)
- Load Game 頁截圖 ✅ (/tmp/pg-6s.png)
- capture 腳本 ✅ ([tools/video/capture_pacgen.sh](../tools/video/capture_pacgen.sh))
- 待補:劇本簡報頁截圖 (Briefing screen)

## 素材產出待辦

按此順序做:

1. **實機素材**(每作 20-30s MP4 + audio):
   - [ ] `tools/video/capture_pg.sh` — PG 主選單 → 選 Barbarossa → briefing → 戰場
   - [ ] `tools/video/capture_ag.sh` — AG 主選單 → 選 Torch → briefing → 戰場
   - [x] `tools/video/capture_pacgen.sh` — PacGen 主選單 → Load Game → 劇本頁 (已有,可擴充)

2. **標題卡設計**(每作 1 張 1280x720 PNG):
   - [ ] 開頭卡:黑底 + 遊戲 logo + 「繁中化」金色副標
   - [ ] 結尾卡:三作 logo 橫排 + GitHub URL + 「他說沒有中文版。現在有了。」

3. **合成腳本**(參考 atlantis `make_gameplay_video.sh`):
   - [ ] `tools/video/make_pg_intro.sh`
   - [ ] `tools/video/make_ag_intro.sh`
   - [ ] `tools/video/make_pacgen_intro.sh`

4. **中文字幕**(SRT format,可貼進 YouTube 上傳):
   - [ ] `docs/video/pg-subtitles.srt`
   - [ ] `docs/video/ag-subtitles.srt`
   - [ ] `docs/video/pacgen-subtitles.srt`

## 音樂授權

三作 iMUSE / MIDI 音樂**版權屬於 SSI/Mindscape/Ubisoft**。宣傳片使用需考量:

- **合理使用 (fair use)**:15-30 秒短片段用於介紹 mod 專案,通常判定 fair use
- **保守做法**:改用 CC0 / royalty-free 交響樂替代(freemusicarchive.org, incompetech.com 的 Kevin MacLeod 二戰主題)
- **YouTube Content ID**:iMUSE 曲目可能觸發 ID match → YouTube 自動廣告分潤給版權方,不下架但也不推薦

**建議 v1 用 royalty-free、v2 若真要用原曲則加免責註記**。

## 技術決策

- **音訊採集**:Xvfb 環境下 wine 通常有 audio driver 問題。方案:
  - **方案 A**:wine 設 `WINE_AUDIO_DRIVER=alsa` + pulseaudio null sink 錄音
  - **方案 B**:遊戲跑 host X (:1) 而非 Xvfb,用 pactl 錄 default sink → ffmpeg 剪
  - **方案 C**:先做無聲版,後製再貼音樂(最簡)
- **解析度**:遊戲 native 640x480,直接錄可拉 2x 到 1280x960 (nearest scale) 或 3x 到 1920x1440
- **輸出**:1080p MP4 H.264 + AAC,YouTube 標準;GitHub 建議也放個 WebM VP9 版體積更小
- **字幕**:燒進影片 (ffmpeg subtitles filter) + 提供 SRT 檔給 YouTube CC

## 拍攝順序

建議先做 PacGen (工具最新、素材已備) → AG (前後對照最戲劇性) → PG (元祖總結)。

三支同一個 pipeline 產出後,再合成一支 90 秒「系列合輯」影片,首頁 pin 用。

## 相關

- 參考 pipeline:[`~/indian_jones/atlantis/scripts/capture_gameplay_video.sh`](file:///home/anr2/indian_jones/atlantis/scripts/capture_gameplay_video.sh) + `make_gameplay_video.sh`
- headless 錄影工具:[`tools/video/capture_pacgen.sh`](../tools/video/capture_pacgen.sh)
- CHT 心得專欄:[`pacgen/docs/`](../pacgen/docs/)(每篇心得文末的「金句」可當字幕素材)
