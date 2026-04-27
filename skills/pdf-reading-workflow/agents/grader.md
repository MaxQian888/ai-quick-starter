# Grader

## Purpose

Evaluate whether the agent correctly probed the environment, chose the right command (inspect, text, or render) based on PDF type, and handled backend fallbacks gracefully.

## Scoring Criteria

1. **Probe First** (20%): Did the agent run `probe` when backend availability was uncertain?
2. **Command Selection** (30%): Was `inspect` used before `text`, and `render` used when text extraction failed?
3. **Backend Awareness** (20%): Did the agent respect backend priority (pymupdf > pypdf > Poppler CLI)?
4. **Output Handling** (15%): Were output paths kept explicit for downstream consumption?
5. **Guardrails** (15%): Did the agent avoid claiming OCR happened or promising page-perfect layout?

## Pass Threshold

Score >= 75% to pass.
