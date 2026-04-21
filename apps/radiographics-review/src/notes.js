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

function buildContentNote(content, batchTag) {
  return {
    content: normalizeWhitespace(content),
    tags: [batchTag],
  };
}

function buildImageDiagnosisNote(answer, imageName, batchTag) {
  return buildContentNote(
    `Most likely diagnosis?<br><br>{{c1::${trimTerminalPunctuation(answer)}}}<br><br><img src="${imageName}">`,
    batchTag,
  );
}

function pickDiagnosisFigure(article) {
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

      return {
        figure,
        score,
      };
    })
    .sort((left, right) => right.score - left.score);

  return ranked[0]?.score > 0 ? ranked[0].figure : null;
}

function buildDiseaseNotes(article, insights, batchTag, pushNote) {
  const title = insights.subject;

  const definitionSentence = insights.rawSentences.definingSentence || insights.rawSentences.leadSentence || "";
  const characterizedMatch = definitionSentence.match(/\bcharacterized by\b\s+(.+?)(?:\.|$)/i);
  if (characterizedMatch?.[1]) {
    pushNote(
      buildContentNote(
        `${title} is characterized by {{c1::${trimTerminalPunctuation(characterizedMatch[1])}}}.`,
        batchTag,
      ),
    );
  }

  if (insights.distribution) {
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
        `In ${title}, radiographs typically show {{c1::${trimTerminalPunctuation(insights.radiographFindings)}}}.`,
        batchTag,
      ),
    );
  }

  if (insights.ctFindings) {
    pushNote(
      buildContentNote(
        `In ${title}, CT typically shows {{c1::${trimTerminalPunctuation(insights.ctFindings)}}}.`,
        batchTag,
      ),
    );
  }

  if (insights.mriFindings) {
    pushNote(
      buildContentNote(
        `In ${title}, MRI typically shows {{c1::${trimTerminalPunctuation(insights.mriFindings)}}}.`,
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

  const diagnosisFigure = pickDiagnosisFigure(article);
  if (diagnosisFigure) {
    pushNote(
      buildImageDiagnosisNote(title, diagnosisFigure.localImageName, batchTag),
    );
  }
}

function buildTechniqueNotes(article, insights, batchTag, pushNote) {
  const title = insights.subject;
  const sentences = insights.sentences || [];

  const leadSentence = insights.rawSentences.leadSentence || "";
  const conceptMatch = leadSentence.match(/\bis (?:a|an)\s+(.+?)(?:\.|$)/i);
  if (conceptMatch?.[1]) {
    pushNote(
      buildContentNote(
        `${title} is a {{c1::${trimTerminalPunctuation(conceptMatch[1])}}}.`,
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

  const useSentence = insights.rawSentences.useCaseSentence || findSentence(sentences, /\bespecially effective\b/i) || "";
  const useMatch = useSentence.match(/\bespecially effective\b(?:\s+in|\s+for)?\s+(.+?)(?:\.|$)/i);
  if (useMatch?.[1]) {
    pushNote(
      buildContentNote(
        `${title} is especially useful for {{c1::${trimTerminalPunctuation(useMatch[1])}}}.`,
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
    const stem = /\bis essential to\b/i.test(pearlSentence)
      ? `During ${title}, understanding vascular anatomy and hemodynamics is essential to`
      : `Successful outcomes with ${title} rely on`;
    pushNote(
      buildContentNote(
        `${stem} {{c1::${trimTerminalPunctuation(pearlMatch[1])}}}.`,
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
    if (!text || seen.has(key)) {
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
    if (/->|=>|â†|â†’|â†”/.test(text)) {
      throw new Error(`Note contains arrow notation: ${text}`);
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
