(function (root, factory) {
    const api = factory();

    if (typeof module === 'object' && module.exports) {
        module.exports = api;
    }

    if (root) {
        root.QuizSessionUtils = api;
    }
}(typeof globalThis !== 'undefined' ? globalThis : this, function () {
    const EXPECTED_OPTION_COUNT = 4;

    function normalizeSmartJsonCharacters(rawText) {
        return rawText
            .replace(/[\u201C\u201D]/g, '"')
            .replace(/[\u2018\u2019]/g, "'")
            .replace(/\u2013/g, '-')
            .replace(/\u2014/g, '-');
    }

    function escapeLikelyInnerQuotes(jsonText) {
        let output = '';
        let inString = false;
        let escaped = false;

        for (let i = 0; i < jsonText.length; i += 1) {
            const char = jsonText[i];

            if (!inString) {
                if (char === '"') inString = true;
                output += char;
                continue;
            }

            if (escaped) {
                output += char;
                escaped = false;
                continue;
            }

            if (char === '\\') {
                output += char;
                escaped = true;
                continue;
            }

            if (char === '"') {
                let j = i + 1;
                while (j < jsonText.length && /\s/.test(jsonText[j])) j += 1;
                const nextChar = jsonText[j];
                const isLikelyClosingQuote = nextChar === ',' || nextChar === '}' || nextChar === ']' || nextChar === ':';

                if (isLikelyClosingQuote) {
                    inString = false;
                    output += char;
                } else {
                    output += '\\"';
                }
                continue;
            }

            output += char;
        }

        return output;
    }

    function parseQuizJsonWithAutoRepair(rawInput) {
        if (typeof rawInput !== 'string') {
            return null;
        }

        const attempts = [
            { text: rawInput, label: 'original input' },
            { text: normalizeSmartJsonCharacters(rawInput), label: 'smart quote normalization' }
        ];

        attempts.push({
            text: escapeLikelyInnerQuotes(attempts[1].text),
            label: 'inner quote escaping'
        });

        for (const attempt of attempts) {
            try {
                return {
                    parsedData: JSON.parse(attempt.text),
                    normalizedText: attempt.text,
                    repaired: attempt.label !== 'original input',
                    repairStep: attempt.label
                };
            } catch (_) {
                // Try next repair attempt.
            }
        }

        return null;
    }

    function shuffleArray(items, randomFn) {
        const rng = typeof randomFn === 'function' ? randomFn : Math.random;
        const shuffled = [...items];

        for (let i = shuffled.length - 1; i > 0; i -= 1) {
            const swapIndex = Math.floor(rng() * (i + 1));
            [shuffled[i], shuffled[swapIndex]] = [shuffled[swapIndex], shuffled[i]];
        }

        return shuffled;
    }

    function shuffleOptionsAvoidingOriginalCorrectSlot(options, correctAnswer, randomFn) {
        const originalOptions = Array.isArray(options) ? [...options] : [];
        const originalCorrectIndex = originalOptions.indexOf(correctAnswer);

        if (originalOptions.length < 2 || originalCorrectIndex === -1) {
            return originalOptions;
        }

        let shuffledOptions = shuffleArray(originalOptions, randomFn);
        let attemptsRemaining = 10;

        while (shuffledOptions.indexOf(correctAnswer) === originalCorrectIndex && attemptsRemaining > 0) {
            shuffledOptions = shuffleArray(originalOptions, randomFn);
            attemptsRemaining -= 1;
        }

        if (shuffledOptions.indexOf(correctAnswer) === originalCorrectIndex) {
            const swapIndex = originalCorrectIndex === 0 ? 1 : 0;
            [shuffledOptions[originalCorrectIndex], shuffledOptions[swapIndex]] = [shuffledOptions[swapIndex], shuffledOptions[originalCorrectIndex]];
        }

        return shuffledOptions;
    }

    function assertNonEmptyString(value, message) {
        if (typeof value !== 'string' || value.trim() === '') {
            throw new Error(message);
        }

        return value;
    }

    function normalizeQuizQuestion(question, index, randomFn) {
        const questionNumber = index + 1;

        if (!question || typeof question !== 'object' || Array.isArray(question)) {
            throw new Error(`Question ${questionNumber} must be an object.`);
        }

        assertNonEmptyString(question.question, `Question ${questionNumber} is missing a valid "question" string.`);

        if (!Array.isArray(question.options)) {
            throw new Error(`Question ${questionNumber} must include an "options" array.`);
        }

        if (question.options.length !== EXPECTED_OPTION_COUNT) {
            throw new Error(`Question ${questionNumber} must have exactly ${EXPECTED_OPTION_COUNT} answer options.`);
        }

        const options = question.options.map((option, optionIndex) => {
            if (typeof option !== 'string' || option.trim() === '') {
                throw new Error(`Question ${questionNumber} option ${optionIndex + 1} must be a non-empty string.`);
            }

            return option;
        });

        if (new Set(options).size !== options.length) {
            throw new Error(`Question ${questionNumber} answer options must be distinct strings.`);
        }

        const correctAnswer = assertNonEmptyString(question.correctAnswer, `Question ${questionNumber} is missing a valid "correctAnswer" string.`);

        if (options.filter(option => option === correctAnswer).length !== 1) {
            throw new Error(`Question ${questionNumber} "correctAnswer" must exactly match one entry in "options".`);
        }

        return {
            ...question,
            options: shuffleOptionsAvoidingOriginalCorrectSlot(options, correctAnswer, randomFn),
            explanation: typeof question.explanation === 'string' ? question.explanation : ''
        };
    }

    function normalizeQuizSessionData(sessionData, options) {
        const settings = options || {};
        const randomFn = settings.randomFn;

        if (!sessionData || typeof sessionData !== 'object' || Array.isArray(sessionData)) {
            throw new Error('Quiz data must be a JSON object.');
        }

        const title = assertNonEmptyString(sessionData.title, 'The JSON object is missing a valid "title" string property.');

        if (!Array.isArray(sessionData.questions) || sessionData.questions.length === 0) {
            throw new Error('The JSON object must have a "questions" property that is an array with at least one question object.');
        }

        return {
            ...sessionData,
            title,
            questions: sessionData.questions.map((question, index) => normalizeQuizQuestion(question, index, randomFn))
        };
    }

    function parseAndNormalizeQuizSession(rawInput, options) {
        const parseResult = parseQuizJsonWithAutoRepair(rawInput);

        if (!parseResult) {
            return null;
        }

        return {
            ...parseResult,
            normalizedData: normalizeQuizSessionData(parseResult.parsedData, options)
        };
    }

    function initializeKeyPointHighlighting() {
        if (typeof document === 'undefined' || typeof window === 'undefined' || window.__quizKeyPointHighlightingInitialized) {
            return;
        }
        window.__quizKeyPointHighlightingInitialized = true;

        const STORAGE_PREFIX = 'quizKeyPointHighlights:';
        const HIGHLIGHT_CLASS = 'key-point-highlight';
        const PANEL_ID = 'key-point-highlight-panel';
        const SAVE_BUTTON_ID = 'save-key-point-highlight-btn';
        const CLEAR_BUTTON_ID = 'clear-key-point-highlight-btn';
        const INPUT_ID = 'key-point-highlight-input';
        const LIST_ID = 'key-point-highlight-list';
        let lastSelectedKeyPoint = '';
        let lastPanelQuestionIndex = -1;

        const getElement = id => document.getElementById(id);
        const escapeHtml = value => String(value || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
        const getActiveTitle = () => sessionStorage.getItem('loadQuizTitle') || document.title || '';
        const getCurrentQuestionIndex = () => {
            const match = (getElement('question-counter')?.textContent || '').match(/Question\s+(\d+)\s+of/i);
            return match ? Number(match[1]) - 1 : -1;
        };
        const getStorageKey = () => getActiveTitle() ? `${STORAGE_PREFIX}${getActiveTitle()}` : '';

        function readHighlightMap() {
            const key = getStorageKey();
            if (!key) return {};

            try {
                const parsed = JSON.parse(localStorage.getItem(key) || '{}');
                return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : {};
            } catch (_) {
                return {};
            }
        }

        function writeHighlightMap(map) {
            const key = getStorageKey();
            if (key) localStorage.setItem(key, JSON.stringify(map));
        }

        function getCurrentHighlights() {
            const highlights = readHighlightMap()[getCurrentQuestionIndex()];
            return Array.isArray(highlights) ? highlights : [];
        }

        function setCurrentHighlights(items) {
            const questionIndex = getCurrentQuestionIndex();
            if (questionIndex < 0) return;

            const cleaned = Array.from(new Set(
                items
                    .map(item => String(item || '').replace(/\s+/g, ' ').trim())
                    .filter(Boolean)
            ));
            const map = readHighlightMap();

            if (cleaned.length) map[questionIndex] = cleaned;
            else delete map[questionIndex];

            writeHighlightMap(map);
        }

        function getSelectionTextFromExplanation() {
            const explanationElement = getElement('explanation');
            const selection = window.getSelection ? window.getSelection() : null;

            if (!explanationElement || !selection || selection.rangeCount === 0 || selection.isCollapsed) {
                return '';
            }

            for (let i = 0; i < selection.rangeCount; i += 1) {
                if (explanationElement.contains(selection.getRangeAt(i).commonAncestorContainer)) {
                    return selection.toString().replace(/\s+/g, ' ').trim();
                }
            }

            return '';
        }

        function captureSelectionForMobile() {
            const selectedText = getSelectionTextFromExplanation();
            if (!selectedText) return;

            lastSelectedKeyPoint = selectedText;
            const input = getElement(INPUT_ID);
            if (input && document.activeElement !== input) {
                input.value = selectedText;
            }
        }

        function clearHighlightMarks(container) {
            container.querySelectorAll(`mark.${HIGHLIGHT_CLASS}`).forEach(mark => {
                mark.replaceWith(document.createTextNode(mark.textContent));
            });
            container.normalize();
        }

        function wrapFirstMatchingTextNode(textNode, snippet) {
            const text = textNode.nodeValue;
            const matchIndex = text.toLowerCase().indexOf(snippet.toLowerCase());
            if (matchIndex < 0) return;

            const fragment = document.createDocumentFragment();
            const mark = document.createElement('mark');
            mark.className = HIGHLIGHT_CLASS;
            mark.textContent = text.slice(matchIndex, matchIndex + snippet.length);

            if (matchIndex) fragment.appendChild(document.createTextNode(text.slice(0, matchIndex)));
            fragment.appendChild(mark);
            if (matchIndex + snippet.length < text.length) {
                fragment.appendChild(document.createTextNode(text.slice(matchIndex + snippet.length)));
            }

            textNode.parentNode.replaceChild(fragment, textNode);
        }

        function applyHighlightMarks() {
            const explanationElement = getElement('explanation');
            if (!explanationElement || explanationElement.dataset.keyPointDecorating === 'true') return;

            const highlights = getCurrentHighlights();
            const signature = JSON.stringify({ questionIndex: getCurrentQuestionIndex(), highlights });
            const existingMarks = explanationElement.querySelectorAll(`mark.${HIGHLIGHT_CLASS}`).length;

            if (
                explanationElement.dataset.keyPointSignature === signature
                && ((highlights.length === 0 && existingMarks === 0) || existingMarks > 0)
            ) {
                return;
            }

            explanationElement.dataset.keyPointDecorating = 'true';
            clearHighlightMarks(explanationElement);

            highlights.forEach(snippet => {
                const walker = document.createTreeWalker(
                    explanationElement,
                    NodeFilter.SHOW_TEXT,
                    {
                        acceptNode(node) {
                            const parent = node.parentElement;
                            if (!parent || parent.tagName === 'STRONG' || parent.closest(`#${PANEL_ID}`)) {
                                return NodeFilter.FILTER_REJECT;
                            }
                            return node.nodeValue.toLowerCase().includes(snippet.toLowerCase())
                                ? NodeFilter.FILTER_ACCEPT
                                : NodeFilter.FILTER_REJECT;
                        }
                    }
                );

                const matchingNode = walker.nextNode();
                if (matchingNode) wrapFirstMatchingTextNode(matchingNode, snippet);
            });

            explanationElement.dataset.keyPointSignature = signature;
            explanationElement.dataset.keyPointDecorating = 'false';
        }

        function renderHighlightList() {
            const list = getElement(LIST_ID);
            if (!list) return;

            const highlights = getCurrentHighlights();
            list.innerHTML = highlights.length
                ? highlights.map(item => `<div class="key-point-item"><span class="key-point-label">Key Point to Test:</span> ${escapeHtml(item)}</div>`).join('')
                : '<div class="key-point-empty">No key point marked yet.</div>';
        }

        function resetDraftIfQuestionChanged() {
            const questionIndex = getCurrentQuestionIndex();
            if (questionIndex === lastPanelQuestionIndex) return;

            lastPanelQuestionIndex = questionIndex;
            lastSelectedKeyPoint = '';
            const input = getElement(INPUT_ID);
            if (input) input.value = '';
        }

        function syncHighlightPanel() {
            const explanationElement = getElement('explanation');
            if (!explanationElement) return;

            let panel = getElement(PANEL_ID);
            if (!panel) {
                panel = document.createElement('div');
                panel.id = PANEL_ID;
                panel.innerHTML = `
                    <div class="key-point-help">Highlight explanation text, or type the exact key point below.</div>
                    <textarea id="${INPUT_ID}" class="key-point-input" placeholder="Key point to test..."></textarea>
                    <div class="key-point-controls">
                        <button id="${SAVE_BUTTON_ID}" type="button">Save Key Point</button>
                        <button id="${CLEAR_BUTTON_ID}" type="button">Clear Key Point</button>
                    </div>
                    <div id="${LIST_ID}" class="key-point-list"></div>`;
                explanationElement.insertAdjacentElement('afterend', panel);

                getElement(SAVE_BUTTON_ID).addEventListener('click', () => {
                    const input = getElement(INPUT_ID);
                    const selectedText = getSelectionTextFromExplanation() || lastSelectedKeyPoint;
                    const typedText = input ? input.value : '';
                    const textToSave = (selectedText || typedText || '').replace(/\s+/g, ' ').trim();

                    if (!textToSave) {
                        alert('Highlight text inside the explanation or type the key point first.');
                        return;
                    }

                    setCurrentHighlights([...getCurrentHighlights(), textToSave]);
                    lastSelectedKeyPoint = '';
                    if (input) input.value = '';
                    window.getSelection()?.removeAllRanges();
                    explanationElement.dataset.keyPointSignature = '';
                    applyHighlightMarks();
                    renderHighlightList();
                });

                getElement(CLEAR_BUTTON_ID).addEventListener('click', () => {
                    setCurrentHighlights([]);
                    lastSelectedKeyPoint = '';
                    const input = getElement(INPUT_ID);
                    if (input) input.value = '';
                    explanationElement.dataset.keyPointSignature = '';
                    applyHighlightMarks();
                    renderHighlightList();
                });
            }

            resetDraftIfQuestionChanged();
            panel.style.display = explanationElement.style.display === 'none' ? 'none' : 'block';
            applyHighlightMarks();
            renderHighlightList();
        }

        function getPastSessionByTitle(sessionTitle) {
            try {
                const sessions = JSON.parse(localStorage.getItem('pastQuizSessions') || '[]');
                return Array.isArray(sessions) ? sessions.find(session => session && session.title === sessionTitle) : null;
            } catch (_) {
                return null;
            }
        }

        function getProgressForTitle(sessionTitle) {
            try {
                return JSON.parse(localStorage.getItem(`quizProgress:${sessionTitle}`) || '{}') || {};
            } catch (_) {
                return {};
            }
        }

        function getActiveFilter() {
            return document.querySelector('.filter-btn[data-filter].active')?.dataset.filter || 'all';
        }

        function isPreviewMode() {
            const backButton = getElement('back-to-quiz-btn');
            return Boolean(backButton && backButton.style.display !== 'none');
        }

        function buildReviewCopyText() {
            const sessionTitle = getActiveTitle();
            const session = getPastSessionByTitle(sessionTitle);
            if (!session || !Array.isArray(session.questions)) return '';

            const progress = getProgressForTitle(sessionTitle);
            const answers = Array.isArray(progress.userAnswers) ? progress.userAnswers : [];
            const favorites = new Set(Array.isArray(progress.favoriteQuestions) ? progress.favoriteQuestions : []);
            const highlightMap = readHighlightMap();
            const filter = getActiveFilter();
            const preview = isPreviewMode();
            let textToCopy = `Quiz Review: ${sessionTitle}\nFilter: ${filter.toUpperCase()}\n\n`;
            let count = 0;

            session.questions.forEach((question, index) => {
                const userAnswer = answers[index] || null;
                const isCorrect = Boolean(userAnswer && userAnswer.isCorrect);
                const isAnswered = userAnswer !== null;
                const isFavorite = favorites.has(index);

                if (preview && !isAnswered) return;
                if (filter === 'correct' && !isCorrect) return;
                if (filter === 'incorrect' && (isCorrect || !isAnswered)) return;
                if (filter === 'favorites' && !isFavorite) return;

                count += 1;
                textToCopy += `Q${index + 1}: ${question.question}${isFavorite ? ' ★' : ''}\n`;
                textToCopy += `Your Answer: ${userAnswer ? userAnswer.selected : 'Skipped'} (${isCorrect ? 'Correct' : 'Incorrect'})\n`;
                if (!isCorrect) textToCopy += `Correct Answer: ${question.correctAnswer}\n`;
                textToCopy += `Explanation: ${question.explanation || ''}\n`;

                const highlights = Array.isArray(highlightMap[index]) ? highlightMap[index] : [];
                if (highlights.length) {
                    textToCopy += `Key Point to Test: ${highlights.join(' | ')}\n`;
                }

                textToCopy += '----------------------------------------\n\n';
            });

            return count ? textToCopy : `${textToCopy}No questions match this filter.`;
        }

        function interceptReviewCopy(event) {
            const button = event.target.closest('#copy-review-btn');
            if (!button) return;

            const textToCopy = buildReviewCopyText();
            if (!textToCopy) return;

            event.preventDefault();
            event.stopImmediatePropagation();

            navigator.clipboard.writeText(textToCopy).then(() => {
                const originalText = button.textContent;
                button.textContent = 'Copied!';
                setTimeout(() => {
                    button.textContent = originalText;
                }, 1500);
            }).catch(error => {
                console.error('Failed to copy review with key points:', error);
                alert('Failed to copy review. Please try again.');
            });
        }

        function annotateReviewCards() {
            const reviewList = getElement('review-list');
            if (!reviewList) return;

            const highlightMap = readHighlightMap();
            reviewList.querySelectorAll('.review-card').forEach((card, visibleIndex) => {
                const match = (card.querySelector('.review-q')?.textContent || '').match(/^\s*(\d+)\./);
                const questionIndex = match ? Number(match[1]) - 1 : visibleIndex;
                const highlights = Array.isArray(highlightMap[questionIndex]) ? highlightMap[questionIndex] : [];
                const joinedHighlights = highlights.join(' | ');
                let row = card.querySelector('.review-key-point');

                if (!joinedHighlights) {
                    if (row) row.remove();
                    return;
                }

                if (row && row.dataset.value === joinedHighlights) return;
                if (!row) {
                    row = document.createElement('div');
                    row.className = 'review-key-point';
                    card.appendChild(row);
                }

                row.dataset.value = joinedHighlights;
                row.innerHTML = `<span class="key-point-label">Key Point to Test:</span> ${escapeHtml(joinedHighlights)}`;
            });
        }

        function addStyles() {
            const style = document.createElement('style');
            style.textContent = `
                .${HIGHLIGHT_CLASS} {
                    background: rgba(255, 210, 90, 0.35);
                    color: #fff;
                    border-radius: 3px;
                    padding: 0 2px;
                }
                #${PANEL_ID} {
                    background-color: #202035;
                    border: 1px solid #4a4a7e;
                    border-radius: 8px;
                    color: var(--font-color, #c0c0fa);
                    display: none;
                    font-size: 0.9em;
                    line-height: 1.45;
                    margin-top: 10px;
                    padding: 12px;
                    text-align: left;
                }
                .key-point-help {
                    margin-bottom: 8px;
                }
                .key-point-input {
                    background-color: #12121f;
                    border: 1px solid #4a4a7e;
                    border-radius: 8px;
                    box-sizing: border-box;
                    color: #f0f0ff;
                    font-family: "Roboto", sans-serif;
                    font-size: 1em;
                    margin: 0 0 10px;
                    min-height: 64px;
                    padding: 10px;
                    resize: vertical;
                    width: 100%;
                }
                .key-point-controls {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                    margin-bottom: 8px;
                }
                .key-point-controls button {
                    background: none;
                    border: 1px solid #4a4af5;
                    border-radius: 16px;
                    color: var(--bright-blue, #8a8aff);
                    cursor: pointer;
                    padding: 8px 12px;
                    touch-action: manipulation;
                }
                .key-point-controls button:hover {
                    background-color: #4a4af5;
                    color: #fff;
                }
                .key-point-item,
                .review-key-point {
                    border-top: 1px solid #3a3a5e;
                    color: #f0e6a0;
                    margin-top: 8px;
                    padding-top: 8px;
                }
                .key-point-empty {
                    opacity: 0.75;
                }
                .key-point-label {
                    color: #ffd25a;
                    font-weight: 700;
                }
            `;
            document.head.appendChild(style);
        }

        function setup() {
            addStyles();
            const explanationElement = getElement('explanation');
            const reviewList = getElement('review-list');

            document.addEventListener('selectionchange', captureSelectionForMobile);

            if (explanationElement) {
                new MutationObserver(() => window.requestAnimationFrame(syncHighlightPanel)).observe(
                    explanationElement,
                    { attributes: true, attributeFilter: ['style'], childList: true, subtree: true }
                );
            }

            if (reviewList) {
                new MutationObserver(() => window.requestAnimationFrame(annotateReviewCards)).observe(
                    reviewList,
                    { childList: true, subtree: true }
                );
            }

            syncHighlightPanel();
            annotateReviewCards();
            document.addEventListener('click', interceptReviewCopy, true);
        }

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', setup, { once: true });
        } else {
            setup();
        }
    }

    initializeKeyPointHighlighting();

    return {
        EXPECTED_OPTION_COUNT,
        normalizeSmartJsonCharacters,
        escapeLikelyInnerQuotes,
        parseQuizJsonWithAutoRepair,
        shuffleArray,
        shuffleOptionsAvoidingOriginalCorrectSlot,
        normalizeQuizSessionData,
        parseAndNormalizeQuizSession,
        initializeKeyPointHighlighting
    };
}));
