param(
  [string]$Path,
  [ValidateSet("default", "temp")][string]$Mode = "default",
  [ValidateSet("auto", "window", "desktop", "region")][string]$Capture = "auto",
  [string]$App,
  [string]$WindowTitle,
  [Nullable[Int64]]$WindowHandle,
  [string]$Region,
  [int]$Framerate = 30,
  [int]$DurationSeconds = 15,
  [switch]$IncludeAudio,
  [string]$AudioDevice,
  [switch]$ListWindows,
  [switch]$ListAudioDevices,
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-Timestamp {
  Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
}

function Get-DefaultDirectory {
  $userHome = [Environment]::GetFolderPath("UserProfile")
  $videos = Join-Path $userHome "Videos"
  $captures = Join-Path $videos "Captures"
  if (Test-Path $captures) { return $captures }
  if (Test-Path $videos) { return $videos }
  return $userHome
}

function New-DefaultFilename {
  param(
    [string]$Prefix,
    [string]$Extension
  )

  if (-not $Prefix) { $Prefix = "recording" }
  "$Prefix-$(Get-Timestamp).$Extension"
}

function Resolve-OutputPath {
  param(
    [string]$RequestedPath,
    [string]$SaveMode,
    [string]$Extension
  )

  if ($RequestedPath) {
    $expanded = [Environment]::ExpandEnvironmentVariables($RequestedPath)
    $homeDir = [Environment]::GetFolderPath("UserProfile")
    if ($expanded -eq "~") {
      $expanded = $homeDir
    } elseif ($expanded.StartsWith("~/") -or $expanded.StartsWith('~\')) {
      $expanded = Join-Path $homeDir $expanded.Substring(2)
    }

    $full = [System.IO.Path]::GetFullPath($expanded)
    if ((Test-Path $full) -and (Get-Item $full).PSIsContainer) {
      $full = Join-Path $full (New-DefaultFilename -Prefix "" -Extension $Extension)
    } elseif (($expanded.EndsWith("\") -or $expanded.EndsWith("/")) -and -not (Test-Path $full)) {
      New-Item -ItemType Directory -Path $full -Force | Out-Null
      $full = Join-Path $full (New-DefaultFilename -Prefix "" -Extension $Extension)
    } elseif ([System.IO.Path]::GetExtension($full) -eq "") {
      $full = "$full.$Extension"
    }

    $parent = Split-Path -Parent $full
    if ($parent) {
      New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    return $full
  }

  if ($SaveMode -eq "temp") {
    $tmp = [System.IO.Path]::GetTempPath()
    return Join-Path $tmp (New-DefaultFilename -Prefix "codex-recording" -Extension $Extension)
  }

  $dest = Get-DefaultDirectory
  return Join-Path $dest (New-DefaultFilename -Prefix "" -Extension $Extension)
}

function Parse-Region {
  param([string]$Value)

  if (-not $Value) { return $null }
  $parts = $Value.Split(",") | ForEach-Object { $_.Trim() }
  if ($parts.Length -ne 4) {
    throw "Region must be x,y,w,h"
  }

  $values = $parts | ForEach-Object {
    $parsed = 0
    if (-not [int]::TryParse($_, [ref]$parsed)) {
      throw "Region values must be integers"
    }
    $parsed
  }

  if ($values[2] -le 0 -or $values[3] -le 0) {
    throw "Region width and height must be positive"
  }

  return $values
}

function Find-Executable {
  param([string]$CommandName)

  $command = Get-Command $CommandName -ErrorAction SilentlyContinue
  if ($command) {
    return $command.Source
  }
  return $null
}

function Get-WindowArea {
  param([object]$Window)

  if (-not $Window) { return 0 }
  return [Math]::Max(0, $Window.Width) * [Math]::Max(0, $Window.Height)
}

function Format-WindowSummary {
  param([object]$Window)

  if (-not $Window) { return "" }
  return ("0x{0} {1} {2}x{3}+{4}+{5} {6}" -f `
    $Window.HexHandle, $Window.ProcessName, $Window.Width, $Window.Height, $Window.Left, $Window.Top, $Window.Title)
}

Add-Type @"
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;

public static class WindowInventory {
  [StructLayout(LayoutKind.Sequential)]
  public struct RECT {
    public int Left;
    public int Top;
    public int Right;
    public int Bottom;
  }

  public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

  [DllImport("user32.dll")]
  public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

  [DllImport("user32.dll")]
  public static extern bool IsWindowVisible(IntPtr hWnd);

  [DllImport("user32.dll")]
  public static extern bool IsIconic(IntPtr hWnd);

  [DllImport("user32.dll", CharSet = CharSet.Unicode)]
  public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

  [DllImport("user32.dll", CharSet = CharSet.Unicode)]
  public static extern int GetWindowTextLength(IntPtr hWnd);

  [DllImport("user32.dll")]
  public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);

  [DllImport("user32.dll")]
  public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);

  public static Dictionary<string, object>[] ListVisibleWindows() {
    var results = new List<Dictionary<string, object>>();
    EnumWindows(delegate (IntPtr hWnd, IntPtr lParam) {
      if (!IsWindowVisible(hWnd)) {
        return true;
      }

      int textLength = GetWindowTextLength(hWnd);
      if (textLength <= 0) {
        return true;
      }

      var builder = new StringBuilder(textLength + 1);
      GetWindowText(hWnd, builder, builder.Capacity);
      string title = builder.ToString();
      if (string.IsNullOrWhiteSpace(title)) {
        return true;
      }

      RECT rect;
      if (!GetWindowRect(hWnd, out rect)) {
        return true;
      }

      int width = rect.Right - rect.Left;
      int height = rect.Bottom - rect.Top;
      if (width <= 0 || height <= 0) {
        return true;
      }

      uint processId;
      GetWindowThreadProcessId(hWnd, out processId);
      string processName = "";
      try {
        processName = Process.GetProcessById((int)processId).ProcessName;
      } catch {
        processName = "";
      }

      results.Add(new Dictionary<string, object> {
        { "Handle", hWnd.ToInt64() },
        { "HexHandle", hWnd.ToInt64().ToString("X") },
        { "Title", title },
        { "ProcessName", processName },
        { "Left", rect.Left },
        { "Top", rect.Top },
        { "Right", rect.Right },
        { "Bottom", rect.Bottom },
        { "Width", width },
        { "Height", height },
        { "IsMinimized", IsIconic(hWnd) }
      });

      return true;
    }, IntPtr.Zero);

    return results.ToArray();
  }
}
"@

function Get-VisibleWindows {
  $windows = [WindowInventory]::ListVisibleWindows() | ForEach-Object {
    [PSCustomObject]@{
      Handle      = [int64]$_.Handle
      HexHandle   = [string]$_.HexHandle
      Title       = [string]$_.Title
      ProcessName = [string]$_.ProcessName
      Left        = [int]$_.Left
      Top         = [int]$_.Top
      Right       = [int]$_.Right
      Bottom      = [int]$_.Bottom
      Width       = [int]$_.Width
      Height      = [int]$_.Height
      IsMinimized = [bool]$_.IsMinimized
    }
  }

  $windows |
    Sort-Object @{ Expression = { $_.IsMinimized } }, @{ Expression = { -(Get-WindowArea $_) } }, ProcessName, Title
}

function Get-MatchingWindows {
  param(
    [object[]]$Windows,
    [string]$AppFilter,
    [string]$TitleFilter,
    [Nullable[Int64]]$HandleFilter
  )

  $matches = $Windows
  if ($HandleFilter -ne $null) {
    $targetHandle = [int64]$HandleFilter
    $matches = $matches | Where-Object { $_.Handle -eq $targetHandle }
  }

  if ($AppFilter) {
    $needle = $AppFilter.ToLowerInvariant()
    $matches = $matches | Where-Object {
      $_.ProcessName.ToLowerInvariant().Contains($needle)
    }
  }

  if ($TitleFilter) {
    $titleNeedle = $TitleFilter.ToLowerInvariant()
    $matches = $matches | Where-Object { $_.Title.ToLowerInvariant().Contains($titleNeedle) }
  }

  return @($matches)
}

function Show-Windows {
  param([object[]]$Windows)

  if (-not $Windows -or $Windows.Count -eq 0) {
    Write-Output "No visible top-level windows matched."
    return
  }

  $Windows | Select-Object `
    @{ Name = "Handle"; Expression = { "0x{0}" -f $_.HexHandle } }, `
    ProcessName, `
    @{ Name = "Min"; Expression = { if ($_.IsMinimized) { "Y" } else { "N" } } }, `
    @{ Name = "Bounds"; Expression = { "{0}x{1}+{2}+{3}" -f $_.Width, $_.Height, $_.Left, $_.Top } }, `
    Title |
    Format-Table -AutoSize | Out-String -Width 4096 | Write-Output
}

function Get-SelectionResult {
  param(
    [object[]]$Windows,
    [string]$CaptureMode,
    [switch]$HasExplicitWindowIntent
  )

  $result = [PSCustomObject]@{
    Selected = $null
    EffectiveCapture = $CaptureMode
    Reason = $null
  }

  if ($CaptureMode -eq "desktop" -or $CaptureMode -eq "region") {
    return $result
  }

  if (-not $HasExplicitWindowIntent) {
    if ($CaptureMode -eq "window") {
      throw "Window capture requires -App, -WindowTitle, or -WindowHandle."
    }
    $result.EffectiveCapture = "desktop"
    $result.Reason = "No window filter was provided; using desktop capture."
    return $result
  }

  if (-not $Windows -or $Windows.Count -eq 0) {
    if ($CaptureMode -eq "window") {
      throw "No visible windows matched. Rerun with -ListWindows to inspect candidates."
    }
    $result.EffectiveCapture = "desktop"
    $result.Reason = "No visible windows matched; falling back to desktop capture."
    return $result
  }

  $usable = @($Windows | Where-Object { -not $_.IsMinimized })
  if ($usable.Count -eq 1) {
    $result.Selected = $usable[0]
    $result.EffectiveCapture = "window"
    return $result
  }

  if ($usable.Count -gt 1) {
    if ($CaptureMode -eq "window") {
      $summaries = $usable | ForEach-Object { Format-WindowSummary $_ }
      throw ("Multiple windows matched. Use -ListWindows and rerun with -WindowHandle. Matches:`n{0}" -f ($summaries -join [Environment]::NewLine))
    }
    $result.EffectiveCapture = "desktop"
    $result.Reason = "Multiple windows matched; falling back to desktop capture to avoid locking onto the wrong surface."
    return $result
  }

  if ($Windows.Count -eq 1) {
    if ($CaptureMode -eq "window") {
      throw "The only matching window is minimized. Restore it and rerun."
    }
    $result.EffectiveCapture = "desktop"
    $result.Reason = "The matching window is minimized; falling back to desktop capture."
    return $result
  }

  if ($CaptureMode -eq "window") {
    throw "Only minimized windows matched. Restore one and rerun."
  }

  $result.EffectiveCapture = "desktop"
  $result.Reason = "Only minimized windows matched; falling back to desktop capture."
  return $result
}

function Get-RecordingPlan {
  param(
    [string]$CaptureMode,
    [int[]]$RegionValues,
    [object]$SelectedWindow
  )

  switch ($CaptureMode) {
    "region" {
      return [PSCustomObject]@{
        Capture = "region"
        Left = $RegionValues[0]
        Top = $RegionValues[1]
        Width = $RegionValues[2]
        Height = $RegionValues[3]
        Summary = "Region $($RegionValues[2])x$($RegionValues[3])+$($RegionValues[0])+$($RegionValues[1])"
      }
    }
    "window" {
      return [PSCustomObject]@{
        Capture = "window"
        Left = $SelectedWindow.Left
        Top = $SelectedWindow.Top
        Width = $SelectedWindow.Width
        Height = $SelectedWindow.Height
        Summary = "Window 0x$($SelectedWindow.HexHandle) $($SelectedWindow.ProcessName) $($SelectedWindow.Width)x$($SelectedWindow.Height)+$($SelectedWindow.Left)+$($SelectedWindow.Top)"
      }
    }
    default {
      return [PSCustomObject]@{
        Capture = "desktop"
        Summary = "Desktop capture"
      }
    }
  }
}

function Get-FfmpegAudioDevices {
  param([string]$FfmpegPath)

  $raw = & $FfmpegPath -hide_banner -list_devices true -f dshow -i dummy 2>&1
  $devices = New-Object System.Collections.Generic.List[string]
  $isAudioSection = $false
  foreach ($line in $raw) {
    $text = [string]$line
    if ($text -match 'DirectShow audio devices') {
      $isAudioSection = $true
      continue
    }
    if ($text -match 'DirectShow video devices') {
      $isAudioSection = $false
      continue
    }
    if ($isAudioSection -and $text -match '"([^"]+)"') {
      $devices.Add($matches[1])
    }
  }
  return $devices
}

function Invoke-FfmpegRecording {
  param(
    [string]$FfmpegPath,
    [object]$Plan,
    [string]$OutputPath,
    [int]$FrameRate,
    [int]$LengthSeconds,
    [switch]$WithAudio,
    [string]$AudioInput,
    [switch]$WhatIf
  )

  $args = New-Object System.Collections.Generic.List[string]
  $args.AddRange(@("-y", "-hide_banner", "-loglevel", "warning"))
  if ($LengthSeconds -gt 0) {
    $args.AddRange(@("-t", [string]$LengthSeconds))
  }

  $args.AddRange(@("-f", "gdigrab", "-framerate", [string]$FrameRate, "-draw_mouse", "1"))
  if ($Plan.Capture -eq "desktop") {
    $args.AddRange(@("-i", "desktop"))
  } else {
    $args.AddRange(@(
        "-offset_x", [string]$Plan.Left,
        "-offset_y", [string]$Plan.Top,
        "-video_size", ("{0}x{1}" -f $Plan.Width, $Plan.Height),
        "-i", "desktop"
      ))
  }

  if ($WithAudio) {
    if (-not $AudioInput) {
      throw "Audio recording requires -AudioDevice. Run with -ListAudioDevices first."
    }
    $args.AddRange(@("-f", "dshow", "-i", "audio=$AudioInput"))
  }

  $args.AddRange(@("-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p"))
  if ($WithAudio) {
    $args.AddRange(@("-c:a", "aac", "-b:a", "160k", "-shortest"))
  } else {
    $args.Add("-an")
  }
  $args.AddRange(@("-movflags", "+faststart", $OutputPath))

  if ($WhatIf) {
    Write-Output "Backend: ffmpeg"
    Write-Output "Plan: $($Plan.Summary)"
    Write-Output ("Command: {0} {1}" -f $FfmpegPath, (($args | ForEach-Object {
            if ($_ -match '\s') { '"{0}"' -f $_ } else { $_ }
          }) -join " "))
    return
  }

  & $FfmpegPath $args
  if ($LASTEXITCODE -ne 0) {
    throw "ffmpeg exited with code $LASTEXITCODE"
  }
}

function Invoke-PsrFallback {
  param(
    [string]$OutputPath,
    [int]$LengthSeconds,
    [string]$Reason,
    [switch]$WhatIf
  )

  $psrPath = Join-Path $env:WINDIR "System32\psr.exe"
  if (-not (Test-Path $psrPath)) {
    throw "ffmpeg is unavailable and psr.exe was not found. Use Xbox Game Bar or install ffmpeg."
  }

  if ($WhatIf) {
    Write-Output "Backend: psr"
    Write-Output "Reason: $Reason"
    Write-Output "Command: $psrPath /start /output `"$OutputPath`" /gui 0 /sc 1"
    if ($LengthSeconds -gt 0) {
      Write-Output "StopAfterSeconds: $LengthSeconds"
    } else {
      Write-Output "StopAfterSeconds: manual"
    }
    return
  }

  Write-Warning "$Reason"
  Write-Warning "PSR records click-by-click screenshots and notes, not continuous video."
  try {
    & $psrPath /start /output $OutputPath /gui 0 /sc 1 | Out-Null
  } catch {
    throw "psr.exe could not be started in this environment. Try an elevated shell, install ffmpeg for direct video capture, or use Xbox Game Bar / Snipping Tool manually."
  }
  if ($LengthSeconds -gt 0) {
    Start-Sleep -Seconds $LengthSeconds
    try {
      & $psrPath /stop | Out-Null
    } catch {
      throw "psr.exe started but could not be stopped cleanly. Stop it manually with `$env:WINDIR\\System32\\psr.exe /stop`."
    }
    Start-Sleep -Milliseconds 500
  } else {
    Write-Output "PSR started. Stop it with: $psrPath /stop"
    Write-Output $OutputPath
    return
  }

  if (-not (Test-Path $OutputPath)) {
    throw "PSR did not produce an output file at $OutputPath"
  }
}

$regionValues = Parse-Region -Value $Region
$hasWindowIntent = $PSBoundParameters.ContainsKey("WindowHandle") -or [bool]$App -or [bool]$WindowTitle

if ($ListWindows -and $regionValues) {
  throw "-ListWindows cannot be combined with -Region."
}
if ($ListWindows -and $Capture -eq "region") {
  throw "-ListWindows cannot be combined with -Capture region."
}
if ($regionValues -and $Capture -ne "region") {
  throw "-Region requires -Capture region."
}
if ($Capture -eq "region" -and -not $regionValues) {
  throw "-Capture region requires -Region x,y,w,h."
}
if ($Capture -eq "window" -and -not $hasWindowIntent) {
  throw "-Capture window requires -App, -WindowTitle, or -WindowHandle."
}
if ($ListAudioDevices -and $ListWindows) {
  throw "Choose either -ListWindows or -ListAudioDevices."
}
if ($ListAudioDevices -and $IncludeAudio) {
  throw "Use either -ListAudioDevices or a recording command, not both."
}
if ($DurationSeconds -lt 0) {
  throw "DurationSeconds must be zero or greater."
}

$ffmpegPath = Find-Executable -CommandName "ffmpeg"
$windows = Get-VisibleWindows

if ($ListWindows) {
  $matches = Get-MatchingWindows -Windows $windows -AppFilter $App -TitleFilter $WindowTitle -HandleFilter $WindowHandle
  Show-Windows -Windows $matches
  return
}

if ($ListAudioDevices) {
  if (-not $ffmpegPath) {
    throw "ffmpeg is not available, so audio devices cannot be enumerated."
  }
  $devices = Get-FfmpegAudioDevices -FfmpegPath $ffmpegPath
  if ($devices.Count -eq 0) {
    Write-Output "No DirectShow audio devices found."
  } else {
    $devices | ForEach-Object { Write-Output $_ }
  }
  return
}

$matches = Get-MatchingWindows -Windows $windows -AppFilter $App -TitleFilter $WindowTitle -HandleFilter $WindowHandle
$selection = Get-SelectionResult -Windows $matches -CaptureMode $Capture -HasExplicitWindowIntent:$hasWindowIntent
if ($selection.Reason) {
  Write-Warning $selection.Reason
}

$plan = Get-RecordingPlan -CaptureMode $selection.EffectiveCapture -RegionValues $regionValues -SelectedWindow $selection.Selected

if ($IncludeAudio -and -not $ffmpegPath) {
  throw "Audio capture requires ffmpeg on PATH."
}

if ($ffmpegPath) {
  $outputPath = Resolve-OutputPath -RequestedPath $Path -SaveMode $Mode -Extension "mp4"
  Invoke-FfmpegRecording -FfmpegPath $ffmpegPath -Plan $plan -OutputPath $outputPath -FrameRate $Framerate -LengthSeconds $DurationSeconds -WithAudio:$IncludeAudio -AudioInput $AudioDevice -WhatIf:$DryRun
  if (-not $DryRun) {
    Write-Output $outputPath
  }
  return
}

$fallbackOutput = Resolve-OutputPath -RequestedPath $Path -SaveMode $Mode -Extension "zip"
if ([System.IO.Path]::GetExtension($fallbackOutput).ToLowerInvariant() -ne ".zip") {
  $fallbackOutput = [System.IO.Path]::ChangeExtension($fallbackOutput, ".zip")
}

$fallbackReason = if ($plan.Capture -eq "desktop") {
  "ffmpeg was not found on PATH; falling back to Windows Problem Steps Recorder."
} else {
  "ffmpeg was not found on PATH; falling back to Windows Problem Steps Recorder, which cannot lock to a fixed $($plan.Capture) surface."
}
Invoke-PsrFallback -OutputPath $fallbackOutput -LengthSeconds $DurationSeconds -Reason $fallbackReason -WhatIf:$DryRun
if (-not $DryRun) {
  Write-Output $fallbackOutput
}
