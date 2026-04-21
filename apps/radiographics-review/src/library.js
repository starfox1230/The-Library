const fs = require("node:fs");
const path = require("node:path");
const { readJson } = require("./utils");

function isSuccessfulGeneratedArticle(article) {
  return Boolean(
    article &&
    article.readerPath &&
    fs.existsSync(article.readerPath) &&
    article.ankiPackagePath &&
    fs.existsSync(article.ankiPackagePath),
  );
}

function loadGeneratedArticles(config, options = {}) {
  if (!fs.existsSync(config.articlesDir)) {
    return [];
  }

  const articles = fs
    .readdirSync(config.articlesDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => path.join(config.articlesDir, entry.name))
    .map((articleDir) => readJson(path.join(articleDir, "article.json"), null))
    .filter(Boolean);

  const filtered = options.includePartial ? articles : articles.filter(isSuccessfulGeneratedArticle);

  return filtered
    .sort((left, right) => {
      const leftTime = Date.parse(left.publishedAt || "") || 0;
      const rightTime = Date.parse(right.publishedAt || "") || 0;
      return rightTime - leftTime;
    });
}

function loadProcessedDois(config) {
  return new Set(
    loadGeneratedArticles(config)
      .map((article) => article.doi)
      .filter(Boolean),
  );
}

module.exports = {
  loadGeneratedArticles,
  loadProcessedDois,
};
