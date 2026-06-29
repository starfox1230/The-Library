# Core Radiology Bone Tumors APKG

Source: Core Radiology, 2nd edition, section 13.03, Bone Tumors.

Source text: `apps/core-studying/Core_Radiology/Chapter13/13.03 - Bone Tumors.txt`

PDF context: canonical PDF `G:\My Drive\0. Radiology\Core Radiology 2nd ed.pdf`, printed pages MSK 934-936, PDF viewer pages 946-948.

Output: `bone-tumors.apkg`

Note count: 29

Asset count: 6

Build command:

```powershell
python apps\anki-card-creation-codex-helper\core-radiology\2026-06-27-bone-tumors\build_package.py
```

Image handling: rendered full-page source screenshots for MSK 934-936 and cropped three front-side radiograph cards from MSK 935 for lamellated periosteal reaction, sunburst periosteal reaction, and Codman triangle.

Intentionally skipped:

- The MSK 934 global approach flowchart was used for card selection but not made into an image-front card because it is a text algorithm rather than a diagnostic image.
- The normal periosteal anatomy and drawn periosteal reaction cartoons on MSK 935 were skipped as front-side images because the radiographs are more board-relevant visual material.
- The rare chondromyxoid fibroma location detail was skipped as lower-yield relative to the main eccentric lesion list.
- The broad list of benign characteristic lesions on MSK 934 was not converted into a memorization list because the follow-up Core Radiology section organizes these by cell of origin.
