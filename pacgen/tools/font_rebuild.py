#!/usr/bin/env python3
"""TFONT1.DAT 重建工具 — Plan B(single-byte 造字 + font 加高)的核心。

已驗證:遊戲繪字管線讀 font header 的 height(offset 0x08),改 header + 重烤
glyph 即可,不用 patch EXE。

功能:
1. 把所有原 8 高 glyph 補到目標高度 H(預設 16),原 pixel 置於格子指定位置
2. header height 8 → H
3. offset table 重算(每 glyph 資料 = 4 + width×H)
4. (可選)把中文 glyph 塞進未用 byte slot

用法:
    python3 font_rebuild.py <原 TFONT1.DAT> <輸出> [目標高度 H]
"""
import struct, sys

def parse(data):
    n = struct.unpack('<I', data[4:8])[0]      # 256
    h = struct.unpack('<I', data[8:12])[0]     # 原高 8
    offs = [struct.unpack('<I', data[0x10+i*4:0x14+i*4])[0] for i in range(n)] + [len(data)]
    glyphs = []
    for ch in range(n):
        o, e = offs[ch], offs[ch+1]
        g = data[o:e]
        if len(g) >= 4:
            w = struct.unpack('<I', g[:4])[0]
            px = g[4:4+w*h]
        else:
            w, px = 0, b''
        glyphs.append((w, px))
    return n, h, glyphs

def rebuild(data, H, vpos='top'):
    """把每 glyph 從原高 h 補到 H。vpos: top(原樣在上)/bottom/center"""
    n, h, glyphs = parse(data)
    # 新 glyph 資料 + 重算 offset table
    header = bytearray(data[:0x10])
    header[8:12] = struct.pack('<I', H)          # height → H
    new_glyphs = []
    for w, px in glyphs:
        if w == 0:
            new_glyphs.append(struct.pack('<I', 0))
            continue
        # px 是 w×h,重排成 w×H
        rows = [px[r*w:(r+1)*w] for r in range(h)]
        blank = bytes(w)
        pad = H - h
        if vpos == 'top':
            newrows = rows + [blank]*pad
        elif vpos == 'bottom':
            newrows = [blank]*pad + rows
        else:  # center
            top = pad//2; bot = pad-top
            newrows = [blank]*top + rows + [blank]*bot
        newpx = b''.join(newrows)
        new_glyphs.append(struct.pack('<I', w) + newpx)
    # 重建 offset table + glyph data
    table_start = 0x10 + n*4
    out = bytearray(header)
    offs = []
    cur = table_start
    for g in new_glyphs:
        offs.append(cur)
        cur += len(g)
    # 寫 offset table
    for o in offs:
        out += struct.pack('<I', o)
    # 寫 glyph data
    for g in new_glyphs:
        out += g
    return bytes(out)

def main():
    src, dst = sys.argv[1], sys.argv[2]
    H = int(sys.argv[3]) if len(sys.argv) > 3 else 16
    vpos = sys.argv[4] if len(sys.argv) > 4 else 'top'
    data = open(src, 'rb').read()
    out = rebuild(data, H, vpos)
    open(dst, 'wb').write(out)
    n, h, _ = parse(data)
    print(f"[font_rebuild] {len(data)} bytes (h={h}) → {len(out)} bytes (H={H}, vpos={vpos})")

if __name__ == '__main__':
    main()
