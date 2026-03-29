const SOUND_LIBRARY = Array.isArray(window.SOUND_LIBRARY) ? window.SOUND_LIBRARY : [];

const STORAGE_KEYS = {
  ratings: "sound-swipe-lab-ratings-v1",
  prefs: "sound-swipe-lab-prefs-v1",
};

const STATUS_LABELS = {
  all: "All Sounds",
  unrated: "Unrated",
  favorite: "Favorite",
  neutral: "Neutral",
  disliked: "Disliked",
};

const RATE_ACTIONS = ["favorite", "neutral", "disliked"];

const state = {
  ratings: loadRatings(),
  view: "swipe",
  folder: "all",
  status: "all",
  search: "",
  swipeIndex: 0,
  swipeHistory: [],
  reviewQueueOpen: false,
  currentSoundId: null,
  currentBrowseId: null,
  drag: null,
  isSwipeAnimating: false,
};

const sounds = SOUND_LIBRARY
  .map((item) => {
    const packLabel = formatPackName(item.pack);
    const title = formatFileName(item.file);
    const relativeFolder = item.path.includes("/") ? item.path.slice(0, item.path.lastIndexOf("/")) : "";
    const category = relativeFolder.endsWith("/Audio") ? "Audio" : "Preview";

    return {
      ...item,
      id: item.path,
      packLabel,
      title,
      category,
      searchText: `${packLabel} ${title} ${item.file} ${item.path}`.toLowerCase(),
    };
  })
  .sort((left, right) => {
    if (left.packLabel !== right.packLabel) {
      return left.packLabel.localeCompare(right.packLabel);
    }

    if (left.isPreview !== right.isPreview) {
      return left.isPreview ? -1 : 1;
    }

    return left.title.localeCompare(right.title, undefined, { numeric: true, sensitivity: "base" });
  });

const soundsById = new Map(sounds.map((sound) => [sound.id, sound]));
const packCounts = sounds.reduce((accumulator, sound) => {
  accumulator[sound.pack] = (accumulator[sound.pack] || 0) + 1;
  return accumulator;
}, {});

const elements = {
  viewToggle: document.getElementById("viewToggle"),
  folderFilter: document.getElementById("folderFilter"),
  statusFilter: document.getElementById("statusFilter"),
  searchInput: document.getElementById("searchInput"),
  clearSearchButton: document.getElementById("clearSearchButton"),
  resetRatingsButton: document.getElementById("resetRatingsButton"),
  statsGrid: document.getElementById("statsGrid"),
  replayButton: document.getElementById("replayButton"),
  stopButton: document.getElementById("stopButton"),
  audioPlayer: document.getElementById("audioPlayer"),
  playerTitle: document.getElementById("playerTitle"),
  playerMeta: document.getElementById("playerMeta"),
  swipeView: document.getElementById("swipeView"),
  browseView: document.getElementById("browseView"),
  swipeQueueMeta: document.getElementById("swipeQueueMeta"),
  reviewQueueToggle: document.getElementById("reviewQueueToggle"),
  reviewQueueToggleLabel: document.querySelector("#reviewQueueToggle .queue-toggle-label"),
  reviewQueuePanel: document.getElementById("reviewQueuePanel"),
  reviewQueueList: document.getElementById("reviewQueueList"),
  browseMeta: document.getElementById("browseMeta"),
  swipeStage: document.getElementById("swipeStage"),
  swipeCard: document.getElementById("swipeCard"),
  nextCardPreview: document.getElementById("nextCardPreview"),
  swipePackPill: document.getElementById("swipePackPill"),
  swipeRatingPill: document.getElementById("swipeRatingPill"),
  swipeTitle: document.getElementById("swipeTitle"),
  swipeSubtitle: document.getElementById("swipeSubtitle"),
  swipeEmptyState: document.getElementById("swipeEmptyState"),
  cardReplayButton: document.getElementById("cardReplayButton"),
  libraryList: document.getElementById("libraryList"),
  libraryEmptyState: document.getElementById("libraryEmptyState"),
  liveRegion: document.getElementById("liveRegion"),
};

initialize();

function initialize() {
  hydratePreferences();
  populateFolderFilter();
  bindEvents();
  render();
}

