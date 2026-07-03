#!/usr/bin/env python3
"""reencode_patches.py — transcode existing Big5 patch bytes to the custom dense
2-byte encoding used by the draw-loop hook.

Both encodings are exactly 2 bytes per CJK char, so every patch's byte length,
absolute offset, and pad count are preserved — this is a pure byte-swap. ASCII
bytes (<0x80) pass through unchanged.

Input : pfp_patches.json  (zh_bytes_hex in Big5, from build_pfp_patches.py)
        build/atlas/charmap.json  (char -> [lead, trail])
Output: pfp_patches_2b.json  (zh_bytes_hex in custom codes; same lengths)

A char present in a patch but missing from charmap is a hard error (the atlas
must cover every shipped char) — we report and abort rather than ship a hole.
"""
import json, sys, os

ROOT = "/home/anr2/game/Panzer_General/pg-cht/pacgen"

def transcode_big5_bytes(b5: bytes, charmap: dict, missing: set) -> bytes:
    """Big5 byte string -> custom-code byte string. ASCII passes through."""
    out = bytearray()
    i = 0
    while i < len(b5):
        c = b5[i]
        if c < 0x80:                      # ASCII / space / punctuation kept as-is
            out.append(c); i += 1
            continue
        # Big5 lead byte: consume 2 bytes, decode to char, look up custom code
        pair = b5[i:i+2]
        try:
            ch = pair.decode("big5")
        except Exception:
            ch = None
        if ch and ch in charmap:
            lead, trail = charmap[ch]
            out += bytes([lead, trail])
        else:
            missing.add(ch if ch else pair.hex())
            out += pair                   # leave original (will be caught by report)
        i += 2
    return bytes(out)

def main():
    inp = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "translations/pfp_patches.json")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "translations/pfp_patches_2b.json")
    charmap = json.load(open(os.path.join(ROOT, "build/atlas/charmap.json"), encoding="utf-8"))
    pj = json.load(open(inp, encoding="utf-8"))
    missing = set()
    n = 0
    for p in pj["patches"]:
        b5 = bytes.fromhex(p["zh_bytes_hex"])
        cc = transcode_big5_bytes(b5, charmap, missing)
        assert len(cc) == len(b5), f"length changed! {p['en']}: {len(b5)}->{len(cc)}"
        p["zh_bytes_hex"] = cc.hex()
        p["encoding"] = "custom-dense-2byte"
        n += 1
    if missing:
        print(f"[reencode] ERROR: {len(missing)} chars/pairs not in atlas charmap:")
        print("   ", " ".join(sorted(missing)))
        print("   -> add them to atlas source and rerun build_atlas.py; aborting.")
        sys.exit(1)
    pj["stats"]["encoding"] = "custom-dense-2byte"
    json.dump(pj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[reencode] {n} patches transcoded Big5 -> custom 2-byte (lengths preserved) -> {out}")

if __name__ == "__main__":
    main()
