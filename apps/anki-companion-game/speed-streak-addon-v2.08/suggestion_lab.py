"""Profile-local decisions for the owner-enabled suggestion lab."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile


@dataclass(frozen=True)
class Suggestion:
    key: str
    title: str
    source: str
    current: str
    behavior: str
    test: str
    live: bool = True


IDEAS = (
    Suggestion("single_color", "One color for every rating", "Reddit · Nov 17",
        "Crystal has a uniform option. Other layouts have individual rating swatches.",
        "Use the blue rating color for all earned pieces across layouts. Your palette stays saved.",
        "Rate Again, Hard and Easy. Switch between Orbital Rings and Brick Layout. Turn the trial off to see the original rating colors return."),
    Suggestion("exit_reset", "Finish the run when leaving review", "Reddit · Oct 17",
        "Resume after restart controls reopening Anki. Normally you can leave the reviewer and continue the same card streak.",
        "Save the active run and start a fresh one whenever you return to a deck overview or the deck list.",
        "Rate three cards, leave with cards still due, then re-enter. Check the saved run in Records and the fresh streak on your next answer."),
    Suggestion("shuffle", "Shuffle rating sounds", "Reddit · Oct 19",
        "Audio settings let you assign one sound to each event.",
        "Each rating draws from its own pool of clips. With two different clips it avoids immediate repeats. Countdown and reveal keep their timing.",
        "Turn Audio Feedback on. Choose Good below, select a few clips, then rate Good three times. Turn off the trial to hear the original assignment."),
    Suggestion("deck_finish", "Bank the streak on deck completion", "AnkiWeb · Nov 5",
        "A continuing streak can appear as a live best before it has a saved row.",
        "Finish and save one run when Anki runs out of cards. Leaving a deck early still allows continuation unless the exit trial is also on.",
        "Turn off Finish on leaving. Finish a two-card practice deck, open Records, undo the final review and answer again. Check for one completed run."),
    Suggestion("touch", "Touch buttons for pause and flags", "AnkiWeb · Nov 1",
        "Pause has a keyboard shortcut. Review Later and Time Drain already have configurable flag colors.",
        "Add finger-sized pause/resume and flag buttons directly on the card. Each flag uses your configured color.",
        "Tap Pause, Resume, then one of the flags. Tap that flag again to remove it. Try a side-panel-free review and No Pause mode."),
    Suggestion("saved", "Show time saved", "AnkiWeb · Nov 10",
        "Sprint Time tracks uninterrupted time spent reviewing.",
        "Count unused seconds on timed card sides. Each side earns at most its base time. Free, untimed and shared-bank sides earn zero.",
        "Use ten-second timers. Spend about two seconds on each side of a timed card. Rate it and look for about 16 seconds saved. Undo and compare."),
    Suggestion("race", "Race your saved-time record", "AnkiWeb · Nov 10",
        "The records strip compares card counts.",
        "Two segmented snakes compare this run’s saved seconds with the best finished lab run in this profile. A first run sets the target.",
        "Finish one run by leaving review, then review again and watch your snake grow toward the previous best. The saved-time run covers one visit to the reviewer. Race also shows the saved-time counter."),
    Suggestion("quiet", "Use a small hourglass", "AnkiWeb · Sep 17",
        "Whole seconds and hidden numbers already work independently on the side and top timers.",
        "Replace the large side countdown with a compact hourglass and shrink the top timer to a quiet progress line.",
        "Enable both timers. Review one timed card slowly and let the sand fall. Compare with the existing whole-second setting."),
    Suggestion("bank", "Share time across cards", "AnkiWeb · Aug 27",
        "Boosts add time to an individual card side.",
        "Start with 120 seconds. Timed question and answer sides draw from the same balance. Every completed timed card adds 12 seconds. An empty bank breaks the streak. Leaving review starts a new bank.",
        "After the free card, spend five seconds on each side. The next card should start near 122 seconds. Pause, resume, and undo a rating to check the balance."),
    Suggestion("hide_window", "Hide the compatibility window", "AnkiWeb · Mar 25",
        "You can already hide the inline panel or keep only the horizontal timer.",
        "Hide the floating window throughout review while the game continues. Turn the trial off here to bring the window back.",
        "Choose Compatibility Window. Enable this trial, rate two cards and disable it. The window should return showing both answers."),
    Suggestion("width", "Set the inline panel width", "AnkiWeb · Mar 23",
        "The panel can be collapsed or moved to the right.",
        "Choose an expanded width in pixels. The collapsed width stays compact.",
        "Choose Inline Pane, expand it and try 240 and 360 pixels. Switch sides and check the review card still fits."),
    Suggestion("move_flag", "Move a newly flagged card to a deck", "AnkiWeb · Mar 24",
        "Review Later already collects flagged cards. It normally leaves them in their original decks.",
        "Applying the Review Later flag moves the current card to your chosen normal deck using Anki’s undoable Change Deck operation.",
        "Choose a practice destination below. Apply the Review Later flag to a practice card, check its deck in Browse, then use Undo Change Deck. Existing flagged cards are untouched."),
    Suggestion("penalty", "Lose one point on timeout", "AnkiWeb · Mar 23",
        "A timeout normally breaks the streak. You can already forgive an answer-side timeout.",
        "In Legacy Points, deduct one point down to zero and restart that side. The streak survives. Shared-bank expiry has priority.",
        "Choose Legacy Points, earn points, then let a timed question expire twice. Expect one point lost each time and a fresh timer."),
    Suggestion("audio_check", "Rating sounds after a restart", "AnkiWeb · Sep 4",
        "Audio/Haptics already includes audio previews, uploaded clips and an Audio Check.",
        "Check the existing Windows playback and selection fix.", "Assign a WAV and an MP3 to different ratings. Restart Anki and test both in the reviewer and in Audio Check.", False),
    Suggestion("haptics", "Controller vibration and strength", "AnkiWeb · Aug 29, May 19 & Apr 19",
        "Per-event haptics and a master switch exist. The DualSense reviewer reported a fix.",
        "Verify support on each controller you use.", "On a Mac, try a rating with vibration on, switch the event pattern, then turn haptics off. The Speed Streak menu has macOS Haptics Diagnostics.", False),
    Suggestion("mac_audio", "Mac audio feedback", "AnkiWeb · May 5 & Mar 24",
        "Rating audio and browser playback are available.", "Check sound playback on macOS.",
        "Preview a packaged clip, then reveal and rate a real card using the same clip.", False),
    Suggestion("performance", "Long streaks and battery use", "AnkiWeb · Jul 15, Apr 1 & Mar 25",
        "Still motion and lightweight layouts are available. Orbital Rings limits its canvas size.",
        "Compare layouts at a high streak on the affected hardware.", "Set a streak above 130 in Developer Testing. Compare Still and Smooth, inspect CPU use and look for pieces going off screen.", False),
    Suggestion("flatpak", "Inline pane on Linux Flatpak", "AnkiWeb · Apr 21",
        "Inline Pane and Compatibility Window are both available.", "Check that the inline pane draws and updates on Flatpak.",
        "On Linux Flatpak select Inline Pane, reveal and rate a card, then switch sides. Compare the same card layout in Compatibility Window.", False),
    Suggestion("integrations", "Inline review with AnkiHub and AMBOSS", "AnkiWeb · Apr 1",
        "Inline and compatibility layouts are available.", "Check card scaling and overlays with the other add-ons installed.",
        "Open a card with an AMBOSS tooltip in Inline Pane, trigger the tooltip, rate the card and repeat in Compatibility Window.", False),
    Suggestion("typed", "Typed-answer timing", "AnkiWeb · May 26",
        "Special Timers can extend or untime the question side of a typed-answer card.",
        "Try the existing card-type rule. It applies for the whole side, including pauses between keystrokes.",
        "Set a short normal timer and a long typed-answer timer. Alternate a typed and a regular card and see whether you still want typing detection.", False),
    Suggestion("one_by_one", "One-by-one reveal timing", "AnkiWeb · Apr 23",
        "AnKing one-by-one cards have special timer rules.", "Give incremental reveals more reading time.",
        "Set a longer one-by-one answer time. Reveal several items and compare with an ordinary cloze card.", False),
    Suggestion("note_types", "Timers by note type", "AnkiWeb · Jul 17",
        "Special Timers supports note-type rules.", "Apply a different timer to one note type.",
        "Give two note types visibly different limits. Alternate between them in review.", False),
    Suggestion("shortcut", "Pause and boost shortcuts", "AnkiWeb · Sep 4, May 24 & Mar 24",
        "Settings → Shortcuts lets you rebind pause and boost.", "Verify the keys alongside your other add-ons.",
        "Choose an unused pause key, press it twice on a timed question, and use the configured boost key.", False),
    Suggestion("light", "Light appearance", "AnkiWeb · Apr 19",
        "Card Match can follow a light card background.", "Compare the existing appearance with the requested light theme.",
        "Pick Card Match, open a light card and compare the panel, timer and labels with your usual theme.", False),
    Suggestion("records", "Best score and five runs in review", "AnkiWeb · Aug 29 & Mar 24",
        "The records strip can show a best run or five runs.", "Compare the saved record displays.",
        "Choose Five Streaks, finish a run and switch to Best Only. Open its detail in Records.", False),
    Suggestion("resume", "Resume after restarting Anki", "AnkiWeb · Mar 24",
        "Resume run after restart already exists.", "Check your preferred restart behavior.",
        "Turn off the exit trial. Enable resume, close Anki mid-streak and reopen. Repeat with resume disabled.", False),
    Suggestion("bar_only", "Keep only the horizontal timer", "AnkiWeb · Jun 23",
        "The side panel can be switched off while the card timer stays visible.", "Compare the existing bar-only layout on a small screen.",
        "Turn off the side panel and keep Top Card Timer on. Check that the review card uses the reclaimed space.", False),
)
BY_KEY = {idea.key: idea for idea in IDEAS}
VERDICTS = ("Undecided", "Keep", "Skip")


class SuggestionLab:
    def __init__(self, root: Path, authorized: bool):
        self.path = root / "suggestion-lab.json"
        self.authorized = authorized
        self.data = {}
        if authorized and self.path.is_file():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                import logging
                logging.getLogger(__name__).warning("Could not read suggestion lab choices: %s", exc)
                return
            if isinstance(raw, dict):
                self.data = raw

    def active(self, key):
        return self.authorized and key in self.data.get("trying", [])

    def verdict(self, key):
        value = self.data.get("decisions", {}).get(key)
        return value if value in VERDICTS else VERDICTS[0]

    def save(self):
        if not self.authorized:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent, delete=False) as stream:
            json.dump(self.data, stream, ensure_ascii=False, indent=2)
        try:
            os.replace(stream.name, self.path)
        finally:
            Path(stream.name).unlink(missing_ok=True)

    def summary(self):
        lines = ["Speed Streak 2.08 · next-build selections"]
        for verdict in VERDICTS[1:] + VERDICTS[:1]:
            lines.extend(["", verdict])
            lines.extend("• " + idea.title for idea in IDEAS if self.verdict(idea.key) == verdict)
        return "\n".join(lines)

