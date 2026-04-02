"""Launcher GUI for the alf-vis script collection.

Tkinter window with buttons to run the main project scripts.
Version: 1.2
"""

import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, PhotoImage

_VERSION = "1.2"

# Paths to runnable scripts
_C1 = "experimental/image_acquisition/main.py"
_C2 = "experimental/image_acquisition/tracker.py"
_C3 = "experimental/image_acquisition/visualize.py"

_C4 = "src/image_analysis/calibration.py"
_C5 = "src/image_analysis/camera.py"
_C6 = "src/image_analysis/viewer.py"
_C7 = "src/image_analysis/map_visualizer.py"


def run_script(path: str) -> None:
    """Launch *path* as a subprocess."""
    try:
        subprocess.Popen([sys.executable, path])
    except Exception as exc:
        messagebox.showerror("Błąd", str(exc))


class ToolTip:
    """Show a floating tooltip after a short hover delay."""

    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self.tip: tk.Toplevel | None = None
        self.after_id: str | None = None

        widget.bind("<Enter>", self.schedule)
        widget.bind("<Leave>", self.hide)
        widget.bind("<Motion>", self.move)

    def schedule(self, event: tk.Event | None = None) -> None:  # noqa: ARG002
        self.after_id = self.widget.after(400, self.show)

    def show(self) -> None:
        if self.tip or not self.text:
            return
        x = self.widget.winfo_pointerx() + 10
        y = self.widget.winfo_pointery() + 10
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tip,
            text=self.text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=("Arial", 9),
        )
        label.pack(ipadx=4, ipady=2)

    def move(self, event: tk.Event) -> None:
        if self.tip:
            self.tip.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

    def hide(self, event: tk.Event | None = None) -> None:  # noqa: ARG002
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        if self.tip:
            self.tip.destroy()
            self.tip = None


def main() -> None:
    """Build and run the launcher window."""
    root = tk.Tk()
    root.title("Launcher skryptów do wizji Alfa")

    try:
        icon = PhotoImage(file="assets/icon.png")
        root.iconphoto(True, icon)
    except Exception:  # noqa: BLE001
        pass

    frm = tk.Frame(root, padx=10, pady=10)
    frm.pack()

    tk.Label(frm, text="Wersja 1").pack(pady=(0, 5))
    for path, tip in (
        (_C1, "Uruchamia główny skrypt akwizycji obrazu"),
        (_C2, "Uruchamia tracker"),
        (_C3, "Uruchamia wizualizację"),
    ):
        btn = tk.Button(frm, text=path, command=lambda p=path: run_script(p))
        btn.pack(fill="x", pady=2)
        ToolTip(btn, tip)

    tk.Label(frm, text="Wersja 2").pack(pady=(10, 5))
    for path, tip in (
        (_C4, "Kalibracja kamery"),
        (_C5, "Obsługa kamery"),
        (_C6, "Podgląd obrazu"),
        (_C7, "Wizualizacja mapy"),
    ):
        btn = tk.Button(frm, text=path, command=lambda p=path: run_script(p))
        btn.pack(fill="x", pady=2)
        ToolTip(btn, tip)

    tk.Button(frm, text="Zamknij okno", command=root.destroy).pack(pady=(20, 0))

    tk.Label(
        root,
        text=f"v{_VERSION}",
        font=("Arial", 9, "bold"),
        fg="white",
        bg="#444",
    ).place(relx=1.0, rely=1.0, anchor="se", x=-5, y=-5)

    root.mainloop()


if __name__ == "__main__":
    main()
