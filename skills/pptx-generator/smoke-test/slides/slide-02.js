const slideConfig = {
  type: "toc",
  index: 2,
  title: "Agenda"
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
    x: 0.6,
    y: 0.55,
    w: 2.1,
    h: 0.45,
    margin: 0,
    fontFace: "Arial",
    fontSize: 24,
    bold: true,
    color: theme.primary
  });

  const items = [
    { num: "01", title: "Scope", body: "Select the narrowest workflow for the incoming PPT task." },
    { num: "02", title: "Build", body: "Create slide modules that obey the documented theme contract." },
    { num: "03", title: "Verify", body: "Extract the generated deck back to Markdown and check the result." }
  ];

  items.forEach((item, index) => {
    const top = 1.45 + index * 1.18;

    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.7,
      y: top,
      w: 0.76,
      h: 0.6,
      rectRadius: 0.12,
      fill: { color: theme.primary },
      line: { color: theme.primary }
    });

    slide.addText(item.num, {
      x: 0.7,
      y: top,
      w: 0.76,
      h: 0.6,
      margin: 0,
      fontFace: "Arial",
      fontSize: 14,
      bold: true,
      align: "center",
      valign: "middle",
      color: "FFFFFF"
    });

    slide.addText(item.title, {
      x: 1.75,
      y: top + 0.03,
      w: 2.15,
      h: 0.25,
      margin: 0,
      fontFace: "Arial",
      fontSize: 17,
      bold: true,
      color: theme.primary
    });

    slide.addText(item.body, {
      x: 1.75,
      y: top + 0.34,
      w: 5.55,
      h: 0.45,
      margin: 0,
      fontFace: "Arial",
      fontSize: 12,
      color: theme.secondary
    });
  });

  slide.addShape(pres.shapes.LINE, {
    x: 7.85,
    y: 1.25,
    w: 0,
    h: 3.55,
    line: { color: theme.light, width: 1.2 }
  });

  slide.addText("Deck shape", {
    x: 8.1,
    y: 1.45,
    w: 1.15,
    h: 0.25,
    margin: 0,
    fontFace: "Arial",
    fontSize: 12,
    bold: true,
    color: theme.primary
  });

  slide.addText([
    { text: "1 cover", options: { bullet: true, breakLine: true } },
    { text: "1 agenda", options: { bullet: true, breakLine: true } },
    { text: "1 content", options: { bullet: true, breakLine: true } },
    { text: "1 closing", options: { bullet: true } }
  ], {
    x: 8.05,
    y: 1.82,
    w: 1.35,
    h: 1.2,
    margin: 0,
    fontFace: "Arial",
    fontSize: 11,
    color: theme.secondary
  });

  addBadge(slide, pres, theme, 2);
  return slide;
}

module.exports = { createSlide, slideConfig };
