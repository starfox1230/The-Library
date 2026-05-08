import express from "express";
import multer from "multer";
import sharp from "sharp";
import { promises as fs } from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const GAME_DIR = path.resolve(__dirname, "../library/2026-05-08-which-one-is-it");
const DATA_FILE = path.join(GAME_DIR, "data/pairs.json");
const PORT = Number(process.env.PORT || 5178);
const TTS_MODEL = process.env.WHICH_ONE_TTS_MODEL || "gpt-4o-mini-tts";
const TTS_VOICE = process.env.WHICH_ONE_TTS_VOICE || "sage";
const TTS_CONCURRENCY = Number(process.env.WHICH_ONE_TTS_CONCURRENCY || 5);
const TTS_INSTRUCTIONS = process.env.WHICH_ONE_TTS_INSTRUCTIONS ||
  "Voice Affect: Warm, gentle, and inviting; sounds like a caring grown-up teaching young children.\n\n" +
  "Tone: Kind, playful, clear, and reassuring. Keep the energy bright but not overwhelming.\n\n" +
  "Pacing: Slightly slower than normal speech with clear pronunciation and short pauses.";
const TOP_TIER_AUDIO_KEYS = new Set(["promptA", "promptB", "answerA", "answerB", "teachingPoint"]);

const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 20 * 1024 * 1024 } });
const app = express();
app.use(express.json({ limit: "4mb" }));
app.use(express.static(path.join(__dirname, "public")));
app.use("/game", express.static(GAME_DIR));

function slugify(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "") || "item";
}

function pairIdFor(labelA, labelB) {
  return `${slugify(labelA)}_vs_${slugify(labelB)}`;
}

function assertInsideGame(absPath) {
  const resolved = path.resolve(absPath);
  if (!resolved.startsWith(GAME_DIR)) throw new Error(`Refusing to write outside game directory: ${resolved}`);
  return resolved;
}

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true });
}

async function readPairs() {
  try {
    return JSON.parse(await fs.readFile(DATA_FILE, "utf8"));
  } catch (error) {
    if (error.code === "ENOENT") return [];
    throw error;
  }
}

async function writePairs(pairs) {
  await ensureDir(path.dirname(DATA_FILE));
  await fs.writeFile(DATA_FILE, `${JSON.stringify(pairs, null, 2)}\n`, "utf8");
}

function normalizePair(pair) {
  return {
    id: pair.id || pairIdFor(pair.labelA, pair.labelB),
    labelA: slugify(pair.labelA),
    labelB: slugify(pair.labelB),
    displayLabelA: pair.displayLabelA || pair.labelA || "",
    displayLabelB: pair.displayLabelB || pair.labelB || "",
    teachingPoint: pair.teachingPoint || "",
    distinguishingCharacteristics: Array.isArray(pair.distinguishingCharacteristics) ? pair.distinguishingCharacteristics : [],
    imagesA: Array.isArray(pair.imagesA) ? pair.imagesA : [],
    imagesB: Array.isArray(pair.imagesB) ? pair.imagesB : [],
    audio: pair.audio || {}
  };
}

function audioItems(pair) {
  const a = pair.displayLabelA || pair.labelA;
  const b = pair.displayLabelB || pair.labelB;
  return [
    { key: "promptA", tier: "top", text: `Which one is the ${a}?`, file: `prompt_${pair.labelA}.mp3` },
    { key: "promptB", tier: "top", text: `Which one is the ${b}?`, file: `prompt_${pair.labelB}.mp3` },
    { key: "answerA", tier: "top", text: `This one is the ${a}.`, file: `answer_${pair.labelA}.mp3` },
    { key: "answerB", tier: "top", text: `This one is the ${b}.`, file: `answer_${pair.labelB}.mp3` },
    { key: "teachingPoint", tier: "top", text: pair.teachingPoint || `${a} and ${b} can look similar. Look for the key differences.`, file: "teaching_point.mp3" },
    { key: "labelA", tier: "secondary", text: a, file: `label_${pair.labelA}.mp3` },
    { key: "labelB", tier: "secondary", text: b, file: `label_${pair.labelB}.mp3` },
    { key: "correctA", tier: "secondary", text: `Correct! That is the ${a}.`, file: `correct_${pair.labelA}.mp3` },
    { key: "correctB", tier: "secondary", text: `Correct! That is the ${b}.`, file: `correct_${pair.labelB}.mp3` },
    { key: "gentleCorrectionA", tier: "secondary", text: `Nice try. This one is the ${a}.`, file: `gentle_correction_${pair.labelA}.mp3` },
    { key: "gentleCorrectionB", tier: "secondary", text: `Nice try. This one is the ${b}.`, file: `gentle_correction_${pair.labelB}.mp3` }
  ];
}

async function existsRelative(relPath) {
  if (!relPath) return false;
  try {
    await fs.access(assertInsideGame(path.join(GAME_DIR, relPath)));
    return true;
  } catch {
    return false;
  }
}

