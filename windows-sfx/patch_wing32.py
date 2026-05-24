#!/usr/bin/env python3
# Patch Microsoft's WING32.DLL (12800-byte build shipped with Win10 / Win11)
# so that its "WinG Installation Error" dialog is never shown.
#
# Why this is needed:
#   WinG 1.0 was written in 1994 to live in C:\WINDOWS\SYSTEM. On modern
#   64-bit Windows, the 32-bit DLL lives in SysWOW64 -- which the original
#   path-check function does not recognise as a valid install location, so
#   it pops a modal MessageBoxA on every process startup that loads it.
#
# The dialog itself is informational, but in our case it bothers users on
# every launch and would prompt the user inside an AppImage/Wine sandbox
# where the message is nonsensical.
#
# Patch: convert one conditional branch in WinG's path-check routine from
#   75 11   jnz dialog_path
# to
#   90 90   nop ; nop
# so the function always falls through into its "looks fine, return 1"
# epilogue. The dialog code is unreachable; the WinG dispatch table is
# left in its normal state and all exports continue to work.
#
# This is a 2-byte, fully reversible change. The original DLL is kept as
# WING32.DLL.bak alongside the patched copy.

import hashlib
import shutil
import sys
from pathlib import Path

PATCH_OFFSET = 0xA55
ORIGINAL_BYTES = bytes([0x75, 0x11])  # jnz +0x11 -- jumps into dialog path
PATCHED_BYTES  = bytes([0x90, 0x90])  # nop ; nop -- always fall through

# Microsoft WinG 1.0, 12800 bytes, as shipped with Windows 10/11
# (identical in C:\Windows\System32, SysWOW64, and System)
EXPECTED_SHA256_ORIG    = "bb1f552e2525e784b61d2fe0ca23f3402adec05aa5f92f4c1dfbea3966a84cbb"
EXPECTED_SHA256_PATCHED = "edd26762e7dfd37c5a4306698c77d1a0c4c1f7e734946b3b82c534fac13065f6"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(target: Path) -> int:
    if not target.is_file():
        print(f"ERROR: {target} does not exist", file=sys.stderr)
        return 2

    data = bytearray(target.read_bytes())
    if len(data) != 12800:
        print(f"WARNING: file size is {len(data)} bytes (expected 12800).")

    pre_hash = sha256(target)
    if pre_hash == EXPECTED_SHA256_PATCHED:
        print(f"Already patched. SHA256={pre_hash}")
        return 0
    if pre_hash != EXPECTED_SHA256_ORIG:
        print(
            f"WARNING: unexpected source SHA256.\n"
            f"  got      {pre_hash}\n"
            f"  expected {EXPECTED_SHA256_ORIG}\n"
            f"  This patch is verified only against Microsoft's 12800-byte\n"
            f"  WING32.DLL. Aborting to avoid corrupting a different build."
        )
        return 3

    if bytes(data[PATCH_OFFSET:PATCH_OFFSET + 2]) != ORIGINAL_BYTES:
        print(
            f"ERROR: bytes at 0x{PATCH_OFFSET:X} are not {ORIGINAL_BYTES.hex()}",
            file=sys.stderr,
        )
        return 4

    backup = target.with_suffix(target.suffix + ".bak")
    if not backup.exists():
        shutil.copy2(target, backup)
        print(f"Saved backup -> {backup}")

    data[PATCH_OFFSET:PATCH_OFFSET + 2] = PATCHED_BYTES
    target.write_bytes(data)

    post_hash = sha256(target)
    if post_hash != EXPECTED_SHA256_PATCHED:
        print(
            f"ERROR: post-patch hash {post_hash} does not match expected"
            f" {EXPECTED_SHA256_PATCHED}",
            file=sys.stderr,
        )
        return 5

    print(f"Patched OK. SHA256={post_hash}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: patch_wing32.py <path-to-WING32.DLL>", file=sys.stderr)
        sys.exit(1)
    sys.exit(main(Path(sys.argv[1])))
