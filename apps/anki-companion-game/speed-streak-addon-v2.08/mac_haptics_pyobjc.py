from __future__ import annotations

import importlib
import logging
import platform
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping


LOGGER = logging.getLogger(__name__)
def _clamp(value: Any, minimum: float = 0.0, maximum: float = 1.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    return max(minimum, min(maximum, numeric))


def _result_value(result: Any) -> Any:
    return result[0] if isinstance(result, tuple) and result else result


def _result_error(result: Any) -> Any:
    return result[1] if isinstance(result, tuple) and len(result) > 1 else None


class _ControllerSession:
    def __init__(self, controller: Any, modules: Mapping[str, Any]) -> None:
        self.controller = controller
        self.modules = modules
        self.localities: List[str] = []
        self.engines: Dict[str, Any] = {}
        self.players: List[Any] = []
        self.last_error = ""
        self._attach()

    @property
    def available(self) -> bool:
        return bool(self.engines)

    @property
    def vendor_name(self) -> str:
        try:
            return str(self.controller.vendorName() or "Unknown controller")
        except Exception:
            return "Unknown controller"

    def play(self, raw_steps: List[Mapping[str, Any]]) -> bool:
        if not self.available:
            return False
        self.stop()
        steps: List[Dict[str, float]] = []
        for raw in raw_steps:
            try:
                steps.append(
                    {
                        "duration": _clamp(raw.get("duration", 0), 0.0, 10_000.0),
                        "weak": _clamp(raw.get("weak", 0)),
                        "strong": _clamp(raw.get("strong", 0)),
                    }
                )
            except Exception:
                continue
        if not steps:
            return False

        played = False
        for role, engine in self.engines.items():
            if role == "left":
                played = self._start_pattern(engine, steps, "strong") or played
            elif role == "right":
                played = self._start_pattern(engine, steps, "weak") or played
            else:
                played = self._start_pattern(engine, steps, "combined") or played
        return played

    def stop(self) -> None:
        for player in self.players:
            try:
                player.stopAtTime_error_(0, None)
            except Exception:
                pass
        self.players = []

    def shutdown(self) -> None:
        self.stop()
        for engine in self.engines.values():
            try:
                engine.stopWithCompletionHandler_(None)
            except Exception:
                pass
        self.engines = {}

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "vendorName": self.vendor_name,
            "supportedLocalities": list(self.localities),
            "activeEngineRoles": sorted(self.engines),
            "lastError": self.last_error,
        }

    def _attach(self) -> None:
        try:
            haptics = self.controller.haptics()
        except Exception as exc:
            self.last_error = f"Could not query controller haptics: {exc}"
            return
        if haptics is None:
            self.last_error = "Apple did not expose haptics for this controller."
            return

        try:
            supported = list(haptics.supportedLocalities() or [])
        except Exception:
            supported = []
        self.localities = [str(value) for value in supported]
        classified = [(self._locality_role(value), value) for value in supported]
        left = next((value for role, value in classified if role == "left"), None)
        right = next((value for role, value in classified if role == "right"), None)

        if left is not None and right is not None:
            left_engine = self._make_engine(haptics, left)
            right_engine = self._make_engine(haptics, right)
            if left_engine is not None:
                self.engines["left"] = left_engine
            if right_engine is not None:
                self.engines["right"] = right_engine
            if self.engines:
                return

        fallback = next((value for role, value in classified if role == "default"), None)
        if fallback is None and supported:
            fallback = supported[0]
        if fallback is not None:
            engine = self._make_engine(haptics, fallback)
            if engine is not None:
                self.engines["default"] = engine
        elif not supported:
            # Some controller/OS combinations expose the Default engine but do
            # not populate supportedLocalities. The reference Anki add-on that
            # physically worked on macOS uses this compatibility fallback.
            engine = self._make_engine(haptics, "Default")
            if engine is not None:
                self.engines["default"] = engine
                self.localities = ["Default (compatibility fallback)"]

    @staticmethod
    def _locality_role(locality: Any) -> str:
        normalized = str(locality or "").replace("_", "").replace(" ", "").lower()
        if "lefthandle" in normalized:
            return "left"
        if "righthandle" in normalized:
            return "right"
        if "default" in normalized:
            return "default"
        return "other"

    def _make_engine(self, haptics: Any, locality: Any) -> Any:
        try:
            engine = _result_value(haptics.createEngineWithLocality_(locality))
            if engine is None:
                return None
            setter = getattr(engine, "setPlaysHapticsOnly_", None)
            if callable(setter):
                setter(True)
            setter = getattr(engine, "setAutoShutdownEnabled_", None)
            if callable(setter):
                setter(False)
            stopped_setter = getattr(engine, "setStoppedHandler_", None)
            if callable(stopped_setter):
                stopped_setter(lambda reason, active_engine=engine: self._restart_engine(active_engine, reason))
            reset_setter = getattr(engine, "setResetHandler_", None)
            if callable(reset_setter):
                reset_setter(lambda active_engine=engine: self._restart_engine(active_engine, "reset"))
            result = engine.startAndReturnError_(None)
            if not bool(_result_value(result)):
                self.last_error = f"Haptic engine start failed: {_result_error(result)}"
                return None
            return engine
        except Exception as exc:
            self.last_error = f"Haptic engine creation failed for {locality}: {exc}"
            return None

    def _restart_engine(self, engine: Any, reason: Any) -> None:
        if "disconnect" in str(reason or "").lower():
            return
        try:
            engine.startAndReturnError_(None)
        except Exception:
            pass

    def _start_pattern(self, engine: Any, steps: List[Mapping[str, float]], channel: str) -> bool:
        core = self.modules["CoreHaptics"]
        events: List[Any] = []
        relative_time = 0.0
        for step in steps:
            duration = _clamp(step.get("duration", 0), 0.0, 10_000.0) / 1000.0
            if channel == "combined":
                intensity = _clamp(float(step.get("strong", 0)) + float(step.get("weak", 0)))
            else:
                intensity = _clamp(step.get(channel, 0))
            if duration > 0 and intensity > 0:
                parameters = [
                    core.CHHapticEventParameter.alloc().initWithParameterID_value_(
                        core.CHHapticEventParameterIDHapticIntensity,
                        intensity,
                    ),
                    core.CHHapticEventParameter.alloc().initWithParameterID_value_(
                        core.CHHapticEventParameterIDHapticSharpness,
                        1.0,
                    ),
                ]
                event = core.CHHapticEvent.alloc().initWithEventType_parameters_relativeTime_duration_(
                    core.CHHapticEventTypeHapticContinuous,
                    parameters,
                    relative_time,
                    duration,
                )
                events.append(event)
            relative_time += duration
        if not events:
            return True
        try:
            engine.startAndReturnError_(None)
            pattern_result = core.CHHapticPattern.alloc().initWithEvents_parameters_error_(
                events,
                [],
                None,
            )
            pattern = _result_value(pattern_result)
            if pattern is None:
                self.last_error = f"CoreHaptics rejected the pattern: {_result_error(pattern_result)}"
                return False
            player_result = engine.createPlayerWithPattern_error_(pattern, None)
            player = _result_value(player_result)
            if player is None:
                self.last_error = f"CoreHaptics could not create a player: {_result_error(player_result)}"
                return False
            start_result = player.startAtTime_error_(0, None)
            if not bool(_result_value(start_result)):
                self.last_error = f"CoreHaptics could not start the player: {_result_error(start_result)}"
                return False
            self.players.append(player)
            return True
        except Exception as exc:
            self.last_error = f"CoreHaptics playback failed: {exc}"
            return False


