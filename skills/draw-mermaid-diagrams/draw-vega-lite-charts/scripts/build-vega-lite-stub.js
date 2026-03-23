#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");

function printUsage() {
  console.error(
    [
      "Usage:",
      "  node scripts/build-vega-lite-stub.js --config <config.json> [--out <spec.json>]",
      "",
      "Config schema (minimal):",
      '{ "mark": "bar", "encoding": { "x": {...}, "y": {...} } }',
    ].join("\n"),
  );
}

function parseArgs(argv) {
  const args = { config: null, out: null };
  for (let i = 2; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === "--config") {
      args.config = argv[i + 1] || null;
      i += 1;
      continue;
    }
    if (token === "--out") {
      args.out = argv[i + 1] || null;
      i += 1;
      continue;
    }
    throw new Error(`Unknown argument: ${token}`);
  }
  if (!args.config) {
    throw new Error("Missing required --config argument.");
  }
  return args;
}

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function loadConfig(configPath) {
  const abs = path.resolve(configPath);
  if (!fs.existsSync(abs)) {
    throw new Error(`Config file not found: ${abs}`);
  }
  const raw = fs.readFileSync(abs, "utf8");
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (err) {
    throw new Error(`Config must be valid JSON: ${err.message}`);
  }
  if (!isObject(parsed)) {
    throw new Error("Config root must be a JSON object.");
  }
  return parsed;
}

function ensureEncoding(encoding) {
  if (!isObject(encoding)) {
    throw new Error("`encoding` must be an object with channel definitions.");
  }
  const channels = Object.keys(encoding);
  if (channels.length === 0) {
    throw new Error("`encoding` must include at least one channel.");
  }
}

function buildSpec(cfg) {
  const schemaUrl = cfg.schemaUrl || "https://vega.github.io/schema/vega-lite/v5.json";
  if (!cfg.mark) {
    throw new Error("`mark` is required.");
  }
  ensureEncoding(cfg.encoding);

  const spec = {
    $schema: schemaUrl,
    data: isObject(cfg.data) ? cfg.data : { url: cfg.dataUrl || "data.csv" },
    mark: cfg.mark,
    encoding: cfg.encoding,
  };

  if (cfg.title) spec.title = cfg.title;
  if (cfg.description) spec.description = cfg.description;
  if (typeof cfg.width !== "undefined") spec.width = cfg.width;
  if (typeof cfg.height !== "undefined") spec.height = cfg.height;
  if (Array.isArray(cfg.transform)) spec.transform = cfg.transform;
  if (Array.isArray(cfg.params)) spec.params = cfg.params;
  if (isObject(cfg.config)) spec.config = cfg.config;

  return spec;
}

function writeOutput(spec, outPath) {
  const json = JSON.stringify(spec, null, 2) + "\n";
  if (!outPath) {
    process.stdout.write(json);
    return;
  }
  const absOut = path.resolve(outPath);
  fs.mkdirSync(path.dirname(absOut), { recursive: true });
  fs.writeFileSync(absOut, json, "utf8");
}

function main() {
  try {
    const { config, out } = parseArgs(process.argv);
    const cfg = loadConfig(config);
    const spec = buildSpec(cfg);
    writeOutput(spec, out);
  } catch (err) {
    console.error(`Error: ${err.message}`);
    printUsage();
    process.exitCode = 1;
  }
}

main();
