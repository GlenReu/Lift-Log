import pandas as pd
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta


def calculate_session_target(last_sessions: List[Dict], exercise_info: Dict) -> Dict:
    """
    Berechnet das Zielgewicht für die gesamte Session basierend auf den letzten 3 Sessions.

    Workflow:
    1. Letzte 3 Sessions laden und gewichten (50% / 30% / 20%)
    2. Gewichteten Durchschnitts-RPE berechnen
    3. Rep-Position prüfen
    4. Zielgewicht basierend auf RPE festlegen
    5. Rep-Range-Sicherheitsregel anwenden

    Args:
        last_sessions: Liste der letzten Sessions (neueste zuerst), jede mit weight, reps, rpe
        exercise_info: Übungsinformationen mit rep_range_min, rep_range_max, weight_increment, exercise_type

    Returns:
        Dict mit 'weight', 'reps', 'suggestion', 'progression_percent'
    """
    rep_min = exercise_info.get('rep_range_min', 5)
    rep_max = exercise_info.get('rep_range_max', 12)
    weight_increment = exercise_info.get('weight_increment', 1.25)
    min_weight = exercise_info.get('min_weight', 20.0)

    # Kein vorheriges Training
    if not last_sessions or len(last_sessions) == 0:
        return {
            'weight': min_weight,
            'reps': rep_min,
            'suggestion': f'Erste Session. Starte mit {rep_min}-{rep_max} Reps.',
            'progression_percent': 0.0
        }

    # 🟩 SCHRITT 1: Gewichtete Durchschnitte berechnen
    weights_list = [0.5, 0.3, 0.2]  # Neueste Session = 50%, dann 30%, 20%

    weighted_weight = 0.0
    weighted_reps = 0.0
    weighted_rpe = 0.0
    total_weight_sum = 0.0

    for i, session in enumerate(last_sessions[:3]):  # Max 3 Sessions
        w = weights_list[i] if i < len(weights_list) else 0.0
        weighted_weight += session['weight'] * w
        weighted_reps += session['reps'] * w
        if session.get('rpe') is not None:
            weighted_rpe += session['rpe'] * w
        total_weight_sum += w

    # Normalisiere falls weniger als 3 Sessions
    if total_weight_sum > 0:
        weighted_weight /= total_weight_sum
        weighted_reps /= total_weight_sum
        weighted_rpe /= total_weight_sum

    last_weight = last_sessions[0]['weight']
    last_reps = last_sessions[0]['reps']
    last_rpe = last_sessions[0].get('rpe', 8.0)

    # 🟦 SCHRITT 2: Rep-Position prüfen
    rep_range = rep_max - rep_min
    rep_middle = rep_min + (rep_range / 2)

    last_in_lower_half = last_reps < rep_middle
    last_in_upper_half = last_reps >= rep_middle
    last_at_max = last_reps >= rep_max

    # 🟨 SCHRITT 3: Progression anhand gewichtetem RPE
    progression_percent = 0.0

    if weighted_rpe <= 7.0:
        # Niedrig - aggressive Progression
        progression_percent = 2.0 if last_in_upper_half else 2.5
    elif 7.0 < weighted_rpe <= 8.5:
        # Moderat - mittlere Progression
        progression_percent = 1.0 if last_in_lower_half else 1.5
    elif 8.5 < weighted_rpe < 9.25:
        # Hoch - Gewicht halten
        progression_percent = 0.0
    else:  # weighted_rpe >= 9.25
        # Sehr hoch - Gewicht senken
        progression_percent = -1.5

    # 🟧 SCHRITT 4: Rep-Range-Sicherheitsregel
    if last_in_lower_half and progression_percent > 0:
        # Sicherheitsbremse: maximal +1% wenn im unteren Rep-Bereich
        progression_percent = min(progression_percent, 1.0)

    # Berechne neues Gewicht
    weight_change = last_weight * (progression_percent / 100.0)
    new_weight = last_weight + weight_change

    # Runde auf Inkrement
    new_weight = round(new_weight / weight_increment) * weight_increment
    new_weight = max(min_weight, new_weight)  # Nicht unter Mindestgewicht

    # Ziel-Reps: Im mittleren Bereich der Rep-Range
    target_reps = int(rep_middle)

    # Generiere Suggestion-Text
    if progression_percent > 0:
        suggestion = f'📈 Gewicht +{progression_percent:.1f}% (Ø-RPE: {weighted_rpe:.1f}). Ziel: {target_reps} Reps @ RPE 8-9.'
    elif progression_percent < 0:
        suggestion = f'📉 Gewicht {progression_percent:.1f}% (Ø-RPE: {weighted_rpe:.1f} zu hoch). Deload für bessere Technik.'
    else:
        suggestion = f'➡️ Gewicht halten (Ø-RPE: {weighted_rpe:.1f}). Ziel: {target_reps} Reps @ RPE 8-9.'

    # Warnung bei niedriger Rep-Position
    if last_in_lower_half and progression_percent > 0:
        suggestion += f' ⚠️ Letzte Session nur {int(last_reps)} Reps - konservative Steigerung.'

    return {
        'weight': new_weight,
        'reps': target_reps,
        'suggestion': suggestion,
        'progression_percent': progression_percent,
        'weighted_rpe': weighted_rpe
    }


