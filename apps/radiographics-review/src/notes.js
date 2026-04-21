const { normalizeWhitespace, splitSentences, uniqueBy } = require("./utils");

function chicagoDateStamp(dateLike = new Date()) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Chicago",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date(dateLike));
  const byType = Object.fromEntries(parts.filter((part) => part.type !== "literal").map((part) => [part.type, part.value]));
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

function removeTerminalPeriod(text) {
  return normalizeWhitespace(String(text || "").replace(/[. ]+$/g, ""));
}

function removeLeadingCue(text) {
  return normalizeWhitespace(
    String(text || "")
      .replace(/^\([A-Z,\s]+\)\s*/i, "")
      .replace(/^Figure\s+\d+\.?\s*/i, ""),
  );
}

function stripTrailingClause(text) {
  return normalizeWhitespace(
    String(text || "")
      .replace(/,\s*(although|but)\b.+$/i, "")
      .replace(/\s+(although|but)\b.+$/i, ""),
  );
}

function diagnosisQuestionForFigure(figure) {
  const caption = (figure.caption || "").toLowerCase();
  if (/\b(radiograph|radiographs|x-ray)\b/.test(caption)) {
    return "What diagnosis is suggested by this radiographic appearance?";
  }
  if (/\b(mri|mr image|mr imaging)\b/.test(caption)) {
    return "What diagnosis is suggested by this MRI appearance?";
  }
  if (/\b(ct|computed tomography)\b/.test(caption)) {
    return "What diagnosis is suggested by this CT appearance?";
  }
  if (/\b(ultrasound|sonography)\b/.test(caption)) {
    return "What diagnosis is suggested by this sonographic appearance?";
  }
  return "What diagnosis is shown in this figure?";
}

function buildQuestionNote(question, answer, batchTag, id, options = {}) {
  const parts = [
    normalizeWhitespace(question),
    `{{c1::${removeTerminalPeriod(answer)}}}`,
  ];

  if (options.imageName) {
    parts.push(`<img src="${options.imageName}">`);
  }

  return {
    content: parts.join("<br><br>"),
    tags: [batchTag],
    id,
  };
}

function buildSentenceNote(sentence, batchTag, id) {
  return {
    content: normalizeWhitespace(sentence),
    tags: [batchTag],
    id,
  };
}

function collectCaptionSentences(article) {
  return uniqueBy(
    (article.figures || [])
      .flatMap((figure) => splitSentences(figure.caption || "").map((sentence) => ({
        figure,
        sentence: removeLeadingCue(sentence),
      })))
      .filter((entry) => entry.sentence.length > 20),
    (entry) => entry.sentence.toLowerCase(),
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
      if (/\bphotograph\b/.test(lowered)) {
        score += 2;
      }
      if (/\b(pathophysiology|proposed causes|diagram|algorithm)\b/.test(lowered)) {
        score -= 6;
      }

      return {
        figure,
        score,
      };
    })
    .sort((left, right) => right.score - left.score);

  return ranked[0]?.score > 0 ? ranked[0].figure : null;
}

