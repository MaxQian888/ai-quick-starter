const slideConfig = {
  type: "cover",
  index: 1,
  title: "PPTX Generator Smoke Test"
};

function createSlide(pres, theme) {
  const slide = pres.addSlide();
  slide.background = { color: theme.bg };

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0,
    y: 0,
    w: 10,
    h: 5.625,
    fill: { color: theme.bg },
    line: { color: theme.bg }
  });

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.55,
    y: 0.55,
    w: 0.18,
    h: 4.4,
    fill: { color: theme.accent },
    line: { color: theme.accent }
  });

  slide.addText(slideConfig.title, {
    x: 0.95,
    y: 1.05,
    w: 7.7,
    h: 1.1,
    margin: 0,
    fontFace: "Arial",
    fontSize: 27,
    bold: true,
    color: theme.primary
  });

  slide.addText("Verify that the skill can produce a real four-slide deck with a cover, agenda, content, and closing slide.", {
    x: 0.95,
    y: 2.1,
    w: 6.2,
    h: 0.95,
    margin: 0,
    fontFace: "Arial",
    fontSize: 16,
    color: theme.secondary
  });

  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.95,
    y: 3.45,
    w: 2.4,
    h: 0.42,
    rectRadius: 0.12,
    fill: { color: theme.primary },
    line: { color: theme.primary }
  });

  slide.addText("skills-test workspace", {
    x: 0.95,
    y: 3.45,
    w: 2.4,
    h: 0.42,
    margin: 0,
    fontFace: "Arial",
    fontSize: 11,
    bold: true,
    align: "center",
    valign: "middle",
    color: "FFFFFF"
  });

  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 7.25,
    y: 0.8,
    w: 2.05,
    h: 3.95,
    rectRadius: 0.16,
    fill: { color: "FFFFFF" },
    line: { color: theme.light, width: 1 }
  });

  slide.addText("Target checks", {
    x: 7.55,
    y: 1.1,
    w: 1.45,
    h: 0.3,
    margin: 0,
    fontFace: "Arial",
    fontSize: 12,
    bold: true,
    color: theme.primary
  });

  slide.addText([
    { text: "16:9 layout", options: { bullet: true, breakLine: true } },
    { text: "Theme contract", options: { bullet: true, breakLine: true } },
    { text: "Page badges", options: { bullet: true, breakLine: true } },
    { text: "writeFile output", options: { bullet: true } }
  ], {
    x: 7.5,
    y: 1.55,
    w: 1.55,
    h: 1.8,
    margin: 0,
    fontFace: "Arial",
    fontSize: 11,
    color: theme.secondary,
    breakLine: false
  });

  slide.addText("April 13, 2026", {
    x: 0.95,
    y: 4.8,
    w: 2.2,
    h: 0.22,
    margin: 0,
    fontFace: "Arial",
    fontSize: 10,
    color: theme.secondary
  });

  return slide;
}

module.exports = { createSlide, slideConfig };
