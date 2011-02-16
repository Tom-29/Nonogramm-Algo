"""
Datenmodell für das Nonogramm-Puzzle.

Trennt die Datenstruktur klar vom Algorithmus und der Benutzeroberfläche.
"""

from enum import IntEnum
from typing import List, Optional, Tuple
from copy import deepcopy


class CellState(IntEnum):
    """Zustand einer Zelle im Nonogramm-Raster."""
    UNKNOWN = 0   # Noch nicht bestimmt
    FILLED = 1    # Ausgefüllt (schwarz)
    EMPTY = -1    # Leer / gekreuzt (weiss)


class NonogramModel:
    """
    Datenmodell eines Nonogramm-Puzzles.

    Attributes:
        rows: Anzahl Zeilen
        cols: Anzahl Spalten
        row_clues: Hinweiszahlen für jede Zeile
        col_clues: Hinweiszahlen für jede Spalte
        grid: 2D-Raster mit Zellzuständen
    """

    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.row_clues: List[List[int]] = [[] for _ in range(rows)]
        self.col_clues: List[List[int]] = [[] for _ in range(cols)]
        self.grid: List[List[int]] = [
            [CellState.UNKNOWN] * cols for _ in range(rows)
        ]

    def set_row_clues(self, row: int, clues: List[int]) -> None:
        """Setzt die Hinweiszahlen für eine bestimmte Zeile."""
        if 0 <= row < self.rows:
            self.row_clues[row] = clues if clues else [0]

    def set_col_clues(self, col: int, clues: List[int]) -> None:
        """Setzt die Hinweiszahlen für eine bestimmte Spalte."""
        if 0 <= col < self.cols:
            self.col_clues[col] = clues if clues else [0]

    def set_cell(self, row: int, col: int, state: int) -> None:
        """Setzt den Zustand einer einzelnen Zelle."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.grid[row][col] = state

    def get_cell(self, row: int, col: int) -> int:
        """Gibt den Zustand einer Zelle zurück."""
        return self.grid[row][col]

    def get_row(self, row: int) -> List[int]:
        """Gibt eine Kopie der Zeile zurück."""
        return list(self.grid[row])

    def get_col(self, col: int) -> List[int]:
        """Gibt eine Kopie der Spalte zurück."""
        return [self.grid[r][col] for r in range(self.rows)]

    def set_row(self, row: int, values: List[int]) -> None:
        """Setzt die gesamte Zeile."""
        for c in range(self.cols):
            self.grid[row][c] = values[c]

    def set_col(self, col: int, values: List[int]) -> None:
        """Setzt die gesamte Spalte."""
        for r in range(self.rows):
            self.grid[r][col] = values[r]

    def is_solved(self) -> bool:
        """Prüft ob alle Zellen bestimmt sind."""
        return all(
            self.grid[r][c] != CellState.UNKNOWN
            for r in range(self.rows)
            for c in range(self.cols)
        )

    def copy(self) -> "NonogramModel":
        """Erstellt eine tiefe Kopie des Modells."""
        new_model = NonogramModel(self.rows, self.cols)
        new_model.row_clues = deepcopy(self.row_clues)
        new_model.col_clues = deepcopy(self.col_clues)
        new_model.grid = deepcopy(self.grid)
        return new_model

    def validate_clues(self) -> Tuple[bool, str]:
        """
        Grundlegende Validierung der Hinweiszahlen.
        Gibt (True, "") zurück wenn gültig, sonst (False, Fehlermeldung).
        """
        for i, clues in enumerate(self.row_clues):
            if not clues:
                return False, f"Zeile {i + 1}: Keine Hinweiszahlen definiert."
            min_length = sum(clues) + len(clues) - 1 if clues != [0] else 0
            if min_length > self.cols:
                return False, (
                    f"Zeile {i + 1}: Hinweiszahlen {clues} passen nicht "
                    f"in {self.cols} Spalten."
                )

        for j, clues in enumerate(self.col_clues):
            if not clues:
                return False, f"Spalte {j + 1}: Keine Hinweiszahlen definiert."
            min_length = sum(clues) + len(clues) - 1 if clues != [0] else 0
            if min_length > self.rows:
                return False, (
                    f"Spalte {j + 1}: Hinweiszahlen {clues} passen nicht "
                    f"in {self.rows} Zeilen."
                )

        return True, ""

    def __repr__(self) -> str:
        symbols = {CellState.UNKNOWN: "?", CellState.FILLED: "█", CellState.EMPTY: "·"}
        lines = []
        for row in self.grid:
            lines.append(" ".join(symbols.get(c, "?") for c in row))
        return "\n".join(lines)
