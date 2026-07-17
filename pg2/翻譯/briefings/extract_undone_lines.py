import os, sys

CLEAN = "/tmp/claude-1000/-home-anr2-game-Panzer-General/27158536-5475-4c32-8969-ef378227dfcf/scratchpad/pg2/翻譯/briefings/clean_src/Panzer2/SCENARIO"
UNDONE_LIST = "/tmp/undone_base.txt"
OUT = "/tmp/claude-1000/-home-anr2-game-Panzer-General/27158536-5475-4c32-8969-ef378227dfcf/scratchpad/pg2/翻譯/briefings/undone_unique_lines.txt"

def read_dos_text_lines(path):
    with open(path, "rb") as f:
        raw = f.read()
    had_eof = raw.endswith(b"\x1a")
    if had_eof:
        raw = raw[:-1]
    text = raw.decode("latin-1")
    if "\r\n" in text:
        lines = text.split("\r\n")
    else:
        lines = text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    return lines, had_eof

bases = [l.strip() for l in open(UNDONE_LIST, encoding="utf-8") if l.strip()]
seen = {}
order = []
per_file_linecount = {}
for base in bases:
    # find actual filename case-insensitively
    fn = None
    for cand in os.listdir(CLEAN):
        if cand.upper() == base.upper() + ".TXT":
            fn = cand
            break
    if fn is None:
        print("MISSING", base)
        continue
    path = os.path.join(CLEAN, fn)
    lines, had_eof = read_dos_text_lines(path)
    per_file_linecount[base] = len(lines)
    for l in lines:
        if l.strip() == "":
            continue
        if l not in seen:
            seen[l] = 0
            order.append(l)
        seen[l] += 1

print("total unique non-blank lines:", len(order))
with open(OUT, "w", encoding="utf-8") as f:
    for l in order:
        f.write(f"{seen[l]}\t{l}\n")
print("wrote", OUT)
