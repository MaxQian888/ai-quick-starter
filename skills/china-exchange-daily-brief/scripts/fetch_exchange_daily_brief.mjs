#!/usr/bin/env node

import { writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

const DEFAULT_TIMEOUT_MS = 25000;
const DEFAULT_MAX_ITEMS = 3;
const USER_AGENT =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36";

const EXCHANGE_DEFINITIONS = [
  {
    id: "sse",
    name: "上海证券交易所",
    listUrl: "https://www.sse.com.cn/aboutus/mediacenter/hotandd/",
    logo: "https://www.sse.com.cn/xhtml/images/logo.png",
    parseList: parseSseList,
  },
  {
    id: "szse",
    name: "深圳证券交易所",
    listUrl: "https://www.szse.cn/aboutus/trends/news/",
    logo: "https://res.szse.cn/common/images/logo.png",
    parseList: parseSzseList,
  },
  {
    id: "hkex",
    name: "香港交易所",
    listUrl: "https://www.hkex.com.hk/News/News-Release?sc_lang=zh-CN",
    logo: "https://www.hkex.com.hk/assets/images/HKEX-Logo.png",
    parseList: parseHkexList,
  },
  {
    id: "bse",
    name: "北京证券交易所",
    listUrl: "https://www.bse.cn/important_news",
    logo: "https://www.bse.cn/images/logo.png",
    parseList: parseBseList,
  },
];

const HELP_TEXT = `
抓取中国主要证券交易所的每日动态并输出逐条摘要。

用法:
  node scripts/fetch_exchange_daily_brief.mjs [选项]

选项:
  --date YYYY-MM-DD            指定目标日期（默认: 亚洲/上海当天）
  --max-items N                每个交易所最多输出 N 条（默认: 3）
  --strict-date                仅输出指定日期条目；无当天条目时不回退
  --include-bse                加入北交所抓取（默认关闭，因部分网络环境会被官方 WAF 拒绝）
  --format markdown|json       输出格式（默认: markdown）
  --output PATH                将结果写入文件
  --timeout-ms N               单次网络请求超时毫秒数（默认: 25000）
  --help                       显示帮助
`;

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    process.stdout.write(HELP_TEXT.trimStart());
    return;
  }

  const targetDate = options.date ?? getShanghaiDateString();
  assertDate(targetDate, "--date");

  const exchanges = EXCHANGE_DEFINITIONS.filter(
    (exchange) => exchange.id !== "bse" || options.includeBse,
  );

  const reports = [];
  for (const exchange of exchanges) {
    reports.push(await buildExchangeReport(exchange, targetDate, options));
  }

  const result = {
    targetDate,
    generatedAt: new Date().toISOString(),
    options: {
      maxItems: options.maxItems,
      strictDate: options.strictDate,
      includeBse: options.includeBse,
      timeoutMs: options.timeoutMs,
    },
    exchanges: reports,
  };

  const outputText =
    options.format === "json"
      ? JSON.stringify(result, null, 2)
      : buildMarkdown(result);

  if (options.output) {
    await writeFile(options.output, outputText, "utf8");
  }

  process.stdout.write(outputText);
  if (!outputText.endsWith("\n")) {
    process.stdout.write("\n");
  }

  const usableCount = reports.filter(
    (item) => item.status !== "error" && item.items.length > 0,
  ).length;
  if (usableCount === 0) {
    process.exitCode = 1;
  }
}

async function buildExchangeReport(exchange, targetDate, options) {
  const report = {
    id: exchange.id,
    name: exchange.name,
    listUrl: exchange.listUrl,
    status: "ok",
    dateMode: "same-day",
    message: "",
    items: [],
  };

  let listHtml;
  try {
    listHtml = await fetchText(exchange.listUrl, options.timeoutMs);
  } catch (error) {
    report.status = "error";
    report.message = `列表抓取失败: ${error.message}`;
    return report;
  }

  let parsedItems = [];
  try {
    parsedItems = dedupeItems(exchange.parseList(listHtml, exchange.listUrl));
  } catch (error) {
    report.status = "error";
    report.message = `列表解析失败: ${error.message}`;
    return report;
  }

  if (parsedItems.length === 0) {
    report.status = "error";
    report.message = "列表解析后无条目";
    return report;
  }

  const sameDayItems = parsedItems.filter((item) => item.date === targetDate);
  const selectedItems = sameDayItems.length
    ? sameDayItems.slice(0, options.maxItems)
    : options.strictDate
      ? []
      : parsedItems.slice(0, options.maxItems);

  if (!sameDayItems.length) {
    if (options.strictDate) {
      report.status = "partial";
      report.message = "无当天条目（strict-date 已开启，不回退）";
      report.dateMode = "same-day";
    } else {
      report.status = "partial";
      report.message = "无当天条目，已回退到最新可用条目";
      report.dateMode = "latest-fallback";
    }
  }

  for (const item of selectedItems) {
    report.items.push(await enrichItem(exchange, item, options.timeoutMs));
  }

  if (report.status === "ok" && report.items.length === 0) {
    report.status = "partial";
    report.message = "未命中可输出条目";
  }

  return report;
}

