const { escapeHtml, splitSentences, truncate } = require("./utils");
const { buildArticleMetadataLine } = require("./studyText");

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

function buildFigureControls(figures) {
  if (!Array.isArray(figures) || figures.length === 0) {
    return "";
  }

  const figureNav = buildFigureNav(figures);
  return `
    <div class="jump-row">
      <a class="jump-chip" href="#figures">Figures</a>
      <details class="figure-picker" data-figure-picker>
        <summary>Figure Selection</summary>
        <div class="figure-picker-panel">
          ${figureNav}
        </div>
      </details>
    </div>
  `;
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

function buildLightboxCaption(figure) {
  return figure.caption || figure.rawCaption || figure.teachingPoint || figure.label || "";
}

function buildImageButton(figure, className = "") {
  const classes = ["image-launch", className].filter(Boolean).join(" ");
  return `
    <button
      class="${classes}"
      type="button"
      data-lightbox-src="${escapeHtml(figure.relativeImagePath)}"
      data-lightbox-alt="${escapeHtml(figure.label || "Figure")}"
      data-lightbox-caption="${escapeHtml(buildLightboxCaption(figure))}"
      aria-label="Expand ${escapeHtml(figure.label || "figure")}"
    >
      <img src="${escapeHtml(figure.relativeImagePath)}" alt="${escapeHtml(figure.label || "Figure")}">
    </button>
  `;
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
          </div>
          <div class="figure-image-wrap">
            ${buildImageButton(figure)}
          </div>
        </section>
      `,
    )
    .join("\n");
}

function buildNarrativeDetails(article) {
  const bodyBlocks = Array.isArray(article.cleanedBodyBlocks)
    ? article.cleanedBodyBlocks.filter(Boolean)
    : [];
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

function buildPageScript() {
  return `
    <script>
      (function () {
        const link = document.querySelector("[data-copy-src]");
        if (link) {
          const originalText = link.textContent;
          link.addEventListener("click", async function (event) {
            const src = link.getAttribute("data-copy-src");
            if (!src) {
              return;
            }

            if (!navigator.clipboard || typeof navigator.clipboard.writeText !== "function") {
              return;
            }

            event.preventDefault();
            try {
              const response = await fetch(src, { credentials: "same-origin" });
              if (!response.ok) {
                throw new Error("Copy source request failed.");
              }
              const text = await response.text();
              await navigator.clipboard.writeText(text);
              link.textContent = "Copied for Chat";
              window.setTimeout(function () {
                link.textContent = originalText;
              }, 1800);
            } catch (error) {
              window.open(src, "_blank", "noopener");
            }
          });
        }

        const picker = document.querySelector("[data-figure-picker]");
        if (picker) {
          picker.querySelectorAll("a[href^='#']").forEach(function (anchor) {
            anchor.addEventListener("click", function () {
              picker.removeAttribute("open");
            });
          });
        }

        const lightbox = document.querySelector("[data-lightbox]");
        if (!lightbox) {
          return;
        }

        const lightboxImage = lightbox.querySelector("[data-lightbox-image]");
        const lightboxCaption = lightbox.querySelector("[data-lightbox-caption]");
        const lightboxStage = lightbox.querySelector(".lightbox-stage");

        function closeLightbox() {
          lightbox.hidden = true;
          document.body.classList.remove("lightbox-open");
          lightboxImage.removeAttribute("src");
          lightboxImage.alt = "";
          lightboxCaption.textContent = "";
        }

        function openLightbox(trigger) {
          const src = trigger.getAttribute("data-lightbox-src");
          if (!src) {
            return;
          }

          lightboxImage.src = src;
          lightboxImage.alt = trigger.getAttribute("data-lightbox-alt") || "";
          lightboxCaption.textContent = trigger.getAttribute("data-lightbox-caption") || "";
          lightbox.hidden = false;
          document.body.classList.add("lightbox-open");
        }

        document.querySelectorAll("[data-lightbox-src]").forEach(function (trigger) {
          trigger.addEventListener("click", function () {
            openLightbox(trigger);
          });
        });

        lightbox.addEventListener("click", closeLightbox);
        if (lightboxStage) {
          lightboxStage.addEventListener("click", function (event) {
            event.stopPropagation();
          });
        }

        document.addEventListener("keydown", function (event) {
          if (event.key === "Escape" && !lightbox.hidden) {
            closeLightbox();
          }
        });
      })();
    </script>
  `;
}

function buildReaderHtml(article) {
  const figures = Array.isArray(article.figures) ? article.figures : [];
  const heroFigure = figures.find((figure) => figure.isVisualAbstract) || figures[0];
  const summarySections = normalizeSummarySections(article);
  const leadSource =
    summarySections[0]?.text ||
    article.abstract ||
    (Array.isArray(article.cleanedBodyBlocks) ? article.cleanedBodyBlocks[0] : "") ||
    "No summary was extracted from the article page.";
  const digestLead = splitSentences(leadSource)[0] || leadSource;
  const heroImageBlock = heroFigure
    ? `
      <div class="hero-visual">
        ${buildImageButton(heroFigure, "hero-image-button")}
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
  if (article.copyChatRelativePath) {
    quickLinks.push(
      `<a href="${escapeHtml(article.copyChatRelativePath)}" target="_blank" rel="noreferrer" data-copy-src="${escapeHtml(article.copyChatRelativePath)}">Copy for Chat</a>`,
    );
  }
  if (article.pdfUrl) {
    quickLinks.push(`<a href="${escapeHtml(article.pdfUrl)}" target="_blank" rel="noreferrer">PDF</a>`);
  }
  if (article.ankiPackageRelativePath) {
    quickLinks.push(`<a href="${escapeHtml(article.ankiPackageRelativePath)}">Download Anki Package</a>`);
  }

  const figureSections = buildFigureSections(figures);
  const figureControls = buildFigureControls(figures);
  const summaryGrid = buildSummaryGrid(summarySections);
  const pageTitle = escapeHtml(article.title);
  const metadataLine = buildArticleMetadataLine(article);

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
        align-items: flex-start;
      }
      .action-row a,
      .jump-chip,
      .figure-picker summary {
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
        color: var(--accent-2);
        cursor: pointer;
      }
      .figure-picker {
        max-width: min(100%, 760px);
      }
      .figure-picker summary {
        list-style: none;
        user-select: none;
      }
      .figure-picker summary::-webkit-details-marker {
        display: none;
      }
      .figure-picker summary::after {
        content: "▾";
        margin-left: 10px;
        font-size: 0.82rem;
      }
      .figure-picker[open] summary::after {
        content: "▴";
      }
      .figure-picker-panel {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 10px;
        padding: 14px;
        border-radius: 22px;
        background: rgba(255, 255, 255, 0.82);
        border: 1px solid rgba(20, 33, 29, 0.12);
      }
      .hero-visual { padding: 18px; }
      .hero-visual img {
        width: 100%;
        display: block;
        border-radius: 18px;
        background: #e8e1d5;
      }
      .image-launch {
        display: block;
        width: 100%;
        padding: 0;
        border: 0;
        background: transparent;
        cursor: zoom-in;
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
      .source-details {
        margin-top: 18px;
        border: 1px solid var(--line);
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.52);
      }
      .source-details summary {
        cursor: pointer;
        padding: 14px 16px;
        font-weight: 700;
      }
      .source-copy {
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
      .lightbox-open {
        overflow: hidden;
      }
      .lightbox {
        position: fixed;
        inset: 0;
        z-index: 999;
        display: grid;
        place-items: center;
        padding: 24px;
        background: rgba(0, 0, 0, 0.94);
      }
      .lightbox[hidden] {
        display: none !important;
      }
      .lightbox-stage {
        max-width: min(100vw - 48px, 1500px);
        max-height: calc(100vh - 48px);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 14px;
      }
      .lightbox-stage img {
        display: block;
        max-width: 100%;
        max-height: calc(100vh - 120px);
        width: auto;
        height: auto;
        background: black;
      }
      .lightbox-caption {
        max-width: min(100%, 960px);
        color: rgba(255, 255, 255, 0.86);
        text-align: center;
        line-height: 1.6;
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
          <div class="meta-row">${escapeHtml(metadataLine)}</div>
          <div class="authors">${escapeHtml(formatAuthors(article.authors))}</div>
          <p class="digest-lead">${escapeHtml(digestLead)}</p>
          <div class="action-row">${quickLinks.join("")}</div>
          ${figureControls}
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

      <section class="figure-area" id="figures">
        <h2>Figure Review</h2>
        <p>Figures are pulled directly from the article assets. Each card surfaces the main teaching point first. Tap any figure to open it fullscreen and read the full caption there.</p>
        <div class="figure-stack">
          ${figureSections}
        </div>
      </section>
    </main>
    <div class="lightbox" data-lightbox hidden>
      <div class="lightbox-stage" role="dialog" aria-modal="true" aria-label="Expanded figure view">
        <img data-lightbox-image alt="">
        <div class="lightbox-caption" data-lightbox-caption></div>
      </div>
    </div>
    ${buildPageScript()}
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
      const metadataLine = buildArticleMetadataLine(article);

      return `
        <article class="card">
          ${
            article.thumbnailIndexPath
              ? `<a class="thumb" href="${escapeHtml(article.readerIndexPath)}"><img src="${escapeHtml(article.thumbnailIndexPath)}" alt="${escapeHtml(article.title)}"></a>`
              : ""
          }
          <div class="eyebrow">${escapeHtml(metadataLine)}</div>
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
        <p>Each article gets a phone-friendly study page, a direct link back to RadioGraphics, a copy-ready study packet, and a downloadable Anki package. New runs add one article at a time to this library.</p>
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
