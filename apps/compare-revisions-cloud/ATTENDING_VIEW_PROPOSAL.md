# Resident and Attending modes

Status: implemented in the replacement source, October 29, 2026. Cloud Run
redeployment is pending. This replaces the earlier two-title proposal with
Sterling's requested mode-specific prompt approach.

## Current behavior

A Resident / Attending segmented control appears directly above Report input,
including while the input panel is collapsed. A fresh visit defaults to Resident.
The choice survives form submission and Clear reports. It is a review preference,
not an institutional role, identity check, or change in permissions.

- Resident uses the existing prompt and resident-anchored memory-cue title.
- Attending uses a separate default prompt with an attending-anchored title.
- The two prompts differ only in the title instructions. All revision actions,
  importance thresholds, section/evidence gates, report order, colors, filters,
  sorting defaults and source grouping remain shared.
- The selected prompt generates one title through the existing analysis call;
  the app does not request two titles or run a second grading analysis.

| Mode | Illustrative title |
| --- | --- |
| Resident | Pelvic mass, uncertain origin |
| Attending | Favored uterine fibroid |

Titles retain source uncertainty and are memory cues, not verified image
findings. The attending remains the textual reference in both modes.

## Prompts and switching

The exact defaults are exported as [ANALYSIS_PROMPT.md](ANALYSIS_PROMPT.md)
(resident, `deltarad-review-1.5`) and
[ATTENDING_ANALYSIS_PROMPT.md](ATTENDING_ANALYSIS_PROMPT.md)
(attending, `deltarad-review-attending-1.0`). The shared response schema is
unchanged. The selected mode's full instructions remain visible and editable.

Switching modes swaps prompt drafts on the current page. Restore default
instructions resets the selected mode only. Form submission preserves the
selected editor text; unused drafts are not sent to the server. Clear reports
discards both drafts and restores the selected mode's default. A fresh visit
starts with Resident and both defaults again.

Changing mode sends no requests and does not retitle existing results. The
helper makes that explicit when older results were analyzed in the other mode;
a title tooltip identifies the mode of its accepted analysis. New analysis or
an explicit retry uses the current mode and editor. In-flight batches retain
their original prompt and mode, even across multiple server batches. A failed
retry retains the previous title's mode until a new response is accepted.

The backend validates mode values before provider access; older API clients
that omit the field retain Resident behavior. No credentials, environment
variables, login rules, model deployment or dependencies change.

## Deliberately deferred

No Major-first default, automatic quote hiding, feedback tracker, Discussed
checkbox, resident assignment, teaching-note storage, dashboard, or study data
collection was added. The view stays the same apart from title anchoring and
the selected-mode labels. QI/research measurement remains a separate proposed
form; see [STUDY_PLAN.md](STUDY_PLAN.md).

## Background

A published web-based comparison/feedback system reported improved satisfaction
and attending participation. This supports reducing friction as a design
objective, without establishing this app's effectiveness. See [Choi et al.,
Journal of Digital Imaging, 2018](https://pubmed.ncbi.nlm.nih.gov/28840360/).