async function enrichItem(exchange, item, timeoutMs) {
  const result = {
    exchange: exchange.name,
    title: item.title,
    date: item.date || "未知日期",
    link: item.url,
    image: exchange.logo,
    summary: summarizeText(item.title, item.title),
    detailStatus: "fallback",
    detailNote: "",
  };

  if (!item.url) {
    result.detailNote = "缺少详情链接";
    return result;
  }

  try {
    const detailHtml = await fetchText(item.url, timeoutMs);
    const image = extractBestImage(detailHtml, item.url, exchange.logo);
    const text = extractBestArticleText(detailHtml);
    result.image = image;
    result.summary = summarizeText(text, item.title);
    result.detailStatus = "ok";
    return result;
  } catch (error) {
    result.detailNote = `详情抓取失败: ${error.message}`;
    return result;
  }
}

function parseSseList(html, baseUrl) {
  const items = [];
  const pattern =
    /<dd>\s*<span>\s*(\d{4}-\d{2}-\d{2})\s*<\/span>\s*<a[^>]*href="([^"]+)"[^>]*title="([^"]+)"[^>]*>/gim;
  for (const match of html.matchAll(pattern)) {
    items.push({
      date: normalizeDate(match[1]),
      url: resolveUrl(baseUrl, decodeHtmlEntities(match[2])),
      title: cleanText(decodeHtmlEntities(match[3])),
    });
  }
  return items;
}

function parseSzseList(html, baseUrl) {
  const items = [];
  const liBlocks = html.match(/<li\b[\s\S]*?<\/li>/gim) ?? [];
  for (const li of liBlocks) {
    const hrefRaw = extractJsVar(li, "curHref");
    const titleRaw = extractJsVar(li, "curTitle");
    const dateRaw = li.match(/(\d{4}-\d{2}-\d{2})/)?.[1] ?? "";
    const href = hrefRaw ? decodeJsString(hrefRaw) : "";
    const title = titleRaw ? decodeJsString(titleRaw) : "";
    if (!href || !title) {
      continue;
    }
    items.push({
      date: normalizeDate(dateRaw) || normalizeDateFromSzseHref(href),
      url: resolveUrl(baseUrl, href),
      title: cleanText(decodeHtmlEntities(title)),
    });
  }
  return items;
}

function parseHkexList(html, baseUrl) {
  const items = [];
  const anchorPattern =
    /<a[^>]*href="([^"]*\/News\/News-Release[^"]*)"[^>]*>([\s\S]*?)<\/a>/gim;

  for (const match of html.matchAll(anchorPattern)) {
    const hrefRaw = decodeHtmlEntities(match[1]);
    const textRaw = match[2];
    const fullUrl = resolveUrl(baseUrl, hrefRaw);
    if (
      /\/News\/News-Release\/?(\?|$)/i.test(fullUrl) ||
      /\/News\/News-Release\/index/i.test(fullUrl)
    ) {
      continue;
    }

    const title = cleanText(stripHtml(textRaw));
    if (title.length < 6 || /^(企业新闻|News Release)$/i.test(title)) {
      continue;
    }

    const context = html.slice(
      Math.max(0, (match.index ?? 0) - 260),
      Math.min(html.length, (match.index ?? 0) + 500),
    );

    const date =
      normalizeDate(extractDateFromHkexUrl(fullUrl)) ||
      normalizeDate(extractDateFromContext(context));

    items.push({
      date,
      url: fullUrl,
      title,
    });
  }

  return items;
}

function parseBseList(html, baseUrl) {
  const items = [];
  const pattern =
    /<li\b[\s\S]*?(?:<span[^>]*>\s*(\d{4}-\d{2}-\d{2})\s*<\/span>)?[\s\S]*?<a[^>]*href="([^"]+)"[^>]*(?:title="([^"]*)")?[^>]*>([\s\S]*?)<\/a>[\s\S]*?<\/li>/gim;

  for (const match of html.matchAll(pattern)) {
    const date = normalizeDate(match[1] ?? "");
    const href = decodeHtmlEntities(match[2] ?? "");
    const title =
      cleanText(decodeHtmlEntities(match[3] ?? "")) ||
      cleanText(stripHtml(decodeHtmlEntities(match[4] ?? "")));
    if (!href || !title) {
      continue;
    }
    items.push({
      date,
      url: resolveUrl(baseUrl, href),
      title,
    });
  }

  return items;
}

