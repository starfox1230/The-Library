const { normalizeWhitespace } = require("./utils");
const { extractArticleInsights } = require("./summarize");

function chicagoDateStamp(dateLike = new Date()) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Chicago",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date(dateLike));
  const byType = Object.fromEntries(
    parts.filter((part) => part.type !== "literal").map((part) => [part.type, part.value]),
  );
  return `${byType.year}.${byType.month}.${byType.day}`;
}

function tagSubject(title) {
  const words = String(title || "Radiographics Article")
    .split(/[^A-Za-z0-9]+/)
    .filter(Boolean)
    .map((word) => `${word.slice(0, 1).toUpperCase()}${word.slice(1)}`);
  return words.join("_") || "Radiographics_Article";
}

function buildBatchTag(article, dateLike = new Date()) {
  return `#AnkiChat::${chicagoDateStamp(dateLike)}_${tagSubject(article.title)}`;
}

function trimTerminalPunctuation(text) {
  return normalizeWhitespace(String(text || "").replace(/[. ]+$/g, ""));
}

function findSentence(sentences, pattern) {
  return (sentences || []).find((sentence) => pattern.test(sentence));
}

function countWords(text) {
  const normalized = normalizeWhitespace(String(text || ""));
  return normalized ? normalized.split(/\s+/).length : 0;
}

function buildContentNote(content, batchTag) {
  return {
    content: normalizeWhitespace(content),
    tags: [batchTag],
  };
}

function buildQuestionAnswerNote(question, answer, batchTag) {
  return buildContentNote(
    `${normalizeWhitespace(question)}<br><br>{{c1::${trimTerminalPunctuation(answer)}}}`,
    batchTag,
  );
}

function buildImageDiagnosisNote(answer, imageName, batchTag) {
  return buildContentNote(
    `Most likely diagnosis?<br><br>{{c1::${trimTerminalPunctuation(answer)}}}<br><br><img src="${imageName}">`,
    batchTag,
  );
}

function buildImageQuestionAnswerNote(question, answer, imageName, batchTag) {
  return buildContentNote(
    `${normalizeWhitespace(question)}<br><br>{{c1::${trimTerminalPunctuation(answer)}}}<br><br><img src="${imageName}">`,
    batchTag,
  );
}

function compactFindingText(text) {
  return trimTerminalPunctuation(
    String(text || "")
      .replace(/\bhypertrophy of both soft and osseous tissues, as well as\b/i, "soft-tissue and osseous hypertrophy with")
      .replace(/\bhypointense fibrous bands within adipose tissue\b/i, "hypointense fibrous bands in adipose tissue")
      .replace(/\s+that cannot be accessed\b.+$/i, "")
      .replace(/\s+or in cases requiring urgent hemostasis due to severe hemorrhage\b/i, "")
      .replace(/,\s*extending\b.+$/i, "")
      .replace(/,\s*with no gender predilection\b/i, "")
      .replace(/^also seen is\s+/i, "")
      .replace(/^note the\s+/i, "")
      .replace(/\s{2,}/g, " "),
  );
}

function noteWordCount(text) {
  const plain = normalizeWhitespace(
    String(text || "")
      .replace(/<img\b[^>]*>/gi, " ")
      .replace(/<br\s*\/?>/gi, " ")
      .replace(/<[^>]+>/g, " ")
      .replace(/\{\{c\d+::/g, "")
      .replace(/::[^}]+(?=\}\})/g, "")
      .replace(/\}\}/g, ""),
  );
  return countWords(plain);
}

function pickDiagnosisFigures(article, maxFigures = 3) {
  const ranked = (article.figures || [])
    .filter((figure) => figure.localImageName && !figure.isVisualAbstract)
    .map((figure) => {
      const lowered = (figure.caption || "").toLowerCase();
      let score = 0;

      if (/\b(radiograph|radiographs|x-ray)\b/.test(lowered)) {
        score += 5;
      }
      if (/\b(mri|mr image|mr imaging)\b/.test(lowered)) {
        score += 4;
      }
      if (/\b(ct|computed tomography)\b/.test(lowered)) {
        score += 4;
      }
      if (/\b(ultrasound|sonography)\b/.test(lowered)) {
        score += 4;
      }
      if (/\b(pathophysiology|diagram|algorithm|visual abstract)\b/.test(lowered)) {
        score -= 8;
      }
      if (/\bconsistent with\b/.test(lowered)) {
        score += 3;
      }
      if (/\bfindings of\b/.test(lowered)) {
        score += 2;
      }

      return {
        figure,
        score,
      };
    })
    .sort((left, right) => right.score - left.score);

  return ranked
    .filter(({ score }) => score > 0)
    .slice(0, maxFigures)
    .map(({ figure }) => figure);
}

