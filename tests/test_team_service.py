import pandas as pd

from logic.team_service import (
    TEAM_COLUMNS,
    build_team_dataframe,
    calculate_kt_status_from_tenure,
    calculate_priority_from_tenure,
    get_kt_status_mapping,
    update_priorities_from_tenure,
)


def test_get_kt_status_mapping_contains_bidirectional_values() -> None:
    mapping = get_kt_status_mapping()

    assert mapping["Nicht gestartet"] == "Not Started"
    assert mapping["In Progress"] == "In Bearbeitung"


def test_tenure_based_calculations_return_expected_buckets() -> None:
    today = pd.Timestamp.today().normalize()

    recent = (today - pd.Timedelta(days=30)).strftime("%Y-%m-%d")
    medium = (today - pd.Timedelta(days=365)).strftime("%Y-%m-%d")
    old = (today - pd.Timedelta(days=1000)).strftime("%Y-%m-%d")

    assert calculate_priority_from_tenure(recent) == "High"
    assert calculate_priority_from_tenure(medium) == "Medium"
    assert calculate_priority_from_tenure(old) == "Low"

    assert calculate_kt_status_from_tenure(recent) == "Not Started"
    assert calculate_kt_status_from_tenure(medium) == "In Progress"
    assert calculate_kt_status_from_tenure(old) == "Completed"


def test_update_priorities_respects_manual_override() -> None:
    today = pd.Timestamp.today().normalize()
    start_recent = (today - pd.Timedelta(days=60)).strftime("%Y-%m-%d")
    start_old = (today - pd.Timedelta(days=1000)).strftime("%Y-%m-%d")

    team_data = [
        {
            "name": "Auto",
            "start_date": start_recent,
            "priority": "Low",
            "knowledge_transfer_status": "Completed",
            "manual_override": False,
        },
        {
            "name": "Manual",
            "start_date": start_old,
            "priority": "Critical",
            "knowledge_transfer_status": "Not Started",
            "manual_override": True,
        },
    ]

    update_priorities_from_tenure(team_data)

    assert team_data[0]["priority"] == "High"
    assert team_data[0]["knowledge_transfer_status"] == "Not Started"
    assert team_data[1]["priority"] == "Critical"
    assert team_data[1]["knowledge_transfer_status"] == "Not Started"


def test_build_team_dataframe_handles_empty_input() -> None:
    df = build_team_dataframe([])
    assert list(df.columns) == TEAM_COLUMNS
    assert df.empty


def test_build_team_dataframe_adds_derived_columns_and_default_team() -> None:
    today = pd.Timestamp.today().normalize()
    planned_exit = (today + pd.Timedelta(days=45)).strftime("%Y-%m-%d")
    start_date = (today - pd.Timedelta(days=400)).strftime("%Y-%m-%d")

    team_data = [
        {
            "name": "Mia",
            "role": "Engineer",
            "employee_type": "Intern",
            "components": "A",
            "start_date": start_date,
            "planned_exit": planned_exit,
            "knowledge_transfer_status": "In Progress",
            "priority": "Medium",
            "dob": "1990-05-10",
        }
    ]

    df = build_team_dataframe(team_data)

    assert "team" in df.columns
    assert df.loc[0, "team"] == "Unassigned"
    assert "age" in df.columns
    assert "days_until_exit" in df.columns
    assert "tenure_days" in df.columns
    assert pd.notna(df.loc[0, "days_until_exit"])
