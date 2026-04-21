const { pickPublicationDate, stripHtml } = require("./utils");

function buildUserAgent(mailto) {
  return `RadiographicsReviewAutomation/0.1 (mailto:${mailto})`;
}

function mapCrossrefItems(items) {
  return items
    .filter((item) => item.type === "journal-article" && item.DOI)
    .map((item) => ({
      doi: item.DOI,
      title: stripHtml(item.title?.[0] || ""),
      link: item.URL || `https://doi.org/${item.DOI}`,
      publishedAt: pickPublicationDate(item),
      authors: (item.author || []).map((author) =>
        [author.given, author.family].filter(Boolean).join(" ").trim(),
      ),
      journal: item["container-title"]?.[0] || "RadioGraphics",
      volume: item.volume || "",
      issue: item.issue || "",
      pages: item.page || "",
      citationCount: Number.parseInt(item["is-referenced-by-count"] || 0, 10) || 0,
    }))
    .sort((left, right) => {
      const leftTime = Date.parse(left.publishedAt || "") || 0;
      const rightTime = Date.parse(right.publishedAt || "") || 0;
      return rightTime - leftTime;
    });
}

async function fetchArticlesPage(config, options = {}) {
  const rows = options.rows || config.defaultMaxResults;
  const url = new URL(`https://api.crossref.org/journals/${config.crossrefIssn}/works`);

  url.searchParams.set("rows", String(rows));
  url.searchParams.set("sort", "published");
  url.searchParams.set("order", "desc");
  url.searchParams.set(
    "select",
    [
      "DOI",
      "URL",
      "title",
      "author",
      "container-title",
      "published-print",
      "published-online",
      "issued",
      "created",
      "deposited",
      "volume",
      "issue",
      "page",
      "type",
      "is-referenced-by-count",
    ].join(","),
  );
  url.searchParams.set("mailto", config.crossrefMailto);
  url.searchParams.set("cursor", options.cursor || "*");

  if (options.fromDate) {
    url.searchParams.set("filter", `from-pub-date:${options.fromDate}`);
  }

  const response = await fetch(url, {
    headers: {
      "User-Agent": buildUserAgent(config.crossrefMailto),
    },
  });

  if (!response.ok) {
    throw new Error(`Crossref request failed with ${response.status} ${response.statusText}`);
  }

  const payload = await response.json();
  return {
    items: mapCrossrefItems(payload?.message?.items || []),
    nextCursor: payload?.message?.["next-cursor"] || "",
  };
}

async function fetchRecentArticles(config, options = {}) {
  const lookbackDays = options.lookbackDays || config.defaultLookbackDays;
  const fromDate = new Date();
  fromDate.setUTCDate(fromDate.getUTCDate() - lookbackDays);

  const page = await fetchArticlesPage(config, {
    rows: options.maxResults || config.defaultMaxResults,
    fromDate: fromDate.toISOString().slice(0, 10),
  });

  return page.items;
}

module.exports = {
  fetchArticlesPage,
  fetchRecentArticles,
};
