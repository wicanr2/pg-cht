#!/usr/bin/env python3
"""build_atlas_pg2.py — build a drawGlyph-compatible HxH CJK atlas (mini-TFONT)
for the PANZER2.EXE draw-loop hook, from an explicit list of test strings.

Atlas layout == PG2 native TFONT (FONTFRA.DAT family):
  [16B header: ver(4) count(4) height=H(4) maxidx(4)]
  [count*4 offset table]  offset[i] = file-relative from atlas base
  [glyph i: u32 width=H][H*H px]   (drawGlyph does font_base + offset[i])
Pixel convention MUST match native FONTFRA: stroke(fg)=0x00, empty(bg)=0xff
(drawGlyph xlatb; xlat[pixel]==0xff => transparent). Verified against 0x41b1a4.

Custom dense 2-byte encoding (both bytes >= 0x80, hook is pure arithmetic):
  dense i -> lead=0x81+i//94, trail=0xA1+i%94 ; hook: dense=(lead-0x81)*94+(trail-0xA1)
The dense map depends ONLY on the char set (sorted by codepoint), not on H/font, so
it is IDENTICAL across every size/face this script has ever produced — the dense-
encoded *.TXT data files never need to be re-touched when H or the font changes.

--- Font size/face history (RE'd + user-decided via a font-size comparison, 2026-07-18) ---
Original shipped recipe (EXE md5 778926f7): H=16, NotoSansCJK-Bold.ttc, TTC face index
left UNSPECIFIED -> PIL defaults to index 0. `fontTools.ttLib.TTCollection` enumeration
of every NotoSansCJK-*.ttc on this box: index 0=JP 1=KR 2=SC 3=TC 4=HK. So the shipped
16px build was quietly rendering with the **Japanese** face, not the Traditional-Chinese
one. For this game's ~1,580-char glossary the two faces are pixel-IDENTICAL for every
Han ideograph; only 3 codepoints differ: 。(U+3002) 、(U+3001) ・(U+00B7) — JP places
them top-left of the cell (kuten convention), TC places them bottom-left (Chinese
convention). Confirmed by rendering both faces and diffing every glossary glyph; see
scratchpad `fontcheck/jp_vs_tc_14px.png` for the visual proof. This is a real (if minor)
localization-fidelity bug, zero-risk to fix (only 3 glyphs' pixels move), so this script
now defaults FONT_INDEX to 3 (TC).
User picked H=14, Noto Sans CJK **Medium** (Bold glyphs at <=14px blur on complex chars
like 驅/戰/籍) from a side-by-side size/weight comparison. That is now this script's
default. `make_release.py` (the older, round-1-only build, superseded by
make_full_release.py) still calls this script with only 2 positional args, so it keeps
the ORIGINAL H=16/Bold/index=0 behaviour verbatim — nothing about its output changes.

Usage: build_atlas_pg2.py <strings.json> <out_dir> [H] [font_ttf] [font_index] [thresh] [ybias]
  strings.json = list of Chinese strings whose chars must be in the atlas.
  H            = glyph cell height in px (default 16, matches the original shipped build)
  font_ttf     = source .ttc/.ttf (default NotoSansCJK-Bold.ttc, matches original)
  font_index   = face index within a .ttc (default 0 = JP face, matches original exactly;
                 the current recommended production value is 3 = Traditional Chinese)
  thresh       = gray>thresh => stroke (default 96)
  ybias        = extra vertical px shift (default 0, + = render glyph lower in cell)
"""
import struct, json, sys, os
from PIL import Image, ImageFont, ImageDraw

H = 16
FONT_TTF = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_INDEX = 0
LEAD0, TRAIL0, TRAILW = 0x81, 0xA1, 94

def is_cjk(c):
    # Formal build: any non-ASCII char that appears in the translated masters needs a
    # glyph (covers CJK ideographs, CJK/fullwidth punctuation, AND stray Latin-1 marks
    # such as U+00B7 middle-dot used in transliterated commander/place names, e.g.
    # "隆美爾" style separators in round-2 briefing prose). Anything < 0x80 stays a
    # single ASCII byte; everything >= 0x80 gets a dense 2-byte atlas glyph.
    # (This widened test was already validated in the round-2 briefings build --
    # a narrower CJK-codepoint-range test misses U+00B7 and aborts encode_master()
    # with "char '·' not in atlas" on files like MALTA.TXT.)
    return ord(c) >= 0x80

