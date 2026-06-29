When you modify files under `apps/radiographics-review`, commit and push the app-scoped changes after verification so the online library updates promptly.

Use:

```powershell
powershell -ExecutionPolicy Bypass -File .\apps\radiographics-review\scripts\publish-site.ps1 -CommitMessage "<message>"
```

Reader pages must keep every figure image as a real link to its asset (`<a href="assets/...">`) with JavaScript-only lightbox enhancement. Do not replace figure links with button-only controls. After changing reader generation or importing/regenerating articles, run `npm test` from `apps/radiographics-review` and verify at least one generated study page opens a figure when clicked.
