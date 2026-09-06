# Anki Card Creation Codex Helper

This folder is the canonical home for Codex-facing Anki card creation instructions.

## Start with the study menu

Use [RADIOLOGY_STUDY_START_HERE.md](RADIOLOGY_STUDY_START_HERE.md) when deciding what to do. It separates the two most-days routes from lecture, Study Calendar, Study Library, YouTube anatomy, Review Later, and card-review routes. The installed `$radiology-study` skill opens and routes from that menu.

## Start a one-time run

Use [RUN_RADIOLOGY_CARDS.md](RUN_RADIOLOGY_CARDS.md) from any local Codex conversation, or invoke the installed `$radiology-cards` skill. Examples: `Run my Notion-to-Anki pathway once`, `Convert my selected daily facts`, or `Run the full nightly packet once`. These select different scopes; the launcher explains the defaults. The recurring scheduler stays separate.

Card-writing policy belongs in CARD_STYLE_GUIDE.md; eligibility belongs in the source workflow; package mechanics belong in APKG_PACKAGING.md. The launcher and skill point to those files rather than copying their content. ChatGPT Generator 3.0 and YT2's AI rewrite prompts are separately maintained.

When card behavior needs to change, edit the smallest relevant canonical file here:

- `CARD_STYLE_GUIDE.md` for how cards should be written.
- `RADIOLOGY_CONVERSATION_ANKI_WORKFLOW.md` for converting selected conversation-mined facts; daily synthesis is stored in the linked Notion workflow page.
- `APKG_PACKAGING.md` for package, media, manifest, and build rules.
- `CORE_RADIOLOGY_WORKFLOW.md` for Core Radiology textbook-specific behavior.
- `BOARDVITALS_WORKFLOW.md` for BoardVitals quiz capture, card generation, and local HTML quiz review behavior.
- `VISUAL_STUDY_AND_ANKI_SPEC.md` for visual feeds, PDF figure handling, image-backed card candidates, reviewer image behavior, and media-aware APKG requirements.
- `YOUTUBE_ANATOMY_ANKI_WORKFLOW.md` for timestamped frame extraction, image cropping, anatomy card construction, and import verification.

Other automations, apps, and workflow notes should point here instead of duplicating the rules.

## Canonical Paths

```text
C:\Users\sterl\Documents\GitHub\The-Library\apps\anki-card-creation-codex-helper\CARD_STYLE_GUIDE.md
C:\Users\sterl\Documents\GitHub\The-Library\apps\anki-card-creation-codex-helper\APKG_PACKAGING.md
C:\Users\sterl\Documents\GitHub\The-Library\apps\anki-card-creation-codex-helper\CORE_RADIOLOGY_WORKFLOW.md
C:\Users\sterl\Documents\GitHub\The-Library\apps\anki-card-creation-codex-helper\BOARDVITALS_WORKFLOW.md
C:\Users\sterl\Documents\GitHub\The-Library\apps\anki-card-creation-codex-helper\VISUAL_STUDY_AND_ANKI_SPEC.md
```

## Prior Art

These sources informed the canonical files but should not be edited as the primary source of card style:

```text
C:\Users\sterl\.codex\automations\anki-cards-needed-daily-roundup\automation.toml
C:\Users\sterl\Documents\GitHub\The-Library\apps\anki-pocket-knife\NOTION_RADIOLOGY_ANKI_AUTOMATION.md
C:\Users\sterl\Documents\GitHub\The-Library\apps\radiographics-review
```
