# Study OS Nightly Orchestration

This is the execution contract for the single 9 p.m. Study OS automation. The automation must work sequentially, persist its progress, and give the bedtime-sensitive card work first priority without allowing one failed artifact to consume or block the rest of the nightly packet.

## Known local resources

- Canonical Core Radiology PDF: `G:\My Drive\0. Radiology\Core Radiology 2nd ed.pdf`
- Text source root: `apps/core-studying/Core_Radiology`
- Canonical card preferences: `CARD_STYLE_GUIDE.md`, `APKG_PACKAGING.md`, `CORE_RADIOLOGY_WORKFLOW.md`, `BOARDVITALS_WORKFLOW.md`, and `VISUAL_STUDY_AND_ANKI_SPEC.md`
- `settings.anki_card_preferences` is an optional user override. If it is missing or blank, use the canonical files above; never fail or defer card creation merely because the setting is absent.
- All private Sites API and media verification requests must include the current SIWC bypass authorization header. An unauthenticated `401` or failed private-media probe is not evidence that uploaded media is missing.

## Durable run ledger

At the beginning of every run, create or resume:

`C:\Users\sterl\OneDrive\Study OS Private\nightly-runs\YYYY-MM-DD\run.json`

The ledger must contain the local run date, start/update timestamps, and these ordered phases:

1. `cards`
2. `coaching`
3. `tomorrow_packet`
4. `finalize`

Each phase and artifact has a stable id and a status of `pending`, `running`, `complete`, `failed`, or `skipped`. Record output identifiers, verification evidence, errors, and retry counts. Write the ledger atomically after every meaningful transition. On a rerun, inspect the ledger and the authoritative destination; reuse only outputs that still pass readback verification.

The ledger is coordination state, not proof by itself. Database/API/media readback is the completion authority.

## Phase 1 — Cards first

Before beginning quiz, audio, or visual generation, process the bedtime-sensitive Anki material:

- unprocessed saved questions and key points from any date;
- unprocessed visual saves from any date;
- newly eligible Notion Radiology entries whose `Created time`, interpreted in `America/Chicago`, falls on the current study date or one of the preceding six local calendar dates and whose `Anki Card` property is `Needed`;
- previously admitted Notion page ids that remain unresolved in the run ledger, even if they have since aged beyond that seven-date window.

Generate candidates under the canonical card instructions, upload required media, GET-verify candidates and media, and publish the usable candidates to the Study OS reviewer as soon as this phase is complete. Mark incorporated study-event ids processed only after verification.

Notion-derived candidates belong in the Cards Reviewer. For each Notion page, update `Anki Card` from `Needed` to `Created` only after all candidates and required media for that page have passed destination readback; then read the Notion page back and verify `Created`. A query count or prose report is not completion. Leave failed pages `Needed` and in the retry ledger. Do not silently expand this nightly scope to the older historical `Needed` backlog.

When a Notion entry says that images are in comments or discussions, preserve the discussion relationship as source data. Map every attachment through its exact `(page id, discussion id, comment id, anchored text, attachment id)` container before drafting cards. Never flatten all images on the page, infer comment membership from global DOM order, or substitute similarly shaped body images. Record the mapping in the run manifest. A normal or contralateral comparison belongs in `Extra`, not as an unrelated Front image. Do not create a generic multi-image case card by pooling images that belong to separate abnormal findings unless the user explicitly requested a diagnosis-level composite. Verification must include a labeled 100% contact sheet or equivalent visual review proving that each stored Front and Extra image still matches its anchored finding; successful byte retrieval alone is not semantic verification. Any unlabeled, ambiguous, or user-marked `double check` attachment fails closed until its target is visually confirmed. The Notion page must remain `Needed` when any required comment-image relationship is unresolved.

Use a distinct stable `(sourceType, sourceId)` pair for every generated candidate. For a Notion page that produces multiple cards, use a compound source id containing the page id and candidate ordinal; never reuse the raw page id for every candidate. After upsert, compare the entire expected candidate-id set and expected per-page count with the destination. The API accepting the request is not proof that every row survived uniqueness constraints. Missing candidates block only their source page and must be repaired before that page can become `Created`.

For every saved pathology image, audit the source caption and image annotations before completing its event. If the image supports a diagnosis and contains established arrow targets, Phase 1 is incomplete until the reviewer contains one diagnosis candidate and one separate candidate for every separately identifiable arrow target, with all required Front and Extra media verified. Do not suppress this mandatory set as redundant; the user makes the keep/discard decision.

Resolve textbook pages from the known Core Radiology PDF and the stored assignment/page provenance. Do not describe the PDF or screenshots as unavailable until the canonical `G:` path has been checked directly. A page-resolution or media problem for one event blocks only that event: publish and process every other independently valid candidate, and leave only the unresolved event pending with a specific reason.

Do not begin Phase 3 until Phase 1 is either:

- `complete`, with verified candidates available to the user; or
- `failed`, after reasonable repair attempts, with an exact blocking error recorded in the ledger and report.

A Phase 1 failure must never be silently treated as completion.

