# Canonical Visual Study and Anki Specification

Use this as the source of truth for the Radiology Study OS visual feed, textbook-image extraction, visual Anki candidate generation, image handling in the card reviewer, and image-aware APKG export.

This file extends, but does not replace:

- `CARD_STYLE_GUIDE.md` for card-writing quality.
- `APKG_PACKAGING.md` for package, media, manifest, note-type, and build behavior.
- `CORE_RADIOLOGY_WORKFLOW.md` for Core Radiology source handling.
- `BOARDVITALS_WORKFLOW.md` for quiz-image capture and annotated-image safeguards.

When visual behavior changes, update this file first and make automations and apps point here instead of relying on conversation memory.

## Product Goals

The visual system has two distinct jobs:

1. Prepare an appealing, low-effort visual review of the assigned reading.
2. Turn selected, diagnostically useful images into reviewable Anki card candidates.

The visual feed is study material, not an obligation and not an automatic Anki deck. Image-backed cards remain candidates until the user reviews and saves them.

## Nightly Timing Contract

The 9 PM workflow performs two independent passes.

### Prepare tomorrow

- Locate tomorrow's exact assigned Core Radiology chunks and PDF pages.
- Extract and organize the associated figures for tomorrow's visual feed.
- Publish the feed before the study day begins.
- Do not automatically create Anki cards merely because tomorrow's figures exist.

### Process completed study signals

- Process pending saved questions, highlights, notes, and visual-feed interactions from today and earlier dates.
- A late save from a prior day belongs in the next unprocessed Anki batch.
- Use stable source IDs and the processed-event ledger so reruns are idempotent.
- Never import directly into Anki. Draft candidates for review, save, APKG download, and user-controlled import.

## Source Priority

For the initial Core Radiology implementation:

1. Use the user's accessible `Core Radiology 2nd ed.pdf`.
2. Include every extractable figure from the assigned page range or record it in an extraction-failure manifest.
3. Preserve figure number, PDF page, section, caption for analysis, and source coordinates when available.
4. Keep copyrighted textbook images private to the authenticated Study OS and Anki package.

External image search is a later phase. Do not silently substitute online images when textbook extraction fails. Future external examples must preserve source URL, attribution, license/usage status, modality, and confidence.

## PDF Figure and Panel Handling

- Preserve the complete figure or composite first.
- When a figure contains multiple educational panels, the feed may then present the panels in source order with panel-specific explanations.
- Keep panels together on one Anki card only when the complete set is needed to answer the prompt, such as paired modalities, pre/post comparison, or a multi-view diagnosis.
- Otherwise, separate panels may become separate feed items or card candidates when each independently tests a useful visual concept.
- Never crop away anatomy, distribution, multiplicity, comparison information, or another panel required for diagnosis.
- Never include caption text in a front-side diagnostic image.
- Annotated or answer-revealing versions belong in `Extra` unless the prompt explicitly asks about the indicated structure or finding.

The Study OS reviewer does not need a panel-segmentation, zoom, or crop editor. Panel extraction and initial grouping occur upstream. If advanced editing is needed, the user may do it outside Study OS and paste or upload the finished image.

## Daily Visual Feed

Each study day should have a stable, date-addressable visual feed. The default route opens the current study day and supports navigation to generated prior or future days.

The feed should be mobile-first, dark, vertically scrollable, and image dominant. It should feel like an appealing substitute for social-media scrolling rather than another formal assignment.

### Figure story format

A multi-panel figure may appear as a short sequence:

1. Complete figure or composite.
2. First useful panel and what to notice.
3. Subsequent panels in source order.
4. A concise synthesis or comparison when valuable.

### Feed item content

Each item should support:

- Large actual imaging or a diagram.
- Pinch-to-zoom or full-screen viewing in the feed itself.
- Modality and anatomy.
- A short `What to notice` explanation.
- Optional tap-to-reveal diagnosis or finding.
- Figure number, PDF page, and section.
- Full-figure or panel position when applicable.
- One-tap save/love and difficult signals.
- Optional user note.
- Copy or download of the best available source image.
- Link back to the relevant PDF location when possible.
- Whether the item has already contributed to an Anki candidate.

