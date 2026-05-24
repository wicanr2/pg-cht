# Build a 7-Zip SFX single-file installer for PG-cht.
#
# Inputs:
#   $Source     : path to the prepared game folder
#                 (PG-cht.exe, WING32.DLL patched, DATA/, ART/, ...)
#   $Output     : path of the .exe to produce
#
# Required on PATH / standard locations:
#   C:\Program Files\7-Zip\7z.exe
#   C:\Program Files\7-Zip\7z.sfx
#
# What it does:
#   1. Stages runtime files (skips dev artifacts: *.bak, tools/, *.reg)
#   2. Compresses to LZMA2 ultra .7z (solid archive)
#   3. Writes config.txt with UTF-8 BOM + CRLF
#   4. Copies 7z.sfx to a writable temp file and stamps PG.ICO into its
#      resource section via UpdateResource (kernel32 P/Invoke). Must happen
#      BEFORE concatenation -- UpdateResource truncates the file at the end
#      of the PE image, which would destroy the appended SFX overlay.
#   5. Concatenates stub + config + payload into the output .exe.
#
# Run from any PowerShell:
#   powershell -ExecutionPolicy Bypass -File build_sfx.ps1
#     [-Source <game-folder>]                 # default: newest PG-cht-1.2_繁中化_* under D:\03_game_tmp\
#     [-Output <out.exe>]                     # default: alongside this script
#     [-SevenZipDir "C:\Program Files\7-Zip"]

param(
  [string] $Source,
  [string] $Output,
  [string] $SevenZipDir = "C:\Program Files\7-Zip"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Auto-detect Source: pick newest D:\03_game_tmp\PG-cht-1.2_繁中化_* if not given
if (-not $Source) {
  $candidates = Get-ChildItem "D:\03_game_tmp" -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match "PG-cht-1\.2_繁中化_\d+" } |
    Sort-Object Name -Descending
  if (-not $candidates) { throw "No PG-cht-1.2_繁中化_* folder found under D:\03_game_tmp; pass -Source explicitly" }
  $Source = $candidates[0].FullName
  Write-Host "Auto-picked Source: $Source"
}
if (-not $Output) {
  $Output = Join-Path (Split-Path -Parent $PSCommandPath) "PanzerGeneralCHT-1.2-portable.exe"
  Write-Host "Auto-picked Output: $Output"
}

$sevenZip = Join-Path $SevenZipDir "7z.exe"
$sfxOrig  = Join-Path $SevenZipDir "7z.sfx"
foreach ($p in @($sevenZip, $sfxOrig, $Source)) {
  if (-not (Test-Path $p)) { throw "Missing: $p" }
}

$workDir = Split-Path -Parent $Output
if (-not (Test-Path $workDir)) { New-Item -ItemType Directory -Path $workDir -Force | Out-Null }
$stage      = Join-Path $workDir "stage"
$payload    = Join-Path $workDir "payload.7z"
$config     = Join-Path $workDir "config.txt"
$sfxStamped = Join-Path $workDir "7z-stamped.sfx"

# ---------- 1. Stage ---------------------------------------------------------
if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Path $stage | Out-Null

$includeFiles = @("PG-cht.exe","WING32.DLL","PG-cht.cmd","PG.ICO","PG.prf",
                  "README-繁中化.txt","README-自含啟動.txt")
$includeDirs  = @("ART","DATA","DATA2","MUSIC","SCENARIO")

foreach ($f in $includeFiles) {
  $sp = Join-Path $Source $f
  if (Test-Path $sp) { Copy-Item -Path $sp -Destination $stage -Force }
  else { Write-Warning "Skipping missing file: $f" }
}
foreach ($d in $includeDirs) {
  $sp = Join-Path $Source $d
  if (Test-Path $sp) { Copy-Item -Path $sp -Destination $stage -Recurse -Force }
  else { throw "Required dir missing: $d" }
}

$totalBytes = (Get-ChildItem $stage -Recurse -File | Measure-Object Length -Sum).Sum
Write-Host ("Staged: {0:N1} MB across $(((Get-ChildItem $stage -Recurse -File).Count)) files" -f ($totalBytes/1MB))

# ---------- 2. Compress ------------------------------------------------------
if (Test-Path $payload) { Remove-Item $payload -Force }
& $sevenZip a -t7z -m0=lzma2 -mx=9 -ms=on -mfb=64 -md=64m -mqs=on -mmt=on $payload "$stage\*" |
  Select-Object -Last 4 | ForEach-Object { Write-Host "  $_" }
$payloadSize = (Get-Item $payload).Length
Write-Host ("payload.7z: {0:N1} MB" -f ($payloadSize/1MB))

