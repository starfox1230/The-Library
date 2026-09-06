# YouTube anatomy image cards

Use this route for a YouTube anatomy or radiology video whose displayed images can support structure-identification or localization cards.

## Start

The user supplies:

- the YouTube URL;
- a transcript, timestamped structure list, or the structures to include;
- any requested card pattern or scope.

If the source is still broad, first create a structure list with the first timestamp at which each structure is actually shown. Normalize obvious transcript errors, but do not invent structures from garbled text. Keep shoulder or background anatomy out of an elbow batch, for example, when it is mentioned but not demonstrated.

## Build the images

1. Obtain the video through the available local tooling.
2. Extract a frame at each selected timestamp.
3. Inspect the actual layout before choosing a crop. Crop the diagnostic or anatomy image panel and exclude the presenter, captions, controls, and unused video canvas.
4. Preserve one stable media filename per structure/timestamp and record the source URL and timestamp.
5. Visually inspect representative early, middle, and late crops before packaging the whole batch.

Crop geometry is batch-specific. Do not copy the wrist crop into another video without checking it.

## Build the cards

Read `CARD_STYLE_GUIDE.md` and `APKG_PACKAGING.md`. Use the user's real installed Anki notetype and its exact fields, templates, CSS, and model id; never create a lookalike model with the same name.

The established anatomy pattern is two prompts per selected structure when both are useful:

1. `Where is the [structure]?` with the cropped image and a visually blank cloze placeholder that still causes Anki to generate the card.
2. `What structure is this?` with the structure name as the cloze answer and the same cropped image.

Use `<br><br>` between the question, cloze, and image. Put a clickable timestamp link in Extra, for example `Source: <a href="VIDEO_URL_WITH_TIME">00:01:30</a>`.

Avoid producing two prompts when the image does not actually permit both tasks. Each image must show enough context for the question to be answerable.

## Package and verify

- Use the current Saved Cards packaging rules and one batch tag.
- Preserve a JSON or manifest mapping structure, timestamp, media filename, note identity, and source URL.
- Verify note/card count, packaged media count, deck, exact note-type metadata, and clickable Extra links.
- Treat APKG creation and Anki import as separate states. Check the local Anki collection by stable batch tag when import verification is requested.

## Existing examples

The prior wrist and elbow builders are in:

`C:\Users\sterl\Documents\Codex\2026-05-28\structure-first-timestamped-link-wrist-00`

They demonstrate frame extraction, crop inspection, use of the real installed note type, packaging, and import verification. They are historical batch implementations; use this current guide and the current shared card/packaging rules for a new video.
