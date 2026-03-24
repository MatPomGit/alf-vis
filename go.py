from tkinter import *
import tkinter as tk
from tkinter import messagebox
import sys
import subprocess
import threading
from tkinter import PhotoImage

wersja = "1.2"
# Ścieżki do skryptów
c1 = "src/image_acquisition/main.py"
c2 = "src/image_acquisition/tracker.py"
c3 = "src/image_acquisition/visualize.py"

c4 = "src/image_analysis/calibration.py"
c5 = "src/image_analysis/camera.py"
c6 = "src/image_analysis/viewer.py"
c7 = "src/image_analysis/map_visualizer.py"


## ________________________________________________

# Banner z numerem wersji w rogu
#banner = Label(root, text=f"v{wersja}", font=("Arial", 8, "bold"), fg="white", bg="#444444", padx=5, pady=2)
#banner.place(relx=1.0, rely=1.0, anchor="se", x=-5, y=-5)  # prawy dolny róg

# Funkcja uruchamiająca skrypt w osobnym wątku
# --- URUCHAMIANIE SKRYPTÓW ---
def run_script(path):
    try:
        subprocess.Popen([sys.executable, path])
    except Exception as e:
        messagebox.showerror("Błąd", str(e))
    # threading.Thread(target=target).start()
    
## ________________________________________________

# --- TOOLTIP ---
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        self.after_id = None

        widget.bind("<Enter>", self.schedule)
        widget.bind("<Leave>", self.hide)
        widget.bind("<Motion>", self.move)

    def schedule(self, event=None):
        self.after_id = self.widget.after(400, self.show)

    def show(self):
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
            font=("Arial", 9)
        )
        label.pack(ipadx=4, ipady=2)

    def move(self, event):
        if self.tip:
            x = event.x_root + 10
            y = event.y_root + 10
            self.tip.geometry(f"+{x}+{y}")

    def hide(self, event=None):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        if self.tip:
            self.tip.destroy()
            self.tip = None

### ________________________________________________
# --- GUI ---
root = tk.Tk()
root.title("Launcher skryptów do wizji Alfa")

# Ikona (opcjonalnie)
try:
    icon = PhotoImage(file="assets/icon.png")
    root.iconphoto(True, icon)
except:
    pass

frm = tk.Frame(root, padx=10, pady=10)
frm.pack()

## ________________________________________________

# Wersja 1
tk.Label(frm, text="Wersja 1").pack(pady=(0,5))
b1 = tk.Button(frm, text=c1, command=lambda: run_script(c1))
b1.pack(fill="x", pady=2)
ToolTip(b1, "Uruchamia główny skrypt akwizycji obrazu")

b2 = tk.Button(frm, text=c2, command=lambda: run_script(c2))
b2.pack(fill="x", pady=2)
ToolTip(b2, "Uruchamia tracker")

b3 = tk.Button(frm, text=c3, command=lambda: run_script(c3))
b3.pack(fill="x", pady=2)
ToolTip(b3, "Uruchamia wizualizację")

# Wersja 2
tk.Label(frm, text="Wersja 2").pack(pady=(10,5))
b4 = tk.Button(frm, text=c4, command=lambda: run_script(c4))
b4.pack(fill="x", pady=2)
ToolTip(b4, "Kalibracja kamery")

b5 = tk.Button(frm, text=c5, command=lambda: run_script(c5))
b5.pack(fill="x", pady=2)
ToolTip(b5, "Obsługa kamery")

b6 = tk.Button(frm, text=c6, command=lambda: run_script(c6))
b6.pack(fill="x", pady=2)
ToolTip(b6, "Podgląd obrazu")

b7 = tk.Button(frm, text=c7, command=lambda: run_script(c7))
b7.pack(fill="x", pady=2)
ToolTip(b7, "Wizualizacja mapy")

# Przycisk zamykający okno
tk.Button(frm, text="Zamknij okno", command=root.destroy).pack(pady=(20,0))

# Banner wersji (prawy dolny róg)
banner = tk.Label(
    root,
    text=f"v{wersja}",
    font=("Arial", 9, "bold"),
    fg="white",
    bg="#444"
)
banner.place(relx=1.0, rely=1.0, anchor="se", x=-5, y=-5)

root.mainloop()