import { createRequire } from "node:module";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

if (process.argv.length !== 4) {
  console.error("Usage: node scripts/render-fragment.mjs input.html output.png");
  process.exit(2);
}

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const input = resolve(process.cwd(), process.argv[2]);
const output = resolve(process.cwd(), process.argv[3]);
const executablePath = process.env.CHROME_PATH || undefined;

const browser = await chromium.launch({ headless: true, executablePath });
const page = await browser.newPage({
  viewport: { width: 1080, height: 500 },
  deviceScaleFactor: 1,
});

await page.goto(pathToFileURL(input).href, { waitUntil: "networkidle" });
const box = await page.locator("#capture").boundingBox();
if (!box) {
  await browser.close();
  throw new Error("Cannot find #capture");
}

await page.screenshot({
  path: output,
  clip: { x: 0, y: 0, width: 1080, height: 500 },
  omitBackground: false,
});

await browser.close();
console.log(output);
