#!/usr/bin/env python3
"""patch_titlefix.py IN OUT
Patch readScenarioTitle's per-byte classifier (0x43dde0..0x43de39, both the DBCS
_isctype path and the direct _pctype-table path) so a scenario title's first line
is terminated ONLY by \\0 / \\r / \\n -- never by a high byte. This removes the
byte-value-dependent mid-title truncation that cut Chinese titles to 1-3 chars.

Frame (from disasm): i = word[ebp-0x10c], str base = [ebp-8], class out = [ebp-0x118].
The stop test kept intact at 0x43de3a: `cmp [ebp-0x118],0 ; je end`. We just make the
class 0 exactly for the three line-enders and non-zero for everything else.
"""
import sys, subprocess, os
VA = 0x43dde0
FO = VA - 0x401000 + 0x400          # 0x3d1e0
REGION_LEN = 0x43de3a - VA          # 90 bytes (up to, not incl, the stop test)
ORIG_HEAD = bytes.fromhex("833d44a74b00010f")   # cmp [0x4ba744],1 ; ...

asm = f"""bits 32
org {VA:#x}
    movsx eax, word [ebp-0x10c]     ; eax = i
    mov   ecx, [ebp-8]              ; ecx = title buffer base
    movzx eax, byte [ecx+eax]       ; al = str[i] (unsigned)
    mov   dword [ebp-0x118], 1      ; class = 1 (safe / keep) by default
    test  al, al                    ; NUL?
    jz    .stop
    cmp   al, 0x0d                  ; CR?
    jz    .stop
    cmp   al, 0x0a                  ; LF?
    jz    .stop
    jmp   .done
.stop:
    mov   dword [ebp-0x118], 0      ; class = 0 -> terminate line
.done:
"""

def main():
    inp, out = sys.argv[1], sys.argv[2]
    d = bytearray(open(inp, "rb").read())
    assert bytes(d[FO:FO+8]) == ORIG_HEAD, f"unexpected bytes @{FO:#x}: {bytes(d[FO:FO+8]).hex()}"
    src = "/tmp/pg2_titlefix.asm"; binf = "/tmp/pg2_titlefix.bin"
    open(src, "w").write(asm)
    subprocess.run(["nasm", "-f", "bin", "-o", binf, src], check=True)
    code = open(binf, "rb").read()
    assert len(code) <= REGION_LEN, f"patch {len(code)}B exceeds {REGION_LEN}B"
    patch = code + b"\x90" * (REGION_LEN - len(code))   # NOP-pad, falls through to stop test
    d[FO:FO+REGION_LEN] = patch
    open(out, "wb").write(d)
    print(f"[titlefix] patched {len(code)}B (+{REGION_LEN-len(code)} nop) @ file {FO:#x} (VA {VA:#x})")
    print(f"[titlefix] wrote {out}")

if __name__ == "__main__":
    main()
