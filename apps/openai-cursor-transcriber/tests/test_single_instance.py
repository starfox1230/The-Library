from __future__ import annotations

import unittest

from cursor_transcriber.single_instance import ERROR_ALREADY_EXISTS, acquire_single_instance


class _FakeKernel32:
    def __init__(self, *, handle: int = 101, last_error_after_create: int = 0) -> None:
        self.handle = handle
        self.last_error_after_create = last_error_after_create
        self.closed_handles: list[int] = []
        self.created_name: str | None = None
        self._last_error_state: dict[str, int] | None = None

    def bind_last_error_state(self, state: dict[str, int]) -> None:
        self._last_error_state = state

    def CreateMutexW(self, _security_attributes, _initial_owner, name: str) -> int:
        self.created_name = name
        if self._last_error_state is not None:
            self._last_error_state["value"] = self.last_error_after_create
        return self.handle

    def CloseHandle(self, handle: int) -> int:
        self.closed_handles.append(handle)
        return 1


class SingleInstanceTests(unittest.TestCase):
    def test_acquire_single_instance_returns_lock_for_first_launch(self) -> None:
        last_error = {"value": 0}
        kernel32 = _FakeKernel32()
        kernel32.bind_last_error_state(last_error)

        lock = acquire_single_instance(
            "Local\\CursorTranscriberTest",
            kernel32=kernel32,
            get_last_error=lambda: last_error["value"],
            set_last_error=lambda value: last_error.__setitem__("value", value),
        )

        self.assertIsNotNone(lock)
        self.assertEqual(kernel32.created_name, "Local\\CursorTranscriberTest")
        self.assertEqual(kernel32.closed_handles, [])

        lock.close()
        self.assertEqual(kernel32.closed_handles, [101])

    def test_acquire_single_instance_returns_none_when_existing_instance_is_running(self) -> None:
        last_error = {"value": 0}
        kernel32 = _FakeKernel32(last_error_after_create=ERROR_ALREADY_EXISTS)
        kernel32.bind_last_error_state(last_error)

        lock = acquire_single_instance(
            "Local\\CursorTranscriberTest",
            kernel32=kernel32,
            get_last_error=lambda: last_error["value"],
            set_last_error=lambda value: last_error.__setitem__("value", value),
        )

        self.assertIsNone(lock)
        self.assertEqual(kernel32.closed_handles, [101])


if __name__ == "__main__":
    unittest.main()
