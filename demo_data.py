"""
Demo-Daten Generator für Lift Log App
Erstellt realistische Trainingshistorie zum Testen der Statistik-Funktionen
"""

from database import TrainingDatabase
from datetime import datetime, timedelta
import random


# Demo-Trainingspläne Definition
DEMO_TRAINING_PLANS = {
    'Push Day (Demo)': [
        {
            'name': 'Bankdrücken (Demo)',
            'description': 'Compound-Übung für Brust, Schultern, Trizeps',
            'type': 'compound',
            'rep_min': 5,
            'rep_max': 8,
            'weight_inc': 2.5,
            'pause': 180,
            'target_sets': 3,
            'start_weight': 60.0
        },
        {
            'name': 'Schrägbankdrücken (Demo)',
            'description': 'Obere Brust fokussiert',
            'type': 'compound',
            'rep_min': 8,
            'rep_max': 12,
            'weight_inc': 2.5,
            'pause': 150,
            'target_sets': 3,
            'start_weight': 50.0
        },
        {
            'name': 'Schulterdrücken (Demo)',
            'description': 'Compound für Schultern',
            'type': 'compound',
            'rep_min': 6,
            'rep_max': 10,
            'weight_inc': 2.5,
            'pause': 150,
            'target_sets': 3,
            'start_weight': 40.0
        },
        {
            'name': 'Trizeps Extensions (Demo)',
            'description': 'Isolation für Trizeps',
            'type': 'isolation',
            'rep_min': 10,
            'rep_max': 15,
            'weight_inc': 1.25,
            'pause': 90,
            'target_sets': 3,
            'start_weight': 20.0
        }
    ],
    'Pull Day (Demo)': [
        {
            'name': 'Kreuzheben (Demo)',
            'description': 'Compound für Rücken, Beine, Core',
            'type': 'compound',
            'rep_min': 3,
            'rep_max': 8,
            'weight_inc': 5.0,
            'pause': 240,
            'target_sets': 3,
            'start_weight': 100.0
        },
        {
            'name': 'Klimmzüge (Demo)',
            'description': 'Compound für breiten Rücken',
            'type': 'compound',
            'rep_min': 5,
            'rep_max': 12,
            'weight_inc': 2.5,
            'pause': 180,
            'target_sets': 3,
            'start_weight': 0.0  # Bodyweight
        },
        {
            'name': 'Rudern (Demo)',
            'description': 'Compound für mittleren Rücken',
            'type': 'compound',
            'rep_min': 8,
            'rep_max': 12,
            'weight_inc': 2.5,
            'pause': 150,
            'target_sets': 3,
            'start_weight': 60.0
        },
        {
            'name': 'Bizeps Curls (Demo)',
            'description': 'Isolation für Bizeps',
            'type': 'isolation',
            'rep_min': 10,
            'rep_max': 15,
            'weight_inc': 1.25,
            'pause': 90,
            'target_sets': 3,
            'start_weight': 15.0
        }
    ],
    'Leg Day (Demo)': [
        {
            'name': 'Kniebeugen (Demo)',
            'description': 'Compound für Beine und Core',
            'type': 'compound',
            'rep_min': 5,
            'rep_max': 10,
            'weight_inc': 5.0,
            'pause': 240,
            'target_sets': 4,
            'start_weight': 80.0
        },
        {
            'name': 'Beinpresse (Demo)',
            'description': 'Machine für Beine',
            'type': 'machine',
            'rep_min': 10,
            'rep_max': 15,
            'weight_inc': 5.0,
            'pause': 120,
            'target_sets': 3,
            'start_weight': 120.0
        },
        {
            'name': 'Beinstrecker (Demo)',
            'description': 'Isolation für Quadrizeps',
            'type': 'isolation',
            'rep_min': 12,
            'rep_max': 20,
            'weight_inc': 2.5,
            'pause': 90,
            'target_sets': 3,
            'start_weight': 40.0
        },
        {
            'name': 'Beinbeuger (Demo)',
            'description': 'Isolation für Hamstrings',
            'type': 'isolation',
            'rep_min': 12,
            'rep_max': 20,
            'weight_inc': 2.5,
            'pause': 90,
            'target_sets': 3,
            'start_weight': 35.0
        }
    ]
}


