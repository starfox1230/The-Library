# How Compare Revisions classifies changes

Prompt version: `deltarad-review-1.5`. This is the app's current custom rubric,
not a claim of an externally validated discrepancy scale. The wording update
keeps the existing importance thresholds. Read the [exact default prompt](ANALYSIS_PROMPT.md)
and [implementation](main.py) to audit it.

## Scope and unit of assessment

- Compare assertions across all recognized Findings and Impression/Conclusion
  sections, including combined sections. Full reports provide context; edits
  to history, technique, indications, comparison or signatures are not graded.
- Classify each distinct meaningful revision, rather than assigning a report
  score. Do not count the same revision twice because it appears in two sections.
- The attending report is the textual reference. This does not establish image
  truth or whether the resident actually saw, missed or misunderstood a finding.
- Match the underlying finding first. An added complication is a change to that
  complication; it does not mean the entire already reported disease was missed.

## Two independent labels

| Action: what the attending edited | Meaning |
| --- | --- |
| Added | A new assertion absent from the resident's eligible text. |
| Removed | A resident assertion is no longer documented, without explicit refutation. Disappearance alone does not establish a false positive or resolution. |
| Changed | Reinterpretation, explicit negation, established relocation/laterality or another substantive modification of the same assertion. |
| Emphasis | The same finding is added to Impression without changing its meaning. It may remain in Findings. |
| Description | Equivalent terminology, supporting detail or useful wording refinement without a new clinical assertion. |

| Importance: how consequential the particular revision is | Current criterion |
| --- | --- |
| Major | Substantial **acute** clinical consequence or likely change to **urgent** clinical decisions in the supplied context, **and** the actual changed assertion meets the Impression/Conclusion section rule below. |
| Minor | A supported clinical assertion changes, but it does not meet the Major criteria. A clear clinical change confined to Findings remains below Major under this app's rule. |
| Wording/detail | Pure emphasis, equivalent phrasing or descriptive refinement without a new clinical assertion. Emphasis and Description actions must use this importance. |
| Needs review | Insufficient evidence/context to confidently assess importance or establish whether assertions concern the same finding. Name the uncertainty rather than forcing a grade. |

Action is not importance: Added can be Major or Minor, Changed can describe a
downward reinterpretation, and placement in Impression alone does not make
something Major. Text-change percentage is never an importance criterion.

## The section rule for Major

For reports with separate Findings and Impression, **the actual changed
assertion must be represented in Impression/Conclusion**. Mention of only the
underlying unchanged disease does not qualify a new body-only attribute.

- For Added, evidence must come from the attending's Impression/Conclusion.
- For Removed, evidence must come from the resident's Impression/Conclusion.
- For Changed, an appropriate endpoint can establish eligibility. A downward
  reinterpretation can qualify using the resident's Impression.
- Combined Findings/Impression and conclusion-only sections are eligible.
- Section eligibility alone is insufficient: the acute/urgent consequence
  threshold must also be met. Nonurgent actionable follow-up is not automatically Major.

This is a deliberate product restriction: **a potentially important change
appearing only in Findings cannot receive Major under the current rubric**.
If the change itself is clear, it remains visible at lower importance; if the
meaning or importance is uncertain, it needs review.

## Calibration examples already in the rubric

These are context-dependent examples, not universal disease classifications.

| Revision | Intended handling |
| --- | --- |
| Existing pneumothorax in resident Findings, added unchanged to attending Impression | Emphasis / Wording; not a newly missed pneumothorax. |
| Important resident pneumothorax call explicitly negated by attending | Changed; potentially Major if both consequence and section criteria hold. |
| Existing diverticulitis, new focal perforation in attending Impression | Added complication; potentially Major when acutely consequential. Do not call the underlying diverticulitis missed. |
| Existing multiloculated perisigmoid collection renamed abscess without a material new assertion | Description / Wording in that supplied context. Do not generalize all collection-to-abscess changes this way. |
| Renal cyst laterality changes | A clinical change, not merely wording; assess importance using the same threshold. |
| Routine conditional 12-month nodule follow-up added | Not automatically Major because it is actionable. |
| Device position changes from stomach to mainstem bronchus with repositioning advised | May be Major when supported by context and eligible Impression evidence. Device identity alone does not set importance. |
| Unchanged retained ballistic fragments newly mentioned | Not Major solely because they are foreign bodies. |

## What the code enforces and what the model judges

**Enforced mechanically:** required response fields and allowed labels; nonempty,
single-line summary fields; exact quotation membership in the named eligible
section; action-specific required source sides; Major evidence in an eligible
section on an allowed side; and keeping Emphasis/Description outside clinical
change counts. Malformed/unmatched items are withheld with an incomplete-inventory
warning. An unsupported Major section classification becomes Needs review.

**Still model judgments:** whether two assertions match, whether an edit is
clinically substantive or only descriptive, whether an excerpt supports the
claimed change, the clinical consequence/urgency, the accuracy of a paraphrase,
and whether every relevant revision was found. An exact quotation check cannot
prove those semantic judgments. In particular, the code does not independently
prove that a quoted Impression passage contains the specific delta claimed by
the model. Offline tests exercise contracts and gates; they are not a live
clinical-quality evaluation.

## Predictable summary wording

Every line uses **resident finding → attending revision**. Resident text uses
the normal reading color; the arrow and attending revision use amber.

- Changed: `Left renal cyst → Right renal cyst`.
- Added without a resident counterpart: `Not documented → Left seventh rib fracture`.
- Removed without an attending counterpart: `Small effusion → Not retained in attending report`.
- Emphasis: `Small right pneumothorax → Added to Impression; finding unchanged`.
- Description: `Simple hepatic cyst → Simple hepatic cyst, 1.2 cm`.

The server standardizes source-absence markers and the attending-side Emphasis
phrase. Quoted evidence is left intact. The model still determines which action
applies; the fixed phrase does not independently verify the action assignment.

## Which instructions actually reach the model

The editor is prefilled with the full default prompt. **Customize instructions
replaces that prompt**, rather than appending to a hidden rubric. Analyze uses
the submitted instructions; a retry uses the editor's current text. The required
schema and mechanical validation remain active even if the instructions change.
Restore default instructions restores this version for subsequent analysis.

The exact default is exported by `python dev/assemble.py` to
`ANALYSIS_PROMPT.md`, and a regression test checks equality with `DEFAULT_PROMPT`.
Neither the export nor these changes updates an existing cloud deployment;
replace `main.py` and redeploy to activate them there.
