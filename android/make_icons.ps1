# Make the Android app's icons from nextup_logo.png: square and round launcher
# icons, the larger squares the launch screen uses, and the foreground of the
# adaptive icon Android shapes itself. Uses Windows' own System.Drawing, so
# there is nothing to install. Run from anywhere:
#     powershell -ExecutionPolicy Bypass -File android\make_icons.ps1
Add-Type -AssemblyName System.Drawing
$root = Split-Path -Parent $PSScriptRoot
$logo = [System.Drawing.Image]::FromFile((Join-Path $root "nextup_logo.png"))
$out = Join-Path $PSScriptRoot "icons"
New-Item -ItemType Directory -Force $out | Out-Null

function New-Icon([int]$size, [string]$path, [double]$scale, [bool]$round) {
    $bmp = New-Object System.Drawing.Bitmap $size, $size
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.Clear([System.Drawing.Color]::Transparent)
    if ($round) {
        $clip = New-Object System.Drawing.Drawing2D.GraphicsPath
        $clip.AddEllipse(0, 0, $size, $size)
        $g.SetClip($clip)
    }
    $inner = [int][math]::Round($size * $scale)
    $off = [int][math]::Round(($size - $inner) / 2)
    $g.DrawImage($logo, $off, $off, $inner, $inner)
    $g.Dispose()
    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
}

# Launcher icons: the logo whole. Round ones are the logo cut to a circle —
# its own corners are rounded already, so very little is lost.
foreach ($s in 48, 72, 96, 144, 192) {
    New-Icon $s (Join-Path $out "nextup-square-$s.png") 1.0 $false
    New-Icon $s (Join-Path $out "nextup-round-$s.png") 1.0 $true
}
# The launch screen's larger squares.
foreach ($s in 320, 480, 640, 960, 1280) {
    New-Icon $s (Join-Path $out "nextup-square-$s.png") 1.0 $false
}
# Adaptive foreground: Android shows only the middle two thirds of this layer,
# in whatever shape the phone uses, over the near-black background. At 72% the
# logo fills that window with only its rounded corners trimmed.
foreach ($s in 108, 162, 216, 324, 432) {
    New-Icon $s (Join-Path $out "nextup-adaptive-$s.png") 0.72 $false
}
$logo.Dispose()
Write-Output "icons written to $out"
