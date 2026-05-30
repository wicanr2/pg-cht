# AG 執行期 UI 補完 (2026-05-30)

接續 AG.EXE (2,167,611 bytes, 同 §AG 版本指紋) 的中文化。本檔記錄四塊「執行期才看得到」的 UI:
回合/簡報畫面內嵌字串、任務簡報 RT_STRING、裝備名稱格式、**戰鬥介面陣營配色選擇 bug**。
所有 offset 為 **file offset**(除非註明 VA)。

## 0. 反組譯位址換算(務必先讀)

分析時餵給 capstone 的「位址」= **file_offset + 0xC00**(方便用的基準,**不是真 VA**)。
- 由分析位址回推 file offset:`file = addr − 0xC00`(例:classify「0x962bb」→ file `0x956bb`)。
- 真 VA:`.text VA = file_offset + 0x400C00`(ImageBase 0x400000)。
- `.data VA → file`:`file = VA − 0x42EE00`(即 `VA − 0x5e8000 + 0x1b9200`)。

---

## 1. ★戰鬥介面陣營配色選擇 — 修正 SKILL.md 舊結論★

舊 SKILL/ag-scenario-menu 把 **Table A getter @file `0x956BB`** 標為「未用(顯示+lookup 都不是)」。
**錯**:它就是**戰鬥介面配色(r/g/a 三套主題)的選擇器** classify。

介面點陣圖以前綴命名三套:`r*`=俄(ru)、`g*`/`ge*`=德、`a*`/`al*`=盟(美/英),
記憶體固定順序 ru,ge,al(例 `rinfowin/ginfowin/ainfowin`、`rmapup/gmapup/amapup`、`ruupmain/geupmain/alupmain`)。

- **主題全域** `[VA 0x5f1b34]`:0=ru、1=ge、2=al(經實機截圖確認 **theme0=ru**)。
- **classify** @file `0x956bb`:把目前戰役名稱對兩張 Big5 指標表做 strcmp。
  - loop1:8 筆,ptr 表 @VA `0x5f1660`(file `0x1c2860`)→ 命中回 **0**(bucket0,北非)。
  - loop2:14 筆,ptr 表 @VA `0x5f1708`(file `0x1c2908`)→ 命中回 **1**(bucket1,西線)。
  - 都沒中 → 回 **2**(其餘/俄戰役)。
- **setter** @file `0x95961`:先看德軍 flag `[0x5f1b54]`,非 0 → 直接存 theme=1(ge,德軍走此路,**不經 switch**);否則 `bucket=classify()` 再進 switch。
- **switch store 點**(原始英文 = 我 session 前 = 完全相同):
  - `0x9599d`:`mov [0x5f1b34], 0`(bucket0/1 → 走這 → theme0=ru)
  - `0x959ac`:`mov [0x5f1b34], 2`(bucket2 → 走這 → theme2=al)

### Bug 與修法
分類表內容是**北非/西線=盟軍戰役名**(見下),命中 → bucket0/1 → **theme0=ru** → 美/英戰場顯示**俄配色**(德軍正常因走 flag)。映射顛倒。
**修法 = 對調兩個 store 立即值**(8 byte 內,已 commit,備份 `AG.EXE.pretheme`):
- `0x9599d+6`:`00 00 00 00` → `02 00 00 00`(bucket0/1 盟軍 → theme2=al)
- `0x959ac+6`:`02 00 00 00` → `00 00 00 00`(bucket2 俄/其餘 → theme0=ru)
驗證:`mov [0x5f1b34],2` @0x9599d、`mov [0x5f1b34],0` @0x959ac。德軍 flag 路徑(@0x96581 `mov [..],1`)不動。

### 分類表內容(Big5,前 session 已譯;**我未動**)
- table-0(北非,→bucket0):西迪巴拉尼/艾季拉/十字軍/馬爾薩布雷加/加查拉/黎波里/阿拉曼/開羅
- table-1(西線,→bucket1):火炬/凱賽林/馬雷斯線/突尼斯/西西里/安齊奧/朱比特/霸王行動/眼鏡蛇/默茲河/摩澤爾/進軍萊茵河/魯爾/德國本土

**覆蓋限制**:盟軍配色只認這 22 個戰役名。**不在表內的盟軍關卡 → bucket2 → 俄配色**。
要讓某盟軍關卡走盟軍配色,得把它的戰役名加進其中一張表(strcmp 來源 = 戰役物件名,非 MAPNAMES;操作名如「火炬/霸王行動」不在 MAPNAMES,只在此 .data 表)。

---

## 2. 回合/開戰畫面內嵌字串(Big5,原地翻譯)

備份 `AG.EXE.preturn`。標籤(回合/天氣/地面/剩餘)走 RT_STRING 已譯;**值**走以下內嵌表:

