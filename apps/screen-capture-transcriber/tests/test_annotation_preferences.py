from __future__ import annotations

import json

from screen_capture_transcriber.annotation_preferences import (
    DEFAULT_ANNOTATION_COLOR,
    AnnotationColorPreferences,
    load_annotation_preferences,
    remember_used_colors,
    save_annotation_preferences,
)


def test_annotation_color_preferences_round_trip_and_validate(tmp_path) -> None:
    path = tmp_path / "annotation-settings.json"
    save_annotation_preferences(
        AnnotationColorPreferences(
            selected_color="#33aaee",
            recent_colors=["#112233", "#445566", "#112233", "invalid"],
        ),
        path,
    )

    loaded = load_annotation_preferences(path)
    assert loaded.selected_color == "#33AAEE"
    assert loaded.recent_colors == ["#112233", "#445566"]

    path.write_text(
        json.dumps(
            {
                "selected_color": "not-a-color",
                "recent_colors": ["bad", "#ABCDEF"],
            }
        ),
        encoding="utf-8",
    )
    recovered = load_annotation_preferences(path)
    assert recovered.selected_color == DEFAULT_ANNOTATION_COLOR
    assert recovered.recent_colors == ["#ABCDEF"]


def test_recent_colors_only_change_when_used_colors_are_recorded() -> None:
    preferences = AnnotationColorPreferences(selected_color="#33AAEE")
    assert preferences.recent_colors == []

    remember_used_colors(preferences, [])
    assert preferences.recent_colors == []

    remember_used_colors(preferences, ["#112233", "#445566", "#112233"])
    assert preferences.recent_colors == ["#112233", "#445566"]
