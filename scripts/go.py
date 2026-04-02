"""Launcher GUI for the alf-vis script collection.

Tkinter window with buttons to run the main project scripts.
Version: 2.0
"""

import os
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import PhotoImage, messagebox

_VERSION = "2.0"

# ---------------------------------------------------------------------------
# Script catalogue
# (path, short description shown in button, long tooltip shown on hover)
# ---------------------------------------------------------------------------
_DEMOS = [
    (
        "experimental/demo_basic_tracking/main.py",
        "Podstawowy tracking (ByteTrack + YOLO)",
        "Detekcja YOLO + tracker ByteTrack 2-D; każdy obiekt otrzymuje unikalny ID.",
    ),
    (
        "experimental/demo_realsense_pipeline/main.py",
        "Potok RealSense + eksport CSV",
        "Kompletny potok RealSense: akwizycja RGB+głębia, SORT tracker, eksport CSV.",
    ),
    (
        "experimental/demo_3d_world_map/main.py",
        "Mapa 3-D głębi + stub SLAM",
        "Projekcja punktów 3-D z RealSense, budowa mapy świata, stub ORB-SLAM3.",
    ),
    (
        "experimental/demo_apriltag_fusion/main.py",
        "Fuzja AprilTag + YOLO + Kalman 3-D",
        "Markery AprilTag wyznaczają pozycję kamery; trajektoria filtrowana Kalmanem.",
    ),
    (
        "experimental/demo_yolo_utils/camera_yolo.py",
        "Narzędzia preprocessingu NCHW",
        "Bilinear resize dla tensorów NCHW w czystym NumPy — bez cv2.",
    ),
    (
        "experimental/fast_camera/main.py",
        "Fast Camera – przetwarzanie w czasie rzeczywistym",
        "Minimalny czas odpowiedzi: wątki producent/konsument, kolejka głębokości 1, imgsz=320.",
    ),
]

_LIBRARY = [
    (
        "src/image_analysis/calibration.py",
        "Kalibracja kamery",
        "Wyznaczanie macierzy kamery i współczynników dystorsji.",
    ),
    (
        "src/image_analysis/camera.py",
        "Obsługa kamery",
        "Abstrakcja strumienia obrazu z kamery USB / pliku wideo.",
    ),
    (
        "src/image_analysis/viewer.py",
        "Podgląd obrazu RGB + głębia",
        "Renderowanie podglądu RGB i fałszywokolorowej mapy głębi side-by-side.",
    ),
    (
        "src/image_analysis/map_visualizer.py",
        "Wizualizacja mapy",
        "Wyświetlanie mapy 2-D / top-view ze ścieżkami obiektów.",
    ),
]


def _find_python() -> list[str]:
    """Return a command prefix that points to a suitable Python interpreter.

    Tries in order:
    1. Active Conda environment (``CONDA_PREFIX``).
    2. Current interpreter (``sys.executable``).
    """
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        for candidate in (
            os.path.join(conda_prefix, "bin", "python"),
            os.path.join(conda_prefix, "python.exe"),
        ):
            if os.path.isfile(candidate):
                return [candidate]

    # Try to activate the base Conda environment if conda is on PATH
    conda_exe = shutil.which("conda")
    if conda_exe:
        return [conda_exe, "run", "--no-capture-output", "-n", "base", sys.executable]

    return [sys.executable]


def run_script(path: str) -> None:
    """Launch *path* as a subprocess using the best available Python."""
    try:
        cmd = _find_python() + [path]
        subprocess.Popen(cmd)
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


def _add_section(frm: tk.Frame, title: str, entries: list[tuple[str, str, str]]) -> None:
    """Add a labelled group of script-launch buttons to *frm*."""
    tk.Label(frm, text=title, font=("Arial", 10, "bold")).pack(pady=(8, 3))
    for path, label, tooltip in entries:
        btn = tk.Button(
            frm,
            text=label,
            anchor="w",
            command=lambda p=path: run_script(p),
        )
        btn.pack(fill="x", pady=2)
        ToolTip(btn, tooltip)


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

    _add_section(frm, "Programy demonstracyjne", _DEMOS)
    _add_section(frm, "Biblioteka image_analysis", _LIBRARY)

    tk.Button(frm, text="Zamknij okno", command=root.destroy).pack(pady=(16, 0))

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

