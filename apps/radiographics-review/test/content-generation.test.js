const test = require("node:test");
const assert = require("node:assert/strict");

const { buildSummarySections, buildTeachingPoint } = require("../src/summarize");
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
  const imageCards = notes.filter((note) => /<img src=/i.test(note.content || ""));

  assert.match(contents, /progressive form of \{\{c1::localized gigantism\}\}/i);
  assert.match(contents, /Macrodystrophia lipomatosa macrodactyly \(MLM\) is characterized by/i);
  assert.match(contents, /estimated birth prevalence .* \{\{c1::one in 100 000 live births\}\}/i);
  assert.match(contents, /proposed molecular cause .* \{\{c1::somatic activating PIK3CA mutations\}\}/i);
  assert.match(contents, /Most likely diagnosis\?/i);
  assert.ok(diagnosisCards.length >= 2);
  assert.ok(imageCards.length >= 4);
  assert.match(contents, /what (?:do|does) the .*arrow/i);
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
  const imageCards = notes.filter((note) => /<img src=/i.test(note.content || ""));

  assert.match(contents, /\{\{c1::liquid embolic agent\}\}/i);
  assert.match(contents, /rapidly polymerizes on contact with \{\{c1::ionic substances such as blood or saline\}\}/i);
  assert.match(contents, /flush the microcatheter before .*?<br><br>\{\{c1::5% dextrose\}\}/i);
  assert.match(contents, /major complication .* \{\{c1::nontarget embolization\}\}/i);
  assert.ok(imageCards.length >= 10);
  assert.match(contents, /what does the arrow indicate on this image\?<br><br>\{\{c1::Contrast medium leakage in the uterine cavity\}\}/i);
  assert.match(contents, /what does the solid arrow indicate on this CT\?<br><br>\{\{c1::Duodenal varix\}\}/i);
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

  assert.match(readerHtml, /document\.createElement\("base"\)/i);
  assert.match(readerHtml, /href="\.\.\/\.\.\/index\.html">RadioGraphics Digest<\/a>/i);
  assert.match(indexHtml, /document\.createElement\("base"\)/i);
  assert.match(indexHtml, /class="title-link" href="articles\/example\/reader\.html">Macrodystrophia Lipomatosis Macrodactyly<\/a>/i);
});

test("figure teaching point ignores not-shown and movie-only sentences", () => {
  const teachingPoint = buildTeachingPoint(
    "Figure 23. Septic arthritis of the right hip in a 62-year-old woman. CT (not shown) showed a pseudoaneurysm within the iliacus muscle. Right internal iliac angiogram shows a large pseudoaneurysm (arrow) supplied by a bleeding branch (arrowhead). Movie 18 illustrates intermittent visualization of the culprit vessel of a large pseudoaneurysm at angiography.",
  );

  assert.equal(
    teachingPoint,
    "Right internal iliac angiogram shows a large pseudoaneurysm (arrow) supplied by a bleeding branch (arrowhead).",
  );
});

test("figure teaching point can combine visible panels while excluding movie references", () => {
  const teachingPoint = buildTeachingPoint(
    "Figure 6. Hemoptysis in a 76-year-old man. Chest CT (not shown) revealed bronchiectasis and a fibrotic lesion in the left upper lobe of the lung. (A) Bronchial angiogram shows mild hypertrophy of the left bronchial artery and opacification of a peripheral pulmonary artery (arrow). (B) Spot image after glue embolization of the left bronchial artery shows a glue cast in the left bronchial artery (arrowheads). Note the small glue cast (arrow) at the point of the shunt between the bronchial artery and pulmonary artery. Movie 5 shows glue embolization performed to treat an entangled vascular structure.",
  );

  assert.doesNotMatch(teachingPoint, /\bnot shown\b/i);
  assert.doesNotMatch(teachingPoint, /\bmovie\b/i);
  assert.match(teachingPoint, /\bBronchial angiogram shows mild hypertrophy\b/i);
  assert.match(teachingPoint, /\bSpot image after glue embolization\b/i);
});

test("reader lightbox includes close control and scrollable overlay", () => {
  const readerHtml = buildReaderHtml(mlmArticle);

  assert.match(readerHtml, /data-lightbox-close/i);
  assert.match(readerHtml, /\.lightbox\s*\{[\s\S]*overflow-y:\s*auto;/i);
  assert.match(readerHtml, /\.lightbox-close\s*\{[\s\S]*position:\s*fixed;/i);
});
