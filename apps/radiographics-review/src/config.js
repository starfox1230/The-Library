const fs = require("node:fs");
const path = require("node:path");

function getLocalAppData() {
  return (
    process.env.LOCALAPPDATA ||
    path.join(process.env.USERPROFILE || process.cwd(), "AppData", "Local")
  );
}

function getConfig() {
  const workspaceRoot = process.cwd();
  const dataDir = path.join(workspaceRoot, "data");
  const digestDir = path.join(workspaceRoot, "digests");
  const articlesDir = path.join(workspaceRoot, "articles");
  const statePath = path.join(dataDir, "review-state.json");
  const localStateRoot =
    process.env.RADIOGRAPHICS_LOCAL_STATE_DIR ||
    path.join(getLocalAppData(), "RadiographicsReview");

  return {
    workspaceRoot,
    dataDir,
    digestDir,
    articlesDir,
    statePath,
    localStateRoot,
    runtimeDir:
      process.env.RADIOGRAPHICS_RUNTIME_DIR ||
      path.join(localStateRoot, "runtime"),
    pythonRuntimeDir:
      process.env.RADIOGRAPHICS_PYTHON_RUNTIME_DIR ||
      path.join(localStateRoot, "python-runtime"),
    browserProfileDir:
      process.env.RADIOGRAPHICS_BROWSER_PROFILE_DIR ||
      path.join(localStateRoot, "browser-profile"),
    remoteDebuggingPort: Number.parseInt(
      process.env.RADIOGRAPHICS_DEBUG_PORT || "9333",
      10,
    ),
    crossrefIssn: "15271323",
    crossrefMailto: process.env.CROSSREF_MAILTO || "local@example.invalid",
    defaultLookbackDays: Number.parseInt(
      process.env.RADIOGRAPHICS_LOOKBACK_DAYS || "120",
      10,
    ),
    defaultMaxResults: Number.parseInt(
      process.env.RADIOGRAPHICS_MAX_RESULTS || "50",
      10,
    ),
    defaultAnkiFigureLimit: Number.parseInt(
      process.env.RADIOGRAPHICS_ANKI_FIGURE_LIMIT || "6",
      10,
    ),
  };
}

function ensureDirectories(config) {
  for (const dir of [
    config.dataDir,
    config.digestDir,
    config.articlesDir,
    config.localStateRoot,
    config.browserProfileDir,
  ]) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

module.exports = {
  ensureDirectories,
  getConfig,
  getLocalAppData,
};
