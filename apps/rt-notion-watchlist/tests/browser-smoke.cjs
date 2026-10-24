// Exercises the real unpacked extension in a disposable Chromium profile.
// The only network destination used by saves is replaced inside the worker.
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const assert = require('node:assert/strict');

(async () => {
  const profile = await fs.mkdtemp(path.join(os.tmpdir(), 'next-up-chrome-test-'));
  const extension = path.resolve(__dirname, '../extension');
  const output = process.env.QA_OUTPUT || path.join(profile, 'screenshots');
  await fs.mkdir(output, {recursive: true});
  const context = await chromium.launchPersistentContext(profile, {
    executablePath: process.env.BROWSER_EXECUTABLE,
    headless: true, viewport: {width: 1280, height: 900},
    args: [`--disable-extensions-except=${extension}`, `--load-extension=${extension}`]
  });
  try {
    const worker = context.serviceWorkers()[0] || await context.waitForEvent('serviceworker');
    const id = new URL(worker.url()).host;
    async function waitWorker(check) {
      const deadline = Date.now() + 10000;
      while (Date.now() < deadline) {
        if (await worker.evaluate(check)) return;
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      throw new Error('Timed out waiting for extension worker');
    }
    await worker.evaluate(() => {
      globalThis.testCalls = [];
      globalThis.testMode = 'new';
      globalThis.fetch = async (url, options) => {
        globalThis.testCalls.push({url, body: options.body ? JSON.parse(options.body) : null});
        const schema = {properties: {Name: {type: 'title'}, Status: {type: 'select', select: {options: [{name: 'For Later'}]}}, Type: {type: 'select', select: {options: [{name: 'Movie'}, {name: 'TV Show'}]}}, 'Rotten Tomatoes': {type: 'url'}, 'Date Added to Watchlist': {type: 'date'}}};
        const page = {id: '12345678-1234-1234-1234-123456789abc'};
        if (globalThis.testMode === 'error') return new Response('{}', {status: 401});
        if (url.endsWith('/query')) {
          const body = JSON.parse(options.body);
          const match = globalThis.testMode === 'existing' || (globalThis.testMode === 'legacy' && body.filter?.and);
          return Response.json({results: match ? [page] : []});
        }
        return Response.json(url.endsWith('/pages') ? page : schema);
      };
    });
    const options = await context.newPage();
    await options.goto(`chrome-extension://${id}/options.html`);
    await options.getByText('Not connected yet.', {exact: false}).waitFor();
    await options.locator('#token').fill('local-test-placeholder');
    await options.locator('#submit').click();
    await options.getByText('Connected. Refresh', {exact: false}).waitFor();
    assert.equal(await options.locator('#token').inputValue(), '');
    await options.locator('#auto-open').check();
    assert.equal(await options.evaluate(async () => (await chrome.storage.local.get('openAfterSave')).openAfterSave), true);
    await options.locator('#auto-open').uncheck();
    await options.screenshot({path: path.join(output, 'settings.png'), fullPage: true});

    await context.route('https://www.rottentomatoes.com/**', route => {
      const tv = route.request().url().includes('/tv/');
      return route.fulfill({contentType: 'text/html; charset=utf-8', body: `<!doctype html><html><head><meta charset="utf-8"><title>Rotten Tomatoes</title></head><body style="margin:0;background:#eee;font-family:system-ui"><header style="background:#fa320a;color:#fff;padding:25px;font-size:24px">ROTTEN TOMATOES · TEST FIXTURE</header><main style="padding:80px">${tv ? '<a href="/tv/severance">Severance</a>' : ''}<h1 id="media-hero-label"><sr-text>${tv ? 'Severance: Season 1' : 'The Wild Robot'}</sr-text></h1><p>Title detail page fixture</p></main></body></html>`});
    });
    const movie = await context.newPage();
    await movie.goto('https://www.rottentomatoes.com/m/the_wild_robot');
    const host = movie.locator('#next-up-notion-watchlist');
    await host.waitFor();
    await movie.screenshot({path: path.join(output, 'movie-before.png')});
    // Closed shadow root protects the widget from page styling. Use its known
    // on-screen layout, and verify effects through the actual extension worker.
    async function saveClick() {
      const box = await host.boundingBox();
      await movie.mouse.click(box.x + box.width / 2, box.y + box.height - 40);
    }
    await saveClick();
    await options.waitForFunction(async () => (await chrome.storage.local.get('token')).token);
    await waitWorker(() => globalThis.testCalls.some(call => call.url.endsWith('/pages')));
    const create = await worker.evaluate(() => globalThis.testCalls.find(call => call.url.endsWith('/pages')));
    assert.equal(create.body.properties.Status.select.name, 'For Later');
    assert.equal(create.body.properties.Name.title[0].text.content, 'The Wild Robot');
    await movie.screenshot({path: path.join(output, 'movie-saved.png')});

    await worker.evaluate(() => {globalThis.testMode = 'existing'; globalThis.testCalls = [];});
    await movie.reload(); await host.waitFor(); await saveClick();
    await waitWorker(() => globalThis.testCalls.some(call => call.url.endsWith('/query')));
    assert.equal(await worker.evaluate(() => globalThis.testCalls.filter(call => call.url.endsWith('/pages')).length), 0);
    await movie.screenshot({path: path.join(output, 'movie-existing.png')});

    await worker.evaluate(() => {globalThis.testMode = 'legacy'; globalThis.testCalls = [];});
    await movie.reload(); await host.waitFor(); await saveClick();
    await waitWorker(() => globalThis.testCalls.filter(call => call.url.endsWith('/query')).length === 2);
    assert.equal(await worker.evaluate(() => globalThis.testCalls.filter(call => call.url.endsWith('/pages')).length), 0);
    await movie.screenshot({path: path.join(output, 'movie-legacy.png')});
    await saveClick();
    await waitWorker(() => globalThis.testCalls.some(call => call.url.endsWith('/pages')));

    await worker.evaluate(() => {globalThis.testMode = 'error'; globalThis.testCalls = [];});
    await movie.reload(); await host.waitFor(); await saveClick();
    await waitWorker(() => globalThis.testCalls.length > 0);
    await movie.screenshot({path: path.join(output, 'movie-error.png')});
    await movie.setViewportSize({width: 390, height: 844});
    await movie.reload(); await host.waitFor();
    const mobileBox = await host.boundingBox();
    assert.ok(mobileBox.x >= 0 && mobileBox.x + mobileBox.width <= 390);
    await movie.screenshot({path: path.join(output, 'movie-mobile.png')});
    await worker.evaluate(() => {globalThis.testMode = 'new'; globalThis.testCalls = [];});
    await movie.goto('https://www.rottentomatoes.com/tv/severance/s01');
    await host.waitFor(); await saveClick();
    await waitWorker(() => globalThis.testCalls.some(call => call.url.endsWith('/pages')));
    const show = await worker.evaluate(() => globalThis.testCalls.find(call => call.url.endsWith('/pages')).body);
    assert.equal(show.properties.Type.select.name, 'TV Show');
    assert.equal(show.properties.Name.title[0].text.content, 'Severance');
    assert.equal(show.properties['Rotten Tomatoes'].url, 'https://www.rottentomatoes.com/tv/severance');
    await movie.goto('https://www.rottentomatoes.com/m/the_wild_robot/reviews');
    await host.waitFor({state: 'hidden'});
    await options.locator('#disconnect').click();
    await options.getByText('Disconnected.', {exact: false}).waitFor();
    assert.equal(await options.evaluate(async () => (await chrome.storage.local.get('token')).token), undefined);
    console.log('PASS: real extension setup, create, existing URL, legacy match, separate create, error, mobile, TV season, review exclusion, disconnect');
    console.log(`Screenshots: ${output}`);
  } finally { await context.close(); }
})().catch(error => {console.error(error); process.exitCode = 1;});
