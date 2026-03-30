"""Session helpers backed by a real SQLite persistence layer."""

from __future__ import annotations

from copy import deepcopy

import streamlit as st

from database.allocation_repository import (
    load_project_allocations,
    save_project_allocations as persist_project_allocations,
)
from database.defaults import (
    DEFAULT_BUDGET_DATA,
    DEFAULT_PROJECT_COLORS,
    DEFAULT_PROJECTS,
    DEFAULT_TEAM_DATA,
    PERSISTED_STATE_DEFAULTS,
    TRANSIENT_STATE_DEFAULTS,
)
from database.finance_repository import (
    load_budget_data,
    load_employee_settings,
    save_budget_data as persist_budget_data,
    save_employee_settings as persist_employee_settings,
)
from database.schema import initialize_database
from database.settings_repository import (
    load_app_settings,
    save_app_setting,
    save_app_settings,
)
from database.team_repository import load_team_members, save_team_members as persist_team_members


def _clone(value):
    """Return a defensive copy for mutable values."""
    return deepcopy(value) if isinstance(value, (dict, list)) else value


def ensure_session_state() -> None:
    """Load persisted application state into the current Streamlit session."""
    initialize_database()

    loaders = {
        "team_data": load_team_members,
        "budget_data": load_budget_data,
        "employee_settings": load_employee_settings,
        "project_allocations": load_project_allocations,
    }

    for key, loader in loaders.items():
        if key not in st.session_state:
            st.session_state[key] = _clone(loader())

    persisted_settings = load_app_settings()
    for key, default_value in PERSISTED_STATE_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = _clone(persisted_settings.get(key, default_value))

    for key, default_value in TRANSIENT_STATE_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = _clone(default_value)


def save_team_data(team_data: list[dict] | None = None) -> None:
    """Persist the current team data list to SQLite."""
    if team_data is None:
        team_data = st.session_state.get("team_data", [])
    persist_team_members(team_data)
    st.session_state["team_data"] = _clone(team_data)


def save_budget_data(budget_data: dict | None = None) -> None:
    """Persist the current budget configuration to SQLite."""
    if budget_data is None:
        budget_data = st.session_state.get("budget_data", DEFAULT_BUDGET_DATA)
    persist_budget_data(budget_data)
    st.session_state["budget_data"] = _clone(budget_data)


def save_employee_settings(employee_settings: dict | None = None) -> None:
    """Persist the current employee-specific finance settings."""
    if employee_settings is None:
        employee_settings = st.session_state.get("employee_settings", {})
    persist_employee_settings(employee_settings)
    st.session_state["employee_settings"] = _clone(employee_settings)


def save_project_allocations(project_allocations: list[dict] | None = None) -> None:
    """Persist the current project allocation list."""
    if project_allocations is None:
        project_allocations = st.session_state.get("project_allocations", [])
    persist_project_allocations(project_allocations)
    st.session_state["project_allocations"] = _clone(project_allocations)


def save_component_state() -> None:
    """Persist component-related planning state."""
    component_settings = {
        "component_map": st.session_state.get("component_map", {}),
        "component_requirements": st.session_state.get("component_requirements", {}),
        "component_transfer_times": st.session_state.get("component_transfer_times", {}),
        "component_products": st.session_state.get("component_products", {}),
    }
    save_app_settings(component_settings)


def save_dark_mode(dark_mode: bool | None = None) -> None:
    """Persist the user's theme preference."""
    if dark_mode is None:
        dark_mode = bool(st.session_state.get("dark_mode", False))
    save_app_setting("dark_mode", dark_mode)
    st.session_state["dark_mode"] = dark_mode
