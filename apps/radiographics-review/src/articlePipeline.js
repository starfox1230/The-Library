const fs = require("node:fs");
const path = require("node:path");
const {
  connectToBrowser,
  launchBrowserProcess,
  stopBrowserProcess,
} = require("./browserControl");
const { buildAnkiPackage } = require("./anki");
const { loadGeneratedArticles } = require("./library");
const { buildAnkiNotes } = require("./notes");
const { buildArticlesIndex, buildReaderHtml } = require("./renderReader");
const {
  buildKeyFacts,
  buildSummarySections,
  buildTeachingPoint,
} = require("./summarize");
const {
  buildCopyForChatText,
  cleanFigureCaption,
  cleanProseBlock,
} = require("./studyText");
const { ensureAuthenticatedArticleAccess, looksLikeAccessWallText } = require("./rsnaAuth");
const {
  formatDate,
  normalizeWhitespace,
  readJson,
  slugify,
  stripHtml,
  unique,
  uniqueBy,
  writeJson,
} = require("./utils");

function articleDirName(article) {
  const published = formatDate(article.publishedAt) || "undated";
  const doiSlug = slugify(article.doi || "article", 32);
  const titleSlug = slugify(article.title || "article", 72);
  return `${published}-${doiSlug}-${titleSlug}`;
}

function imageExtension(src) {
  try {
    const extension = path.extname(new URL(src).pathname).toLowerCase();
    if ([".jpg", ".jpeg", ".png", ".webp", ".gif"].includes(extension)) {
      return extension === ".jpeg" ? ".jpg" : extension;
    }
  } catch (error) {
    // Ignore malformed URLs and fall back to PNG.
  }

  return ".png";
}

function filterAccessWallBlocks(blocks) {
  return (blocks || []).filter((block) => !looksLikeAccessWallText(block));
}

function ensureArticleBodyAccess(extracted) {
  const joinedText = normalizeWhitespace(
    [
      ...(extracted.cleanedBodyBlocks || []),
      extracted.cleanedBodyText || "",
    ].join(" "),
  );

  if (!joinedText || looksLikeAccessWallText(joinedText)) {
    throw new Error(
      "Article full text was not accessible in the current RSNA session. Re-run `npm run login` in the dedicated browser profile, confirm the full article body loads, and then try again.",
    );
  }
}

