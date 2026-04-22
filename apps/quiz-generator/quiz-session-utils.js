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

    return {
        EXPECTED_OPTION_COUNT,
        normalizeSmartJsonCharacters,
        escapeLikelyInnerQuotes,
        parseQuizJsonWithAutoRepair,
        shuffleArray,
        shuffleOptionsAvoidingOriginalCorrectSlot,
        normalizeQuizSessionData,
        parseAndNormalizeQuizSession
    };
}));
