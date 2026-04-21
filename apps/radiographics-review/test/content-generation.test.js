const test = require("node:test");
const assert = require("node:assert/strict");

const { buildSummarySections } = require("../src/summarize");
const { buildAnkiNotes } = require("../src/notes");
const { buildArticlesIndex, buildReaderHtml } = require("../src/renderReader");

const mlmArticle = require("../articles/2026-05-01-10-1148-rg-250248-macrodystrophia-lipomatosis-macrodactyly/article.json");
const nbcaArticle = require("../articles/2026-05-01-10-1148-rg-250122-embolization-with-n-butyl-cyanoacrylate-properties-techniques-applicatio/article.json");

test("disease article summary stays concrete and study-oriented", () => {
  const sections = buildSummarySections(mlmArticle);
  const labels = sections.map((section) => section.label);
  const joined = sections.map((section) => section.text).join(" ");

  assert.deepEqual(labels, [
    "Core diagnosis",
    "Typical distribution",
    "Imaging hallmarks",
    "Management",
  ]);
  assert.doesNotMatch(joined, /\bnot yet been well established\b/i);
  assert.doesNotMatch(joined, /\bWhat it is\b/i);
  assert.ok(sections.every((section) => !/^Typically\b/.test(section.text)));
});

test("disease article notes avoid generic question stems", () => {
  const { notes } = buildAnkiNotes(mlmArticle, new Date("2026-04-21T12:00:00-05:00"));
  const contents = notes.map((note) => note.content).join("\n");
  const diagnosisCards = notes.filter((note) => /Most likely diagnosis\?/i.test(note.content || ""));

  assert.match(contents, /progressive form of \{\{c1::localized gigantism\}\}/i);
  assert.match(contents, /Macrodystrophia lipomatosa macrodactyly \(MLM\) is characterized by/i);
  assert.match(contents, /estimated birth prevalence .* \{\{c1::one in 100 000 live births\}\}/i);
  assert.match(contents, /Most likely diagnosis\?/i);
  assert.ok(diagnosisCards.length >= 2);
  assert.doesNotMatch(contents, /\bWhich .* pattern suggests\b/i);
  assert.doesNotMatch(contents, /\bkey teaching point\b/i);
});

test("technique article summary does not collapse into disease imaging cards", () => {
  const sections = buildSummarySections(nbcaArticle);
  const labels = sections.map((section) => section.label);

  assert.deepEqual(labels, [
    "Core concept",
    "How it works",
    "Clinical use",
    "Technical pearl",
    "Main risk",
  ]);
  assert.ok(!labels.includes("Imaging hallmarks"));
});

test("technique article notes capture mechanism and risk", () => {
  const { notes } = buildAnkiNotes(nbcaArticle, new Date("2026-04-21T12:00:00-05:00"));
  const contents = notes.map((note) => note.content).join("\n");

  assert.match(contents, /\{\{c1::liquid embolic agent\}\}/i);
  assert.match(contents, /rapidly polymerizes on contact with \{\{c1::ionic substances such as blood or saline\}\}/i);
  assert.match(contents, /flush the microcatheter before .*?<br><br>\{\{c1::5% dextrose\}\}/i);
  assert.match(contents, /major complication .* \{\{c1::nontarget embolization\}\}/i);
  assert.doesNotMatch(contents, /Most likely diagnosis\?/i);
});

test("reader and library navigation link back into the study library", () => {
  const readerHtml = buildReaderHtml(mlmArticle);
  const indexHtml = buildArticlesIndex([
    {
      ...mlmArticle,
      readerIndexPath: "articles/example/reader.html",
      thumbnailIndexPath: "articles/example/assets/figure-01.jpg",
      ankiIndexPath: "articles/example/anki/article.apkg",
    },
  ]);

  assert.match(readerHtml, /href="\.\.\/index\.html">RadioGraphics Digest<\/a>/i);
  assert.match(indexHtml, /class="title-link" href="articles\/example\/reader\.html">Macrodystrophia Lipomatosis Macrodactyly<\/a>/i);
});
