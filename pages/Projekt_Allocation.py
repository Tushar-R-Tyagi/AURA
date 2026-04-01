import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import numpy as np

from database.session_store import (
    DEFAULT_PROJECT_COLORS,
    DEFAULT_PROJECTS,
    ensure_session_state,
    save_project_allocations,
)
from logic.allocation_service import (
    check_overallocation,
    get_next_allocation_id,
    validate_allocation_dates,
)
from logic.team_service import build_team_dataframe
from ui.theme import load_theme, render_sidebar_navigation

# Page config
st.set_page_config(
    page_title="Projekt-Allocation",
    page_icon="📅",
    layout="wide"
)

ensure_session_state()
load_theme()
render_sidebar_navigation()

# ===== DYNAMIC PRODUCT & COLOR ASSIGNMENT =====
def generate_color_palette():
    """Generate a color palette for all products (defaults + new ones dynamically)."""
    # Get all products from products_data
    products_data = st.session_state.get("products_data", [])
    product_names = [p.get("product_name") for p in products_data if p.get("product_name")]
    
    # Start with default colors
    color_map = dict(DEFAULT_PROJECT_COLORS)
    
    # Define a palette of nice distinct colors for new products
    color_palette = [
        "#9C27B0",  # Purple
        "#FF6F00",  # Orange
        "#E91E63",  # Pink
        "#00BCD4",  # Cyan
        "#4CAF50",  # Green
        "#2196F3",  # Blue
        "#F44336",  # Red
        "#3F51B5",  # Indigo
        "#795548",  # Brown
        "#009688",  # Teal
        "#607D8B",  # Blue Grey
        "#37474F",  # Dark Blue Grey
    ]
    
    # Assign colors to any new products
    used_colors = set(color_map.values())
    color_idx = 0
    
    for product_name in product_names:
        if product_name not in color_map:
            # Find unused color
            while color_palette[color_idx % len(color_palette)] in used_colors:
                color_idx += 1
            
            color_map[product_name] = color_palette[color_idx % len(color_palette)]
            used_colors.add(color_map[product_name])
            color_idx += 1
    
    return color_map, product_names


# Get dynamic projects and colors
PROJECT_COLORS, PROJECTS = generate_color_palette()

st.title("📅 Projekt-Allocation Management")
st.markdown("Verfolgung der Mitarbeiter-Allokation auf Projekte über Zeit")

# Get team data
df_team = build_team_dataframe(st.session_state.team_data)

# Sidebar for allocation management
st.sidebar.markdown("### ➕ Neue Allocation hinzufügen")

with st.sidebar.form("add_allocation"):
    # Employee selection
    employee_options = df_team['name'].tolist()
    selected_employee = st.selectbox("Mitarbeiter", employee_options)

    # Project selection - now includes all products from database
    selected_project = st.selectbox("Projekt", PROJECTS)

    # Month range selection
    col1, col2 = st.columns(2)
    with col1:
        start_month = st.date_input("Start Monat", value=datetime.now().replace(day=1))
    with col2:
        end_month = st.date_input("End Monat", value=(datetime.now() + timedelta(days=365)).replace(day=1))

    # Allocation percentage
    allocation_percentage = st.slider("Allokationsprozentsatz (%)", 0, 100, 50)

    submitted = st.form_submit_button("💾 Allocation speichern")

    if submitted:
        if not validate_allocation_dates(start_month, end_month):
            st.error("Enddatum muss nach Startdatum liegen!")
        else:
            overallocated, over_allocation_month, total_allocation = check_overallocation(
                st.session_state.project_allocations,
                selected_employee,
                start_month,
                end_month,
                allocation_percentage,
            )

            if overallocated:
                st.error(
                    f"Overallokation in {over_allocation_month}! Gesamtallokation würde {total_allocation}% übersteigen (max. 100%)."
                )
            else:
                allocation = {
                    'employee': selected_employee,
                    'project': selected_project,
                    'start_date': start_month,
                    'end_date': end_month,
                    'percentage': allocation_percentage,
                    'id': get_next_allocation_id(st.session_state.project_allocations)
                }
                st.session_state.project_allocations.append(allocation)
                save_project_allocations(st.session_state.project_allocations)
                st.success(f"✅ Allocation für {selected_employee} auf {selected_project} ({allocation_percentage}%) gespeichert!")

# Display current allocations
st.markdown("---")
st.markdown("### 📋 Aktuelle Projekt-Allocations")

