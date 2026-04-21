const fs = require("node:fs");
const path = require("node:path");
const { spawn } = require("node:child_process");
const { getPlaywright } = require("./runtime");

function browserCandidates() {
  const localAppData = process.env.LOCALAPPDATA || "";
  const programFiles = process.env.ProgramFiles || "C:\\Program Files";
  const programFilesX86 =
    process.env["ProgramFiles(x86)"] || "C:\\Program Files (x86)";

  return [
    {
      name: "Chrome",
      executablePath: path.join(
        localAppData,
        "Google",
        "Chrome",
        "Application",
        "chrome.exe",
      ),
    },
    {
      name: "Chrome",
      executablePath: path.join(
        programFiles,
        "Google",
        "Chrome",
        "Application",
        "chrome.exe",
      ),
    },
    {
      name: "Chrome",
      executablePath: path.join(
        programFilesX86,
        "Google",
        "Chrome",
        "Application",
        "chrome.exe",
      ),
    },
    {
      name: "Edge",
      executablePath: path.join(
        localAppData,
        "Microsoft",
        "Edge",
        "Application",
        "msedge.exe",
      ),
    },
    {
      name: "Edge",
      executablePath: path.join(
        programFiles,
        "Microsoft",
        "Edge",
        "Application",
        "msedge.exe",
      ),
    },
    {
      name: "Edge",
      executablePath: path.join(
        programFilesX86,
        "Microsoft",
        "Edge",
        "Application",
        "msedge.exe",
      ),
    },
  ];
}

function findBrowserExecutable() {
  const override = process.env.RADIOGRAPHICS_BROWSER_PATH;
  if (override && fs.existsSync(override)) {
    return {
      name: path.basename(override),
      executablePath: override,
    };
  }

  for (const candidate of browserCandidates()) {
    if (fs.existsSync(candidate.executablePath)) {
      return candidate;
    }
  }

  throw new Error(
    [
      "Chrome or Edge was not found.",
      "Set RADIOGRAPHICS_BROWSER_PATH to the browser executable if needed.",
    ].join(" "),
  );
}

function browserArgs(config, options = {}) {
  const args = [
    `--remote-debugging-port=${config.remoteDebuggingPort}`,
    `--user-data-dir=${config.browserProfileDir}`,
    "--no-first-run",
    "--no-default-browser-check",
    "--new-window",
  ];

  if (options.startMinimized) {
    args.push("--start-minimized");
  }

  if (options.url) {
    args.push(options.url);
  }

  return args;
}

function delay(milliseconds) {
  return new Promise((resolve) => {
    setTimeout(resolve, milliseconds);
  });
}

async function waitForDebugEndpoint(port, timeoutMs = 20000) {
  const deadline = Date.now() + timeoutMs;
  const url = `http://127.0.0.1:${port}/json/version`;
  let lastError = null;

  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      lastError = error;
    }

    await delay(250);
  }

  throw lastError || new Error(`Timed out waiting for browser debug endpoint on ${url}.`);
}

function launchBrowserProcess(config, options = {}) {
  const browser = findBrowserExecutable();
  const child = spawn(browser.executablePath, browserArgs(config, options), {
    stdio: "ignore",
    windowsHide: false,
  });

  child.unref();

  return {
    browser,
    child,
  };
}

async function connectToBrowser(config) {
  const { chromium } = getPlaywright();
  await waitForDebugEndpoint(config.remoteDebuggingPort);
  return chromium.connectOverCDP(`http://127.0.0.1:${config.remoteDebuggingPort}`);
}

async function stopBrowserProcess(child) {
  if (!child || child.exitCode !== null || child.killed) {
    return;
  }

  child.kill();
  await delay(500);
}

module.exports = {
  connectToBrowser,
  findBrowserExecutable,
  launchBrowserProcess,
  stopBrowserProcess,
};
