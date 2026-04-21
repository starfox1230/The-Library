const path = require("node:path");
const { escapeHtml, formatDate } = require("./utils");

function formatAuthors(authors) {
  if (!authors?.length) {
    return "Unknown authors";
  }

  if (authors.length <= 6) {
    return authors.join(", ");
  }

  return `${authors.slice(0, 6).join(", ")}, et al.`;
}

function buildFigureNav(figures) {
  return figures
    .map(
      (figure) =>
        `<a class="jump-chip" href="#${escapeHtml(figure.anchor)}">${escapeHtml(figure.label)}</a>`,
    )
    .join("");
}

function buildFigureSections(figures) {
  return figures
    .map(
      (figure) => `
        <section class="figure-panel" id="${escapeHtml(figure.anchor)}">
          <div class="figure-copy">
            <div class="eyebrow">${escapeHtml(figure.label)}</div>
            <h2>${escapeHtml(figure.teachingPoint)}</h2>
            <p class="caption">${escapeHtml(figure.caption || "")}</p>
          </div>
          <div class="figure-image-wrap">
            <img src="${escapeHtml(figure.relativeImagePath)}" alt="${escapeHtml(figure.label)}">
          </div>
        </section>
      `,
    )
    .join("\n");
}

function buildReaderHtml(article) {
  const heroFigure = article.figures.find((figure) => figure.isVisualAbstract) || article.figures[0];
  const heroImageBlock = heroFigure
    ? `
      <div class="hero-visual">
        <img src="${escapeHtml(heroFigure.relativeImagePath)}" alt="${escapeHtml(heroFigure.label)}">
        <div class="hero-caption">${escapeHtml(heroFigure.label)}</div>
      </div>
    `
    : "";

  const keyFacts = article.keyFacts
    .map((fact) => `<li>${escapeHtml(fact)}</li>`)
    .join("");
  const quickLinks = [];

  if (article.link) {
    quickLinks.push(`<a href="${escapeHtml(article.link)}" target="_blank" rel="noreferrer">Open Article</a>`);
  }
  if (article.pdfUrl) {
    quickLinks.push(`<a href="${escapeHtml(article.pdfUrl)}" target="_blank" rel="noreferrer">PDF</a>`);
  }
  if (article.ankiPackageRelativePath) {
    quickLinks.push(`<a href="${escapeHtml(article.ankiPackageRelativePath)}">Anki Package</a>`);
  }

  const figureSections = buildFigureSections(article.figures);
  const figureNav = buildFigureNav(article.figures);
  const pageTitle = escapeHtml(article.title);
  const metadataBits = [
    article.journal || "RadioGraphics",
    formatDate(article.publishedAt) || "Unknown date",
    article.volume ? `Vol ${article.volume}` : "",
    article.issue ? `Issue ${article.issue}` : "",
    article.pages ? `Pages ${article.pages}` : "",
  ].filter(Boolean);
  const relativeJsonPath = path.posix.join(".", path.basename(article.jsonPath));

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
        --panel: rgba(255, 251, 245, 0.88);
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
      .sidebar,
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
      .eyebrow {
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
      .meta-row,
      .authors {
        margin-top: 10px;
        color: var(--muted);
        font-size: 0.96rem;
      }
      .abstract {
        margin-top: 18px;
        color: #273833;
        font-size: 1.02rem;
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
      .content-grid {
        display: grid;
        grid-template-columns: minmax(0, 1fr) 300px;
        gap: 24px;
        margin-top: 24px;
      }
      .sidebar {
        position: sticky;
        top: 18px;
        height: fit-content;
        padding: 22px;
      }
      .sidebar h2 {
        margin: 0 0 16px;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--muted);
      }
      .sidebar ul {
        margin: 0;
        padding-left: 18px;
        line-height: 1.7;
      }
      .sidebar li + li {
        margin-top: 12px;
      }
      .sidebar small {
        display: block;
        margin-top: 18px;
        color: var(--muted);
      }
      .figure-stack {
        display: grid;
        gap: 22px;
      }
      .figure-panel { padding: 18px; }
      .figure-copy h2 {
        margin: 12px 0;
        font-family: "Georgia", "Times New Roman", serif;
        font-size: clamp(1.4rem, 3vw, 2.1rem);
        line-height: 1.15;
      }
      .caption {
        margin: 0;
        color: #30453f;
        line-height: 1.7;
        white-space: pre-wrap;
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
        .hero,
        .content-grid {
          grid-template-columns: 1fr;
        }
        .sidebar { position: static; }
      }
    </style>
  </head>
  <body>
    <main class="shell">
      <section class="hero">
        <article class="hero-copy">
          <div class="eyebrow">RadioGraphics Reader</div>
          <h1>${pageTitle}</h1>
          <div class="meta-row">${escapeHtml(metadataBits.join(" · "))}</div>
          <div class="authors">${escapeHtml(formatAuthors(article.authors))}</div>
          <p class="abstract">${escapeHtml(article.abstract || "No abstract was available from the article page.")}</p>
          <div class="action-row">${quickLinks.join("")}</div>
          <div class="jump-row">${figureNav}</div>
        </article>
        ${heroImageBlock}
      </section>

      <section class="content-grid">
        <div class="figure-stack">
          ${figureSections}
        </div>
        <aside class="sidebar">
          <h2>Key Facts</h2>
          <ul>${keyFacts}</ul>
          <small>DOI: ${escapeHtml(article.doi)}</small>
          <small>Article JSON: ${escapeHtml(relativeJsonPath)}</small>
        </aside>
      </section>
    </main>
  </body>
</html>
`;
}

function buildArticlesIndex(articles) {
  const cards = articles
    .map(
      (article) => `
        <article class="card">
          <div class="eyebrow">${escapeHtml(formatDate(article.publishedAt) || "Undated")}</div>
          <h2>${escapeHtml(article.title)}</h2>
          <p>${escapeHtml((article.keyFacts || []).slice(0, 2).join(" "))}</p>
          <div class="links">
            <a href="${escapeHtml(article.readerIndexPath)}">Reader</a>
            ${
              article.ankiIndexPath
                ? `<a href="${escapeHtml(article.ankiIndexPath)}">Anki Package</a>`
                : ""
            }
          </div>
        </article>
      `,
    )
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
        width: min(1100px, calc(100vw - 32px));
        margin: 0 auto;
        padding: 32px 0 48px;
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 18px;
      }
      .card {
        background: rgba(255, 251, 245, 0.9);
        border-radius: 24px;
        border: 1px solid rgba(20, 33, 29, 0.12);
        padding: 20px;
      }
      .card h2 {
        margin: 12px 0;
        font-family: "Georgia", serif;
        line-height: 1.1;
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
      <h1>RadioGraphics Review Library</h1>
      <p>Image-first article readers and Anki packages generated from your RSNA session.</p>
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
