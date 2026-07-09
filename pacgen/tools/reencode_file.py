#!/usr/bin/env python3
"""reencode_file.py — transcode a whole Big5 text file to the custom dense
2-byte codes the draw hook understands. For free-form files (scenario TIT/DES)
that the game reads whole (no length constraint) — ASCII and any non-Big5 bytes
pass through unchanged; Big5 CJK pairs become custom (lead,trail).

  reencode_file.py <in_big5> <out_custom> [charmap.json] [--wrap-px N]

--wrap-px N: insert explicit newlines so each display line is <= N pixels wide
  (CJK/full-width glyph = 16px, ASCII = 8px). The word-wrap module only hooks the
  RENDER loop (draws CJK at 16px) but NOT the FILL loop (measures wrap width with
  the original narrow byte metrics), so without pre-set breaks CJK briefings pack
  too many glyphs per line and spill past the box. FILL honours '\n' (0x0a), so
  pre-breaking sidesteps both the overflow and the space-backtrack error path.
"""
import sys, json, os

ROOT = "/home/anr2/game/Panzer_General/pg-cht/pacgen"

def transcode(b5: bytes, charmap: dict, missing: set) -> bytes:
    out = bytearray(); i = 0
    while i < len(b5):
        c = b5[i]
        if c < 0x80:
            out.append(c); i += 1; continue
        pair = b5[i:i+2]
        try:
            ch = pair.decode("big5")
        except Exception:
            ch = None
        if ch and ch in charmap:
            out += bytes(charmap[ch]); i += 2
        elif ch is not None and len(pair) == 2:
            missing.add(ch); out += pair; i += 2      # unknown CJK: leave, report
        else:
            out.append(c); i += 1                      # stray high byte: passthrough
    return bytes(out)

def wrap_big5(b5: bytes, max_px: int) -> bytes:
    """Insert 0x0a so each rendered line's width <= max_px. Break only after a
    full-width char or an ASCII space, never inside an ASCII word (e.g. "1944")."""
    out = bytearray(); w = 0; brk = None; i = 0
    def tail_width(buf, start):
        ww = 0; j = start
        while j < len(buf):
            ww += 8 if buf[j] < 0x80 else 16
            j += 2 if buf[j] >= 0x80 else 1
        return ww
    while i < len(b5):
        c = b5[i]
        if c == 0x0a:                       # honour existing breaks, reset
            out.append(c); i += 1; w = 0; brk = None; continue
        cw = 8 if c < 0x80 else 16
        if w + cw > max_px and brk is not None:   # break BEFORE the char that would spill
            nl = brk
            while nl > 0 and out[nl-1] == 0x20:    # drop trailing spaces at the break
                nl -= 1
            out.insert(nl, 0x0a)
            w = tail_width(out, nl + 1)
            brk = None
        if c < 0x80:
            out.append(c); i += 1; w += 8
            if c == 0x20:
                brk = len(out)              # may break after a space
        else:
            out += b5[i:i+2]; i += 2; w += 16
            brk = len(out)                  # may break after a full-width char
    return bytes(out)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    src, dst = args[0], args[1]
    cmpath = args[2] if len(args) > 2 else os.path.join(ROOT, "build/atlas/charmap.json")
    wrap_px = 0
    for a in sys.argv[1:]:
        if a.startswith("--wrap-px"):
            wrap_px = int(a.split("=", 1)[1]) if "=" in a else int(sys.argv[sys.argv.index(a)+1])
    charmap = json.load(open(cmpath, encoding="utf-8"))
    missing = set()
    data = open(src, "rb").read()
    if wrap_px:
        data = wrap_big5(data, wrap_px)
    out = transcode(data, charmap, missing)
    open(dst, "wb").write(out)
    tag = f" [MISSING {len(missing)}: {''.join(sorted(missing))}]" if missing else ""
    wtag = f" [wrap {wrap_px}px]" if wrap_px else ""
    print(f"[reencode_file] {os.path.basename(src)} -> {os.path.basename(dst)} ({len(out)}B){wtag}{tag}")
    return 1 if missing else 0

if __name__ == "__main__":
    sys.exit(main())
