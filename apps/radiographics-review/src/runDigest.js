const fs = require("node:fs");
const path = require("node:path");
const { ensureDirectories, getConfig } = require("./config");
const { fetchRecentArticles } = require("./crossref");
const { formatDate, readJson, truncate, writeJson } = require("./utils");

function parseArgs(argv) {
  const args = {
    enrich: true,
    maxResults: undefined,
    lookbackDays: undefined,
    includeSeen: false,
  };

  for (const raw of argv) {
    if (raw === "--no-enrich") {
      args.enrich = false;
      continue;
    }

    if (raw === "--include-seen") {
      args.includeSeen = true;
      continue;
    }

    if (raw.startsWith("--limit=")) {
      args.maxResults = Number.parseInt(raw.split("=")[1], 10);
      continue;
    }

    if (raw.startsWith("--lookback-days=")) {
      args.lookbackDays = Number.parseInt(raw.split("=")[1], 10);
    }
  }

  return args;
}

function localDateStamp(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function buildDigestMarkdown(metadata) {
  const lines = [
    `# RadioGraphics Digest - ${metadata.generatedAtLocal}`,
    "",
    `- Recent records scanned: ${metadata.scannedCount}`,
    `- Articles packaged: ${metadata.newCount}`,
    `- Packaging run: ${metadata.packagingSummary}`,
    "",
  ];

  if (metadata.newArticles.length === 0) {
    lines.push("No new articles were detected in the current lookback window.");
    if (metadata.indexPath) {
      lines.push(`Library index: ${metadata.indexPath}`);
    }
    lines.push("");
    return lines.join("\n");
  }

  metadata.newArticles.forEach((article, index) => {
    lines.push(`## ${index + 1}. ${article.title || article.doi}`);
    lines.push("");
    lines.push(`- Status: ${article.status || "unknown"}`);
    lines.push(`- Published: ${formatDate(article.publishedAt) || "Unknown"}`);
    lines.push(`- DOI: \`${article.doi}\``);
    lines.push(`- Link: ${article.link}`);

    if (article.readerPath) {
      lines.push(`- Reader: ${article.readerPath}`);
    }

    if (article.ankiPackagePath) {
      lines.push(`- Anki package: ${article.ankiPackagePath}`);
    }

    if (article.pdfUrl) {
      lines.push(`- PDF: ${article.pdfUrl}`);
    }

    if (article.volume || article.issue || article.pages) {
      const citationBits = [];
      if (article.volume) {
        citationBits.push(`vol. ${article.volume}`);
      }
      if (article.issue) {
        citationBits.push(`issue ${article.issue}`);
      }
      if (article.pages) {
        citationBits.push(`pages ${article.pages}`);
      }
      lines.push(`- Citation: ${citationBits.join(", ")}`);
    }

    if (article.authors?.length) {
      const displayAuthors =
        article.authors.length > 6
          ? `${article.authors.slice(0, 6).join(", ")}, et al.`
          : article.authors.join(", ");
      lines.push(`- Authors: ${displayAuthors}`);
    }

    if (article.abstract) {
      lines.push(`- Abstract: ${truncate(article.abstract, 900)}`);
    }

    if (article.keyFacts?.length) {
      lines.push(`- Key facts: ${article.keyFacts.slice(0, 3).join(" | ")}`);
    }

    if (article.packagingError) {
      lines.push(`- Packaging note: ${article.packagingError}`);
    }

    lines.push("");
  });

  if (metadata.indexPath) {
    lines.push(`Library index: ${metadata.indexPath}`);
    lines.push("");
  }

  return lines.join("\n");
}

async function main() {
  const config = getConfig();
  ensureDirectories(config);

  const args = parseArgs(process.argv.slice(2));
  const state = readJson(config.statePath, {
    seenDois: [],
    lastRunAt: null,
    lastDigestPath: null,
  });
  const seenDois = new Set(state.seenDois || []);

  const recentArticles = await fetchRecentArticles(config, {
    maxResults: args.maxResults,
    lookbackDays: args.lookbackDays,
  });
  const candidateArticles = args.includeSeen
    ? recentArticles
    : recentArticles.filter((article) => !seenDois.has(article.doi));

  let packaging;
  if (args.enrich) {
    const { captureArticlePackages } = require("./articlePipeline");
    packaging = await captureArticlePackages(config, candidateArticles);
  } else {
    packaging = {
      enabled: false,
      reason: "Disabled with --no-enrich.",
      articles: candidateArticles.map((article) => ({
        ...article,
        status: "metadata-only",
      })),
      indexPath: path.join(config.articlesDir, "index.html"),
    };
  }

  const now = new Date();
  const digestFileName = `${localDateStamp(now)}-radiographics-digest.md`;
  const digestPath = path.join(config.digestDir, digestFileName);
  const localTimestamp = new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  }).format(now);
  const packagingSummary = packaging.enabled ? packaging.reason : `Skipped. ${packaging.reason}`;

  const digestBody = buildDigestMarkdown({
    generatedAtLocal: localTimestamp,
    scannedCount: recentArticles.length,
    newCount: packaging.articles.length,
    packagingSummary,
    indexPath: packaging.indexPath,
    newArticles: packaging.articles,
  });

  fs.writeFileSync(digestPath, `${digestBody}\n`, "utf8");

  const processedDois = packaging.articles
    .filter((article) => article.status !== "error" && article.status !== "metadata-only")
    .map((article) => article.doi);

  writeJson(config.statePath, {
    seenDois: Array.from(new Set([...(state.seenDois || []), ...processedDois])),
    lastRunAt: now.toISOString(),
    lastDigestPath: digestPath,
  });

  console.log(`Wrote digest to ${digestPath}`);
  console.log(`Recent records scanned: ${recentArticles.length}`);
  console.log(`Articles packaged: ${packaging.articles.length}`);
  console.log(`Packaging run: ${packagingSummary}`);
  if (packaging.indexPath) {
    console.log(`Library index: ${packaging.indexPath}`);
  }
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});