def suggest_next_top_set(last_top_set: Optional[Dict], exercise_info: Optional[Dict] = None) -> Dict:
    """
    Schlägt das nächste Top-Set basierend auf progressiver Überlastung vor.

    Neue Regeln:
    1. Compound Lifts: Nie Gewicht UND Reps gleichzeitig erhöhen
    2. RPE >= 9: Sehr konservativ - Gewicht/Reps halten oder sogar -1 Rep
    3. Machines/Isolation: Gewicht+Reps-Kombination erlaubt

    Args:
        last_top_set: Letztes Top-Set mit weight, reps, rpe
        exercise_info: Übungsinformationen mit rep_range_min, rep_range_max, min_weight, exercise_type
    """
    # Standard-Werte
    rep_min = exercise_info.get('rep_range_min', 5) if exercise_info else 5
    rep_max = exercise_info.get('rep_range_max', 12) if exercise_info else 12
    min_weight = exercise_info.get('min_weight', 20.0) if exercise_info else 20.0
    exercise_type = exercise_info.get('exercise_type', 'compound') if exercise_info else 'compound'

    if not last_top_set:
        return {
            'weight': min_weight,
            'reps': rep_min,
            'suggestion': f'Kein vorheriges Set gefunden. Starte mit {rep_min}-{rep_max} Reps bei Mindestgewicht.'
        }

    last_weight = last_top_set['weight']
    last_reps = last_top_set['reps']
    last_rpe = last_top_set.get('rpe')

    # Prüfe ob am oberen Ende der Rep Range
    at_max_reps = last_reps >= rep_max
    is_compound = exercise_type == 'compound'

    # Progression basierend auf RPE und Rep Range
    if last_rpe is not None:
        # NEUE REGEL: RPE >= 9 - Sehr konservativ!
        if last_rpe >= 9.0:
            # Bei sehr hohem RPE: Gewicht UND Reps halten oder sogar reduzieren
            if last_reps > rep_min:
                new_weight = last_weight
                new_reps = max(rep_min, last_reps - 1)  # 1 Rep weniger
                suggestion = f'RPE sehr hoch ({last_rpe}). Reduziere auf {new_reps} Reps für bessere Technik.'
            else:
                # Schon am Minimum - alles halten
                new_weight = last_weight
                new_reps = last_reps
                suggestion = f'RPE sehr hoch ({last_rpe}). Halte Gewicht und Reps, fokussiere auf perfekte Technik!'

        elif at_max_reps:
            # Am oberen Ende der Rep Range -> Gewicht erhöhen, Reps auf Minimum
            if last_rpe <= 7.0:
                new_weight = last_weight + 2.5
                new_reps = rep_min
                suggestion = f'RPE niedrig ({last_rpe}) und max Reps erreicht. Erhöhe auf {new_weight}kg mit {rep_min} Reps.'
            elif last_rpe <= 8.5:
                new_weight = last_weight + 1.25
                new_reps = rep_min
                suggestion = f'RPE moderat ({last_rpe}) und max Reps erreicht. Erhöhe auf {new_weight}kg mit {rep_min} Reps.'
            else:
                # RPE 8.5-9: Noch nicht bereit für Gewichtssteigerung
                new_weight = last_weight
                new_reps = rep_max
                suggestion = f'RPE hoch ({last_rpe}). Halte {rep_max} Reps mit besserer Form.'

        else:
            # Noch innerhalb der Rep Range
            if last_rpe <= 7.0:
                # NEUE REGEL: Bei Compound Lifts NUR Gewicht ODER Reps
                if is_compound:
                    # Bei freien Übungen: Nur Gewicht erhöhen
                    new_weight = last_weight + 2.5
                    new_reps = rep_min
                    suggestion = f'RPE niedrig ({last_rpe}). Erhöhe Gewicht auf {new_weight}kg (freie Übung: keine Reps-Steigerung).'
                else:
                    # Bei Maschinen/Isos: Gewicht UND Reps erhöhen erlaubt
                    new_weight = last_weight + 2.5
                    new_reps = max(rep_min, last_reps - 1)
                    suggestion = f'RPE niedrig ({last_rpe}). Erhöhe auf {new_weight}kg (Maschine/Iso: Gewicht+Reps ok).'

            elif last_rpe <= 8.5:
                # Moderat - nur Reps erhöhen
                new_weight = last_weight
                new_reps = min(last_reps + 1, rep_max)
                suggestion = f'RPE moderat ({last_rpe}). Versuche {new_reps} Reps mit gleichem Gewicht.'

            else:
                # RPE 8.5-9: Nur 1 Rep mehr, Fokus Form
                new_weight = last_weight
                new_reps = min(last_reps + 1, rep_max)
                suggestion = f'RPE hoch ({last_rpe}). Versuche {new_reps} Reps, fokussiere auf Form.'

    else:
        # Keine RPE - konservative Progression
        if at_max_reps:
            new_weight = round((last_weight * 1.025) / 1.25) * 1.25
            new_reps = rep_min
            suggestion = f'Max Reps erreicht. Erhöhe konservativ auf {new_weight}kg mit {rep_min} Reps.'
        else:
            new_weight = last_weight
            new_reps = min(last_reps + 1, rep_max)
            suggestion = f'Erhöhe auf {new_reps} Reps. Trage RPE ein für bessere Vorschläge!'

    # Stelle sicher, dass Mindestgewicht eingehalten wird
    new_weight = max(new_weight, min_weight)

    return {
        'weight': round(new_weight, 2),
        'reps': int(new_reps),
        'suggestion': suggestion,
        'rep_range': f'{rep_min}-{rep_max}'
    }


