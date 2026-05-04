Set-StrictMode -Version 2.0

Add-Type -AssemblyName System.Drawing

function Convert-HexColorToRgb {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Color
  )

  $normalized = $Color.Trim()
  if ($normalized.StartsWith("#")) {
    $normalized = $normalized.Substring(1)
  }

  if ($normalized.Length -eq 3) {
    $normalized = ($normalized.ToCharArray() | ForEach-Object { "$_$_" }) -join ""
  }

  if ($normalized.Length -ne 6 -or $normalized -notmatch '^[0-9A-Fa-f]{6}$') {
    throw "Unsupported background color format: $Color"
  }

  return [pscustomobject]@{
    R = [Convert]::ToInt32($normalized.Substring(0, 2), 16)
    G = [Convert]::ToInt32($normalized.Substring(2, 2), 16)
    B = [Convert]::ToInt32($normalized.Substring(4, 2), 16)
  }
}

function Resolve-PixelColor {
  param(
    [Parameter(Mandatory = $true)]
    [System.Drawing.Color]$Color,

    [Parameter(Mandatory = $true)]
    [pscustomobject]$Background
  )

  if ($Color.A -ge 255) {
    return [pscustomobject]@{
      R = [int]$Color.R
      G = [int]$Color.G
      B = [int]$Color.B
    }
  }

  $alpha = $Color.A / 255.0

  return [pscustomobject]@{
    R = [int][Math]::Round(($Color.R * $alpha) + ($Background.R * (1 - $alpha)))
    G = [int][Math]::Round(($Color.G * $alpha) + ($Background.G * (1 - $alpha)))
    B = [int][Math]::Round(($Color.B * $alpha) + ($Background.B * (1 - $alpha)))
  }
}

function Get-TargetRenderSize {
  param(
    [Parameter(Mandatory = $true)]
    [int]$ImageWidth,

    [Parameter(Mandatory = $true)]
    [int]$ImageHeight,

    [Parameter(Mandatory = $true)]
    [int]$TargetColumns,

    [switch]$AllowUpscale
  )

  if ($ImageWidth -le 0 -or $ImageHeight -le 0) {
    throw "Image dimensions must be positive."
  }

  if ($TargetColumns -le 0) {
    throw "TargetColumns must be positive."
  }

  $targetWidth = if ($AllowUpscale) { $TargetColumns } else { [Math]::Min($TargetColumns, $ImageWidth) }
  $targetHeight = [Math]::Ceiling(($ImageHeight * $targetWidth) / [double]$ImageWidth)
  if ($targetHeight -lt 2) {
    $targetHeight = 2
  }
  if ($targetHeight % 2 -ne 0) {
    $targetHeight += 1
  }

  return [pscustomobject]@{
    Width = [int]$targetWidth
    Height = [int]$targetHeight
    RowCount = [int]($targetHeight / 2)
  }
}

function Resize-Bitmap {
  param(
    [Parameter(Mandatory = $true)]
    [System.Drawing.Bitmap]$Bitmap,

    [Parameter(Mandatory = $true)]
    [int]$Width,

    [Parameter(Mandatory = $true)]
    [int]$Height
  )

  # Pin the output to Format32bppArgb so LockBits has a predictable stride and byte layout
  # regardless of whether the source PNG is 24bpp, 8bpp indexed, etc.
  $resized = New-Object System.Drawing.Bitmap $Width, $Height, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $graphics = [System.Drawing.Graphics]::FromImage($resized)

  try {
    $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
    $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality

    $destination = New-Object System.Drawing.Rectangle 0, 0, $Width, $Height
    $graphics.DrawImage($Bitmap, $destination)
  }
  finally {
    $graphics.Dispose()
  }

  return $resized
}

function Get-AnsiStyle {
  param(
    [Parameter(Mandatory = $true)]
    [pscustomobject]$Foreground,

    [Parameter(Mandatory = $true)]
    [pscustomobject]$Background
  )

  $escape = [char]27
  return "${escape}[38;2;$($Foreground.R);$($Foreground.G);$($Foreground.B)m${escape}[48;2;$($Background.R);$($Background.G);$($Background.B)m"
}

function Get-GrayscaleCharacter {
  param(
    [Parameter(Mandatory = $true)]
    [double]$Luma
  )

  $palette = " .:-=+*#%@"
  $normalized = [Math]::Min(255.0, [Math]::Max(0.0, $Luma))
  $index = [int][Math]::Round(($normalized / 255.0) * ($palette.Length - 1))
  return [string]$palette[$index]
}

