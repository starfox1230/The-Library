const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const assert = require("node:assert/strict");
const http = require("node:http");
const extension = path.resolve(__dirname, "../extension");
(async () => {
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), "website-timer-browser-"));
  const output = process.env.TIMER_QA_OUTPUT || profile;
  fs.mkdirSync(output, { recursive: true });
  const context = await chromium.launchPersistentContext(profile, {
    ...(process.env.TIMER_TEST_BROWSER ? { executablePath: process.env.TIMER_TEST_BROWSER } : {}),
    headless: true,
    args: ["--disable-extensions-except=" + extension, "--load-extension=" + extension],
    viewport: { width: 1280, height: 850 }
  });
  try {
    const errors = [];
    context.on("weberror", error => errors.push(error.error().message));
    let worker = context.serviceWorkers()[0];
    if (!worker) worker = await context.waitForEvent("serviceworker", { timeout: 20000 });
    worker.on("console", message => { if (message.type() === "error") errors.push(message.text()); });
    const id = new URL(worker.url()).host;
    assert.equal(await worker.evaluate(() => chrome.runtime.getManifest().name), "Website Timer");
    const page = await context.newPage();
    await page.route("https://www.facebook.com/**", route => route.fulfill({ contentType: "text/html", body: "<!doctype html><title>Facebook test fixture</title><body style='background:#f2f4f7;font:18px system-ui;padding:70px'><h1>Facebook</h1><p>Website Timer browser verification fixture.</p><p>Only this site's foreground time counts.</p></body>" }));
    await page.goto("https://www.facebook.com/");
    await page.locator("#library-website-timer").waitFor();
    await page.waitForTimeout(2200);
    await page.screenshot({ path: path.join(output, "page-timer.png") });
    console.log("PASS actual Manifest V3 load and page injection");
    const popup = await context.newPage();
    await popup.goto("chrome-extension://" + id + "/popup.html");
    await popup.locator('[data-site="facebook"]').waitFor();
    await popup.screenshot({ path: path.join(output, "settings.png") });
    await popup.locator('[name="facebook-cutoffEnabled"]').check();
    await popup.locator('[name="facebook-cutoff"]').fill("00:00");
    await popup.getByRole("button", { name: "Save limits" }).click();
    await popup.getByRole("status").filter({ hasText: "Saved" }).waitFor();
    await page.waitForURL("**/blocked.html?site=facebook");
    await page.locator("#reason").filter({ hasText: "cutoff" }).waitFor();
    const rules = await worker.evaluate(() => chrome.declarativeNetRequest.getDynamicRules());
    assert.equal(rules.length, 1);
    console.log("PASS settings save, dynamic redirect rule, and existing-tab block");
    const second = await context.newPage();
    await second.goto("https://m.facebook.com/another-page").catch(() => {});
    await second.waitForURL("**/blocked.html?site=facebook");
    await second.screenshot({ path: path.join(output, "blocked.png") });
    console.log("PASS network redirect blocks a fresh subdomain navigation");
    await popup.locator('[name="facebook-cutoffEnabled"]').uncheck();
    await popup.getByRole("button", { name: "Save limits" }).click();
    await popup.getByRole("status").filter({ hasText: "Saved" }).waitFor();
    assert.equal((await worker.evaluate(() => chrome.declarativeNetRequest.getDynamicRules())).length, 0);
    await page.goto("https://www.facebook.com/");
    await page.locator("#library-website-timer").waitFor();
    console.log("PASS disabling limit restores access");
    const rt = await context.newPage();
    await rt.route("https://www.rottentomatoes.com/**", route => route.fulfill({ contentType: "text/html", body: "<!doctype html><title>Rotten Tomatoes fixture</title><h1>Rotten Tomatoes</h1>" }));
    await rt.goto("https://www.rottentomatoes.com/m/example");
    await rt.locator("#library-website-timer").waitFor();
    console.log("PASS Rotten Tomatoes timer injection");
    await popup.setViewportSize({ width: 440, height: 600 });
    await popup.screenshot({ path: path.join(output, "settings-compact.png"), fullPage: true });
    assert.ok(await popup.getByRole("button", { name: "Save limits" }).isVisible());
    const repo = path.resolve(__dirname, "../../../..");
    const server = http.createServer((request, response) => {
      const url = new URL(request.url, "http://localhost");
      let filename = path.resolve(repo, "." + decodeURIComponent(url.pathname));
      if (!filename.startsWith(repo + path.sep)) { response.writeHead(403).end(); return; }
      if (fs.existsSync(filename) && fs.statSync(filename).isDirectory()) filename = path.join(filename, "index.html");
      const types = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".json": "application/json" };
      fs.readFile(filename, (error, body) => {
        response.writeHead(error ? 404 : 200, { "Content-Type": types[path.extname(filename)] || "application/octet-stream" });
        response.end(error ? "Not found" : body);
      });
    });
    await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
    try {
      const library = await context.newPage();
      await library.goto("http://127.0.0.1:" + server.address().port + "/apps/chrome-extensions/");
      await library.locator(".card").nth(5).waitFor();
      assert.equal(await library.locator(".card").count(), 6);
      assert.match(await library.locator(".card code").first().innerText(), /Chrome Extensions\\Website Timer$/);
      await library.screenshot({ path: path.join(output, "library-desktop.png"), fullPage: true });
      await library.setViewportSize({ width: 390, height: 844 });
      assert.equal(await library.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      await library.screenshot({ path: path.join(output, "library-mobile.png"), fullPage: true });
      console.log("PASS shared catalog registration and desktop/mobile layout");
    } finally { await new Promise(resolve => server.close(resolve)); }
    assert.deepEqual(errors, []);
    console.log("PASS no extension or page runtime errors");
    console.log("QA artifacts: " + output);
  } finally { await context.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
