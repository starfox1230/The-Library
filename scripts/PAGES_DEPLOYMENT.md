# Library web publication

GitHub Pages publishes the staged output of `scripts/build-pages.py`, rather than the entire repository. The previous all-repository artifact was over 2 GB and timed out in Pages deployment.

The staging script keeps the web pages and their runtime files. It excludes hidden development folders, caches, temporary/export directories, native Anki packages and binaries, native companion audio, and binary test fixtures. Selected large public media (Anki helper review images, the manual audio player MP3s, and the top-level Radionuclides images) also stay in GitHub rather than being copied into Pages.

For omitted files, explicit relative references in published HTML, CSS, JavaScript, JSON, and other text assets are rewritten to HTTPS raw.githubusercontent.com URLs pinned to the deployed commit. The repository source files and original assets remain intact. These assets require network access to GitHub; they are not bundled for offline use. Pages URLs for omitted files are not standalone download endpoints; use their rewritten links from the published pages or the repository itself.

The builder refuses missing tracked web files and packages above 950,000,000 bytes, leaving space for archive metadata below Pages' 1 GB limit. It also checks that the Library landing page and Afterglow's page, alert script, and bell audio are present. `.nojekyll` is generated in the staged site.

Run from a full checkout:

```sh
python scripts/build-pages.py --output /tmp/library-pages
```

The output must be a new directory. The workflow validates the quizzes, builds this package, and uploads only the staged directory. After deployment, check the Actions result and the actual live app release.
