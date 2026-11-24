from __future__ import annotations

from pathlib import Path
import sys
import time

from PySide6.QtCore import QCoreApplication, QUrl
from PySide6.QtMultimedia import QSoundEffect


ROOT = Path(__file__).resolve().parents[1] / "Audio_trimmed"
RELATIVE_PATHS = (
    "kenney_impact-sounds/Audio/footstep_grass_004.wav",
    "kenney_rpg-audio/Audio/drawKnife2.wav",
    "kenney_impact-sounds/Audio/impactSoft_heavy_000.wav",
    "kenney_impact-sounds/Audio/impactPlank_medium_002.wav",
    "kenney_casino-audio/Audio/chips-handle-3.wav",
    "kenney_impact-sounds/Audio/impactMining_002.wav",
    "kenney_rpg-audio/Audio/bookFlip2.wav",
    "kenney_ui-audio/Audio/switch9.wav",
    "kenney_impact-sounds/Audio/impactBell_heavy_000.wav",
)


def main() -> None:
    application = QCoreApplication.instance() or QCoreApplication([])
    effects: list[QSoundEffect] = []
    for relative_path in RELATIVE_PATHS:
        effect = QSoundEffect()
        effect.setSource(QUrl.fromLocalFile(str((ROOT / relative_path).resolve())))
        effects.append(effect)

    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline and not all(effect.isLoaded() for effect in effects):
        application.processEvents()
        time.sleep(0.01)

    loaded = sum(effect.isLoaded() for effect in effects)
    print(f"loaded {loaded} of {len(effects)}")
    for relative_path, effect in zip(RELATIVE_PATHS, effects):
        print(relative_path, effect.status())
    if loaded != len(effects):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
