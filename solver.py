"""
Nonogramm-Lösungsalgorithmus.

Verwendet Constraint-Propagation (Zeilenweise/Spaltenweise) kombiniert
mit Backtracking für schwierigere Puzzles.

Algorithmus-Übersicht:
1. Constraint-Propagation: Für jede Zeile/Spalte werden alle gültigen
   Belegungen erzeugt, die zu den Hinweiszahlen und bereits bekannten
   Zellen passen. Zellen, die in ALLEN gültigen Belegungen gleich sind,
   werden festgelegt.
2. Iteration: Schritt 1 wird wiederholt, bis sich nichts mehr ändert.
3. Backtracking: Falls das Puzzle noch nicht gelöst ist, wird eine
   unbekannte Zelle geraten und rekursiv weitergelöst.
"""

from typing import List, Optional, Callable, Tuple
from model import NonogramModel, CellState


# Typ für die Callback-Funktion zur Visualisierung
# callback(model, message, row_or_col_idx, is_row)
SolveCallback = Optional[Callable[[NonogramModel, str, int, bool], None]]


def generate_line_arrangements(clues: List[int], length: int,
                                current_line: List[int]) -> List[List[int]]:
    """
    Erzeugt alle gültigen Belegungen einer Zeile/Spalte, die mit den
    Hinweiszahlen und den bereits bekannten Zellen kompatibel sind.

    Args:
        clues: Hinweiszahlen für diese Linie
        length: Länge der Linie
        current_line: Aktueller Zustand der Linie

    Returns:
        Liste aller gültigen Belegungen (jede Belegung ist eine Liste
        aus FILLED/EMPTY)
    """
    if clues == [0]:
        # Keine Blöcke: Alle Zellen müssen leer sein
        arrangement = [CellState.EMPTY] * length
        if _is_compatible(arrangement, current_line):
            return [arrangement]
        return []

    results = []
    _generate_recursive(clues, 0, length, [], current_line, results)
    return results


def _generate_recursive(clues: List[int], clue_idx: int, length: int,
                         partial: List[int], current_line: List[int],
                         results: List[List[int]]) -> None:
    """Rekursive Hilfsfunktion zum Erzeugen aller Belegungen."""
    if clue_idx == len(clues):
        # Alle Blöcke platziert, Rest mit EMPTY auffüllen
        arrangement = partial + [CellState.EMPTY] * (length - len(partial))
        if _is_compatible(arrangement, current_line):
            results.append(arrangement)
        return

    block_size = clues[clue_idx]
    remaining_clues = clues[clue_idx + 1:]
    # Minimaler Platz den die restlichen Blöcke noch brauchen
    min_remaining = sum(remaining_clues) + len(remaining_clues)

    pos = len(partial)
    max_start = length - block_size - min_remaining

    for start in range(pos, max_start + 1):
        # Lücke vor dem Block mit EMPTY auffüllen
        gap = [CellState.EMPTY] * (start - pos)
        block = [CellState.FILLED] * block_size

        new_partial = partial + gap + block

        # Nach dem Block muss ein EMPTY kommen (Trenner), ausser am Ende
        if clue_idx < len(clues) - 1:
            new_partial.append(CellState.EMPTY)

        # Frühzeitig prüfen ob bisherige Belegung kompatibel ist
        if _is_compatible_partial(new_partial, current_line):
            _generate_recursive(clues, clue_idx + 1, length,
                                new_partial, current_line, results)


def _is_compatible(arrangement: List[int], current_line: List[int]) -> bool:
    """Prüft ob eine vollständige Belegung mit der aktuellen Linie kompatibel ist."""
    for i in range(len(arrangement)):
        if current_line[i] != CellState.UNKNOWN and current_line[i] != arrangement[i]:
            return False
    return True


def _is_compatible_partial(partial: List[int], current_line: List[int]) -> bool:
    """Prüft ob eine teilweise Belegung mit der aktuellen Linie kompatibel ist."""
    for i in range(len(partial)):
        if current_line[i] != CellState.UNKNOWN and current_line[i] != partial[i]:
            return False
    return True