| 項目 | file off | 槽長 | 譯文 |
|---|---|---|---|
| 天氣 Clear/Overcast/Raining/Snowing | `0x1c3a5c`/`64`/`70`/`78` | 8/12/8/8 | 晴朗/陰天/下雨/下雪 |
| 地面 Dry/Muddy/Frozen | `0x1c3a80`/`84`/`8c` | 4/8/8 | 乾/泥濘/結冰 |
| 陣營 Allied/Axis | `0x1c3adc`/`0x1c3ae4` | 8/8 | 盟軍/軸心 |
| 月份 January..December | `0x1c781c` 起 stride **0x14**,slot1..12 | 20 | 一月..十二月(slot0="Error" 不譯) |

★**踩雷**:`0x1c3a5c` 上方/附近的**小寫**字串(`dry/mud/sno/clear`@`0x1c3a34`、`rainsno/snomud/overcsno/clearsno`@`0x1c3a9c`-`0x1c3ad0`)是**地形貼圖檔名**,經 `"%s%s"`@`0x1c3a94` 組檔名 + strcmp `0x40508d`——**絕不翻譯**。只翻**大寫顯示字**(已反組譯確認 turn-header renderer @ ~`0x4a40xx` 用大寫做 text-draw)。
日期格式 `"%s %d, 19%d"` @.rdata `0x1cb280`/`0x1cb294`(月名+日+年);中文呈現為「十二月 9, 1940」。

---

## 3. ★任務簡報 RT_STRING — 兩個致命踩雷★

AG 長簡報 = **RT_STRING(資源 type 6)** bundle,每 bundle 16 字串,UTF-16LE,**長度前綴(u16 wLen,非 NUL 結尾)**。共 76 bundle / 1216 字串(.rsrc `0x1D2800` 起)。
一個劇本簡報 = 連續數個 string ID:日期字串(`"12 May 1942\n"`)、之後**一句一個 slot**,段落間以 **`' '`(單一空格)字串當空行分隔**。

- **踩雷 A(排版)**:前 session 為保持 wLen 不變,把較短的中文用**大量尾端空格**補滿(某句 58 字 + 173 空格)。遊戲自動換行時這些空格把字推到右邊界 → 明顯怪異斷行/大空洞。
- **踩雷 B(重複,最隱蔽)**:把**所有**尾端空格剪光,會把當「空行」用的 `' '` 變成 **空字串(wLen=0)**。簡報組字器遇 wLen=0 會**重用上一段 buffer → 回顯上一句**。1 句 + 4 個空 slot = 畫面顯示**5 次**同句(實際吻合)。

### 正解(已 commit,備份 `AG.EXE.prebrief` / `.prebrief2`)
把**每個字串的尾端空格數還原成與英文原版 `AG.EXE.bak` 相同**:
- `new = chinese.rstrip(' ') + (' ' × 英文原字串尾端空格數)`
- 句子 → 0 尾端空格(靠遊戲自動換行,如英文);`' '` 空行 → 保留 1 空格。
- 這同時解掉 A(去掉長 padding)與 B(空行不變空字串)。

### RT_STRING 就地重打包(不動 PE 資源目錄)
因為只會**變短**:把該 bundle 的 16 字串重新打包(每串 `u16 wLen + UTF-16LE`)寫回原 file offset、**尾端補零**,**保持資源 data-entry 的 Size 不變**(遊戲讀滿 16 串就停,尾端忽略)。無需改 .rsrc 目錄、無需重排。`assert 新長度 ≤ 原 dSize`。

★另注:字串內**孤立 CR(0x000D)是原版格式**(英文 `.bak` 也有 12 個),**不要**清掉(會誤砍原本的軟換行)。

---

## 4. PANZEQUP.EQP 記錄格式 + 裝備名縮短

(細部補 file-formats.md)記錄 **50 byte (0x32)**,名稱欄 **20 byte**,落在 lattice(名稱 offset ≡ 首筆、stride 50;record0="RESERVED"/"保留")。本 EXE 共 438 筆。
名稱欄**內含國名前綴**(英文 `US `/`GE `/`IT `/`GB `/`ST `/`AF `/`FFR `/`FPO `…;德軍本土無前綴)。前 session 已譯為 `美國 /英國 /蘇聯 /義大利 ` 等(2 字 + 空格)→ 偏長甚至被截斷。

