# Attending review view — proposal

Status: proposed, not implemented. This revision follows the user's preference
for a simple review tool, with study measurement outside the website. It
supersedes the earlier feedback-tracker-oriented proposal.

## Purpose

Help an attending quickly revisit their revisions and identify useful points
to discuss with a resident. Keep the first version focused on report review.
Do not require a feedback checklist, Discussed status, longitudinal dashboard,
resident assignment or saved teaching notes. Those remain optional future work.

## Small interface change

- Add a Resident / Attending view toggle behind the existing UAB sign-in. It
  changes presentation, not permissions or institutional roles.
- Resident mode retains resident-anchored titles to support recall of the
  original interpretation. Attending mode uses attending-anchored titles to
  support recall of the attending's revised interpretation.
- Keep the resident → attending comparison order, linked evidence, uncertainty
  notices and source-case numbers in both views. A different memory cue does
  not change the direction of the comparison or its clinical grading.
- Attending mode can default to Major-first ordering, with meaningful Minor
  changes readily accessible and quote blocks initially hidden. Major is not
  the only source of useful feedback; the rubric excludes Findings-only Major.
- Measure study behavior with a separate short form. Reviewing reports should
  not require completing research forms or tracking individual conversations.

## Two titles, one comparison

The current implemented `title` is explicitly based primarily on the resident's
principal finding or normal result. Attending mode should not simply reuse it.
A future implementation should request both resident and attending title fields
in the same structured response, then display the appropriate one. Switching
views should require no new analysis or independent grading prompt.

| View | Illustrative title |
| --- | --- |
| Resident | Pelvic mass, uncertain origin |
| Attending | Favored exophytic uterine fibroid |

Retain source uncertainty. Titles are memory cues, not verified image diagnoses.
Avoid patient identifiers, revision lists and treating the attending report as
independently proven truth. If information is insufficient, use a neutral title.
Do not guess an attending title from an arbitrary revision summary; the full
attending report is already available to the model.

## Evaluation outside the product

Ask whether access increases useful case review and case-specific feedback
residents actually receive. Tool use, reports opened, cases reviewed and feedback
received are distinct measures; a click does not establish that a conversation
occurred. Keep any data collection consistent in tool and control periods.

See [STUDY_PLAN.md](STUDY_PLAN.md) for proposed measurement, timing and allocation.
No survey, analytics, enrollment or communication feature has been deployed.

## Deferred features

Optional case selection, a feedback draft or source-linked themes may be useful
later if requested. Do not add them solely to make measurement easier. Report
pairs do not establish prior communication, resident competence or an enduring
performance trend. An attending can give feedback through the ordinary workflow
without recording it in this review tool.

## Background

A published web-based comparison/feedback system reported improved satisfaction
and attending participation. This supports reducing friction as a design
objective, without establishing this app's effectiveness. See [Choi et al.,
Journal of Digital Imaging, 2018](https://pubmed.ncbi.nlm.nih.gov/28840360/).
