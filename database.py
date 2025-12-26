import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd

# PostgreSQL Support
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False


class TrainingDatabase:
    """Verwaltet alle Datenbankoperationen für die Training-App"""

    def __init__(self, db_path: str = "training.db"):
        self.db_path = db_path
        # Check if we should use PostgreSQL (on Render.com) or SQLite (local)
        self.database_url = os.environ.get('DATABASE_URL')
        self.is_postgres = self.database_url is not None and HAS_POSTGRES
        self.init_database()

    def get_connection(self):
        """Erstellt eine neue Datenbankverbindung (PostgreSQL oder SQLite)"""
        if self.is_postgres:
            # PostgreSQL connection
            conn = psycopg2.connect(self.database_url)
            return conn
        else:
            # SQLite connection
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn

    def _cursor(self, conn):
        """Helper to get cursor with proper dict factory"""
        if self.is_postgres:
            return conn.cursor(cursor_factory=RealDictCursor)
        else:
            return conn.cursor()

    def _get_pk_type(self):
        """Returns PRIMARY KEY type based on database"""
        return "SERIAL PRIMARY KEY" if self.is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"

    def _get_real_type(self):
        """Returns REAL/FLOAT type based on database"""
        return "REAL" if not self.is_postgres else "REAL"

    def _convert_query(self, query: str) -> str:
        """Converts SQLite query to PostgreSQL if needed"""
        if not self.is_postgres:
            return query

        # Replace ? placeholders with %s for PostgreSQL
        converted = query.replace('?', '%s')

        # Replace INSERT OR IGNORE with INSERT ... ON CONFLICT DO NOTHING
        if 'INSERT OR IGNORE' in converted:
            converted = converted.replace('INSERT OR IGNORE', 'INSERT')
            # For training_plan_exercises, specify the conflict columns
            if 'training_plan_exercises' in converted:
                # Add ON CONFLICT after the VALUES clause
                if 'VALUES' in converted and ')' in converted:
                    # Find the closing paren of VALUES clause
                    parts = converted.split('VALUES')
                    if len(parts) == 2:
                        values_part = parts[1]
                        # Find first closing paren after VALUES
                        paren_idx = values_part.find(')')
                        if paren_idx != -1:
                            converted = (parts[0] + 'VALUES' + values_part[:paren_idx+1] +
                                       ' ON CONFLICT (training_plan_id, exercise_id) DO NOTHING')
            else:
                # Generic ON CONFLICT DO NOTHING for other tables
                if 'VALUES' in converted and ')' in converted:
                    parts = converted.split('VALUES')
                    if len(parts) == 2:
                        values_part = parts[1]
                        paren_idx = values_part.find(')')
                        if paren_idx != -1:
                            converted = parts[0] + 'VALUES' + values_part[:paren_idx+1] + ' ON CONFLICT DO NOTHING'

        return converted

    def _execute(self, cursor, query: str, params=None):
        """Execute query with automatic conversion for PostgreSQL"""
        converted_query = self._convert_query(query)
        if params:
            cursor.execute(converted_query, params)
        else:
            cursor.execute(converted_query)

    def _column_exists(self, cursor, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table"""
        if self.is_postgres:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = %s AND column_name = %s
                )
            """, (table_name, column_name))
            return cursor.fetchone()[0]
        else:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            return column_name in columns

    def _get_last_insert_id(self, cursor, query: str, params: tuple) -> int:
        """Execute INSERT and return the inserted ID (works for both databases)"""
        if self.is_postgres:
            # PostgreSQL: use RETURNING id
            query_with_returning = self._convert_query(query) + " RETURNING id"
            cursor.execute(query_with_returning, params)
            return cursor.fetchone()[0]
        else:
            # SQLite: use lastrowid
            self._execute(cursor, query, params)
            return cursor.lastrowid

    def _read_sql(self, query: str, conn, params=None) -> pd.DataFrame:
        """Wrapper for pd.read_sql_query with automatic query conversion"""
        converted_query = self._convert_query(query)
        if params:
            return pd.read_sql_query(converted_query, conn, params=params)
        else:
            return pd.read_sql_query(converted_query, conn)

    def init_database(self):
        """Initialisiert die Datenbank mit allen benötigten Tabellen"""
        conn = self.get_connection()
        cursor = self._cursor(conn)

        pk_type = self._get_pk_type()

        # Tabelle für Trainingspläne
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS training_plans (
                id {pk_type},
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabelle für Übungen
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS exercises (
                id {pk_type},
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                rep_range_min INTEGER DEFAULT 5,
                rep_range_max INTEGER DEFAULT 12,
                min_weight REAL DEFAULT 20.0,
                pause_duration INTEGER DEFAULT 180,
                exercise_type TEXT DEFAULT 'compound',
                target_sets INTEGER DEFAULT 3,
                weight_increment REAL DEFAULT 1.25,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migration: Füge neue Spalten zu existierenden exercises-Tabellen hinzu
        if not self._column_exists(cursor, 'exercises', 'rep_range_min'):
            cursor.execute("ALTER TABLE exercises ADD COLUMN rep_range_min INTEGER DEFAULT 5")
        if not self._column_exists(cursor, 'exercises', 'rep_range_max'):
            cursor.execute("ALTER TABLE exercises ADD COLUMN rep_range_max INTEGER DEFAULT 12")
        if not self._column_exists(cursor, 'exercises', 'min_weight'):
            cursor.execute("ALTER TABLE exercises ADD COLUMN min_weight REAL DEFAULT 20.0")
        if not self._column_exists(cursor, 'exercises', 'pause_duration'):
            cursor.execute("ALTER TABLE exercises ADD COLUMN pause_duration INTEGER DEFAULT 180")
        if not self._column_exists(cursor, 'exercises', 'exercise_type'):
            cursor.execute("ALTER TABLE exercises ADD COLUMN exercise_type TEXT DEFAULT 'compound'")
        if not self._column_exists(cursor, 'exercises', 'target_sets'):
            cursor.execute("ALTER TABLE exercises ADD COLUMN target_sets INTEGER DEFAULT 3")
        if not self._column_exists(cursor, 'exercises', 'weight_increment'):
            cursor.execute("ALTER TABLE exercises ADD COLUMN weight_increment REAL DEFAULT 1.25")

        # Verknüpfungstabelle: Welche Übungen gehören zu welchem Trainingsplan
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS training_plan_exercises (
                id {pk_type},
                training_plan_id INTEGER NOT NULL,
                exercise_id INTEGER NOT NULL,
                order_index INTEGER DEFAULT 0,
                FOREIGN KEY (training_plan_id) REFERENCES training_plans(id) ON DELETE CASCADE,
                FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE,
                UNIQUE(training_plan_id, exercise_id)
            )
        """)

        # Tabelle für Trainingseinheiten
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS workouts (
                id {pk_type},
                exercise_id INTEGER NOT NULL,
                training_plan_id INTEGER,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE,
                FOREIGN KEY (training_plan_id) REFERENCES training_plans(id) ON DELETE SET NULL
            )
        """)

        # Migration: Füge training_plan_id zu existierenden workouts hinzu
        if not self._column_exists(cursor, 'workouts', 'training_plan_id'):
            cursor.execute("ALTER TABLE workouts ADD COLUMN training_plan_id INTEGER")

        # Tabelle für Sets
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS sets (
                id {pk_type},
                workout_id INTEGER NOT NULL,
                set_number INTEGER NOT NULL,
                weight REAL NOT NULL,
                reps INTEGER NOT NULL,
                rpe REAL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workout_id) REFERENCES workouts(id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        conn.close()

    # === Übungen (Exercises) ===

    def add_exercise(self, name: str, description: str = "",
                     rep_range_min: int = 5, rep_range_max: int = 12,
                     min_weight: float = 20.0, pause_duration: int = 180,
                     exercise_type: str = 'compound', target_sets: int = 3,
                     weight_increment: float = 1.25) -> int:
        """Fügt eine neue Übung hinzu

        exercise_type: 'compound', 'isolation', oder 'machine'
        target_sets: Ziel-Anzahl Sets pro Training
        """
        conn = self.get_connection()
        cursor = self._cursor(conn)
        exercise_id = self._get_last_insert_id(
            cursor,
            """INSERT INTO exercises (name, description, rep_range_min, rep_range_max, min_weight, pause_duration, exercise_type, target_sets, weight_increment)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, description, rep_range_min, rep_range_max, min_weight, pause_duration, exercise_type, target_sets, weight_increment)
        )
        conn.commit()
        conn.close()
        return exercise_id

    def update_exercise(self, exercise_id: int, name: str = None, description: str = None,
                       rep_range_min: int = None, rep_range_max: int = None,
                       min_weight: float = None, weight_increment: float = None,
                       exercise_type: str = None, pause_duration: int = None,
                       target_sets: int = None):
        """Aktualisiert eine Übung"""
        conn = self.get_connection()
        cursor = self._cursor(conn)

        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if rep_range_min is not None:
            updates.append("rep_range_min = ?")
            params.append(rep_range_min)
        if rep_range_max is not None:
            updates.append("rep_range_max = ?")
            params.append(rep_range_max)
        if min_weight is not None:
            updates.append("min_weight = ?")
            params.append(min_weight)
        if weight_increment is not None:
            updates.append("weight_increment = ?")
            params.append(weight_increment)
        if exercise_type is not None:
            updates.append("exercise_type = ?")
            params.append(exercise_type)
        if pause_duration is not None:
            updates.append("pause_duration = ?")
            params.append(pause_duration)
        if target_sets is not None:
            updates.append("target_sets = ?")
            params.append(target_sets)

        if updates:
            params.append(exercise_id)
            query = f"UPDATE exercises SET {', '.join(updates)} WHERE id = ?"
            self._execute(cursor, query, tuple(params))
            conn.commit()

        conn.close()

    def get_all_exercises(self) -> List[Dict]:
        """Gibt alle Übungen zurück"""
        conn = self.get_connection()
        cursor = self._cursor(conn)
        self._execute(cursor, "SELECT * FROM exercises ORDER BY name")
        exercises = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return exercises

    def get_exercise_by_id(self, exercise_id: int) -> Optional[Dict]:
        """Gibt eine spezifische Übung zurück"""
        conn = self.get_connection()
        cursor = self._cursor(conn)
        self._execute(cursor, "SELECT * FROM exercises WHERE id = ?", (exercise_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def delete_exercise(self, exercise_id: int):
        """Löscht eine Übung und alle zugehörigen Daten"""
        conn = self.get_connection()
        cursor = self._cursor(conn)
        self._execute(cursor, "DELETE FROM exercises WHERE id = ?", (exercise_id,))
        conn.commit()
        conn.close()

    # === Trainingspläne (Training Plans) ===

    def add_training_plan(self, name: str, description: str = "") -> int:
        """Erstellt einen neuen Trainingsplan"""
        conn = self.get_connection()
        cursor = self._cursor(conn)
        plan_id = self._get_last_insert_id(
            cursor,
            "INSERT INTO training_plans (name, description) VALUES (?, ?)",
            (name, description)
        )
        conn.commit()
        conn.close()
        return plan_id

    def get_all_training_plans(self) -> List[Dict]:
        """Gibt alle Trainingspläne zurück"""
        conn = self.get_connection()
        cursor = self._cursor(conn)
        self._execute(cursor, "SELECT * FROM training_plans ORDER BY name")
        plans = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return plans

    def get_training_plan_by_id(self, plan_id: int) -> Optional[Dict]:
        """Gibt einen spezifischen Trainingsplan zurück"""
        conn = self.get_connection()
        cursor = self._cursor(conn)
        self._execute(cursor, "SELECT * FROM training_plans WHERE id = ?", (plan_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def delete_training_plan(self, plan_id: int):
        """Löscht einen Trainingsplan"""
        conn = self.get_connection()
        cursor = self._cursor(conn)
        self._execute(cursor, "DELETE FROM training_plans WHERE id = ?", (plan_id,))
        conn.commit()
        conn.close()

    def add_exercise_to_plan(self, plan_id: int, exercise_id: int, order_index: int = 0):
        """Fügt eine Übung zu einem Trainingsplan hinzu"""
        conn = self.get_connection()
        cursor = self._cursor(conn)
        self._execute(
            cursor,
            """INSERT OR IGNORE INTO training_plan_exercises
               (training_plan_id, exercise_id, order_index) VALUES (?, ?, ?)""",
            (plan_id, exercise_id, order_index)
        )
        conn.commit()
        conn.close()

    def remove_exercise_from_plan(self, plan_id: int, exercise_id: int):
        """Entfernt eine Übung aus einem Trainingsplan"""
        conn = self.get_connection()
        cursor = self._cursor(conn)
        self._execute(
            cursor,
            "DELETE FROM training_plan_exercises WHERE training_plan_id = ? AND exercise_id = ?",
            (plan_id, exercise_id)
        )
        conn.commit()
        conn.close()

    def get_exercises_for_plan(self, plan_id: int) -> List[Dict]:
        """Gibt alle Übungen für einen Trainingsplan zurück"""
        conn = self.get_connection()
        cursor = self._cursor(conn)
        query = """
            SELECT e.*, tpe.order_index
            FROM exercises e
            JOIN training_plan_exercises tpe ON e.id = tpe.exercise_id
            WHERE tpe.training_plan_id = ?
            ORDER BY tpe.order_index, e.name
        """
        self._execute(cursor, query, (plan_id,))
        exercises = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return exercises

    def get_plans_for_exercise(self, exercise_id: int) -> List[Dict]:
        """Gibt alle Trainingspläne zurück, die eine bestimmte Übung enthalten"""
        conn = self.get_connection()
        cursor = self._cursor(conn)
        query = """
            SELECT tp.*
            FROM training_plans tp
            JOIN training_plan_exercises tpe ON tp.id = tpe.training_plan_id
            WHERE tpe.exercise_id = ?
            ORDER BY tp.name
        """
        self._execute(cursor, query, (exercise_id,))
        plans = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return plans

    def move_exercise_in_plan(self, plan_id: int, exercise_id: int, direction: str):
        """Verschiebt eine Übung in einem Plan nach oben oder unten"""
        conn = self.get_connection()
        cursor = self._cursor(conn)

        # Hole aktuelle Position
        self._execute(
            cursor,
            "SELECT order_index FROM training_plan_exercises WHERE training_plan_id = ? AND exercise_id = ?",
            (plan_id, exercise_id)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return

        current_index = row['order_index']

        if direction == "up":
            new_index = current_index - 1
            # Tausche mit dem Element darüber
            self._execute(
                cursor,
                "UPDATE training_plan_exercises SET order_index = ? WHERE training_plan_id = ? AND order_index = ?",
                (current_index, plan_id, new_index)
            )
            self._execute(
                cursor,
                "UPDATE training_plan_exercises SET order_index = ? WHERE training_plan_id = ? AND exercise_id = ?",
                (new_index, plan_id, exercise_id)
            )
        elif direction == "down":
            new_index = current_index + 1
            # Tausche mit dem Element darunter
            self._execute(
                cursor,
                "UPDATE training_plan_exercises SET order_index = ? WHERE training_plan_id = ? AND order_index = ?",
                (current_index, plan_id, new_index)
            )
            self._execute(
                cursor,
                "UPDATE training_plan_exercises SET order_index = ? WHERE training_plan_id = ? AND exercise_id = ?",
                (new_index, plan_id, exercise_id)
            )

        conn.commit()
        conn.close()

    # === Trainingseinheiten (Workouts) ===

    def create_workout(self, exercise_id: int, training_plan_id: Optional[int] = None) -> int:
        """Erstellt eine neue Trainingseinheit"""
        conn = self.get_connection()
        cursor = self._cursor(conn)
        workout_id = self._get_last_insert_id(
            cursor,
            "INSERT INTO workouts (exercise_id, training_plan_id) VALUES (?, ?)",
            (exercise_id, training_plan_id)
        )
        conn.commit()
        conn.close()
        return workout_id

    def get_workouts_for_exercise(self, exercise_id: int) -> List[Dict]:
        """Gibt alle Trainingseinheiten für eine Übung zurück"""
        conn = self.get_connection()
        cursor = self._cursor(conn)
        self._execute(
            cursor,
            "SELECT * FROM workouts WHERE exercise_id = ? ORDER BY date DESC",
            (exercise_id,)
        )
        workouts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return workouts

    # === Sets ===

    def add_set(self, workout_id: int, set_number: int, weight: float,
                reps: int, rpe: Optional[float] = None, notes: str = "") -> int:
        """Fügt ein Set zu einer Trainingseinheit hinzu"""
        conn = self.get_connection()
        cursor = self._cursor(conn)
        set_id = self._get_last_insert_id(
            cursor,
            """INSERT INTO sets (workout_id, set_number, weight, reps, rpe, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (workout_id, set_number, weight, reps, rpe, notes)
        )
        conn.commit()
        conn.close()
        return set_id

    def get_sets_for_workout(self, workout_id: int) -> List[Dict]:
        """Gibt alle Sets für eine Trainingseinheit zurück"""
        conn = self.get_connection()
        cursor = self._cursor(conn)
        self._execute(
            cursor,
            "SELECT * FROM sets WHERE workout_id = ? ORDER BY set_number",
            (workout_id,)
        )
        sets = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return sets

    def get_all_sets_for_exercise(self, exercise_id: int) -> pd.DataFrame:
        """Gibt alle Sets für eine Übung als DataFrame zurück"""
        conn = self.get_connection()
        query = """
            SELECT
                s.id,
                s.workout_id,
                s.set_number,
                s.weight,
                s.reps,
                s.rpe,
                s.notes,
                s.created_at,
                w.date as workout_date,
                e.name as exercise_name
            FROM sets s
            JOIN workouts w ON s.workout_id = w.id
            JOIN exercises e ON w.exercise_id = e.id
            WHERE e.id = ?
            ORDER BY w.date, s.set_number
        """
        df = self._read_sql(query, conn, params=(exercise_id,))
        conn.close()
        return df

    def get_last_top_set(self, exercise_id: int) -> Optional[Dict]:
        """Gibt das letzte Top-Set (höchstes Gewicht) für eine Übung zurück"""
        conn = self.get_connection()
        cursor = self._cursor(conn)
        query = """
            SELECT s.*, w.date as workout_date
            FROM sets s
            JOIN workouts w ON s.workout_id = w.id
            WHERE w.exercise_id = ?
            ORDER BY s.weight DESC, w.date DESC
            LIMIT 1
        """
        self._execute(cursor, query, (exercise_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_last_n_sessions(self, exercise_id: int, n: int = 3) -> list:
        """
        Gibt die Top-Sets der letzten N Sessions zurück (neueste zuerst).

        Für jede Session wird das Set mit dem höchsten Gewicht ausgewählt.
        """
        conn = self.get_connection()
        cursor = self._cursor(conn)
        query = """
            WITH top_sets_per_workout AS (
                SELECT
                    w.id as workout_id,
                    w.date,
                    MAX(s.weight) as max_weight
                FROM workouts w
                JOIN sets s ON s.workout_id = w.id
                WHERE w.exercise_id = ?
                GROUP BY w.id, w.date
                ORDER BY w.date DESC
                LIMIT ?
            )
            SELECT s.weight, s.reps, s.rpe, w.date
            FROM sets s
            JOIN workouts w ON s.workout_id = w.id
            JOIN top_sets_per_workout t ON t.workout_id = w.id AND s.weight = t.max_weight
            WHERE w.exercise_id = ?
            ORDER BY w.date DESC
        """
        self._execute(cursor, query, (exercise_id, n, exercise_id))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_exercise_history(self, exercise_id: int) -> pd.DataFrame:
        """Gibt die komplette Historie einer Übung als DataFrame zurück"""
        conn = self.get_connection()
        query = """
            SELECT
                w.date,
                s.weight,
                s.reps,
                s.rpe,
                s.set_number,
                s.notes
            FROM sets s
            JOIN workouts w ON s.workout_id = w.id
            WHERE w.exercise_id = ?
            ORDER BY w.date, s.set_number
        """
        df = self._read_sql(query, conn, params=(exercise_id,))
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
        conn.close()
        return df

    def export_to_csv(self, exercise_id: Optional[int] = None) -> pd.DataFrame:
        """Exportiert alle Daten (oder für eine spezifische Übung) als DataFrame"""
        conn = self.get_connection()
        if exercise_id:
            query = """
                SELECT
                    e.name as exercise,
                    w.date as workout_date,
                    s.set_number,
                    s.weight,
                    s.reps,
                    s.rpe,
                    s.notes
                FROM sets s
                JOIN workouts w ON s.workout_id = w.id
                JOIN exercises e ON w.exercise_id = e.id
                WHERE e.id = ?
                ORDER BY w.date, s.set_number
            """
            df = self._read_sql(query, conn, params=(exercise_id,))
        else:
            query = """
                SELECT
                    e.name as exercise,
                    w.date as workout_date,
                    s.set_number,
                    s.weight,
                    s.reps,
                    s.rpe,
                    s.notes
                FROM sets s
                JOIN workouts w ON s.workout_id = w.id
                JOIN exercises e ON w.exercise_id = e.id
                ORDER BY e.name, w.date, s.set_number
            """
            df = self._read_sql(query, conn)
        conn.close()
        return df
