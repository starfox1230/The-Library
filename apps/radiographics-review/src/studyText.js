const { formatDate, normalizeWhitespace, stripHtml } = require("./utils");

function stripInlineCitations(text) {
  return (text || "").replace(/\s*\(\d+(?:\s*[-,\u2013]\s*\d+)*\)/g, "");
}

function removeUiBoilerplate(text) {
  return (text || "")
    .replace(/\bOPEN IN VIEWER\b/gi, "")
    .replace(/\bDownload as PowerPoint\b/gi, "")
    .replace(/\bView all available purchase options\b/gi, "")
    .replace(/\bTo read the full-text\b/gi, "");
}

function cleanStudyText(text) {
  return normalizeWhitespace(
    stripInlineCitations(
      removeUiBoilerplate(stripHtml(text || ""))
        .replace(/\s+\((?:Fig(?:ure)?|Table)\s*[A-Za-z0-9.\- ]+\)/gi, "")
        .replace(/\s+/g, " "),
    ),
  ).trim();
}

function cleanProseBlock(text) {
  return cleanStudyText(text);
}

function cleanFigureCaption(text) {
  return normalizeWhitespace(
    stripInlineCitations(
      removeUiBoilerplate(stripHtml(text || ""))
        .replace(/\s+/g, " "),
    ),
  ).trim();
}

function buildArticleMetadataLine(article) {
  return [
    article.journal || "RadioGraphics",
    formatDate(article.publishedAt) || "Unknown date",
    article.volume ? `Vol ${article.volume}` : "",
    article.issue ? `Issue ${article.issue}` : "",
    article.pages ? `Pages ${article.pages}` : "",
  ].filter(Boolean).join(" | ");
}

function buildCopyForChatText(article) {
  const proseBlocks = article.cleanedBodyBlocks || article.bodyBlocks || [];
  const lines = [
    article.title || "Untitled article",
    buildArticleMetadataLine(article),
    `DOI: ${article.doi || "Unknown DOI"}`,
    `RadioGraphics URL: ${article.link || ""}`,
    "",
  ];

  if (article.authors?.length) {
    lines.push(`Authors: ${article.authors.join(", ")}`);
    lines.push("");
  }

  lines.push("ARTICLE PROSE");
  lines.push("");
  for (const block of proseBlocks) {
    lines.push(block);
    lines.push("");
  }

  lines.push("FIGURE CAPTIONS");
  lines.push("");
  for (const [index, figure] of (article.figures || []).entries()) {
    lines.push(`${index + 1}. ${figure.caption || figure.rawCaption || ""}`.trim());
    lines.push("");
  }

  return `${lines.join("\n").trim()}\n`;
}

module.exports = {
  buildArticleMetadataLine,
  buildCopyForChatText,
  cleanFigureCaption,
  cleanProseBlock,
  cleanStudyText,
  stripInlineCitations,
};
