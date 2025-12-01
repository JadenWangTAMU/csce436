import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import csv
import os

categories = [
    "Animals", "Architecture", "Chemistry", "Energy", "Environment",
    "Health", "Music", "Physics", "Space", "Technology"
]


def apply_style(root: tk.Tk):
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("TButton", padding=(12, 8), font=("Segoe UI", 10))
    style.configure("TLabel", font=("Segoe UI", 10))

    style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"))
    style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))

    # Optional: make ttk Frames match a nicer background
    # bg = style.lookup("TFrame", "background")
    # root.configure(bg=bg)


# ----------------------------------------------------------
# ONE-FACT-AT-A-TIME PAGER (shared base)
# ----------------------------------------------------------
class FactPagerPage(tk.Frame):
    def __init__(
        self,
        master,
        category,
        go_home_callback,
        other_mode_callback,
        other_mode_label="Auto Scroll",
        auto_advance=False,
        auto_ms=2500,
    ):
        super().__init__(master)
        self.category = category
        self.go_home_callback = go_home_callback
        self.other_mode_callback = other_mode_callback
        self.other_mode_label = other_mode_label

        self.entries = self.load_entries()
        self.idx = 0

        self.auto_advance = auto_advance
        self.auto_ms = auto_ms
        self._auto_job = None

        # swipe state
        self._swipe_start_x = None
        self._swipe_threshold = 80  # pixels

        # Layout: title, canvas, nav row
        ttk.Label(self, text=category, style="Title.TLabel").pack(pady=(12, 8))

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=16, pady=8)

        nav = ttk.Frame(self)
        nav.pack(fill="x", padx=16, pady=(8, 12))

        ttk.Button(nav, text=" Prev", command=self.prev_fact).pack(side="left")
        ttk.Button(nav, text="Back", command=self.go_home_callback).pack(side="left", padx=8)
        ttk.Button(nav, text=self.other_mode_label, command=self.other_mode_callback).pack(side="left", padx=8)
        ttk.Button(nav, text="Next ", command=self.next_fact).pack(side="right")

        # Create one "card" (rectangle + text). Reposition on resize.
        self.card_rect = self.canvas.create_rectangle(0, 0, 0, 0, outline="#222", width=2)

        self.card_text = self.canvas.create_text(
            0, 0,
            text="",
            font=("Segoe UI", 14),
            anchor="center",
            width=300,
        )

        # Animation state
        self._animating = False
        self._anim_job = None
        self._anim_steps = 20      # more = smoother/slower
        self._anim_dx = 0          # computed per animation

        # Bind resize + swipe + keys
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # Arrow keys to navigate (bind on this page only)
        self.bind_all("<Left>", lambda e: self.prev_fact())
        self.bind_all("<Right>", lambda e: self.next_fact())

        # Initial render
        self.render_current()

        # Auto advance (optional)
        if self.auto_advance:
            self.schedule_auto()

    def destroy(self):
        # Clean up auto job + key bindings
        if self._auto_job is not None:
            self.after_cancel(self._auto_job)
            self._auto_job = None
        try:
            self.unbind_all("<Left>")
            self.unbind_all("<Right>")
        except Exception:
            pass
        super().destroy()

    def load_entries(self):
        filename = f"{self.category}.csv"
        if not os.path.exists(filename):
            return [f"Missing file: {filename}"]

        entries = []
        with open(filename, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    entries.append(", ".join(row))
        return entries

    def clamp_idx(self):
        if not self.entries:
            self.idx = 0
        else:
            self.idx %= len(self.entries)

    def current_text(self):
        if not self.entries:
            return "(No entries)"
        return self.entries[self.idx]

    def render_current(self):
        self.clamp_idx()
        self.canvas.itemconfigure(self.card_text, text=self.current_text())
        self.position_card()


    def _fit_text_in_height(self, text_item_id: int, max_h: int):
        """
        Shrinks font until the text bbox height fits within max_h.
        If still too tall, truncates with ellipsis.
        """
        # Start / bounds
        start_size = 14
        min_size = 10

        f = tkfont.Font(family="Segoe UI", size=start_size)
        self.canvas.itemconfigure(text_item_id, font=f)

        self.canvas.update_idletasks()
        bbox = self.canvas.bbox(text_item_id)
        if bbox is None:
            return

        def height_of():
            b = self.canvas.bbox(text_item_id)
            return (b[3] - b[1]) if b else 0

        # Shrink font until it fits or we hit min_size
        size = start_size
        while height_of() > max_h and size > min_size:
            size -= 1
            f.configure(size=size)
            self.canvas.itemconfigure(text_item_id, font=f)
            self.canvas.update_idletasks()

        # If still too tall at min font size, truncate text
        if height_of() > max_h:
            original = self.canvas.itemcget(text_item_id, "text")
            truncated = self._truncate_to_height(original, text_item_id, max_h)
            self.canvas.itemconfigure(text_item_id, text=truncated)
            self.canvas.update_idletasks()

    def _truncate_to_height(self, s: str, text_item_id: int, max_h: int) -> str:
        """
        Truncates string with "..." until bbox height fits.
        """
        ell = "..."
        lo, hi = 0, len(s)
        best = ""

        # Binary search for longest prefix that fits (faster than chopping 1 char at a time)
        while lo <= hi:
            mid = (lo + hi) // 2
            candidate = s[:mid].rstrip() + ell
            self.canvas.itemconfigure(text_item_id, text=candidate)
            self.canvas.update_idletasks()

            b = self.canvas.bbox(text_item_id)
            h = (b[3] - b[1]) if b else 0

            if h <= max_h:
                best = candidate
                lo = mid + 1
            else:
                hi = mid - 1

        # If nothing fits, show just ellipsis
        return best if best else ell

    def position_card(self):
        cw = max(1, self.canvas.winfo_width())
        ch = max(1, self.canvas.winfo_height())

        MIN_W, MIN_H = 420, 220
        pad = 20

        card_w = max(MIN_W, int(cw * 0.90))
        card_h = max(MIN_H, int(ch * 0.70))
        card_w = min(card_w, cw - 2 * pad)
        card_h = min(card_h, ch - 2 * pad)

        x1 = (cw - card_w) / 2
        y1 = (ch - card_h) / 2
        x2 = x1 + card_w
        y2 = y1 + card_h

        self.canvas.coords(self.card_rect, x1, y1, x2, y2)

        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2

        # Inner padding inside the card
        inner_pad_x = 40
        inner_pad_y = 28

        wrap = max(200, int(card_w - 2 * inner_pad_x))
        max_h = max(60, int(card_h - 2 * inner_pad_y))

        # Apply wrap + center position first
        self.canvas.itemconfigure(self.card_text, width=wrap)
        self.canvas.coords(self.card_text, cx, cy)

        # Fit text (font size + (optional) truncation)
        self._fit_text_in_height(self.card_text, max_h)

    def on_canvas_resize(self, _event):
        # If you resize mid-animation, it's simplest to snap to final layout
        if self._animating:
            # Cancel animation and re-render cleanly
            if self._anim_job is not None:
                self.after_cancel(self._anim_job)
                self._anim_job = None
            self._animating = False
            self.render_current()
        else:
            self.position_card()


    def next_fact(self):
        if not self.entries or self._animating:
            return
        self._animate_to(direction=+1)

    def prev_fact(self):
        if not self.entries or self._animating:
            return
        self._animate_to(direction=-1)

    def _animate_to(self, direction: int):
        """
        direction = +1 for next (swipe left), -1 for prev (swipe right)
        """
        self._animating = True
        if self._anim_job is not None:
            self.after_cancel(self._anim_job)
            self._anim_job = None

        # Compute the next index but DON'T commit it yet
        n = len(self.entries)
        next_idx = (self.idx + direction) % n
        next_text = self.entries[next_idx]

        # Ensure card is positioned so coords are accurate
        self.position_card()

        # Card geometry
        x1, y1, x2, y2 = self.canvas.coords(self.card_rect)
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        card_w = (x2 - x1)

        # Incoming starts off-screen to the right if going next, left if going prev
        incoming_start_x = cx + card_w if direction == +1 else cx - card_w

        wrap = max(200, int(card_w - 80))

        incoming = self.canvas.create_text(
            incoming_start_x, cy,
            text=next_text,
            font=("Segoe UI", 14),
            anchor="center",
            width=wrap,
        )

        # Move per frame
        total_shift = card_w
        step_shift = total_shift / self._anim_steps
        dx = -step_shift if direction == +1 else +step_shift  # current moves left for next
        self._anim_dx = dx

        step = 0

        def tick():
            nonlocal step
            step += 1

            # Move both texts
            self.canvas.move(self.card_text, dx, 0)
            self.canvas.move(incoming, dx, 0)

            if step < self._anim_steps:
                self._anim_job = self.after(12, tick)  # ~60 FPS
                return

            # Finalize: swap items
            self.canvas.delete(self.card_text)
            self.card_text = incoming
            self.idx = next_idx

            # Re-center perfectly (avoid drift)
            self.position_card()

            self._animating = False
            self._anim_job = None

        tick()


    # "Swipe" (mouse drag) support:
    # drag left => next, drag right => prev
    def on_press(self, event):
        self._swipe_start_x = event.x

    def on_release(self, event):
        if self._swipe_start_x is None:
            return
        dx = event.x - self._swipe_start_x
        self._swipe_start_x = None

        if dx <= -self._swipe_threshold:
            self.next_fact()
        elif dx >= self._swipe_threshold:
            self.prev_fact()

    def schedule_auto(self):
        # Advance every auto_ms
        if self._auto_job is not None:
            self.after_cancel(self._auto_job)
        self._auto_job = self.after(self.auto_ms, self._auto_tick)

    def _auto_tick(self):
        self.next_fact()
        self.schedule_auto()


# ----------------------------------------------------------
# MANUAL MODE (one fact at a time)
# ----------------------------------------------------------
class ManualScrollPage(FactPagerPage):
    def __init__(self, master, category, go_home_callback, go_auto_callback):
        super().__init__(
            master,
            category,
            go_home_callback=go_home_callback,
            other_mode_callback=go_auto_callback,
            other_mode_label="Auto Scroll",
            auto_advance=False,
        )


# ----------------------------------------------------------
# AUTO MODE (one fact at a time, advances automatically)
# ----------------------------------------------------------
class AutoScrollPage(FactPagerPage):
    def __init__(self, master, category, go_home_callback, go_manual_callback):
        super().__init__(
            master,
            category,
            go_home_callback=go_home_callback,
            other_mode_callback=go_manual_callback,
            other_mode_label="Manual",
            auto_advance=True,
            auto_ms=2500,   # tweak speed here
        )

# ----------------------------------------------------------
# HOME PAGE
# ----------------------------------------------------------
class HomePage(tk.Frame):
    def __init__(self, master, open_category_callback):
        super().__init__(master)
        self.master = master
        self.open_category_callback = open_category_callback

        ttk.Label(self, text="Choose a Category", style="Title.TLabel").pack(pady=15)


        grid_frame = tk.Frame(self)
        grid_frame.pack()

        for i, cat in enumerate(categories):
            btn = ttk.Button(
                grid_frame,
                text=cat,
                command=lambda c=cat: self.open_category_callback(c)
            )
            btn.grid(row=i // 2, column=i % 2, padx=15, pady=8)


# ----------------------------------------------------------
# APP
# ----------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Category Viewer")
        self.geometry("450x450")

        apply_style(self)

        self.current_frame = None
        self.current_category = None
        self.show_home()

    def clear_frame(self):
        if self.current_frame:
            self.current_frame.destroy()

    def show_home(self):
        self.clear_frame()
        self.current_frame = HomePage(self, self.open_category_initial)
        self.current_frame.pack(fill="both", expand=True)

    def open_category_initial(self, category):
        self.current_category = category
        self.show_auto_scroll()

    def show_auto_scroll(self):
        self.clear_frame()
        self.current_frame = AutoScrollPage(
            self,
            self.current_category,
            go_home_callback=self.show_home,
            go_manual_callback=self.show_manual_scroll
        )
        self.current_frame.pack(fill="both", expand=True)

    def show_manual_scroll(self):
        self.clear_frame()
        self.current_frame = ManualScrollPage(
            self,
            self.current_category,
            go_home_callback=self.show_home,
            go_auto_callback=self.show_auto_scroll
        )
        self.current_frame.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = App()
    app.mainloop()
