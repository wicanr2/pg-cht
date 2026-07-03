#!/usr/bin/env python3
"""build_atlas.py — Big5 2-byte CJK atlas builder for the draw-loop hook.

Gathers every CHT string in the project, extracts the unique CJK char set,
maps each char to its Big5 2-byte code, renders a 16x16 bitmap glyph, and emits:

  1. atlas.bin        — dense glyph blob: for dense index i, [4B width][width*16 px]
                        (same per-glyph format as TFONT1.DAT glyphs, height 16)
  2. big5_to_dense.tsv — lead trail dense_index char   (the hook's lookup table)
  3. atlas_index.json  — metadata (count, height, ranges)
  4. proof.png         — montage of all glyphs for visual legibility check

The hook (P2/P3) reads a lead byte, consumes the trail byte, computes the dense
atlas index by PURE ARITHMETIC (no lookup table), and blits atlas glyph[dense].
ASCII (<0x80) stays on the original single-byte TFONT path.

Encoding = custom dense 2-byte (NOT raw Big5): dense index i ->
  lead  = LEAD0 + i // TRAILW      (0x81, 0x82, ...)
  trail = TRAIL0 + i % TRAILW      (0xA1 ..)
Both bytes >= 0x80 so no ASCII/control byte is ever ambiguous. The hook inverts:
  dense = (lead - LEAD0) * TRAILW + (trail - TRAIL0)
We regenerate all string patches from source, so re-encoding costs nothing and
buys a table-free hook (just a multiply-add) that fits any small code cave.
"""
import struct, json, glob, os, sys
from PIL import Image, ImageFont, ImageDraw

H = 16
FONT_TTF = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
ROOT = "/home/anr2/game/Panzer_General/pg-cht/pacgen"
OUT = os.path.join(ROOT, "build/atlas")

# custom dense 2-byte encoding parameters (both bytes >= 0x80)
LEAD0 = 0x81
TRAIL0 = 0xA1
TRAILW = 94                 # trail range 0xA1..0xFE = 94 codes; 529 chars -> 6 leads (0x81-0x86)

