const slideConfig = {
  type: "summary",
  index: 4,
  title: "Result"
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

function createSlide(pres, theme) {
  const slide = pres.addSlide();
  slide.background = { color: "FFFFFF" };

  slide.addText(slideConfig.title, {
    x: 0.7,
    y: 0.6,
    w: 2.2,
    h: 0.45,
    margin: 0,
    fontFace: "Arial",
    fontSize: 24,
    bold: true,
    color: theme.primary
  });

  slide.addText("The skill now has a live-generated artifact that proves the core documented workflow can run end to end.", {
    x: 0.7,
    y: 1.18,
    w: 4.8,
    h: 0.42,
    margin: 0,
    fontFace: "Arial",
    fontSize: 12,
    color: theme.secondary
  });

  const boxes = [
    {
      x: 0.75,
      title: "Generated",
      body: "A real PPTX file was written with PptxGenJS."
    },
    {
      x: 3.35,
      title: "Extracted",
      body: "MarkItDown can read the output back to Markdown."
    },
    {
      x: 5.95,
      title: "Reviewed",
      body: "The extracted text can be reviewed for order and completeness."
    }
  ];

  boxes.forEach((box) => {
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: box.x,
      y: 2.05,
      w: 2.15,
      h: 1.75,
      rectRadius: 0.14,
      fill: { color: theme.bg },
      line: { color: theme.light, width: 1 }
    });

    slide.addText(box.title, {
      x: box.x + 0.18,
      y: 2.28,
      w: 1.7,
      h: 0.22,
      margin: 0,
      fontFace: "Arial",
      fontSize: 13,
      bold: true,
      color: theme.primary
    });

    slide.addText(box.body, {
      x: box.x + 0.18,
      y: 2.62,
      w: 1.78,
      h: 0.7,
      margin: 0,
      fontFace: "Arial",
      fontSize: 11,
      color: theme.secondary
    });
  });

  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.75,
    y: 4.35,
    w: 4.2,
    h: 0.46,
    rectRadius: 0.15,
    fill: { color: theme.primary },
    line: { color: theme.primary }
  });

  slide.addText("Next: expand this smoke test into reusable scripts only if you want repeatable CI coverage.", {
    x: 0.95,
    y: 4.35,
    w: 3.8,
    h: 0.46,
    margin: 0,
    fontFace: "Arial",
    fontSize: 11,
    bold: true,
    align: "center",
    valign: "middle",
    color: "FFFFFF"
  });

  addBadge(slide, pres, theme, 4);
  return slide;
}

module.exports = { createSlide, slideConfig };
