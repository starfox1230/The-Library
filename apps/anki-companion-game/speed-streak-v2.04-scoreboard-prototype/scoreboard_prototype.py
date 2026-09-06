from __future__ import annotations

import tkinter as tk
from copy import deepcopy
from dataclasses import dataclass
from tkinter import ttk


@dataclass
class Run:
    streak: int
    when: str
    pause_count: int = 0
    resumed: bool = False


INITIAL_RUNS = [
    Run(61, "Mon 8:12 PM"),
    Run(168, "Tue 7:41 AM", pause_count=2),
    Run(104, "Tue 6:20 PM"),
    Run(72, "Wed 7:08 AM", resumed=True),
    Run(131, "Wed 8:34 PM"),
    Run(94, "Thu 7:16 AM"),
    Run(118, "Thu 6:53 PM", pause_count=1),
    Run(79, "Today 7:22 AM"),
]


class ScoreboardPrototype:
    WIDTH = 340
    HEIGHT = 700

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Speed Streak 2.04 — Scoreboard Layout Lab")
        self.root.geometry("790x758")
        self.root.minsize(735, 738)
        self.root.configure(bg="#12151d")

        self.runs = deepcopy(INITIAL_RUNS)
        self.current_streak = 86
        self.paused = False
        self.resumed = False
        self.popup_open = True
        self.new_best = False
        self.layout_mode = tk.StringVar(value="compact")
        self.comparison_set = tk.StringVar(value="recent")
        self.row_order = tk.StringVar(value="ranked")
        self.status_text = tk.StringVar(value="Click +1 or +10 to watch LIVE climb the comparison set.")

        self._build_shell()
        self.render()

    def _build_shell(self) -> None:
        shell = tk.Frame(self.root, bg="#12151d")
        shell.pack(fill="both", expand=True, padx=18, pady=18)

        controls = tk.Frame(shell, width=360, bg="#191e29", highlightthickness=1, highlightbackground="#30384a")
        controls.pack(side="left", fill="y", padx=(0, 18))
        controls.pack_propagate(False)

        tk.Label(
            controls,
            text="2.04 SCOREBOARD LAB",
            bg="#191e29",
            fg="#eef3ff",
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor="w", padx=18, pady=(18, 4))
        tk.Label(
            controls,
            text="A separate prototype. It does not import or modify the add-on.",
            bg="#191e29",
            fg="#94a3bf",
            justify="left",
            wraplength=320,
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=18, pady=(0, 16))

        self._section(controls, "LAYOUT")
        self._radio(controls, "Compact target + popover  · recommended", "compact", self.layout_mode)
        self._radio(controls, "Always-visible ladder", "ladder", self.layout_mode)
        self._radio(controls, "Best only", "best", self.layout_mode)

        self._section(controls, "COMPARISON SET")
        self._radio(controls, "Five most recent completed runs", "recent", self.comparison_set)
        self._radio(controls, "Five best completed runs", "best", self.comparison_set)

        self._section(controls, "ROW ORDER")
        self._radio(controls, "Ranked — climb visually", "ranked", self.row_order)
        self._radio(controls, "Chronological — newest first", "chronological", self.row_order)

        self._section(controls, "SIMULATE")
        action_row = tk.Frame(controls, bg="#191e29")
        action_row.pack(fill="x", padx=18, pady=(2, 7))
        self._button(action_row, "+1", lambda: self.add_cards(1)).pack(side="left", expand=True, fill="x", padx=(0, 4))
        self._button(action_row, "+10", lambda: self.add_cards(10)).pack(side="left", expand=True, fill="x", padx=4)
        self._button(action_row, "End run", self.end_run).pack(side="left", expand=True, fill="x", padx=(4, 0))

        state_row = tk.Frame(controls, bg="#191e29")
        state_row.pack(fill="x", padx=18, pady=(0, 7))
        self._button(state_row, "Pause / resume", self.toggle_pause).pack(side="left", expand=True, fill="x", padx=(0, 4))
        self._button(state_row, "Restart / restore", self.toggle_restored).pack(side="left", expand=True, fill="x", padx=(4, 0))

        manage_row = tk.Frame(controls, bg="#191e29")
        manage_row.pack(fill="x", padx=18, pady=(0, 10))
        self._button(manage_row, "Delete best", self.delete_best).pack(side="left", expand=True, fill="x", padx=(0, 4))
        self._button(manage_row, "Reset history", self.reset_history).pack(side="left", expand=True, fill="x", padx=(4, 0))

        tk.Label(
            controls,
            textvariable=self.status_text,
            bg="#191e29",
            fg="#b8c4da",
            justify="left",
            wraplength=320,
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=18, pady=(4, 14))

        preview_frame = tk.Frame(shell, bg="#0b0d12", highlightthickness=1, highlightbackground="#3a4356")
        preview_frame.pack(side="left", fill="none")
        self.canvas = tk.Canvas(
            preview_frame,
            width=self.WIDTH,
            height=self.HEIGHT,
            bg="#080b14",
            highlightthickness=0,
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        for variable in (self.layout_mode, self.comparison_set, self.row_order):
            variable.trace_add("write", lambda *_: self.render())

    @staticmethod
    def _section(parent: tk.Widget, text: str) -> None:
        tk.Label(
            parent,
            text=text,
            bg="#191e29",
            fg="#7586a8",
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", padx=18, pady=(9, 3))

    def _radio(self, parent: tk.Widget, text: str, value: str, variable: tk.StringVar) -> None:
        tk.Radiobutton(
            parent,
            text=text,
            value=value,
            variable=variable,
            command=self.render,
            bg="#191e29",
            fg="#dfe8f8",
            activebackground="#191e29",
            activeforeground="#ffffff",
            selectcolor="#25334a",
            anchor="w",
            font=("Segoe UI", 9),
        ).pack(fill="x", padx=14, pady=1)

    @staticmethod
    def _button(parent: tk.Widget, text: str, command) -> ttk.Button:
        return ttk.Button(parent, text=text, command=command)

    def comparison_runs(self) -> list[Run]:
        if self.comparison_set.get() == "best":
            selected = sorted(self.runs, key=lambda run: run.streak, reverse=True)[:5]
        else:
            selected = self.runs[-5:]
        if self.row_order.get() == "ranked":
            selected = sorted(selected, key=lambda run: run.streak, reverse=True)
        else:
            selected = list(reversed(selected))
        return selected

    def live_rank(self) -> int:
        return 1 + sum(run.streak > self.current_streak for run in self.comparison_runs())

    def historical_best(self) -> int:
        return max((run.streak for run in self.runs), default=0)

    def add_cards(self, amount: int) -> None:
        old_best = self.historical_best()
        self.current_streak += amount
        if self.current_streak > old_best:
            self.new_best = True
            self.status_text.set("The live run crossed the completed-run record. Celebration appears once at the crossing.")
        else:
            self.status_text.set(f"LIVE is now #{self.live_rank()} versus the selected five completed runs.")
        self.render()

    def end_run(self) -> None:
        if self.current_streak <= 0:
            self.status_text.set("A zero-card attempt is not stored as a completed run.")
            return
        old_best = self.historical_best()
        self.runs.append(
            Run(
                self.current_streak,
                "Just now",
                pause_count=1 if self.paused else 0,
                resumed=self.resumed,
            )
        )
        beat_best = self.current_streak > old_best
        completed = self.current_streak
        self.current_streak = 0
        self.paused = False
        self.resumed = False
        self.new_best = beat_best
        self.status_text.set(
            f"Stored a {completed}-card run. "
            + ("It became the completed-run record." if beat_best else "The next run starts at zero.")
        )
        self.render()

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        self.status_text.set(
            "Manual pauses are recorded as metadata but do not invalidate or split the run."
        )
        self.render()

    def toggle_restored(self) -> None:
        self.resumed = not self.resumed
        self.status_text.set(
            "Leaving Review or restoring after restart keeps the same run ID; the history can note that it was resumed."
        )
        self.render()

    def delete_best(self) -> None:
        if not self.runs:
            return
        best_index = max(range(len(self.runs)), key=lambda index: self.runs[index].streak)
        deleted = self.runs.pop(best_index)
        self.new_best = False
        self.status_text.set(f"Deleted the {deleted.streak}-card run. BEST was recalculated from remaining runs.")
        self.render()

    def reset_history(self) -> None:
        self.runs.clear()
        self.new_best = False
        self.status_text.set("Completed-run history was cleared. The active run remains active.")
        self.render()

    def _on_canvas_click(self, event: tk.Event) -> None:
        if self.layout_mode.get() == "compact" and 244 <= event.y <= 282:
            self.popup_open = not self.popup_open
            self.render()

    def render(self) -> None:
        c = self.canvas
        c.delete("all")
        self._draw_window_chrome()
        self._draw_timer_and_economy()

        mode = self.layout_mode.get()
        if mode == "compact":
            self._draw_compact_target()
            self._draw_stage(center_y=440, radius=73)
            if self.popup_open:
                self._draw_ladder(22, 293, 318, overlay=True)
        elif mode == "ladder":
            self._draw_ladder(18, 247, 322, overlay=False)
            self._draw_stage(center_y=500, radius=58)
        else:
            self._draw_best_only()
            self._draw_stage(center_y=422, radius=78)

        self._draw_bottom()

    def _draw_window_chrome(self) -> None:
        c = self.canvas
        c.create_rectangle(0, 0, self.WIDTH, self.HEIGHT, fill="#080b14", outline="#42506a")
        c.create_rectangle(1, 1, self.WIDTH - 1, 28, fill="#1b202b", outline="")
        c.create_oval(10, 10, 19, 19, fill="#ff6b72", outline="")
        c.create_oval(25, 10, 34, 19, fill="#f0be56", outline="")
        c.create_oval(40, 10, 49, 19, fill="#61d889", outline="")
        c.create_text(170, 15, text="Speed Streak", fill="#dfe8f8", font=("Segoe UI", 9, "bold"))
        for x in range(16, 332, 28):
            c.create_line(x, 40, x, 686, fill="#101828")
        for y in range(44, 686, 28):
            c.create_line(8, y, 332, y, fill="#101828")
        c.create_text(25, 49, text="●", fill="#65f0c2", font=("Segoe UI", 13))
        c.create_text(313, 50, text="⚙", fill="#aab9d4", font=("Segoe UI Symbol", 14))

    def _draw_timer_and_economy(self) -> None:
        c = self.canvas
        c.create_oval(106, 48, 234, 176, fill="#0b1220", outline="#15243b", width=10)
        c.create_arc(106, 48, 234, 176, start=90, extent=-265, style="arc", outline="#e9b83e", width=9)
        c.create_text(170, 101, text="QUESTION", fill="#8fa1c4", font=("Segoe UI", 8, "bold"))
        c.create_text(170, 127, text="8.4", fill="#f1f5ff", font=("Segoe UI", 25, "bold"))
        c.create_text(170, 193, text="⚡  ⚡  ⚡  ◇  ◇", fill="#65f0c2", font=("Segoe UI Symbol", 13, "bold"))
        c.create_rectangle(118, 210, 222, 214, fill="#273144", outline="")
        c.create_rectangle(118, 210, 183, 214, fill="#65f0c2", outline="")
        c.create_text(170, 228, text="NEXT BOOST 6 / 10", fill="#8092b4", font=("Segoe UI", 7, "bold"))

    def _target_text(self) -> tuple[str, str]:
        best = self.historical_best()
        rank = self.live_rank()
        if self.current_streak > best:
            return f"BEST {best}", "LIVE · NEW BEST PACE"
        distance = max(0, best - self.current_streak)
        return f"BEST {best}", f"LIVE #{rank} vs 5  ·  {distance} TO GO"

    def _draw_compact_target(self) -> None:
        left, right = self._target_text()
        self.canvas.create_rectangle(15, 246, 325, 280, fill="#111a29", outline="#314564", width=1)
        self.canvas.create_text(27, 263, text=left, anchor="w", fill="#f0cf72", font=("Segoe UI", 9, "bold"))
        self.canvas.create_text(313, 263, text=right, anchor="e", fill="#d8e4f7", font=("Segoe UI", 8, "bold"))
        self.canvas.create_text(318, 263, text="▴" if self.popup_open else "▾", fill="#8da4c8", font=("Segoe UI", 8))

    def _draw_best_only(self) -> None:
        best = self.historical_best()
        self.canvas.create_rectangle(121, 246, 219, 276, fill="#111a29", outline="#5b4f2c")
        self.canvas.create_text(170, 261, text=f"★  BEST {best}", fill="#f0cf72", font=("Segoe UI", 9, "bold"))

    def _draw_ladder(self, x1: int, y1: int, x2: int, *, overlay: bool) -> None:
        rows = [(run.streak, run.when, False, run) for run in self.comparison_runs()]
        rows.append((self.current_streak, "LIVE", True, None))
        if self.row_order.get() == "ranked":
            rows.sort(key=lambda row: row[0], reverse=True)
        else:
            rows = [row for row in rows if not row[2]] + [row for row in rows if row[2]]

        row_height = 26
        header_height = 31
        y2 = y1 + header_height + len(rows) * row_height + 8
        fill = "#0d1524" if overlay else "#101827"
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="#314564", width=1)
        source = "RECENT 5" if self.comparison_set.get() == "recent" else "BEST 5"
        self.canvas.create_text(x1 + 12, y1 + 16, text=f"RUNS TO BEAT  ·  {source}", anchor="w", fill="#8ea2c5", font=("Segoe UI", 8, "bold"))

        for index, (streak, when, live, run) in enumerate(rows, start=1):
            top = y1 + header_height + (index - 1) * row_height
            if live:
                self.canvas.create_rectangle(x1 + 6, top + 2, x2 - 6, top + row_height - 2, fill="#1f3a3a", outline="")
            self.canvas.create_text(x1 + 13, top + 13, text=str(index), anchor="w", fill="#7386a9", font=("Segoe UI", 8, "bold"))
            self.canvas.create_text(x1 + 39, top + 13, text=when, anchor="w", fill="#dbe5f5" if live else "#aebbd2", font=("Segoe UI", 8, "bold" if live else "normal"))
            metadata = ""
            if run and run.resumed:
                metadata = "↻"
            elif run and run.pause_count:
                metadata = "Ⅱ"
            self.canvas.create_text(x2 - 55, top + 13, text=metadata, fill="#7589ab", font=("Segoe UI Symbol", 8))
            self.canvas.create_text(x2 - 13, top + 13, text=str(streak), anchor="e", fill="#65f0c2" if live else "#eef3ff", font=("Segoe UI", 9, "bold"))

    def _draw_stage(self, center_y: int, radius: int) -> None:
        c = self.canvas
        if self.new_best:
            c.create_text(170, center_y - radius - 32, text="✦  NEW BEST  ✦", fill="#f0cf72", font=("Segoe UI Symbol", 10, "bold"))
            for x, y in ((75, center_y - 55), (260, center_y - 65), (90, center_y + 55), (248, center_y + 44)):
                c.create_text(x, y, text="✦", fill="#f0cf72", font=("Segoe UI Symbol", 12))
        c.create_oval(170 - radius - 28, center_y - radius - 28, 170 + radius + 28, center_y + radius + 28, outline="#1c3550", width=2)
        c.create_oval(170 - radius - 12, center_y - radius - 12, 170 + radius + 12, center_y + radius + 12, outline="#234664", width=2)
        c.create_oval(170 - radius, center_y - radius, 170 + radius, center_y + radius, fill="#102437", outline="#5fd8ca", width=3)
        c.create_oval(170 - radius + 12, center_y - radius + 12, 170 + radius - 12, center_y + radius - 12, fill="#19364a", outline="#6debd6")
        c.create_text(170, center_y, text=str(self.current_streak), fill="#f4f8ff", font=("Segoe UI", max(20, int(radius * 0.48)), "bold"))
        state_bits = []
        if self.paused:
            state_bits.append("PAUSED")
        if self.resumed:
            state_bits.append("RESTORED")
        if state_bits:
            c.create_text(170, center_y + radius + 48, text=" · ".join(state_bits), fill="#96a8c6", font=("Segoe UI", 7, "bold"))

    def _draw_bottom(self) -> None:
        c = self.canvas
        c.create_text(170, 626, text="Question 8.4s", fill="#8ea0c2", font=("Segoe UI", 8, "bold"))
        c.create_line(14, 644, 326, 644, fill="#273348")
        c.create_text(29, 668, text="◉", fill="#7fb0ff", font=("Segoe UI Symbol", 13))
        c.create_text(170, 668, text="Speed Streak", fill="#647899", font=("Segoe UI", 8, "bold"))
        c.create_text(310, 668, text="🎮", fill="#9db0cd", font=("Segoe UI Emoji", 12))


def main() -> None:
    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", 1.0)
    except tk.TclError:
        pass
    ScoreboardPrototype(root)
    root.mainloop()


if __name__ == "__main__":
    main()
