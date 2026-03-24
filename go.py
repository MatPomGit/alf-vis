from tkinter import *
import tkinter as tk
from tkinter import messagebox
import sys
import subprocess
import threading
from tkinter import PhotoImage

# Ścieżki do skryptów
c1 = "src/image_acquisition/main.py"
c2 = "src/image_acquisition/tracker.py"
c3 = "src/image_acquisition/visualize.py"

c4 = "src/image_analysis/calibration.py"
c5 = "src/image_analysis/camera.py"
c6 = "src/image_analysis/viewer.py"
c7 = "src/image_analysis/map_visualizer.py"
wersja = "1.1"

# Tworzenie okna głównego
root = tk.Tk()
root.title("Launcher skryptów do wizji")

# Dodanie ikony
ikona = PhotoImage(file="icon.png")  # PNG 32x32 najlepiej
root.iconphoto(True, ikona)

# Banner z numerem wersji w rogu
banner = Label(root, text=f"v{wersja}", font=("Arial", 10, "bold"), fg="white", bg="#444444", padx=5, pady=2)
banner.place(relx=1.0, rely=1.0, anchor="se", x=-5, y=-5)  # prawy dolny róg

# Funkcja uruchamiająca skrypt w osobnym wątku
def run_script(path):
    def target():
        try:
            subprocess.Popen(["python", path])
            messagebox.showinfo("Sukces", f"Skrypt {path} uruchomiony!")
        except Exception as e:
            messagebox.showerror("Błąd", str(e))
    threading.Thread(target=target).start()

# Klasa do prostego tooltipa
class ToolTip(object):
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tip or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert") if hasattr(self.widget, "bbox") else (0,0,0,0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tip = Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        label = Label(self.tip, text=self.text, background="#ffffe0", relief="solid", borderwidth=1, font=("Arial", 10))
        label.pack()

    def hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None

# Frame do przycisków i etykiet
frm = tk.Frame(root, padx=10, pady=10)
frm.pack()

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

# Numer wersji w prawym dolnym rogu
ver_label = Label(root, text=f"Wersja {wersja}", font=("Arial", 9), fg="gray")
ver_label.pack(side="bottom", anchor="e", padx=5, pady=5)

root.mainloop()