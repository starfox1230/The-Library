const readline = require("node:readline/promises");
const { stdin, stdout } = require("node:process");
const { ensureDirectories, getConfig } = require("./config");
const {
  connectToBrowser,
  launchBrowserProcess,
  stopBrowserProcess,
} = require("./browserControl");

async function main() {
  const config = getConfig();
  ensureDirectories(config);

  const prompt = readline.createInterface({ input: stdin, output: stdout });
  const launched = launchBrowserProcess(config, {
    startMinimized: false,
    url: "https://pubs.rsna.org/journal/radiographics",
  });
  const browser = await connectToBrowser(config);

  try {
    console.log(`Opened ${launched.browser.name} with the dedicated local profile.`);
    console.log(
      `Profile path: ${config.browserProfileDir}`,
    );
    console.log(`Optional stored credential setup: npm run set-credentials`);
    console.log("1. Complete any Cloudflare challenge in that browser window.");
    console.log("2. Sign into RSNA there.");
    console.log("3. Open a RadioGraphics article page and confirm it loads normally.");
    console.log("4. Return here and press Enter. The session stays in that local browser profile.");

    await prompt.question("\nPress Enter after the login is complete. ");
    console.log(`Saved login state in ${config.browserProfileDir}`);
  } finally {
    prompt.close();
    await browser.close();
    await stopBrowserProcess(launched.child);
  }
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});
