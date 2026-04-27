#!/usr/bin/env python3
"""Cross-platform Stitch asset fetch helper."""

from __future__ import annotations

import argparse
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch a Stitch asset URL to a local file path.")
    parser.add_argument("url", help="Asset URL to download.")
    parser.add_argument("output_path", help="Destination file path.")
    parser.add_argument("--timeout", type=float, default=20.0, help="Request timeout in seconds.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("Initiating high-reliability fetch for Stitch HTML...")

    request = Request(args.url, headers={"User-Agent": "skills-test-react-components-fetch/1.0"})
    try:
        with urlopen(request, timeout=args.timeout) as response:
            output_path.write_bytes(response.read())
    except HTTPError as exc:
        print("ERROR: Failed to retrieve content. Check TLS/SNI or URL expiration.")
        print(f"HTTP status: {exc.code}")
        return 1
    except URLError as exc:
        print("ERROR: Failed to retrieve content. Check TLS/SNI or URL expiration.")
        print(str(exc.reason))
        return 1
    except OSError as exc:
        print("ERROR: Failed to write output file.")
        print(str(exc))
        return 1

    print(f"OK: Successfully retrieved HTML at: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
