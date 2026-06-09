const DATA_URL = "data/quiz_ready.json";
const STORAGE_KEY = "radiologyPhysicsReview.v1";

const els = {
  loading: document.getElementById("loading"),
  card: document.getElementById("questionCard"),
  scope: document.getElementById("scopeSelect"),
  order: document.getElementById("orderSelect"),
  reset: document.getElementById("resetBtn"),
  position: document.getElementById("positionLabel"),
  block: document.getElementById("blockLabel"),
  title: document.getElementById("questionTitle"),
  text: document.getElementById("questionText"),
  images: document.getElementById("imageStrip"),
  choices: document.getElementById("choices"),
  feedback: document.getElementById("feedback"),
  feedbackTitle: document.getElementById("feedbackTitle"),
  explanation: document.getElementById("explanation"),
  prev: document.getElementById("prevBtn"),
  next: document.getElementById("nextBtn"),
  copy: document.getElementById("copyBtn"),
  settings: document.getElementById("settingsBtn"),
  closeSettings: document.getElementById("closeSettingsBtn"),
  settingsPanel: document.getElementById("settingsPanel"),
  settingsBackdrop: document.getElementById("settingsBackdrop"),
  answered: document.getElementById("answeredCount"),
  correctPct: document.getElementById("correctPct"),
  missed: document.getElementById("missedCount"),
  remaining: document.getElementById("remainingCount"),
};

let questions = [];
let state = loadState();

function loadState() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
  } catch {
    return {};
  }
}

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function inferBlock(id) {
  const match = String(id || "").match(/b(?:lock)?[_-]?(\d+)/i);
  return match ? `Block ${match[1]}` : "Block 1";
}

function inferQuestionNumber(id) {
  const matches = String(id || "").match(/\d+/g);
  return matches ? Number(matches[matches.length - 1]) : null;
}

function normalizeQuestion(raw) {
  const block = normalizeBlock(raw.block || raw.block_id || inferBlock(raw.id));
  return {
    ...raw,
    block,
    questionNumber: raw.question_number || raw.display_number || inferQuestionNumber(raw.id),
    choices: Array.isArray(raw.choices) ? raw.choices : [],
    images: Array.isArray(raw.images) ? raw.images : [],
  };
}

function normalizeBlock(value) {
  if (typeof value === "number") return `Block ${value}`;
  const text = String(value || "");
  return /^\d+$/.test(text) ? `Block ${text}` : text;
}

function slug(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function sessionKey() {
  return `${state.scope || "all"}:${state.orderMode || "sequential"}`;
}

function getSession() {
  state.scope ||= "all";
  state.orderMode ||= "sequential";
  state.sessions ||= {};
  const key = sessionKey();
  if (!state.sessions[key]) {
    state.sessions[key] = buildSession();
  }
  return state.sessions[key];
}

function buildSession() {
  const ids = filterQuestions().map((q) => q.id);
  const order = state.orderMode === "random" ? shuffle([...ids]) : ids;
  return { order, index: 0, answers: {}, createdAt: new Date().toISOString() };
}

function filterQuestions() {
  if (state.scope === "missed") {
    const missedIds = new Set(Object.values(state.sessions || {}).flatMap((session) =>
      Object.entries(session.answers || {})
        .filter(([, answer]) => answer.correct === false)
        .map(([id]) => id)
    ));
    return questions.filter((q) => missedIds.has(q.id));
  }
  if (state.scope && state.scope !== "all") {
    return questions.filter((q) => slug(q.block) === state.scope);
  }
  return questions;
}

function shuffle(items) {
  for (let i = items.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [items[i], items[j]] = [items[j], items[i]];
  }
  return items;
}

function currentQuestion() {
  const session = getSession();
  const id = session.order[session.index];
  return questions.find((q) => q.id === id) || null;
}

function renderScopes() {
  const blocks = [...new Set(questions.map((q) => q.block))].sort((a, b) =>
    String(a).localeCompare(String(b), undefined, { numeric: true })
  );
  els.scope.innerHTML = `<option value="all">All questions</option>`;
  for (const block of blocks) {
    const option = document.createElement("option");
    option.value = slug(block);
    option.textContent = block;
    els.scope.appendChild(option);
  }
  const missed = document.createElement("option");
  missed.value = "missed";
  missed.textContent = "Missed questions";
  els.scope.appendChild(missed);
}

function render() {
  const session = getSession();
  const q = currentQuestion();
  els.scope.value = state.scope || "all";
  els.order.value = state.orderMode || "sequential";

  if (!q) {
    els.loading.hidden = false;
    els.loading.textContent = "No questions in this scope yet.";
    els.card.hidden = true;
    updateStats();
    return;
  }

  els.loading.hidden = true;
  els.card.hidden = false;
  els.position.textContent = `Question ${session.index + 1} of ${session.order.length}`;
  els.block.textContent = q.block;
  els.title.textContent = q.questionNumber ? `${q.block}, Question ${q.questionNumber}` : q.id;
  els.text.textContent = q.question_text || "";
  renderImages(q);
  renderChoices(q, session.answers[q.id]);
  renderFeedback(q, session.answers[q.id]);
  els.prev.disabled = session.index === 0;
  els.next.textContent = session.index >= session.order.length - 1 ? "Finish" : "Next";
  updateStats();
}

function setSettingsOpen(open) {
  els.settingsPanel.hidden = !open;
  els.settingsBackdrop.hidden = !open;
  els.settings.setAttribute("aria-expanded", String(open));
}

function renderImages(q) {
  els.images.innerHTML = "";
  for (const src of q.images) {
    const wrap = document.createElement("div");
    wrap.className = "image-wrap";
    const img = document.createElement("img");
    img.src = src;
    img.alt = `${q.id} image`;
    const link = document.createElement("a");
    link.href = src;
    link.target = "_blank";
    link.rel = "noopener";
    link.textContent = "Open image";
    wrap.append(img, link);
    els.images.appendChild(wrap);
  }
}

function choiceLetter(choice) {
  const match = String(choice || "").trim().match(/^([A-E])[\).\s]/i);
  return match ? match[1].toUpperCase() : null;
}

