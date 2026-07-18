#!/usr/bin/env python3
"""patch_briefing_wrapcount_clone.py -- briefing-only CLONE of the wrap/line-count routine
countLines @0x43fdd5 that reads the ORIGINAL (pre-repoint) _pctype table, undoing the §7.9
repoint blast-radius on the on-map campaign/advisor briefing panel WITHOUT touching the
shared routine or its 17 other callers.

=== IMPORTANT: corrects the earlier (wrong) target ===
The first attempt (patch_briefing_measure_table.py) cloned measureWidthMultiline @0x43eba0,
per the hand-off diagnosis. WINE A/B PROVED that clone is a NO-OP for the briefing box:
redirecting briefing_open's measure call changed nothing, and SUPPRESSING briefing_open
(ret at 0x460f17) left the box fully intact -> briefing_open does NOT draw the on-map
briefing panel. First-principles confirms it: measureWidthMultiline's line count (=box
HEIGHT) increments only on '\n' and is NOT ctype-dependent; only its width is. But the
regression collapses the box HEIGHT. The real drawer is 0x456d32 / 0x456efb (the two live
0x4604cb box-draw callers), whose HEIGHT comes from countLines @0x43fdd5. A targeted probe
(patch countLines' two [0x4ba538] reads to 0x4ba542) restored the TALL box, pixel-identical
to a full repoint-revert, 0 page faults -> countLines is the true culprit.

=== Mechanism ===
countLines @0x43fdd5 wraps prose and counts the resulting display lines; the box HEIGHT is
derived from that count. It classifies each byte via the CRT ctype table twice
(0x43ff02, 0x43ffc5: `mov ecx,[0x4ba538]`). Pre-repoint, a high (CJK) byte -> movsx negative
index -> live string data below the table -> classes let the wrapper break between CJK ->
many wrapped lines -> TALL box (repo hero shot evidence/pg2-campaign-briefing-cht.png).
Post-repoint the pointer -> a 0x0100 (_ALPHA) shadow -> CJK reads as unbreakable "alpha" ->
the wrapper cannot break the CJK run -> few lines -> the box collapses and text spills onto
the map.

=== Why a clone (not a global revert) ===
countLines @0x43fdd5 has 19 callers (the repoint doc's "requisition family" reads 0x43ff02/
0x43ffc5 ARE these). Reverting them globally would change every countLines-sized text box.
So we clone countLines into a fresh section, change ONLY its two ctype-table bases back to
the original 0x4ba542, and redirect ONLY the two on-map briefing/advisor box drawers
(0x456e01 in fn 0x456d32, 0x457000 in fn 0x456efb). The shared routine and its other 17
callers are byte-for-byte untouched -> zero blast radius by construction.

=== The clone (byte-exact copy + edits) ===
  * copy VA 0x43fdd5..0x440051 (637 bytes, through the tail `pop edi/esi/ebx;leave;ret`)
  * 2x `8B 0D 38 A5 4B 00` (mov ecx,[0x4ba538]) -> `B9 42 A5 4B 00 90` (mov ecx,0x4ba542;nop)
  * recompute all external E8 rel32 (targets unchanged, clone at a new VA):
        strlen 0x48c5e0, _isctype 0x48d540 (x2), glyphWidth 0x41b013 (x2)
  * internal jumps are self-relative and move as a unit -> preserved automatically
  * absolute data refs [0x4d74c4] (game font) and [0x4ba744] (DBCS flag) are
    position-independent immediates (non-ASLR, ImageBase 0x400000) -> kept
  * placed in a fresh appended `.brm` section at end-of-file (the convention .cjk/.ctyp use;
    shifts nothing existing). Must run after the repoint step so SizeOfImage is final.
"""
import struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

TEXT_VA, TEXT_RAW = 0x401000, 0x400
def va2file(va): return va - TEXT_VA + TEXT_RAW

SRC_VA   = 0x43fdd5
SRC_END  = 0x440051                 # inclusive (the ret)
CLONE_LEN = SRC_END - SRC_VA + 1    # 0x27d = 637
TAIL5    = bytes.fromhex("5f5e5bc9c3")   # pop edi;pop esi;pop ebx;leave;ret

CTYPE_ORIG = bytes.fromhex("8b0d38a54b00")   # mov ecx,[0x4ba538]
CTYPE_NEW  = bytes.fromhex("b942a54b0090")   # mov ecx,0x4ba542 ; nop
ORIG_TAB   = 0x4ba542

EXPECTED_CALLS = {0x48c5e0: "strlen", 0x48d540: "_isctype", 0x41b013: "glyphWidth"}
REDIRECT_CALLERS = [0x456e01, 0x457000]      # the two on-map briefing box drawers
SRC_CALLED = 0x43fdd5                         # what those callers currently call

SECT_NAME = b".brm"
SECT_CHARS = 0x60000020    # CODE | EXECUTE | READ


