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
const fixture = `<!doctype html><html><head><style>
html { background: white !important; } body { color: black; }
nav { background: #eee; padding: 10px; } .card { background: white; color: black; }
#qa { margin-top: 30px; } #ansarea { background: white; }
</style></head><body>
<nav><input id="search" aria-label="Search"><a href="/decks">Decks</a></nav>
<main><div id="quiz">
<div class="float-start" id="review-tools"><a href="/study/options">Limits</a></div>
<div class="float-end" id="counts"><span class="count new">3</span> +
<span class="count learn">4</span> + <span class="count review">5</span></div>
<div id="qa_box" class="card"><div id="qa">Fixture question</div></div>
<div id="ansarea"></div></div></main>
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

async function review(url = "https://ankiuser.net/study") {
  const page = await context.newPage();
  await page.goto(url);
  await page.locator("#ansarea button").waitFor();
  return page;
}

async function clicks(page) {
  return page.evaluate(() => window.clicks);
}

// Inspect the isolated content-script world on our local fixture only.
async function isolated(page) {
  const client = await context.newCDPSession(page);
  const worlds = [];
  client.on('Runtime.executionContextCreated', event => worlds.push(event.context.id));
  await client.send('Runtime.enable');
  for (const contextId of worlds) {
    const probe = await client.send('Runtime.evaluate', {
      contextId, expression: 'Boolean(globalThis.AnkiWebEnhancer?.session)', returnByValue: true,
    });
    if (probe.result.value) return async expression => {
      const result = await client.send('Runtime.evaluate', { contextId, expression, returnByValue: true });
      assert.equal(result.exceptionDetails, undefined);
      return result.result.value;
    };
  }
  throw new Error('Extension isolated world was not found');
}

test('session stats start empty with no XP or combo, and count every grade once', async () => {
  const page = await review();
  try {
    const stats = page.locator('#ankiweb-enhancer-session');
    assert.equal(await stats.locator('#cards').textContent(), '0');
    assert.equal(await stats.locator('#average').textContent(), '—');
    assert.doesNotMatch(await stats.textContent(), /XP|combo/i);
    for (const [index, key] of ['1', '2', '3', '4'].entries()) {
      await page.evaluate(() => window.showAnswer());
      if (index) await page.waitForTimeout(370);
      await page.keyboard.press(key);
      await page.waitForFunction(expected => document.querySelector('#ankiweb-enhancer-session')
        .shadowRoot.querySelector('#cards').textContent === String(expected), index + 1);
    }
    assert.deepEqual(await clicks(page), ['again', 'hard', 'good', 'easy']);
    assert.equal(Number(await stats.locator('#average').textContent()) > 0, true);
    assert.equal(Number(await stats.locator('#rate').textContent()) > 0, true);
  } finally { await page.close(); }
});

test('stats wait for the next question; slow, duplicate, and failed clicks do not inflate counts', async () => {
  const page = await review();
  try {
    const cards = page.locator('#ankiweb-enhancer-session #cards');
    await page.evaluate(() => { window.slow = true; window.showAnswer(); });
    await page.keyboard.press('3');
    await page.waitForTimeout(400);
    await page.keyboard.press('4');
    await page.locator('#qa').evaluate(element => { element.style.color = 'red'; });
    assert.equal(await cards.textContent(), '0');
    assert.deepEqual(await clicks(page), ['good']);
    await page.evaluate(() => window.showQuestion());
    await page.waitForFunction(() => document.querySelector('#ankiweb-enhancer-session')
      .shadowRoot.querySelector('#cards').textContent === '1');
    await page.keyboard.press('3'); // A number on the question cannot count.
    assert.equal(await cards.textContent(), '1');
    await page.evaluate(() => window.showAnswer());
    await page.locator('#ansarea button').filter({ hasText: 'Again' }).click();
    assert.equal(await cards.textContent(), '1');
    await page.evaluate(() => window.showQuestion());
    await page.waitForFunction(() => document.querySelector('#ankiweb-enhancer-session')
      .shadowRoot.querySelector('#cards').textContent === '2');
    await page.evaluate(() => {
      window.showAnswer();
      for (const button of document.querySelectorAll('#ansarea button')) button.onclick = () => {};
    });
    await page.waitForTimeout(370);
    await page.keyboard.press('2');
    assert.equal(await cards.textContent(), '2');
  } finally { await page.close(); }
});

test('pace timer resets by side, never grades on timeout, and stats use full card thinking time', async () => {
  const page = await review();
  try {
    const run = await isolated(page);
    const initial = await run(`globalThis.testNow = performance.now();
      Object.defineProperty(performance, 'now', {value: () => globalThis.testNow});
      AnkiWebEnhancer.session.snapshot()`);
    await run('testNow += 14000; AnkiWebEnhancer.session.sync()');
    assert.equal(await page.locator('#ankiweb-enhancer-session .value').textContent(), '0.0s');
    assert.equal(await page.locator('#ankiweb-enhancer-session .timer').getAttribute('data-urgency'), 'late');
    assert.deepEqual(await clicks(page), []);
    await page.keyboard.press('Space');
    assert.equal(await page.locator('#ankiweb-enhancer-session .value').textContent(), '8.0s');
    await run('testNow += 4000; AnkiWebEnhancer.session.sync()');
    await page.keyboard.press('3');
    const result = await run('AnkiWebEnhancer.session.snapshot()');
    assert.equal(result.reviews, 1);
    assert.ok(Math.abs(result.completedMs - initial.activeMs - 18000) < 1);
    assert.equal(result.averageSeconds, result.completedMs / 1000);
    assert.ok(Math.abs(result.reviewsPerMinute - 60000 / result.completedMs) < 0.001);
    assert.equal(await page.locator('#ankiweb-enhancer-session .value').textContent(), '12.0s');
  } finally { await page.close(); }
});

test('hidden tabs and modal dialogs pause timing without restarting the current card', async () => {
  const page = await review();
  try {
    const run = await isolated(page);
    await run(`globalThis.testNow = performance.now();
      Object.defineProperty(performance, 'now', {value: () => globalThis.testNow});
      globalThis.testHidden = false;
      Object.defineProperty(document, 'hidden', {get: () => globalThis.testHidden});`);
    await run('testNow += 2000; AnkiWebEnhancer.session.sync()');
    const before = await run('AnkiWebEnhancer.session.snapshot()');
    await run("testHidden = true; document.dispatchEvent(new Event('visibilitychange')); testNow += 30000");
    assert.equal((await run('AnkiWebEnhancer.session.snapshot()')).activeMs, before.activeMs);
    await run("testHidden = false; document.dispatchEvent(new Event('visibilitychange'))");
    await page.evaluate(() => {
      const dialog = document.createElement('dialog'); dialog.textContent = 'Paused';
      document.body.append(dialog); dialog.showModal();
    });
    await run('testNow += 30000');
    assert.equal((await run('AnkiWebEnhancer.session.snapshot()')).activeMs, before.activeMs);
    await page.evaluate(() => document.querySelector('dialog').remove());
    await run('testNow += 1000; AnkiWebEnhancer.session.sync()');
    const after = await run('AnkiWebEnhancer.session.snapshot()');
    assert.equal(after.phase, 'question');
    assert.equal(after.activeMs, before.activeMs + 1000);
    assert.equal(after.phaseMs, before.phaseMs + 1000);
  } finally { await page.close(); }
});

test('G and T independently toggle stats/timer, preserve timing, and match both themes', async () => {
  const page = await review();
  try {
    const host = page.locator('#ankiweb-enhancer-session');
    const initialColor = await host.locator('.wrap').evaluate(node => getComputedStyle(node).backgroundColor);
    assert.equal(initialColor, 'rgb(255, 255, 255)');
    await page.keyboard.press('d');
    assert.equal(await host.locator('.wrap').evaluate(node => getComputedStyle(node).backgroundColor), 'rgb(23, 26, 32)');
    await page.keyboard.down('g'); await page.keyboard.down('g'); await page.keyboard.up('g');
    assert.equal(await host.locator('.metrics').isVisible(), false);
    assert.equal(await host.locator('.timer').isVisible(), true);
    await page.keyboard.press('t');
    assert.equal(await host.isVisible(), false);
    assert.equal(await page.locator('body').evaluate(node => getComputedStyle(node).paddingTop), '0px');
    await page.evaluate(() => window.showAnswer()); await page.keyboard.press('1');
    await page.keyboard.press('g');
    assert.equal(await host.locator('#cards').textContent(), '1');
    assert.equal(await host.locator('.metrics').isVisible(), true);
    assert.equal(await host.locator('.timer').isVisible(), false);
    await page.keyboard.press('t'); await page.keyboard.press('d');
    assert.equal(await host.locator('.timer').isVisible(), true);
    assert.equal(await host.locator('.wrap').evaluate(node => getComputedStyle(node).backgroundColor), initialColor);
    assert.equal(await host.evaluate(node => getComputedStyle(node).pointerEvents), 'none');
    assert.ok(await page.locator('body').evaluate(node => parseFloat(getComputedStyle(node).paddingTop)) > 40);
  } finally { await page.close(); }
});

test('G/T stay out of text entry, modifiers and dialogs', async () => {
  const page = await review();
  try {
    const host = page.locator('#ankiweb-enhancer-session');
    await page.locator('#search').click(); await page.keyboard.type('gtGT');
    assert.equal(await page.locator('#search').inputValue(), 'gtGT');
    await page.locator('#qa').click();
    await page.keyboard.press('Control+g'); await page.keyboard.press('Alt+t');
    assert.equal(await host.locator('.metrics').isVisible(), true);
    assert.equal(await host.locator('.timer').isVisible(), true);
    await page.evaluate(() => {
      const dialog = document.createElement('dialog'); dialog.textContent = 'Modal';
      document.body.append(dialog); dialog.showModal();
    });
    await page.keyboard.press('g'); await page.keyboard.press('t');
    assert.equal(await host.locator('.metrics').isVisible(), true);
    assert.equal(await host.locator('.timer').isVisible(), true);
    assert.deepEqual(await clicks(page), []);
  } finally { await page.close(); }
});

test('final card counts on finished route; leaving review removes UI, reentry preserves stats, refresh resets', async () => {
  const page = await review();
  try {
    const run = await isolated(page);
    await page.evaluate(() => {
      window.showAnswer();
      for (const button of document.querySelectorAll('#ansarea button')) button.onclick = () => {
        history.pushState({}, '', '/study/finished'); document.querySelector('#quiz').remove();
      };
    });
    await page.keyboard.press('4');
    assert.equal((await run('AnkiWebEnhancer.session.snapshot()')).reviews, 1);
    assert.equal(await page.locator('#ankiweb-enhancer-session').isVisible(), false);
    assert.equal(await page.locator('html').getAttribute('data-ankiweb-session-ui'), null);
    await page.evaluate(() => {
      history.pushState({}, '', '/study');
      document.querySelector('main').innerHTML = '<div id="quiz"><div id="qa_box"><div id="qa"></div></div><div id="ansarea"></div></div>';
      window.showQuestion();
    });
    assert.equal(await page.locator('#ankiweb-enhancer-session #cards').textContent(), '1');
    await page.reload();
    assert.equal(await page.locator('#ankiweb-enhancer-session #cards').textContent(), '0');
    assert.equal(await page.locator('#ankiweb-enhancer-session #average').textContent(), '—');
  } finally { await page.close(); }
});

test('session UI is absent on non-review pages', async () => {
  const page = await review('https://ankiuser.net/decks');
  try {
    await page.keyboard.press('g'); await page.keyboard.press('t');
    assert.equal(await page.locator('#ankiweb-enhancer-session').count(), 0);
    assert.equal(await page.locator('html').getAttribute('data-ankiweb-session-ui'), null);
  } finally { await page.close(); }
});

test("manifest requests only the two exact HTTPS Anki hosts", () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(root, "manifest.json"), "utf8"));
  assert.equal(manifest.manifest_version, 3);
  assert.deepEqual(manifest.content_scripts[0].matches, ["https://ankiweb.net/*", "https://ankiuser.net/*"]);
  for (const key of ["permissions", "host_permissions", "background", "externally_connectable", "web_accessible_resources"])
    assert.equal(manifest[key], undefined);
  for (const file of manifest.content_scripts[0].js) assert.ok(fs.existsSync(path.join(root, file)));
  for (const file of manifest.content_scripts[0].css) assert.ok(fs.existsSync(path.join(root, file)));
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

test("clicking card content or page background restores Show Answer focus", async () => {
  const page = await review();
  try {
    await page.locator('#qa').click();
    await page.waitForFunction(() => document.activeElement?.textContent === 'Show Answer');
    assert.deepEqual(await clicks(page), []);
    await page.keyboard.press('Space');
    assert.deepEqual(await clicks(page), ['reveal']);
    await page.waitForTimeout(400);
    await page.evaluate(() => {
      window.showQuestion();
      const blank = document.createElement('div'); blank.id = 'background';
      blank.style.height = '120px'; document.body.append(blank);
    });
    await page.locator('#background').click();
    await page.waitForFunction(() => document.activeElement?.textContent === 'Show Answer');
    await page.keyboard.press('Space');
    assert.deepEqual(await clicks(page), ['reveal', 'reveal']);
  } finally { await page.close(); }
});

test("focus recovery preserves question-side text input across clicks and mutations", async () => {
  const page = await review();
  try {
    await page.evaluate(() => {
      document.querySelector('#qa').innerHTML = '<input id="answer-field">';
    });
    await page.locator('#answer-field').click();
    await page.keyboard.type('1234 ');
    await page.evaluate(() => document.querySelector('nav').append(document.createElement('span')));
    await page.waitForTimeout(100);
    assert.equal(await page.evaluate(() => document.activeElement.id), 'answer-field');
    assert.equal(await page.locator('#answer-field').inputValue(), '1234 ');
    assert.deepEqual(await clicks(page), []);
  } finally { await page.close(); }
});

test("new question controls regain focus without autofocus or page scrolling", async () => {
  const page = await review();
  try {
    await page.evaluate(() => {
      document.body.style.minHeight = '2500px'; window.scrollTo(0, 500);
      document.querySelector('#ansarea').innerHTML = '<button>Show Answer</button>';
      document.querySelector('#ansarea button').onclick = () => {
        window.clicks.push('reveal'); window.showAnswer();
      };
    });
    await page.waitForFunction(() => document.activeElement?.textContent === 'Show Answer');
    assert.equal(await page.evaluate(() => window.scrollY), 500);
    await page.keyboard.press('Space');
    assert.deepEqual(await clicks(page), ['reveal']);
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

for (const [key, label, color] of [
  ['1', 'Again', 'rgb(255, 105, 97)'], ['2', 'Hard', 'rgb(255, 184, 97)'],
  ['3', 'Good', 'rgb(97, 255, 184)'], ['4', 'Easy', 'rgb(97, 168, 255)'],
]) {
  test(`${label} feedback persists across next question then expires`, async () => {
    const page = await review();
    try {
      await page.evaluate(() => window.showAnswer());
      await page.keyboard.press(key);
      const feedback = page.getByRole('status');
      assert.equal(await feedback.innerText(), label);
      assert.equal(await feedback.evaluate(element => getComputedStyle(element).backgroundColor), color);
      assert.equal(await page.getByRole('button', { name: 'Show Answer', exact: true }).count(), 1);
      await page.waitForTimeout(450);
      assert.equal(await feedback.innerText(), label);
      await page.waitForTimeout(550);
      assert.equal(await feedback.count(), 0);
    } finally { await page.close(); }
  });
}

test('mouse ratings show the same feedback and subsequent rating replaces it', async () => {
  const page = await review();
  try {
    await page.evaluate(() => window.showAnswer());
    await page.getByRole('button', { name: 'Hard', exact: true }).click();
    assert.equal(await page.getByRole('status').innerText(), 'Hard');
    await page.waitForTimeout(400);
    await page.evaluate(() => window.showAnswer());
    await page.keyboard.press('4');
    assert.equal(await page.getByRole('status').count(), 1);
    assert.equal(await page.getByRole('status').innerText(), 'Easy');
    await page.waitForTimeout(550);
    assert.equal(await page.getByRole('status').innerText(), 'Easy');
    await page.waitForTimeout(450);
    assert.equal(await page.getByRole('status').count(), 0);
  } finally { await page.close(); }
});

test('reveal, invalid grades, and blocked double grades do not show or extend feedback', async () => {
  const page = await review();
  try {
    await page.keyboard.press('1'); await page.keyboard.press('Space');
    assert.equal(await page.getByRole('status').count(), 0);
    await page.waitForTimeout(400);
    await page.evaluate(() => { window.slow = true; });
    await page.keyboard.press('1');
    await page.waitForTimeout(500); await page.keyboard.press('3');
    assert.equal(await page.getByRole('status').innerText(), 'Again');
    await page.waitForTimeout(500);
    assert.equal(await page.getByRole('status').count(), 0);
    assert.deepEqual(await clicks(page), ['reveal', 'again']);
  } finally { await page.close(); }
});

test('feedback does not intercept next-question clicks or steal input focus', async () => {
  const page = await review();
  try {
    await page.evaluate(() => window.showAnswer()); await page.keyboard.press('3');
    assert.equal(await page.getByRole('status').innerText(), 'Good');
    assert.equal(await page.locator('#ankiweb-enhancer-answer-feedback')
      .evaluate(element => getComputedStyle(element).pointerEvents), 'none');
    await page.getByRole('button', { name: 'Show Answer', exact: true }).click();
    assert.deepEqual(await clicks(page), ['good', 'reveal']);
    await page.locator('#search').click(); await page.keyboard.type('1234 ');
    assert.equal(await page.locator('#search').inputValue(), '1234 ');
    assert.equal(await page.evaluate(() => document.activeElement.id), 'search');
    assert.deepEqual(await clicks(page), ['good', 'reveal']);
  } finally { await page.close(); }
});

test('TTS echo disappears across formatted spans while the normal card remains intact', async () => {
  const page = await review();
  try {
    await page.evaluate(() => {
      document.querySelector('#qa').innerHTML = '<p id="normal">Original <b>cloze</b> text.</p>' +
        '<p>[anki:tts lang=en_US voices=Apple_Evan_(Enhanced) speed=1.1]Duplicate <span>[...]</span> text.[/anki:tts] &#x20;</p>';
    });
    await page.waitForFunction(() => !document.querySelector('#qa').textContent.includes('[anki:tts'));
    assert.equal(await page.locator('#normal').innerText(), 'Original cloze text.');
    assert.equal(await page.locator('#normal b').innerText(), 'cloze');
    assert.ok(!(await page.locator('#qa').innerText()).includes('Duplicate'));
    await page.keyboard.press('Space');
    assert.deepEqual(await clicks(page), ['reveal']);
  } finally { await page.close(); }
});

test('multiple TTS blocks are removed on successive question and answer updates', async () => {
  const page = await review();
  try {
    for (const side of ['question', 'answer']) {
      await page.evaluate(side => {
        if (side === 'answer') window.showAnswer(); else window.showQuestion();
        document.querySelector('#qa').innerHTML = 'Keep A [anki:tts lang=en_US]echo 1[/anki:tts]' +
          ' Keep B [anki:tts lang=en_US]<b>echo 2</b>[/anki:tts] Keep C';
      }, side);
      await page.waitForFunction(() => !document.querySelector('#qa').textContent.includes('[anki:tts'));
      assert.equal(await page.locator('#qa').innerText(), 'Keep A Keep B Keep C');
    }
  } finally { await page.close(); }
});

test('TTS cleanup leaves editors, scripts, media, and unmatched text alone', async () => {
  const page = await review();
  try {
    await page.evaluate(() => {
      document.querySelector('#qa').innerHTML = '<textarea>[anki:tts]Editable[/anki:tts]</textarea>' +
        '<div contenteditable="true">[anki:tts]Edit me[/anki:tts]</div>' +
        '<audio controls></audio><script type="application/json">"[anki:tts]Script[/anki:tts]"</script>' +
        '<p>Keep unmatched [anki:tts lang=en_US]text without a closing marker.</p>';
    });
    await page.waitForTimeout(100);
    assert.equal(await page.locator('#qa textarea').inputValue(), '[anki:tts]Editable[/anki:tts]');
    assert.equal(await page.locator('#qa [contenteditable]').innerText(), '[anki:tts]Edit me[/anki:tts]');
    assert.equal(await page.locator('#qa audio').count(), 1);
    assert.equal(await page.locator('#qa script').textContent(), '"[anki:tts]Script[/anki:tts]"');
    assert.ok((await page.locator('#qa p').innerText()).includes('Keep unmatched [anki:tts'));
  } finally { await page.close(); }
});

test('F and D independently toggle focus and night mode without a reload', async () => {
  const page = await review();
  try {
    await page.keyboard.press('f');
    assert.equal(await page.locator('nav').isVisible(), false);
    assert.equal(await page.locator('#review-tools').isVisible(), false);
    assert.equal(await page.locator('#qa').isVisible(), true);
    assert.equal(await page.locator('#ansarea').isVisible(), true);
    assert.equal(await page.locator('#counts').isVisible(), true);
    await page.keyboard.press('d');
    assert.equal(await page.locator('body').evaluate(element => getComputedStyle(element).backgroundColor), 'rgb(18, 20, 25)');
    await page.keyboard.press('f');
    assert.equal(await page.locator('nav').isVisible(), true);
    assert.equal(await page.locator('#review-tools').isVisible(), true);
    assert.equal(await page.locator('html').getAttribute('data-ankiweb-dark'), '');
    await page.keyboard.press('d');
    assert.equal(await page.locator('html').getAttribute('data-ankiweb-dark'), null);
    assert.equal(await page.locator('#qa_box').evaluate(element => getComputedStyle(element).backgroundColor), 'rgb(255, 255, 255)');
    assert.deepEqual(await clicks(page), []);
  } finally { await page.close(); }
});

test('night mode preserves card images and explicit text/background formatting', async () => {
  const page = await review();
  try {
    await page.evaluate(() => {
      document.querySelector('#qa').innerHTML = '<img id="card-image" src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==">' +
        '<span id="formatted" style="color:rgb(220,80,120);background-color:rgb(255,255,255);font-weight:700">Card formatting</span>';
    });
    const imageSource = await page.locator('#card-image').getAttribute('src');
    await page.keyboard.press('d');
    assert.equal(await page.locator('#card-image').getAttribute('src'), imageSource);
    assert.equal(await page.locator('#card-image').evaluate(element => getComputedStyle(element).filter), 'none');
    assert.deepEqual(await page.locator('#formatted').evaluate(element => {
      const style = getComputedStyle(element);
      return [style.color, style.backgroundColor, style.fontWeight];
    }), ['rgb(220, 80, 120)', 'rgb(255, 255, 255)', '700']);
    assert.equal(await page.locator('#qa').evaluate(element => getComputedStyle(element).color), 'rgb(229, 231, 235)');
    assert.equal(await page.locator('#counts .learn').evaluate(element => getComputedStyle(element).color), 'rgb(255, 184, 97)');
  } finally { await page.close(); }
});

test('F/D stay out of typing fields and ignore modified key combinations', async () => {
  const page = await review();
  try {
    await page.locator('#search').click(); await page.keyboard.type('fdFD');
    assert.equal(await page.locator('#search').inputValue(), 'fdFD');
    assert.equal(await page.locator('html').getAttribute('data-ankiweb-focus'), null);
    assert.equal(await page.locator('html').getAttribute('data-ankiweb-dark'), null);
    await page.locator('#qa').click();
    await page.keyboard.press('Shift+F'); await page.keyboard.press('Alt+d');
    assert.equal(await page.locator('html').getAttribute('data-ankiweb-focus'), null);
    assert.equal(await page.locator('html').getAttribute('data-ankiweb-dark'), null);
    assert.deepEqual(await clicks(page), []);
  } finally { await page.close(); }
});

test('holding mode keys toggles once, independent of the review debounce', async () => {
  const page = await review();
  try {
    await page.keyboard.down('f'); await page.keyboard.down('f'); await page.keyboard.up('f');
    assert.equal(await page.locator('html').getAttribute('data-ankiweb-focus'), '');
    await page.keyboard.down('d'); await page.keyboard.down('d'); await page.keyboard.up('d');
    assert.equal(await page.locator('html').getAttribute('data-ankiweb-dark'), '');
    await page.keyboard.press('Space');
    await page.waitForTimeout(400); await page.keyboard.press('1');
    assert.deepEqual(await clicks(page), ['reveal', 'again']);
    assert.equal(await page.locator('html').getAttribute('data-ankiweb-focus'), '');
    assert.equal(await page.locator('html').getAttribute('data-ankiweb-dark'), '');
  } finally { await page.close(); }
});

test('modes survive replaced review DOM, turn off outside review, and return on reentry', async () => {
  const page = await review();
  try {
    await page.keyboard.press('f'); await page.keyboard.press('d');
    await page.evaluate(() => {
      document.querySelector('#quiz').replaceWith(document.querySelector('#quiz').cloneNode(true));
      window.showQuestion();
    });
    await page.waitForFunction(() => document.querySelector('#qa').hasAttribute('data-ankiweb-card-text'));
    assert.equal(await page.locator('nav').isVisible(), false);
    await page.evaluate(() => { history.pushState({}, '', '/decks'); document.querySelector('#qa').textContent = 'Deck list'; });
    await page.waitForFunction(() => !document.documentElement.hasAttribute('data-ankiweb-review'));
    assert.equal(await page.locator('nav').isVisible(), true);
    await page.evaluate(() => { history.pushState({}, '', '/study'); window.showQuestion(); });
    await page.waitForFunction(() => document.documentElement.hasAttribute('data-ankiweb-dark'));
    assert.equal(await page.locator('nav').isVisible(), false);
    await page.reload();
    assert.equal(await page.locator('html').getAttribute('data-ankiweb-focus'), null);
    assert.equal(await page.locator('html').getAttribute('data-ankiweb-dark'), null);
  } finally { await page.close(); }
});

test('focus mode does not hide navigation or media embedded in card content', async () => {
  const page = await review();
  try {
    await page.evaluate(() => { document.querySelector('#qa').innerHTML = '<nav id="card-nav">Card navigation</nav><audio controls></audio>'; });
    await page.keyboard.press('f');
    assert.equal(await page.locator('body > nav').isVisible(), false);
    assert.equal(await page.locator('#card-nav').isVisible(), true);
    assert.equal(await page.locator('#qa audio').isVisible(), true);
  } finally { await page.close(); }
});

test('mode shortcuts are blocked by a visible modal dialog', async () => {
  const page = await review();
  try {
    await page.evaluate(() => {
      const dialog = document.createElement('dialog'); dialog.textContent = 'Dialog';
      document.body.append(dialog); dialog.showModal();
    });
    await page.keyboard.press('f'); await page.keyboard.press('d');
    assert.equal(await page.locator('html').getAttribute('data-ankiweb-focus'), null);
    assert.equal(await page.locator('html').getAttribute('data-ankiweb-dark'), null);
  } finally { await page.close(); }
});

test('mode shortcuts and mode CSS leave a non-review page alone', async () => {
  const page = await review('https://ankiuser.net/decks');
  try {
    await page.locator('#qa').click();
    await page.keyboard.press('f'); await page.keyboard.press('d');
    assert.equal(await page.locator('nav').isVisible(), true);
    assert.equal(await page.locator('html').getAttribute('data-ankiweb-review'), null);
    assert.equal(await page.locator('#qa_box').evaluate(element => getComputedStyle(element).backgroundColor), 'rgb(255, 255, 255)');
  } finally { await page.close(); }
});

test('AnkiWeb host remains supported alongside the real ankiuser review host', async () => {
  const page = await review('https://ankiweb.net/study');
  try {
    await page.keyboard.press('Space');
    assert.deepEqual(await clicks(page), ['reveal']);
    await page.waitForTimeout(400); await page.keyboard.press('3');
    assert.deepEqual(await clicks(page), ['reveal', 'good']);
  } finally { await page.close(); }
});

for (const url of ["https://example.com/study", "https://ankiweb.net/account/login", "https://ankiweb.net/study/finished", "https://ankiuser.net/account/login", "https://ankiuser.net/study/finished", "https://ankiuser.net.example.com/study", "http://ankiuser.net/study"]) {
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
