# Resident and Attending title perspectives

Implemented in source, November 2, 2026, website build 2026.11.02. Live deployment
and the actual-model/workstation trial remain pending.

Every grouped pair uses one model request returning `title_resident`,
`title_attending` and one shared revision inventory. Resident titles recall the
initial interpretation; Attending titles follow the final interpretation. Both
preserve source uncertainty. Clinical judgments and resident-to-attending order
are unchanged.

The Resident/Attending toggle is above live report input and also present in the
offline reader. It selects a title immediately without rerunning analysis or
changing edited instructions. In-flight responses display according to the
currently selected perspective when they arrive. A new live visit defaults to
Resident. Saving a corrected offline reader retains the selected perspective.
Legacy results with one title use that same title in both views.

The two exported prompt files contain the same shared default. Edited instructions
replace it for a new batch or explicit retry, subject to existing schema/evidence
validation. This supersedes the October 29 mode-specific prompt implementation.
No additional calls, credentials, dependencies or permission changes are introduced.

Feedback tracking, automated feedback messages and participant attribution are
not implemented. The study uses separate forms and operator-defined recipient
batches; a title perspective is not an identity or access-control setting.