function renderChoices(q, answer) {
  els.choices.innerHTML = "";
  q.choices.forEach((choice) => {
    const letter = choiceLetter(choice);
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "choice";
    btn.textContent = choice;
    btn.disabled = Boolean(answer);
    if (answer) {
      if (letter === q.correct_answer) btn.classList.add("correct");
      if (letter === answer.selected && letter !== q.correct_answer) btn.classList.add("wrong");
    }
    btn.addEventListener("click", () => answerQuestion(q, letter));
    els.choices.appendChild(btn);
  });
}

function answerQuestion(q, selected) {
  const session = getSession();
  session.answers[q.id] = {
    selected,
    correct: selected === q.correct_answer,
    answeredAt: new Date().toISOString(),
  };
  saveState();
  render();
}

function renderFeedback(q, answer) {
  els.feedback.hidden = !answer;
  if (!answer) return;
  els.feedbackTitle.className = `feedback-title ${answer.correct ? "correct" : "wrong"}`;
  els.feedbackTitle.textContent = answer.correct
    ? `Correct: ${q.correct_answer}. ${q.correct_answer_text || ""}`
    : `Incorrect. Correct answer: ${q.correct_answer}. ${q.correct_answer_text || ""}`;
  els.explanation.textContent = q.explanation || "";
}

function updateStats() {
  const session = getSession();
  const answers = Object.values(session.answers || {});
  const answered = answers.length;
  const correct = answers.filter((a) => a.correct).length;
  const missed = answers.filter((a) => a.correct === false).length;
  els.answered.textContent = answered;
  els.correctPct.textContent = answered ? `${Math.round((correct / answered) * 100)}%` : "0%";
  els.missed.textContent = missed;
  els.remaining.textContent = Math.max(0, session.order.length - answered);
}

function move(delta) {
  const session = getSession();
  session.index = Math.min(Math.max(0, session.index + delta), Math.max(0, session.order.length - 1));
  saveState();
  render();
}

function fullText(q, selected) {
  return [
    `${q.block}${q.questionNumber ? `, Question ${q.questionNumber}` : ""}`,
    "",
    q.question_text || "",
    "",
    ...(q.choices || []),
    "",
    `Selected answer: ${selected}`,
    `Correct answer: ${q.correct_answer || ""}. ${q.correct_answer_text || ""}`,
    "",
    "Explanation:",
    q.explanation || "",
  ].join("\n");
}

async function copyText() {
  const q = currentQuestion();
  if (!q) return;
  const answer = getSession().answers[q.id];
  const selected = answer?.selected || "Not answered";
  await navigator.clipboard.writeText(fullText(q, selected));
}

function resetCurrentSession() {
  state.sessions ||= {};
  state.sessions[sessionKey()] = buildSession();
  saveState();
  render();
}

async function init() {
  try {
    const response = await fetch(DATA_URL, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    questions = (await response.json()).map(normalizeQuestion);
    questions.sort((a, b) =>
      String(a.block).localeCompare(String(b.block), undefined, { numeric: true }) ||
      (a.questionNumber || 0) - (b.questionNumber || 0) ||
      String(a.id).localeCompare(String(b.id))
    );
    state.scope ||= "all";
    state.orderMode ||= "sequential";
    renderScopes();
    render();
  } catch (error) {
    els.loading.textContent = `Could not load question data: ${error.message}`;
  }
}

els.scope.addEventListener("change", () => {
  state.scope = els.scope.value;
  saveState();
  render();
});
els.order.addEventListener("change", () => {
  state.orderMode = els.order.value;
  resetCurrentSession();
});
els.reset.addEventListener("click", resetCurrentSession);
els.prev.addEventListener("click", () => move(-1));
els.next.addEventListener("click", () => move(1));
els.copy.addEventListener("click", copyText);
els.settings.addEventListener("click", () => setSettingsOpen(els.settingsPanel.hidden));
els.closeSettings.addEventListener("click", () => setSettingsOpen(false));
els.settingsBackdrop.addEventListener("click", () => setSettingsOpen(false));

init();