def dense_to_code(i):
    return (LEAD0 + i // TRAILW, TRAIL0 + i % TRAILW)

def is_cjk(c):
    o = ord(c)
    return (0x4E00 <= o <= 0x9FFF) or (0x3400 <= o <= 0x4DBF) or (0xF900 <= o <= 0xFAFF) or (0x3000 <= o <= 0x303F) or (0xFF00 <= o <= 0xFFEF)

# strings hardcoded in patchers (not in the TSV/JSON sources) — must be in atlas
EXTRA_STRINGS = ["選擇軸心戰役", "選擇盟軍戰役", "開始"]

def gather_chars():
    chars = set()
    # 0) hardcoded strings (campaign selection screen, EXE test signals)
    for s in EXTRA_STRINGS:
        for c in s:
            if is_cjk(c): chars.add(c)
    # 1) pfp_patches.json zh values (UI, already Big5-patched)
    pj = json.load(open(os.path.join(ROOT, "translations/pfp_patches.json")))
    def walk(o):
        if isinstance(o, str):
            for c in o:
                if is_cjk(c): chars.add(c)
        elif isinstance(o, dict):
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(pj)
    # 2) equip glossary
    for line in open(os.path.join(ROOT, "translations/glossary_equip.tsv"), encoding="utf-8"):
        for c in line:
            if is_cjk(c): chars.add(c)
    # 3) scenario titles + briefings
    for fn in ["translations/scenario_titles.tsv", "translations/scenario_briefings_zh.tsv"]:
        for c in open(os.path.join(ROOT, fn), encoding="utf-8").read():
            if is_cjk(c): chars.add(c)
    return chars

def big5(c):
    try:
        b = c.encode("big5")
        if len(b) == 2 and 0x81 <= b[0] <= 0xFE:
            return b[0], b[1]
    except Exception:
        pass
    return None

def render(ch):
    img = Image.new("L", (H, H), 0)
    d = ImageDraw.Draw(img)
    fnt = ImageFont.truetype(FONT_TTF, H)
    bb = d.textbbox((0, 0), ch, font=fnt)
    w = bb[2]-bb[0]; h = bb[3]-bb[1]
    x = (H-w)//2 - bb[0]; y = (H-h)//2 - bb[1]
    d.text((x, y), ch, fill=255, font=fnt)
    px = bytearray()
    for r in range(H):
        for c in range(H):
            px.append(0xff if img.getpixel((c, r)) > 96 else 0x00)
    return bytes(px), img

def main():
    os.makedirs(OUT, exist_ok=True)
    chars = gather_chars()
    # keep only Big5-encodable, sort by big5 code for determinism
    entries = []
    no_big5 = []
    for ch in chars:
        b = big5(ch)
        if b is None:
            no_big5.append(ch)
        else:
            entries.append((b[0], b[1], ch))
    entries.sort()
    print(f"unique CJK chars: {len(chars)}  big5-ok: {len(entries)}  NOT-big5: {len(no_big5)}")
    if no_big5:
        print("  NOT-big5 (need fallback):", "".join(no_big5))

    # build atlas as a drawGlyph-compatible mini-TFONT + custom-code map + proof
    #   TFONT layout: [16B header][count*4 offset table][glyph data]
    #   header = version(4) count(4) height(4) maxidx(4); glyph = [width u32][width*H px]
    #   offset[i] is FILE-RELATIVE (from atlas start) — drawGlyph does font_base+offset[i].
    n = len(entries)
    tsv = ["dense\tlead\ttrail\tbig5_lead\tbig5_trail\tchar\tcodepoint"]
    charmap = {}          # char -> [lead, trail]  (the re-encoder consumes this)
    proof_imgs = []
    glyph_blobs = []
    for i, (b5lead, b5trail, ch) in enumerate(entries):
        px, img = render(ch)
        lead, trail = dense_to_code(i)
        glyph_blobs.append(struct.pack("<I", H) + px)   # width=16, then 16*16 px
        tsv.append(f"{i}\t{lead:02x}\t{trail:02x}\t{b5lead:02x}\t{b5trail:02x}\t{ch}\tU+{ord(ch):04X}")
        charmap[ch] = [lead, trail]
        proof_imgs.append(img)

    table_start = 0x10 + n*4
    offsets = []
    cur = table_start
    for g in glyph_blobs:
        offsets.append(cur); cur += len(g)
    atlas = bytearray()
    atlas += struct.pack("<I", 0x00002e31)          # version tag "1." (matches TFONT1)
    atlas += struct.pack("<I", n)                   # glyph count
    atlas += struct.pack("<I", H)                   # height = 16  -> drawGlyph reads [font+8]
    atlas += struct.pack("<I", n-1)                 # max index
    for o in offsets:
        atlas += struct.pack("<I", o)
    for g in glyph_blobs:
        atlas += g

    maxlead = LEAD0 + (n-1)//TRAILW
    open(os.path.join(OUT, "atlas_font.dat"), "wb").write(bytes(atlas))
    open(os.path.join(OUT, "code_map.tsv"), "w", encoding="utf-8").write("\n".join(tsv)+"\n")
    json.dump(charmap, open(os.path.join(OUT, "charmap.json"), "w"), ensure_ascii=False)
    json.dump({"count": n, "height": H, "glyph_width": H,
               "glyph_stride": 4 + H*H, "not_big5": no_big5,
               "atlas_font_size": len(atlas), "table_start": table_start,
               "encoding": "custom-dense-2byte",
               "LEAD0": LEAD0, "TRAIL0": TRAIL0, "TRAILW": TRAILW,
               "lead_range": [LEAD0, maxlead], "trail_range": [TRAIL0, TRAIL0+TRAILW-1],
               "hook_formula": "dense = (lead-%d)*%d + (trail-%d)" % (LEAD0, TRAILW, TRAIL0)},
              open(os.path.join(OUT, "atlas_index.json"), "w"), ensure_ascii=False, indent=1)
    print(f"atlas_font.dat {len(atlas)}B (TFONT fmt, {n} glyphs, height {H})")
    print(f"custom-dense encoding: lead 0x{LEAD0:02x}-0x{maxlead:02x}, trail 0x{TRAIL0:02x}-0x{TRAIL0+TRAILW-1:02x}")

    # proof montage: 32 cols
    cols = 32; rows = (len(proof_imgs)+cols-1)//cols
    sheet = Image.new("L", (cols*H, rows*H), 40)
    for i, im in enumerate(proof_imgs):
        sheet.paste(im, ((i % cols)*H, (i//cols)*H))
    sheet.resize((cols*H*2, rows*H*2), Image.NEAREST).save(os.path.join(OUT, "proof.png"))
    print(f"proof.png {cols}x{rows} montage -> {OUT}")

if __name__ == "__main__":
    main()
