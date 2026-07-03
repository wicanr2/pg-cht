#!/usr/bin/env python3
"""reencode_file.py — transcode a whole Big5 text file to the custom dense
2-byte codes the draw hook understands. For free-form files (scenario TIT/DES)
that the game reads whole (no length constraint) — ASCII and any non-Big5 bytes
pass through unchanged; Big5 CJK pairs become custom (lead,trail).

  reencode_file.py <in_big5> <out_custom> [charmap.json]
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

def main():
    src, dst = sys.argv[1], sys.argv[2]
    cmpath = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "build/atlas/charmap.json")
    charmap = json.load(open(cmpath, encoding="utf-8"))
    missing = set()
    out = transcode(open(src, "rb").read(), charmap, missing)
    open(dst, "wb").write(out)
    tag = f" [MISSING {len(missing)}: {''.join(sorted(missing))}]" if missing else ""
    print(f"[reencode_file] {os.path.basename(src)} -> {os.path.basename(dst)} ({len(out)}B){tag}")
    return 1 if missing else 0

if __name__ == "__main__":
    sys.exit(main())
