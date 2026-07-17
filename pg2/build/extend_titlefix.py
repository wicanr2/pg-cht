#!/usr/bin/env python3
"""extend_titlefix.py — OPTIONAL complete-build extension.

The spec build's title_fix patches ONLY readScenarioTitle's classifier @0x43dde0, which
fixes the SCENARIO list. But PG2 has 5 byte-identical copies of the same "read a text field,
terminate the line at the first ctype-class-0 byte" routine; the signed-char _pctype
underflow truncates CJK in ALL of them.  The CAMPAIGN list reads its name via one of the
other 4 copies, so campaign titles still truncate to 1 char.

This extends the exact same proven transform (line terminates ONLY on \\0/\\r/\\n; no high
byte ever truncates) to the 4 remaining sibling classifiers.  All 5 share i=[ebp-0x10c] and
buffer=[ebp-8]; only the class-output ebp slot differs, so the patch is parameterised by it.
Zero risk to ASCII (unchanged termination on \\0/\\r/\\n) and zero re-encoding.

Input : build/PANZER2.EXE (the spec 4-patch EXE)   Output: build/PANZER2.5fix.EXE
"""
import subprocess, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = HERE

# (classifier start VA, class-output ebp displacement) for the 4 UNPATCHED siblings.
# 0x43dde0 (readScenarioTitle) is already handled by the spec title_fix.
SIBLINGS = [
    (0x43d3d4, 0x180),
    (0x43d681, 0x118),
    (0x43d927, 0x118),
    (0x43db59, 0x114),
]
SPAN = 0x5a                       # 90 bytes, classifier -> stop-test, identical for all 5
ORIG_HEAD = bytes.fromhex("833d44a74b00010f")   # cmp [0x4ba744],1 ; jle ...

def va2file(va): return va - 0x401000 + 0x400

def assemble(va, class_off):
    asm = f"""bits 32
org {va:#x}
    movsx eax, word [ebp-0x10c]
    mov   ecx, [ebp-8]
    movzx eax, byte [ecx+eax]
    mov   dword [ebp-{class_off:#x}], 1
    test  al, al
    jz    .stop
    cmp   al, 0x0d
    jz    .stop
    cmp   al, 0x0a
    jz    .stop
    jmp   .done
.stop:
    mov   dword [ebp-{class_off:#x}], 0
.done:
"""
    src = os.path.join(SCRATCH, f"sib_{va:x}.asm"); binf = os.path.join(SCRATCH, f"sib_{va:x}.bin")
    open(src, "w").write(asm)
    subprocess.run(["nasm", "-f", "bin", "-o", binf, src], check=True)
    return open(binf, "rb").read()

def main():
    exe_in  = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "build", "PANZER2.EXE")
    exe_out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "build", "PANZER2.5fix.EXE")
    d = bytearray(open(exe_in, "rb").read())
    for va, class_off in SIBLINGS:
        fo = va2file(va)
        assert bytes(d[fo:fo+8]) == ORIG_HEAD, f"@{va:#x} unexpected head {bytes(d[fo:fo+8]).hex()}"
        code = assemble(va, class_off)
        assert len(code) <= SPAN, f"@{va:#x} code {len(code)}B > {SPAN}"
        d[fo:fo+SPAN] = code + b"\x90" * (SPAN - len(code))
        print(f"[sibling-title-fix] classifier @{va:#x} (class [ebp-{class_off:#x}]) -> "
              f"\\0/\\r/\\n-only stop ({len(code)}B +{SPAN-len(code)} nop)")
    open(exe_out, "wb").write(d)
    print(f"[done] wrote {exe_out} ({len(d)} bytes) — 5-classifier complete title fix")

if __name__ == "__main__":
    main()
