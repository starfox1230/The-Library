import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, statSync } from "node:fs";
import { createHash } from "node:crypto";
import { runInNewContext } from "node:vm";

test("the offline cache revision matches all shipped runtime files", () => {
  const root = new URL("../", import.meta.url);
  const manifest = readFileSync(new URL("precache-manifest.js", root), "utf8");
  const revision = manifest.match(/QUIET_HARBOR_REVISION = "([a-f0-9]+)"/)[1];
  const assets = JSON.parse(manifest.match(/QUIET_HARBOR_ASSETS = ([\s\S]*);/)[1]);
  const hash = createHash("sha256");
  for (const name of assets) {
    const file = new URL(name, root);
    if (statSync(file).isFile()) {
      const bytes = readFileSync(file);
      const content = /\.(js|json|html|css|svg|webmanifest)$/.test(name) ? bytes.toString("utf8").replace(/\r\n/g, "\n") : bytes;
      hash.update(name).update(content);
    }
  }
  assert.equal(revision, hash.digest("hex").slice(0, 16), "run python scripts/generate-precache.py after runtime changes");
  const worker = readFileSync(new URL("sw.js", root), "utf8");
  assert.ok(worker.includes("quiet-harbor-assets-${self.QUIET_HARBOR_REVISION}"));
});

test("a Home Screen app keeps its document and cached modules on the same release", async () => {
  const handlers = new Map();
  let networkRequests = 0;
  let installed = [];
  const scope = "https://example.test/quiet-harbor/";
  const cache = {
    match: async (request) => request.url === scope ? new Response("matching cached app document") : undefined,
    put: async () => {},
    addAll: async (requests) => { installed = requests; },
  };
  const self = { QUIET_HARBOR_REVISION: "test", QUIET_HARBOR_ASSETS: ["./index.html", "./app.js"], registration: { scope }, addEventListener: (name, fn) => handlers.set(name, fn) };
  runInNewContext(readFileSync(new URL("../sw.js", import.meta.url), "utf8"), {
    self, URL, Request, importScripts() {}, caches: { open: async () => cache },
    fetch: async () => { networkRequests++; return new Response("fresh review document"); },
  });
  let installation;
  handlers.get("install")({ waitUntil: (promise) => { installation = promise; } });
  await installation;
  assert.deepEqual(installed.map((request) => request.url), [scope + "index.html", scope + "app.js"]);
  assert.ok(installed.every((request) => request.cache === "reload"), "new revisions must not install stale HTTP-cache files");
  let response;
  handlers.get("fetch")({ request: { method: "GET", mode: "navigate", url: scope }, respondWith: (promise) => { response = promise; } });
  assert.equal(await (await response).text(), "matching cached app document");
  assert.equal(networkRequests, 0);
  handlers.get("fetch")({ request: { method: "GET", mode: "navigate", url: scope + "tests/landmark-review.html" }, respondWith: (promise) => { response = promise; } });
  assert.equal(await (await response).text(), "fresh review document");
  assert.equal(networkRequests, 1);
});
