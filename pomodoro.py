import tkinter as tk
from tkinter import ttk
import winsound
import math

WORK_MIN = 25
SHORT_BREAK_MIN = 5
LONG_BREAK_MIN = 15
POMODOROS_BEFORE_LONG = 4

WORK_COLOR = "#e74c3c"
SHORT_BREAK_COLOR = "#2ecc71"
LONG_BREAK_COLOR = "#3498db"
BG_COLOR = "#2c2c2c"
TEXT_COLOR = "#ffffff"
BTN_BG = "#3c3c3c"
BTN_ACTIVE = "#505050"


class PomodoroApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("番茄钟")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)

        window_width = 360
        window_height = 440
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.remaining = WORK_MIN * 60
        self.phase = "work"
        self.pomodoro_count = 0
        self.running = False
        self.timer_id = None
        self.topmost_var = tk.BooleanVar(value=True)

        self._build_ui()
        self._sync_topmost()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _build_ui(self):
        # Title
        title = tk.Label(
            self.root,
            text="🍅 番茄钟",
            font=("Microsoft YaHei", 18, "bold"),
            bg=BG_COLOR,
            fg=TEXT_COLOR,
        )
        title.pack(pady=(20, 0))

        # Phase label
        self.phase_label = tk.Label(
            self.root,
            text="准备工作",
            font=("Microsoft YaHei", 13),
            bg=BG_COLOR,
            fg=WORK_COLOR,
        )
        self.phase_label.pack(pady=(8, 0))

        # Canvas timer
        self.canvas_size = 220
        self.canvas = tk.Canvas(
            self.root,
            width=self.canvas_size,
            height=self.canvas_size,
            bg=BG_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack(pady=(10, 0))

        # Progress ring
        self._draw_ring(1.0)

        # Time text on canvas
        self.time_text = self.canvas.create_text(
            self.canvas_size // 2,
            self.canvas_size // 2,
            text="25:00",
            font=("Consolas", 42, "bold"),
            fill=TEXT_COLOR,
        )

        # Button frame
        btn_frame = tk.Frame(self.root, bg=BG_COLOR)
        btn_frame.pack(pady=(12, 0))

        self.start_btn = tk.Button(
            btn_frame,
            text="开始",
            font=("Microsoft YaHei", 11),
            width=8,
            bg=BTN_BG,
            fg=TEXT_COLOR,
            activebackground=BTN_ACTIVE,
            activeforeground=TEXT_COLOR,
            relief="flat",
            command=self.start,
        )
        self.start_btn.pack(side="left", padx=4)

        self.pause_btn = tk.Button(
            btn_frame,
            text="暂停",
            font=("Microsoft YaHei", 11),
            width=8,
            bg=BTN_BG,
            fg=TEXT_COLOR,
            activebackground=BTN_ACTIVE,
            activeforeground=TEXT_COLOR,
            relief="flat",
            command=self.pause,
        )
        self.pause_btn.pack(side="left", padx=4)

        self.reset_btn = tk.Button(
            btn_frame,
            text="重置",
            font=("Microsoft YaHei", 11),
            width=8,
            bg=BTN_BG,
            fg=TEXT_COLOR,
            activebackground=BTN_ACTIVE,
            activeforeground=TEXT_COLOR,
            relief="flat",
            command=self.reset,
        )
        self.reset_btn.pack(side="left", padx=4)

        # Pomodoro counter
        dots_frame = tk.Frame(self.root, bg=BG_COLOR)
        dots_frame.pack(pady=(16, 0))

        self.tomato_dots = []
        for i in range(POMODOROS_BEFORE_LONG):
            dot = tk.Label(
                dots_frame,
                text="🍅",
                font=("", 14),
                bg=BG_COLOR,
                fg="#555555",
            )
            dot.pack(side="left", padx=3)
            self.tomato_dots.append(dot)

        self.count_label = tk.Label(
            self.root,
            text="已完成: 0 个番茄",
            font=("Microsoft YaHei", 10),
            bg=BG_COLOR,
            fg="#aaaaaa",
        )
        self.count_label.pack(pady=(6, 0))

        # Topmost toggle
        topmost_cb = tk.Checkbutton(
            self.root,
            text="窗口置顶",
            variable=self.topmost_var,
            command=self._sync_topmost,
            font=("Microsoft YaHei", 9),
            bg=BG_COLOR,
            fg="#aaaaaa",
            selectcolor=BG_COLOR,
            activebackground=BG_COLOR,
            activeforeground="#aaaaaa",
        )
        topmost_cb.pack(pady=(8, 0))

    def _draw_ring(self, fraction):
        self.canvas.delete("ring")
        cx = self.canvas_size // 2
        cy = self.canvas_size // 2
        r = 90
        width = 8

        color = self._phase_color()

        # Background ring
        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline="#444444",
            width=width,
            tags="ring",
        )

        if fraction <= 0:
            return

        # Progress arc
        angle = fraction * 360
        # tkinter arc goes counter-clockwise from 3-o'clock
        start = 90
        extent = -angle
        self.canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=start,
            extent=extent,
            outline=color,
            width=width,
            style="arc",
            tags="ring",
        )

    def _phase_color(self):
        if self.phase == "work":
            return WORK_COLOR
        elif self.phase == "short_break":
            return SHORT_BREAK_COLOR
        else:
            return LONG_BREAK_COLOR

    def _phase_text(self):
        if self.phase == "work":
            return "⏰ 工作中"
        elif self.phase == "short_break":
            return "☕ 短休息"
        else:
            return "🌴 长休息"

    def _total_seconds(self):
        if self.phase == "work":
            return WORK_MIN * 60
        elif self.phase == "short_break":
            return SHORT_BREAK_MIN * 60
        else:
            return LONG_BREAK_MIN * 60

    def _format_time(self, seconds):
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"

    def _sync_topmost(self):
        self.root.attributes("-topmost", self.topmost_var.get())

    def start(self):
        if self.running:
            return
        self.running = True
        self._tick()

    def pause(self):
        self.running = False
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    def reset(self):
        self.pause()
        self.remaining = self._total_seconds()
        self._update_display()

    def _tick(self):
        if not self.running:
            return

        if self.remaining > 0:
            self.remaining -= 1
            self._update_display()
            self.timer_id = self.root.after(1000, self._tick)
        else:
            self.running = False
            self._play_notification()
            self._switch_phase()

    def _update_display(self):
        total = self._total_seconds()
        fraction = self.remaining / total if total > 0 else 0
        self._draw_ring(fraction)
        self.canvas.itemconfig(self.time_text, text=self._format_time(self.remaining))

    def _switch_phase(self):
        if self.phase == "work":
            self.pomodoro_count += 1
            self._update_tomato_dots()
            if self.pomodoro_count % POMODOROS_BEFORE_LONG == 0:
                self.phase = "long_break"
            else:
                self.phase = "short_break"
        else:
            self.phase = "work"

        self.remaining = self._total_seconds()
        color = self._phase_color()
        self.phase_label.config(text=self._phase_text(), fg=color)
        self._update_display()

    def _update_tomato_dots(self):
        completed_in_cycle = self.pomodoro_count % POMODOROS_BEFORE_LONG
        if completed_in_cycle == 0:
            completed_in_cycle = POMODOROS_BEFORE_LONG
        for i in range(POMODOROS_BEFORE_LONG):
            if i < completed_in_cycle:
                self.tomato_dots[i].config(fg=TEXT_COLOR)
            else:
                self.tomato_dots[i].config(fg="#555555")
        self.count_label.config(text=f"已完成: {self.pomodoro_count} 个番茄")

    def _play_notification(self):
        self._beep_sequence(3)

    def _beep_sequence(self, count):
        if count <= 0:
            return
        winsound.MessageBeep()
        self.root.after(400, lambda: self._beep_sequence(count - 1))

    def _on_close(self):
        self.pause()
        self.root.destroy()


if __name__ == "__main__":
    PomodoroApp()
