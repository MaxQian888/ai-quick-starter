---
name: pptx-generator
description: |
  Use whenever you need to inspect, update, or generate PowerPoint decks (.pptx, PowerPoint, slide deck, presentation), especially when the task involves MarkItDown extraction, XML-level template edits, or PptxGenJS slide generation. Make sure to use this skill whenever the user asks for "slides", "presentation", "PowerPoint", "PPTX", "deck", "pitch deck", "keynote", or "slide deck" — even if they only have a rough outline or want to edit an existing file. Also trigger for extracting text from presentations, finding placeholder text, applying brand colors, or converting structured content into slides. Covers reading existing decks, editing templates, and building new decks from scratch with JavaScript.
---

# PPTX Generator

Use this skill for three distinct PowerPoint paths. Pick the narrowest path that matches the user's artifact instead of forcing every request through a from-scratch workflow.

## Adaptive Detection

Before starting, detect the user's starting point:

1. **Existing deck?** Check if the user provided a `.pptx` file or wants to edit an existing template.
2. **Content source?** Determine if content comes from an outline, markdown, JSON data, or design mockups.
3. **Tooling available?** Check for `node_modules` (PptxGenJS), Python environment (MarkItDown), or neither.
4. **Output requirements?** Note slide count, language, brand colors, and chart needs.
5. **Platform constraints?** Confirm if the deck is for desktop PowerPoint, Google Slides import, or web viewing.

## Choose the Path

| Need | Path |
|------|------|
| Read slide text, notes, or placeholder structure | Extract Markdown with MarkItDown, then inspect the `.md` output |
| Reuse or patch an existing deck/template | Follow [editing.md](references/editing.md) |
| Build a new deck in JavaScript | Follow the workflow below with PptxGenJS |

## Tooling

- Install MarkItDown with `pip install "markitdown[pptx]"` or `pip install "markitdown[all]"`. Use the `markitdown` CLI.
- Install PptxGenJS as a project dependency with `npm install pptxgenjs`. Do not rely on a global install.
- Install optional icon helpers with `npm install react-icons react react-dom sharp`.
- MarkItDown requires Python 3.10 or higher.
- `pptx.writeFile()` returns a Promise. Await it in Node scripts.

## Quick Reference