function bindEvents() {
  elements.viewToggle.addEventListener("click", (event) => {
    const button = event.target.closest("[data-view]");
    if (!button) {
      return;
    }

    state.view = button.dataset.view;
    persistPreferences();
    render();
  });

  elements.folderFilter.addEventListener("change", () => {
    state.folder = elements.folderFilter.value;
    state.swipeIndex = 0;
    persistPreferences();
    render();
  });

  elements.statusFilter.addEventListener("change", () => {
    state.status = elements.statusFilter.value;
    state.swipeIndex = 0;
    persistPreferences();
    render();
  });

  elements.searchInput.addEventListener("input", () => {
    state.search = elements.searchInput.value.trim();
    state.swipeIndex = 0;
    persistPreferences();
    render();
  });

  elements.clearSearchButton.addEventListener("click", () => {
    state.search = "";
    elements.searchInput.value = "";
    state.swipeIndex = 0;
    persistPreferences();
    render();
  });

  elements.resetRatingsButton.addEventListener("click", () => {
    const confirmed = window.confirm("Reset every favorite, neutral, and disliked rating in Sound Swipe Lab?");
    if (!confirmed) {
      return;
    }

    state.ratings = {};
    state.swipeHistory = [];
    persistRatings();
    announce("All sound ratings were reset.");
    render();
  });

  elements.reviewQueueToggle.addEventListener("click", () => {
    if (!getFilteredSounds().length) {
      return;
    }

    state.reviewQueueOpen = !state.reviewQueueOpen;
    renderSwipeView();
  });

  elements.replayButton.addEventListener("click", () => {
    playActiveSound({ restart: true });
  });

  elements.cardReplayButton.addEventListener("click", () => {
    const currentSound = getCurrentSwipeSound();
    if (!currentSound) {
      return;
    }

    setActiveSound(currentSound.id, { autoplay: true, restart: true, syncBrowse: false });
  });

  elements.stopButton.addEventListener("click", () => {
    elements.audioPlayer.pause();
    elements.audioPlayer.currentTime = 0;
  });

  document.querySelectorAll("[data-rate-action]").forEach((button) => {
    button.addEventListener("click", () => {
      applySwipeRating(button.dataset.rateAction);
    });
  });

  elements.statsGrid.addEventListener("click", (event) => {
    const button = event.target.closest("[data-status-filter]");
    if (!button) {
      return;
    }

    state.status = button.dataset.statusFilter;
    elements.statusFilter.value = state.status;
    state.swipeIndex = 0;
    persistPreferences();
    render();
  });

  elements.libraryList.addEventListener("click", (event) => {
    const playButton = event.target.closest("[data-play-sound]");
    if (playButton) {
      const soundId = playButton.dataset.playSound;
      state.currentBrowseId = soundId;
      setActiveSound(soundId, { autoplay: true, restart: true, syncBrowse: true });
      renderBrowseList();
      return;
    }

    const rateButton = event.target.closest("[data-library-rate]");
    if (rateButton) {
      const soundId = rateButton.dataset.soundId;
      const nextRating = rateButton.dataset.libraryRate;
      setRating(soundId, nextRating);
      state.currentBrowseId = soundId;
      announce(`${soundsById.get(soundId).title} marked ${labelForStatus(nextRating)}.`);
      render();
      return;
    }

    const item = event.target.closest("[data-library-item]");
    if (!item) {
      return;
    }

    const soundId = item.dataset.libraryItem;
    state.currentBrowseId = soundId;
    setActiveSound(soundId, { autoplay: true, restart: true, syncBrowse: true });
    renderBrowseList();
  });

  elements.reviewQueueList.addEventListener("click", (event) => {
    const queueItem = event.target.closest("[data-queue-index]");
    if (!queueItem) {
      return;
    }

    const nextIndex = Number(queueItem.dataset.queueIndex);
    const queue = getFilteredSounds();
    const selectedSound = queue[nextIndex];
    if (!selectedSound) {
      return;
    }

    state.swipeIndex = nextIndex;
    state.reviewQueueOpen = false;
    render();
    setActiveSound(selectedSound.id, { autoplay: true, restart: true, syncBrowse: false });
    announce(`Jumped to ${selectedSound.title}.`);
  });

  document.addEventListener("keydown", handleKeyboardShortcuts);
  bindSwipeGestures();
}

