import tkinter as tk
from tkinter import messagebox
import subprocess

def uruchom_skrypt():
    # Twoja logika skryptu tutaj
    # subprocess.run(["python", "main.py"])
    # albo
    # with open("twoj_skrypt.py") as f:
    #   exec(f.read())
    messagebox.showinfo("Sukces", "Skrypt uruchomiony!")

root = tk.Tk()
button = tk.Button(root, text="Uruchom skrypt", command=uruchom_skrypt)
button.pack()
root.mainloop()