function buildArticleNotes(article, dateLike = new Date()) {
  const batchTag = buildBatchTag(article, dateLike);
  const title = article.title || "This article";
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

  const proseSentences = uniqueBy(
    (article.cleanedBodyBlocks || [])
      .flatMap((block) => splitSentences(block))
      .map((sentence) => normalizeWhitespace(sentence))
      .filter((sentence) => sentence.length > 20),
    (sentence) => sentence.toLowerCase(),
  );

  const characterizedSentence = proseSentences.find((sentence) => /\bcharacterized by\b/i.test(sentence));
  if (characterizedSentence) {
    const match = characterizedSentence.match(/\bcharacterized by\b\s+(.+?)(?:\.|$)/i);
    if (match?.[1]) {
      pushNote(
        buildQuestionNote(
          `Which tissue pattern defines ${title}?`,
          match[1],
          batchTag,
        ),
      );
    }
  }

  const distributionSentence = proseSentences.find((sentence) =>
    /\b(typically affects|usually affects|most often affects)\b/i.test(sentence),
  );
  if (distributionSentence) {
    const answer = distributionSentence
      .replace(/\b(It|This condition|The disease)\s+/i, "")
      .replace(/\b(typically affects|usually affects|most often affects)\b/i, "")
      .replace(/^\s+/, "");
    if (answer) {
      pushNote(
        buildQuestionNote(
          `What anatomic distribution is typical for ${title}?`,
          stripTrailingClause(answer),
          batchTag,
        ),
      );
    }
  }

  const radiographSentence = proseSentences.find((sentence) => /\b(radiograph|radiographs|x-ray)\b/i.test(sentence));
  if (radiographSentence) {
    const answer = removeTerminalPeriod(
      radiographSentence
        .replace(/^Radiographs?\s+(?:may\s+)?(?:show|demonstrate)\s+/i, ""),
    );
    if (answer) {
      pushNote(
        buildQuestionNote(
          `Which radiographic finding pattern suggests ${title}?`,
          answer,
          batchTag,
        ),
      );
    }
  }

  const ctSentence = proseSentences.find((sentence) => /\bct\b/i.test(sentence));
  if (ctSentence) {
    const answer = removeTerminalPeriod(
      ctSentence
        .replace(/^CT\s+shows\s+/i, "")
        .replace(/^Characteristic CT findings include\s+/i, ""),
    );
    if (answer) {
      pushNote(
        buildQuestionNote(
          `Which CT finding pattern suggests ${title}?`,
          answer,
          batchTag,
        ),
      );
    }
  }

  const mriSentence = proseSentences.find((sentence) => /\b(mri|mr image|mr imaging)\b/i.test(sentence));
  if (mriSentence) {
    const answer = removeTerminalPeriod(
      mriSentence
        .replace(/^MRI\s+shows\s+/i, "")
        .replace(/^At\s+(?:T1-weighted|T2-weighted)\s+MRI,\s*/i, "")
        .replace(/^On MRI,\s*/i, ""),
    );
    if (answer) {
      pushNote(
        buildQuestionNote(
          `Which MRI finding pattern suggests ${title}?`,
          answer,
          batchTag,
        ),
      );
    }
  }

  const managementSentence = proseSentences.find((sentence) =>
    /\b(treatment(?: options)? range(?:s)? from|management(?: options)? range(?:s)? from)\b/i.test(sentence),
  );
  if (managementSentence) {
    const match = managementSentence.match(/\brange(?:s)? from\b\s+(.+?)\s+\bto\b\s+(.+?)(?:\.|$)/i);
    if (match?.[1] && match?.[2]) {
      pushNote(
        buildSentenceNote(
          `Management for symptomatic ${title} ranges from {{c1::${removeTerminalPeriod(match[1])}}} to {{c2::${removeTerminalPeriod(match[2])}}}.`,
          batchTag,
        ),
      );
    }
  }

  const captionSentences = collectCaptionSentences(article);
  const proposedCauses = captionSentences.find((entry) => /\bproposed causes?\b/i.test(entry.sentence));
  if (proposedCauses) {
    const match = proposedCauses.sentence.match(/\b(.+?)\s+are the proposed causes?\b/i);
    if (match?.[1]) {
      pushNote(
        buildQuestionNote(
          `Which mechanisms are proposed causes of ${title}?`,
          match[1],
          batchTag,
        ),
      );
    }
  }

  const diagnosisFigure = pickDiagnosisFigure(article);
  if (diagnosisFigure) {
    pushNote(
      buildQuestionNote(
        diagnosisQuestionForFigure(diagnosisFigure),
        title,
        batchTag,
        undefined,
        { imageName: diagnosisFigure.localImageName },
      ),
    );
  }

  if (notes.length === 0) {
    for (const section of article.summarySections || []) {
      pushNote(
        buildQuestionNote(
          `What is an important point about ${title}?`,
          section.text,
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
    if (/->|=>|←|→|↔/.test(text)) {
      throw new Error(`Note contains arrow notation: ${text}`);
    }
  }
}

module.exports = {
  buildAnkiNotes: buildArticleNotes,
  buildBatchTag,
  validateNotes,
};