function bindSwipeGestures() {
  elements.swipeCard.addEventListener("pointerdown", (event) => {
    if (state.view !== "swipe" || state.isSwipeAnimating || !getCurrentSwipeSound()) {
      return;
    }

    if (event.target.closest("button")) {
      return;
    }

    state.drag = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      deltaX: 0,
      deltaY: 0,
    };

    elements.swipeCard.classList.add("dragging");
    elements.swipeCard.setPointerCapture(event.pointerId);
  });

  elements.swipeCard.addEventListener("pointermove", (event) => {
    if (!state.drag || state.drag.pointerId !== event.pointerId) {
      return;
    }

    state.drag.deltaX = event.clientX - state.drag.startX;
    state.drag.deltaY = event.clientY - state.drag.startY;
    updateSwipeTransform();
  });

  const releaseGesture = (event) => {
    if (!state.drag || state.drag.pointerId !== event.pointerId) {
      return;
    }

    const action = actionFromGesture(state.drag.deltaX, state.drag.deltaY);
    elements.swipeCard.releasePointerCapture(event.pointerId);
    state.drag = null;
    elements.swipeCard.classList.remove("dragging");

    if (!action) {
      resetSwipeTransform();
      return;
    }

    applySwipeRating(action);
  };

  elements.swipeCard.addEventListener("pointerup", releaseGesture);
  elements.swipeCard.addEventListener("pointercancel", releaseGesture);
}

function handleKeyboardShortcuts(event) {
  if (state.view !== "swipe") {
    return;
  }

  const target = event.target;
  const tagName = target && target.tagName ? target.tagName.toLowerCase() : "";
  if (tagName === "input" || tagName === "textarea" || tagName === "select") {
    return;
  }

  if (event.code === "Space") {
    event.preventDefault();
    const currentSound = getCurrentSwipeSound();
    if (currentSound) {
      setActiveSound(currentSound.id, { autoplay: true, restart: true, syncBrowse: false });
    }
    return;
  }

  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "z") {
    event.preventDefault();
    undoLastSwipeAction();
    return;
  }

  if (event.key === "1") {
    event.preventDefault();
    applySwipeRating("disliked");
    return;
  }

  if (event.key === "2") {
    event.preventDefault();
    applySwipeRating("neutral");
    return;
  }

  if (event.key === "4") {
    event.preventDefault();
    applySwipeRating("favorite");
  }
}

function render() {
  ensureValidSelection();
  renderControls();
  renderStats();
  renderPlayerPanel();
  renderSwipeView();
  renderBrowseList();
}

function renderControls() {
  elements.folderFilter.value = state.folder;
  elements.statusFilter.value = state.status;
  elements.searchInput.value = state.search;

  elements.viewToggle.querySelectorAll("[data-view]").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === state.view);
  });

  elements.swipeView.classList.toggle("hidden", state.view !== "swipe");
  elements.browseView.classList.toggle("hidden", state.view !== "browse");
}

function renderStats() {
  const summarySounds = getSummarySounds();
  const totals = {
    all: summarySounds.length,
    favorite: 0,
    neutral: 0,
    disliked: 0,
    unrated: 0,
  };

  summarySounds.forEach((sound) => {
    const rating = getRating(sound.id);
    totals[rating] += 1;
  });

  const cards = [
    { key: "all", label: "Visible Scope", help: scopeLabel(summarySounds.length) },
    { key: "favorite", label: "Favorites", help: "Saved keepers" },
    { key: "neutral", label: "Neutral", help: "Maybe later" },
    { key: "disliked", label: "Disliked", help: "Not for now" },
    { key: "unrated", label: "Unrated", help: "Still waiting" },
  ];

  elements.statsGrid.innerHTML = cards
    .map((card) => {
      const isActive = state.status === card.key || (card.key === "all" && state.status === "all");
      return `
        <button type="button" class="summary-card ${isActive ? "is-active" : ""}" data-status-filter="${card.key}">
          <span class="summary-label">${card.label}</span>
          <span class="summary-value">${totals[card.key]}</span>
          <span class="summary-help">${card.help}</span>
        </button>
      `;
    })
    .join("");
}

