#!/usr/bin/env python3
"""Cross-platform Stitch asset downloader."""

from __future__ import annotations

import argparse
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download a Stitch screen asset to disk.")
    parser.add_argument("download_url", help="Download URL from Stitch metadata.")
    parser.add_argument("output_path", help="Destination path for the downloaded asset.")
    parser.add_argument("--timeout", type=float, default=20.0, help="Request timeout in seconds.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading from: {args.download_url}")
    print(f"Saving to: {output_path}")

    request = Request(args.download_url, headers={"User-Agent": "skills-test-remotion-download/1.0"})
    try:
        with urlopen(request, timeout=args.timeout) as response:
            output_path.write_bytes(response.read())
    except HTTPError as exc:
        print("ERROR: Download failed")
        print(f"HTTP status: {exc.code}")
        return 1
    except URLError as exc:
        print("ERROR: Download failed")
        print(str(exc.reason))
        return 1
    except OSError as exc:
        print("ERROR: Download failed")
        print(str(exc))
        return 1

    print(f"OK: Successfully downloaded to {output_path}")
    print(f"  File size: {output_path.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
