import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
from database import TrainingDatabase
from utils import (
    suggest_next_top_set,
    calculate_session_target,
    calculate_estimated_1rm,
    calculate_rep_position,
    calculate_rolling_average_e1rm,
    calculate_fatigue_index,
    project_sessions_to_goal,
    get_workout_summary,
    analyze_progression,
    check_deload_triggers,
    analyze_block_progress
)
from demo_data import load_demo_data, clear_demo_data, get_demo_stats

# Seitenkonfiguration
st.set_page_config(
    page_title="Lift Log",
    layout="centered",  # Besser für Mobile
    initial_sidebar_state="auto"  # Auf Mobile automatisch eingeklappt
)

# Datenbank initialisieren
@st.cache_resource
def get_database():
    return TrainingDatabase("training.db")

db = get_database()

# Session State initialisieren
if 'current_workout_id' not in st.session_state:
    st.session_state.current_workout_id = None
if 'current_exercise_id' not in st.session_state:
    st.session_state.current_exercise_id = None
if 'timer_start' not in st.session_state:
    st.session_state.timer_start = None
if 'timer_duration' not in st.session_state:
    st.session_state.timer_duration = 180
if 'current_sets' not in st.session_state:
    st.session_state.current_sets = []
if 'training_active' not in st.session_state:
    st.session_state.training_active = False
if 'active_plan_id' not in st.session_state:
    st.session_state.active_plan_id = None
if 'exercise_sets' not in st.session_state:
    st.session_state.exercise_sets = {}  # {exercise_id: [sets]}


def format_timer(seconds: int) -> str:
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins:02d}:{secs:02d}"


