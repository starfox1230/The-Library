const fs = require("node:fs");
const path = require("node:path");
const { ensureDirectories, getConfig } = require("./config");
const { fetchArticlesPage, fetchRecentArticles } = require("./crossref");
const { loadGeneratedArticles, loadProcessedDois } = require("./library");
const { formatDate, truncate, writeJson } = require("./utils");

function parseArgs(argv) {
  const args = {
    enrich: true,
    maxResults: 1,
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

  if (!args.maxResults || args.maxResults < 1) {
    args.maxResults = 1;
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
    lines.push("No new or backfill articles were selected in the current run.");
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

    if (article.copyChatPath) {
      lines.push(`- Copy packet: ${article.copyChatPath}`);
    }

    if (article.ankiNotesPath) {
      lines.push(`- Anki notes JSON: ${article.ankiNotesPath}`);
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

    if (article.cleanedBodyBlocks?.length) {
      lines.push(`- Prose sample: ${truncate(article.cleanedBodyBlocks[0], 280)}`);
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

function recentFromDate(config, overrideDays) {
  const lookbackDays = overrideDays || config.defaultLookbackDays;
  const fromDate = new Date();
  fromDate.setUTCDate(fromDate.getUTCDate() - lookbackDays);
  return fromDate.toISOString().slice(0, 10);
}

async function collectQueueArticles(config, options = {}) {
  const limit = options.maxResults || 1;
  const processedDois = options.includeSeen ? new Set() : loadProcessedDois(config);
  const reservedDois = new Set(processedDois);
  const selected = [];
  const recentScan = await fetchRecentArticles(config, {
    maxResults: config.defaultMaxResults,
    lookbackDays: options.lookbackDays,
  });
  const scannedCount = recentScan.length;

  async function searchPhase(searchOptions) {
    let cursor = "*";
    let pageCount = 0;

    while (selected.length < limit && pageCount < 200) {
      const page = await fetchArticlesPage(config, {
        rows: config.defaultMaxResults,
        cursor,
        fromDate: searchOptions.fromDate,
      });

      if (page.items.length === 0) {
        break;
      }

      for (const article of page.items) {
        if (reservedDois.has(article.doi)) {
          continue;
        }
        selected.push(article);
        reservedDois.add(article.doi);
        if (selected.length >= limit) {
          break;
        }
      }

      if (!page.nextCursor || page.nextCursor === cursor) {
        break;
      }

      cursor = page.nextCursor;
      pageCount += 1;
    }
  }

  await searchPhase({ fromDate: recentFromDate(config, options.lookbackDays) });

  if (selected.length < limit && !options.includeSeen) {
    await searchPhase({});
  }

  return {
    scannedCount,
    selected,
    processedDois: Array.from(processedDois),
  };
}

async function main() {
  const config = getConfig();
  ensureDirectories(config);

  const args = parseArgs(process.argv.slice(2));
  const generatedArticles = loadGeneratedArticles(config);
  const queue = await collectQueueArticles(config, {
    includeSeen: args.includeSeen,
    lookbackDays: args.lookbackDays,
    maxResults: args.maxResults,
  });

  let packaging;
  if (args.enrich) {
    const { captureArticlePackages } = require("./articlePipeline");
    packaging = await captureArticlePackages(config, queue.selected);
  } else {
    packaging = {
      enabled: false,
      reason: "Disabled with --no-enrich.",
      articles: queue.selected.map((article) => ({
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
    scannedCount: queue.scannedCount,
    newCount: packaging.articles.length,
    packagingSummary,
    indexPath: packaging.indexPath,
    newArticles: packaging.articles,
  });

  fs.writeFileSync(digestPath, `${digestBody}\n`, "utf8");

  const outputDois = new Set([
    ...generatedArticles.map((article) => article.doi).filter(Boolean),
    ...packaging.articles
      .filter((article) => article.status !== "error" && article.status !== "metadata-only")
      .map((article) => article.doi),
  ]);

  writeJson(config.statePath, {
    seenDois: [
      ...new Set([
        ...queue.processedDois,
        ...outputDois,
      ]),
    ],
    processedDoisFromOutputs: Array.from(outputDois),
    lastRunAt: now.toISOString(),
    lastDigestPath: digestPath,
  });

  console.log(`Wrote digest to ${digestPath}`);
  console.log(`Recent records scanned: ${queue.scannedCount}`);
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
