const { normalizeWhitespace, splitSentences, truncate, uniqueBy } = require("./utils");
const { cleanFigureCaption, cleanStudyText } = require("./studyText");

function looksLikeNoise(sentence) {
  const lowered = sentence.toLowerCase();
  if (!sentence || sentence.length < 30) {
    return true;
  }

  return [
    "open in viewer",
    "download as powerpoint",
    "download original video",
    "supplemental files",
    "conflicts of interest",
    "view options",
    "references figures tables media share",
    "teaching point",
  ].some((fragment) => lowered.includes(fragment));
}

function collectNarrativeSentences(article) {
  const sources = [];

  if (Array.isArray(article.cleanedBodyBlocks) && article.cleanedBodyBlocks.length > 0) {
    sources.push(...article.cleanedBodyBlocks);
  } else if (Array.isArray(article.bodyBlocks)) {
    sources.push(...article.bodyBlocks);
  }

  if (article.abstract) {
    sources.push(article.abstract);
  }

  return uniqueBy(
    sources
      .flatMap((text) => splitSentences(cleanStudyText(text)))
      .map((sentence) => normalizeWhitespace(sentence))
      .filter((sentence) => !looksLikeNoise(sentence)),
    (sentence) => sentence.toLowerCase(),
  );
}

function findSentence(sentences, matcher, excluded = new Set()) {
  return sentences.find((sentence) => !excluded.has(sentence) && matcher(sentence.toLowerCase(), sentence));
}

function rewriteSentence(sentence) {
  return cleanStudyText(sentence)
    .replace(/^It typically affects\b/i, "Typically affects")
    .replace(/^It usually affects\b/i, "Usually affects")
    .replace(/^Radiographs may demonstrate\b/i, "Radiographs show")
    .replace(/^Characteristic CT findings include\b/i, "CT shows")
    .replace(/^At T1-weighted MRI,\s*/i, "MRI shows ")
    .replace(/^At T2-weighted MRI,\s*/i, "MRI shows ")
    .replace(/^At MRI,\s*/i, "MRI shows ")
    .replace(/^On MRI,\s*/i, "MRI shows ")
    .replace(/^While there is no reference standard for management,\s*/i, "")
    .replace(/^Treatment options range from\b/i, "Treatment ranges from")
    .trim();
}

function joinDistinct(parts) {
  return uniqueBy(
    parts.filter(Boolean).map((part) => rewriteSentence(part)),
    (part) => part.toLowerCase(),
  ).join(" ");
}

