#!/usr/bin/env python3
"""patch_null_guard.py — add a NULL-format guard to PG2's internal _output (0x48FAD0).

The player-path crash `Unhandled page fault on read access to 00000000 at 0048FAEF`
is _output reading the first char of a NULL format pointer (`mov bl,[eax]`). PG2's UI
draws many labels with `sprintf(buf, name, ...)` — the looked-up name IS the format
string — and some drawString variants (e.g. 0x43e563, 45 callers) do NOT null-check the
name (unlike the guarded 0x43e4e0 which logs "null string at %d,%d" and skips). When a
hex/terrain/unit name resolves to NULL (right-click info popup), sprintf -> _output ->
crash.

Fix: hook _output entry. If arg2 (format) is NULL, return 0 immediately (the sprintf
wrapper then null-terminates its dest buffer -> empty string; the label draws blank
instead of crashing). A NULL format is never legitimate, so this is strictly safer.
Universal: covers all 4 _output callers (sprintf 0x48d210 and the 3 others).

Stub goes in the existing .cjk section's raw slack (no file growth, SizeOfImage
unchanged). Standalone post-patch of an already-hooked build.
"""
import struct, subprocess, sys, os

TEXT_VA, TEXT_RAW = 0x401000, 0x400
def va2file(va): return va - TEXT_VA + TEXT_RAW

VA_OUTPUT = 0x48FAD0
OUTPUT_HEAD = bytes.fromhex("81ec48020000")   # sub esp,0x248  (6 bytes)

def build(exe_in, exe_out, scratch="/tmp"):
    d = bytearray(open(exe_in, "rb").read())
    # locate .cjk section
    e = struct.unpack_from('<I', d, 0x3c)[0]; coff = e + 4
    nsec = struct.unpack_from('<H', d, coff+2)[0]; osz = struct.unpack_from('<H', d, coff+16)[0]
    opt = coff + 20; st = opt + osz
    soi = struct.unpack_from('<I', d, opt+56)[0]
    cjk = None
    for i in range(nsec):
        b = st + i*40; nm = d[b:b+8].split(b'\0')[0]
        if nm == b'.cjk':
            vs = struct.unpack_from('<I', d, b+8)[0]; va = struct.unpack_from('<I', d, b+12)[0]
            rs = struct.unpack_from('<I', d, b+16)[0]; raw = struct.unpack_from('<I', d, b+20)[0]
            cjk = (b, vs, va, rs, raw)
    assert cjk, ".cjk section not found (run on an already-hooked EXE)"
    bhdr, vs, va, rs, raw = cjk
    # place stub 16-aligned just past current content, inside the raw slack
    stub_off = (vs + 15) & ~15                       # section-relative offset
    STUB_VA = 0x400000 + va + stub_off
    stub_file = raw + stub_off
    # assemble
    asm = f"""bits 32
org {STUB_VA:#x}
    mov  eax, [esp+8]        ; arg2 = format pointer (esp unchanged at _output entry)
    test eax, eax
    jz   .nullfmt
    sub  esp, 0x248          ; replay the overwritten _output prologue
    jmp  {VA_OUTPUT+6:#x}    ; continue in _output at 0x48fad6
.nullfmt:
    xor  eax, eax            ; NULL format -> return 0 (no output); caller terminates dest
    ret
"""
    src = os.path.join(scratch, "nullguard.asm"); binf = os.path.join(scratch, "nullguard.bin")
    open(src, "w").write(asm)
    subprocess.run(["nasm", "-f", "bin", "-o", binf, src], check=True)
    stub = open(binf, "rb").read()
    assert stub_off + len(stub) <= rs, f"stub overflows .cjk raw slack ({stub_off+len(stub):#x} > {rs:#x})"
    # write stub into the raw slack
    assert all(x == 0 for x in d[stub_file:stub_file+len(stub)]), "slack not zero — refuse to overwrite"
    d[stub_file:stub_file+len(stub)] = stub
    # bump .cjk VSize to cover the stub (SizeOfImage must stay the same page-rounded value)
    new_vs = stub_off + len(stub)
    assert ((new_vs + 0xfff) & ~0xfff) == ((vs + 0xfff) & ~0xfff), "stub crosses a page -> SizeOfImage would change"
    struct.pack_into('<I', d, bhdr+8, new_vs)
    # patch _output entry -> jmp stub (5 bytes) + nop (orig prologue is 6 bytes)
    of = va2file(VA_OUTPUT)
    assert bytes(d[of:of+6]) == OUTPUT_HEAD, f"_output head mismatch: {bytes(d[of:of+6]).hex()}"
    d[of:of+5] = b"\xe9" + struct.pack('<i', STUB_VA - (VA_OUTPUT + 5))
    d[of+5] = 0x90
    open(exe_out, "wb").write(d)
    print(f"[null-guard] OGSTUB {len(stub)}B @ {STUB_VA:#x} (off {stub_off:#x}, file {stub_file:#x})")
    print(f"[null-guard] _output @ {VA_OUTPUT:#x} -> jmp stub;  .cjk VSize {vs:#x} -> {new_vs:#x}; SizeOfImage {soi:#x} (unchanged)")
    print(f"[null-guard] wrote {exe_out} ({len(d)} bytes)")

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "/tmp")
