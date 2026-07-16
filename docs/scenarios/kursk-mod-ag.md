# 盟軍元帥加入 Kursk 庫斯克戰役（issue #4）

在《盟軍元帥》(Allied General) 蘇軍(東線)戰役路線加入 **Kursk 庫斯克(1943-07)**,插在 **哈爾科夫'43 → 第聶伯河** 之間。原版 AG 東線從哈爾科夫'43(1943-02)直接跳到第聶伯河(1943-08),跳過史上最大裝甲會戰;此 mod 補上這一環。**原始裝備 / 修改數值 兩個發佈變體皆已套用。**

## 素材來源與相容性(為何 raw copy 可行)

- Kursk 地圖取自《裝甲元帥》(Panzer General) 的 `SCENARIO/GAME030.SCN`(13408 bytes,地圖內嵌於 SCN,無外部地圖檔),直接放進 AG 成為 `SCENARIO/GAME040.SCN`(byte 相同的 raw copy)。
- **單位天然正確,不需重映**:PG、AG 原始裝備、AG 修改數值 三個 `PANZEQUP.EQP` 都是 **437 records × 50-byte stride、offset 0x34→0x52d8 一致、單位 ID 排序完全相同**(如 id6=ME262、id35=88mm 反戰車砲、id37–40=Pz38(t) 系列)。三者差異只在名稱欄(中文化/縮寫),排序不變。因此 PG SCN 內以 ID 引用的單位,在 AG 兩版都映到同一單位。這正是「原始裝備」變體保留原始 SSI 單位表的設計價值。
- 實機佐證:Kursk 在 AG 內六角地圖 render 正常(草原/森林/河/戰壕/機場、蘇軍紅旗單位,無花屏),開場 **1943-07-05(庫斯克歷史開戰日)、20 回合**,目標城「庫斯克 (18,20)」。

## 引擎接線(AG.EXE + SCENARIO.TDB)

AG 的「劇本名 → `GAME###.SCN`」不靠 TDB 位置,而是 **AG.EXE 內硬編的英文劇本名表(Table B)** + strcmp 迴圈 getter:

- 原始:名陣列 @ file `0x1C2A2C`(39 名)、pointer table @ `0x1C2BB8`;getter B @ VA `0x494DE5`(file `0x941E5`),cap `cmp eax,0x27`(39)。
- **未接線時的崩潰**:直接載入 slot 40 會 `page fault read 00000027(=39) at 00592E27`——英文名表 index 39 越界。
- **修法(pointer table 搬遷,因原 pointer[39] 位置被 Table C 佔用)**:
  - 新 40-entry pointer table 置於 free `.data` @ VA `0x5EED00`(file `0x1BFF00`):複製原 39 pointer + 第 40 個指向新英文字串 `"Kursk\0"` @ file `0x1BFFA0`。
  - repoint 三個 base 參照:getter B `@0x94211`、Function1 `@0x9425C`、Function2 `@0x94935`。
  - campaign getter cap `@0x94201`:`0x27`→`0x28`。
  - 另在中文戰術選單名表 B'(`@0x1BFEE8` → Big5「庫斯克」@`0x1BFEF0`)加第 40 項 + 戰術 grid loop bound `@0x57a94` `0x27`→`0x28`,讓「庫斯克」可在戰術選單單獨遊玩。
- **`SCENARIO.TDB`**(純文字 139-byte 記錄):count header `00000039`→`00000040`;新增 Kursk 記錄(字母序插在 Korsun 與 Lake Balaton 之間):`paint=karkov、大勝→Dniepr、小勝→Dniepr、落敗→Zhitomir、dvps=1500 / mvps=1000 / lspr=500`;並把 `Kharkov '43` 的大勝/小勝 `Dniepr`→`Kursk`(落敗保留 Zhitomir)。
- 東線新鏈:… 哈爾科夫'42 → **哈爾科夫'43 → 庫斯克 → 第聶伯河** → 明斯克 …

## 驗證與殘餘風險(誠實標註)

- **已實機驗證**:AG 完整 render;Kursk 載入不崩、地圖/單位正常;戰術選單顯示 40 個劇本含「庫斯克」;蘇軍戰役正常啟動(patched EXE 未破壞既有流程)。
- **機制驗證(非逐關玩通)**:哈爾科夫'43→庫斯克→第聶伯河 的轉場以三塊獨立驗證替代——TDB 鏈已改對(parse 確認)+ getter B 已能解析 "Kursk"(disasm 確認 cap 40 + 新表含 Kursk)+ GAME040 實機可載入無崩潰;且轉場走的是全部 39 個既有場景共用、已運作的同一機制。未做「從芬蘭 GUI 玩 ~10 場到哈爾科夫'43 再取轉場截圖」(不切實際,且 AG 存檔 `GEN_TEMP.HIS` 含疑似 checksum 不宜盲改跳關)。殘餘風險低。

## 兩變體與備份

- 套用於兩個來源目錄:`AlliedGeneral_CHT_v1.1_原始裝備_portable_20260702/` 與 `AlliedGeneral_CHT_v1.1_portable_20260531/`(各自 `AlliedGeneral_CHT_v1.1/`)。兩版 `AG.EXE`、`SCENARIO.TDB`、`GAME040.SCN` byte 相同,Kursk 內單位各吃該版 `PANZEQUP.EQP` 數值(排序一致故皆正確)。
- 原檔備份:`AG.EXE.pre-kursk-20260716`、`DATA/SCENARIO.TDB.pre-kursk-20260716`。
- 散布套件(`dist-all/` 的 AG 兩版 portable zip + AppImage)已重打包含此 mod;舊版備份 `*.pre-kursk`。
