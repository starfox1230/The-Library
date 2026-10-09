# AnkiWeb Enhancer — Milestone 1

Private, locally installed Manifest V3 Chrome extension. It clicks AnkiWeb's
existing review buttons. AnkiWeb continues to display cards, choose due cards,
schedule reviews, record ratings, and sync your collection.

## Install with Load unpacked

1. Download `ankiweb-enhancer-milestone-1.zip` from `dist/`, or clone this repository.
2. **Extract the ZIP first.** Keep the extracted folder in a permanent location.
3. In Chrome, enter `chrome://extensions` in the address bar.
4. Turn on **Developer mode** at the upper right.
5. Click **Load unpacked**.
6. Select the **`ankiweb-enhancer` folder containing `manifest.json`**. Do not
   select the ZIP, `src/`, or the outer extraction folder.
   When using the repository directly, select `apps/ankiweb-enhancer/`.
7. Open or refresh <https://ankiweb.net/decks>, log in normally, choose a deck,
   and start reviewing. You do not need to close Anki desktop to install this
   Chrome extension.

The browser must be able to keep reading the selected folder. Moving or deleting
it breaks the installation. This is a Chrome extension, not an Anki desktop add-on.

## Keyboard controls

| Key | Action |
| --- | --- |
| Space or Enter | Show answer, only on the question side |
| 1 | Again, only when its button is present on the answer side |
| 2 | Hard, only when its button is present on the answer side |
| 3 | Good, only when its button is present on the answer side |
| 4 | Easy, only when its button is present on the answer side |

Missing buttons are never reassigned: `3` always means Good. Space and Enter
do nothing on the answer side, even when a grading button has keyboard focus.
Holding a key cannot repeat the action. Modified keys and text editing retain
their normal browser behavior. Shortcuts stay out of inputs, textareas, selects,
contenteditable elements, and accessible text fields, including shadow DOM fields.

Version **0.1.1** restores focus to **Show Answer** after ordinary clicks on card
content or the page background, and when AnkiWeb renders a new question. The
focus change does not scroll the page or reveal the answer. Typing fields,
links, and media controls keep their focus so you can still interact with them.

AnkiWeb currently has native number shortcuts on **keyup** that do not check text
fields. During review, this extension stops those events from reaching AnkiWeb
while preserving typing's default behavior. It owns both keydown and keyup to
avoid a native second grade after an extension click.

Actions have a **350 ms** debounce. After a grading click, further shortcut actions
remain locked until AnkiWeb shows the next question, even if the first response is
slow. An unrelated DOM update cannot release that lock. If AnkiWeb fails to advance,
use its normal controls or refresh; the extension does not retry a rating.

Version **0.1.2** adds Pocket Knife-style selected-answer feedback: a large
pastel red/orange/green/blue label for Again/Hard/Good/Easy appears over the review
controls for **900 ms**, including after the next question appears. Keyboard and
mouse ratings both trigger it. The label is click-through and never takes focus.
It confirms which rating was selected; it does not claim the server finished
recording the review. A newer rating replaces the previous label immediately.

Version **0.1.3** removes complete unsupported `[anki:tts …]…[/anki:tts]`
blocks, including their duplicated spoken text, from the rendered card on
AnkiWeb. Normal card text and cloze formatting remain. This runs on both card
sides as AnkiWeb updates them. It does not change your saved Anki cards or add
speech playback. Editors, scripts, and media are left alone; incomplete markers
are preserved rather than guessing how much text to remove.

Milestone 1, selected-answer feedback, and TTS cleanup are implemented. Focus mode, dark mode, F/D/G/S toggles,
gamification, a popup, settings, and persistent preferences are deferred.

## Permissions and privacy

The sole site access declaration is `content_scripts.matches`:
**`https://ankiweb.net/*`**, restricted to the exact HTTPS host. Matching all paths
allows the content script to survive AnkiWeb's client-side navigation from decks
to review. Actions require `/study` and the verified review structure.

There is **no `permissions` list**, no extra `host_permissions`, and no access to
other websites, history, cookies, passwords, or the clipboard. There is no
storage, authentication code, networking, analytics, telemetry, advertising,
external API, remote script, or server in the extension. The script checks only
review structure, button labels, and input focus, and transiently reads rendered
card text to remove unsupported TTS blocks. It does not read credential values,
store card contents, or transmit them. It runs in Chrome's isolated content-script world,
in the top frame only. No service worker is needed in milestone 1.

