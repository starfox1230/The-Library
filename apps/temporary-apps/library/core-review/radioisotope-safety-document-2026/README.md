# Radioisotope Safety Document 2026 Quiz Series

This series converts the eight sections of the 2026 RISC source corpus into separate interactive quizzes.

| Chapter | Questions |
| --- | ---: |
| 1. Introduction and Radiation Protection | 18 |
| 2. Radiation Biology | 29 |
| 3. Transport and Management of Radioactive Materials | 24 |
| 4. Regulatory Exposure Limits | 18 |
| 5. Radiopharmaceutical Administration | 24 |
| 6. Administrative Regulations, Responsibilities, and Training | 38 |
| 7. Emergency Procedures and Special Circumstances | 24 |
| 8. Radiation-Measuring Instrumentation and QC | 12 |
| **Total** | **187** |

The authoritative text files are in `apps/core-studying/Radioisotope Safety Document 2026/`. The manually authored bank is in `scripts/risc_curated_bank.py`.

Source ambiguities intentionally omitted from scored items include the conflicting 5.3 mSv and 6.2 mSv annual-population totals and the internally inconsistent Chapter 4 public-dose line that pairs 50 mrem with 5 mSv.

Regenerate the full series with:

```powershell
python scripts\generate_risc_quizzes.py
```

The generator validates sequential IDs, unique choices, closed lead-ins, answer keys, and balanced A-D positions. Bank version 2 intentionally starts with empty progress because the original mechanically generated questions were replaced.
