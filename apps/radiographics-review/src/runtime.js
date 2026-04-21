const path = require("node:path");
const { createRequire } = require("node:module");
const { getConfig } = require("./config");

function getRuntimeRequire() {
  const config = getConfig();
  const entryPoint = path.join(config.runtimeDir, "package.json");
  return createRequire(entryPoint);
}

function getPlaywright() {
  try {
    return getRuntimeRequire()("playwright-core");
  } catch (error) {
    const config = getConfig();
    throw new Error(
      [
        `playwright-core is not installed in ${config.runtimeDir}.`,
        "Run: powershell -ExecutionPolicy Bypass -File .\\scripts\\install-runtime.ps1",
      ].join(" "),
    );
  }
}

module.exports = {
  getPlaywright,
};
