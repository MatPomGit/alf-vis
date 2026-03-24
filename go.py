from tkinter import *
import tkinter as tk
from tkinter import messagebox
import subprocess

c1 = "src/image_acquisition/main.py"
c2 = "src/image_acquisition/tracker.py"
c3 = "src/image_acquisition/visualize.py"


def run_script(path):
    subprocess.run(["python", path])
    # albo
    # with open("twoj_skrypt.py") as f:
    #   exec(f.read())
    messagebox.showinfo("Sukces", "Skrypt uruchomiony!")

root = tk.Tk()
frm = tk.Frame(root, padding=10)
tk.Label(frm, text="Wersja 2").grid(column=0, row=0)

button = tk.Button(root, text=c1, command=run_script(c1), fg="red", bg="blue")
button = tk.Button(root, text=c2, command=run_script(c2))
button = tk.Button(root, text=c3, command=run_script(c3))

tk.Label(frm, text="Wersja 2").grid(column=0, row=0)


button = tk.Button(root, text="Zamknij okno", command=destroy .)
fred.pack(expand=1)

button.pack()
root.mainloop()
