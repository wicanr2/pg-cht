#!/bin/sh -e
DIR="$(dirname "$(readlink -f "$0")")"
ws32="$DIR/wineserver32"
ws64="$DIR/wineserver64"
if test -x "$ws64"; then exec "$ws64" -p0 "$@"
elif test -x "$ws32"; then exec "$ws32" -p0 "$@"
else echo "no wineserver" >&2; exit 1; fi
