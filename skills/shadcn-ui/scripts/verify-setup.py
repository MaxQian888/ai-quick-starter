#!/usr/bin/env python3
"""Cross-platform shadcn/ui setup verifier."""

from __future__ import annotations

from pathlib import Path


def find_first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def main() -> int:
    root = Path(".").resolve()
    ok = True

    print("Verifying shadcn/ui setup...\n")

    components_json = root / "components.json"
    if components_json.exists():
        print("OK: components.json found")
    else:
        print("ERROR: components.json not found")
        print("  Run: npx shadcn@latest init")
        return 1

    tailwind_js = root / "tailwind.config.js"
    tailwind_ts = root / "tailwind.config.ts"
    if tailwind_js.exists() or tailwind_ts.exists():
        print("OK: Tailwind config found")
    else:
        print("ERROR: tailwind.config.js not found")
        print("  Install Tailwind: npm install -D tailwindcss postcss autoprefixer")
        return 1

    tsconfig = root / "tsconfig.json"
    if tsconfig.exists():
        content = tsconfig.read_text(encoding="utf-8", errors="replace")
        if '"@/*"' in content:
            print("OK: Path aliases configured in tsconfig.json")
        else:
            print("WARN: Path aliases not found in tsconfig.json")
    else:
        print("WARN: tsconfig.json not found (TypeScript not configured)")

    css_file = find_first_existing(
        [root / "src/index.css", root / "src/globals.css", root / "app/globals.css"]
    )
    if css_file:
        print("OK: Global CSS file found")
        css_content = css_file.read_text(encoding="utf-8", errors="replace")
        if "@tailwind base" in css_content:
            print("OK: Tailwind directives present")
        else:
            print("ERROR: Tailwind directives missing")
            ok = False

        if ":root" in css_content or "@layer base" in css_content:
            print("OK: CSS variables defined")
        else:
            print("WARN: CSS variables not found")
    else:
        print("ERROR: Global CSS file not found")
        ok = False

    ui_dir = find_first_existing([root / "src/components/ui", root / "components/ui"])
    if ui_dir:
        component_count = len(list(ui_dir.rglob("*.tsx"))) + len(list(ui_dir.rglob("*.jsx")))
        print("OK: components/ui directory exists")
        print(f"  {component_count} components installed")
    else:
        print("WARN: components/ui directory not found")

    utils_file = find_first_existing([root / "src/lib/utils.ts", root / "lib/utils.ts"])
    if utils_file:
        print("OK: lib/utils.ts exists")
        utils_content = utils_file.read_text(encoding="utf-8", errors="replace")
        if "export function cn" in utils_content:
            print("OK: cn() utility function present")
        else:
            print("ERROR: cn() utility function missing")
            ok = False
    else:
        print("ERROR: lib/utils.ts not found")
        ok = False

    print("")
    if ok:
        print("OK: Setup verification complete!")
        return 0
    print("ERROR: Setup verification found blocking issues.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