function detectFigureModality(figure) {
  const lowered = `${figure?.caption || ""} ${figure?.label || ""}`.toLowerCase();
  if (/\b(mri|mr image|mr imaging|t1-weighted|t2-weighted)\b/.test(lowered)) {
    return "MRI";
  }
  if (/\b(ct|computed tomography|ct scan)\b/.test(lowered)) {
    return "CT";
  }
  if (/\b(radiograph|radiographs|x-ray)\b/.test(lowered)) {
    return "radiograph";
  }
  if (/\b(ultrasound|sonography)\b/.test(lowered)) {
    return "ultrasound";
  }
  if (/\b(angiogram|venogram)\b/.test(lowered)) {
    return "angiogram";
  }
  if (/\bphotograph\b/.test(lowered)) {
    return "photograph";
  }
  return "image";
}

function extractArrowFindingCandidates(figure) {
  const caption = String(figure?.caption || "");
  if (!caption || !/\barrow(?:s|heads)?\b/i.test(caption)) {
    return [];
  }

  const keywordPatterns = [
    "marked enlargement",
    "fatty infiltration",
    "ankylosis",
    "hypertrophic osteoarthritis",
    "advanced osteoarthritis",
    "pseudoaneurysm",
    "extravasation",
    "bleeding vessel",
    "stenosis",
    "occlusion",
    "calcification",
    "hemorrhage",
    "thrombus",
    "aneurysm",
    "mass",
  ];

  const candidates = [];
  for (const keyword of keywordPatterns) {
    const pattern = new RegExp(`(${keyword}[^.]{0,160}?)\\s*\\((?:[^)]*\\barrow(?:s|heads)?\\b[^)]*)\\)`, "ig");
    let match;
    while ((match = pattern.exec(caption)) !== null) {
      const answer = compactFindingText(match[1]);
      if (!answer || countWords(answer) < 3) {
        continue;
      }

      let score = 0;
      if (/\bmedian nerve|fatty infiltration|pseudoaneurysm|extravasation|thrombus\b/i.test(answer)) {
        score += 6;
      }
      if (/\bankylosis|osteoarthritis|stenosis|occlusion|bleeding\b/i.test(answer)) {
        score += 4;
      }
      if (countWords(answer) <= 12) {
        score += 2;
      }
      if (countWords(answer) <= 18) {
        score += 1;
      }

      candidates.push({
        answer,
        score,
      });
    }
  }

  return candidates
    .sort((left, right) => right.score - left.score)
    .filter((candidate, index, list) => list.findIndex((item) => item.answer.toLowerCase() === candidate.answer.toLowerCase()) === index);
}

function buildFigureEvidenceNotes(article, title, batchTag, pushNote) {
  for (const figure of article.figures || []) {
    if (!figure?.localImageName) {
      continue;
    }

    const modality = detectFigureModality(figure);
    const arrowFinding = extractArrowFindingCandidates(figure)[0];
    if (arrowFinding) {
      pushNote(
        buildImageQuestionAnswerNote(
          `In ${title}, what do the arrows indicate on this ${modality}?`,
          arrowFinding.answer,
          figure.localImageName,
          batchTag,
        ),
      );
    }
  }
}

function buildPathogenesisNotes(article, title, batchTag, pushNote) {
  const captionText = (article.figures || [])
    .map((figure) => figure.caption || "")
    .join(" ");
  const bodyText = Array.isArray(article.cleanedBodyBlocks)
    ? article.cleanedBodyBlocks.join(" ")
    : article.cleanedBodyText || "";
  const sourceText = `${captionText} ${bodyText}`;

  const mutationMatch = sourceText.match(/\b(somatic activating\s+[A-Z0-9-]+\s+mutations?)\b/i);
  if (mutationMatch?.[1]) {
    pushNote(
      buildContentNote(
        `A proposed molecular cause of ${title} is {{c1::${trimTerminalPunctuation(mutationMatch[1])}}}.`,
        batchTag,
      ),
    );
  }
}

