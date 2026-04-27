# Grader

## Purpose

Evaluate whether the agent correctly selected the platform helper, chose the appropriate capture mode, handled permissions, and reported saved file paths.

## Scoring Criteria

1. **Tool Priority** (20%): Did the agent prefer tool-specific capture when available, falling back to this skill appropriately?
2. **Platform Selection** (25%): Was the correct helper used (PowerShell on Windows, Python on macOS/Linux)?
3. **Mode Selection** (20%): Was the right mode chosen (full screen, app, active window, region, temp)?
4. **Permission Handling** (20%): Were macOS permissions preflighted when needed?
5. **Path Reporting** (15%): Was the saved file path reported in the response?

## Pass Threshold

Score >= 75% to pass.
