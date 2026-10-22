/* Shared, buildless helpers. All captured content is rendered as text. */
(function (root) {
  'use strict';
  const SCHEMA = 1;
  const now = () => new Date().toISOString();
  const text = value => String(value ?? '').trim();
  const imageData = value => /^data:image\/(?:png|jpeg|webp|gif);base64,[A-Za-z0-9+/=]+$/.test(value || '');
  function safeSource(value) {
    try { const u = new URL(value); return u.origin === 'https://app.radprimer.com' ? u.href : ''; } catch { return ''; }
  }
  async function caseId(stem, answers) {
    const key = text(stem) + '\n' + answers.map(a => a.id || a.text).sort().join('\n');
    const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(key));
    return 'rp-' + Array.from(new Uint8Array(bytes), b => b.toString(16).padStart(2, '0')).join('');
  }
  function mediaCount(c) {
    return (c.groups || []).flatMap(g => g.images).reduce((a, i) => {
      a.total++; if (imageData(i.original)) a.saved++; if (i.error) a.failed++;
      return a;
    }, { total: 0, saved: 0, failed: 0 });
  }
  function mergeCapture(old, incoming) {
    const result = { ...incoming, schema: SCHEMA, savedAt: old?.savedAt || now(), updatedAt: now(),
      notes: old?.notes || '', highlights: old?.highlights || [], tier: old?.tier || 'review',
      ankiStatus: old?.ankiStatus || 'none', reviewedAt: old?.reviewedAt || null,
      dueAt: old?.dueAt || null, archived: old?.archived || false };
    // A later question-only capture must not erase a previously complete answer.
    if (old?.answered && !incoming.answered) {
      result.answered = true; result.answers = old.answers; result.teachingPoint = old.teachingPoint;
    }
    result.groups = (incoming.groups || []).map(g => {
      const previous = old?.groups?.find(p => p.id === g.id);
      return { ...g, images: g.images.map(i => {
        const p = previous?.images.find(p => p.id === i.id);
        const merged = { ...i, original: i.original || p?.original || '', annotated: i.annotated || p?.annotated || '',
          annotationExpected: !!(i.annotationExpected || p?.annotationExpected),
          annotatedUrl: i.annotatedUrl || p?.annotatedUrl || '', caption: i.caption || p?.caption || '' };
        if (imageData(merged.original) && (!merged.annotationExpected || imageData(merged.annotated))) merged.error = '';
        return merged;
      }) };
    });
    return result;
  }
  function validateCase(c) {
    if (!c || !/^rp-[a-f0-9]{64}$/.test(c.id || '') || !text(c.stem) || !Array.isArray(c.answers) || !c.answers.length || !Array.isArray(c.groups)) {
      throw new Error('This file contains an invalid case. Nothing was imported.');
    }
    if (c.answers.length > 100 || c.groups.length > 100) throw new Error('Case exceeds supported size.');
    const clean = { schema: SCHEMA, id: c.id, stem: text(c.stem), sourceUrl: safeSource(c.sourceUrl),
      sourceLabel: text(c.sourceLabel), questionLabel: text(c.questionLabel), author: text(c.author),
      answered: !!c.answered, teachingPoint: text(c.teachingPoint), savedAt: text(c.savedAt) || now(), updatedAt: text(c.updatedAt) || now(),
      notes: text(c.notes), highlights: Array.isArray(c.highlights) ? c.highlights.map(text).filter(Boolean) : [],
      tier: ['review', 'reference', 'essential'].includes(c.tier) ? c.tier : 'review',
      ankiStatus: ['none', 'queued', 'done'].includes(c.ankiStatus) ? c.ankiStatus : 'none',
      reviewedAt: Number.isFinite(Date.parse(c.reviewedAt)) ? c.reviewedAt : null,
      dueAt: Number.isFinite(Date.parse(c.dueAt)) ? c.dueAt : null, archived: !!c.archived,
      answers: c.answers.map(a => ({ id: text(a.id), text: text(a.text), correctness: ['correct','incorrect','almost'].includes(a.correctness) ? a.correctness : '', explanation: text(a.explanation), selected: !!a.selected })),
      groups: c.groups.map(g => {
        if (!g || !Array.isArray(g.images) || g.images.length > 1000) throw new Error('Invalid image group.');
        return { id: text(g.id), title: text(g.title), images: g.images.map(i => ({
          id: text(i.id), alt: text(i.alt), caption: text(i.caption), originalUrl: safeSource(i.originalUrl), annotatedUrl: safeSource(i.annotatedUrl),
          original: imageData(i.original) ? i.original : '', annotated: imageData(i.annotated) ? i.annotated : '',
          annotationExpected: !!i.annotationExpected, error: text(i.error) || (!imageData(i.original) ? 'Original image not stored' : '')
        })) };
      }) };
    return clean;
  }
  function parseBackup(data) {
    if (data?.schema !== SCHEMA || !['radprimer-library','radprimer-anki-packet'].includes(data?.format) || !Array.isArray(data.cases)) throw new Error('Choose a RadPrimer library backup or Anki packet (schema 1).');
    const ids = new Set();
    return data.cases.map(c => { const result = validateCase(c); if (ids.has(result.id)) throw new Error('Duplicate case IDs in import.'); ids.add(result.id); return result; });
  }
  function packet(cases) {
    return { format: 'radprimer-anki-packet', schema: SCHEMA, exportedAt: now(),
      instructions: 'These are source cases, not generated Anki cards. Read AGENTS.md, CARD_STYLE_GUIDE.md and APKG_PACKAGING.md in The-Library before authoring. Use only the personal notes and highlights to select the desired facts; ask if the scope is unclear. Use the existing saCloze++ model, Text/Extra fields, Saved Cards deck, and tags. Preserve image-group/key alignment. For image-based cards, inspect both the pathological images and their keys/descriptions, then look up a verified normal imaging counterpart of the same anatomy. Match modality, projection/plane, sequence/contrast phase, orientation, level, field of view and relevant age/skeletal maturity as closely as possible to mimic the original framing. Add the locally saved normal image to Extra, labeled Normal comparison, with a brief normal-appearance caption and source-page citation/attribution. Verify normality and usable image rights; record material differences and source-image/group mapping in the manifest. Do not fabricate, generatively repair, or distort an image to claim a matched normal study. If a suitable verified counterpart is unavailable, omit it and report the limitation. This is Extra-only enrichment, not permission to add tested facts or cards. Report case IDs completed; do not assume exporting means cards were created.',
      cases: cases.filter(c => c.ankiStatus === 'queued' && !c.archived) };
  }
  root.RadCore = { SCHEMA, now, caseId, safeSource, imageData, mediaCount, mergeCapture, validateCase, parseBackup, packet };
  if (typeof module !== 'undefined') module.exports = root.RadCore;
})(typeof globalThis !== 'undefined' ? globalThis : this);