function Convert-BitmapToPixelArt {
  param(
    [Parameter(Mandatory = $true)]
    [System.Drawing.Bitmap]$Bitmap,

    [int]$Columns = 80,

    [ValidateSet("truecolor", "none")]
    [string]$ColorMode = "truecolor",

    [string]$Background = "#000000",

    [switch]$AllowUpscale
  )

  $size = Get-TargetRenderSize -ImageWidth $Bitmap.Width -ImageHeight $Bitmap.Height -TargetColumns $Columns -AllowUpscale:$AllowUpscale
  $bg = Convert-HexColorToRgb -Color $Background
  $argbFormat = [System.Drawing.Imaging.PixelFormat]::Format32bppArgb

  # Always work from a 32bppArgb buffer with the target dimensions. This avoids LockBits
  # surprises on indexed/24bpp source images and removes the per-pixel GetPixel hot path
  # entirely.
  $needsResize = ($Bitmap.Width -ne $size.Width) -or ($Bitmap.Height -ne $size.Height) -or ($Bitmap.PixelFormat -ne $argbFormat)
  if ($needsResize) {
    $workingBitmap = Resize-Bitmap -Bitmap $Bitmap -Width $size.Width -Height $size.Height
    $ownsWorkingBitmap = $true
  }
  else {
    $workingBitmap = $Bitmap
    $ownsWorkingBitmap = $false
  }

  try {
    $width = $workingBitmap.Width
    $height = $workingBitmap.Height

    # Bulk-copy the entire pixel buffer once, instead of paying the GetPixel marshalling
    # cost twice per output cell. For an 80x40 render this drops ~6,400 native calls to 1.
    $rect = New-Object System.Drawing.Rectangle 0, 0, $width, $height
    $data = $workingBitmap.LockBits($rect, [System.Drawing.Imaging.ImageLockMode]::ReadOnly, $argbFormat)
    try {
      $stride = $data.Stride
      $byteCount = $stride * $height
      $bytes = New-Object byte[] $byteCount
      [System.Runtime.InteropServices.Marshal]::Copy($data.Scan0, $bytes, 0, $byteCount)
    }
    finally {
      $workingBitmap.UnlockBits($data)
    }

    $rows = New-Object System.Collections.Generic.List[string]
    $halfBlock = [char]0x2580
    $escape = [char]27
    $resetSequence = "${escape}[0m"
    $bgR = $bg.R
    $bgG = $bg.G
    $bgB = $bg.B

    for ($y = 0; $y -lt $height; $y += 2) {
      $builder = New-Object System.Text.StringBuilder
      $lastStyle = $null
      $topRow = $y * $stride
      $bottomRow = ($y + 1) * $stride

      for ($x = 0; $x -lt $width; $x++) {
        $tOff = $topRow + ($x * 4)
        $bOff = $bottomRow + ($x * 4)

        # Format32bppArgb stores pixels as B,G,R,A in memory (little-endian ARGB).
        $tB = [int]$bytes[$tOff]
        $tG = [int]$bytes[$tOff + 1]
        $tR = [int]$bytes[$tOff + 2]
        $tA = [int]$bytes[$tOff + 3]
        $bB = [int]$bytes[$bOff]
        $bG = [int]$bytes[$bOff + 1]
        $bR = [int]$bytes[$bOff + 2]
        $bA = [int]$bytes[$bOff + 3]

        if ($tA -lt 255) {
          $alpha = $tA / 255.0
          $inv = 1.0 - $alpha
          $tR = [int][Math]::Round(($tR * $alpha) + ($bgR * $inv))
          $tG = [int][Math]::Round(($tG * $alpha) + ($bgG * $inv))
          $tB = [int][Math]::Round(($tB * $alpha) + ($bgB * $inv))
        }
        if ($bA -lt 255) {
          $alpha = $bA / 255.0
          $inv = 1.0 - $alpha
          $bR = [int][Math]::Round(($bR * $alpha) + ($bgR * $inv))
          $bG = [int][Math]::Round(($bG * $alpha) + ($bgG * $inv))
          $bB = [int][Math]::Round(($bB * $alpha) + ($bgB * $inv))
        }

        if ($ColorMode -eq "truecolor") {
          $style = "${escape}[38;2;${tR};${tG};${tB}m${escape}[48;2;${bR};${bG};${bB}m"
          if ($style -ne $lastStyle) {
            [void]$builder.Append($style)
            $lastStyle = $style
          }
          [void]$builder.Append($halfBlock)
        }
        else {
          $averageR = ($tR + $bR) / 2.0
          $averageG = ($tG + $bG) / 2.0
          $averageB = ($tB + $bB) / 2.0
          $luma = (0.2126 * $averageR) + (0.7152 * $averageG) + (0.0722 * $averageB)
          [void]$builder.Append((Get-GrayscaleCharacter -Luma $luma))
        }
      }

      if ($ColorMode -eq "truecolor") {
        [void]$builder.Append($resetSequence)
      }

      [void]$rows.Add($builder.ToString())
    }

    return ,$rows.ToArray()
  }
  finally {
    if ($ownsWorkingBitmap -and ($null -ne $workingBitmap)) {
      $workingBitmap.Dispose()
    }
  }
}

function Convert-ImageFileToPixelArt {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path,

    [int]$Columns = 80,

    [ValidateSet("truecolor", "none")]
    [string]$ColorMode = "truecolor",

    [string]$Background = "#000000",

    [switch]$AllowUpscale
  )

  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    throw "Image not found: $Path"
  }

  $resolvedPath = (Resolve-Path -LiteralPath $Path).Path

  # Read via a memory stream so the file handle is released as soon as we have an
  # in-memory bitmap. Bitmap::FromFile would otherwise keep the file locked for the
  # lifetime of the bitmap object, which surprises callers that try to overwrite the
  # source image immediately afterwards.
  $bytes = [System.IO.File]::ReadAllBytes($resolvedPath)
  $stream = New-Object System.IO.MemoryStream(, $bytes)
  $sourceBitmap = $null
  try {
    $loaded = [System.Drawing.Image]::FromStream($stream)
    try {
      $sourceBitmap = New-Object System.Drawing.Bitmap $loaded
    }
    finally {
      $loaded.Dispose()
    }
  }
  finally {
    $stream.Dispose()
  }

  try {
    return Convert-BitmapToPixelArt -Bitmap $sourceBitmap -Columns $Columns -ColorMode $ColorMode -Background $Background -AllowUpscale:$AllowUpscale
  }
  finally {
    $sourceBitmap.Dispose()
  }
}