def constrain_line(clues: List[int], current_line: List[int]) -> Optional[List[int]]:
    """
    Wendet Constraint-Propagation auf eine einzelne Linie an.

    Erzeugt alle gültigen Belegungen und bestimmt Zellen, die in
    allen Belegungen den gleichen Wert haben.

    Args:
        clues: Hinweiszahlen
        current_line: Aktueller Zustand der Linie

    Returns:
        Neuer Zustand der Linie, oder None wenn keine gültige
        Belegung existiert (Widerspruch).
    """
    length = len(current_line)
    arrangements = generate_line_arrangements(clues, length, current_line)

    if not arrangements:
        return None  # Widerspruch!

    # Schnittmenge aller Belegungen bilden
    new_line = list(current_line)
    for i in range(length):
        if new_line[i] != CellState.UNKNOWN:
            continue

        values = set(arr[i] for arr in arrangements)
        if len(values) == 1:
            new_line[i] = values.pop()

    return new_line


def propagate(model: NonogramModel,
              callback: SolveCallback = None) -> bool:
    """
    Führt iterative Constraint-Propagation durch.

    Wiederholt die Analyse aller Zeilen und Spalten bis sich nichts
    mehr verändert.

    Args:
        model: Das Nonogramm-Modell (wird in-place verändert)
        callback: Optionale Callback-Funktion für Visualisierung

    Returns:
        True wenn kein Widerspruch aufgetreten ist, False sonst.
    """
    changed = True
    iteration = 0

    while changed:
        changed = False
        iteration += 1

        # Alle Zeilen verarbeiten
        for r in range(model.rows):
            current = model.get_row(r)
            if CellState.UNKNOWN not in current:
                continue

            new_line = constrain_line(model.row_clues[r], current)

            if new_line is None:
                if callback:
                    callback(model, f"Widerspruch in Zeile {r + 1}!", r, True)
                return False

            if new_line != current:
                model.set_row(r, new_line)
                changed = True
                if callback:
                    callback(
                        model,
                        f"Iteration {iteration}: Zeile {r + 1} aktualisiert",
                        r, True
                    )

        # Alle Spalten verarbeiten
        for c in range(model.cols):
            current = model.get_col(c)
            if CellState.UNKNOWN not in current:
                continue

            new_line = constrain_line(model.col_clues[c], current)

            if new_line is None:
                if callback:
                    callback(model, f"Widerspruch in Spalte {c + 1}!", c, False)
                return False

            if new_line != current:
                model.set_col(c, new_line)
                changed = True
                if callback:
                    callback(
                        model,
                        f"Iteration {iteration}: Spalte {c + 1} aktualisiert",
                        c, False
                    )

    return True


# ─── Verfügbare Algorithmen ──────────────────────────────────────────────────

ALGORITHMS = {
    "CP + Backtracking": "Constraint-Propagation kombiniert mit Backtracking (Standard)",
    "Nur Constraint-Propagation": "Nur Constraint-Propagation, kein Backtracking",
    "Brute Force": "Reines Backtracking ohne Constraint-Propagation",
    "Zeile-für-Zeile": "Löst zeilenweise durch Aufzählung gültiger Belegungen",
}


def solve(model: NonogramModel,
          callback: SolveCallback = None,
          algorithm: str = "CP + Backtracking") -> bool:
    """
    Löst das Nonogramm mit dem gewählten Algorithmus.

    Args:
        model: Das Nonogramm-Modell (wird in-place verändert)
        callback: Optionale Callback-Funktion für Visualisierung
        algorithm: Name des Algorithmus (siehe ALGORITHMS)

    Returns:
        True wenn eine Lösung gefunden wurde, False sonst.
    """
    # Validierung
    valid, msg = model.validate_clues()
    if not valid:
        if callback:
            callback(model, f"Fehler: {msg}", -1, True)
        return False

    if callback:
        callback(model, f"Algorithmus: {algorithm}", -1, True)

    if algorithm == "CP + Backtracking":
        return _solve_cp_backtracking(model, callback)
    elif algorithm == "Nur Constraint-Propagation":
        return _solve_cp_only(model, callback)
    elif algorithm == "Brute Force":
        return _solve_brute_force(model, callback)
    elif algorithm == "Zeile-für-Zeile":
        return _solve_row_by_row(model, callback)
    else:
        return _solve_cp_backtracking(model, callback)


