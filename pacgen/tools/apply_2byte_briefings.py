#!/usr/bin/env python3
"""apply_2byte_briefings.py — byte-length-preserving patch of in-battle word-wrap
briefings in TXT.PFP with custom 2-byte codes.

Briefings are packed in a large block; the game reads each by (offset, len). We
overwrite [offset, len] with the custom-coded Chinese (CJK->2 bytes, \\n->0x0a,
ASCII kept) padded with spaces to exactly `len`, so no downstream offset shifts.
\\n gives explicit line breaks so the word-wrap FILL never has to backtrack for a
space in continuous CJK (which would hit the 'word too long' error path).
"""
import json, sys, os

ROOT = "/home/anr2/game/Panzer_General/pg-cht/pacgen"

def encode(zh, charmap):
    out = bytearray()
    for ch in zh:
        if ch == "\n":
            out.append(0x0a)
        elif ord(ch) < 0x80:
            out.append(ord(ch))
        else:
            out += bytes(charmap[ch])   # KeyError = atlas gap (loud)
    return bytes(out)

def apply(src, dst, charmap_path, briefings_path):
    data = bytearray(open(src, "rb").read())
    orig = len(data)
    charmap = json.load(open(charmap_path, encoding="utf-8"))
    briefings = json.load(open(briefings_path, encoding="utf-8"))
    n = 0
    for b in briefings:
        off, ln = b["offset"], b["len"]
        enc = encode(b["zh"], charmap)
        assert len(enc) <= ln, f"briefing @{off} too long: {len(enc)}>{ln}"
        data[off:off+ln] = enc + b" " * (ln - len(enc))
        n += 1
    assert len(data) == orig, f"size changed {orig}->{len(data)}"
    open(dst, "wb").write(bytes(data))
    print(f"[briefings] {n} briefings patched (byte-length preserved) -> {dst}")

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    cm = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "build/atlas/charmap.json")
    bp = sys.argv[4] if len(sys.argv) > 4 else os.path.join(ROOT, "translations/briefings_zh.json")
    apply(src, dst, cm, bp)