def main():
    # Apple Touch Icon und Web App Meta-Tags (Base64-encoded für Deployment)
    import base64
    import os

    icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
    if os.path.exists(icon_path):
        with open(icon_path, "rb") as f:
            icon_data = base64.b64encode(f.read()).decode()

        st.markdown(f"""
            <link rel="apple-touch-icon" href="data:image/png;base64,{icon_data}">
            <link rel="icon" type="image/png" href="data:image/png;base64,{icon_data}">
            <meta name="apple-mobile-web-app-capable" content="yes">
            <meta name="apple-mobile-web-app-status-bar-style" content="black">
            <meta name="apple-mobile-web-app-title" content="Lift Log">
        """, unsafe_allow_html=True)
    else:
        # Fallback ohne Icon
        st.markdown("""
            <meta name="apple-mobile-web-app-capable" content="yes">
            <meta name="apple-mobile-web-app-status-bar-style" content="black">
            <meta name="apple-mobile-web-app-title" content="Lift Log">
        """, unsafe_allow_html=True)

    # Custom CSS für Schriftart und Sidebar-Styling
    st.markdown("""
        <style>
        /* Aptos Mono Schriftart */
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@300;400;500;600;700&display=swap');

        /* Monospace NUR für spezifische Content-Elemente (NICHT für UI-Elemente) */
        .stMarkdown p,
        .stMarkdown h1,
        .stMarkdown h2,
        .stMarkdown h3,
        .stMarkdown h4,
        .stMarkdown h5,
        .stMarkdown h6,
        .stMarkdown li,
        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea,
        [data-testid="stMetricLabel"],
        [data-testid="stMetricValue"],
        .stDataFrame,
        .stTable {
            font-family: 'Aptos Mono', 'Roboto Mono', 'Courier New', monospace !important;
        }

        /* UI-Elemente bleiben bei System-Font (für Icons) */
        button, select, details, summary,
        [data-baseweb],
        [role="button"],
        .stButton,
        .stSelectbox label {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }

        /* Mobile Optimierungen */
        @media (max-width: 768px) {
            /* Größere Touch-Targets für Buttons */
            .stButton > button {
                min-height: 48px !important;
                font-size: 16px !important;
                padding: 12px 20px !important;
            }

            /* Inputs größer und besser lesbar */
            .stTextInput input,
            .stNumberInput input,
            .stSelectbox select {
                font-size: 16px !important;
                min-height: 48px !important;
            }

            /* Metrics größer auf Mobile */
            [data-testid="stMetricValue"] {
                font-size: 24px !important;
            }

            /* Expander leichter klickbar */
            details summary {
                min-height: 48px !important;
                padding: 12px !important;
                font-size: 16px !important;
            }

            /* Verhindere horizontales Scrollen */
            .main {
                max-width: 100vw;
                overflow-x: hidden;
            }
        }

        /* Sidebar Radio Buttons ohne Punkte */
        [data-testid="stSidebar"] [role="radiogroup"] label {
            background-color: transparent;
            border: none;
            padding: 8px 0px;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label div {
            font-size: 16px;
            font-weight: 400;
        }

        /* Radio Button Kreise verstecken */
        [data-testid="stSidebar"] [role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
            margin: 0;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label::before {
            display: none !important;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label span {
            display: none;
        }

        /* Hover-Effekt */
        [data-testid="stSidebar"] [role="radiogroup"] label:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }

        /* Aktiver Zustand */
        [data-testid="stSidebar"] [role="radiogroup"] label[data-baseweb="radio"] > div:first-child {
            display: none;
        }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar Navigation
    st.sidebar.markdown("### Lift Log")

    # Hauptnavigation
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Training"

    page = st.sidebar.radio(
        "Navigation",
        ["Training", "Übungen", "Trainingspläne", "Statistiken"],
        label_visibility="collapsed"
    )

    # Export am unteren Rand
    st.sidebar.markdown("---")
    st.sidebar.markdown("<br>" * 10, unsafe_allow_html=True)

    # Demo-Modus Toggle mit Auto-Load/Clear
    demo_mode = st.sidebar.toggle("🎓 Test-Modus", value=False, key="demo_mode_toggle")

    # Demo-Daten automatisch laden/löschen basierend auf Toggle
    if demo_mode:
        # Check ob Demo-Daten existieren
        demo_stats = get_demo_stats(db)
        if demo_stats['demo_exercises'] == 0:
            # Auto-load Demo-Daten
            with st.spinner("Lade Demo-Daten..."):
                try:
                    load_demo_data(db)
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Fehler: {e}")
        else:
            # Zeige Indikator dass Demo-Modus aktiv ist
            st.sidebar.success("📈 Test-Modus aktiv")
    else:
        # Check ob Demo-Daten existieren und lösche sie
        demo_stats = get_demo_stats(db)
        if demo_stats['demo_exercises'] > 0:
            with st.spinner("Lösche Demo-Daten..."):
                try:
                    clear_demo_data(db)
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Fehler: {e}")

    if st.sidebar.button("Export", use_container_width=True):
        page = "Export"

    if page == "Training":
        training_page()
    elif page == "Übungen":
        exercises_page()
    elif page == "Trainingspläne":
        training_plans_page()
    elif page == "Statistiken":
        statistics_page()
    elif page == "Export":
        export_page()


def exercises_page():
    st.header("Übungen")

    exercises = db.get_all_exercises()

    # Neue Übung erstellen
    with st.expander("➕ Neue Übung erstellen", expanded=False):
        with st.form("new_exercise_form"):
            ex_name = st.text_input("Name*", placeholder="z.B. Bankdrücken")
            ex_desc = st.text_area("Beschreibung", placeholder="Optional...")

            col1, col2 = st.columns(2)
            with col1:
                ex_type = st.selectbox(
                    "Übungstyp*",
                    options=['compound', 'isolation', 'machine'],
                    format_func=lambda x: {
                        'compound': 'Compound (freie Grundübung)',
                        'isolation': 'Isolation',
                        'machine': 'Maschine'
                    }[x],
                    index=0
                )
            with col2:
                target_sets = st.number_input("Ziel-Sets", min_value=1, value=3, step=1)

            col3, col4, col5 = st.columns(3)
            with col3:
                rep_min = st.number_input("Min. Reps", min_value=1, value=5, step=1)
            with col4:
                rep_max = st.number_input("Max. Reps", min_value=1, value=12, step=1)
            with col5:
                weight_inc = st.number_input("Gewichtsinkrement (kg)", min_value=0.25, value=1.25, step=0.25)

            pause_dur = st.number_input("Pausendauer (Sek.)", min_value=30, value=180, step=30)

            submitted = st.form_submit_button("Übung erstellen")

            if submitted:
                if ex_name.strip():
                    if rep_max < rep_min:
                        st.error("Max. Reps muss >= Min. Reps sein")
                    else:
                        try:
                            db.add_exercise(
                                ex_name.strip(),
                                ex_desc.strip(),
                                rep_min,
                                rep_max,
                                20.0,  # min_weight - default
                                pause_dur,
                                ex_type,
                                target_sets,
                                weight_inc
                            )
                            st.success(f"Übung '{ex_name}' erstellt")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Fehler: {e}")
                else:
                    st.warning("Bitte Namen eingeben")

    st.divider()

    # Alle Übungen anzeigen
    st.subheader("Alle Übungen")

    if not exercises:
        st.info("Keine Übungen vorhanden")
    else:
        for ex in exercises:
            type_labels = {'compound': 'C', 'isolation': 'I', 'machine': 'M'}
            type_label = type_labels.get(ex.get('exercise_type', 'compound'), 'C')

            with st.expander(f"[{type_label}] {ex['name']}", expanded=False):
                # Details anzeigen
                col1, col2 = st.columns(2)
                with col1:
                    type_full = {'compound': 'Compound', 'isolation': 'Isolation', 'machine': 'Maschine'}
                    st.markdown(f"**Typ:** [{type_label}] {type_full.get(ex.get('exercise_type', 'compound'), 'Compound')}")
                    st.markdown(f"**Rep-Range:** {ex.get('rep_range_min', 5)}-{ex.get('rep_range_max', 12)} Reps")
                    st.markdown(f"**Ziel-Sets:** {ex.get('target_sets', 3)}")
                with col2:
                    st.markdown(f"**Gewichtsinkrement:** {ex.get('weight_increment', 1.25)} kg")
                    st.markdown(f"**Pausendauer:** {ex.get('pause_duration', 180)} Sek.")

                if ex.get('description'):
                    st.caption(f"_{ex['description']}_")

                # Statistik-Link
                workouts = db.get_workouts_for_exercise(ex['id'])
                if workouts:
                    st.info(f"📊 {len(workouts)} Trainingseinheiten absolviert")

                st.divider()

                # Bearbeiten/Löschen
                col_edit, col_delete = st.columns(2)

                with col_edit:
                    edit_key = f"edit_ex_{ex['id']}"
                    if edit_key not in st.session_state:
                        st.session_state[edit_key] = False

                    if st.button("✎ Bearbeiten", key=f"btn_edit_{ex['id']}", use_container_width=True):
                        st.session_state[edit_key] = not st.session_state[edit_key]
                        st.rerun()

                with col_delete:
                    if st.button("🗑️ Löschen", key=f"btn_del_{ex['id']}", use_container_width=True):
                        try:
                            db.delete_exercise(ex['id'])
                            st.success("Übung gelöscht")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Fehler: {e}")

                # Bearbeiten-Dialog
                if st.session_state.get(edit_key, False):
                    with st.form(f"edit_form_{ex['id']}"):
                        st.markdown("### Übung bearbeiten")

                        new_name = st.text_input("Name*", value=ex['name'])
                        new_desc = st.text_area("Beschreibung", value=ex.get('description', ''))

                        col1, col2 = st.columns(2)
                        with col1:
                            new_type = st.selectbox(
                                "Übungstyp*",
                                options=['compound', 'isolation', 'machine'],
                                format_func=lambda x: {
                                    'compound': 'Compound (freie Grundübung)',
                                    'isolation': 'Isolation',
                                    'machine': 'Maschine'
                                }[x],
                                index=['compound', 'isolation', 'machine'].index(ex.get('exercise_type', 'compound')),
                                key=f"type_edit_{ex['id']}"
                            )
                        with col2:
                            new_target = st.number_input(
                                "Ziel-Sets",
                                min_value=1,
                                value=ex.get('target_sets', 3),
                                step=1,
                                key=f"sets_edit_{ex['id']}"
                            )

                        col3, col4, col5 = st.columns(3)
                        with col3:
                            new_rep_min = st.number_input(
                                "Min. Reps",
                                min_value=1,
                                value=ex.get('rep_range_min', 5),
                                step=1,
                                key=f"repmin_edit_{ex['id']}"
                            )
                        with col4:
                            new_rep_max = st.number_input(
                                "Max. Reps",
                                min_value=1,
                                value=ex.get('rep_range_max', 12),
                                step=1,
                                key=f"repmax_edit_{ex['id']}"
                            )
                        with col5:
                            new_inc = st.number_input(
                                "Gewichtsinkrement (kg)",
                                min_value=0.25,
                                value=ex.get('weight_increment', 1.25),
                                step=0.25,
                                key=f"inc_edit_{ex['id']}"
                            )

                        new_pause = st.number_input(
                            "Pausendauer (Sek.)",
                            min_value=30,
                            value=ex.get('pause_duration', 180),
                            step=30,
                            key=f"pause_edit_{ex['id']}"
                        )

                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            save = st.form_submit_button("💾 Speichern", use_container_width=True)
                        with col_cancel:
                            cancel = st.form_submit_button("❌ Abbrechen", use_container_width=True)

                        if save:
                            if new_name.strip():
                                try:
                                    db.update_exercise(
                                        ex['id'],
                                        name=new_name.strip(),
                                        description=new_desc.strip(),
                                        rep_range_min=new_rep_min,
                                        rep_range_max=new_rep_max,
                                        pause_duration=new_pause,
                                        exercise_type=new_type,
                                        target_sets=new_target,
                                        weight_increment=new_inc
                                    )
                                    st.session_state[edit_key] = False
                                    st.success("Übung aktualisiert")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Fehler: {e}")
                            else:
                                st.warning("Name darf nicht leer sein")

                        if cancel:
                            st.session_state[edit_key] = False
                            st.rerun()


def training_plans_page():
    st.header("Trainingspläne")

    # Neuen Plan erstellen
    with st.expander("➕ Neuer Plan erstellen", expanded=False):
        with st.form("add_plan_form"):
            plan_name = st.text_input("Name*", placeholder="z.B. Push Day")
            plan_desc = st.text_area("Beschreibung", placeholder="Optional...")
            submitted = st.form_submit_button("Erstellen")

            if submitted:
                if plan_name.strip():
                    try:
                        db.add_training_plan(plan_name.strip(), plan_desc.strip())
                        st.success(f"Plan '{plan_name}' erstellt")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {e}")
                else:
                    st.warning("Bitte Namen eingeben")

    st.divider()

    # Pläne anzeigen und bearbeiten
    st.subheader("Meine Pläne")
    plans = db.get_all_training_plans()

    if not plans:
        st.info("Keine Trainingspläne vorhanden")
    else:
        for plan in plans:
            with st.expander(f"📋 {plan['name']}", expanded=False):
                if plan['description']:
                    st.caption(plan['description'])

                plan_exercises = db.get_exercises_for_plan(plan['id'])

                # Übungen anzeigen mit Bearbeiten-Funktionen
                if plan_exercises:
                    st.markdown("**Übungen:**")
                    for i, ex in enumerate(plan_exercises, 1):
                        col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                        with col1:
                            rep_min = ex.get('rep_range_min', 5)
                            rep_max = ex.get('rep_range_max', 12)
                            target_sets = ex.get('target_sets', 3)
                            min_weight = ex.get('min_weight', 20.0)
                            ex_type = ex.get('exercise_type', 'compound')
                            type_label = {'compound': 'C', 'isolation': 'I', 'machine': 'M'}.get(ex_type, 'C')
                            st.text(f"{i}. [{type_label}] {ex['name']} | {target_sets}x {rep_min}-{rep_max} Reps | {min_weight}kg")
                        with col2:
                            # Reihenfolge ändern
                            col_up, col_down = st.columns(2)
                            with col_up:
                                if i > 1:  # Nicht beim ersten Element
                                    if st.button("↑", key=f"up_{plan['id']}_{ex['id']}"):
                                        db.move_exercise_in_plan(plan['id'], ex['id'], "up")
                                        st.rerun()
                            with col_down:
                                if i < len(plan_exercises):  # Nicht beim letzten Element
                                    if st.button("↓", key=f"down_{plan['id']}_{ex['id']}"):
                                        db.move_exercise_in_plan(plan['id'], ex['id'], "down")
                                        st.rerun()
                        with col3:
                            # Bearbeiten Button
                            edit_key = f"edit_{plan['id']}_{ex['id']}"
                            if edit_key not in st.session_state:
                                st.session_state[edit_key] = False
                            if st.button("✎", key=f"edit_btn_{plan['id']}_{ex['id']}"):
                                st.session_state[edit_key] = not st.session_state[edit_key]
                                st.rerun()
                        with col4:
                            if st.button("✕", key=f"remove_{plan['id']}_{ex['id']}"):
                                db.remove_exercise_from_plan(plan['id'], ex['id'])
                                st.rerun()

                        # Bearbeiten-Dialog
                        if st.session_state.get(f"edit_{plan['id']}_{ex['id']}", False):
                            with st.expander("✎ Übung bearbeiten", expanded=True):
                                with st.form(f"edit_exercise_form_{plan['id']}_{ex['id']}"):
                                    new_name = st.text_input("Name*", value=ex['name'])
                                    new_desc = st.text_area("Beschreibung", value=ex.get('description', ''))

                                    col1, col2 = st.columns(2)
                                    with col1:
                                        new_type = st.selectbox(
                                            "Übungstyp*",
                                            options=['compound', 'isolation', 'machine'],
                                            format_func=lambda x: {
                                                'compound': 'Compound (freie Grundübung)',
                                                'isolation': 'Isolation',
                                                'machine': 'Maschine'
                                            }[x],
                                            index=['compound', 'isolation', 'machine'].index(ex.get('exercise_type', 'compound'))
                                        )
                                    with col2:
                                        new_target_sets = st.number_input("Ziel-Sets", min_value=1, value=target_sets, step=1)

                                    col3, col4, col5 = st.columns(3)
                                    with col3:
                                        new_rep_min = st.number_input("Min. Reps", min_value=1, value=rep_min, step=1)
                                    with col4:
                                        new_rep_max = st.number_input("Max. Reps", min_value=1, value=rep_max, step=1)
                                    with col5:
                                        new_increment = st.number_input(
                                            "Gewichtsinkrement (kg)",
                                            min_value=0.25,
                                            value=ex.get('weight_increment', 1.25),
                                            step=0.25
                                        )

                                    new_pause = st.number_input(
                                        "Pausendauer (Sek.)",
                                        min_value=30,
                                        value=ex.get('pause_duration', 180),
                                        step=30
                                    )

                                    col_save, col_cancel = st.columns(2)
                                    with col_save:
                                        save_btn = st.form_submit_button("Speichern", use_container_width=True)
                                    with col_cancel:
                                        cancel_btn = st.form_submit_button("Abbrechen", use_container_width=True)

                                    if save_btn:
                                        if new_name.strip():
                                            try:
                                                db.update_exercise(
                                                    ex['id'],
                                                    name=new_name.strip(),
                                                    description=new_desc.strip(),
                                                    rep_range_min=new_rep_min,
                                                    rep_range_max=new_rep_max,
                                                    pause_duration=new_pause,
                                                    exercise_type=new_type,
                                                    target_sets=new_target_sets,
                                                    weight_increment=new_increment
                                                )
                                                st.session_state[f"edit_{plan['id']}_{ex['id']}"] = False
                                                st.success(f"'{new_name}' aktualisiert")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Fehler: {e}")
                                        else:
                                            st.warning("Name darf nicht leer sein")

                                    if cancel_btn:
                                        st.session_state[f"edit_{plan['id']}_{ex['id']}"] = False
                                        st.rerun()
                else:
                    st.caption("Noch keine Übungen")

                # Übung hinzufügen
                st.divider()
                with st.expander("➕ Übung hinzufügen", expanded=False):
                    add_mode = st.radio(
                        "Modus:",
                        ["Bestehende Übung", "Neue Übung erstellen"],
                        key=f"add_mode_{plan['id']}"
                    )

                    if add_mode == "Bestehende Übung":
                        # Alle Übungen abrufen
                        all_exercises = db.get_all_exercises()
                        # Bereits im Plan vorhandene Übungen filtern
                        plan_exercise_ids = [ex['id'] for ex in plan_exercises] if plan_exercises else []
                        available_exercises = [ex for ex in all_exercises if ex['id'] not in plan_exercise_ids]

                        if not available_exercises:
                            st.info("Alle vorhandenen Übungen sind bereits im Plan")
                        else:
                            with st.form(f"add_existing_form_{plan['id']}"):
                                type_labels = {'compound': 'C', 'isolation': 'I', 'machine': 'M'}
                                exercise_dict = {f"{ex['name']} [{type_labels.get(ex.get('exercise_type', 'compound'), 'C')}]": ex['id']
                                               for ex in available_exercises}
                                selected_exercise = st.selectbox(
                                    "Übung auswählen:",
                                    options=list(exercise_dict.keys())
                                )
                                add_btn = st.form_submit_button("Zum Plan hinzufügen")

                                if add_btn and selected_exercise:
                                    try:
                                        ex_id = exercise_dict[selected_exercise]
                                        db.add_exercise_to_plan(plan['id'], ex_id, len(plan_exercises))
                                        st.success(f"Übung hinzugefügt")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Fehler: {e}")

                    else:  # Neue Übung erstellen
                        with st.form(f"add_exercise_form_{plan['id']}"):
                            exercise_name = st.text_input("Name*", placeholder="z.B. Bankdrücken")
                            exercise_desc = st.text_area("Beschreibung", placeholder="Optional...")

                            col1, col2 = st.columns(2)
                            with col1:
                                exercise_type = st.selectbox(
                                    "Übungstyp*",
                                    options=['compound', 'isolation', 'machine'],
                                    format_func=lambda x: {
                                        'compound': 'Compound (freie Grundübung)',
                                        'isolation': 'Isolation',
                                        'machine': 'Maschine'
                                    }[x],
                                    index=0,
                                    key=f"type_{plan['id']}"
                                )
                            with col2:
                                target_sets = st.number_input("Ziel-Sets", min_value=1, value=3, step=1, key=f"sets_{plan['id']}")

                            col3, col4, col5 = st.columns(3)
                            with col3:
                                rep_min = st.number_input("Min. Reps", min_value=1, value=5, step=1, key=f"repmin_{plan['id']}")
                            with col4:
                                rep_max = st.number_input("Max. Reps", min_value=1, value=12, step=1, key=f"repmax_{plan['id']}")
                            with col5:
                                weight_increment = st.number_input(
                                    "Gewichtsinkrement (kg)",
                                    min_value=0.25,
                                    value=1.25,
                                    step=0.25,
                                    key=f"increment_{plan['id']}"
                                )

                            pause_duration = st.number_input(
                                "Pausendauer (Sek.)",
                                min_value=30,
                                value=180,
                                step=30,
                                key=f"pause_{plan['id']}"
                            )

                            submitted = st.form_submit_button("Übung erstellen")

                            if submitted:
                                if exercise_name.strip():
                                    if rep_max < rep_min:
                                        st.error("Max. Reps muss >= Min. Reps sein")
                                    else:
                                        try:
                                            # Übung erstellen
                                            ex_id = db.add_exercise(
                                                exercise_name.strip(),
                                                exercise_desc.strip(),
                                                rep_min,
                                                rep_max,
                                                20.0,  # min_weight - default
                                                pause_duration,
                                                exercise_type,
                                                target_sets,
                                                weight_increment
                                            )
                                            # Direkt zum Plan hinzufügen
                                            db.add_exercise_to_plan(plan['id'], ex_id, len(plan_exercises))
                                            st.success(f"Übung '{exercise_name}' erstellt")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Fehler: {e}")
                                else:
                                    st.warning("Bitte Namen eingeben")

                # Plan löschen
                st.divider()
                if st.button("🗑️ Plan löschen", key=f"delete_plan_{plan['id']}"):
                    db.delete_training_plan(plan['id'])
                    st.rerun()


def training_page():
    st.header("Trainieren")

    plans = db.get_all_training_plans()

    if not plans:
        st.warning("Erstelle zuerst einen Trainingsplan unter 'Trainingspläne'")
        return

    # Wenn Training nicht aktiv: Plan auswählen
    if not st.session_state.training_active:
        plan_names = {plan['name']: plan['id'] for plan in plans}
        selected_plan_name = st.selectbox(
            "Trainingsplan:",
            options=list(plan_names.keys())
        )
        selected_plan_id = plan_names[selected_plan_name]

        # Übungen aus dem Plan
        plan_exercises = db.get_exercises_for_plan(selected_plan_id)

        if not plan_exercises:
            st.warning("Dieser Plan enthält noch keine Übungen")
            return

        # Starten Button
        if st.button("Starten", type="primary", use_container_width=True):
            st.session_state.training_active = True
            st.session_state.active_plan_id = selected_plan_id
            # Erstelle Workouts für alle Übungen
            st.session_state.exercise_sets = {}
            for exercise in plan_exercises:
                workout_id = db.create_workout(exercise['id'], selected_plan_id)
                st.session_state.exercise_sets[exercise['id']] = {
                    'workout_id': workout_id,
                    'sets': []
                }
            st.rerun()

    # Wenn Training aktiv: Zeige alle Übungen
    else:
        plan_exercises = db.get_exercises_for_plan(st.session_state.active_plan_id)

        # Übungen anzeigen
        for exercise in plan_exercises:
            exercise_id = exercise['id']
            exercise_info = db.get_exercise_by_id(exercise_id)

            st.divider()
            st.subheader(exercise['name'])

            # 🟨 ZIELGEWICHT FÜR DIE GESAMTE SESSION
            # Berechne Zielgewicht VOR der Session (nur einmal, dann konstant halten)
            target_key = f"session_target_{exercise_id}"

            if target_key not in st.session_state or not st.session_state.exercise_sets[exercise_id]['sets']:
                # Berechne neues Ziel (nur beim Start der Session)
                last_sessions = db.get_last_n_sessions(exercise_id, 3)
                suggestion = calculate_session_target(last_sessions, exercise_info)
                st.session_state[target_key] = suggestion
            else:
                # Verwende gespeichertes Ziel (während der Session)
                suggestion = st.session_state[target_key]

            # Zwei Spalten: Links Sets, Rechts Soll-Werte
            col_left, col_right = st.columns([3, 1])

            with col_right:
                st.markdown("**Session-Ziel**")

                # Zeige Fortschritt (X von Y Sets)
                current_sets_count = len(st.session_state.exercise_sets[exercise_id]['sets'])
                target_sets_count = exercise_info.get('target_sets', 3)
                st.caption(f"Set {current_sets_count + 1} von {target_sets_count}")

                # Zielgewicht & Reps
                st.metric("Gewicht", f"{suggestion['weight']} kg")
                st.metric("Reps", suggestion['reps'])
                rep_min = exercise_info.get('rep_range_min', 5)
                rep_max = exercise_info.get('rep_range_max', 12)
                st.caption(f"Rep-Range: {rep_min}-{rep_max}")

                # Zeige Progression und RPE-Info
                if 'progression_percent' in suggestion:
                    prog_pct = suggestion['progression_percent']
                    if prog_pct != 0:
                        delta_color = "normal" if prog_pct > 0 else "inverse"
                        st.caption(f"Progression: {prog_pct:+.1f}%")
                    if 'weighted_rpe' in suggestion:
                        st.caption(f"Ø-RPE (3 Sessions): {suggestion['weighted_rpe']:.1f}")

                # Suggestion-Text
                st.info(suggestion['suggestion'])

                # Berechne 1RM vom letzten Set (falls vorhanden)
                if st.session_state.exercise_sets[exercise_id]['sets']:
                    last_set = st.session_state.exercise_sets[exercise_id]['sets'][-1]
                    est_1rm = calculate_estimated_1rm(
                        last_set['weight'],
                        last_set['reps'],
                        last_set.get('rpe')
                    )
                    st.metric("Est. 1RM", f"{est_1rm} kg")

                # Timer direkt hier anzeigen
                st.divider()
                st.markdown("**Pause**")
                if st.session_state.timer_start is not None:
                    elapsed = int(time.time() - st.session_state.timer_start)
                    remaining = max(0, st.session_state.timer_duration - elapsed)

                    if remaining > 0:
                        progress = elapsed / st.session_state.timer_duration
                        st.progress(min(progress, 1.0))
                        st.markdown(f"### {format_timer(remaining)}")
                        if st.button("Stop", key=f"stop_timer_{exercise_id}", use_container_width=True):
                            st.session_state.timer_start = None
                            st.rerun()
                        # Auto-refresh für Timer
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.success("Bereit!")
                        st.session_state.timer_start = None
                else:
                    st.info("Startet nach Set")

            with col_left:
                # Set-Eingabe
                with st.form(f"set_form_{exercise_id}", clear_on_submit=True):
                    cols = st.columns([2, 2, 2, 3])

                    with cols[0]:
                        weight = st.number_input(
                            "Gewicht (kg)",
                            min_value=0.0,
                            value=suggestion['weight'],
                            step=1.25,
                            key=f"weight_{exercise_id}"
                        )
                    with cols[1]:
                        reps = st.number_input(
                            "Reps",
                            min_value=1,
                            value=suggestion['reps'],
                            step=1,
                            key=f"reps_{exercise_id}"
                        )
                    with cols[2]:
                        rpe = st.number_input(
                            "RPE",
                            min_value=0.0,
                            max_value=10.0,
                            value=8.0,
                            step=0.5,
                            key=f"rpe_{exercise_id}"
                        )
                    with cols[3]:
                        notes = st.text_input("Notizen", key=f"notes_{exercise_id}")

                    submitted = st.form_submit_button("Set hinzufügen")

                    if submitted:
                        workout_id = st.session_state.exercise_sets[exercise_id]['workout_id']
                        set_number = len(st.session_state.exercise_sets[exercise_id]['sets']) + 1

                        db.add_set(
                            workout_id,
                            set_number,
                            weight,
                            reps,
                            rpe if rpe > 0 else None,
                            notes
                        )

                        st.session_state.exercise_sets[exercise_id]['sets'].append({
                            'set_number': set_number,
                            'weight': weight,
                            'reps': reps,
                            'rpe': rpe,
                            'notes': notes
                        })

                        # Timer starten
                        pause_duration = exercise_info.get('pause_duration', 180)
                        st.session_state.timer_duration = pause_duration
                        st.session_state.timer_start = time.time()
                        st.rerun()

                # Zeige eingetragene Sets
                if st.session_state.exercise_sets[exercise_id]['sets']:
                    st.markdown("**Absolvierte Sets:**")
                    sets_df = pd.DataFrame(st.session_state.exercise_sets[exercise_id]['sets'])
                    sets_df['Volumen'] = sets_df['weight'] * sets_df['reps']
                    st.dataframe(
                        sets_df[['set_number', 'weight', 'reps', 'rpe', 'Volumen', 'notes']].rename(columns={
                            'set_number': 'Set',
                            'weight': 'Gewicht',
                            'reps': 'Reps',
                            'rpe': 'RPE',
                            'notes': 'Notizen'
                        }),
                        use_container_width=True,
                        hide_index=True
                    )

        # Training beenden
        st.divider()
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Training beenden", type="primary", use_container_width=True):
                st.session_state.training_active = False
                st.session_state.active_plan_id = None
                st.session_state.exercise_sets = {}
                st.session_state.timer_start = None

                # Session-Ziele zurücksetzen
                keys_to_remove = [k for k in st.session_state.keys() if k.startswith('session_target_')]
                for key in keys_to_remove:
                    del st.session_state[key]

                st.success("Training beendet")
                time.sleep(1)
                st.rerun()


def render_rest_timer():
    st.subheader("Pause Timer")

    # Timer Anzeige
    if st.session_state.timer_start is not None:
        elapsed = int(time.time() - st.session_state.timer_start)
        remaining = max(0, st.session_state.timer_duration - elapsed)

        if remaining > 0:
            progress = elapsed / st.session_state.timer_duration
            st.progress(min(progress, 1.0))
            st.markdown(f"### {format_timer(remaining)}")

            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("Stop", use_container_width=True):
                    st.session_state.timer_start = None
                    st.rerun()

            time.sleep(1)
            st.rerun()
        else:
            st.success("Pause beendet")
            st.session_state.timer_start = None
    else:
        st.info("Timer startet automatisch nach jedem Set")


def statistics_page():
    st.header("Statistiken")

    exercises = db.get_all_exercises()

    if not exercises:
        st.warning("Keine Übungen vorhanden. Erstelle Übungen in deinen Trainingsplänen.")
        return

    # Hole alle Trainingstage (über alle Übungen)
    all_workouts = []
    for ex in exercises:
        workouts = db.get_workouts_for_exercise(ex['id'])
        all_workouts.extend(workouts)

    if not all_workouts:
        st.info("Keine Trainingsdaten vorhanden")
        return

    # Extrahiere unique Trainingstage
    workout_dates = sorted(list(set([pd.to_datetime(w['date']).date() for w in all_workouts])))

    # KALENDER-ANSICHT
    st.subheader("Trainingskalender")

    if workout_dates:
        # Berechne Trainingsfrequenz (letzte 4 Wochen vs. davor)
        from datetime import date, timedelta
        import calendar
        today = date.today()
        four_weeks_ago = today - timedelta(weeks=4)
        eight_weeks_ago = today - timedelta(weeks=8)

        recent_days = [d for d in workout_dates if d > four_weeks_ago]
        older_days = [d for d in workout_dates if eight_weeks_ago < d <= four_weeks_ago]

        recent_freq = len(recent_days) / 4  # Pro Woche
        older_freq = len(older_days) / 4 if older_days else recent_freq

        freq_change = recent_freq - older_freq
        freq_trend = "📈 Steigend" if freq_change > 0.2 else "📉 Sinkend" if freq_change < -0.2 else "➡️ Stabil"

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Letzte 4 Wochen", f"{len(recent_days)} Tage", f"{recent_freq:.1f}x/Woche")
        with col2:
            st.metric("Frequenz-Trend", freq_trend)
        with col3:
            st.metric("Gesamt Trainingstage", len(workout_dates))

        # Monatskalender-Ansicht (aktueller + letzter Monat)
        def create_month_calendar(year, month, workout_dates_set):
            """Erstellt einen Monatskalender als HTML-Tabelle"""
            cal = calendar.monthcalendar(year, month)
            month_name = calendar.month_name[month]

            html = f"<div style='margin: 10px 0;'>"
            html += f"<h4 style='text-align: center;'>{month_name} {year}</h4>"
            html += "<table style='width: 100%; border-collapse: collapse; text-align: center;'>"
            html += "<tr>"
            for day in ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']:
                html += f"<th style='padding: 8px; background-color: #f0f0f0; border: 1px solid #ddd;'>{day}</th>"
            html += "</tr>"

            for week in cal:
                html += "<tr>"
                for day in week:
                    if day == 0:
                        html += "<td style='padding: 8px; border: 1px solid #ddd;'></td>"
                    else:
                        day_date = date(year, month, day)
                        is_today = day_date == today
                        is_workout = day_date in workout_dates_set

                        bg_color = '#4CAF50' if is_workout else '#ffffff'
                        text_color = '#ffffff' if is_workout else '#000000'
                        border = '3px solid #2196F3' if is_today else '1px solid #ddd'
                        font_weight = 'bold' if is_today else 'normal'

                        html += f"<td style='padding: 8px; background-color: {bg_color}; color: {text_color}; border: {border}; font-weight: {font_weight};'>{day}</td>"
                html += "</tr>"

            html += "</table></div>"
            return html

        workout_dates_set = set(workout_dates)

        # Zeige aktuellen und vorherigen Monat
        current_month = today.month
        current_year = today.year

        prev_month = current_month - 1 if current_month > 1 else 12
        prev_year = current_year if current_month > 1 else current_year - 1

        col_cal1, col_cal2 = st.columns(2)
        with col_cal1:
            st.markdown(create_month_calendar(prev_year, prev_month, workout_dates_set), unsafe_allow_html=True)
        with col_cal2:
            st.markdown(create_month_calendar(current_year, current_month, workout_dates_set), unsafe_allow_html=True)

    st.divider()

    # FORTSCHRITTS-ANALYSE
    st.subheader("Fortschritts-Analyse")

    # Übungsauswahl direkt über dem Diagramm
    exercise_names = {ex['name']: ex['id'] for ex in exercises}
    selected_exercise_name = st.selectbox(
        "Übung auswählen:",
        options=list(exercise_names.keys()),
        key="stats_exercise"
    )
    selected_exercise_id = exercise_names[selected_exercise_name]
    exercise_info = db.get_exercise_by_id(selected_exercise_id)
    history_df = db.get_exercise_history(selected_exercise_id)

    # STAGNATIONS-WARNUNG
    if not history_df.empty and len(history_df) >= 6:
        deload_check = check_deload_triggers(history_df, exercise_info)
        if deload_check['needs_deload']:
            st.error(f"⚠️ **WARNUNG: {deload_check['reason']}**")
            st.warning(f"📉 Empfehlung: {deload_check['recommendation']}")

    if history_df.empty:
        st.info("Keine Trainingsdaten für diese Übung")
        return

    # Berechne e1RM für jeden Eintrag
    history_df['e1rm'] = history_df.apply(
        lambda row: calculate_estimated_1rm(row['weight'], row['reps'], row['rpe']),
        axis=1
    )

    # Gruppiere nach Datum (Top-Set pro Tag)
    daily_data = history_df.groupby('date').agg({
        'weight': 'max',
        'reps': 'max',
        'rpe': 'mean',
        'e1rm': 'max'
    }).reset_index()
    daily_data = daily_data.sort_values('date')
    daily_data['date_dt'] = pd.to_datetime(daily_data['date'])

    # Erstelle Plot - immer historische Daten zeigen
    plot_df = daily_data[['date_dt', 'e1rm']].copy()
    plot_df.columns = ['date', 'e1rm']
    plot_df['type'] = 'Ist'

    # Prognose nur wenn genug Daten (mindestens 4 Trainingseinheiten)
    has_prognosis = len(daily_data) >= 4

    if has_prognosis:
        # Berechne durchschnittliche e1RM-Steigerung pro Woche
        days_span = (daily_data['date_dt'].max() - daily_data['date_dt'].min()).days
        weeks_span = max(days_span / 7, 1)

        e1rm_start = daily_data.iloc[0]['e1rm']
        e1rm_end = daily_data.iloc[-1]['e1rm']
        weekly_increase = (e1rm_end - e1rm_start) / weeks_span if weeks_span > 0 else 0

        # Erstelle Prognose für nächste 3 Wochen
        last_date = daily_data['date_dt'].max()
        prognosis_data = []

        for week in range(1, 4):
            future_date = last_date + timedelta(weeks=week)
            projected_e1rm = e1rm_end + (weekly_increase * week)
            prognosis_data.append({
                'date': future_date,
                'e1rm': projected_e1rm,
                'type': 'Prognose'
            })

        prog_df = pd.DataFrame(prognosis_data)
        combined_df = pd.concat([plot_df, prog_df], ignore_index=True)

        title = f'e1RM Fortschritt + 3-Wochen-Prognose'
    else:
        combined_df = plot_df
        title = f'e1RM Fortschritt'

    # Visualisierung
    fig = px.line(
        combined_df,
        x='date',
        y='e1rm',
        color='type',
        title=title,
        markers=True,
        color_discrete_map={'Ist': 'blue', 'Prognose': 'orange'}
    )
    fig.update_layout(
        xaxis_title="Datum",
        yaxis_title="Geschätztes 1RM (kg)",
        template="plotly_white",
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)

    # Metriken
    e1rm_start = daily_data.iloc[0]['e1rm']
    e1rm_end = daily_data.iloc[-1]['e1rm']

    if has_prognosis:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Aktuelles e1RM", f"{e1rm_end:.1f} kg")
        with col2:
            st.metric("Steigerung/Woche", f"{weekly_increase:.2f} kg")
        with col3:
            projected_3w = e1rm_end + (weekly_increase * 3)
            st.metric("Prognose (3 Wochen)", f"{projected_3w:.1f} kg")
        with col4:
            total_gain = e1rm_end - e1rm_start
            st.metric("Gesamt-Zuwachs", f"+{total_gain:.1f} kg")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Aktuelles e1RM", f"{e1rm_end:.1f} kg")
        with col2:
            st.metric("Erstes e1RM", f"{e1rm_start:.1f} kg")
        with col3:
            total_gain = e1rm_end - e1rm_start
            st.metric("Zuwachs", f"+{total_gain:.1f} kg")
        st.info("💡 Mindestens 4 Trainingseinheiten nötig für 3-Wochen-Prognose")


def export_page():
    st.header("Export")

    exercises = db.get_all_exercises()

    if not exercises:
        st.warning("Keine Daten vorhanden. Erstelle Trainingspläne und Übungen oder lade Demo-Daten.")
        return

    st.subheader("CSV Export")

    export_option = st.radio(
        "Export-Umfang:",
        ["Alle Übungen", "Spezifische Übung"]
    )

    if export_option == "Spezifische Übung":
        exercise_names = {ex['name']: ex['id'] for ex in exercises}
        selected_exercise_name = st.selectbox(
            "Übung:",
            options=list(exercise_names.keys())
        )
        selected_exercise_id = exercise_names[selected_exercise_name]
        export_df = db.export_to_csv(selected_exercise_id)
        filename = f"{selected_exercise_name.replace(' ', '_')}_export.csv"
    else:
        export_df = db.export_to_csv()
        filename = "alle_uebungen_export.csv"

    if export_df.empty:
        st.info("Keine Daten vorhanden")
    else:
        st.write(f"Vorschau ({len(export_df)} Zeilen):")
        st.dataframe(export_df.head(20), use_container_width=True)

        csv = export_df.to_csv(index=False).encode('utf-8')

        st.download_button(
            label="CSV herunterladen",
            data=csv,
            file_name=filename,
            mime='text/csv'
        )


if __name__ == "__main__":
    main()
