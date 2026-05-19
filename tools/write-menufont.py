#!/usr/bin/env python3
"""產生 wine reg 檔,把 WindowMetrics 內所有 LOGFONTW 改成 PMingLiU,
讓 menu / caption / status / message / icon 字體都有中文 glyph。
"""
import struct, os

FACE_NAME = "Tahoma"
PT_SMALL  = 9   # menu / status
PT_NORMAL = 10  # caption
PT_ICON   = 8   # icon

def make_logfont(face: str, pt: int, weight: int = 400) -> bytes:
    height = -int(round(pt * 96 / 72))  # negative = ascent-based, 96dpi
    # LOGFONTW (Little-Endian)
    head = struct.pack(
        '<llllllBBBBBBBB',
        height,                                    # lfHeight
        0,                                         # lfWidth
        0,                                         # lfEscapement
        0,                                         # lfOrientation
        weight,                                    # lfWeight
        0,                                         # padding (none actually, 但 LONG 對齊)
        0,                                         # lfItalic
        0,                                         # lfUnderline
        0,                                         # lfStrikeOut
        1,                                         # lfCharSet = DEFAULT_CHARSET
        0,                                         # lfOutPrecision = OUT_DEFAULT_PRECIS
        0,                                         # lfClipPrecision = CLIP_DEFAULT_PRECIS
        0,                                         # lfQuality = DEFAULT_QUALITY
        0x12,                                      # lfPitchAndFamily = VARIABLE_PITCH | FF_SWISS
    )
    # 上面 pack 多塞了一個 0 LONG,扣掉:用更精確的 layout
    # LOGFONTW 28 bytes(LONG×5 + BYTE×8) + WCHAR[32]
    head = struct.pack(
        '<lllllBBBBBBBB',
        height, 0, 0, 0, weight,
        0, 0, 0, 1, 0, 0, 0, 0x12,
    )
    assert len(head) == 28, f"head len={len(head)}"
    name = face.encode('utf-16-le')
    if len(name) > 62:
        name = name[:62]
    name += b'\x00' * (64 - len(name))
    return head + name

ENTRIES = [
    ("CaptionFont",   PT_NORMAL, 700),  # 視窗標題,粗體
    ("SmCaptionFont", PT_SMALL,  400),
    ("MenuFont",      PT_SMALL,  400),
    ("StatusFont",    PT_SMALL,  400),
    ("MessageFont",   PT_SMALL,  400),
    ("IconFont",      PT_ICON,   400),
]

reg_lines = ["REGEDIT4", "", "[HKEY_CURRENT_USER\\Control Panel\\Desktop\\WindowMetrics]"]
for name, pt, weight in ENTRIES:
    blob = make_logfont(FACE_NAME, pt, weight)
    assert len(blob) == 92, f"{name} len={len(blob)}"
    hex_str = ",".join(f"{b:02x}" for b in blob)
    # 換行每 24 byte
    parts = hex_str.split(",")
    wrapped = ""
    for i in range(0, len(parts), 24):
        chunk = ",".join(parts[i:i+24])
        if i + 24 < len(parts):
            chunk += ",\\"
        wrapped += "  " + chunk + "\n"
    reg_lines.append(f'"{name}"=hex:\\')
    reg_lines.append(wrapped.rstrip())

reg_lines.append("")
out = "\n".join(reg_lines)
print(out)

with open("/tmp/pg-cht-menufont.reg", "w") as f:
    f.write(out)
print("\n寫入 /tmp/pg-cht-menufont.reg")
