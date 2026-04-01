import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
import json

from database.session_store import (
    ensure_session_state,
    save_component_state,
    save_employee_settings,
    save_project_allocations,
    save_team_data,
)
from database.defaults import DEFAULT_PROJECTS
from logic.team_service import (
    build_team_dataframe,
    calculate_kt_status_from_tenure,
    calculate_priority_from_tenure,
    get_kt_status_mapping,
)
from ui.theme import load_theme, render_sidebar_navigation


st.set_page_config(
    page_title="Stammdaten Management",
    page_icon="🛠️",
    layout="wide",
)

ensure_session_state()
load_theme()
render_sidebar_navigation()
st.session_state.setdefault("editing_index", None)


def parse_component_names(value):
    """Normalize component values into a clean string list."""
    if isinstance(value, (list, tuple, set)):
        raw_items = value
    else:
        raw_items = str(value or "").split(",")
    return [str(item).strip() for item in raw_items if str(item).strip()]


# ============= BULK IMPORT HELPER FUNCTIONS =============

def create_employee_template():
    """Create a sample Excel template for employee bulk import."""
    template_data = {
        'name': ['Max Mustermann', 'Anna Schmidt'],
        'role': ['Senior Developer', 'Product Manager'],
        'employee_type': ['Intern', 'Lead Cost Employee (LCE)'],
        'team': ['CS1', 'CS2'],
        'components': ['Component A, Component B', 'Component C'],
        'weekly_hours': [35, 40],
        'hourly_rate': [75.50, 85.00],
        'start_date': ['2024-01-15', '2023-06-01'],
        'planned_exit': ['2026-12-31', '2025-12-31'],
        'dob': ['1990-05-20', '1988-11-10'],
    }
    return pd.DataFrame(template_data)


def create_product_template():
    """Create a sample Excel template for product bulk import."""
    template_data = {
        'product_name': ['Product A', 'Product B'],
        'current_phase': ['Umsetzung', 'Planung'],
        'description': ['Description of Product A', 'Description of Product B'],
    }
    return pd.DataFrame(template_data)


def create_component_template():
    """Create a sample Excel template for component bulk import."""
    template_data = {
        'component_name': ['Component A', 'Component B'],
        'product_name': ['Product A', 'Product A'],
        'responsible_persons': ['Max Mustermann; Anna Schmidt', 'Max Mustermann'],
        'complexity_score': [7, 5],
        'required_resources': [2, 1],
        'knowledge_transfer_time_needed': [6, 3],
        'documentation_status': ['Gut', 'Mittel'],
        'backup_available': [True, False],
    }
    return pd.DataFrame(template_data)


def validate_employee_data(df):
    """Validate employee data before importing."""
    errors = []
    required_cols = ['name', 'role', 'employee_type']
    
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"❌ Pflicht-Spalte fehlt: '{col}'")
    
    if not errors:
        for idx, row in df.iterrows():
            if pd.isna(row['name']) or str(row['name']).strip() == '':
                errors.append(f"❌ Zeile {idx+1}: Name ist erforderlich")
            if pd.isna(row['role']) or str(row['role']).strip() == '':
                errors.append(f"❌ Zeile {idx+1}: Role ist erforderlich")
            if row['employee_type'] not in ['Intern', 'Lead Cost Employee (LCE)', 'Extern']:
                errors.append(f"❌ Zeile {idx+1}: Ungültiger Mitarbeitertyp (erlaubt: Intern, Lead Cost Employee (LCE), Extern)")
    
    return errors


def validate_product_data(df):
    """Validate product data before importing."""
    errors = []
    required_cols = ['product_name', 'current_phase']
    
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"❌ Pflicht-Spalte fehlt: '{col}'")
    
    if not errors:
        valid_phases = ["Idee", "Planung", "Design", "Umsetzung", "Test", "Rollout", "Betrieb"]
        for idx, row in df.iterrows():
            if pd.isna(row['product_name']) or str(row['product_name']).strip() == '':
                errors.append(f"❌ Zeile {idx+1}: Produktname ist erforderlich")
            if row['current_phase'] not in valid_phases:
                errors.append(f"❌ Zeile {idx+1}: Ungültige Phase (erlaubt: {', '.join(valid_phases)})")
    
    return errors