def load_demo_data(db: TrainingDatabase):
    """
    Lädt Demo-Trainingsdaten in die Datenbank.

    Erstellt:
    - 3 Trainingspläne (Push/Pull/Legs)
    - 12 Übungen (4 pro Plan)
    - 4 Wochen Trainingshistorie (3-4x pro Woche)
    - Progressive Overload mit realistischen Schwankungen
    - RPE-Werte die den Fortschritt widerspiegeln
    """

    # 1. Trainingspläne erstellen
    plan_ids = {}
    for plan_name in DEMO_TRAINING_PLANS.keys():
        # Check ob Plan schon existiert
        existing_plans = db.get_all_training_plans()
        exists = any(p['name'] == plan_name for p in existing_plans)

        if not exists:
            plan_id = db.add_training_plan(plan_name, f"Demo-Plan: {plan_name}")
            plan_ids[plan_name] = plan_id
        else:
            plan_id = next(p['id'] for p in existing_plans if p['name'] == plan_name)
            plan_ids[plan_name] = plan_id

    # 2. Übungen erstellen und zu Plänen hinzufügen
    exercise_map = {}  # {exercise_name: (exercise_id, plan_id, start_weight)}

    for plan_name, exercises in DEMO_TRAINING_PLANS.items():
        plan_id = plan_ids[plan_name]

        for i, ex_def in enumerate(exercises):
            # Check ob Übung existiert
            existing = db.get_all_exercises()
            exists = any(e['name'] == ex_def['name'] for e in existing)

            if not exists:
                ex_id = db.add_exercise(
                    name=ex_def['name'],
                    description=ex_def['description'],
                    rep_range_min=ex_def['rep_min'],
                    rep_range_max=ex_def['rep_max'],
                    min_weight=ex_def['start_weight'],
                    pause_duration=ex_def['pause'],
                    exercise_type=ex_def['type'],
                    target_sets=ex_def['target_sets'],
                    weight_increment=ex_def['weight_inc']
                )
            else:
                ex_id = next(e['id'] for e in existing if e['name'] == ex_def['name'])

            # Übung zu Plan hinzufügen
            db.add_exercise_to_plan(plan_id, ex_id, order_index=i)

            # Für Training-Generator speichern
            exercise_map[ex_def['name']] = (ex_id, plan_id, ex_def['start_weight'], ex_def['weight_inc'])

    # 3. Trainingshistorie generieren (4 Wochen, 3-4x pro Woche)
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=4)

    # Trainingsplan-Rotation: Push -> Pull -> Legs -> Rest -> Push -> ...
    plan_rotation = ['Push Day (Demo)', 'Pull Day (Demo)', 'Leg Day (Demo)']
    current_plan_idx = 0
    current_date = start_date

    workout_count = 0
    while current_date < end_date and workout_count < 16:  # ~4 Trainings/Woche
        # Welcher Plan heute?
        current_plan_name = plan_rotation[current_plan_idx]
        current_plan_id = plan_ids[current_plan_name]

        # Alle Übungen des Plans trainieren
        plan_exercises = DEMO_TRAINING_PLANS[current_plan_name]

        for ex_def in plan_exercises:
            ex_id, _, start_weight, weight_inc = exercise_map[ex_def['name']]

            # Progressive Overload berechnen (basierend auf Woche)
            weeks_passed = (current_date - start_date).days // 7
            progression_increments = weeks_passed  # Jede Woche +1 Increment
            current_weight = start_weight + (progression_increments * weight_inc)

            # Workout erstellen
            workout_id = db.create_workout(ex_id, current_plan_id)

            # Sets generieren
            num_sets = ex_def['target_sets']

            for set_num in range(1, num_sets + 1):
                # Realistische Rep-Ranges
                rep_min = ex_def['rep_min']
                rep_max = ex_def['rep_max']

                # Top-Set hat beste Reps, dann Fatigue
                if set_num == 1:
                    reps = random.randint(rep_max - 2, rep_max)
                    rpe = round(random.uniform(7.5, 8.5), 1)
                    weight = current_weight
                elif set_num == 2:
                    reps = random.randint(rep_min + 1, rep_max - 1)
                    rpe = round(random.uniform(8.0, 9.0), 1)
                    weight = current_weight
                else:
                    reps = random.randint(rep_min, rep_max - 2)
                    rpe = round(random.uniform(8.5, 9.5), 1)
                    # Letzter Satz manchmal leichter
                    weight = current_weight if random.random() > 0.4 else current_weight - weight_inc

                # Set speichern
                db.add_set(
                    workout_id=workout_id,
                    set_number=set_num,
                    weight=weight,
                    reps=reps,
                    rpe=rpe,
                    notes=f"Demo {current_plan_name} - Set {set_num}"
                )

        # Nächstes Training
        workout_count += 1
        current_plan_idx = (current_plan_idx + 1) % len(plan_rotation)

        # 1-2 Tage Pause (3-4 Trainings/Woche)
        current_date += timedelta(days=random.choice([1, 2]))

    return len(DEMO_TRAINING_PLANS)


def clear_demo_data(db: TrainingDatabase):
    """
    Entfernt alle Demo-Daten (Pläne und Übungen mit "(Demo)" im Namen)
    """
    # Lösche Demo-Trainingspläne
    all_plans = db.get_all_training_plans()
    demo_plans = [p for p in all_plans if '(Demo)' in p['name']]

    for plan in demo_plans:
        db.delete_training_plan(plan['id'])

    # Lösche Demo-Übungen
    all_exercises = db.get_all_exercises()
    demo_exercises = [ex for ex in all_exercises if '(Demo)' in ex['name']]

    for ex in demo_exercises:
        db.delete_exercise(ex['id'])

    return len(demo_plans) + len(demo_exercises)


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