def _solve_cp_backtracking(model: NonogramModel,
                           callback: SolveCallback = None) -> bool:
    """
    Löst das Nonogramm mit Constraint-Propagation und Backtracking.
    """
    # Schritt 1: Constraint-Propagation
    if not propagate(model, callback):
        return False

    # Wenn gelöst, fertig
    if model.is_solved():
        if callback:
            callback(model, "Puzzle gelöst! ✓", -1, True)
        return True

    # Schritt 2: Backtracking - finde erste unbekannte Zelle
    target = _find_best_unknown(model)
    if target is None:
        return False

    row, col = target

    if callback:
        callback(
            model,
            f"Backtracking: Rate Zelle ({row + 1}, {col + 1})",
            row, True
        )

    # Versuch 1: Zelle als FILLED setzen
    model_copy = model.copy()
    model_copy.set_cell(row, col, CellState.FILLED)

    if callback:
        callback(
            model_copy,
            f"Versuch: Zelle ({row + 1}, {col + 1}) = GEFÜLLT",
            row, True
        )

    if _solve_cp_backtracking(model_copy, callback):
        # Lösung gefunden - übernehmen
        for r in range(model.rows):
            for c in range(model.cols):
                model.grid[r][c] = model_copy.grid[r][c]
        return True

    # Versuch 2: Zelle als EMPTY setzen
    model_copy = model.copy()
    model_copy.set_cell(row, col, CellState.EMPTY)

    if callback:
        callback(
            model_copy,
            f"Versuch: Zelle ({row + 1}, {col + 1}) = LEER",
            row, True
        )

    if _solve_cp_backtracking(model_copy, callback):
        # Lösung gefunden - übernehmen
        for r in range(model.rows):
            for c in range(model.cols):
                model.grid[r][c] = model_copy.grid[r][c]
        return True

    return False


def _solve_cp_only(model: NonogramModel,
                   callback: SolveCallback = None) -> bool:
    """
    Löst das Nonogramm nur mit Constraint-Propagation (kein Backtracking).
    Kann nicht alle Puzzles lösen, aber ist sehr schnell.
    """
    if not propagate(model, callback):
        return False

    if model.is_solved():
        if callback:
            callback(model, "Puzzle gelöst! ✓", -1, True)
        return True

    if callback:
        # Zähle verbleibende unbekannte Zellen
        unknown_count = sum(
            1 for r in range(model.rows) for c in range(model.cols)
            if model.grid[r][c] == CellState.UNKNOWN
        )
        callback(
            model,
            f"Constraint-Propagation abgeschlossen. "
            f"{unknown_count} Zellen bleiben unbestimmt. "
            f"Backtracking wäre nötig.",
            -1, True
        )
    return False


def _solve_brute_force(model: NonogramModel,
                       callback: SolveCallback = None) -> bool:
    """
    Löst das Nonogramm mit reinem Backtracking (ohne Constraint-Propagation).
    Langsamer, aber konzeptionell einfacher.
    """
    if model.is_solved():
        # Prüfe ob Lösung gültig ist
        if _validate_solution(model):
            if callback:
                callback(model, "Puzzle gelöst! ✓", -1, True)
            return True
        return False

    target = _find_first_unknown(model)
    if target is None:
        return _validate_solution(model)

    row, col = target

    for state, name in [(CellState.FILLED, "GEFÜLLT"), (CellState.EMPTY, "LEER")]:
        model.set_cell(row, col, state)

        if callback:
            callback(
                model,
                f"Brute Force: Zelle ({row + 1}, {col + 1}) = {name}",
                row, True
            )

        # Frühzeitige Prüfung: Sind die bisherigen Zeilen/Spalten noch möglich?
        if _is_consistent(model, row, col):
            if _solve_brute_force(model, callback):
                return True

    # Beide Optionen gescheitert - zurücksetzen
    model.set_cell(row, col, CellState.UNKNOWN)
    return False


def _solve_row_by_row(model: NonogramModel,
                      callback: SolveCallback = None) -> bool:
    """
    Löst das Nonogramm zeilenweise: Für jede Zeile werden alle gültigen
    Belegungen erzeugt und nacheinander versucht, geprüft ob die
    Spaltenbedingungen noch erfüllbar sind.
    """
    return _solve_row_recursive(model, 0, callback)


def _solve_row_recursive(model: NonogramModel, row: int,
                         callback: SolveCallback = None) -> bool:
    """Rekursiver Helfer für den Zeile-für-Zeile Algorithmus."""
    if row == model.rows:
        # Alle Zeilen platziert - Spalten prüfen
        if _validate_solution(model):
            if callback:
                callback(model, "Puzzle gelöst! ✓", -1, True)
            return True
        return False

    current = model.get_row(row)
    arrangements = generate_line_arrangements(
        model.row_clues[row], model.cols, [CellState.UNKNOWN] * model.cols
    )

    if callback:
        callback(
            model,
            f"Zeile {row + 1}: {len(arrangements)} mögliche Belegungen",
            row, True
        )

    for arr in arrangements:
        model.set_row(row, arr)

        if callback:
            callback(
                model,
                f"Zeile {row + 1}: Belegung testen",
                row, True
            )

        # Prüfe ob Spalten noch erfüllbar sind
        if _columns_still_feasible(model, row):
            if _solve_row_recursive(model, row + 1, callback):
                return True

    # Zeile zurücksetzen
    model.set_row(row, [CellState.UNKNOWN] * model.cols)
    return False


