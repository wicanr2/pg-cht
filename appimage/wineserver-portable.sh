#!/bin/sh -e
DIR="$(dirname "$(readlink -f "$0")")"
APPDIR_ROOT="$(readlink -f "$DIR/../..")"
ws32="$APPDIR_ROOT/usr/lib/wine/wineserver32"
ws64="$APPDIR_ROOT/usr/lib/wine/wineserver64"
if test -x "$ws64"; then exec "$ws64" "$@"
elif test -x "$ws32"; then exec "$ws32" "$@"
else echo "no wineserver" >&2; exit 1; fi