function renderPlayerPanel() {
  const activeSound = soundsById.get(state.currentSoundId);
  if (!activeSound) {
    elements.playerTitle.textContent = "Pick a sound to start";
    elements.playerMeta.textContent = "Use the controls below or hit space in swipe mode to replay the current sound.";
    elements.audioPlayer.removeAttribute("src");
    elements.audioPlayer.load();
    return;
  }

  elements.playerTitle.textContent = activeSound.title;
  elements.playerMeta.innerHTML = `${activeSound.packLabel} • ${labelForStatus(getRating(activeSound.id))} • <span class="player-meta-accent">${activeSound.path}</span>`;

  const desiredSource = activeSound.path;
  const currentSource = decodeURIComponent(elements.audioPlayer.getAttribute("src") || "");
  if (currentSource !== desiredSource) {
    elements.audioPlayer.src = desiredSource;
    elements.audioPlayer.load();
  }
}

function renderSwipeView() {
  const queue = getFilteredSounds();
  const currentSound = queue[state.swipeIndex] || null;
  const nextSound = queue[state.swipeIndex + 1] || null;

  elements.swipeQueueMeta.textContent = queue.length
    ? `${state.swipeIndex + 1} of ${queue.length} in this review queue`
    : "No sounds match the current queue";
  elements.reviewQueueToggle.disabled = queue.length === 0;
  elements.reviewQueueToggle.setAttribute("aria-expanded", String(state.reviewQueueOpen && queue.length > 0));
  elements.reviewQueueToggleLabel.textContent = state.reviewQueueOpen && queue.length > 0 ? "Hide review queue" : "See review queue";
  elements.reviewQueuePanel.classList.toggle("hidden", !(state.reviewQueueOpen && queue.length > 0));
  elements.reviewQueueList.innerHTML = renderReviewQueue(queue, currentSound);

  elements.swipeEmptyState.classList.toggle("hidden", Boolean(currentSound));
  elements.swipeCard.classList.toggle("hidden", !currentSound);
  elements.nextCardPreview.classList.toggle("hidden", !nextSound);

  if (!currentSound) {
    state.reviewQueueOpen = false;
    resetSwipeTransform();
    return;
  }

  elements.swipePackPill.textContent = currentSound.packLabel;
  elements.swipeTitle.textContent = currentSound.title;
  elements.swipeSubtitle.textContent = `${currentSound.category} clip • ${currentSound.path}`;
  applyRatingPill(elements.swipeRatingPill, getRating(currentSound.id));

  if (nextSound) {
    elements.nextCardPreview.innerHTML = `
      <div class="card-topline">
        <span class="pill pack-pill">${nextSound.packLabel}</span>
        <span class="pill rating-pill ${getRating(nextSound.id)}">${labelForStatus(getRating(nextSound.id))}</span>
      </div>
      <h3>${nextSound.title}</h3>
      <p class="card-subtitle">${nextSound.category} clip • ${nextSound.path}</p>
    `;
  } else {
    elements.nextCardPreview.innerHTML = "";
  }

  if (state.view === "swipe") {
    state.currentSoundId = currentSound.id;
    renderPlayerPanel();
  }
}

function renderBrowseList() {
  const filteredSounds = getFilteredSounds();
  elements.browseMeta.textContent = filteredSounds.length
    ? `${filteredSounds.length} sound${filteredSounds.length === 1 ? "" : "s"} ready to click through`
    : "No sounds match this library filter";

  elements.libraryEmptyState.classList.toggle("hidden", filteredSounds.length !== 0);
  elements.libraryList.classList.toggle("hidden", filteredSounds.length === 0);

  if (!filteredSounds.length) {
    elements.libraryList.innerHTML = "";
    return;
  }

  elements.libraryList.innerHTML = filteredSounds
    .map((sound) => {
      const rating = getRating(sound.id);
      const isSelected = state.currentBrowseId === sound.id || (state.view === "browse" && state.currentSoundId === sound.id);
      return `
        <article class="library-item ${isSelected ? "is-selected" : ""}" data-library-item="${sound.id}">
          <div class="library-main">
            <button type="button" class="play-row-button" data-play-sound="${sound.id}">Play</button>
            <div class="library-copy">
              <p class="library-pack">${sound.packLabel}</p>
              <h3 class="library-title">${sound.title}</h3>
              <p class="library-path">${sound.path}</p>
            </div>
          </div>

          <div class="library-actions">
            <span class="library-status ${rating}">${labelForStatus(rating)}</span>
            ${renderLibraryRateButton(sound, "disliked", "No")}
            ${renderLibraryRateButton(sound, "neutral", "Maybe")}
            ${renderLibraryRateButton(sound, "favorite", "Yes")}
          </div>
        </article>
      `;
    })
    .join("");
}

