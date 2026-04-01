$libraryPath = Join-Path $PSScriptRoot "..\scripts\lib\pixel_art_renderer.ps1"
$scriptPath = Join-Path $PSScriptRoot "..\scripts\render_image_as_pixel_art.ps1"

if (-not (Test-Path $libraryPath)) {
  throw "Renderer library not found: $libraryPath"
}

. $libraryPath

function New-TestBitmap {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path
  )

  Add-Type -AssemblyName System.Drawing

  $bitmap = New-Object System.Drawing.Bitmap 2, 2
  try {
    $bitmap.SetPixel(0, 0, [System.Drawing.Color]::FromArgb(255, 255, 0, 0))
    $bitmap.SetPixel(1, 0, [System.Drawing.Color]::FromArgb(255, 0, 255, 0))
    $bitmap.SetPixel(0, 1, [System.Drawing.Color]::FromArgb(255, 0, 0, 255))
    $bitmap.SetPixel(1, 1, [System.Drawing.Color]::FromArgb(255, 255, 255, 255))
    $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
  }
  finally {
    $bitmap.Dispose()
  }
}

Describe "pixel art renderer" {
  It "keeps width and returns an even pixel height" {
    $size = Get-TargetRenderSize -ImageWidth 400 -ImageHeight 201 -TargetColumns 80

    $size.Width | Should Be 80
    $size.Height | Should Be 42
    $size.RowCount | Should Be 21
  }

  It "renders ANSI half-block rows for paired pixels" {
    Add-Type -AssemblyName System.Drawing

    $bitmap = New-Object System.Drawing.Bitmap 2, 2
    try {
      $bitmap.SetPixel(0, 0, [System.Drawing.Color]::FromArgb(255, 255, 0, 0))
      $bitmap.SetPixel(1, 0, [System.Drawing.Color]::FromArgb(255, 0, 255, 0))
      $bitmap.SetPixel(0, 1, [System.Drawing.Color]::FromArgb(255, 0, 0, 255))
      $bitmap.SetPixel(1, 1, [System.Drawing.Color]::FromArgb(255, 255, 255, 255))

      $lines = Convert-BitmapToPixelArt -Bitmap $bitmap -Columns 2 -ColorMode truecolor -AllowUpscale

      $escape = [char]27
      $halfBlock = [char]0x2580

      $lines.Count | Should Be 1
      $lines[0] | Should Match ([regex]::Escape("${escape}[38;2;255;0;0m${escape}[48;2;0;0;255m") + $halfBlock)
      $lines[0] | Should Match ([regex]::Escape("${escape}[38;2;0;255;0m${escape}[48;2;255;255;255m") + $halfBlock)
      $lines[0] | Should Match ([regex]::Escape("${escape}[0m") + "$")
    }
    finally {
      $bitmap.Dispose()
    }
  }

  It "falls back to grayscale characters when color is disabled" {
    Add-Type -AssemblyName System.Drawing

    $bitmap = New-Object System.Drawing.Bitmap 2, 2
    try {
      $bitmap.SetPixel(0, 0, [System.Drawing.Color]::FromArgb(255, 0, 0, 0))
      $bitmap.SetPixel(1, 0, [System.Drawing.Color]::FromArgb(255, 255, 255, 255))
      $bitmap.SetPixel(0, 1, [System.Drawing.Color]::FromArgb(255, 0, 0, 0))
      $bitmap.SetPixel(1, 1, [System.Drawing.Color]::FromArgb(255, 255, 255, 255))

      $lines = Convert-BitmapToPixelArt -Bitmap $bitmap -Columns 2 -ColorMode none -AllowUpscale

      $lines.Count | Should Be 1
      $lines[0].Length | Should Be 2
      $lines[0] | Should Not Match ([regex]::Escape([char]27))
    }
    finally {
      $bitmap.Dispose()
    }
  }

  It "prints rendered rows from the CLI wrapper" {
    $tempImage = Join-Path $env:TEMP "pixel-art-render-test.png"
    New-TestBitmap -Path $tempImage

    try {
      $result = & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath -Path $tempImage -Columns 2 -ColorMode none 2>&1

      $LASTEXITCODE | Should Be 0
      ($result -join [Environment]::NewLine).Trim().Length -gt 0 | Should Be $true
    }
    finally {
      Remove-Item $tempImage -Force -ErrorAction SilentlyContinue
    }
  }
}
