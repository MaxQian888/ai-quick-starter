#!/usr/bin/env python3
"""Enforce minimum code coverage threshold from common coverage outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


METRIC_KEYS = ("lines", "statements", "functions", "branches")


def _coerce_pct(value: Any) -> float | None:
    """Accept numeric, numeric-string, or None pct fields."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_summary_json(path: Path) -> dict[str, float]:
    data = json.loads(path.read_text(encoding="utf-8"))
    total = data.get("total", {})
    metrics: dict[str, float] = {}
    for key in METRIC_KEYS:
        node = total.get(key)
        if isinstance(node, dict):
            pct = _coerce_pct(node.get("pct"))
            if pct is not None:
                metrics[key] = pct
    return metrics


def parse_lcov(path: Path) -> dict[str, float]:
    lf = lh = brf = brh = fnf = fnh = 0
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if raw.startswith("LF:"):
            lf += int(raw.split(":", 1)[1])
        elif raw.startswith("LH:"):
            lh += int(raw.split(":", 1)[1])
        elif raw.startswith("BRF:"):
            brf += int(raw.split(":", 1)[1])
        elif raw.startswith("BRH:"):
            brh += int(raw.split(":", 1)[1])
        elif raw.startswith("FNF:"):
            fnf += int(raw.split(":", 1)[1])
        elif raw.startswith("FNH:"):
            fnh += int(raw.split(":", 1)[1])

    metrics: dict[str, float] = {}
    if lf > 0:
        pct = (lh / lf) * 100
        metrics["lines"] = pct
        metrics["statements"] = pct
    if fnf > 0:
        metrics["functions"] = (fnh / fnf) * 100
    if brf > 0:
        metrics["branches"] = (brh / brf) * 100
    return metrics


def find_per_file_offenders(
    summary_path: Path, threshold: float, metrics: list[str], limit: int = 10
) -> list[tuple[str, str, float]]:
    """Return (file, metric, pct) for files below threshold on any required metric.

    Istanbul/Vitest summary files include per-file rows alongside `total`. Surfacing
    these turns a vague "branches=72%" failure into actionable file paths.
    """
    try:
        data = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    offenders: list[tuple[str, str, float]] = []
    for file_path, payload in data.items():
        if file_path == "total" or not isinstance(payload, dict):
            continue
        for metric in metrics:
            node = payload.get(metric)
            if not isinstance(node, dict):
                continue
            pct = _coerce_pct(node.get("pct"))
            if pct is None or pct >= threshold:
                continue
            offenders.append((file_path, metric, pct))
    offenders.sort(key=lambda item: item[2])
    return offenders[:limit]


def resolve_inputs(root: Path, summary_path: str | None, lcov_path: str | None) -> tuple[Path | None, Path | None]:
    summary = root / "coverage" / "coverage-summary.json" if not summary_path else Path(summary_path)
    lcov = root / "coverage" / "lcov.info" if not lcov_path else Path(lcov_path)
    if summary.exists():
        return summary, lcov if lcov.exists() else None
    if lcov.exists():
        return None, lcov
    return None, None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check coverage metrics against a minimum threshold."
    )
    parser.add_argument("--root", default=".", help="Project root directory.")
    parser.add_argument(
        "--threshold",
        type=float,
        default=80.0,
        help="Minimum required percentage for each metric.",
    )
    parser.add_argument(
        "--metrics",
        default=",".join(METRIC_KEYS),
        help="Comma-separated metrics to enforce.",
    )
    parser.add_argument(
        "--summary",
        help="Path to coverage-summary.json (optional).",
    )
    parser.add_argument(
        "--lcov",
        help="Path to lcov.info (optional).",
    )
    parser.add_argument(
        "--per-file",
        action="store_true",
        help="When summary JSON is available, list files below threshold.",
    )
    parser.add_argument(
        "--per-file-limit",
        type=int,
        default=10,
        help="Cap on per-file offenders to print (default 10).",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"root_not_found: {root}")
        return 2

    summary_file, lcov_file = resolve_inputs(root, args.summary, args.lcov)
    if summary_file is None and lcov_file is None:
        print("coverage_not_found: expected coverage/coverage-summary.json or coverage/lcov.info")
        return 2

    metrics: dict[str, float] = {}
    source = ""
    if summary_file is not None:
        metrics = parse_summary_json(summary_file)
        source = summary_file.as_posix()
    elif lcov_file is not None:
        metrics = parse_lcov(lcov_file)
        source = lcov_file.as_posix()

    required = [m.strip() for m in args.metrics.split(",") if m.strip()]
    missing_required = [m for m in required if m not in metrics]
    failed = {m: metrics[m] for m in required if m in metrics and metrics[m] < args.threshold}

    print(f"coverage_source: {source}")
    print(f"threshold: {args.threshold:.2f}")
    for metric in required:
        if metric in metrics:
            print(f"{metric}: {metrics[metric]:.2f}%")
        else:
            print(f"{metric}: unavailable")

    if missing_required:
        print(f"missing_metrics: {', '.join(missing_required)}")
    if failed:
        formatted = ", ".join(f"{k}={v:.2f}%" for k, v in failed.items())
        print(f"below_threshold: {formatted}")

        if args.per_file and summary_file is not None:
            offenders = find_per_file_offenders(
                summary_file, args.threshold, list(failed.keys()), args.per_file_limit
            )
            if offenders:
                print(f"per_file_offenders (top {len(offenders)}):")
                for file_path, metric, pct in offenders:
                    print(f"  - {file_path}: {metric}={pct:.2f}%")

    if missing_required or failed:
        return 1
    print("coverage_gate: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
