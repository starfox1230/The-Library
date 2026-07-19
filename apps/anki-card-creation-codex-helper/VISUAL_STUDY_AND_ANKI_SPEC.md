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

- Treat a textbook figure and its individual image panels as different things. The daily feed must present each diagnostic radiograph, CT image, MR image, ultrasound image, photograph, or independently interpretable schematic panel as its own tightly cropped feed item in stable caption order. A shared figure number or caption is not permission to combine panels.
- Do not add a redundant complete composite to the feed when its component diagnostic panels have been extracted. Preserve the complete source figure privately for provenance and source-page reconstruction.
- A combined feed item is permitted only when the source is genuinely one coherent visual whose meaning depends on the side-by-side relationship, such as a single comparative schematic with shared labels. Record that exception explicitly as `kind: comparison diagram`; do not use the exception for multi-view diagnostic imaging.
- Keep panels together on one Anki card only when the complete set is needed to answer the prompt, such as paired modalities, pre/post comparison, or a multi-view diagnosis.
- Panel grouping on a later Anki card never changes the feed rule: the source panels remain separate feed items and may be assembled into one card only downstream.
- Never crop away anatomy, distribution, multiplicity, comparison information, or another panel required for diagnosis.
- Crop to the visual boundary. Never include page headings, body prose, bullets, captions, page numbers, neighboring images, or decorative page whitespace in a diagnostic image. Text that explains the image belongs in the item's `Caption`, `What to notice`, or provenance metadata—not in the crop.
- Embedded labels or annotations that are part of a diagram or image are allowed only when they are integral to that source panel. This exception must be declared; it never permits surrounding textbook prose.
- Annotated or answer-revealing versions belong in `Extra` unless the prompt explicitly asks about the indicated structure or finding.

Every extraction manifest must identify `sourceFigureId`, `sourcePanelIndex`, and `sourcePanelCount` for every item and must attest `qa.singleSourcePanel: true` and `qa.noSurroundingPageText: true`. For a figure with N diagnostic panels, the manifest must contain N corresponding feed items. Missing or duplicate panel indices are a failed extraction, not an acceptable partial feed.

The Study OS reviewer does not need a panel-segmentation, zoom, or crop editor. Panel extraction and initial grouping occur upstream. If advanced editing is needed, the user may do it outside Study OS and paste or upload the finished image.

## Daily Visual Feed

Each study day should have a stable, date-addressable visual feed. The default route opens the current study day and supports navigation to generated prior or future days.

The feed should be mobile-first, dark, vertically scrollable, and image dominant. It should feel like an appealing substitute for social-media scrolling rather than another formal assignment.

### Figure story format

A multi-panel figure appears as a short sequence of individually cropped panels in source order. The feed can repeat shared figure context in each item's metadata or add a concise text-only synthesis, but it must not use a combined page crop as a shortcut.

### Feed item content

Each item should support:

- Large actual imaging or a diagram.
- Pinch-to-zoom or full-screen viewing in the feed itself.
- Modality and anatomy.
- A short `What to notice` explanation.
- The exact source-figure caption, stored for every feed item and exposed behind a collapsed `Caption` disclosure so it remains available without cluttering the default feed. Preserve arrow colors, singular/plural wording, panel references, sequence names, and all finding-to-arrow mappings exactly. If the source has no separate prose caption, record that explicitly rather than inventing one.
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

- `What is the most likely diagnosis?`
- `What named fracture is shown?`
- `What imaging finding is shown?`
- `What device is shown?`
- `What artifact is shown?`
- `What structure is indicated?`

Use the minimum clinical, anatomic, tracer, or modality context needed to make the answer unambiguous. Use one answer cloze. Follow all image-front rules in `CARD_STYLE_GUIDE.md`.

For pathology imaging, default to one of the user's two established card forms:

1. A diagnosis card using `What is the most likely diagnosis?`, optionally preceded by one brief locking-context sentence.
2. An arrow card using `What is indicated by the [color] arrow(s)?`, with the complete arrow phrase colored to visually match the arrow in the image.

Both forms use prompt, two HTML line breaks, one answer cloze, two HTML line breaks, and then the image area.

### Required multi-image case

- Put all required images on the front in a stable order.
- Put `1/N` immediately above the first image when more than one image is present.
- Put each image on its own following line after the fraction.
- For the same patient shown with complementary views, modalities, sequences, or panels, normally include the full set required to understand the pathology.
- Use this only when the images jointly provide the diagnostic task. Arrow cards normally use one image unless the indicated finding truly requires more than one.

### Separate representative-image cards

