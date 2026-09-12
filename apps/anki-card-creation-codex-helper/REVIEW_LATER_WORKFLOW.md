# Review Later workflow

Use this when an existing Anki card causes confusion, exposes an incomplete mental model, or reveals that the card itself needs repair.

Review Later can produce two independent results. A session may produce either result or both:

1. A disposition for the existing Anki card.
2. New cards for concepts discovered while understanding that card.

## Start the session

Open the Review Later item and discuss or reconstruct the underlying concept in the current ChatGPT or Codex conversation. Use the card, all available fields, images, tags, review reason, and surrounding context. Continue until the distinction or mechanism is clear enough to explain in plain language.

## Result 1: handle the existing card

Choose a concrete disposition:

- Keep it unchanged when the card is accurate and the problem was only a temporary knowledge gap.
- Edit it when wording, context, cloze placement, or Extra can be improved without changing the tested fact.
- Split it when one card tests multiple separable ideas.
- Replace it when the current prompt tests the wrong thing or cannot be repaired cleanly.
- Suspend it when it should not remain active.
- Research it when accuracy is still unresolved.

When the conversation has access to the local Anki collection, ask it to apply the chosen change and verify the actual note after writing. Otherwise, preserve exact proposed card text and the note identifier so the change can be made later. Discussion alone does not complete an edit.

## Result 2: capture new concepts found during review

This is common. A failed card can expose related concepts or contrasts that deserve their own cards even when the original card is retained or repaired.

Paste this prompt into the same conversation after the explanation is complete:

```text
Turn this Review Later discussion into a list of the facts I clearly considered important. Write each fact as a simple, accurate, self-contained statement that does not rely on an antecedent, the original card, or the earlier conversation. Keep one main idea per statement. When a fact matters because it contrasts with another fact, write the related statements in parallel so the differences stand out. Include newly clarified concepts that deserve their own cards. Do not write cloze deletions or JSON yet.
```

This wording is based on the phrasing used in the recent detector Review Later conversation: simplified facts, no antecedent, and parallel wording when the contrast is what matters.

Then complete the new-card branch:

1. Review the fact list and remove anything you do not want to retain.
2. Paste the selected statements into the ChatGPT project **Anki Card Generator 3.0 - For Companion App**.
3. Copy the JSON returned by that project.
4. Open the **YT2 Anki Card Reviewer** at `https://yt2anki.onrender.com/reviewer`.
5. Paste the JSON into the reviewer.
6. Edit, save, or discard each candidate. If review reveals another missing concept, add it to the fact list and repeat the generator step.
7. Export the approved cards as an APKG.
8. Import the APKG into Anki and verify the imported cards.

## Quick prompts

To extract new facts, say:

```text
Use the Review Later fact-extraction prompt on what we just discussed.
```

To handle the existing card, say:

```text
Decide the disposition of the original Review Later card, apply any needed change in Anki if you have access, and verify the actual note afterward.
```

To do both, say:

```text
Finish this Review Later item: decide and verify the original card's disposition, then extract any new card-worthy concepts as simple self-contained statements using the saved Review Later workflow.
```

## Completion record

Record these separately:

- Existing card: note/card identifier and disposition.
- New concepts: fact list, JSON batch, YT2 Anki Card Reviewer status, APKG, import verification, and relationship to the original card when useful.

Do not require a new card when clarification or an edit is enough. Do not treat the original card as resolved merely because new cards were created.
