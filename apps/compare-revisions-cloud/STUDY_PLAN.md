# Attending review aid — QI/research planning brief

Status: proposed elements for discussion, not an approved protocol or an
implemented study. No enrollment, analytics, survey collection or additional
report storage is activated. The roster, sample, timing, analysis and
institutional determination remain to be settled.

## A narrow primary question

Does access to the attending report-review aid increase the proportion of
eligible attending–resident index-shift pairs in which the resident receives
at least one case-specific feedback interaction about those reports within a
prespecified period?

Suggested definition: discussion or a message that identifies an actual case
revision and explains a point about interpretation/reporting. General praise
alone does not qualify; positive feedback can qualify if equally specific.
Agree on the definition before collecting data and use it in both conditions.

This measures reported feedback received. It does not directly observe all
conversations or establish improved diagnostic accuracy, learning or patient
outcomes. Those are separate questions requiring suitable measures.

## Keep measurement outside the website

Use a short, separate institution-approved form with the same schedule and
wording in tool and usual-workflow periods. Prefill the index shift, attending
code and resident code so multiple attendings and repeated shifts are not mixed.

### Primary outcome

Recommended starting outcome: resident-reported receipt of at least one
case-specific feedback interaction from the named/coded attending about the
specified source shift within 24 hours after that shift ends.

Twenty-four hours is a proposed operational choice, not an established standard.
Confirm roster feasibility first. If 48 hours works better, choose it before
the comparison starts and use it consistently. Attribute feedback to the source
shift and its assigned review condition, not just the conversation's calendar day.

Define eligibility from a prespecified roster of attending–resident source-shift
pairs and agreed feedback opportunities. Do not define it by whether someone
used the tool or returned a form. Prespecify terminal shifts, absence and
unavailable reports rather than excluding inconvenient observations afterward.

### Short resident form

Complete after the outcome window, with source shift and attending prefilled:

1. Did this attending give you case-specific feedback about reports from this
   shift during the specified window? **Yes / No / Unsure.**
2. If Yes, how many distinct cases were discussed? **1 / 2 / 3 / 4+.**
3. If Yes, how useful was it? For example: **No useful learning point /
   Somewhat useful / Clearly useful / Very useful.**

These are draft behaviorally anchored items, not a validated questionnaire.
Pilot-test clarity and burden. The primary outcome is receipt, not satisfaction.

### Short attending form

For the same source shift, ask:

1. Did you deliberately review your revisions? **Yes / No.**
2. Which method? **Usual workflow / Tool / Both / Neither.**
3. Did you provide case-specific feedback? **Yes / No**; if Yes, use the same
   distinct-case count categories as the resident form.
4. Approximate review time: **Under 2 / 2–5 / 6–10 / Over 10 minutes.**

Resident reporting is the proposed main feedback outcome; attending reporting
is complementary. Both are self-reports, not objective gold standards. Their
disagreement is informative and should not automatically favor either account.
A general post-project satisfaction survey can be secondary.

### Measurement guardrails

- Logins, analysis completion, reports opened and cases selected measure tool
  use, not feedback delivered or received.
- App-specific telemetry is an intervention process measure. Ordinary review
  without an app log is not zero review.
- Missing forms mean missing data, not No feedback. Track response rates by
  condition; prespecify follow-up and missing-data/sensitivity handling.
- Keep report text, patient identifiers and case descriptions out of a general
  feedback questionnaire. Coded provider data still need appropriate handling;
  study codes are not automatically anonymous.

## Refine the half-block idea

One attending per week using the tool for half of a block, with their other
shifts and concurrent attendings as controls, is a reasonable feasibility
starting point. Control observations alone do not make it randomized.

If feasible, randomize/counterbalance period order in advance across attendings.
Some use usual workflow first; others have tool access first. Predetermine the
split for an odd number of shifts. Always assigning the tool to the second
half would mix tool access with fatigue, weekday mix and position in the block.

Illustration only, for six eligible review opportunities per attending:

| Sequence | First three opportunities | Last three opportunities |
| --- | --- | --- |
| A | Usual workflow | Tool available |
| B | Tool available | Usual workflow |

This is not an actual roster or sample-size estimate. Map every review
opportunity to its source reports. With next-evening review, avoid assigning
a previous night's reports to the wrong half-block simply because the date changed.

- Within-attending comparisons help address stable personal feedback habits.
  Concurrent attendings give calendar/workload context, but are not automatically
  comparable controls.
- Tool exposure can change later habits or resident expectations. A short
  washout cannot be assumed to erase this. Record crossover use and acknowledge
  carryover/contamination; an off period is not a naive baseline.
- Give both conditions comparable review opportunities and form/reminder
  schedules if estimating the tool's incremental benefit. If protected review
  time/reminders are added only with the tool, evaluate that combined package.
- Use assigned availability as the primary comparison. Restricting analysis
  to actual users introduces self-selection; treat such analyses as secondary.

Current crossover reporting guidance emphasizes period effects, carryover and
correlated observations. See the [CONSORT cluster crossover extension, BMJ
2025](https://www.bmj.com/content/388/bmj-2024-080472.full).

## Timing: pilot the workflow before deciding

A practical first test is a brief review at the beginning of the next consecutive
shift, using the previous completed shift's finalized reports, followed by
feedback early in overlap with the relevant resident. This is a recommendation
to test, not evidence that this timing is best at the intended service.

Terminal shifts need a prespecified alternative, such as a short end-of-block
review and feedback through the usual approved channel within the same outcome
window. Record missing overlap, unavailable reports and other logistical barriers.
Do not selectively extend the window or move cases between allocation periods.

Before the comparative phase, test a few actual workflows: total extraction,
analysis and review time; finalized-report availability; ability to reach the
correct resident; and form burden. Pick end-of-shift versus next-shift timing
from that feasibility work and the actual roster.

## Sample, analysis and versioning

One attending–resident index-shift pair is a candidate observational unit.
Observations repeat within attendings and residents; calendar period also
matters. Hundreds of reports are not hundreds of independent participants.
Use a biostatistician to prespecify analysis and small-cluster inference from
actual participant counts, eligible opportunities, baseline feedback rate and
the minimum meaningful effect.

A month with only a few attending blocks should be treated as a feasibility
pilot unless the planned sample supports a stronger effectiveness claim.
Report feedback rates, response rates, within-attending differences and
uncertainty. Do not promise statistical significance or calculate a sample
size without these inputs.

Stabilize the workflow, instructions, forms and outcome definition before the
comparative phase. Record app, model/deployment, prompt and form versions.
Document needed fixes and their timing; prospectively handle analytic effects.
A later iterative QI rollout may use planned improvement cycles, but those
cycles should be visible rather than treated as an unchanged intervention.

## QI, research and publication

Publication intent alone does not determine whether an activity is research.
OHRP distinguishes intent to publish from the purpose/design of the activity.
UAB offers a QI Self Determination Tool for certain projects and states that
not all QI projects can use it. Obtain the appropriate determination for this
specific educational/provider-feedback design before prospective comparative
collection. This brief does not classify it or assume an exemption.

Sources: [OHRP QI FAQ](https://www.hhs.gov/ohrp/regulations-and-policy/guidance/faq/quality-improvement-activities/index.html)
and [UAB Office of Research forms](https://www.uab.edu/research/home/irb-forms).

## Open decisions

Roster and sample; source-shift/review mapping; feasible review window; 24 versus
48 hours; feedback definition; form wording; allocation; contamination handling;
missing-data plan; sample size/analysis; institutional determination/data handling.
These are proposed choices, not settled decisions or deployed features.
