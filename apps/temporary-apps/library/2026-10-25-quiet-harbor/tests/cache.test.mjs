import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, statSync } from "node:fs";
import { createHash } from "node:crypto";

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
