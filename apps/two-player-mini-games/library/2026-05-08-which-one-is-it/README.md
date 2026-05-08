# Which One Is It?

`Which One Is It?` is a content-driven two-player mini-game for teaching children how to distinguish commonly confused visual pairs.

## Where It Lives

Playable game:

`apps/two-player-mini-games/library/2026-05-08-which-one-is-it/index.html`

Local builder:

`apps/two-player-mini-games/which-one-builder/`

Content files used by the game:

- `data/pairs.json`
- `images/<pair-id>/<label>/...`
- `audio/<pair-id>/...`

## Run The Mini-Game

Open:

`apps/two-player-mini-games/library/2026-05-08-which-one-is-it/index.html`

The game can also be launched from:

`apps/two-player-mini-games/index.html`

Controls:

- Player 1 left/right: `A` / `D`
- Player 1 continue: `W`
- Player 2 left/right: `ArrowLeft` / `ArrowRight`
- Player 2 continue: `ArrowUp`
- Continue also works with `Enter` or `Space`

## Run The Local Builder

From the repo root:

```powershell
cd apps\two-player-mini-games\which-one-builder
npm install
$env:OPENAI_API_KEY="your_api_key_here"
npm start
```

Then open:

`http://localhost:5178`

If `OPENAI_API_KEY` is not set, image/content editing still works, but audio generation will fail with a missing-key message.

## Add A New Pair

1. Start the builder.
2. Enter two labels, such as `butterfly` and `moth`.
3. Click `Create / Open Pair`.
4. Add teaching text and one distinguishing characteristic per line.
5. Click `Save Teaching Content`.
6. Paste images into the Side A or Side B paste boxes.
7. Click `Generate Missing Audio` when ready.

## Pasted Images

The builder accepts copied web images and screenshots from the clipboard. Click the side's paste box first, then paste.

Images are saved as WebP files with consistent names:

`images/<pair-id>/<label>/<label>_001.webp`

The builder updates `data/pairs.json` automatically after each save.

## Audio Generation

The builder uses the OpenAI Audio Speech endpoint through the local Node server. Defaults:

- Model: `gpt-4o-mini-tts`
- Voice: `sage`
- Concurrency: `5`

Override with environment variables:

```powershell
$env:WHICH_ONE_TTS_MODEL="gpt-4o-mini-tts"
$env:WHICH_ONE_TTS_VOICE="sage"
$env:WHICH_ONE_TTS_CONCURRENCY="5"
```

Generated audio is saved locally:

`audio/<pair-id>/prompt_<label>.mp3`

The builder updates the pair's `audio` paths in `data/pairs.json`.

Audio is split into two tiers:

- Top tier: `promptA`, `promptB`, `answerA`, `answerB`, `teachingPoint`
- Secondary: `labelA`, `labelB`, `correctA`, `correctB`, `gentleCorrectionA`, `gentleCorrectionB`

The game currently plays:

- `promptA` or `promptB` when the question appears.
- `answerA` or `answerB` on the reveal screen while the correct image gets a green glow and arrow.
- `teachingPoint` after the neutral answer audio, when available.

The builder can generate missing top-tier audio separately from the full secondary set. If an audio file already exists and you regenerate it, the builder creates a new preview first; use `Keep New` to replace the current file.

## Troubleshooting

- If the game shows a content error, check that `data/pairs.json` is valid JSON.
- If a pair does not appear in play, make sure it has at least one image on both sides.
- If images do not show, make sure the image paths in `pairs.json` are relative to the game folder.
- If audio does not play, the game still works; check whether the audio file exists and whether the path is listed in `pairs.json`.
- If audio generation fails, confirm `OPENAI_API_KEY` is set in the same terminal where the builder server is running.