if st.session_state.project_allocations:
    # Convert to DataFrame for display
    df_allocations = pd.DataFrame(st.session_state.project_allocations)

    # Format dates
    df_allocations['start_date'] = pd.to_datetime(df_allocations['start_date']).dt.strftime('%Y-%m')
    df_allocations['end_date'] = pd.to_datetime(df_allocations['end_date']).dt.strftime('%Y-%m')

    # Display table
    st.dataframe(df_allocations[['employee', 'project', 'start_date', 'end_date', 'percentage']].rename(columns={
        'employee': 'Mitarbeiter',
        'project': 'Projekt',
        'start_date': 'Start',
        'end_date': 'Ende',
        'percentage': 'Prozent (%)'
    }), use_container_width=True)

    # Delete allocation option
    st.markdown("#### 🗑️ Allocation löschen")
    allocation_options = [f"{alloc['employee']} - {alloc['project']} ({alloc['percentage']}%) - {pd.to_datetime(alloc['start_date']).strftime('%Y-%m')} bis {pd.to_datetime(alloc['end_date']).strftime('%Y-%m')}"
                         for alloc in st.session_state.project_allocations]

    if allocation_options:
        selected_to_delete = st.selectbox("Zu löschende Allocation auswählen", allocation_options)
        if st.button("🗑️ Löschen", type="secondary"):
            # Find and remove the allocation
            for i, alloc in enumerate(st.session_state.project_allocations):
                alloc_str = f"{alloc['employee']} - {alloc['project']} ({alloc['percentage']}%) - {pd.to_datetime(alloc['start_date']).strftime('%Y-%m')} bis {pd.to_datetime(alloc['end_date']).strftime('%Y-%m')}"
                if alloc_str == selected_to_delete:
                    del st.session_state.project_allocations[i]
                    save_project_allocations(st.session_state.project_allocations)
                    st.success("✅ Allocation gelöscht!")
                    st.rerun()
                    break
else:
    st.info("Keine Projekt-Allocations vorhanden. Fügen Sie eine neue Allocation hinzu.")

# Initialize date range variables
gantt_start_date = None
gantt_end_date = None

# Gantt Chart Visualization
st.markdown("---")
st.markdown("### 📊 Gantt-Chart: Projekt-Allocations")

# Time period filter
st.markdown("#### 📅 Zeitraum-Filter")

