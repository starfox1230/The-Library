const { normalizeWhitespace, splitSentences, truncate, uniqueBy } = require("./utils");
const { cleanFigureCaption, cleanStudyText } = require("./studyText");

function looksLikeNoise(sentence) {
  const lowered = String(sentence || "").toLowerCase();
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
    "movie ",
  ].some((fragment) => lowered.includes(fragment));
}

function cleanInsightText(text) {
  return normalizeWhitespace(
    cleanStudyText(String(text || ""))
      .replace(/\bTEACHING POINT\b/gi, "")
      .replace(/^Introduction\s+/i, "")
      .replace(/\s+([,.;)])/g, "$1")
      .replace(/\(\s+/g, "(")
      .trim(),
  );
}

function articleSubject(article) {
  return normalizeWhitespace(article?.title || "This article");
}

function subjectFromSentence(sentence) {
  const match = cleanInsightText(sentence).match(/^(.+?)\s+is\s+/i);
  const candidate = normalizeWhitespace(match?.[1] || "");
  if (!candidate || candidate.length > 90) {
    return "";
  }
  return candidate;
}

function detectArticleMode(article) {
  const haystack = `${article?.title || ""} ${article?.abstract || ""}`.toLowerCase();
  return /\b(embolization|technique|pitfalls|applications|properties|procedure|workflow|practical approach|interventional)\b/.test(
    haystack,
  )
    ? "technique"
    : "disease";
}

function collectNarrativeSentences(article) {
  const sources = [];

  if (article.abstract) {
    sources.push(article.abstract);
  }

  if (Array.isArray(article.cleanedBodyBlocks) && article.cleanedBodyBlocks.length > 0) {
    sources.push(...article.cleanedBodyBlocks);
  } else if (Array.isArray(article.bodyBlocks)) {
    sources.push(...article.bodyBlocks);
  }

  return uniqueBy(
    sources
      .flatMap((text) => splitSentences(cleanInsightText(text)))
      .map((sentence) => normalizeWhitespace(sentence))
      .filter((sentence) => !looksLikeNoise(sentence)),
    (sentence) => sentence.toLowerCase(),
  );
}

function findSentence(sentences, matcher, excluded = new Set()) {
  return sentences.find((sentence) => !excluded.has(sentence) && matcher(sentence.toLowerCase(), sentence));
}

function stripTrailingWeakClause(text) {
  return normalizeWhitespace(
    String(text || "")
      .replace(/,\s*although\b.+$/i, "")
      .replace(/\s+although\b.+$/i, "")
      .replace(/,\s*but\b.+$/i, "")
      .replace(/\s+but\b.+$/i, "")
      .replace(/,\s*however\b.+$/i, "")
      .replace(/\s+however\b.+$/i, "")
      .replace(/,\s*with no gender predilection$/i, ""),
  );
}

function rewriteWithSubject(sentence, subject) {
  return stripTrailingWeakClause(
    cleanInsightText(sentence)
      .replace(/^It\s+/i, `${subject} `)
      .replace(/^This condition\s+/i, `${subject} `)
      .replace(/^The disease\s+/i, `${subject} `)
      .replace(/^This property makes it\s+/i, `${subject} is `)
      .replace(/^Treatment options range from\b/i, "Management ranges from")
      .replace(/^While there is no reference standard for management,\s*treatment options range from\b/i, "Management ranges from"),
  );
}

function trimTerminalPunctuation(text) {
  return normalizeWhitespace(String(text || "").replace(/[. ]+$/g, ""));
}

function joinDistinct(parts) {
  return uniqueBy(
    parts
      .filter(Boolean)
      .map((part) => cleanInsightText(part))
      .map((part) => stripTrailingWeakClause(part)),
    (part) => part.toLowerCase(),
  ).join(" ");
}

function extractFindingPhrase(sentence, patterns = []) {
  let value = cleanInsightText(sentence);
  for (const [pattern, replacement] of patterns) {
    value = value.replace(pattern, replacement);
  }

  return trimTerminalPunctuation(
    value
      .replace(/\b(?:are|is) the major findings\b/gi, "")
      .replace(/\b(?:are|is) characteristic\b/gi, "")
      .replace(/\b(?:are|is) typical\b/gi, "")
      .replace(/\b(?:can|may) be seen\b/gi, "")
      .replace(/\bmajor findings include\b/gi, "")
      .replace(/\s{2,}/g, " "),
  );
}

