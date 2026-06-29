const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const { buildAnkiPackage } = require("./anki");
const { ensureDirectories, getConfig } = require("./config");
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
const { readJson, slugify, writeJson } = require("./utils");

function parseArgs(argv) {
  const pdfs = [];
  for (const raw of argv) {
    if (!raw || raw.startsWith("-")) {
      continue;
    }
    pdfs.push(path.resolve(raw));
  }
  if (pdfs.length === 0) {
    throw new Error("Pass one or more PDF paths.");
  }
  return { pdfs };
}

function pythonExecutable() {
  return process.env.RADIOGRAPHICS_PDF_PYTHON || "py";
}

function pdftoppmExecutable() {
  return process.env.RADIOGRAPHICS_PDFTOPPM || "";
}

function runPythonExtraction(config, pdfPath) {
  const scriptPath = path.join(config.workspaceRoot, "scripts", "extract_pdf_article.py");
  const args = [
    scriptPath,
    "--pdf",
    pdfPath,
    "--articles-dir",
    config.articlesDir,
  ];
  const pdftoppm = pdftoppmExecutable();
  if (pdftoppm) {
    args.push("--pdftoppm", pdftoppm);
  }

  const result = spawnSync(pythonExecutable(), args, {
    cwd: config.workspaceRoot,
    encoding: "utf8",
    env: {
      ...process.env,
      PYTHONIOENCODING: "utf-8",
    },
  });

  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    throw new Error(result.stderr || result.stdout || `PDF extraction failed with exit code ${result.status}.`);
  }
  return JSON.parse(result.stdout);
}

function writeReaderIndex(config) {
  const articles = loadGeneratedArticles(config).map((article) => ({
    ...article,
    readerIndexPath: path.posix.join(
      "articles",
      path.basename(article.articleDir),
      "reader.html",
    ),
    thumbnailIndexPath: article.figures?.[0]?.relativeImagePath
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

async function packageExtractedArticle(config, extracted) {
  const articleDir = extracted.articleDir;
  const ankiDir = path.join(articleDir, "anki");
  fs.mkdirSync(ankiDir, { recursive: true });

  const cleanedBodyBlocks = (extracted.bodyBlocks || extracted.rawBodyBlocks || [])
    .map((block) => cleanProseBlock(block))
    .filter(Boolean);
  const figures = (extracted.figures || []).map((figure, index) => {
    const caption = cleanFigureCaption(figure.caption || figure.rawCaption || "");
    return {
      ...figure,
      label: figure.label || `Figure ${index + 1}`,
      caption,
      rawCaption: caption,
      anchor: slugify(figure.label || `Figure ${index + 1}`, 32),
      teachingPoint: buildTeachingPoint(caption),
    };
  });
  const generatedAt = new Date().toISOString();
  const articlePayload = {
    ...extracted,
    slug: slugify(extracted.title, 80),
    generatedAt,
    cleanedBodyBlocks,
    cleanedBodyText: cleanedBodyBlocks.join("\n\n"),
    bodyBlocks: cleanedBodyBlocks,
    bodyText: cleanedBodyBlocks.join("\n\n"),
    figures,
  };
  articlePayload.summarySections = buildSummarySections(articlePayload);
  articlePayload.keyFacts = buildKeyFacts(articlePayload);

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
  return articlePayload;
}

function updateState(config, importedArticles) {
  const previous = readJson(config.statePath, {});
  const outputDois = new Set([
    ...(previous.seenDois || []),
    ...loadGeneratedArticles(config).map((article) => article.doi).filter(Boolean),
    ...importedArticles.map((article) => article.doi).filter(Boolean),
  ]);
  writeJson(config.statePath, {
    ...previous,
    seenDois: Array.from(outputDois),
    processedDoisFromOutputs: Array.from(outputDois),
    lastRunAt: new Date().toISOString(),
  });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const config = getConfig();
  ensureDirectories(config);
  const importedArticles = [];

  for (const pdfPath of args.pdfs) {
    const extracted = runPythonExtraction(config, pdfPath);
    const article = await packageExtractedArticle(config, extracted);
    importedArticles.push(article);
    console.log(`Imported ${article.title}`);
    console.log(`Reader: ${article.readerPath}`);
    console.log(`Anki: ${article.ankiPackagePath}`);
  }

  const indexPath = writeReaderIndex(config);
  updateState(config, importedArticles);
  console.log(`Library index: ${indexPath}`);
  console.log(`Imported PDFs: ${importedArticles.length}`);
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});