if st.session_state.project_allocations:
    # Get date range from allocations (ensure date objects)
    all_dates = []
    for alloc in st.session_state.project_allocations:
        start_date = alloc['start_date']
        end_date = alloc['end_date']
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(end_date, datetime):
            end_date = end_date.date()

        # write back normalized dates
        alloc['start_date'] = start_date
        alloc['end_date'] = end_date

        all_dates.extend([start_date, end_date])

    if all_dates:
        min_date = min(all_dates)
        max_date = max(all_dates)

        # Default to showing last 12 months if current date is within range
        today = datetime.now().date()
        default_start = max(min_date, today - timedelta(days=365))
        default_end = min(max_date, today + timedelta(days=180))  # 6 months ahead

        # Quick preset options
        st.markdown("**Schnellauswahl:**")
        preset_col1, preset_col2, preset_col3, preset_col4 = st.columns(4)

        with preset_col1:
            if st.button("📅 Letzte 6 Monate", use_container_width=True):
                st.session_state.gantt_start = max(min_date, today - timedelta(days=180))
                st.session_state.gantt_end = min(max_date, today)
                st.rerun()

        with preset_col2:
            if st.button("🔮 Nächste 6 Monate", use_container_width=True):
                st.session_state.gantt_start = max(min_date, today)
                st.session_state.gantt_end = min(max_date, today + timedelta(days=180))
                st.rerun()

        with preset_col3:
            if st.button("📊 Aktuelles Jahr", use_container_width=True):
                current_year = today.year
                st.session_state.gantt_start = max(min_date, date(current_year, 1, 1))
                st.session_state.gantt_end = min(max_date, date(current_year, 12, 31))
                st.rerun()

        with preset_col4:
            if st.button("🔍 Alle Daten", use_container_width=True):
                st.session_state.gantt_start = min_date
                st.session_state.gantt_end = max_date
                st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            gantt_start_date = st.date_input(
                "Startdatum für Gantt-Chart",
                value=st.session_state.get('gantt_start', default_start),
                min_value=min_date,
                max_value=max_date,
                key="gantt_start"
            )

        with col2:
            gantt_end_date = st.date_input(
                "Enddatum für Gantt-Chart",
                value=st.session_state.get('gantt_end', default_end),
                min_value=min_date,
                max_value=max_date,
                key="gantt_end"
            )

        # Validate date range
        if gantt_start_date and gantt_end_date:
            if gantt_start_date >= gantt_end_date:
                st.error("⚠️ Enddatum muss nach dem Startdatum liegen!")
                gantt_end_date = gantt_start_date + timedelta(days=30)  # Default to 1 month
        else:
            st.warning("⚠️ Bitte wählen Sie beide Daten aus!")

        # Filter allocations for the selected period
        filtered_allocations = []
        if gantt_start_date and gantt_end_date:
            for alloc in st.session_state.project_allocations:
                # Include allocation if it overlaps with the selected period
                if not (alloc['end_date'] < gantt_start_date or alloc['start_date'] > gantt_end_date):
                    filtered_allocations.append(alloc)

            st.info(f"📊 Zeige {len(filtered_allocations)} von {len(st.session_state.project_allocations)} Allokationen im Zeitraum {gantt_start_date.strftime('%Y-%m')} bis {gantt_end_date.strftime('%Y-%m')}")

            if filtered_allocations:
                # Create Gantt chart data with filtered allocations
                gantt_data = []

                for alloc in filtered_allocations:
                    # Get employee info
                    employee_info = df_team[df_team['name'] == alloc['employee']].iloc[0] if not df_team[df_team['name'] == alloc['employee']].empty else None

                    if employee_info is not None:
                        # Calculate FTE based on allocation percentage
                        fte_value = alloc['percentage'] / 100.0

                        gantt_data.append({
                            'Task': f"{alloc['employee']} ({alloc['project']})",
                            'Start': alloc['start_date'],
                            'Finish': alloc['end_date'],
                            'Resource': alloc['project'],
                            'Percentage': alloc['percentage'],
                            'FTE': fte_value,
                            'Employee_Type': employee_info['employee_type'],
                            'Role': employee_info['role']
                        })

                if gantt_data:
                    df_gantt = pd.DataFrame(gantt_data)

                    # Make sure date types are accepted by plotly (datetime64)
                    df_gantt['Start'] = pd.to_datetime(df_gantt['Start'])
                    df_gantt['Finish'] = pd.to_datetime(df_gantt['Finish'])

                    # Create Gantt chart with plotly.express timeline for reliable bars
                    fig = px.timeline(
                        df_gantt,
                        x_start='Start',
                        x_end='Finish',
                        y='Task',
                        color='Resource',
                        color_discrete_map=PROJECT_COLORS,
                        hover_data=['Percentage', 'FTE', 'Employee_Type', 'Role']
                    )

                    # Add percentage labels on each bar
                    for idx, row in df_gantt.iterrows():
                        mid_date = row['Start'] + (row['Finish'] - row['Start']) / 2
                        fig.add_annotation(
                            x=mid_date,
                            y=row['Task'],
                            text=f"{row['Percentage']:.0f}%",
                            showarrow=False,
                            font=dict(color='white', size=12, family='Arial Black'),
                            bgcolor='rgba(0,0,0,0.3)',
                            bordercolor='rgba(255,255,255,0.5)',
                            borderwidth=1,
                            borderpad=4,
                            ax=0,
                            ay=0
                        )

                    fig.update_yaxes(autorange='reversed')
                    fig.update_layout(
                        title=f"Projekt-Allocation Gantt-Chart ({gantt_start_date.strftime('%Y-%m')} bis {gantt_end_date.strftime('%Y-%m')})",
                        xaxis_title='Zeitraum',
                        yaxis_title='Mitarbeiter (Projekt)',
                        height=max(400, len(df_gantt) * 30),
                        legend_title='Projekt'
                    )

                    fig.update_xaxes(type='date', range=[gantt_start_date, gantt_end_date])

                    st.plotly_chart(fig, use_container_width=True)

                    # Summary statistics for filtered period
                    st.markdown("#### 📈 Zusammenfassung für ausgewählten Zeitraum")

                    # Create dynamic columns based on number of projects
                    num_projects = len(PROJECTS)
                    cols = st.columns(min(num_projects, 4))  # Max 4 columns per row

                    for i, project in enumerate(PROJECTS):
                        project_allocs = df_gantt[df_gantt['Resource'] == project]
                        total_fte_months = 0

                        for idx, row in project_allocs.iterrows():
                            # Convert Timestamp to date for comparison
                            row_start = row['Start'].date() if hasattr(row['Start'], 'date') else row['Start']
                            row_end = row['Finish'].date() if hasattr(row['Finish'], 'date') else row['Finish']

                            # Calculate actual months shown in the filtered period
                            actual_start = max(row_start, gantt_start_date)
                            actual_end = min(row_end, gantt_end_date)
                            if actual_start < actual_end:
                                months_diff = (actual_end.year - actual_start.year) * 12 + (actual_end.month - actual_start.month) + 1
                                total_fte_months += row['FTE'] * months_diff

                        col_index = i % min(num_projects, 4)
                        with cols[col_index]:
                            st.metric(f"{project} FTE-Monate", f"{total_fte_months:.1f}")
                else:
                    st.info("Keine Allokationen im ausgewählten Zeitraum gefunden.")
        else:
            st.info("Bitte wählen Sie einen gültigen Zeitraum aus.")
    else:
        st.info("Keine Allokationsdaten verfügbar.")
