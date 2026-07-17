#!/usr/bin/env python3
"""build_atlas_pg2.py — build a drawGlyph-compatible 16x16 CJK atlas (mini-TFONT)
for the PANZER2.EXE draw-loop hook, from an explicit list of test strings.

Atlas layout == PG2 native TFONT (FONTFRA.DAT family):
  [16B header: ver(4) count(4) height=16(4) maxidx(4)]
  [count*4 offset table]  offset[i] = file-relative from atlas base
  [glyph i: u32 width=16][16*16 px]   (drawGlyph does font_base + offset[i])
Pixel convention MUST match native FONTFRA: stroke(fg)=0x00, empty(bg)=0xff
(drawGlyph xlatb; xlat[pixel]==0xff => transparent). Verified against 0x41b1a4.

Custom dense 2-byte encoding (both bytes >= 0x80, hook is pure arithmetic):
  dense i -> lead=0x81+i//94, trail=0xA1+i%94 ; hook: dense=(lead-0x81)*94+(trail-0xA1)
Usage: build_atlas_pg2.py <strings.json> <out_dir>
  strings.json = list of Chinese strings whose chars must be in the atlas.
"""
import struct, json, sys, os
from PIL import Image, ImageFont, ImageDraw

H = 16
FONT_TTF = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
LEAD0, TRAIL0, TRAILW = 0x81, 0xA1, 94

def is_cjk(c):
    o = ord(c)
    return (0x4E00 <= o <= 0x9FFF) or (0x3400 <= o <= 0x4DBF) or (0xF900 <= o <= 0xFAFF) \
        or (0x3000 <= o <= 0x303F) or (0xFF01 <= o <= 0xFF5E)

def render(ch, fnt):
    img = Image.new("L", (H, H), 0)
    d = ImageDraw.Draw(img)
    bb = d.textbbox((0, 0), ch, font=fnt)
    w = bb[2]-bb[0]; h = bb[3]-bb[1]
    x = (H-w)//2 - bb[0]; y = (H-h)//2 - bb[1]
    d.text((x, y), ch, fill=255, font=fnt)
    px = bytearray()
    for r in range(H):
        for c in range(H):
            px.append(0x00 if img.getpixel((c, r)) > 96 else 0xff)   # fg=0x00, bg=0xff
    return bytes(px), img

def main():
    strings_path, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    strings = json.load(open(strings_path, encoding="utf-8"))
    chars = set()
    for s in strings:
        for c in s:
            if is_cjk(c):
                chars.add(c)
    entries = sorted(chars, key=ord)
    n = len(entries)
    fnt = ImageFont.truetype(FONT_TTF, H)

    charmap = {}
    glyph_blobs = []
    proof = []
    tsv = ["dense\tlead\ttrail\tchar\tU+"]
    for i, ch in enumerate(entries):
        px, img = render(ch, fnt)
        lead, trail = LEAD0 + i // TRAILW, TRAIL0 + i % TRAILW
        glyph_blobs.append(struct.pack("<I", H) + px)
        charmap[ch] = [lead, trail]
        proof.append(img)
        tsv.append(f"{i}\t{lead:02x}\t{trail:02x}\t{ch}\tU+{ord(ch):04X}")

    table_start = 0x10 + n*4
    offsets = []
    cur = table_start
    for g in glyph_blobs:
        offsets.append(cur); cur += len(g)
    atlas = bytearray()
    atlas += struct.pack("<I", 0x00002e31)   # "1.\0\0" version tag, matches FONTFRA
    atlas += struct.pack("<I", n)
    atlas += struct.pack("<I", H)
    atlas += struct.pack("<I", max(n-1, 0))
    for o in offsets: atlas += struct.pack("<I", o)
    for g in glyph_blobs: atlas += g

    maxlead = LEAD0 + (max(n-1, 0))//TRAILW
    open(os.path.join(out, "atlas_font.dat"), "wb").write(bytes(atlas))
    json.dump(charmap, open(os.path.join(out, "charmap.json"), "w"), ensure_ascii=False)
    open(os.path.join(out, "code_map.tsv"), "w", encoding="utf-8").write("\n".join(tsv)+"\n")
    json.dump({"count": n, "height": H, "atlas_size": len(atlas),
               "LEAD0": LEAD0, "TRAIL0": TRAIL0, "TRAILW": TRAILW,
               "maxlead": maxlead, "table_start": table_start},
              open(os.path.join(out, "atlas_index.json"), "w"), indent=1)
    # proof montage
    cols = 24; rows = (n+cols-1)//cols if n else 1
    sheet = Image.new("L", (cols*H, rows*H), 40)
    for i, im in enumerate(proof):
        sheet.paste(im, ((i % cols)*H, (i//cols)*H))
    sheet.resize((cols*H*3, rows*H*3), Image.NEAREST).save(os.path.join(out, "proof.png"))
    print(f"[atlas] {n} glyphs, {len(atlas)}B, lead 0x{LEAD0:02x}-0x{maxlead:02x} -> {out}")
    print("[atlas] chars:", "".join(entries))

if __name__ == "__main__":
    main()
