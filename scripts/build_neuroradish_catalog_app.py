"""Generate the phone-first NeuroRadish catalog app from the JSON export."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "exports" / "neuroradish" / "neuroradish_video_catalog.json"
APP_PATH = ROOT / "apps" / "neuroradish-catalog" / "index.html"


TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#091018">
<title>NeuroRadish Video Catalog</title>
<style>
  :root {
    --bg: #091018;
    --card: #101a25;
    --card-2: #0d151f;
    --text: #e9f4ff;
    --muted: #9eb2c6;
    --accent: #48e4ff;
    --accent-2: #8af1ff;
    --good: #36e6a7;
    --gold: #ffe08a;
    --border: rgba(255,255,255,.09);
    --shadow: 0 12px 32px rgba(0,0,0,.28);
    --radius: 16px;
  }
  * { box-sizing: border-box; }
  html, body { min-height: 100%; }
  body {
    margin: 0;
    background: radial-gradient(circle at top, #142333 0, var(--bg) 45%, #06090d 100%);
    color: var(--text);
    font: 16px/1.45 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  a { color: var(--accent); text-decoration: none; }
  button, input, select, textarea { font: inherit; }
  button, select, input { -webkit-tap-highlight-color: transparent; }
  .wrap { width: min(960px, 100%); margin: 0 auto; padding: 14px; }
  header { display: grid; gap: 12px; margin-bottom: 12px; }
  .titlebar { display: flex; justify-content: space-between; align-items: flex-start; gap: 14px; }
  .kicker { color: var(--accent); font-size: 11px; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
  h1 { margin: 3px 0 3px; font-size: clamp(23px, 6vw, 34px); line-height: 1.1; }
  .subtitle { margin: 0; color: var(--muted); font-size: 13px; max-width: 680px; }
  .btn, .select, .search {
    background: var(--card);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 12px;
    box-shadow: var(--shadow);
  }
  .btn { padding: 9px 12px; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; gap: 7px; }
  .btn:active { transform: scale(.98); }
  .btn.primary { border-color: rgba(72,228,255,.55); background: linear-gradient(135deg, rgba(72,228,255,.2), rgba(72,228,255,.08)); }
  .btn.ghost { background: transparent; box-shadow: none; }
  .btn.small { padding: 7px 9px; font-size: 13px; box-shadow: none; }
  .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .stat { padding: 10px 11px; background: var(--card); border: 1px solid var(--border); border-radius: 14px; box-shadow: var(--shadow); }
  .stat .number { font-size: 22px; font-weight: 800; font-variant-numeric: tabular-nums; }
  .stat .label { color: var(--muted); font-size: 11px; }
  .progress { display: flex; align-items: center; gap: 10px; padding: 10px 12px; background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow); }
  .progress-track { flex: 1; height: 11px; overflow: hidden; border-radius: 999px; background: #080d13; }
  .progress-track span { display: block; width: 0; height: 100%; background: linear-gradient(90deg, var(--accent), var(--good)); transition: width .2s ease; }
  .progress-label { min-width: 42px; text-align: right; color: var(--accent-2); font-size: 13px; font-variant-numeric: tabular-nums; }
  .nextup { display: grid; grid-template-columns: 1fr auto; gap: 12px; align-items: center; margin: 14px 0 12px; padding: 13px; background: linear-gradient(135deg, rgba(72,228,255,.12), rgba(16,26,37,.96)); border: 1px solid rgba(72,228,255,.25); border-radius: var(--radius); box-shadow: var(--shadow); }
  .nextup[hidden] { display: none; }
  .next-label { color: var(--accent); font-size: 11px; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
  .next-title { margin-top: 3px; font-weight: 750; }
  .next-meta { margin-top: 3px; color: var(--muted); font-size: 13px; }
  .toolbar { display: grid; gap: 9px; margin: 10px 0 12px; }
  .tabs { display: grid; grid-template-columns: repeat(5, 1fr); gap: 7px; }
  .tab { padding: 10px 5px; border: 1px solid var(--border); border-radius: 12px; background: var(--card-2); color: var(--muted); cursor: pointer; font-size: 13px; }
  .tab.active { color: var(--text); border-color: rgba(72,228,255,.5); box-shadow: 0 0 0 2px rgba(72,228,255,.1) inset; }
  .search-row { display: grid; grid-template-columns: 1fr 190px; gap: 8px; }
  .search, .select { width: 100%; padding: 10px 11px; outline: none; }
  .search:focus, .select:focus { border-color: rgba(72,228,255,.6); box-shadow: 0 0 0 3px rgba(72,228,255,.12); }
  .filter-toggle { width: 100%; justify-content: space-between; }
  .filter-panel { display: grid; gap: 12px; margin-top: 8px; padding: 12px; background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow); }
  .filter-panel[hidden] { display: none; }
  .facet h2 { margin: 0 0 7px; color: var(--muted); font-size: 11px; letter-spacing: .1em; text-transform: uppercase; }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; }
  .chip { padding: 7px 9px; border: 1px solid var(--border); border-radius: 999px; background: var(--card-2); color: var(--muted); cursor: pointer; font-size: 12px; }
  .chip span { color: #71869a; margin-left: 3px; }
  .chip.active { color: var(--text); border-color: rgba(72,228,255,.58); background: rgba(72,228,255,.1); }
  .results-line { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin: 13px 2px 8px; color: var(--muted); font-size: 13px; }
  .results-line strong { color: var(--text); }
  .list { display: grid; gap: 9px; }
  .row { display: grid; grid-template-columns: 44px 1fr; gap: 10px; padding: 11px; background: linear-gradient(180deg, rgba(255,255,255,.025), rgba(255,255,255,.01)), var(--card); border: 1px solid var(--border); border-radius: 14px; box-shadow: var(--shadow); }
  .row.watched { opacity: .67; }
  .order { display: grid; place-items: center; align-self: start; width: 42px; min-height: 42px; border: 1px solid rgba(72,228,255,.2); border-radius: 12px; color: var(--accent-2); background: #08111a; font-size: 13px; font-weight: 800; font-variant-numeric: tabular-nums; }
  .row-main { min-width: 0; }
  .title-line { display: flex; align-items: flex-start; gap: 7px; min-width: 0; }
  .series-pill { flex: 0 0 auto; padding: 3px 7px; border: 1px solid rgba(72,228,255,.25); border-radius: 999px; color: var(--accent-2); background: rgba(72,228,255,.08); font-size: 11px; white-space: nowrap; }
  .title-button { min-width: 0; padding: 0; border: 0; background: none; color: var(--text); cursor: pointer; text-align: left; font-weight: 750; line-height: 1.3; }
  .title-button:hover { text-decoration: underline; }
  .metadata { margin-top: 4px; color: var(--muted); font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .topics { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 7px; }
  .topic { padding: 3px 7px; border-radius: 999px; background: rgba(0,0,0,.2); border: 1px solid rgba(255,255,255,.08); color: #bfd0e1; font-size: 11px; }
  .actions { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 9px; }
  .actions .btn { font-size: 12px; padding: 7px 9px; }
  .empty { padding: 25px 12px; text-align: center; color: var(--muted); background: var(--card); border: 1px dashed var(--border); border-radius: var(--radius); }
  footer { display: flex; flex-wrap: wrap; gap: 7px; margin: 14px 0 28px; }
  .hint { width: 100%; color: var(--muted); font-size: 12px; }
  dialog { width: min(720px, 94vw); max-height: 88vh; padding: 0; border: 1px solid var(--border); border-radius: var(--radius); background: var(--card); color: var(--text); box-shadow: 0 24px 70px rgba(0,0,0,.55); }
  dialog::backdrop { background: rgba(0,0,0,.68); backdrop-filter: blur(2px); }
  .dialog-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; padding: 12px 14px; border-bottom: 1px solid var(--border); }
  .dialog-body { padding: 14px; overflow: auto; }
  .detail-title { margin: 0; font-size: 20px; line-height: 1.2; }
  .detail-description { white-space: pre-wrap; color: #cbd9e7; font-size: 13px; max-height: 340px; overflow: auto; }
  .notes { width: 100%; min-height: 220px; resize: vertical; padding: 11px; border: 1px solid var(--border); border-radius: 12px; background: #08111a; color: var(--text); outline: none; }
  .dialog-actions { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 12px; }
  @media (max-width: 620px) {
    .wrap { padding: 12px; }
    .titlebar { flex-direction: column; }
    .titlebar > .btn { align-self: stretch; }
    .tabs { grid-template-columns: repeat(3, 1fr); }
    .search-row { grid-template-columns: 1fr; }
    .nextup { grid-template-columns: 1fr; }
    .nextup .btn { width: 100%; }
    .title-line { display: block; }
    .series-pill { display: inline-flex; margin-bottom: 4px; }
    .metadata { white-space: normal; }
  }
</style>
</head>
<body>
<main class="wrap">
  <header>
    <div class="titlebar">
      <div>
        <div class="kicker">The Library / Radiology</div>
        <h1>NeuroRadish Video Catalog</h1>
        <p class="subtitle">A numbered, study-oriented catalog of the channel. Start with the default study order, or filter by series, anatomy/topic, format, and Shorts.</p>
      </div>
      <button class="btn ghost" id="btnHelp" type="button">How to use</button>
    </div>
    <div class="stats">
      <div class="stat"><div class="number" id="watchedCount">0</div><div class="label">Watched</div></div>
      <div class="stat"><div class="number" id="leftCount">0</div><div class="label">Left</div></div>
      <div class="stat"><div class="number" id="shownCount">0</div><div class="label">Shown by filters</div></div>
    </div>
    <div class="progress" aria-label="Overall progress"><div class="progress-track"><span id="progressFill"></span></div><div class="progress-label" id="progressLabel">0%</div></div>
  </header>

  <section class="nextup" id="nextUp" hidden>
    <div><div class="next-label">Next up</div><div class="next-title" id="nextTitle"></div><div class="next-meta" id="nextMeta"></div></div>
    <button class="btn primary" id="nextButton" type="button">Open next</button>
  </section>

  <section class="toolbar">
    <div class="tabs" role="tablist" aria-label="Watch status">
      <button class="tab active" data-view="need" role="tab">Need</button>
      <button class="tab" data-view="all" role="tab">All</button>
      <button class="tab" data-view="seen" role="tab">Seen</button>
      <button class="tab" data-view="favorites" role="tab">Favorites</button>
      <button class="tab" data-view="shorts" role="tab">Shorts</button>
    </div>
    <div class="search-row"><input class="search" id="search" type="search" placeholder="Search title, topic, series, or description…" aria-label="Search videos"><select class="select" id="sort" aria-label="Sort videos"><option value="study">Study order</option><option value="topic">Category / topic</option><option value="newest">Newest first</option><option value="oldest">Oldest first</option><option value="shortest">Shortest first</option><option value="longest">Longest first</option><option value="title">Title A–Z</option></select></div>
    <select class="select" id="approach" aria-label="Choose a saved watching approach"><option value="guided">Approach: Guided study order</option><option value="board-brain">Approach: Brain board review</option><option value="board-spine">Approach: Spine board review</option><option value="board-pediatric">Approach: Pediatric board review</option><option value="board-head-neck">Approach: Head / Neck board review</option><option value="buzzword">Approach: Buzzword Core Exam</option><option value="rapid">Approach: Rapid review compilations</option><option value="foundations">Approach: Foundations &amp; approach</option><option value="shorts">Approach: Sign Shorts</option><option value="custom">Approach: Current custom view</option></select>
    <button class="btn filter-toggle" id="filterToggle" type="button" aria-expanded="false"><span>Filters</span><span id="filterArrow">▾</span></button>
    <div class="filter-panel" id="filterPanel" hidden>
      <div class="facet"><h2>Study track</h2><div class="chips" id="trackFilters"></div></div>
      <div class="facet"><h2>Category / topic</h2><div class="chips" id="categoryFilters"></div></div>
      <div class="facet"><h2>Format</h2><div class="chips" id="formatFilters"></div></div>
      <button class="btn small ghost" id="clearFilters" type="button">Clear topic filters</button>
    </div>
  </section>

  <div class="results-line"><span id="resultsSummary"></span><span id="savedState">Saved locally on this phone</span></div>
  <section class="list" id="videoList"></section>

  <footer>
    <button class="btn small" id="downloadBackup" type="button">Download backup</button>
    <label class="btn small" for="restoreFile">Restore backup</label><input id="restoreFile" type="file" accept="application/json" hidden>
    <button class="btn small" id="downloadNotes" type="button">Export notes</button>
    <button class="btn small ghost" id="resetWatched" type="button">Reset watched</button>
    <div class="hint">Progress, favorites, and notes stay in this browser. Export a backup before changing phones.</div>
  </footer>
</main>

<dialog id="detailDialog"><div class="dialog-head"><strong>Video details</strong><button class="btn small ghost" data-close="detailDialog" type="button">Close</button></div><div class="dialog-body"><div id="detailContent"></div></div></dialog>
<dialog id="notesDialog"><div class="dialog-head"><strong id="notesHeading">Notes</strong><button class="btn small ghost" data-close="notesDialog" type="button">Close</button></div><div class="dialog-body"><textarea class="notes" id="notesArea" placeholder="What do you want to remember?"></textarea><div class="dialog-actions"><button class="btn primary" id="saveNotes" type="button">Save notes</button></div></div></dialog>
<dialog id="helpDialog"><div class="dialog-head"><strong>How to use this catalog</strong><button class="btn small ghost" data-close="helpDialog" type="button">Close</button></div><div class="dialog-body"><p><strong>Default study order:</strong> foundations and approach → numbered Board Review cases → Buzzword Core Exam cases → rapid compilations → sign review and Shorts.</p><p><strong>Numbers:</strong> the blue badge is the overall catalog position. The title and cyan pill preserve the original series number, such as <em>Board review · spine · Case 1</em> or <em>Buzzword · Case 40</em>.</p><p><strong>Choose an approach:</strong> use the Approach menu for a ready-made queue such as Brain board review, Spine board review, Buzzword Core Exam, or Sign Shorts. You can then refine it with filters or sorting.</p><p><strong>One at a time:</strong> use <em>Need</em>, open the first item, and mark it watched when finished. <em>Next up</em> follows the current filtered queue.</p><p><strong>Persistence:</strong> the selected approach, filters, sort order, search, watched status, favorites, and notes are saved locally in this phone/browser.</p></div></dialog>

<script>
const videos = __DATA__;
const STORAGE_KEY = 'neuroradish-catalog-v1';
const stateDefaults = { watched: {}, favorites: {}, notes: {}, ui: { view: 'need', sort: 'study', search: '', approach: 'guided', filters: { track: [], category: [], format: [] }, filterOpen: false } };
let state = loadState();
let currentNotesId = null;

function $(id) { return document.getElementById(id); }
function normalizeState(raw) {
  const s = Object.assign({}, stateDefaults, raw || {});
  s.watched = Object.assign({}, (raw && raw.watched) || {});
  s.favorites = Object.assign({}, (raw && raw.favorites) || {});
  s.notes = Object.assign({}, (raw && raw.notes) || {});
  s.ui = Object.assign({}, stateDefaults.ui, (raw && raw.ui) || {});
  s.ui.filters = Object.assign({}, stateDefaults.ui.filters, (raw && raw.ui && raw.ui.filters) || {});
  return s;
}
function loadState() {
  try { return normalizeState(JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')); }
  catch (_) { return normalizeState({}); }
}
function saveState() { try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (_) {} }
function esc(value) { return String(value ?? '').replace(/[&<>'"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch])); }
function watched(v) { return !!state.watched[v.video_id]; }
function favorite(v) { return !!state.favorites[v.video_id]; }
function categoryName(v) { return v.category.replace(' — ', ' · '); }
function seriesLabel(v) {
  if (v.track === 'Board Review Cases') return `${categoryName(v)}${v.series_number ? ` · Case ${v.series_number}` : ''}`;
  if (v.track === 'Core Exam / Buzzword Cases') return `Buzzword · Case ${v.series_number}`;
  if (v.track === 'Rapid Review Compilations' && v.series_number) return `Rapid review · ${v.series_number}`;
  return categoryName(v);
}
function searchText(v) { return [v.title, v.track, v.category, v.subcategory, v.format, v.description].join(' ').toLowerCase(); }
function facetValues(field) {
  const counts = {};
  videos.forEach(v => { counts[v[field]] = (counts[v[field]] || 0) + 1; });
  return Object.entries(counts).sort((a,b) => a[0].localeCompare(b[0], undefined, { sensitivity: 'base' }));
}
function renderFacet(field, id) {
  const selected = state.ui.filters[field] || [];
  $(id).innerHTML = facetValues(field).map(([value, count]) => `<button class="chip ${selected.includes(value) ? 'active' : ''}" data-facet="${field}" data-value="${esc(value)}" type="button">${esc(categoryName({category:value}))}<span>${count}</span></button>`).join('');
  $(id).querySelectorAll('[data-facet]').forEach(btn => btn.onclick = () => {
    const f = btn.dataset.facet, value = btn.dataset.value, list = state.ui.filters[f] || [];
    markCustomApproach(); state.ui.filters[f] = list.includes(value) ? list.filter(x => x !== value) : [...list, value];
    saveState(); renderAll();
  });
}
function filteredVideos() {
  const view = state.ui.view;
  const term = (state.ui.search || '').trim().toLowerCase();
  const fs = state.ui.filters || {};
  let result = videos.filter(v => {
    if (view === 'need' && watched(v)) return false;
    if (view === 'seen' && !watched(v)) return false;
    if (view === 'favorites' && !favorite(v)) return false;
    if (view === 'shorts' && v.format !== 'Short') return false;
    if (term && !searchText(v).includes(term)) return false;
    for (const field of ['track','category','format']) if ((fs[field] || []).length && !fs[field].includes(v[field])) return false;
    return true;
  });
  const sort = state.ui.sort;
  const byTitle = (a,b) => a.title.localeCompare(b.title, undefined, { sensitivity: 'base' });
  if (sort === 'topic') result.sort((a,b) => a.category.localeCompare(b.category) || Number(a.series_number || 9999) - Number(b.series_number || 9999) || byTitle(a,b));
  else if (sort === 'newest') result.sort((a,b) => b.upload_date.localeCompare(a.upload_date) || byTitle(a,b));
  else if (sort === 'oldest') result.sort((a,b) => a.upload_date.localeCompare(b.upload_date) || byTitle(a,b));
  else if (sort === 'shortest') result.sort((a,b) => Number(a.duration_seconds || 0) - Number(b.duration_seconds || 0) || byTitle(a,b));
  else if (sort === 'longest') result.sort((a,b) => Number(b.duration_seconds || 0) - Number(a.duration_seconds || 0) || byTitle(a,b));
  else if (sort === 'title') result.sort(byTitle);
  else result.sort((a,b) => Number(a.catalog_order) - Number(b.catalog_order));
  return result;
}
function renderStats() {
  const watchedCount = videos.filter(watched).length;
  const pct = videos.length ? Math.round(watchedCount / videos.length * 100) : 0;
  $('watchedCount').textContent = watchedCount;
  $('leftCount').textContent = videos.length - watchedCount;
  $('shownCount').textContent = filteredVideos().length;
  $('progressFill').style.width = `${pct}%`;
  $('progressLabel').textContent = `${pct}%`;
}
function renderNextUp(rows) {
  const next = rows.find(v => !watched(v)) || (state.ui.view === 'need' ? null : videos.find(v => !watched(v)));
  if (!next) { $('nextUp').hidden = true; return; }
  $('nextUp').hidden = false;
  $('nextTitle').textContent = `${next.catalog_order}. ${next.title}`;
  $('nextMeta').textContent = `${seriesLabel(next)} · ${next.duration}`;
  $('nextButton').onclick = () => openVideo(next);
}
const approaches = {
  guided: { view: 'need', sort: 'study', search: '', filters: { track: [], category: [], format: [] } },
  'board-brain': { view: 'need', sort: 'study', search: '', filters: { track: ['Board Review Cases'], category: ['Board review — brain'], format: [] } },
  'board-spine': { view: 'need', sort: 'study', search: '', filters: { track: ['Board Review Cases'], category: ['Board review — spine'], format: [] } },
  'board-pediatric': { view: 'need', sort: 'study', search: '', filters: { track: ['Board Review Cases'], category: ['Board review — pediatric'], format: [] } },
  'board-head-neck': { view: 'need', sort: 'study', search: '', filters: { track: ['Board Review Cases'], category: ['Board review — head & neck'], format: [] } },
  buzzword: { view: 'need', sort: 'study', search: '', filters: { track: ['Core Exam / Buzzword Cases'], category: [], format: [] } },
  rapid: { view: 'need', sort: 'study', search: '', filters: { track: ['Rapid Review Compilations'], category: [], format: [] } },
  foundations: { view: 'need', sort: 'study', search: '', filters: { track: ['Foundations & Approach'], category: [], format: [] } },
  shorts: { view: 'shorts', sort: 'title', search: '', filters: { track: [], category: [], format: [] } }
};
function chooseApproach(key) {
  const preset = approaches[key];
  if (!preset) return;
  state.ui.approach = key;
  state.ui.view = preset.view;
  state.ui.sort = preset.sort;
  state.ui.search = preset.search;
  state.ui.filters = JSON.parse(JSON.stringify(preset.filters));
  saveState(); renderAll();
}
function markCustomApproach() { if (state.ui.approach !== 'custom') state.ui.approach = 'custom'; }
function rowHtml(v) {
  const isWatched = watched(v), isFav = favorite(v);
  const topicList = [v.subcategory, v.format].filter(Boolean);
  return `<article class="row ${isWatched ? 'watched' : ''}" data-id="${v.video_id}">
    <div class="order" aria-label="Catalog position ${v.catalog_order}">${v.catalog_order}</div>
    <div class="row-main">
      <div class="title-line"><span class="series-pill">${esc(seriesLabel(v))}</span><button class="title-button" data-detail="${v.video_id}" type="button">${esc(v.title)}</button></div>
      <div class="metadata">${esc(v.duration)} · uploaded ${esc(v.upload_date)} · ${Number(v.views || 0).toLocaleString()} views</div>
      <div class="topics">${topicList.map(x => `<span class="topic">${esc(x)}</span>`).join('')}</div>
      <div class="actions">
        <a class="btn primary" data-open="${v.video_id}" href="${v.url}" target="_blank" rel="noopener">Open</a>
        <button class="btn" data-watch="${v.video_id}" type="button">${isWatched ? '✓ Watched' : 'Mark watched'}</button>
        <button class="btn" data-favorite="${v.video_id}" type="button">${isFav ? '★ Favorite' : '☆ Favorite'}</button>
        <button class="btn" data-notes="${v.video_id}" type="button">Notes</button>
      </div>
    </div>
  </article>`;
}
function renderList(rows) {
  $('videoList').innerHTML = rows.length ? rows.map(rowHtml).join('') : '<div class="empty">No videos match this view. Try clearing a filter or switching to All.</div>';
  $('videoList').querySelectorAll('[data-open]').forEach(el => el.onclick = () => { markWatched(el.dataset.open, true); });
  $('videoList').querySelectorAll('[data-watch]').forEach(el => el.onclick = () => { markWatched(el.dataset.watch, !state.watched[el.dataset.watch]); });
  $('videoList').querySelectorAll('[data-favorite]').forEach(el => el.onclick = () => { const id = el.dataset.favorite; state.favorites[id] = !state.favorites[id]; saveState(); renderAll(); });
  $('videoList').querySelectorAll('[data-notes]').forEach(el => el.onclick = () => openNotes(el.dataset.notes));
  $('videoList').querySelectorAll('[data-detail]').forEach(el => el.onclick = () => openDetail(el.dataset.detail));
}
function markWatched(id, value) { if (value) state.watched[id] = true; else delete state.watched[id]; saveState(); renderAll(); }
function openVideo(v) { markWatched(v.video_id, true); window.open(v.url, '_blank', 'noopener'); }
function openDetail(id) {
  const v = videos.find(x => x.video_id === id); if (!v) return;
  $('detailContent').innerHTML = `<h2 class="detail-title">${esc(v.title)}</h2><div class="topics"><span class="topic">${esc(seriesLabel(v))}</span><span class="topic">${esc(v.duration)}</span><span class="topic">${esc(v.format)}</span></div><p class="detail-description">${esc(v.description || 'No description was supplied by YouTube.')}</p><div class="dialog-actions"><a class="btn primary" href="${v.url}" target="_blank" rel="noopener" data-detail-open="${v.video_id}">Open on YouTube</a><button class="btn" type="button" data-detail-watch="${v.video_id}">${watched(v) ? '✓ Watched' : 'Mark watched'}</button></div>`;
  $('detailDialog').showModal();
  $('detailContent').querySelector('[data-detail-open]').onclick = () => markWatched(v.video_id, true);
  $('detailContent').querySelector('[data-detail-watch]').onclick = () => markWatched(v.video_id, !watched(v));
}
function openNotes(id) { const v = videos.find(x => x.video_id === id); if (!v) return; currentNotesId = id; $('notesHeading').textContent = `Notes · ${v.title}`; $('notesArea').value = state.notes[id] || ''; $('notesDialog').showModal(); setTimeout(() => $('notesArea').focus(), 50); }
function saveNotes() { if (!currentNotesId) return; const value = $('notesArea').value.trim(); if (value) state.notes[currentNotesId] = value; else delete state.notes[currentNotesId]; saveState(); $('notesDialog').close(); }
function setView(view) { markCustomApproach(); state.ui.view = view; saveState(); renderAll(); }
function renderAll() {
  const rows = filteredVideos();
  document.querySelectorAll('.tab').forEach(btn => { const active = btn.dataset.view === state.ui.view; btn.classList.toggle('active', active); btn.setAttribute('aria-selected', String(active)); });
  $('search').value = state.ui.search || '';
  $('sort').value = state.ui.sort || 'study';
  $('approach').value = state.ui.approach || 'custom';
  $('filterPanel').hidden = !state.ui.filterOpen;
  $('filterToggle').setAttribute('aria-expanded', String(state.ui.filterOpen));
  $('filterArrow').textContent = state.ui.filterOpen ? '▴' : '▾';
  renderFacet('track', 'trackFilters'); renderFacet('category', 'categoryFilters'); renderFacet('format', 'formatFilters');
  renderStats(); renderNextUp(rows); renderList(rows);
  $('resultsSummary').innerHTML = `<strong>${rows.length}</strong> of ${videos.length} videos · ${esc(state.ui.sort === 'study' ? 'study order' : $('sort').selectedOptions[0].textContent)}`;
}
function download(filename, text, type) { const blob = new Blob([text], { type }); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = filename; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 1000); }
function notesText() { return videos.map(v => state.notes[v.video_id] ? `${v.catalog_order}. ${v.title}\n${state.notes[v.video_id]}` : '').filter(Boolean).join('\n\n---\n\n') || 'No notes yet.'; }

document.querySelectorAll('.tab').forEach(btn => btn.onclick = () => setView(btn.dataset.view));
$('approach').onchange = e => chooseApproach(e.target.value);
$('search').oninput = e => { markCustomApproach(); state.ui.search = e.target.value; saveState(); renderAll(); };
$('sort').onchange = e => { markCustomApproach(); state.ui.sort = e.target.value; saveState(); renderAll(); };
$('filterToggle').onclick = () => { state.ui.filterOpen = !state.ui.filterOpen; saveState(); renderAll(); };
$('clearFilters').onclick = () => { markCustomApproach(); state.ui.filters = { track: [], category: [], format: [] }; saveState(); renderAll(); };
$('saveNotes').onclick = saveNotes;
$('btnHelp').onclick = () => $('helpDialog').showModal();
document.querySelectorAll('[data-close]').forEach(btn => btn.onclick = () => $(btn.dataset.close).close());
document.querySelectorAll('dialog').forEach(dialog => dialog.addEventListener('click', e => { if (e.target === dialog) dialog.close(); }));
$('downloadBackup').onclick = () => download(`neuroradish-catalog-backup-${new Date().toISOString().slice(0,10)}.json`, JSON.stringify({ version: 1, catalog: 'neuroradish', state }, null, 2), 'application/json');
$('downloadNotes').onclick = () => download(`neuroradish-notes-${new Date().toISOString().slice(0,10)}.txt`, notesText(), 'text/plain');
$('restoreFile').onchange = e => { const file = e.target.files && e.target.files[0]; if (!file) return; const reader = new FileReader(); reader.onload = () => { try { const data = JSON.parse(reader.result); state = normalizeState(data.state || data); saveState(); renderAll(); } catch (_) { alert('That backup could not be read.'); } }; reader.readAsText(file); e.target.value = ''; };
$('resetWatched').onclick = () => { if (!confirm('Clear watched status? Favorites and notes will remain.')) return; state.watched = {}; saveState(); renderAll(); };
renderAll();
</script>
</body>
</html>
'''


def main():
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    data = json.dumps(payload["videos"], ensure_ascii=False, separators=(",", ":"))
    data = data.replace("</", "<\\/")
    APP_PATH.parent.mkdir(parents=True, exist_ok=True)
    APP_PATH.write_text(TEMPLATE.replace("__DATA__", data), encoding="utf-8")
    print(f"Wrote {APP_PATH} with {len(payload['videos'])} videos")


if __name__ == "__main__":
    main()