function buildDiseaseNotes(article, insights, batchTag, pushNote) {
  const title = insights.subject;
  const leadSentence = insights.rawSentences.leadSentence || "";
  const definitionSentence = insights.rawSentences.definingSentence || leadSentence || "";
  const combinedDefinition = normalizeWhitespace([leadSentence, definitionSentence].filter(Boolean).join(" "));

  const diseaseTypeMatch = combinedDefinition.match(
    /\bis a[n]?\s+(.+? disease)(?:\s+affecting|\s+with|\s+characterized|\s*,|\.|$)/i,
  );
  if (diseaseTypeMatch?.[1]) {
    pushNote(
      buildContentNote(
        `${title} is a {{c1::${trimTerminalPunctuation(diseaseTypeMatch[1])}}}.`,
        batchTag,
      ),
    );
  }

  const formMatch = combinedDefinition.match(/\bprogressive form of\b\s+(.+?)(?:\s+characterized by|,|\.|$)/i);
  if (formMatch?.[1]) {
    pushNote(
      buildContentNote(
        `${title} is a progressive form of {{c1::${trimTerminalPunctuation(formMatch[1])}}}.`,
        batchTag,
      ),
    );
  }

  const prevalenceMatch = combinedDefinition.match(/\baffecting approximately\s+(.+?)\s+live births\b/i);
  if (prevalenceMatch?.[1]) {
    pushNote(
      buildContentNote(
        `The estimated birth prevalence of ${title} is about {{c1::${trimTerminalPunctuation(prevalenceMatch[1])} live births}}.`,
        batchTag,
      ),
    );
  }

  const characterizedMatch = definitionSentence.match(/\bcharacterized by\b\s+(.+?)(?:\.|$)/i);
  if (characterizedMatch?.[1]) {
    pushNote(
      buildContentNote(
        `${title} is characterized by {{c1::${trimTerminalPunctuation(characterizedMatch[1])}}}.`,
        batchTag,
      ),
    );
  }

  const distributionSentence = insights.rawSentences.distributionSentence || insights.distribution || "";
  const locationAndLateralityMatch = distributionSentence.match(
    /\b(?:typically|usually|most often)\s+affects?\s+(.+?)\s+(unilaterally|bilaterally)\b/i,
  );
  if (locationAndLateralityMatch?.[1] && locationAndLateralityMatch?.[2]) {
    const laterality = /bilaterally/i.test(locationAndLateralityMatch[2]) ? "bilateral" : "unilateral";
    pushNote(
      buildContentNote(
        `${title} most often involves {{c1::${trimTerminalPunctuation(locationAndLateralityMatch[1])}}} and is usually {{c2::${laterality}}}.`,
        batchTag,
      ),
    );
  } else if (insights.distribution) {
    const distributionAnswer = trimTerminalPunctuation(
      insights.distribution
        .replace(new RegExp(`^${title.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s+`, "i"), "")
        .replace(/^(typically affects|usually affects|most often affects)\s+/i, ""),
    );
    if (distributionAnswer) {
      pushNote(
        buildContentNote(
          `${title} typically affects {{c1::${distributionAnswer}}}.`,
          batchTag,
        ),
      );
    }
  }

  if (insights.radiographFindings) {
    pushNote(
      buildContentNote(
        `In ${title}, radiographs typically show {{c1::${compactFindingText(insights.radiographFindings)}}}.`,
        batchTag,
      ),
    );
  }

  if (insights.ctFindings) {
    pushNote(
      buildContentNote(
        `In ${title}, CT typically shows {{c1::${compactFindingText(insights.ctFindings)}}}.`,
        batchTag,
      ),
    );
  }

  if (insights.mriFindings) {
    pushNote(
      buildContentNote(
        `In ${title}, MRI typically shows {{c1::${compactFindingText(insights.mriFindings)}}}.`,
        batchTag,
      ),
    );
  }

  if (insights.managementFrom && insights.managementTo) {
    pushNote(
      buildContentNote(
        `In symptomatic ${title}, management ranges from {{c1::${trimTerminalPunctuation(insights.managementFrom)}}} to {{c2::${trimTerminalPunctuation(insights.managementTo)}}}.`,
        batchTag,
      ),
    );
  }

  buildPathogenesisNotes(article, title, batchTag, pushNote);
  buildFigureEvidenceNotes(article, title, batchTag, pushNote);

  for (const diagnosisFigure of pickDiagnosisFigures(article)) {
    pushNote(
      buildImageDiagnosisNote(title, diagnosisFigure.localImageName, batchTag),
    );
  }
}

