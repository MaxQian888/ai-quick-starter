---
name: react-components
description: |
  Use whenever you need to convert Stitch designs into modular React components with reusable structure and implementation-ready output. Make sure to use this skill whenever the user mentions "Stitch", "design to React", "convert design", "implement this screen", "build this UI", or "React components from mockup" — even if they only have a screenshot or HTML export. Also trigger when the task involves downloading design assets, extracting Tailwind config from HTML, creating mock data, or validating React components against a design system. Covers Next.js, Vite, CRA, and any React project using TypeScript and Tailwind CSS.
---

# Stitch to React Components

You are a frontend engineer focused on transforming designs into clean React code. You follow a modular approach and use automated tools to ensure code quality.

## Adaptive Detection

Before converting designs, detect the project context:

1. **Framework**: Check for Next.js (`app/`, `pages/`), Vite, or CRA.
2. **Styling**: Confirm Tailwind CSS is installed and check for `tailwind.config.*`.
3. **TypeScript**: Verify `tsconfig.json` and type-checking setup.
4. **Existing components**: Look for `src/components/`, `src/ui/`, or similar patterns.
5. **Data layer**: Check if the project uses static data, API clients, or mock data conventions.

Use these signals to match the generated components to the project's existing patterns.

## Retrieval and networking
1. **Namespace discovery**: Run `list_tools` to find the Stitch MCP prefix. Use this prefix (e.g., `stitch:`) for all subsequent calls.
2. **Metadata fetch**: Call `[prefix]:get_screen` to retrieve the design JSON.
3. **Check for existing designs**: Before downloading, check if `.stitch/designs/{page}.html` and `.stitch/designs/{page}.png` already exist:
   - **If files exist**: Ask the user whether to refresh the designs from the Stitch project using the MCP, or reuse the existing local files. Only re-download if the user confirms.
   - **If files do not exist**: Proceed to step 4.
4. **High-reliability download**: Internal AI fetch tools can fail on Google Cloud Storage domains.
   - **HTML (Python, cross-platform)**: `python scripts/fetch-stitch.py "[htmlCode.downloadUrl]" ".stitch/designs/{page}.html"`
   - **HTML (bash)**: `bash scripts/fetch-stitch.sh "[htmlCode.downloadUrl]" ".stitch/designs/{page}.html"`
   - **HTML (PowerShell)**: `./scripts/fetch-stitch.ps1 "[htmlCode.downloadUrl]" ".stitch/designs/{page}.html"`
   - **Screenshot (Python, cross-platform)**: `python scripts/fetch-stitch.py "[screenshot.downloadUrl]=w{width}" ".stitch/designs/{page}.png"`
   - **Screenshot (bash)**: Append `=w{width}` to the screenshot URL first, where `{width}` is the `width` value from the screen metadata (Google CDN serves low-res thumbnails by default). Then run: `bash scripts/fetch-stitch.sh "[screenshot.downloadUrl]=w{width}" ".stitch/designs/{page}.png"`
   - **Screenshot (PowerShell)**: `./scripts/fetch-stitch.ps1 "[screenshot.downloadUrl]=w{width}" ".stitch/designs/{page}.png"`
   - This script handles the necessary redirects and security handshakes.
5. **Visual audit**: Review the downloaded screenshot (`.stitch/designs/{page}.png`) to confirm design intent and layout details.

## Architectural rules
* **Modular components**: Break the design into independent files. Avoid large, single-file outputs.
* **Logic isolation**: Move event handlers and business logic into custom hooks in `src/hooks/`.
* **Data decoupling**: Move all static text, image URLs, and lists into `src/data/mockData.ts`.
* **Type safety**: Every component must include a `Readonly` TypeScript interface named `[ComponentName]Props`.
* **Project specific**: Focus on the target project's needs and constraints. Leave Google license headers out of the generated React components.
* **Style mapping**:
    * Extract the `tailwind.config` from the HTML `<head>`.
    * Sync these values with `resources/style-guide.json`.
    * Use theme-mapped Tailwind classes instead of arbitrary hex codes.

## Execution steps
1. **Environment setup**: If `node_modules` is missing, run `npm install` to enable the validation tools.
2. **Data layer**: Create `src/data/mockData.ts` based on the design content.
3. **Component drafting**: Use `resources/component-template.tsx` as a base. Find and replace all instances of `StitchComponent` with the actual name of the component you are creating.
4. **Application wiring**: Update the project entry point (like `App.tsx`) to render the new components.
5. **Quality check**:
    * Run `npm run validate <file_path>` for each component.
    * Verify the final output against the `resources/architecture-checklist.md`.
    * Start the dev server with `npm run dev` to verify the live result.

## Troubleshooting
* **Fetch errors**: Ensure the URL is quoted in the shell command to prevent parsing errors.
* **Validation errors**: Review the AST report and fix any missing interfaces or hardcoded styles.

## Examples

### Example 1: Download design assets

```bash
python scripts/fetch-stitch.py "https://example.com/download" ".stitch/designs/landing.html"
python scripts/fetch-stitch.py "https://example.com/screenshot=w1200" ".stitch/designs/landing.png"
```

### Example 2: Validate a generated component

```bash
npm run validate src/components/HeroSection.tsx
```
