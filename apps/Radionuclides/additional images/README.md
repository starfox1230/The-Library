# Additional Images Placeholder Folders

These subfolders are reserved for future additional images for each radionuclide card.

- `co-57/`
- `cr-51/`
- `f-18/`
- `ga-67/`
- `ga-68/`
- `i-123/`
- `i-125/`
- `i-131/`
- `in-111/`
- `kr-81/`
- `lu-177/`
- `mo-99/`
- `n-13/`
- `p-32/`
- `ra-223/`
- `rb-82/`
- `sm-153/`
- `sr-89/`
- `tc-99/`
- `tl-201/`
- `xe-133/`
- `y-90/`

## Naming behavior

The app now checks for additional images in this order:

1. Local directory listing, when the page is served by a server that exposes folder contents.
2. A cached GitHub repository-tree lookup, which auto-discovers arbitrary filenames from the repo without a manual manifest.
3. A numbered-file fallback for strict local/offline cases.

That means arbitrary filenames like `Girl with glowing orb at cave entrance.png` will work on supported local servers and on the deployed GitHub-backed app.

If you open the app in an environment that does not expose directory listings and cannot reach GitHub, use sequential numeric filenames (`1.png`, `2.png`, `3.jpg`, etc.) so the fallback can still discover them.
