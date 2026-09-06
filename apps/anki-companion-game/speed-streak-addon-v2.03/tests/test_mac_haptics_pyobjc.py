from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "mac_haptics_pyobjc.py"
SPEC = importlib.util.spec_from_file_location("speed_streak_mac_haptics_pyobjc", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class _AllocatingType:
    @classmethod
    def alloc(cls):
        return cls()


class _Parameter(_AllocatingType):
    def initWithParameterID_value_(self, parameter_id, value):
        self.value = (parameter_id, value)
        return self


class _Event(_AllocatingType):
    def initWithEventType_parameters_relativeTime_duration_(self, event_type, parameters, when, duration):
        self.value = (event_type, parameters, when, duration)
        return self


class _Pattern(_AllocatingType):
    def initWithEvents_parameters_error_(self, events, parameters, error):
        self.events = events
        return (self, None)


class _Player:
    def __init__(self):
        self.started = False

    def startAtTime_error_(self, when, error):
        self.started = True
        return (True, None)

    def stopAtTime_error_(self, when, error):
        self.started = False
        return (True, None)


class _Engine:
    def __init__(self):
        self.players = []

    def setPlaysHapticsOnly_(self, value):
        pass

    def setAutoShutdownEnabled_(self, value):
        pass

    def setStoppedHandler_(self, callback):
        self.stopped_handler = callback

    def setResetHandler_(self, callback):
        self.reset_handler = callback

    def startAndReturnError_(self, error):
        return (True, None)

    def createPlayerWithPattern_error_(self, pattern, error):
        player = _Player()
        self.players.append(player)
        return (player, None)

    def stopWithCompletionHandler_(self, callback):
        pass


class _DeviceHaptics:
    def __init__(self, localities):
        self.localities = localities
        self.engines = {}

    def supportedLocalities(self):
        return self.localities

    def createEngineWithLocality_(self, locality):
        engine = _Engine()
        self.engines[str(locality)] = engine
        return engine


class _Controller:
    def __init__(self, localities):
        self.device_haptics = _DeviceHaptics(localities)

    def haptics(self):
        return self.device_haptics

    def vendorName(self):
        return "Test Pad"


CORE = type(
    "CoreHaptics",
    (),
    {
        "CHHapticEventParameter": _Parameter,
        "CHHapticEvent": _Event,
        "CHHapticPattern": _Pattern,
        "CHHapticEventParameterIDHapticIntensity": "intensity",
        "CHHapticEventParameterIDHapticSharpness": "sharpness",
        "CHHapticEventTypeHapticContinuous": "continuous",
    },
)


class PyObjCMacHapticsTests(unittest.TestCase):
    def test_dual_handle_controller_preserves_strong_and_weak_channels(self):
        controller = _Controller(["LeftHandle", "RightHandle", "Default"])
        session = MODULE._ControllerSession(controller, {"CoreHaptics": CORE})

        self.assertTrue(session.available)
        self.assertEqual(sorted(session.engines), ["left", "right"])
        self.assertTrue(session.play([{"duration": 100, "strong": 0.8, "weak": 0.25}]))
        self.assertTrue(controller.device_haptics.engines["LeftHandle"].players[0].started)
        self.assertTrue(controller.device_haptics.engines["RightHandle"].players[0].started)

    def test_default_locality_plays_combined_pattern(self):
        controller = _Controller(["Default"])
        session = MODULE._ControllerSession(controller, {"CoreHaptics": CORE})

        self.assertEqual(sorted(session.engines), ["default"])
        self.assertTrue(session.play([{"duration": 80, "strong": 0.4, "weak": 0.3}]))

    def test_backend_is_silent_outside_macos(self):
        backend = MODULE.PyObjCMacHaptics(MODULE_PATH.parent)
        if not sys.platform.startswith("darwin"):
            self.assertFalse(backend.available)
            self.assertEqual(backend.backend_name, "not-macos")
            self.assertFalse(backend.diagnostics["dependencyInstallAttempted"])

    def test_macos_uses_browser_fallback_without_starting_dependency_install(self):
        with mock.patch.object(MODULE.sys, "platform", "darwin"):
            backend = MODULE.PyObjCMacHaptics(MODULE_PATH.parent)
            self.assertFalse(backend.available)
            self.assertEqual(backend.backend_name, "browser-fallback")
            self.assertEqual(backend.diagnostics["dependencyInstallState"], "disabled-browser-fallback")
            self.assertTrue(backend.diagnostics["browserFallbackSelected"])
            self.assertFalse(backend.diagnostics["dependencyInstallAttempted"])

        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("sys.executable", source)
        self.assertNotIn("subprocess.run", source)
        self.assertNotIn('"-m"', source)


if __name__ == "__main__":
    unittest.main()
