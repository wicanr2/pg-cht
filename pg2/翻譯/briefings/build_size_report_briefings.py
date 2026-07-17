#!/usr/bin/env python3
"""估算第二輪(SCENARIO 簡報散文,249 檔)dense 2-byte 編碼後大小,對照 32KB 上限。
邏輯同第一輪 pg2/翻譯/build_size_report.py。"""
import os

HERE = "/tmp/claude-1000/-home-anr2-game-Panzer-General/27158536-5475-4c32-8969-ef378227dfcf/scratchpad/pg2/翻譯/briefings"
OUT_ROOT = os.path.join(HERE, "out", "SCENARIO")
SCENARIO_LIMIT = 32 * 1024


def is_cjk(ch):
    o = ord(ch)
    return (
        0x4E00 <= o <= 0x9FFF or
        0x3400 <= o <= 0x4DBF or
        0x3000 <= o <= 0x303F or
        0xFF00 <= o <= 0xFFEF
    )


def estimate_dense_bytes(text):
    n = 0
    for ch in text:
        if ch in ("\r", "\n"):
            n += 1
        elif is_cjk(ch):
            n += 2
        else:
            n += 1
    return n


def main():
    rows = []
    for fn in sorted(os.listdir(OUT_ROOT)):
        if not fn.upper().endswith(".TXT"):
            continue
        path = os.path.join(OUT_ROOT, fn)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        size = estimate_dense_bytes(text)
        over = size > SCENARIO_LIMIT
        rows.append((fn, size, SCENARIO_LIMIT, "超限" if over else "OK"))

    out_path = os.path.join(HERE, "size_report_briefings.tsv")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("檔案\t估計dense2byte大小(bytes)\t上限(bytes)\t狀態\n")
        for r in rows:
            f.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\n")

    over_rows = [r for r in rows if r[3] == "超限"]
    max_row = max(rows, key=lambda r: r[1])
    print(f"wrote {out_path}: {len(rows)} files checked, {len(over_rows)} over limit")
    print(f"largest: {max_row[0]} = {max_row[1]} bytes (limit {max_row[2]})")
    if over_rows:
        print("[WARN] over-limit files:")
        for r in over_rows:
            print(f"    {r[0]}: {r[1]} bytes > {r[2]} bytes limit")


if __name__ == "__main__":
    main()