function buildMarkdown(result) {
  const lines = [];
  lines.push(`# 中国证券交易所动态简报（${result.targetDate}）`);
  lines.push("");
  lines.push(`生成时间：${result.generatedAt}`);
  lines.push("");

  for (const exchange of result.exchanges) {
    lines.push(`## ${exchange.name}`);
    lines.push(`- 列表源：<${exchange.listUrl}>`);
    lines.push(`- 状态：${formatExchangeStatus(exchange)}`);
    lines.push("");

    if (!exchange.items.length) {
      lines.push("- 无可输出条目");
      lines.push("");
      continue;
    }

    let index = 1;
    for (const item of exchange.items) {
      lines.push(`### ${index}. ${item.title}`);
      lines.push(`- 日期：${item.date}`);
      lines.push(`- 摘要：${item.summary}`);
      lines.push(`- 链接：[原文](<${item.link}>)`);
      lines.push(`- 配图：![${exchange.id}-${index}](<${item.image}>)`);
      if (item.detailStatus !== "ok" && item.detailNote) {
        lines.push(`- 备注：${item.detailNote}`);
      }
      lines.push("");
      index += 1;
    }
  }

  return lines.join("\n").trimEnd() + "\n";
}

function formatExchangeStatus(exchange) {
  const base =
    exchange.status === "ok"
      ? "成功（当天条目）"
      : exchange.status === "partial"
        ? "部分成功"
        : "失败";
  if (!exchange.message) {
    return base;
  }
  return `${base} - ${exchange.message}`;
}

function dedupeItems(items) {
  const seen = new Set();
  const output = [];
  for (const item of items) {
    const key = `${item.url}@@${item.title}`;
    if (!item.url || !item.title || seen.has(key)) {
      continue;
    }
    seen.add(key);
    output.push(item);
  }
  return output;
}

function extractBestArticleText(html) {
  const metaDescription =
    extractMetaContent(html, "name", "description") ||
    extractMetaContent(html, "property", "og:description") ||
    extractMetaContent(html, "name", "twitter:description");

  if (metaDescription && cleanText(metaDescription).length >= 24) {
    return cleanText(metaDescription);
  }

  const paragraphs = [];
  for (const match of html.matchAll(/<p\b[^>]*>([\s\S]*?)<\/p>/gim)) {
    const text = cleanText(stripHtml(match[1]));
    if (isGoodParagraph(text)) {
      paragraphs.push(text);
    }
  }

  if (paragraphs.length > 0) {
    return paragraphs.slice(0, 3).join("");
  }

  return cleanText(stripHtml(html));
}

function extractBestImage(html, detailUrl, fallback) {
  const candidates = [];
  const og = extractMetaContent(html, "property", "og:image");
  const twitter = extractMetaContent(html, "name", "twitter:image");
  if (og) {
    candidates.push(og);
  }
  if (twitter) {
    candidates.push(twitter);
  }

  for (const match of html.matchAll(/<img\b[^>]*src="([^"]+)"[^>]*>/gim)) {
    candidates.push(match[1]);
  }

  for (const candidate of candidates) {
    const normalized = resolveUrl(detailUrl, decodeHtmlEntities(candidate));
    if (isLikelyContentImage(normalized)) {
      return normalized;
    }
  }
  return fallback;
}

function summarizeText(text, fallbackTitle, maxLen = 120) {
  const candidate = cleanText(text) || cleanText(fallbackTitle) || "暂无摘要";
  const parts = candidate
    .split(/(?<=[。！？!?；;])/u)
    .map((part) => cleanText(part))
    .filter(Boolean);

  let summary = "";
  for (const part of parts) {
    if (summary.length + part.length > maxLen) {
      break;
    }
    summary += part;
    if (summary.length >= 60) {
      break;
    }
  }

  if (!summary) {
    summary = candidate.slice(0, maxLen);
  }

  if (summary.length > maxLen) {
    summary = `${summary.slice(0, maxLen - 1)}…`;
  }
  return summary;
}

