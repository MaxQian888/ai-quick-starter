import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  buildMarkdown,
  parseSseList,
  parseSzseList,
} from "../scripts/fetch_exchange_daily_brief.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const scriptPath = resolve(__dirname, "../scripts/fetch_exchange_daily_brief.mjs");

test("help output is available without network access", () => {
  const result = spawnSync(process.execPath, [scriptPath, "--help"], {
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /用法:/);
  assert.match(result.stdout, /--format markdown\|json/);
});

test("parseSseList extracts dated titles and absolute links", () => {
  const html = `
    <dd>
      <span>2026-04-11</span>
      <a href="/aboutus/mediacenter/hotandd/c/123.html" title="上交所发布新规"></a>
    </dd>
  `;

  const items = parseSseList(html, "https://www.sse.com.cn/aboutus/mediacenter/hotandd/");

  assert.equal(items.length, 1);
  assert.equal(items[0].date, "2026-04-11");
  assert.equal(items[0].title, "上交所发布新规");
  assert.equal(items[0].url, "https://www.sse.com.cn/aboutus/mediacenter/hotandd/c/123.html");
});

test("parseSzseList resolves JS variables and inferred dates", () => {
  const html = `
    <li>
      <script>
        var curHref = '/aboutus/trends/news/t20260411_12345.html';
        var curTitle = '深交所发布通知';
      </script>
    </li>
  `;

  const items = parseSzseList(html, "https://www.szse.cn/aboutus/trends/news/");

  assert.equal(items.length, 1);
  assert.equal(items[0].date, "2026-04-11");
  assert.equal(items[0].title, "深交所发布通知");
  assert.equal(items[0].url, "https://www.szse.cn/aboutus/trends/news/t20260411_12345.html");
});

test("buildMarkdown renders exchange status and item summaries", () => {
  const markdown = buildMarkdown({
    targetDate: "2026-04-11",
    generatedAt: "2026-04-11T08:00:00.000Z",
    exchanges: [
      {
        name: "上海证券交易所",
        listUrl: "https://www.sse.com.cn/aboutus/mediacenter/hotandd/",
        status: "partial",
        message: "无当天条目，已回退到最新可用条目",
        items: [
          {
            title: "上交所发布新规",
            date: "2026-04-10",
            summary: "围绕交易规则进行了更新。",
            link: "https://www.sse.com.cn/aboutus/mediacenter/hotandd/c/123.html",
            image: "https://www.sse.com.cn/xhtml/images/logo.png",
            detailStatus: "fallback",
            detailNote: "详情抓取失败",
          },
        ],
      },
    ],
  });

  assert.match(markdown, /中国证券交易所动态简报（2026-04-11）/);
  assert.match(markdown, /部分成功 - 无当天条目，已回退到最新可用条目/);
  assert.match(markdown, /上交所发布新规/);
  assert.match(markdown, /围绕交易规则进行了更新。/);
});
