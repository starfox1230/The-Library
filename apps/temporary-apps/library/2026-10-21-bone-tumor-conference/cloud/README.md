# Private Sites progress service

The owner-private Sites publication uses the maintained Sites Vinext starter, its `sites()` build integration, a D1 binding named `DB`, and the existing project ID. Authentication remains Sites dispatch-owned. The public GitHub Pages copy stays static and device-local; it links to the private reading room for account sync.

`progress-api.mjs` is the authored request handler. Install it as `lib/progress-api.mjs` in the private checkout. The `/api/progress` route exports dynamic GET and POST handlers that call `handleProgress(request, env.DB)`, importing `env` from `cloudflare:workers`. Place this app's HTML, JS, guide, private corpus, images, and PDFs in the starter's `public/` directory. Remove `static` from `.openai/hosting.json`, preserve `project_id`, and set `d1` to `DB` and unused `r2` to null. The root can serve the existing public `index.html`.

`schema.ts` is the Drizzle schema. The private checkout includes its generated initial SQL migration and Drizzle journal/snapshot. `0000_study_progress.sql` here is an equivalent review/test fixture, not a second migration to apply. Generate and commit migrations in the private Site through the Sites workflow; never create tables in request handlers. Sites applies published migrations before starting the Worker. Source PDFs and runtime progress must never enter this public repository.

Records are scoped by the authenticated Site user ID supplied in `oai-authenticated-user-id`. The request body cannot choose an account. The API rejects unauthenticated access, cross-origin writes, unknown fields, invalid values, future timestamps, and oversized batches. It sends private/no-store responses. Each check, flag, note, or reader preference is a separate record. The newest timestamp wins for the same field, with a deterministic value tie-breaker. Separate fields merge independently. Explicit false/empty values preserve removals. Client clocks adjust to the server after the initial pull.

`sync.js` keeps a durable local queue, migrates existing browser annotations with their historical timestamps, pulls before pushing, debounces edits, and refreshes every 15 seconds while visible or on focus/reconnect. Small requests use keepalive when the page closes. A failed write remains queued until that device reconnects. The save indicator exposes success, pending, sign-in, offline, and retry states. Reader position restores on opening without jumping an active reader to another device's page. No credentials or account IDs are embedded in browser code.

Run the regression checks with Node 24 or newer:

```powershell
node cloud/test-sync.mjs
```

The tests use an isolated in-memory SQLite database and two independent browser storage models. Local browser QA additionally uses the Sites portable mock sign-in and D1 binding, with `127.0.0.1` and `localhost` as separate storage contexts for the same mock account.
