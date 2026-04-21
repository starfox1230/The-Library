const path = require("node:path");
const { escapeHtml, formatDate, splitSentences, truncate } = require("./utils");

function formatAuthors(authors) {
  if (!authors?.length) {
    return "Unknown authors";
  }

  if (authors.length <= 6) {
    return authors.join(", ");
  }

  return `${authors.slice(0, 6).join(", ")}, et al.`;
}

function normalizeSummarySections(article) {
  if (Array.isArray(article.summarySections) && article.summarySections.length > 0) {
    return article.summarySections;
  }

  return (article.keyFacts || []).map((fact, index) => ({
    label: index === 0 ? "Key point" : `Key point ${index + 1}`,
    text: fact,
  }));
}

function buildFigureNav(figures) {
  return figures
    .map(
      (figure) =>
        `<a class="jump-chip" href="#${escapeHtml(figure.anchor)}">${escapeHtml(figure.label)}</a>`,
    )
    .join("");
}

function buildSummaryGrid(summarySections) {
  return summarySections
    .map(
      (section) => `
        <article class="summary-card">
          <div class="summary-label">${escapeHtml(section.label)}</div>
          <p>${escapeHtml(section.text)}</p>
        </article>
      `,
    )
    .join("\n");
}

function buildFigureSections(figures) {
  return figures
    .map(
      (figure) => `
        <section class="figure-panel" id="${escapeHtml(figure.anchor)}">
          <div class="figure-copy">
            <div class="figure-meta-row">
              <div class="eyebrow">${escapeHtml(figure.label)}</div>
            </div>
            <h2>${escapeHtml(figure.teachingPoint)}</h2>
            <details class="caption-details">
              <summary>Full figure caption</summary>
              <p class="caption">${escapeHtml(figure.caption || "")}</p>
            </details>
          </div>
          <div class="figure-image-wrap">
            <img src="${escapeHtml(figure.relativeImagePath)}" alt="${escapeHtml(figure.label)}">
          </div>
        </section>
      `,
    )
    .join("\n");
}

function buildNarrativeDetails(article) {
  const bodyBlocks = Array.isArray(article.bodyBlocks) ? article.bodyBlocks.filter(Boolean) : [];
  if (bodyBlocks.length === 0) {
    return "";
  }

  const paragraphs = bodyBlocks
    .map((paragraph) => `<p>${escapeHtml(paragraph)}</p>`)
    .join("");

  return `
    <details class="source-details">
      <summary>View extracted article prose</summary>
      <div class="source-copy">${paragraphs}</div>
    </details>
  `;
}