# ---------- 3. SFX config (UTF-8 BOM + CRLF) ---------------------------------
$configText = @"
;!@Install@!UTF-8!
Title="Panzer General Win95 繁體中文版 1.2"
BeginPrompt="即將解壓並啟動 Panzer General Win95 繁體中文化版 1.2 (裝甲元帥)。\n\n會在你指定的位置建立 'PG-cht-1.2' 資料夾，存放遊戲檔與存檔。\n\n繼續嗎？"
ExtractPathTitle="選擇解壓位置"
ExtractPathText="請選擇要把遊戲解壓到的資料夾："
ExtractDialogText="正在解壓檔案，請稍候..."
ExtractCancelText="確定要取消嗎？已解壓的檔案會被刪除。"
Progress="yes"
Directory="PG-cht-1.2"
RunProgram="PG-cht.cmd"
;!@InstallEnd@!
"@
$crlf = $configText -replace "`r?`n", "`r`n"
$bom  = [byte[]](0xEF,0xBB,0xBF)
[System.IO.File]::WriteAllBytes($config, $bom + [System.Text.Encoding]::UTF8.GetBytes($crlf))

# ---------- 4. Icon-stamp a copy of 7z.sfx -----------------------------------
# Doing it on the stub BEFORE concat preserves the appended 7z overlay; doing
# it after concat truncates the overlay because UpdateResource rewrites the
# file using the PE image size as the end-of-file.
Copy-Item -Path $sfxOrig -Destination $sfxStamped -Force

Add-Type -Namespace W3 -Name K -MemberDefinition @"
[DllImport("kernel32.dll", CharSet=CharSet.Auto, SetLastError=true)]
public static extern IntPtr BeginUpdateResource(string fileName, bool deleteExisting);
[DllImport("kernel32.dll", CharSet=CharSet.Auto, SetLastError=true)]
public static extern bool UpdateResource(IntPtr hUpdate, IntPtr type, IntPtr name, ushort lang, byte[] data, uint cb);
[DllImport("kernel32.dll", CharSet=CharSet.Auto, SetLastError=true)]
public static extern bool EndUpdateResource(IntPtr hUpdate, bool discard);
"@

$icoPath = Join-Path $Source "PG.ICO"
$ico = [System.IO.File]::ReadAllBytes($icoPath)
$count = [BitConverter]::ToUInt16($ico, 4)
$ms = New-Object System.IO.MemoryStream
$bw = New-Object System.IO.BinaryWriter $ms
$bw.Write([UInt16]0); $bw.Write([UInt16]1); $bw.Write([UInt16]$count)
$images = @()
for ($i = 0; $i -lt $count; $i++) {
  $eo = 6 + $i * 16
  $bw.Write([byte]$ico[$eo]); $bw.Write([byte]$ico[$eo+1])
  $bw.Write([byte]$ico[$eo+2]); $bw.Write([byte]$ico[$eo+3])
  $bw.Write([UInt16]([BitConverter]::ToUInt16($ico,$eo+4)))
  $bw.Write([UInt16]([BitConverter]::ToUInt16($ico,$eo+6)))
  $bw.Write([UInt32]([BitConverter]::ToUInt32($ico,$eo+8)))
  $bw.Write([UInt16]($i+1))
  $sz = [BitConverter]::ToUInt32($ico,$eo+8)
  $of = [BitConverter]::ToUInt32($ico,$eo+12)
  $d = New-Object byte[] $sz
  [Array]::Copy($ico, $of, $d, 0, $sz)
  $images += ,$d
}
$bw.Flush()
$grp = $ms.ToArray()

$h = [W3.K]::BeginUpdateResource($sfxStamped, $false)
if ($h -eq [IntPtr]::Zero) { throw "BeginUpdateResource failed" }
for ($i = 0; $i -lt $count; $i++) {
  [void][W3.K]::UpdateResource($h, [IntPtr]3, [IntPtr]($i+1), [UInt16]0, $images[$i], [uint32]$images[$i].Length)
}
[void][W3.K]::UpdateResource($h, [IntPtr]14, [IntPtr]1, [UInt16]0, $grp, [uint32]$grp.Length)
if (-not [W3.K]::EndUpdateResource($h, $false)) { throw "EndUpdateResource failed" }

# ---------- 5. Concat stub + config + payload --------------------------------
cmd /c "copy /b `"$sfxStamped`" + `"$config`" + `"$payload`" `"$Output`"" | Out-Null

$o = Get-Item $Output
Write-Host ""
Write-Host ("Built: $($o.Name)")
Write-Host ("  Size:   {0:N0} bytes ({1:N2} MB)" -f $o.Length, ($o.Length/1MB))
Write-Host ("  SHA256: {0}" -f (Get-FileHash $Output).Hash)