class PyObjCMacHaptics:
    """Disabled experimental native backend retained for safe cleanup.

    Anki's macOS process executable can be the application launcher rather than
    a Python interpreter. Trying to use it for dependency installation made
    Anki interpret installer arguments as import targets and could destabilize
    startup. Speed Streak now relies on its existing embedded-browser Gamepad
    haptics path and never installs or loads PyObjC automatically.
    """

    def __init__(self, addon_root: Path) -> None:
        self._addon_root = Path(addon_root)
        self._lock = threading.RLock()
        self._modules: Dict[str, Any] = {}
        self._sessions: Dict[int, _ControllerSession] = {}
        self._observers: List[Any] = []
        self._frameworks_loaded = False
        self._notifications_registered = False
        self._install_state = "not-macos"
        self._install_attempted = False
        self._install_output_tail = ""
        self._last_error = ""
        self._main_thread_id = threading.main_thread().ident
        self._dependency_target = self._default_dependency_target()
        self._native_backend_enabled = False
        if not sys.platform.startswith("darwin"):
            return
        self._install_state = "disabled-browser-fallback"

    @property
    def available(self) -> bool:
        if not self._native_backend_enabled:
            return False
        self._load_frameworks_if_main_thread()
        self.refresh_controllers()
        with self._lock:
            return any(session.available for session in self._sessions.values())

    @property
    def transport_ready(self) -> bool:
        return bool(self._frameworks_loaded and self._notifications_registered)

    @property
    def backend_name(self) -> str:
        if not sys.platform.startswith("darwin"):
            return "not-macos"
        if not self._native_backend_enabled:
            return "browser-fallback"
        if self.available:
            return "native-macos-pyobjc"
        if self._install_state == "installing":
            return "browser-fallback-pyobjc-installing"
        if self.transport_ready:
            return "browser-fallback-pyobjc-monitoring"
        return "browser-fallback-pyobjc-unavailable"

    @property
    def diagnostics(self) -> Dict[str, Any]:
        with self._lock:
            controllers = [session.diagnostics() for session in self._sessions.values()]
            haptic_count = sum(1 for session in self._sessions.values() if session.available)
            return {
                "backend": self.backend_name,
                "automaticSelection": True,
                "nativeOutputActive": bool(haptic_count),
                "directPyObjC": bool(self._native_backend_enabled),
                "browserFallbackSelected": bool(
                    sys.platform.startswith("darwin") and not self._native_backend_enabled
                ),
                "dependencyInstallState": self._install_state,
                "dependencyInstallAttempted": self._install_attempted,
                "dependencyTarget": str(self._dependency_target),
                "dependencyTargetExists": self._dependency_target.is_dir(),
                "pyobjcFrameworksLoaded": self._frameworks_loaded,
                "notificationsRegistered": self._notifications_registered,
                "controllerCount": len(controllers),
                "hapticControllerCount": haptic_count,
                "controllers": controllers,
                "lastError": self._last_error,
                "installOutputTail": self._install_output_tail,
            }

    def refresh_controllers(self) -> None:
        if not self._frameworks_loaded:
            return
        controller_class = getattr(self._modules.get("GameController"), "GCController", None)
        if controller_class is None:
            return
        try:
            controllers = list(controller_class.controllers() or [])
        except Exception as exc:
            self._last_error = f"Could not enumerate GameController devices: {exc}"
            return
        live_ids = {self._controller_id(controller) for controller in controllers}
        for controller in controllers:
            self._attach(controller)
        for identifier in list(self._sessions):
            if identifier not in live_ids:
                self._sessions.pop(identifier).shutdown()

    def play_sequence(self, steps: List[Mapping[str, Any]]) -> bool:
        if not self.available:
            return False
        played = False
        for session in list(self._sessions.values()):
            if session.available:
                played = session.play(steps) or played
        return played

    def stop(self) -> None:
        for session in list(self._sessions.values()):
            session.stop()

    def shutdown(self) -> None:
        self.stop()
        foundation = self._modules.get("Foundation")
        if foundation is not None and self._observers:
            try:
                center = foundation.NSNotificationCenter.defaultCenter()
                for observer in self._observers:
                    center.removeObserver_(observer)
            except Exception:
                pass
        controller_class = getattr(self._modules.get("GameController"), "GCController", None)
        if controller_class is not None:
            stopper = getattr(controller_class, "stopWirelessControllerDiscovery", None)
            if callable(stopper):
                try:
                    stopper()
                except Exception:
                    pass
        for session in list(self._sessions.values()):
            session.shutdown()
        self._sessions = {}
        self._observers = []

    def _default_dependency_target(self) -> Path:
        python_tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
        machine = (platform.machine() or "unknown").lower()
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "Anki2"
            / "addons21"
            / ".speed-streak-dependencies"
            / f"pyobjc-{python_tag}-{machine}"
        )

    def _activate_dependency_target(self) -> None:
        target = str(self._dependency_target)
        if target not in sys.path:
            sys.path.insert(0, target)
        importlib.invalidate_caches()

    def _load_frameworks_if_main_thread(self) -> bool:
        if not self._native_backend_enabled:
            return False
        if self._frameworks_loaded:
            return True
        if not sys.platform.startswith("darwin") or threading.get_ident() != self._main_thread_id:
            return False
        try:
            self._activate_dependency_target()
            modules = {
                "objc": importlib.import_module("objc"),
                "Foundation": importlib.import_module("Foundation"),
                "GameController": importlib.import_module("GameController"),
                "CoreHaptics": importlib.import_module("CoreHaptics"),
            }
            self._modules = modules
            self._frameworks_loaded = True
            self._install_state = "ready"
            self._last_error = ""
            self._start_monitoring()
            self.refresh_controllers()
            return True
        except Exception as exc:
            self._last_error = f"PyObjC frameworks are not ready: {type(exc).__name__}: {exc}"
            return False

    def _start_monitoring(self) -> None:
        if self._notifications_registered:
            return
        foundation = self._modules["Foundation"]
        game_controller = self._modules["GameController"]
        try:
            controller_class = game_controller.GCController
            setter = getattr(controller_class, "setShouldMonitorBackgroundEvents_", None)
            if callable(setter):
                try:
                    setter(True)
                except Exception:
                    pass
            center = foundation.NSNotificationCenter.defaultCenter()
            connected = center.addObserverForName_object_queue_usingBlock_(
                game_controller.GCControllerDidConnectNotification,
                None,
                None,
                lambda note: self._attach(note.object()),
            )
            disconnected = center.addObserverForName_object_queue_usingBlock_(
                game_controller.GCControllerDidDisconnectNotification,
                None,
                None,
                lambda note: self._detach(note.object()),
            )
            self._observers = [connected, disconnected]
            self._notifications_registered = True
            starter = getattr(controller_class, "startWirelessControllerDiscoveryWithCompletionHandler_", None)
            if callable(starter):
                try:
                    starter(None)
                except Exception:
                    pass
        except Exception as exc:
            self._last_error = f"GameController monitoring could not start: {type(exc).__name__}: {exc}"

    def _attach(self, controller: Any) -> None:
        if controller is None or not self._frameworks_loaded:
            return
        identifier = self._controller_id(controller)
        if identifier in self._sessions:
            return
        self._sessions[identifier] = _ControllerSession(controller, self._modules)

    def _detach(self, controller: Any) -> None:
        if controller is None:
            return
        session = self._sessions.pop(self._controller_id(controller), None)
        if session is not None:
            session.shutdown()

    def _controller_id(self, controller: Any) -> int:
        objc = self._modules.get("objc")
        resolver = getattr(objc, "pyobjc_id", None) if objc is not None else None
        if callable(resolver):
            try:
                return int(resolver(controller))
            except Exception:
                pass
        return id(controller)
