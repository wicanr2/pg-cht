#!/bin/sh -e
DIR="$(dirname "$(readlink -f "$0")")"
APPDIR_ROOT="$(readlink -f "$DIR/../..")"
wine32="$APPDIR_ROOT/usr/lib/wine/wine"
wine64="$APPDIR_ROOT/usr/lib/wine/wine64"
if test -x "$wine32"; then
    wine="$wine32"
elif test -x "$wine64"; then
    wine="$wine64"
    test -z "$WINELOADER" && export WINELOADER="$wine64"
else
    echo "error: no wine loader in $APPDIR_ROOT/usr/lib/wine/" >&2
    exit 1
fi
test -z "$WINELOADER" && export WINELOADER="$wine"
test -z "$WINESERVER" && export WINESERVER="$APPDIR_ROOT/usr/bin/wineserver"
exec "$wine" "$@"
