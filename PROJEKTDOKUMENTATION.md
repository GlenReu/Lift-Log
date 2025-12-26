# Lift Log - Projektdokumentation

**Projekt:** Intelligente Trainings-Tracking App mit Progressive Overload Algorithmus
**Entwickler:** Glen Reumann
**Zeitraum:** Dezember 2024
**Technologie-Stack:** Python, Streamlit, PostgreSQL/SQLite, Pandas, Plotly

---

## Inhaltsverzeichnis

1. [Projektübersicht](#projektübersicht)
2. [Features & Funktionalität](#features--funktionalität)
3. [Technische Architektur](#technische-architektur)
4. [Progressive Overload Algorithmus](#progressive-overload-algorithmus)
5. [Entwicklungsiterationen](#entwicklungsiterationen)
6. [Deployment-Optionen](#deployment-optionen)
7. [Datenbank-Design](#datenbank-design)
8. [Mobile Optimierungen](#mobile-optimierungen)

---

## Projektübersicht

### Problemstellung

Beim Krafttraining ist die **Progressive Overload** (kontinuierliche Steigerung der Belastung) der wichtigste Faktor für Muskelaufbau. Bestehende Apps bieten entweder:
- Keine intelligenten Empfehlungen
- Zu simple Algorithmen (z.B. nur +2.5kg)
- Keine Berücksichtigung von RPE (Rate of Perceived Exertion)

### Lösung

Eine intelligente Training-Tracking App die:
- Trainingsfortschritt automatisch analysiert
- Wissenschaftlich fundierte Gewichtsempfehlungen gibt
- RPE-basierte Progression nutzt
- Mobile-optimiert für einfache Nutzung im Gym ist

### Zielgruppe

- Kraftsportler die systematisch trainieren
- Athleten die progressive Overload anwenden
- Nutzer die ihre Trainingshistorie analysieren möchten

---

## Features & Funktionalität

### 1. Training Logging

**Funktion:** Erfassung einzelner Trainingssets

**Features:**
- Set-Nummer, Gewicht, Wiederholungen
- RPE-Rating (6.0-10.0 Skala)
- Notizen zu jedem Set
- Pausentimer zwischen Sets
- Session-basierte Target-Berechnung

**Technische Umsetzung:**
- Streamlit Session State für temporäre Speicherung
- Echtzeit-Berechnung der e1RM (Estimated 1 Rep Max)
- Automatische Speicherung in Datenbank

### 2. Intelligente Gewichtsempfehlung

**Funktion:** KI-gestützte Berechnung des optimalen Trainingsgewichts

**Algorithmus-Grundlage:**
- Gewichteter Durchschnitt der letzten 3 Sessions (50% / 30% / 20%)
- RPE-basierte Progression:
  - RPE ≤7.0: +2.0-2.5% Steigerung
  - RPE 7.5-8.5: +1.0-1.5% Steigerung
  - RPE 8.5-9.25: Halten (0%)
  - RPE ≥9.5: -1.5% Deload
- Rep-Range Safety Rule: Bei niedrigen Reps max. +1%
- Berücksichtigung des weight_increment (2.5kg/1.25kg)

**Besonderheiten:**
- Session-basiert (nicht per-Set)
- Verhindert zu aggressive Progression
- Automatischer Deload bei Übertraining

### 3. Trainingspläne

**Funktion:** Organisation von Übungen in Plänen

**Features:**
- Erstellung mehrerer Pläne (Push/Pull/Legs, etc.)
- Übungen zu Plänen hinzufügen (bestehende oder neue)
- Sortierung per Drag & Drop
- Plan-basiertes Training starten

**Use Case:**
```
Plan: "Push Day"
├── Bankdrücken (Compound, 5-8 Reps, 3 Sets)
├── Schulterdrücken (Compound, 8-12 Reps, 3 Sets)
└── Trizeps Extensions (Isolation, 10-15 Reps, 3 Sets)
```

### 4. Übungsverwaltung

**Funktion:** CRUD-Operationen für Übungen

**Übungsparameter:**
- Name & Beschreibung
- Typ: Compound / Isolation / Machine
- Rep-Range: Min-Max (z.B. 5-12)
- Gewichts-Inkrement: 2.5kg oder 1.25kg
- Pausendauer: 60-300 Sekunden
- Ziel-Sets pro Training

**Technische Umsetzung:**
- Zentrale exercises-Tabelle
- Verknüpfung zu training_plans über Junction Table
- Unique Constraint auf exercise_name

### 5. Statistiken & Analysen

**Funktion:** Visualisierung des Trainingsfortschritts

**Visualisierungen:**
- **Gewichtsverlauf:** Line Chart über Zeit
- **Volumen-Analyse:** Gewicht × Reps × Sets
- **RPE-Tracking:** Durchschnittliche Belastung
- **e1RM-Progression:** Geschätzte 1RM über Zeit
- **Set-Konsistenz:** Analyse der Set-Qualität

**Technologie:**
- Plotly für interaktive Charts
- Pandas für Datenverarbeitung
- Aggregation über Workouts

### 6. Export-Funktion

**Funktion:** Datenexport für externe Analyse

**Formate:**
- CSV-Export aller Trainings
- Exercise-spezifischer Export
- Kompletter Datenbank-Dump

---

## Technische Architektur

### Stack-Übersicht

```
Frontend:    Streamlit (Python Web Framework)
Backend:     Python 3.11+
Datenbank:   PostgreSQL (Production) / SQLite (Development)
Deployment:  Render.com (Cloud) / Raspberry Pi (Self-hosted)
Analytics:   Pandas, Plotly
```

### Projekt-Struktur

```
Lift-Log/
├── app.py                      # Main Streamlit Application
├── database.py                 # Database Layer (ORM)
├── utils.py                    # Progressive Overload Algorithmus
├── requirements.txt            # Python Dependencies
├── icon.png / icon.svg         # App Icons
├── SUPABASE_SETUP.md          # Supabase Setup Guide
├── POSTGRES_SETUP.md          # PostgreSQL Setup Guide
└── PROJEKTDOKUMENTATION.md    # Diese Datei
```

### Datenbankschema

**Tabellen:**

1. **exercises** - Übungsdefinitionen
   ```sql
   id: SERIAL PRIMARY KEY
   name: TEXT UNIQUE
   description: TEXT
   rep_range_min: INTEGER (Default: 5)
   rep_range_max: INTEGER (Default: 12)
   weight_increment: REAL (Default: 1.25)
   pause_duration: INTEGER (Default: 180)
   exercise_type: TEXT (compound/isolation/machine)
   target_sets: INTEGER (Default: 3)
   ```

2. **training_plans** - Trainingspläne
   ```sql
   id: SERIAL PRIMARY KEY
   name: TEXT UNIQUE
   description: TEXT
   created_at: TIMESTAMP
   ```

3. **training_plan_exercises** - Junction Table
   ```sql
   id: SERIAL PRIMARY KEY
   training_plan_id: INTEGER FK
   exercise_id: INTEGER FK
   order_index: INTEGER
   UNIQUE(training_plan_id, exercise_id)
   ```

4. **workouts** - Trainingseinheiten
   ```sql
   id: SERIAL PRIMARY KEY
   exercise_id: INTEGER FK
   training_plan_id: INTEGER FK (optional)
   date: TIMESTAMP
   ```

5. **sets** - Einzelne Sets
   ```sql
   id: SERIAL PRIMARY KEY
   workout_id: INTEGER FK
   set_number: INTEGER
   weight: REAL
   reps: INTEGER
   rpe: REAL (6.0-10.0)
   notes: TEXT
   created_at: TIMESTAMP
   ```

### Dual-Database Support

**Problem:** Render.com Free Tier löscht Daten nach Neustart

**Lösung:** Automatische Datenbank-Erkennung

```python
# Auto-detect PostgreSQL via DATABASE_URL
database_url = os.environ.get('DATABASE_URL')
is_postgres = database_url is not None

if is_postgres:
    # Production: Use PostgreSQL
    conn = psycopg2.connect(database_url)
else:
    # Development: Use SQLite
    conn = sqlite3.connect('training.db')
```

**Query-Konvertierung:**
- SQLite `?` → PostgreSQL `%s`
- SQLite `INTEGER PRIMARY KEY AUTOINCREMENT` → PostgreSQL `SERIAL PRIMARY KEY`
- SQLite `INSERT OR IGNORE` → PostgreSQL `INSERT ... ON CONFLICT DO NOTHING`
- SQLite `cursor.lastrowid` → PostgreSQL `RETURNING id`

---

## Progressive Overload Algorithmus

### Wissenschaftliche Grundlage

Der Algorithmus basiert auf:
- **Periodization Theory** (Bompa & Haff, 2009)
- **RPE-basiertes Training** (Zourdos et al., 2016)
- **Autoregulation Principles** (Mann et al., 2010)

### Implementierung

**Datei:** `utils.py` → `calculate_session_target()`

**Workflow:**

```python
def calculate_session_target(last_sessions, exercise_info):
    # 1. Gewichtete Session-Analyse (50% / 30% / 20%)
    weights = [0.5, 0.3, 0.2]

    # 2. Gewichteten Durchschnitts-RPE berechnen
    weighted_rpe = sum(s['rpe'] * w for s, w in zip(sessions, weights))

    # 3. Rep-Position prüfen (upper/lower half of range)
    rep_position = analyze_rep_range_position(last_session)

    # 4. Progression basierend auf RPE
    if weighted_rpe <= 7.0:
        progression = 2.0 if upper_half else 2.5  # Aggressive
    elif 7.0 < weighted_rpe <= 8.5:
        progression = 1.5 if upper_half else 1.0  # Moderat
    elif 8.5 < weighted_rpe < 9.25:
        progression = 0.0  # Halten
    else:  # >= 9.25
        progression = -1.5  # Deload

    # 5. Safety Rule: Max +1% wenn in lower half
    if in_lower_half and progression > 0:
        progression = min(progression, 1.0)

    # 6. Gewicht runden auf weight_increment
    new_weight = round_to_increment(
        last_weight * (1 + progression/100),
        weight_increment
    )

    return {
        'weight': new_weight,
        'reps': target_reps,
        'progression_percent': progression,
        'weighted_rpe': weighted_rpe
    }
```

### Beispiel-Berechnung

**Ausgangsdaten:**
- Session 1 (neueste): 100kg × 6 Reps @ RPE 8.5
- Session 2: 97.5kg × 8 Reps @ RPE 8.0
- Session 3 (älteste): 95kg × 7 Reps @ RPE 7.5
- Rep-Range: 5-12
- Weight Increment: 2.5kg

**Berechnung:**
```
1. Gewichteter RPE:
   RPE = 8.5×0.5 + 8.0×0.3 + 7.5×0.2 = 8.15

2. Progression:
   8.15 liegt in [7.5-8.5] → +1.0-1.5%
   Letzte Session: 6 Reps (lower half von 5-12) → +1.0%

3. Neues Gewicht:
   100kg × 1.01 = 101kg
   Gerundet auf 2.5kg → 100kg (kein Increment möglich)

4. Empfehlung: "Versuch 100kg mit mehr Reps zu schaffen"
```

### Vorteile des Algorithmus

✅ **Wissenschaftlich fundiert** - Basiert auf Studien
✅ **Individuell anpassbar** - Berücksichtigt persönliche RPE
✅ **Sicher** - Verhindert zu schnelle Progression
✅ **Autoregulativ** - Passt sich an Tagesform an
✅ **Deload-Erkennung** - Automatische Entlastungsphasen

---

## Entwicklungsiterationen

### Version 1.0 - MVP (Minimum Viable Product)

**Features:**
- Basic Exercise Logging
- Simple Statistiken
- SQLite Datenbank
- Lokales Deployment

**Probleme:**
- Keine intelligenten Empfehlungen
- Kein Progressive Overload
- Nur Desktop-fähig

### Version 2.0 - Progressive Overload

**Neue Features:**
- ✅ RPE-basierter Algorithmus
- ✅ Gewichteter 3-Session-Durchschnitt
- ✅ Rep-Range Safety Rule
- ✅ Automatischer Deload

**Verbesserungen:**
- Wissenschaftlich fundierte Empfehlungen
- Session-basierte Targets (nicht per-Set)

### Version 3.0 - Trainingspläne & Übungsverwaltung

**Neue Features:**
- ✅ Trainingspläne (Push/Pull/Legs)
- ✅ Übungsdatenbank mit CRUD
- ✅ Exercise Types (Compound/Isolation/Machine)
- ✅ Übungen zu Plänen hinzufügen

**Verbesserungen:**
- Bessere Organisation
- Wiederverwendbare Übungen
- Plan-basiertes Training

### Version 4.0 - Mobile & Deployment

**Neue Features:**
- ✅ Mobile-optimiertes UI
- ✅ iPhone PWA Support
- ✅ Apple Touch Icon
- ✅ Render.com Deployment
- ✅ GitHub Integration

**Verbesserungen:**
- Responsive Design
- Touch-friendly Buttons (48px)
- Auto-collapse Sidebar
- CSS Media Queries

### Version 5.0 - PostgreSQL Migration

**Neue Features:**
- ✅ Dual-Database Support (PostgreSQL + SQLite)
- ✅ Auto-Detection via DATABASE_URL
- ✅ Supabase Integration
- ✅ Persistente Datenspeicherung

**Technische Verbesserungen:**
- Query-Konvertierung (SQLite ↔ PostgreSQL)
- Environment-basierte Config
- Production-ready Deployment

### Version 5.1 - Self-Hosting (Aktuell)

**Neue Features:**
- ✅ Raspberry Pi Support
- ✅ Cloud-init Configuration
- ✅ Raspberry Pi Connect Integration
- ✅ Lokales Hosting

**Deployment-Optionen:**
- Cloud: Render.com + Supabase
- Self-hosted: Raspberry Pi + SQLite

---

## Deployment-Optionen

### Option 1: Render.com (Cloud) ⭐ Empfohlen

**Stack:**
- **Web Service:** Render.com Free Tier
- **Datenbank:** Supabase PostgreSQL (dauerhaft kostenlos)

**Vorteile:**
- ✅ Dauerhaft kostenlos
- ✅ Automatische Backups (Supabase)
- ✅ Von überall erreichbar
- ✅ Kein Hardware-Setup
- ✅ Auto-Deploy via GitHub

**Setup:**
1. GitHub Repository erstellen
2. Render.com Web Service anlegen
3. Supabase PostgreSQL erstellen
4. DATABASE_URL in Render Environment setzen

**Dokumentation:** `SUPABASE_SETUP.md`

### Option 2: Raspberry Pi (Self-Hosted)

**Stack:**
- **Hardware:** Raspberry Pi 4/5
- **OS:** Raspberry Pi OS Lite (64-bit)
- **Datenbank:** SQLite (lokal)
- **Remote Access:** Raspberry Pi Connect

**Vorteile:**
- ✅ Vollständige Kontrolle
- ✅ Keine Cloud-Abhängigkeit
- ✅ Daten bleiben lokal
- ✅ Lerneffekt

**Setup:**
1. Raspberry Pi OS flashen
2. WLAN/Ethernet konfigurieren
3. Git Repository klonen
4. Dependencies installieren
5. Streamlit Server starten

**Dokumentation:** `DEPLOYMENT.md`

### Option 3: Lokal (Development)

**Stack:**
- **OS:** macOS / Linux / Windows
- **Datenbank:** SQLite
- **Server:** Streamlit Development Server

**Vorteile:**
- ✅ Sofort einsatzbereit
- ✅ Kein Setup nötig
- ✅ Perfekt zum Testen

**Setup:**
```bash
git clone https://github.com/GlenReu/Lift-Log.git
cd Lift-Log
pip install -r requirements.txt
streamlit run app.py
```

---

## Datenbank-Design

### Design-Entscheidungen

**1. Normalisierung**

Datenbank ist in **3. Normalform (3NF):**
- ✅ Keine wiederholenden Gruppen
- ✅ Alle Attribute abhängig vom Primärschlüssel
- ✅ Keine transitiven Abhängigkeiten

**Beispiel:**
```
❌ SCHLECHT: training_sessions
   - id, exercise_name, exercise_type, weight, reps
   (exercise_type hängt transitiv von exercise_name ab)

✅ GUT: workouts + exercises
   workouts: id, exercise_id, date
   exercises: id, name, type
```

**2. Foreign Keys & Cascading**

```sql
-- Workout wird gelöscht → Sets werden automatisch gelöscht
FOREIGN KEY (workout_id) REFERENCES workouts(id) ON DELETE CASCADE

-- Plan wird gelöscht → Verknüpfungen werden gelöscht
FOREIGN KEY (training_plan_id) REFERENCES training_plans(id) ON DELETE CASCADE

-- Übung wird gelöscht → Was passiert?
FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE
```

**3. Indexes**

```sql
-- Schnelle Abfragen
CREATE INDEX idx_workouts_exercise ON workouts(exercise_id);
CREATE INDEX idx_sets_workout ON sets(workout_id);
CREATE INDEX idx_workouts_date ON workouts(date);
```

**4. Unique Constraints**

```sql
-- Eine Übung pro Plan nur einmal
UNIQUE(training_plan_id, exercise_id)

-- Exercise Namen müssen unique sein
UNIQUE(name)
```

### Migrations-System

**Problem:** Schema ändert sich über Zeit

**Lösung:** `ALTER TABLE` Migrations beim Start

```python
def init_database():
    # Tabellen erstellen
    cursor.execute("CREATE TABLE IF NOT EXISTS exercises ...")

    # Migrations: Neue Spalten hinzufügen
    if not column_exists('exercises', 'weight_increment'):
        cursor.execute(
            "ALTER TABLE exercises ADD COLUMN weight_increment REAL DEFAULT 1.25"
        )
```

**Vorteil:** Bestehende Datenbanken werden automatisch geupdatet

---

## Mobile Optimierungen

### Responsive Design

**Problem:** Streamlit ist Desktop-first

**Lösung:** CSS Media Queries

```css
@media (max-width: 768px) {
    /* Touch-friendly Buttons */
    .stButton > button {
        min-height: 48px !important;
        font-size: 16px !important;
        padding: 12px 20px !important;
    }

    /* Größere Input-Felder */
    .stTextInput input,
    .stNumberInput input {
        font-size: 16px !important;
        min-height: 48px !important;
    }

    /* Keine Zoom-Probleme */
    input, select, textarea {
        font-size: 16px !important;
    }
}
```

### Layout-Änderungen

**Vorher:** `layout="wide"` (Desktop-optimiert)
**Nachher:** `layout="centered"` (Mobile-optimiert)

**Sidebar:**
- Desktop: Immer sichtbar
- Mobile: Auto-collapse (`initial_sidebar_state="auto"`)

### PWA-Features (Progressive Web App)

**Apple Touch Icon:**
```html
<link rel="apple-touch-icon" href="data:image/png;base64,...">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="apple-mobile-web-app-title" content="Lift Log">
```

**Icon-Generierung:**
- SVG-Design mit Waldgrün-Farben
- Export als 180×180 PNG
- Base64-Encoding für Embedding

---

## Technologie-Entscheidungen

### Warum Streamlit?

**Vorteile:**
✅ Schnelle Entwicklung (Pure Python)
✅ Integrierte UI-Komponenten
✅ Automatisches Reloading
✅ Session State Management
✅ Einfaches Deployment

**Nachteile:**
❌ Limitierte CSS-Kontrolle
❌ Kein echtes Routing
❌ Performance bei vielen Widgets

**Fazit:** Perfekt für Data-Apps und MVP

### Warum PostgreSQL + SQLite?

**Dual-Support Begründung:**

**PostgreSQL (Production):**
- ✅ Production-ready
- ✅ ACID-Compliance
- ✅ Skalierbar
- ✅ Cloud-freundlich

**SQLite (Development):**
- ✅ Zero-Config
- ✅ File-based
- ✅ Perfekt für lokales Testen
- ✅ Kein Server nötig

**Implementierung:** Automatische Erkennung via `DATABASE_URL`

### Warum Pandas & Plotly?

**Pandas:**
- Datenverarbeitung & Aggregation
- CSV Export
- DataFrame Operations

**Plotly:**
- Interaktive Charts
- Zoom, Pan, Hover
- Mobile-freundlich
- Schönes Design

**Alternative:** Matplotlib (statisch, weniger Features)

---

## Testing & Quality Assurance

### Manuelle Tests

**Testszenarien:**

1. **Training Logging:**
   - [ ] Set hinzufügen
   - [ ] RPE eingeben
   - [ ] Notizen speichern
   - [ ] Training abschließen

2. **Progressive Overload:**
   - [ ] Erste Session → Basis-Gewicht
   - [ ] Zweite Session → Progression berechnet
   - [ ] Hohe RPE → Deload-Empfehlung
   - [ ] Niedrige RPE → Aggressive Progression

3. **Trainingspläne:**
   - [ ] Plan erstellen
   - [ ] Übung hinzufügen
   - [ ] Reihenfolge ändern
   - [ ] Plan löschen

4. **Mobile:**
   - [ ] iPhone Safari Test
   - [ ] Touch-Targets > 48px
   - [ ] Kein Auto-Zoom
   - [ ] Sidebar Auto-Collapse

5. **Datenbank:**
   - [ ] SQLite lokal funktioniert
   - [ ] PostgreSQL auf Render funktioniert
   - [ ] Migrations laufen durch
   - [ ] Daten persistieren

### Edge Cases

**Behandelte Fälle:**
- ✅ Keine vorherigen Sessions → Default-Gewicht
- ✅ Nur 1-2 Sessions → Gewichtung angepasst
- ✅ RPE fehlt → Warnung anzeigen
- ✅ Division by Zero → Try-Catch
- ✅ Leere Datenbank → Initialisierung

---

## Lessons Learned

### Technische Learnings

**1. Streamlit State Management ist tricky**
- Problem: State geht bei Rerun verloren
- Lösung: `st.session_state` für Persistenz

**2. SQLite ≠ PostgreSQL**
- Problem: Query-Syntax unterschiedlich
- Lösung: Abstraktions-Layer mit Auto-Konvertierung

**3. Mobile CSS ist komplex**
- Problem: iOS Safari ignoriert manche CSS-Regeln
- Lösung: `!important` + Apple-spezifische Meta-Tags

**4. Free Tier Limitierungen**
- Problem: Render.com löscht Daten
- Lösung: Externe PostgreSQL (Supabase)

### Design Learnings

**1. Keep It Simple**
- Weniger Features, bessere UX
- Progressive Disclosure statt alles auf einmal

**2. Mobile First**
- Erst Mobile designen, dann Desktop erweitern
- Touch-Targets mindestens 48×48px

**3. Data Visualization**
- Interaktive Charts > Statische Bilder
- Weniger ist mehr bei Dashboards

---

## Zukünftige Features (Roadmap)

### Version 6.0 (Geplant)

**Features:**
- [ ] Multi-User Support (Login/Authentifizierung)
- [ ] Öffentliche Workout-Sharing
- [ ] Export zu TrainAsOne / MyFitnessPal
- [ ] Ernährungstracking-Integration

**Technisch:**
- [ ] REST API für Mobile Apps
- [ ] WebSocket für Echtzeit-Updates
- [ ] Caching-Layer (Redis)

### Version 7.0 (Vision)

**Features:**
- [ ] KI-Injury Prediction
- [ ] Form-Check via Video-Upload
- [ ] Community-Features (Leaderboards)
- [ ] Personal Trainer Chat-Bot

---

## Fazit

### Projekterfolg

**Ziele erreicht:**
- ✅ Intelligente Progressive Overload Empfehlungen
- ✅ Mobile-optimierte Nutzung
- ✅ Cloud & Self-hosted Deployment
- ✅ Wissenschaftlich fundierter Algorithmus
- ✅ Production-ready Code

**Technische Highlights:**
- Dual-Database Support (PostgreSQL/SQLite)
- Session-basierter Algorithmus
- RPE-integrierte Progression
- Mobile PWA Features

### Persönliches Learning

**Skills entwickelt:**
- Python Backend-Entwicklung
- Datenbank-Design & Migrations
- Mobile-first CSS
- Cloud Deployment (Render, Supabase)
- Git Workflow & Version Control

**Verbesserungspotenzial:**
- Testing-Framework (pytest)
- CI/CD Pipeline
- Type Hints (mypy)
- Code Documentation (Sphinx)

---

## Ressourcen

### Code Repository
- **GitHub:** https://github.com/GlenReu/Lift-Log

### Deployment
- **Live App:** https://lift-log.onrender.com
- **Supabase Dashboard:** https://supabase.com/dashboard

### Dokumentation
- `README.md` - Projekt-Übersicht
- `SUPABASE_SETUP.md` - Datenbank Setup
- `DEPLOYMENT.md` - Self-Hosting Guide
- `PROJEKTDOKUMENTATION.md` - Diese Datei

### Dependencies
```txt
streamlit>=1.31.0
pandas>=2.2.0
plotly>=5.18.0
psycopg2-binary>=2.9.9
```

---

**Projekt-Status:** ✅ Production-Ready
**Letzte Aktualisierung:** 26. Dezember 2024
**Lizenz:** MIT
