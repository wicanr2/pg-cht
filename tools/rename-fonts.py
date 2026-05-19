#!/usr/bin/env python3
"""把 MoeStandardSong.ttf 複製成 mingliu / pmingliu / sserif (內含中文 glyph)
並重寫 name table,讓 Wine 看到對應的 face name。
"""
import shutil
from pathlib import Path
from fontTools.ttLib import TTFont

SRC = Path("/usr/share/fonts/truetype/moe/MoeStandardSong.ttf")
OUT_DIR = Path.home() / ".wine-pgcht/drive_c/windows/Fonts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# (檔名, family, full name, postscript)
TARGETS = [
    ("mingliu.ttf",   "MingLiU",   "MingLiU",   "MingLiU"),
    ("pmingliu.ttf",  "PMingLiU",  "PMingLiU",  "PMingLiU"),
    ("simsun.ttf",    "SimSun",    "SimSun",    "SimSun"),
    ("nsimsun.ttf",   "NSimSun",   "NSimSun",   "NSimSun"),
    # 把 Win 老 raster face name 也覆寫成 vector 含中文
    ("ssserife.ttf",  "MS Sans Serif", "MS Sans Serif Regular", "MS-Sans-Serif"),
    ("system.ttf",    "System",    "System Regular", "System"),
]

# 對應的 ttLib name record: (nameID, platformID, platEncID, langID) → value
# 覆蓋這些 nameID 的所有條目:1=family, 2=style, 3=unique, 4=full, 6=postscript,
# 16=preferred family, 17=preferred style, 18=mac full
ID_TO_OVERRIDE = {1, 4, 6, 16}

for fname, family, fullname, psname in TARGETS:
    dst = OUT_DIR / fname
    shutil.copy(SRC, dst)
    font = TTFont(str(dst))
    name_table = font["name"]
    for rec in list(name_table.names):
        if rec.nameID not in ID_TO_OVERRIDE:
            continue
        if rec.nameID == 1 or rec.nameID == 16:
            new_str = family
        elif rec.nameID == 4:
            new_str = fullname
        elif rec.nameID == 6:
            new_str = psname
        else:
            continue
        rec.string = new_str.encode("utf-16-be") if rec.platformID == 3 else new_str.encode("mac-roman", "replace")
    font.save(str(dst))
    print(f"  {dst.name}  → family={family!r}, full={fullname!r}, postscript={psname!r}")

print(f"\n寫入位置: {OUT_DIR}")