Saved state, notes, reveal state, and Anki-source links must synchronize across devices. Scroll position may remain device-local.

### Diagrams and schematics

- Include useful diagrams and schematics in the feed.
- Provide a high-quality copy/download action so the user can make an Image Occlusion note manually.
- Allow a `Good for image occlusion` signal.
- Do not automatically create image-occlusion cards in the initial pipeline.

## Canonical Visual Anki Card Types

### Diagnostic image card

Use actual imaging on the front with a direct prompt such as:

- `Most likely diagnosis?`
- `What named fracture is shown?`
- `What imaging finding is shown?`
- `What device is shown?`
- `What artifact is shown?`
- `What structure is indicated?`

Use the minimum clinical, anatomic, tracer, or modality context needed to make the answer unambiguous. Use one answer cloze. Follow all image-front rules in `CARD_STYLE_GUIDE.md`.

### Required multi-image case

- Put all required images on the front in a stable order.
- Put `1/N` immediately above the first image when more than one image is present.
- Use this only when the images jointly provide the diagnostic task.

### Separate representative-image cards

Create separate candidates when different images independently test useful appearances, modalities, or presentations. Avoid redundant near-duplicates.

### Image Multitude behavior

The user's legacy Image Multitude card can cycle among interchangeable examples, including with the `N` shortcut. This is a recognized prior preference but is not the default output until compatibility with the canonical `saCloze++` note type and APKG builder is explicitly implemented and tested.

### Arrow or label card

Create only when the user explicitly requests it, marks an image for it, or the learning task is genuinely structure/marker identification. Use a concrete prompt naming the marker and modality. Do not generate arbitrary caption-trivia cards.

### Supporting-image text card

For a nonvisual retrieval target, keep the concise cloze in `Text` and place useful figures, source-page context, and the short explanation in `Extra`.

### Diagram or anatomy occlusion candidate

Preserve the high-quality diagram and source link. Default to manual Image Occlusion creation. Do not automatically infer masks or generate occlusions in the initial version.

## Card Reviewer Image Requirements

The Cards reviewer must support image-backed candidates without turning into a full image editor.

### Required

- Render images in both `Text`/Front and `Extra`.
- Paste an image from the clipboard into whichever field currently has focus.
- Upload one or more JPG, PNG, WebP, or GIF images directly to Front or Extra.
- Show ordered image thumbnails for Front and Extra.
- Reorder images within either field.
- Remove an image from a field.
- Move or copy an image between Front and Extra with a simple control; ordinary copy/paste must also work.
- Preserve existing HTML editing, cloze controls, AI menu, tags, save/discard states, and fast optimistic interactions.
- Store media privately with stable filenames and synchronize candidates across devices.

### Explicitly out of scope for the reviewer

- Image cropping.
- Panel segmentation.
- Diagnostic/supporting/annotated/diagram classification controls.
- A full image-occlusion editor.
- Advanced pixel editing.

These operations may occur upstream or in a dedicated external tool.

## Media-Aware APKG Requirement

An image-containing saved card must download successfully as an APKG. Image support is not complete while the exporter rejects `<img>` tags.

The exporter must:

- Export only saved cards selected by the existing reviewer workflow.
- Resolve each Study OS image reference to its stored media object.
- Assign a stable local media filename.
- Rewrite card HTML to `<img src="filename.ext">` references.
- Include every referenced media file in the APKG media map.
- Preserve image order in Front and Extra.
- Reuse the canonical `saCloze++` model exactly.
- Use the `Saved Cards` deck.
- Validate that every HTML media reference resolves before claiming the APKG is ready.
- Fail clearly without deleting or altering the user's saved candidates.
- Preserve a machine-readable manifest linking candidate, media, feed item, figure, source page, and generation-spec version.

## Interaction-to-Anki Rules

- A saved/loved image is a strong signal, not an automatic command to create a card.
- A user note or `Difficult` mark increases priority and should guide the tested point.
- If the user explicitly selects `Use for Anki`, generate at least one candidate unless the image is unusable or ambiguous; report the reason when skipped.
- Deduplicate against existing candidates and previously exported source links.
- Preserve the exact feed item, image, concept, PDF page, and event IDs used to make each candidate.
- Late interactions from prior days remain eligible until processed successfully.

