from __future__ import annotations

import ctypes
import math
import queue
import threading
import tkinter as tk
from dataclasses import dataclass
from ctypes import wintypes

import pystray
from PIL import Image, ImageDraw


APP_NAME = "Xbox Couch Controller"

VK = {
    "BACKSPACE": 0x08,
    "CTRL": 0x11,
    "ALT": 0x12,
    "1": 0x31,
    "C": 0x43,
    "V": 0x56,
    "F3": 0x72,
    "F9": 0x78,
    "F10": 0x79,
    "PERIOD": 0xBE,
}

KEYEVENTF_KEYUP = 0x0002
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


def tap_key(vk: int) -> None:
    user32.keybd_event(vk, 0, 0, 0)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


def combo(*keys: int) -> None:
    for key in keys:
        user32.keybd_event(key, 0, 0, 0)
    for key in reversed(keys):
        user32.keybd_event(key, 0, KEYEVENTF_KEYUP, 0)


def active_window_title() -> str:
    hwnd = user32.GetForegroundWindow()
    length = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def is_anki_active() -> bool:
    return "anki" in active_window_title().lower()


@dataclass(frozen=True)
class RadialAction:
    label: str
    run: callable


class RadialMenu(tk.Toplevel):
    def __init__(self, master: tk.Tk, actions: list[RadialAction], on_click_choose: callable):
        super().__init__(master)
        self.actions = actions
        self.selected = -1
        self.size = 430
        self.button_radius = 150
        self.deadzone = 45
        self.max_cursor_radius = 205

        self.configure(bg="#080b12")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.96)

        half = self.size / 2
        pointer_x = self.winfo_pointerx()
        pointer_y = self.winfo_pointery()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.center_x = int(max(half + 10, min(screen_w - half - 10, pointer_x)))
        self.center_y = int(max(half + 10, min(screen_h - half - 10, pointer_y)))
        self.geometry(f"{self.size}x{self.size}+{int(self.center_x - half)}+{int(self.center_y - half)}")
        user32.SetCursorPos(self.center_x, self.center_y)

        self.canvas = tk.Canvas(
            self,
            width=self.size,
            height=self.size,
            bg="#080b12",
            highlightthickness=0,
            cursor="none",
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", lambda _: on_click_choose())
        self.draw()

    def update_from_mouse(self) -> None:
        mx = self.winfo_pointerx()
        my = self.winfo_pointery()
        dx = mx - self.center_x
        dy = my - self.center_y
        distance = math.hypot(dx, dy)

        if distance > self.max_cursor_radius:
            scale = self.max_cursor_radius / distance
            mx = int(self.center_x + dx * scale)
            my = int(self.center_y + dy * scale)
            user32.SetCursorPos(mx, my)
            dx = mx - self.center_x
            dy = my - self.center_y
            distance = self.max_cursor_radius

        if distance < self.deadzone:
            new_selected = -1
        else:
            angle = math.degrees(math.atan2(dy, dx))
            step = 360 / len(self.actions)
            relative = (angle - -90 + step / 2) % 360
            new_selected = int(relative / step) % len(self.actions)

        if new_selected != self.selected:
            self.selected = new_selected
            self.draw()

    def choose(self) -> None:
        if self.selected >= 0:
            self.actions[self.selected].run()
        self.destroy()

    def draw(self) -> None:
        c = self.canvas
        c.delete("all")
        cx = cy = self.size / 2
        c.create_oval(18, 18, self.size - 18, self.size - 18, fill="#0b1020", outline="#1e2a44", width=2)
        c.create_oval(72, 72, self.size - 72, self.size - 72, outline="#26395e", width=1)

        step = 360 / len(self.actions)
        for i, action in enumerate(self.actions):
            angle = math.radians(-90 + i * step)
            x = cx + math.cos(angle) * self.button_radius
            y = cy + math.sin(angle) * self.button_radius
            active = i == self.selected
            fill = "#0f3142" if active else "#101827"
            outline = "#20e3ff" if active else "#26395e"
            text = "#8ff4ff" if active else "#dce8ff"
            c.create_oval(x - 61, y - 34, x + 61, y + 34, fill=fill, outline=outline, width=2)
            c.create_text(x, y, text=action.label, fill=text, font=("Segoe UI", 12, "bold"))

        center_label = "Select" if self.selected < 0 else self.actions[self.selected].label
        c.create_oval(cx - 72, cy - 72, cx + 72, cy + 72, fill="#111a2c", outline="#314c80", width=2)
        c.create_text(cx, cy - 8, text=center_label, fill="#9fefff", font=("Segoe UI", 16, "bold"))
        c.create_text(cx, cy + 24, text="Move mouse to aim   click to choose", fill="#7f8da8", font=("Segoe UI", 9))


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("760x520")
        self.root.configure(bg="#080b12")
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.events: queue.Queue[tuple[str, object | None]] = queue.Queue()
        self.running = True
        self.paused = False
        self.radial: RadialMenu | None = None
        self.hotkey_thread_id: int | None = None
        self.status_var = tk.StringVar(value="JoyToKey companion active")
        self.mode_var = tk.StringVar(value="F9 opens radial menu. F10 sends Anki-aware Backspace/1.")

        self.build_ui()
        self.tray = self.build_tray()
        threading.Thread(target=self.tray.run, daemon=True).start()
        threading.Thread(target=self.hotkey_loop, daemon=True).start()
        self.root.after(16, self.drain_events)

    def build_ui(self) -> None:
        frame = tk.Frame(self.root, bg="#080b12")
        frame.pack(fill="both", expand=True, padx=28, pady=24)
        tk.Label(frame, text=APP_NAME, bg="#080b12", fg="#eaf2ff", font=("Segoe UI", 24, "bold")).pack(anchor="w")
        tk.Label(frame, text="Night mode function-key layer for JoyToKey-driven couch control.", bg="#080b12", fg="#8795ad", font=("Segoe UI", 11)).pack(anchor="w", pady=(4, 18))

        status = tk.Frame(frame, bg="#0e1524", highlightbackground="#1f2b45", highlightthickness=1)
        status.pack(fill="x", pady=(0, 18))
        tk.Label(status, textvariable=self.status_var, bg="#0e1524", fg="#8ff4ff", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=18, pady=(16, 2))
        tk.Label(status, textvariable=self.mode_var, bg="#0e1524", fg="#dce8ff", font=("Segoe UI", 10)).pack(anchor="w", padx=18, pady=(0, 16))

        grid = tk.Frame(frame, bg="#080b12")
        grid.pack(fill="both", expand=True)
        cards = [
            ("JoyToKey", "JoyToKey keeps owning mouse movement, clicks, and non-function key output."),
            ("F9", "Consumed by this app. Opens or closes the radial menu."),
            ("F10", "Consumed by this app. Sends 1 when Anki is active; otherwise sends Backspace."),
            ("F3", "Not consumed by this app. JoyToKey's F3 mappings pass through unchanged."),
            ("Radial", "While open, the cursor is hidden and constrained to the radial menu."),
            ("Tray", "Use the tray icon to show, pause, resume, or quit."),
        ]
        for idx, (title, body) in enumerate(cards):
            card = tk.Frame(grid, bg="#101827", highlightbackground="#243450", highlightthickness=1)
            card.grid(row=idx // 2, column=idx % 2, padx=8, pady=8, sticky="nsew")
            tk.Label(card, text=title, bg="#101827", fg="#f4f7ff", font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=16, pady=(14, 4))
            tk.Label(card, text=body, bg="#101827", fg="#9ba9c0", font=("Segoe UI", 10), wraplength=300, justify="left").pack(anchor="w", padx=16, pady=(0, 16))
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

    def build_tray(self) -> pystray.Icon:
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((8, 8, 56, 56), radius=14, fill="#0b1020", outline="#20e3ff", width=3)
        draw.ellipse((22, 22, 42, 42), fill="#20e3ff")
        menu = pystray.Menu(
            pystray.MenuItem("Show", lambda *_: self.events.put(("show", None))),
            pystray.MenuItem("Pause / Resume", lambda *_: self.events.put(("toggle_pause", None))),
            pystray.MenuItem("Quit", lambda *_: self.events.put(("quit", None))),
        )
        return pystray.Icon("xbox-couch-controller", image, APP_NAME, menu)

    def hotkey_loop(self) -> None:
        self.hotkey_thread_id = kernel32.GetCurrentThreadId()
        user32.RegisterHotKey(None, 1, 0, VK["F9"])
        user32.RegisterHotKey(None, 2, 0, VK["F10"])
        user32.RegisterHotKey(None, 3, MOD_CONTROL | MOD_ALT, VK["F9"])
        msg = wintypes.MSG()
        while self.running and user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_HOTKEY:
                if msg.wParam == 1:
                    self.events.put(("toggle_radial", None))
                elif msg.wParam == 2:
                    self.events.put(("anki_or_backspace", None))
                elif msg.wParam == 3:
                    self.events.put(("close_radial", None))
        user32.UnregisterHotKey(None, 1)
        user32.UnregisterHotKey(None, 2)
        user32.UnregisterHotKey(None, 3)

    def radial_actions(self) -> list[RadialAction]:
        return [
            RadialAction("Paste", lambda: combo(VK["CTRL"], VK["V"])),
            RadialAction("Copy", lambda: combo(VK["CTRL"], VK["C"])),
            RadialAction("Backspace", lambda: tap_key(VK["BACKSPACE"])),
            RadialAction("Period", lambda: tap_key(VK["PERIOD"])),
            RadialAction("Ctrl+F3", lambda: combo(VK["CTRL"], VK["F3"])),
        ]

    def drain_events(self) -> None:
        while not self.events.empty():
            event, _ = self.events.get()
            if event == "show":
                self.show_window()
            elif event == "toggle_pause":
                self.paused = not self.paused
                self.mode_var.set("Paused" if self.paused else "F9 opens radial menu. F10 sends Anki-aware Backspace/1.")
            elif event == "quit":
                self.quit()
            elif event == "toggle_radial" and not self.paused:
                if self.radial:
                    self.close_radial()
                else:
                    self.radial = RadialMenu(self.root, self.radial_actions(), lambda: self.events.put(("choose_radial", None)))
            elif event == "anki_or_backspace" and not self.paused:
                if self.radial:
                    self.choose_radial()
                elif is_anki_active():
                    tap_key(VK["1"])
                else:
                    tap_key(VK["BACKSPACE"])
            elif event == "choose_radial":
                self.choose_radial()
            elif event == "close_radial":
                self.close_radial()

        if self.radial:
            self.radial.update_from_mouse()
        if self.running:
            self.root.after(16, self.drain_events)

    def show_window(self) -> None:
        self.root.deiconify()
        self.root.lift()

    def hide_window(self) -> None:
        self.root.withdraw()

    def close_radial(self) -> None:
        if self.radial:
            user32.SetCursorPos(self.radial.center_x, self.radial.center_y)
            self.radial.destroy()
            self.radial = None

    def choose_radial(self) -> None:
        if self.radial:
            radial = self.radial
            self.radial = None
            radial.choose()

    def quit(self) -> None:
        self.running = False
        self.close_radial()
        if self.hotkey_thread_id:
            user32.PostThreadMessageW(self.hotkey_thread_id, WM_QUIT, 0, 0)
        self.tray.stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
