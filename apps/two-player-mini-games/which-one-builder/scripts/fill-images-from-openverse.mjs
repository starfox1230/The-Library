import { promises as fs } from "fs";
import path from "path";
import { fileURLToPath } from "url";
import sharp from "sharp";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BUILDER_DIR = path.resolve(__dirname, "..");
const GAME_DIR = path.resolve(BUILDER_DIR, "../library/2026-05-08-which-one-is-it");
const DATA_FILE = path.join(GAME_DIR, "data/pairs.json");
const TARGET_COUNT = Number(process.env.WHICH_ONE_IMAGE_TARGET || 4);
const REQUEST_DELAY_MS = Number(process.env.WHICH_ONE_IMAGE_DELAY_MS || 350);
const DOWNLOAD_TIMEOUT_MS = Number(process.env.WHICH_ONE_IMAGE_DOWNLOAD_TIMEOUT_MS || 20000);

const queryOverrides = new Map(Object.entries({
  squirrel: "tree squirrel animal",
  turtle: "turtle animal",
  tortoise: "tortoise animal",
  frog: "frog animal",
  toad: "toad animal",
  crocodile: "crocodile animal",
  alligator: "alligator animal",
  dolphin: "dolphin animal",
  porpoise: "porpoise animal",
  beluga: "beluga whale",
  seal: "seal animal",
  sea_lion: "sea lion animal",
  rabbit: "rabbit animal",
  hare: "hare animal",
  bee: "bee insect",
  wasp: "wasp insect",
  butterfly: "butterfly insect",
  moth: "moth insect",
  cheetah: "cheetah animal",
  leopard: "leopard animal",
  jaguar: "jaguar animal",
  octopus: "octopus animal",
  squid: "squid animal",
  fork: "dinner fork utensil",
  spoon: "spoon utensil",
  truck: "truck vehicle",
  van: "van vehicle",
  bus: "bus vehicle",
  rv: "recreational vehicle motorhome",
  helicopter: "helicopter aircraft",
  airplane: "airplane aircraft",
  violin: "violin musical instrument",
  guitar: "guitar musical instrument",
  bridge: "bridge structure",
  tunnel: "tunnel entrance",
  castle: "castle building",
  house: "house building",
  river: "river landscape",
  lake: "lake landscape",
  mountain: "mountain landscape",
  hill: "hill landscape",
  cloud: "cloud sky",
  smoke: "smoke plume",
  desert: "desert landscape",
  beach: "beach landscape",
  rock: "rock stone",
  shell: "seashell",
  flower: "flower plant",
  tree: "tree plant",
  b: "lowercase letter b",
  d: "lowercase letter d",
  p: "lowercase letter p",
  q: "lowercase letter q",
  m: "lowercase letter m",
  w: "lowercase letter w",
  "6": "number 6 digit",
  "9": "number 9 digit",
  "2": "number 2 digit",
  "5": "number 5 digit",
  lowercase_l: "lowercase letter l",
  uppercase_i: "uppercase letter I",
  map: "world map",
  globe: "globe Earth",
  city: "city skyline",
  country: "countryside landscape",
  fruit: "fruit food",
  vegetable: "vegetables food",
  mammal: "mammal animal",
  reptile: "reptile animal",
  herbivore: "herbivore animal grazing",
  carnivore: "carnivore animal predator",
  comb: "hair comb",
  brush: "hair brush"
}));

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function sideDir(pair, side) {
  const label = side === "A" ? pair.labelA : pair.labelB;
  return path.join(GAME_DIR, "images", pair.id, label);
}

function sideKey(side) {
  return side === "A" ? "imagesA" : "imagesB";
}

function sideLabel(pair, side) {
  return side === "A" ? pair.labelA : pair.labelB;
}

function imageQuery(label) {
  return queryOverrides.get(label) || `${label.replaceAll("_", " ")} image`;
}

function relPath(absPath) {
  return path.relative(GAME_DIR, absPath).replaceAll("\\", "/");
}

async function searchOpenverse(query) {
  const params = new URLSearchParams({
    q: query,
    page_size: "30",
    mature: "false",
    unstable__include_sensitive_results: "false"
  });
  const response = await fetch(`https://api.openverse.org/v1/images/?${params}`, {
    headers: {
      "User-Agent": "WhichOneIsItEducationalBuilder/1.0"
    }
  });
  if (!response.ok) throw new Error(`Openverse search failed ${response.status} for ${query}`);
  const data = await response.json();
  return (data.results || []).filter((item) => item.url && item.thumbnail && !/\.svg($|\?)/i.test(item.url));
}