def _find_first_unknown(model: NonogramModel) -> Optional[Tuple[int, int]]:
    """Findet die erste unbekannte Zelle (links-oben nach rechts-unten)."""
    for r in range(model.rows):
        for c in range(model.cols):
            if model.grid[r][c] == CellState.UNKNOWN:
                return (r, c)
    return None


def _is_consistent(model: NonogramModel, row: int, col: int) -> bool:
    """
    Prüft ob die aktuelle Belegung der Zeile/Spalte einer Zelle
    noch konsistent mit den Hinweiszahlen ist.
    """
    # Zeile prüfen: Sind alle Zellen der Zeile bestimmt?
    row_line = model.get_row(row)
    if CellState.UNKNOWN not in row_line:
        if not _line_matches_clues(row_line, model.row_clues[row]):
            return False
    else:
        # Teilweise Prüfung: Maximal-Blöcke nicht überschritten?
        if not _partial_line_feasible(row_line, model.row_clues[row]):
            return False

    # Spalte prüfen
    col_line = model.get_col(col)
    if CellState.UNKNOWN not in col_line:
        if not _line_matches_clues(col_line, model.col_clues[col]):
            return False
    else:
        if not _partial_line_feasible(col_line, model.col_clues[col]):
            return False

    return True


def _line_matches_clues(line: List[int], clues: List[int]) -> bool:
    """Prüft ob eine vollständig bestimmte Linie den Hinweiszahlen entspricht."""
    # Blöcke zählen
    blocks = []
    count = 0
    for cell in line:
        if cell == CellState.FILLED:
            count += 1
        else:
            if count > 0:
                blocks.append(count)
                count = 0
    if count > 0:
        blocks.append(count)

    if not blocks:
        blocks = [0]

    return blocks == clues


def _partial_line_feasible(line: List[int], clues: List[int]) -> bool:
    """
    Prüft ob eine teilweise bestimmte Linie noch zu den Hinweiszahlen
    passen kann (einfache Prüfung).
    """
    arrangements = generate_line_arrangements(clues, len(line), line)
    return len(arrangements) > 0


def _validate_solution(model: NonogramModel) -> bool:
    """Prüft ob das gesamte Modell eine gültige Lösung ist."""
    for r in range(model.rows):
        line = model.get_row(r)
        if CellState.UNKNOWN in line:
            return False
        if not _line_matches_clues(line, model.row_clues[r]):
            return False

    for c in range(model.cols):
        line = model.get_col(c)
        if CellState.UNKNOWN in line:
            return False
        if not _line_matches_clues(line, model.col_clues[c]):
            return False

    return True


def _columns_still_feasible(model: NonogramModel, up_to_row: int) -> bool:
    """
    Prüft ob die Spalten bis zur gegebenen Zeile noch mit den
    Hinweiszahlen vereinbar sind.
    """
    for c in range(model.cols):
        partial_col = [model.grid[r][c] for r in range(up_to_row + 1)]
        remaining = model.rows - up_to_row - 1
        full_col = partial_col + [CellState.UNKNOWN] * remaining
        arrangements = generate_line_arrangements(
            model.col_clues[c], model.rows, full_col
        )
        if not arrangements:
            return False
    return True


def _find_best_unknown(model: NonogramModel) -> Optional[Tuple[int, int]]:
    """
    Findet die beste unbekannte Zelle für Backtracking.

    Wählt die Zelle, deren Zeile oder Spalte die wenigsten
    unbekannten Zellen hat (Most Constrained Variable Heuristik).
    """
    best = None
    best_score = float('inf')

    for r in range(model.rows):
        for c in range(model.cols):
            if model.grid[r][c] == CellState.UNKNOWN:
                # Zähle unbekannte Zellen in Zeile und Spalte
                row_unknowns = sum(
                    1 for v in model.get_row(r) if v == CellState.UNKNOWN
                )
                col_unknowns = sum(
                    1 for v in model.get_col(c) if v == CellState.UNKNOWN
                )
                score = min(row_unknowns, col_unknowns)

                if score < best_score:
                    best_score = score
                    best = (r, c)

    return best
