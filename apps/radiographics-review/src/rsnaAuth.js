const { normalizeWhitespace } = require("./utils");
const { loadStoredRsnaCredential } = require("./credentials");

const ACCESS_WALL_PATTERNS = [
  /\bget full access to this article\b/i,
  /\balready a subscriber\b/i,
  /\bsign in as an individual\b/i,
  /\bvia your institution\b/i,
  /\bavailable purchase options\b/i,
  /\baccess through your institution\b/i,
  /\bindividual access\b/i,
];

function looksLikeAccessWallText(text) {
  const value = normalizeWhitespace(String(text || ""));
  if (!value) {
    return false;
  }

  const matches = ACCESS_WALL_PATTERNS.filter((pattern) => pattern.test(value)).length;
  return matches >= 2 || /\bget full access to this article\b/i.test(value);
}

function looksLikeCloudflareChallenge(text) {
  return /\b(verify you are human|checking your browser|cloudflare)\b/i.test(String(text || ""));
}

async function readBodyText(page) {
  return normalizeWhitespace((await page.textContent("body").catch(() => "")) || "");
}

async function firstVisibleFromLocators(locators) {
  for (const locator of locators) {
    const count = await locator.count().catch(() => 0);
    for (let index = 0; index < count; index += 1) {
      const candidate = locator.nth(index);
      if (await candidate.isVisible().catch(() => false)) {
        return candidate;
      }
    }
  }

  return null;
}

async function fillFirstVisible(page, selectors, value) {
  const locator = await firstVisibleFromLocators(selectors.map((selector) => page.locator(selector)));
  if (!locator) {
    return false;
  }

  await locator.fill(value);
  return true;
}

async function clickFirstVisible(page, locatorFactories) {
  const locator = await firstVisibleFromLocators(locatorFactories.map((factory) => factory(page)));
  if (!locator) {
    return false;
  }

  await locator.click({ timeout: 5000 });
  return true;
}

async function attemptStoredRsnaLogin(page, config, articleLink) {
  const credential = loadStoredRsnaCredential(config);
  if (!credential?.username || !credential?.password) {
    return {
      attempted: false,
      success: false,
      reason: "Stored RSNA credential could not be loaded.",
    };
  }

  let bodyText = await readBodyText(page);
  if (looksLikeCloudflareChallenge(bodyText)) {
    return {
      attempted: false,
      success: false,
      reason:
        "Cloudflare challenge detected before login. Complete `npm run login` in the dedicated browser profile once to refresh the session.",
    };
  }

  if (!/login|signin/i.test(page.url())) {
    await clickFirstVisible(page, [
      (currentPage) => currentPage.getByRole("link", { name: /sign in|log in/i }),
      (currentPage) => currentPage.getByRole("button", { name: /sign in|log in/i }),
      (currentPage) => currentPage.locator('a[href*="login"], a[href*="signin"]'),
      (currentPage) => currentPage.locator('button:has-text("Sign In"), button:has-text("Log In")'),
    ]).catch(() => false);
    await page.waitForLoadState("domcontentloaded", { timeout: 20000 }).catch(() => {});
    await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  }

  bodyText = await readBodyText(page);
  if (looksLikeCloudflareChallenge(bodyText)) {
    return {
      attempted: true,
      success: false,
      reason:
        "Cloudflare challenge appeared before the RSNA form loaded. Complete `npm run login` manually once to refresh the browser profile.",
    };
  }

  const filledUsername = await fillFirstVisible(
    page,
    [
      'input[type="email"]',
      'input[name="email"]',
      'input[id="email"]',
      'input[name="username"]',
      'input[id="username"]',
      'input[name="user"]',
      'input[id="user"]',
      'input[type="text"][name="login"]',
    ],
    credential.username,
  );
  const filledPassword = await fillFirstVisible(
    page,
    [
      'input[type="password"]',
      'input[name="password"]',
      'input[id="password"]',
    ],
    credential.password,
  );

  if (!filledPassword) {
    return {
      attempted: true,
      success: false,
      reason:
        "Stored credentials are available, but the RSNA password field was not detected automatically.",
    };
  }

  await clickFirstVisible(page, [
    (currentPage) => currentPage.getByRole("button", { name: /sign in|log in|submit|continue/i }),
    (currentPage) => currentPage.locator('button[type="submit"]'),
    (currentPage) => currentPage.locator('input[type="submit"]'),
  ]).catch(async () => {
    await page.keyboard.press("Enter");
  });

  await page.waitForLoadState("domcontentloaded", { timeout: 20000 }).catch(() => {});
  await page.waitForLoadState("networkidle", { timeout: 20000 }).catch(() => {});

  await page.goto(articleLink, {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });
  await page.waitForLoadState("networkidle", { timeout: 20000 }).catch(() => {});

  bodyText = await readBodyText(page);
  if (looksLikeCloudflareChallenge(bodyText)) {
    return {
      attempted: true,
      success: false,
      reason:
        "Cloudflare challenge appeared after the stored RSNA credential was submitted. Manual refresh via `npm run login` is still required.",
    };
  }

  if (looksLikeAccessWallText(bodyText)) {
    return {
      attempted: true,
      success: false,
      reason:
        "Stored RSNA credential was submitted, but the article remained behind the access wall.",
    };
  }

  return {
    attempted: true,
    success: true,
    reason: filledUsername
      ? "Stored RSNA credential refreshed the article session."
      : "Stored RSNA password refreshed the article session.",
  };
}

async function ensureAuthenticatedArticleAccess(page, config, articleLink) {
  const bodyText = await readBodyText(page);
  if (looksLikeCloudflareChallenge(bodyText)) {
    return {
      attempted: false,
      success: false,
      reason:
        "Cloudflare challenge detected. Complete `npm run login` in the dedicated browser profile once to refresh the session.",
    };
  }

  if (!looksLikeAccessWallText(bodyText)) {
    return {
      attempted: false,
      success: true,
      reason: "Article body is already accessible.",
    };
  }

  try {
    return await attemptStoredRsnaLogin(page, config, articleLink);
  } catch (error) {
    return {
      attempted: true,
      success: false,
      reason: error.message,
    };
  }
}

module.exports = {
  ensureAuthenticatedArticleAccess,
  looksLikeAccessWallText,
  looksLikeCloudflareChallenge,
};