async function extractPageArticle(page, seedArticle) {
  const payload = await page.evaluate(() => {
    function clean(text) {
      return (text || "").replace(/\s+/g, " ").trim();
    }

    function meta(name) {
      const byName = document.querySelector(`meta[name="${name}"]`);
      const byProperty = document.querySelector(`meta[property="${name}"]`);
      return byName?.content || byProperty?.content || "";
    }

    function abstractText() {
      const abstractRoot =
        document.querySelector('[data-title="Abstract"]') ||
        document.querySelector("#abstract") ||
        document.querySelector(".abstract") ||
        document.querySelector(".hlFld-Abstract");
      const sectionText = clean(abstractRoot?.innerText || "");
      if (sectionText) {
        return sectionText.replace(/^abstract\s*/i, "").trim();
      }
      return "";
    }

    function looksLikeAccessWallText(text) {
      const value = clean(text || "");
      if (!value) {
        return false;
      }

      const patterns = [
        /\bget full access to this article\b/i,
        /\balready a subscriber\b/i,
        /\bsign in as an individual\b/i,
        /\bvia your institution\b/i,
        /\bavailable purchase options\b/i,
        /\baccess through your institution\b/i,
        /\bindividual access\b/i,
      ];
      const matches = patterns.filter((pattern) => pattern.test(value)).length;
      return matches >= 2 || /\bget full access to this article\b/i.test(value);
    }

    function extractBodyBlocks() {
      const root =
        document.querySelector("#bodymatter") ||
        document.querySelector(".hlFld-Fulltext") ||
        document.querySelector("main article") ||
        document.querySelector("article");
      if (!root) {
        return [];
      }

      const containers = [root.querySelector(".core-container"), root].filter(Boolean);
      const blocks = [];

      for (const container of containers) {
        const children = Array.from(container.children || []);
        for (const child of children) {
          if (!(child instanceof HTMLElement)) {
            continue;
          }
          if (child.matches(".figure-wrap, figure, .table-wrap, .media-wrap, .supplemental-materials")) {
            continue;
          }

          const text = clean(child.innerText || "");
          if (text.length >= 40 && !looksLikeAccessWallText(text)) {
            blocks.push(text);
          }
        }

        if (blocks.length > 0) {
          return [...new Set(blocks)];
        }
      }

      return [];
    }

    const figures = Array.from(document.querySelectorAll("figure.graphic")).map((figure, index) => {
      const image = figure.querySelector("img");
      const src = image?.currentSrc || image?.src || "";
      const rawCaption = clean(figure.querySelector("figcaption, .caption")?.innerText || "");
      const isVisualAbstract =
        /\.va\./i.test(src) ||
        clean(figure.innerText || "").toLowerCase().includes("visual abstract");

      return {
        index: index + 1,
        src,
        rawCaption,
        isVisualAbstract,
      };
    });

    return {
      title:
        meta("citation_title") ||
        meta("og:title") ||
        clean(document.querySelector("h1")?.innerText || document.title || ""),
      abstract: meta("description") || abstractText(),
      rawBodyBlocks: extractBodyBlocks(),
      pdfUrl: meta("citation_pdf_url"),
      authors: Array.from(document.querySelectorAll('meta[name="citation_author"]'))
        .map((node) => clean(node.content))
        .filter(Boolean),
      figures,
    };
  });

  const dedupedFigures = uniqueBy(
    (payload.figures || []).filter((figure) => figure.src),
    (figure) => figure.src,
  ).map((figure, index) => {
    const label = figure.isVisualAbstract
      ? "Visual Abstract"
      : figure.rawCaption.match(/^Figure\s+\d+/i)?.[0] || `Figure ${index + 1}`;
    return {
      ...figure,
      label,
    };
  });

  const rawBodyBlocks = filterAccessWallBlocks(
    (payload.rawBodyBlocks || [])
    .map((block) => normalizeWhitespace(stripHtml(block)))
    .filter(Boolean),
  );
  const cleanedBodyBlocks = filterAccessWallBlocks(
    rawBodyBlocks
    .map((block) => cleanProseBlock(block))
    .filter(Boolean),
  );

  const extracted = {
    ...seedArticle,
    title: stripHtml(payload.title || seedArticle.title)
      .replace(/\s*\|\s*RadioGraphics\s*$/i, "")
      .replace(/\s*RadioGraphics\s*$/i, "")
      .trim(),
    link: page.url(),
    abstract: cleanProseBlock(
      stripHtml(payload.abstract || "")
        .replace(/^View all available purchase options.*$/i, "")
        .replace(/^To read the full-text.*$/i, "")
        .trim(),
    ),
    rawBodyBlocks,
    rawBodyText: rawBodyBlocks.join("\n\n"),
    cleanedBodyBlocks,
    cleanedBodyText: cleanedBodyBlocks.join("\n\n"),
    bodyBlocks: cleanedBodyBlocks,
    bodyText: cleanedBodyBlocks.join("\n\n"),
    pdfUrl: payload.pdfUrl || "",
    authors: unique([...(payload.authors || []), ...(seedArticle.authors || [])]),
    figures: dedupedFigures,
  };

  ensureArticleBodyAccess(extracted);
  return extracted;
}

async function hideFigureCaptureOverlays(page) {
  await page.evaluate(() => {
    const selectors = [
      "#cookie-popup",
      ".st-header",
      ".navbar-in",
      ".references-popup-wrapper",
      ".figure-pop-btn",
      ".core-figure-tools",
      "#publication__menu__content",
      "#a2a_modal",
      "#a2apage_full",
    ];

    for (const selector of selectors) {
      for (const node of document.querySelectorAll(selector)) {
        node.style.setProperty("display", "none", "important");
        node.style.setProperty("visibility", "hidden", "important");
      }
    }
  }).catch(() => {});
}

async function captureFigureAssets(page, figures, assetsDir) {
  const locator = page.locator("figure.graphic");
  const total = await locator.count();
  const savedFigures = [];
  let numberedFigure = 1;
  const request = page.context().request;

  for (let index = 0; index < Math.min(total, figures.length); index += 1) {
    const figure = figures[index];
    if (!figure.src) {
      continue;
    }

    const extension = imageExtension(figure.src);
    const fileName = figure.isVisualAbstract
      ? `visual-abstract${extension}`
      : `figure-${String(numberedFigure).padStart(2, "0")}${extension}`;
    const filePath = path.join(assetsDir, fileName);

    let saved = false;
    try {
      const response = await request.get(figure.src);
      if (response.ok()) {
        fs.writeFileSync(filePath, await response.body());
        saved = true;
      }
    } catch (error) {
      saved = false;
    }

    if (!saved) {
      const imageLocator = locator.nth(index).locator("img").first();
      const hasImage = await imageLocator.count();
      if (!hasImage) {
        continue;
      }

      await hideFigureCaptureOverlays(page);
      await imageLocator.scrollIntoViewIfNeeded();
      await imageLocator.screenshot({ path: filePath });
    }

    const cleanedCaption = cleanFigureCaption(figure.rawCaption);
    savedFigures.push({
      ...figure,
      caption: cleanedCaption,
      anchor: slugify(figure.label, 32),
      localImageName: fileName,
      localImagePath: filePath,
      relativeImagePath: path.posix.join("assets", fileName),
      teachingPoint: buildTeachingPoint(cleanedCaption),
    });

    if (!figure.isVisualAbstract) {
      numberedFigure += 1;
    }
  }

  return savedFigures;
}

