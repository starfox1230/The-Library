# RVU Rush // Neon Shift

A local-first daily radiology work-RVU tracker presented as a neon arcade/RPG shift.

The primary mobile surface is optimized as an iPhone companion: a fixed-height one-handed
logger, safe-area-aware bottom navigation, dedicated scrolling study list, 44+ px touch
targets, no input zoom, and a lower-cost graphics profile on compact/coarse-pointer devices.
It also includes an install manifest for Safari's **Add to Home Screen** workflow.

## Data

- Source: CMS Physician Fee Schedule relative value file `RVU26C`
- Release: July 2026 release, published May 20, 2026
- Field used: physician `WORK RVU`
- Component used: modifier `26` (professional component)
- CMS page: <https://www.cms.gov/medicare/payment/fee-schedules/physician/pfs-relative-value-files/rvu26c>
- Coding guardrails: 2026 CMS NCCI Policy Manual, Chapter 9 (Radiology Services)
  <https://www.cms.gov/files/document/09-chapter9-ncci-medicare-policy-manual-2026-final.pdf>

The app uses original plain-language study labels rather than copying CMS/AMA descriptions.
Values are intended for personal productivity tracking, not billing, reimbursement, or
employment compensation calculations.

## Interaction model

- Click modality, then study.
- Click one of three recent studies to repeat it in one action.
- Press `Alt+1` through `Alt+7` to switch modality.
- Press `1` through `9` to log one of the first visible studies.
- Press `Q`, `W`, or `E` to repeat a recent study.
- Press `/`, type a study or CPT code, and press `Enter` to log the top match.
- Press `L` to enter link mode, select multiple studies, then press `Enter` to log the set.
- Common linked presets cover CT chest/abdomen/pelvis, CTA head/neck, trauma CT,
  pelvic ultrasound, screening mammography/tomosynthesis, and brain MRI/MRA.

Linked sets keep each study separately identifiable and add their work RVUs. Known cases
where one comprehensive code represents both selected services are automatically merged
instead of double-counted. Linking is a workflow tool, not a claim-scrubbing or billability
determination.

All records remain in browser `localStorage` unless exported manually as CSV.