Chrome documents this approach in [Content scripts](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts)
and [Load an unpacked extension](https://developer.chrome.com/docs/extensions/get-started/tutorial/hello-world#load-unpacked).

## Update

Replace the files in your installed folder with the new version, then:

1. Return to `chrome://extensions`.
2. Click **Reload** on AnkiWeb Enhancer.
3. Refresh any already-open AnkiWeb tabs so they receive the updated scripts.

To disable or uninstall, use the extension's toggle or **Remove** button and
refresh AnkiWeb. No collection data or settings need to be cleaned up.

## Debugging

- On AnkiWeb, press **F12** or **Ctrl+Shift+J** to inspect the tab's console.
  In the console's execution-context dropdown, select **AnkiWeb Enhancer** to
  inspect its isolated world. `AnkiWebEnhancer.dom.getSnapshot()` reports the
  detected phase and button elements without exposing card contents.
- On `chrome://extensions`, inspect **Errors**, if displayed, and **Details**.
  Confirm site access is allowed on `https://ankiweb.net`.
- There is no background service worker, so no **Inspect service worker** link
  is expected. If a later milestone adds one, inspect it from this same page.
- If a shortcut does nothing, check input focus, a modal dialog, the debounce,
  and whether the intended AnkiWeb button is visible and enabled. If AnkiWeb
  changes its HTML, update the adapter in `src/content/anki-dom.js` first.

## Current AnkiWeb DOM verification

The public AnkiWeb `/study` JavaScript was inspected on **October 9, 2026**. It
renders `#quiz`, card content in `#qa` inside `#qa_box`, and controls in `#ansarea`.
The controls have English labels `Show Answer`, `Again`, `Hard`, `Good`, and `Easy`;
interval text is in separate elements above the grading buttons. Native grades
are registered on document keyup.

Automated tests use a simulated review page shaped like that source; **your
authenticated AnkiWeb collection has not been reviewed or graded during development**.
Verify the checklist below in your browser. Localized labels, a future layout,
or iframe-based cards are not assumed supported. Ambiguous or unfamiliar controls
are ignored, rather than guessed. Only the top frame receives shortcuts; click
outside an embedded card iframe to return keyboard focus to the review page.

## Manual testing checklist

- [ ] On a question, Space reveals the answer once.
- [ ] On another question, Enter reveals the answer once.
- [ ] Click card text or page background: Show Answer regains focus and Space works.
- [ ] On a question, 1–4 do not grade or reveal the card.
- [ ] On answers, 1/2/3/4 activate Again/Hard/Good/Easy respectively.
- [ ] Mouse and keyboard ratings show the matching colored label for about 900 ms,
      continuing over the next question without blocking clicks or typing.
- [ ] An unavailable or disabled Hard/Easy button is not activated or remapped.
- [ ] Space/Enter on an answer do not accidentally activate a focused grade button.
- [ ] Hold Space, Enter, or a number: only one click occurs; release before another action.
- [ ] Rapidly press multiple grade keys: only the first accepted rating is submitted.
- [ ] With a slow response, repeated grades remain blocked on the same answer.
- [ ] Type spaces, numbers, and Enter in an input, textarea, or editable card field:
      editing works and no review is submitted, including on key release.
- [ ] Ctrl/Alt/Shift combinations and IME composition do not trigger shortcuts.
- [ ] Navigate out of review and back, or move to the next card: no refresh is needed.
- [ ] Refresh AnkiWeb: controls still work; no preferences exist to corrupt in milestone 1.
- [ ] The extension does nothing on login, deck lists, finished review, or other websites.

Focus/dark toggles, game statistics, and settings tests begin with their respective
future milestones and are intentionally not applicable to this build.

## Architecture and developer validation

```text
ankiweb-enhancer/
  manifest.json
  src/content/
    anki-dom.js       # Review route, selectors, button detection, normal clicks
    keyboard.js       # Capture events, protect editing, suppress native duplicates
    answer-feedback.js # Brief click-through selected-rating label
    card-cleanup.js   # Remove unsupported TTS echoes from displayed card text
    content.js        # Bootstrap, debounce, transition latch, MutationObserver
  tests/review.test.cjs
  scripts/package.py
  dist/ankiweb-enhancer-milestone-1.zip
  README.md
```

No build step or dependency is required to install. For development only, the
browser test requires Node.js, Playwright, and a Playwright Chromium installation:

```powershell
node --test apps/ankiweb-enhancer/tests/review.test.cjs
python apps/ankiweb-enhancer/scripts/package.py
```

If Playwright is installed outside Node's usual search paths, set `NODE_PATH` to
that package directory. `ANKI_TEST_BROWSER` can point to an existing Playwright
Chromium executable. Tests load the **actual unpacked extension**, use local
fixtures via request routing, and never log into AnkiWeb or use a real collection.
The ZIP contains only the manifest, the five content scripts, and this README.

Validation on October 9, 2026: **36 tests passed** with the actual unpacked
extension loaded in Playwright Chromium on Windows. This covers all grade
mappings, native-event suppression, debounce, transition locks, editing and
shadow DOM protection, navigation, reload, and non-review/non-AnkiWeb pages.
The focus regression tests cover card/background clicks, preservation of answer
input focus, and replacement Show Answer controls without page scrolling.
The authenticated AnkiWeb checklist above remains a manual verification step.