def render(ch, fnt, h, thresh, ybias):
    img = Image.new("L", (h, h), 0)
    d = ImageDraw.Draw(img)
    bb = d.textbbox((0, 0), ch, font=fnt)
    w = bb[2]-bb[0]; hh = bb[3]-bb[1]
    x = (h-w)//2 - bb[0]; y = (h-hh)//2 - bb[1] + ybias
    d.text((x, y), ch, fill=255, font=fnt)
    px = bytearray()
    for r in range(h):
        for c in range(h):
            px.append(0x00 if img.getpixel((c, r)) > thresh else 0xff)   # fg=0x00, bg=0xff
    return bytes(px), img

def main():
    strings_path, out = sys.argv[1], sys.argv[2]
    h = int(sys.argv[3]) if len(sys.argv) > 3 else H
    font_ttf = sys.argv[4] if len(sys.argv) > 4 else FONT_TTF
    font_index = int(sys.argv[5]) if len(sys.argv) > 5 else FONT_INDEX
    thresh = int(sys.argv[6]) if len(sys.argv) > 6 else 96
    ybias = int(sys.argv[7]) if len(sys.argv) > 7 else 0
    os.makedirs(out, exist_ok=True)
    strings = json.load(open(strings_path, encoding="utf-8"))
    chars = set()
    for s in strings:
        for c in s:
            if is_cjk(c):
                chars.add(c)
    entries = sorted(chars, key=ord)
    n = len(entries)
    fnt = ImageFont.truetype(font_ttf, h, index=font_index)

    charmap = {}
    glyph_blobs = []
    proof = []
    tsv = ["dense\tlead\ttrail\tchar\tU+"]
    for i, ch in enumerate(entries):
        px, img = render(ch, fnt, h, thresh, ybias)
        lead, trail = LEAD0 + i // TRAILW, TRAIL0 + i % TRAILW
        glyph_blobs.append(struct.pack("<I", h) + px)
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
    atlas += struct.pack("<I", h)
    atlas += struct.pack("<I", max(n-1, 0))
    for o in offsets: atlas += struct.pack("<I", o)
    for g in glyph_blobs: atlas += g

    maxlead = LEAD0 + (max(n-1, 0))//TRAILW
    open(os.path.join(out, "atlas_font.dat"), "wb").write(bytes(atlas))
    json.dump(charmap, open(os.path.join(out, "charmap.json"), "w"), ensure_ascii=False)
    open(os.path.join(out, "code_map.tsv"), "w", encoding="utf-8").write("\n".join(tsv)+"\n")
    json.dump({"count": n, "height": h, "atlas_size": len(atlas), "font": font_ttf,
               "font_index": font_index, "thresh": thresh, "ybias": ybias,
               "LEAD0": LEAD0, "TRAIL0": TRAIL0, "TRAILW": TRAILW,
               "maxlead": maxlead, "table_start": table_start},
              open(os.path.join(out, "atlas_index.json"), "w"), indent=1)
    # proof montage
    cols = 24; rows = (n+cols-1)//cols if n else 1
    sheet = Image.new("L", (cols*h, rows*h), 40)
    for i, im in enumerate(proof):
        sheet.paste(im, ((i % cols)*h, (i//cols)*h))
    sheet.resize((cols*h*3, rows*h*3), Image.NEAREST).save(os.path.join(out, "proof.png"))
    print(f"[atlas] H={h} font={os.path.basename(font_ttf)}#{font_index} thr={thresh} ybias={ybias} "
          f"{n} glyphs, {len(atlas)}B, lead 0x{LEAD0:02x}-0x{maxlead:02x} -> {out}")
    print("[atlas] chars:", "".join(entries))

if __name__ == "__main__":
    main()
