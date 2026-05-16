import { promises as fs } from "fs";
import path from "path";
import { fileURLToPath } from "url";
import sharp from "sharp";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BUILDER_DIR = path.resolve(__dirname, "..");
const GAME_DIR = path.resolve(BUILDER_DIR, "../library/2026-05-08-which-one-is-it");
const DATA_FILE = path.join(GAME_DIR, "data/pairs.json");
const MIN_SIDE = Number(process.env.WHICH_ONE_MIN_IMAGE_SIDE || 300);
const TARGET_SIDE = Number(process.env.WHICH_ONE_TARGET_IMAGE_SIDE || 500);
const REQUEST_DELAY_MS = Number(process.env.WHICH_ONE_IMAGE_DELAY_MS || 300);
const DOWNLOAD_TIMEOUT_MS = Number(process.env.WHICH_ONE_IMAGE_DOWNLOAD_TIMEOUT_MS || 18000);
const USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36";

const queryOverrides = new Map(Object.entries({
  squirrel: "tree squirrel animal photo",
  flying_squirrel: "flying squirrel animal photo",
  sugar_glider: "sugar glider animal photo",
  turtle: "turtle animal photo",
  tortoise: "tortoise animal photo",
  frog: "frog animal photo",
  toad: "toad animal photo",
  crocodile: "crocodile animal photo",
  alligator: "alligator animal photo",
  dolphin: "dolphin animal photo",
  porpoise: "porpoise animal photo",
  beluga: "beluga whale photo",
  seal: "seal animal photo",
  sea_lion: "sea lion animal photo",
  rabbit: "rabbit animal photo",
  hare: "hare animal photo",
  bee: "bee insect photo",
  wasp: "wasp insect photo",
  butterfly: "butterfly insect photo",
  moth: "moth insect photo",
  cheetah: "cheetah animal photo",
  leopard: "leopard animal photo",
  jaguar: "jaguar animal photo",
  octopus: "octopus animal photo",
  squid: "squid animal photo",
  truck: "truck vehicle photo",
  van: "van vehicle photo",
  shell: "seashell photo",
  rib: "simple rib bone anatomy drawing",
  spine: "simple spine anatomy drawing",
  toe: "toe body part photo",
  finger: "finger body part photo",
  b: "lowercase letter b alphabet card",
  d: "lowercase letter d alphabet card",
  p: "lowercase letter p alphabet card",
  q: "lowercase letter q alphabet card",
  m: "lowercase letter m alphabet card",
  w: "lowercase letter w alphabet card",
  "2": "number 2 digit card",
  "5": "number 5 digit card",
  "6": "number 6 digit card",
  "9": "number 9 digit card"
}));

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function sideKey(side) {
  return side === "A" ? "imagesA" : "imagesB";
}

function sideLabel(pair, side) {
  return side === "A" ? pair.labelA : pair.labelB;
}

function absPath(rel) {
  return path.join(GAME_DIR, rel);
}

function relPath(abs) {
  return path.relative(GAME_DIR, abs).replaceAll("\\", "/");
}

function imageQuery(label) {
  return queryOverrides.get(label) || `${label.replaceAll("_", " ")} photo`;
}

async function imageMeta(rel) {
  const meta = await sharp(absPath(rel)).metadata();
  const width = meta.width || 0;
  const height = meta.height || 0;
  return { width, height, minSide: Math.min(width, height), pixels: width * height };
}

async function imageFingerprint(rel) {
  const raw = await sharp(absPath(rel)).resize(16, 16, { fit: "fill" }).greyscale().raw().toBuffer();
  return Array.from(raw, (value) => Math.round(value / 24)).join(",");
}

function hammingLike(a, b) {
  const aa = a.split(",");
  const bb = b.split(",");
  let diff = 0;
  for (let i = 0; i < Math.min(aa.length, bb.length); i += 1) {
    if (aa[i] !== bb[i]) diff += 1;
  }
  return diff;
}

async function getVqd(query) {
  const html = await fetch(`https://duckduckgo.com/?q=${encodeURIComponent(query)}&iax=images&ia=images`, {
    headers: { "User-Agent": USER_AGENT }
  }).then((response) => response.text());
  const match = html.match(/vqd="([^"]+)"/) || html.match(/'vqd':'([^']+)'/) || html.match(/vqd=([\d-]+)&/);
  if (!match) throw new Error(`Could not get image token for ${query}`);
  return match[1];
}

async function searchDuckDuckGo(query) {
  const vqd = await getVqd(query);
  const url = `https://duckduckgo.com/i.js?l=us-en&o=json&q=${encodeURIComponent(query)}&vqd=${encodeURIComponent(vqd)}&f=,,,&p=1`;
  const response = await fetch(url, {
    headers: { "User-Agent": USER_AGENT, Referer: "https://duckduckgo.com/" }
  });
  if (!response.ok) throw new Error(`image search failed ${response.status} for ${query}`);
  const data = await response.json();
  return data.results || [];
}

