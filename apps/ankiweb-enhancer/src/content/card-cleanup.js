(() => {
  "use strict";
  const app = globalThis.AnkiWebEnhancer = globalThis.AnkiWebEnhancer || {};
  const excluded = 'script, style, noscript, input, textarea, select, iframe, [contenteditable], [role="textbox"]';

  function hideUnsupportedTts(root) {
    if (!root) return;
    // Read rendered text only, transiently. Never rewrite innerHTML, card fields,
    // collection data, or media. Complete TTS blocks can span cloze/format spans.
    const groups = [];
    let group = [];
    function flush() { if (group.length) groups.push(group); group = []; }
    function visit(node) {
      if (node.nodeType === Node.ELEMENT_NODE && node.matches(excluded)) { flush(); return; }
      if (node.nodeType === Node.TEXT_NODE) group.push(node);
      else for (const child of node.childNodes) visit(child);
    }
    visit(root);
    flush();
    for (const nodes of groups) {
      const text = nodes.map(node => node.data).join('');
      const matches = [...text.matchAll(/\[anki:tts\b[^\]]*\][\s\S]*?\[\/anki:tts\]/gi)];
      // Change only matched text slices, preserving elements, listeners, cloze
      // formatting, and surrounding card text. Process from right to left.
      for (const match of matches.reverse()) {
        let offset = 0;
        const start = match.index;
        const end = start + match[0].length;
        for (const node of nodes) {
          const length = node.data.length;
          const from = Math.max(0, start - offset);
          const to = Math.min(length, end - offset);
          if (to > from) node.deleteData(from, to - from);
          offset += length;
        }
      }
    }
  }
  app.cardCleanup = Object.freeze({ hideUnsupportedTts });
})();