function buildReaderHtml(article) {
  const heroFigure = article.figures.find((figure) => figure.isVisualAbstract) || article.figures[0];
  const summarySections = normalizeSummarySections(article);
  const leadSource =
    summarySections[0]?.text ||
    article.abstract ||
    (Array.isArray(article.bodyBlocks) ? article.bodyBlocks[0] : "") ||
    "No summary was extracted from the article page.";
  const digestLead =
    splitSentences(leadSource)[0] ||
    leadSource;
  const heroImageBlock = heroFigure
    ? `
      <div class="hero-visual">
        <img src="${escapeHtml(heroFigure.relativeImagePath)}" alt="${escapeHtml(heroFigure.label)}">
        <div class="hero-caption">${escapeHtml(heroFigure.label)}</div>
      </div>
    `
    : "";
  const quickLinks = [];

  if (article.link) {
    quickLinks.push(
      `<a href="${escapeHtml(article.link)}" target="_blank" rel="noreferrer">Open at RadioGraphics</a>`,
    );
  }
  if (article.pdfUrl) {
    quickLinks.push(`<a href="${escapeHtml(article.pdfUrl)}" target="_blank" rel="noreferrer">PDF</a>`);
  }
  if (article.ankiPackageRelativePath) {
    quickLinks.push(`<a href="${escapeHtml(article.ankiPackageRelativePath)}">Download Anki Package</a>`);
  }

  const figureSections = buildFigureSections(article.figures);
  const figureNav = buildFigureNav(article.figures);
  const summaryGrid = buildSummaryGrid(summarySections);
  const pageTitle = escapeHtml(article.title);
  const metadataBits = [
    article.journal || "RadioGraphics",
    formatDate(article.publishedAt) || "Unknown date",
    article.volume ? `Vol ${article.volume}` : "",
    article.issue ? `Issue ${article.issue}` : "",
    article.pages ? `Pages ${article.pages}` : "",
  ].filter(Boolean);

  return `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>${pageTitle}</title>
    <style>
      :root {
        --ink: #14211d;
        --muted: #576863;
        --paper: #f5f1e8;
        --panel: rgba(255, 251, 245, 0.92);
        --panel-strong: #fffaf2;
        --accent: #aa5e2b;
        --accent-2: #184a45;
        --line: rgba(20, 33, 29, 0.12);
        --shadow: 0 20px 60px rgba(20, 33, 29, 0.12);
      }

      * { box-sizing: border-box; }
      html { scroll-behavior: smooth; }
      body {
        margin: 0;
        color: var(--ink);
        font-family: "Aptos", "Segoe UI", "Helvetica Neue", sans-serif;
        background:
          radial-gradient(circle at top left, rgba(170, 94, 43, 0.18), transparent 36%),
          radial-gradient(circle at top right, rgba(24, 74, 69, 0.2), transparent 28%),
          linear-gradient(180deg, #f7f3eb 0%, #efe9dc 100%);
      }
      a { color: var(--accent-2); }
      .shell {
        width: min(1240px, calc(100vw - 32px));
        margin: 0 auto;
        padding: 28px 0 48px;
      }
      .hero {
        display: grid;
        grid-template-columns: minmax(0, 1.15fr) minmax(320px, 0.85fr);
        gap: 24px;
        align-items: stretch;
      }
      .hero-copy,
      .hero-visual,
      .summary-card,
      .narrative-panel,
      .figure-panel {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 28px;
        box-shadow: var(--shadow);
      }
      .hero-copy { padding: 28px; }
      .hero-copy h1 {
        margin: 0 0 16px;
        font-family: "Georgia", "Times New Roman", serif;
        font-size: clamp(2rem, 4vw, 3.8rem);
        line-height: 1.02;
      }
      .eyebrow,
      .summary-label {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 14px;
        border-radius: 999px;
        background: rgba(24, 74, 69, 0.08);
        color: var(--accent-2);
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-size: 0.78rem;
        font-weight: 700;
      }
      .summary-label {
        background: rgba(170, 94, 43, 0.1);
        color: var(--accent);
      }
      .meta-row,
      .authors {
        margin-top: 10px;
        color: var(--muted);
        font-size: 0.96rem;
      }
      .digest-lead {
        margin-top: 18px;
        color: #273833;
        font-size: 1.06rem;
        line-height: 1.75;
      }
      .action-row,
      .jump-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 18px;
      }
      .action-row a,
      .jump-chip {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 42px;
        padding: 0 16px;
        border-radius: 999px;
        background: white;
        border: 1px solid rgba(20, 33, 29, 0.14);
        text-decoration: none;
        font-weight: 700;
      }
      .hero-visual { padding: 18px; }
      .hero-visual img {
        width: 100%;
        display: block;
        border-radius: 18px;
        background: #e8e1d5;
      }
      .hero-caption {
        margin-top: 10px;
        color: var(--muted);
        font-size: 0.9rem;
      }
      .summary-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 18px;
        margin-top: 24px;
      }
      .summary-card {
        padding: 22px;
      }
      .summary-card p {
        margin: 14px 0 0;
        line-height: 1.7;
        color: #273833;
      }
      .narrative-panel {
        margin-top: 24px;
        padding: 24px;
      }
      .narrative-panel h2,
      .figure-area h2 {
        margin: 0 0 10px;
        font-family: "Georgia", "Times New Roman", serif;
        font-size: clamp(1.5rem, 3vw, 2.2rem);
      }
      .narrative-panel p,
      .figure-area p {
        line-height: 1.75;
        color: #30453f;
      }
      .source-details,
      .caption-details {
        margin-top: 18px;
        border: 1px solid var(--line);
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.52);
      }
      .source-details summary,
      .caption-details summary {
        cursor: pointer;
        padding: 14px 16px;
        font-weight: 700;
      }
      .source-copy,
      .caption {
        padding: 0 16px 16px;
      }
      .figure-area {
        margin-top: 28px;
      }
      .figure-stack {
        display: grid;
        gap: 22px;
        margin-top: 18px;
      }
      .figure-panel {
        padding: 18px;
      }
      .figure-meta-row {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: center;
      }
      .figure-copy h2 {
        margin: 12px 0 0;
        font-family: "Georgia", "Times New Roman", serif;
        font-size: clamp(1.35rem, 3vw, 2rem);
        line-height: 1.18;
      }
      .figure-image-wrap {
        margin-top: 16px;
        border-radius: 18px;
        overflow: hidden;
        background: #e6dece;
      }
      .figure-image-wrap img {
        display: block;
        width: 100%;
        height: auto;
      }
      @media (max-width: 980px) {
        .hero {
          grid-template-columns: 1fr;
        }
      }
    </style>
  </head>
  <body>
    <main class="shell">
      <section class="hero">
        <article class="hero-copy">
          <div class="eyebrow">RadioGraphics Digest</div>
          <h1>${pageTitle}</h1>
          <div class="meta-row">${escapeHtml(metadataBits.join(" | "))}</div>
          <div class="authors">${escapeHtml(formatAuthors(article.authors))}</div>
          <p class="digest-lead">${escapeHtml(digestLead)}</p>
          <div class="action-row">${quickLinks.join("")}</div>
          <div class="jump-row">${figureNav}</div>
        </article>
        ${heroImageBlock}
      </section>

      <section class="summary-grid">
        ${summaryGrid}
      </section>

      <section class="narrative-panel">
        <h2>Why This Article Matters</h2>
        <p>This page is meant to be a quick study digest rather than a full-text mirror. Use the summary cards first, review the figures next, and open the original article when you want the full discussion and references.</p>
        ${buildNarrativeDetails(article)}
      </section>

      <section class="figure-area">
        <h2>Figure Review</h2>
        <p>Figures are pulled directly from the article assets. Each card surfaces the main teaching point first, with the full caption tucked behind a toggle.</p>
        <div class="figure-stack">
          ${figureSections}
        </div>
      </section>
    </main>
  </body>
</html>
`;
}