function renderLibraryRateButton(sound, rating, label) {
  const isActive = getRating(sound.id) === rating;
  return `
    <button
      type="button"
      class="mini-rate-button ${rating} ${isActive ? "is-active" : ""}"
      data-library-rate="${rating}"
      data-sound-id="${sound.id}"
    >
      ${label}
    </button>
  `;
}

function renderReviewQueue(queue, currentSound) {
  if (!queue.length) {
    return "";
  }

  return queue
    .map((sound, index) => {
      const rating = getRating(sound.id);
      const isActive = currentSound && currentSound.id === sound.id;
      return `
        <button type="button" class="review-queue-item ${isActive ? "is-active" : ""}" data-queue-index="${index}">
          <span class="review-queue-index">${index + 1}</span>
          <span class="review-queue-copy">
            <span class="review-queue-name">${sound.title}</span>
            <span class="review-queue-path">${sound.packLabel} • ${sound.path}</span>
          </span>
          <span class="pill rating-pill ${rating}">${labelForStatus(rating)}</span>
        </button>
      `;
    })
    .join("");
}

function ensureValidSelection() {
  const filteredSounds = getFilteredSounds();

  if (state.swipeIndex >= filteredSounds.length) {
    state.swipeIndex = Math.max(0, filteredSounds.length - 1);
  }

  if (state.view === "swipe") {
    const currentSound = getCurrentSwipeSound();
    state.currentSoundId = currentSound ? currentSound.id : null;
    return;
  }

  if (state.currentBrowseId && filteredSounds.some((sound) => sound.id === state.currentBrowseId)) {
    state.currentSoundId = state.currentBrowseId;
    return;
  }

  const fallback = filteredSounds[0] || null;
  state.currentBrowseId = fallback ? fallback.id : null;
  state.currentSoundId = fallback ? fallback.id : null;
}

function getCurrentSwipeSound() {
  const queue = getFilteredSounds();
  return queue[state.swipeIndex] || null;
}

function getFilteredSounds() {
  const searchQuery = state.search.toLowerCase();

  return sounds.filter((sound) => {
    if (state.folder !== "all" && sound.pack !== state.folder) {
      return false;
    }

    if (searchQuery && !sound.searchText.includes(searchQuery)) {
      return false;
    }

    if (state.status !== "all" && getRating(sound.id) !== state.status) {
      return false;
    }

    return true;
  });
}

function getSummarySounds() {
  const searchQuery = state.search.toLowerCase();

  return sounds.filter((sound) => {
    if (state.folder !== "all" && sound.pack !== state.folder) {
      return false;
    }

    if (searchQuery && !sound.searchText.includes(searchQuery)) {
      return false;
    }

    return true;
  });
}