def build(exe_in, exe_out):
    d = bytearray(open(exe_in, "rb").read())
    md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True

    # --- PE geometry ---
    e = struct.unpack_from('<I', d, 0x3c)[0]; coff = e + 4
    nsec = struct.unpack_from('<H', d, coff+2)[0]; osz = struct.unpack_from('<H', d, coff+16)[0]
    opt = coff + 20; st = opt + osz
    soi = struct.unpack_from('<I', d, opt+56)[0]; hdrs = struct.unpack_from('<I', d, opt+60)[0]
    salign = struct.unpack_from('<I', d, opt+32)[0]; falign = struct.unpack_from('<I', d, opt+36)[0]

    # --- copy the source function out of .text ---
    sf = va2file(SRC_VA)
    clone = bytearray(d[sf:sf+CLONE_LEN])
    assert clone[0] == 0x55, f"source head not `push ebp`: {clone[0]:#x}"
    assert bytes(clone[-5:]) == TAIL5, f"source tail not the epilogue: {bytes(clone[-5:]).hex()}"

    # --- new .brm section geometry (appended at end-of-file) ---
    hdr_off = st + nsec*40
    assert hdr_off + 40 <= hdrs, "no room for a new section header"
    assert all(x == 0 for x in d[hdr_off:hdr_off+40]), "section-header slot not zero"
    new_rva = (soi + salign - 1) & ~(salign - 1)
    raw_off = len(d)
    assert raw_off % falign == 0, f"file end {raw_off:#x} not file-aligned"
    CLONE_VA = 0x400000 + new_rva

    # --- scan the ORIGINAL clone bytes: external calls, ctype reads, out-of-block jumps ---
    ext_calls = []      # (offset, target)
    ctype_offs = []     # offsets of `mov ecx,[0x4ba538]`
    for ins in md.disasm(bytes(clone), SRC_VA):
        off = ins.address - SRC_VA
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == 2:
            tgt = ins.operands[0].imm
            if not (SRC_VA <= tgt <= SRC_END):
                ext_calls.append((off, tgt))
        elif ins.mnemonic in ("jmp","je","jne","jg","jge","jl","jle","ja","jb","jae","jbe","js","jns"):
            t = ins.operands[0]
            if t.type == 2:
                assert SRC_VA <= t.imm <= SRC_END, \
                    f"out-of-block jump @{ins.address:#x} -> {t.imm:#x} (unexpected)"
        if bytes(clone[off:off+6]) == CTYPE_ORIG:
            ctype_offs.append(off)

    # verify what we found matches the spec
    for off, tgt in ext_calls:
        assert tgt in EXPECTED_CALLS, f"unexpected external call @+{off:#x} -> {tgt:#x}"
    assert len(ctype_offs) == 2, f"expected 2 ctype reads, found {len(ctype_offs)}: {[hex(o) for o in ctype_offs]}"

    # --- edit: ctype base -> original table ---
    for off in ctype_offs:
        clone[off:off+6] = CTYPE_NEW

    # --- edit: recompute external call rel32 for the clone's VA ---
    call_report = []
    for off, tgt in ext_calls:
        assert clone[off] == 0xE8
        orig_rel = struct.unpack_from('<i', clone, off+1)[0]
        assert SRC_VA + off + 5 + orig_rel == tgt, "source rel32 self-check failed"
        new_rel = tgt - (CLONE_VA + off + 5)
        struct.pack_into('<i', clone, off+1, new_rel)
        assert CLONE_VA + off + 5 + struct.unpack_from('<i', clone, off+1)[0] == tgt
        call_report.append((off, tgt, orig_rel, new_rel))

    # --- append the .brm section ---
    vsize = CLONE_LEN
    raw_size = (vsize + falign - 1) & ~(falign - 1)
    body = bytes(clone) + bytes(raw_size - vsize)
    new_hdr = SECT_NAME.ljust(8, b"\0") + struct.pack('<IIII', vsize, new_rva, raw_size, raw_off) \
              + struct.pack('<IIHHI', 0, 0, 0, 0, SECT_CHARS)
    d[hdr_off:hdr_off+40] = new_hdr
    struct.pack_into('<H', d, coff+2, nsec + 1)
    new_soi = new_rva + ((vsize + salign - 1) & ~(salign - 1))
    struct.pack_into('<I', d, opt+56, new_soi)
    d += body

    # --- redirect the two briefing box-drawer callers to the clone ---
    for cva in REDIRECT_CALLERS:
        cf = va2file(cva)
        assert d[cf] == 0xE8, f"caller @{cva:#x} not a call: {d[cf]:#x}"
        cur = cva + 5 + struct.unpack_from('<i', d, cf+1)[0]
        assert cur == SRC_CALLED, f"caller @{cva:#x} target {cur:#x} != {SRC_CALLED:#x}"
        struct.pack_into('<i', d, cf+1, CLONE_VA - (cva + 5))
        assert cva + 5 + struct.unpack_from('<i', d, cf+1)[0] == CLONE_VA
        print(f"[redirect] countLines caller @{cva:#x}  {SRC_CALLED:#x} -> {CLONE_VA:#x}")

    open(exe_out, "wb").write(d)

    # --- self-verification report ---
    print(f"[clone] countLines @0x43fdd5 ({CLONE_LEN} B) -> .brm RVA {new_rva:#x} (VA {CLONE_VA:#x}) "
          f"raw@{raw_off:#x} raw_size {raw_size:#x}  SizeOfImage {soi:#x}->{new_soi:#x}")
    for off in ctype_offs:
        print(f"[clone] +0x{off:<4x} (0x{SRC_VA+off:x}): mov ecx,[0x4ba538] -> mov ecx,0x{ORIG_TAB:x};nop")
    for off, tgt, orel, nrel in call_report:
        print(f"[clone] +0x{off:<4x} call {EXPECTED_CALLS[tgt]:10s} -> {tgt:#x}  "
              f"(rel {orel & 0xffffffff:#010x} -> {nrel & 0xffffffff:#010x})")
    # shared-routine untouched check
    assert d[va2file(SRC_VA)+0x12d:va2file(SRC_VA)+0x12d+6] == CTYPE_ORIG, "shared countLines modified!"
    print(f"[clone] shared countLines @0x43fdd5 unchanged (still reads [0x4ba538]); wrote {exe_out} ({len(d)} bytes)")
    return CLONE_VA


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
