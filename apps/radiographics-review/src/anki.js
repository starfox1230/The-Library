const fs = require("node:fs");
const path = require("node:path");
const { spawn } = require("node:child_process");

function buildAnkiPackage(config, article) {
  return new Promise((resolve, reject) => {
    const outputPath = path.join(article.articleDir, "anki", `${article.slug}.apkg`);
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });

    const pythonPath = process.env.PYTHONPATH
      ? `${config.pythonRuntimeDir}${path.delimiter}${process.env.PYTHONPATH}`
      : config.pythonRuntimeDir;
    const scriptPath = path.join(config.workspaceRoot, "scripts", "build_anki_package.py");
    const child = spawn(
      "py",
      [scriptPath, "--article-json", article.jsonPath, "--output", outputPath],
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
