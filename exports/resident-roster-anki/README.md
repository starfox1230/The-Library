# Resident Roster Visual Cloze Cards

Source: `AY26-27 Trainee Composite 11x17.pdf`, page 1, from Gmail message `19f15f2ef2778168`.

Output deck: `Saved Cards`

Note type style: `saCloze++`

Cards: 45

Media assets: 45 cropped resident portraits in `assets/`

Card layout: the cloze prompt appears above the portrait:

```html
Who is this resident? {{c1::Resident Name}}<br><img src="resident-roster-name.png">
```

Build command:

```powershell
python scripts\build_manifest_apkg.py --manifest exports\resident-roster-anki\notes.json --output exports\resident-roster-anki\resident-roster-visual-cloze.apkg
```

Artifacts:

- `notes.json`: manifest used by the existing APKG builder.
- `resident-roster-visual-cloze.apkg`: importable Anki package.
- `crop_preview_contact_sheet.jpg`: visual QA sheet for crop/name pairing.
- `resident_page.png`: rendered resident roster source page used for cropping.

Skipped material: page 2 of the PDF contains fellows, not residents.
