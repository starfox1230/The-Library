# Attending report-review aid: four-week feasibility/QI pilot

Updated October 29, 2026 after Sterling specified one attending per week for
four weeks. Assumption: four different attendings, each contributing one weekly
work block. If an attending repeats, the number of independent providers is
smaller. These are recommended design choices, not an approved protocol. No
recruitment, allocation, data collection, analytics or report storage is enabled
by this document. Exact shifts, eligibility and institutional review are open.

## Aim and claims

Determine whether the attending workflow can be delivered and measured with
acceptable effort, and obtain a preliminary description of resident-received
case-specific feedback. The intervention is the whole report-review workflow:
extractor, Attending mode, full-context AI comparison, clinical diff and human
review. This pilot cannot isolate the AI component's contribution.

**Primary pilot objectives:** workflow completion without investigator help,
end-to-end time, uptake, form completion and implementation barriers.

**Exploratory educational outcome:** resident-reported receipt of case-specific
educational feedback about the assigned source shift, during that shift or
within 48 hours of its end. Examples include a discussion or approved message
identifying an actual revision and explaining an interpretation/reporting point.
Generic praise or a bare notification without a learning point does not qualify.
Positive case-specific feedback can qualify. Pilot-test these definitions.
Reading a final report or AI output alone does not count as attending-delivered
feedback; a human attending-resident interaction must actually occur.

Forty-eight hours is a proposed practical window, not a literature standard.
Choose and fix the window before the first collection; 24 hours is an alternative
only if roster testing establishes feasibility before enrollment. Feedback during
the source shift counts, so routine timely feedback is not omitted from baseline.
Ordinary urgent clinical communication continues in every period.

## Four weekly blocks: usual workflow, then tool

Use each attending's own usual-workflow period as a descriptive baseline. If
there are five eligible source shifts in a block, a concrete split is:

| Period within each attending's week | Assignment |
| --- | --- |
| First two eligible source shifts | Usual workflow |
| Next three eligible source shifts | Tool-supported review |

Repeat across the four blocks. This would give eight usual-workflow and twelve
tool-assigned source shifts if every attending contributes five eligible shifts.
Those numbers are an illustration from the assumed roster, not a sample-size
calculation. Multiple residents can create more attending-resident observations,
but not more independent attendings. Fix an alternative split in advance for
blocks of another length rather than choosing a favorable transition afterward.

Train each attending briefly at the transition to the tool period. Keep review
opportunities, survey wording and reminders comparable in both periods. If a
protected review interval is offered, offer it in both. Otherwise the evaluated
intervention includes that additional time/reminder package. Participation is
assigned use, not a claim that website access is technically restricted; record
actual use and any use of the tool during usual-workflow periods.