def calculate_estimated_1rm(weight: float, reps: int, rpe: Optional[float] = None) -> float:
    """
    Berechnet das geschätzte 1RM (One Rep Max) - e1RM.

    Formel: e1RM = Gewicht × (1 + Reps / 30)

    Mit RPE-Korrektur (falls angegeben):
    - Berechnet RIR (Reps in Reserve) = 10 - RPE
    - Verwendet effective_reps = reps + RIR
    """
    if rpe is not None:
        # Reps in Reserve berechnen
        rir = 10 - rpe
        effective_reps = reps + rir
    else:
        effective_reps = reps

    # Epley-Formel
    estimated_1rm = weight * (1 + effective_reps / 30)
    return round(estimated_1rm, 2)


def calculate_rep_position(reps: int, rep_min: int, rep_max: int) -> float:
    """
    Berechnet die Rep-Position innerhalb der Rep Range (0.0 - 1.0).

    Formel: (Reps - RepMin) / (RepMax - RepMin)

    0.0 = am unteren Ende, 1.0 = am oberen Ende
    """
    if rep_max == rep_min:
        return 0.5
    position = (reps - rep_min) / (rep_max - rep_min)
    return max(0.0, min(1.0, position))


def calculate_rolling_average_e1rm(e1rm_history: list, window: int = 4) -> float:
    """
    Berechnet den gleitenden Durchschnitt des e1RM über die letzten N Sessions.

    Args:
        e1rm_history: Liste von e1RM-Werten (neueste zuerst)
        window: Anzahl Sessions für Average (default: 4)
    """
    if not e1rm_history:
        return 0.0

    recent = e1rm_history[:window]
    return round(sum(recent) / len(recent), 2)


