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
  await page.locator('#day-info').getByText('Today\'s date:').waitFor();
  await page.locator('#date-input').fill(date);
  await page.locator('#date-input').dispatchEvent('change');
  const [year, month, day] = date.split('-');
  await page.locator('#day-info').getByText(`Today's date: ${month}/${day}/${year}`, { exact: true }).waitFor();
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

async function checkExports(page, context, date, width) {
  const quiz = JSON.parse(fs.readFileSync(path.join(root, `${date}.json`), 'utf8'));
  await page.locator('#play-quiz').click();
  const dialog = page.getByRole('dialog', { name: 'Daily Come Follow Me quiz' });
  const rows = dialog.locator('.cfm-quiz__level-row');
  await rows.first().waitFor();
  assert.equal(await rows.count(), 3);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  for (const [i, level] of ['kid', 'high-school', 'expert'].entries()) {
    const row = rows.nth(i);
    const bounds = await row.boundingBox();
    assert.ok(bounds.x >= 0 && bounds.x + bounds.width <= width, 'level row must fit viewport');
    const popupPromise = page.waitForEvent('popup');
    await row.locator('.cfm-quiz__export').click();
    const popup = await popupPromise;
    await popup.waitForURL('https://quiz-duel.lovable.app/');
    assert.equal(await popup.evaluate(() => window.opener === null), true);
    await page.bringToFront();
    const clipboard = await page.evaluate(() => navigator.clipboard.readText());
    assert.deepEqual(JSON.parse(clipboard), quiz.quizDuel[level]);
    await popup.close();
    assert.match(await row.locator('[role="status"]').textContent(), /JSON copied/);
  }
  // A slow or denied clipboard write must never navigate the reserved tab.
  await page.evaluate(() => {
    window.cfmWriteText = navigator.clipboard.writeText.bind(navigator.clipboard);
    navigator.clipboard.writeText = () => new Promise((resolve, reject) => {
      window.cfmRejectCopy = () => reject(new Error('denied'));
    });
  });
  const deniedPopupPromise = page.waitForEvent('popup');
  await rows.first().locator('.cfm-quiz__export').click();
  const deniedPopup = await deniedPopupPromise;
  assert.equal(deniedPopup.url(), 'about:blank');
  const closed = deniedPopup.waitForEvent('close');
  await page.evaluate(() => window.cfmRejectCopy());
  await closed;
  await rows.first().getByText('Could not copy JSON.', { exact: false }).waitFor();
  assert.equal(await rows.first().locator('.cfm-quiz__export').isEnabled(), true);
  // Successful copy with a blocked popup offers a usable link and keeps JSON.
  await page.evaluate(() => {
    navigator.clipboard.writeText = window.cfmWriteText;
    window.cfmOpen = window.open;
    window.open = () => null;
  });
  await rows.nth(1).locator('.cfm-quiz__export').click();
  const link = rows.nth(1).getByRole('link', { name: 'Open QuizDuel' });
  await link.waitFor();
  assert.equal(await link.getAttribute('href'), 'https://quiz-duel.lovable.app/');
  assert.deepEqual(JSON.parse(await page.evaluate(() => navigator.clipboard.readText())), quiz.quizDuel['high-school']);
  // Browsers without Clipboard API use a synchronous copy fallback.
  await page.evaluate(() => {
    window.cfmClipboard = navigator.clipboard;
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: undefined });
  });
  await rows.nth(2).locator('.cfm-quiz__export').click();
  await rows.nth(2).getByRole('link', { name: 'Open QuizDuel' }).waitFor();
  await page.evaluate(() => {
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: window.cfmClipboard });
    window.open = window.cfmOpen;
  });
  assert.deepEqual(JSON.parse(await page.evaluate(() => navigator.clipboard.readText())), quiz.quizDuel.expert);
  const screenshotPath = process.env.CFM_SCREENSHOT_DIR;
  if (screenshotPath) await page.screenshot({ path: path.join(screenshotPath, `cfm-quizduel-${width}.png`) });
  await dialog.getByRole('button', { name: '✕ Close' }).click();
}

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath });
  const errors = [];
  try {
    for (const width of [390, 1280]) {
      const context = await browser.newContext({ viewport: { width, height: 844 }, hasTouch: width === 390, isMobile: width === 390 });
      await context.grantPermissions(['clipboard-read', 'clipboard-write'], { origin: new URL(url).origin });
      await context.route('https://quiz-duel.lovable.app/**', route => route.fulfill({ contentType: 'text/html', body: '<title>QuizDuel navigation test</title>' }));
      const page = await context.newPage();
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(url);
      await selectDate(page, '2026-09-27');
      await page.locator('#play-quiz').waitFor({ state: 'visible' });
      await checkExports(page, context, '2026-09-27', width);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth), true, `overflow at ${width}`);
      assert.equal(await page.evaluate(() => innerWidth), width, 'content must not expand the mobile layout viewport');
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
      // Exercise the corrected bank and every future prepared date, not only the original sample.
      await selectDate(page, '2026-10-07');
      await checkExports(page, context, '2026-10-07', width);
      if (width === 390) {
        for (const date of ['2026-10-07', '2026-10-08', '2026-10-09', '2026-10-10', '2026-10-11']) {
          await selectDate(page, date);
          for (const level of ['kid', 'high-school', 'expert']) await playLevel(page, level, date);
        }
      }
      await context.close();
    }
    assert.deepEqual(errors, []);
    console.log('CFM quiz browser smoke test passed (mobile, desktop, QuizDuel clipboard/navigation/failures, levels, completion, exit, and reading controls).');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
