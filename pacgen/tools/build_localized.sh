#!/bin/bash
# Assemble a fully-localized Pacific General workdir from pristine originals.
# Original game files are NEVER modified (hardlinks broken before writing).
#   usage: build_localized.sh <workdir>
set -eu
WORKDIR="${1:-/home/anr2/pg2b}"
REPO="/home/anr2/game/Panzer_General/pg-cht/pacgen"
GAME="/home/anr2/game/Panzer_General/太平洋元帥/Pacific General"
SCRATCH="${SCRATCH:-/tmp/pacgen-build-scratch}"; mkdir -p "$SCRATCH/hook"
CM="$REPO/build/atlas/charmap.json"

echo "== regenerate atlas + reencode UI patches =="
python3 "$REPO/tools/build_atlas.py" | tail -1
python3 "$REPO/tools/reencode_patches.py" | tail -1

echo "== fresh workdir $WORKDIR (hardlink, break the files we edit) =="
rm -rf "$WORKDIR"; cp -al "$GAME" "$WORKDIR"
cd "$WORKDIR"
for f in PACGEN.EXE TFONT1.DAT data/TXT.PFP; do
  cp --remove-destination "$GAME/$f" "$f.r"; rm -f "$f"; mv "$f.r" "$f"
done

echo "== hooked EXE (.cjk section + drawString hook) =="
python3 "$REPO/tools/build_hooked_exe.py" "$GAME/PACGEN.EXE" "$REPO/build/atlas/atlas_font.dat" "$WORKDIR/PACGEN.EXE" "$SCRATCH/hook" | tail -1

echo "== font height 8->16 =="
python3 "$REPO/tools/font_rebuild.py" "$GAME/TFONT1.DAT" "$WORKDIR/TFONT1.DAT" 16 "${VPOS:-bottom}" | tail -1

echo "== TXT.PFP UI (117+2 custom-code patches) =="
python3 "$REPO/tools/apply_2byte_pfp.py" "$GAME/data/TXT.PFP" "$REPO/translations/pfp_patches_2b.json" "$WORKDIR/data/TXT.PFP" "$CM" | tail -1

echo "== TXT.PFP in-battle briefings (word-wrap, byte-length preserved) =="
if [ -f "$REPO/translations/briefings_zh.json" ]; then
  cp "$WORKDIR/data/TXT.PFP" "$WORKDIR/data/TXT.PFP.tmp"
  python3 "$REPO/tools/apply_2byte_briefings.py" "$WORKDIR/data/TXT.PFP.tmp" "$WORKDIR/data/TXT.PFP" "$CM" "$REPO/translations/briefings_zh.json" | tail -1
  rm -f "$WORKDIR/data/TXT.PFP.tmp"
fi

echo "== PACEQUIP unit names (glossary matches, custom codes) =="
rm -f "$WORKDIR/data/PACEQUIP.TXT"
python3 "$REPO/tools/apply_2byte_equip.py" "$GAME/data/PACEQUIP.TXT" "$WORKDIR/data/PACEQUIP.TXT" "$CM" | tail -1

echo "== scenario TIT/DES (free-form whole-file, custom codes) =="
miss=0
for f in "$REPO"/translations/scen_zh/*.TIT "$REPO"/translations/scen_zh/*.DES; do
  base=$(basename "$f")
  # break hardlink on the target then write transcoded
  if [ -e "$WORKDIR/scen/$base" ]; then rm -f "$WORKDIR/scen/$base"; fi
  python3 "$REPO/tools/reencode_file.py" "$f" "$WORKDIR/scen/$base" "$CM" | grep -q MISSING && { python3 "$REPO/tools/reencode_file.py" "$f" "$WORKDIR/scen/$base" "$CM"; miss=1; }
done
[ "$miss" = 0 ] && echo "  all scenario TIT/DES transcoded, no atlas gaps"

echo "== DONE: $WORKDIR =="
