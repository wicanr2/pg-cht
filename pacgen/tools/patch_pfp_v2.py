#!/usr/bin/env python3
"""v2:套用 build_pfp_patches.py 產生的 pfp_patches.json 到原版 TXT.PFP,
產出全 CHT patched TXT.PFP (byte-length preserving)。

用法:
    python3 patch_pfp_v2.py <原版 TXT.PFP> <patches.json> <輸出 TXT.PFP>

驗證:
- 每條 patch 檢查 zh_bytes + pad = orig_len
- 檔案總長度不變
- 各 patch 的 abs_offset 之前段落原封不動 (無 overwrite 相鄰字串)
"""
import sys, json

def apply(src, patches_json, dst):
    data = bytearray(open(src, 'rb').read())
    orig_size = len(data)
    j = json.load(open(patches_json, encoding='utf-8'))
    patches = j['patches']
    print(f"applying {len(patches)} patches...")
    for p in patches:
        off = p['abs_offset']
        n = p['orig_len']
        zh_bytes = bytes.fromhex(p['zh_bytes_hex'])
        pad = p['pad_spaces']
        assert len(zh_bytes) + pad == n, f"length mismatch: {p!r}"
        new = zh_bytes + b' ' * pad
        data[off:off + n] = new
    # patch section 47 (Campaign Selection Screen) - v0.2.1 手動的兩條
    campaign_patches = [
        (0x5fdb, 20, '選擇軸心戰役'),
        (0x5ff1, 22, '選擇盟軍戰役'),
    ]
    for off, n, zh in campaign_patches:
        zb = zh.encode('big5')
        pad = n - len(zb)
        data[off:off + n] = zb + b' ' * pad
        print(f"  0x{off:x}: {zh!r} + {pad} spaces = {n}B")
    open(dst, 'wb').write(bytes(data))
    assert len(data) == orig_size, f"size changed! {orig_size} → {len(data)}"
    print(f"OK: {orig_size} bytes preserved → {dst}")

if __name__ == '__main__':
    apply(sys.argv[1], sys.argv[2], sys.argv[3])
