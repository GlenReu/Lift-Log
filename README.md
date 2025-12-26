# Lift Log

Eine umfassende Python-basierte Trainings-Tracking-App mit Streamlit, SQLite und fortgeschrittenen Analyse-Features.

## Features

### ✅ Implementierte Funktionen

1. **Übungsverwaltung**
   - Übungen erstellen, anzeigen und löschen
   - Beschreibungen und Metadaten speichern

2. **Training Session Interface**
   - Sets mit Gewicht, Wiederholungen, RPE und Notizen eintragen
   - Live-Verfolgung der aktuellen Trainingseinheit
   - Automatische Set-Nummerierung

3. **Rest Timer**
   - Konfigurierbarer Countdown-Timer (30-300 Sekunden)
   - Visuelle Progress-Bar
   - Automatischer Start nach Set-Eingabe

4. **Progressive Overload Algorithmus**
   - Intelligente Vorschläge für das nächste Top-Set
   - RPE-basierte Progression:
     - RPE ≤ 7: +2.5kg
     - RPE 7.5-8.5: +1.25kg oder +1 Rep
     - RPE ≥ 9: +1 Rep
   - Geschätzte 1RM-Berechnung (Epley-Formel mit RPE-Korrektur)

5. **Visualisierungen**
   - Gewicht über die Zeit (Liniendiagramm)
   - Wiederholungen vs. Gewicht (Scatter-Plot mit RPE-Farbcodierung)
   - Volumen-Entwicklung (Balkendiagramm)

6. **Projektion**
   - Geschätzte Anzahl Trainingseinheiten bis zum Zielgewicht
   - Konfigurierbare durchschnittliche Progression
   - Zeitprojektion (Wochen bei 2-3x Training/Woche)
   - Visuelle Darstellung des projizierten Fortschritts

7. **CSV-Export**
   - Export aller Übungen oder spezifischer Übungen
   - Download-Button für CSV-Datei
   - Vollständige Trainingsdaten mit Metadaten

8. **SQLite-Datenbank**
   - Drei Tabellen: exercises, workouts, sets
   - Referentielle Integrität mit Foreign Keys
   - Cascade Delete für saubere Datenbereinigung

## Installation

### Voraussetzungen
- Python 3.8 oder höher

### Setup

1. Navigiere zum Projektverzeichnis:
```bash
cd /Users/glen/Documents/Python/Tracker
```

2. Installiere die Abhängigkeiten:
```bash
pip install -r requirements.txt
```

## Verwendung

### App starten

```bash
streamlit run app.py
```

Die App öffnet sich automatisch in deinem Browser unter `http://localhost:8501`

### Workflow

1. **Übungen einrichten**
   - Gehe zu "📊 Übungen verwalten"
   - Füge deine Übungen hinzu (z.B. Bankdrücken, Kniebeugen, Kreuzheben)

2. **Training starten**
   - Gehe zu "🏋️ Training starten"
   - Wähle eine Übung
   - Schaue dir den Vorschlag für dein nächstes Top-Set an
   - Starte eine neue Trainingseinheit
   - Trage deine Sets ein (Gewicht, Reps, RPE, Notizen)
   - Nutze den Rest-Timer zwischen den Sets

3. **Fortschritt analysieren**
   - Gehe zu "📈 Statistiken & Analyse"
   - Wähle eine Übung
   - Betrachte deine Fortschritts-Trends
   - Visualisiere Gewicht, Reps und Volumen über die Zeit
   - Setze ein Zielgewicht und schaue dir die Projektion an

4. **Daten exportieren**
   - Gehe zu "💾 Export"
   - Wähle eine oder alle Übungen
   - Lade die CSV-Datei herunter

## Projektstruktur

```
Tracker/
├── app.py              # Haupt-Streamlit-App
├── database.py         # Datenbankverwaltung und CRUD-Operationen
├── utils.py            # Hilfsfunktionen und Algorithmen
├── requirements.txt    # Python-Abhängigkeiten
├── README.md          # Diese Datei
└── training.db        # SQLite-Datenbank (wird automatisch erstellt)
```

## Datenbank-Schema

### exercises
- `id`: INTEGER PRIMARY KEY
- `name`: TEXT (UNIQUE)
- `description`: TEXT
- `created_at`: TIMESTAMP

### workouts
- `id`: INTEGER PRIMARY KEY
- `exercise_id`: INTEGER (Foreign Key)
- `date`: TIMESTAMP

### sets
- `id`: INTEGER PRIMARY KEY
- `workout_id`: INTEGER (Foreign Key)
- `set_number`: INTEGER
- `weight`: REAL
- `reps`: INTEGER
- `rpe`: REAL (optional)
- `notes`: TEXT
- `created_at`: TIMESTAMP

## Technologie-Stack

- **Frontend**: Streamlit 1.31.0
- **Datenbank**: SQLite3
- **Datenverarbeitung**: Pandas 2.2.0
- **Visualisierung**: Plotly 5.18.0
- **Backend**: Python 3.x

## Algorithmen

### Progressive Overload
Der Algorithmus berücksichtigt RPE (Rate of Perceived Exertion) für intelligente Gewichtssteigerung:
- Niedriges RPE (≤7): Deutliche Steigerung möglich
- Moderates RPE (7.5-8.5): Kleine Steigerung oder mehr Reps
- Hohes RPE (≥9): Nur Wiederholungen erhöhen

### 1RM-Schätzung
Verwendet die Epley-Formel mit RPE-Anpassung:
```
1RM = Gewicht × (1 + (Reps + RIR) / 30)
```
wobei RIR (Reps in Reserve) = 10 - RPE

### Projektion
Lineare Projektion basierend auf durchschnittlicher Gewichtssteigerung pro Session.

## Tipps

- **RPE verwenden**: Trage immer dein RPE ein für bessere Vorschläge
- **Regelmäßig tracken**: Je mehr Daten, desto besser die Analysen
- **Ziele setzen**: Nutze die Projektions-Funktion zur Motivation
- **Timer nutzen**: Konsistente Pausenzeiten verbessern die Vergleichbarkeit

## Erweiterungsmöglichkeiten

- Multi-User-Support
- Mobile App (React Native)
- Cloud-Synchronisation
- Trainingspläne und Templates
- Bodyweight-Tracking
- Deload-Wochen automatisch erkennen
- Social Features (teilen, vergleichen)

## Lizenz

Dieses Projekt wurde für Bildungszwecke erstellt.
