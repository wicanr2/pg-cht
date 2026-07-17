import os, re, json

SRC = "/tmp/claude-1000/-home-anr2-game-Panzer-General/27158536-5475-4c32-8969-ef378227dfcf/scratchpad/pg2/Panzer2/SCENARIO"
OUT = "/tmp/claude-1000/-home-anr2-game-Panzer-General/27158536-5475-4c32-8969-ef378227dfcf/scratchpad/pg2/翻譯"

scn_bases = set()
for f in os.listdir(SRC):
    if f.upper().endswith(".SCN"):
        scn_bases.add(f[:-4].upper())

files = []
for f in os.listdir(SRC):
    if f.upper().endswith(".TXT") and f[:-4].upper() in scn_bases:
        files.append(f)
files.sort()

def has_lower(s):
    return any(c.islower() for c in s)

place_lines = {}   # unique string -> count
code_lines = {}     # unique string -> count
per_file = {}

for fn in files:
    path = os.path.join(SRC, fn)
    with open(path, 'rb') as fh:
        raw = fh.read()
    text = raw.decode('latin-1')
    lines = text.split('\r\n') if '\r\n' in text else text.split('\n')
    # drop possible trailing empty line from split
    per_file[fn] = lines
    for ln in lines:
        s = ln.strip('\r\n')
        if s == '':
            continue
        if has_lower(s):
            place_lines[s] = place_lines.get(s, 0) + 1
        else:
            code_lines[s] = code_lines.get(s, 0) + 1

print("files:", len(files))
print("unique place/text strings:", len(place_lines))
print("unique code/number strings:", len(code_lines))

with open(os.path.join(OUT, "scenario_unique_placenames.txt"), "w", encoding="utf-8") as f:
    for s in sorted(place_lines.keys(), key=lambda x: (-place_lines[x], x)):
        f.write(f"{place_lines[s]}\t{s}\n")

with open(os.path.join(OUT, "scenario_unique_codes.txt"), "w", encoding="utf-8") as f:
    for s in sorted(code_lines.keys(), key=lambda x: (-code_lines[x], x)):
        f.write(f"{code_lines[s]}\t{s}\n")

with open(os.path.join(OUT, "scenario_perfile.json"), "w", encoding="utf-8") as f:
    json.dump(per_file, f, ensure_ascii=False)

with open(os.path.join(OUT, "scenario_matching_files.txt"), "w") as f:
    for fn in files:
        f.write(fn + "\n")
