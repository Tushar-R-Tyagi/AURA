"""Team-related business logic extracted from the Streamlit pages."""

from __future__ import annotations

import pandas as pd

TEAM_COLUMNS = [
    "name",
    "role",
    "employee_type",
    "components",
    "start_date",
    "planned_exit",
    "knowledge_transfer_status",
    "priority",
    "team",
    "dob",
]


def get_kt_status_mapping() -> dict[str, str]:
    """Return bidirectional mappings for UI display and stored values."""
    return {
        "Nicht gestartet": "Not Started",
        "In Bearbeitung": "In Progress",
        "Abgeschlossen": "Completed",
        "Not Started": "Nicht gestartet",
        "In Progress": "In Bearbeitung",
        "Completed": "Abgeschlossen",
    }


def calculate_priority_from_tenure(start_date_str: str) -> str:
    """Calculate priority based on employee tenure."""
    start_date = pd.to_datetime(start_date_str)
    tenure_days = (pd.Timestamp.today() - start_date).days

    if tenure_days < 180:
        return "High"
    if tenure_days < 730:
        return "Medium"
    return "Low"


def calculate_kt_status_from_tenure(start_date_str: str) -> str:
    """Calculate knowledge transfer status based on employee tenure."""
    start_date = pd.to_datetime(start_date_str)
    tenure_days = (pd.Timestamp.today() - start_date).days

    if tenure_days < 180:
        return "Not Started"
    if tenure_days < 730:
        return "In Progress"
    return "Completed"


def update_priorities_from_tenure(team_data: list[dict]) -> None:
    """Update derived priority and KT values for non-overridden members."""
    for member in team_data:
        if "manual_override" not in member:
            member["manual_override"] = False

        if not member.get("manual_override", False):
            member["priority"] = calculate_priority_from_tenure(member["start_date"])
            member["knowledge_transfer_status"] = calculate_kt_status_from_tenure(member["start_date"])


def build_team_dataframe(team_data: list[dict]) -> pd.DataFrame:
    """Create a normalized dataframe for dashboard and forecast logic."""
    df = pd.DataFrame(team_data)
    if df.empty:
        return pd.DataFrame(columns=TEAM_COLUMNS)

    if "team" not in df.columns:
        df["team"] = "Unassigned"

    for column in ["planned_exit", "start_date", "dob"]:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce")

    today = pd.Timestamp.today()

    if "dob" in df.columns:
        df["age"] = (
            today.year
            - df["dob"].dt.year
            - (
                (today.month < df["dob"].dt.month)
                | (
                    (today.month == df["dob"].dt.month)
                    & (today.day < df["dob"].dt.day)
                )
            )
        )

    if "planned_exit" in df.columns:
        df["days_until_exit"] = (df["planned_exit"] - today).dt.days

    if "start_date" in df.columns:
        df["tenure_days"] = (today - df["start_date"]).dt.days

    return df
