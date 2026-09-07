# Radiology conversation facts → Anki

This is the downstream contract for selected conversation facts. The daily synthesis prompt lives in [Radiology Learning System — Daily Workflow](https://app.notion.com/p/3c51d706353981e2b85cf69b25683db5); it produces facts, not cards.

## Source and selection

Fetch **Radiology Conversation Card Sources** at https://app.notion.com/p/7edc70051d5543c7a33bc501e17437d7.
The data source is `collection://c1e60edc-2031-4cae-b423-3578bdd83eb0`.

Process rows with **Make Anki? checked** and **Anki Created? unchecked**, across dates unless the user limits the date. Fetch selected rows fresh. A daily review page supplies the dated scope and instructions when the ordinary Notion-to-Anki run admits that page through `Anki Card = Needed`. The tested knowledge still comes from the selected rows, not from the container title.

```sql
SELECT url, "Card Source", "Extra", "Category", "date:Learning Date:start"
FROM "collection://c1e60edc-2031-4cae-b423-3578bdd83eb0"
WHERE "Make Anki?" = '__YES__'
  AND COALESCE("Anki Created?", '__NO__') = '__NO__'
ORDER BY "date:Learning Date:start", url
```

## Tested knowledge

**Card Source is the only authority for tested knowledge.** It contains the complete fact, not a label. Choose the cloze and write the card here, following `CARD_STYLE_GUIDE.md` and `APKG_PACKAGING.md`. Preserve the selected fact's meaning and essential qualifiers. Default to one focused note per selected atomic fact.

**Extra is supplemental only.** It may inform wording or populate the Anki Extra field, but cannot supply a new answer, another tested fact, or a separate card. The same applies to row-body context. Do not expand the selected scope with general high-yield additions. An incomplete or inaccurate Card Source needs review; record the issue and leave it pending rather than silently substituting a fact from Extra.

## Output and completion

Use the existing saCloze++ model and Saved Cards packaging path from the canonical guides. Save the source row URL, Card Source and Extra snapshots, stable note key based on the row UUID, and output location in the run manifest. Reuse that key on retries. The original conversation is not needed.

Before generating again, reconcile pending rows with prior manifests and verified output by row UUID. A generated StudyOS candidate is complete only when its stable ID exists in the New queue with `status = new`, `approved_at = null`, and `deleted_at = null`. Editing content or tags does not approve a card. Read back those fields for the full output set; do not infer visibility from a successful write or total card count.

After the full card output, source mapping, and New-queue state pass validation, mark only those rows' Anki Created? checked and read back the change. A draft, hidden/approved candidate, or failed build does not qualify. Preserve Make Anki?. If an output already succeeded but the Notion update failed, repair the status using verified output rather than generating a duplicate. If the fact changed after that output, flag it for reconciliation.

Run only when the user asks to convert selected conversation facts; this document does not create a schedule or authorize an import into the live Anki collection.

## How daily pages enter the card run

Every Radiology Notes page marked `Anki Card = Needed` is eligible for the ordinary Notion-to-Anki run, including Daily Learning pages. For an eligible Daily Learning page, follow its embedded dated view and apply the row selection contract above. Do not recursively mine unrelated linked databases or facts outside that dated view. The end-of-day synthesis prompt must continue to avoid pulling unrelated Notion entries into the daily page.

The former Radiology Learning Points database (`collection://02ef8780-cf71-4e10-8701-ad49b2313235`, https://app.notion.com/p/95b2617c032d469ab832aea3f137ab37) is deprecated for new capture. Its rows, selections, and historical views are preserved. A dated legacy view embedded in an eligible Daily Learning page is an explicit source for that page: process its `Make Anki?` checked, `Anki Created?` unchecked rows using `Learning Point` as the tested source, `Image Plan` as an instruction, and `Source Note` as provenance. This does not admit other legacy dates or unchecked rows.