else:
    st.info("Keine Daten für Gantt-Chart verfügbar.")

# Monthly allocation overview
st.markdown("---")
st.markdown("### 📅 Monatliche Übersicht")

if st.session_state.project_allocations:
    # Use the same date range as Gantt chart for consistency
    if gantt_start_date and gantt_end_date:
        monthly_start = gantt_start_date
        monthly_end = gantt_end_date
    else:
        # Fallback to full range
        all_dates = []
        for alloc in st.session_state.project_allocations:
            all_dates.extend([alloc['start_date'], alloc['end_date']])
        monthly_start = min(all_dates) if all_dates else datetime.now().date()
        monthly_end = max(all_dates) if all_dates else datetime.now().date() + timedelta(days=365)

    # Generate monthly breakdown for selected period
    monthly_data = []

    # Generate all months in selected range
    current_date = monthly_start.replace(day=1) if hasattr(monthly_start, 'replace') else monthly_start
    end_limit = monthly_end.replace(day=1) if hasattr(monthly_end, 'replace') else monthly_end
    
    while current_date <= end_limit:
        month_data = {'Month': current_date.strftime('%Y-%m')}

        # Calculate per project FTE
        for project in PROJECTS:
            total_fte = 0
            for alloc in st.session_state.project_allocations:
                if (alloc['project'] == project and
                    alloc['start_date'] <= current_date <= alloc['end_date']):
                    total_fte += alloc['percentage'] / 100.0
            month_data[f'{project} FTE'] = total_fte

        # Calculate per employee total allocation
        employee_allocations = {}
        for alloc in st.session_state.project_allocations:
            if alloc['start_date'] <= current_date <= alloc['end_date']:
                emp = alloc['employee']
                if emp not in employee_allocations:
                    employee_allocations[emp] = 0
                employee_allocations[emp] += alloc['percentage']

        for emp in df_team['name'].unique():
            month_data[f'{emp} Total %'] = employee_allocations.get(emp, 0)

        monthly_data.append(month_data)
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)

    df_monthly = pd.DataFrame(monthly_data)
    st.dataframe(df_monthly, use_container_width=True)

    # Monthly chart
    fig_monthly = go.Figure()

    for project in PROJECTS:
        fig_monthly.add_trace(go.Scatter(
            x=df_monthly['Month'],
            y=df_monthly[f'{project} FTE'],
            mode='lines+markers',
            name=project,
            line=dict(color=PROJECT_COLORS[project], width=3),
            marker=dict(size=8)
        ))

    fig_monthly.update_layout(
        title=f"Monatliche FTE-Entwicklung pro Projekt ({monthly_start.strftime('%Y-%m')} bis {monthly_end.strftime('%Y-%m')})",
        xaxis_title="Monat",
        yaxis_title="Gesamt FTE",
        height=400
    )

    st.plotly_chart(fig_monthly, use_container_width=True)

    # Employee utilization chart
    st.markdown("#### 👥 Mitarbeiter-Auslastung")

    employee_cols = [col for col in df_monthly.columns if 'Total %' in col]
    if employee_cols:
        fig_employees = go.Figure()

        for emp_col in employee_cols:
            emp_name = emp_col.replace(' Total %', '')
            fig_employees.add_trace(go.Scatter(
                x=df_monthly['Month'],
                y=df_monthly[emp_col],
                mode='lines+markers',
                name=emp_name,
                line=dict(width=2),
                marker=dict(size=6)
            ))

        # Add 100% reference line
        fig_employees.add_trace(go.Scatter(
            x=df_monthly['Month'],
            y=[100] * len(df_monthly),
            mode='lines',
            name='100% Kapazität',
            line=dict(color='red', dash='dash', width=1),
            showlegend=True
        ))

        fig_employees.update_layout(
            title=f"Mitarbeiter-Gesamtauslastung über Zeit ({monthly_start.strftime('%Y-%m')} bis {monthly_end.strftime('%Y-%m')})",
            xaxis_title="Monat",
            yaxis_title="Auslastung (%)",
            height=400
        )

        st.plotly_chart(fig_employees, use_container_width=True)
else:
    st.info("Keine monatlichen Daten verfügbar.")