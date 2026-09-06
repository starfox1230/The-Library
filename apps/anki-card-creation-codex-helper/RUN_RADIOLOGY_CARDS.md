# Run radiology cards once
Revision: 2026-09-05

This is the entry point for a fresh Codex conversation. Execute the requested work in the current conversation; finding the old StudyOS task is unnecessary. The ChatGPT Anki Card Generator 3.0 project remains separate.

## Resolve current resources

The current Library checkout is `C:\Users\sterl\Documents\GitHub\The-Library`.
Resolve this guide and sibling guides from the same checkout. Prefer repository-relative paths inside the repository. If the checkout is unavailable, locate the configured Library project and verify its files; do not create an empty replacement or silently use a historical backup. The old OneDrive Documents GitHub path is not the current checkout.

StudyOS site: https://radiology-study-os.glut4.chatgpt.site
Site project: `appgprj_6a51c26bc9808191b3a487c7f49e6d32`
Local site checkout: `C:\Users\sterl\Documents\Codex\2026-07-10\files-mentioned-by-the-user-here\study-os-site`
Verify the project id against its `.openai/hosting.json` before using site tools. Use connected Notion and Sites tools; discover available capabilities rather than assuming a previous conversation's tool handles exist.

Run `python scripts/instruction_preflight.py --scope notion` from this directory (substitute the chosen scope). Read the returned required files in full. This script checks instruction availability and fingerprints only; it does not read Notion, generate cards, or verify remote access.

## Choose scope from the user's request

| Request | Scope | Work |
|---|---|---|
| Run my Notion-to-Anki pathway / Notion cards once | notion | Ordinary Radiology Notes marked Needed: current Chicago date plus previous six dates, and previously admitted unresolved pages. A supplied page/date/backlog request overrides this default cohort. |
| Convert my selected daily/conversation facts | conversation | Make Anki? checked and Anki Created? unchecked, using the separate conversation contract. |
| Process my StudyOS saved items | saved | Unprocessed saved events across dates. |
| Run the card phase once | cards | Eligible Radiology Notes, including Daily Learning pages, plus StudyOS saved events. |
| Run the nightly orchestration once / full nightly packet | nightly | Cards, coaching, tomorrow's quiz/audio/visual packet, and finalization. |

State the selected scope and date briefly, then proceed. Do not ask the user to choose when the wording already identifies the mode. A Notion-to-Anki run processes every admitted Radiology Notes page marked `Anki Card = Needed`, including Daily Learning pages. For a Daily Learning page, follow its dated linked view and process only rows marked `Make Anki?` whose `Anki Created?` box remains unchecked. The page-level `Needed` flag admits the container; the row-level check selects the facts.

The direct “selected conversation facts” scope remains a shortcut for running the row queue without waiting for its parent Daily Learning page to enter the ordinary date cohort. It is not a reason to exclude a `Needed` Daily Learning page from a Notion run. Legacy selected facts normally require an explicit legacy request, except when an eligible Daily Learning page explicitly embeds a dated legacy view; then that view is part of the admitted page's source.

A one-time run does not unpause, create, or change a recurring automation. The existing paused heartbeat is a separate entry point. Cards-only work does not require a current textbook assignment; a full packet needs an actual next assignment before generating its source-dependent artifacts.

## Load the relevant contracts

All card modes read `CARD_STYLE_GUIDE.md` and `APKG_PACKAGING.md`.
- notion: read `ANKI_COACHING_WORKFLOW.md` for the Notion source/output rules and `NIGHTLY_ORCHESTRATION.md` for Phase 1 and reconciliation. Do not generate coaching or tomorrow's packet in this mode.
- conversation: read `RADIOLOGY_CONVERSATION_ANKI_WORKFLOW.md`.
- saved/cards: read `NIGHTLY_ORCHESTRATION.md`, `ANKI_COACHING_WORKFLOW.md`, and `VISUAL_STUDY_AND_ANKI_SPEC.md`.
- nightly: read all of the above except the separate conversation contract unless selected conversation facts were requested; also read the Core and BoardVitals contracts named by the nightly workflow.
- Add the visual/PDF, Core, or BoardVitals guide when the actual source requires it, even in notion or conversation mode.

Ordinary Notion database: https://app.notion.com/p/0e388fc41d3949379a04de887ec774d8
Data source: `collection://09e980e6-c21b-4daa-beff-b70ca0decb2a`.
Fetch the current schema before querying or writing. Selection, source fields, and completion conditions come from the applicable source contract.

Use the current shared guide for writing, the source contract for eligibility, and packaging rules for the output format. Historical examples and older copied summaries are reference material. Apply current explicit user preferences without losing source identity, verified completion, or exact note-type compatibility. If StudyOS card preferences are absent, use the shared guide.

## Reconcile before generation

Use the shared ledger root `C:\Users\sterl\OneDrive\Study OS Private\nightly-runs`; this is an intentional private-data path, not the obsolete repository path.
Inspect prior run ledgers across dates for admitted unresolved sources and verified outputs. Record the current scope so a completed full packet cannot imply that a newly requested cohort has already been processed.
Before writes, check for a concurrent run touching the same sources. Serialize overlapping work rather than allowing two conversations to create competing candidates.

Preserve stable source and candidate identities from prior manifests. For multi-card sources, assign and persist the candidate mapping once; never recompute ordinals from a newly sorted batch on retry. Reconcile against active AND soft-deleted reviewer records. A user-edited, saved, or discarded candidate is not a missing candidate to recreate. Changed source content requires an explicit revision/reconciliation decision, not blind upsert over user work.
Compare against candidates already generated from other requested inputs to prevent duplicate imports of the same fact. Retain distinct intentional retrieval targets and required diagnosis/arrow sets. If access prevents reconciliation, report that source pending instead of claiming deduplication.

Capture an instruction receipt in the run ledger: scope, actual model/effort if exposed (otherwise unknown), resolved guide paths and SHA-256 hashes from preflight, optional preference snapshot, source IDs, candidate IDs, and output verification. This records the exact current files even when they have uncommitted changes. Preflight fingerprints do not prove that the model followed them.

## Finish at the correct boundary

Ordinary notes and saved events produce editable StudyOS candidates with required media; verify full ID sets and media before source status changes. Selected conversation facts follow their own output/checkbox contract. Use that contract's stable row IDs and verify prior output before setting Anki Created?.
Do not import into the live Anki collection as part of this entry point. The user reviews and imports.
Report source count, note/candidate count, output location, verified status changes, skipped/pending items, and next human action. Distinguish candidate approval, package export, and confirmed Anki import. An empty eligible cohort is a valid result.

## Model choice

Luna high is a reasonable starting trial for simple, well-specified text batches; it is not yet benchmarked for this user's workflow. Use the model selected in the conversation; a prompt cannot silently change it. Record actual settings if available.
For a difficult image relationship, contradictory source, or repeated quality failure, report the specific issue and recommend a stronger model for that item. A higher reasoning setting does not guarantee equivalence to Astra.
Judge by edits needed, omitted/duplicated targets, unsupported claims, image alignment, and verified handoffs. Do not infer Codex credit consumption from API token prices.
