const { pickPublicationDate, stripHtml } = require("./utils");

function buildUserAgent(mailto) {
  return `RadiographicsReviewAutomation/0.1 (mailto:${mailto})`;
}

async function fetchRecentArticles(config, options = {}) {
  const rows = options.maxResults || config.defaultMaxResults;
  const lookbackDays = options.lookbackDays || config.defaultLookbackDays;
  const fromDate = new Date();
  fromDate.setUTCDate(fromDate.getUTCDate() - lookbackDays);

  const url = new URL(
    `https://api.crossref.org/journals/${config.crossrefIssn}/works`,
  );
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
    ].join(","),
  );
  url.searchParams.set("filter", `from-pub-date:${fromDate.toISOString().slice(0, 10)}`);
  url.searchParams.set("mailto", config.crossrefMailto);

  const response = await fetch(url, {
    headers: {
      "User-Agent": buildUserAgent(config.crossrefMailto),
    },
  });

  if (!response.ok) {
    throw new Error(`Crossref request failed with ${response.status} ${response.statusText}`);
  }

  const payload = await response.json();
  const items = payload?.message?.items || [];

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
    }))
    .sort((left, right) => {
      const leftTime = Date.parse(left.publishedAt || "") || 0;
      const rightTime = Date.parse(right.publishedAt || "") || 0;
      return rightTime - leftTime;
    });
}

module.exports = {
  fetchRecentArticles,
};