**縮短規則**(備份 `PANZEQUP.EQP.preshort`):
- 國名 → **1 字**並去掉其後空格:美國→美、英國→英、蘇聯→蘇、義大利→義、法國/自由法國→法、荷蘭→荷、比利時→比、保加利亞→保、匈牙利→匈、羅馬尼亞→羅、南斯拉夫→南、希臘→希、芬蘭→芬(longest-first 比對開頭)。
- **刪重複英文機名尾碼**:當名稱含中文且另有「含數字的型號 token」時,刪掉最後一個「純英文字母(≥2、**非羅馬數字**)」token。例:`美野馬 P51B Mustg`→`美野馬 P51B`、`美空中堡壘B17F FF`→`美空中堡壘B17F`。
- **保留**:羅馬數字變體(`Spit IX`)、含數字型號代碼、英文前綴 `AF`/`FPO`(英文可留);德軍裝備原本就短,不動。
- 收斂多餘空白。每筆 Big5 ≤ 20 byte,清空原欄再寫 + NUL 補滿。

---

## 5. 兵種類別名修正
`水平轟炸機`(Level Bomber)@file `0x1c319c`(10 byte)→ `戰略轟炸機`(同長覆寫)。旁邊 `戰術轟炸機`@`0x1c3188` 正確不動。

## 6. ★破解者隱藏簽名(reversed + XOR 0xFF)— grep 找不到的原因★
Lite 重打包者把自己的 email `raywolf@chuvashia.ru` 藏進 EXE,顯示在**狀態列中央 line-1**(hover **未命名格子**的「地名」欄;hover「無法移動的位置」顯示的也是同一欄)。
**為何任何文字搜尋都找不到**(明文/反向/UTF-16/單 byte XOR·ADD·SUB/mov 子序列 全 0):blob 以 **反向儲存 + 逐 byte XOR 0xFF** 雙重編碼。
- 解碼器 @VA `0x43dd7c`(file `0x3d17c`):`esi=0x43dd7a`,往回讀 28 bytes,各 `xor 0xFF`,寫入 buffer `0x5ebcf4`(file `0x1bcef4`);buffer 當 status-bar line-1 的 printf format。
- blob:解碼器讀 28B(`out[i] = file[0x3d17a−i] ^ 0xFF`)= `raywolf@chuvashia.ru\0[%d]\0`,但 email 只用到 `out[0..19]`(20 字)+ `out[20]`=null。
- **定位法**:先找狀態列座標 format(line-2 `"%s (%d,%d)"` @VA `0x5ebd18`/file `0x1bcf18`),其 caller 即狀態列 renderer;line-1 的「無城名」ELSE 分支(VA `0x4525ea`)call 解碼器後把 buffer 當 format。
- ★★**致命踩雷:blob 尾端 2 byte 與「程式碼」重疊**★★。28B blob 範圍 file `0x3d15f–0x3d17a`,但 `0x3d15f`(=`00`)與 `0x3d160`(=`c3`)其實是**可執行指令**:`call 0x43dda3`(@`0x3d15b`,`e8 43 00 00 00`,`0x3d15f` 是運算元高位)+ `ret`(`0x3d160`)。解碼器把它們當 buffer 尾端沒用到的 `out[26]/out[27]` 讀。**進入戰場時會執行到這段 call+ret**。若整段 28B 全覆寫(尤其把 `0x3d15f/0x3d160` 改掉)→ call 運算元/ret 毀掉 → **一進戰場就崩潰閃退**(我犯過:NEW 用 `ff×16 …` 把前 16 byte 全填 0xff,結果遊戲選單可開、一進關卡就跳出)。純資料只在 `0x3d161` 起。
- **正解修法**(備份 `.premail` / 修正版備份 `.premail2`):**只改字串需要的 13 byte**(`0x3d16e`=null、`0x3d16f–0x3d17a`=Big5×12),**保留 `0x3d15f–0x3d16d` 原樣**(含那 2 個 code byte)。安全 28B 區(file 序)= `00 c3 ff a2 9b da a4 ff 8a 8d d1 9e 96 97 8c` + `ff` + `b5 5a bb 52 2c 52 b0 53 2c 57 13 52`。解出 `原來是個胖仔\0`(止於 `out[12]` null),`out[13..27]` 維持原 email 尾段(在 null 後、不顯示)。驗證:反組譯 `0x3d15b` 仍是 `call 0x43dda3` + `ret`;Big5 無 `0x00`/`0x25` 不會提前截斷或誤判 `%`。

`kilroy was here.`(16-byte **明文**,兩份 @file `0x1bceac`/`0x1bcec0`,其一經 strcmp @VA `0x452364`)→ 改 Big5「盟軍元帥中文版」(14B + NUL pad 至 16,備份 `.prekilroy`)。另有短字串 `kilroy`@`0x1bce30`(緊鄰 `exNilPtr`,6B 放不下中文,保留)。

★**通用教訓**:cracker 簽名常以 reversed / XOR / 多 byte 編碼藏匿以躲過 grep+replace。明文找不到時,測「**反向 + 單 byte XOR**」組合;或直接反組譯顯示處(由座標/狀態列 format string 的 caller 回溯到組字/解碼點),從 buffer 反推編碼。