This refines our earlier half-block crossover idea: use baseline first rather
than expecting an off period after tool exposure to be an untouched control.
A lasting teaching/learning effect is a recognized problem for crossover designs;
[CONSORT cluster-crossover guidance](https://www.bmj.com/content/388/bmj-2024-080472)
explicitly discusses persistent educational effects. Even baseline-first periods
have fixed-order, workload, fatigue, novelty and measurement effects. They do
not establish a causal treatment effect. Overlapping feedback windows and
cross-period discussion are additional possible contamination.

Do not add concurrent nonparticipating attendings as a primary control group
unless they can be prospectively measured with comparable eligibility and
follow-up. Otherwise use them only as descriptive service context. For a larger
subsequent comparative study, favor a concurrent randomized immediate-versus-
delayed-start design at attending level, with baseline measurement and enough
clusters, rather than repeatedly withdrawing an educational intervention.

## Fit the review into the service

Test a brief review at the start of the next consecutive shift using the previous
completed shift's finalized reports, followed by feedback early in resident
overlap or through the usual approved channel. Treat this as a workflow proposal;
it has not been shown to be the best timing for this service.

For the terminal source shift, prearrange an end-of-block review or another
brief opportunity within the same outcome window. Record no-overlap and report-
availability barriers. Avoid a design in which the last tool shift silently has
no review opportunity.

Every batch and feedback form stays attached to its **source shift**, attending
and resident, not merely the calendar date on which the app was opened. Prior
usual-workflow source shifts retain that assignment after the tool period starts;
record crossover use. Do not selectively extend feedback windows. Define who
and which finalized reports belong to a source shift before collecting data.

Keep the resident-facing tool's availability constant during the pilot and record
relevant use; introducing it only during tool periods would change the intervention.

## Measures and separate forms

The observation is an eligible **attending-resident-source-shift pair**, defined
from the roster, not from who used the tool or answered a survey. Include failed
runs and nonuse in the assigned-period record. Record planned absence, terminal
shifts and unavailable reports prospectively.

| Measure | Collection |
| --- | --- |
| Workflow completed without help | Attending: extraction, analysis and review completed? Yes/No; reasons if No |
| Feedback received | Resident: case-specific educational feedback from this attending about this source shift during the shift or by the 48-hour deadline? Yes/No/Unsure |
| Cases discussed | Resident: 0 / 1 / 2 / 3 / 4+ distinct clinical cases |
| Timing | Resident: during source shift / after it / both, when feedback occurred |
| Review and burden | Attending: deliberately reviewed revisions? Method: usual/tool/both/neither; approximate total minutes including extraction, loading and review |
| Implementation quality | Attending: technical failure, assistance needed, or clearly misleading/unhelpful summaries encountered? Brief categorical reason |
| Data completeness | Eligible pairs, due forms, completed forms and Unsure responses by period |

Prefill source shift and provider codes. Collect the resident form just after the
fixed outcome window and the attending form after the review opportunity. Aim
for roughly 20-30 seconds each; test the real burden. A short end-of-week interview
can ask what prevented use and what would make the process worth continuing.
Perceived usefulness is secondary and is not evidence that feedback occurred.

Coded providers are not automatically anonymous. Use an institution-approved
form/location and keep the linkage securely. Keep patient identifiers, report
text and case narratives out of general surveys. Keep individual resident
responses confidential from the attending being rated; present aggregate results.
The website itself does not need a feedback tracker or research form.

App use, opened reports and attending-reported feedback are process/complementary
measures, not proof of resident receipt. Resident reports also have recall and
response limitations; disagreements should be retained rather than automatically
resolved in favor of either participant. Missing forms are missing, not No.

Count a linked chest/abdomen-pelvis review episode once when reporting distinct
clinical cases discussed; do not multiply it by the number of duplicate report
rows. Automatic text groups are a heuristic, not verified patient identity.
Source rows, review groups, clinical cases, feedback interactions and provider-
shift observations are different denominators.

## Quality, stability and progression

Before collecting comparative pilot data, check the extractor, timing and form
wording with synthetic examples and an institution-approved workflow trial.
Record prior tool exposure. Do not mistake an already trained champion for a
naive baseline participant.

Have a clinician audit a small consecutive sample of outputs for faithful
summaries and distracting/misleading items, especially incorrect high-importance
labels. A second independent reviewer and adjudication can strengthen a later
report-level evaluation. This is report fidelity, not image-based diagnostic
accuracy. Attending assessment of their own output is not an independent gold
standard. Report observed problems; feedback rates do not validate AI accuracy.

Agree on practical progression targets before collection. Suggested starting
points, **not validated standards**, are at least 80% completion of tool-assigned
workflows without help, at least 80% resident form completion, and a median total
workflow time no longer than 10 minutes. Use the actual roster, burdens and
clinical review to accept or revise these proposed targets before enrollment.
Persistent misleading summaries require revision/review before wider evaluation.

Freeze the deployed app, extractor, model/deployment, both prompts, grouping
rule, forms and outcome definition during this short pilot. Record exact
versions and necessary fixes. If substantial changes are needed, describe
separate improvement cycles rather than pooling everything as one intervention.

## Analysis and publication

Report each attending's usual/tool period results, pooled descriptive results,
workflow times, assistance/failure rates, feedback reports, survey completion
and barriers. Keep counts of eligible observations and missing/Unsure responses
visible by period. Prespecify missing-data and sensitivity handling with the
methodology adviser; do not turn nonresponse into no feedback.

Four attending blocks do not support a confident effectiveness claim merely
because many reports were processed. Avoid treating reports or repeated resident
surveys as independent participants, a naive report-level chi-square test, or
p-value hunting. A statistician can advise appropriate uncertainty summaries
with so few providers. A later powered design needs the actual participant pool,
source-shift opportunities, baseline rate, meaningful target improvement and
correlation assumptions, not just a large report count. Pilot effect estimates
are imprecise and should not by themselves set the later target effect.

A suitable first manuscript is a **feasibility and preliminary-impact study**.
Use [SQUIRE 2.0](https://pmc.ncbi.nlm.nih.gov/articles/PMC4625997/) to document the
problem, context, intervention, measures, changes, burden and limitations when
reporting QI work. Randomized pilot guidance similarly emphasizes feasibility
objectives rather than formal effectiveness testing:
[CONSORT pilot/feasibility extension](https://www.bmj.com/content/355/bmj.i5239).

Report-comparison feedback systems already have precedent, including
[Choi et al.](https://pubmed.ncbi.nlm.nih.gov/28840360/). The useful contribution
here is testing an attending-focused AI-assisted workflow in routine overnight
practice and measuring feedback residents actually receive, with honest limits.
Do not promise improved diagnostic accuracy, learning retention or patient
outcomes from these measures.

## Institutional determination and immediate decisions

Obtain the appropriate UAB QI/HRPP determination before prospective collection.
Publication intent alone does not decide whether a project is research; see
[OHRP QI FAQ](https://www.hhs.gov/ohrp/regulations-and-policy/guidance/faq/quality-improvement-activities/index.html).
UAB lists a QI Self Determination Tool for certain projects, with limits on
eligibility: [UAB IRB forms](https://www.uab.edu/research/home/irb-forms). This
brief does not classify the project or establish approval/consent requirements.

Confirm: four distinct attendings; shifts per block; participating residents;
source-shift attribution; exact usual/tool split; review and terminal-shift
opportunities; fixed feedback window; short forms; confidentiality; progression
criteria; and the actual stable deployed software versions. No study is launched
by this plan.
