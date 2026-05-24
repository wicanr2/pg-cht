# Replace the embedded icon of a Win32 PE binary with one from an .ico file.
# Uses BeginUpdateResource / UpdateResource / EndUpdateResource (kernel32).
# No external tools required.

param(
  [Parameter(Mandatory=$true)][string] $TargetExe,
  [Parameter(Mandatory=$true)][string] $IcoFile
)

if (-not (Test-Path $TargetExe)) { throw "Target exe not found: $TargetExe" }
if (-not (Test-Path $IcoFile))   { throw "Icon file not found: $IcoFile" }

Add-Type -Namespace W -Name K32 -MemberDefinition @"
[DllImport("kernel32.dll", CharSet=CharSet.Auto, SetLastError=true)]
public static extern IntPtr BeginUpdateResource(string fileName, bool deleteExisting);
[DllImport("kernel32.dll", CharSet=CharSet.Auto, SetLastError=true)]
public static extern bool UpdateResource(IntPtr hUpdate, IntPtr type, IntPtr name, ushort lang, byte[] data, uint cb);
[DllImport("kernel32.dll", CharSet=CharSet.Auto, SetLastError=true)]
public static extern bool EndUpdateResource(IntPtr hUpdate, bool discard);
"@

# ICO file layout:
#   ICONDIR { u16 reserved=0; u16 type=1; u16 count; }
#   ICONDIRENTRY[count] { u8 w,h,colors,resv; u16 planes,bpp; u32 imgSize; u32 imgOffset; }
#   imageData[count]
$ico = [System.IO.File]::ReadAllBytes($IcoFile)
$count = [BitConverter]::ToUInt16($ico, 4)
Write-Host "ICO contains $count image(s)"

# Build the RT_GROUP_ICON resource: same header but replace 4-byte offset with 2-byte resource-ID
# GRPICONDIR { u16 resv; u16 type; u16 count; }
# GRPICONDIRENTRY[count] { u8 w,h,colors,resv; u16 planes,bpp; u32 imgSize; u16 resID; }
$grpStream = New-Object System.IO.MemoryStream
$grpW = New-Object System.IO.BinaryWriter $grpStream
$grpW.Write([UInt16]0)
$grpW.Write([UInt16]1)
$grpW.Write([UInt16]$count)

$images = @()
for ($i = 0; $i -lt $count; $i++) {
  $eo = 6 + $i * 16
  $w  = $ico[$eo]
  $h  = $ico[$eo+1]
  $c  = $ico[$eo+2]
  $r  = $ico[$eo+3]
  $pl = [BitConverter]::ToUInt16($ico, $eo+4)
  $bc = [BitConverter]::ToUInt16($ico, $eo+6)
  $sz = [BitConverter]::ToUInt32($ico, $eo+8)
  $of = [BitConverter]::ToUInt32($ico, $eo+12)

  $grpW.Write([byte]$w); $grpW.Write([byte]$h); $grpW.Write([byte]$c); $grpW.Write([byte]$r)
  $grpW.Write([UInt16]$pl); $grpW.Write([UInt16]$bc)
  $grpW.Write([UInt32]$sz)
  $grpW.Write([UInt16]($i+1))  # resource ID for this RT_ICON

  $imgData = New-Object byte[] $sz
  [Array]::Copy($ico, $of, $imgData, 0, $sz)
  $images += ,$imgData
}
$grpW.Flush()
$grpData = $grpStream.ToArray()

# Resource types and IDs (RT_ICON = 3, RT_GROUP_ICON = 14)
$RT_ICON       = [IntPtr]3
$RT_GROUP_ICON = [IntPtr]14
$GROUP_NAME    = [IntPtr]1   # numeric ID 1 (commonly "MAINICON" but numeric works)
$lang          = [UInt16]0   # neutral

$h = [W.K32]::BeginUpdateResource($TargetExe, $false)
if ($h -eq [IntPtr]::Zero) { throw "BeginUpdateResource failed ($([Runtime.InteropServices.Marshal]::GetLastWin32Error()))" }

for ($i = 0; $i -lt $count; $i++) {
  $ok = [W.K32]::UpdateResource($h, $RT_ICON, [IntPtr]($i+1), $lang, $images[$i], [uint32]$images[$i].Length)
  if (-not $ok) { throw "UpdateResource RT_ICON $($i+1) failed" }
}
$ok = [W.K32]::UpdateResource($h, $RT_GROUP_ICON, $GROUP_NAME, $lang, $grpData, [uint32]$grpData.Length)
if (-not $ok) { throw "UpdateResource RT_GROUP_ICON failed" }

$ok = [W.K32]::EndUpdateResource($h, $false)
if (-not $ok) { throw "EndUpdateResource failed ($([Runtime.InteropServices.Marshal]::GetLastWin32Error()))" }

Write-Host "Icon stamped successfully into $TargetExe"
