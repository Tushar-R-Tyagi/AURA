import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

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

st.title("🛠️ Stammdaten & Teamverwaltung")
st.markdown("Alle Eingaben, Bearbeitungen und administrativen Aktionen sind jetzt hier gebündelt – getrennt vom Executive Dashboard.")

team_tab, master_tab, admin_tab = st.tabs([
    "👥 Teamdaten bearbeiten",
    "🧩 Produkte & Komponenten",
    "⚙️ Admin-Aktionen",
])

with team_tab:
    st.markdown("### 👥 Teamdaten pflegen")
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