async function pairStatus(pair) {
  const normalized = normalizePair(pair);
  const audio = {};
  for (const item of audioItems(normalized)) audio[item.key] = await existsRelative(normalized.audio[item.key]);
  const hasTeaching = Boolean(normalized.teachingPoint.trim());
  const hasCharacteristics = normalized.distinguishingCharacteristics.length > 0;
  const hasImages = normalized.imagesA.length > 0 && normalized.imagesB.length > 0;
  const hasCoreAudio = audio.promptA && audio.promptB && audio.answerA && audio.answerB && audio.teachingPoint;
  let status = "Incomplete";
  if (!hasImages) status = "Needs images";
  else if (!hasTeaching || !hasCharacteristics) status = "Playable, needs teaching";
  else if (!hasCoreAudio) status = "Playable, needs audio";
  else status = "Complete";
  return {
    id: normalized.id,
    labelA: normalized.labelA,
    labelB: normalized.labelB,
    displayName: `${normalized.displayLabelA} vs ${normalized.displayLabelB}`,
    imageCountA: normalized.imagesA.length,
    imageCountB: normalized.imagesB.length,
    teachingText: hasTeaching,
    distinguishingCharacteristics: hasCharacteristics,
    audio,
    status
  };
}

async function nextImageName(pair, side) {
  const label = side === "A" ? pair.labelA : pair.labelB;
  const dir = path.join(GAME_DIR, "images", pair.id, label);
  await ensureDir(dir);
  const files = await fs.readdir(dir).catch(() => []);
  const next = files
    .map((name) => Number((name.match(/_(\d+)\.webp$/) || [])[1] || 0))
    .reduce((max, n) => Math.max(max, n), 0) + 1;
  return { dir, rel: `images/${pair.id}/${label}/${label}_${String(next).padStart(3, "0")}.webp` };
}

async function ttsMp3(text) {
  if (!process.env.OPENAI_API_KEY) throw new Error("Missing OPENAI_API_KEY.");
  const response = await fetch("https://api.openai.com/v1/audio/speech", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model: TTS_MODEL,
      voice: TTS_VOICE,
      input: text,
      instructions: TTS_INSTRUCTIONS
    })
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new Error(`OpenAI TTS failed (${response.status}): ${detail.slice(0, 400)}`);
  }
  return Buffer.from(await response.arrayBuffer());
}

async function mapLimit(items, limit, worker) {
  const results = [];
  let cursor = 0;
  const runners = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (cursor < items.length) {
      const index = cursor;
      cursor += 1;
      results[index] = await worker(items[index], index);
    }
  });
  await Promise.all(runners);
  return results;
}

app.get("/api/pairs", async (_req, res) => {
  const pairs = (await readPairs()).map(normalizePair);
  res.json({ pairs, statuses: await Promise.all(pairs.map(pairStatus)), gameDir: GAME_DIR });
});

app.post("/api/pairs", async (req, res) => {
  const pairs = (await readPairs()).map(normalizePair);
  const incoming = normalizePair({
    ...req.body,
    id: req.body.id || pairIdFor(req.body.labelA || req.body.displayLabelA, req.body.labelB || req.body.displayLabelB)
  });
  if (!incoming.displayLabelA || !incoming.displayLabelB) return res.status(400).json({ error: "Both labels are required." });
  incoming.labelA = slugify(incoming.displayLabelA);
  incoming.labelB = slugify(incoming.displayLabelB);
  incoming.id = incoming.id || pairIdFor(incoming.labelA, incoming.labelB);
  await ensureDir(path.join(GAME_DIR, "images", incoming.id, incoming.labelA));
  await ensureDir(path.join(GAME_DIR, "images", incoming.id, incoming.labelB));
  await ensureDir(path.join(GAME_DIR, "audio", incoming.id));
  const existingIndex = pairs.findIndex((pair) => pair.id === incoming.id);
  if (existingIndex >= 0) pairs[existingIndex] = { ...pairs[existingIndex], ...incoming };
  else pairs.push(incoming);
  await writePairs(pairs);
  res.json({ pair: incoming });
});

app.post("/api/pairs/:id/images/:side", upload.single("image"), async (req, res) => {
  const pairs = (await readPairs()).map(normalizePair);
  const pair = pairs.find((item) => item.id === req.params.id);
  if (!pair) return res.status(404).json({ error: "Pair not found." });
  const side = req.params.side === "B" ? "B" : "A";
  if (!req.file?.buffer?.length) return res.status(400).json({ error: "No image uploaded." });
  const { rel } = await nextImageName(pair, side);
  const abs = assertInsideGame(path.join(GAME_DIR, rel));
  await sharp(req.file.buffer).rotate().resize({ width: 1400, height: 1000, fit: "inside", withoutEnlargement: true }).webp({ quality: 86 }).toFile(abs);
  const key = side === "A" ? "imagesA" : "imagesB";
  pair[key].push(rel.replaceAll("\\", "/"));
  await writePairs(pairs);
  res.json({ path: rel, pair });
});