This gate controls ordering, not global success. Once the bounded card attempt is complete or has recorded its per-event failures, continue to Phase 3 with a fresh attention budget. Never skip quiz generation because card creation failed.

## Phase 2 — Anki Coaching

Generate the coaching report from Notion, Speed Streak Review Later, and Pocket Knife Study Repair according to `ANKI_COACHING_WORKFLOW.md`. Publish and read back the report. This phase may reuse the verified Notion candidates from Phase 1 and must not duplicate them.

This phase is complete only when its eligible Review Later and Study Repair items receive actual concept teaching and contextualization. Operational status, source counts, and Phase 1 card summaries may be included as secondary metadata but cannot replace the teaching. If the required local Anki snapshot is missing or stale, record coaching as `partial` or `failed` with the exact reason; never upload a pipeline report under the Anki Coaching title and mark the phase complete.

Filter Review Later by absolute `addedAt` timestamps converted to the report date in `America/Chicago`, then deduplicate overlap with Study Repair for teaching while preserving each cohort's independent source count. Record both the unique-card count and the two source counts. Verify that the published `contentText` contains actual card-specific teaching rather than only a status summary.

## Phase 3 — Tomorrow's packet

Resolve tomorrow's active assignment, then independently prepare and verify its quiz, audio, and visual feed. Each artifact remains idempotent: reuse a complete matching artifact and repair only missing, incomplete, changed, or explicitly forced work. A failure in one artifact must not prevent attempts on the others.

Treat the full quiz, quick quiz, audio, and visual feed as four independent subphases with their own start, verification, and failure entries. Complete the full and quick quiz before starting TTS. Quiz generation is mandatory when matching sessions are absent; a prior phase failure is not a reason to report them absent without generating them.

For TTS shell execution, use `scripts/generate-tts.mjs --concurrency 30` (30 is also the generator default and hard maximum) so all available chunks generate in parallel. Preserve numbered WAV parts, per-part validation, deterministic source-order assembly, and the single final 24 kHz mono 128 kbps MP3 encode; concurrency must never change splice order or reintroduce direct MP3 joining. Allow at least 10 minutes (`timeout_ms >= 600000`) for retries and final encoding. Reuse already generated valid parts on repair when possible. A one-minute shell timeout is a workflow defect, not an audio-generation failure.

For visual verification, first GET the feed and every media URL with the SIWC bypass header. Panel `imageUrl` values may be relative paths such as `/api/visual-media/<id>`; resolve them against `https://radiology-study-os.glut4.chatgpt.site` before requesting them. An invalid-URI result from treating a relative path as a complete URL is a verifier bug, not missing media. Do not force-reupload a complete matching feed merely because an unauthenticated or malformed media request failed. Reupload only panels that remain missing or corrupt after correctly resolved, authenticated retrieval.

Visual extraction fails closed. Split every diagnostic panel into its own tightly cropped feed item, even when several panels share one figure number or caption. Do not upload combined radiograph/CT/MR/ultrasound panels, captions, headings, page prose, page numbers, neighboring figures, or excess page whitespace. A combined item is allowed only for a genuinely inseparable comparative schematic with shared labels, and it must be declared as `kind: comparison diagram`. Every item requires source figure/panel metadata and affirmative single-panel/no-page-text QA. Before upload, build and inspect a contact sheet containing 100% of the proposed items and run PDF-text-intersection validation; any questionable crop blocks the upload. After upload, verify the exact revision id, the entire expected panel-id set, expected count, and authenticated nonzero-byte retrieval of every image. If the API cannot delete stale panels from an existing feed, use a new revision feed id and verify that it is the active feed for the date rather than mixing corrected and stale panels.

For quiz questions, stems, answer choices, and explanations, present the medical content directly. Do not say `according to the source`, `in the source`, `based on the reading`, `the text states`, or use equivalent source-framing language. It is already understood that the quiz is constrained to the supplied material. This rule does not relax source-only generation: do not add outside knowledge or unsupported claims.

## Phase 4 — Finalize

- Update a Notion entry from `Needed` to `Created` only after all cards and required media attributable to it have passed verification; read the page back to verify the property.
- Run the portable backup and verify its report.
- Produce one concise run report listing each phase and artifact as reused, generated, repaired, skipped, or failed.

## Attention and quality rules

- Finish and verify one phase before advancing; do not draft all outputs superficially in one pass.
- Use deterministic scripts for extraction, TTS, uploads, packaging, and backups. Use model reasoning for source interpretation, question writing, card construction, image understanding, coaching, and repair decisions.
- Do not reduce question/card/image quality to make the run appear complete.
- Preserve partial verified success. Never delete a good artifact merely because a later phase failed.
- Never invent source content, completion evidence, or successful readback.
- In both quiz and card prose, treat supported source content as the operative truth for the exercise and omit unnecessary source-framing phrases.
- Use bounded work queues. Process Study OS saved events before the general Notion backlog. A large Notion backlog must not prevent the current day's saved cards or tomorrow's quiz/audio/visual packet from being produced.
- Never summarize an artifact as merely absent when the task is to create it. Attempt creation, verification, and one targeted repair before recording failure.
