import tkinter as tk
from tkinter import ttk
import csv
import os

categories = [
    "Animals", "Architecture", "Chemistry", "Energy", "Environment",
    "Health", "Music", "Physics", "Space", "Technology"
]


# ----------------------------------------------------------
# MANUAL SCROLL VIEW
# ----------------------------------------------------------
class ManualScrollPage(tk.Frame):
    def __init__(self, master, category, go_home_callback, go_auto_callback):
        super().__init__(master)
        self.master = master
        self.category = category
        self.go_home_callback = go_home_callback
        self.go_auto_callback = go_auto_callback

        ttk.Label(self, text=f"{category}", font=("Arial", 20)).pack(pady=10)

        # Canvas dimensions
        self.canvas_width = 800
        self.canvas_height = 600

        # Scrollable canvas
        self.canvas = tk.Canvas(self, width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack(side=tk.LEFT, fill="both", expand=True)

        # Vertical scrollbar
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Load entries
        self.entries = self.load_entries()
        self.items = []

        # Draw rectangles and text directly on the canvas
        y_offset = 0
        entry_height = 120
        margin = 5

        for entry in self.entries:
            x1 = margin
            x2 = self.canvas_width - margin
            y1 = y_offset
            y2 = y_offset + entry_height

            rect = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline="black",
                width=2
            )

            text = self.canvas.create_text(
                self.canvas_width // 2,
                y1 + entry_height // 2,
                text=entry,
                font=("Arial", 14),
                anchor="center",
                width=self.canvas_width - 40  # wrap text inside rectangle
            )

            self.items.append((rect, text))
            y_offset += entry_height + 40  # spacing between entries

        # After drawing all items, bind a configure event
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        # Configure scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        # Bind mouse wheel
        self.canvas.bind_all("<MouseWheel>", self.on_wheel)

        # Navigation buttons
        ttk.Button(self, text="Back", command=self.go_home_callback).pack(pady=10)
        ttk.Button(self, text="Auto Scroll", command=self.go_auto_callback).pack(pady=5)

    def load_entries(self):
        filename = f"{self.category}.csv"
        if not os.path.exists(filename):
            return [f"Missing file: {filename}"]

        entries = []
        with open(filename, newline='', encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    # Join multiple columns in case commas exist in entry
                    entries.append(', '.join(row))
        return entries

    def on_wheel(self, event):
        # Scroll the canvas
        self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def on_canvas_resize(self, event):
        canvas_width = event.width
        desired_rect_width = 800  # fixed width for rectangles

        for rect, text in self.items:
            # Keep rectangle height the same
            x1, y1, x2, y2 = self.canvas.coords(rect)
            rect_height = y2 - y1

            # Center rectangle horizontally
            new_x1 = (canvas_width - desired_rect_width) // 2
            new_x2 = new_x1 + desired_rect_width
            self.canvas.coords(rect, new_x1, y1, new_x2, y2)

            # Center text inside rectangle
            _, text_y = self.canvas.coords(text)
            text_x = new_x1 + desired_rect_width // 2
            self.canvas.coords(text, text_x, text_y)

# ----------------------------------------------------------
# AUTO SCROLL VIEW (your original)
# ----------------------------------------------------------
class AutoScrollPage(tk.Frame):
    def __init__(self, master, category, go_home_callback, go_manual_callback):
        super().__init__(master)
        self.master = master
        self.category = category
        self.go_home_callback = go_home_callback
        self.go_manual_callback = go_manual_callback

        ttk.Label(self, text=f"{category}", font=("Arial", 20)).pack(pady=10)

        self.canvas_height = 600
        self.canvas_width = 800

        self.canvas = tk.Canvas(self, width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack()

        self.entries = self.load_entries()
        self.items = []

        y_offset = 0
        for entry in self.entries:
            x1 = 5
            x2 = self.canvas_width - 5
            y1 = y_offset - 60
            y2 = y_offset + 60

            rect = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline="black",
                width=2
            )
            text = self.canvas.create_text(
                x1 + 5,
                y_offset,
                text=entry,
                font=("Arial", 14),
                anchor="w",
                width=self.canvas_width - 40
            )

            self.items.append((rect, text))
            y_offset += 160

        self.scroll_speed = 1
        self.after(30, self.scroll)

        ttk.Button(self, text="Back", command=self.go_home_callback).pack(pady=10)
        ttk.Button(self, text="Manual Scroll", command=self.go_manual_callback).pack()

    def load_entries(self):
        filename = f"{self.category}.csv"
        if not os.path.exists(filename):
            return [f"Missing file: {filename}"]

        entries = []
        with open(filename, newline='', encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    entries.append(row[0])
        return entries

    def scroll(self):
        if not self.items:
            self.after(30, self.scroll)
            return

        y_offset = 0

        for rect, text in self.items:
            self.canvas.move(rect, 0, -self.scroll_speed)
            self.canvas.move(text, 0, -self.scroll_speed)

        bottom_y = max(self.canvas.coords(text)[1] for _, text in self.items)

        for rect, text in self.items:
            _, y = self.canvas.coords(text)

            if y < -20:
                y_offset += 160
                new_y = bottom_y + y_offset

                x1, old_y1, x2, old_y2 = self.canvas.coords(rect)
                dy = new_y - (old_y1 + 60)

                self.canvas.move(rect, 0, dy)
                self.canvas.coords(text, 10, new_y)

                bottom_y = new_y

        self.after(30, self.scroll)


# ----------------------------------------------------------
# HOME PAGE
# ----------------------------------------------------------
class HomePage(tk.Frame):
    def __init__(self, master, open_category_callback):
        super().__init__(master)
        self.master = master
        self.open_category_callback = open_category_callback

        ttk.Label(self, text="Choose a Category", font=("Arial", 20)).pack(pady=15)

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
