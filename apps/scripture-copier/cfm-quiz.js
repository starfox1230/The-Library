(() => {
  'use strict';
  const LEVELS = [
    ['kid', 'Kid'],
    ['high-school', 'High School'],
    ['expert', 'PhD / Expert'],
  ];
  const QUIZDUEL_URL = 'https://quiz-duel.lovable.app/';
  const element = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const shuffle = items => {
    const copy = [...items];
    for (let i = copy.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
  };

  function create(trigger) {
    const overlay = element('section', 'cfm-quiz');
    overlay.hidden = true;
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', 'Daily Come Follow Me quiz');
    const shell = element('div', 'cfm-quiz__shell');
    const top = element('div', 'cfm-quiz__top');
    top.append(element('span', 'cfm-quiz__brand', '✦ DAILY QUIZ'));
    const closeButton = element('button', 'cfm-quiz__close', '✕ Close');
    closeButton.type = 'button';
    top.append(closeButton);
    const content = element('main');
    shell.append(top, content);
    overlay.append(shell);
    document.body.append(overlay);
    let date = '', data = null, level = '', index = 0, score = 0, answered = false;
    let questionOrder = [], previousFocus = null, requestId = 0;

    function close() {
      if (overlay.hidden) return;
      overlay.hidden = true;
      document.body.style.overflow = '';
      content.replaceChildren();
      data = null;
      requestId++;
      (previousFocus?.isConnected ? previousFocus : trigger).focus();
    }
    function addHeading(eyebrow, heading, subtitle) {
      content.replaceChildren(element('p', 'cfm-quiz__eyebrow', eyebrow), element('h2', '', heading));
      if (subtitle) content.append(element('p', 'cfm-quiz__subtitle', subtitle));
    }
    function button(label, handler, className = 'cfm-quiz__level') {
      const node = element('button', className, label);
      node.type = 'button';
      node.addEventListener('click', handler);
      return node;
    }
    function showLevels() {
      addHeading(date, 'Choose your level');
      const list = element('div', 'cfm-quiz__levels');
      for (const [id, label] of LEVELS) {
        const row = element('div', 'cfm-quiz__level-row');
        const choice = button(label, () => start(id));
        choice.setAttribute('aria-label', label);
        const status = element('p', 'cfm-quiz__export-status');
        status.setAttribute('role', 'status');
        const copy = button('Copy JSON + QuizDuel ↗', () => exportLevel(id, label, copy, status), 'cfm-quiz__export');
        copy.setAttribute('aria-label', `Copy ${label} JSON and open QuizDuel`);
        row.append(choice, copy, status);
        list.append(row);
      }
      content.append(list);
      list.querySelector('button').focus();
    }
    function legacyCopy(text) {
      const previous = document.activeElement;
      const input = element('textarea', 'cfm-quiz__clipboard');
      input.value = text;
      input.setAttribute('aria-label', 'QuizDuel JSON');
      shell.append(input);
      try {
        input.focus();
        input.select();
        if (!document.execCommand('copy')) throw new Error('Clipboard unavailable');
      } finally {
        input.remove();
        previous?.focus();
      }
    }
    async function exportLevel(id, label, copy, status) {
      const quiz = data?.quizDuel?.[id];
      if (!quiz?.quizName || quiz.questions?.length !== 10) {
        status.textContent = 'This level’s QuizDuel export is unavailable. Please reload.';
        return;
      }
      copy.disabled = true;
      status.textContent = 'Copying…';
      let destination = null;
      try {
        const text = JSON.stringify(quiz, null, 2);
        // Start clipboard access and reserve a tab inside the click gesture.
        // Navigate only after copying succeeds, even when permission takes time.
        const copying = navigator.clipboard?.writeText
          ? navigator.clipboard.writeText(text)
          : Promise.resolve(legacyCopy(text));
        try {
          destination = window.open('about:blank', '_blank');
          if (destination) destination.opener = null;
        } catch { /* Offer a normal link if the browser blocks new tabs. */ }
        await copying;
        status.textContent = `${label} JSON copied. Paste it into QuizDuel to create a match.`;
        if (destination && !destination.closed) {
          destination.location.replace(QUIZDUEL_URL);
        } else {
          status.append(document.createTextNode(' Your browser blocked the new tab. '));
          const link = element('a', '', 'Open QuizDuel');
          link.href = QUIZDUEL_URL;
          link.target = '_blank';
          link.rel = 'noopener';
          status.append(link);
        }
      } catch {
        if (destination && !destination.closed) destination.close();
        status.textContent = 'Could not copy JSON. Allow clipboard access, then try again.';
      } finally {
        copy.disabled = false;
      }
    }
    function start(selectedLevel) {
      if (!data?.levels?.[selectedLevel] || data.levels[selectedLevel].length !== 10) return;
      level = selectedLevel;
      index = 0;
      score = 0;
      questionOrder = [...data.levels[level]];
      showQuestion();
    }
    function showQuestion() {
      answered = false;
      const q = questionOrder[index];
      addHeading(LEVELS.find(item => item[0] === level)[1], q.question);
      const progress = element('div', 'cfm-quiz__progress');
      const bar = element('span');
      bar.style.width = `${index * 10}%`;
      progress.append(bar);
      content.append(progress, element('p', 'cfm-quiz__counter', `Question ${index + 1} of 10 · ${score} correct`));
      const choices = element('div');
      for (const option of shuffle(q.options)) {
        const choice = button(option.text, () => answer(q, option.id, choices), 'cfm-quiz__choice');
        choice.dataset.optionId = option.id;
        choices.append(choice);
      }
      content.append(choices);
      choices.querySelector('button').focus();
    }
    function answer(q, id, choices) {
      if (answered) return;
      answered = true;
      const correct = id === q.correctOptionId;
      if (correct) score++;
      content.querySelector('.cfm-quiz__progress span').style.width = `${(index + 1) * 10}%`;
      for (const choice of choices.children) {
        choice.disabled = true;
        if (choice.dataset.optionId === q.correctOptionId) choice.classList.add('is-correct');
        else if (choice.dataset.optionId === id) choice.classList.add('is-wrong');
        else choice.classList.add('is-muted');
      }
      const feedback = element('div', 'cfm-quiz__feedback');
      feedback.setAttribute('role', 'status');
      feedback.append(element('strong', '', correct ? 'That’s it! ✦' : 'Good try — here’s the connection.'));
      feedback.append(element('p', '', q.explanation));
      const source = element('a', '', q.source.reference);
      source.href = q.source.url;
      source.target = '_blank';
      source.rel = 'noopener';
      feedback.append(source);
      const next = button(index === 9 ? 'See results →' : 'Next question →', () => {
        if (index === 9) showResults();
        else { index++; showQuestion(); }
      }, 'cfm-quiz__next');
      feedback.append(next);
      content.append(feedback);
      next.focus();
    }
    function showResults() {
      addHeading('Quiz complete', 'Nicely done!', `You finished the ${LEVELS.find(item => item[0] === level)[1]} quiz for ${date}.`);
      content.append(element('div', 'cfm-quiz__score', `${score} / 10`));
      const actions = element('div', 'cfm-quiz__actions');
      actions.append(button('Try another level', showLevels), button('Back to today’s reading', close));
      content.append(actions);
      actions.querySelector('button').focus();
    }
    function showError(message) {
      addHeading(date, 'Quiz unavailable');
      content.append(element('p', 'cfm-quiz__error', message));
      content.append(button('Back to reading', close));
      content.querySelector('button').focus();
    }
    async function open() {
      if (!overlay.hidden || !date) return;
      previousFocus = document.activeElement;
      overlay.hidden = false;
      document.body.style.overflow = 'hidden';
      addHeading(date, 'Loading your quiz…');
      closeButton.focus();
      const thisRequest = ++requestId;
      try {
        const response = await fetch(`quizzes/${date}.json?v=quality-20261007`, { cache: 'no-cache' });
        if (!response.ok) throw new Error('No quiz has been published for this date yet.');
        const loaded = await response.json();
        if (overlay.hidden || thisRequest !== requestId) return;
        if (loaded.date !== date || LEVELS.some(([id]) => loaded.levels?.[id]?.length !== 10)) throw new Error('This quiz could not be loaded.');
        data = loaded;
        showLevels();
      } catch (error) {
        if (!overlay.hidden && thisRequest === requestId) showError(error.message || 'Please try again later.');
      }
    }
    trigger.addEventListener('click', open);
    closeButton.addEventListener('click', close);
    overlay.addEventListener('keydown', event => {
      if (event.key === 'Escape') { event.preventDefault(); close(); }
      if (event.key !== 'Tab') return;
      const focusable = [...overlay.querySelectorAll('button:not(:disabled), a[href], textarea')];
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    });
    return { setDate(nextDate, isDay) { date = nextDate; trigger.hidden = !isDay; } };
  }
  window.CFMQuiz = { create };
})();