function buildCardSummary(article) {
  const summarySections = normalizeSummarySections(article);
  const parts = summarySections
    .slice(0, 2)
    .map((section) => `${section.label}: ${section.text}`);

  if (parts.length > 0) {
    return truncate(parts.join(" "), 280);
  }

  return truncate((article.keyFacts || []).slice(0, 2).join(" "), 280);
}

function buildArticlesIndex(articles) {
  const cards = articles
    .map((article) => {
      const metadataBits = [
        formatDate(article.publishedAt) || "Undated",
        article.volume ? `Vol ${article.volume}` : "",
        article.issue ? `Issue ${article.issue}` : "",
      ].filter(Boolean);

      return `
        <article class="card">
          ${
            article.thumbnailIndexPath
              ? `<a class="thumb" href="${escapeHtml(article.readerIndexPath)}"><img src="${escapeHtml(article.thumbnailIndexPath)}" alt="${escapeHtml(article.title)}"></a>`
              : ""
          }
          <div class="eyebrow">${escapeHtml(metadataBits.join(" | "))}</div>
          <h2>${escapeHtml(article.title)}</h2>
          <p>${escapeHtml(buildCardSummary(article))}</p>
          <div class="links">
            <a href="${escapeHtml(article.readerIndexPath)}">Study Page</a>
            ${
              article.ankiIndexPath
                ? `<a href="${escapeHtml(article.ankiIndexPath)}">Anki Package</a>`
                : ""
            }
          </div>
        </article>
      `;
    })
    .join("\n");

  return `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>RadioGraphics Review Library</title>
    <style>
      body {
        margin: 0;
        font-family: "Aptos", "Segoe UI", sans-serif;
        background: linear-gradient(180deg, #f6f1e7 0%, #ece4d7 100%);
        color: #14211d;
      }
      main {
        width: min(1120px, calc(100vw - 32px));
        margin: 0 auto;
        padding: 32px 0 48px;
      }
      .hero {
        margin-bottom: 24px;
      }
      .hero h1 {
        margin: 0 0 10px;
        font-family: "Georgia", serif;
        font-size: clamp(2rem, 4vw, 3.4rem);
      }
      .hero p {
        margin: 0;
        max-width: 760px;
        line-height: 1.7;
        color: #30453f;
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 20px;
      }
      .card {
        background: rgba(255, 251, 245, 0.92);
        border-radius: 24px;
        border: 1px solid rgba(20, 33, 29, 0.12);
        padding: 18px;
        box-shadow: 0 18px 40px rgba(20, 33, 29, 0.08);
      }
      .thumb {
        display: block;
        margin: -6px -6px 16px;
        border-radius: 18px;
        overflow: hidden;
        background: #e6dece;
      }
      .thumb img {
        display: block;
        width: 100%;
        aspect-ratio: 4 / 3;
        object-fit: cover;
      }
      .card h2 {
        margin: 12px 0;
        font-family: "Georgia", serif;
        line-height: 1.1;
      }
      .card p {
        margin: 0 0 16px;
        color: #30453f;
        line-height: 1.65;
      }
      .links {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
      }
      .links a,
      .eyebrow {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
      }
      .links a {
        min-height: 40px;
        padding: 0 14px;
        background: white;
        border: 1px solid rgba(20, 33, 29, 0.14);
        text-decoration: none;
        font-weight: 700;
        color: #184a45;
      }
      .eyebrow {
        padding: 6px 12px;
        background: rgba(24, 74, 69, 0.08);
        color: #184a45;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
      }
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <h1>RadioGraphics Review Library</h1>
        <p>Each article gets a phone-friendly study page, a direct link back to RadioGraphics, and a downloadable Anki package. New runs add to this library; your phone only needs to read the finished output.</p>
      </section>
      <section class="grid">
        ${cards}
      </section>
    </main>
  </body>
</html>`;
}

module.exports = {
  buildArticlesIndex,
  buildReaderHtml,
};