function applySwipeRating(nextRating) {
  if (state.view !== "swipe" || state.isSwipeAnimating) {
    return;
  }

  const queueBefore = getFilteredSounds();
  const currentSound = queueBefore[state.swipeIndex];
  if (!currentSound) {
    return;
  }

  const previousRating = getRating(currentSound.id);
  const nextSoundId = queueBefore[state.swipeIndex + 1]?.id || queueBefore[state.swipeIndex - 1]?.id || null;
  const exitClass = nextRating === "favorite" ? "exit-right" : nextRating === "disliked" ? "exit-left" : "exit-up";

  state.isSwipeAnimating = true;
  elements.swipeCard.classList.add(exitClass);

  window.setTimeout(() => {
    pushSwipeHistory({
      soundId: currentSound.id,
      previousRating,
      nextRating,
      previousSwipeIndex: state.swipeIndex,
      filterState: {
        folder: state.folder,
        status: state.status,
        search: state.search,
      },
    });
    setRating(currentSound.id, nextRating);
    announce(`${currentSound.title} marked ${labelForStatus(nextRating)}.`);

    const queueAfter = getFilteredSounds();
    if (!queueAfter.length) {
      state.swipeIndex = 0;
    } else if (nextSoundId) {
      const nextIndex = queueAfter.findIndex((sound) => sound.id === nextSoundId);
      state.swipeIndex = nextIndex >= 0 ? nextIndex : Math.min(state.swipeIndex, queueAfter.length - 1);
    } else {
      state.swipeIndex = Math.min(state.swipeIndex, queueAfter.length - 1);
    }

    elements.swipeCard.classList.remove(exitClass);
    state.isSwipeAnimating = false;
    resetSwipeTransform();
    render();

    const nextCurrentSound = getCurrentSwipeSound();
    if (nextCurrentSound) {
      setActiveSound(nextCurrentSound.id, { autoplay: true, restart: true, syncBrowse: false });
    }
  }, 180);
}

function setRating(soundId, nextRating) {
  if (nextRating === "unrated") {
    delete state.ratings[soundId];
    persistRatings();
    return;
  }

  if (!RATE_ACTIONS.includes(nextRating)) {
    return;
  }

  state.ratings[soundId] = nextRating;
  persistRatings();
}

function pushSwipeHistory(entry) {
  state.swipeHistory.push(entry);

  if (state.swipeHistory.length > 150) {
    state.swipeHistory.shift();
  }
}

function undoLastSwipeAction() {
  if (state.view !== "swipe" || state.isSwipeAnimating) {
    return;
  }

  const lastAction = state.swipeHistory.pop();
  if (!lastAction) {
    announce("Nothing to undo.");
    return;
  }

  state.folder = lastAction.filterState.folder;
  state.status = lastAction.filterState.status;
  state.search = lastAction.filterState.search;
  setRating(lastAction.soundId, lastAction.previousRating);
  persistPreferences();

  const queueAfterUndo = getFilteredSounds();
  const restoredIndex = queueAfterUndo.findIndex((sound) => sound.id === lastAction.soundId);

  if (restoredIndex >= 0) {
    state.swipeIndex = restoredIndex;
  } else if (queueAfterUndo.length) {
    state.swipeIndex = Math.max(0, Math.min(lastAction.previousSwipeIndex, queueAfterUndo.length - 1));
  } else {
    state.swipeIndex = 0;
  }

  render();

  if (restoredIndex >= 0) {
    setActiveSound(lastAction.soundId, { autoplay: true, restart: true, syncBrowse: false });
    const restoredSound = soundsById.get(lastAction.soundId);
    announce(`Went back to ${restoredSound ? restoredSound.title : "the previous sound"}.`);
    return;
  }

  announce("Undid the last swipe.");
}

function getRating(soundId) {
  return state.ratings[soundId] || "unrated";
}

function setActiveSound(soundId, options = {}) {
  const { autoplay = false, restart = false, syncBrowse = true } = options;
  const sound = soundsById.get(soundId);
  if (!sound) {
    return;
  }

  state.currentSoundId = sound.id;
  if (syncBrowse) {
    state.currentBrowseId = sound.id;
  }

  renderPlayerPanel();

  const sameSource = decodeURIComponent(elements.audioPlayer.getAttribute("src") || "") === sound.path;
  if (!sameSource) {
    elements.audioPlayer.src = sound.path;
    elements.audioPlayer.load();
  }

  if (restart) {
    elements.audioPlayer.currentTime = 0;
  }

  if (autoplay) {
    const playPromise = elements.audioPlayer.play();
    if (playPromise && typeof playPromise.catch === "function") {
      playPromise.catch(() => {});
    }
  }
}

function playActiveSound(options = {}) {
  const activeSound = soundsById.get(state.currentSoundId);
  if (!activeSound) {
    return;
  }

  setActiveSound(activeSound.id, { autoplay: true, restart: options.restart !== false, syncBrowse: state.view === "browse" });
}