function buildTechniqueNotes(article, insights, batchTag, pushNote) {
  const title = insights.subject;
  const sentences = insights.sentences || [];

  const leadSentence = insights.rawSentences.leadSentence || "";
  const conceptSentence = findSentence(sentences, /\bliquid embolic agent\b/i) || leadSentence;
  const conceptAnswer = /\bliquid embolic agent\b/i.test(conceptSentence)
    ? "liquid embolic agent"
    : trimTerminalPunctuation(conceptSentence.match(/\bis (?:a|an)\s+(.+?)(?:\.|$)/i)?.[1] || "");
  if (conceptAnswer) {
    pushNote(
      buildContentNote(
        `${title} is a {{c1::${conceptAnswer}}}.`,
        batchTag,
      ),
    );
  }

  const polymerizationSentence = findSentence(sentences, /\bpolymerizes on contact with\b/i);
  const polymerizationMatch = polymerizationSentence?.match(/\bpolymerizes on contact with\b\s+(.+?)(?:,|\.|$)/i);
  if (polymerizationMatch?.[1]) {
    pushNote(
      buildContentNote(
        `${title} rapidly polymerizes on contact with {{c1::${trimTerminalPunctuation(polymerizationMatch[1])}}}.`,
        batchTag,
      ),
    );
  }

  const mixingSentence = findSentence(sentences, /\bmixing\b.+\bwith\b.+\bto\b/i);
  const mixingMatch =
    mixingSentence?.match(/\bmixing\b.+?\bwith\b\s+(.+?)\s+\bto\b\s+(.+?)(?:\.|$)/i) ||
    mixingSentence?.match(/\bmixed with\b\s+(.+?)\s+\bto\b\s+(.+?)(?:\.|$)/i);
  if (mixingMatch?.[1] && mixingMatch?.[2]) {
    pushNote(
      buildContentNote(
        `In ${title}, NBCA is mixed with {{c1::${trimTerminalPunctuation(mixingMatch[1])}}} to {{c2::${trimTerminalPunctuation(mixingMatch[2])}}}.`,
        batchTag,
      ),
    );
  }

  const flushSentence =
    findSentence(sentences, /\bflushed with\b.+\b5%\s*dextrose\b/i) ||
    findSentence(sentences, /\b5%\s*dextrose\b.+\bprevent premature polymerization\b/i);
  const flushMatch =
    flushSentence?.match(/\bflushed with\b\s+(.+?)(?:\s+to\b|,|\.|$)/i) ||
    flushSentence?.match(/\bwith\b\s+(.+?)(?:\s+to prevent premature polymerization|,|\.|$)/i);
  if (flushMatch?.[1]) {
    const flushAnswer = /5%\s*dextrose/i.test(flushMatch[1]) ? "5% dextrose" : flushMatch[1];
    pushNote(
      buildQuestionAnswerNote(
        `What solution should be used to flush the microcatheter before ${title}?`,
        flushAnswer,
        batchTag,
      ),
    );
  }

  const salineSentence = findSentence(sentences, /\b(normal saline|ionic solutions)\b.+\b(premature|early)\b.+\b(polymerization|solidification)\b/i);
  if (salineSentence) {
    pushNote(
      buildContentNote(
        `Before ${title}, normal saline should be avoided because it can {{c1::induce premature NBCA polymerization}}.`,
        batchTag,
      ),
    );
  }

  const useSentence = insights.rawSentences.useCaseSentence || findSentence(sentences, /\bespecially effective\b/i) || "";
  const useMatch = useSentence.match(/\bespecially effective\b(?:\s+in|\s+for)?\s+(.+?)(?:\.|$)/i);
  if (useMatch?.[1]) {
    const useAnswer = compactFindingText(useMatch[1]);
    pushNote(
      buildContentNote(
        `${title} is especially useful for {{c1::${useAnswer}}}.`,
        batchTag,
      ),
    );
  }

  const riskSentence = insights.rawSentences.riskSentence || findSentence(sentences, /\brisk of\b/i) || "";
  const riskMatch = riskSentence.match(/\brisk of\b\s+(.+?)(?:,|\.|$)/i);
  if (riskMatch?.[1]) {
    const riskAnswer = trimTerminalPunctuation(
      riskMatch[1].replace(/\s+remains\b.+$/i, ""),
    );
    const suffix = /tissue necrosis|ischemia/i.test(riskSentence)
      ? " and can cause tissue necrosis or ischemia"
      : "";
    pushNote(
      buildContentNote(
        `A major complication of ${title} is {{c1::${riskAnswer}}}${suffix}.`,
        batchTag,
      ),
    );
  }

  const pearlSentence =
    findSentence(sentences, /\bunderstanding of the vascular anatomy and hemodynamics is essential\b/i) ||
    findSentence(sentences, /\bsuccessful outcomes rely on\b/i) ||
    insights.rawSentences.technicalPearlSentence ||
    "";
  const pearlMatch =
    pearlSentence.match(/\bis essential to\b\s+(.+?)(?:\.|$)/i) ||
    pearlSentence.match(/\brely on\b\s+(.+?)(?:\.|$)/i);
  if (pearlMatch?.[1]) {
    const answer = compactFindingText(pearlMatch[1]);
    const stem = /\bis essential to\b/i.test(pearlSentence)
      ? `During ${title}, understanding vascular anatomy and hemodynamics is essential to`
      : `Successful outcomes with ${title} rely on`;
    pushNote(
      buildContentNote(
        `${stem} {{c1::${answer}}}.`,
        batchTag,
      ),
    );
  }
}

