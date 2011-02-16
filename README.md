# Nonogramm-Löser

Ein Python-Programm zum Lösen von Nonogrammen (auch bekannt als Picross, Griddlers oder Hanjie) mit grafischer Benutzeroberfläche und animierter Visualisierung des Lösungsalgorithmus.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Tkinter](https://img.shields.io/badge/UI-Tkinter-green)

---

## Was ist ein Nonogramm?

Ein Nonogramm ist ein Logikrätsel, bei dem ein Bild durch Ausfüllen von Zellen in einem Raster entsteht. Für jede Zeile und Spalte gibt es **Hinweiszahlen**, die angeben, wie viele zusammenhängende gefüllte Blöcke es gibt und wie lang diese sind.

**Beispiel:** Die Hinweiszahl `2 3` bedeutet: Es gibt einen Block von 2 gefüllten Zellen, dann mindestens eine leere Zelle, dann einen Block von 3 gefüllten Zellen.

---

## Starten

```bash
python main.py
```

**Voraussetzungen:** Python 3.10+ mit Tkinter (bei den meisten Python-Installationen bereits enthalten).

---

## Bedienung

### 1. Raster erstellen
- Anzahl **Zeilen** und **Spalten** eingeben (1–50)
- Auf **"Raster erstellen"** klicken

### 2. Hinweiszahlen eingeben
- **Zeilen-Hinweise** (links): Zahlen durch Leerzeichen getrennt, z.B. `1 3 2`
- **Spalten-Hinweise** (oben): Zahlen durch Leerzeichen getrennt, z.B. `4 1`
- `0` bedeutet: keine gefüllten Zellen in dieser Zeile/Spalte

### 3. Vorgaben setzen (optional)
- **Linksklick** auf eine Zelle: Zelle als **gefüllt** markieren (schwarz)
- **Rechtsklick** auf eine Zelle: Zelle als **leer** markieren (Kreuz)
- Erneuter Klick setzt die Zelle zurück

### 4. Lösen
- Auf **"▶ Lösen"** klicken
- Der Algorithmus löst das Puzzle schrittweise mit Animation
- Die **Geschwindigkeit** kann über den Regler angepasst werden (10–1000 ms pro Schritt)

### 5. Beispiel
- **"Beispiel laden"** lädt ein 5×5-Herz-Muster zum Ausprobieren

---

## Architektur

Das Projekt folgt einer klaren **Trennung von Algorithmus und Darstellung (MVC-Prinzip)**:

```
nonogramm/
├── main.py       # Einstiegspunkt – startet die Anwendung
├── model.py      # Datenmodell – Raster, Zellzustände, Hinweiszahlen
├── solver.py     # Algorithmus – Constraint-Propagation + Backtracking
├── ui.py         # Benutzeroberfläche – Tkinter-GUI mit Visualisierung
└── README.md     # Diese Dokumentation
```

| Modul       | Verantwortung                                    |
|-------------|--------------------------------------------------|
| `model.py`  | Datenstruktur des Puzzles, Validierung           |
| `solver.py` | Lösungsalgorithmus, komplett UI-unabhängig        |
| `ui.py`     | Eingabe, Darstellung, Animation                  |
| `main.py`   | Startet die Anwendung                            |

Der Solver kennt die UI nicht – er kommuniziert über eine **Callback-Funktion**, die bei jedem Lösungsschritt aufgerufen wird. So kann der Algorithmus auch ohne UI (z.B. als Bibliothek oder in Tests) verwendet werden.

---

## Algorithmus

Der Solver verwendet zwei Techniken in Kombination:

### 1. Constraint-Propagation (Haupttechnik)

Für jede Zeile und Spalte wird analysiert, welche Zellen **eindeutig bestimmt** sind:

1. **Alle gültigen Belegungen erzeugen:** Für eine Linie (Zeile oder Spalte) mit gegebenen Hinweiszahlen werden alle möglichen Anordnungen der Blöcke generiert, die mit den bereits bekannten Zellen kompatibel sind.

2. **Schnittmenge bilden:** Wenn eine Zelle in **allen** gültigen Belegungen den gleichen Wert hat, ist sie eindeutig bestimmt und wird festgelegt.

3. **Iterieren:** Durch das Festlegen neuer Zellen können sich für andere Zeilen/Spalten weitere Einschränkungen ergeben. Der Prozess wird wiederholt, bis sich nichts mehr ändert.

**Beispiel:**
```
Hinweiszahl: [3]    Linienlänge: 5

Mögliche Belegungen:
███··     Position 0-2
·███·     Position 1-3
··███     Position 2-4

Schnittmenge:
??█??     → Zelle 3 ist in allen Belegungen gefüllt!
```

### 2. Backtracking (Fallback)

Wenn die Constraint-Propagation allein das Puzzle nicht lösen kann (bei mehrdeutigen Puzzles):

1. Die **am stärksten eingeschränkte unbekannte Zelle** wird gewählt (Most Constrained Variable – Heuristik: Zelle mit den wenigsten Unbekannten in ihrer Zeile/Spalte).

2. Die Zelle wird versuchsweise als **GEFÜLLT** gesetzt und weitergelöst.

3. Führt das zu einem Widerspruch, wird sie als **LEER** gesetzt.

4. Der Prozess ist rekursiv und garantiert eine Lösung, falls eine existiert.

### Ablauf im Detail

```
┌─────────────────────────────┐
│   Hinweiszahlen validieren  │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  Constraint-Propagation     │◄──┐
│  (alle Zeilen & Spalten)    │   │
└──────────────┬──────────────┘   │
               ▼                  │
          Änderungen?  ──Ja──────►┘
               │ Nein
               ▼
          Gelöst?  ──Ja──► Fertig! ✓
               │ Nein
               ▼
┌─────────────────────────────┐
│  Backtracking:              │
│  1. Unbekannte Zelle wählen │
│  2. GEFÜLLT versuchen       │
│  3. Falls Widerspruch:      │
│     LEER versuchen          │
└─────────────────────────────┘
```

### Komplexität

- **Einfache Puzzles** (die meisten Zeitungsrätsel): Werden allein durch Constraint-Propagation gelöst – typisch in wenigen Millisekunden.
- **Schwierige Puzzles:** Benötigen Backtracking. Im Worst-Case exponentiell, aber durch die Propagation in der Praxis meist schnell.

---

## Visualisierung

Während der Lösung zeigt die Animation:

| Farbe         | Bedeutung                          |
|---------------|------------------------------------|
| ⬛ Schwarz     | Gefüllte Zelle                     |
| ✕ Kreuz (rot) | Leere Zelle                        |
| 🟨 Gelb        | Aktuell analysierte Zeile          |
| 🟦 Blau        | Aktuell analysierte Spalte         |
| ⬜ Grau        | Noch unbestimmte Zelle             |

Das **Lösungsprotokoll** unten zeigt jeden Schritt im Detail (welche Zeile/Spalte analysiert wurde, ob Backtracking nötig war, etc.).

---

## Beispiele

### 5×5 Herz (eingebaut)
```
Zeilen: 1 1 | 5 | 5 | 3 | 1
Spalten: 2 | 4 | 4 | 4 | 2

Lösung:
·█·█·
█████
█████
·███·
··█··
```

### 10×10 Anker
```
Zeilen: 2 | 4 | 2 | 2 | 10 | 2 | 2 | 2 | 2 | 4
Spalten: 1 | 3 | 1 1 | 1 1 | 1 5 | 1 5 | 1 1 | 1 1 | 3 | 1
```

---

## Technische Details

- **Sprache:** Python 3.10+
- **GUI:** Tkinter (Standard-Bibliothek, keine zusätzlichen Pakete nötig)
- **Threading:** Der Solver läuft in einem separaten Thread, damit die UI während der Animation flüssig bleibt
- **Callback-Pattern:** Der Solver kommuniziert Fortschritt über eine optionale Callback-Funktion – saubere Trennung von Logik und Darstellung