function updateSwipeTransform() {
  if (!state.drag) {
    return;
  }

  const rotate = state.drag.deltaX * 0.06;
  elements.swipeCard.style.transform = `translate(${state.drag.deltaX}px, ${state.drag.deltaY}px) rotate(${rotate}deg)`;
  elements.swipeStage.classList.toggle("show-like", state.drag.deltaX > 90);
  elements.swipeStage.classList.toggle("show-dislike", state.drag.deltaX < -90);
  elements.swipeStage.classList.toggle("show-neutral", state.drag.deltaY < -90 && Math.abs(state.drag.deltaY) > Math.abs(state.drag.deltaX));
}

function resetSwipeTransform() {
  elements.swipeCard.style.transform = "";
  elements.swipeStage.classList.remove("show-like", "show-dislike", "show-neutral");
}

function actionFromGesture(deltaX, deltaY) {
  if (deltaX > 110) {
    return "favorite";
  }

  if (deltaX < -110) {
    return "disliked";
  }

  if (deltaY < -105 && Math.abs(deltaY) > Math.abs(deltaX)) {
    return "neutral";
  }

  return null;
}

function populateFolderFilter() {
  const packOptions = Object.keys(packCounts)
    .sort((left, right) => formatPackName(left).localeCompare(formatPackName(right)))
    .map((pack) => `<option value="${pack}">${formatPackName(pack)} (${packCounts[pack]})</option>`);

  elements.folderFilter.innerHTML = `<option value="all">All Folders (${sounds.length})</option>${packOptions.join("")}`;
}

function hydratePreferences() {
  try {
    const savedPrefs = JSON.parse(window.localStorage.getItem(STORAGE_KEYS.prefs) || "{}");
    state.view = savedPrefs.view === "browse" ? "browse" : "swipe";
    state.folder = savedPrefs.folder && (savedPrefs.folder === "all" || packCounts[savedPrefs.folder]) ? savedPrefs.folder : "all";
    state.status = savedPrefs.status && STATUS_LABELS[savedPrefs.status] ? savedPrefs.status : "all";
    state.search = typeof savedPrefs.search === "string" ? savedPrefs.search : "";
  } catch (error) {
    state.view = "swipe";
    state.folder = "all";
    state.status = "all";
    state.search = "";
  }
}

function persistPreferences() {
  const payload = {
    view: state.view,
    folder: state.folder,
    status: state.status,
    search: state.search,
  };

  window.localStorage.setItem(STORAGE_KEYS.prefs, JSON.stringify(payload));
}

function loadRatings() {
  try {
    const savedRatings = JSON.parse(window.localStorage.getItem(STORAGE_KEYS.ratings) || "{}");
    if (!savedRatings || typeof savedRatings !== "object") {
      return {};
    }

    return savedRatings;
  } catch (error) {
    return {};
  }
}

function persistRatings() {
  window.localStorage.setItem(STORAGE_KEYS.ratings, JSON.stringify(state.ratings));
}

function applyRatingPill(element, rating) {
  element.className = `pill rating-pill ${rating}`;
  element.textContent = labelForStatus(rating);
}

function labelForStatus(rating) {
  return STATUS_LABELS[rating] || "Unrated";
}

function formatPackName(pack) {
  return prettifyLabel(pack.replace(/^kenney[_-]/i, "").replace(/[_-]+/g, " "));
}

function formatFileName(fileName) {
  const baseName = fileName.replace(/\.[^.]+$/, "");
  const spaced = baseName
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/([A-Za-z])(\d)/g, "$1 $2")
    .replace(/[_-]+/g, " ");

  return prettifyLabel(spaced);
}

function titleize(text) {
  return text
    .split(/\s+/)
    .filter(Boolean)
    .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1).toLowerCase())
    .join(" ");
}

function prettifyLabel(text) {
  return titleize(text)
    .replace(/\bUi\b/g, "UI")
    .replace(/\bRpg\b/g, "RPG")
    .replace(/\bSci Fi\b/g, "Sci-Fi");
}

function scopeLabel(count) {
  const folderText = state.folder === "all" ? "Across all folders" : formatPackName(state.folder);
  return `${folderText} • ${count} clips`;
}

function announce(message) {
  elements.liveRegion.textContent = "";
  window.setTimeout(() => {
    elements.liveRegion.textContent = message;
  }, 30);
}
