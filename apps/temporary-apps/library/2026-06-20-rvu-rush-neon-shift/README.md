# RVU Rush // Neon Shift

A local-first daily radiology work-RVU tracker presented as a neon arcade/RPG shift.

## Data

- Source: CMS Physician Fee Schedule relative value file `RVU26C`
- Release: July 2026 release, published May 20, 2026
- Field used: physician `WORK RVU`
- Component used: modifier `26` (professional component)
- CMS page: <https://www.cms.gov/medicare/payment/fee-schedules/physician/pfs-relative-value-files/rvu26c>

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

All records remain in browser `localStorage` unless exported manually as CSV.