def calculate_fatigue_index(e1rm: float, rpe: float) -> float:
    """
    Berechnet den Fatigue-Index: e1RM / RPE

    Höherer Index = Bessere Performance bei gegebener Anstrengung
    Sinkender Index = Zunehmende Ermüdung
    """
    if rpe == 0:
        return 0.0
    return round(e1rm / rpe, 2)


def project_sessions_to_goal(
    current_weight: float,
    current_reps: int,
    goal_weight: float,
    avg_progression_per_session: float = 2.5
) -> Tuple[int, str]:
    """
    Projiziert die Anzahl der benötigten Trainingseinheiten bis zum Zielgewicht.

    Args:
        current_weight: Aktuelles Arbeitsgewicht
        current_reps: Aktuelle Wiederholungen
        goal_weight: Zielgewicht
        avg_progression_per_session: Durchschnittliche Gewichtssteigerung pro Session

    Returns:
        Tuple von (geschätzte_sessions, erklärung)
    """
    if goal_weight <= current_weight:
        return 0, "Zielgewicht bereits erreicht oder überschritten!"

    weight_diff = goal_weight - current_weight
    estimated_sessions = int(weight_diff / avg_progression_per_session)

    # Berechne geschätzte Zeit (angenommen 2-3 Sessions pro Woche)
    weeks_min = estimated_sessions / 3
    weeks_max = estimated_sessions / 2

    explanation = (
        f"Um von {current_weight}kg auf {goal_weight}kg zu kommen, "
        f"benötigst du schätzungsweise {estimated_sessions} Trainingseinheiten. "
        f"Bei 2-3x Training pro Woche: {weeks_min:.0f}-{weeks_max:.0f} Wochen."
    )

    return estimated_sessions, explanation


def calculate_volume(df: pd.DataFrame) -> pd.DataFrame:
    """
    Berechnet das Trainingsvolumen (Gewicht × Reps) für jedes Set.
    """
    if df.empty:
        return df

    df_copy = df.copy()
    df_copy['volume'] = df_copy['weight'] * df_copy['reps']
    return df_copy


def get_workout_summary(sets_df: pd.DataFrame) -> Dict:
    """
    Erstellt eine Zusammenfassung einer Trainingseinheit.

    Returns:
        Dict mit Statistiken: total_volume, avg_weight, max_weight, total_reps
    """
    if sets_df.empty:
        return {
            'total_volume': 0,
            'avg_weight': 0,
            'max_weight': 0,
            'total_reps': 0,
            'total_sets': 0
        }

    return {
        'total_volume': (sets_df['weight'] * sets_df['reps']).sum(),
        'avg_weight': sets_df['weight'].mean(),
        'max_weight': sets_df['weight'].max(),
        'total_reps': sets_df['reps'].sum(),
        'total_sets': len(sets_df)
    }


