#!/usr/bin/env python3
"""把 prefix 內 tahoma.ttf / tahomabd.ttf 換成「以教育部標準宋體為底、face name 仍叫 Tahoma」
這樣 PG-cht.exe 呼叫 CreateFont("Tahoma", ...) 拿到的字體就有 CJK glyph。
原 Microsoft Tahoma 改名 tahoma_orig.ttf 留作備份(不被 wine 索引,因為 face name 重複會被 skip)。
"""
import shutil
from pathlib import Path
from fontTools.ttLib import TTFont

SRC      = Path("/usr/share/fonts/truetype/moe/MoeStandardSong.ttf")
FONTS    = Path.home() / ".wine-pgcht/drive_c/windows/Fonts"
TARGETS  = [
    # (檔名, family, style/full, weight, postscript)
    ("tahoma.ttf",   "Tahoma", "Regular", 400, "Tahoma"),
    ("tahomabd.ttf", "Tahoma", "Bold",    700, "Tahoma-Bold"),
]

# 先備份(若還沒備份)
for fname, *_ in TARGETS:
    p = FONTS / fname
    bak = FONTS / (fname + ".microsoft.bak")
    if p.exists() and not bak.exists():
        shutil.copy(p, bak)
        print(f"  備份 {p} → {bak}")

OVERRIDE_IDS = {1, 2, 4, 6, 16, 17}  # family/subfamily/full/postscript/preferred

for fname, family, subfamily, weight, psname in TARGETS:
    dst = FONTS / fname
    shutil.copy(SRC, dst)
    font = TTFont(str(dst))
    name = font["name"]
    for rec in list(name.names):
        if rec.nameID not in OVERRIDE_IDS:
            continue
        if rec.nameID == 1 or rec.nameID == 16:
            v = family
        elif rec.nameID == 2 or rec.nameID == 17:
            v = subfamily
        elif rec.nameID == 4:
            v = f"{family} {subfamily}" if subfamily != "Regular" else family
        elif rec.nameID == 6:
            v = psname
        else:
            continue
        rec.string = v.encode("utf-16-be") if rec.platformID == 3 else v.encode("mac-roman", "replace")
    # OS/2 fsSelection + weight
    os2 = font["OS/2"]
    os2.usWeightClass = weight
    # Bold flag bit 5 (fsSelection)
    if weight >= 700:
        os2.fsSelection = (os2.fsSelection | 0x20) & ~0x40  # 設 BOLD,清 REGULAR
        font["head"].macStyle |= 0x01
    else:
        os2.fsSelection = (os2.fsSelection | 0x40) & ~0x20  # 設 REGULAR,清 BOLD
        font["head"].macStyle &= ~0x01
    font.save(str(dst))
    print(f"  {dst.name}  → family={family!r} subfamily={subfamily!r} weight={weight}")

print("\n完成。")
