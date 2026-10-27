# Getting report revisions internally from PowerScribe

Research date: October 2, 2026. Sterling reports **PowerScribe 360 v4.0 SP9, build 7.0.528.24** under Help → About on the UAB workstation.

An API or a server-side export could remove the repeated GUI operations entirely. That is a separate integration from the native keyboard executable. Availability depends on the installed version, the supported interface, and the site's configured access.

## Strongest current leads

Sterling supplied an August 27, 2026 email exchange in which Dr. Steven Rothenberg said his PowerScribe integrations collect draft and preliminary reports for all residents every four minutes. He offered to share the code after preparing it for public release and offered a demonstration call. This is direct correspondence supplied by Sterling, not an independently verified deployment or a published API specification. A public release of his specific tool was not located in this search. His email does not establish whether it also retrieves final reports or historical revisions.

A separate public project, Phillip Cheng's [ReportDiff](https://pcheng.org/reportdiff/), describes direct collection of resident preliminary reports followed by retrieval of their final versions. Its [retrieval repository](https://github.com/pmcheng/reportdiff) includes actual PowerScribe 360 integration code. This is a concrete implementation reference, superseding the earlier finding that no public retrieval methods had been located. It is not Rothenberg's code.

### What the public code actually does

- [powerscribe.py](https://github.com/pmcheng/reportdiff/blob/master/powerscribe/powerscribe.py) constructs authenticated SOAP requests to PowerScribe 360 services under `/RAS/`. It implements `BrowseOrdersDV`, `GetReportChain`, `GetReport`, accession search, and account lookup. Its report-status filters include Draft, PendingSignature, and Final. These are methods in historical third-party code, not a verified current vendor-supported API contract for UAB.
- [ps_reportdiff.py](https://github.com/pmcheng/reportdiff/blob/master/powerscribe/ps_reportdiff.py) searches PendingSignature reports, saves their text and dictator information locally, and later checks the same accessions for Final text and signer information. It also records timestamps. Its loop waits five minutes between passes. It captures preliminary text prospectively; it does not demonstrate recovery of an old preliminary revision after finalization.
- The project dates to 2015, and the integration module carries a 2015-2019 copyright and Apache 2.0 license. Treat it as a reference requiring compatibility review, not a ready-to-run connector for the current hospital installation.

Direct retrieval is the preferred integration to investigate. The current native keyboard exporter remains a fallback for manual collection while access and compatibility are resolved.

### Portable workstation diagnostic

The separate [PowerScribe API Probe v0.5](api-probe/README.md) provides offline configuration/registry server discovery, connection-only sign-in, and exact-accession `GetReportChain` / `GetReport` tests. The initial finder returned RADPEER and Critical Results addresses at UAB; v0.2 excludes those unrelated services and reads address settings under Nuance/Commissure registry branches. Its executable has no Python, PowerShell, or AHK runtime dependency. A separate fixed-category diagnostic summary excludes report values, identifiers, credentials, and server address; retrieved text remains available only in the local report tab and optional local export. v0.3 adds bounded local SOAP error details with exact entered-secret redaction. v0.4 adds credential-free WSDL/XSD inspection with restricted same-service imports, and defaults the client build to the observed workstation build. The metadata summary can include strictly constrained Nuance protocol action identifiers, never arbitrary remote text or endpoint URLs. v0.5 distinguishes inspection/connection/accession save labels and replaces stale inspection results after a test setup failure with a current no-request-sent explanation. Saving writes the displayed result; it does not run a test. 68 simulated/form/registry-fixture/loopback tests pass.

Sterling's October 2 v0.2 test, recorded in [Cross Talk with codex](https://app.notion.com/p/3ed1d7063539809ba891da68306bc08d), used HTTPS and client build `7.0.154.0` and stopped at sign-in with a generic SOAP fault. No accession search occurred. The response indicates a SOAP service answered; it does not establish correct application configuration or identify the reason for the rejection. Successful UAB authentication and historical revision retrieval remain unconfirmed.

The subsequent v0.3 test identified **Missing/Invalid Session Header** in Nuance's `AccountSessionMessageInspector.AfterReceiveRequest`. This suggests a rejection in session handling before sign-in completes, rather than demonstrating an incorrect password. The implemented initial sign-in omits a session token, matching historical ReportDiff. The current UAB sign-in contract and server configuration need investigation; changing the client build or reading WSDL is diagnostic, not an established solution.

## What the official documentation confirms

- **PowerScribe 360 has a Web Services API.** Nuance's [version feature comparison](https://isupportcontent.nuance.com/healthcare/documents/ats/resource/p36/p36a039.pdf) explicitly describes NPI exposure through that API in versions 3.5 and 4.0. This establishes that an interface exists; it does not establish a method for fetching historical report text.
- **The 360 portal can find and display reports.** Nuance's [portal help](https://isupportcontent.nuance.com/Healthcare/Admin_Portal_Help/Using_the_PS360_Portal_Web_Page.htm) lists report access for resident, fellow, and attending roles. The feature comparison also documents CDA report downloads from the portal beginning in version 2.5. Neither source confirms a bulk download of paired resident and final revisions.
- The [360 System Administrator Guide](https://isupportcontent.nuance.com/healthcare/documents/sales/opmanual/3900/l-3906.pdf) documents Web Services logging and administrator-configured portal access. Site administrators are the practical source for the relevant API documentation and installed configuration.
- **PowerScribe One** documents licensed Web Service APIs and IRadWhere desktop integration in its [system configuration guide](https://learn.microsoft.com/en-us/industry/healthcare/powerscribe-one/admin-guide/set-up-your-organization/system-configuration). That is a different product/version context and should not be assumed to apply unchanged to 360.

## What has not been established

Public code establishes a concrete route for **prospective preliminary/final collection**. It does not establish which UAB permissions or licenses are required, or whether Compare Report Revisions history can be exported after reports are finalized. Sterling attempted a local SOAP sign-in on the UAB workstation; it returned a fault before any report lookup. This agent has not accessed the UAB workstation or its services.

Exporting only final reports is insufficient for the comparison workflow. A useful source must retain and expose historical revision text, revision state, authors, and the association between versions of the same study. A preliminary-report interface might help only if the resident's relevant revision is actually retained and exposed in that configuration.

For prospective polling, a report could be finalized between collection passes before its resident text is saved. The collection design therefore needs a way to recover missed revisions, or a measured and accepted completeness limit. Neither the email nor the public example establishes complete capture of all resident reports.

## Follow-up for Dr. Rothenberg

Ask for the current code or repository and the PowerScribe product/version it targets. Confirm whether it uses server services, database queries, or another interface; what account permissions and configuration it requires; whether it pairs resident text with final attending text and author identities; and whether it supports historical backfill or only ongoing collection. An example export with synthetic report text would let us design the converter without connecting to the hospital first.

## Concrete question for radiology informatics / the PowerScribe administrator

> For my resident report-review workflow, can our PowerScribe 360 installation provide a read-only bulk export or supported API access to the resident's approved/submitted report text and the attending's final signed text for the same studies? I need the matching report/study IDs, revision dates, and author/signer names. Does the Web Services API expose historical report revisions, or could your team provide an extract from the revision history used by Compare Report Revisions?

The minimum useful extract is one paired record per study, with `study_id`, `report_id`, `resident_revision_id`, `resident_text`, `resident_timestamp`, `resident_author`, `final_revision_id`, `final_text`, `final_timestamp`, and `final_signer`. Fields can be adapted to the supported export rather than requiring those exact column names. This is a proposed output contract, not a claim about the database schema.

Once a documented supported interface or an example export is available, the local converter can produce the existing Case / Attending Report / Resident Report document without repeatedly opening the comparison window. An administrator-provided export is an option to request; it is not confirmed to exist in the current installation.
