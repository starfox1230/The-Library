const test = require("node:test");
const assert = require("node:assert/strict");

const { buildSummarySections, buildTeachingPoint } = require("../src/summarize");
const { buildAnkiNotes } = require("../src/notes");
const { buildArticlesIndex, buildReaderHtml } = require("../src/renderReader");
const { cleanProseBlock } = require("../src/studyText");

const mlmArticle = require("../articles/2026-05-01-10-1148-rg-250248-macrodystrophia-lipomatosis-macrodactyly/article.json");
const nbcaArticle = require("../articles/2026-05-01-10-1148-rg-250122-embolization-with-n-butyl-cyanoacrylate-properties-techniques-applicatio/article.json");
const ceusArticle = require("../articles/2023-02-01-10-1148-rg-220093-artifacts-and-technical-considerations-at-contrast-enhanced-us/article.json");

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
  assert.match(indexHtml, /articles\\\/index\\\.html\$\//i);
  assert.match(indexHtml, /class="title-link" href="articles\/example\/reader\.html">Macrodystrophia Lipomatosis Macrodactyly<\/a>/i);
});

test("library index can sort by date added or published", () => {
  const indexHtml = buildArticlesIndex([
    {
      ...mlmArticle,
      generatedAt: "2026-04-21T14:08:52.848Z",
      readerIndexPath: "articles/example/reader.html",
      thumbnailIndexPath: "articles/example/assets/figure-01.jpg",
      ankiIndexPath: "articles/example/anki/article.apkg",
    },
  ]);

  assert.match(indexHtml, /data-sort-value="added" aria-pressed="true">Date Added<\/button>/i);
  assert.match(indexHtml, /data-sort-value="published" aria-pressed="false">Date Published<\/button>/i);
  assert.match(indexHtml, /localStorage\.getItem\(storageKey\)/i);
  assert.match(indexHtml, /data-date-added="\d+"/i);
  assert.match(indexHtml, /data-date-published="\d+"/i);
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

test("reader figure images remain real links with lightbox enhancement", () => {
  const readerHtml = buildReaderHtml(mlmArticle);

  assert.match(readerHtml, /<a\s+class="image-launch hero-image-button"\s+href="assets\/figure-01\.jpg"/i);
  assert.match(readerHtml, /document\.querySelectorAll\("\.image-launch\[href\]"\)/i);
  assert.match(readerHtml, /event\.preventDefault\(\);[\s\S]*openLightbox\(trigger\)/i);
  assert.doesNotMatch(readerHtml, /<button\s+class="image-launch/i);
  assert.doesNotMatch(readerHtml, /data-lightbox-src/i);
});

test("plain-text comparison thresholds survive study text cleanup", () => {
  const cleaned = cleanProseBlock(
    "At a low MI (<0.1), microbubbles oscillate; a higher MI (>0.5) destroys them.",
  );

  assert.match(cleaned, /MI \(<0\.1\)/);
  assert.match(cleaned, /MI \(>0\.5\)/);
});

test("CEUS article notes prioritize physics, optimization, and artifacts", () => {
  const { notes } = buildAnkiNotes(ceusArticle, new Date("2026-06-22T12:00:00-05:00"));
  const contents = notes.map((note) => note.content).join("\n");

  assert.equal(notes.length, 18);
  assert.match(contents, /mechanical index of about \{\{c1::<0\.1\}\}/i);
  assert.match(contents, /focal zone \{\{c1::deep to the target\}\}/i);
  assert.match(contents, /Pseudowashout from continuous insonation/i);
  assert.match(contents, /figure-21\.jpg/i);
  assert.doesNotMatch(contents, /Mplete nonenhancement/i);
  assert.doesNotMatch(contents, /A major complication/i);
});

test("CEUS summary surfaces actionable setup and artifact correction", () => {
  const sections = buildSummarySections(ceusArticle);

  assert.deepEqual(
    sections.map((section) => section.label),
    ["Core physics", "Optimal setup", "Signal tradeoff", "Major pitfalls", "Corrective strategy"],
  );
  assert.match(sections[1].text, /<0\.1/);
  assert.match(sections[4].text, /intermittent imaging/i);
});