function buildSummarySections(article, maxSections = 5) {
  const sentences = collectNarrativeSentences(article);
  const used = new Set();
  const sections = [];

  function pushSection(label, text, pickedSentences = []) {
    if (!text) {
      return;
    }

    sections.push({
      label,
      text,
    });

    for (const sentence of pickedSentences) {
      used.add(sentence);
    }
  }

  const rarity = findSentence(
    sentences,
    (lowered) => /\b(rare|uncommon|congenital|progressive form|localized gigantism)\b/.test(lowered),
    used,
  );
  const corePattern = findSentence(
    sentences,
    (lowered) => /\b(characterized by|defined by|caused by|results in|associated with)\b/.test(lowered),
    used,
  );
  if (rarity || corePattern) {
    pushSection("What it is", joinDistinct([rarity, corePattern]), [rarity, corePattern].filter(Boolean));
  }

  const distribution = findSentence(
    sentences,
    (lowered) => /\b(typically affects|usually affects|most often affects|unilateral|bilateral|predilection)\b/.test(lowered),
    used,
  );
  if (distribution) {
    pushSection("Typical pattern", rewriteSentence(distribution), [distribution]);
  }

  const imagingSentences = [
    findSentence(sentences, (lowered) => /\b(radiograph|radiographs|x-ray)\b/.test(lowered), used),
    findSentence(sentences, (lowered) => /\bct\b/.test(lowered), used),
    findSentence(sentences, (lowered) => /\b(mri|mr image|mr imaging)\b/.test(lowered), used),
    findSentence(sentences, (lowered) => /\b(ultrasound|sonography)\b/.test(lowered), used),
  ].filter(Boolean);
  if (imagingSentences.length > 0) {
    pushSection("Imaging clues", joinDistinct(imagingSentences), imagingSentences);
  }

  const management = findSentence(
    sentences,
    (lowered) => /\b(management|treatment|orthotics|surgical|debulking|osteotomy|resection)\b/.test(lowered),
    used,
  );
  if (management) {
    pushSection("Management", rewriteSentence(management), [management]);
  }

  const differential = findSentence(
    sentences,
    (lowered) => /\b(differential|mimic|mimics|distinguish|distinguishes)\b/.test(lowered),
    used,
  );
  if (differential) {
    pushSection("Differential", rewriteSentence(differential), [differential]);
  }

  const pathogenesis = findSentence(
    sentences,
    (lowered) => /\b(pathophysiology|mutation|mutations|pik3ca|etiology|cause)\b/.test(lowered),
    used,
  );
  if (pathogenesis) {
    pushSection("Pathogenesis", rewriteSentence(pathogenesis), [pathogenesis]);
  }

  if (sections.length === 0) {
    const fallback = uniqueBy(
      (article.figures || [])
        .map((figure) => buildTeachingPoint(figure.caption))
        .filter((sentence) => sentence && sentence !== "High-yield figure from the article."),
      (sentence) => sentence.toLowerCase(),
    );

    for (const sentence of fallback.slice(0, maxSections)) {
      pushSection("Figure takeaway", sentence);
    }
  }

  if (sections.length === 0 && article.title) {
    pushSection("Article", article.title.replace(/\s*\|\s*RadioGraphics\s*$/i, ""));
  }

  return sections.slice(0, maxSections);
}

function buildKeyFacts(article, maxFacts = 5) {
  return buildSummarySections(article, maxFacts).map(
    (section) => `${section.label}: ${truncate(section.text, 260)}`,
  );
}

function buildTeachingPoint(caption) {
  const cleanedCaption = cleanFigureCaption(caption)
    .replace(/^Figure\s+\d+\.?\s*/i, "")
    .replace(/^Visual Abstract\.?\s*/i, "");
  const sentences = splitSentences(cleanedCaption).map((sentence) => normalizeWhitespace(sentence)).filter(Boolean);

  if (sentences.length === 0) {
    return "High-yield figure from the article.";
  }

  const normalizeTeachingPoint = (sentence) =>
    sentence
      .replace(/^\([A-Z,\s]+\)\s*/i, "")
      .trim();

  const rankedSentence = sentences
    .map((sentence) => {
      const lowered = sentence.toLowerCase();
      let score = 0;

      if (/\b(radiograph|radiographs|ct|mri|mr image|mr imaging|ultrasound)\b/.test(lowered)) {
        score += 5;
      }
      if (/\b(show|shows|demonstrates|demonstrate|findings|illustrates|depicts)\b/.test(lowered)) {
        score += 3;
      }
      if (/\b(pathophysiology|proliferation|fibroadipose|fatty infiltration|lipomatosis|broadened phalanges|ankylosis|osteoarthritis|osseous|bone)\b/.test(lowered)) {
        score += 4;
      }
      if (/\bphotograph shows\b/.test(lowered)) {
        score -= 3;
      }
      if (/\b\d{1,3}-year-old\b/.test(lowered)) {
        score -= 2;
      }

      return {
        sentence,
        score,
      };
    })
    .sort((left, right) => right.score - left.score)[0];

  if (rankedSentence?.score > 0) {
    return truncate(normalizeTeachingPoint(rankedSentence.sentence), 220);
  }

  const withoutCaseLead =
    sentences.length > 1 && /\b\d{1,3}-year-old\b/i.test(sentences[0])
      ? sentences.slice(1, 3)
      : sentences.slice(0, 2);

  return truncate(normalizeTeachingPoint(withoutCaseLead.join(" ")), 260);
}

module.exports = {
  buildKeyFacts,
  buildSummarySections,
  buildTeachingPoint,
};