function buildImagingSummary(insights) {
  const parts = [];

  if (insights.radiographFindings) {
    parts.push(`Radiographs typically show ${insights.radiographFindings}.`);
  }
  if (insights.ctFindings) {
    parts.push(`CT typically shows ${insights.ctFindings}.`);
  }
  if (insights.mriFindings) {
    parts.push(`MRI typically shows ${insights.mriFindings}.`);
  }
  if (insights.ultrasoundFindings) {
    parts.push(`Ultrasound typically shows ${insights.ultrasoundFindings}.`);
  }

  return joinDistinct(parts);
}

function isUsefulInsight(label, text) {
  const lowered = String(text || "").toLowerCase();
  if (!text || text.length < 35) {
    return false;
  }

  if (
    [
      "high-yield figure from the article",
      "download as powerpoint",
      "open in viewer",
      "get full access to this article",
      "already a subscriber",
      "sign in as an individual",
      "not yet been well established",
      "not well established",
    ].some((fragment) => lowered.includes(fragment))
  ) {
    return false;
  }

  if (label !== "Imaging hallmarks" && /^(radiographs|ct|mri|ultrasound)\b/i.test(text)) {
    return false;
  }

  if (label === "Typical distribution" && !/\b(?:affects|involves|unilateral|bilateral|digit|digits|hand|foot)\b/i.test(text)) {
    return false;
  }

  return true;
}

function extractArticleInsights(article) {
  const mode = detectArticleMode(article);
  const sentences = collectNarrativeSentences(article);
  const leadSentence = sentences[0] || "";
  const subject = subjectFromSentence(leadSentence) || articleSubject(article);
  const used = new Set();
  const definingSentence = findSentence(
    sentences,
    (lowered) =>
      /\b(characterized by|defined by|progressive form of|minimally invasive technique|embolic agent|has emerged as)\b/.test(
        lowered,
      ),
    used,
  );

  const coreConcept = joinDistinct([
    rewriteWithSubject(leadSentence, subject),
    definingSentence && definingSentence !== leadSentence
      ? rewriteWithSubject(definingSentence, subject)
      : "",
  ]);
  if (leadSentence) {
    used.add(leadSentence);
  }
  if (definingSentence) {
    used.add(definingSentence);
  }

  const distributionSentence =
    mode === "disease"
      ? findSentence(
          sentences,
          (lowered) => /\b(typically affects|usually affects|most often affects|unilateral|bilateral)\b/.test(lowered),
          used,
        )
      : "";
  const distribution = distributionSentence
    ? rewriteWithSubject(distributionSentence, subject)
    : "";
  if (distributionSentence) {
    used.add(distributionSentence);
  }

  const radiographSentence =
    mode === "disease"
      ? findSentence(sentences, (lowered) => /\b(radiograph|radiographs|x-ray)\b/.test(lowered), used)
      : "";
  const ctSentence =
    mode === "disease"
      ? findSentence(sentences, (lowered) => /\bct\b/.test(lowered), used)
      : "";
  const mriSentence =
    mode === "disease"
      ? findSentence(sentences, (lowered) => /\b(mri|mr image|mr imaging)\b/.test(lowered), used)
      : "";
  const ultrasoundSentence =
    mode === "disease"
      ? findSentence(sentences, (lowered) => /\b(ultrasound|sonography)\b/.test(lowered), used)
      : "";

  const radiographFindings = radiographSentence
    ? extractFindingPhrase(radiographSentence, [
        [/^Radiographs?\s+(?:may\s+)?(?:show|demonstrate)\s+/i, ""],
      ])
    : "";
  const ctFindings = ctSentence
    ? extractFindingPhrase(ctSentence, [
        [/^CT\s+shows\s+/i, ""],
        [/^Characteristic CT findings include\s+/i, ""],
      ])
    : "";
  const mriFindings = mriSentence
    ? extractFindingPhrase(mriSentence, [
        [/^MRI\s+shows\s+/i, ""],
        [/^At\s+(?:T1-weighted|T2-weighted)\s+MRI,\s*/i, ""],
        [/^At MRI,\s*/i, ""],
        [/^On MRI,\s*/i, ""],
      ])
    : "";
  const ultrasoundFindings = ultrasoundSentence
    ? extractFindingPhrase(ultrasoundSentence, [
        [/^Ultrasound\s+shows\s+/i, ""],
        [/^Sonography\s+shows\s+/i, ""],
      ])
    : "";

  [radiographSentence, ctSentence, mriSentence, ultrasoundSentence].filter(Boolean).forEach((sentence) => {
    used.add(sentence);
  });

  const mechanismSentence = findSentence(
    sentences,
    (lowered) =>
      /\b(polymerizes|polymerization|mixed with|mixing|viscosity|pathophysiology|mutation|mutations|hemodynamics)\b/.test(
        lowered,
      ),
    used,
  );
  const mechanism = mechanismSentence ? rewriteWithSubject(mechanismSentence, subject) : "";
  if (mechanismSentence) {
    used.add(mechanismSentence);
  }

  const useCaseSentence = findSentence(
    sentences,
    (lowered) =>
      /\b(especially effective|applications include|used in|used to|indicated in|particularly valuable)\b/.test(
        lowered,
      ),
    used,
  );
  const clinicalUse = useCaseSentence ? rewriteWithSubject(useCaseSentence, subject) : "";
  if (useCaseSentence) {
    used.add(useCaseSentence);
  }

  const technicalPearlSentence = findSentence(
    sentences,
    (lowered) =>
      /\b(pressure-dependent|flow-dependent|flow-controlled|ratio|microcatheter|vascular anatomy|hemodynamics|operator experience|procedural protocols)\b/.test(
        lowered,
      ),
    used,
  );
  const technicalPearl = technicalPearlSentence ? rewriteWithSubject(technicalPearlSentence, subject) : "";
  if (technicalPearlSentence) {
    used.add(technicalPearlSentence);
  }

  const riskSentence = findSentence(
    sentences,
    (lowered) =>
      /\b(risk|complication|pitfall|nontarget embolization|tissue necrosis|ischemia|catheter entrapment)\b/.test(
        lowered,
      ),
    used,
  );
  const mainRisk = riskSentence ? rewriteWithSubject(riskSentence, subject) : "";
  if (riskSentence) {
    used.add(riskSentence);
  }

  const managementSentence =
    mode === "disease"
      ? findSentence(
          sentences,
          (lowered) =>
            /\b(management|treatment|orthotics|surgical|debulking|osteotomy|resection)\b/.test(lowered),
          used,
        )
      : "";
  let management = "";
  let managementFrom = "";
  let managementTo = "";

  if (managementSentence) {
    const rangeMatch = managementSentence.match(/\brange(?:s)? from\b\s+(.+?)\s+\bto\b\s+(.+?)(?:\.|$)/i);
    if (rangeMatch?.[1] && rangeMatch?.[2]) {
      managementFrom = trimTerminalPunctuation(rangeMatch[1]);
      managementTo = trimTerminalPunctuation(
        rangeMatch[2].replace(/\s+for patients with.+$/i, ""),
      );
      management = `Management ranges from ${managementFrom} to ${managementTo} in symptomatic patients with functional limitation.`;
    } else {
      management = rewriteWithSubject(managementSentence, subject);
    }
  }

  return {
    mode,
    subject,
    sentences,
    coreConcept,
    distribution,
    imagingHallmarks: buildImagingSummary({
      radiographFindings,
      ctFindings,
      mriFindings,
      ultrasoundFindings,
    }),
    mechanism,
    clinicalUse,
    technicalPearl,
    mainRisk,
    management,
    managementFrom,
    managementTo,
    radiographFindings,
    ctFindings,
    mriFindings,
    ultrasoundFindings,
    rawSentences: {
      leadSentence,
      definingSentence,
      distributionSentence,
      radiographSentence,
      ctSentence,
      mriSentence,
      ultrasoundSentence,
      mechanismSentence,
      useCaseSentence,
      technicalPearlSentence,
      riskSentence,
      managementSentence,
    },
  };
}

