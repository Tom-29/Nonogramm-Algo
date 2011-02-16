"""
Tkinter-basierte Benutzeroberfläche für den Nonogramm-Löser.

Bietet:
- Eingabe der Rastergrösse und Hinweiszahlen
- Vorgegebene Zellen setzen (Kreuze / gefüllte Felder)
- Lösen mit animierter Schritt-für-Schritt-Visualisierung
- Geschwindigkeitsregler für die Animation
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from typing import Optional

from model import NonogramModel, CellState
from solver import solve, ALGORITHMS


# ─── Farben & Layout ─────────────────────────────────────────────────────────

COLOR_BG = "#f0f0f0"
COLOR_GRID_BG = "#ffffff"
COLOR_FILLED = "#2d2d2d"
COLOR_EMPTY = "#ffffff"
COLOR_UNKNOWN = "#e8e8e8"
COLOR_CROSS = "#cc4444"
COLOR_HIGHLIGHT_ROW = "#fff3cd"
COLOR_HIGHLIGHT_COL = "#cce5ff"
COLOR_BORDER = "#333333"
COLOR_CLUE_BG = "#fafafa"

CELL_SIZE = 32
MIN_CELL_SIZE = 16
MAX_CELL_SIZE = 60
CLUE_AREA_WIDTH = 120
CLUE_AREA_HEIGHT = 80


class NonogramUI:
    """Hauptfenster der Nonogramm-Anwendung."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Nonogramm-Löser")
        self.root.configure(bg=COLOR_BG)
        self.root.minsize(700, 550)

        self.model: Optional[NonogramModel] = None
        self.cell_size = CELL_SIZE
        self.solving = False
        self.solve_thread: Optional[threading.Thread] = None
        self.animation_delay = 200  # ms
        self.highlight_row = -1
        self.highlight_col = -1
        self.step_log: list[str] = []

        # Eingabefelder für Hinweiszahlen
        self.row_clue_entries: list[tk.Entry] = []
        self.col_clue_entries: list[tk.Entry] = []

        self._build_ui()

    # ─── UI aufbauen ─────────────────────────────────────────────────────

    def _build_ui(self):
        """Erstellt das gesamte UI-Layout."""

        # === Oberer Bereich: Einstellungen ===
        settings_frame = ttk.LabelFrame(
            self.root, text="Einstellungen", padding=10
        )
        settings_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        # Zeilen / Spalten
        ttk.Label(settings_frame, text="Zeilen:").grid(
            row=0, column=0, padx=(0, 5), sticky=tk.W
        )
        self.rows_var = tk.StringVar(value="5")
        self.rows_entry = ttk.Entry(
            settings_frame, textvariable=self.rows_var, width=5
        )
        self.rows_entry.grid(row=0, column=1, padx=(0, 15))

        ttk.Label(settings_frame, text="Spalten:").grid(
            row=0, column=2, padx=(0, 5), sticky=tk.W
        )
        self.cols_var = tk.StringVar(value="5")
        self.cols_entry = ttk.Entry(
            settings_frame, textvariable=self.cols_var, width=5
        )
        self.cols_entry.grid(row=0, column=3, padx=(0, 15))

        self.create_btn = ttk.Button(
            settings_frame, text="Raster erstellen", command=self._create_grid
        )
        self.create_btn.grid(row=0, column=4, padx=(0, 15))

        # Algorithmus-Auswahl
        ttk.Label(settings_frame, text="Algorithmus:").grid(
            row=0, column=5, padx=(15, 5), sticky=tk.W
        )
        self.algorithm_var = tk.StringVar(value="CP + Backtracking")
        self.algorithm_combo = ttk.Combobox(
            settings_frame, textvariable=self.algorithm_var,
            values=list(ALGORITHMS.keys()), state="readonly", width=25
        )
        self.algorithm_combo.grid(row=0, column=6, padx=(0, 5))
        self.algorithm_combo.bind("<<ComboboxSelected>>", self._on_algorithm_change)

        self.algo_desc_label = ttk.Label(
            settings_frame,
            text=ALGORITHMS["CP + Backtracking"],
            font=("Segoe UI", 8), foreground="#666666"
        )
        self.algo_desc_label.grid(row=1, column=5, columnspan=3, padx=(15, 0), sticky=tk.W)

        # Geschwindigkeit
        ttk.Label(settings_frame, text="Geschwindigkeit:").grid(
            row=0, column=7, padx=(15, 5), sticky=tk.W
        )
        self.speed_var = tk.IntVar(value=200)
        self.speed_scale = ttk.Scale(
            settings_frame, from_=10, to=1000, variable=self.speed_var,
            orient=tk.HORIZONTAL, length=120,
            command=self._on_speed_change
        )
        self.speed_scale.grid(row=0, column=8, padx=(0, 5))
        self.speed_label = ttk.Label(settings_frame, text="200 ms")
        self.speed_label.grid(row=0, column=9)

        # === Mittlerer Bereich: Hinweiszahlen und Raster ===
        self.main_frame = ttk.Frame(self.root, padding=5)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Scrollbarer Canvas für grosse Raster
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            self.canvas_frame, bg=COLOR_BG, highlightthickness=0
        )

        self.scroll_y = ttk.Scrollbar(
            self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview
        )
        self.scroll_x = ttk.Scrollbar(
            self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview
        )
        self.canvas.configure(
            xscrollcommand=self.scroll_x.set,
            yscrollcommand=self.scroll_y.set
        )

        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Innerer Frame im Canvas
        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.inner_frame, anchor=tk.NW
        )
        self.inner_frame.bind("<Configure>", self._on_frame_configure)

        # === Unterer Bereich: Buttons und Log ===
        bottom_frame = ttk.Frame(self.root, padding=5)
        bottom_frame.pack(fill=tk.X, padx=10, pady=(5, 10))

        btn_frame = ttk.Frame(bottom_frame)
        btn_frame.pack(fill=tk.X)

        self.solve_btn = ttk.Button(
            btn_frame, text="▶ Lösen", command=self._start_solve,
            state=tk.DISABLED
        )
        self.solve_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.reset_btn = ttk.Button(
            btn_frame, text="↺ Zurücksetzen", command=self._reset_grid,
            state=tk.DISABLED
        )
        self.reset_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.load_example_btn = ttk.Button(
            btn_frame, text="Beispiel laden", command=self._load_example
        )
        self.load_example_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Status
        self.status_var = tk.StringVar(value="Bitte Rastergrösse festlegen und erstellen.")
        status_bar = ttk.Label(
            bottom_frame, textvariable=self.status_var, relief=tk.SUNKEN,
            anchor=tk.W, padding=(5, 2)
        )
        status_bar.pack(fill=tk.X, pady=(5, 0))

        # Log-Bereich
        log_frame = ttk.LabelFrame(bottom_frame, text="Lösungsprotokoll", padding=5)
        log_frame.pack(fill=tk.X, pady=(5, 0))

        self.log_text = tk.Text(
            log_frame, height=5, wrap=tk.WORD, state=tk.DISABLED,
            font=("Consolas", 9)
        )
        log_scroll = ttk.Scrollbar(
            log_frame, orient=tk.VERTICAL, command=self.log_text.yview
        )
        self.log_text.configure(yscrollcommand=log_scroll.set)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(fill=tk.X)

    def _on_frame_configure(self, event=None):
        """Aktualisiert die Scroll-Region."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_algorithm_change(self, event=None):
        """Aktualisiert die Beschreibung bei Algorithmus-Wechsel."""
        algo = self.algorithm_var.get()
        desc = ALGORITHMS.get(algo, "")
        self.algo_desc_label.config(text=desc)

    def _on_speed_change(self, value):
        """Aktualisiert die Animationsgeschwindigkeit."""
        self.animation_delay = int(float(value))
        self.speed_label.config(text=f"{self.animation_delay} ms")

    # ─── Raster erstellen ────────────────────────────────────────────────

    def _create_grid(self):
        """Erstellt das Raster basierend auf den Eingaben."""
        try:
            rows = int(self.rows_var.get())
            cols = int(self.cols_var.get())
        except ValueError:
            messagebox.showerror("Fehler", "Bitte gültige Zahlen eingeben.")
            return

        if rows < 1 or cols < 1 or rows > 50 or cols > 50:
            messagebox.showerror("Fehler", "Grösse muss zwischen 1 und 50 liegen.")
            return

        self.model = NonogramModel(rows, cols)

        # Zellgrösse anpassen
        self.cell_size = max(MIN_CELL_SIZE, min(MAX_CELL_SIZE, CELL_SIZE))

        # Altes Raster entfernen
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        self._build_clue_inputs()
        self._build_grid_canvas()

        self.solve_btn.config(state=tk.NORMAL)
        self.reset_btn.config(state=tk.NORMAL)
        self.status_var.set(
            f"Raster {rows}×{cols} erstellt. "
            "Hinweiszahlen eingeben und auf Lösen klicken."
        )

    def _build_clue_inputs(self):
        """Erstellt die Eingabefelder für Hinweiszahlen."""
        rows = self.model.rows
        cols = self.model.cols
        cs = self.cell_size

        # Frame-Layout: Spalten-Hinweise oben, Zeilen-Hinweise links
        # Ecke oben links mit Beschriftung
        corner = tk.Frame(self.inner_frame, width=CLUE_AREA_WIDTH,
                          height=CLUE_AREA_HEIGHT, bg=COLOR_BG)
        corner.grid(row=0, column=0, sticky=tk.NSEW)
        corner.grid_propagate(False)

        tk.Label(
            corner, text="Spalten ↓\nZeilen →\n(z.B. 1 3 2)",
            font=("Segoe UI", 8), anchor=tk.SE, justify=tk.RIGHT,
            bg=COLOR_BG
        ).place(relx=1.0, rely=1.0, anchor=tk.SE, x=-5, y=-5)

        # Spalten-Hinweise (oben) – Verwende grid-Layout statt place
        col_clue_frame = tk.Frame(self.inner_frame, bg=COLOR_BG,
                                  width=cols * cs, height=CLUE_AREA_HEIGHT)
        col_clue_frame.grid(row=0, column=1, sticky=tk.SW)
        col_clue_frame.grid_propagate(False)

        self.col_clue_entries = []
        for c in range(cols):
            entry = tk.Entry(
                col_clue_frame, width=4, justify=tk.CENTER,
                font=("Consolas", 9), relief=tk.SOLID, bd=1
            )
            entry.place(x=c * cs, y=CLUE_AREA_HEIGHT - 28, width=cs, height=24)
            entry.insert(0, "0")
            self.col_clue_entries.append(entry)

        # Zeilen-Hinweise (links) – Verwende feste Grösse
        row_clue_frame = tk.Frame(self.inner_frame, bg=COLOR_BG,
                                  width=CLUE_AREA_WIDTH, height=rows * cs)
        row_clue_frame.grid(row=1, column=0, sticky=tk.NE)
        row_clue_frame.grid_propagate(False)

        self.row_clue_entries = []
        for r in range(rows):
            entry = tk.Entry(
                row_clue_frame, width=12, justify=tk.RIGHT,
                font=("Consolas", 9), relief=tk.SOLID, bd=1
            )
            entry.place(
                x=2, y=r * cs + (cs - 24) // 2,
                width=CLUE_AREA_WIDTH - 7, height=24
            )
            entry.insert(0, "0")
            self.row_clue_entries.append(entry)

    def _build_grid_canvas(self):
        """Erstellt den Canvas für das Nonogramm-Raster."""
        rows = self.model.rows
        cols = self.model.cols
        cs = self.cell_size

        canvas_w = cols * cs + 1
        canvas_h = rows * cs + 1

        self.grid_canvas = tk.Canvas(
            self.inner_frame, width=canvas_w, height=canvas_h,
            bg=COLOR_GRID_BG, highlightthickness=1,
            highlightbackground=COLOR_BORDER
        )
        self.grid_canvas.grid(row=1, column=1, sticky=tk.NW)

        # Zellen zeichnen
        self._draw_grid()

        # Klick-Handler für Zellen
        self.grid_canvas.bind("<Button-1>", self._on_cell_left_click)
        self.grid_canvas.bind("<Button-3>", self._on_cell_right_click)

    def _draw_grid(self):
        """Zeichnet das gesamte Raster neu."""
        if self.model is None:
            return

        self.grid_canvas.delete("all")
        rows = self.model.rows
        cols = self.model.cols
        cs = self.cell_size

        for r in range(rows):
            for c in range(cols):
                x1, y1 = c * cs, r * cs
                x2, y2 = x1 + cs, y1 + cs

                state = self.model.get_cell(r, c)

                # Hintergrundfarbe
                if state == CellState.FILLED:
                    fill = COLOR_FILLED
                elif state == CellState.EMPTY:
                    fill = COLOR_EMPTY
                else:
                    # Hervorhebung bei Animation
                    if r == self.highlight_row:
                        fill = COLOR_HIGHLIGHT_ROW
                    elif c == self.highlight_col:
                        fill = COLOR_HIGHLIGHT_COL
                    else:
                        fill = COLOR_UNKNOWN

                # 5er-Block-Linien dicker zeichnen
                border_w = 1
                border_color = "#999999"

                self.grid_canvas.create_rectangle(
                    x1, y1, x2, y2, fill=fill, outline=border_color,
                    width=border_w, tags=f"cell_{r}_{c}"
                )

                # Kreuz für EMPTY-Zellen zeichnen
                if state == CellState.EMPTY:
                    pad = cs * 0.25
                    self.grid_canvas.create_line(
                        x1 + pad, y1 + pad, x2 - pad, y2 - pad,
                        fill=COLOR_CROSS, width=2
                    )
                    self.grid_canvas.create_line(
                        x2 - pad, y1 + pad, x1 + pad, y2 - pad,
                        fill=COLOR_CROSS, width=2
                    )

        # 5er-Block dicke Linien
        for r in range(0, rows + 1, 5):
            y = r * cs
            self.grid_canvas.create_line(
                0, y, cols * cs, y, fill=COLOR_BORDER, width=2
            )
        for c in range(0, cols + 1, 5):
            x = c * cs
            self.grid_canvas.create_line(
                x, 0, x, rows * cs, fill=COLOR_BORDER, width=2
            )

        # Äusserer Rahmen
        self.grid_canvas.create_rectangle(
            0, 0, cols * cs, rows * cs, outline=COLOR_BORDER, width=2
        )

    # ─── Zell-Klick-Handler ──────────────────────────────────────────────

    def _get_cell_from_event(self, event) -> Optional[tuple]:
        """Bestimmt Zeile/Spalte aus einem Maus-Event."""
        if self.model is None:
            return None
        cs = self.cell_size
        col = event.x // cs
        row = event.y // cs
        if 0 <= row < self.model.rows and 0 <= col < self.model.cols:
            return row, col
        return None

    def _on_cell_left_click(self, event):
        """Linksklick: Zelle als FILLED toggeln (für Vorgaben)."""
        if self.solving:
            return
        cell = self._get_cell_from_event(event)
        if cell is None:
            return
        r, c = cell
        current = self.model.get_cell(r, c)
        if current == CellState.FILLED:
            self.model.set_cell(r, c, CellState.UNKNOWN)
        else:
            self.model.set_cell(r, c, CellState.FILLED)
        self._draw_grid()

    def _on_cell_right_click(self, event):
        """Rechtsklick: Zelle als EMPTY toggeln (Kreuz)."""
        if self.solving:
            return
        cell = self._get_cell_from_event(event)
        if cell is None:
            return
        r, c = cell
        current = self.model.get_cell(r, c)
        if current == CellState.EMPTY:
            self.model.set_cell(r, c, CellState.UNKNOWN)
        else:
            self.model.set_cell(r, c, CellState.EMPTY)
        self._draw_grid()

    # ─── Hinweiszahlen lesen ────────────────────────────────────────────

    def _read_clues(self) -> bool:
        """Liest die Hinweiszahlen aus den Eingabefeldern."""
        try:
            for r in range(self.model.rows):
                text = self.row_clue_entries[r].get().strip()
                if not text:
                    text = "0"
                clues = [int(x) for x in text.split()]
                self.model.set_row_clues(r, clues)

            for c in range(self.model.cols):
                text = self.col_clue_entries[c].get().strip()
                if not text:
                    text = "0"
                clues = [int(x) for x in text.split()]
                self.model.set_col_clues(c, clues)

            return True
        except ValueError:
            messagebox.showerror(
                "Fehler",
                "Hinweiszahlen müssen Ganzzahlen sein, getrennt durch Leerzeichen.\n"
                "Beispiel: 1 3 2"
            )
            return False

    # ─── Lösen ───────────────────────────────────────────────────────────

    def _start_solve(self):
        """Startet den Lösungsvorgang in einem eigenen Thread."""
        if self.solving or self.model is None:
            return

        if not self._read_clues():
            return

        valid, msg = self.model.validate_clues()
        if not valid:
            messagebox.showerror("Validierungsfehler", msg)
            return

        self.solving = True
        self.solve_btn.config(state=tk.DISABLED)
        self.create_btn.config(state=tk.DISABLED)
        self.load_example_btn.config(state=tk.DISABLED)
        self._clear_log()
        self.status_var.set("Löse...")

        # In einem separaten Thread lösen damit UI nicht blockiert
        self.solve_thread = threading.Thread(
            target=self._solve_worker, daemon=True
        )
        self.solve_thread.start()

    def _solve_worker(self):
        """Arbeits-Thread für den Solver."""
        start_time = time.time()

        def callback(model, message, idx, is_row):
            """Callback aus dem Solver - aktualisiert UI thread-sicher."""
            self.model = model
            self.highlight_row = idx if is_row else -1
            self.highlight_col = idx if not is_row else -1
            # UI-Updates im Main-Thread
            self.root.after(0, self._update_display, message)
            time.sleep(self.animation_delay / 1000.0)

        algorithm = self.algorithm_var.get()
        success = solve(self.model, callback=callback, algorithm=algorithm)

        elapsed = time.time() - start_time

        # Ergebnis im Main-Thread anzeigen
        self.root.after(0, self._on_solve_complete, success, elapsed)

    def _update_display(self, message: str):
        """Aktualisiert die Anzeige (wird im Main-Thread aufgerufen)."""
        self._draw_grid()
        self._append_log(message)
        self.status_var.set(message)

    def _on_solve_complete(self, success: bool, elapsed: float):
        """Wird nach Abschluss des Lösens aufgerufen."""
        self.solving = False
        self.highlight_row = -1
        self.highlight_col = -1
        self._draw_grid()

        self.solve_btn.config(state=tk.NORMAL)
        self.create_btn.config(state=tk.NORMAL)
        self.load_example_btn.config(state=tk.NORMAL)

        if success:
            msg = f"Puzzle gelöst in {elapsed:.2f} Sekunden!"
            self.status_var.set(msg)
            self._append_log(f"\n{msg}")
        else:
            msg = "Keine Lösung gefunden. Bitte Hinweiszahlen überprüfen."
            self.status_var.set(msg)
            self._append_log(f"\n{msg}")
            messagebox.showwarning("Keine Lösung", msg)

    # ─── Zurücksetzen ────────────────────────────────────────────────────

    def _reset_grid(self):
        """Setzt das Raster zurück (behält Hinweiszahlen)."""
        if self.model is None or self.solving:
            return
        for r in range(self.model.rows):
            for c in range(self.model.cols):
                self.model.set_cell(r, c, CellState.UNKNOWN)
        self.highlight_row = -1
        self.highlight_col = -1
        self._draw_grid()
        self._clear_log()
        self.status_var.set("Raster zurückgesetzt.")

    # ─── Beispiel laden ──────────────────────────────────────────────────

    def _load_example(self):
        """Lädt ein Beispiel-Nonogramm (Herz 5×5)."""
        self.rows_var.set("5")
        self.cols_var.set("5")
        self._create_grid()

        # Herz-Muster
        row_clues = ["1 1", "5", "5", "3", "1"]
        col_clues = ["2", "4", "4", "4", "2"]

        for r, clue in enumerate(row_clues):
            self.row_clue_entries[r].delete(0, tk.END)
            self.row_clue_entries[r].insert(0, clue)

        for c, clue in enumerate(col_clues):
            self.col_clue_entries[c].delete(0, tk.END)
            self.col_clue_entries[c].insert(0, clue)

        self.status_var.set(
            "Beispiel geladen (Herz 5×5). Klicke 'Lösen' zum Starten."
        )

    # ─── Logging ─────────────────────────────────────────────────────────

    def _append_log(self, message: str):
        """Fügt eine Nachricht zum Lösungsprotokoll hinzu."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _clear_log(self):
        """Leert das Lösungsprotokoll."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)
