import struct
from PIL import Image, ImageFont, ImageDraw

FONT_TTF = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
SRC = "/home/anr2/tfont16.dat"   # 已補 16 高的 font
DST = "/home/anr2/tfont16-cjk.dat"
H = 16

def render_cjk(ch, size=16):
    """渲染中文字成 size×size 的 0x00/0xff bitmap (width=size)"""
    img = Image.new('L', (size, size), 0)
    d = ImageDraw.Draw(img)
    fnt = ImageFont.truetype(FONT_TTF, size)
    # 置中
    bbox = d.textbbox((0,0), ch, font=fnt)
    w = bbox[2]-bbox[0]; h = bbox[3]-bbox[1]
    x = (size-w)//2 - bbox[0]; y = (size-h)//2 - bbox[1]
    d.text((x,y), ch, fill=255, font=fnt)
    px = bytearray()
    for row in range(size):
        for col in range(size):
            px.append(0xff if img.getpixel((col,row)) > 96 else 0x00)
    return size, bytes(px)  # width=16, 16×16 pixels

# 讀 rebuilt font
data = open(SRC,'rb').read()
n = struct.unpack('<I', data[4:8])[0]
h = struct.unpack('<I', data[8:12])[0]
assert h == H
offs = [struct.unpack('<I', data[0x10+i*4:0x14+i*4])[0] for i in range(n)] + [len(data)]
glyphs = []
for ch in range(n):
    g = data[offs[ch]:offs[ch+1]]
    glyphs.append(g)

# 塞「開始戰役」到 slot 0x01-0x04
CJK = {0x80:"開", 0x81:"始", 0x82:"戰", 0x83:"役"}
for slot, cjk in CJK.items():
    w, px = render_cjk(cjk, H)
    glyphs[slot] = struct.pack('<I', w) + px

# 重建 font: header + offset table + glyph data
out = bytearray(data[:0x10])
table_start = 0x10 + n*4
cur = table_start
offtab = []
for g in glyphs:
    offtab.append(cur); cur += len(g)
for o in offtab:
    out += struct.pack('<I', o)
for g in glyphs:
    out += g
open(DST,'wb').write(bytes(out))
print(f"POC font: {len(out)} bytes, slots 0x01-0x04 = 開始戰役 16×16")
