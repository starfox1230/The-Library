# PowerScribe release delivery

The user explicitly requested on 2026-10-02 that every future update to the report
extractor or API probe also be put in their existing Google Drive release folder.
Include this delivery step whenever publishing an updated portable build.

- Drive path: `My Drive / Mouse Settings / AutoHotKey / UAB / Review AHKs`
- Folder ID: `1-uUzIOH9ja_QxGk0KekCXUVlx0ZbOgRj`
- Folder URL: https://drive.google.com/drive/folders/1-uUzIOH9ja_QxGk0KekCXUVlx0ZbOgRj
- Local Google Drive for desktop path on Sterling's computer:
  `G:\My Drive\Mouse Settings\AutoHotKey\UAB\Review AHKs`

Build and run the appropriate checks, package a versioned portable ZIP, then
upload it to this folder. Preserve older versions and existing sharing. Reuse an
existing identical ZIP instead of creating duplicates. If the same version name
contains different bytes, increment the release version before publishing.

Use the Google Drive connector when write access is available. On 2026-10-02 its
upload action returned `ACCESS_TOKEN_SCOPE_INSUFFICIENT`; the mounted Google
Drive folder is an authorized alternative. Verify its existing contents match
the Drive folder before copying. Verify local SHA-256 after copying and use
connector readback to confirm cloud synchronization before saying it is uploaded.
If synchronization is pending, report that explicitly.

Include observed Drive download links in the final delivery. Do not upload report
exports, credentials, logs, or other workstation data as part of release delivery.
This instruction covers both `PowerScribeReportExporter-v*.zip` and
`PowerScribeApiProbe-v*.zip`, including updates made under `api-probe/`.
