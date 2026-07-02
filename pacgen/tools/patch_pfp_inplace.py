#!/usr/bin/env python3
"""就地 patch TXT.PFP 內 section 47 (Campaign Selection Screen) 兩條字串,
保持整體 byte length 不變 → PFPDATA.IDX 無需重寫。

用法:
    python3 patch_pfp_inplace.py <source TXT.PFP> <output TXT.PFP>

v0.2.1 只 patch 兩條:
- 0x5fdb: "Select Axis Campaign" (20B) → "選擇軸心戰役" (Big5 12B) + 8 空格
- 0x5ff1: "Select Allied Campaign" (22B) → "選擇盟軍戰役" (Big5 12B) + 10 空格

策略評估:
- ✅ PFP patch 本身 boot OK (fresh source + PFP patch 已驗)
- ⚠️  CHT DES (33 個劇本簡報) 併用會撞 crash (見 06-txt-pfp-inplace-patch.md)
  → v0.2.1 只 ship: PFP patch + CHT TIT (劇本標題),不 ship CHT DES
- v0.3 目標:擴充 patch 到其他 UI 節區 (main menu、buttons、weather 等)
"""
import sys

PATCHES = [
    # (file_offset, orig_byte_len, chinese_replacement)
    (0x5fdb, 20, '選擇軸心戰役'),
    (0x5ff1, 22, '選擇盟軍戰役'),
]

def apply(src_path, dst_path):
    data = bytearray(open(src_path, 'rb').read())
    orig_size = len(data)
    for off, n, zh in PATCHES:
        zh_bytes = zh.encode('big5')
        pad = n - len(zh_bytes)
        assert pad >= 0, f"CJK too long: {zh!r} = {len(zh_bytes)}B > {n}B slot"
        data[off:off + n] = zh_bytes + b' ' * pad
        print(f"  0x{off:x}: {zh!r} + {pad} spaces = {n}B")
    open(dst_path, 'wb').write(bytes(data))
    assert len(data) == orig_size, f"size changed! {orig_size} → {len(data)}"
    print(f"OK: {orig_size} bytes preserved → {dst_path}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: patch_pfp_inplace.py <src TXT.PFP> <dst TXT.PFP>")
        sys.exit(1)
    apply(sys.argv[1], sys.argv[2])
