# Physics Video Quiz Library

This collection organizes transcript-based physics quizzes by modality. The initial MRI release contains 28 quizzes and 150 questions.

Sources are the transcripts and video links registered in `apps/core-studying/YT Physics/index.json`. Question content is curated in `scripts/mri_physics_video_bank.py`; rendering and validation are handled by `scripts/generate_mri_physics_video_quizzes.py`.

Regenerate with:

```powershell
python scripts\generate_mri_physics_video_quizzes.py
```
