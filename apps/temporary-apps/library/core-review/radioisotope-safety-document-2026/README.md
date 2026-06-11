# Radioisotope Safety Document 2026 Quiz Series

This series converts the eight sections of the 2026 RISC source corpus into separate interactive quizzes.

| Chapter | Questions |
| --- | ---: |
| 1. Introduction and Radiation Protection | 28 |
| 2. Radiation Biology | 60 |
| 3. Transport and Management of Radioactive Materials | 58 |
| 4. Regulatory Exposure Limits | 34 |
| 5. Radiopharmaceutical Administration | 61 |
| 6. Administrative Regulations, Responsibilities, and Training | 145 |
| 7. Emergency Procedures and Special Circumstances | 42 |
| 8. Radiation-Measuring Instrumentation and QC | 21 |
| **Total** | **449** |

The authoritative text files are in `apps/core-studying/Radioisotope Safety Document 2026/`. The section-by-section coverage map is `apps/core-studying/Radioisotope Safety Document/RISC-game-design-plan.md`.

Regenerate the full series with:

```powershell
python scripts\generate_risc_quizzes.py
```

The generator preserves stable app IDs, empty default answers, source-section explanations, balanced correct-answer positions, and the standard Tutor/Quiz mode interface.