| Task | Approach |
|------|----------|
| Read or analyze content | `markitdown presentation.pptx -o presentation.md` |
| Patch an existing deck | See [editing.md](references/editing.md) |
| Create a new deck | See [Creating from Scratch](#creating-from-scratch-workflow) |
| QA for placeholders | `rg -n -i "xxxx\|lorem\|ipsum\|placeholder\|this.*(page\|slide).*layout" presentation.md` |

| Item | Value |
|------|-------|
| Dimensions | 10" x 5.625" (`LAYOUT_16x9`) |
| Colors | 6-char hex without `#` for PptxGenJS color props |
| English font | Arial by default, or another approved font pairing |
| Chinese font | Microsoft YaHei |
| Page badge position | x: 9.3", y: 5.1" |
| Theme keys | `primary`, `secondary`, `accent`, `light`, `bg` |
| Core shapes | `RECTANGLE`, `OVAL`, `LINE`, `ROUNDED_RECTANGLE` |
| Common charts | `BAR`, `LINE`, `PIE`, `DOUGHNUT`, `SCATTER`, `BUBBLE`, `RADAR` |

## Read Existing Content

Extract deck content to Markdown first, then review structure, notes, and leftover placeholders from the text view before touching XML or slide code.

```bash
markitdown presentation.pptx -o presentation.md
```

- Review `presentation.md` for slide titles, ordering, placeholder text, and notes.
- Search the extracted Markdown with `rg` before declaring the deck clean.
- If the user only needs content analysis, stop here and summarize the extracted structure.

## Edit Existing Decks

Use [editing.md](references/editing.md) when the user already has a `.pptx` template or reference deck.

- Do structural XML operations first: duplicate, delete, or reorder slides before changing text.
- Then edit slide XML content and run MarkItDown again on the rebuilt deck to confirm the rendered text matches the intended output.
- Keep the original deck untouched. Work on a copied `template.pptx` in the task directory.

## Creating from Scratch Workflow

Use this path when no template or reference presentation is available.

### Step 1: Research Requirements

Identify the topic, audience, purpose, tone, required visuals, and slide count before choosing layouts.

### Step 2: Select Palette and Fonts

Use [design-system.md](references/design-system.md#color-palette-reference) for palette selection and [design-system.md](references/design-system.md#font-reference) for font pairing.

### Step 3: Select Design Style

Use [design-system.md](references/design-system.md#style-recipes) to choose a visual style: Sharp, Soft, Rounded, or Pill.

### Step 4: Plan the Slide Outline

Classify every slide as exactly one of the [5 page types](references/slide-types.md). Keep adjacent slides visually distinct. Do not repeat the same layout pattern across the whole deck.

### Step 5: Generate Slide Modules

Create one JS file per slide in `slides/`. Each file must export a synchronous `createSlide(pres, theme)` function. Use [slide-types.md](references/slide-types.md) for type-specific expectations and [pptxgenjs.md](references/pptxgenjs.md) for API details.

If subagents are available, use them only for independent slide modules.

Tell each subagent:
1. File naming: `slides/slide-01.js`, `slides/slide-02.js`, and so on
2. Images go in `slides/imgs/`
3. Final PPTX goes in `slides/output/`
4. Layout is `LAYOUT_16x9`
5. Fonts must follow the selected pairing
6. Colors for PptxGenJS props must be 6-char hex without `#`
7. The theme object contract below is mandatory
8. The slide function must stay synchronous

### Step 6: Compile the Deck

Create `slides/compile.js` to combine all slide modules and await the final write.

```javascript
// slides/compile.js
const pptxgen = require("pptxgenjs");

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Codex";
  pres.title = "Presentation Title";

  const theme = {
    primary: "22223B",
    secondary: "4A4E69",
    accent: "9A8C98",
    light: "C9ADA7",
    bg: "F2E9E4"
  };

  for (let i = 1; i <= 12; i += 1) {
    const num = String(i).padStart(2, "0");
    const slideModule = require(`./slide-${num}.js`);
    slideModule.createSlide(pres, theme);
  }

  await pres.writeFile({ fileName: "./output/presentation.pptx" });
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
```

Run with `node compile.js` inside `slides/`.

### Step 7: QA

Use [pitfalls.md](references/pitfalls.md#qa-process) before calling the deck finished.

### Output Structure

```text
slides/
|-- slide-01.js
|-- slide-02.js
|-- imgs/
`-- output/
    `-- presentation.pptx
```

## Slide Output Format

Each slide file must be complete and runnable on its own for preview generation.

```javascript
// slide-01.js
const pptxgen = require("pptxgenjs");

const slideConfig = {
  type: "cover",
  index: 1,
  title: "Presentation Title"
};

function createSlide(pres, theme) {
  const slide = pres.addSlide();
  slide.background = { color: theme.bg };

  slide.addText(slideConfig.title, {
    x: 0.5,
    y: 2,
    w: 9,
    h: 1.2,
    fontSize: 48,
    fontFace: "Arial",
    color: theme.primary,
    bold: true,
    align: "center"
  });

  return slide;
}

if (require.main === module) {
  (async () => {
    const pres = new pptxgen();
    pres.layout = "LAYOUT_16x9";

    const theme = {
      primary: "22223B",
      secondary: "4A4E69",
      accent: "9A8C98",
      light: "C9ADA7",
      bg: "F2E9E4"
    };

    createSlide(pres, theme);
    await pres.writeFile({ fileName: "slide-01-preview.pptx" });
  })().catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
}

module.exports = { createSlide, slideConfig };
```

## Theme Object Contract

The compile script passes a theme object with these exact keys:

| Key | Purpose | Example |
|-----|---------|---------|
| `theme.primary` | Darkest color, titles | `"22223B"` |
| `theme.secondary` | Dark accent, body text | `"4A4E69"` |
| `theme.accent` | Mid-tone accent | `"9A8C98"` |
| `theme.light` | Light accent | `"C9ADA7"` |
| `theme.bg` | Background color | `"F2E9E4"` |

Never rename these keys to `background`, `text`, `muted`, `darkest`, or `lightest`.

## Page Number Badge

All slides except the cover page must include a page number badge in the bottom-right corner.

- Position: x: 9.3", y: 5.1"
- Show the current number only, such as `3` or `03`
- Keep it subtle and consistent with the deck palette

### Circle Badge

```javascript
slide.addShape(pres.shapes.OVAL, {
  x: 9.3,
  y: 5.1,
  w: 0.4,
  h: 0.4,
  fill: { color: theme.accent }
});

slide.addText("3", {
  x: 9.3,
  y: 5.1,
  w: 0.4,
  h: 0.4,
  fontSize: 12,
  fontFace: "Arial",
  color: "FFFFFF",
  bold: true,
  align: "center",
  valign: "middle"
});
```

### Pill Badge

```javascript
slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 9.1,
  y: 5.15,
  w: 0.6,
  h: 0.35,
  fill: { color: theme.accent },
  rectRadius: 0.15
});

slide.addText("03", {
  x: 9.1,
  y: 5.15,
  w: 0.6,
  h: 0.35,
  fontSize: 11,
  fontFace: "Arial",
  color: "FFFFFF",
  bold: true,
  align: "center",
  valign: "middle"
});
```

## Verification

1. Generate the deck or the slide preview.
2. Extract Markdown with `markitdown`.
3. Search for placeholders with `rg`.
4. Fix issues and re-run extraction until the Markdown view matches the intended content.

## Examples

### Example 1: Extract and analyze an existing deck

```bash
markitdown presentation.pptx -o presentation.md
rg -n -i "xxxx|lorem|ipsum|placeholder" presentation.md
```

### Example 2: Compile a new deck

```bash
cd slides && node compile.js
markitdown output/presentation.pptx -o output/verify.md
```

## Reference Files

| File | Purpose |
|------|---------|
| [slide-types.md](references/slide-types.md) | Slide type contracts, layout choices, and per-type QA |
| [design-system.md](references/design-system.md) | Palettes, font pairings, spacing, and style recipes |
| [editing.md](references/editing.md) | XML-level workflow for template-driven editing |
| [pitfalls.md](references/pitfalls.md) | QA loop and common failure modes |
| [pptxgenjs.md](references/pptxgenjs.md) | API reference and implementation gotchas |

## Verified Docs

- PptxGenJS docs: https://gitbrent.github.io/PptxGenJS/
- MarkItDown README: https://github.com/microsoft/markitdown
- MarkItDown package details: https://pypi.org/project/markitdown/
