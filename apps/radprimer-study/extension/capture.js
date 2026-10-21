/* Adapter based on the authenticated RadPrimer assessment DOM inspected 2026-10-21.
   Never reads application internals or submits an answer. Only the current case is captured. */
(function (root) {
  'use strict';
  const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
  function readable(node) {
    if (!node) return '';
    const copy = node.cloneNode(true);
    copy.querySelectorAll('img').forEach(img => img.replaceWith(' [' + (img.alt || 'image') + '] '));
    copy.querySelectorAll('.visually-hidden,.sr-only,script,style').forEach(e => e.remove());
    return copy.textContent.replace(/\s+/g, ' ').trim();
  }
  function signature(doc) {
    return readable(doc.querySelector('#mcq-question-stem')) + '|' + Array.from(doc.querySelectorAll('.mcq-answer')).map(e => e.dataset.answerId).join('|');
  }
  function answered(doc) {
    const button = doc.querySelector('.answer-detail');
    return !!button && (button.disabled || button.getAttribute('aria-disabled') === 'true') && !!doc.querySelector('.mcq-answer-justification.in,.answer-justification-js.in,.teaching-point-js:not(:empty)') && !doc.querySelector('.mcq-teaching-point.hidden');
  }
  function snapshot(doc = document) {
    const stem = readable(doc.querySelector('#mcq-question-stem'));
    const rows = Array.from(doc.querySelectorAll('.mcq-answer[data-answer-id]'));
    if (!stem || !rows.length) throw new Error('Open a RadPrimer assessment question before saving. This layout is not recognized.');
    const revealed = answered(doc);
    return { schema: 1, stem, sourceUrl: doc.location.href, sourceLabel: readable(doc.querySelector('.breadcrumb')),
      questionLabel: readable(doc.querySelector('.question-count-js')), author: readable(doc.querySelector('.authors-js')),
      answered: revealed, teachingPoint: revealed ? readable(doc.querySelector('.teaching-point-js')) : '',
      answers: rows.map(row => {
        const justification = row.querySelector('.mcq-answer-justification');
        const correctness = readable(justification?.querySelector('.mcq-answer-justification-correctness')).replace(/:$/, '').toLowerCase();
        return { id: row.dataset.answerId, text: readable(row.querySelector('.answer-js')),
          selected: row.querySelector('.answer-detail')?.getAttribute('aria-pressed') === 'true',
          correctness: revealed ? correctness : '', explanation: revealed ? readable(justification).replace(/^(?:incorrect|correct|almost):\s*/i, '') : '' };
      }), groups: [] };
  }
  async function fetchImage(url) {
    const u = new URL(url, location.href);
    if (u.origin !== 'https://app.radprimer.com' || !u.pathname.startsWith('/images/')) throw new Error('Unsupported image source');
    const response = await fetch(u.href, { credentials: 'same-origin', signal: AbortSignal.timeout(20000) });
    if (!response.ok) throw new Error('Image download returned ' + response.status);
    const blob = await response.blob();
    if (!/^image\/(png|jpeg|webp|gif)(;|$)/i.test(blob.type) || blob.size > 25 * 1024 * 1024 || !blob.size) throw new Error('Invalid or oversized image response');
    return new Promise((resolve, reject) => {
      const reader = new FileReader(); reader.onload = () => resolve(reader.result); reader.onerror = () => reject(reader.error); reader.readAsDataURL(blob);
    });
  }
  async function capture(doc = document, loadImage = fetchImage, progress = () => {}) {
    const start = signature(doc), c = snapshot(doc);
    const guard = () => { if (signature(doc) !== start) throw new Error('The question changed while saving. Return to it and save again.'); };
    c.id = await RadCore.caseId(c.stem, c.answers);
    const groups = Array.from(doc.querySelectorAll('.image-group[data-image-group-id]'));
    const active = groups.findIndex(g => !g.classList.contains('hidden'));
    const selected = groups.map(g => g.querySelector('.image-slider-button.selected'));
    const groupIndex = () => groups.findIndex(g => !g.classList.contains('hidden'));
    async function showGroup(index) {
      for (let attempts = 0; groupIndex() !== index && attempts <= groups.length; attempts++) {
        guard();
        const direction = groupIndex() < index ? '.next-image-group' : '.previous-image-group';
        const button = doc.querySelector(direction);
        if (!button || button.classList.contains('disabled')) throw new Error('Could not visit every image group. Save again after the page loads.');
        button.click(); await pause(60);
      }
      if (groupIndex() !== index) throw new Error('Image group navigation did not finish.');
    }
    let count = 0;
    const total = groups.reduce((n, g) => n + g.querySelectorAll('.image-slider-button').length, 0);
    try {
      for (let gi = 0; gi < groups.length; gi++) {
        guard(); await showGroup(gi);
        const group = groups[gi];
        const out = { id: group.dataset.imageGroupId, title: readable(doc.querySelector('.image-group-title')) || 'Group ' + (gi + 1), images: [] };
        const buttons = Array.from(group.querySelectorAll('.image-slider-button[data-image-id]'));
        if (!buttons.length) throw new Error('An image group has no recognized images. Save again after it loads.');
        for (const button of buttons) {
          guard(); button.click(); await pause(40); guard();
          const id = button.dataset.imageId, displayed = group.querySelector('.image-large-js');
          if (!displayed?.getAttribute('src')?.includes(id)) throw new Error('Image selection did not match its key. Please save again.');
          const original = new URL(displayed.getAttribute('src'), doc.location.href);
          original.searchParams.set('style', 'xlarge'); original.searchParams.delete('annotated');
          const annotated = new URL(original); annotated.searchParams.set('annotated', 'true');
          const hasAnnotations = c.answered && !!group.querySelector('.annotations-toggle:not(.hidden)');
          const image = { id, alt: button.querySelector('img')?.alt || 'Image ' + (out.images.length + 1),
            caption: c.answered ? readable(group.querySelector('.image-caption-js')) : '', originalUrl: original.href,
            annotatedUrl: hasAnnotations ? annotated.href : '', annotationExpected: hasAnnotations, original: '', annotated: '', error: '' };
          progress('Saving image ' + (++count) + ' of ' + total + '…');
          try { image.original = await loadImage(original.href); } catch (error) { image.error = 'Original: ' + error.message; }
          if (hasAnnotations) {
            try { image.annotated = await loadImage(annotated.href); } catch (error) { image.error += (image.error ? '; ' : '') + 'Annotated: ' + error.message; }
          }
          guard(); out.images.push(image);
        }
        c.groups.push(out);
      }
      guard(); return c;
    } finally {
      // Only restore controls if the same question is still open.
      if (signature(doc) === start) {
        for (const b of selected) b?.click();
        if (active >= 0) await showGroup(active);
      }
    }
  }
  root.RadCapture = { readable, signature, answered, snapshot, capture, fetchImage };
})(globalThis);
