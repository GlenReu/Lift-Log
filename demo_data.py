"""
Demo-Daten Generator für Lift Log App
Erstellt realistische Trainingshistorie zum Testen der Statistik-Funktionen
"""

from database import TrainingDatabase
from datetime import datetime, timedelta
import random


def load_demo_data(db: TrainingDatabase):
    """
    Lädt Demo-Trainingsdaten in die Datenbank.

    Erstellt:
    - 3 Übungen (Bankdrücken, Kniebeugen, Kreuzheben)
    - 8 Wochen Trainingshistorie
    - Progressive Overload mit realistischen Schwankungen
    - RPE-Werte die den Fortschritt widerspiegeln
    """

    # Demo-Übungen erstellen
    exercises = [
        {
            'name': 'Bankdrücken (Demo)',
            'description': 'Compound-Übung für Brust, Schultern, Trizeps',
            'rep_range_min': 5,
            'rep_range_max': 8,
            'weight_increment': 2.5,
            'pause_duration': 180,
            'exercise_type': 'compound',
            'target_sets': 3
        },
        {
            'name': 'Kniebeugen (Demo)',
            'description': 'Compound-Übung für Beine',
            'rep_range_min': 5,
            'rep_range_max': 12,
            'weight_increment': 2.5,
            'pause_duration': 240,
            'exercise_type': 'compound',
            'target_sets': 3
        },
        {
            'name': 'Kreuzheben (Demo)',
            'description': 'Compound-Übung für Rücken, Beine',
            'rep_range_min': 3,
            'rep_range_max': 8,
            'weight_increment': 5.0,
            'pause_duration': 300,
            'exercise_type': 'compound',
            'target_sets': 3
        }
    ]

    exercise_ids = []
    for ex in exercises:
        # Check ob Übung schon existiert
        existing = db.get_all_exercises()
        exists = any(e['name'] == ex['name'] for e in existing)

        if not exists:
            ex_id = db.add_exercise(**ex)
            exercise_ids.append(ex_id)
        else:
            # Finde existierende ID
            ex_id = next(e['id'] for e in existing if e['name'] == ex['name'])
            exercise_ids.append(ex_id)

    # Trainingshistorie generieren (8 Wochen, 2-3x pro Woche pro Übung)
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=8)

    # Startgewichte für jede Übung
    start_weights = {
        exercise_ids[0]: 60.0,   # Bankdrücken
        exercise_ids[1]: 80.0,   # Kniebeugen
        exercise_ids[2]: 100.0   # Kreuzheben
    }

    # Progression simulieren
    for exercise_id in exercise_ids:
        current_weight = start_weights[exercise_id]
        current_date = start_date

        # 2-3 Trainings pro Woche
        training_count = 0
        while current_date < end_date:
            # Workout erstellen
            workout_id = db.create_workout(exercise_id)

            # 3-4 Sets pro Training
            num_sets = random.choice([3, 3, 4])

            for set_num in range(1, num_sets + 1):
                # Realistische Wiederholungen (Top-Set am Anfang)
                if set_num == 1:
                    reps = random.randint(6, 8)
                    rpe = round(random.uniform(7.5, 8.5), 1)
                elif set_num == 2:
                    reps = random.randint(5, 7)
                    rpe = round(random.uniform(8.0, 9.0), 1)
                else:
                    reps = random.randint(4, 6)
                    rpe = round(random.uniform(8.5, 9.5), 1)

                # Kleine Schwankungen im Gewicht (Warmup-Sets ignoriert)
                if set_num == 1:
                    weight = current_weight
                else:
                    # Spätere Sets: leicht reduziert oder gleich
                    weight = current_weight if random.random() > 0.3 else current_weight - 2.5

                # Set speichern
                db.add_set(
                    workout_id=workout_id,
                    set_number=set_num,
                    weight=weight,
                    reps=reps,
                    rpe=rpe,
                    notes=f"Demo-Set {set_num}"
                )

            # Progressive Overload: Gewicht alle 2-3 Trainings erhöhen
            training_count += 1
            if training_count % 3 == 0:
                # Steigerung basierend auf Übung
                if exercise_id == exercise_ids[2]:  # Kreuzheben
                    current_weight += 5.0
                else:
                    current_weight += 2.5

            # Alle 12 Trainings: Deload (10% runter)
            if training_count % 12 == 0:
                current_weight *= 0.9
                current_weight = round(current_weight / 2.5) * 2.5  # Auf 2.5kg runden

            # Nächstes Training: 3-4 Tage später
            current_date += timedelta(days=random.randint(3, 4))

    return len(exercise_ids)


def clear_demo_data(db: TrainingDatabase):
    """
    Entfernt alle Demo-Daten (Übungen mit "(Demo)" im Namen)
    """
    all_exercises = db.get_all_exercises()
    demo_exercises = [ex for ex in all_exercises if '(Demo)' in ex['name']]

    for ex in demo_exercises:
        db.delete_exercise(ex['id'])

    return len(demo_exercises)


def get_demo_stats(db: TrainingDatabase):
    """
    Gibt Statistiken über geladene Demo-Daten zurück
    """
    all_exercises = db.get_all_exercises()
    demo_exercises = [ex for ex in all_exercises if '(Demo)' in ex['name']]

    total_workouts = 0
    total_sets = 0

    for ex in demo_exercises:
        workouts = db.get_workouts_for_exercise(ex['id'])
        total_workouts += len(workouts)

        for workout in workouts:
            sets = db.get_sets_for_workout(workout['id'])
            total_sets += len(sets)

    return {
        'demo_exercises': len(demo_exercises),
        'total_workouts': total_workouts,
        'total_sets': total_sets
    }
