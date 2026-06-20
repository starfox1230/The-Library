# Speed Streak v1.23 Special Timing Test Deck

This folder builds a small Anki deck for testing the v1.23 Special Card Timing settings.

## Output

- `speed-streak-v1.23-special-timing-test.apkg`

## Cards

- Normal baseline card.
- Native Anki typed-answer card using `{{type:Answer}}`.
- Custom tag card with `speedstreak::extended_time`.
- Custom tag card with `speedstreak::untimed`.
- Typed-answer card with a custom tag for precedence testing.
- Official AnKingOverhaul one-by-one card with a populated `One by one` field.
- Official AnKingOverhaul one-by-one card with a custom tag for precedence testing.

## AnKing One-By-One Note

The test deck imports the official AnKingOverhaul front template, back template, and styling from the AnKing Note Types GitHub repository when the deck is built. It includes a real `One by one` field populated with `y`.

For your normal collection and full AnKing note-type management, install the AnKing Note Types add-on from AnkiWeb:

- Add-on code: `952691989`
- Page: https://ankiweb.net/shared/info/952691989

AnkiHub guidance currently describes the one-by-one feature as requiring the right AnKing note type, such as `B. Step by Step One`, plus content in the `One by one` field.

If the imported test note type conflicts with an existing local AnKing note type, import it into a disposable Anki profile first.

## Suggested Speed Streak Settings

Open `Tools -> Speed Streak -> Settings -> Special Card Timing`.

Suggested first pass:

- AnKing one-by-one: `Extra time`, question `0 s`, answer `15 s`
- Typed-answer cards: `Extra time`, question `15 s`, answer `0 s`
- Custom tag: `speedstreak::extended_time`, `Extra time`, question `0 s`, answer `15 s`

Suggested no-timeout pass:

- Custom tag: `speedstreak::untimed`, `No timeout`

## Build

```powershell
cd "C:\Users\sterl\OneDrive\Documents\GitHub\The-Library\apps\anki-companion-game\test-decks\speed-streak-v1.23-special-timing"
python .\build_speed_streak_timing_test_deck.py
```

Import the generated `.apkg` into Anki after installing Speed Streak v1.23.
