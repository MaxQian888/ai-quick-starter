const fs = require("node:fs");
const path = require("node:path");
const pptxgen = require("pptxgenjs");

const slideModules = [
  require("./slide-01"),
  require("./slide-02"),
  require("./slide-03"),
  require("./slide-04")
];

async function main() {
  const outputDir = path.join(__dirname, "output");
  fs.mkdirSync(outputDir, { recursive: true });

  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Codex";
  pres.company = "skills-test";
  pres.subject = "pptx-generator smoke test";
  pres.title = "PPTX Generator Smoke Test";
  pres.lang = "en-US";

  const theme = {
    primary: "22223B",
    secondary: "4A4E69",
    accent: "9A8C98",
    light: "C9ADA7",
    bg: "F2E9E4"
  };

  for (const slideModule of slideModules) {
    slideModule.createSlide(pres, theme);
  }

  const outputFile = path.join(outputDir, "pptx-generator-smoke-test.pptx");
  await pres.writeFile({ fileName: outputFile });
  console.log(outputFile);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
