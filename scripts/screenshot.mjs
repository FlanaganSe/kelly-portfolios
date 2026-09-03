#!/usr/bin/env node
// Screenshot a list of routes on an already-running server, at a desktop and a mobile
// width. Builds nothing and starts nothing: point it at `pnpm preview` or `pnpm dev`.
//
//   node scripts/screenshot.mjs <baseUrl> <outDir> <path>[,<path>...] [--dark] [--full]
//
//   node scripts/screenshot.mjs http://localhost:4321 .claude/scratch/shots /,/portfolios/,/funds/
//
// Each route lands as `<outDir>/<route>.<desktop|mobile>.png`, so `/tools/placement/`
// becomes `tools-placement.desktop.png` and `/` becomes `home.mobile.png`. The exit code
// is 1 if any route answered other than 200 or logged a console error, so the script
// can sit in a shell loop as a check as well as a camera.
//
// `--dark` pins `prefers-color-scheme: dark`; the default is light. `--full` captures
// the whole page rather than the first viewport. `scripts/shoot.mjs` is the older,
// three-width, four-theme variant; this one is the small one meant for a quick look.

import { mkdir } from "node:fs/promises";
import { chromium } from "playwright";

const args = process.argv.slice(2);
const flags = new Set(args.filter((a) => a.startsWith("--")));
const [base, outDir, routeList] = args.filter((a) => !a.startsWith("--"));

if (!base || !outDir || !routeList) {
  console.error("usage: node scripts/screenshot.mjs <baseUrl> <outDir> <path>[,<path>...] [--dark] [--full]");
  process.exit(2);
}

const routes = routeList.split(",").filter(Boolean);
const fullPage = flags.has("--full");
const colorScheme = flags.has("--dark") ? "dark" : "light";

// 1440 is the desktop composition with the margin column open (the aside opens at
// 74rem); 390 is the phone width the stacked tables are designed for.
const widths = [
  ["desktop", 1440, 900],
  ["mobile", 390, 844],
];

const fileName = (route) => route.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "") || "home";

await mkdir(outDir, { recursive: true });
const browser = await chromium.launch();
const problems = [];

for (const [label, width, height] of widths) {
  const context = await browser.newContext({
    viewport: { width, height },
    deviceScaleFactor: 2,
    colorScheme,
  });
  const page = await context.newPage();
  page.on("console", (m) => {
    if (m.type() === "error") problems.push(`${label} ${page.url()} :: console: ${m.text()}`);
  });
  page.on("pageerror", (e) => problems.push(`${label} ${page.url()} :: ${e.message}`));

  for (const route of routes) {
    const url = new URL(route, base).href;
    const res = await page.goto(url, { waitUntil: "networkidle" });
    const status = res?.status() ?? 0;
    if (status !== 200) problems.push(`${label} ${url} :: HTTP ${status}`);
    const file = `${outDir}/${fileName(route)}.${label}.png`;
    await page.screenshot({ path: file, fullPage });
    console.log(`${status} ${route} @${label} -> ${file}`);
  }
  await context.close();
}

await browser.close();

if (problems.length) {
  console.log("\nPROBLEMS:");
  for (const p of problems) console.log(`  ${p}`);
  process.exit(1);
}
console.log("\nall routes 200, no console errors");