async function downloadBuffer(url) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DOWNLOAD_TIMEOUT_MS);
  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        "User-Agent": "WhichOneIsItEducationalBuilder/1.0"
      }
    });
    if (!response.ok) throw new Error(`download failed ${response.status}`);
    return Buffer.from(await response.arrayBuffer());
  } finally {
    clearTimeout(timeout);
  }
}

async function nextFilePath(pair, side) {
  const label = sideLabel(pair, side);
  const dir = sideDir(pair, side);
  await fs.mkdir(dir, { recursive: true });
  const files = await fs.readdir(dir).catch(() => []);
  const next = files
    .map((name) => Number((name.match(/_(\d+)\.webp$/) || [])[1] || 0))
    .reduce((max, n) => Math.max(max, n), 0) + 1;
  return path.join(dir, `${label}_${String(next).padStart(3, "0")}.webp`);
}

async function saveWebp(buffer, outPath) {
  await sharp(buffer)
    .rotate()
    .resize({ width: 1400, height: 1000, fit: "inside", withoutEnlargement: true })
    .webp({ quality: 84 })
    .toFile(outPath);
}

function currentImageCount(pair, side) {
  return (pair[sideKey(side)] || []).length;
}

async function reconcileSide(pair, side) {
  const key = sideKey(side);
  const dir = sideDir(pair, side);
  const label = sideLabel(pair, side);
  await fs.mkdir(dir, { recursive: true });
  const files = await fs.readdir(dir).catch(() => []);
  const discovered = files
    .filter((name) => name.startsWith(`${label}_`) && /\.(webp|svg|png|jpe?g)$/i.test(name))
    .map((name) => relPath(path.join(dir, name)));
  pair[key] = Array.isArray(pair[key]) ? pair[key] : [];
  for (const rel of discovered) {
    if (!pair[key].includes(rel)) pair[key].push(rel);
  }
}

async function fillSide(pair, side) {
  await reconcileSide(pair, side);
  const key = sideKey(side);
  const needed = TARGET_COUNT - currentImageCount(pair, side);
  if (needed <= 0) return { added: 0, errors: [] };

  const label = sideLabel(pair, side);
  const query = imageQuery(label);
  const errors = [];
  let added = 0;
  let results = [];

  try {
    results = await searchOpenverse(query);
  } catch (error) {
    return { added, errors: [`${label}: ${error.message}`] };
  }

  for (const result of results) {
    if (added >= needed) break;
    const candidates = [result.url, result.thumbnail].filter(Boolean);
    for (const url of candidates) {
      if (added >= needed) break;
      try {
        await sleep(REQUEST_DELAY_MS);
        const buffer = await downloadBuffer(url);
        const outPath = await nextFilePath(pair, side);
        await saveWebp(buffer, outPath);
        const rel = relPath(outPath);
        if (!pair[key].includes(rel)) pair[key].push(rel);
        added += 1;
      } catch (error) {
        errors.push(`${label}: ${error.message}`);
      }
    }
  }

  return { added, errors };
}

const pairs = JSON.parse(await fs.readFile(DATA_FILE, "utf8"));
const summary = [];

for (const pair of pairs) {
  for (const side of ["A", "B"]) {
    const before = currentImageCount(pair, side);
    const result = await fillSide(pair, side);
    const after = currentImageCount(pair, side);
    summary.push({ pair: pair.id, side, before, after, added: result.added, errors: result.errors.slice(0, 3) });
    console.log(`${pair.id} ${side}: ${before} -> ${after}`);
    await fs.writeFile(DATA_FILE, `${JSON.stringify(pairs, null, 2)}\n`, "utf8");
    await sleep(REQUEST_DELAY_MS);
  }
}

await fs.writeFile(DATA_FILE, `${JSON.stringify(pairs, null, 2)}\n`, "utf8");

const failed = summary.filter((item) => item.after < TARGET_COUNT);
console.log(JSON.stringify({
  target: TARGET_COUNT,
  totalSides: summary.length,
  incompleteSides: failed.length,
  incomplete: failed.slice(0, 30)
}, null, 2));
