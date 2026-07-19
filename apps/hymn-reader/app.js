(function () {
  "use strict";

  const STORAGE_KEY = "hymn-reader-preferences-v1";
  const SIZE_STEPS = [
    { label: "Small", value: "1.22rem" },
    { label: "Medium", value: "1.55rem" },
    { label: "Large", value: "1.9rem" },
    { label: "Extra large", value: "2.25rem" }
  ];

  const sourceHymns = Array.isArray(window.HYMN_DATA) ? window.HYMN_DATA : [];
  const hymns = sourceHymns
    .filter(isValidHymn)
    .map(hymn => ({
      number: hymn.number,
      title: String(hymn.title).trim(),
      lyrics: String(hymn.lyrics).trim()
    }))
    .sort((a, b) => compareHymnNumbers(a.number, b.number));

  const elements = {
    libraryView: document.getElementById("libraryView"),
    readerView: document.getElementById("readerView"),
    search: document.getElementById("hymnSearch"),
    clearSearch: document.getElementById("clearSearch"),
    resultSummary: document.getElementById("resultSummary"),
    results: document.getElementById("hymnResults"),
    emptyLibrary: document.getElementById("emptyLibrary"),
    noResults: document.getElementById("noResults"),
    back: document.getElementById("backToLibrary"),
    readerNumber: document.getElementById("readerNumber"),
    readerTitle: document.getElementById("readerTitle"),
    settingsButton: document.getElementById("readerSettingsButton"),
    settings: document.getElementById("readerSettings"),
    glowMode: document.getElementById("glowModeButton"),
    textMode: document.getElementById("textModeButton"),
    decreaseText: document.getElementById("decreaseText"),
    increaseText: document.getElementById("increaseText"),
    textSizeLabel: document.getElementById("textSizeLabel"),
    stage: document.getElementById("readerStage"),
    lyrics: document.getElementById("lyricsDisplay"),
    progress: document.getElementById("readerProgress"),
    tapHint: document.getElementById("tapHint"),
    wordCounter: document.getElementById("wordCounter")
  };

  const state = {
    hymn: null,
    words: [],
    wordIndex: 0,
    mode: "glow",
    sizeIndex: 1,
    pointerStart: null
  };

  loadPreferences();
  applyPreferences();
  renderResults("");
  bindEvents();
  openFromHash();

  function isValidHymn(hymn) {
    if (!hymn || typeof hymn !== "object") return false;
    const keys = Object.keys(hymn).sort();
    const permittedKeys = ["lyrics", "number", "title"];
    const hasOnlyPermittedFields = keys.length === permittedKeys.length && keys.every((key, index) => key === permittedKeys[index]);
    return hasOnlyPermittedFields && String(hymn.number).trim() && String(hymn.title).trim() && String(hymn.lyrics).trim();
  }

  function compareHymnNumbers(a, b) {
    const aNumber = Number(a);
    const bNumber = Number(b);
    if (Number.isFinite(aNumber) && Number.isFinite(bNumber)) return aNumber - bNumber;
    return String(a).localeCompare(String(b), undefined, { numeric: true });
  }

  function normalize(value) {
    return String(value)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLocaleLowerCase()
      .trim();
  }

  function isNumericQuery(query) {
    return /^\d+$/.test(query);
  }

  function searchHymns(rawQuery) {
    const query = normalize(rawQuery);
    if (!query) return hymns;

    if (isNumericQuery(query)) {
      return hymns
        .filter(hymn => String(hymn.number).startsWith(query))
        .sort((a, b) => {
          const aExact = String(a.number) === query ? 0 : 1;
          const bExact = String(b.number) === query ? 0 : 1;
          return aExact - bExact || compareHymnNumbers(a.number, b.number);
        });
    }

    return hymns
      .map(hymn => {
        const title = normalize(hymn.title);
        const lyrics = normalize(hymn.lyrics);
        let rank = 3;
        if (title === query) rank = 0;
        else if (title.startsWith(query)) rank = 1;
        else if (title.includes(query)) rank = 2;
        return { hymn, rank, matches: title.includes(query) || lyrics.includes(query) };
      })
      .filter(result => result.matches)
      .sort((a, b) => a.rank - b.rank || compareHymnNumbers(a.hymn.number, b.hymn.number))
      .map(result => result.hymn);
  }

  function renderResults(rawQuery) {
    const results = searchHymns(rawQuery);
    const query = normalize(rawQuery);
    const numeric = isNumericQuery(query);
    elements.results.replaceChildren();
    elements.emptyLibrary.hidden = hymns.length !== 0;
    elements.noResults.hidden = hymns.length === 0 || results.length !== 0;
    elements.clearSearch.hidden = rawQuery.length === 0;

    if (hymns.length === 0) {
      elements.resultSummary.textContent = "Waiting for hymn text";
      return;
    }

    elements.resultSummary.textContent = query
      ? `${results.length} ${results.length === 1 ? "hymn" : "hymns"} found`
      : `${hymns.length} hymns`;

    const fragment = document.createDocumentFragment();
    results.forEach(hymn => fragment.appendChild(createResultCard(hymn, query, numeric)));
    elements.results.appendChild(fragment);
  }

  function createResultCard(hymn, query, numeric) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "hymn-card";
    button.setAttribute("role", "listitem");
    button.setAttribute("aria-label", `Hymn ${hymn.number}, ${hymn.title}`);
    button.addEventListener("click", () => openHymn(hymn, true));

    const badge = document.createElement("span");
    badge.className = "hymn-badge";
    badge.textContent = hymn.number;

    const copy = document.createElement("span");
    copy.className = "hymn-card-copy";
    const title = document.createElement("span");
    title.className = "hymn-title";
    appendHighlightedText(title, hymn.title, numeric ? "" : query);
    copy.appendChild(title);

    if (query && !numeric && !normalize(hymn.title).includes(query)) {
      const excerpt = document.createElement("span");
      excerpt.className = "hymn-excerpt";
      appendHighlightedText(excerpt, lyricExcerpt(hymn.lyrics, query), query);
      copy.appendChild(excerpt);
    }

    const arrow = document.createElement("span");
    arrow.className = "result-arrow";
    arrow.setAttribute("aria-hidden", "true");
    arrow.textContent = "›";

    button.append(badge, copy, arrow);
    return button;
  }

  function appendHighlightedText(parent, text, normalizedQuery) {
    if (!normalizedQuery) {
      parent.textContent = text;
      return;
    }

    const source = String(text);
    const normalizedSource = normalize(source);
    const matchIndex = normalizedSource.indexOf(normalizedQuery);
    if (matchIndex < 0) {
      parent.textContent = source;
      return;
    }

    parent.append(document.createTextNode(source.slice(0, matchIndex)));
    const mark = document.createElement("mark");
    mark.textContent = source.slice(matchIndex, matchIndex + normalizedQuery.length);
    parent.append(mark, document.createTextNode(source.slice(matchIndex + normalizedQuery.length)));
  }

  function lyricExcerpt(lyrics, query) {
    const clean = String(lyrics).replace(/\s+/g, " ").trim();
    const index = normalize(clean).indexOf(query);
    if (index < 0) return clean.slice(0, 110);
    const start = Math.max(0, index - 36);
    const end = Math.min(clean.length, index + query.length + 62);
    return `${start > 0 ? "…" : ""}${clean.slice(start, end).trim()}${end < clean.length ? "…" : ""}`;
  }

  function openHymn(hymn, updateHash) {
    state.hymn = hymn;
    state.wordIndex = 0;
    elements.readerNumber.textContent = `Hymn ${hymn.number}`;
    elements.readerTitle.textContent = hymn.title;
    elements.libraryView.hidden = true;
    elements.readerView.hidden = false;
    elements.readerView.dataset.mode = state.mode;
    document.title = `${hymn.number} · ${hymn.title} — Hymn Reader`;
    renderLyrics();
    updateReader();
    elements.stage.scrollTop = 0;
    elements.stage.focus({ preventScroll: true });
    if (updateHash) history.pushState({ hymnNumber: String(hymn.number) }, "", `#hymn-${encodeURIComponent(hymn.number)}`);
  }

  function renderLyrics() {
    elements.lyrics.replaceChildren();
    state.words = [];
    const fragment = document.createDocumentFragment();
    const lines = state.hymn.lyrics.replace(/\r\n/g, "\n").split("\n");

    lines.forEach((line, lineIndex) => {
      const lineElement = document.createElement("p");
      lineElement.className = "lyric-line";
      lineElement.dataset.lineIndex = lineIndex;

      if (!line.trim()) {
        lineElement.classList.add("stanza-break");
        lineElement.setAttribute("aria-hidden", "true");
      } else {
        const tokens = line.split(/([\p{L}\p{N}]+(?:[’'\-][\p{L}\p{N}]+)*)/gu);
        tokens.forEach(token => {
          if (!token) return;
          if (/^[\p{L}\p{N}]/u.test(token)) {
            const word = document.createElement("span");
            word.className = "lyric-word";
            word.textContent = token;
            word.dataset.wordIndex = state.words.length;
            word.dataset.lineIndex = lineIndex;
            state.words.push(word);
            lineElement.appendChild(word);
          } else {
            lineElement.appendChild(document.createTextNode(token));
          }
        });
      }

      fragment.appendChild(lineElement);
    });

    elements.lyrics.appendChild(fragment);
  }

  function updateReader(options = {}) {
    const total = state.words.length;
    state.wordIndex = Math.max(0, Math.min(state.wordIndex, Math.max(0, total - 1)));
    const activeWord = total ? state.words[state.wordIndex] : null;
    const activeLineIndex = activeWord ? Number(activeWord.dataset.lineIndex) : -1;

    state.words.forEach((word, index) => word.classList.toggle("is-active", state.mode === "glow" && index === state.wordIndex));
    elements.lyrics.querySelectorAll(".lyric-line").forEach(line => {
      const lineIndex = Number(line.dataset.lineIndex);
      line.classList.toggle("is-active", state.mode === "glow" && lineIndex === activeLineIndex);
      line.classList.toggle("is-past", state.mode === "glow" && lineIndex < activeLineIndex);
    });

    const progress = total ? ((state.wordIndex + 1) / total) * 100 : 0;
    elements.progress.style.width = state.mode === "glow" ? `${progress}%` : "100%";
    elements.wordCounter.textContent = state.mode === "glow" && total ? `${state.wordIndex + 1} / ${total}` : "";
    elements.tapHint.textContent = state.mode === "glow" ? "Tap left or right to move through the hymn" : "Full hymn text";

    if (activeWord && options.scroll !== false && state.mode === "glow") {
      const activeLine = activeWord.closest(".lyric-line");
      activeLine.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  function moveWord(direction) {
    if (!state.hymn || state.mode !== "glow" || state.words.length === 0) return;
    const nextIndex = Math.max(0, Math.min(state.wordIndex + direction, state.words.length - 1));
    if (nextIndex === state.wordIndex) return;
    state.wordIndex = nextIndex;
    updateReader();
  }

  function closeReader(updateHistory) {
    if (!state.hymn) return;
    state.hymn = null;
    state.words = [];
    elements.settings.hidden = true;
    elements.settingsButton.setAttribute("aria-expanded", "false");
    elements.readerView.hidden = true;
    elements.libraryView.hidden = false;
    document.title = "Hymn Reader";
    if (updateHistory) history.replaceState({}, "", `${location.pathname}${location.search}`);
    requestAnimationFrame(() => elements.search.focus({ preventScroll: true }));
  }

  function setMode(mode) {
    state.mode = mode === "text" ? "text" : "glow";
    elements.readerView.dataset.mode = state.mode;
    elements.glowMode.classList.toggle("active", state.mode === "glow");
    elements.textMode.classList.toggle("active", state.mode === "text");
    elements.glowMode.setAttribute("aria-pressed", String(state.mode === "glow"));
    elements.textMode.setAttribute("aria-pressed", String(state.mode === "text"));
    updateReader({ scroll: state.mode === "glow" });
    savePreferences();
  }

  function changeTextSize(change) {
    state.sizeIndex = Math.max(0, Math.min(state.sizeIndex + change, SIZE_STEPS.length - 1));
    applyPreferences();
    savePreferences();
  }

  function applyPreferences() {
    const size = SIZE_STEPS[state.sizeIndex];
    document.documentElement.style.setProperty("--reader-size", size.value);
    elements.textSizeLabel.textContent = size.label;
    elements.decreaseText.disabled = state.sizeIndex === 0;
    elements.increaseText.disabled = state.sizeIndex === SIZE_STEPS.length - 1;
    elements.readerView.dataset.mode = state.mode;
    elements.glowMode.classList.toggle("active", state.mode === "glow");
    elements.textMode.classList.toggle("active", state.mode === "text");
    elements.glowMode.setAttribute("aria-pressed", String(state.mode === "glow"));
    elements.textMode.setAttribute("aria-pressed", String(state.mode === "text"));
  }

  function loadPreferences() {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
      if (saved?.mode === "text" || saved?.mode === "glow") state.mode = saved.mode;
      if (Number.isInteger(saved?.sizeIndex)) state.sizeIndex = Math.max(0, Math.min(saved.sizeIndex, SIZE_STEPS.length - 1));
    } catch (_error) {
      // Continue with defaults when local storage is unavailable or malformed.
    }
  }

  function savePreferences() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ mode: state.mode, sizeIndex: state.sizeIndex }));
    } catch (_error) {
      // Reading remains fully usable without saved preferences.
    }
  }

  function openFromHash() {
    const match = location.hash.match(/^#hymn-(.+)$/);
    if (!match) return;
    const number = decodeURIComponent(match[1]);
    const hymn = hymns.find(item => String(item.number) === number);
    if (hymn) openHymn(hymn, false);
  }

  function bindEvents() {
    elements.search.addEventListener("input", event => renderResults(event.target.value));
    elements.clearSearch.addEventListener("click", () => {
      elements.search.value = "";
      renderResults("");
      elements.search.focus();
    });
    elements.back.addEventListener("click", () => closeReader(true));
    elements.settingsButton.addEventListener("click", () => {
      const willOpen = elements.settings.hidden;
      elements.settings.hidden = !willOpen;
      elements.settingsButton.setAttribute("aria-expanded", String(willOpen));
    });
    elements.glowMode.addEventListener("click", () => setMode("glow"));
    elements.textMode.addEventListener("click", () => setMode("text"));
    elements.decreaseText.addEventListener("click", () => changeTextSize(-1));
    elements.increaseText.addEventListener("click", () => changeTextSize(1));

    elements.readerView.addEventListener("pointerdown", event => {
      if (event.target.closest("[data-reader-control], button")) return;
      if (event.pointerType === "mouse" && event.button !== 0) return;
      state.pointerStart = { x: event.clientX, y: event.clientY };
    });

    elements.readerView.addEventListener("pointerup", event => {
      if (!state.pointerStart) return;
      if (state.mode !== "glow") {
        state.pointerStart = null;
        return;
      }
      if (event.target.closest("[data-reader-control], button")) {
        state.pointerStart = null;
        return;
      }
      const moved = Math.hypot(event.clientX - state.pointerStart.x, event.clientY - state.pointerStart.y);
      state.pointerStart = null;
      if (moved > 12) return;
      moveWord(event.clientX < window.innerWidth / 2 ? -1 : 1);
    });

    elements.readerView.addEventListener("pointercancel", () => {
      state.pointerStart = null;
    });

    document.addEventListener("click", event => {
      if (elements.settings.hidden || event.target.closest("#readerSettings") || event.target.closest("#readerSettingsButton")) return;
      elements.settings.hidden = true;
      elements.settingsButton.setAttribute("aria-expanded", "false");
    });

    document.addEventListener("keydown", event => {
      if (!state.hymn || event.target.matches("input, button")) return;
      if (event.key === "ArrowRight" || event.key === " ") {
        event.preventDefault();
        moveWord(1);
      } else if (event.key === "ArrowLeft") {
        event.preventDefault();
        moveWord(-1);
      } else if (event.key === "Escape") {
        if (!elements.settings.hidden) {
          elements.settings.hidden = true;
          elements.settingsButton.setAttribute("aria-expanded", "false");
        } else {
          closeReader(true);
        }
      }
    });

    window.addEventListener("popstate", () => {
      const match = location.hash.match(/^#hymn-(.+)$/);
      if (match) {
        const number = decodeURIComponent(match[1]);
        const hymn = hymns.find(item => String(item.number) === number);
        if (hymn) openHymn(hymn, false);
      } else if (state.hymn) {
        closeReader(false);
      }
    });
  }
})();
