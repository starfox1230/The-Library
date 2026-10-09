"use strict";

const { test, before, after } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
let context;
let profile;

// Same structure and native document keyup behavior as the public AnkiWeb
// reviewer, but without network access, accounts, collections, or scheduling.
const fixture = `<!doctype html><html><body>
<nav><input id="search" aria-label="Search"></nav>
<div id="quiz"><div id="qa_box"><div id="qa">Fixture question</div></div>
<div id="ansarea"></div></div>
<script>
window.clicks = []; window.nativeGrades = []; window.slow = false;
window.labels = ['Again', 'Hard', 'Good', 'Easy'];
window.showQuestion = () => {
  document.querySelector('#qa').textContent = 'Fixture question';
  document.querySelector('#ansarea').innerHTML = '<button>Show Answer</button>';
  const button = document.querySelector('#ansarea button'); button.focus();
  button.onclick = () => { window.clicks.push('reveal'); window.showAnswer(); };
};
window.showAnswer = () => {
  document.querySelector('#qa').textContent = 'Fixture answer';
  document.querySelector('#ansarea').innerHTML = window.labels.map(label =>
    '<div><div>10m</div><button>' + label + '</button></div>').join('');
  for (const button of document.querySelectorAll('#ansarea button')) {
    button.onclick = () => {
      window.clicks.push(button.textContent.toLowerCase());
      if (!window.slow) window.showQuestion();
    };
  }
  document.querySelectorAll('#ansarea button')[2]?.focus();
};
document.addEventListener('keyup', event => {
  if ('1234'.includes(event.key)) {
    window.nativeGrades.push(event.key);
    if (document.querySelector('#ansarea')?.textContent.includes('Again')) {
      window.clicks.push('native-grade-' + event.key); window.showQuestion();
    }
  }
});
window.showQuestion();
</script></body></html>`;

before(async () => {
  profile = fs.mkdtempSync(path.join(os.tmpdir(), "ankiweb-enhancer-test-"));
  context = await chromium.launchPersistentContext(profile, {
    channel: "chromium",
    executablePath: process.env.ANKI_TEST_BROWSER || chromium.executablePath(),
    headless: true,
    args: [`--disable-extensions-except=${root}`, `--load-extension=${root}`],
  });
  await context.route("**/*", route => route.fulfill({ contentType: "text/html", body: fixture }));
});

after(async () => {
  await context?.close();
  if (profile) fs.rmSync(profile, { recursive: true, force: true });
});

async function review(url = "https://ankiweb.net/study") {
  const page = await context.newPage();
  await page.goto(url);
  await page.locator("#ansarea button").waitFor();
  return page;
}

async function clicks(page) {
  return page.evaluate(() => window.clicks);
}

test("manifest requests only exact HTTPS AnkiWeb content-script access", () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(root, "manifest.json"), "utf8"));
  assert.equal(manifest.manifest_version, 3);
  assert.deepEqual(manifest.content_scripts[0].matches, ["https://ankiweb.net/*"]);
  for (const key of ["permissions", "host_permissions", "background", "externally_connectable", "web_accessible_resources"])
    assert.equal(manifest[key], undefined);
  for (const file of manifest.content_scripts[0].js) assert.ok(fs.existsSync(path.join(root, file)));
});

test("Space and Enter reveal once; numbers cannot grade the question", async () => {
  const page = await review();
  try {
    for (const key of ["1", "2", "3", "4"]) await page.keyboard.press(key);
    assert.deepEqual(await clicks(page), []);
    assert.deepEqual(await page.evaluate(() => window.nativeGrades), []);
    await page.keyboard.press("Space");
    assert.deepEqual(await clicks(page), ["reveal"]);
    await page.waitForTimeout(400);
    await page.keyboard.press("Enter"); // Good is autofocus; must NOT click it.
    await page.keyboard.press("Space");
    assert.deepEqual(await clicks(page), ["reveal"]);
    await page.evaluate(() => window.showQuestion());
    await page.keyboard.press("Enter");
    assert.deepEqual(await clicks(page), ["reveal", "reveal"]);
  } finally { await page.close(); }
});

