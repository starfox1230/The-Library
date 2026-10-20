(() => {
  'use strict';
  const stamp = /^(?:\d{1,2}:)?\d{1,2}:\d{2}(?:\.\d+)?$/;
  function extract(doc, options = {}) {
    const groups = new Map();
    for (const row of doc.querySelectorAll('[data-item]')) {
      if (!options.includeHidden && row.closest('[hidden], [aria-hidden="true"]')) continue;
      const parts = Array.from(row.querySelectorAll('p')).map(p => (p.innerText || p.textContent || '').trim());
      if (parts.length < 2 || !stamp.test(parts[0]) || !parts[1]) continue;
      const parent = row.parentElement;
      if (!groups.has(parent)) groups.set(parent, []);
      groups.get(parent).push({ time: parts[0], text: parts.slice(1).join(' '), index: Number(row.getAttribute('data-item')) });
    }
    const rows = [...groups.values()].sort((a, b) => b.length - a.length)[0] || [];
    rows.sort((a, b) => a.index - b.index);
    return rows.map(({ time, text }) => ({ time, text }));
  }
  function canonical(value) {
    const url = new URL(value);
    if (url.protocol !== 'https:' || !/(^|\.)(medality|mrionline)\.com$/.test(url.hostname)) throw new Error('Not a Medality lesson.');
    if (!url.pathname.includes('/unit/')) throw new Error('Open a lesson first.');
    return `https://medality.com${url.pathname.replace(/\/?$/, '/')}`;
  }
  function capture(doc, href, options = {}) {
    const cues = extract(doc, options);
    if (!cues.length) throw new Error('No transcript found. Open the lesson’s Transcript panel, then try again.');
    const url = canonical(href);
    const title = doc.querySelector('h1')?.textContent.trim() || 'Medality lesson';
    const course = doc.querySelector('nav[aria-label="breadcrumb"] a, [aria-label="breadcrumb"] a')?.textContent.trim() || 'Medality';
    return { url, title, course, cues, text: cues.map(cue => cue.text).join(' '), capturedAt: new Date().toISOString() };
  }
  function format(item) { return `${item.title}\n${item.url}\n\n${item.text}`; }
  globalThis.MedalityTranscript = { extract, canonical, capture, format };
})();
