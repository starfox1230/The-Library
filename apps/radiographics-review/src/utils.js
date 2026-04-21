const fs = require("node:fs");
const path = require("node:path");

function readJson(filePath, fallback) {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (error) {
    if (error.code === "ENOENT") {
      return fallback;
    }
    throw error;
  }
}

function writeJson(filePath, value) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function formatDate(dateLike) {
  if (!dateLike) {
    return "";
  }

  const value = new Date(dateLike);
  if (Number.isNaN(value.getTime())) {
    return "";
  }

  return value.toISOString().slice(0, 10);
}

function toDateFromParts(parts) {
  if (!Array.isArray(parts) || parts.length === 0) {
    return null;
  }

  const [year, month = 1, day = 1] = parts;
  const value = new Date(Date.UTC(year, month - 1, day));
  return Number.isNaN(value.getTime()) ? null : value.toISOString();
}

function pickPublicationDate(item) {
  const candidates = [
    item["published-print"]?.["date-parts"]?.[0],
    item["published-online"]?.["date-parts"]?.[0],
    item.issued?.["date-parts"]?.[0],
    item.created?.["date-parts"]?.[0],
    item.deposited?.["date-parts"]?.[0],
  ];

  for (const candidate of candidates) {
    const value = toDateFromParts(candidate);
    if (value) {
      return value;
    }
  }

  return null;
}

function stripHtml(text) {
  return (text || "")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function truncate(text, maxLength) {
  if (!text || text.length <= maxLength) {
    return text;
  }

  return `${text.slice(0, Math.max(0, maxLength - 3)).trim()}...`;
}

function normalizeWhitespace(text) {
  return (text || "").replace(/\s+/g, " ").trim();
}

function slugify(text, maxLength = 80) {
  const slug = normalizeWhitespace(text)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

  if (!slug) {
    return "untitled";
  }

  return slug.slice(0, maxLength).replace(/-+$/g, "") || "untitled";
}

function splitSentences(text) {
  return normalizeWhitespace(text)
    .split(/(?<=[.!?])\s+(?=[A-Z0-9(])/)
    .map((sentence) => sentence.trim())
    .filter(Boolean);
}

function escapeHtml(text) {
  return String(text || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function uniqueBy(items, selector) {
  const seen = new Set();
  const result = [];

  for (const item of items) {
    const key = selector(item);
    if (!key || seen.has(key)) {
      continue;
    }
    seen.add(key);
    result.push(item);
  }

  return result;
}

function unique(items) {
  return [...new Set(items.filter(Boolean))];
}

module.exports = {
  escapeHtml,
  formatDate,
  normalizeWhitespace,
  pickPublicationDate,
  readJson,
  slugify,
  splitSentences,
  stripHtml,
  truncate,
  unique,
  uniqueBy,
  writeJson,
};
