# Radionuclides Anki Reference Cards

Source: `apps/Radionuclides/deck.json` and associated local images.

- Deck: `Saved Cards`
- Note type: `saCloze++`
- Tag: `#AnkiChat::2026.05.26_Radionuclides`
- Radionuclides included: 21
- Notes generated: 84
- Media files packaged: 62

Each included radionuclide has four single-cloze notes covering production, decay,
principal photon energies, and half-life. The answer-side Extra field contains the
full reference summary, the main app image, and an Additional images section when
associated images exist in the app.

## Skipped

- Iodine-125: Main image is missing from the Radionuclides app: i-125.png

## Build

```powershell
python .\build_radionuclides_package.py
```

The generated `media/` folder and `.apkg` are kept locally for import but ignored by git
because the package embeds the source images and exceeds GitHub's 100 MB per-file limit.
