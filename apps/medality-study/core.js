(() => {
  'use strict';
  function url(value) {
    const parsed = new URL(value);
    if (parsed.protocol !== 'https:' || !/(^|\.)(medality|mrionline)\.com$/.test(parsed.hostname) || !parsed.pathname.includes('/unit/')) throw new Error('Use a Medality lesson URL.');
    return `https://medality.com${parsed.pathname.replace(/\/?$/, '/')}`;
  }
  function normalize(item) {
    if (!item || typeof item !== 'object') throw new Error('Invalid transcript entry.');
    const cues = Array.isArray(item.cues) ? item.cues.filter(cue => cue && typeof cue.text === 'string').map(cue => ({ time: String(cue.time || '').slice(0,20), text: cue.text })).slice(0,20000) : [];
    const text = typeof item.text === 'string' ? item.text : cues.map(cue => cue.text).join(' ');
    if (text.length > 2000000 || cues.reduce((total, cue) => total + cue.text.length, 0) > 2000000) throw new Error('Transcript is too large.');
    return { url: url(item.url), title: String(item.title || 'Medality lesson').slice(0,300), course: String(item.course || 'Medality').slice(0,200), text, cues, capturedAt: String(item.capturedAt || '') };
  }
  function imported(data) {
    const list = Array.isArray(data) ? data : data?.items;
    if (!Array.isArray(list) || list.length > 500) throw new Error('Choose a transcript JSON export containing an items list.');
    const items = list.map(normalize);
    return [...new Map(items.map(item => [item.url, item])).values()];
  }
  function transcript(item, timestamps) {
    return timestamps && item.cues?.length ? item.cues.map(cue => `${cue.time}  ${cue.text}`).join('\n') : item.text || '';
  }
  function packet(items, options = {}) {
    const sections = [], missing = [];
    for (const item of items) {
      const parts = [];
      if (options.mode !== 'notes') {
        const text = transcript(item, options.timestamps).trim();
        if (text) parts.push(`Transcript\n${text}`); else missing.push(item.title);
      }
      if (options.mode !== 'transcripts') {
        if (item.focus) parts.push(`Study focus (course-index note, not a transcript summary)\n${item.focus}`);
        if (item.note?.trim()) parts.push(`My notes\n${item.note.trim()}`);
      }
      if (parts.length) sections.push(`## ${item.title}\nSource: ${item.url}\n\n${parts.join('\n\n')}`);
    }
    const prompt = options.prompt ? 'Create a concise abdomen MRI study sheet from the supplied material. Explain the discriminating imaging features, organize important contrasts, and flag uncertainty. Distinguish what requires image review from what can be learned from text. Verify current LI-RADS diagnostic and treatment-response rules before treating older teaching as current. Do not invent findings or missing material.\n\n' : '';
    return { text: sections.length ? prompt + sections.join('\n\n---\n\n') : '', missing, included: sections.length };
  }
  globalThis.MedalityCore = { url, normalize, imported, transcript, packet };
})();
