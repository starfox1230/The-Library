import { promises as fs } from "fs";
import path from "path";
import { fileURLToPath } from "url";
import sharp from "sharp";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BUILDER_DIR = path.resolve(__dirname, "..");
const GAME_DIR = path.resolve(BUILDER_DIR, "../library/2026-05-08-which-one-is-it");
const DATA_FILE = path.join(GAME_DIR, "data/pairs.json");
const TARGET_COUNT = Number(process.env.WHICH_ONE_IMAGE_TARGET || 4);
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
  fork: "dinner fork utensil photo",
  spoon: "spoon utensil photo",
  truck: "truck vehicle photo",
  van: "van vehicle photo",
  bus: "bus vehicle photo",
  rv: "recreational vehicle motorhome photo",
  helicopter: "helicopter aircraft photo",
  airplane: "airplane aircraft photo",
  violin: "violin musical instrument photo",
  guitar: "guitar musical instrument photo",
  bridge: "bridge structure photo",
  tunnel: "tunnel entrance photo",
  castle: "castle building photo",
  house: "house building photo",
  river: "river landscape photo",
  lake: "lake landscape photo",
  mountain: "mountain landscape photo",
  hill: "hill landscape photo",
  cloud: "cloud sky photo",
  smoke: "smoke plume photo",
  desert: "desert landscape photo",
  beach: "beach landscape photo",
  rock: "rock stone photo",
  shell: "seashell photo",
  flower: "flower plant photo",
  tree: "tree plant photo",
  b: "lowercase letter b alphabet card",
  d: "lowercase letter d alphabet card",
  p: "lowercase letter p alphabet card",
  q: "lowercase letter q alphabet card",
  m: "lowercase letter m alphabet card",
  w: "lowercase letter w alphabet card",
  "6": "number 6 digit card",
  "9": "number 9 digit card",
  "2": "number 2 digit card",
  "5": "number 5 digit card",
  lowercase_l: "lowercase letter l alphabet card",
  uppercase_i: "uppercase letter I alphabet card",
  map: "world map photo",
  globe: "globe Earth photo",
  city: "city skyline photo",
  country: "countryside landscape photo",
  fruit: "fruit food photo",
  vegetable: "vegetables food photo",
  mammal: "mammal animal photo",
  reptile: "reptile animal photo",
  herbivore: "herbivore animal grazing photo",
  carnivore: "carnivore animal predator photo",
  comb: "hair comb photo",
  brush: "hair brush photo"
  ,lung: "simple lung anatomy drawing"
  ,liver: "simple liver anatomy drawing"
  ,spleen: "simple spleen anatomy drawing"
  ,kidney: "simple kidney anatomy drawing"
  ,heart: "simple heart anatomy drawing"
  ,stomach: "simple stomach anatomy drawing"
  ,intestines: "simple intestines anatomy drawing"
  ,brain: "simple brain anatomy drawing"
  ,rib: "simple rib bone anatomy drawing"
  ,spine: "simple spine anatomy drawing"
  ,skull: "simple skull anatomy drawing"
  ,pelvis: "simple pelvis anatomy drawing"
  ,elbow: "elbow body part photo"
  ,knee: "knee body part photo"
  ,wrist: "wrist body part photo"
  ,ankle: "ankle body part photo"
  ,shoulder: "shoulder body part photo"
  ,hip: "hip body part photo"
  ,hand: "hand body part photo"
  ,foot: "foot body part photo"
  ,thumb: "thumb body part photo"
  ,finger: "finger body part photo"
  ,toe: "toe body part photo"
  ,upper_arm: "upper arm body part photo"
  ,forearm: "forearm body part photo"
  ,thigh: "thigh body part photo"
  ,shin: "shin body part photo"
  ,eye: "eye body part photo"
  ,ear: "ear body part photo"
  ,nose: "nose body part photo"
  ,mouth: "mouth body part photo"
  ,tooth: "tooth anatomy drawing"
  ,tongue: "tongue anatomy drawing"
  ,cat: "cat animal photo"
  ,dog: "dog animal photo"
  ,mouse: "mouse animal photo"
  ,rat: "rat animal photo"
  ,horse: "horse animal photo"
  ,donkey: "donkey animal photo"
  ,goat: "goat animal photo"
  ,sheep: "sheep animal photo"
  ,duck: "duck bird photo"
  ,goose: "goose bird photo"
  ,crow: "crow bird photo"
  ,raven: "raven bird photo"
  ,owl: "owl bird photo"
  ,hawk: "hawk bird photo"
  ,crab: "crab animal photo"
  ,lobster: "lobster animal photo"
  ,shrimp: "shrimp animal photo"
  ,crawfish: "crawfish animal photo"
  ,zebra: "zebra animal photo"
  ,moose: "moose animal photo"
  ,deer: "deer animal photo"
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

function sideDir(pair, side) {
  return path.join(GAME_DIR, "images", pair.id, sideLabel(pair, side));
}

function relPath(absPath) {
  return path.relative(GAME_DIR, absPath).replaceAll("\\", "/");
}

function imageQuery(label) {
  return queryOverrides.get(label) || `${label.replaceAll("_", " ")} photo`;
}

async function getVqd(query) {
  const html = await fetch(`https://duckduckgo.com/?q=${encodeURIComponent(query)}&iax=images&ia=images`, {
    headers: { "User-Agent": USER_AGENT }
  }).then((response) => response.text());
  const match = html.match(/vqd="([^"]+)"/) || html.match(/'vqd':'([^']+)'/) || html.match(/vqd=([\d-]+)&/);
  if (!match) throw new Error(`Could not get image token for ${query}`);
  return match[1];
}

async function searchImages(query) {
  const vqd = await getVqd(query);
  const url = `https://duckduckgo.com/i.js?l=us-en&o=json&q=${encodeURIComponent(query)}&vqd=${encodeURIComponent(vqd)}&f=,,,&p=1`;
  const response = await fetch(url, {
    headers: {
      "User-Agent": USER_AGENT,
      "Referer": "https://duckduckgo.com/"
    }
  });
  if (!response.ok) throw new Error(`image search failed ${response.status} for ${query}`);
  const data = await response.json();
  return (data.results || []).filter((item) => item.image || item.thumbnail);
}

async function downloadBuffer(url) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DOWNLOAD_TIMEOUT_MS);
  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: { "User-Agent": USER_AGENT }
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

function currentImageCount(pair, side) {
  return (pair[sideKey(side)] || []).length;
}

async function fillSide(pair, side) {
  await reconcileSide(pair, side);
  const key = sideKey(side);
  const needed = TARGET_COUNT - currentImageCount(pair, side);
  if (needed <= 0) return { added: 0, errors: [] };

  const label = sideLabel(pair, side);
  const query = imageQuery(label);
  const errors = [];
  let results = [];
  let added = 0;

  try {
    results = await searchImages(query);
  } catch (error) {
    return { added, errors: [`${label}: ${error.message}`] };
  }

  for (const result of results) {
    if (added >= needed) break;
    const url = result.image || result.thumbnail;
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