## Minimal Data Contract

Persist stable records for:

- Visual study day and generation status.
- Reading section and PDF page range.
- Concept and concise teaching point.
- Image asset, figure/panel identity, order, dimensions, hash, source, and private object key.
- Feed item and reveal/copy/save/difficult interactions.
- Card candidate media order for Front and Extra.
- Anki source links and processed-event IDs.
- Extraction failures and manual corrections.

Use content hashes and stable source coordinates to detect duplicates and make reruns repair the existing day instead of creating a second copy.

## Nightly Generation and Verification

For each tomorrow visual packet:

1. Resolve the active plan and exact PDF pages.
2. Extract embedded images and page renders needed for clean figures.
3. Produce a manifest of expected, extracted, and failed figures.
4. Associate figures with section text and captions.
5. Analyze actual image content and panel relationships.
6. Generate concise, source-grounded feed explanations.
7. Hash and deduplicate assets.
8. Upload private media and upsert the date's feed.
9. GET-verify the feed, item count, image count, and failure manifest.
10. Preserve the prior valid feed if regeneration fails.

### Early completion and rerun policy

- Before extraction or upload, GET the target date and compare the active assignment, stable feed id, expected panel count, and panel ids.
- If a matching feed is already complete and its images verify, reuse it and skip generation, extraction, TTS-adjacent work, and upload for that visual packet.
- If the matching feed is incomplete, repair only the missing or invalid work and verify it again.
- If the active assignment or source range changed, create the newly identified feed while preserving the prior feed in history.
- Rebuild an otherwise complete matching feed only when the user explicitly requests regeneration or a correction requires `--force`.
- Never replace a verified feed with a failed or partial rerun.

For each Anki batch:

1. Read all canonical card and visual specifications plus editable Study OS preferences.
2. Process pending events across all dates.
3. Draft source-linked image and text candidates with stable IDs.
4. Upload and verify all required media.
5. GET-verify candidate content and media associations.
6. Mark only incorporated events processed.

## Quality and Safety Gates

- Use only source-grounded diagnoses and findings.
- Do not claim an image shows a finding unsupported by its caption, surrounding text, or reliable analysis.
- Keep low-confidence matches out of automatic card generation.
- Never expose copyrighted textbook images through a public unauthenticated repository or URL.
- Never silently replace a failed textbook extraction with a generic online image.
- Keep corrections durable so regeneration does not undo the user's decisions.
- Every visual card must still pass the Smart Student Test and all canonical card-style validation.

## Initial Implementation Order

1. Build and approve this canonical specification.
2. Make the active nightly automation read it.
3. Run a one-section Core Radiology extraction/feed pilot.
4. Validate figure completeness, panel ordering, and explanations with the user.
5. Add Front/Extra paste, upload, reorder, remove, and move/copy behavior to the reviewer.
6. Implement media-aware APKG export.
7. Connect visual-feed interactions to the pending-event ledger.
8. Add external examples, Image Multitude, and optional automated occlusion only after the core pipeline is reliable.

## Near-Term Reuse Modes

The visual-feed generator must become a reusable pipeline, not a one-off MSK implementation.

### Scheduled Study-Plan Mode

- A study plan owns an ordered sequence of assignments across dates.
- Each assignment may point to a different chapter or even a different source PDF.
- Changing rotations or starting Neuro should create or activate another saved plan; it must not erase the MSK plan or its feed history.
- Codex should be able to build a new plan from a concise request plus a source/range, or import the existing Core Study plan JSON when the user wants its exact dates and chunking.
- The same extraction, explanation, storage, review, and Anki pathways are reused after only the source mapping and schedule change.

### Standalone Collection Mode

- A Radiographics article, conference handout, or miscellaneous PDF can produce one named visual collection without joining the daily calendar.
- Standalone collections use the same figure-story format, saved-panel events, and Anki media rules as scheduled feeds.
- Collections remain in a browsable history instead of replacing one another.
- A future Visuals library should separate `Daily plans` from `Collections` while allowing a direct link to any feed or collection.

The immediate interface may expose only daily feeds. Preserve plan, source, date, and collection identifiers now so these reuse modes can be added without rebuilding the pipeline.
