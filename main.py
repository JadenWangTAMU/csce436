import tkinter as tk
from tkinter import messagebox

categories=["Animals", "Architecture", "Chemistry", "Energy", "Environment", "Health", "Music", "Physics", "Space", "Technology"]

def on_category_click(category):
    # For now, show a dialog—swap this with your own function
    messagebox.showinfo("Selected", f"You chose: {category}")

def main():
    root = tk.Tk()
    root.title("Category Selector")
    root.geometry("400x350")
    title_label = tk.Label(root, text="Choose a Category", font=("Arial", 16))
    title_label.pack(pady=10)

    # Container for buttons
    frame = tk.Frame(root)
    frame.pack(pady=10)

    for i, cat in enumerate(categories):
        btn = tk.Button(
            frame,
            text=cat,
            width=20,
            command=lambda c=cat: on_category_click(c)
        )
        btn.grid(row=i // 2, column=i % 2, padx=10, pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()