#!/usr/bin/env python3
"""apply_2byte_pfp.py — apply the custom-2-byte-encoded UI patches to TXT.PFP.

Unlike patch_pfp_v2.py (which wrote Big5 bytes), every CJK char here is emitted
as the custom dense 2-byte code the draw-loop hook understands. Byte lengths are
preserved (custom code = 2 bytes/char, same as Big5), so offsets/padding are
unchanged and the file size is identical.

Sources:
  translations/pfp_patches_2b.json  — 117 auto patches (already custom-coded)
  hardcoded campaign strings         — encoded here via charmap.json
"""
import sys, json, os

ROOT = "/home/anr2/game/Panzer_General/pg-cht/pacgen"

# section-47 campaign selection strings (were manual Big5 in patch_pfp_v2.py)
CAMPAIGN = [(0x5fdb, 20, "選擇軸心戰役"), (0x5ff1, 22, "選擇盟軍戰役")]

def encode_custom(s, charmap):
    out = bytearray()
    for ch in s:
        lead, trail = charmap[ch]      # KeyError = atlas gap, surfaced loudly
        out += bytes([lead, trail])
    return bytes(out)

def apply(src, patches_json, dst, charmap_path):
    data = bytearray(open(src, "rb").read())
    orig = len(data)
    charmap = json.load(open(charmap_path, encoding="utf-8"))
    patches = json.load(open(patches_json, encoding="utf-8"))["patches"]
    for p in patches:
        off, n = p["abs_offset"], p["orig_len"]
        zb = bytes.fromhex(p["zh_bytes_hex"]); pad = p["pad_spaces"]
        assert len(zb) + pad == n, f"len mismatch {p['en']}"
        data[off:off+n] = zb + b" " * pad
    for off, n, zh in CAMPAIGN:
        zb = encode_custom(zh, charmap); pad = n - len(zb)
        assert pad >= 0, f"campaign too long: {zh}"
        data[off:off+n] = zb + b" " * pad
    assert len(data) == orig, f"size changed {orig}->{len(data)}"
    open(dst, "wb").write(bytes(data))
    print(f"[apply] {len(patches)} UI + {len(CAMPAIGN)} campaign patches, {orig}B preserved -> {dst}")

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "translations/txt_pfp_orig/TXT.PFP")
    pj  = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "translations/pfp_patches_2b.json")
    dst = sys.argv[3]
    cm  = sys.argv[4] if len(sys.argv) > 4 else os.path.join(ROOT, "build/atlas/charmap.json")
    apply(src, pj, dst, cm)