app.delete("/api/pairs/:id/images", async (req, res) => {
  const rel = String(req.query.path || "");
  const pairs = (await readPairs()).map(normalizePair);
  const pair = pairs.find((item) => item.id === req.params.id);
  if (!pair) return res.status(404).json({ error: "Pair not found." });
  pair.imagesA = pair.imagesA.filter((item) => item !== rel);
  pair.imagesB = pair.imagesB.filter((item) => item !== rel);
  await fs.rm(assertInsideGame(path.join(GAME_DIR, rel)), { force: true });
  await writePairs(pairs);
  res.json({ ok: true });
});

app.put("/api/pairs/:id/content", async (req, res) => {
  const pairs = (await readPairs()).map(normalizePair);
  const pair = pairs.find((item) => item.id === req.params.id);
  if (!pair) return res.status(404).json({ error: "Pair not found." });
  pair.displayLabelA = req.body.displayLabelA ?? pair.displayLabelA;
  pair.displayLabelB = req.body.displayLabelB ?? pair.displayLabelB;
  pair.teachingPoint = req.body.teachingPoint ?? pair.teachingPoint;
  pair.distinguishingCharacteristics = Array.isArray(req.body.distinguishingCharacteristics) ? req.body.distinguishingCharacteristics : pair.distinguishingCharacteristics;
  await writePairs(pairs);
  res.json({ pair });
});

app.post("/api/pairs/:id/audio/generate", async (req, res) => {
  const pairs = (await readPairs()).map(normalizePair);
  const pair = pairs.find((item) => item.id === req.params.id);
  if (!pair) return res.status(404).json({ error: "Pair not found." });
  const onlyMissing = req.body.onlyMissing !== false;
  const keys = Array.isArray(req.body.keys) && req.body.keys.length ? new Set(req.body.keys) : null;
  const tier = req.body.tier === "top" ? "top" : req.body.tier === "secondary" ? "secondary" : "all";
  await ensureDir(path.join(GAME_DIR, "audio", pair.id));
  await ensureDir(path.join(GAME_DIR, "audio", pair.id, "_previews"));
  const candidates = [];
  for (const item of audioItems(pair)) {
    if (keys && !keys.has(item.key)) continue;
    if (tier !== "all" && item.tier !== tier) continue;
    const rel = `audio/${pair.id}/${item.file}`;
    const exists = await existsRelative(pair.audio[item.key] || rel);
    if (!onlyMissing || !exists) candidates.push({ ...item, rel });
  }
  const results = await mapLimit(candidates, TTS_CONCURRENCY, async (item) => {
    try {
      const buffer = await ttsMp3(item.text);
      const existingPath = pair.audio[item.key] || item.rel;
      const existing = await existsRelative(existingPath);
      if (!onlyMissing && existing) {
        const previewRel = `audio/${pair.id}/_previews/${item.key}_${Date.now()}.mp3`;
        await fs.writeFile(assertInsideGame(path.join(GAME_DIR, previewRel)), buffer);
        return { key: item.key, status: "preview", currentPath: existingPath, previewPath: previewRel };
      }
      await fs.writeFile(assertInsideGame(path.join(GAME_DIR, item.rel)), buffer);
      pair.audio[item.key] = item.rel;
      return { key: item.key, status: "generated", path: item.rel };
    } catch (error) {
      return { key: item.key, status: "failed", error: error.message };
    }
  });
  await writePairs(pairs);
  res.json({ results, pair, model: TTS_MODEL, voice: TTS_VOICE, concurrency: TTS_CONCURRENCY });
});

app.post("/api/pairs/:id/audio/keep-preview", async (req, res) => {
  const pairs = (await readPairs()).map(normalizePair);
  const pair = pairs.find((item) => item.id === req.params.id);
  if (!pair) return res.status(404).json({ error: "Pair not found." });
  const key = String(req.body.key || "");
  const previewPath = String(req.body.previewPath || "");
  const item = audioItems(pair).find((entry) => entry.key === key);
  if (!item) return res.status(400).json({ error: "Unknown audio key." });
  if (!previewPath.includes(`audio/${pair.id}/_previews/`)) return res.status(400).json({ error: "Preview path is invalid." });
  const finalRel = `audio/${pair.id}/${item.file}`;
  await fs.copyFile(assertInsideGame(path.join(GAME_DIR, previewPath)), assertInsideGame(path.join(GAME_DIR, finalRel)));
  await fs.rm(assertInsideGame(path.join(GAME_DIR, previewPath)), { force: true });
  pair.audio[key] = finalRel;
  await writePairs(pairs);
  res.json({ pair, key, path: finalRel });
});

app.listen(PORT, () => {
  console.log(`Which One builder running at http://localhost:${PORT}`);
  console.log(`Writing game content in ${GAME_DIR}`);
});