async function searchOpenverse(query) {
  const params = new URLSearchParams({
    q: query,
    page_size: "40",
    mature: "false",
    unstable__include_sensitive_results: "false"
  });
  const response = await fetch(`https://api.openverse.org/v1/images/?${params}`, {
    headers: { "User-Agent": "WhichOneIsItEducationalBuilder/1.0" }
  });
  if (!response.ok) throw new Error(`Openverse search failed ${response.status} for ${query}`);
  const data = await response.json();
  return (data.results || []).map((item) => ({ image: item.url, thumbnail: item.thumbnail }));
}

async function searchImages(query) {
  try {
    return await searchDuckDuckGo(query);
  } catch {
    return searchOpenverse(query);
  }
}

async function downloadBuffer(url) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DOWNLOAD_TIMEOUT_MS);
  try {
    const response = await fetch(url, { signal: controller.signal, headers: { "User-Agent": USER_AGENT } });
    if (!response.ok) throw new Error(`download failed ${response.status}`);
    return Buffer.from(await response.arrayBuffer());
  } finally {
    clearTimeout(timeout);
  }
}

async function nextFilePath(pair, side) {
  const label = sideLabel(pair, side);
  const dir = path.join(GAME_DIR, "images", pair.id, label);
  await fs.mkdir(dir, { recursive: true });
  const files = await fs.readdir(dir).catch(() => []);
  const next = files
    .map((name) => Number((name.match(/_(\d+)\.webp$/) || [])[1] || 0))
    .reduce((max, n) => Math.max(max, n), 0) + 1;
  return path.join(dir, `${label}_${String(next).padStart(3, "0")}.webp`);
}

async function saveCandidate(buffer, outPath) {
  await sharp(buffer)
    .rotate()
    .resize({ width: 1400, height: 1000, fit: "inside", withoutEnlargement: true })
    .webp({ quality: 86 })
    .toFile(outPath);
}

async function replacementFor(pair, side, existingFingerprints) {
  const label = sideLabel(pair, side);
  const results = await searchImages(imageQuery(label));
  for (const result of results) {
    const urls = [result.image, result.url, result.thumbnail].filter(Boolean);
    for (const url of urls) {
      let outPath;
      try {
        await sleep(REQUEST_DELAY_MS);
        const buffer = await downloadBuffer(url);
        outPath = await nextFilePath(pair, side);
        await saveCandidate(buffer, outPath);
        const rel = relPath(outPath);
        const meta = await imageMeta(rel);
        if (meta.minSide < TARGET_SIDE) {
          await fs.rm(outPath, { force: true });
          continue;
        }
        const fingerprint = await imageFingerprint(rel);
        if (existingFingerprints.some((existing) => hammingLike(existing, fingerprint) <= 18)) {
          await fs.rm(outPath, { force: true });
          continue;
        }
        return rel;
      } catch {
        if (outPath) await fs.rm(outPath, { force: true }).catch(() => {});
      }
    }
  }
  return null;
}

const pairs = JSON.parse(await fs.readFile(DATA_FILE, "utf8"));
const replacements = [];
const failures = [];

for (const pair of pairs) {
  for (const side of ["A", "B"]) {
    const key = sideKey(side);
    pair[key] = Array.isArray(pair[key]) ? pair[key] : [];
    const lowRes = [];
    for (const rel of pair[key]) {
      try {
        const meta = await imageMeta(rel);
        if (meta.minSide < MIN_SIDE) lowRes.push({ rel, meta });
      } catch {
        lowRes.push({ rel, meta: { minSide: 0 } });
      }
    }
    if (!lowRes.length) continue;

    const existingFingerprints = [];
    for (const rel of pair[key]) {
      if (lowRes.some((item) => item.rel === rel)) continue;
      try {
        existingFingerprints.push(await imageFingerprint(rel));
      } catch {}
    }

    for (const item of lowRes) {
      const replacement = await replacementFor(pair, side, existingFingerprints);
      if (!replacement) {
        failures.push(`${item.rel} (${item.meta.minSide}px)`);
        continue;
      }
      const index = pair[key].indexOf(item.rel);
      if (index >= 0) pair[key][index] = replacement;
      await fs.rm(absPath(item.rel), { force: true }).catch(() => {});
      existingFingerprints.push(await imageFingerprint(replacement));
      replacements.push(`${item.rel} -> ${replacement}`);
      await fs.writeFile(DATA_FILE, `${JSON.stringify(pairs, null, 2)}\n`, "utf8");
      console.log(`${item.rel} -> ${replacement}`);
    }
  }
}

await fs.writeFile(DATA_FILE, `${JSON.stringify(pairs, null, 2)}\n`, "utf8");
console.log(`Replaced ${replacements.length} image(s).`);
if (failures.length) {
  console.log("Could not replace:");
  for (const failure of failures) console.log(`- ${failure}`);
}
