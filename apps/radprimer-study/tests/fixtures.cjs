const fs = require('node:fs');
const path = require('node:path');
const { webcrypto } = require('node:crypto');
const { TextEncoder } = require('node:util');
const { JSDOM } = require('jsdom');
const { IDBFactory } = require('fake-indexeddb');
const runtime = path.join(__dirname, '../extension');
const pixel = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==';
function boot(html = '', url = 'https://app.radprimer.com/assessment/synthetic-test') {
  const dom = new JSDOM(html, { url, runScripts: 'outside-only', pretendToBeVisual: true });
  const w = dom.window;
  Object.defineProperty(w, 'crypto', { value: webcrypto }); w.TextEncoder = TextEncoder;
  w.indexedDB = new IDBFactory();
  const load = name => w.eval(fs.readFileSync(path.join(runtime, name), 'utf8'));
  load('core.js'); load('db.js');
  return { dom, w, load };
}
function fixture(revealed = true) {
  const html = `<main id="container"><div class="breadcrumb">Synthetic practice</div><div class="mcq-title-row"><h1 class="question-count-js">Question 7 of 10</h1><div class="authors-js">Fixture author</div></div><div id="mcq-question-stem">Which shape is shown in this synthetic example?</div>
  ${['Circle','Square','Triangle'].map((t,n)=>`<div class="mcq-answer" data-answer-id="answer-${n}"><button class="answer-detail" aria-pressed="${n===1}" ${revealed?'disabled aria-disabled="true"':''}><div class="answer-js"><span class="visually-hidden">Answer:</span>${t}</div></button><div class="mcq-answer-justification ${revealed?'in':''}"><span class="mcq-answer-justification-correctness">${n===1?'correct':'incorrect'}:</span>Secret explanation ${n}</div></div>`).join('')}
  <div class="mcq-teaching-point ${revealed?'':'hidden'}"><div class="teaching-point-js">Secret teaching point</div></div><div class="previous-image-group">Previous group</div><div class="next-image-group">Next group</div><div class="image-group-title">Group 2</div>
  ${[0,1].map(gi=>`<div class="image-group ${gi===0?'hidden':''}" data-image-group-id="group-${gi}">${[0,1].map(ii=>`<button class="image-slider-button ${ii===1?'selected':''}" data-image-id="g${gi}-i${ii}"><img src="/images/g${gi}-i${ii}?style=thumbnail" alt="Synthetic group ${gi} image ${ii}"></button>`).join('')}<img class="image-large-js" src="/images/g${gi}-i1?style=large${revealed?'&annotated=true':''}"><button class="annotations-toggle ${revealed?'':'hidden'}">Annotations</button><div class="image-caption-js">Key g${gi}-i1 <img alt="White solid arrow" src="/img/arrows/WS.png"></div></div>`).join('')}</main>`;
  const env = boot(html), { w } = env, doc = w.document;
  function setGroup(gi) {
    Array.from(doc.querySelectorAll('.image-group')).forEach((g,n)=>g.classList.toggle('hidden',n!==gi));
    doc.querySelector('.image-group-title').textContent = 'Group '+(gi+1);
  }
  doc.querySelector('.next-image-group').onclick = () => setGroup(1);
  doc.querySelector('.previous-image-group').onclick = () => setGroup(0);
  doc.querySelectorAll('.image-slider-button').forEach(b => b.onclick = () => {
    const g=b.closest('.image-group');g.querySelectorAll('.image-slider-button').forEach(p=>p.classList.toggle('selected',p===b));
    g.querySelector('.image-large-js').src='/images/'+b.dataset.imageId+'?style=large'+(revealed?'&annotated=true':'');
    g.querySelector('.image-caption-js').innerHTML='Key '+b.dataset.imageId+' <img alt="White solid arrow" src="/img/arrows/WS.png">';
  });
  env.load('capture.js'); return env;
}
async function record(overrides = {}) {
  const env = fixture();
  try { return { ...await env.w.RadCapture.capture(env.w.document, async()=>pixel), ...overrides }; } finally { env.dom.window.close(); }
}
module.exports = { boot, fixture, record, runtime, pixel };
