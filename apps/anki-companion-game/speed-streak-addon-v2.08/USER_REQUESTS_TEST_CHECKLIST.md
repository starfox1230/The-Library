# 2.08 release checks

Build `2.08.0`. Use the Suggestion Lab for individual feedback trials.

## Install and preserve existing data

1. Close Anki. Run `install_to_anki.ps1` in this folder, then restart Anki.
2. Confirm only one Speed Streak add-on is active. Confirm the settings footer/build
   and What's New show 2.08. Orbital Rings should remain available in its visual picker.
3. Confirm your existing timers, shortcuts, sounds, flags, records and custom colors
   survived. Check both an existing Anki profile and a fresh profile if available.
4. After the following tests, close and reopen Anki and verify every new setting persists.

## Timer appearance — Settings → Visuals → Timer appearance

5. The default is seconds with one decimal, matching previous behavior. Watch both
   the top card bar and side-panel timer count down normally.
6. Choose **Whole seconds** independently for Circle timer numbers and Horizontal timer numbers. The selected timer should show no decimal. Positive fractions
   round up: 8.1 seconds displays 9, and 0.1 seconds displays 1 until expiry.
7. Choose **Hide numbers** for each timer. Only that timer’s numeric countdown disappears;
   progress indicators keep moving. Test mixed settings (for example, a hidden horizontal
   number with whole seconds in the circle), then swap the two. Test with the side panel on and off, and in
   Inline Left Pane and Compatibility Window modes. Switch back to decimals.
8. Under Timers, use **Timer appearance…** to reach the same Visuals control.
   Verify audio timing, Boost duration and actual expiry have not changed with
   the chosen number format. Test Time Drain too if you use that flag.

## Answer-side timer — Settings → Timers → General Timers

9. Turn on **Pause timer on the answer side**. Use a normally timed card after the
   free first card. Reveal the answer, wait longer than its configured answer time,
   and confirm there is no answer timeout or countdown sound. The top bar says
   ANSWER UNTIMED; the side panel is untimed. Rating buttons remain usable.
10. Rate the card. The next question must start its normal countdown. Repeat with
    No Pause mode enabled; the answer rule still applies. Deliberate pause shortcuts
    continue to follow No Pause mode.
11. Turn answer pause off. Answer timing should return. The stored answer duration
    and answer-timeout streak rule are retained while their controls are disabled.
12. Try question/answer sides with an existing untimed special rule, the free first
    card, and a Time Drain card. Answer pause wins over timed answer rules, but it
    does not stop question timeouts. It does not use the global paused overlay.

## Deck timers — Settings → Timers → Special Timers

13. Enable **Deck-Specific Timers**, add a rule and choose several decks. Search the
    picker, use Select visible/Clear visible, and press OK. Cancel should preserve
    the previous selection. Full `Parent::Child` names identify nested decks.
14. Set obvious values, such as 20-second questions and 30-second answers. Check
    selected decks and an unselected deck. Unselected decks retain their normal rules.
15. Select a parent deck with **Include subdecks** on. Confirm a nested child matches.
    Turn it off; only cards directly in the selected deck should match.
16. Try a card in a filtered deck: matching uses its original/home deck. Rename a
    selected deck: its rule should still work. Deleted decks stay marked unavailable
    in the picker and do not accidentally match another deck.
17. Test Untimed on either side. Combine deck, tag and note-type rules: the longest
    matching time wins independently on each side, and any matching Untimed wins.
    A deck rule is an exact override, so it can be shorter than the general timer.
18. Disable a rule, disable all deck rules, and remove a rule. Confirm the appropriate
    fallback each time. Open unrelated settings without opening Special Timers and
    save a change; existing deck rules must remain intact.

## Boost earning — Settings → Gameplay → Boost Rules

19. All four ratings are selected by default. With space in the Boost bank, check
    that Again, Hard, Good and Easy each contribute one card toward the next Boost.
20. Deselect Again; an Again answer should not advance the meter, but the other
    selected ratings should. Try Good only and then no ratings. Selecting none
    stops new earnings but preserves existing Boosts and accumulated progress.
21. Set a small threshold and cross it with eligible ratings. Check that only one
    Boost is earned at the threshold and that a full bank does not accumulate credit.
    Untimed cards can still earn progress when their rating is selected.
22. Switch the top mode control to Legacy Points. Boost controls should become
    unavailable, Focus rules should remain usable, and legacy scoring should work.
    Switch back: your rating choices and Boost settings should still be present.
23. If using Undo, undo an eligible review and verify Boost balance/progress restores
    with the review. Reset settings to defaults only if desired: decimals, answer
    pause off, deck rules off, and all ratings eligible should be restored.

## Settings organization

- Collapse and expand Boost Rules and Focus Rules independently; Focus remains
  available when Boost is collapsed or Legacy Points is selected.
- Each rating checkbox and its label have their own compact outlined control.
  Click the label as well as the box, and verify the intended rating changes.
- Collapse the major settings sections; their controls should hide and reappear.
- Under Visuals, Timer Appearance contains independent Circle timer numbers and
  Horizontal timer numbers controls, followed by Top Card Timer.
- Collapse General Timers and Special Timers. The Timer visuals shortcut remains
  available and opens/expands Timer Appearance in Visuals.
- Audio/Haptics shows Audio and Haptics directly, both initially collapsed.
- Shortcuts and Tools show their controls directly, without a category toggle.
- Tools no longer contains a Quick Guide.

## Final release smoke test

24. Review normally with audio/haptics, shortcuts, the top bar, records and your
    preferred visual. Test on macOS if publishing macOS support; this development
    machine verifies Windows/browser behavior only.
25. Inspect the rebuilt `speed_streak_v2_08.ankiaddon` for local testing.
    Public upload is a separate step after this manual review.

Automated coverage includes engine behavior, preference round-trip/reset, deck IDs,
subdecks, filtered decks, overlapping rules, native Qt settings/picker controls,
both browser timer surfaces, package/source equality and shared-track consistency.