for (const [key, label] of [["1", "again"], ["2", "hard"], ["3", "good"], ["4", "easy"]]) {
  test(`${key} clicks only ${label}, with no native keyup duplicate`, async () => {
    const page = await review();
    try {
      await page.evaluate(() => window.showAnswer());
      await page.keyboard.press(key);
      assert.deepEqual(await clicks(page), [label]);
      assert.deepEqual(await page.evaluate(() => window.nativeGrades), []);
    } finally { await page.close(); }
  });
}

test("missing, disabled, and hidden grades never remap or click", async () => {
  const page = await review();
  try {
    await page.evaluate(() => { window.labels = ["Again", "Good"]; window.showAnswer(); });
    await page.keyboard.press("2"); await page.keyboard.press("4");
    assert.deepEqual(await clicks(page), []);
    await page.keyboard.press("3");
    assert.deepEqual(await clicks(page), ["good"]);
    await page.waitForTimeout(400);
    await page.evaluate(() => {
      window.labels = ['Again', 'Hard', 'Good', 'Easy']; window.showAnswer();
      document.querySelectorAll('#ansarea button')[1].disabled = true;
      document.querySelectorAll('#ansarea button')[3].parentElement.hidden = true;
    });
    await page.keyboard.press("2"); await page.keyboard.press("4");
    assert.deepEqual(await clicks(page), ["good"]);
  } finally { await page.close(); }
});

test("held reveal and grading keys never repeat across DOM transitions", async () => {
  const page = await review();
  try {
    await page.keyboard.down("Space");
    await page.waitForTimeout(400);
    await page.keyboard.down("Space");
    await page.keyboard.up("Space");
    assert.deepEqual(await clicks(page), ["reveal"]);
    await page.keyboard.down("1");
    await page.waitForTimeout(400);
    await page.evaluate(() => window.showAnswer());
    await page.keyboard.down("1");
    await page.keyboard.up("1");
    assert.deepEqual(await clicks(page), ["reveal", "again"]);
    await page.keyboard.press("1");
    assert.deepEqual(await clicks(page), ["reveal", "again", "again"]);
  } finally { await page.close(); }
});

test("debounce prevents rapid reveal-to-grade and grade-to-next-card actions", async () => {
  const page = await review();
  try {
    await page.keyboard.press("Space"); await page.keyboard.press("1");
    assert.deepEqual(await clicks(page), ["reveal"]);
    await page.waitForTimeout(400); await page.keyboard.press("1");
    await page.keyboard.press("Space");
    assert.deepEqual(await clicks(page), ["reveal", "again"]);
    await page.waitForTimeout(400); await page.keyboard.press("Space");
    assert.deepEqual(await clicks(page), ["reveal", "again", "reveal"]);
  } finally { await page.close(); }
});

test("slow grading stays locked despite unrelated updates or replaced answer controls", async () => {
  const page = await review();
  try {
    await page.evaluate(() => { window.slow = true; window.showAnswer(); });
    await page.keyboard.press("1");
    await page.waitForTimeout(500);
    await page.evaluate(() => {
      document.querySelector('nav').append(document.createElement('span'));
      window.showAnswer(); // A replaced button does not prove a new question.
    });
    await page.keyboard.press("2"); await page.keyboard.press("3");
    assert.deepEqual(await clicks(page), ["again"]);
    await page.evaluate(() => window.showQuestion());
    await page.keyboard.press("Enter");
    await page.waitForTimeout(400); await page.keyboard.press("4");
    assert.deepEqual(await clicks(page), ["again", "reveal", "easy"]);
  } finally { await page.close(); }
});

test("manual grade also blocks an immediate keyboard grade on a slow answer", async () => {
  const page = await review();
  try {
    await page.evaluate(() => { window.slow = true; window.showAnswer(); });
    await page.getByRole("button", { name: "Again", exact: true }).click();
    await page.waitForTimeout(400); await page.keyboard.press("3");
    assert.deepEqual(await clicks(page), ["again"]);
  } finally { await page.close(); }
});

