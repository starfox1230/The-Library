const { splitSentences, stripHtml, truncate, uniqueBy } = require("./utils");

function cleanSentence(sentence) {
  return stripHtml(sentence)
    .replace(/\bDownload as PowerPoint\b/gi, "")
    .replace(/\s+/g, " ")
    .trim();
}

function buildKeyFacts(article, maxFacts = 5) {
  const sentences = uniqueBy(
    splitSentences(article.abstract || "").map(cleanSentence),
    (sentence) => sentence.toLowerCase(),
  ).filter((sentence) => sentence.length > 30);

  const facts = [];
  for (const sentence of sentences) {
    facts.push(truncate(sentence, 220));
    if (facts.length >= maxFacts) {
      break;
    }
  }

  if (facts.length === 0) {
    const figureFacts = uniqueBy(
      (article.figures || [])
        .map((figure) => buildTeachingPoint(figure.caption))
        .filter((sentence) => sentence && sentence !== "High-yield figure from the article."),
      (sentence) => sentence.toLowerCase(),
    );

    for (const fact of figureFacts) {
      facts.push(truncate(fact, 220));
      if (facts.length >= maxFacts) {
        break;
      }
    }
  }

  if (facts.length === 0 && article.title) {
    facts.push(article.title.replace(/\s*\|\s*RadioGraphics\s*$/i, ""));
  }

  return facts;
}

function buildTeachingPoint(caption) {
  const cleanedCaption = cleanSentence(caption)
    .replace(/^Figure\s+\d+\.?\s*/i, "")
    .replace(/^Visual Abstract\.?\s*/i, "");
  const sentences = splitSentences(cleanedCaption).map(cleanSentence).filter(Boolean);

  if (sentences.length === 0) {
    return "High-yield figure from the article.";
  }

  return truncate(sentences.slice(0, 2).join(" "), 260);
}

function pickAnkiFigures(figures, maxFigures) {
  const visualAbstract = figures.find((figure) => figure.isVisualAbstract);
  const regularFigures = figures.filter(
    (figure) => !figure.isVisualAbstract && figure.localImagePath && figure.caption,
  );

  const picked = [];
  if (visualAbstract) {
    picked.push(visualAbstract);
  }

  for (const figure of regularFigures) {
    picked.push(figure);
    if (picked.length >= maxFigures) {
      break;
    }
  }

  return picked;
}

module.exports = {
  buildKeyFacts,
  buildTeachingPoint,
  pickAnkiFigures,
};