function writeReaderIndex(config) {
  const articles = loadGeneratedArticles(config).map((article) => ({
    ...article,
    readerIndexPath: path.posix.join(
      "articles",
      path.basename(article.articleDir),
      "reader.html",
    ),
    thumbnailIndexPath:
      article.figures?.[0]?.relativeImagePath
        ? path.posix.join(
            "articles",
            path.basename(article.articleDir),
            article.figures[0].relativeImagePath,
          )
        : "",
    ankiIndexPath: article.ankiPackageRelativePath
      ? path.posix.join(
          "articles",
          path.basename(article.articleDir),
          article.ankiPackageRelativePath,
        )
      : "",
  }));

  const indexHtml = buildArticlesIndex(articles);
  const appIndexPath = path.join(config.workspaceRoot, "index.html");
  const legacyIndexPath = path.join(config.articlesDir, "index.html");
  fs.writeFileSync(appIndexPath, indexHtml, "utf8");
  fs.writeFileSync(legacyIndexPath, indexHtml, "utf8");
  return appIndexPath;
}

async function captureArticlePackages(config, articles) {
  if (articles.length === 0) {
    return {
      enabled: false,
      reason: "No articles required packaging.",
      articles,
      indexPath: writeReaderIndex(config),
    };
  }

  const launched = launchBrowserProcess(config, {
    startMinimized: true,
    url: "about:blank",
  });
  const browser = await connectToBrowser(config);
  const context = browser.contexts()[0];
  const page = context.pages()[0] || (await context.newPage());

  try {
    const packagedArticles = [];

    for (const article of articles) {
      const articleDir = path.join(config.articlesDir, articleDirName(article));
      const assetsDir = path.join(articleDir, "assets");
      const ankiDir = path.join(articleDir, "anki");
      fs.mkdirSync(assetsDir, { recursive: true });
      fs.mkdirSync(ankiDir, { recursive: true });

      try {
        await page.goto(article.link, {
          waitUntil: "domcontentloaded",
          timeout: 60000,
        });
        await page.waitForLoadState("networkidle", { timeout: 20000 }).catch(() => {});

        const authResult = await ensureAuthenticatedArticleAccess(page, config, article.link);
        if (!authResult.success) {
          throw new Error(authResult.reason);
        }

        const extracted = await extractPageArticle(page, article);
        const figures = await captureFigureAssets(page, extracted.figures, assetsDir);
        const generatedAt = new Date().toISOString();
        const articlePayload = {
          ...extracted,
          slug: slugify(extracted.title, 80),
          articleDir,
          generatedAt,
          figures,
          summarySections: buildSummarySections({ ...extracted, figures }),
          keyFacts: buildKeyFacts({ ...extracted, figures }),
        };

        const jsonPath = path.join(articleDir, "article.json");
        const copyChatPath = path.join(articleDir, "copy-for-chat.txt");
        const notesJsonPath = path.join(ankiDir, "notes.json");
        articlePayload.jsonPath = jsonPath;
        articlePayload.copyChatPath = copyChatPath;
        articlePayload.copyChatRelativePath = "copy-for-chat.txt";
        articlePayload.ankiNotesPath = notesJsonPath;
        articlePayload.ankiNotesRelativePath = path.posix.join("anki", "notes.json");

        const noteBundle = buildAnkiNotes(articlePayload, generatedAt);
        articlePayload.ankiBatchTag = noteBundle.batchTag;
        articlePayload.ankiNotesCount = noteBundle.notes.length;

        fs.writeFileSync(copyChatPath, buildCopyForChatText(articlePayload), "utf8");
        writeJson(notesJsonPath, noteBundle.notes);
        writeJson(jsonPath, articlePayload);

        const ankiResult = await buildAnkiPackage(config, articlePayload);
        articlePayload.ankiPackagePath = ankiResult.packagePath;
        articlePayload.ankiPackageRelativePath = path.posix.join(
          "anki",
          path.basename(ankiResult.packagePath),
        );

        const readerPath = path.join(articleDir, "reader.html");
        articlePayload.readerPath = readerPath;
        fs.writeFileSync(readerPath, buildReaderHtml(articlePayload), "utf8");
        writeJson(jsonPath, articlePayload);

        packagedArticles.push({
          ...articlePayload,
          status: "success",
        });
      } catch (error) {
        packagedArticles.push({
          ...article,
          articleDir,
          status: "error",
          packagingError: error.message,
        });
      }
    }

    return {
      enabled: true,
      reason: "Article readers, copy packets, note JSON, and Anki packages were generated from the dedicated browser profile.",
      articles: packagedArticles,
      indexPath: writeReaderIndex(config),
    };
  } finally {
    await browser.close();
    await stopBrowserProcess(launched.child);
  }
}

module.exports = {
  articleDirName,
  captureArticlePackages,
};
