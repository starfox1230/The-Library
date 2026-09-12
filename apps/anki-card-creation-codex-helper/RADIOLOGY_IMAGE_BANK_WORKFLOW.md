# Radiology Image Bank workflow

Use this for deliberate, high-volume visual recognition practice. The current implementation is the **MSK Image Bank** prototype; the intended broader system is **Radiology Image Bank — Rapid Visual Review**.

This is an as-needed study route with two activities:

1. **Curate:** deliberately build a visual library for a few diagnoses.
2. **Review:** move quickly through the collected images to strengthen recognition and radiology description.

It is a separate visual-learning system from the text-focused StudyOS routes. It can eventually send selected images to Anki, but Anki is not required for an Image Bank session to be useful.

## Open the current prototype

Desktop curation tool:

```powershell
Set-Location 'C:\Users\sterl\Documents\GitHub\The-Library\apps\temporary-apps\library\2026-09-02-msk-image-bank'
.\launch.ps1
```

If the PySide6 dependency has not been installed:

```powershell
py -m pip install -r 'C:\Users\sterl\Documents\GitHub\The-Library\apps\temporary-apps\library\2026-09-02-msk-image-bank\requirements.txt'
```

Phone or browser review:

https://starfox1230.github.io/The-Library/apps/temporary-apps/library/2026-09-02-msk-image-bank/mobile/

The detailed product plan is the Notion page **Radiology Image Bank — Rapid Visual Review**:

https://app.notion.com/p/3d11d7063539813cadcacb537582d123

## Curate a few diagnoses

1. Choose a diagnosis in the desktop MSK Image Bank.
2. Open its Google Images searches. XR, CT, and MRI searches are available in the current MSK prototype.
3. Paste screenshots, drag local images, or drop image URLs into the appropriate modality panel.
4. Keep multiple examples so the bank shows the breadth of appearances and meaningful overlap with mimics.
5. Add a short caption or source note when useful.
6. Refine the concise modality-specific report wording.
7. Favorite the best individual images. Pathology-level Favorite currently acts as a rough collection marker; a separate completion state is planned.
8. Click **Publish mobile** when the phone review copy should be updated. The app writes the mobile bundle, commits only that bundle, and pushes the current Git branch.

The act of choosing examples is part of the study session. Do not assume that automatically collecting every available image would preserve the same learning value.

## Review the bank

Open the mobile URL, choose a pathology, and swipe or scroll through its images. The current mobile viewer fills the screen and prevents ordinary document scrolling. It advances image by image within the selected pathology.

Use the images to practice:

- rapid recognition of a diagnosis or imaging finding;
- the range of its appearances across patients and modalities;
- overlap with important mimics and differentials;
- a concise way to describe the finding in a radiology report.

## Current state — September 6, 2026

| Item | Verified state |
|---|---|
| Starter list | 54 MSK diagnoses in six groups |
| Local curation state | 115 images across 10 populated diagnoses |
| Local favorite images | 97 |
| Published mobile bundle | 111 images across nine populated diagnoses; 52 diagnoses present in the bundle |
| Local unpublished difference | Mazabraud syndrome has four local images that are not in the current mobile bundle |
| Current mobile navigation | One selected pathology at a time; swipe, wheel, or arrow between its images |
| Desktop tests | Two tests pass |

The local state lives under:

`C:\Users\sterl\AppData\Local\MSK Image Bank`

The published bundle lives under:

`C:\Users\sterl\Documents\GitHub\The-Library\apps\temporary-apps\library\2026-09-02-msk-image-bank\mobile`

## Planned expansion

These are intended features and should not be described as current behavior:

- Generalize from the MSK prototype to a radiology-wide Image Bank.
- Use *Core Radiology* chapter by chapter to generate the diagnosis checklist and starter findings/report wording.
- Keep chapter or subspecialty as the main grouping and diagnosis as the main container; treat modality primarily as metadata.
- Add explicit pathology status such as empty, in progress, and adequately populated.
- Add per-image **Flag for Anki**, **Best example**, and review history separate from Favorite.
- Add a rapid reveal step for diagnosis, one to three features, and concise report wording.
- Add randomized, chapter-specific, favorites, unreviewed, least-recently-seen, and continuous cross-pathology review.
- Add optional auto-advance or slideshow behavior for low-energy review and AirPlay to Apple TV.

The most useful next product change is a continuous review queue that can move between pathologies. That resolves the current one-pathology-at-a-time limitation and creates the low-effort endless-review mode Sterling described. The Core Radiology inventory can then expand the content systematically.

## Relationship to Anki

The current app supports Favorite but does not yet have a distinct per-image Anki flag or automatic Anki export. The future route is:

`individual image flagged for Anki → existing visual-card candidate/media workflow → review candidate → APKG → Anki import verification`

Do not create cards from every image. An Image Bank is valuable as direct visual practice; send only especially useful images or distinct testable concepts to Anki.

## Commands for a new conversation

To open this route:

```text
$radiology-study Open my Radiology Image Bank route.
```

To continue building it:

```text
$radiology-study Help me curate the next few diagnoses in my Radiology Image Bank.
```

To work on the app itself:

```text
Continue the Radiology Image Bank project from the current MSK Image Bank prototype. Read RADIOLOGY_IMAGE_BANK_WORKFLOW.md and the linked Notion plan before changing the app.
```
