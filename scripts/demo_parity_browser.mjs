// Drives the demo page in headless Chromium for every parity case and writes the raw results.
//   npm i playwright && npx playwright install chromium
//   node scripts/demo_parity_browser.mjs https://saadosama10.github.io/diet-optimization/demo/ browser.json
import { chromium } from 'playwright';
import fs from 'node:fs';

const [url, outFile = 'browser.json'] = process.argv.slice(2);
const cases = [];
for (const u of [1, 2]) for (const a of ['nsga2', 'spea2']) for (const s of [42, 2024]) cases.push([u, a, s]);

const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto(url);
await page.waitForFunction(() => !document.getElementById('run').disabled, null, { timeout: 300000 });
const out = {};
for (const [u, a, s] of cases) {
  await page.selectOption('#user', String(u));
  await page.click(`[data-algo="${a}"]`);
  await page.fill('#seed', String(s));
  await page.evaluate(() => { window.__demoResult = null; });
  const t0 = Date.now();
  await page.click('#run');
  await page.waitForFunction(() => window.__demoResult, null, { timeout: 300000 });
  out[`user${u}_${a}_seed${s}`] = await page.evaluate(() => window.__demoResult);
  console.log(`user${u} ${a} seed ${s}: ${((Date.now() - t0) / 1000).toFixed(1)} s`);
}
fs.writeFileSync(outFile, JSON.stringify(out));
await browser.close();