function buildArticleNotes(article, dateLike = new Date()) {
  const batchTag = buildBatchTag(article, dateLike);
  const insights = extractArticleInsights(article);
  const notes = [];
  const seen = new Set();

  function pushNote(note) {
    const text = normalizeWhitespace(note.content || note.html || "");
    const key = text.toLowerCase();
    if (!text || seen.has(key) || noteWordCount(text) > 42) {
      return;
    }

    note.id = `note-${String(notes.length + 1).padStart(3, "0")}`;
    notes.push(note);
    seen.add(key);
  }

  if (insights.mode === "technique") {
    buildTechniqueNotes(article, insights, batchTag, pushNote);
  } else {
    buildDiseaseNotes(article, insights, batchTag, pushNote);
  }

  if (notes.length === 0) {
    for (const section of article.summarySections || []) {
      pushNote(
        buildContentNote(
          `${section.label} for ${insights.subject} includes {{c1::${trimTerminalPunctuation(section.text)}}}.`,
          batchTag,
        ),
      );
      if (notes.length >= 3) {
        break;
      }
    }
  }

  validateNotes(notes, batchTag);
  return {
    batchTag,
    notes,
  };
}

function validateNotes(notes, batchTag) {
  const seenIds = new Set();
  const allowedKeys = new Set(["content", "html", "tags", "id"]);

  for (const note of notes) {
    for (const key of Object.keys(note)) {
      if (!allowedKeys.has(key)) {
        throw new Error(`Invalid note key: ${key}`);
      }
    }

    const hasContent = typeof note.content === "string";
    const hasHtml = typeof note.html === "string";
    if ((hasContent ? 1 : 0) + (hasHtml ? 1 : 0) !== 1) {
      throw new Error("Each note must have exactly one of content or html.");
    }

    if (!Array.isArray(note.tags) || note.tags.length !== 1 || note.tags[0] !== batchTag) {
      throw new Error("Each note must contain exactly one batch tag.");
    }

    if (note.id) {
      if (seenIds.has(note.id)) {
        throw new Error(`Duplicate note id: ${note.id}`);
      }
      seenIds.add(note.id);
    }

    const text = note.content || note.html;
    if (!/\{\{c\d+::/.test(text)) {
      throw new Error(`Note is missing cloze syntax: ${text}`);
    }
    if (noteWordCount(text) > 42) {
      throw new Error(`Note is too wordy for review: ${text}`);
    }
    if (/->|=>|â†|â†’|â†”/.test(text)) {
      throw new Error(`Note contains arrow notation: ${text}`);
    }
    if (/Most likely diagnosis\?/i.test(text) && !/<img\b/i.test(text)) {
      throw new Error(`Diagnosis note is missing an image: ${text}`);
    }
    if (
      /\b(high-yield figure from the article|key teaching point|which .* pattern suggests|not yet been well established)\b/i.test(
        text,
      )
    ) {
      throw new Error(`Note failed quality filter: ${text}`);
    }
  }
}

module.exports = {
  buildAnkiNotes: buildArticleNotes,
  buildBatchTag,
  validateNotes,
};
