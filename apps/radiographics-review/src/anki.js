const fs = require("node:fs");
const path = require("node:path");
const { spawn } = require("node:child_process");
const { slugify } = require("./utils");

function buildAnkiPackage(config, article) {
  return new Promise((resolve, reject) => {
    const packageSlug = slugify(article.title || article.doi || "article", 40);
    const outputPath = path.join(
      article.articleDir,
      "anki",
      `${slugify(article.doi || "rg", 24)}-${packageSlug}.apkg`,
    );
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    if (!article.ankiNotesPath) {
      reject(new Error("Missing article.ankiNotesPath before Anki package build."));
      return;
    }

    const pythonPath = process.env.PYTHONPATH
      ? `${config.pythonRuntimeDir}${path.delimiter}${process.env.PYTHONPATH}`
      : config.pythonRuntimeDir;
    const scriptPath = path.join(config.workspaceRoot, "scripts", "build_anki_package.py");
    const child = spawn(
      "py",
      [
        scriptPath,
        "--article-json",
        article.jsonPath,
        "--notes-json",
        article.ankiNotesPath,
        "--output",
        outputPath,
      ],
      {
        cwd: config.workspaceRoot,
        env: {
          ...process.env,
          PYTHONPATH: pythonPath,
        },
      },
    );

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("error", (error) => {
      reject(error);
    });
    child.on("close", (code) => {
      if (code !== 0) {
        reject(
          new Error(
            stderr.trim() || stdout.trim() || `Anki package build failed with exit code ${code}.`,
          ),
        );
        return;
      }

      resolve({
        packagePath: outputPath,
        log: stdout.trim(),
      });
    });
  });
}

module.exports = {
  buildAnkiPackage,
};
