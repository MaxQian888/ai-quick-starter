const slideConfig = {
  type: "content",
  index: 3,
  title: "What This Smoke Test Covers"
};

function addBadge(slide, pres, theme, value) {
  slide.addShape(pres.shapes.OVAL, {
    x: 9.3,
    y: 5.1,
    w: 0.4,
    h: 0.4,
    fill: { color: theme.accent },
    line: { color: theme.accent }
  });

  slide.addText(String(value), {
    x: 9.3,
    y: 5.1,
    w: 0.4,
    h: 0.4,
    margin: 0,
    fontFace: "Arial",
    fontSize: 12,
    bold: true,
    align: "center",
    valign: "middle",
    color: "FFFFFF"
  });
}

function createBar(slide, pres, theme, top, label, percent, fillColor) {
  slide.addText(label, {
    x: 0.8,
    y: top,
    w: 2.3,
    h: 0.22,
    margin: 0,
    fontFace: "Arial",
    fontSize: 12,
    bold: true,
    color: theme.primary
  });

  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.8,
    y: top + 0.32,
    w: 4.2,
    h: 0.24,
    rectRadius: 0.1,
    fill: { color: "EDE9EF" },
    line: { color: "EDE9EF" }
  });

  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.8,
    y: top + 0.32,
    w: 4.2 * percent,
    h: 0.24,
    rectRadius: 0.1,
    fill: { color: fillColor },
    line: { color: fillColor }
  });

  slide.addText(`${Math.round(percent * 100)}%`, {
    x: 5.2,
    y: top + 0.26,
    w: 0.6,
    h: 0.25,
    margin: 0,
    fontFace: "Arial",
    fontSize: 11,
    bold: true,
    align: "right",
    color: theme.secondary
  });
}

function createSlide(pres, theme) {
  const slide = pres.addSlide();
  slide.background = { color: theme.bg };

  slide.addText(slideConfig.title, {
    x: 0.7,
    y: 0.55,
    w: 4.2,
    h: 0.45,
    margin: 0,
    fontFace: "Arial",
    fontSize: 24,
    bold: true,
    color: theme.primary
  });

  slide.addText("A real smoke test should prove the documented workflow can create a structured deck, not just sample snippets.", {
    x: 0.7,
    y: 1.08,
    w: 5.3,
    h: 0.5,
    margin: 0,
    fontFace: "Arial",
    fontSize: 12,
    color: theme.secondary
  });

  createBar(slide, pres, theme, 1.9, "Theme object contract", 1.0, theme.primary);
  createBar(slide, pres, theme, 2.75, "Page number badges", 1.0, theme.accent);
  createBar(slide, pres, theme, 3.6, "PPTX write and reopen", 0.95, theme.secondary);

  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 6.35,
    y: 1.55,
    w: 2.7,
    h: 2.6,
    rectRadius: 0.16,
    fill: { color: "FFFFFF" },
    line: { color: theme.light, width: 1 }
  });

  slide.addText("Verification loop", {
    x: 6.65,
    y: 1.83,
    w: 1.9,
    h: 0.25,
    margin: 0,
    fontFace: "Arial",
    fontSize: 13,
    bold: true,
    color: theme.primary
  });

  slide.addText([
    { text: "Build the deck", options: { bullet: true, breakLine: true } },
    { text: "Extract Markdown", options: { bullet: true, breakLine: true } },
    { text: "Check for leftover text", options: { bullet: true, breakLine: true } },
    { text: "Confirm slide text", options: { bullet: true } }
  ], {
    x: 6.58,
    y: 2.22,
    w: 1.95,
    h: 1.35,
    margin: 0,
    fontFace: "Arial",
    fontSize: 11,
    color: theme.secondary
  });

  addBadge(slide, pres, theme, 3);
  return slide;
}

module.exports = { createSlide, slideConfig };
