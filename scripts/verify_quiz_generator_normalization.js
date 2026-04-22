const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const quizUtils = require(path.join(__dirname, '..', 'apps', 'quiz-generator', 'quiz-session-utils.js'));

const fixturePath = path.join(__dirname, '..', 'apps', 'quiz-generator', 'ct-pattern-recognition-quiz.json');
const validFixtureText = fs.readFileSync(fixturePath, 'utf8');

function createDeterministicRandom(seed) {
    let state = seed >>> 0;

    return function random() {
        state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
        return state / 0x100000000;
    };
}

function loadFixtureObject() {
    return JSON.parse(validFixtureText);
}

function getCorrectAnswerIndexes(sessionData) {
    return sessionData.questions.map(question => question.options.indexOf(question.correctAnswer));
}

function assertIndexesVaried(indexes, label) {
    assert.ok(indexes.every(index => index >= 0 && index < 4), `${label}: every correct answer should remain within the four answer slots`);
    assert.ok(new Set(indexes).size > 1, `${label}: correct answer positions should vary after normalization`);
}

function testMalformedPasteAutoRepair() {
    const malformedText = validFixtureText.replace('\\"moth-eaten\\"', '"moth-eaten"');
    const parseResult = quizUtils.parseAndNormalizeQuizSession(malformedText, { randomFn: createDeterministicRandom(11) });

    assert.ok(parseResult, 'auto-repair should recover the malformed quiz JSON');
    assert.equal(parseResult.repairStep, 'inner quote escaping', 'the malformed quote case should be repaired by the inner quote heuristic');
    assert.equal(parseResult.normalizedData.questions.length, 15, 'the repaired sample should still contain 15 questions');
    assert.ok(getCorrectAnswerIndexes(parseResult.normalizedData).every(index => index !== 0), 'the repaired sample should not leave any correct answers in slot A');
}

function testSingleUploadNormalization() {
    const normalizedSession = quizUtils.normalizeQuizSessionData(loadFixtureObject(), { randomFn: createDeterministicRandom(29) });
    const indexes = getCorrectAnswerIndexes(normalizedSession);

    assertIndexesVaried(indexes, 'single upload normalization');
}

function testMergeNormalization() {
    const firstSession = loadFixtureObject();
    const secondSession = loadFixtureObject();
    secondSession.title = 'Foundations of CT Pattern Recognition Copy';

    const mergedSessions = [
        quizUtils.normalizeQuizSessionData(firstSession, { randomFn: createDeterministicRandom(41) }),
        quizUtils.normalizeQuizSessionData(secondSession, { randomFn: createDeterministicRandom(53) })
    ];

    assert.equal(mergedSessions.length, 2, 'merge normalization should keep both sessions');
    mergedSessions.forEach((sessionData, index) => {
        assertIndexesVaried(getCorrectAnswerIndexes(sessionData), `merge normalization session ${index + 1}`);
    });
}

function testInvalidCorrectAnswerRejected() {
    const invalidSession = loadFixtureObject();
    invalidSession.questions[2].correctAnswer = 'Not one of the listed options';

    assert.throws(
        () => quizUtils.normalizeQuizSessionData(invalidSession),
        /Question 3 "correctAnswer" must exactly match one entry in "options"\./,
        'invalid correct answers should fail with the offending question number'
    );
}

function testNormalizationDoesNotMutateStoredSessions() {
    const originalSession = loadFixtureObject();
    const originalSnapshot = JSON.stringify(originalSession);

    quizUtils.normalizeQuizSessionData(originalSession, { randomFn: createDeterministicRandom(67) });

    assert.equal(JSON.stringify(originalSession), originalSnapshot, 'normalization should not mutate the stored session object in place');
}

try {
    testMalformedPasteAutoRepair();
    testSingleUploadNormalization();
    testMergeNormalization();
    testInvalidCorrectAnswerRejected();
    testNormalizationDoesNotMutateStoredSessions();
    console.log('Quiz generator normalization checks passed.');
} catch (error) {
    console.error('Quiz generator normalization checks failed.');
    console.error(error.stack || error.message);
    process.exit(1);
}
