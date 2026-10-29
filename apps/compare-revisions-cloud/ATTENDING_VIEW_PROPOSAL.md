# Attending feedback view — proposal

Status: design proposal, not an implemented mode. The existing resident view
remains the shipped experience. These recommendations address the requested
overnight emergency-radiology feedback workflow without assuming UAB has
approved a specific workflow, rubric or communication policy.

## Primary task

Help an attending turn a batch of report revisions into a short, verified set
of feedback points for a resident. The first screen should answer: which
changes deserve discussion, what exactly changed, and which points have I
already discussed? Keep the existing case layout and linked report evidence.

## One analysis, two views

Use a Resident / Attending toggle within the existing authenticated app.
Initially this changes presentation and review controls only. It does not
identify the user's institutional role, grant permissions or change the UAB
sign-in flow. Both views use the same accepted comparison, source quotations,
clinical categories and uncertainty notices. Switching views should require
no new analysis, added model calls or resubmission of reports.

The resident view supports a complete review of personal report changes. The
attending view supports selecting and communicating a few feedback points.
Two independent grading prompts could disagree about the same change; avoid
that inconsistency in the first version.

## Proposed attending screen

| Element | Proposed behavior |
| --- | --- |
| Default case order | Major first, followed by Minor. Keep Minor changes accessible: the current rubric forbids Major for Findings-only changes. Category is a starting point for human review, not proof that a change needs a conversation. |
| Initial detail | Compact resident finding → attending revision, with a brief reason when useful. Hide quote blocks by default; reveal exact evidence on demand. Text-change percentage can stay secondary or be omitted in this view. |
| Select for feedback | A single per-case or per-revision action adds a point to a short discussion list. It does not contact the resident. |
| Discussed | Mark a point as discussed, with Undo. Default communication status is **Not recorded**. The report pair cannot reveal whether a conversation already occurred. |
| Correct or dismiss | Let the attending correct an inaccurate suggestion or dismiss an unhelpful one, rather than treating the AI label as settled. |
| Positive feedback | An optional attending-written positive note. The tool cannot infer a perceptive image finding or diagnostic accuracy solely from two matching reports. |
| Review problems | Analysis failures and skipped inputs remain visible and actionable, distinct from clinical teaching points. |
| Feedback preview | A short editable list of selected points, each linked back to its source case. The attending verifies it before using or copying it. No automatic messages. |

Do not label a worklist "changes not communicated" unless communication was
explicitly recorded. "Selected for discussion" and "Discussion status not
recorded" describe what the tool actually knows. Teaching feedback and any
clinical communication follow-up should be separate statuses and workflows.

## Summarizing a shift

Offer themes only from the submitted, explicitly grouped batch. For example,
"Laterality changed in cases 4 and 11" is a traceable description. Each theme
should show the supporting case numbers and the number of applicable cases.
Do not infer fatigue, a perception error, a resident's intent, competence or a
longitudinal weakness. Do not call one example a recurring pattern.

Current report inputs do not reliably establish resident identity or shift
boundaries. The first version should ask the user to supply a batch for the
intended resident/shift, rather than guessing ownership or mixing residents.
One batch can suggest topics to discuss; it cannot establish a performance trend
over time. Preserve the unreviewed/incomplete case count alongside any summary.

## Prompt strategy

1. Keep the current comparison prompt as the shared evidence and classification
   step. Retain the fixed resident → attending order and all evidence checks.
2. Build the first attending view from those results and human selections.
   Selection, discussion status and layout do not need an AI call.
3. If an editable feedback draft later proves useful, make it a separate,
   explicitly requested synthesis step using selected, reviewed revisions.
   Supply case IDs, report-side summaries, exact evidence, categories, reasons,
   uncertainty and attending edits; do not ask it to re-grade the reports.

The synthesis instructions should produce one or a few short discussion points,
cite their case IDs, preserve uncertainty, and avoid inventing image findings,
clinical outcomes, prior communication or the attending's reasoning. A draft
can identify an interpretation change and invite discussion of the distinction;
it cannot assert the imaging feature that caused the change without evidence.

Illustrative source-grounded point:

> Case 12: Both reports describe diverticulitis. The revision adds focal
> perforation. Review that added complication together.

Any broader teaching advice or image-based explanation must be provided or
confirmed by the attending. The tool does not have the images in this workflow.

## Small first implementation

Start with the view toggle, Major-first ordering with Minor accessible, local
selection for discussion, explicit Discussed/Undo, editable notes and a compact
selected-points preview. Retain selections when switching views. Keep the first
version within the current review session; adding persistent histories,
multi-user assignment or distribution is a separate feature decision.

Evaluate whether attendings can select useful points quickly, whether the
selected points are accurate and specific, and whether the workflow leads to
actual feedback. A large automatically generated narrative is not the primary
success measure. No usability or time-saving result is claimed for this proposal.

## Supporting evidence

A published resident/attending feedback-system study describes a streamlined
web workflow combining report comparisons and case-specific feedback, and
reports improved user satisfaction and attending participation. This supports
reducing friction as a design direction; it does not establish the effectiveness
of this proposed app or an LLM-generated summary. See [Choi et al., Journal of
Digital Imaging, 2018](https://pubmed.ncbi.nlm.nih.gov/28840360/).