function isGoodParagraph(text) {
  if (!text || text.length < 24) {
    return false;
  }
  const badTokens = [
    "扫一扫",
    "免责声明",
    "返回顶部",
    "打印",
    "附件",
    "点击下载",
    "分享至",
  ];
  return !badTokens.some((token) => text.includes(token));
}

function isLikelyContentImage(url) {
  if (!url || /^data:/i.test(url) || /\.svg(\?|$)/i.test(url)) {
    return false;
  }
  const rejectTokens = [
    "logo",
    "icon",
    "favicon",
    "qrcode",
    "二维码",
    "ewm",
    "beian",
    "conac",
    "share",
    "wechat",
    "weibo",
  ];
  return !rejectTokens.some((token) => url.toLowerCase().includes(token));
}

function extractMetaContent(html, attrName, attrValue) {
  const escaped = escapeRegex(attrValue);
  const patternA = new RegExp(
    `<meta[^>]*${attrName}=["']${escaped}["'][^>]*content=["']([^"']+)["'][^>]*>`,
    "i",
  );
  const patternB = new RegExp(
    `<meta[^>]*content=["']([^"']+)["'][^>]*${attrName}=["']${escaped}["'][^>]*>`,
    "i",
  );
  const matched = patternA.exec(html) ?? patternB.exec(html);
  return matched ? cleanText(decodeHtmlEntities(matched[1])) : "";
}

function extractJsVar(text, varName) {
  const regex = new RegExp(
    String.raw`(?:^|[\r\n])\s*var\s+${escapeRegex(
      varName,
    )}\s*=\s*'((?:\\.|[^'])*)'`,
    "g",
  );
  let value = "";
  for (const match of text.matchAll(regex)) {
    value = match[1];
  }
  return value;
}

function decodeJsString(value) {
  return value
    .replace(/\\'/g, "'")
    .replace(/\\"/g, '"')
    .replace(/\\n/g, " ")
    .replace(/\\r/g, " ")
    .replace(/\\\\/g, "\\");
}

function normalizeDateFromSzseHref(href) {
  const matched = href.match(/t(\d{4})(\d{2})(\d{2})_/);
  if (!matched) {
    return "";
  }
  return `${matched[1]}-${matched[2]}-${matched[3]}`;
}

function extractDateFromHkexUrl(url) {
  const matched = url.match(/\/News\/News-Release\/(\d{4})\/(\d{6})/i);
  if (!matched) {
    return "";
  }
  const year = matched[1];
  const code = matched[2];
  const month = code.slice(2, 4);
  const day = code.slice(4, 6);
  return `${year}-${month}-${day}`;
}

function extractDateFromContext(text) {
  const candidate =
    text.match(/\b\d{4}[-/.]\d{1,2}[-/.]\d{1,2}\b/)?.[0] ??
    text.match(/\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b/)?.[0] ??
    text.match(/\b[A-Za-z]{3,9}\s+\d{1,2},\s*\d{4}\b/)?.[0] ??
    text.match(/\d{4}年\d{1,2}月\d{1,2}日/)?.[0];
  return candidate || "";
}

function normalizeDate(input) {
  const text = cleanText(input);
  if (!text) {
    return "";
  }

  let matched = text.match(/^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$/);
  if (matched) {
    return formatDateParts(matched[1], matched[2], matched[3]);
  }

  matched = text.match(/^(\d{4})年(\d{1,2})月(\d{1,2})日$/);
  if (matched) {
    return formatDateParts(matched[1], matched[2], matched[3]);
  }

  matched = text.match(/^(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})$/);
  if (matched) {
    const month = monthNameToNumber(matched[2]);
    return month ? formatDateParts(matched[3], month, matched[1]) : "";
  }

  matched = text.match(/^([A-Za-z]{3,9})\s+(\d{1,2}),\s*(\d{4})$/);
  if (matched) {
    const month = monthNameToNumber(matched[1]);
    return month ? formatDateParts(matched[3], month, matched[2]) : "";
  }

  return "";
}

function monthNameToNumber(name) {
  const map = {
    jan: "01",
    january: "01",
    feb: "02",
    february: "02",
    mar: "03",
    march: "03",
    apr: "04",
    april: "04",
    may: "05",
    jun: "06",
    june: "06",
    jul: "07",
    july: "07",
    aug: "08",
    august: "08",
    sep: "09",
    sept: "09",
    september: "09",
    oct: "10",
    october: "10",
    nov: "11",
    november: "11",
    dec: "12",
    december: "12",
  };
  return map[name.toLowerCase()] ?? "";
}

function formatDateParts(year, month, day) {
  const y = String(year).padStart(4, "0");
  const m = String(month).padStart(2, "0");
  const d = String(day).padStart(2, "0");
  if (!/^\d{4}$/.test(y) || !/^\d{2}$/.test(m) || !/^\d{2}$/.test(d)) {
    return "";
  }
  const monthNum = Number(m);
  const dayNum = Number(d);
  if (monthNum < 1 || monthNum > 12 || dayNum < 1 || dayNum > 31) {
    return "";
  }
  return `${y}-${m}-${d}`;
}

function getShanghaiDateString() {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
}

function assertDate(value, flagName) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    throw new Error(`${flagName} 必须是 YYYY-MM-DD`);
  }
}