def validate_component_data(df, available_products, available_employees):
    """Validate component data before importing."""
    errors = []
    required_cols = ['component_name', 'product_name', 'responsible_persons']
    
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"❌ Pflicht-Spalte fehlt: '{col}'")
    
    if not errors:
        for idx, row in df.iterrows():
            if pd.isna(row['component_name']) or str(row['component_name']).strip() == '':
                errors.append(f"❌ Zeile {idx+1}: Komponentenname ist erforderlich")
            if pd.isna(row['product_name']) or str(row['product_name']).strip() == '':
                errors.append(f"❌ Zeile {idx+1}: Produktname ist erforderlich")
            elif str(row['product_name']).strip() not in available_products:
                errors.append(f"❌ Zeile {idx+1}: Produkt '{row['product_name']}' existiert nicht")
            if pd.isna(row['responsible_persons']) or str(row['responsible_persons']).strip() == '':
                errors.append(f"❌ Zeile {idx+1}: Verantwortliche Person(en) erforderlich (durch Semikolon trennen)")
    
    return errors


def import_employees_from_df(df):
    """Import employees from DataFrame."""
    imported_count = 0
    skipped_count = 0
    skipped_names = []
    
    for idx, row in df.iterrows():
        name = str(row.get('name', '')).strip()
        
        # Check if employee already exists
        existing = next((emp for emp in st.session_state.team_data if emp['name'] == name), None)
        if existing:
            skipped_count += 1
            skipped_names.append(name)
            continue
        
        # Parse components
        components_str = str(row.get('components', '')).strip()
        all_components = parse_component_names(components_str)
        
        # Get defaults for missing values
        employee_type = str(row.get('employee_type', 'Intern')).strip()
        weekly_hours = int(row.get('weekly_hours', 35)) if pd.notna(row.get('weekly_hours')) else 35
        hourly_rate = float(row.get('hourly_rate', 0)) if pd.notna(row.get('hourly_rate')) else 0.0
        start_date = row.get('start_date', datetime.now().strftime('%Y-%m-%d'))
        planned_exit = row.get('planned_exit', (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'))
        dob = row.get('dob', '1990-01-01')
        team = str(row.get('team', 'Unassigned')).strip()
        
        # Create employee record
        new_member = {
            'name': name,
            'role': str(row.get('role', '')).strip(),
            'employee_type': employee_type,
            'components': ', '.join(all_components),
            'start_date': str(start_date).strip(),
            'planned_exit': str(planned_exit).strip(),
            'knowledge_transfer_status': 'Nicht gestartet',
            'priority': calculate_priority_from_tenure(str(start_date).strip()),
            'dob': str(dob).strip(),
            'team': team,
            'manual_override': True,
        }
        
        st.session_state.team_data.append(new_member)
        st.session_state.employee_settings[name] = {
            'hourly_rate': float(hourly_rate),
            'weekly_hours': int(weekly_hours),
        }
        imported_count += 1
    
    return imported_count, skipped_count, skipped_names


def import_products_from_df(df):
    """Import products from DataFrame."""
    imported_count = 0
    updated_count = 0
    
    for idx, row in df.iterrows():
        product_name = str(row.get('product_name', '')).strip()
        
        if not product_name:
            continue
        
        product_record = {
            'product_name': product_name,
            'current_phase': str(row.get('current_phase', 'Planung')).strip(),
            'description': str(row.get('description', '')).strip(),
            'components': [],
        }
        
        # Check if product exists
        existing_idx = next(
            (i for i, p in enumerate(st.session_state.products_data) if p.get('product_name') == product_name),
            None
        )
        
        if existing_idx is not None:
            st.session_state.products_data[existing_idx] = product_record
            updated_count += 1
        else:
            st.session_state.products_data.append(product_record)
            imported_count += 1
    
    return imported_count, updated_count


def import_components_from_df(df):
    """Import components from DataFrame."""
    imported_count = 0
    updated_count = 0
    errors = []
    
    for idx, row in df.iterrows():
        component_name = str(row.get('component_name', '')).strip()
        
        if not component_name:
            continue
        
        # Parse responsible persons (semicolon-separated)
        responsible_str = str(row.get('responsible_persons', '')).strip()
        responsible_list = [p.strip() for p in responsible_str.split(';') if p.strip()]
        
        component_record = {
            'component_name': component_name,
            'product_name': str(row.get('product_name', '')).strip(),
            'responsible_persons': responsible_list,
            'complexity_score': int(row.get('complexity_score', 5)) if pd.notna(row.get('complexity_score')) else 5,
            'knowledge_transfer_time_needed': int(row.get('knowledge_transfer_time_needed', 6)) if pd.notna(row.get('knowledge_transfer_time_needed')) else 6,
            'required_resources': int(row.get('required_resources', 1)) if pd.notna(row.get('required_resources')) else 1,
            'documentation_status': str(row.get('documentation_status', 'Nicht bewertet')).strip(),
            'backup_available': bool(row.get('backup_available', False)) if pd.notna(row.get('backup_available')) else False,
        }
        
        # Check if component exists
        existing_idx = next(
            (i for i, c in enumerate(st.session_state.components_data) if c.get('component_name') == component_name),
            None
        )
        
        if existing_idx is not None:
            st.session_state.components_data[existing_idx] = component_record
            updated_count += 1
        else:
            st.session_state.components_data.append(component_record)
            imported_count += 1
    
    return imported_count, updated_count



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


sync_master_data_to_legacy_state()
df = build_team_dataframe(st.session_state.team_data)

# Ensure DEFAULT_PROJECTS (CG, iUZ, IBS) are always in products_data
existing_product_names = {p.get("product_name") for p in st.session_state.products_data}
for default_product in DEFAULT_PROJECTS:
    if default_product not in existing_product_names:
        st.session_state.products_data.append({
            "product_name": default_product,
            "current_phase": "Betrieb" if default_product in ["CG", "iUZ"] else "Planung",
            "description": f"Standardprodukt: {default_product}",
            "components": [],
        })
        save_component_state()



st.title("🛠️ Stammdaten & Teamverwaltung")
st.markdown("Alle Eingaben, Bearbeitungen und administrativen Aktionen sind jetzt hier gebündelt – getrennt vom Executive Dashboard.")

team_tab, master_tab, admin_tab = st.tabs([
    "👥 Teamdaten bearbeiten",
    "🧩 Produkte & Komponenten",
    "⚙️ Admin-Aktionen",
])

with team_tab:
    st.markdown("### 👥 Teamdaten pflegen")
    
    # Bulk import section
    st.markdown("#### 📥 Großmengen-Import für Mitarbeiter")
    import_col1, import_col2 = st.columns(2)
    
    with import_col1:
        st.markdown("**Schritt 1:** Vorlage herunterladen")
        employee_template = create_employee_template()
        csv_buffer = BytesIO()
        employee_template.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        st.download_button(
            label="📄 Mitarbeiter-Vorlage (CSV)",
            data=csv_buffer.getvalue(),
            file_name="mitarbeiter_vorlage.csv",
            mime="text/csv",
        )
    
    with import_col2:
        st.markdown("**Schritt 2:** Datei hochladen")
        uploaded_employees = st.file_uploader(
            "CSV oder Excel-Datei mit Mitarbeitern",
            type=["csv", "xlsx"],
            key="employee_uploader",
            help="Verwenden Sie die heruntergeladene Vorlage"
        )
    
    if uploaded_employees is not None:
        try:
            if uploaded_employees.name.endswith('.csv'):
                employee_df = pd.read_csv(uploaded_employees)
            else:
                employee_df = pd.read_excel(uploaded_employees)
            
            # Validate data
            validation_errors = validate_employee_data(employee_df)
            
            if validation_errors:
                st.error("⚠️ Daten-Validierungsfehler:")
                for error in validation_errors:
                    st.write(error)
            else:
                st.success(f"✅ {len(employee_df)} Mitarbeiter gefunden - Vorschau:")
                st.dataframe(employee_df.head(10), use_container_width=True)
                
                if st.button("💾 Mitarbeiter importieren", key="import_employees_btn"):
                    imported, skipped, skipped_names = import_employees_from_df(employee_df)
                    save_team_data(st.session_state.team_data)
                    save_employee_settings(st.session_state.employee_settings)
                    
                    st.success(f"✅ {imported} Mitarbeiter importiert")
                    if skipped > 0:
                        st.warning(f"⏭️ {skipped} Mitarbeiter übersprungen (existieren bereits): {', '.join(skipped_names)}")
                    st.rerun()
        except Exception as e:
            st.error(f"❌ Fehler beim Lesen der Datei: {str(e)}")
    
    st.markdown("---")
    
    form_col, summary_col = st.columns([1.1, 0.9])

    with form_col:
        st.markdown("#### ➕ Neues Teammitglied hinzufügen")
        known_component_options = sorted(
            set(st.session_state.get("component_map", {}).keys()).union(
                {
                    component.get("component_name", "")
                    for component in st.session_state.get("components_data", [])
                    if component.get("component_name")
                }
            )
        )

        with st.form("add_member", clear_on_submit=True):
            name = st.text_input("Vollständiger Name")
            role = st.text_input("Rolle/Position")
            employee_type = st.selectbox("Mitarbeitertyp", ["Intern", "Lead Cost Employee (LCE)", "Extern"])
            team = st.selectbox("Team", ["CS1", "CS2", "CS3", "CS4", "CS5", "Unassigned"], index=5)
            selected_components = st.multiselect("Zugeordnete Komponenten", options=known_component_options)
            extra_components = st.text_input("Weitere Komponenten (kommagetrennt)")
            dob = st.date_input("Geburtsdatum", value=datetime(1990, 1, 1))

            col_fin1, col_fin2 = st.columns(2)
            with col_fin1:
                weekly_hours_default = int(st.session_state.budget_data.get(employee_type, {}).get("weekly_hours", 35) or 35)
                weekly_hours = st.number_input("Kontakt-/Wochenstunden", min_value=0, max_value=80, value=weekly_hours_default, step=1)
            with col_fin2:
                hourly_rate_default = float(st.session_state.budget_data.get(employee_type, {}).get("hourly_rate", 0) or 0)
                hourly_rate = st.number_input("Stundensatz (€/h)", min_value=0.0, value=hourly_rate_default, step=0.5)

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Startdatum", value=datetime.now())
            with col2:
                planned_exit = st.date_input("Planned Exit", value=datetime.now() + timedelta(days=365))

            col3, col4 = st.columns(2)
            with col3:
                calculated_kt_status = calculate_kt_status_from_tenure(start_date.strftime("%Y-%m-%d"))
                kt_mapping = get_kt_status_mapping()
                kt_options = ["Nicht gestartet", "In Bearbeitung", "Abgeschlossen"]
                kt_status_display = kt_mapping.get(calculated_kt_status, calculated_kt_status)
                kt_status_display = st.selectbox(
                    "Status der Wissensübergabe",
                    kt_options,
                    index=kt_options.index(kt_status_display) if kt_status_display in kt_options else 0,
                    key="add_kt_status_admin",
                )
                kt_status = kt_mapping.get(kt_status_display, kt_status_display)
            with col4:
                calculated_priority = calculate_priority_from_tenure(start_date.strftime("%Y-%m-%d"))
                priority_options = ["Low", "Medium", "High", "Critical"]
                priority = st.selectbox(
                    "Prioritätsstufe",
                    priority_options,
                    index=priority_options.index(calculated_priority) if calculated_priority in priority_options else 0,
                    key="add_priority_admin",
                )

            submitted = st.form_submit_button("💾 Teammitglied speichern", use_container_width=True)
            if submitted:
                if name and role:
                    all_components = sorted(dict.fromkeys(selected_components + parse_component_names(extra_components)))
                    new_member = {
                        "name": name,
                        "role": role,
                        "employee_type": employee_type,
                        "components": ", ".join(all_components),
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "planned_exit": planned_exit.strftime("%Y-%m-%d"),
                        "knowledge_transfer_status": kt_status,
                        "priority": priority,
                        "dob": dob.strftime("%Y-%m-%d"),
                        "team": team,
                        "manual_override": True,
                    }
                    st.session_state.team_data.append(new_member)
                    st.session_state.employee_settings[name] = {
                        "hourly_rate": float(hourly_rate),
                        "weekly_hours": int(weekly_hours),
                    }
                    save_team_data(st.session_state.team_data)
                    save_employee_settings(st.session_state.employee_settings)
                    st.success(f"✅ {name} wurde hinzugefügt.")
                    st.rerun()
                else:
                    st.error("Bitte mindestens Name und Rolle ausfüllen.")

    with summary_col:
        st.markdown("#### 📋 Aktuelles Team")
        if not df.empty:
            st.metric("Teamgröße", len(df))
            st.metric("Kritische Exits (<180 Tage)", int((df["days_until_exit"] < 180).sum()))
            st.metric("Teams", int(df["team"].nunique()))
            roster_df = df[["name", "role", "team", "employee_type", "priority", "days_until_exit"]].copy()
            roster_df.columns = ["Name", "Rolle", "Team", "Typ", "Priorität", "Tage bis Austritt"]
            st.dataframe(roster_df, use_container_width=True, height=360)
        else:
            st.info("Noch keine Teamdaten vorhanden.")

    st.markdown("---")
    st.markdown("#### ✏️ Bestehende Teammitglieder bearbeiten")

    if not st.session_state.team_data:
        st.info("Keine Teammitglieder vorhanden.")
    else:
        for i, member in enumerate(st.session_state.team_data):
            with st.expander(f"👤 {member['name']} - {member['role']}", expanded=False):
                info_col, action_col = st.columns([3, 1])

                with info_col:
                    st.write(f"**Components:** {member['components']}")
                    st.write(f"**Team:** {member.get('team', 'Unassigned')}")
                    st.write(f"**Startdatum:** {member['start_date']}")
                    st.write(f"**Planned Exit:** {member['planned_exit']}")
                    st.write(f"**Wissensübergabe:** {member['knowledge_transfer_status']}")
                    st.write(f"**Priorität:** {member['priority']}")

                with action_col:
                    col_edit, col_del = st.columns(2)
                    with col_edit:
                        if st.button("✏️ Edit", key=f"admin_edit_{i}", use_container_width=True):
                            st.session_state.editing_index = i
                    with col_del:
                        if st.button("🗑️ Delete", key=f"admin_delete_{i}", use_container_width=True):
                            removed_member = st.session_state.team_data.pop(i)
                            st.session_state.employee_settings.pop(removed_member["name"], None)
                            save_team_data(st.session_state.team_data)
                            save_employee_settings(st.session_state.employee_settings)
                            st.success(f"✅ {removed_member['name']} wurde gelöscht.")
                            st.rerun()

    if st.session_state.editing_index is not None and st.session_state.editing_index < len(st.session_state.team_data):
        st.markdown("---")
        st.markdown("#### 📝 Teammitglied bearbeiten")

        edit_index = st.session_state.editing_index
        member = st.session_state.team_data[edit_index]

        existing_settings = st.session_state.employee_settings.get(member["name"], {})
        default_weekly_hours = int(existing_settings.get("weekly_hours", st.session_state.budget_data.get(member.get("employee_type", "Intern"), {}).get("weekly_hours", 35) or 35))
        default_hourly_rate = float(existing_settings.get("hourly_rate", st.session_state.budget_data.get(member.get("employee_type", "Intern"), {}).get("hourly_rate", 0) or 0))

        with st.form(f"edit_form_{edit_index}"):
            col1, col2 = st.columns(2)

            with col1:
                edit_name = st.text_input("Vollständiger Name", value=member["name"])
                edit_role = st.text_input("Rolle/Position", value=member["role"])
                edit_employee_type = st.selectbox(
                    "Mitarbeitertyp",
                    ["Intern", "Lead Cost Employee (LCE)", "Extern"],
                    index=["Intern", "Lead Cost Employee (LCE)", "Extern"].index(member.get("employee_type", "Intern")),
                )
                edit_components = st.text_area("Wichtige Komponenten/Verantwortlichkeiten", value=member["components"])
                edit_weekly_hours = st.number_input("Kontakt-/Wochenstunden", min_value=0, max_value=80, value=default_weekly_hours, step=1)
                edit_hourly_rate = st.number_input("Stundensatz (€/h)", min_value=0.0, value=default_hourly_rate, step=0.5)

            with col2:
                edit_start_date = st.date_input("Startdatum", value=datetime.strptime(member["start_date"], "%Y-%m-%d"))
                edit_planned_exit = st.date_input("Geplantes Austrittsdatum", value=datetime.strptime(member["planned_exit"], "%Y-%m-%d"))
                calculated_kt_status = calculate_kt_status_from_tenure(member["start_date"])
                kt_mapping = get_kt_status_mapping()
                kt_options = ["Nicht gestartet", "In Bearbeitung", "Abgeschlossen"]
                current_kt_value = member.get("knowledge_transfer_status", calculated_kt_status)
                current_kt_display = kt_mapping.get(current_kt_value, current_kt_value)
                edit_kt_status_display = st.selectbox(
                    "Status der Wissensübergabe",
                    kt_options,
                    index=kt_options.index(current_kt_display) if current_kt_display in kt_options else 0,
                )
                edit_kt_status = kt_mapping.get(edit_kt_status_display, edit_kt_status_display)
                calculated_priority = calculate_priority_from_tenure(member["start_date"])
                priority_options = ["Low", "Medium", "High", "Critical"]
                edit_priority = st.selectbox(
                    "Prioritätsstufe",
                    priority_options,
                    index=priority_options.index(member.get("priority", calculated_priority)) if member.get("priority", calculated_priority) in priority_options else 0,
                )
                edit_dob = st.date_input("Geburtsdatum", value=datetime.strptime(member.get("dob", "1990-01-01"), "%Y-%m-%d"))
                teams = ["CS1", "CS2", "CS3", "CS4", "CS5", "Unassigned"]
                edit_team = st.selectbox("Team", teams, index=teams.index(member.get("team", "Unassigned")))

            col_save, col_cancel = st.columns(2)
            with col_save:
                save_clicked = st.form_submit_button("💾 Änderungen speichern", use_container_width=True)
            with col_cancel:
                cancel_clicked = st.form_submit_button("❌ Abbrechen", use_container_width=True)

            if save_clicked:
                previous_name = member["name"]
                st.session_state.team_data[edit_index] = {
                    "name": edit_name,
                    "role": edit_role,
                    "employee_type": edit_employee_type,
                    "components": edit_components,
                    "start_date": edit_start_date.strftime("%Y-%m-%d"),
                    "planned_exit": edit_planned_exit.strftime("%Y-%m-%d"),
                    "knowledge_transfer_status": edit_kt_status,
                    "priority": edit_priority,
                    "dob": edit_dob.strftime("%Y-%m-%d"),
                    "team": edit_team,
                    "manual_override": True,
                }
                if previous_name != edit_name and previous_name in st.session_state.employee_settings:
                    del st.session_state.employee_settings[previous_name]
                st.session_state.employee_settings[edit_name] = {
                    "hourly_rate": float(edit_hourly_rate),
                    "weekly_hours": int(edit_weekly_hours),
                }
                save_team_data(st.session_state.team_data)
                save_employee_settings(st.session_state.employee_settings)
                st.session_state.editing_index = None
                st.success(f"✅ {edit_name} wurde aktualisiert.")
                st.rerun()

            if cancel_clicked:
                st.session_state.editing_index = None
                st.info("Bearbeitung abgebrochen.")
                st.rerun()

with master_tab:
    st.markdown("### 🧩 Produkt- und Komponentenpflege")
    st.caption("Tipp: Wenn Sie einen bestehenden Namen erneut speichern, wird der Datensatz aktualisiert.")

    if "component_map" not in st.session_state:
        st.session_state.component_map = {}
    if "component_products" not in st.session_state:
        st.session_state.component_products = {}
    if "products_data" not in st.session_state:
        st.session_state.products_data = []
    if "components_data" not in st.session_state:
        st.session_state.components_data = []

    # ===== BULK IMPORT SECTIONS =====
    st.markdown("#### 📥 Großmengen-Import")
    bulk_col1, bulk_col2 = st.columns(2)
    
    with bulk_col1:
        st.markdown("**Produkte importieren**")
        product_template = create_product_template()
        product_csv = BytesIO()
        product_template.to_csv(product_csv, index=False)
        product_csv.seek(0)
        
        st.download_button(
            label="📄 Produkt-Vorlage (CSV)",
            data=product_csv.getvalue(),
            file_name="produkte_vorlage.csv",
            mime="text/csv",
            key="product_template_btn"
        )
        
        uploaded_products = st.file_uploader(
            "CSV oder Excel mit Produkten",
            type=["csv", "xlsx"],
            key="product_uploader",
            help="Produktname, aktuelle Phase, Beschreibung"
        )
        
        if uploaded_products is not None:
            try:
                if uploaded_products.name.endswith('.csv'):
                    product_df = pd.read_csv(uploaded_products)
                else:
                    product_df = pd.read_excel(uploaded_products)
                
                validation_errors = validate_product_data(product_df)
                if validation_errors:
                    st.error("⚠️ Validierungsfehler:")
                    for error in validation_errors:
                        st.write(error)
                else:
                    st.success(f"✅ {len(product_df)} Produkte - Vorschau:")
                    st.dataframe(product_df.head(10), use_container_width=True)
                    
                    if st.button("💾 Produkte importieren", key="import_products_btn"):
                        imported, updated = import_products_from_df(product_df)
                        save_component_state()
                        st.success(f"✅ {imported} neue Produkte, {updated} aktualisiert")
                        st.rerun()
            except Exception as e:
                st.error(f"❌ Fehler: {str(e)}")
    
    with bulk_col2:
        st.markdown("**Komponenten importieren**")
        component_template = create_component_template()
        component_csv = BytesIO()
        component_template.to_csv(component_csv, index=False)
        component_csv.seek(0)
        
        st.download_button(
            label="📄 Komponenten-Vorlage (CSV)",
            data=component_csv.getvalue(),
            file_name="komponenten_vorlage.csv",
            mime="text/csv",
            key="component_template_btn"
        )
        
        uploaded_components = st.file_uploader(
            "CSV oder Excel mit Komponenten",
            type=["csv", "xlsx"],
            key="component_uploader",
            help="Name, Produkt, Verantwortliche (durch ; trennen)"
        )
        
        if uploaded_components is not None:
            try:
                if uploaded_components.name.endswith('.csv'):
                    component_df = pd.read_excel(uploaded_components)
                else:
                    component_df = pd.read_excel(uploaded_components)
                
                available_products = [p.get('product_name') for p in st.session_state.products_data]
                available_employees = [e['name'] for e in st.session_state.team_data]
                
                validation_errors = validate_component_data(component_df, available_products, available_employees)
                if validation_errors:
                    st.error("⚠️ Validierungsfehler:")
                    for error in validation_errors:
                        st.write(error)
                else:
                    st.success(f"✅ {len(component_df)} Komponenten - Vorschau:")
                    st.dataframe(component_df.head(10), use_container_width=True)
                    
                    if st.button("💾 Komponenten importieren", key="import_components_btn"):
                        imported, updated = import_components_from_df(component_df)
                        sync_master_data_to_legacy_state()
                        save_component_state()
                        st.success(f"✅ {imported} neue Komponenten, {updated} aktualisiert")
                        st.rerun()
            except Exception as e:
                st.error(f"❌ Fehler: {str(e)}")
    
    st.markdown("---")

    product_col, component_col = st.columns(2)

    with product_col:
        st.markdown("#### 🧭 Produkt anlegen oder aktualisieren")
        with st.form("add_product_form", clear_on_submit=True):
            product_name_input = st.text_input("Produktname")
            current_phase = st.selectbox("Aktuelle Phase", ["Idee", "Planung", "Design", "Umsetzung", "Test", "Rollout", "Betrieb"])
            product_description = st.text_input("Kurzbeschreibung / Ziel")
            product_submitted = st.form_submit_button("💾 Produkt speichern", use_container_width=True)

            if product_submitted:
                product_name_clean = product_name_input.strip()
                if product_name_clean:
                    linked_components = sorted(
                        component.get("component_name", "")
                        for component in st.session_state.components_data
                        if component.get("product_name") == product_name_clean and component.get("component_name")
                    )
                    product_record = {
                        "product_name": product_name_clean,
                        "current_phase": current_phase,
                        "description": product_description.strip(),
                        "components": linked_components,
                    }
                    existing_product_index = next(
                        (
                            index
                            for index, existing in enumerate(st.session_state.products_data)
                            if existing.get("product_name") == product_name_clean
                        ),
                        None,
                    )
                    if existing_product_index is not None:
                        st.session_state.products_data[existing_product_index] = product_record
                    else:
                        st.session_state.products_data.append(product_record)
                    save_component_state()
                    st.success(f"✅ Produkt '{product_name_clean}' gespeichert.")
                    st.rerun()
                else:
                    st.error("Bitte geben Sie einen Produktnamen ein.")

    with component_col:
        st.markdown("#### 🧪 Komponente anlegen oder aktualisieren")
        product_options = [item.get("product_name") for item in st.session_state.products_data if item.get("product_name")] or ["CG", "iUZ", "iBS"]
        with st.form("add_component_form", clear_on_submit=True):
            component_name = st.text_input("Komponentenname")
            product_name = st.selectbox("Produkt", options=product_options)
            responsible_persons = st.multiselect("Verantwortliche Person(en)", options=[member["name"] for member in st.session_state.team_data])
            complexity_score = st.slider("Komplexität (1-10)", min_value=1, max_value=10, value=5)
            required_count = st.number_input("Benötigte Anzahl Personen (permanent)", min_value=1, max_value=10, value=1)
            transfer_time = st.number_input("Wissensübergabe Zeit (Monate)", min_value=1, max_value=24, value=6)
            documentation_status = st.selectbox("Dokumentationsgrad", ["Nicht bewertet", "Niedrig", "Mittel", "Gut"])
            backup_available = st.checkbox("Backup verfügbar")
            component_submitted = st.form_submit_button("💾 Komponente speichern", use_container_width=True)

            if component_submitted:
                component_name_clean = component_name.strip()
                if component_name_clean and responsible_persons:
                    component_record = {
                        "component_name": component_name_clean,
                        "product_name": product_name,
                        "responsible_persons": responsible_persons,
                        "complexity_score": int(complexity_score),
                        "knowledge_transfer_time_needed": int(transfer_time),
                        "required_resources": int(required_count),
                        "documentation_status": documentation_status,
                        "backup_available": bool(backup_available),
                    }
                    existing_component_index = next(
                        (
                            index
                            for index, existing in enumerate(st.session_state.components_data)
                            if existing.get("component_name") == component_name_clean
                        ),
                        None,
                    )
                    if existing_component_index is not None:
                        st.session_state.components_data[existing_component_index] = component_record
                    else:
                        st.session_state.components_data.append(component_record)

                    matching_product = next(
                        (item for item in st.session_state.products_data if item.get("product_name") == product_name),
                        None,
                    )
                    if matching_product is None:
                        st.session_state.products_data.append(
                            {
                                "product_name": product_name,
                                "current_phase": "Planung",
                                "description": "",
                                "components": [component_name_clean],
                            }
                        )
                    else:
                        matching_product["components"] = sorted(
                            set(parse_component_names(matching_product.get("components", [])) + [component_name_clean])
                        )

                    sync_master_data_to_legacy_state()
                    save_component_state()
                    st.success(f"✅ '{component_name_clean}' wurde gespeichert.")
                    st.rerun()
                else:
                    st.error("Bitte geben Sie einen Namen ein und wählen Sie mindestens eine verantwortliche Person aus.")

    st.markdown("---")
    overview_col1, overview_col2 = st.columns(2)
    with overview_col1:
        st.markdown("#### 📦 Aktuelle Produkte")
        product_df = pd.DataFrame(st.session_state.products_data)
        if not product_df.empty:
            st.dataframe(product_df, use_container_width=True)
        else:
            st.info("Noch keine Produkte hinterlegt.")

    with overview_col2:
        st.markdown("#### 🔩 Aktuelle Komponenten")
        component_df = pd.DataFrame(st.session_state.components_data)
        if not component_df.empty:
            st.dataframe(component_df, use_container_width=True)
        else:
            st.info("Noch keine Komponenten hinterlegt.")

with admin_tab:
    st.markdown("### ⚙️ Administrative Aktionen")
    action_col1, action_col2 = st.columns(2)

    with action_col1:
        st.markdown("#### 📊 Daten exportieren")
        st.write("Exportiert den aktuellen Teamstand als Excel-Datei.")
        if st.button("📥 Teamdaten nach Excel exportieren", use_container_width=True):
            current_df = build_team_dataframe(st.session_state.team_data)
            if not current_df.empty:
                current_df.to_excel("siemens_capacity_plan.xlsx", index=False)
                st.success("✅ Excel-Datei wurde als 'siemens_capacity_plan.xlsx' exportiert.")
            else:
                st.error("Keine Daten zum Exportieren vorhanden.")

    with action_col2:
        st.markdown("#### 🧪 System zurücksetzen")
        confirm_reset = st.checkbox("Ich bestätige, dass alle Stammdaten und Planungen gelöscht werden sollen.")
        if st.button("🗑️ Alles neu starten", type="secondary", use_container_width=True):
            if confirm_reset:
                st.session_state.team_data = []
                st.session_state.project_allocations = []
                st.session_state.employee_settings = {}
                st.session_state.component_map = {}
                st.session_state.component_requirements = {}
                st.session_state.component_transfer_times = {}
                st.session_state.component_products = {}
                st.session_state.products_data = []
                st.session_state.components_data = []
                st.session_state.editing_index = None
                save_team_data([])
                save_project_allocations([])
                save_employee_settings({})
                save_component_state()
                st.success("✅ Alle Daten wurden zurückgesetzt.")
                st.rerun()
            else:
                st.warning("Bitte bestätigen Sie den Reset zuerst.")

    st.markdown("---")
    st.info("💡 Das Executive Dashboard auf der Startseite zeigt jetzt nur noch Management-relevante KPIs und Warnungen. Alle Pflegefunktionen bleiben hier gebündelt.")
