import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import plotly.graph_objects as go
import numpy as np

from database.session_store import (
    ensure_session_state,
    save_component_state,
    save_employee_settings,
    save_project_allocations,
    save_team_data,
)
from logic.team_service import (
    build_team_dataframe,
    calculate_kt_status_from_tenure,
    calculate_priority_from_tenure,
    get_kt_status_mapping,
    update_priorities_from_tenure,
)
from ui.theme import (
    get_colors as shared_get_colors,
    load_theme as shared_load_theme,
    render_sidebar_navigation as shared_render_sidebar_navigation,
)

# SEITENKONFIGURATION - MUSS DER ERSTE STREAMLIT-BEFEHL SEIN
st.set_page_config(
    page_title="AURA Executive Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Centralized initialization for shared application state
ensure_session_state()

# Color palette function based on the fixed app theme
def get_colors():
    """Return the shared executive color palette."""
    return shared_get_colors()

# THEMA
def load_theme():
    """Load the shared light executive theme."""
    shared_load_theme()

load_theme()


# Shared defaults now live in `database.session_store`.

def parse_component_names(value):
    """Normalize component values into a clean string list."""
    if isinstance(value, (list, tuple, set)):
        raw_items = value
    else:
        raw_items = str(value or "").split(",")
    return [str(item).strip() for item in raw_items if str(item).strip()]


def sync_master_data_to_legacy_state():
    """Keep experimental master-data records in sync with legacy dashboard state."""
    st.session_state.setdefault("products_data", [])
    st.session_state.setdefault("components_data", [])

    if not st.session_state.components_data:
        return

    component_map = {}
    component_products = {}
    component_requirements = {}
    component_transfer_times = {}

    for component in st.session_state.components_data:
        component_name = str(component.get("component_name", "")).strip()
        if not component_name:
            continue

        responsible_people = parse_component_names(component.get("responsible_persons", []))
        component_map[component_name] = responsible_people
        component_products[component_name] = component.get("product_name", "Unknown")
        component_requirements[component_name] = int(component.get("required_resources", 1))
        component_transfer_times[component_name] = int(component.get("knowledge_transfer_time_needed", 6))

    st.session_state.component_map = component_map
    st.session_state.component_products = component_products
    st.session_state.component_requirements = component_requirements
    st.session_state.component_transfer_times = component_transfer_times

    for product in st.session_state.products_data:
        product_name = str(product.get("product_name", "")).strip()
        if not product_name:
            continue
        product["components"] = sorted(
            component_name
            for component_name, mapped_product in component_products.items()
            if mapped_product == product_name
        )


def get_active_component_assignments(frame: pd.DataFrame, component_name: str, responsible_list: list[str]) -> list[dict]:
    """Return active employees mapped to a component and the matching assignment."""
    if frame.empty:
        return []

    matches = []
    component_key = component_name.strip().lower()

    for _, row in frame.iterrows():
        person_name = str(row.get("name", "")).strip()
        person_components = parse_component_names(row.get("components", ""))
        matched_components = [item for item in person_components if item.strip().lower() == component_key]

        if matched_components or person_name in responsible_list:
            matches.append(
                {
                    "name": person_name,
                    "matched_components": matched_components or [component_name],
                }
            )

    return matches


def render_sidebar_navigation() -> None:
    """Render the single sidebar navigation block for the dashboard."""
    shared_render_sidebar_navigation()


def main():
    sync_master_data_to_legacy_state()

    # Update priorities based on tenure at the start of each run
    update_priorities_from_tenure(st.session_state.team_data)
    render_sidebar_navigation()
    
    # KOPFZEILE
    st.markdown('<h1 class="main-header">🏢 AURA </h1>', unsafe_allow_html=True)
    colors = get_colors()
    
    # Initialize component map
    if 'component_map' not in st.session_state:
        st.session_state.component_map = {}
    # Anzahl benötigter Personen pro Komponente
    if 'component_requirements' not in st.session_state:
        st.session_state.component_requirements = {}

    # Wissensübergabe Zeiten pro Komponente
    if 'component_transfer_times' not in st.session_state:
        st.session_state.component_transfer_times = {}

    
    # Convert to DataFrame via the logic layer
    df = build_team_dataframe(st.session_state.team_data)
    critical_cases_df = df[df['days_until_exit'] < 180].sort_values('days_until_exit') if not df.empty else pd.DataFrame()
    component_rows = []

    if 'component_map' in st.session_state and st.session_state.component_map:
        today = pd.Timestamp.today().normalize()
        for component, responsible in st.session_state.component_map.items():
            responsible_list = responsible if isinstance(responsible, (list, tuple)) else [responsible]
            comp_key = component.strip().lower()
            active_count = 0

            for _, row in df.iterrows():
                name = str(row.get('name', '')).strip()
                comps_field = row.get('components', '') or ''
                comps = [c.strip().lower() for c in str(comps_field).split(',') if c.strip()]

                try:
                    sd = pd.to_datetime(row['start_date'])
                except Exception:
                    continue
                pe = pd.to_datetime(row.get('planned_exit'))

                started = sd <= today
                not_left = pd.isna(pe) or (pe > today)
                assigned = (comp_key in comps) or (name in responsible_list)
                if assigned and started and not_left:
                    active_count += 1

            required = int(st.session_state.component_requirements.get(component, 1))
            if active_count == 0:
                status = "UNBESETZT"
            elif active_count < required:
                status = "UNTERBESETZT - SINGLE" if active_count == 1 else "UNTERBESETZT"
            else:
                status = "OK"

            component_rows.append(
                {
                    "Komponente": component,
                    "Verantwortlich": ", ".join(responsible_list),
                    "Aktive Ressourcen": active_count,
                    "Benötigt": required,
                    "Status": status,
                }
            )

    comp_df = pd.DataFrame(component_rows).sort_values(["Status", "Komponente"], ascending=[True, True]) if component_rows else pd.DataFrame()

    total_members = len(df)
    critical_cases = len(critical_cases_df)
    urgent_cases = len(df[df['days_until_exit'] < 90]) if not df.empty else 0
    completed_kt = len(df[df['knowledge_transfer_status'] == "Completed"]) if not df.empty else 0
    kt_completion_rate = int((completed_kt / total_members) * 100) if total_members else 0
    staffing_gap_count = len(comp_df[comp_df['Status'] != 'OK']) if not comp_df.empty else 0

    # EXECUTIVE SNAPSHOT
    colors = get_colors()
    st.markdown("---")
    st.caption(f"Stand: {pd.Timestamp.today().strftime('%d.%m.%Y')} • Fokus auf Kapazität, Risiko und Kontinuität")
    st.markdown('<h3 class="section-header">📊 Executive Snapshot</h3>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin:0; color: {colors['primary']};">👥</h3>
            <h2 style="margin:0; color: {colors['primary']};">{total_members}</h2>
            <p style="margin:0; color: {colors['text_secondary']};">Aktive Teammitglieder</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin:0; color: {colors['info']};">🚨</h3>
            <h2 style="margin:0; color: {colors['info']};">{critical_cases}</h2>
            <p style="margin:0; color: {colors['text_secondary']};">Kritische Exits (&lt; 180 Tage)</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin:0; color: {colors['success']};">✅</h3>
            <h2 style="margin:0; color: {colors['success']};">{kt_completion_rate}%</h2>
            <p style="margin:0; color: {colors['text_secondary']};">KT-Abschlussquote</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin:0; color: {colors['warning']};">🧩</h3>
            <h2 style="margin:0; color: {colors['warning']};">{staffing_gap_count}</h2>
            <p style="margin:0; color: {colors['text_secondary']};">Komponenten mit Besetzungsrisiko</p>
        </div>
        """, unsafe_allow_html=True)

    top_risk = "Keine unmittelbare Eskalation" if critical_cases_df.empty else f"{critical_cases_df.iloc[0]['name']} ({critical_cases_df.iloc[0]['role']})"
    continuity_message = "Alle Kernkomponenten sind aktuell ausreichend besetzt." if staffing_gap_count == 0 else f"{staffing_gap_count} Komponenten brauchen kurzfristige Aufmerksamkeit."
    alert_border = colors['success'] if staffing_gap_count == 0 and urgent_cases == 0 else colors['warning']
    st.markdown(f"""
    <div style="border-left: 6px solid {alert_border}; padding: 1rem 1.2rem; border-radius: 12px; background: rgba(77, 208, 225, 0.08); margin-top: 0.5rem;">
        <h4 style="margin: 0 0 0.6rem 0;">🎯 Executive Briefing</h4>
        <p style="margin: 0 0 0.35rem 0;"><b>Top-Risiko:</b> {top_risk}</p>
        <p style="margin: 0 0 0.35rem 0;"><b>Kontinuität:</b> {continuity_message}</p>
        <p style="margin: 0;"><b>Heute priorisieren:</b> {urgent_cases} hochkritische Fälle unter 90 Tagen.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # CRITICAL ALERTS SECTION  
    st.markdown("---")
    st.markdown('<h3 class="section-header">🔷 Kritische Ressourcenwarnungen</h3>', unsafe_allow_html=True)
    
    if not df.empty:
        critical_cases = df[df['days_until_exit'] < 180].sort_values('days_until_exit')
        
        if not critical_cases.empty:
            for _, person in critical_cases.iterrows():
                # Turquoise blue color coding based on urgency
                
                if person['days_until_exit'] < 90:
                    urgency_color = "#FF4D4F"  # Red
                    urgency_bg = "#FF4D4F"
                    urgency_text = "EXTREMELY URGENT"
                elif person['days_until_exit'] < 180:
                    urgency_color = "#FFA500"  # Orange
                    urgency_bg = "#FFA500"
                    urgency_text = "URGENT"
                elif person['days_until_exit'] < 365:
                    urgency_color = "#FFD700"  # Gold
                    urgency_bg = "#FFD700"
                    urgency_text = "Monitor"
                else:
                    urgency_color = "#52C41A"  # Green

                
                st.markdown(f"""
                <div class="critical-alert">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <h4 style="margin:0; color: {urgency_color};">🔷 {person['name']} - {person['role']}</h4>
                            <p style="margin:0.3rem 0;"><b>Status: {urgency_text} - Leaves in {person['days_until_exit']} days</b></p>
                            <p style="margin:0.3rem 0;">Components: {person['components']}</p>
                            <p style="margin:0.3rem 0;">Wissensübergabe: <b>{person['knowledge_transfer_status']}</b> | Priorität: <b>{person['priority']}</b></p>
                        </div>
                        <div style="background-color: {urgency_bg}; color: white; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: bold;">
                            {person['days_until_exit']} days
                        </div>
                    </div>
                    <p style="margin:0.5rem 0 0 0; font-style: italic;">💡 Empfohlene Maßnahme: Ressourcenaufbau bald starten</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ Keine kritischen Personalengpässe in den nächsten 6 Monaten")
    else:
        st.info("ℹ️ Keine Teamdaten verfügbar. Fügen Sie Teammitglieder hinzu, um kritische Warnungen zu sehen.")
    
    # COMPONENT-SPECIFIC CRITICAL ALERTS (Color-coded)
    if not comp_df.empty:
        def status_style(val):
            if val == "UNBESETZT":
                return "background-color: #ff4d4f; color: white; font-weight: bold"
            if val == "UNTERBESETZT - SINGLE":
                return "background-color: #ff4d4f; color: white; font-weight: bold"
            if val == "UNTERBESETZT":
                return "background-color: #fa8c16; color: white; font-weight: bold"
            if val == "OK":
                return "background-color: #52c41a; color: white; font-weight: bold"
            return ""

        styled_comp_df = comp_df.style.applymap(lambda v: status_style(v), subset=["Status"])
        st.markdown("#### 🧩 Komponentenübersicht & Staffing-Status")
        st.dataframe(styled_comp_df, use_container_width=True)
    else:
        st.info("ℹ️ Keine Komponenten zugewiesen.")

    
    # VISUALIZATIONS ROW
    if not df.empty:
        st.markdown("---")
        st.markdown('<h3 class="section-header">📈 Strategische Übersicht</h3>', unsafe_allow_html=True)
        
        # grouping control
        group_by = st.selectbox("Group timeline by", ["Name", "Team"], index=0, help="Wähle, ob die Timeline pro Person oder pro Team gruppiert werden soll.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Enhanced Timeline Gantt Chart
            y_axis = "name" if group_by == "Name" else "team"
            colors = get_colors()
            fig_timeline = px.timeline(df, x_start="start_date", x_end="planned_exit", y=y_axis,
                                     color="priority", 
                                     hover_data=["name", "role"] if y_axis == "team" else ["role"],
                                     title="Zeitplan der Teammitglieder (Farbe nach Priorität)",
                                     color_discrete_map={
                                         "Critical": "#d40000",
                                         "High": "#ED8727", 
                                         "Medium": "#4dd0e1",
                                         "Low": "#4FCA11"
                                     })
            fig_timeline.update_layout(
                height=450,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color=colors['text'])
            )
            fig_timeline.update_xaxes(gridcolor=colors['border'])
            fig_timeline.update_yaxes(gridcolor=colors['border'])
            st.plotly_chart(fig_timeline, use_container_width=True)

            # Altersverteilung nach Gruppen (jetzt links)
            if 'age' in df.columns and not df['age'].dropna().empty:
                ages = df['age'].dropna().astype(int)
                # Age groups up to 65 — remove the separate '65+' label
                bins = [0, 24, 34, 44, 54, 64]
                labels = ["<25", "25-34", "35-44", "45-54", "55-64"]
                age_groups = pd.cut(ages, bins=bins, labels=labels, right=True, include_lowest=True)
                age_counts = age_groups.value_counts().reindex(labels).fillna(0).astype(int)
                fig_age = px.bar(
                    x=age_counts.index,
                    y=age_counts.values,
                    labels={'x': 'Altersgruppe', 'y': 'Anzahl'},
                    title="Altersverteilung (Gruppen)"
                )
                fig_age.update_layout(height=300, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_age, use_container_width=True)
            else:
                st.info("ℹ️ Keine Altersdaten vorhanden.")
        
        with col2:
            # Risk Assessment Donut Chart
            status_counts = df['knowledge_transfer_status'].value_counts()
            fig_donut = px.pie(values=status_counts.values, names=status_counts.index, 
                              title="Status der Wissensübergabe Overview",
                              hole=0.4,
                              color=status_counts.index,
                              color_discrete_map={
                                  "Not Started": "#d40000",
                                  "In Progress": "#4dd0e1", 
                                  "Completed": "#52C41A"
                              })
            colors = get_colors()
            fig_donut.update_layout(
                height=450,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color=colors['text'])
            )
            st.plotly_chart(fig_donut, use_container_width=True)
            
    # Prognose: Forecast for next period with selectable granularity
    st.markdown("---")
    st.markdown("#### 📈 Teamprognose")
    
    # Granularity selector
    granularity = st.selectbox(
        "Granularität wählen:",
        options=["Monatlich", "Quartalsweise", "Jährlich"],
        index=0,
        help="Wählen Sie die Zeitgranularität für die Prognose aus."
    )
    
    # Set freq based on granularity
    if granularity == "Monatlich":
        freq = 'MS'
        x_title = 'Monat'
        title_suffix = 'pro Monat'
    elif granularity == "Quartalsweise":
        freq = 'QS'
        x_title = 'Quartal'
        title_suffix = 'pro Quartal'
    else:  # Jährlich
        freq = 'YS'
        x_title = 'Jahr'
        title_suffix = 'pro Jahr'
    
    # Time period selector with calendar
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Startdatum:",
            value=pd.Timestamp.today().normalize(),
            help="Wählen Sie das Startdatum für die Prognose aus."
        )
    with col2:
        end_date = st.date_input(
            "Enddatum:",
            value=pd.Timestamp.today().normalize() + pd.DateOffset(years=2),
            help="Wählen Sie das Enddatum für die Prognose aus."
        )
    
    # Validate dates
    if start_date >= end_date:
        st.error("Das Startdatum muss vor dem Enddatum liegen.")
        st.stop()
    
    # Calculate periods based on granularity and date range
    start_month = pd.Timestamp(start_date).replace(day=1)
    date_range = pd.date_range(start=start_month, end=end_date, freq=freq)
    periods = len(date_range)
    
    forecast_periods = date_range
    forecast_df = pd.DataFrame({x_title: forecast_periods})

    forecast_df['Aktive Mitglieder'] = forecast_df[x_title].apply(
        lambda m: ((df['start_date'] <= m) & ((df['planned_exit'].isna()) | (df['planned_exit'] > m))).sum()
    )
    forecast_df['Geplante Austritte'] = forecast_df[x_title].apply(
        lambda m: (df['planned_exit'].dt.to_period(freq[0].upper()) == m.to_period(freq[0].upper())).sum()
    )

    fig_forecast = px.line(
        forecast_df,
        x=x_title,
        y=['Aktive Mitglieder', 'Geplante Austritte'],
        labels={'value': 'Anzahl', x_title: x_title, 'variable': 'Metrik'},
        title=f'Teamprognose: Aktive Mitglieder und Austritte {title_suffix}'
    )

    # Add range slider for better navigation when many periods
    fig_forecast.update_xaxes(rangeslider_visible=True)

    st.plotly_chart(fig_forecast, use_container_width=True)

    # Summary chart: Entries and Exits per Year
    years = pd.date_range(start=start_date, end=end_date, freq='YS').year
    summary_data = []
    for year in years:
        entries = ((df['start_date'].dt.year == year)).sum()
        exits = ((df['planned_exit'].dt.year == year)).sum()
        summary_data.append({'Jahr': year, 'Eintritte': entries, 'Austritte': exits})
    
    summary_df = pd.DataFrame(summary_data)
    
    if not summary_df.empty:
        fig_summary = px.bar(
            summary_df,
            x='Jahr',
            y=['Eintritte', 'Austritte'],
            labels={'value': 'Anzahl', 'Jahr': 'Jahr', 'variable': 'Typ'},
            title='Jährliche Eintritte und Austritte',
            barmode='group'
        )
        fig_summary.update_layout(height=300)
        st.plotly_chart(fig_summary, use_container_width=True)

    # Kritische Alerts Tabelle
    critical_df = df[df['days_until_exit'] < 180][['name', 'role', 'components', 'days_until_exit', 'priority']]
    critical_df = critical_df.sort_values('days_until_exit')

    st.markdown("#### 🚨 Kritische Austritte (< 180 Tage)")
    if not critical_df.empty:
        st.dataframe(critical_df, use_container_width=True)
    else:
        st.success("✅ Keine kritischen Austritte in den nächsten 6 Monaten.") # Langere Augenblick , weil Rekrutierunngsphase (ca.3 Monate) laenger braucht.

    # Geburtstagsliste für den aktuellen Monat
    current_month = pd.Timestamp.today().month
    birthday_df = df[df['dob'].dt.month == current_month][['name', 'role', 'dob', 'age']]
    birthday_df = birthday_df.sort_values('dob')

    st.markdown("#### 🎂 Geburtstage diesen Monat")
    if not birthday_df.empty:
        st.dataframe(birthday_df, use_container_width=True)
    else:
        st.info("ℹ️ Keine Geburtstage in diesem Monat.")

    # DISPLAY COMPONENT RESPONSIBILITIES TABLE
    if 'component_map' in st.session_state and st.session_state.component_map:
        st.markdown("---")
        st.markdown("#### 🧪 Komponentenübersicht (Kurz)")
        # create a compact view: Komponente, Verantwortlich, Benötigt
        comp_list = []
        transfer_alerts = []
        for comp, resp in st.session_state.component_map.items():
            needed = int(st.session_state.component_requirements.get(comp, 1))
            transfer_months = int(st.session_state.component_transfer_times.get(comp, 6))
            resp_list = resp if isinstance(resp, (list, tuple)) else [resp]
            comp_list.append({"Komponente": comp, "Verantwortlich": ", ".join(resp_list), "Benötigt": needed, "WU-Zeit (Monate)": transfer_months})
            
            # Check for transfer alerts
            for person in resp_list:
                person_data = df[df['name'] == person]
                if not person_data.empty:
                    days_left = person_data['days_until_exit'].iloc[0]
                    if days_left < transfer_months * 30:
                        transfer_alerts.append({
                            "Komponente": comp,
                            "Verantwortlich": person,
                            "Tage bis Austritt": days_left,
                            "Benötigte WU-Zeit (Tage)": transfer_months * 30
                        })
        
        short_comp_df = pd.DataFrame(comp_list)
        st.dataframe(short_comp_df, use_container_width=True)
        
        # Transfer Alerts
        if transfer_alerts:
            st.markdown("#### 🚨 Wissensübergabe-Alerts")
            alert_df = pd.DataFrame(transfer_alerts)
            st.dataframe(alert_df, use_container_width=True)
            st.warning("⚠️ Diese Personen verlassen das Unternehmen, bevor die Wissensübergabe abgeschlossen werden kann. Planen Sie Einstellungen oder Ersatz!")
    else:
        st.info("ℹ️ Noch keine Komponenten hinzugefügt.")

    # PRODUKTEN ÜBERSICHT SECTION - CATCHY AND ILLUSTRATED
    st.markdown("---")
    st.markdown("""
    <style>
        .product-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            color: white;
            margin: 1rem 0;
        }
        .product-title {
            font-size: 2.5rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 2rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .product-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
            color: #333;
        }
        .product-card-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin: -1.5rem -1.5rem 1rem -1.5rem;
            font-size: 1.3rem;
            font-weight: 700;
        }
        .component-item {
            background: #f5f5f5;
            padding: 1rem;
            margin: 0.8rem 0;
            border-left: 4px solid #667eea;
            border-radius: 5px;
        }
        .responsible-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.7rem 0;
            background: #fafafa;
            padding: 0.7rem;
            margin: 0.5rem 0;
            border-radius: 5px;
        }
        .responsible-name {
            font-weight: 600;
            color: #333;
        }
        .critical-warning {
            background: #ffebee;
            border-left: 4px solid #ff4d4f;
            padding: 0.7rem;
            margin: 0.5rem 0;
            border-radius: 5px;
            color: #c41d7f;
            font-weight: 600;
        }
        .days-to-hire {
            background: #fff3cd;
            color: #856404;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9rem;
        }
        .safe-status {
            background: #d4edda;
            color: #155724;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    if 'component_map' in st.session_state and st.session_state.component_map:
        st.markdown('<div class="product-section">', unsafe_allow_html=True)
        st.markdown('<div class="product-title">🎯 Produkten Übersicht 🚀</div>', unsafe_allow_html=True)
        
        product_phase_lookup = {
            item.get("product_name", ""): item.get("current_phase", "Unbekannt")
            for item in st.session_state.get("products_data", [])
            if item.get("product_name")
        }
        component_details_lookup = {
            item.get("component_name", ""): item
            for item in st.session_state.get("components_data", [])
            if item.get("component_name")
        }

        # Group components by product
        products = {}
        for component, responsible in st.session_state.component_map.items():
            product = st.session_state.component_products.get(component, "Unknown")
            if product not in products:
                products[product] = {
                    "phase": product_phase_lookup.get(product, "Unbekannt"),
                    "components": [],
                }
            products[product]["components"].append(
                {
                    "name": component,
                    "responsible": responsible,
                    "details": component_details_lookup.get(component, {}),
                }
            )
        
        # Display each product
        for product in sorted(products.keys()):
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            
            # Product header with emoji
            product_emojis = {"CG": "🔧", "iUZ": "⚙️", "iBS": "💼"}
            emoji = product_emojis.get(product, "📦")
            phase = products[product]["phase"]
            st.markdown(f'<div class="product-card-header">{emoji} Produkt: {product} • Phase: {phase}</div>', unsafe_allow_html=True)
            
            # Components under this product
            st.markdown(f"**Komponenten ({len(products[product]['components'])}):**")
            for component_entry in products[product]["components"]:
                component = component_entry["name"]
                responsible = component_entry["responsible"]
                details = component_entry["details"]
                responsible_list = responsible if isinstance(responsible, (list, tuple)) else [responsible]
                complexity_score = int(details.get("complexity_score", 5))
                required_people = int(details.get("required_resources", st.session_state.component_requirements.get(component, 1)))
                transfer_time_months = int(details.get("knowledge_transfer_time_needed", st.session_state.component_transfer_times.get(component, 6)))
                documentation_status = details.get("documentation_status", "Nicht bewertet")
                backup_available = "Ja" if details.get("backup_available", False) else "Nein"
                active_assignments = get_active_component_assignments(df, component, responsible_list)

                st.markdown(f'<div class="component-item"><strong>📦 {component}</strong>', unsafe_allow_html=True)
                st.markdown(
                    f"Komplexität: **{complexity_score}/10** • Bedarf: **{required_people}** • KT-Zeit: **{transfer_time_months} Monate** • Doku: **{documentation_status}** • Backup: **{backup_available}**"
                )
                if active_assignments:
                    active_summary = ", ".join(
                        f"{item['name']} ({', '.join(item['matched_components'])})"
                        for item in active_assignments
                    )
                    st.markdown(f"**Aktive Mitarbeitende:** {active_summary}")
                else:
                    st.markdown("**Aktive Mitarbeitende:** Keine Zuordnung gefunden")
                
                # Get responsible persons data
                transfer_time_days = transfer_time_months * 30
                
                # Check each responsible person
                critical_people = []
                safe_people = []
                
                for person_name in responsible_list:
                    person_data = df[df['name'] == person_name]
                    if not person_data.empty:
                        days_until_exit = person_data['days_until_exit'].iloc[0]
                        kt_status = person_data['knowledge_transfer_status'].iloc[0]
                        
                        # Calculate days to start hiring
                        days_to_start_hiring = days_until_exit - transfer_time_days
                        
                        if days_until_exit < transfer_time_days:
                            # Critical - not enough time for knowledge transfer
                            critical_people.append({
                                'name': person_name,
                                'days_until_exit': days_until_exit,
                                'days_to_start_hiring': days_to_start_hiring,
                                'kt_status': kt_status
                            })
                        else:
                            safe_people.append({
                                'name': person_name,
                                'days_until_exit': days_until_exit,
                                'days_to_start_hiring': days_to_start_hiring,
                                'kt_status': kt_status
                            })
                
                # Display safe people first
                if safe_people:
                    st.markdown("**✅ Verantwortliche Mitarbeiter (ausreichend Zeit):**")
                    for person in safe_people:
                        st.markdown(f"""
                        <div class="responsible-item">
                            <span class="responsible-name">👤 {person['name']}</span>
                            <span class="safe-status">Sicher • Austritt: {person['days_until_exit']} Tage</span>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Display critical people in red
                if critical_people:
                    st.markdown("**🔴 KRITISCH**")
                    for person in critical_people:
                        days_msg = f"START HIRING IN {abs(person['days_to_start_hiring'])} DAYS!" if person['days_to_start_hiring'] >= 0 else f"HIRE NOW - {abs(person['days_to_start_hiring'])} DAYS OVERDUE!"
                        st.markdown(f"""
                        <div class="critical-warning">
                            👤 {person['name']}<br>
                            ⏰ Austritt in {person['days_until_exit']} Tagen<br>
                            📋 Wissensübergabe benötigt: {transfer_time_months} Monate<br>
                            🚨 {days_msg}
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="product-section">
            <div class="product-title">🎯 Produkten Übersicht</div>
            <p style="text-align: center; color: white; font-size: 1.1rem;">ℹ️ Noch keine Komponenten hinzugefügt. Fügen Sie Komponenten in der Sidebar hinzu, um die Produktübersicht zu sehen.</p>
        </div>
        """, unsafe_allow_html=True)

    colors = get_colors()
    st.sidebar.markdown(f'<h3 style="color: {colors["primary"]};">📈 Schnellstatistiken</h3>', unsafe_allow_html=True)

    if not df.empty:
        st.sidebar.metric("Gesamtes Team", len(df))
        st.sidebar.metric("Kritische Exits", len(df[df['days_until_exit'] < 180]))
        st.sidebar.metric("Komponenten-Risiken", len(comp_df[comp_df['Status'] != 'OK']) if not comp_df.empty else 0)
    else:
        st.sidebar.write("Keine Daten verfügbar")

if __name__ == "__main__":
    main()