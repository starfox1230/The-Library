from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .settings import get_setting, set_setting, toggle_setting


TTS_AUDIO_SETTING = "tts_enabled_card_audio"
_PATCHED = False
_ORIGINAL_PLAY_TAGS = None
_ORIGINAL_APPEND_TAGS = None


def is_tts_audio_enabled() -> bool:
    return bool(get_setting(TTS_AUDIO_SETTING))


def set_tts_audio_enabled(enabled: bool) -> bool:
    return bool(set_setting(TTS_AUDIO_SETTING, bool(enabled)))


def toggle_tts_audio_enabled() -> bool:
    return bool(toggle_setting(TTS_AUDIO_SETTING))


def _tts_tag_type():
    try:
        from anki.sound import TTSTag
    except Exception:
        return None
    return TTSTag


def _is_tts_tag(tag: Any) -> bool:
    tts_tag = _tts_tag_type()
    if tts_tag is not None:
        try:
            return isinstance(tag, tts_tag)
        except Exception:
            pass
    return type(tag).__name__ == "TTSTag"


def _filtered_tags(tags: Iterable[Any] | None) -> list[Any]:
    tag_list = list(tags or [])
    if is_tts_audio_enabled():
        return tag_list
    return [tag for tag in tag_list if not _is_tts_tag(tag)]


def _patch_av_player() -> None:
    global _PATCHED
    global _ORIGINAL_PLAY_TAGS
    global _ORIGINAL_APPEND_TAGS

    if _PATCHED:
        return

    try:
        from aqt.sound import av_player
    except Exception:
        return

    player_cls = av_player.__class__
    if getattr(player_cls, "_anki_pocket_knife_tts_audio_patched", False):
        _PATCHED = True
        return

    original_play_tags = getattr(player_cls, "play_tags", None)
    original_append_tags = getattr(player_cls, "append_tags", None)
    if not callable(original_play_tags) or not callable(original_append_tags):
        return

    _ORIGINAL_PLAY_TAGS = original_play_tags
    _ORIGINAL_APPEND_TAGS = original_append_tags

    def patched_play_tags(self, tags) -> None:
        filtered = _filtered_tags(tags)
        _ORIGINAL_PLAY_TAGS(self, filtered)

    def patched_append_tags(self, tags) -> None:
        filtered = _filtered_tags(tags)
        if not filtered:
            return
        _ORIGINAL_APPEND_TAGS(self, filtered)

    setattr(player_cls, "play_tags", patched_play_tags)
    setattr(player_cls, "append_tags", patched_append_tags)
    setattr(player_cls, "_anki_pocket_knife_tts_audio_patched", True)
    _PATCHED = True


def install() -> None:
    _patch_av_player()
