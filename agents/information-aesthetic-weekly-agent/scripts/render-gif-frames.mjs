import { createRequire } from "node:module";
import { mkdirSync } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

if (process.argv.length !== 8) {
  console.error("Usage: node render-gif-frames.mjs input.html output-dir width height frame-count frame-delay-ms");
  process.exit(2);
}

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const input = resolve(process.cwd(), process.argv[2]);
const outputDir = resolve(process.cwd(), process.argv[3]);
const width = Number(process.argv[4]);
const height = Number(process.argv[5]);
const frameCount = Number(process.argv[6]);
const frameDelay = Number(process.argv[7]);
const executablePath = process.env.CHROME_PATH || undefined;

mkdirSync(outputDir, { recursive: true });

const browser = await chromium.launch({ headless: true, executablePath });
const page = await browser.newPage({
  viewport: { width, height },
  deviceScaleFactor: 1,
});

await page.goto(pathToFileURL(input).href, { waitUntil: "networkidle" });
await page.locator("#capture").waitFor();

for (let idx = 0; idx < frameCount; idx += 1) {
  await page.screenshot({
    path: resolve(outputDir, `frame-${String(idx).padStart(3, "0")}.png`),
    clip: { x: 0, y: 0, width, height },
    omitBackground: false,
  });
  await page.waitForTimeout(frameDelay);
}

await browser.close();
console.log(outputDir);