Create separate candidates when different images independently test useful appearances, modalities, or presentations. Avoid redundant near-duplicates.

### Image Multitude behavior

The user's legacy Image Multitude card can cycle among interchangeable examples, including with the `N` shortcut. This is a recognized prior preference but is not the default output until compatibility with the canonical `saCloze++` note type and APKG builder is explicitly implemented and tested.

### Arrow or label card

Arrow-indicated pathology cards are a default supported type, not an exceptional type. Use the exact stem `What is indicated by the [color] arrow(s)?` when an arrow identifies a useful finding, structure, or manifestation. Color the complete arrow phrase with inline HTML to visually match the arrow. Do not generate arbitrary caption-trivia cards.

The original source caption is authoritative for what each arrow indicates. Whenever a saved pathology image supports a diagnosis and also contains at least one meaningful arrow whose target can be established from the caption or source context, candidate generation is mandatory and exhaustive: create one separate diagnosis candidate and one separate focused arrow candidate for every separately identifiable arrow target. Do this regardless of apparent redundancy, predicted card quality, or whether the generator believes the user will keep every candidate; the user decides which candidates to save or discard in the reviewer. Never substitute a single combined card for this required set. Multiple arrowheads that clearly function together as one plural annotation of the same target count as one arrow target and use `arrow(s)` appropriately; arrows that identify different targets, even on the same image or in the same color, require separate candidates. Do not create an arrow card only when the source does not establish what the arrow indicates or the mark is not a meaningful annotation.

### PDF source-page context in Extra

For every card derived from a textbook or article PDF, include the correct full screenshot of the source PDF page in `Extra`, after a concise explanation and source citation. This also applies to text-first and auto-generated-quiz cards, not only visual-feed cards. Preserve exact source-page mapping upstream; if multiple pages are genuinely required, include them in source order. If a page cannot be identified, captured, or stored, record the exception instead of guessing or silently omitting it.

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
- When only one image from a complementary same-patient set is saved and that image independently supports a fair card, respect the saved subset and make the single-image candidate; do not automatically add every neighboring panel.
- When the saved image would be ambiguous or diagnostically incomplete alone, add only the necessary unsaved companion image(s) from the same verified source set, or report why no fair candidate could be made.
- When all complementary images in a same-patient set are saved, normally create one deduplicated multi-image diagnosis candidate using the canonical `1/N` format rather than redundant diagnosis cards.
- When multiple saved images independently test distinct appearances or indicated findings, create separate focused candidates. Saving multiple near-duplicates must not produce redundant cards.
- Apply the mandatory caption-driven arrow-card rule independently of diagnosis grouping: if an image supports a diagnosis and contains established arrow targets, create one diagnosis candidate plus one focused candidate for every separately identifiable arrow target. These candidates must coexist even when they appear redundant; the user, not the generator, decides which to keep.
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
8. Render a contact sheet and visually inspect every crop at useful size. Confirm one source panel per item, complete anatomy, correct panel order, and zero surrounding page text. This is a required 100% review, not a spot check.
9. Run automated crop validation. Non-diagram crops must have zero intersecting extractable PDF text; integral diagram labels require an explicit `allowEmbeddedText` exception. Any uncertain crop fails closed and is not uploaded.
10. Upload private media and upsert the date's feed only after both reviews pass.
11. GET-verify the exact feed id, expected count, complete panel-id set, and successful nonzero-byte retrieval of every image.
12. Preserve the prior valid feed if regeneration fails.

### Early completion and rerun policy

- Before extraction or upload, GET the target date and compare the active assignment, stable feed id, expected panel count, and panel ids.
- If a matching feed is already complete and its images verify, reuse it and skip generation, extraction, TTS-adjacent work, and upload for that visual packet.
- If the matching feed is incomplete, repair only the missing or invalid work and verify it again.
- If the active assignment or source range changed, create the newly identified feed while preserving the prior feed in history.
- Rebuild an otherwise complete matching feed only when the user explicitly requests regeneration or a correction requires `--force`.
- When correcting a live feed and the storage API cannot prune obsolete panels, publish a new revision feed id, verify that it is the active newest feed for the date, and leave the prior feed only as inactive history. Never reuse an id if that would leave stale panels mixed into the corrected feed.
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
- The builder must reject missing/duplicate ids, absent source-panel metadata, false QA attestations, and disallowed PDF-text intersections. The uploader must reject count or panel-id mismatch, failed QA, duplicate ids, and any media retrieval failure.
- A successful upload response is insufficient. Completion requires authenticated readback of the exact revision and every expected image.
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
