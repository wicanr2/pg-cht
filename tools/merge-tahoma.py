#!/usr/bin/env python3
"""把 Microsoft Tahoma(只有西文 glyph)與 MoeStandardSong(完整 CJK glyph)merge,
產出一個 face name 仍叫 Tahoma、含 CJK fallback glyph 的字體,放進 wine prefix。

策略:
  1. 載入兩個來源字體
  2. 從 MoeStandardSong subset 出 *只含 CJK*(Tahoma cmap 沒有的 codepoint)的 .ttf
  3. 用 fontTools.merge.Merger 合併
  4. 改 fontRevision = 32767.99,確保贏過 /usr/share/wine/fonts/tahoma.ttf
"""
import shutil, sys
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter
from fontTools.merge import Merger

TAHOMA_SRC   = Path("/home/anr2/game/tahoma.ttf")
MOE_SRC      = Path("/usr/share/fonts/truetype/moe/MoeStandardSong.ttf")
FONTS        = Path.home() / ".wine-pgcht/drive_c/windows/Fonts"
OUT_REG      = FONTS / "tahoma.ttf"
OUT_BOLD     = FONTS / "tahomabd.ttf"

TMP          = Path("/tmp/tahoma_merge")
TMP.mkdir(parents=True, exist_ok=True)

# ---- step 1: 找出 Tahoma 已有 / 需要新增的 codepoint
tahoma = TTFont(str(TAHOMA_SRC))
tahoma_cps = set(tahoma.getBestCmap().keys())

moe = TTFont(str(MOE_SRC))
moe_cps = set(moe.getBestCmap().keys())

needed_cps = sorted(moe_cps - tahoma_cps)  # MoE 有、Tahoma 沒有 → CJK 與符號
print(f"Tahoma cmap: {len(tahoma_cps)}  MoE cmap: {len(moe_cps)}  to add: {len(needed_cps)}")

# ---- step 2: subset MoeStandardSong 只留需要的 codepoint
moe_sub_path = TMP / "moe_subset.ttf"
moe2 = TTFont(str(MOE_SRC))
subs = Subsetter()
subs.populate(unicodes=needed_cps)
subs.subset(moe2)
# 改 family name 為 Tahoma,避免 merge 時被視為兩個 family
for rec in list(moe2["name"].names):
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
moe2.save(str(moe_sub_path))
print(f"  subset 寫入 {moe_sub_path}  size={moe_sub_path.stat().st_size:,}")

# ---- step 3: merge
merged_path = TMP / "tahoma_merged.ttf"
merger = Merger()
font = merger.merge([str(TAHOMA_SRC), str(moe_sub_path)])
font.save(str(merged_path))
print(f"  merged 寫入 {merged_path}  size={merged_path.stat().st_size:,}")

# ---- step 4: 拉 fontRevision,確保贏過系統 Tahoma
m = TTFont(str(merged_path))
m["head"].fontRevision = 32767.99
# 把 OS/2.ulCodePageRange1 補上 Big5 bit
os2 = m["OS/2"]
os2.ulCodePageRange1 |= (1 << 20)   # CP950 ChineseBig5
os2.ulCodePageRange1 |= (1 << 18)   # CP936 GBK (bonus)
m.save(str(merged_path))

# 確認
m2 = TTFont(str(merged_path))
final_cmap = m2.getBestCmap()
print(f"  最終 cmap size = {len(final_cmap)}")
print(f"  has 檔/案/裝/中/文/繁 = "
      f"{0x6a94 in final_cmap}/{0x6848 in final_cmap}/{0x88dd in final_cmap}/"
      f"{0x4e2d in final_cmap}/{0x6587 in final_cmap}/{0x7e41 in final_cmap}")
fam = [r.toUnicode() for r in m2["name"].names if r.nameID == 1 and r.platformID == 3][:1]
print(f"  family = {fam}, fontRevision = {m2['head'].fontRevision}")

# ---- step 5: 放進 prefix (覆蓋之前的 CJK 假 Tahoma)
FONTS.mkdir(parents=True, exist_ok=True)
shutil.copy(merged_path, OUT_REG)
# Bold:暫時也用同一份(沒 Tahoma Bold 就用同字體,fonttools 改 weight)
import os
os.chmod(OUT_BOLD, 0o644) if OUT_BOLD.exists() else None
shutil.copy(merged_path, OUT_BOLD)
b = TTFont(str(OUT_BOLD))
b["OS/2"].usWeightClass = 700
b["OS/2"].fsSelection = (b["OS/2"].fsSelection | 0x20) & ~0x40
b["head"].macStyle |= 0x01
# subfamily / full → Bold
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

print(f"\n寫入 {OUT_REG} ({OUT_REG.stat().st_size:,} bytes)")
print(f"寫入 {OUT_BOLD} ({OUT_BOLD.stat().st_size:,} bytes)")