for (const [label, html] of [
  ["input", '<input id="editor">'],
  ["textarea", '<textarea id="editor"></textarea>'],
  ["contenteditable descendant", '<div contenteditable="true"><span id="editor">text</span></div>'],
  ["accessible textbox", '<div id="editor" role="textbox" tabindex="0"></div>'],
  ["select", '<select id="editor"><option>One</option><option>Two</option></select>'],
]) {
  test(`editing a ${label} never reaches native or extension grading`, async () => {
    const page = await review();
    try {
      await page.evaluate(html => {
        window.showAnswer(); document.querySelector('#qa').innerHTML = html;
        const field = document.querySelector('#editor');
        (field.closest('[contenteditable]') || field).focus();
      }, html);
      await page.keyboard.type("1234 "); await page.keyboard.press("Enter");
      assert.deepEqual(await clicks(page), []);
      assert.deepEqual(await page.evaluate(() => window.nativeGrades), []);
      if (["input", "textarea"].includes(label))
        assert.ok((await page.locator("#editor").inputValue()).startsWith("1234 "));
    } finally { await page.close(); }
  });
}

test("shadow DOM input keeps typing and suppresses native keyup", async () => {
  const page = await review();
  try {
    await page.evaluate(() => {
      window.showAnswer(); const host = document.createElement('div');
      document.querySelector('#qa').append(host);
      const shadow = host.attachShadow({ mode: 'open' });
      shadow.innerHTML = '<input id="shadow-editor">'; shadow.querySelector('input').focus();
    });
    await page.keyboard.type("1234 "); await page.keyboard.press("Enter");
    assert.deepEqual(await clicks(page), []);
    assert.deepEqual(await page.evaluate(() => window.nativeGrades), []);
    assert.equal(await page.locator("#shadow-editor").inputValue(), "1234 ");
  } finally { await page.close(); }
});

test("modifiers and composition never submit a rating", async () => {
  const page = await review();
  try {
    await page.evaluate(() => window.showAnswer());
    await page.keyboard.press("Shift+1");
    await page.keyboard.press("Alt+3");
    await page.evaluate(() => {
      for (const type of ['keydown', 'keypress', 'keyup'])
        document.activeElement.dispatchEvent(new KeyboardEvent(type, {
          key: '3', code: 'Digit3', bubbles: true, cancelable: true, isComposing: true,
        }));
    });
    assert.deepEqual(await clicks(page), []);
    assert.deepEqual(await page.evaluate(() => window.nativeGrades), []);
  } finally { await page.close(); }
});

test("ambiguous controls, card-contained fake controls, and dialogs fail closed", async () => {
  const page = await review();
  try {
    await page.evaluate(() => {
      window.showAnswer();
      document.querySelector('#ansarea').append(document.querySelector('#ansarea button').cloneNode(true));
    });
    await page.keyboard.press("1");
    assert.deepEqual(await clicks(page), []);
    await page.evaluate(() => {
      window.showQuestion();
      document.querySelector('#qa').innerHTML = '<button>Again</button><button>Good</button>';
    });
    await page.keyboard.press("1");
    assert.deepEqual(await clicks(page), []);
    await page.evaluate(() => {
      window.showAnswer(); const dialog = document.createElement('dialog');
      dialog.innerHTML = '<input>'; document.body.append(dialog); dialog.showModal();
    });
    await page.keyboard.press("3");
    assert.deepEqual(await clicks(page), []);
  } finally { await page.close(); }
});

test("client-side navigation and page reload need no reinjection", async () => {
  const page = await review("https://ankiweb.net/decks");
  try {
    await page.locator("#search").focus(); await page.keyboard.type("123");
    assert.equal(await page.locator("#search").inputValue(), "123");
    await page.evaluate(() => { history.pushState({}, '', '/study'); window.showQuestion(); });
    await page.keyboard.press("Space");
    assert.deepEqual(await clicks(page), ["reveal"]);
    await page.reload(); await page.locator("#ansarea button").waitFor();
    await page.keyboard.press("Enter");
    assert.deepEqual(await clicks(page), ["reveal"]);
  } finally { await page.close(); }
});

for (const url of ["https://example.com/study", "https://ankiweb.net/account/login", "https://ankiweb.net/study/finished"]) {
  test(`no extension button actions on ${url}`, async () => {
    const page = await review(url);
    try {
      // Blur the HTML button to distinguish a default browser click from extension behavior.
      await page.locator("#search").focus(); await page.keyboard.press("Tab");
      await page.evaluate(() => document.activeElement.blur());
      await page.keyboard.press("Space");
      assert.deepEqual(await clicks(page), []);
      if (url.includes("example.com")) {
        await page.keyboard.press("1");
        assert.deepEqual(await page.evaluate(() => window.nativeGrades), ["1"]);
      }
    } finally { await page.close(); }
  });
}
