#!/usr/bin/env python3
"""把 Microsoft Tahoma + Source Han Sans Heavy (weight 900) merge,
產出 face name 仍叫 Tahoma 但 CJK 字形是 Heavy 粗體的版本。
regular 與 bold 兩份都用同一個 (Heavy CJK) 作為 fallback。
"""
import shutil
from pathlib import Path
from fontTools.ttLib import TTFont, TTCollection
from fontTools.subset import Subsetter
from fontTools.merge import Merger

TAHOMA_SRC   = Path("/home/anr2/game/tahoma.ttf")
SHS_TTC      = Path.home() / ".wine-pgcht/drive_c/windows/Fonts/sourcehansans.ttc"
SHS_INDEX    = 20   # Source Han Sans Heavy (weight 900)
FONTS        = Path.home() / ".wine-pgcht/drive_c/windows/Fonts"
OUT_REG      = FONTS / "tahoma.ttf"
OUT_BOLD     = FONTS / "tahomabd.ttf"

TMP          = Path("/tmp/tahoma_merge_bold")
TMP.mkdir(parents=True, exist_ok=True)

# ---- step 1: 從 TTC 取 idx=20 (Heavy) 存成獨立 TTF
ttc = TTCollection(str(SHS_TTC))
shs_heavy = ttc.fonts[SHS_INDEX]
shs_heavy_path = TMP / "shs_heavy.ttf"
shs_heavy.save(str(shs_heavy_path))
print(f"[1/4] 從 TTC idx={SHS_INDEX} (Source Han Sans Heavy) 存出 {shs_heavy_path}  "
      f"({shs_heavy_path.stat().st_size:,} bytes)")

# ---- step 2: 找 Tahoma 沒有的 codepoint (Heavy 有的 - Tahoma 有的)
tahoma = TTFont(str(TAHOMA_SRC))
tahoma_cps = set(tahoma.getBestCmap().keys())
shs = TTFont(str(shs_heavy_path))
shs_cps = set(shs.getBestCmap().keys())
needed = sorted(shs_cps - tahoma_cps)
print(f"[2/4] Tahoma={len(tahoma_cps)} cp, Heavy={len(shs_cps)} cp, 要加入 {len(needed)} cp")

# ---- step 3: subset Heavy 只留 CJK,並改 family name 為 Tahoma
shs2 = TTFont(str(shs_heavy_path))
subs = Subsetter()
subs.populate(unicodes=needed)
subs.subset(shs2)
for rec in list(shs2["name"].names):
    if rec.nameID in {1, 4, 6, 16, 17}:
        if rec.nameID == 1 or rec.nameID == 16:
            v = "Tahoma"
        elif rec.nameID == 2 or rec.nameID == 17:
            v = "Regular"
        elif rec.nameID == 4:
            v = "Tahoma"
        elif rec.nameID == 6:
            v = "Tahoma"
        else:
            continue
        rec.string = v.encode("utf-16-be") if rec.platformID == 3 else v.encode("mac-roman", "replace")
shs_sub_path = TMP / "shs_heavy_subset.ttf"
shs2.save(str(shs_sub_path))
print(f"[3/4] subset 寫入 {shs_sub_path}  ({shs_sub_path.stat().st_size:,} bytes)")

# ---- step 4: merge + 拉 fontRevision + 補 OS/2 codepage + 寫進 prefix
merger = Merger()
font = merger.merge([str(TAHOMA_SRC), str(shs_sub_path)])
font["head"].fontRevision = 32767.99
font["OS/2"].ulCodePageRange1 |= (1 << 20)   # CP950 Big5
font["OS/2"].ulCodePageRange1 |= (1 << 18)   # CP936 GBK
merged_path = TMP / "tahoma_merged_bold.ttf"
font.save(str(merged_path))

# 驗證
m = TTFont(str(merged_path))
cmap = m.getBestCmap()
print(f"[4/4] merged cmap={len(cmap)} has_檔={0x6a94 in cmap} has_案={0x6848 in cmap}  "
      f"fontRev={m['head'].fontRevision}")

# 覆蓋進 prefix
for p in (OUT_REG, OUT_BOLD):
    if p.exists():
        import os
        os.chmod(p, 0o644)
shutil.copy(merged_path, OUT_REG)
shutil.copy(merged_path, OUT_BOLD)
# tahomabd.ttf 把 weight/style 標 Bold
b = TTFont(str(OUT_BOLD))
b["OS/2"].usWeightClass = 700
b["OS/2"].fsSelection = (b["OS/2"].fsSelection | 0x20) & ~0x40
b["head"].macStyle |= 0x01
for rec in list(b["name"].names):
    if rec.nameID == 2 or rec.nameID == 17:
        v = "Bold"
    elif rec.nameID == 4:
        v = "Tahoma Bold"
    elif rec.nameID == 6:
        v = "Tahoma-Bold"
    else:
        continue
    rec.string = v.encode("utf-16-be") if rec.platformID == 3 else v.encode("mac-roman", "replace")
b.save(str(OUT_BOLD))

print(f"\n寫入 {OUT_REG}  ({OUT_REG.stat().st_size:,} bytes)")
print(f"寫入 {OUT_BOLD} ({OUT_BOLD.stat().st_size:,} bytes)")
