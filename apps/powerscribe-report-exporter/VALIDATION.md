# First-pair investigation — November 2, 2026

The user confirmed the duplicate is already in the saved comparison text, before
website ingestion. This places the failure upstream of website analysis.

## Evidence and limits

- The actual v0.18 and v0.19 release assemblies were each tested across 40
  synthetic three-case exports, at source-label starts 1 and 11. The 240 distinct
  pairs remained distinct through archive, comparison file, injected clipboard
  delivery, copied-text viewer and website parser. This did not reproduce an
  unconditional duplicate append, and does not establish what PowerScribe
  returned on the hospital workstation.
- A separate controlled replay **does reproduce** a first-pair duplicate in the
  published v0.18 binary. The fake desktop advances correctly twice and issues
  exactly six Ctrl+C commands for three studies. During each second-study read,
  the earlier string is returned while the clipboard sequence advances to newer
  data. The old acceptance check associates that earlier string with the newer
  update number. Saved case 2 repeats case 1; the same occurs at starts 11/12.
- In the v0.20 binary, the exact same fixture saves the correct second pair.
  Both replays keep two row advances and six copy commands; no comparison
  reopen is needed. This demonstrates a real read/check race, not proof that it
  is the cause of the user's workstation failure.

Run the binary comparison on Windows after building:

```powershell
python apps/powerscribe-report-exporter/dev/check-published-first-pair-race.py
```

The script needs the preserved v0.18 ZIP in `dist` and the current built EXE.
It runs real assemblies against synthetic desktop/clipboard implementations;
it does not operate PowerScribe or the real clipboard. Harnesses and exports are
kept in a unique temporary directory and are not included in the release.

## v0.20 verification

**134 synthetic/native-control tests passed.** Relevant new checks cover:

- A mid-read clipboard replacement at starts 1 and 11: correct source/report
  association without extra Ctrl+C, comparison opens, navigation or confirmation.
- Permanently changing clipboard snapshots: no save or Down, with an explicit
  unstable-read diagnosis. Existing delayed-rendering and clipboard-lock checks
  remain valid. The optional accessibility copy path also samples sequence and
  owner on both sides of the read; no actual PowerScribe provider was tested.
- Snapshot object reuse and mutation, immutable source-number/formatted-record
  binding, and exact capture/save token joins for both output files.
- Deliberate same-length first-record substitution during writing: byte readback
  rejects it and retains the previously verified prefix. Duplicate source saves
  and wrong source-pair serialization are rejected before appending.
- Delivery excludes an unverified tail and rejects a truncated verified prefix.
- Repeated pairs already present at capture are distinguishable from save errors
  in the new capture-checks ledger. No report text/headers appear in that ledger;
  its equality key is random per run and never persisted.
- Existing interrupted-run recovery, cancellation, linked-study preservation,
  pending/unavailable handling and launcher checks still pass. The speculative
  automatic first-pair comparison reopen from v0.19 has been removed.

Workstation follow-up: export three known distinct studies and inspect the saved
comparison text. If it still repeats, retain `.capture-checks.csv` and the normal
progress log; the capture versus verified-save stages can then be compared
without submitting report text. The original hospital failure is not marked
resolved until that trial confirms it.

## Portable delivery

- [PowerScribeReportExporter-v0.20.zip](https://drive.google.com/file/d/18-aYcd1Kygx2Ldc1G5j1S8Y9Z2zfjq-A/view?usp=drivesdk)
- ZIP: **71,910 bytes**; SHA-256
  `69a7ff2ae9ea44ccc31d8e37b3034ddc7bea53c3bf0d3cf388689067318ef488`.
- Tested EXE SHA-256:
  `15a01953a95ef8a1fc725f6af7d9b76bd196a94b84a2332cda8c63c936e28548`.
- Archive allowlist: tested EXE, README.md and QUICK_START.txt. No captures,
  diagnostics, source reports, tests, settings or credentials are included.
- Embedded EXE hash and mounted-Drive copy hash match. Connector readback
  confirmed synced file name/size/ID and the existing release-folder parent.
  Prior versions and sharing were preserved. This update changes only the
  extractor; it does not deploy the earlier website changes.
