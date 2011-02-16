"""
Nonogramm-Löser - Einstiegspunkt

Startet die grafische Benutzeroberfläche.
"""

import tkinter as tk
from ui import NonogramUI


def main():
    root = tk.Tk()
    root.geometry("900x750")
    app = NonogramUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