function parseArgs(argv) {
  const options = {
    date: "",
    strictDate: false,
    includeBse: false,
    format: "markdown",
    output: "",
    maxItems: DEFAULT_MAX_ITEMS,
    timeoutMs: DEFAULT_TIMEOUT_MS,
    help: false,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--date") {
      options.date = requireArgValue(argv, i, "--date");
      i += 1;
    } else if (arg === "--max-items") {
      const value = Number(requireArgValue(argv, i, "--max-items"));
      if (!Number.isInteger(value) || value < 1) {
        throw new Error("--max-items 必须是正整数");
      }
      options.maxItems = value;
      i += 1;
    } else if (arg === "--strict-date") {
      options.strictDate = true;
    } else if (arg === "--include-bse") {
      options.includeBse = true;
    } else if (arg === "--format") {
      const value = requireArgValue(argv, i, "--format");
      if (value !== "markdown" && value !== "json") {
        throw new Error("--format 仅支持 markdown 或 json");
      }
      options.format = value;
      i += 1;
    } else if (arg === "--output") {
      options.output = requireArgValue(argv, i, "--output");
      i += 1;
    } else if (arg === "--timeout-ms") {
      const value = Number(requireArgValue(argv, i, "--timeout-ms"));
      if (!Number.isInteger(value) || value < 1000) {
        throw new Error("--timeout-ms 必须是 >=1000 的整数");
      }
      options.timeoutMs = value;
      i += 1;
    } else if (arg === "--help" || arg === "-h") {
      options.help = true;
    } else {
      throw new Error(`未知参数: ${arg}`);
    }
  }
  return options;
}

function requireArgValue(argv, index, name) {
  const value = argv[index + 1];
  if (!value || value.startsWith("--")) {
    throw new Error(`${name} 缺少参数值`);
  }
  return value;
}

async function fetchText(url, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      method: "GET",
      redirect: "follow",
      signal: controller.signal,
      headers: {
        "user-agent": USER_AGENT,
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      },
    });
    if (!response.ok) {
      throw new Error(`${response.status} ${response.statusText}`);
    }
    return await response.text();
  } finally {
    clearTimeout(timer);
  }
}

function resolveUrl(baseUrl, maybeRelative) {
  try {
    return new URL(maybeRelative, baseUrl).toString();
  } catch {
    return maybeRelative;
  }
}

function stripHtml(input) {
  return input
    .replace(/<script\b[\s\S]*?<\/script>/gim, " ")
    .replace(/<style\b[\s\S]*?<\/style>/gim, " ")
    .replace(/<[^>]+>/gim, " ");
}

function cleanText(input) {
  return decodeHtmlEntities(input ?? "")
    .replace(/\u00a0/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function decodeHtmlEntities(text) {
  const entityMap = {
    amp: "&",
    lt: "<",
    gt: ">",
    quot: '"',
    apos: "'",
    nbsp: " ",
    mdash: "-",
    ndash: "-",
    middot: "·",
    hellip: "…",
  };

  return String(text).replace(/&(#x?[0-9a-fA-F]+|[a-zA-Z]+);/g, (full, value) => {
    if (value.startsWith("#x") || value.startsWith("#X")) {
      const num = Number.parseInt(value.slice(2), 16);
      return Number.isNaN(num) ? full : String.fromCodePoint(num);
    }
    if (value.startsWith("#")) {
      const num = Number.parseInt(value.slice(1), 10);
      return Number.isNaN(num) ? full : String.fromCodePoint(num);
    }
    const mapped = entityMap[value.toLowerCase()];
    return mapped ?? full;
  });
}

function escapeRegex(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export {
  buildMarkdown,
  parseSseList,
  parseSzseList,
  parseHkexList,
  parseBseList,
  normalizeDate,
  summarizeText,
};

const isDirectRun =
  process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;

if (isDirectRun) {
  main().catch((error) => {
    process.stderr.write(`ERROR: ${error.message}\n`);
    process.exitCode = 1;
  });
}