def check_deload_triggers(df: pd.DataFrame, exercise_info: Dict) -> Dict:
    """
    Prüft, ob ein Deload empfohlen wird basierend auf:
    1. e1RM Plateau (±1% über 6-8 Einheiten)
    2. RPE ≥9 in 3 aufeinanderfolgenden Einheiten
    3. Volumen steigt, aber e1RM nicht

    Returns:
        Dict mit Deload-Empfehlung und Begründung
    """
    if df.empty or len(df) < 6:
        return {
            'needs_deload': False,
            'reason': 'Nicht genug Daten',
            'sessions_analyzed': len(df)
        }

    # Gruppiere nach Datum und berechne Top-Set pro Session
    daily_data = df.groupby('date').agg({
        'weight': 'max',
        'reps': 'max',
        'rpe': 'mean'
    }).reset_index()
    daily_data = daily_data.sort_values('date', ascending=False)

    rep_min = exercise_info.get('rep_range_min', 5)
    rep_max = exercise_info.get('rep_range_max', 12)

    # Berechne e1RM für jede Session
    daily_data['e1rm'] = daily_data.apply(
        lambda row: calculate_estimated_1rm(row['weight'], row['reps'], row['rpe']),
        axis=1
    )

    # Trigger 1: e1RM Plateau (±1% über letzte 6-8 Sessions)
    recent_sessions = daily_data.head(min(8, len(daily_data)))
    if len(recent_sessions) >= 6:
        e1rm_values = recent_sessions['e1rm'].tolist()
        e1rm_max = max(e1rm_values)
        e1rm_min = min(e1rm_values)
        e1rm_variation = ((e1rm_max - e1rm_min) / e1rm_min) * 100 if e1rm_min > 0 else 0

        if e1rm_variation <= 1.0:
            return {
                'needs_deload': True,
                'reason': f'e1RM Plateau: Nur {e1rm_variation:.1f}% Variation über {len(recent_sessions)} Sessions',
                'recommendation': 'Deload: -10-15% Volumen',
                'sessions_analyzed': len(recent_sessions)
            }

    # Trigger 2: RPE ≥9 in 3 aufeinanderfolgenden Sessions
    if len(daily_data) >= 3:
        last_3_rpe = daily_data.head(3)['rpe'].tolist()
        if all(rpe >= 9.0 for rpe in last_3_rpe if pd.notna(rpe)):
            return {
                'needs_deload': True,
                'reason': 'RPE ≥9 in 3 aufeinanderfolgenden Sessions',
                'recommendation': 'Deload: -10-15% Volumen, Fokus auf Technik',
                'sessions_analyzed': len(daily_data)
            }

    # Trigger 3: Volumen steigt, e1RM nicht
    if len(daily_data) >= 8:
        # Vergleiche erste 4 mit letzten 4 Sessions
        recent_4 = daily_data.head(4)
        older_4 = daily_data.iloc[4:8]

        # Berechne durchschnittliches Volumen (näherungsweise mit Reps * Weight)
        recent_vol = (recent_4['weight'] * recent_4['reps']).mean()
        older_vol = (older_4['weight'] * older_4['reps']).mean()

        recent_e1rm = recent_4['e1rm'].mean()
        older_e1rm = older_4['e1rm'].mean()

        vol_increase = ((recent_vol - older_vol) / older_vol) * 100 if older_vol > 0 else 0
        e1rm_increase = ((recent_e1rm - older_e1rm) / older_e1rm) * 100 if older_e1rm > 0 else 0

        if vol_increase > 5 and e1rm_increase < 1:
            return {
                'needs_deload': True,
                'reason': f'Volumen +{vol_increase:.1f}%, aber e1RM nur +{e1rm_increase:.1f}%',
                'recommendation': 'Deload: Reduziere Volumen, akkumulierte Ermüdung',
                'sessions_analyzed': len(daily_data)
            }

    return {
        'needs_deload': False,
        'reason': 'Progression läuft gut',
        'sessions_analyzed': len(daily_data)
    }


