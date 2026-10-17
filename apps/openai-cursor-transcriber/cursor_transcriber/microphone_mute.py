from __future__ import annotations

import logging


def get_default_microphone_muted() -> bool | None:
    """Return the default Windows microphone endpoint mute state when available."""
    try:
        from pycaw.pycaw import AudioUtilities

        microphone = AudioUtilities.CreateDevice(AudioUtilities.GetMicrophone())
        if microphone is None:
            return None
        return bool(microphone.EndpointVolume.GetMute())
    except Exception:
        logging.exception("Could not read the default microphone mute state")
        return None


def set_default_microphone_muted(muted: bool) -> bool:
    """Set the default Windows microphone endpoint mute state."""
    try:
        from pycaw.pycaw import AudioUtilities

        microphone = AudioUtilities.CreateDevice(AudioUtilities.GetMicrophone())
        if microphone is None:
            return False
        microphone.EndpointVolume.SetMute(int(muted), None)
        return bool(microphone.EndpointVolume.GetMute()) == muted
    except Exception:
        logging.exception("Could not change the default microphone mute state")
        return False
