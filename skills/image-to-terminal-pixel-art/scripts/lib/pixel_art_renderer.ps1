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

  $resized = New-Object System.Drawing.Bitmap $Width, $Height
  $graphics = [System.Drawing.Graphics]::FromImage($resized)

  try {
    $graphics.Clear([System.Drawing.Color]::Black)
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
  $backgroundRgb = Convert-HexColorToRgb -Color $Background
  $workingBitmap = $null

  if ($Bitmap.Width -eq $size.Width -and $Bitmap.Height -eq $size.Height) {
    $workingBitmap = New-Object System.Drawing.Bitmap $Bitmap
  }
  else {
    $workingBitmap = Resize-Bitmap -Bitmap $Bitmap -Width $size.Width -Height $size.Height
  }

  try {
    $rows = New-Object System.Collections.Generic.List[string]
    $halfBlock = [char]0x2580

    for ($y = 0; $y -lt $workingBitmap.Height; $y += 2) {
      $builder = New-Object System.Text.StringBuilder
      $lastStyle = $null

      for ($x = 0; $x -lt $workingBitmap.Width; $x++) {
        $topPixel = Resolve-PixelColor -Color ($workingBitmap.GetPixel($x, $y)) -Background $backgroundRgb
        $bottomPixel = Resolve-PixelColor -Color ($workingBitmap.GetPixel($x, $y + 1)) -Background $backgroundRgb

        if ($ColorMode -eq "truecolor") {
          $style = Get-AnsiStyle -Foreground $topPixel -Background $bottomPixel
          if ($style -ne $lastStyle) {
            [void]$builder.Append($style)
            $lastStyle = $style
          }
          [void]$builder.Append($halfBlock)
        }
        else {
          $averageR = ($topPixel.R + $bottomPixel.R) / 2.0
          $averageG = ($topPixel.G + $bottomPixel.G) / 2.0
          $averageB = ($topPixel.B + $bottomPixel.B) / 2.0
          $luma = (0.2126 * $averageR) + (0.7152 * $averageG) + (0.0722 * $averageB)
          [void]$builder.Append((Get-GrayscaleCharacter -Luma $luma))
        }
      }

      if ($ColorMode -eq "truecolor") {
        [void]$builder.Append(([string]([char]27) + "[0m"))
      }

      [void]$rows.Add($builder.ToString())
    }

    return ,$rows.ToArray()
  }
  finally {
    if ($null -ne $workingBitmap) {
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
  $bitmap = [System.Drawing.Bitmap]::FromFile($resolvedPath)

  try {
    return Convert-BitmapToPixelArt -Bitmap $bitmap -Columns $Columns -ColorMode $ColorMode -Background $Background -AllowUpscale:$AllowUpscale
  }
  finally {
    $bitmap.Dispose()
  }
}