def analyze_block_progress(df: pd.DataFrame, exercise_info: Dict, weeks: int = 4) -> Dict:
    """
    Analysiert Fortschritt über einen 4-6 Wochen Block.

    Prüft:
    - e1RM-Trend (jetzt vs. vor N Wochen)
    - Steigt e1RM bei gleichem RPE?
    - Steigt RPE ohne e1RM-Zuwachs?
    - Prognose basierend auf Niveau
    """
    if df.empty:
        return {'status': 'Keine Daten'}

    # Gruppiere nach Datum
    daily_data = df.groupby('date').agg({
        'weight': 'max',
        'reps': 'max',
        'rpe': 'mean'
    }).reset_index()
    daily_data['date'] = pd.to_datetime(daily_data['date'])
    daily_data = daily_data.sort_values('date')

    # Berechne e1RM
    daily_data['e1rm'] = daily_data.apply(
        lambda row: calculate_estimated_1rm(row['weight'], row['reps'], row['rpe']),
        axis=1
    )

    # Finde Datum vor N Wochen
    latest_date = daily_data['date'].max()
    cutoff_date = latest_date - timedelta(weeks=weeks)

    recent_data = daily_data[daily_data['date'] > cutoff_date]
    older_data = daily_data[daily_data['date'] <= cutoff_date]

    if len(recent_data) < 2 or len(older_data) < 2:
        return {
            'status': 'Nicht genug Daten für Block-Analyse',
            'weeks_analyzed': weeks
        }

    # Mittelwerte berechnen
    recent_e1rm = recent_data['e1rm'].mean()
    older_e1rm = older_data['e1rm'].mean()
    recent_rpe = recent_data['rpe'].mean()
    older_rpe = older_data['rpe'].mean()

    e1rm_change = ((recent_e1rm - older_e1rm) / older_e1rm) * 100 if older_e1rm > 0 else 0
    rpe_change = recent_rpe - older_rpe

    # Prognose basierend auf Niveau (heuristisch)
    monthly_rate = (e1rm_change / weeks) * 4  # Hochrechnung auf Monat

    if monthly_rate >= 2.0:
        level = 'Anfänger'
        expected_range = '2-3%'
    elif monthly_rate >= 0.5:
        level = 'Fortgeschritten'
        expected_range = '0.5-1%'
    else:
        level = 'Sehr Fortgeschritten'
        expected_range = '0.3-0.5%'

    # Status bewerten
    if e1rm_change > 1 and rpe_change <= 0.5:
        status = '✅ Exzellent: e1RM steigt, RPE stabil'
    elif e1rm_change > 0 and rpe_change <= 1:
        status = '✅ Gut: e1RM steigt leicht'
    elif e1rm_change < 0.5 and rpe_change > 1:
        status = '⚠️ Warnung: RPE steigt, e1RM stagniert'
    else:
        status = '🔄 Ok: Langsamer Fortschritt'

    return {
        'status': status,
        'weeks_analyzed': weeks,
        'e1rm_change_percent': round(e1rm_change, 2),
        'rpe_change': round(rpe_change, 2),
        'recent_e1rm': round(recent_e1rm, 2),
        'older_e1rm': round(older_e1rm, 2),
        'estimated_level': level,
        'expected_monthly_range': expected_range,
        'actual_monthly_rate': round(monthly_rate, 2)
    }


def analyze_progression(df: pd.DataFrame) -> Dict:
    """
    Analysiert den Fortschritt über die Zeit.

    Args:
        df: DataFrame mit 'date', 'weight', 'reps' Spalten

    Returns:
        Dict mit Progressionsmetriken
    """
    if df.empty or len(df) < 2:
        return {
            'trend': 'Nicht genug Daten',
            'avg_weight_increase': 0,
            'total_increase': 0,
            'num_sessions': 0,
            'first_weight': 0,
            'last_weight': 0
        }

    # Gruppiere nach Datum und finde Max-Gewicht pro Session
    daily_max = df.groupby('date')['weight'].max().reset_index()
    daily_max = daily_max.sort_values('date')

    if len(daily_max) < 2:
        return {
            'trend': 'Nicht genug Sessions',
            'avg_weight_increase': 0,
            'total_increase': 0,
            'num_sessions': len(daily_max),
            'first_weight': daily_max.iloc[0]['weight'] if len(daily_max) > 0 else 0,
            'last_weight': daily_max.iloc[0]['weight'] if len(daily_max) > 0 else 0
        }

    first_weight = daily_max.iloc[0]['weight']
    last_weight = daily_max.iloc[-1]['weight']
    total_increase = last_weight - first_weight
    num_sessions = len(daily_max)
    avg_increase = total_increase / (num_sessions - 1) if num_sessions > 1 else 0

    trend = 'Positiv' if total_increase > 0 else 'Stagnierend' if total_increase == 0 else 'Negativ'

    return {
        'trend': trend,
        'avg_weight_increase': round(avg_increase, 2),
        'total_increase': round(total_increase, 2),
        'num_sessions': num_sessions,
        'first_weight': first_weight,
        'last_weight': last_weight
    }
