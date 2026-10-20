(() => {
  'use strict';
  function canonical(value) {
    const url = new URL(value);
    if (url.protocol !== 'https:' || !/(^|\.)(medality|mrionline)\.com$/.test(url.hostname) || !url.pathname.includes('/unit/')) throw new Error('Invalid lesson URL');
    return `https://medality.com${url.pathname.replace(/\/?$/, '/')}`;
  }
  function date(value) { return typeof value === 'string' && Number.isFinite(Date.parse(value)) ? value : ''; }
  function time(item) { return Date.parse(item.watchedAt || item.capturedAt) || 0; }
  function clean(item) {
    if (!item || typeof item !== 'object') throw new Error('Invalid entry');
    const text = typeof item.text === 'string' ? item.text : '';
    if (text.length > 2000000) throw new Error('Transcript too large');
    const cues = Array.isArray(item.cues) ? item.cues.filter(c => c && typeof c.text === 'string').slice(0,20000).map(c => ({time:String(c.time || '').slice(0,20),text:c.text.slice(0,20000)})) : [];
    return {url:canonical(item.url),title:String(item.title || 'Medality lecture').slice(0,300),course:String(item.course || 'Medality').slice(0,200),text,cues,note:typeof item.note === 'string'?item.note.slice(0,200000):'',capturedAt:date(item.capturedAt),watchedAt:date(item.watchedAt),transcriptStatus:text.trim()?'saved':'unavailable'};
  }
  function entries(storage) {
    const rows = new Map();
    for (const [key,item] of Object.entries(storage)) {
      if (!key.startsWith('transcript:') && !key.startsWith('watch:')) continue;
      try {
        const next = clean(item), old = rows.get(next.url) || {};
        rows.set(next.url, {...old,...next,text:next.text || old.text || '',note:next.note || old.note || '',cues:next.cues.length?next.cues:old.cues || [],watchedAt:next.watchedAt || old.watchedAt || '',capturedAt:next.capturedAt || old.capturedAt || ''});
      } catch {}
    }
    return [...rows.values()].sort((a,b) => time(b)-time(a) || a.url.localeCompare(b.url));
  }
  function packet(rows, options = {}) {
    const ordered = [...rows].sort((a,b)=>time(a)-time(b) || a.url.localeCompare(b.url));
    const ready = ordered.filter(item=>item.text.trim());
    const parts = ready.map(item => `## ${item.title}\nCourse: ${item.course}\nSource: ${item.url}\n${item.watchedAt?'Watched: '+item.watchedAt:'Saved: '+item.capturedAt}\n\n${options.timestamps && item.cues.length?item.cues.map(c=>`${c.time}  ${c.text}`).join('\n'):item.text}`);
    const prompt = options.prompt && parts.length ? 'Help me retain the following lectures. Extract the key facts and discriminating imaging features, explain important contrasts, then quiz me with short recall questions. Distinguish transcript claims from your additions and flag anything requiring verification against current guidance.\n\n' : '';
    return {text:prompt+parts.join('\n\n---\n\n'),missing:ordered.length-ready.length};
  }
  globalThis.MedalityHistory = {canonical,clean,entries,packet};
})();
