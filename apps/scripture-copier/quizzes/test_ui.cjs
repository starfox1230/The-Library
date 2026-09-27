// Browser smoke test. Start a static server at the repository root, then set
// NODE_PATH to a Node installation with Playwright and run this script.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');

const root = __dirname;
const url = process.env.CFM_TEST_URL || 'http://localhost:8765/apps/scripture-copier/cfm-2026.html';
const edge = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const executablePath = process.env.CFM_BROWSER_PATH || (process.platform === 'win32' && fs.existsSync(edge) ? edge : undefined);

async function selectDate(page, date) {
  await page.locator('#date-input').fill(date);
  await page.locator('#date-input').dispatchEvent('change');
  await page.locator('#day-info').getByText('Today\'s date:').waitFor();
}

async function playLevel(page, level, date, quitEarly = false) {
  const quiz = JSON.parse(fs.readFileSync(path.join(root, `${date}.json`), 'utf8'));
  await page.locator('#play-quiz').click();
  const dialog = page.getByRole('dialog', { name: 'Daily Come Follow Me quiz' });
  await dialog.getByRole('button', { name: 'Kid', exact: true }).waitFor();
  assert.equal(await dialog.locator('.cfm-quiz__subtitle').count(), 0);
  assert.equal(await dialog.locator('.cfm-quiz__level small').count(), 0);
  assert.equal(await dialog.getByRole('button', { name: 'Kid', exact: true }).count(), 1);
  await dialog.getByRole('button', { name: new RegExp(`^${level === 'kid' ? 'Kid' : level === 'high-school' ? 'High School' : 'PhD / Expert'}`) }).click();
  const items = quiz.levels[level];
  const end = quitEarly ? 3 : 10;
  for (let i = 0; i < end; i++) {
    await dialog.getByText(`Question ${i + 1} of 10`, { exact: false }).waitFor();
    const item = items[i];
    const right = item.options.find(option => option.id === item.correctOptionId);
    const selected = i === 0 && level === 'high-school' ? item.options.find(option => option.id !== item.correctOptionId) : right;
    const choice = dialog.getByRole('button', { name: selected.text, exact: true });
    if (i === 0) await choice.evaluate(node => { node.click(); node.click(); });
    else await choice.click();
    assert.equal(await dialog.locator('.cfm-quiz__choice.is-correct').count(), 1);
    assert.equal(await dialog.locator('.cfm-quiz__feedback').count(), 1);
    assert.equal(await choice.isDisabled(), true);
    if (i === 0) assert.equal(await dialog.locator('.cfm-quiz__feedback').count(), 1, 'double tap must submit once');
    if (quitEarly && i === end - 1) break;
    await dialog.getByRole('button', { name: i === 9 ? 'See results →' : 'Next question →' }).click();
  }
  if (quitEarly) {
    await dialog.getByRole('button', { name: '✕ Close' }).click();
    assert.equal(await page.locator('#day-info').textContent().then(x => x.includes('09/27/2026')), true);
    assert.equal(await dialog.isHidden(), true);
  } else {
    assert.match(await dialog.locator('.cfm-quiz__score').textContent(), level === 'high-school' ? /9 \/ 10/ : /10 \/ 10/);
    await dialog.getByRole('button', { name: 'Back to today’s reading' }).click();
    assert.equal(await dialog.isHidden(), true);
  }
}

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath });
  const errors = [];
  try {
    for (const width of [390, 1280]) {
      const context = await browser.newContext({ viewport: { width, height: 844 }, hasTouch: width === 390, isMobile: width === 390 });
      const page = await context.newPage();
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(url);
      await selectDate(page, '2026-09-27');
      await page.locator('#play-quiz').waitFor({ state: 'visible' });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, `overflow at ${width}`);
      assert.match(await page.locator('#manual-links a').getAttribute('href'), /week|2026\/39/);
      await page.locator('#toggle-btn').click();
      assert.equal(await page.locator('#toggle-btn').textContent(), 'Show Verses');
      await page.locator('#toggle-btn').click();
      assert.equal(await page.locator('#toggle-btn').textContent(), 'Show Chapters');
      await page.locator('#mode-week').click();
      assert.equal(await page.locator('#play-quiz').isHidden(), true);
      await page.locator('#mode-day').click();
      await page.locator('#play-quiz').waitFor({ state: 'visible' });
      if (width === 390) {
        await playLevel(page, 'kid', '2026-09-27', true);
        await playLevel(page, 'kid', '2026-09-27');
        await playLevel(page, 'high-school', '2026-09-27');
        await playLevel(page, 'expert', '2026-09-27');
      } else {
        await selectDate(page, '2026-10-04');
        await playLevel(page, 'expert', '2026-10-04');
        await page.locator('#prev-btn').click();
        assert.match(await page.locator('#day-info').textContent(), /10\/03\/2026/);
      }
      await context.close();
    }
    assert.deepEqual(errors, []);
    console.log('CFM quiz browser smoke test passed (mobile, desktop, levels, completion, exit, and reading controls).');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
