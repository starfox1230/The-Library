const { connectToBrowser, launchBrowserProcess, stopBrowserProcess } = require("./browserControl");
const { stripHtml, truncate, unique } = require("./utils");

async function extractPageData(page) {
  return page.evaluate(() => {
    function clean(text) {
      return (text || "").replace(/\s+/g, " ").trim();
    }

    function meta(name) {
      const byName = document.querySelector(`meta[name="${name}"]`);
      const byProperty = document.querySelector(`meta[property="${name}"]`);
      return byName?.content || byProperty?.content || "";
    }

    function textFromSelector(selector) {
      const node = document.querySelector(selector);
      return clean(node?.innerText || "");
    }

    function findAbstract() {
      const directSelectors = [
        '[data-title="Abstract"]',
        "#abstract",
        ".abstract",
        ".abstractSection",
        ".hlFld-Abstract",
        ".article__abstract",
      ];

      for (const selector of directSelectors) {
        const text = textFromSelector(selector);
        if (text) {
          return text;
        }
      }

      const sections = Array.from(document.querySelectorAll("section, div, article"));
      for (const section of sections) {
        const heading = clean(
          section.querySelector("h1, h2, h3, h4, .section__title, .article-section__title")
            ?.innerText || "",
        );
        if (/^abstract$/i.test(heading)) {
          const text = clean(section.innerText || "");
          if (text) {
            return text.replace(/^abstract\s*/i, "").trim();
          }
        }
      }

      return "";
    }

    const citationAuthors = Array.from(
      document.querySelectorAll('meta[name="citation_author"]'),
    )
      .map((node) => clean(node.content))
      .filter(Boolean);

    return {
      finalUrl: location.href,
      title:
        meta("citation_title") ||
        meta("og:title") ||
        clean(document.querySelector("h1")?.innerText || document.title || ""),
      abstract:
        meta("description") ||
        meta("citation_abstract_html_url") ||
        findAbstract(),
      pdfUrl: meta("citation_pdf_url"),
      authors: citationAuthors,
    };
  });
}

async function enrichArticles(config, articles) {
  if (articles.length === 0) {
    return {
      enabled: false,
      reason: "No articles required enrichment.",
      articles,
    };
  }

  const launched = launchBrowserProcess(config, {
    startMinimized: true,
    url: "about:blank",
  });
  const browser = await connectToBrowser(config);
  const context = browser.contexts()[0];

  try {
    const enriched = [];
    const page = context.pages()[0] || (await context.newPage());

    for (const article of articles) {
      try {
        await page.goto(article.link, {
          waitUntil: "domcontentloaded",
          timeout: 45000,
        });
        await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});

        const challengeText = (await page.textContent("body").catch(() => "")) || "";
        if (/verify you are human|checking your browser|cloudflare/i.test(challengeText)) {
          throw new Error(
            "Cloudflare challenge detected during enrichment. Re-run `npm run login` and complete the challenge in the dedicated browser profile.",
          );
        }

        const pageData = await extractPageData(page);
        enriched.push({
          ...article,
          link: pageData.finalUrl || article.link,
          title: stripHtml(pageData.title || article.title),
          abstract: truncate(stripHtml(pageData.abstract), 1200),
          pdfUrl: pageData.pdfUrl || "",
          authors: unique([...(pageData.authors || []), ...article.authors]),
        });
      } catch (error) {
        enriched.push({
          ...article,
          enrichmentError: error.message,
        });
      }
    }

    return {
      enabled: true,
      reason: `Browser enrichment attempted with the dedicated local browser profile.`,
      articles: enriched,
    };
  } finally {
    await browser.close();
    await stopBrowserProcess(launched.child);
  }
}

module.exports = {
  enrichArticles,
};
