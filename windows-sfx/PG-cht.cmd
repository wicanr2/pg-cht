@echo off
REM ---------------------------------------------------------------------
REM Self-contained launcher for PG-cht (Panzer General Win95, Big5 build).
REM
REM Why this exists:
REM   PG-cht.exe links against WING32.DLL (Microsoft WinG 1.0, 1994),
REM   whose surfaces require an 8-bit palettized display. Modern Windows
REM   runs the desktop at 32 bpp, so the game refuses to start or paints
REM   garbage unless a 256-color compatibility shim is active.
REM
REM   This launcher applies that shim via the __COMPAT_LAYER environment
REM   variable, scoped to the spawned process only -- no registry edit,
REM   no persistent system change, fully portable.
REM
REM Bundled files used:
REM   WING32.DLL  -- genuine Microsoft WinG runtime, picked up from the
REM                  executable folder via the standard DLL search order.
REM ---------------------------------------------------------------------

setlocal
cd /d "%~dp0"
set "__COMPAT_LAYER=256COLOR"
start "" "%~dp0PG-cht.exe" %*
endlocal