function buildSummarySections(article, maxSections = 5) {
  const insights = extractArticleInsights(article);
  const sections = [];

  function push(label, text) {
    if (!isUsefulInsight(label, text)) {
      return;
    }

    sections.push({
      label,
      text,
    });
  }

  push(insights.mode === "technique" ? "Core concept" : "Core diagnosis", insights.coreConcept);

  if (insights.mode === "technique") {
    push("How it works", insights.mechanism);
    push("Clinical use", insights.clinicalUse);
    push("Technical pearl", insights.technicalPearl);
    push("Main risk", insights.mainRisk);
  } else {
    push("Typical distribution", insights.distribution);
    push("Imaging hallmarks", insights.imagingHallmarks);
    push("Management", insights.management);
    if (insights.mechanism && /\b(pathophysiology|mutation|mutations|mechanism)\b/i.test(insights.mechanism)) {
      push("Proposed mechanism", insights.mechanism);
    }
  }

  if (sections.length === 0 && article.title) {
    sections.push({
      label: "Article",
      text: article.title.replace(/\s*\|\s*RadioGraphics\s*$/i, ""),
    });
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
  const sentences = splitSentences(cleanedCaption)
    .map((sentence) => normalizeWhitespace(sentence))
    .filter(Boolean);

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
  extractArticleInsights,
};
